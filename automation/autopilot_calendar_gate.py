#!/usr/bin/env python3
"""Fire a brief autopilot on days the exchange may open, and on no others.

The pre-open (08:40) and wrap (15:40) autopilots used to fire on Multica's
own weekday cron, which cannot express the exchange calendar: on the Chuseok
holidays both ran, opened issues and spent PM runs on a closed market. So the
schedule now lives in a CronJob that runs this script at those times. On a
known KRX closure it does nothing; otherwise it triggers the autopilot once.
An uncertain calendar day counts as open — the session may still run, and the
watcher keeps going on one too.

Why not keep Multica's trigger and switch it off for the holiday: a schedule
trigger that is re-enabled after missing a slot fires the missed run within
seconds, even though the update reports a future ``next_run_at`` (checked on
2026-10-02 with a throwaway autopilot). Re-enabling on the morning after a
holiday would have run the holiday's brief and wrap at 08:30. The Multica
triggers therefore stay disabled; turning one back on fires once.

A paused autopilot is left alone. Its status is the operator's emergency stop
(``multica autopilot update <id> --status paused``), and a manual trigger is
not assumed to honour it, so this script checks it first.

Idempotent: if the autopilot already has a run triggered today (KST), nothing
is triggered — a Job retry, a manual re-run or a leftover Multica trigger can
not produce a second brief. Exits non-zero when a Multica call fails, so the
Job retries and the failure shows; a missing brief also surfaces in the 16:00
digest as an unconfirmed BRIEF_DONE / WRAP_DONE.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

# automation/ lands on sys.path[0], not the repo root — same shim as
# daily_ops_digest.py so `src.services` is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.krx_calendar import DAY_CLOSED, krx_day_status  # noqa: E402

KST = timezone(timedelta(hours=9))
MULTICA_BIN = os.environ.get("MULTICA_BIN", "multica")


def closure(day: date) -> str | None:
    """Why the exchange is shut on ``day``, or None when it is (or may be) open."""

    status = krx_day_status(day)
    return status.reason if status.state == DAY_CLOSED else None


def _multica(*args: str) -> object:
    proc = subprocess.run(
        [MULTICA_BIN, *args, "--output", "json"],
        capture_output=True, text=True, check=False, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"multica {' '.join(args[:2])} failed: {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def _kst_date(stamp: object) -> date | None:
    try:
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).astimezone(KST).date()
    except ValueError:
        return None


def status_of(autopilot_id: str) -> str | None:
    data = _multica("autopilot", "get", autopilot_id)
    data = data if isinstance(data, dict) else {}
    return (data.get("autopilot") or data).get("status")


def runs_on(autopilot_id: str, day: date) -> list[dict]:
    """The autopilot's runs triggered on ``day`` (KST), newest first."""

    data = _multica("autopilot", "runs", autopilot_id, "--limit", "20")
    runs = data if isinstance(data, list) else (data or {}).get("runs", [])
    return [
        run for run in runs
        if isinstance(run, dict) and _kst_date(run.get("triggered_at")) == day
    ]


def fire(autopilot_id: str, day: date, *, dry_run: bool = False) -> str:
    """Trigger the autopilot for ``day`` unless that would be wrong; say what happened."""

    why_closed = closure(day)
    if why_closed:
        return f"{day} KRX 휴장({why_closed}) — {autopilot_id} 발화 안 함"
    status = status_of(autopilot_id)
    if status != "active":
        return f"{day} {autopilot_id}: 상태 {status} — 발화 안 함 (수동 정지 존중)"
    existing = runs_on(autopilot_id, day)
    if existing:
        first = existing[-1]
        return (
            f"{day} {autopilot_id}: 오늘 이미 실행됨 "
            f"({first.get('source')} {first.get('triggered_at')}) — 다시 발화하지 않음"
        )
    if dry_run:
        return f"{day} {autopilot_id}: 발화할 예정 (dry-run)"
    run = _multica("autopilot", "trigger", autopilot_id)
    run = run if isinstance(run, dict) else {}
    return f"{day} {autopilot_id}: 발화 — run {run.get('id')} {run.get('status')}"


def main() -> int:
    ap = argparse.ArgumentParser(prog="autopilot_calendar_gate", description=__doc__)
    ap.add_argument("--autopilot", required=True, help="발화할 autopilot id")
    ap.add_argument("--date", help="판정할 날짜 YYYY-MM-DD (기본 오늘, KST)")
    ap.add_argument("--dry-run", action="store_true", help="발화하지 않고 판정만 출력")
    args = ap.parse_args()
    day = date.fromisoformat(args.date) if args.date else datetime.now(KST).date()
    try:
        print(fire(args.autopilot, day, dry_run=args.dry_run))
    except (RuntimeError, ValueError) as exc:
        print(f"{day} {args.autopilot}: 실패 — {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
