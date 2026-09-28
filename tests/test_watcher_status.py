"""Tests for the WatcherStatusRegistry + status HTTP app."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from starlette.testclient import TestClient  # noqa: E402

from src.services.watcher_status import (  # noqa: E402
    KST,
    RECENT_TRIGGER_LIMIT,
    WatcherStatusRegistry,
)
from src.services.watcher_status_server import build_status_app  # noqa: E402


def test_snapshot_initially_quiet():
    r = WatcherStatusRegistry()
    snap = r.snapshot()
    assert snap["cycle_count"] == 0
    assert snap["mode"] == "unknown"
    assert snap["in_flight"] == []


def test_lifecycle_marks_started_and_stopped():
    r = WatcherStatusRegistry()
    r.mark_started(mode="live", execute_orders=False, poll_interval_seconds=30)
    snap = r.snapshot()
    assert snap["mode"] == "live"
    assert snap["execute_orders"] is False
    assert snap["poll_interval_seconds"] == 30
    assert snap["started_at"] is not None
    assert snap["stopped_at"] is None

    r.mark_stopped()
    assert r.snapshot()["stopped_at"] is not None


def test_effective_config_is_published_verbatim():
    # Observers must be able to read what this process actually runs — the live
    # deployment overrides most thresholds via CLI args, so anything rebuilding
    # them from code defaults reports the wrong numbers.
    r = WatcherStatusRegistry()
    config = {"stop_loss_pct": -4.0, "max_positions": 1, "entry_mode": "below_ma"}
    r.mark_started(
        mode="live", execute_orders=True, poll_interval_seconds=30, config=config
    )

    snap = r.snapshot()
    assert snap["config"] == config
    # Snapshot must not alias the caller's dict.
    config["max_positions"] = 99
    assert r.snapshot()["config"]["max_positions"] == 1


def test_config_defaults_to_empty_when_not_reported():
    r = WatcherStatusRegistry()
    r.mark_started(mode="live", execute_orders=False, poll_interval_seconds=30)

    # Empty, never a fabricated set of defaults — consumers key off this to say
    # "this watcher does not report its config" instead of inventing values.
    assert r.snapshot()["config"] == {}


def test_mark_tick_increments_cycle_and_clears_error():
    r = WatcherStatusRegistry()
    r.mark_tick_error("oops")
    assert r.snapshot()["last_error"] == "oops"
    r.mark_tick(
        regime={"regime": "neutral"},
        holding_count=2,
        open_order_count=1,
        candidate_count=10,
        api_failure_count=0,
    )
    snap = r.snapshot()
    assert snap["cycle_count"] == 1
    assert snap["regime"] == {"regime": "neutral"}
    assert snap["portfolio"]["holding_count"] == 2
    assert snap["last_error"] is None


def test_record_trigger_appends_newest_first():
    r = WatcherStatusRegistry()
    e1 = r.record_trigger(
        trigger_type="stop_loss", tier=1, scope="stock", target_role="self",
        stock_code="001", stock_name="A", reason="-3%",
    )
    e2 = r.record_trigger(
        trigger_type="holding_swing", tier=2, scope="stock", target_role="evaluator",
        stock_code="002", stock_name="B", reason="+2%",
    )
    items = r.recent()
    assert items[0]["trigger_type"] == e2.trigger_type
    assert items[1]["trigger_type"] == e1.trigger_type


def test_record_trigger_ring_buffer_caps_at_limit():
    r = WatcherStatusRegistry(recent_limit=5)
    for i in range(20):
        r.record_trigger(
            trigger_type=f"t{i}", tier=1, scope="stock", target_role="self",
            stock_code=None, stock_name=None, reason="",
        )
    items = r.recent()
    assert len(items) == 5
    assert items[0]["trigger_type"] == "t19"  # newest first


def test_dispatch_outcome_lifecycle():
    r = WatcherStatusRegistry()
    e = r.record_trigger(
        trigger_type="holding_swing", tier=2, scope="stock", target_role="evaluator",
        stock_code="001", stock_name="A", reason="x",
    )
    r.mark_dispatched(e, issue_id="iss-1")
    r.mark_outcome(e, outcome="executed", action="TRIM", detail="qty/2")
    items = r.recent()
    assert items[0]["dispatched"] is True
    assert items[0]["outcome"] == "executed"
    assert items[0]["action"] == "TRIM"
    assert items[0]["detail"] == "qty/2"
    assert items[0]["completed_at"] is not None


def test_in_flight_add_remove():
    r = WatcherStatusRegistry()
    r.add_in_flight(
        scope_key="stock:001",
        trigger_type="holding_swing",
        target_role="evaluator",
        stock_code="001",
        stock_name="A",
        started_at=datetime.now(KST),
        issue_id="iss-1",
    )
    snap = r.snapshot()
    assert len(snap["in_flight"]) == 1
    assert snap["in_flight"][0]["scope_key"] == "stock:001"
    r.remove_in_flight("stock:001")
    assert r.snapshot()["in_flight"] == []


# -- HTTP app -------------------------------------------------------------


def test_candidate_slots_counts_only_qualifying_ticks():
    """A tick with nothing worth buying is not a blocked opportunity."""

    r = WatcherStatusRegistry()
    r.record_candidate_slots(trading_day="2026-09-18", available_slots=0)
    r.record_candidate_slots(
        trading_day="2026-09-18", available_slots=0, top_score=8, top_name="HMM"
    )
    r.record_candidate_slots(
        trading_day="2026-09-18", available_slots=1, top_score=9, top_name="SK"
    )

    slots = r.snapshot()["candidate_slots"]
    assert slots["qualified_ticks"] == 2
    assert slots["starved_ticks"] == 1
    # The score-9 tick had a slot, so it is not a missed opportunity.
    assert slots["best_starved_score"] == 8
    assert slots["best_starved_name"] == "HMM"


def test_candidate_slots_reset_on_a_new_trading_day():
    """The digest asks about today, so yesterday must not leak into it."""

    r = WatcherStatusRegistry()
    for _ in range(5):
        r.record_candidate_slots(
            trading_day="2026-09-17", available_slots=0, top_score=9, top_name="HMM"
        )
    r.record_candidate_slots(
        trading_day="2026-09-18", available_slots=1, top_score=8, top_name="SK"
    )

    slots = r.snapshot()["candidate_slots"]
    assert slots["trading_day"] == "2026-09-18"
    assert slots["qualified_ticks"] == 1
    assert slots["starved_ticks"] == 0
    assert slots["best_starved_score"] is None


def test_candidate_slots_reproduce_the_september_16_to_18_shape():
    """Those three sessions: a held position, candidates all day, no dispatch.

    The wraps reported "eligible 0건" from a post-close rescan and nobody
    could tell a quiet market from a full portfolio.
    """

    r = WatcherStatusRegistry()
    for _ in range(180):
        r.record_candidate_slots(
            trading_day="2026-09-18", available_slots=0, top_score=8, top_name="HMM"
        )

    slots = r.snapshot()["candidate_slots"]
    assert slots["qualified_ticks"] == slots["starved_ticks"] == 180


def test_the_best_starved_candidate_is_kept_not_the_last():
    """Tick count alone cannot rule on a missed rotation.

    2026-09-21 ran 99.2% starved and the wrap could not say whether a
    better name went by — while the day's last snapshot held HMM at score
    9, over the rotation threshold, with zero slots. Keeping the maximum
    is what makes that answerable the next morning.
    """

    r = WatcherStatusRegistry()
    for score, name in ((8, "한화생명"), (9, "HMM"), (8, "LG전자")):
        r.record_candidate_slots(
            trading_day="2026-09-21",
            available_slots=0,
            top_score=score,
            top_name=name,
        )

    slots = r.snapshot()["candidate_slots"]
    assert slots["best_starved_score"] == 9
    assert slots["best_starved_name"] == "HMM"


def test_a_candidate_that_had_a_slot_is_never_recorded_as_starved():
    """It was asked about; whatever happened next is the screener's call."""

    r = WatcherStatusRegistry()
    r.record_candidate_slots(
        trading_day="2026-09-21", available_slots=1, top_score=10, top_name="삼성전자"
    )

    slots = r.snapshot()["candidate_slots"]
    assert slots["starved_ticks"] == 0
    assert slots["best_starved_score"] is None


def test_status_app_state_endpoint():
    r = WatcherStatusRegistry()
    r.mark_started(mode="mock", execute_orders=False, poll_interval_seconds=30)
    app = build_status_app(r)
    client = TestClient(app)
    resp = client.get("/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "mock"
    assert data["cycle_count"] == 0


def test_status_app_recent_with_limit():
    r = WatcherStatusRegistry()
    for i in range(10):
        r.record_trigger(
            trigger_type=f"t{i}", tier=1, scope="stock", target_role="self",
            stock_code=None, stock_name=None, reason="",
        )
    app = build_status_app(r)
    client = TestClient(app)
    resp = client.get("/recent?limit=3")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 3
    assert items[0]["trigger_type"] == "t9"


def test_status_app_health():
    r = WatcherStatusRegistry()
    app = build_status_app(r)
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_status_app_ledger_endpoint_passes_filters():
    seen = {}

    def view(*, limit, trading_day):
        seen.update(limit=limit, trading_day=trading_day)
        return {"available": True, "recent": []}

    client = TestClient(build_status_app(WatcherStatusRegistry(), ledger_view=view))
    resp = client.get("/ledger?limit=7&trading_day=2026-09-23")

    assert resp.status_code == 200
    assert resp.json()["available"] is True
    assert seen == {"limit": 7, "trading_day": "2026-09-23"}


def test_status_app_ledger_endpoint_without_a_ledger():
    client = TestClient(build_status_app(WatcherStatusRegistry()))

    resp = client.get("/ledger")

    assert resp.status_code == 503
    assert resp.json()["available"] is False
