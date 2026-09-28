"""Reconstruct the agent decision timeline from Multica threads + watcher state.

The watcher does not keep *why* an agent decided anything. ``ActionResponse.output``
— the actual reasoning prose — is a local variable in ``watcher._await_and_apply``
and only its ``len()`` ever reaches a log line. The status registry's widest text
field is ``TriggerLogEntry.detail`` (a ~300 char summary). So the only durable
record of agent reasoning is **Multica itself**, in the issue comment threads the
watcher posts to.

This module turns those threads back into structured decisions.

Two things make that non-trivial, and both were confirmed against live data:

1. **A thread is not a decision.** ``[PM 코멘트] <date> 사이클 점검`` accumulates an
   entire trading day of ``periodic_review`` / ``regime_flip`` / ``extreme_risk_off``
   dispatches as comments on one issue (SWO-690: 32 comments, 15 dispatches).
   Per-stock issues happen to hold exactly one. The unit is therefore a *segment*:
   one watcher dispatch comment plus the agent comments that follow it before the
   next dispatch.

2. **Tier 1 never appears here at all.** Stop-loss, take-profit, max-position
   overflow and stale-order cancels are executed directly by code with no agent
   round trip, so they have no issue and no comment. They come from the watcher's
   ``/recent`` ring buffer instead and are merged in by :func:`merge_tier1`.

Everything here is a pure function over already-fetched data — no I/O, no CLI, no
HTTP — so the whole thing is testable without a network.

.. warning::
   :func:`parse_dispatch_comment` is a parser coupled to a *producer's* string
   format: ``IntradayWatcher._build_trigger_comment`` in ``services/watcher.py``.
   If that template changes, this must change with it. The parser is written to
   degrade rather than raise — an unrecognised comment is simply not a dispatch,
   and a field it cannot read becomes ``None`` while the raw text is preserved.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence

from .multica_dispatch import extract_action_tag

KST = timezone(timedelta(hours=9))

# `**[09:01:03 KST] [트리거: new_candidate]**` — written by
# watcher._build_trigger_comment(). The header carries a wall-clock time but no
# date; the date comes from the comment's created_at (see _combine_date_time).
_HEADER_RE = re.compile(
    r"^\*\*\[(?P<time>\d{2}:\d{2}:\d{2})\s*KST\]\s*\[트리거:\s*(?P<trigger>[a-z0-9_]+)\]\*\*",
    re.MULTILINE,
)

# `종목: 삼성전자 (005930)` — present only for stock-scoped triggers. Global
# triggers (periodic_review, regime_flip, api_failures…) omit the line entirely.
_TARGET_RE = re.compile(r"^종목:\s*(?P<name>.+?)\s*\((?P<code>[A-Za-z]?\d+)\)\s*$", re.MULTILINE)

_REASON_RE = re.compile(r"^사유:\s*(?P<reason>.+?)\s*$", re.MULTILINE)

# `[위임] 10:29 risk_off 전환 리스크 점검` — a squad leader delegating a boundary
# case to a member. This is the *real* delegation mechanism (a child issue with
# parent_issue_id), as opposed to an agent threading a reply onto a dispatch
# comment. The leading HH:MM is optional; some titles name a stock instead.
_DELEGATION_RE = re.compile(r"^\[위임\]\s*(?:(?P<hour>\d{2}):(?P<minute>\d{2})\s*)?(?P<subject>.*)$")

# The snapshot block is a BARE ``` fence — watcher._build_trigger_comment writes
# f"```\n{snapshot_json}\n```" with no info string. Do not key on ```json.
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*\n(?P<body>.*?)\n?```", re.DOTALL)

# Follow-up notes the watcher posts into the same thread when a dispatch times out
# or its ACTION is discarded as stale. They are authored as `member` exactly like a
# dispatch, so they are excluded by prefix. In practice they also lack the header
# above, but the check is anchored at the start of the body rather than searched
# anywhere in it — a legitimate `사유:` string must never be able to trip it.
_WATCHER_NOTE_PREFIX = "**[watcher]**"

# How far apart a Multica dispatch and a watcher /recent entry may be and still be
# considered the same decision. The two clocks are the same process, so the gap is
# just "time to build and POST the comment" — a couple of seconds in practice.
# 90s is deliberately loose; the ambiguity guard below is what keeps it honest.
JOIN_TOLERANCE_SECONDS = 90.0

# If the two best candidates are this close to each other, picking "the nearest"
# is arbitrary. Attach nothing rather than guess an order outcome onto a decision.
JOIN_AMBIGUITY_SECONDS = 5.0


# ---------------------------------------------------------------------------
# Value types
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class DispatchInfo:
    """The watcher's side of one decision: what it saw and what it asked."""

    trigger_type: str
    dispatched_at: datetime
    stock_code: str | None = None
    stock_name: str | None = None
    reason: str | None = None
    snapshot: dict[str, Any] | None = None
    # Preserved when the fenced block exists but is not valid JSON, so the UI can
    # still show *something* rather than silently dropping the evidence.
    snapshot_raw: str | None = None

    @property
    def scope(self) -> str:
        return "stock" if self.stock_code else "global"


@dataclass(slots=True)
class AgentResponse:
    """One agent comment answering a dispatch.

    An agent may answer the same dispatch more than once — Multica re-runs a task
    when the first run ends without a usable ACTION tag, and each run posts its
    own comment. The last one is the answer; the earlier ones are working notes.
    """

    text: str
    created_at: datetime | None = None
    action: str | None = None
    # Whether the comment was posted as a reply to the dispatch comment rather
    # than at top level. Purely descriptive: in a thread carrying a whole day of
    # dispatches, threading is simply how an agent says *which* one it is
    # answering. It does NOT mean the reply came from a delegated squad member —
    # real delegation is a separate `[위임] …` child issue, not a comment.
    threaded: bool = False
    author_id: str | None = None


@dataclass(slots=True)
class Segment:
    """One dispatch and every agent response that belongs to it."""

    dispatch: DispatchInfo
    responses: list[AgentResponse] = field(default_factory=list)

    @property
    def final_action(self) -> str | None:
        """The last real ACTION in the segment.

        Later comments supersede earlier ones — a re-run's verdict lands after
        the first run's working note, and it is the one the watcher applied.
        ``NO_TAG`` is not an action.
        """

        for response in reversed(self.responses):
            if response.action and response.action != "NO_TAG":
                return response.action
        return None

    @property
    def final_response(self) -> AgentResponse | None:
        """The response that carried the applied ACTION, else the last one."""

        for response in reversed(self.responses):
            if response.action and response.action != "NO_TAG":
                return response
        return self.responses[-1] if self.responses else None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def normalize_stock_code(raw: Any) -> str | None:
    """Normalize a Kiwoom stock code to bare 6-digit form.

    The two APIs disagree and both end up in our data: the account API returns
    ``A018880`` (so holding-analysis issue titles carry the prefix) while the
    market API returns ``018880`` (candidate issues). Joining Multica rows to
    watcher rows without normalizing silently drops every holding trigger.
    """

    if raw is None:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return None
    return digits[-6:].zfill(6)


def _parse_iso(value: Any) -> datetime | None:
    """Parse an ISO timestamp into a KST-aware datetime, or None."""

    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        # Multica timestamps are UTC; a naive one is still UTC, not local.
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(KST)


def _combine_date_time(header_time: str, posted_at: datetime | None) -> datetime | None:
    """Rebuild a full timestamp from the header's clock time + the post date.

    The header only has ``HH:MM:SS``. The comment's ``created_at`` supplies the
    date. They are normally seconds apart, but a dispatch detected at 23:59:58 can
    be posted at 00:00:01 the next day — so snap to whichever adjacent day puts the
    two closest together instead of assuming they share a date.
    """

    if posted_at is None:
        return None
    try:
        hour, minute, second = (int(part) for part in header_time.split(":"))
        candidate = posted_at.replace(
            hour=hour, minute=minute, second=second, microsecond=0
        )
    except ValueError:
        return None
    best = candidate
    for shift in (-1, 1):
        shifted = candidate + timedelta(days=shift)
        if abs(shifted - posted_at) < abs(best - posted_at):
            best = shifted
    return best


def _extract_snapshot(content: str) -> tuple[dict[str, Any] | None, str | None]:
    match = _FENCE_RE.search(content)
    if not match:
        return None, None
    body = match.group("body").strip()
    if not body:
        return None, None
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return None, body
    if isinstance(parsed, dict):
        return parsed, None
    # A non-object payload is still evidence; keep it readable rather than lose it.
    return None, body


def parse_dispatch_comment(content: str, created_at: Any = None) -> DispatchInfo | None:
    """Parse a watcher dispatch comment, or return None if it isn't one.

    Never raises. See the module warning about producer coupling —
    ``watcher._build_trigger_comment`` is the source format.
    """

    if not content:
        return None
    if content.lstrip().startswith(_WATCHER_NOTE_PREFIX):
        return None
    header = _HEADER_RE.search(content)
    if not header:
        return None

    posted_at = _parse_iso(created_at)
    dispatched_at = _combine_date_time(header.group("time"), posted_at) or posted_at
    if dispatched_at is None:
        return None

    info = DispatchInfo(
        trigger_type=header.group("trigger"),
        dispatched_at=dispatched_at,
    )

    target = _TARGET_RE.search(content)
    if target:
        info.stock_code = normalize_stock_code(target.group("code"))
        name = target.group("name").strip()
        # The producer falls back to the code when it has no name; don't echo
        # the code back as if it were a company name.
        info.stock_name = name or None
        if info.stock_name and normalize_stock_code(info.stock_name) == info.stock_code:
            info.stock_name = None

    reason = _REASON_RE.search(content)
    if reason:
        info.reason = reason.group("reason").strip() or None

    info.snapshot, info.snapshot_raw = _extract_snapshot(content)
    return info


def _clean_action(text: str) -> str | None:
    action = extract_action_tag(text or "")
    if not action or action == "NO_TAG":
        return None
    # extract_action_tag marks out-of-vocabulary tags with a trailing "?".
    return action


def segment_thread(comments: Sequence[dict[str, Any]]) -> list[Segment]:
    """Split one issue's comments into (dispatch → responses) segments.

    Comments are processed oldest-first regardless of the order they arrive in.
    ``system`` comments (Multica's own squad notifications) are ignored, and any
    agent comment appearing before the first dispatch is dropped — it answers a
    dispatch we cannot see.
    """

    ordered = sorted(
        (c for c in comments if isinstance(c, dict)),
        key=lambda c: str(c.get("created_at") or c.get("createdAt") or ""),
    )

    segments: list[Segment] = []
    for comment in ordered:
        author_type = comment.get("author_type") or comment.get("authorType")
        if author_type == "system":
            continue
        content = comment.get("content") or comment.get("body") or ""
        created_at = comment.get("created_at") or comment.get("createdAt")

        if author_type == "member":
            dispatch = parse_dispatch_comment(content, created_at)
            if dispatch is not None:
                segments.append(Segment(dispatch=dispatch))
            # A member comment that isn't a dispatch (timeout/stale notice) is
            # context, not a new decision — skip it without closing the segment.
            continue

        if author_type != "agent" or not segments:
            continue

        segments[-1].responses.append(
            AgentResponse(
                text=content.strip(),
                created_at=_parse_iso(created_at),
                action=_clean_action(content),
                threaded=bool(comment.get("parent_id") or comment.get("parentId")),
                author_id=comment.get("author_id") or comment.get("authorId"),
            )
        )
    return segments


# ---------------------------------------------------------------------------
# Joining Multica decisions to watcher outcomes
# ---------------------------------------------------------------------------


def _recent_time(item: dict[str, Any]) -> datetime | None:
    return _parse_iso(item.get("detected_at"))


def _outcome_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "outcome": item.get("outcome"),
        "action": item.get("action"),
        "detail": item.get("detail"),
        "completed_at": item.get("completed_at"),
        "dispatched": item.get("dispatched"),
    }


def join_outcome(
    dispatch: DispatchInfo,
    recent_items: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    """Find the watcher ``/recent`` entry describing this dispatch's outcome.

    There is no shared id to join on: ``mark_dispatched`` writes ``issue=<id>``
    into ``detail`` but ``mark_outcome`` overwrites the same field, so a completed
    trigger carries no link back to its issue. We therefore match on
    (trigger_type, normalized stock code, time proximity).

    Returns ``(outcome_or_None, source)`` where source is one of ``watcher``,
    ``unmatched`` or ``ambiguous``. Callers must render the last two as *not
    verified* — never as "no order was placed", which is a different claim.
    """

    scored: list[tuple[float, dict[str, Any]]] = []
    for item in recent_items:
        if not isinstance(item, dict):
            continue
        if item.get("trigger_type") != dispatch.trigger_type:
            continue
        if normalize_stock_code(item.get("stock_code")) != dispatch.stock_code:
            continue
        detected = _recent_time(item)
        if detected is None:
            continue
        delta = abs((detected - dispatch.dispatched_at).total_seconds())
        if delta <= JOIN_TOLERANCE_SECONDS:
            scored.append((delta, item))

    if not scored:
        return None, "unmatched"
    scored.sort(key=lambda pair: pair[0])
    if len(scored) > 1 and (scored[1][0] - scored[0][0]) <= JOIN_AMBIGUITY_SECONDS:
        return None, "ambiguous"
    return _outcome_payload(scored[0][1]), "watcher"


def _segment_row(
    segment: Segment,
    issue: dict[str, Any] | None,
    recent_items: Sequence[dict[str, Any]],
    *,
    join_enabled: bool,
) -> dict[str, Any]:
    dispatch = segment.dispatch
    if join_enabled:
        outcome, source = join_outcome(dispatch, recent_items)
    else:
        # The watcher restarted (or is unreachable), so /recent cannot describe
        # anything. Say so once at the payload level instead of marking every row
        # "unmatched", which would read like a reconciliation failure.
        outcome, source = None, "unavailable"

    return {
        "kind": "tier2",
        "trigger_type": dispatch.trigger_type,
        "tier": 2,
        "scope": dispatch.scope,
        "dispatched_at": dispatch.dispatched_at.isoformat(),
        "stock_code": dispatch.stock_code,
        "stock_name": dispatch.stock_name,
        "reason": dispatch.reason,
        "snapshot": dispatch.snapshot,
        "snapshot_raw": dispatch.snapshot_raw,
        "issue": _issue_ref(issue),
        "responses": [
            {
                "text": response.text,
                "created_at": response.created_at.isoformat() if response.created_at else None,
                "action": response.action,
                "threaded": response.threaded,
            }
            for response in segment.responses
        ],
        "final_action": segment.final_action,
        "outcome": outcome,
        "outcome_source": source,
    }


def _tier1_row(item: dict[str, Any]) -> dict[str, Any] | None:
    detected = _recent_time(item)
    if detected is None:
        return None
    return {
        "kind": "tier1",
        "trigger_type": item.get("trigger_type"),
        "tier": 1,
        "scope": item.get("scope") or ("stock" if item.get("stock_code") else "global"),
        "dispatched_at": detected.isoformat(),
        "stock_code": normalize_stock_code(item.get("stock_code")),
        "stock_name": item.get("stock_name"),
        "reason": item.get("reason"),
        "snapshot": None,
        "snapshot_raw": None,
        "issue": None,
        # Tier 1 is executed by code with no agent round trip, so there is no
        # reasoning to show. That is the design, not missing data.
        "responses": [],
        "final_action": item.get("action"),
        "outcome": _outcome_payload(item),
        "outcome_source": "watcher",
    }


def delegation_row(
    issue: dict[str, Any],
    comments: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    """Build a row for a squad delegation child issue, or None if not one.

    Squad leaders delegate boundary cases (regime flips, scores on the Tier-2
    edge) to a member as a **child issue** — this is the cross-check that stands
    in for peer review on squad-routed triggers. Without this the second
    opinion is invisible, because the delegated reasoning never touches the
    parent thread.
    """

    title = issue.get("title") or ""
    match = _DELEGATION_RE.match(title)
    if not match:
        return None

    posted = None
    responses: list[AgentResponse] = []
    for comment in sorted(
        (c for c in comments if isinstance(c, dict)),
        key=lambda c: str(c.get("created_at") or c.get("createdAt") or ""),
    ):
        if (comment.get("author_type") or comment.get("authorType")) != "agent":
            continue
        created = _parse_iso(comment.get("created_at") or comment.get("createdAt"))
        posted = posted or created
        responses.append(
            AgentResponse(
                text=(comment.get("content") or comment.get("body") or "").strip(),
                created_at=created,
                action=_clean_action(comment.get("content") or comment.get("body") or ""),
                threaded=bool(comment.get("parent_id") or comment.get("parentId")),
            )
        )

    at = posted or _parse_iso(issue.get("created_at") or issue.get("createdAt"))
    if at is None:
        return None
    hour, minute = match.group("hour"), match.group("minute")
    if hour and minute:
        # The title's clock time is when the leader delegated; the comment lands
        # later. Prefer the title so the row sorts next to its parent decision.
        at = at.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

    final = None
    for response in reversed(responses):
        if response.action:
            final = response.action
            break

    return {
        "kind": "delegation",
        # Named like the watcher's own trigger types so it reads consistently
        # alongside them; the UI adds a 위임 pill rather than repeating the word.
        "trigger_type": "squad_delegation",
        "tier": 2,
        "scope": "global",
        "dispatched_at": at.isoformat(),
        "stock_code": None,
        "stock_name": None,
        "reason": match.group("subject").strip() or title,
        "snapshot": None,
        "snapshot_raw": None,
        "issue": _issue_ref(issue),
        "responses": [
            {
                "text": r.text,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "action": r.action,
                "threaded": r.threaded,
            }
            for r in responses
        ],
        "final_action": final,
        # A delegation produces an opinion, not an order. There is nothing to
        # reconcile against the broker.
        "outcome": None,
        "outcome_source": "not_applicable",
    }


def _issue_ref(issue: dict[str, Any] | None) -> dict[str, Any] | None:
    if not issue:
        return None
    return {
        "id": issue.get("id"),
        "identifier": issue.get("identifier"),
        "title": issue.get("title"),
        "status": issue.get("status"),
    }


def build_rows(
    threads: Iterable[tuple[dict[str, Any] | None, Sequence[dict[str, Any]]]],
    recent_items: Sequence[dict[str, Any]] | None,
    *,
    include_tier1: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Build the merged, newest-first decision timeline.

    ``threads`` is an iterable of ``(issue_summary, comments)`` pairs.
    ``recent_items`` is the watcher's ``/recent`` list, or None/empty when the
    watcher is unreachable or was restarted (its ring buffer is process-lifetime,
    so a restart legitimately empties it).
    """

    items = [i for i in (recent_items or []) if isinstance(i, dict)]
    join_enabled = bool(items)

    rows: list[dict[str, Any]] = []
    for issue, comments in threads:
        delegation = delegation_row(issue, comments or []) if issue else None
        if delegation is not None:
            rows.append(delegation)
            continue
        for segment in segment_thread(comments or []):
            rows.append(_segment_row(segment, issue, items, join_enabled=join_enabled))

    if include_tier1:
        for item in items:
            if item.get("tier") != 1:
                continue
            row = _tier1_row(item)
            if row is not None:
                rows.append(row)

    rows.sort(key=lambda row: row["dispatched_at"], reverse=True)
    if limit is not None and limit >= 0:
        rows = rows[:limit]
    return rows


__all__ = [
    "AgentResponse",
    "delegation_row",
    "DispatchInfo",
    "JOIN_AMBIGUITY_SECONDS",
    "JOIN_TOLERANCE_SECONDS",
    "Segment",
    "build_rows",
    "join_outcome",
    "normalize_stock_code",
    "parse_dispatch_comment",
    "segment_thread",
]
