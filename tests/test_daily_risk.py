"""Tests for the daily new-entry circuit breaker (P0-1).

The invariant under test throughout: the breaker blocks *opening new
exposure* and nothing else. Every latch, reset and fail-closed path here is
about buys — the sell/cancel side is verified in `test_watcher.py`, where
the real order routing lives.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.daily_risk import (  # noqa: E402
    BLOCK_ACCOUNT_DATA,
    BLOCK_CALENDAR_UNCERTAIN,
    BLOCK_DAILY_LOSS_KRW,
    BLOCK_DAILY_LOSS_PCT,
    BLOCK_LOSS_SOURCE_UNVERIFIED,
    BLOCK_MAX_NEW_ENTRIES,
    BLOCK_STATE_UNAVAILABLE,
    KST,
    AccountDailySnapshot,
    DailyEntryBreaker,
    DailyRiskLimits,
    current_trading_day,
    next_trading_day,
    next_trading_day_status,
    read_account_daily_snapshot,
    should_reset,
)


def _at(year: int, month: int, day: int, hour: int = 10) -> datetime:
    return datetime(year, month, day, hour, 0, tzinfo=KST)


def _breaker(tmp_path: Path, *, verified: bool = False, **limits) -> DailyEntryBreaker:
    """Build a breaker. `verified=True` is the operator acknowledgement.

    Defaulting to False keeps every test honest about which behaviour it is
    exercising: the loss limits do nothing until someone opts in, exactly as
    in production.
    """

    return DailyEntryBreaker(
        DailyRiskLimits(loss_source_verified=verified, **limits),
        state_path=tmp_path / "daily_risk_state.json",
        now=_at(2026, 7, 27),
    )


def _verified_limits(**kwargs) -> DailyRiskLimits:
    """Limits with the daily-loss source explicitly acknowledged."""

    return DailyRiskLimits(loss_source_verified=True, **kwargs)


# -- account adapter -------------------------------------------------------


def test_reads_daily_pl_from_the_documented_field():
    """`tdy_lspft` is 당일투자손익; `tdy_lspft_amt` is principal, not P&L."""

    snapshot = read_account_daily_snapshot(
        {
            "daily_pl_krw": -12_000,
            "estimated_assets": 1_000_000,
            "daily_pl_pct_broker": -4.8,
        }
    )

    assert snapshot.valid is True
    assert snapshot.daily_pl_krw == -12_000
    assert snapshot.loss_krw == 12_000
    assert snapshot.loss_pct == 1.2  # 12k of a 1M account, not of the principal
    # The broker's own rate is carried for cross-checking but not used for
    # any threshold — its denominator is today's invested principal.
    assert snapshot.broker_daily_pl_pct == -4.8


def test_profit_is_not_a_loss():
    snapshot = read_account_daily_snapshot(
        {"daily_pl_krw": 8_000, "estimated_assets": 1_000_000}
    )

    assert snapshot.valid is True
    assert snapshot.loss_krw == 0
    assert snapshot.loss_pct == 0.0


def test_missing_daily_pl_is_invalid_not_zero():
    """A silent zero would read as "flat day, keep trading"."""

    snapshot = read_account_daily_snapshot({"estimated_assets": 1_000_000})

    assert snapshot.valid is False
    assert snapshot.daily_pl_krw is None
    assert snapshot.loss_krw is None
    assert snapshot.loss_pct is None
    assert "tdy_lspft" in (snapshot.reason or "")


def test_missing_total_assets_keeps_the_krw_figure():
    """Losing the denominator must not lose the KRW reading with it."""

    snapshot = read_account_daily_snapshot(
        {"daily_pl_krw": -5_000, "estimated_assets": 0}
    )

    assert snapshot.valid is False
    assert snapshot.loss_krw == 5_000  # KRW limit can still be judged
    assert snapshot.loss_pct is None  # pct limit cannot


def test_adapter_parses_kiwoom_string_numerics():
    snapshot = read_account_daily_snapshot(
        {"daily_pl_krw": "-12,000", "estimated_assets": "1000000"}
    )

    assert snapshot.daily_pl_krw == -12_000
    assert snapshot.total_assets_krw == 1_000_000


def test_garbage_portfolio_is_invalid():
    assert read_account_daily_snapshot(None).valid is False
    assert read_account_daily_snapshot("nope").valid is False


# -- disabled by default ---------------------------------------------------


def test_disabled_by_default_allows_everything(tmp_path):
    breaker = _breaker(tmp_path)

    assert breaker.enabled is False
    assert breaker.check_new_entry().allowed is True
    # Even with no account data at all — a disabled breaker never fails closed.
    breaker.observe(AccountDailySnapshot(valid=False, reason="no data"))
    assert breaker.check_new_entry().allowed is True
    # And it never writes state for a feature nobody turned on.
    assert not (tmp_path / "daily_risk_state.json").exists()


# -- KRW loss limit --------------------------------------------------------


def test_buy_allowed_below_the_krw_threshold(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_krw=50_000)

    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -49_999, "estimated_assets": 1_000_000}
        )
    )

    assert breaker.tripped is False
    assert breaker.check_new_entry().allowed is True


def test_buy_blocked_at_the_krw_threshold(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_krw=50_000)

    tripped = breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -50_000, "estimated_assets": 1_000_000}
        )
    )

    assert tripped is not None
    assert tripped.code == BLOCK_DAILY_LOSS_KRW
    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_DAILY_LOSS_KRW


def test_a_trip_does_not_clear_when_the_loss_recovers(tmp_path):
    """A breach means the day's assumptions were wrong, not that the next
    tick is trustworthy."""

    breaker = _breaker(tmp_path, verified=True, max_daily_loss_krw=50_000)
    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    assert breaker.tripped is True

    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": 20_000, "estimated_assets": 1_000_000}
        )
    )

    assert breaker.tripped is True
    assert breaker.check_new_entry().allowed is False


# -- percent loss limit ----------------------------------------------------


def test_buy_allowed_below_the_pct_threshold(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0)

    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -29_000, "estimated_assets": 1_000_000}  # 2.9%
        )
    )

    assert breaker.check_new_entry().allowed is True


def test_buy_blocked_at_the_pct_threshold(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0)

    tripped = breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -30_000, "estimated_assets": 1_000_000}  # 3.0%
        )
    )

    assert tripped is not None
    assert tripped.code == BLOCK_DAILY_LOSS_PCT
    assert breaker.check_new_entry().allowed is False
    assert breaker.state.observed_value == 3.0
    assert breaker.state.limit_value == 3.0


def test_pct_uses_account_assets_not_the_broker_rate(tmp_path):
    """The broker's 당일손익율 divides by today's invested principal, which
    for a partially-deployed account trips at a far smaller real drawdown."""

    breaker = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0)

    breaker.observe(
        read_account_daily_snapshot(
            {
                "daily_pl_krw": -10_000,
                "estimated_assets": 1_000_000,  # 1.0% of the account
                "daily_pl_pct_broker": -25.0,  # 25% of the deployed principal
            }
        )
    )

    assert breaker.tripped is False  # judged on 1.0%, not on -25.0
    assert breaker.check_new_entry().allowed is True


# -- new-entry count limit -------------------------------------------------


def test_new_entry_count_limit_latches(tmp_path):
    breaker = _breaker(tmp_path, max_daily_new_entries=2)

    assert breaker.check_new_entry().allowed is True
    breaker.record_new_entry()
    assert breaker.check_new_entry().allowed is True
    breaker.record_new_entry()

    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_MAX_NEW_ENTRIES
    assert breaker.state.new_entries == 2


def test_entry_count_limit_does_not_need_account_data(tmp_path):
    """A count-only setup has nothing to fail closed about."""

    breaker = _breaker(tmp_path, max_daily_new_entries=2)
    breaker.observe(AccountDailySnapshot(valid=False, reason="no data"))

    assert breaker.check_new_entry().allowed is True


# -- fail-closed on missing/invalid account data ---------------------------


def test_missing_account_snapshot_blocks_new_buys(tmp_path):
    """Never observed yet + a loss limit armed = we cannot prove we are safe."""

    breaker = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0)

    decision = breaker.check_new_entry()

    assert decision.allowed is False
    assert decision.code == BLOCK_ACCOUNT_DATA
    # ...and it is NOT latched: a bad poll must not cost the session.
    assert breaker.tripped is False


def test_invalid_account_data_blocks_new_buys_then_recovers(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0)

    breaker.observe(read_account_daily_snapshot({"estimated_assets": 1_000_000}))
    assert breaker.check_new_entry().allowed is False
    assert breaker.tripped is False  # transient, not latched

    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -1_000, "estimated_assets": 1_000_000}
        )
    )
    assert breaker.check_new_entry().allowed is True


def test_krw_limit_still_judges_without_the_denominator(tmp_path):
    """Only the pct limit needs total assets; don't block what we can judge."""

    breaker = _breaker(tmp_path, verified=True, max_daily_loss_krw=50_000)

    breaker.observe(
        read_account_daily_snapshot({"daily_pl_krw": -1_000, "estimated_assets": 0})
    )

    assert breaker.check_new_entry().allowed is True

    breaker.observe(
        read_account_daily_snapshot({"daily_pl_krw": -80_000, "estimated_assets": 0})
    )
    assert breaker.tripped is True


def test_pct_limit_fails_closed_without_the_denominator(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0)

    breaker.observe(
        read_account_daily_snapshot({"daily_pl_krw": -1_000, "estimated_assets": 0})
    )

    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_ACCOUNT_DATA


# -- restart durability ----------------------------------------------------


def test_latch_survives_a_restart_on_the_same_trading_day(tmp_path):
    state_path = tmp_path / "daily_risk_state.json"
    limits = _verified_limits(max_daily_loss_krw=50_000)

    first = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 27, 10))
    first.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    assert first.tripped is True

    # Process dies, comes back the same trading day.
    restarted = DailyEntryBreaker(
        limits, state_path=state_path, now=_at(2026, 7, 27, 14)
    )

    assert restarted.tripped is True
    decision = restarted.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_DAILY_LOSS_KRW
    # The original reason and timestamp survive, not a regenerated one.
    assert restarted.state.observed_value == 60_000.0
    assert restarted.state.tripped_at == first.state.tripped_at


def test_entry_count_survives_a_restart(tmp_path):
    state_path = tmp_path / "daily_risk_state.json"
    limits = DailyRiskLimits(max_daily_new_entries=2)

    first = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 27))
    first.record_new_entry()

    restarted = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 27))

    assert restarted.state.new_entries == 1
    assert restarted.check_new_entry().allowed is True
    restarted.record_new_entry()
    assert restarted.check_new_entry().allowed is False


def test_next_trading_day_restart_starts_clean(tmp_path):
    state_path = tmp_path / "daily_risk_state.json"
    limits = _verified_limits(max_daily_loss_krw=50_000)

    first = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 27))
    first.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    assert first.tripped is True

    tomorrow = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 28))

    assert tomorrow.tripped is False
    # A loss limit is armed and no snapshot has arrived yet, so the first
    # check still fails closed — but for "no data", not for yesterday's latch.
    assert tomorrow.check_new_entry().code == BLOCK_ACCOUNT_DATA
    tomorrow.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -100, "estimated_assets": 1_000_000}
        )
    )
    assert tomorrow.check_new_entry().allowed is True


def test_roll_day_resets_a_running_process(tmp_path):
    """The watcher sleeps through the close; the roll is the day reset."""

    breaker = _breaker(tmp_path, verified=True, max_daily_loss_krw=50_000)
    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    breaker.record_new_entry()
    assert breaker.tripped is True

    assert breaker.roll_day(now=_at(2026, 7, 27, 15)) is False  # same day
    assert breaker.tripped is True

    assert breaker.roll_day(now=_at(2026, 7, 28, 9)) is True
    assert breaker.tripped is False
    assert breaker.state.new_entries == 0
    assert breaker.state.trading_day == "2026-07-28"


def test_corrupt_state_file_fails_new_buys_closed(tmp_path):
    """We cannot tell whether that file was holding a latch, so assume it was.

    Starting clean would silently resume buying after exactly the kind of
    disk problem that could have eaten a trip.
    """

    state_path = tmp_path / "daily_risk_state.json"
    state_path.write_text("{not json", encoding="utf-8")

    breaker = DailyEntryBreaker(
        DailyRiskLimits(max_daily_new_entries=2),
        state_path=state_path,
        now=_at(2026, 7, 27),
    )

    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_STATE_UNAVAILABLE
    assert "매도/취소는 허용" in (decision.reason or "")
    # It is a block, not a latched trip: the cause is the file, not the market.
    assert breaker.tripped is False
    assert breaker.to_dict()["state_error"]


def test_unparseable_trading_day_fails_new_buys_closed(tmp_path):
    """A state we cannot age out is a state we cannot trust."""

    state_path = tmp_path / "daily_risk_state.json"
    state_path.write_text(
        json.dumps({"trading_day": "yesterday", "tripped": True}), encoding="utf-8"
    )

    breaker = DailyEntryBreaker(
        DailyRiskLimits(max_daily_new_entries=2),
        state_path=state_path,
        now=_at(2026, 7, 27),
    )

    assert breaker.check_new_entry().code == BLOCK_STATE_UNAVAILABLE


def test_corrupt_state_clears_on_the_next_trading_day(tmp_path):
    """Automatic recovery, but only once any same-day latch would have expired."""

    state_path = tmp_path / "daily_risk_state.json"
    state_path.write_text("{not json", encoding="utf-8")
    breaker = DailyEntryBreaker(
        DailyRiskLimits(max_daily_new_entries=2),
        state_path=state_path,
        now=_at(2026, 7, 27),
    )
    assert breaker.check_new_entry().code == BLOCK_STATE_UNAVAILABLE

    # Same day: still blocked, no silent recovery.
    assert breaker.roll_day(now=_at(2026, 7, 27, 15)) is False
    assert breaker.check_new_entry().code == BLOCK_STATE_UNAVAILABLE

    # Next trading day: a good write replaces the bad file and clears it.
    assert breaker.roll_day(now=_at(2026, 7, 28, 9)) is True
    assert breaker.check_new_entry().allowed is True
    assert breaker.to_dict()["state_error"] is None


def test_disabled_breaker_ignores_a_corrupt_state_file(tmp_path):
    """A feature nobody turned on must not start blocking buys."""

    state_path = tmp_path / "daily_risk_state.json"
    state_path.write_text("{not json", encoding="utf-8")

    breaker = DailyEntryBreaker(
        DailyRiskLimits(), state_path=state_path, now=_at(2026, 7, 27)
    )

    assert breaker.check_new_entry().allowed is True


def test_failed_latch_persist_fails_new_buys_closed(tmp_path, monkeypatch):
    """An un-durable latch is a latch a pod restart would silently undo."""

    state_path = tmp_path / "daily_risk_state.json"
    breaker = DailyEntryBreaker(
        DailyRiskLimits(max_daily_new_entries=5),
        state_path=state_path,
        now=_at(2026, 7, 27),
    )
    assert breaker.check_new_entry().allowed is True

    def boom(*args, **kwargs):
        raise OSError("read-only filesystem")

    monkeypatch.setattr(Path, "write_text", boom)
    breaker.record_new_entry()  # the count could not be made durable

    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_STATE_UNAVAILABLE
    assert "상태 저장 실패" in (decision.reason or "")

    # Recovers as soon as a write lands again.
    monkeypatch.undo()
    breaker.record_new_entry()
    assert breaker.check_new_entry().allowed is True


def test_failed_persist_does_not_block_when_disabled(tmp_path, monkeypatch):
    breaker = DailyEntryBreaker(
        DailyRiskLimits(),
        state_path=tmp_path / "daily_risk_state.json",
        now=_at(2026, 7, 27),
    )

    def boom(*args, **kwargs):
        raise OSError("read-only filesystem")

    monkeypatch.setattr(Path, "write_text", boom)
    breaker.record_new_entry()

    assert breaker.check_new_entry().allowed is True


def test_persisted_state_is_written_atomically(tmp_path):
    state_path = tmp_path / "daily_risk_state.json"
    breaker = DailyEntryBreaker(
        _verified_limits(max_daily_loss_krw=10),
        state_path=state_path,
        now=_at(2026, 7, 27),
    )
    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -20, "estimated_assets": 1_000_000}
        )
    )

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["tripped"] is True
    assert payload["trip_code"] == BLOCK_DAILY_LOSS_KRW
    assert payload["trading_day"] == "2026-07-27"
    # No half-written temp file left behind.
    assert not (tmp_path / "daily_risk_state.tmp").exists()


# -- observability ---------------------------------------------------------


def test_state_payload_exposes_reason_limit_observed_and_time(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0)
    breaker.observe(
        read_account_daily_snapshot(
            {
                "daily_pl_krw": -40_000,
                "estimated_assets": 1_000_000,
                "daily_pl_pct_broker": -9.9,
            }
        ),
        now=_at(2026, 7, 27, 11),
    )

    payload = breaker.to_dict()

    assert payload["enabled"] is True
    assert payload["tripped"] is True
    assert payload["trip_code"] == BLOCK_DAILY_LOSS_PCT
    assert payload["limit_value"] == 3.0
    assert payload["observed_value"] == 4.0
    assert payload["tripped_at"] == _at(2026, 7, 27, 11).isoformat()
    assert payload["trading_day"] == "2026-07-27"
    assert payload["resets_on"] == "2026-07-28"
    assert payload["limits"]["max_daily_loss_pct"] == 3.0
    # The broker's own rate rides along for cross-checking.
    assert payload["account"]["broker_daily_pl_pct"] == -9.9
    assert payload["account"]["loss_pct"] == 4.0


# -- calendar helpers ------------------------------------------------------


def test_next_trading_day_skips_the_weekend():
    # 2026-07-31 is a Friday.
    assert next_trading_day(date(2026, 7, 31)) == date(2026, 8, 3)


def test_current_trading_day_is_kst():
    # 2026-07-27 23:30 UTC is already the 28th in Seoul.
    utc_late = datetime.fromisoformat("2026-07-27T23:30:00+00:00")
    assert current_trading_day(utc_late) == date(2026, 7, 28)


# -- weekend / holiday latch preservation (review correction) --------------
#
# The reset keys on reaching the next KRX *trading* day, not on the calendar
# date changing. Those differ across every weekend and holiday, and the
# difference is a dropped latch.


def test_should_reset_only_once_the_next_trading_day_is_reached():
    friday = date(2026, 7, 31)

    assert should_reset(friday, date(2026, 7, 31)) is False  # same day
    assert should_reset(friday, date(2026, 8, 1)) is False  # Sat
    assert should_reset(friday, date(2026, 8, 2)) is False  # Sun
    assert should_reset(friday, date(2026, 8, 3)) is True  # Mon — open

    # 2026-08-17 is a 광복절 substitute holiday, so a Friday latch has to
    # survive a three-day close.
    aug14 = date(2026, 8, 14)
    assert should_reset(aug14, date(2026, 8, 17)) is False  # closed Monday
    assert should_reset(aug14, date(2026, 8, 18)) is True

    # Clock skew into the future never resets — the conservative direction.
    assert should_reset(date(2026, 9, 1), date(2026, 7, 31)) is False


def test_saturday_restart_preserves_a_friday_latch(tmp_path):
    state_path = tmp_path / "daily_risk_state.json"
    limits = _verified_limits(max_daily_loss_krw=50_000)

    friday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 31, 14))
    friday.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    assert friday.tripped is True

    # Pod restarts over the weekend (rollout, node reboot).
    saturday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 8, 1, 10))

    assert saturday.tripped is True
    assert saturday.check_new_entry().allowed is False
    # The latch still belongs to Friday, not to Saturday.
    assert saturday.state.trading_day == "2026-07-31"
    assert saturday.state.tripped_at == friday.state.tripped_at


def test_weekend_state_payload_still_reports_the_latch(tmp_path):
    """`/state` on a Saturday must not look like a clean breaker."""

    state_path = tmp_path / "daily_risk_state.json"
    limits = _verified_limits(max_daily_loss_krw=50_000)

    friday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 31, 14))
    friday.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )

    sunday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 8, 2, 10))
    payload = sunday.to_dict()

    assert payload["tripped"] is True
    assert payload["trip_code"] == BLOCK_DAILY_LOSS_KRW
    assert payload["trading_day"] == "2026-07-31"
    assert payload["resets_on"] == "2026-08-03"


def test_holiday_restart_preserves_the_latch(tmp_path):
    """2026-08-17 is a substitute holiday — a Friday latch spans three days."""

    state_path = tmp_path / "daily_risk_state.json"
    limits = _verified_limits(max_daily_loss_krw=50_000)

    DailyEntryBreaker(
        limits, state_path=state_path, now=_at(2026, 8, 14, 14)
    ).observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )

    holiday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 8, 17, 10))
    assert holiday.tripped is True
    assert holiday.to_dict()["resets_on"] == "2026-08-18"

    reopened = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 8, 18, 9))
    assert reopened.tripped is False
    assert reopened.state.trading_day == "2026-08-18"


def test_weekend_restart_preserves_the_new_entry_count(tmp_path):
    """The daily entry budget must not be refilled by a Saturday reboot."""

    state_path = tmp_path / "daily_risk_state.json"
    limits = DailyRiskLimits(max_daily_new_entries=2)

    friday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 7, 31, 10))
    friday.record_new_entry()
    friday.record_new_entry()
    assert friday.check_new_entry().allowed is False

    saturday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 8, 1, 10))
    assert saturday.state.new_entries == 2
    assert saturday.check_new_entry().allowed is False

    monday = DailyEntryBreaker(limits, state_path=state_path, now=_at(2026, 8, 3, 9))
    assert monday.state.new_entries == 0
    assert monday.check_new_entry().allowed is True


def test_roll_day_does_not_reset_over_a_weekend(tmp_path):
    """A long-running process sleeping through the close behaves the same."""

    breaker = _breaker(tmp_path, verified=True, max_daily_loss_krw=50_000)
    breaker._state.trading_day = "2026-07-31"
    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    assert breaker.tripped is True

    assert breaker.roll_day(now=_at(2026, 8, 1, 10)) is False  # Sat
    assert breaker.roll_day(now=_at(2026, 8, 2, 10)) is False  # Sun
    assert breaker.tripped is True

    assert breaker.roll_day(now=_at(2026, 8, 3, 9)) is True  # Mon
    assert breaker.tripped is False


# -- loss-source verification (second review correction) -------------------
#
# `tdy_lspft` parses as a number, but what it counts is undocumented. A
# below-threshold reading from a source that might exclude unrealized P&L is
# not evidence of a safe account, so an armed loss limit does not enforce a
# threshold until an operator says the source has been validated live.


def test_below_threshold_loss_still_blocks_while_unverified(tmp_path):
    """The core of the decision: syntactically valid ≠ semantically valid."""

    breaker = _breaker(tmp_path, max_daily_loss_krw=50_000)  # NOT verified

    # A perfectly parseable reading, nowhere near the limit.
    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -1_000, "estimated_assets": 1_000_000}
        )
    )

    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_LOSS_SOURCE_UNVERIFIED
    assert "매도/취소는 허용" in (decision.reason or "")
    # Not a latched trip — the market did nothing wrong, the metadata did.
    assert breaker.tripped is False


def test_pct_limit_also_blocks_while_unverified(tmp_path):
    breaker = _breaker(tmp_path, max_daily_loss_pct=3.0)
    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -1_000, "estimated_assets": 1_000_000}  # 0.1%
        )
    )

    assert breaker.check_new_entry().code == BLOCK_LOSS_SOURCE_UNVERIFIED


def test_profitable_day_still_blocks_while_unverified(tmp_path):
    """Even an apparent gain proves nothing if the field may omit unrealized."""

    breaker = _breaker(tmp_path, max_daily_loss_krw=50_000)
    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": 100_000, "estimated_assets": 1_000_000}
        )
    )

    assert breaker.check_new_entry().code == BLOCK_LOSS_SOURCE_UNVERIFIED


def test_unverified_breaker_does_not_latch_on_the_loss_figure(tmp_path):
    """Don't record a trip reason we cannot stand behind."""

    breaker = _breaker(tmp_path, max_daily_loss_krw=50_000)

    tripped = breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -900_000, "estimated_assets": 1_000_000}  # way over
        )
    )

    assert tripped is None
    assert breaker.tripped is False
    assert breaker.state.trip_code is None
    # ...but the reading is still published, because that is the raw material
    # an operator needs to actually do the validation.
    assert breaker.to_dict()["account"]["daily_pl_krw"] == -900_000


def test_count_only_limit_is_fully_usable_while_unverified(tmp_path):
    """`max_daily_new_entries` counts our own orders — no broker P&L needed."""

    breaker = _breaker(tmp_path, max_daily_new_entries=2)

    assert breaker.limits.loss_source_unverified is False
    assert breaker.check_new_entry().allowed is True
    breaker.record_new_entry()
    assert breaker.check_new_entry().allowed is True
    breaker.record_new_entry()

    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_MAX_NEW_ENTRIES  # its own limit, not the gate


def test_mixed_limits_still_latch_the_entry_count_while_unverified(tmp_path):
    """An unverified loss limit must not swallow the count limit's latch."""

    breaker = _breaker(tmp_path, max_daily_loss_krw=50_000, max_daily_new_entries=1)

    assert breaker.check_new_entry().code == BLOCK_LOSS_SOURCE_UNVERIFIED
    breaker.record_new_entry()

    # The count limit is checked first and latches durably, so the recorded
    # reason is the real one rather than the metadata caveat.
    decision = breaker.check_new_entry()
    assert decision.code == BLOCK_MAX_NEW_ENTRIES
    assert breaker.tripped is True


def test_verified_mode_restores_threshold_behaviour(tmp_path):
    breaker = _breaker(tmp_path, verified=True, max_daily_loss_krw=50_000)

    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -1_000, "estimated_assets": 1_000_000}
        )
    )
    assert breaker.check_new_entry().allowed is True  # below threshold: allowed

    breaker.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    decision = breaker.check_new_entry()
    assert decision.allowed is False
    assert decision.code == BLOCK_DAILY_LOSS_KRW  # the real reason, not the gate
    assert breaker.tripped is True


def test_verification_defaults_to_false():
    """The acknowledgement must never be a default or an inference."""

    assert DailyRiskLimits().loss_source_verified is False
    assert DailyRiskLimits(max_daily_loss_krw=1).loss_source_verified is False
    assert DailyRiskLimits(max_daily_loss_pct=1.0).loss_source_unverified is True
    # A count-only setup has no loss source to verify.
    assert DailyRiskLimits(max_daily_new_entries=1).loss_source_unverified is False


def test_state_payload_reports_verification_status(tmp_path):
    unverified = _breaker(tmp_path, max_daily_loss_pct=3.0).to_dict()
    assert unverified["loss_source_status"] == "unverified"
    assert unverified["loss_limits_enforced"] is False
    assert unverified["limits"]["loss_source_verified"] is False

    verified = _breaker(tmp_path, verified=True, max_daily_loss_pct=3.0).to_dict()
    assert verified["loss_source_status"] == "verified"
    assert verified["loss_limits_enforced"] is True

    count_only = _breaker(tmp_path, max_daily_new_entries=2).to_dict()
    assert count_only["loss_source_status"] == "n/a"
    assert count_only["loss_limits_enforced"] is False


def test_disabled_breaker_is_unaffected_by_verification(tmp_path):
    breaker = _breaker(tmp_path)  # no limits at all

    assert breaker.check_new_entry().allowed is True
    assert breaker.to_dict()["loss_source_status"] == "n/a"


# -- unsupported years / uncertain special sessions -----------------------


def test_unsupported_year_never_becomes_an_implicit_trading_day(tmp_path):
    breaker = DailyEntryBreaker(
        DailyRiskLimits(),
        state_path=tmp_path / "daily_risk_state.json",
        now=_at(2027, 1, 4),
    )

    decision = breaker.check_new_entry()

    assert breaker.enabled is False  # calendar gate is independent of limits
    assert decision.allowed is False
    assert decision.code == BLOCK_CALENDAR_UNCERTAIN
    payload = breaker.to_dict()
    assert payload["calendar"]["state"] == "uncertain"
    assert payload["calendar"]["supported"] is False
    assert payload["calendar"]["observed_at"] == _at(2027, 1, 4).isoformat()


def test_year_boundary_without_calendar_preserves_latch_on_restart(tmp_path):
    state_path = tmp_path / "daily_risk_state.json"
    limits = _verified_limits(max_daily_loss_krw=50_000)
    latched = DailyEntryBreaker(
        limits,
        state_path=state_path,
        now=_at(2026, 12, 30, 14),
    )
    latched.observe(
        read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        ),
        now=_at(2026, 12, 30, 14),
    )

    assert latched.tripped is True
    assert next_trading_day(date(2026, 12, 30)) is None
    assert should_reset(date(2026, 12, 30), date(2027, 1, 4)) is False

    restarted = DailyEntryBreaker(
        limits,
        state_path=state_path,
        now=_at(2027, 1, 4),
    )
    assert restarted.tripped is True
    assert restarted.state.trading_day == "2026-12-30"
    assert restarted.roll_day(_at(2027, 2, 1)) is False

    payload = restarted.to_dict()
    assert payload["trip_code"] == BLOCK_DAILY_LOSS_KRW
    assert payload["resets_on"] is None
    assert payload["reset_schedule"]["exact"] is False
    assert "unsupported" in payload["reset_schedule"]["reason"]
    assert payload["calendar"]["state"] == "uncertain"


def test_uncertain_special_session_delays_reset_to_next_definite_day(tmp_path):
    schedule = next_trading_day_status(date(2026, 11, 18))
    assert schedule.resets_on == date(2026, 11, 20)
    assert schedule.exact is False
    assert schedule.uncertain_dates == (date(2026, 11, 19),)

    state_path = tmp_path / "daily_risk_state.json"
    limits = DailyRiskLimits(max_daily_new_entries=1)
    before = DailyEntryBreaker(
        limits,
        state_path=state_path,
        now=_at(2026, 11, 18, 14),
    )
    before.record_new_entry()
    assert before.check_new_entry().allowed is False

    uncertain = DailyEntryBreaker(
        limits,
        state_path=state_path,
        now=_at(2026, 11, 19),
    )
    assert uncertain.tripped is True
    assert uncertain.to_dict()["resets_on"] == "2026-11-20"
    assert uncertain.to_dict()["reset_schedule"]["exact"] is False
    assert uncertain.to_dict()["calendar"]["state"] == "uncertain"

    after = DailyEntryBreaker(
        limits,
        state_path=state_path,
        now=_at(2026, 11, 20),
    )
    assert after.tripped is False
    assert after.state.new_entries == 0
