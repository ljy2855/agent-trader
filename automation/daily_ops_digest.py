"""Daily operations health digest → Discord.

Read-only end-of-day system check for the intraday watcher stack. Runs as
a K8s CronJob at 16:00 KST (after the 15:55 post-market forwarder +
--close-resolved cleanup). Collects metrics from the watcher status
server (in-cluster) and the multica CLI, classifies anomalies against
fixed thresholds, and always posts a digest to Discord.

Scope is deterministic reporting only — it never modifies the trading
system. Code/deploy/strategy changes stay human-reviewed (see CLAUDE.md
§10 roadmap). stale-drop counts are log-only and intentionally omitted
here; api_failure_count (post-retry failures) is the meaningful proxy.

Data sources (all reachable from a CronJob pod, no RBAC needed):
  * http://kiwoom-watcher:8001/state — live watcher state
  * multica CLI (issue list / runs / comment list) with config secret
  * Discord webhook (env)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, time as dtime, timedelta, timezone

# Running `python automation/daily_ops_digest.py` puts automation/ on
# sys.path[0], not the repo root, so the src package isn't importable
# without this. (main_watcher.py runs from the root and never hit this.)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Used to gate the "watcher didn't tick today" check so it doesn't
    # false-positive on KRX holidays.
    from src.services.krx_calendar import is_krx_trading_day
except Exception:  # pragma: no cover - import fallback
    is_krx_trading_day = None  # type: ignore[assignment]

KST = timezone(timedelta(hours=9))
ACTION_RE = re.compile(r"<!--\s*ACTION:\s*([A-Z0-9_]+)", re.IGNORECASE)

MULTICA_BIN = os.environ.get("MULTICA_BIN", "multica")
PROJECT = os.environ.get("MULTICA_PROJECT", "")
DAILY_LABEL = os.environ.get("TRADING_MODE_LABEL", "")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
# The digest runs in-cluster, so the ClusterIP service name resolves here.
# (It does not resolve on the host where the multica agents run; they reach
# the dashboard through its LAN hostname instead.)
DASHBOARD_URL = os.environ.get(
    "KIWOOM_DASHBOARD_URL", "http://kiwoom-mcp:8000/api/dashboard"
)
WATCHER_STATE_URL = os.environ.get(
    "WATCHER_STATE_URL", "http://kiwoom-watcher:8001/state"
)

VALID_ACTIONS = frozenset(
    {
        "HOLD", "TRIM", "TAKE_PROFIT", "CUT_LOSS", "ROTATE", "ACKNOWLEDGE",
        "ESCALATE", "MITIGATE", "TIER1", "TIER2", "REJECT",
        "WRAP_DONE", "BRIEF_DONE",
    }
)

# `api_failure_count` is a *consecutive* counter — the watcher resets it to 0
# on any healthy cycle — so this only catches a sustained outage, never an
# intermittent one. Keep it, but do not read it as a daily total.
API_FAILURE_WARN = 10

# Share of cycles a single failure category may burn before it is worth
# saying out loud. The cumulative `failures` map is what catches slow bleed:
# the 2026-07-29 DNS fault failed ~25% of reads and stacked 140 planner
# failures over two days while api_failure_count sat at 0 the whole time,
# because a success landed between nearly every pair of failures. Rates
# rather than counts, so a watcher up for a week isn't judged on totals.
FAILURE_RATE_WARN = 0.02
FAILURE_RATE_ALERT = 0.10

COLOR_INFO = 3447003
COLOR_SUCCESS = 3066993
COLOR_WARN = 16705372
COLOR_ERROR = 15158332


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _today_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def _run(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [MULTICA_BIN, *args], capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout, proc.stderr


def _fetch_state() -> dict | None:
    try:
        with urllib.request.urlopen(WATCHER_STATE_URL, timeout=10) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        _err(f"watcher /state unreachable: {exc}")
        return None


def _fetch_benchmark() -> dict | None:
    """Account return vs KOSPI, computed by the MCP server.

    The digest has no Kiwoom client — it reads HTTP and shells out to the
    multica CLI. The dashboard builder already holds a client and already
    fetches the account's daily asset series, so the comparison is computed
    there and read over the wire here, the same way /state is.

    A missing benchmark must never cost the digest: everything else it
    reports is unrelated.
    """

    try:
        with urllib.request.urlopen(DASHBOARD_URL, timeout=20) as resp:
            payload = json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        _err(f"dashboard unreachable (benchmark skipped): {exc}")
        return None
    data = payload.get("benchmark")
    return data if isinstance(data, dict) else None


def _benchmark_line(data: dict | None) -> str | None:
    """One line: did the account keep up with the index it trades in?"""

    if not data:
        return None
    if not data.get("available"):
        return f"📈 벤치마크: 비교 불가 — {data.get('reason', '사유 미상')}"
    acct = data.get("account_return_pct")
    idx = data.get("index_return_pct")
    alpha = data.get("alpha_pct")
    if acct is None or idx is None or alpha is None:
        return None

    # Grade the part the strategy controls. The headline alpha compares a
    # mostly-cash account to a fully invested index, so it goes red on every
    # rally whatever the picks did — measured 2026-09-24, exposure averaged
    # 8% and -4.9p of a -6.9p alpha was simply the idle cash. Alarming on
    # that is alarming on a position the operator chose.
    selection = data.get("selection_alpha_pct")
    graded = selection if selection is not None else alpha
    mark = "🔴" if graded <= -3 else ("🟡" if graded < 0 else "🟢")
    line = (
        f"{mark} 벤치마크 ({data.get('start_date')}~{data.get('end_date')}, "
        f"{data.get('compared_days')}거래일): "
        f"계좌 {acct:+.2f}% · KOSPI {idx:+.2f}% · **α {alpha:+.2f}%p**"
    )
    if selection is not None:
        line += (
            f"\n　└ 투자비중 {data.get('avg_exposure_pct'):.1f}% → "
            f"현금대기 {data.get('cash_drag_pct'):+.2f}%p · "
            f"**종목선택 {selection:+.2f}%p**"
        )
    # A single window is a window somebody picked, and on this account the
    # pick has swung alpha from +16.57p to -10.87p (2026-09-21, measured).
    # Print the trailing spans next to it so no one reads one as the answer.
    for w in data.get("windows") or []:
        line += (
            f"\n　└ 최근 {w.get('trading_days')}일: "
            f"계좌 {w.get('account_return_pct'):+.2f}% · "
            f"KOSPI {w.get('index_return_pct'):+.2f}% · "
            f"α {w.get('alpha_pct'):+.2f}%p"
        )
    excluded = data.get("excluded_days") or []
    if excluded:
        # Say it out loud: those days were dropped as suspected cash flows,
        # so the reader knows the window has holes rather than assuming not.
        line += f"\n　(입출금 추정 {len(excluded)}일 제외)"
    return line


def _slot_line(data: dict | None) -> str | None:
    """How often a qualifying candidate met a full portfolio today.

    `detect_tier2_new_candidates` returns `[]` at zero slots, so these
    ticks are invisible everywhere else — no dispatch, no issue, no log.
    Reporting the ratio makes "quiet day" and "no room" tell apart, which
    they did not for the three sessions of 2026-09-16..18.
    """

    if not isinstance(data, dict):
        return None
    qualified = data.get("qualified_ticks") or 0
    starved = data.get("starved_ticks") or 0
    if not qualified:
        return "🎯 후보: 오늘 게이트 통과 후보 없음"
    pct = starved / qualified * 100
    mark = "🔴" if pct >= 80 else ("🟡" if pct >= 40 else "🟢")
    line = (
        f"{mark} 후보: 게이트 통과 {qualified}틱 중 "
        f"**슬롯 0이라 미질의 {starved}틱** ({pct:.0f}%)"
    )
    # The rate alone cannot separate "held through a quiet tape" from "let a
    # better name go by" — 2026-09-21 ran 99.2% starved and the wrap could
    # not rule on a missed rotation. The best blocked score can.
    best = data.get("best_starved_score")
    if best is not None:
        name = data.get("best_starved_name") or "?"
        line += f"\n　└ 막힌 최고: **{name} score {best:g}**"
    return line


def _today_issues() -> list[dict]:
    if not PROJECT:
        return []
    # Default sort is "position" (manual kanban order), unrelated to recency,
    # and the API caps results at 100 regardless of --limit — with 400+ issues
    # in the project, an unsorted page can miss today's issues entirely (seen
    # 2026-07-24: pre-open BRIEF_DONE false-positive because SWO-614 wasn't in
    # the first 100 position-ordered issues). Sort by created_at desc so
    # "today" is always within the first page.
    rc, out, _err_ = _run(
        [
            "issue", "list", "--project", PROJECT, "--limit", "200",
            "--sort", "created_at", "--direction", "desc", "--output", "json",
        ]
    )
    if rc != 0:
        return []
    try:
        items = json.loads(out).get("issues", [])
    except (json.JSONDecodeError, AttributeError):
        return []
    today = _today_kst()
    out_issues = []
    for it in items:
        created = it.get("created_at") or ""
        try:
            cdate = datetime.fromisoformat(
                created.replace("Z", "+00:00")
            ).astimezone(KST).strftime("%Y-%m-%d")
        except ValueError:
            cdate = created[:10]
        if cdate == today:
            out_issues.append(it)
    return out_issues


def _issue_actions(issue_id: str) -> list[str]:
    rc, out, _e = _run(["issue", "comment", "list", issue_id, "--output", "json"])
    if rc != 0:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    comments = data if isinstance(data, list) else data.get("comments", [])
    tags = []
    for c in comments:
        if not isinstance(c, dict):
            continue
        m = ACTION_RE.search(c.get("content") or c.get("body") or "")
        if m:
            tags.append(m.group(1).upper())
    return tags


# A failed agent run is two different events wearing one status. The quota
# running out took the PM down for 3.5 hours on 2026-09-15 (11 runs, every
# one "You've hit your usage limit"). A provider capacity blip — "Selected
# model is at capacity" — fails one run and the next one succeeds a few
# minutes later. Grading both 🔴 raised a [점검 필요] handoff for the blip
# three times (09-17, 09-18, 09-22), each needing a hand to wave it off.
QUOTA_ERROR_MARKERS = ("usage limit",)
# Sustained failure is serious whatever the message says.
FAILED_RUN_ALERT_COUNT = 3


def _failed_run_errors(issue_id: str) -> list[str]:
    """Error text of every failed run on an issue ("" when none was given)."""

    rc, out, _e = _run(["issue", "runs", issue_id, "--output", "json"])
    if rc != 0:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    runs = data if isinstance(data, list) else data.get("runs", [])
    return [
        str(r.get("error") or "")
        for r in runs
        if isinstance(r, dict) and r.get("status") == "failed"
    ]


def grade_failed_runs(failed: dict[str, list[str]]) -> tuple[str | None, str | None]:
    """(alert, warning) for failed runs grouped by issue title.

    Red when the quota is gone or failures pile up; yellow for an isolated
    transient failure, which still gets reported so a trend cannot hide.
    """

    total = sum(len(errs) for errs in failed.values())
    if not total:
        return None, None
    quota = any(
        marker in err.lower()
        for errs in failed.values()
        for err in errs
        for marker in QUOTA_ERROR_MARKERS
    )
    titles = ", ".join(failed)
    if quota:
        return f"failed run {total}건 — **codex 사용 한도 소진**: {titles}", None
    if total >= FAILED_RUN_ALERT_COUNT:
        return f"failed run {total}건 (반복 실패): {titles}", None
    reasons = sorted({(e.split(".")[0] or "사유 없음")[:60] for errs in failed.values() for e in errs})
    return None, f"일시 실패 run {total}건 ({'; '.join(reasons)}): {titles}"


def _ensure_ops_issue(today: str, alerts: list[str], warns: list[str]) -> None:
    """Leave a `[점검 필요]` handoff marker in multica when anomalies exist.

    This is the cloud→local bridge: the digest can't make code-fix
    judgments, but it queues the operational anomaly so the operator's
    local Claude Code (via a SessionStart hook) surfaces it on next open.
    Unassigned on purpose — must not trigger a trading agent run. Idempotent
    per day: skips if a `[점검 필요] {today}` issue already exists.
    """

    if not PROJECT or not (alerts or warns):
        return
    title = f"[점검 필요] {today} 운영 이상"
    rc, out, _e = _run(
        [
            "issue", "list", "--project", PROJECT, "--limit", "200",
            "--sort", "created_at", "--direction", "desc", "--output", "json",
        ]
    )
    if rc == 0:
        try:
            for it in json.loads(out).get("issues", []):
                if it.get("title") == title and it.get("status") not in ("done", "cancelled"):
                    return  # already queued today
        except (json.JSONDecodeError, AttributeError):
            pass
    body_lines = ["digest가 운영 이상을 감지했습니다. 로컬에서 조사 후 처리하세요.", ""]
    if alerts:
        body_lines.append("## 🔴 경보")
        body_lines += [f"- {a}" for a in alerts]
    if warns:
        body_lines.append("## 🟡 주의")
        body_lines += [f"- {w}" for w in warns]
    priority = "high" if alerts else "medium"
    crc, _o, cerr = _run(
        [
            "issue", "create", "--project", PROJECT,
            "--title", title, "--description", "\n".join(body_lines),
            "--priority", priority, "--output", "json",
        ]
    )
    if crc != 0:
        _err(f"ops-issue create failed: {cerr.strip()}")


def _post_discord(embeds: list[dict]) -> None:
    if not WEBHOOK_URL:
        _err("DISCORD_WEBHOOK_URL not set — printing payload instead")
        print(json.dumps({"embeds": embeds}, ensure_ascii=False, indent=2))
        return
    payload = {
        "username": f"Kiwoom Ops {DAILY_LABEL}".strip(),
        "embeds": embeds[:10],
    }
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "kiwoom-ops-digest/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status not in (200, 204):
                _err(f"discord status {resp.status}")
    except urllib.error.HTTPError as exc:
        _err(f"discord HTTP error {exc.code}: {exc.read()[:200]!r}")
    except urllib.error.URLError as exc:
        _err(f"discord network error: {exc}")


def _failure_rate_lines(
    failures: dict, cycle_count: int
) -> list[tuple[str, str]]:
    """Grade each failure category by the share of cycles it burned.

    Returns ``(level, line)`` pairs, worst first. `last_detail` rides along
    because the count alone is what made the 2026-07-29 fault undiagnosable:
    the operator could see *that* something failed 140 times and never
    *which* read broke.
    """

    graded: list[tuple[float, str, str]] = []
    cycles = max(int(cycle_count or 0), 1)
    for name, bucket in sorted((failures or {}).items()):
        if not isinstance(bucket, dict):
            continue
        count = int(bucket.get("count") or 0)
        if count <= 0:
            continue
        rate = count / cycles
        if rate >= FAILURE_RATE_ALERT:
            level = "alert"
        elif rate >= FAILURE_RATE_WARN:
            level = "warn"
        else:
            continue
        detail = str(bucket.get("last_detail") or "").strip()
        line = f"{name} 실패 {count}건 / {cycles} 사이클 ({rate:.1%})"
        if detail:
            line += f" — 최근: `{detail[:160]}`"
        graded.append((rate, level, line))

    graded.sort(key=lambda row: -row[0])
    return [(level, line) for _, level, line in graded]


def main() -> int:
    today = _today_kst()
    state = _fetch_state()

    # Hard failure: no state at all. Still post so the absence is visible.
    if state is None:
        _post_discord([{
            "title": f"🔴 {today} Ops Digest — watcher 상태 조회 실패",
            "description": (
                f"`{WATCHER_STATE_URL}` 응답 없음. watcher pod 다운 또는 "
                "status server 장애 가능. 즉시 점검 필요.\n"
                "`kubectl -n tools get pods -l app=kiwoom-watcher`"
            ),
            "color": COLOR_ERROR,
        }])
        return 0

    alerts: list[str] = []  # 🔴
    warns: list[str] = []   # 🟡

    # --- watcher health ---
    regime = state.get("regime") or {}
    portfolio = state.get("portfolio") or {}
    last_error = state.get("last_error")
    api_fail = state.get("api_failure_count") or 0
    in_flight = state.get("in_flight") or []
    cycle = state.get("cycle_count") or 0
    last_tick = state.get("last_tick_at") or "-"
    execute = state.get("execute_orders")
    started_at = state.get("started_at") or ""

    if last_error:
        alerts.append(f"watcher last_error: `{last_error}`")

    # Stale tick: on a trading day, after market open, last_tick must be
    # today. A frozen watcher (cycle/last_tick stuck) is the single most
    # important failure to catch — without this the digest greenlights a
    # dead trading loop. Gated on KRX trading-day + post-open so off-hours
    # and holiday runs don't false-positive.
    now_kst = datetime.now(KST)
    trading_today = is_krx_trading_day(now_kst.date()) if is_krx_trading_day else True
    market_opened = now_kst.time() >= dtime(9, 0)
    if trading_today and market_opened and last_tick:
        try:
            tick_date = datetime.fromisoformat(
                last_tick.replace("Z", "+00:00")
            ).astimezone(KST).strftime("%Y-%m-%d")
            if tick_date != today:
                alerts.append(
                    f"watcher가 오늘 미가동 — last_tick {last_tick[:19]} "
                    f"(cycle {cycle} 정체). 루프 정지 의심, 즉시 점검"
                )
        except ValueError:
            pass

    # Unexpected restart: watcher should persist across the trading day, so
    # a start timestamp dated today (KST) means it was restarted.
    try:
        sdate = datetime.fromisoformat(
            started_at.replace("Z", "+00:00")
        ).astimezone(KST).strftime("%Y-%m-%d")
        if sdate == today:
            warns.append(f"watcher가 오늘 재시작됨 (started_at {started_at[:19]})")
    except ValueError:
        pass
    if api_fail > API_FAILURE_WARN:
        warns.append(
            f"연속 실패 {api_fail}회 진행 중 (api_failure_count, 임계 {API_FAILURE_WARN} 초과)"
        )
    if in_flight:
        warns.append(f"in_flight {len(in_flight)}건 미해소 (stuck dispatch 의심)")

    # Cumulative per-category failures, as a share of cycles run. This is the
    # only signal that sees an *intermittent* upstream fault — the consecutive
    # counter above cannot, by construction.
    failure_lines = _failure_rate_lines(state.get("failures") or {}, cycle)
    for level, line in failure_lines:
        (alerts if level == "alert" else warns).append(line)

    # --- multica issues today ---
    issues = _today_issues()
    action_counts: dict[str, int] = {}
    notag_issues: list[str] = []
    failed_issues: dict[str, list[str]] = {}
    pre_open_done = wrap_done = False

    for it in issues:
        title = it.get("title", "")
        tags = _issue_actions(it["id"])
        valid = [t for t in tags if t in VALID_ACTIONS]
        for t in valid:
            action_counts[t] = action_counts.get(t, 0) + 1
        if "BRIEF_DONE" in valid:
            pre_open_done = True
        if "WRAP_DONE" in valid:
            wrap_done = True
        # NO_TAG concern: a candidate/PM issue with comments but no valid ACTION
        non_template = [t for t in tags if t != "XXX"]
        if tags and not valid and not non_template:
            pass  # only the trigger template — agent hasn't answered yet
        errors = _failed_run_errors(it["id"])
        if errors:
            failed_issues[title[:40]] = errors

    failed_alert, failed_warn = grade_failed_runs(failed_issues)
    if failed_alert:
        alerts.append(failed_alert)
    if failed_warn:
        warns.append(failed_warn)
    if issues and not pre_open_done:
        warns.append("pre-open BRIEF_DONE 미확인")
    if issues and not wrap_done:
        warns.append("wrap WRAP_DONE 미확인")

    # --- compose ---
    if alerts:
        head_color, head_icon = COLOR_ERROR, "🔴"
    elif warns:
        head_color, head_icon = COLOR_WARN, "🟡"
    else:
        head_color, head_icon = COLOR_SUCCESS, "🟢"

    # A degraded index read zeroes every figure below and still sets
    # extreme_risk_off (the entry veto). Printed bare that reads as a crash,
    # which is how the 2026-07-29/30 DNS outage got diagnosed as a market
    # event. Say which one it is.
    regime_line = (
        f"{regime.get('regime', '?')}"
        f"{' · extreme_risk_off' if regime.get('extreme_risk_off') else ''}"
        f" · avg {regime.get('average_change_pct', '?')}%"
        f" · breadth {regime.get('breadth_score', '?')}"
    )
    # The average dilutes the market we actually trade — show that one too,
    # or a KOSPI-only selloff hides behind a flat KOSDAQ (2026-08-06).
    primary = regime.get("primary_market")
    if primary:
        regime_line += (
            f"\n└ 거래시장 {primary.upper()} "
            f"{regime.get('primary_change_pct', '?')}% · "
            f"breadth {regime.get('primary_breadth', '?')}"
        )
    if not regime.get("market_data_complete", True):
        regime_line += "\n⚠️ 지수 조회 불완전 — 위 수치는 시장이 아니라 조회 실패를 반영"
    action_line = ", ".join(f"{k}×{v}" for k, v in sorted(action_counts.items())) or "없음"

    summary = (
        f"**모드**: {state.get('mode', '?')} · execute_orders={execute}\n"
        f"**사이클**: {cycle} · last_tick {last_tick[:19]}\n"
        f"**레짐**: {regime_line}\n"
        f"**포트폴리오**: 보유 {portfolio.get('holding_count', '?')} · "
        f"미체결 {portfolio.get('open_order_count', '?')} · "
        f"후보 {portfolio.get('candidate_count', '?')}\n"
        f"**오늘 ACTION**: {action_line}\n"
        f"**api_failure**: {api_fail}"
    )

    # Opportunity cost, which nothing reported until 2026-09-21. Over
    # 2026-08-03..09-18 the account returned -0.03% against KOSPI's +10.84%
    # and the gap had to be found by hand.
    bench_line = _benchmark_line(_fetch_benchmark())
    if bench_line:
        summary += f"\n{bench_line}"

    slot_line = _slot_line(state.get("candidate_slots"))
    if slot_line:
        summary += f"\n{slot_line}"

    embeds = [{
        "title": f"{head_icon} {today} Ops Digest",
        "description": summary,
        "color": head_color,
    }]

    if alerts or warns:
        lines = []
        if alerts:
            lines.append("**🔴 경보**\n" + "\n".join(f"- {a}" for a in alerts))
        if warns:
            lines.append("**🟡 주의**\n" + "\n".join(f"- {w}" for w in warns))
        embeds.append({
            "title": "점검 항목",
            "description": "\n\n".join(lines)[:3900],
            "color": head_color,
        })
    else:
        embeds[0]["description"] += "\n\n✅ 이상 없음"

    # Handoff marker for local Claude Code (SessionStart hook surfaces it).
    try:
        _ensure_ops_issue(today, alerts, warns)
    except Exception as exc:  # never let the marker break the digest
        _err(f"ops-issue error: {exc}")

    _post_discord(embeds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
