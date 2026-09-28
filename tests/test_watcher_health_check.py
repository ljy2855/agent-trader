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


# --- spam suppression / state machine ------------------------------------


def _run_main(monkeypatch, argv, posts):
    monkeypatch.setattr(sys, "argv", ["watcher_health_check", *argv])
    monkeypatch.setattr(hc, "_post_discord",
                        lambda t, d, c: posts.append((t, d, c)))
    # Always treat as in-session so tests don't depend on wall-clock.
    monkeypatch.setattr(hc, "is_krx_regular_session_open", lambda now: True)
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


def test_off_session_skips_entirely(monkeypatch):
    _stub_endpoints(monkeypatch, health=None, state=None)
    posts = []
    monkeypatch.setattr(sys, "argv", ["watcher_health_check"])
    monkeypatch.setattr(hc, "_post_discord", lambda t, d, c: posts.append(t))
    monkeypatch.setattr(hc, "is_krx_regular_session_open", lambda now: False)
    assert hc.main() == 0
    assert posts == []  # off-hours staleness is normal, must not page
