"""Brief/wrap forwarder — the KRX holiday gate."""

import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
fab = importlib.import_module("forward_autopilot_brief")

KST = timezone(timedelta(hours=9))

PRE_OPEN_ARGS = [
    "forward_autopilot_brief",
    "--autopilot=autopilot-1",
    "--title-prefix=[Pre-open]",
    "--required-action=BRIEF_DONE",
    "--discord-title=Pre-Open Brief",
]


def _pin(monkeypatch, *parts):
    """Make the module's clock read the given KST time."""

    class Pinned(datetime):
        @classmethod
        def now(cls, tz=None):
            at = datetime(*parts, tzinfo=KST)
            return at.astimezone(tz) if tz else at

    monkeypatch.setattr(fab, "datetime", Pinned)


def test_closure_comes_from_the_krx_calendar(monkeypatch):
    _pin(monkeypatch, 2026, 10, 5, 8, 50)
    assert fab._krx_closure_today() == "개천절 대체공휴일"
    _pin(monkeypatch, 2026, 10, 6, 8, 50)
    assert fab._krx_closure_today() is None
    # An unverified special session is uncertain, not closed: it may trade.
    _pin(monkeypatch, 2026, 11, 19, 8, 50)
    assert fab._krx_closure_today() is None


def test_holiday_run_neither_forwards_nor_cleans_up(monkeypatch):
    _pin(monkeypatch, 2026, 10, 5, 15, 55)
    calls = []
    monkeypatch.setattr(fab, "_run", lambda args: calls.append(args) or (0, "{}", ""))
    monkeypatch.setattr(fab, "_post_discord", lambda *a, **k: calls.append(("discord", a)))
    monkeypatch.setattr(sys, "argv", [*PRE_OPEN_ARGS, "--close-resolved"])

    assert fab.main() == 0
    assert calls == []


def test_trading_day_still_pages_when_the_brief_is_missing(monkeypatch):
    _pin(monkeypatch, 2026, 10, 6, 8, 50)
    looked, posts = [], []
    monkeypatch.setattr(fab, "_autopilot_today_issue_id", lambda ap: looked.append(ap))
    monkeypatch.setattr(fab, "_list_today_issues", lambda prefix: [])
    monkeypatch.setattr(fab, "_post_discord", lambda title, desc, **k: posts.append(desc))
    monkeypatch.setattr(sys, "argv", PRE_OPEN_ARGS)

    assert fab.main() == 0
    assert looked == ["autopilot-1"]
    assert posts and "찾지 못했습니다" in posts[0]
