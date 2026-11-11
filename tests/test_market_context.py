"""Reference market data: parsers on real response shapes, and fail-soft assembly.

Every payload below is cut from a live response captured on 2026-11-11
(Yahoo v8 chart, Cboe's VIX history CSV, ECOS StatisticSearch, Kiwoom
ka40003), keeping the producer's own keys and value formats.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services import market_context as mc  # noqa: E402

KST = timezone(timedelta(hours=9))

YAHOO_NQ = {"chart": {"result": [{"meta": {
    "currency": "USD", "symbol": "NQ=F", "exchangeName": "CME", "instrumentType": "FUTURE",
    "regularMarketTime": 1794406030, "gmtoffset": -18000, "timezone": "EST",
    "exchangeTimezoneName": "America/New_York", "regularMarketPrice": 28360.75,
    "chartPreviousClose": 27085.25, "dataGranularity": "1d", "range": "5d"},
    "timestamp": [1793941200, 1794200400, 1794286800, 1794373200],
    "indicators": {"quote": [{"close": [27085.25, 28014.5, 27835.25, 28360.75],
                              "open": [26640.25, 26878.5, 28064.0, 27899.5]}],
                   "adjclose": [{"adjclose": [27085.25, 28014.5, 27835.25, 28360.75]}]}}],
    "error": None}}

NEW_YORK = ZoneInfo("America/New_York")

# NQ=F hourly closes cut from the same capture (range=5d, interval=60m), by
# bar start in New York time. `None` is how Yahoo sends an hour without a
# trade: the 17:00 maintenance hour and the weekend.
NQ_HOURLY = [
    ("11/06 14:00", 27205.5), ("11/06 15:00", 27076.5), ("11/06 16:00", 27085.25),
    ("11/06 17:00", None), ("11/08 17:00", None), ("11/08 18:00", 26967.0),
    ("11/09 14:00", 28025.5), ("11/09 15:00", 28004.75), ("11/09 16:00", 28073.25),
    ("11/09 17:00", 28073.25), ("11/09 18:00", 28076.75), ("11/10 13:00", 27694.5),
    ("11/10 14:00", 27748.75), ("11/10 15:00", 27835.25), ("11/10 16:00", 27900.75),
    ("11/10 17:00", None), ("11/10 18:00", 27952.75), ("11/10 19:00", 28021.0),
    ("11/10 23:00", 28195.75), ("11/11 00:00", 28244.5), ("11/11 07:00", 28356.75),
    ("11/11 08:00", 28374.0), ("11/11 09:00", 28359.75),
]


def _new_york(label: str) -> int:
    return int(datetime.strptime(f"2026/{label}", "%Y/%m/%d %H:%M").replace(tzinfo=NEW_YORK).timestamp())


def _hourly(rows=NQ_HOURLY, *, seen: str, price: float) -> dict:
    """The hourly answer as it stood at `seen` (New York), in Yahoo's shape.

    Yahoo appends the live quote as a last point stamped with the quote
    time; the capture ends `1794405600` (09:00) then `1794407450` (09:30:50).
    """

    at = _new_york(seen)
    past = [(_new_york(label), close) for label, close in rows if _new_york(label) <= at]
    return {"chart": {"result": [{"meta": {
        "currency": "USD", "symbol": "NQ=F", "exchangeName": "CME", "instrumentType": "FUTURE",
        "regularMarketTime": at, "gmtoffset": -18000, "timezone": "EST",
        "exchangeTimezoneName": "America/New_York", "regularMarketPrice": price,
        "chartPreviousClose": 27085.25, "dataGranularity": "1h", "range": "5d"},
        "timestamp": [stamp for stamp, _ in past] + [at],
        "indicators": {"quote": [{"close": [close for _, close in past] + [price]}]}}],
        "error": None}}


YAHOO_NQ_HOURLY = _hourly(seen="11/11 09:30", price=28370.0)

YAHOO_069500 = {"chart": {"result": [{"meta": {
    "currency": "KRW", "symbol": "069500.KS", "exchangeName": "KSC", "instrumentType": "ETF",
    "regularMarketTime": 1794378622, "gmtoffset": 32400, "timezone": "KST",
    "exchangeTimezoneName": "Asia/Seoul", "regularMarketPrice": 84540.0,
    "chartPreviousClose": 105650.0, "dataGranularity": "1d", "range": "1mo"},
    "timestamp": [1793836800, 1793923200, 1794182400, 1794268800, 1794355200],
    "indicators": {"quote": [{"close": [84610.0, 79005.0, 78490.0, 82000.0, 84540.0],
                              "open": [87890.0, 77065.0, 78715.0, 82495.0, 81835.0]}],
                   "adjclose": [{"adjclose": [84610.0, 79005.0, 78490.0, 82000.0, 84540.0]}]}}],
    "error": None}}

CBOE_CSV = (
    "DATE,OPEN,HIGH,LOW,CLOSE\n"
    "01/02/1990,17.240000,17.240000,17.240000,17.240000\n"
    "11/06/2026,27.680000,27.760000,23.470000,25.640000\n"
    "11/09/2026,25.080000,25.080000,19.640000,19.920000\n"
    "11/10/2026,19.760000,21.610000,19.290000,19.460000\n"
)


def _ecos_row(day: str, value: str) -> dict:
    return {
        "STAT_CODE": "731Y001", "STAT_NAME": "3.1.1.1. 주요국 통화의 대원화환율",
        "ITEM_CODE1": "0000001", "ITEM_NAME1": "원/미국달러(매매기준율)",
        "ITEM_CODE2": None, "ITEM_NAME2": None, "ITEM_CODE3": None, "ITEM_NAME3": None,
        "ITEM_CODE4": None, "ITEM_NAME4": None, "UNIT_NAME": "원", "WGT": None,
        "TIME": day, "DATA_VALUE": value,
    }


ECOS = {"StatisticSearch": {"list_total_count": 2, "row": [
    _ecos_row("20261110", "1355.7"), _ecos_row("20261111", "1343.3"),
]}}
ECOS_EMPTY = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}

KA40003_133690 = {"return_code": 0, "return_msg": "정상적으로 처리되었습니다", "etfdaly_trnsn": [
    {"cntr_dt": "20261111", "cur_prc": "+165925", "pre_sig": "2", "pred_pre": "+890",
     "pre_rt": "+0.54", "trde_qty": "3378852", "nav": "-163667.77", "acc_trde_prica": "559888",
     "navidex_dispty_rt": "0.00", "navetfdispty_rt": "+1.36", "trace_eor_rt": "9",
     "trace_cur_prc": "0", "trace_pred_pre": "0", "trace_pre_sig": "3"},
]}
KA40003_069500 = {"return_code": 0, "return_msg": "정상적으로 처리되었습니다", "etfdaly_trnsn": [
    {"cntr_dt": "20261111", "cur_prc": "+84540", "pre_sig": "2", "pred_pre": "+2540",
     "pre_rt": "+3.10", "trde_qty": "25352983", "nav": "+84675.55", "acc_trde_prica": "2114100",
     "navidex_dispty_rt": "+1.01", "navetfdispty_rt": "-0.16", "trace_eor_rt": "69",
     "trace_cur_prc": "+83832", "trace_pred_pre": "+2401", "trace_pre_sig": "2"},
]}


# -- parsers -----------------------------------------------------------------


def test_yahoo_change_comes_from_the_last_two_bars_not_chart_previous_close():
    """`chartPreviousClose` is the close before the range (27,085 here), five
    sessions back. Using it would report +4.7% for a +1.9% day."""

    chart = mc.parse_yahoo_chart(YAHOO_NQ)

    assert chart["last"] == 28360.75
    assert chart["prev_close"] == 27835.25
    assert mc._quote(chart, "x")["change_pct"] == 1.89
    assert chart["last_date"] == "2026-11-11"  # exchange-local date of the last bar
    assert chart["as_of"].startswith("2026-11-11T")  # reported in KST


def test_the_hourly_fixture_stamps_bars_as_the_capture_did():
    assert _new_york("11/10 15:00") == 1794340800
    assert YAHOO_NQ_HOURLY["chart"]["result"][0]["timestamp"][-2] == 1794405600


def test_futures_change_is_measured_from_the_last_us_cash_close():
    """The capture itself: 09:30 New York on 11/11, before the cash open."""

    chart = mc.parse_yahoo_futures(YAHOO_NQ_HOURLY)

    assert chart["last"] == 28370.0
    assert chart["prev_close"] == 27835.25  # 11/10's 15:00 bar, which ended at the close
    assert chart["prev_close_as_of"] == "2026-11-11T06:00+09:00"
    assert mc._futures_quote(chart, "x")["change_pct"] == 1.92


def test_futures_baseline_is_todays_close_once_the_cash_session_has_ended():
    """Brief time in Seoul. Yahoo's daily bar for 11/10 is still open here, so
    the last two daily bars measure from 11/09's settlement (28,014.5) and
    read -0.22% for a future that had risen since the close."""

    chart = mc.parse_yahoo_futures(_hourly(seen="11/10 18:59", price=27952.75))

    assert chart["prev_close"] == 27835.25
    assert mc._futures_quote(chart, "x")["change_pct"] == 0.42
    assert chart["last_date"] == "2026-11-10"  # New York's date
    assert chart["as_of"] == "2026-11-11T08:59+09:00"


def test_a_futures_bar_still_forming_at_the_close_is_not_its_own_baseline():
    """15:30 New York: the 15:00 bar holds a live price, not a close."""

    chart = mc.parse_yahoo_futures(_hourly(seen="11/10 15:30", price=27800.0))

    assert chart["prev_close"] == 28004.75  # 11/09's close
    assert chart["prev_close_as_of"] == "2026-11-10T06:00+09:00"


def test_futures_on_sunday_evening_measure_from_fridays_close():
    chart = mc.parse_yahoo_futures(_hourly(seen="11/08 18:30", price=26967.0))

    assert chart["prev_close"] == 27076.5  # Friday's 15:00 bar, not the 16:00 one
    assert chart["prev_close_as_of"] == "2026-11-07T06:00+09:00"


def test_futures_with_no_bar_before_the_close_give_the_price_without_a_change():
    chart = mc.parse_yahoo_futures(_hourly(NQ_HOURLY[-3:], seen="11/11 09:30", price=28370.0))

    quote = mc._futures_quote(chart, "x")
    assert quote["value"] == 28370.0
    assert quote["prev_close"] is None and quote["change_pct"] is None


def test_yahoo_krx_bars_are_dated_in_seoul_and_carry_the_1530_close():
    chart = mc.parse_yahoo_chart(YAHOO_069500)

    bars = dict(chart["bars"])
    assert bars["2026-11-10"] == 82000.0  # KRX's 15:30 close, not a later print
    assert bars["2026-11-11"] == 84540.0
    assert len(bars) == 5


def test_yahoo_error_payload_raises_instead_of_returning_an_empty_quote():
    with pytest.raises(ValueError):
        mc.parse_yahoo_chart({"chart": {"result": None, "error": {"code": "Not Found"}}})


def test_cboe_vix_reads_the_last_two_closes():
    vix = mc.parse_cboe_vix(CBOE_CSV)

    assert vix["value"] == 19.46 and vix["date"] == "2026-11-10"
    assert vix["prev_close"] == 19.92
    assert vix["change_pct"] == -2.31


def test_cboe_rejects_a_page_that_is_not_the_csv():
    with pytest.raises(ValueError):
        mc.parse_cboe_vix("<html><body>307 Temporary Redirect</body></html>")


def test_ecos_takes_the_newest_reference_rate():
    rate = mc.parse_ecos_usdkrw(ECOS)

    assert rate["value"] == 1343.3 and rate["date"] == "2026-11-11"
    assert rate["prev_close"] == 1355.7


def test_ecos_no_data_answer_raises_with_its_message():
    with pytest.raises(ValueError, match="해당하는 데이터가 없습니다"):
        mc.parse_ecos_usdkrw(ECOS_EMPTY)


def test_etf_nav_is_a_magnitude_and_the_premium_keeps_its_sign():
    """Kiwoom prefixes prices with the day's direction: "-163667.77" is a NAV
    on a down day, not a negative NAV. The premium's sign is real."""

    etf = mc.parse_etf_daily_trend(KA40003_133690)

    assert etf == {
        "date": "2026-11-11", "close": 165925.0, "nav": 163667.77,
        "premium_pct": 1.36, "source": "키움 ka40003 ETF일별추이",
    }
    assert mc.parse_etf_daily_trend(KA40003_069500)["premium_pct"] == -0.16


def test_etf_business_error_raises():
    with pytest.raises(ValueError, match="ka40003"):
        mc.parse_etf_daily_trend({"return_code": 3, "return_msg": "인증에 실패했습니다"})


# -- assembly ----------------------------------------------------------------


class _Kiwoom:
    """Answers ka40003 the way the live client does: an httpx-like response."""

    def __init__(self, fail: bool = False):
        self.calls: list[dict] = []
        self.fail = fail

    async def post(self, url, *, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        if self.fail:
            raise httpx.ConnectError("kiwoom down")
        body = KA40003_133690 if json["stk_cd"] == "133690" else KA40003_069500
        return httpx.Response(200, json=body)


def _transport(*, yahoo_ok: bool = True, counter: dict | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if counter is not None:
            counter[host] = counter.get(host, 0) + 1
        if host == "query1.finance.yahoo.com":
            if not yahoo_ok:
                return httpx.Response(429, text="Too Many Requests")
            if request.url.params.get("interval") == "60m":
                return httpx.Response(200, json=YAHOO_NQ_HOURLY)
            return httpx.Response(200, json=YAHOO_069500 if ".KS" in request.url.path else YAHOO_NQ)
        if host == "cdn.cboe.com":
            return httpx.Response(200, text=CBOE_CSV)
        if host == "ecos.bok.or.kr":
            return httpx.Response(200, json=ECOS)
        raise AssertionError(f"unexpected host {host}")

    return httpx.MockTransport(handler)


def _build(kiwoom=None, **transport_kwargs):
    async def run():
        async with httpx.AsyncClient(transport=_transport(**transport_kwargs)) as http:
            return await mc.build_market_context(
                kiwoom, now=datetime(2026, 11, 11, 23, 0, tzinfo=KST), http=http
            )

    return asyncio.run(run())


def test_context_carries_every_leg_with_its_source():
    kiwoom = _Kiwoom()

    ctx = _build(kiwoom)

    futures = ctx["us"]["nasdaq100_futures"]
    assert futures["value"] == 28370.0 and futures["change_pct"] == 1.92
    assert futures["prev_close_as_of"] == "2026-11-11T06:00+09:00" and "마감" in futures["basis"]
    assert futures["source"].startswith("Yahoo NQ=F")
    # An index says which close its change is measured from.
    assert ctx["us"]["nasdaq100"]["prev_close_date"] == "2026-11-10"
    assert ctx["vix"]["value"] == 19.46 and "Cboe" in ctx["vix"]["source"]
    assert ctx["usd_krw"]["reference"]["value"] == 1343.3
    assert ctx["etf"]["133690"] == {
        "name": "TIGER 미국나스닥100", "date": "2026-11-11", "close": 165925.0,
        "nav": 163667.77, "premium_pct": 1.36, "source": "키움 ka40003 ETF일별추이",
    }
    # Kiwoom is asked for the two ETFs' NAV and nothing else.
    assert sorted(c["json"]["stk_cd"] for c in kiwoom.calls) == ["069500", "133690"]
    assert {c["headers"]["api-id"] for c in kiwoom.calls} == {"ka40003"}


def test_one_source_failing_leaves_the_others_standing():
    ctx = _build(_Kiwoom(fail=True), yahoo_ok=False)

    assert "error" in ctx["us"]["nasdaq100_futures"]
    assert "error" in ctx["usd_krw"]["market"]
    assert "error" in ctx["etf"]["069500"] and ctx["etf"]["069500"]["name"] == "KODEX 200"
    assert ctx["vix"]["value"] == 19.46  # Cboe still answered
    assert ctx["usd_krw"]["reference"]["value"] == 1343.3  # so did ECOS


def test_without_a_kiwoom_client_the_etf_leg_says_so_and_nothing_else_breaks():
    ctx = _build(None)

    assert "error" in ctx["etf"]
    assert ctx["vix"]["value"] == 19.46


def test_a_second_request_is_served_from_cache_including_kiwoom():
    kiwoom, hits = _Kiwoom(), {}

    _build(kiwoom, counter=hits)
    first = dict(hits)
    _build(kiwoom, counter=hits)

    assert hits == first  # no new outbound requests
    assert len(kiwoom.calls) == 2  # one per ETF, once


def test_a_failing_source_is_not_retried_on_every_request():
    """The agent tab polls every 30 seconds; a dead source must not cost its
    timeout each time."""

    hits: dict = {}

    _build(None, yahoo_ok=False, counter=hits)
    first = hits["query1.finance.yahoo.com"]
    _build(None, yahoo_ok=False, counter=hits)

    assert hits["query1.finance.yahoo.com"] == first


def test_a_source_that_hangs_is_remembered_as_failed(monkeypatch):
    """Kiwoom's client waits ten seconds per phase. Cut off from outside, the
    call was cancelled rather than failed, nothing was cached, and the next
    request called Kiwoom and waited all over again."""

    monkeypatch.setattr(mc, "LEG_TIMEOUT_SECONDS", 0.01)

    class Hanging(_Kiwoom):
        async def post(self, url, *, headers, json):
            self.calls.append(json)
            await asyncio.sleep(5)

    kiwoom = Hanging()

    first = _build(kiwoom)
    second = _build(kiwoom)

    assert "TimeoutError" in first["etf"]["069500"]["error"]
    assert "TimeoutError" in second["etf"]["133690"]["error"]
    assert len(kiwoom.calls) == 2  # one per ETF, and not asked again
    assert first["vix"]["value"] == 19.46  # the rest still rendered


def test_daily_closes_return_every_symbol_or_raise():
    async def run(ok: bool):
        async with httpx.AsyncClient(transport=_transport(yahoo_ok=ok)) as http:
            return await mc.fetch_daily_closes(
                {"069500": "069500.KS", "133690": "133690.KS"}, http=http
            )

    closes = asyncio.run(run(True))
    assert closes["069500"]["2026-11-10"] == 82000.0
    assert set(closes) == {"069500", "133690"}

    mc.clear_cache()
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(run(False))


def test_the_suite_default_refuses_the_network():
    """conftest's guard: with no transport installed, nothing leaves the box."""

    ctx = asyncio.run(mc.build_market_context(None))

    assert "error" in ctx["vix"] and "ConnectError" in ctx["vix"]["error"]
