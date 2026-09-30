"""Watcher liveness alarm tests — detection logic and spam suppression."""

import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
hc = importlib.import_module("watcher_health_check")

UTC = timezone.utc


def _iso(minutes_ago: float) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat()


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch):
    """Point state at a temp file so tests never touch the real PVC path."""
    monkeypatch.setattr(hc, "STATE_PATH", tmp_path / "health.json")
    monkeypatch.setattr(hc, "WEBHOOK_URL", "")  # never post during tests
    return tmp_path


def _stub_endpoints(monkeypatch, *, health, state):
    def fake_get(url, timeout=10.0):
        if url.endswith("/health"):
            return health
        if url.endswith("/state"):
            return state
        return None
    monkeypatch.setattr(hc, "_get_json", fake_get)


# --- detection ------------------------------------------------------------


def test_healthy_when_health_ok_and_tick_fresh(monkeypatch):
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(0.5), "cycle_count": 42})
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert healthy
    assert problems == []


def test_unreachable_health_endpoint_is_a_problem(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert not healthy
    assert any("응답 없음" in p for p in problems)


def test_stale_tick_detected_even_when_health_returns_ok(monkeypatch):
    # The wedged-loop case: status server answers, trading loop frozen.
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(45), "cycle_count": 7})
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert not healthy
    assert any("루프 정지 의심" in p for p in problems)


def test_last_error_is_reported(monkeypatch):
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(0.2), "last_error": "boom"})
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert not healthy
    assert any("boom" in p for p in problems)


def test_missing_last_tick_is_a_problem(monkeypatch):
    _stub_endpoints(monkeypatch, health={"status": "ok"}, state={})
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert not healthy
    assert any("last_tick_at 없음" in p for p in problems)


def test_no_tick_is_tolerated_right_after_startup(monkeypatch):
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"started_at": _iso(1)})  # started 1 min ago
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert healthy, problems


def test_no_tick_alerts_once_past_the_grace_window(monkeypatch):
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"started_at": _iso(30)})  # up 30 min, still no tick
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert not healthy
    assert any("루프가 한 번도 돌지 않음" in p for p in problems)
    assert any("기동 30분 경과" in p for p in problems)


def test_stale_tick_still_alerts_even_for_a_fresh_start(monkeypatch):
    # Grace applies only to a *missing* tick. An actual stale tick is a
    # wedge regardless of how recently the process started.
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"started_at": _iso(1), "last_tick_at": _iso(60)})
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert not healthy
    assert any("루프 정지 의심" in p for p in problems)


def test_unparseable_tick_is_a_problem(monkeypatch):
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": "not-a-date"})
    healthy, problems, _ = hc.check(stale_minutes=5)
    assert not healthy
    assert any("파싱 불가" in p for p in problems)


# --- the first minutes of a session --------------------------------------

# What /state holds when the 09:00 run reads it, about eight seconds in.
_AT_THE_OPEN = 8 / 60


def test_yesterdays_tick_is_not_stale_at_the_open(monkeypatch):
    # Up since yesterday: the last tick on record is the 15:29 one, 17.5
    # hours old, because today's first tick has not finished yet.
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(1050), "cycle_count": 733})
    healthy, problems, _ = hc.check(stale_minutes=5, session_age_min=_AT_THE_OPEN)
    assert healthy, problems


def test_no_tick_is_not_a_problem_at_the_open_after_an_overnight_restart(monkeypatch):
    # Restarted the evening before: `last_tick_at` lives in process memory,
    # so there is none until the first tick of the new process.
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"started_at": _iso(745)})
    healthy, problems, _ = hc.check(stale_minutes=5, session_age_min=_AT_THE_OPEN)
    assert healthy, problems


def test_stale_tick_pages_once_the_session_is_a_stale_window_old(monkeypatch):
    # The next run, ten minutes in: a loop that never woke is now overdue.
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(1060), "cycle_count": 733})
    healthy, problems, _ = hc.check(stale_minutes=5, session_age_min=10)
    assert not healthy
    assert any("루프 정지 의심" in p for p in problems)

    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"started_at": _iso(755)})
    healthy, problems, _ = hc.check(stale_minutes=5, session_age_min=10)
    assert not healthy
    assert any("루프가 한 번도 돌지 않음" in p for p in problems)


def test_the_open_does_not_excuse_a_watcher_that_is_down_or_erroring(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    healthy, problems, _ = hc.check(stale_minutes=5, session_age_min=_AT_THE_OPEN)
    assert not healthy
    assert any("응답 없음" in p for p in problems)

    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(1050), "last_error": "boom"})
    healthy, problems, _ = hc.check(stale_minutes=5, session_age_min=_AT_THE_OPEN)
    assert not healthy
    assert any("boom" in p for p in problems)


def test_session_age_is_measured_from_the_days_open():
    kst = hc.KST
    assert hc.session_age_minutes(
        datetime(2026, 9, 30, 9, 0, 8, tzinfo=kst)
    ) == pytest.approx(8 / 60)
    assert hc.session_age_minutes(datetime(2026, 9, 30, 9, 10, 8, tzinfo=kst)) > 10
    # A delayed special session is measured from its own open (10:00).
    assert hc.session_age_minutes(
        datetime(2026, 1, 2, 10, 3, tzinfo=kst)
    ) == pytest.approx(3)
    # No session, no age: before the open, after the close, on a holiday.
    assert hc.session_age_minutes(datetime(2026, 9, 30, 8, 59, tzinfo=kst)) is None
    assert hc.session_age_minutes(datetime(2026, 9, 30, 15, 31, tzinfo=kst)) is None
    assert hc.session_age_minutes(datetime(2026, 10, 5, 9, 0, 8, tzinfo=kst)) is None


# --- spam suppression / state machine ------------------------------------


def _run_main(monkeypatch, argv, posts, *, session_age=60.0):
    monkeypatch.setattr(sys, "argv", ["watcher_health_check", *argv])
    monkeypatch.setattr(hc, "_post_discord",
                        lambda t, d, c: posts.append((t, d, c)))
    # Always treat as in-session so tests don't depend on wall-clock — and
    # as mid-session unless a test is about the open.
    monkeypatch.setattr(hc, "is_krx_regular_session_open", lambda now: True)
    monkeypatch.setattr(hc, "session_age_minutes", lambda now: session_age)
    return hc.main()


def test_first_failure_pages_and_records_state(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    posts = []
    assert _run_main(monkeypatch, [], posts) == 0
    assert len(posts) == 1
    assert "Watcher 이상" in posts[0][0]
    saved = json.loads(hc.STATE_PATH.read_text())
    assert saved["alerting"] is True
    assert saved["last_alert_at"]


def test_repeat_failure_within_cooldown_is_suppressed(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    hc.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    hc.STATE_PATH.write_text(json.dumps({
        "alerting": True,
        "last_alert_at": datetime.now(hc.KST).isoformat(),
    }))
    posts = []
    _run_main(monkeypatch, ["--alert-cooldown-minutes", "30"], posts)
    assert posts == []  # still broken, but too soon to page again


def test_repeat_failure_after_cooldown_pages_again(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    hc.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    hc.STATE_PATH.write_text(json.dumps({
        "alerting": True,
        "last_alert_at": (datetime.now(hc.KST) - timedelta(minutes=90)).isoformat(),
    }))
    posts = []
    _run_main(monkeypatch, ["--alert-cooldown-minutes", "30"], posts)
    assert len(posts) == 1


def test_suppressed_check_preserves_original_alert_timestamp(monkeypatch):
    # Cooldown must measure from the last *sent* page; otherwise a
    # flapping check would push the deadline forward forever and the
    # follow-up alert would never fire.
    _stub_endpoints(monkeypatch, health=None, state=None)
    original = (datetime.now(hc.KST) - timedelta(minutes=5)).isoformat()
    hc.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    hc.STATE_PATH.write_text(json.dumps({"alerting": True, "last_alert_at": original}))
    _run_main(monkeypatch, ["--alert-cooldown-minutes", "30"], [])
    assert json.loads(hc.STATE_PATH.read_text())["last_alert_at"] == original


def test_recovery_posts_all_clear_once(monkeypatch):
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(0.1), "cycle_count": 99})
    hc.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    hc.STATE_PATH.write_text(json.dumps({
        "alerting": True,
        "last_alert_at": datetime.now(hc.KST).isoformat(),
    }))
    posts = []
    _run_main(monkeypatch, [], posts)
    assert len(posts) == 1 and "복구" in posts[0][0]
    assert json.loads(hc.STATE_PATH.read_text())["alerting"] is False

    # A second healthy run must stay silent.
    posts.clear()
    _run_main(monkeypatch, [], posts)
    assert posts == []


def test_run_at_the_open_neither_pages_nor_sends_the_all_clear(monkeypatch):
    # An alert from yesterday afternoon is still open, and the watcher
    # answers /health with yesterday's tick. That is not evidence of a stuck
    # loop this early — and not evidence of a recovery either.
    _stub_endpoints(monkeypatch, health={"status": "ok"},
                    state={"last_tick_at": _iso(1050), "cycle_count": 733})
    before = json.dumps({
        "alerting": True,
        "last_alert_at": (datetime.now(hc.KST) - timedelta(hours=18)).isoformat(),
    })
    hc.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    hc.STATE_PATH.write_text(before)

    posts = []
    assert _run_main(monkeypatch, [], posts, session_age=_AT_THE_OPEN) == 0
    assert posts == []
    assert hc.STATE_PATH.read_text() == before

    # Ten minutes in the same stale tick is a stuck loop, and it pages.
    assert _run_main(monkeypatch, [], posts, session_age=10.0) == 0
    assert len(posts) == 1 and "Watcher 이상" in posts[0][0]


def test_run_at_the_open_still_pages_when_the_watcher_is_down(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    posts = []
    _run_main(monkeypatch, [], posts, session_age=_AT_THE_OPEN)
    assert len(posts) == 1 and "Watcher 이상" in posts[0][0]


def test_off_session_skips_entirely(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    posts = []
    monkeypatch.setattr(sys, "argv", ["watcher_health_check"])
    monkeypatch.setattr(hc, "_post_discord", lambda t, d, c: posts.append(t))
    monkeypatch.setattr(hc, "is_krx_regular_session_open", lambda now: False)
    assert hc.main() == 0
    assert posts == []  # off-hours staleness is normal, must not page
