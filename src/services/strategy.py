"""Strategy planning and mock execution helpers for Kiwoom OpenAPI."""

from __future__ import annotations

import json
from datetime import datetime
from math import floor
from pathlib import Path
from collections.abc import Awaitable, Callable, Sequence
from typing import Any
from zoneinfo import ZoneInfo

from ..config import Settings
from ..constants.universe import (
    ROSTER_CODES,
    UNIVERSE_BOTH,
    UNIVERSE_LEADERS,
    UNIVERSE_ROSTER,
)
from . import account, market, order
from .kiwoom_client import KiwoomClient
from .entry_rules import BELOW_MA_MAX_DIP_PCT, moving_average_discount
from .order_ledger import normalize_stock_code

KST = ZoneInfo("Asia/Seoul")
ETF_KEYWORDS = (
    "KODEX",
    "TIGER",
    "KOSEF",
    "KBSTAR",
    "HANARO",
    "ARIRANG",
    "ACE",
    "PLUS",
    "RISE",
    "SOL",
    "TIMEFOLIO",
    "FOCUS",
    "ETN",
    "인버스",
    "레버리지",
    "2X",
)


def _pick_first(record: dict[str, Any], *keys: str) -> Any:
    """Return the first non-empty value for the given keys."""

    for key in keys:
        value = record.get(key)
        if value not in ("", None):
            return value
    return None


def _to_float(value: Any) -> float | None:
    """Convert a Kiwoom numeric field to a float when possible."""

    if value in ("", None):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    sign = 1.0
    if text[0] == "+":
        text = text[1:]
    elif text[0] == "-":
        sign = -1.0
        text = text[1:]
    try:
        return sign * float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    """Convert a Kiwoom numeric field to an int when possible."""

    number = _to_float(value)
    if number is None:
        return None
    return int(number)


def to_price(value: Any) -> int | None:
    """Convert a price-like Kiwoom field to a positive integer.

    Public because the watcher prices protective sells off the same
    order-book fields this module reads. One parser, so the two cannot
    drift -- the reason `normalize_stock_code` was published too.
    """

    number = _to_int(value)
    if number is None:
        return None
    return abs(number)


_to_price = to_price


def _to_ratio(value: Any) -> float | None:
    """Convert a percentage-like Kiwoom field to a float."""

    return _to_float(value)


def _position_rate(profit_rate: Any, avg_price: int | None, current_price: int | None) -> float | None:
    """Return a holding profit rate from either the row or derived prices."""

    rate = _to_ratio(profit_rate)
    if rate is not None:
        return rate
    if avg_price and current_price:
        return ((current_price - avg_price) / avg_price) * 100
    return None


def _sanitize_watchlist(
    watchlist: list[str] | None,
    holdings: list[dict[str, Any]],
) -> list[str]:
    """Merge the user watchlist and current holdings."""

    merged: list[str] = []
    for code in watchlist or []:
        if code and code not in merged:
            merged.append(code)
    for holding in holdings:
        stock_code = holding.get("stock_code")
        if stock_code and stock_code not in merged:
            merged.append(stock_code)
    return merged


def _is_excluded_security(name: str) -> bool:
    """Return True for instruments the strategy intentionally ignores."""

    if not name:
        return True
    if name.endswith("우") or "스팩" in name or "SPAC" in name.upper():
        return True
    return any(keyword in name for keyword in ETF_KEYWORDS)


def _normalize_holding_rows(evaluation_result: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract account summary and holdings from the evaluation response."""

    rows = evaluation_result.get("evaluation_data", [])
    if not isinstance(rows, list) or not rows:
        return {}, []

    evaluation_record = rows[0] if isinstance(rows[0], dict) else {}
    raw_holdings = []
    for page in rows:
        if not isinstance(page, dict):
            continue
        page_holdings = page.get("stk_acnt_evlt_prst", [])
        if isinstance(page_holdings, list):
            raw_holdings.extend(page_holdings)

    holdings = []
    for row in raw_holdings:
        if not isinstance(row, dict):
            continue
        stock_code = str(_pick_first(row, "stk_cd", "code") or "").strip()
        quantity = abs(_to_int(_pick_first(row, "rmnd_qty", "qty", "hold_qty", "bal_qty")) or 0)
        if not stock_code or quantity <= 0:
            continue
        avg_price = _to_price(_pick_first(row, "avg_prc", "pur_uv", "buy_uv", "avg_uv"))
        current_price = _to_price(_pick_first(row, "cur_prc", "now_prc", "close_pric"))
        holdings.append(
            {
                "stock_code": stock_code,
                "stock_name": str(_pick_first(row, "stk_nm", "item_nm", "name") or stock_code),
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": current_price,
                "profit_loss": _to_int(_pick_first(row, "lspft_amt", "pl_amt", "evlt_pl")),
                "profit_rate": _position_rate(
                    _pick_first(row, "lspft_rt", "lspft_ratio", "pl_rt"),
                    avg_price,
                    current_price,
                ),
            }
        )

    return evaluation_record, holdings


def _extract_open_order_codes(unexecuted_result: dict[str, Any]) -> set[str]:
    """Return the set of stock codes that already have open orders."""

    rows = unexecuted_result.get("unexecuted_orders_data", [])
    if not isinstance(rows, list):
        return set()
    return {
        str(_pick_first(row, "stk_cd", "code"))
        for row in rows
        if isinstance(row, dict) and _pick_first(row, "stk_cd", "code")
    }


def _degraded_sources(
    evaluation_result: dict[str, Any], snapshot: dict[str, Any]
) -> list[dict[str, Any]]:
    """Name the upstream reads that failed, for the cycle's failure detail.

    ``success`` is an AND over the account evaluation and every market leg, but
    the plan's ``message`` is a fixed string, so a caller recording that message
    learns only *that* a cycle degraded, never *which* read broke. Market legs
    swallow transport errors into ``success=False`` (``market._post_market_query``)
    rather than raising, so nothing else logs them either — a 2026-07-29 DNS
    fault degraded ~10% of cycles and left no diagnosable trace anywhere.
    """

    degraded: list[dict[str, Any]] = []

    def add(name: str, result: Any) -> None:
        if not isinstance(result, dict) or result.get("success"):
            return
        entry: dict[str, Any] = {"source": name}
        for key in ("api_id", "error", "return_code", "return_msg"):
            value = result.get(key)
            if value not in (None, ""):
                entry[key] = value
        degraded.append(entry)

    add("account_evaluation", evaluation_result)
    sources = snapshot.get("sources") if isinstance(snapshot, dict) else None
    if isinstance(sources, dict):
        for name in sorted(sources):
            add(name, sources[name])
    elif isinstance(snapshot, dict) and not snapshot.get("success"):
        # Older/stubbed snapshots may omit `sources`; still record the failure.
        degraded.append({"source": "market_snapshot"})
    return degraded


# below_ma buy band upper edge: deeper than this reads as a broken trend
# rather than a temporary deviation (2026-06-29 backtest).
_BELOW_MA_MAX_DIP_PCT = BELOW_MA_MAX_DIP_PCT

# Crash-level thresholds for the new-entry veto. One definition, applied both
# to the two-market average and to the market the strategy actually trades —
# a second number here would be a silent policy change.
_EXTREME_CHANGE_PCT = -5.0
_EXTREME_BREADTH = 0.2

# Exit thresholds for the *dispatch* hysteresis band. Crossing back out of a
# crash reading has to clear these, not merely the entry thresholds above, so
# a metric hovering on the line stops re-arming the rising edge every tick.
#
# 2026-09-02 measured the need: primary_breadth sat at 0.19 against a 0.20
# threshold and oscillated across it, producing 8 rising edges in one session
# (80 of 183 snapshots read extreme). Each one paged the PM squad onto a
# single day-scoped issue whose thread every subsequent run re-read, and that
# is what exhausted the codex quota for the day.
#
# The band is deliberately narrow — roughly a tenth above each entry line. It
# suppresses line-hugging noise, not a market that genuinely recovers.
#
# ⚠️ These govern *agent dispatch only*. `extreme_risk_off` itself, and the
# new-entry veto it drives, keep using the entry thresholds with no
# hysteresis: a veto must react on the tick the market crosses the line, and
# widening it here would loosen a safety gate to save API calls.
_EXTREME_CHANGE_EXIT_PCT = -4.5
_EXTREME_BREADTH_EXIT = 0.22

# leaders_market_tp -> the index whose health actually governs our exposure.
# "000" scans both, so no single index governs and only the average applies.
_PRIMARY_MARKET_BY_TP = {"001": "kospi", "101": "kosdaq"}


def _build_market_regime(
    snapshot: dict[str, Any], *, leaders_market_tp: str = "000"
) -> dict[str, Any]:
    """Classify the current market into risk-on, neutral, or risk-off.

    A failed index read returns no rows, so `rising`/`fall` coerce to 0 and
    `breadth_score` lands at exactly 0.0 — numerically indistinguishable from
    a crash, and below the 0.2 extreme threshold. The 2026-07-29/30 DNS fault
    turned that into two false P0 "extreme risk-off + 계좌 0원" pages whose
    market figures were all 0.0. So publish whether the regime rests on a
    complete read, and let each consumer pick its own safe direction:
    new entries stay vetoed (fail-closed, and now also when a *partial* read
    leaves breadth above 0.2), while agent dispatch requires confidence.

    The veto also reads the traded market on its own. Averaging two indices
    dilutes the one we are exposed to: on 2026-08-06 KOSPI fell 4.58% while
    KOSDAQ sat at +0.26%, so the average was only -2.16% — and with
    `leaders_market_tp="001"` every candidate came from that KOSPI. Under the
    average alone a KOSPI-only crash needs roughly -10% to register. Breadth
    has the same shape: it counts issues equally while the strategy holds
    cap-weighted large caps, and that day KOSPI breadth read 1.29 (490 up vs
    381 down) even as the index fell, because the damage was concentrated in
    the mega caps we buy. The per-market legs are OR-ed onto the average ones,
    never replacing them, so this can only veto more entries — never fewer.
    """

    indices = snapshot.get("indices") or {}
    kospi = indices.get("kospi", {})
    kosdaq = indices.get("kosdaq", {})

    sources = snapshot.get("sources")
    if isinstance(sources, dict):
        # Only the two index legs feed the regime; a failed leaderboard leg
        # yields no candidates rather than a wrong market reading.
        market_data_complete = all(
            bool((sources.get(name) or {}).get("success"))
            for name in ("kospi", "kosdaq")
        )
    else:
        # Older/stubbed snapshots omit `sources`; fall back to the overall
        # flag and default to complete so existing callers keep their meaning.
        market_data_complete = bool(snapshot.get("success", True))

    kospi_change = _to_ratio(kospi.get("flu_rt")) or 0.0
    kosdaq_change = _to_ratio(kosdaq.get("flu_rt")) or 0.0
    kospi_rising = _to_int(kospi.get("rising")) or 0
    kospi_falling = _to_int(kospi.get("fall")) or 0
    kosdaq_rising = _to_int(kosdaq.get("rising")) or 0
    kosdaq_falling = _to_int(kosdaq.get("fall")) or 0

    # Transport success is not semantic completeness. For the first seconds
    # after 09:00 both index legs answer 200 with every field zeroed because
    # no tick has printed yet, and those zeros are numerically identical to a
    # crash: breadth becomes 0/max(0,1) = 0.0, under the 0.2 extreme
    # threshold. Unlike a failed read this one counted as complete, so it did
    # not just veto entries (harmless at the open) — it also dispatched the PM
    # squad, producing a false extreme_risk_off at the open on 2026-09-10
    # (SWO-884) and again on 2026-09-17 (SWO-938). A live tape always has
    # issues moving on one side or the other, so a leg reporting zero on both
    # sides has no data rather than a market where nothing trades.
    if kospi_rising + kospi_falling == 0 or kosdaq_rising + kosdaq_falling == 0:
        market_data_complete = False

    kospi_breadth = kospi_rising / max(kospi_falling, 1)
    kosdaq_breadth = kosdaq_rising / max(kosdaq_falling, 1)
    breadth_score = (kospi_breadth + kosdaq_breadth) / 2
    average_change = (kospi_change + kosdaq_change) / 2

    if average_change >= 0.5 and breadth_score >= 1.15:
        regime = "risk_on"
    elif average_change <= -0.5 or breadth_score < 0.85:
        regime = "risk_off"
    else:
        regime = "neutral"

    # Extreme risk-off: hard veto for new entries (crash-level selloff).
    # An incomplete read vetoes too — a half-read snapshot can leave breadth
    # above 0.2 (one good leg + one zeroed leg) and silently open the gate.
    primary_market = _PRIMARY_MARKET_BY_TP.get(leaders_market_tp)
    if primary_market == "kospi":
        primary_change, primary_breadth = kospi_change, kospi_breadth
    elif primary_market == "kosdaq":
        primary_change, primary_breadth = kosdaq_change, kosdaq_breadth
    else:
        primary_change = primary_breadth = None

    crash_signal = (
        average_change <= _EXTREME_CHANGE_PCT
        or breadth_score < _EXTREME_BREADTH
        or (primary_change is not None and primary_change <= _EXTREME_CHANGE_PCT)
        or (primary_breadth is not None and primary_breadth < _EXTREME_BREADTH)
    )
    extreme_risk_off = crash_signal or not market_data_complete

    # Same predicate at the exit thresholds. A tick that is extreme by the
    # entry band but *not* by this one sits inside the hysteresis band: the
    # veto still applies, while dispatch treats it as a continuation of the
    # existing state rather than a fresh crash.
    crash_signal_at_exit_band = (
        average_change <= _EXTREME_CHANGE_EXIT_PCT
        or breadth_score < _EXTREME_BREADTH_EXIT
        or (primary_change is not None and primary_change <= _EXTREME_CHANGE_EXIT_PCT)
        or (primary_breadth is not None and primary_breadth < _EXTREME_BREADTH_EXIT)
    )

    return {
        "regime": regime,
        "risk_on": regime == "risk_on",
        "extreme_risk_off": extreme_risk_off,
        "extreme_risk_off_sticky": crash_signal_at_exit_band or not market_data_complete,
        "market_data_complete": market_data_complete,
        "primary_market": primary_market,
        "primary_change_pct": (
            None if primary_change is None else round(primary_change, 2)
        ),
        "primary_breadth": (
            None if primary_breadth is None else round(primary_breadth, 2)
        ),
        "average_change_pct": round(average_change, 2),
        "breadth_score": round(breadth_score, 2),
        "kospi_change_pct": round(kospi_change, 2),
        "kosdaq_change_pct": round(kosdaq_change, 2),
        "kospi_breadth": round(kospi_breadth, 2),
        "kosdaq_breadth": round(kosdaq_breadth, 2),
    }


def _merge_leaderboards(
    snapshot: dict[str, Any],
    *,
    carryover_codes: list[str] | None = None,
    value_first: bool = False,
    roster_codes: Sequence[str] | None = None,
    include_leaders: bool = True,
) -> list[dict[str, Any]]:
    """Merge leaderboard rows into a candidate universe with source tags.

    `carryover_codes` are stock codes that were eligible in the immediately
    prior cycle but did not get bought (typically because they fell short
    of `auto_buy_min_score`). Carrying them forward gives the strategy a
    multi-cycle persistence check — if the same name shows up eligible
    across two cycles, that's a much stronger signal than a single
    snapshot-time pass. They also surface candidates that have rolled OFF
    the leaderboards (e.g. their day-change cooled below +1%) so we don't
    silently drop a name we were just about to buy.

    `roster_codes` seed a fixed large-cap pool into the universe, and
    `include_leaders=False` drops the movers leaderboards entirely. A
    mean-reversion entry wants names that did *not* move, so scanning only
    what topped a movers board hides most of what it would buy — see
    `src/constants/universe.py`. Roster entries sort ahead of leaderboard
    rows: the caller scores only `scan_limit` of this list, and a roster
    name carries no leaderboard rank to compete on.
    """

    universe: dict[str, dict[str, Any]] = {}
    leaders = snapshot.get("leaders", {}) if include_leaders else {}

    for position, code in enumerate(roster_codes or [], start=1):
        code = (code or "").strip()
        if not code:
            continue
        universe.setdefault(
            code,
            {
                "stock_code": code,
                "stock_name": code,
                "sources": ["roster"],
                "ranks": {"roster": position},
                "seed_row": {},
            },
        )

    for source_name, rows in leaders.items():
        if not isinstance(rows, list):
            continue
        for rank, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            stock_code = str(_pick_first(row, "stk_cd", "code") or "").strip()
            stock_name = str(_pick_first(row, "stk_nm", "item_nm", "name") or stock_code)
            if not stock_code or _is_excluded_security(stock_name):
                continue
            entry = universe.setdefault(
                stock_code,
                {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "sources": [],
                    "ranks": {},
                    "seed_row": row,
                },
            )
            entry["stock_name"] = stock_name
            entry["seed_row"] = row
            entry["sources"].append(source_name)
            entry["ranks"][source_name] = rank

    for code in carryover_codes or []:
        code = (code or "").strip()
        if not code:
            continue
        entry = universe.setdefault(
            code,
            {
                "stock_code": code,
                "stock_name": code,
                "sources": [],
                "ranks": {},
                "seed_row": {},
            },
        )
        if "carryover" not in entry["sources"]:
            entry["sources"].append("carryover")
            entry["ranks"]["carryover"] = 1

    # Roster names lead regardless of leaderboard ordering: they have no
    # leaderboard rank, so any movers-based key would sort them past
    # `scan_limit` and they would never be scored.
    def roster_rank(item: dict[str, Any]) -> tuple[int, int]:
        if "roster" in item["sources"]:
            return (0, item["ranks"].get("roster", 999))
        return (1, 0)

    if value_first:
        # Large-cap mode: 거래대금(value) leaders carry the big-caps (삼성/SK…),
        # so rank by value first; 등락률(gainers) is just a tiebreaker. The
        # market-cap filter downstream still rejects anything below threshold.
        return sorted(
            universe.values(),
            key=lambda item: (
                roster_rank(item),
                -int("value" in item["sources"]),
                item["ranks"].get("value", 999),
                -len(item["sources"]),
                item["ranks"].get("volume", 999),
                item["ranks"].get("gainers", 999),
                item["ranks"].get("carryover", 999),
            ),
        )
    return sorted(
        universe.values(),
        key=lambda item: (
            roster_rank(item),
            -int("gainers" in item["sources"]),
            -len(item["sources"]),
            item["ranks"].get("value", 999),
            item["ranks"].get("gainers", 999),
            item["ranks"].get("volume", 999),
            item["ranks"].get("carryover", 999),
        ),
    )


# --- Eligible-candidate carryover (cross-cycle persistence) ---------------
#
# Each cycle persists the codes of eligible candidates we DIDN'T buy so the
# next cycle can re-score them even if they've slipped off the live
# leaderboards. The window is short (default 60 minutes) so a stock from
# yesterday's close doesn't pollute today's morning sample.

_CARRYOVER_DIR = Path(__file__).resolve().parents[2] / "automation"
_CARRYOVER_TTL_MINUTES = 60
_CARRYOVER_TOP_N = 8


def _carryover_path(settings: Settings) -> Path:
    suffix = "mock" if settings.use_mock else "live"
    return _CARRYOVER_DIR / f"eligible_carryover_{suffix}.json"


def _load_carryover(path: Path) -> list[str]:
    try:
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        ts_raw = data.get("timestamp")
        if not ts_raw:
            return []
        ts = datetime.fromisoformat(ts_raw)
        age_min = (datetime.now(KST) - ts).total_seconds() / 60.0
        if age_min > _CARRYOVER_TTL_MINUTES:
            return []
        codes = data.get("codes", [])
        return [str(c) for c in codes if isinstance(c, str)][:_CARRYOVER_TOP_N]
    except Exception:
        return []


def _save_carryover(path: Path, codes: list[str]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(KST).isoformat(),
            "codes": codes[:_CARRYOVER_TOP_N],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False))
    except Exception:
        # Carryover is best-effort — a write failure must never break the cycle.
        pass


def _select_entry_price(detail: dict[str, Any]) -> tuple[str, str]:
    """Choose a conservative entry order type and price."""

    orderbook = detail.get("orderbook", {})
    best_ask = _to_price(orderbook.get("sel_fpr_bid"))
    if best_ask:
        return "0", str(best_ask)
    return "3", ""


def _select_exit_price(
    detail: dict[str, Any],
    *,
    is_stop_loss: bool = False,
) -> tuple[str, str]:
    """Choose a conservative exit order type and price.

    For stop-loss orders (``is_stop_loss=True``), always use market order
    (order_type_code "3") to guarantee immediate execution.  For regular
    take-profit or de-risk sells, use limit order at best bid — but
    validate that the bid is not *above* the current price (stale
    snapshot protection).
    """

    # Stop-loss → unconditionally market order for immediate fill.
    if is_stop_loss:
        return "3", ""

    orderbook = detail.get("orderbook", {})
    best_bid = _to_price(orderbook.get("buy_fpr_bid"))
    if best_bid:
        # Guard: if snapshot bid is stale and exceeds current price,
        # fall back to market order to avoid a non-filling limit order.
        quote = detail.get("quote", {})
        cur_prc = _to_price(quote.get("cur_prc"))
        if cur_prc and best_bid > cur_prc:
            return "3", ""
        return "0", str(best_bid)
    return "3", ""


def moving_average(bars: list[Any], period: int) -> float | None:
    """Simple MA of the most-recent ``period`` daily closes (bars[0] = latest).

    Public so the agents' daily-bar tool computes MA20 with the function the
    watcher scores with; a second copy would be free to disagree.
    """
    closes: list[int] = []
    for b in bars[:period]:
        if isinstance(b, dict):
            c = _to_price(b.get("close_pric") or b.get("cur_prc"))
            if c:
                closes.append(c)
    return sum(closes) / len(closes) if len(closes) >= period else None


_moving_average = moving_average

# Window for "거래량 배수" — the screener skill asks for today against the
# 20-trading-day average.
VOLUME_AVERAGE_DAYS = 20


def volume_ratio_vs_average(
    bars: list[Any], period: int = VOLUME_AVERAGE_DAYS
) -> float | None:
    """Latest bar's volume over the mean volume of the ``period`` bars before it.

    During a session bars[0] is today and holds only what has traded so far,
    so the ratio starts the day low and climbs. It is not scaled to the time
    of day. None unless ``period`` earlier bars carry a positive volume.
    """

    if not bars or not isinstance(bars[0], dict):
        return None
    latest = _to_int(bars[0].get("trde_qty"))
    prior = [
        volume
        for volume in (
            _to_int(b.get("trde_qty")) for b in bars[1 : period + 1] if isinstance(b, dict)
        )
        if volume and volume > 0
    ]
    if latest is None or latest < 0 or len(prior) < period:
        return None
    return latest / (sum(prior) / len(prior))


def limit_distance_pct(price: int | None, limit: int | None) -> float | None:
    """How far a price limit sits from ``price``, as an unsigned % of price."""

    if not price or not limit or price <= 0 or limit <= 0:
        return None
    return abs(limit - price) / price * 100


def _score_candidate(
    candidate: dict[str, Any],
    detail: dict[str, Any],
    regime: dict[str, Any],
    min_market_cap_krw: int = 0,
    day_change_min: float = 1.0,
    day_change_max: float = 29.5,
    entry_mode: str = "momentum",
    ma_period: int = 20,
) -> tuple[bool, dict[str, Any]]:
    """Score one candidate and decide whether it is eligible for entry.

    ``min_market_cap_krw`` (>0) enables a large-cap hard filter: candidates
    whose market cap is below the threshold are rejected. Market cap is
    computed from the quote we already fetch (no extra API call) as
    ``current_price × flo_stkcnt × 1000`` — ``flo_stkcnt`` is in 천주
    (thousand-share units), calibrated against known names (삼성/SK = 대형주,
    HS화성 ≈ 1,350억 = 소형주). See plan: prefer large-caps to stop the
    small-cap chase-buy losses (2026-06-13).

    ``entry_mode`` selects the entry thesis (2026-06-29 backtest: mean-reversion
    beats momentum on big-caps, +0.384 vs +0.188%/trade):
      "momentum" — chase a day_change rise (rides strength; legacy).
      "below_ma" — buy a shallow pullback below MA(``ma_period``) — "저렴할 때
                   매수". Rejects deep dips (>5% below MA = falling knife) and
                   names above the MA (not cheap). day_change/breakout/고점근접
                   momentum terms are dropped; the dip depth is scored instead.
    """

    quote = detail.get("quote", {})
    orderbook = detail.get("orderbook", {})
    bars = detail.get("daily_bars", [])
    stock_name = str(quote.get("stk_nm") or candidate.get("stock_name") or candidate["stock_code"])

    current_price = _to_price(quote.get("cur_prc"))
    listed_shares = _to_int(quote.get("flo_stkcnt"))  # 천주 단위
    market_cap = (
        current_price * listed_shares * 1000
        if current_price and listed_shares and listed_shares > 0
        else None
    )
    open_price = _to_price(quote.get("open_pric"))
    high_price = _to_price(quote.get("high_pric"))
    prev_close = _to_price(quote.get("pred_close_pric"))
    prev_high = None
    if len(bars) > 1 and isinstance(bars[1], dict):
        prev_high = _to_price(bars[1].get("high_pric"))

    day_change_pct = _to_ratio(quote.get("flu_rt"))
    total_buy = _to_price(orderbook.get("tot_buy_req")) or 0
    total_sell = _to_price(orderbook.get("tot_sel_req")) or 0
    orderbook_ratio = total_buy / max(total_sell, 1)
    best_bid = _to_price(orderbook.get("buy_fpr_bid"))
    best_ask = _to_price(orderbook.get("sel_fpr_bid"))
    spread_pct = None
    if best_bid and best_ask and best_bid > 0:
        spread_pct = ((best_ask - best_bid) / best_bid) * 100

    moving_avg = _moving_average(bars, ma_period)
    ma_dip_pct = moving_average_discount(current_price, moving_avg)
    volume_ratio = volume_ratio_vs_average(bars)
    upper_limit_distance = limit_distance_pct(current_price, _to_price(quote.get("upl_pric")))

    reasons: list[str] = []
    if not regime.get("market_data_complete", True):
        # Same veto, honest label: the market may be fine, we just can't see it.
        reasons.append("시장 데이터 불완전 (진입 불가)")
    elif regime.get("extreme_risk_off", False):
        reasons.append("극단적 시장 약세 (진입 불가)")
    if current_price is None or open_price is None or high_price is None or prev_close is None:
        reasons.append("시세 데이터가 불완전함")
    if current_price and current_price < 3000:
        reasons.append("저가주 필터")
    # Large-cap hard filter (2026-06-13). Small-cap KOSDAQ names dominated
    # the 6/9~6/12 chase-buy losses; restrict new entries to large-caps.
    # Missing/zero flo_stkcnt → conservative reject (can't verify cap).
    if min_market_cap_krw > 0 and (market_cap is None or market_cap < min_market_cap_krw):
        reasons.append("시총 미달 (대형주 아님)")

    if entry_mode == "below_ma":
        # Mean-reversion: buy a SHALLOW dip below the MA. Reject names above
        # the MA (not cheap) and deep dips (>5% below = trend broken, falling
        # knife — backtest 2026-06-29: deep dips revert to negative).
        if ma_dip_pct is None:
            reasons.append("이평 계산 불가 (일봉 부족)")
        elif ma_dip_pct <= 0:
            reasons.append("이평 위 (저렴하지 않음)")
        elif ma_dip_pct > _BELOW_MA_MAX_DIP_PCT:
            reasons.append("이평 5%+ 하회 (추세 하락)")
    else:
        # Momentum: chase a day_change rise within the parameterized band.
        if day_change_pct is None or day_change_pct < day_change_min or day_change_pct > day_change_max:
            reasons.append("당일 상승률 조건 미충족")
        elif 25 < day_change_pct <= day_change_max:
            # Late-stage breakout — must show buy-side dominance + prev-high break.
            if not (orderbook_ratio >= 1.5 and prev_high and current_price and current_price >= prev_high):
                reasons.append("당일 상승률 조건 미충족")
        if current_price and open_price and (open_price - current_price) / max(open_price, 1) > 0.02:
            reasons.append("시가 대비 2% 이상 하회")
        if current_price and high_price and (high_price - current_price) / max(current_price, 1) > 0.08:
            reasons.append("고가 대비 너무 멀어짐")
        if orderbook_ratio < 1.0:  # momentum needs buy-side dominance
            reasons.append("매수 잔량 우위 부족")
    if entry_mode == "below_ma" and orderbook_ratio < 0.5:
        # A dip naturally has sell-side pressure (that's WHY it's cheap), so the
        # momentum "buy-side dominance" gate would reject every pullback. Only
        # reject an extreme one-sided dump (ratio < 0.5 = 매도 잔량 2배+).
        reasons.append("극단적 매도 우위 (투매)")

    score = 0
    # Regime-based scoring. Momentum chases strength → reward risk_on. But
    # below_ma is CONTRARIAN — it buys weakness, so a risk_off tape is a normal
    # (even favorable) backdrop, not a penalty. Giving risk_off +0 there would
    # zero out the regime term on exactly the days below_ma is meant to act
    # (2026-06-30: KOSPI +1.61% but big-cap value-leaders weak → risk_off →
    # below_ma candidates fell short of the score gate). So below_ma scores
    # neutral/risk_off flat (extreme_risk_off is still a hard filter elsewhere).
    regime_name = regime.get("regime", "neutral")
    if entry_mode == "below_ma":
        score += 1 if regime_name != "risk_on" else 2  # weakness is the setup
    elif regime_name == "risk_on":
        score += 3
    elif regime_name == "neutral":
        score += 1
    # momentum risk_off: no bonus (penalty implicit via missing points)

    # Source bonus capped at 3 because the three leaderboards
    # (value/gainers/volume) are highly correlated for momentum names —
    # crediting +6 for being on all three over-counts the same signal.
    source_set = set(candidate.get("sources", []))
    source_bonus = 0
    if "value" in source_set:
        source_bonus = max(source_bonus, 3)
    if "gainers" in source_set:
        source_bonus = max(source_bonus, 2)
    if "volume" in source_set:
        source_bonus = max(source_bonus, 1)
    # Multi-source confirmation gives at most +1 over the strongest single
    # source, retaining some signal without inflating it.
    if len(source_set) >= 2:
        source_bonus += 1
    score += min(source_bonus, 3)

    if entry_mode == "below_ma":
        # Mean-reversion: reward the SHALLOW pullback (a 0~2% dip below MA is
        # the sweet spot; 2~5% still credited but less). Momentum terms
        # (day_change tier, distance-from-high, breakout) are dropped — they'd
        # penalize exactly the "cheap" entries this mode targets.
        if ma_dip_pct is not None:
            if 0 < ma_dip_pct <= 2:
                score += 3
            elif 2 < ma_dip_pct <= 5:
                score += 2
        if current_price and open_price and current_price >= open_price:
            score += 1  # intraday bounce off the dip
    else:
        # Momentum: strong day_change + tag-the-high + breakout score higher.
        if day_change_pct is not None:
            if 1 <= day_change_pct < 5:
                score += 1
            elif 5 <= day_change_pct < 15:
                score += 2
            elif 15 <= day_change_pct <= 25:
                score += 3
            elif 25 < day_change_pct <= 29.5:
                score += 1  # late stage — chase risk discount
        if current_price and open_price and current_price >= open_price:
            score += 1
        if current_price and high_price:
            distance_from_high = (high_price - current_price) / max(current_price, 1)
            if distance_from_high <= 0.01:
                score += 2
            elif distance_from_high <= 0.03:
                score += 1
        if prev_high and current_price and current_price >= prev_high:
            score += 2
    if orderbook_ratio >= 1.5:  # liquidity/buy-pressure — both modes
        score += 2
    elif orderbook_ratio >= 1.2:
        score += 1
    if spread_pct is not None and spread_pct <= 0.35:
        score += 1

    breakout = bool(prev_high and current_price and current_price >= prev_high)
    eligible = not reasons and score >= 7

    return eligible, {
        "stock_code": candidate["stock_code"],
        "stock_name": stock_name,
        "sources": list(source_set),
        "score": score,
        "eligible": eligible,
        "reasons": reasons,
        "ma_dip_pct": (
            round(ma_dip_pct, 2) if isinstance(ma_dip_pct, (int, float)) else None
        ),
        # What the screener skill calls 필수 체크. All derived from the quote and
        # bars fetched above — no extra API call. Until 2026-09-27 none of it
        # reached the trigger, and the screener repeatedly deferred score-8
        # names because "MA20 이격·거래량 배수가 트리거에 없다".
        "ma_period": ma_period,
        "ma_value": round(moving_avg) if moving_avg is not None else None,
        "market_cap_krw": market_cap,
        "volume_ratio_20d": round(volume_ratio, 2) if volume_ratio is not None else None,
        "upper_limit_distance_pct": (
            round(upper_limit_distance, 2) if upper_limit_distance is not None else None
        ),
        "current_price": current_price,
        "open_price": open_price,
        "high_price": high_price,
        "prev_close": prev_close,
        "prev_high": prev_high,
        "day_change_pct": day_change_pct,
        "orderbook_ratio": round(orderbook_ratio, 2),
        "spread_pct": round(spread_pct, 3) if spread_pct is not None else None,
        "breakout": breakout,
        "entry_order_type_code": _select_entry_price(detail)[0],
        "entry_price": _select_entry_price(detail)[1],
    }


def _review_holding(
    holding: dict[str, Any],
    detail: dict[str, Any],
    regime: dict[str, Any],
    *,
    stop_loss_pct: float = -3.0,
    hard_take_profit_pct: float = 8.0,
) -> dict[str, Any]:
    """Review an existing holding and decide whether to hold or exit.

    ``stop_loss_pct``/``hard_take_profit_pct`` default to main_watcher.py's
    CLI defaults so this MCP-only/mock-only planner path (the live watcher
    never calls this — its Tier1 hard exits are a separate, independently
    parameterized implementation in watcher_triggers.py) doesn't silently
    diverge from the documented defaults. Pass the live deployment's actual
    values (see k8s/kiwoom-watcher.yaml) to mirror them exactly.
    """

    quote = detail.get("quote", {})
    current_price = _to_price(quote.get("cur_prc")) or holding.get("current_price")
    open_price = _to_price(quote.get("open_pric"))
    profit_rate = holding.get("profit_rate")
    quantity = holding.get("quantity", 0)

    action = "hold"
    priority = 0
    reason = "추세 유지"

    if profit_rate is not None and profit_rate <= stop_loss_pct:
        action = "sell"
        priority = 100
        reason = "손절 규칙"
    elif profit_rate is not None and profit_rate >= hard_take_profit_pct:
        action = "sell"
        priority = 90
        reason = f"익절 규칙 ({hard_take_profit_pct}%+ 수익 실현)"
    elif (
        regime.get("regime") == "risk_off"
        and profit_rate is not None
        and profit_rate >= 3.0
    ):
        action = "sell"
        priority = 85
        reason = "시장 약세 중 수익 보호 (3%+ 확보)"
    elif (
        regime.get("regime") == "risk_off"
        and profit_rate is not None
        and profit_rate <= 1.0
    ):
        action = "sell"
        priority = 80
        reason = "시장 약세로 디리스킹"
    elif (
        current_price
        and open_price
        and current_price < open_price
        and profit_rate is not None
        and profit_rate < -1.0
    ):
        action = "sell"
        priority = 70
        reason = "시가 이탈 + 손실 포지션"

    is_stop_loss = action == "sell" and "손절" in reason
    order_type_code, exit_price = _select_exit_price(
        detail, is_stop_loss=is_stop_loss,
    )
    return {
        "action": action,
        "priority": priority,
        "stock_code": holding["stock_code"],
        "stock_name": holding["stock_name"],
        "quantity": quantity,
        "profit_rate": profit_rate,
        "reason": reason,
        "order_type_code": order_type_code,
        "order_price": exit_price,
    }


def _safe_budget_amount(
    evaluation_record: dict[str, Any],
    *,
    position_budget_pct: int,
) -> int:
    """Estimate a safe per-position budget from account evaluation data."""

    total_estimated = _to_price(_pick_first(evaluation_record, "prsm_dpst_aset_amt", "aset_evlt_amt")) or 0
    cash_available = _to_price(_pick_first(evaluation_record, "entr", "d2_entra", "ord_psbl_amt")) or 0
    base_amount = total_estimated or cash_available
    target_budget = floor(base_amount * (position_budget_pct / 100))
    if cash_available > 0:
        target_budget = min(target_budget, cash_available)
    return max(target_budget, 0)


async def _execute_strategy_actions(
    client: KiwoomClient,
    *,
    planned_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Execute the planned actions as mock orders."""

    executions = []
    for action in planned_actions:
        if action["action"] == "buy":
            result = await order.place_stock_buy_order(
                client,
                stk_cd=action["stock_code"],
                ord_qty=str(action["quantity"]),
                order_type_code=action["order_type_code"],
                ord_uv=action["order_price"],
            )
        elif action["action"] == "sell":
            result = await order.place_stock_sell_order(
                client,
                stk_cd=action["stock_code"],
                ord_qty=str(action["quantity"]),
                order_type_code=action["order_type_code"],
                ord_uv=action["order_price"],
            )
        else:
            continue
        executions.append(
            {
                "action": action,
                "order_result": result,
            }
        )
    return executions


async def plan_intraday_momentum_strategy(
    client: KiwoomClient,
    settings: Settings,
    *,
    watchlist: list[str] | None = None,
    leaders_limit: int = 10,
    candidate_limit: int = 5,
    max_positions: int = 3,
    max_new_positions: int = 1,
    position_budget_pct: int = 10,
    execute_orders: bool = False,
    confirm_mock_orders: bool = False,
    confirm_live_orders: bool = False,
    auto_buy_min_score: int = 14,
    candidate_scan_multiplier: int = 4,
    stock_detail_cache_ttl_seconds: float = 0.0,
    min_market_cap_krw: int = 0,
    leaders_market_tp: str = "000",
    day_change_min: float = 1.0,
    day_change_max: float = 29.5,
    entry_mode: str = "momentum",
    ma_period: int = 20,
    stop_loss_pct: float = -3.0,
    hard_take_profit_pct: float = 8.0,
    universe_mode: str = UNIVERSE_LEADERS,
    holding_observer: Callable[[list[dict[str, Any]]], Awaitable[None]] | None = None,
) -> dict[str, Any]:
    """Build and optionally execute a conservative intraday momentum strategy.

    ``min_market_cap_krw`` (>0) restricts new-entry candidates to large-caps
    (market cap ≥ threshold). Default 0 = filter off (legacy behaviour).
    ``leaders_market_tp`` scopes the leaderboards ("001" = KOSPI-only for the
    large-cap strategy); when it's KOSPI-only the universe sort leans on
    거래대금(value) rank instead of 등락률(gainers).

    ``stop_loss_pct``/``hard_take_profit_pct`` only affect the holding-review
    output (`holding_actions`/sell `planned_actions`) computed here — the
    live watcher's Tier1 hard exits are a separate, independently
    parameterized code path (see `watcher_triggers.detect_tier1_holding_rules`
    and `main_watcher.py`'s `--stop-loss-pct`/`--hard-take-profit-pct`) and
    never call this function. Defaults mirror `main_watcher.py`'s CLI
    defaults; pass the live deployment's actual values (see
    k8s/kiwoom-watcher.yaml) to mirror them exactly for inspection.
    """

    evaluation_result = await account.get_account_evaluation(client)
    evaluation_record, holdings = _normalize_holding_rows(evaluation_result)
    if holding_observer is not None and evaluation_result.get("success"):
        await holding_observer(holdings)
    unexecuted_result = await account.get_unexecuted_orders(client, "0", "0", "1")
    open_order_codes = _extract_open_order_codes(unexecuted_result)

    merged_watchlist = _sanitize_watchlist(watchlist, holdings)
    snapshot = await market.get_market_snapshot(
        client,
        watchlist=merged_watchlist,
        leaders_limit=leaders_limit,
        stock_detail_cache_ttl_seconds=stock_detail_cache_ttl_seconds,
        leaders_market_tp=leaders_market_tp,
    )
    regime = _build_market_regime(snapshot, leaders_market_tp=leaders_market_tp)

    detail_cache: dict[str, dict[str, Any]] = {}
    for detail in snapshot.get("watchlist_details", []):
        stock_code = detail.get("stock_code")
        if stock_code:
            detail_cache[stock_code] = detail

    holding_actions = []
    for holding in holdings:
        stock_code = holding["stock_code"]
        detail = detail_cache.get(stock_code)
        if detail is None:
            detail = await market.get_stock_detail_bundle(
                client,
                stock_code=stock_code,
                cache_ttl_seconds=stock_detail_cache_ttl_seconds,
            )
            detail_cache[stock_code] = detail
        holding_actions.append(
            _review_holding(
                holding,
                detail,
                regime,
                stop_loss_pct=stop_loss_pct,
                hard_take_profit_pct=hard_take_profit_pct,
            )
        )

    carryover_path = _carryover_path(settings)
    carryover_codes = _load_carryover(carryover_path)
    # `below_ma` buys quiet dips, which by construction are not on a movers
    # leaderboard; scanning only leaders hid ~9 in-band large caps a day
    # (§10.2). The roster is also exactly what backtest/ measures, so live
    # and backtest describe one strategy only in roster/both mode.
    universe = _merge_leaderboards(
        snapshot,
        carryover_codes=carryover_codes,
        value_first=(leaders_market_tp != "000"),
        roster_codes=(
            ROSTER_CODES if universe_mode in (UNIVERSE_ROSTER, UNIVERSE_BOTH) else None
        ),
        include_leaders=(universe_mode != UNIVERSE_ROSTER),
    )
    candidate_rows = []
    skipped_candidates = []

    # Holdings come back as "A105560" while the roster and leaderboards use
    # the bare six digits, so a raw comparison never matches and a held
    # name reads as brand new.
    held_codes = {normalize_stock_code(h["stock_code"]) for h in holdings}
    safe_budget = _safe_budget_amount(
        evaluation_record,
        position_budget_pct=position_budget_pct,
    )
    available_slots = max(max_positions - len(holdings), 0)
    buy_slots = min(available_slots, max_new_positions)

    scan_limit = max(candidate_limit * max(candidate_scan_multiplier, 1), candidate_limit)
    for candidate in universe[:scan_limit]:
        stock_code = candidate["stock_code"]
        if normalize_stock_code(stock_code) in held_codes:
            skipped_candidates.append(
                {
                    "stock_code": stock_code,
                    "stock_name": candidate["stock_name"],
                    "reason": "이미 보유 중",
                }
            )
            continue
        if stock_code in open_order_codes:
            skipped_candidates.append(
                {
                    "stock_code": stock_code,
                    "stock_name": candidate["stock_name"],
                    "reason": "기존 미체결 주문 존재",
                }
            )
            continue

        detail = detail_cache.get(stock_code)
        if detail is None:
            detail = await market.get_stock_detail_bundle(
                client,
                stock_code=stock_code,
                bar_limit=max(ma_period + 5, 5),  # enough closes for the MA
                cache_ttl_seconds=stock_detail_cache_ttl_seconds,
            )
            detail_cache[stock_code] = detail

        eligible, scored = _score_candidate(
            candidate,
            detail,
            regime,
            min_market_cap_krw=min_market_cap_krw,
            day_change_min=day_change_min,
            day_change_max=day_change_max,
            entry_mode=entry_mode,
            ma_period=ma_period,
        )
        candidate_rows.append(scored)

        if not eligible or buy_slots <= 0:
            continue

        entry_price = _to_price(scored.get("entry_price"))
        if not entry_price or safe_budget <= 0:
            skipped_candidates.append(
                {
                    "stock_code": stock_code,
                    "stock_name": candidate["stock_name"],
                    "reason": "주문 가능 예산 부족",
                }
            )
            continue

        quantity = floor(safe_budget / entry_price)
        if quantity < 1:
            skipped_candidates.append(
                {
                    "stock_code": stock_code,
                    "stock_name": candidate["stock_name"],
                    "reason": "주문 수량이 1주 미만",
                }
            )
            continue

        # Operational PM gate (2026-04-24, SWO-122/135/156): only auto-buy
        # when score meets the high-confidence threshold. Lower-score eligible
        # rows still appear in `candidate_rows` for human/PM review but do
        # not generate `planned_action` entries — preventing
        # `--execute-orders` from auto-buying PM-rejected candidates.
        if scored["score"] < auto_buy_min_score:
            scored["auto_buy_blocked_reason"] = (
                f"score {scored['score']} < auto_buy_min_score {auto_buy_min_score}"
            )
            continue

        scored["planned_action"] = {
            "action": "buy",
            "priority": 50 + scored["score"],
            "stock_code": stock_code,
            "stock_name": candidate["stock_name"],
            "quantity": quantity,
            "order_type_code": scored["entry_order_type_code"],
            "order_price": scored["entry_price"],
            "reason": "유동성/추세/호가 우위 조건 충족",
            "score": scored["score"],
        }
        buy_slots -= 1

    planned_actions = [
        {
            "action": action["action"],
            "priority": action["priority"],
            "stock_code": action["stock_code"],
            "stock_name": action["stock_name"],
            "quantity": action["quantity"],
            "order_type_code": action["order_type_code"],
            "order_price": action["order_price"],
            "reason": action["reason"],
        }
        for action in holding_actions
        if action["action"] == "sell"
    ]
    planned_actions.extend(
        row["planned_action"]
        for row in candidate_rows
        if isinstance(row.get("planned_action"), dict)
    )
    planned_actions.sort(key=lambda item: (-item["priority"], item["stock_code"]))

    # Persist this cycle's eligible-but-not-bought codes so the next cycle can
    # re-score them even if they roll off the live leaderboards. Top eligible
    # rows by score (so we carry the strongest near-misses, not stale clutter).
    carry_codes = [
        row["stock_code"]
        for row in sorted(
            (r for r in candidate_rows if r.get("eligible")),
            key=lambda r: -int(r.get("score") or 0),
        )
        if not isinstance(row.get("planned_action"), dict)  # exclude already-bought
    ]
    _save_carryover(carryover_path, carry_codes)

    executed_orders: list[dict[str, Any]] = []
    execution_allowed = execute_orders and (
        (settings.use_mock and confirm_mock_orders)
        or ((not settings.use_mock) and confirm_live_orders)
    )
    if execute_orders and not execution_allowed:
        executed_orders.append(
            {
                "action": None,
                "order_result": {
                    "success": False,
                    "message": "주문 실행 확인이 없어 전략 주문을 전송하지 않았습니다",
                },
            }
        )
    elif execution_allowed:
        executed_orders = await _execute_strategy_actions(
            client,
            planned_actions=planned_actions,
        )

    # Defensive summary so JSON consumers cannot misread an empty
    # `executed_orders` list as "nothing happened" (SWO-122 RC2).
    succeeded = sum(
        1 for e in executed_orders
        if (e.get("order_result") or {}).get("success") is True
    )
    failed = sum(
        1 for e in executed_orders
        if (e.get("order_result") or {}).get("success") is False
    )
    execution_summary = {
        "execution_requested": bool(execute_orders),
        "execution_allowed": bool(execution_allowed),
        "orders_planned": len(planned_actions),
        "orders_attempted": len(executed_orders),
        "orders_succeeded": succeeded,
        "orders_failed": failed,
    }

    return {
        "success": evaluation_result.get("success", False) and snapshot.get("success", False),
        "degraded_sources": _degraded_sources(evaluation_result, snapshot),
        "strategy_name": "krx_intraday_momentum_v1",
        "generated_at": datetime.now(KST).isoformat(),
        "environment": {
            "mode": "mock" if settings.use_mock else "live",
            "execution_allowed": execution_allowed,
        },
        "regime": regime,
        "portfolio": {
            "estimated_assets": _to_price(_pick_first(evaluation_record, "prsm_dpst_aset_amt", "aset_evlt_amt")),
            "cash_available": _to_price(_pick_first(evaluation_record, "entr", "d2_entra")),
            # Same cash, different settlement basis. `entr` is today's
            # deposit; `d2_entra` is the D+2 estimate, which is what
            # `estimated_assets` (prsm_dpst_aset_amt) is also built on. A
            # sale credits D+2 immediately and `entr` only on settlement, so
            # between them sits the unsettled proceeds. Report both or the
            # gap reads as a position — see the serializer in watcher.py.
            "cash_d2": _to_price(_pick_first(evaluation_record, "d2_entra")),
            # Account-level P&L for today, straight off kt00004. `_to_int`,
            # not `_to_price` — the latter takes abs() and the sign is the
            # whole point here. Per kiwoom_api_spec.md `tdy_lspft` is
            # 당일투자손익; `tdy_lspft_amt` is 당일투자*원금* and is NOT this.
            # Consumed by services/daily_risk.py; see that module for the
            # documented limits of these fields.
            "daily_pl_krw": _to_int(_pick_first(evaluation_record, "tdy_lspft")),
            "daily_pl_pct_broker": _to_float(
                _pick_first(evaluation_record, "tdy_lspft_rt")
            ),
            "holding_count": len(holdings),
            "open_order_count": len(open_order_codes),
            "position_budget": safe_budget,
            "max_positions": max_positions,
            "max_new_positions": max_new_positions,
        },
        "holdings": holdings,
        "holding_actions": holding_actions,
        "candidate_rows": candidate_rows,
        "skipped_candidates": skipped_candidates,
        "planned_actions": planned_actions,
        "executed_orders": executed_orders,
        "execution_summary": execution_summary,
        "market_snapshot": {
            "indices": snapshot.get("indices", {}),
            "leaders": snapshot.get("leaders", {}),
            "sector_rows": snapshot.get("sector_rows", []),
        },
        "message": "Built intraday strategy plan"
        if not execution_allowed
        else "Built and executed intraday strategy plan",
    }


__all__ = ["plan_intraday_momentum_strategy"]
