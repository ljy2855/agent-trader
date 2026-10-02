"""Calendar gate that fires the brief autopilots."""

import importlib
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
gate = importlib.import_module("autopilot_calendar_gate")


class FakeMultica:
    def __init__(self, runs=(), fail=False, status="active"):
        self.runs = list(runs)
        self.fail = fail
        self.status = status
        self.triggered = []

    def __call__(self, *args):
        if self.fail:
            raise RuntimeError("boom")
        if args[:2] == ("autopilot", "get"):
            return {"autopilot": {"id": args[2], "status": self.status}, "triggers": []}
        if args[:2] == ("autopilot", "runs"):
            return {"runs": self.runs}
        if args[:2] == ("autopilot", "trigger"):
            self.triggered.append(args[2])
            return {"id": "run-1", "status": "running"}
        raise AssertionError(args)


def test_closures_come_from_the_krx_calendar():
    assert gate.closure(date(2026, 10, 5)) == "개천절 대체공휴일"
    assert gate.closure(date(2026, 10, 6)) is None
    # Unverified special session and an unsupported year are uncertain, not shut.
    assert gate.closure(date(2026, 11, 19)) is None
    assert gate.closure(date(2027, 1, 4)) is None


def test_holiday_fires_nothing(monkeypatch):
    fake = FakeMultica()
    monkeypatch.setattr(gate, "_multica", fake)
    assert "휴장" in gate.fire("pre", date(2026, 10, 5))
    assert fake.triggered == []


def test_trading_day_fires_once(monkeypatch):
    fake = FakeMultica(runs=[{"source": "schedule", "triggered_at": "2026-10-01T23:40:07Z"}])
    monkeypatch.setattr(gate, "_multica", fake)
    # Yesterday's run (08:40 KST on 10-02) does not count for 10-06.
    assert "발화 —" in gate.fire("pre", date(2026, 10, 6))
    assert fake.triggered == ["pre"]


def test_a_run_already_triggered_today_is_not_repeated(monkeypatch):
    # 2026-10-05T23:40Z is 08:40 KST on 10-06.
    fake = FakeMultica(runs=[{"source": "manual", "triggered_at": "2026-10-05T23:40:03Z"}])
    monkeypatch.setattr(gate, "_multica", fake)
    assert "이미 실행됨" in gate.fire("pre", date(2026, 10, 6))
    assert fake.triggered == []


def test_dry_run_only_reports(monkeypatch):
    fake = FakeMultica()
    monkeypatch.setattr(gate, "_multica", fake)
    assert "dry-run" in gate.fire("pre", date(2026, 10, 6), dry_run=True)
    assert fake.triggered == []


def test_a_failed_multica_call_exits_non_zero(monkeypatch):
    monkeypatch.setattr(gate, "_multica", FakeMultica(fail=True))
    monkeypatch.setattr(sys, "argv", ["autopilot_calendar_gate", "--autopilot=pre", "--date=2026-10-06"])
    assert gate.main() == 1


def test_a_paused_autopilot_is_not_fired(monkeypatch):
    # Pausing the autopilot is the documented emergency stop for the briefs.
    fake = FakeMultica(status="paused")
    monkeypatch.setattr(gate, "_multica", fake)
    assert "paused" in gate.fire("pre", date(2026, 10, 6))
    assert fake.triggered == []
