"""Explicit, fail-closed KRX regular-session calendar.

The trading loops must not rely on weekday + clock checks alone: Korean
public holidays, substitute holidays, election days, KRX-specific closures,
and special sessions vary by year.  A weekday outside
``SUPPORTED_KRX_CALENDAR_YEARS`` is therefore *uncertain*, never implicitly a
trading day.

Calendar uncertainty is intentionally distinct from a known market close.
Callers that can open exposure must require ``SESSION_OPEN``.  Safety loops
may continue on ``SESSION_UNCERTAIN`` so protective sells and cancels are not
disabled by incomplete calendar data.  See ``docs/krx-calendar-maintenance.md``
before adding another supported year; official data is reviewed and entered
manually, not fetched at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

DAY_TRADING = "trading"
DAY_CLOSED = "closed"
DAY_UNCERTAIN = "uncertain"

SESSION_OPEN = "open"
SESSION_CLOSED = "closed"
SESSION_UNCERTAIN = "uncertain"

# A year is added only after its weekday holidays, year-end closure and
# announced special sessions have passed the documented annual review.
SUPPORTED_KRX_CALENDAR_YEARS = frozenset({2026})


@dataclass(frozen=True, slots=True)
class KrxDayStatus:
    """Whether a KST calendar date is definitely trading, closed, or unknown."""

    day: date
    state: str
    reason: str

    @property
    def supported(self) -> bool:
        return self.day.year in SUPPORTED_KRX_CALENDAR_YEARS

    @property
    def is_trading_day(self) -> bool:
        return self.state == DAY_TRADING

    def to_dict(self) -> dict[str, str | int | bool]:
        return {
            "date": self.day.isoformat(),
            "year": self.day.year,
            "state": self.state,
            "supported": self.supported,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class KrxSessionStatus:
    """Regular-session verdict at one KST observation time."""

    observed_at: datetime
    state: str
    reason: str
    day_status: KrxDayStatus
    opens_at: time | None = None
    closes_at: time | None = None

    @property
    def is_open(self) -> bool:
        return self.state == SESSION_OPEN

    @property
    def uncertain(self) -> bool:
        return self.state == SESSION_UNCERTAIN

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "state": self.state,
            "supported": self.day_status.supported,
            "reason": self.reason,
            "opens_at": self.opens_at.isoformat() if self.opens_at else None,
            "closes_at": self.closes_at.isoformat() if self.closes_at else None,
        }


@dataclass(frozen=True, slots=True)
class KrxSessionHours:
    opens_at: time
    closes_at: time
    reason: str


# Explicit KRX non-trading weekdays. Weekends are handled separately.
# Keep this table year-scoped because Lunar New Year, Chuseok, Buddha's
# Birthday, substitute holidays, election days, and temporary holidays vary
# by year.
KRX_WEEKDAY_HOLIDAYS: dict[date, str] = {
    # 2026 Korean public holidays / substitute holidays / KRX closures.
    date(2026, 1, 1): "신정",
    date(2026, 2, 16): "설날 연휴",
    date(2026, 2, 17): "설날",
    date(2026, 2, 18): "설날 연휴",
    date(2026, 3, 2): "삼일절 대체공휴일",
    date(2026, 5, 1): "근로자의 날",
    date(2026, 5, 5): "어린이날",
    date(2026, 5, 25): "부처님오신날 대체공휴일",
    date(2026, 6, 3): "제9회 전국동시지방선거",
    date(2026, 8, 17): "광복절 대체공휴일",
    date(2026, 9, 24): "추석 연휴",
    date(2026, 9, 25): "추석",
    date(2026, 10, 5): "개천절 대체공휴일",
    date(2026, 10, 9): "한글날",
    date(2026, 12, 25): "기독탄신일",
    date(2026, 12, 31): "연말 휴장일",
}

# Confirmed departures from the normal 09:00-15:30 regular session.
KRX_SPECIAL_SESSIONS: dict[date, KrxSessionHours] = {
    date(2026, 1, 2): KrxSessionHours(
        time(10, 0),
        time(15, 30),
        "2026년 증권시장 개장식 — 정규장 1시간 지연",
    ),
}

# A date goes here as soon as a likely special schedule is known but before
# KRX has published/verified the exact stock regular-session hours. It is
# removed only when moved to KRX_SPECIAL_SESSIONS or confirmed regular.
KRX_UNCERTAIN_SESSION_DATES: dict[date, str] = {
    date(2026, 11, 19): (
        "2027학년도 대학수학능력시험일 — KRX 정규장 시간 공식 검증 대기"
    ),
}


def market_holiday_name(day: date | datetime) -> str | None:
    """Return a known non-trading-day label, not an uncertainty label."""

    current = day.date() if isinstance(day, datetime) else day
    if current.weekday() >= 5:
        return "주말"
    return KRX_WEEKDAY_HOLIDAYS.get(current)


def krx_day_status(day: date | datetime) -> KrxDayStatus:
    """Return the supported/closed/uncertain verdict for ``day``."""

    current = day.date() if isinstance(day, datetime) else day
    holiday = market_holiday_name(current)
    if holiday is not None:
        return KrxDayStatus(current, DAY_CLOSED, holiday)
    if current.year not in SUPPORTED_KRX_CALENDAR_YEARS:
        return KrxDayStatus(
            current,
            DAY_UNCERTAIN,
            f"KRX calendar year {current.year} is unsupported",
        )
    uncertain = KRX_UNCERTAIN_SESSION_DATES.get(current)
    if uncertain is not None:
        return KrxDayStatus(current, DAY_UNCERTAIN, uncertain)
    return KrxDayStatus(current, DAY_TRADING, "verified KRX trading day")


def is_krx_trading_day(day: date | datetime) -> bool:
    """Return True only for a definitely supported KRX trading day."""

    return krx_day_status(day).is_trading_day


def _as_kst(now: datetime | None = None) -> datetime:
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    return current.astimezone(KST)


def krx_regular_session_status(now: datetime | None = None) -> KrxSessionStatus:
    """Return a three-state KRX regular-session verdict.

    ``SESSION_UNCERTAIN`` is never an entry permission.  It exists so a
    caller can keep observing holdings and submitting protective exits
    without pretending the calendar authoritatively says the market is open.
    """

    current = _as_kst(now)
    day_status = krx_day_status(current)
    if day_status.state == DAY_CLOSED:
        return KrxSessionStatus(
            current,
            SESSION_CLOSED,
            day_status.reason,
            day_status,
        )
    if day_status.state == DAY_UNCERTAIN:
        return KrxSessionStatus(
            current,
            SESSION_UNCERTAIN,
            day_status.reason,
            day_status,
        )

    special = KRX_SPECIAL_SESSIONS.get(current.date())
    opens_at = special.opens_at if special else time(9, 0)
    closes_at = special.closes_at if special else time(15, 30)
    label = special.reason if special else "verified regular session"
    current_time = current.timetz().replace(tzinfo=None)
    state = (
        SESSION_OPEN
        if opens_at <= current_time <= closes_at
        else SESSION_CLOSED
    )
    reason = label if state == SESSION_OPEN else f"{label}; outside session hours"
    return KrxSessionStatus(
        current,
        state,
        reason,
        day_status,
        opens_at,
        closes_at,
    )


def is_krx_regular_session_open(now: datetime | None = None) -> bool:
    """Return True only when the supported regular session is definitely open."""

    return krx_regular_session_status(now).is_open


def next_regular_session_open(
    now: datetime | None = None, *, horizon_days: int = 14
) -> tuple[datetime, bool] | None:
    """When the next regular session opens, and whether that day is uncertain.

    Display only — nothing may gate an order on this. An uncertain day is
    still returned (flagged) rather than skipped: skipping would report a
    later date as "next open" on a day the market may well trade, and the
    flag already tells the reader not to rely on it. Returns None past the
    horizon or the supported calendar, where there is nothing honest to say.
    """

    current = _as_kst(now)
    for offset in range(horizon_days + 1):
        day = current.date() + timedelta(days=offset)
        status = krx_day_status(day)
        if status.state == DAY_CLOSED:
            continue
        if not status.supported:
            return None
        special = KRX_SPECIAL_SESSIONS.get(day)
        opens_at = datetime.combine(
            day, special.opens_at if special else time(9, 0), tzinfo=KST
        )
        if opens_at > current:
            return opens_at, status.state == DAY_UNCERTAIN
    return None


__all__ = [
    "DAY_CLOSED",
    "DAY_TRADING",
    "DAY_UNCERTAIN",
    "KRX_SPECIAL_SESSIONS",
    "KRX_UNCERTAIN_SESSION_DATES",
    "KRX_WEEKDAY_HOLIDAYS",
    "KrxDayStatus",
    "KrxSessionHours",
    "KrxSessionStatus",
    "SESSION_CLOSED",
    "SESSION_OPEN",
    "SESSION_UNCERTAIN",
    "SUPPORTED_KRX_CALENDAR_YEARS",
    "is_krx_regular_session_open",
    "is_krx_trading_day",
    "krx_day_status",
    "krx_regular_session_status",
    "market_holiday_name",
    "next_regular_session_open",
]
