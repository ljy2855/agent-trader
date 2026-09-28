"""Builders for the dashboard's agent endpoints.

``/api/agent_overview`` returns the live operating picture in one payload:

* **Watcher status** — live state pulled from the watcher pod's status
  HTTP server (``$KIWOOM_WATCHER_STATUS_URL/state``). Includes cycle
  counter, regime label, in-flight Tier-2 dispatches, recent errors, and
  the watcher's own effective config.
* **Autopilot status** — live state pulled from the Multica CLI
  (``multica autopilot list / get`` + ``multica issue list``). Includes
  next/last fire times, today's brief and wrap issues with run status.

``/api/agent_timeline`` returns the decision history — see
:func:`build_agent_timeline`. It is a separate endpoint because its Multica
comment fan-out costs seconds, and the overview above should not wait on it.

Every layer is fail-soft: if a sub-fetch errors, that section reports
``{"status": "error", "error": "..."}`` while the other layers still
render. The UI degrades gracefully rather than blanking out.

.. note::
   This module used to also emit a static ``topology`` layer built from a
   freshly constructed ``WatcherConfig()`` — i.e. **code defaults**. The live
   watcher runs entirely different args, so the dashboard was confidently
   printing wrong thresholds (-3% stop loss when live was -4%, score 14 when
   live was 8, and five more). Live config now comes from the watcher's own
   ``/state`` payload; there are deliberately no hardcoded thresholds here.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from .services import krx_calendar
from .services.strategy import BELOW_MA_MAX_DIP_PCT
from .services.agent_timeline import build_rows, normalize_stock_code

KST = timezone(timedelta(hours=9))


# ---------------------------------------------------------------------------
# Live watcher status (HTTP fetch)
# ---------------------------------------------------------------------------


async def fetch_watcher_status(
    *,
    base_url: str | None = None,
    timeout_seconds: float = 5.0,
    recent_limit: int = 50,
) -> dict[str, Any]:
    """Pull `/state` and `/recent` from the watcher pod's status server."""

    base_url = base_url or os.environ.get("KIWOOM_WATCHER_STATUS_URL", "")
    if not base_url:
        return {
            "status": "disabled",
            "error": "KIWOOM_WATCHER_STATUS_URL 미설정",
        }
    base_url = base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            state_resp, recent_resp = await asyncio.gather(
                client.get(f"{base_url}/state"),
                client.get(f"{base_url}/recent", params={"limit": recent_limit}),
            )
        state_resp.raise_for_status()
        recent_resp.raise_for_status()
        recent_payload = recent_resp.json() or {}
        return {
            "status": "ok",
            "state": state_resp.json(),
            "recent": recent_payload.get("items", []),
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": f"watcher status fetch 실패: {exc}",
        }


async def fetch_watcher_ledger(
    *,
    limit: int = 50,
    trading_day: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    """Pull the order-intent ledger view from the watcher's `/ledger`."""

    base_url = base_url or os.environ.get("KIWOOM_WATCHER_STATUS_URL", "")
    if not base_url:
        return {"available": False, "error": "KIWOOM_WATCHER_STATUS_URL 미설정"}
    params: dict[str, Any] = {"limit": limit}
    if trading_day:
        params["trading_day"] = trading_day
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.get(f"{base_url.rstrip('/')}/ledger", params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"available": False, "error": f"watcher ledger fetch 실패: {exc}"}


# ---------------------------------------------------------------------------
# Live autopilot + brief issue status (multica CLI fetch)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _MulticaContext:
    binary: str
    project: str


def _multica_ctx() -> _MulticaContext | None:
    binary = os.environ.get("MULTICA_BIN", "/usr/local/bin/multica")
    project = os.environ.get("MULTICA_PROJECT", "")
    if not project:
        return None
    return _MulticaContext(binary=binary, project=project)


def _run_cli(ctx: _MulticaContext, args: list[str], *, timeout: float = 8.0) -> Any:
    proc = subprocess.run(
        [ctx.binary, *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"exit {proc.returncode}")
    if not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON 파싱 실패: {exc}") from exc


def _fetch_autopilots(ctx: _MulticaContext) -> list[dict[str, Any]]:
    data = _run_cli(ctx, ["autopilot", "list", "--output", "json"])
    items = []
    if isinstance(data, dict):
        items = data.get("autopilots") or []
    elif isinstance(data, list):
        items = data
    out = []
    for ap in items:
        if not isinstance(ap, dict):
            continue
        if "kiwoom" not in (ap.get("title") or "").lower():
            # filter to our autopilots only
            continue
        try:
            detail = _run_cli(
                ctx, ["autopilot", "get", ap["id"], "--output", "json"]
            ) or {}
        except Exception as exc:
            detail = {"_error": str(exc)}
        triggers = (
            detail.get("triggers")
            if isinstance(detail, dict) and isinstance(detail.get("triggers"), list)
            else []
        )
        out.append(
            {
                "id": ap.get("id"),
                "title": ap.get("title"),
                "status": ap.get("status"),
                "execution_mode": ap.get("execution_mode"),
                "issue_title_template": ap.get("issue_title_template"),
                "last_run_at": ap.get("last_run_at"),
                "triggers": [
                    {
                        "label": t.get("label"),
                        "cron": t.get("cron_expression"),
                        "timezone": t.get("timezone"),
                        "enabled": t.get("enabled"),
                        "next_run_at": t.get("next_run_at"),
                        "last_fired_at": t.get("last_fired_at"),
                    }
                    for t in triggers
                    if isinstance(t, dict)
                ],
                "error": detail.get("_error") if isinstance(detail, dict) else None,
            }
        )
    return out


async def fetch_autopilot_status() -> dict[str, Any]:
    ctx = _multica_ctx()
    if ctx is None:
        return {"status": "disabled", "error": "MULTICA_PROJECT 미설정"}
    try:
        autopilots = await asyncio.to_thread(_fetch_autopilots, ctx)
        # Today's issue list used to be fetched here too, for a parent/child
        # hierarchy card. /api/agent_timeline supersedes that view and does its
        # own (date-scoped) listing, so this endpoint no longer pays for it.
        return {
            "status": "ok",
            "autopilots": autopilots,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Agent decision timeline (multica threads + watcher outcomes)
# ---------------------------------------------------------------------------

# `[한국전력] (015760) 2026-08-13 후보 평가` / `[한온시스템] (A018880) … 보유 분석`
# — the code prefix differs by source API, so normalize before using it.
_ISSUE_STOCK_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\s*\((?P<code>[A-Za-z]?\d+)\)")

# Bounded fan-out: one `issue comment list` costs ~1.2s, and a trading day has
# roughly 5-15 issues. Five at a time keeps a full rebuild around 2-3s without
# spawning a dozen concurrent CLI subprocesses inside an HTTP handler.
_TIMELINE_CONCURRENCY = 5
_TIMELINE_BUDGET_SECONDS = 25.0

# Past days are append-only once the session ends, so they can be cached hard.
# Today's threads keep growing, so they get a short TTL.
_TIMELINE_TTL_TODAY = 30.0
_TIMELINE_TTL_PAST = 600.0

_timeline_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


def _kst_date(raw: Any) -> str | None:
    if not raw:
        return None
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(KST).strftime("%Y-%m-%d")


def _issue_summary(issue: dict[str, Any]) -> dict[str, Any]:
    title = issue.get("title") or ""
    summary = {
        "id": issue.get("id"),
        "identifier": issue.get("identifier"),
        "title": title,
        "status": issue.get("status"),
        "assignee_type": issue.get("assignee_type"),
        "stock_code": None,
        "stock_name": None,
    }
    match = _ISSUE_STOCK_RE.match(title)
    if match:
        summary["stock_code"] = normalize_stock_code(match.group("code"))
        summary["stock_name"] = match.group("name")
    return summary


def _fetch_issues_for_date(ctx: _MulticaContext, date: str) -> list[dict[str, Any]]:
    """Return the day's issues, newest first.

    Matches on either the KST date of ``created_at`` or the date embedded in the
    title — every watcher-created title carries one (see the ``ensure_*_issue``
    helpers in ``multica_dispatch``), and the two disagree across the UTC/KST
    boundary.
    """

    data = _run_cli(
        ctx,
        [
            "issue", "list",
            "--project", ctx.project,
            "--limit", "200",
            "--sort", "created_at",
            "--direction", "desc",
            "--output", "json",
        ],
        timeout=10.0,
    )
    items = data if isinstance(data, list) else (data or {}).get("issues", [])
    out: list[dict[str, Any]] = []
    for issue in items:
        if not isinstance(issue, dict):
            continue
        title = issue.get("title") or ""
        created = issue.get("created_at") or issue.get("createdAt")
        if date not in title and _kst_date(created) != date:
            continue
        out.append(issue)
    return out


def _fetch_comments(ctx: _MulticaContext, issue: dict[str, Any]) -> list[dict[str, Any]]:
    key = issue.get("identifier") or issue.get("id")
    if not key:
        return []
    data = _run_cli(ctx, ["issue", "comment", "list", str(key), "--output", "json"])
    if isinstance(data, list):
        return data
    return (data or {}).get("comments", []) or []


async def build_agent_timeline(
    *,
    date: str | None = None,
    limit: int = 60,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Build the agent decision timeline for one KST trading day.

    Merges two sources that no shared id connects:

    * **Multica threads** carry the reasoning — the watcher's dispatch payload,
      the agent's prose, the ACTION tag, squad delegation replies.
    * **The watcher's** ``/recent`` **ring buffer** carries what actually happened
      to the order, and is the *only* source for Tier-1 rules, which execute in
      code without ever touching an agent.

    See ``services/agent_timeline`` for the segmentation and join rules. When the
    watcher has restarted its ring buffer is empty and every row reports
    ``outcome_source: "unavailable"`` — the UI must say "not verified", never "no
    order was placed".
    """

    date = date or datetime.now(KST).strftime("%Y-%m-%d")
    today = datetime.now(KST).strftime("%Y-%m-%d")
    ctx = _multica_ctx()

    cache_key = (ctx.project if ctx else "-", date)
    if use_cache:
        cached = _timeline_cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]

    watcher = await fetch_watcher_status(recent_limit=200)
    recent_items = watcher.get("recent") or [] if watcher.get("status") == "ok" else []

    source: dict[str, Any] = {
        "watcher": watcher.get("status", "error"),
        "multica": "ok",
        "outcome_join": "ok" if recent_items else "unavailable",
        "note": None,
    }
    if not recent_items and watcher.get("status") == "ok":
        # The ring buffer is process-lifetime, so this is the normal state right
        # after a rollout — not an error, but reasoning shows without outcomes.
        source["note"] = (
            "watcher 재시작 이후 트리거 기록이 비어 있어 주문 결과를 대사할 수 없습니다."
        )
    elif watcher.get("status") != "ok":
        source["note"] = watcher.get("error")

    threads: list[tuple[dict[str, Any] | None, list[dict[str, Any]]]] = []
    if ctx is None:
        source["multica"] = "disabled"
        source["note"] = "MULTICA_PROJECT 미설정"
    else:
        deadline = time.monotonic() + _TIMELINE_BUDGET_SECONDS
        try:
            issues = await asyncio.to_thread(_fetch_issues_for_date, ctx, date)
        except Exception as exc:
            issues = []
            source["multica"] = "error"
            source["note"] = f"issue list 실패: {exc}"

        semaphore = asyncio.Semaphore(_TIMELINE_CONCURRENCY)
        truncated = False

        async def load(issue: dict[str, Any]) -> None:
            nonlocal truncated
            async with semaphore:
                if time.monotonic() > deadline:
                    truncated = True
                    return
                try:
                    comments = await asyncio.to_thread(_fetch_comments, ctx, issue)
                except Exception:
                    # One unreadable thread must not blank the whole timeline.
                    truncated = True
                    return
                threads.append((_issue_summary(issue), comments))

        if issues:
            await asyncio.gather(*(load(issue) for issue in issues))
        if truncated:
            source["multica"] = "partial"
            source["note"] = "일부 스레드를 시간 내 읽지 못했습니다 (부분 결과)."

    rows = build_rows(threads, recent_items, limit=max(0, min(limit, 200)))

    payload = {
        "generated_at": datetime.now(KST).isoformat(),
        "date": date,
        "source": source,
        "rows": rows,
    }
    ttl = _TIMELINE_TTL_TODAY if date == today else _TIMELINE_TTL_PAST
    _timeline_cache[cache_key] = (time.monotonic() + ttl, payload)
    return payload


# ---------------------------------------------------------------------------
# Composite payload
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Market session (local calendar — no network)
# ---------------------------------------------------------------------------

_SESSION_LABELS = {
    "open": "장중",
    "pre_open": "개장 전",
    "after_close": "장 마감",
    "holiday": "휴장",
    "uncertain": "캘린더 불확실",
}


def market_session_overview(now: datetime | None = None) -> dict[str, Any]:
    """Where the market is right now, in words a person reads at a glance.

    The watcher's own counters cannot say this: outside the session it
    sleeps without ticking, so every live field sits at zero — on the
    Chuseok morning of 2026-09-24 the tab showed cycle 0 and a dash in
    every box, which reads the same as a dead process. Saying "휴장, next
    open 09-28 09:00" beside those zeros is what makes them mean something.

    Computed from the same calendar the watcher gates on, locally, so it
    never depends on the watcher being reachable.
    """

    status = krx_calendar.krx_regular_session_status(now)
    day = status.day_status
    if status.is_open:
        phase = "open"
    elif status.uncertain:
        phase = "uncertain"
    elif day.state == krx_calendar.DAY_CLOSED:
        phase = "holiday"
    elif status.opens_at and status.observed_at.time() < status.opens_at:
        phase = "pre_open"
    else:
        phase = "after_close"

    nxt = krx_calendar.next_regular_session_open(now)
    return {
        "phase": phase,
        "label": _SESSION_LABELS[phase],
        # Holiday name ("추석", "주말") or the calendar's own reason.
        "reason": day.reason if phase in ("holiday", "uncertain") else None,
        "is_open": status.is_open,
        "opens_at": status.opens_at.strftime("%H:%M") if status.opens_at else None,
        "closes_at": status.closes_at.strftime("%H:%M") if status.closes_at else None,
        "next_open": nxt[0].isoformat() if nxt else None,
        "next_open_uncertain": bool(nxt and nxt[1]),
    }


async def build_agent_overview() -> dict[str, Any]:
    watcher, autopilot = await asyncio.gather(
        fetch_watcher_status(),
        fetch_autopilot_status(),
    )
    return {
        "generated_at": datetime.now(KST).isoformat(),
        "session": market_session_overview(),
        # Strategy constants that are code, not config, so the watcher does
        # not report them. Served from the same image the watcher runs, so
        # the dashboard never carries a second copy of the number.
        "strategy_constants": {
            "below_ma_max_dip_pct": BELOW_MA_MAX_DIP_PCT,
        },
        "watcher": watcher,
        "autopilot": autopilot,
    }


__all__ = [
    "market_session_overview",
    "build_agent_overview",
    "build_agent_timeline",
    "fetch_autopilot_status",
    "fetch_watcher_status",
]
