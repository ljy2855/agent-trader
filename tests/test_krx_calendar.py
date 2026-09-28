from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import Settings
from src.services.krx_calendar import (
    DAY_UNCERTAIN,
    SESSION_UNCERTAIN,
    SUPPORTED_KRX_CALENDAR_YEARS,
    is_krx_regular_session_open,
    is_krx_trading_day,
    krx_day_status,
    krx_regular_session_status,
    market_holiday_name,
)
from src.services.order_ledger import OrderLedger
from src.services.watcher import WatcherConfig, IntradayWatcher
from src.trade_engine import (
    CALENDAR_PROTECTIVE_ONLY,
    _calendar_cycle_mode,
)

KST = ZoneInfo("Asia/Seoul")


class StubNotifier:
    async def info(self, title: str, description: str) -> None:
        pass

    async def success(self, title: str, description: str) -> None:
        pass

    async def warn(self, title: str, description: str) -> None:
        pass

    async def error(self, title: str, description: str) -> None:
        pass


def _settings() -> Settings:
    return Settings(
        KIWOOM_USE_MOCK="true",
        KIWOOM_MOCK_APPKEY="mock-key",
        KIWOOM_MOCK_SECRETKEY="mock-secret",
    )


def test_childrens_day_2026_is_non_trading_day():
    day = datetime(2026, 5, 5, 10, 0, tzinfo=KST)

    assert market_holiday_name(day) == "어린이날"
    assert not is_krx_trading_day(day)
    assert not is_krx_regular_session_open(day)


def test_regular_weekday_session_is_open():
    assert is_krx_regular_session_open(datetime(2026, 5, 4, 10, 0, tzinfo=KST))


def test_substitute_and_election_holidays_are_closed():
    assert not is_krx_regular_session_open(datetime(2026, 5, 25, 10, 0, tzinfo=KST))
    assert not is_krx_regular_session_open(datetime(2026, 6, 3, 10, 0, tzinfo=KST))


def test_2026_year_end_closure_is_explicit():
    assert market_holiday_name(date(2026, 12, 31)) == "연말 휴장일"
    assert not is_krx_trading_day(date(2026, 12, 31))


def test_supported_years_are_explicit_and_unsupported_weekday_is_uncertain():
    assert SUPPORTED_KRX_CALENDAR_YEARS == frozenset({2026})

    day = date(2027, 1, 4)  # Monday, but no reviewed 2027 KRX calendar.
    status = krx_day_status(day)
    session = krx_regular_session_status(
        datetime(2027, 1, 4, 10, 0, tzinfo=KST)
    )

    assert status.state == DAY_UNCERTAIN
    assert status.supported is False
    assert "unsupported" in status.reason
    assert is_krx_trading_day(day) is False
    assert session.state == SESSION_UNCERTAIN
    assert is_krx_regular_session_open(session.observed_at) is False


def test_confirmed_2026_new_year_special_session_uses_delayed_open():
    assert not is_krx_regular_session_open(
        datetime(2026, 1, 2, 9, 30, tzinfo=KST)
    )
    assert is_krx_regular_session_open(
        datetime(2026, 1, 2, 10, 0, tzinfo=KST)
    )


def test_unverified_special_session_is_uncertain_not_regular_open():
    at = datetime(2026, 11, 19, 10, 0, tzinfo=KST)
    status = krx_regular_session_status(at)

    assert status.state == SESSION_UNCERTAIN
    assert status.day_status.supported is True
    assert "공식 검증 대기" in status.reason
    assert not is_krx_regular_session_open(at)


def test_watcher_market_open_uses_krx_holiday_calendar():
    watcher = IntradayWatcher(
        _settings(),
        WatcherConfig(),
        dispatcher=object(),  # type: ignore[arg-type]
        client=object(),
        notifier=StubNotifier(),  # type: ignore[arg-type]
        ledger=OrderLedger(None),  # in-memory; keep the repo's output/ clean
    )

    assert not watcher._is_market_open(datetime(2026, 5, 5, 10, 0, tzinfo=KST))
    assert watcher._is_market_open(datetime(2026, 5, 4, 10, 0, tzinfo=KST))


def test_calendar_uncertainty_keeps_protective_cycles_alive_but_not_open():
    watcher = IntradayWatcher(
        _settings(),
        WatcherConfig(),
        dispatcher=object(),  # type: ignore[arg-type]
        client=object(),
        notifier=StubNotifier(),  # type: ignore[arg-type]
        ledger=OrderLedger(None),
    )
    unsupported = datetime(2027, 1, 4, 10, 0, tzinfo=KST)

    assert watcher._is_market_open(unsupported) is False
    assert watcher._should_run_tick(unsupported) is True
    assert _calendar_cycle_mode(unsupported) == CALENDAR_PROTECTIVE_ONLY
