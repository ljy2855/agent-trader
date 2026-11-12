"""Reference market data for the agents' brief and wrap — not a trading input.

The pre-open brief and the daily wrap quote US index futures, VIX and
USD/KRW. Until 2026-11-11 the agents found those with ad-hoc web search:
the 11/11 brief took VIX from a third-party page that disagreed with itself
(19.54 against 19.43, while Cboe's close was 19.46) and found no futures
quote for the right time. This module gives them one place to read those
numbers from, each with its source and as-of time.

Nothing on the order path reads this. Third-party feeds — the Yahoo chart
endpoint in particular is unofficial — can change shape or start refusing
without notice, and an allocation must not hang on them. So every source is
fail-soft: a failure comes back as that entry's ``error`` while the others
still render, and a cached value is reused until it expires.

Kiwoom is used for one thing only: the ETFs' NAV and premium (ka40003).
No other free source publishes them for the same day — Naver's mobile API
showed 11/10's NAV on the evening of 11/11. Everything else comes from
outside so that the app key's rate limit stays with the watcher, and the
Kiwoom leg is cached for half an hour.
"""

from __future__ import annotations

import asyncio
import csv
import io
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Awaitable, Callable
from zoneinfo import ZoneInfo

import httpx

from ..constants import ETF_APIS
from .etf_allocation import TARGETS as ETF_TARGETS

KST = timezone(timedelta(hours=9))

# A generic client name; nothing identifying the account owner.
USER_AGENT = "Mozilla/5.0 (compatible; kiwoom-mcp/1.0)"
HTTP_TIMEOUT_SECONDS = 8.0

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
CBOE_VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
# The Bank of Korea publishes a `sample` key for ECOS that answers at most
# ten rows per call — enough for the latest reference rate, which is all
# this asks for. A registered key can replace it without other changes.
ECOS_URL = (
    "https://ecos.bok.or.kr/api/StatisticSearch/sample/json/kr/1/10/"
    "731Y001/D/{start}/{end}/0000001"
)

# Yahoo symbols. Futures move while Korea trades; the cash indices are the
# last US close the ETFs' NAV is built on.
US_INDEX_SYMBOLS = {
    "nasdaq100": "^NDX",
    "sp500": "^GSPC",
}
US_FUTURES_SYMBOLS = {
    "nasdaq100_futures": "NQ=F",
    "sp500_futures": "ES=F",
}
USD_KRW_SYMBOL = "KRW=X"
# Cboe posts its official close hours after the session: the file for
# 2026-11-11 is stamped 21:11 New York time, 11:11 in Korea. The 08:40 brief
# therefore read the close of the day before from it. Yahoo carries the same
# closes (17.49, 19.46 and 19.92 matched to the cent) as soon as the session
# ends, so it is shown beside the official figure.
VIX_SYMBOL = "^VIX"

# The US cash session ends at 16:00 New York time.
US_CASH_CLOSE_HOUR = 16

# Seconds each leg stays cached. Futures and FX move; a daily close and a
# NAV do not change within the hour.
TTL_LIVE = 600
TTL_DAILY = 3600
TTL_ETF_NAV = 1800


# A failure is remembered briefly too. Without it a source that is down
# would cost its full timeout on every overview request — the dashboard's
# agent tab polls every 30 seconds — instead of once a minute.
TTL_FAILURE = 60

# One outbound call, start to finish. The limit sits inside the cache so that
# running out of time is remembered like any other failure. A limit applied
# from outside cancels the call instead, and a cancellation is not an
# `Exception`: nothing would be cached, and a source that hangs — Kiwoom's
# own client waits ten seconds per phase — would be called again, and waited
# for again, on every request.
LEG_TIMEOUT_SECONDS = HTTP_TIMEOUT_SECONDS + 2

_cache: dict[str, tuple[float, Any, bool]] = {}


async def _cached(key: str, ttl: float, fetch: Callable[[], Awaitable[Any]]) -> Any:
    hit = _cache.get(key)
    if hit and hit[0] > time.monotonic():
        if hit[2]:
            raise hit[1]
        return hit[1]
    try:
        value = await asyncio.wait_for(fetch(), LEG_TIMEOUT_SECONDS)
    except Exception as exc:
        _cache[key] = (time.monotonic() + TTL_FAILURE, exc, True)
        raise
    _cache[key] = (time.monotonic() + ttl, value, False)
    return value


def clear_cache() -> None:
    _cache.clear()


def _round(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def _change_pct(last: float | None, prev: float | None) -> float | None:
    if last is None or not prev:
        return None
    return round((last / prev - 1.0) * 100.0, 2)


# -- Yahoo chart -------------------------------------------------------------


def parse_yahoo_chart(payload: dict[str, Any]) -> dict[str, Any]:
    """Daily bars and the latest quote from a v8 chart response.

    ``meta.chartPreviousClose`` is the close *before the requested range*,
    not the previous session, so the change is taken from the last two
    daily bars instead. For a future the last bar is the session in
    progress; for an index after the US close it is that close.
    """

    result = ((payload or {}).get("chart") or {}).get("result") or []
    if not result:
        error = ((payload or {}).get("chart") or {}).get("error")
        raise ValueError(f"Yahoo chart 응답에 결과가 없다: {error}")
    body = result[0]
    meta = body.get("meta") or {}
    tz = ZoneInfo(meta.get("exchangeTimezoneName") or "UTC")
    stamps = body.get("timestamp") or []
    closes = (((body.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
    bars: list[tuple[str, float]] = []
    for stamp, close in zip(stamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(stamp, tz).date().isoformat()
        if bars and bars[-1][0] == day:
            bars[-1] = (day, float(close))
        else:
            bars.append((day, float(close)))
    if not bars:
        raise ValueError("Yahoo chart 응답에 종가가 없다")
    market_time = meta.get("regularMarketTime")
    as_of = (
        datetime.fromtimestamp(market_time, KST).isoformat(timespec="minutes")
        if isinstance(market_time, (int, float)) else None
    )
    last_day, last = bars[-1]
    prev_day, prev = bars[-2] if len(bars) > 1 else (None, None)
    return {
        "symbol": meta.get("symbol"),
        "currency": meta.get("currency"),
        "bars": bars,
        "last": last,
        "last_date": last_day,
        "prev_close": prev,
        "prev_close_date": prev_day,
        "as_of": as_of,
    }


def parse_yahoo_futures(payload: dict[str, Any]) -> dict[str, Any]:
    """Latest futures price against its level at the last US cash close.

    Takes *hourly* bars, because daily ones cannot answer this. Yahoo dates
    a future's daily bar by the New York calendar day, and a finished day's
    close is its settlement near 16:00. From 16:00 until midnight New York
    — 06:00 to 14:00 in Seoul, which is when the pre-open brief runs — the
    newest daily bar is still that same day, so "the last two daily bars"
    measures from the settlement *before* the session that just closed.
    Replayed on the 2026-11-11 capture at 19:00 New York on 11/10 (09:00
    KST), that reads -0.2% while the future stood +0.4% above its level at
    the close: the wrong sign for the one number the brief wants from it.

    The baseline is the last hourly bar that ended at or before the most
    recent weekday 16:00 New York. That is the future as the cash index
    closed, so the change always means "since the US close" — and on a
    13:00 half day it is the last trade before the early halt.
    """

    result = ((payload or {}).get("chart") or {}).get("result") or []
    if not result:
        error = ((payload or {}).get("chart") or {}).get("error")
        raise ValueError(f"Yahoo chart 응답에 결과가 없다: {error}")
    body = result[0]
    meta = body.get("meta") or {}
    tz = ZoneInfo(meta.get("exchangeTimezoneName") or "America/New_York")
    stamps = body.get("timestamp") or []
    closes = (((body.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
    bars = [(int(stamp), float(close)) for stamp, close in zip(stamps, closes) if close is not None]
    if not bars:
        raise ValueError("Yahoo chart 응답에 종가가 없다")
    market_time = meta.get("regularMarketTime")
    if not isinstance(market_time, (int, float)):
        market_time = bars[-1][0]
    price = meta.get("regularMarketPrice")
    last = float(price) if isinstance(price, (int, float)) else bars[-1][1]

    seen = datetime.fromtimestamp(market_time, tz)
    cash_close = seen.replace(hour=US_CASH_CLOSE_HOUR, minute=0, second=0, microsecond=0)
    while cash_close > seen or cash_close.weekday() >= 5:
        cash_close -= timedelta(days=1)
    cutoff = cash_close.timestamp()
    # Only bars that had finished by then. The bar still forming — and the
    # live point Yahoo appends, stamped with the quote time — start too late.
    base = None
    for start, close in bars:
        if start + 3600 <= cutoff:
            base = (start + 3600, close)
    return {
        "symbol": meta.get("symbol"),
        "last": last,
        "last_date": seen.date().isoformat(),
        "as_of": datetime.fromtimestamp(market_time, KST).isoformat(timespec="minutes"),
        "prev_close": base[1] if base else None,
        "prev_close_as_of": (
            datetime.fromtimestamp(base[0], KST).isoformat(timespec="minutes") if base else None
        ),
    }


async def _yahoo_chart(
    http: httpx.AsyncClient, symbol: str, *, range_: str, ttl: float
) -> dict[str, Any]:
    async def fetch() -> dict[str, Any]:
        response = await http.get(
            YAHOO_CHART_URL.format(symbol=symbol),
            params={"range": range_, "interval": "1d"},
        )
        response.raise_for_status()
        return parse_yahoo_chart(response.json())

    return await _cached(f"yahoo:{symbol}:{range_}", ttl, fetch)


async def _yahoo_futures(http: httpx.AsyncClient, symbol: str, *, ttl: float) -> dict[str, Any]:
    async def fetch() -> dict[str, Any]:
        response = await http.get(
            YAHOO_CHART_URL.format(symbol=symbol),
            params={"range": "5d", "interval": "60m"},
        )
        response.raise_for_status()
        return parse_yahoo_futures(response.json())

    return await _cached(f"yahoo-futures:{symbol}", ttl, fetch)


def _quote(chart: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "value": _round(chart["last"]),
        "prev_close": _round(chart["prev_close"]),
        "prev_close_date": chart["prev_close_date"],
        "change_pct": _change_pct(chart["last"], chart["prev_close"]),
        "date": chart["last_date"],
        "as_of": chart["as_of"],
        "source": source,
    }


FUTURES_BASIS = "change_pct는 가장 최근 미국 정규장 마감(뉴욕 16:00) 때의 선물가 대비다"


def _futures_quote(chart: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "value": _round(chart["last"]),
        "prev_close": _round(chart["prev_close"]),
        "prev_close_as_of": chart["prev_close_as_of"],
        "change_pct": _change_pct(chart["last"], chart["prev_close"]),
        "basis": FUTURES_BASIS,
        "date": chart["last_date"],
        "as_of": chart["as_of"],
        "source": source,
    }


async def fetch_daily_closes(
    symbols: dict[str, str],
    *,
    range_: str = "6mo",
    http: httpx.AsyncClient | None = None,
) -> dict[str, dict[str, float]]:
    """{key: {YYYY-MM-DD: close}} from Yahoo daily bars, cached for an hour.

    For KRX listings (``069500.KS``) the close is the exchange's 15:30 close
    — the price our closing-auction orders fill at — unlike Kiwoom's daily
    bars, whose close is the last trade near 20:00 (roadmap §10.2).
    Raises if any symbol fails, so a caller never mixes a partial set.
    """

    async def run(client: httpx.AsyncClient) -> dict[str, dict[str, float]]:
        charts = await asyncio.gather(
            *(_yahoo_chart(client, symbol, range_=range_, ttl=TTL_DAILY)
              for symbol in symbols.values())
        )
        return {key: dict(chart["bars"]) for key, chart in zip(symbols, charts)}

    if http is not None:
        return await run(http)
    async with _http_client() as client:
        return await run(client)


# -- Cboe VIX ----------------------------------------------------------------


def parse_cboe_vix(text: str) -> dict[str, Any]:
    """Last two daily closes from Cboe's VIX history CSV."""

    rows = [row for row in csv.reader(io.StringIO(text)) if row]
    if len(rows) < 3 or rows[0][:1] != ["DATE"]:
        raise ValueError("Cboe VIX CSV 형식이 예상과 다르다")
    header = rows[0]
    close_at = header.index("CLOSE")

    def day(raw: str) -> str:
        return datetime.strptime(raw, "%m/%d/%Y").date().isoformat()

    last, prev = rows[-1], rows[-2]
    last_close, prev_close = float(last[close_at]), float(prev[close_at])
    return {
        "value": _round(last_close),
        "prev_close": _round(prev_close),
        "change_pct": _change_pct(last_close, prev_close),
        "date": day(last[0]),
        "source": "Cboe VIX 일별 종가 (공식)",
    }


async def _cboe_vix(http: httpx.AsyncClient) -> dict[str, Any]:
    async def fetch() -> dict[str, Any]:
        response = await http.get(CBOE_VIX_URL)
        response.raise_for_status()
        return parse_cboe_vix(response.text)

    return await _cached("cboe:vix", TTL_DAILY, fetch)


# -- Bank of Korea ECOS --------------------------------------------------------


def parse_ecos_usdkrw(payload: dict[str, Any]) -> dict[str, Any]:
    """Latest USD/KRW reference rate (매매기준율) from an ECOS search."""

    block = (payload or {}).get("StatisticSearch") or {}
    rows = [r for r in block.get("row") or [] if r.get("DATA_VALUE") not in (None, "")]
    if not rows:
        result = (payload or {}).get("RESULT") or {}
        raise ValueError(f"ECOS 응답에 값이 없다: {result.get('MESSAGE') or result}")
    rows.sort(key=lambda r: r.get("TIME") or "")
    last = rows[-1]
    prev = rows[-2] if len(rows) > 1 else None
    value = float(last["DATA_VALUE"])
    prev_value = float(prev["DATA_VALUE"]) if prev else None
    raw_day = str(last.get("TIME") or "")
    return {
        "value": _round(value),
        "prev_close": _round(prev_value),
        "change_pct": _change_pct(value, prev_value),
        "date": f"{raw_day[:4]}-{raw_day[4:6]}-{raw_day[6:]}" if len(raw_day) == 8 else raw_day,
        "source": "한국은행 ECOS 원/미국달러 매매기준율 (공식, 일별)",
    }


async def _ecos_usdkrw(http: httpx.AsyncClient, today: date) -> dict[str, Any]:
    # Ten calendar days hold at most eight business days, inside the sample
    # key's ten-row answer, so the newest rate is never cut off.
    start = (today - timedelta(days=10)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    async def fetch() -> dict[str, Any]:
        response = await http.get(ECOS_URL.format(start=start, end=end))
        response.raise_for_status()
        return parse_ecos_usdkrw(response.json())

    return await _cached(f"ecos:usdkrw:{end}", TTL_DAILY, fetch)


# -- Kiwoom ETF NAV (ka40003) ------------------------------------------------


def _signed(raw: Any) -> float | None:
    text = str(raw or "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_etf_daily_trend(payload: dict[str, Any]) -> dict[str, Any]:
    """Latest row of ka40003 that has a NAV: close, NAV and the premium.

    Prices carry Kiwoom's direction sign (``"-163667.77"`` is a NAV on a
    down day), so they are read as magnitudes. ``navetfdispty_rt`` is the
    one signed number that means what its sign says: the market price
    against NAV, in percent.

    Before the open the first row is already today's, with no NAV in it yet:
    the 2026-11-12 08:40 brief was handed a NAV of 0 and a premium of 0%
    for both ETFs. A row without a NAV is passed over, so the answer is the
    last published one under its own date.
    """

    if (payload or {}).get("return_code") not in (0, None):
        raise ValueError(f"ka40003 오류: {payload.get('return_msg')}")
    rows = (payload or {}).get("etfdaly_trnsn") or []
    if not rows:
        raise ValueError("ka40003 응답에 일별 행이 없다")
    row = next((r for r in rows if _signed(r.get("nav"))), None)
    if row is None:
        raise ValueError("ka40003 응답에 NAV가 있는 행이 없다")
    close = _signed(row.get("cur_prc"))
    nav = _signed(row.get("nav"))
    raw_day = str(row.get("cntr_dt") or "")
    return {
        "date": f"{raw_day[:4]}-{raw_day[4:6]}-{raw_day[6:]}" if len(raw_day) == 8 else raw_day,
        "close": abs(close) if close is not None else None,
        "nav": _round(abs(nav)) if nav is not None else None,
        "premium_pct": _signed(row.get("navetfdispty_rt")),
        "source": "키움 ka40003 ETF일별추이",
    }


async def _kiwoom_etf(kiwoom_client: Any, code: str) -> dict[str, Any]:
    api = ETF_APIS["ka40003"]

    async def fetch() -> dict[str, Any]:
        response = await kiwoom_client.post(
            api.url,
            headers={"api-id": api.api_id, "cont-yn": "N"},
            json={"stk_cd": code},
        )
        return parse_etf_daily_trend(response.json())

    return await _cached(f"kiwoom:ka40003:{code}", TTL_ETF_NAV, fetch)


# -- assembly ----------------------------------------------------------------


def _http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=HTTP_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


async def _settle(name: str, coro: Awaitable[Any]) -> tuple[str, Any]:
    # Every leg is bounded inside `_cached`, where a timeout is remembered.
    try:
        return name, await coro
    except Exception as exc:  # noqa: BLE001 - each leg fails alone
        return name, {"error": f"{type(exc).__name__}: {str(exc)[:160]}"}


NOTE = (
    "참고용이다. watcher는 이 값을 읽지 않으며 주문은 이 값과 무관하다. "
    "인용할 때 source와 date·as_of를 함께 적어라. "
    "등락률의 기준이 항목마다 다르다. 지수·환율의 change_pct는 직전 일봉 종가(prev_close_date) 대비이고, "
    "선물의 change_pct는 가장 최근 미국 정규장 마감 때의 선물가(prev_close_as_of) 대비다. "
    "그래서 미국 장이 끝난 뒤의 선물 등락률은 지수의 당일 등락에 더해진 마감 이후 움직임이다. "
    "VIX는 둘이다. reference(Cboe 공식)는 미국 장이 끝나고 몇 시간 뒤에 올라와서 한국 아침에는 "
    "하루 전 종가일 수 있다. market(Yahoo)은 최근 값이니 두 항목의 date를 견주어 적어라. "
    "ETF NAV는 국내 장 마감 기준이고, 미국 지수 ETF의 NAV는 전일 미국 종가 기준이라 "
    "장중 괴리율에는 밤사이 선물·환율 이동이 섞인다. 그날 NAV가 아직 없으면(장 전) "
    "ETF 항목은 NAV가 있는 마지막 날의 값이고 date가 그 날짜다."
)


async def build_market_context(
    kiwoom_client: Any = None,
    *,
    now: datetime | None = None,
    http: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """US indices and futures, VIX, USD/KRW and the held ETFs' NAV."""

    now = now or datetime.now(KST)

    async def run(client: httpx.AsyncClient) -> dict[str, Any]:
        legs: list[Awaitable[tuple[str, Any]]] = []
        for key, symbol in US_INDEX_SYMBOLS.items():
            legs.append(_settle(key, _yahoo_chart(client, symbol, range_="5d", ttl=TTL_LIVE)))
        for key, symbol in US_FUTURES_SYMBOLS.items():
            legs.append(_settle(key, _yahoo_futures(client, symbol, ttl=TTL_LIVE)))
        legs.append(_settle("usd_krw_market", _yahoo_chart(client, USD_KRW_SYMBOL, range_="5d", ttl=TTL_LIVE)))
        legs.append(_settle("vix_market", _yahoo_chart(client, VIX_SYMBOL, range_="5d", ttl=TTL_LIVE)))
        legs.append(_settle("vix_reference", _cboe_vix(client)))
        legs.append(_settle("usd_krw_reference", _ecos_usdkrw(client, now.date())))
        if kiwoom_client is not None:
            for code in ETF_TARGETS:
                legs.append(_settle(f"etf:{code}", _kiwoom_etf(kiwoom_client, code)))
        return dict(await asyncio.gather(*legs))

    if http is not None:
        got = await run(http)
    else:
        async with _http_client() as client:
            got = await run(client)

    def yahoo(key: str, source: str, shape: Callable[[dict[str, Any], str], dict[str, Any]] = _quote) -> dict[str, Any]:
        value = got.get(key)
        if isinstance(value, dict) and "error" in value:
            return {**value, "source": source}
        return shape(value, source)

    us = {
        "nasdaq100": yahoo("nasdaq100", "Yahoo ^NDX (비공식)"),
        "sp500": yahoo("sp500", "Yahoo ^GSPC (비공식)"),
        "nasdaq100_futures": yahoo("nasdaq100_futures", "Yahoo NQ=F 근월물 (비공식)", _futures_quote),
        "sp500_futures": yahoo("sp500_futures", "Yahoo ES=F 근월물 (비공식)", _futures_quote),
    }
    etf: dict[str, Any] = {}
    if kiwoom_client is None:
        etf = {"error": "키움 클라이언트 없음 — ETF NAV 생략"}
    else:
        for code, name in ETF_TARGETS.items():
            etf[code] = {"name": name, **got.get(f"etf:{code}", {"error": "조회 안 됨"})}

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "note": NOTE,
        "us": us,
        "vix": {
            "market": yahoo("vix_market", "Yahoo ^VIX (비공식)"),
            "reference": got.get("vix_reference"),
        },
        "usd_krw": {
            "market": yahoo("usd_krw_market", "Yahoo KRW=X (비공식, 장중 환율)"),
            "reference": got.get("usd_krw_reference"),
        },
        "etf": etf,
    }


__all__ = [
    "build_market_context",
    "clear_cache",
    "fetch_daily_closes",
    "parse_cboe_vix",
    "parse_ecos_usdkrw",
    "parse_etf_daily_trend",
    "parse_yahoo_chart",
    "parse_yahoo_futures",
]
