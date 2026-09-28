"""Append-only journal of candidate scores, for threshold calibration.

Nothing records why a session bought nothing. The watcher scores every
candidate each tick and throws the numbers away; the only surviving trace
is a dispatch, which happens exactly when the score already cleared the
gate. So the distribution *below* the gate — the part that says whether
the gate is set sanely — has never been observable.

That question is live: after the 2026-08-17 universe fix, in-band names
finally reach the scorer (KB금융 scored 6 against a gate of 8 on 08-18),
and deciding whether 8 is right needs the spread of those scores, not
anecdotes. Changing the gate off a handful of remembered numbers is the
kind of tuning §10.0 warns about; this is how the sample gets collected
instead.

Only in-band candidates are written, and at most one record per
``min_interval_seconds``, so a session costs a few hundred short lines.
Writes are best-effort: this is observability, and a journal failure must
never interrupt a trading tick.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# Sampling interval. Scores drift slowly, and any crossing of the gate is
# already visible as a dispatch, so this only needs to shape a histogram.
DEFAULT_MIN_INTERVAL_SECONDS = 120


def in_band(row: dict[str, Any]) -> bool:
    """True when the candidate passed the below_ma dip gate.

    Keyed on the published `ma_dip_pct` rather than the Korean reason text,
    so the journal does not break when a message is reworded.
    """

    dip = row.get("ma_dip_pct")
    if not isinstance(dip, (int, float)):
        return False
    from .strategy import _BELOW_MA_MAX_DIP_PCT

    return 0 < dip <= _BELOW_MA_MAX_DIP_PCT


def build_record(
    *,
    now: datetime,
    regime: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    min_score: int,
    available_slots: int | None = None,
    holding_count: int | None = None,
) -> dict[str, Any] | None:
    """Compact snapshot of the in-band candidates, or None if none are.

    ``available_slots`` is what `detect_tier2_new_candidates` will see a few
    lines later: `max_positions - len(holdings)`, capped by
    `max_new_positions`. At zero it returns `[]` before building any event,
    so the screener is never asked and the day leaves no trace of what was
    turned away. Measured over 2026-08-19..09-18 that silence covered a lot:
    78.7% of snapshots held a gate-passing candidate while only 5 entries
    were made in 23 trading days, because a position was open 83% of the
    time. Recording the slot count here is what makes "we had candidates and
    no room" countable instead of a thing someone has to notice by hand.

    Both are optional so older callers and replayed fixtures keep working;
    they are simply absent from the record when not supplied.
    """

    band = [row for row in candidate_rows or [] if in_band(row)]
    if not band:
        return None
    band.sort(key=lambda row: -(row.get("score") or 0))
    return {
        "ts": now.isoformat(),
        "trading_day": now.astimezone(KST).strftime("%Y-%m-%d"),
        "regime": (regime or {}).get("regime"),
        "extreme_risk_off": bool((regime or {}).get("extreme_risk_off")),
        "min_score": min_score,
        "scanned": len(candidate_rows or []),
        **(
            {"available_slots": available_slots}
            if available_slots is not None
            else {}
        ),
        **({"holding_count": holding_count} if holding_count is not None else {}),
        "band": [
            {
                "code": row.get("stock_code"),
                "name": row.get("stock_name"),
                "score": row.get("score"),
                "dip_pct": row.get("ma_dip_pct"),
                "eligible": bool(row.get("eligible")),
                "blocked_by": [
                    reason for reason in (row.get("reasons") or [])
                    if "이평" not in reason
                ],
            }
            for row in band
        ],
    }


class CandidateJournal:
    """Rate-limited JSONL sink for candidate score snapshots."""

    def __init__(
        self,
        path: str | Path | None,
        *,
        min_interval_seconds: int = DEFAULT_MIN_INTERVAL_SECONDS,
    ) -> None:
        self._path = Path(path) if path else None
        self._min_interval = max(int(min_interval_seconds), 0)
        self._last_written_at: datetime | None = None

    @property
    def enabled(self) -> bool:
        return self._path is not None

    def _due(self, now: datetime) -> bool:
        if self._last_written_at is None:
            return True
        return now - self._last_written_at >= timedelta(seconds=self._min_interval)

    def record(
        self,
        *,
        now: datetime,
        regime: dict[str, Any],
        candidate_rows: list[dict[str, Any]],
        min_score: int,
        available_slots: int | None = None,
        holding_count: int | None = None,
    ) -> dict[str, Any] | None:
        """Append one snapshot when due. Returns it, or None if skipped."""

        if not self._path or not self._due(now):
            return None
        record = build_record(
            now=now,
            regime=regime,
            candidate_rows=candidate_rows,
            min_score=min_score,
            available_slots=available_slots,
            holding_count=holding_count,
        )
        if record is None:
            return None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            # Observability must never take a trading tick down with it.
            return None
        self._last_written_at = now
        return record


__all__ = [
    "CandidateJournal",
    "DEFAULT_MIN_INTERVAL_SECONDS",
    "build_record",
    "in_band",
]
