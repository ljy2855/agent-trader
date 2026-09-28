"""Watcher liveness alarm → Discord (intraday, every few minutes).

Closes the P1 gap in CLAUDE.md §10.1: ``kiwoom-watcher`` runs as a single
replica, so if the pod dies or its loop wedges mid-session, nothing
notices until the 16:00 ops digest — or until the operator happens to
open a session. A dead trading loop holding open positions is the worst
failure mode in this system: stop-losses stop firing while the market
keeps moving.

Two failure shapes, both covered:

  * **pod/service down** — ``/health`` unreachable. Alerts immediately.
  * **loop wedged** — ``/health`` answers but ``last_tick_at`` has gone
    stale (the asyncio loop is stuck, e.g. a hung agent dispatch or a
    blocked API call). The status server runs in a separate task, so it
    happily returns 200 while the trading loop is frozen — which is why
    checking liveness alone would miss this.

Alerting is gated to KRX regular sessions: off-hours the watcher
deliberately sleeps in a 600s loop, so "stale" is normal then and paging
on it would train the operator to ignore the channel.

**Spam control.** A state file on a small dedicated PVC tracks the last
alert; repeat alerts for a continuing outage are suppressed for
``--alert-cooldown-minutes`` (default 30). A recovery notice fires once
when health returns, so an "all clear" always closes an alert thread.
Read-only with respect to trading — this script never places, cancels,
or modifies an order.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# automation/ lands on sys.path[0], not the repo root — same shim as
# daily_ops_digest.py so `src.services` is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.services.krx_calendar import is_krx_regular_session_open
except Exception:  # pragma: no cover - import fallback
    is_krx_regular_session_open = None  # type: ignore[assignment]

KST = timezone(timedelta(hours=9))

WATCHER_BASE = os.environ.get("WATCHER_BASE_URL", "http://kiwoom-watcher:8001")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
MODE_LABEL = os.environ.get("TRADING_MODE_LABEL", "")
STATE_PATH = Path(os.environ.get("HEALTH_STATE_PATH", "/app/health/watcher_health.json"))

COLOR_ERROR = 15158332
COLOR_SUCCESS = 3066993


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _get_json(url: str, timeout: float = 10.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError, ValueError) as exc:
        _err(f"GET {url} failed: {exc}")
        return None


def _load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False))
    except OSError as exc:
        # A state-write failure must not suppress the alert itself; worst
        # case we re-alert next run.
        _err(f"state write failed: {exc}")


def _post_discord(title: str, description: str, color: int) -> None:
    payload = {
        "username": f"Kiwoom Watchdog {MODE_LABEL}".strip(),
        "embeds": [{"title": title, "description": description[:3900], "color": color}],
    }
    if not WEBHOOK_URL:
        _err("DISCORD_WEBHOOK_URL not set — printing instead")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "kiwoom-watcher-health/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status not in (200, 204):
                _err(f"discord status {resp.status}")
    except (urllib.error.URLError, OSError) as exc:
        _err(f"discord post failed: {exc}")


def check(stale_minutes: int) -> tuple[bool, list[str], dict]:
    """Return (healthy, problems, state_snapshot)."""
    problems: list[str] = []

    health = _get_json(f"{WATCHER_BASE}/health")
    if health is None:
        problems.append(
            f"`{WATCHER_BASE}/health` 응답 없음 — pod 다운 또는 status server 장애"
        )
        return False, problems, {}

    state = _get_json(f"{WATCHER_BASE}/state") or {}

    # A freshly (re)started watcher legitimately has no tick yet — the loop
    # needs one poll interval to produce one. Without this grace window
    # every rollout during market hours would page a false alarm, which is
    # exactly how a watchdog gets muted. Observed 2026-07-25 while
    # verifying this script right after a deploy.
    started_age_min: float | None = None
    started_at = state.get("started_at")
    if started_at:
        try:
            started_dt = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
            started_age_min = (
                datetime.now(timezone.utc) - started_dt.astimezone(timezone.utc)
            ).total_seconds() / 60
        except (ValueError, TypeError):
            started_age_min = None
    just_started = started_age_min is not None and started_age_min < stale_minutes

    # Loop-wedged detection: the status server answers from a separate
    # asyncio task, so a 200 here does NOT imply the trading loop ticked.
    last_tick = state.get("last_tick_at")
    if last_tick:
        try:
            tick_dt = datetime.fromisoformat(str(last_tick).replace("Z", "+00:00"))
            age_min = (datetime.now(timezone.utc) - tick_dt.astimezone(timezone.utc)).total_seconds() / 60
            if age_min > stale_minutes:
                problems.append(
                    f"last_tick {age_min:.0f}분 전 (임계 {stale_minutes}분) — "
                    f"루프 정지 의심 (cycle {state.get('cycle_count')})"
                )
        except (ValueError, TypeError):
            problems.append(f"last_tick_at 파싱 불가: {last_tick!r}")
    elif not just_started:
        age_note = (
            f" (기동 {started_age_min:.0f}분 경과)" if started_age_min is not None else ""
        )
        problems.append(f"last_tick_at 없음 — 루프가 한 번도 돌지 않음{age_note}")

    if state.get("last_error"):
        problems.append(f"last_error: `{state['last_error']}`")

    return (not problems), problems, state


def main() -> int:
    ap = argparse.ArgumentParser(prog="watcher_health_check")
    ap.add_argument("--stale-minutes", type=int, default=5,
                    help="last_tick 이보다 오래되면 루프 정지로 간주 (poll 30s 기준 넉넉히)")
    ap.add_argument("--alert-cooldown-minutes", type=int, default=30,
                    help="같은 장애에 대한 재알림 억제 간격")
    ap.add_argument("--ignore-session-gate", action="store_true",
                    help="장중 여부와 무관하게 검사 (수동 점검용)")
    args = ap.parse_args()

    now = datetime.now(KST)
    in_session = True
    if is_krx_regular_session_open is not None and not args.ignore_session_gate:
        in_session = is_krx_regular_session_open(now)
    if not in_session:
        print(f"{now:%Y-%m-%d %H:%M} KST — 장외/휴장, 검사 skip")
        return 0

    healthy, problems, state = check(args.stale_minutes)
    prev = _load_state()
    was_alerting = bool(prev.get("alerting"))
    last_alert_raw = prev.get("last_alert_at")

    if healthy:
        print(f"{now:%H:%M} 🟢 watcher 정상 (cycle {state.get('cycle_count')})")
        if was_alerting:
            _post_discord(
                "🟢 Watcher 복구됨",
                f"watcher가 정상 응답합니다.\n"
                f"cycle {state.get('cycle_count')} · "
                f"last_tick {str(state.get('last_tick_at'))[:19]}",
                COLOR_SUCCESS,
            )
        _save_state({"alerting": False, "last_ok_at": now.isoformat()})
        return 0

    # Unhealthy — decide whether to page or stay quiet under cooldown.
    should_alert = True
    if was_alerting and last_alert_raw:
        try:
            since = (now - datetime.fromisoformat(last_alert_raw)).total_seconds() / 60
            should_alert = since >= args.alert_cooldown_minutes
        except ValueError:
            should_alert = True

    detail = "\n".join(f"- {p}" for p in problems)
    print(f"{now:%H:%M} 🔴 문제 감지 (알림={'예' if should_alert else '쿨다운'})\n{detail}")

    if should_alert:
        _post_discord(
            f"🔴 Watcher 이상 — {now:%m/%d %H:%M} KST",
            f"장중 트레이딩 루프에 문제가 감지됐습니다. **보유 포지션이 있으면 "
            f"손절이 동작하지 않을 수 있습니다.**\n\n{detail}\n\n"
            f"```\nkubectl -n tools get pods -l app=kiwoom-watcher\n"
            f"kubectl -n tools logs deploy/kiwoom-watcher --tail=50\n```",
            COLOR_ERROR,
        )
        _save_state({"alerting": True, "last_alert_at": now.isoformat()})
    else:
        # Keep the original alert timestamp so cooldown measures from the
        # last *sent* page, not from this suppressed check.
        _save_state({"alerting": True, "last_alert_at": last_alert_raw})
    return 0


if __name__ == "__main__":
    sys.exit(main())
