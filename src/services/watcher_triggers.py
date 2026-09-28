"""Pure trigger-detection logic for the intraday watcher.

These functions take cycle snapshots (holdings, regime, candidate rows,
open orders, prior state) and return ``TriggerEvent`` lists. They never
touch the network, file system, or order routing — keeping the rules
unit-testable in isolation.

Two tiers:

* **Tier 1** (``tier=1``) — fires for hard, deterministic rules that the
  watcher executes immediately in code (stop-loss, hard take-profit,
  ``max_positions`` overflow, stale unfilled order). No agent consult.
* **Tier 2** (``tier=2``) — fires for soft judgments that the watcher
  hands off to a Multica agent. The ``target_role`` field selects which
  agent: ``evaluator`` for holdings, ``screener`` for candidates,
  ``pm`` for portfolio-level events, ``risk`` for infra/health events.

Trigger granularity follows the user's "종목별로" decision: per-stock
triggers carry ``scope='stock'`` and a ``stock_code``, portfolio-level
triggers carry ``scope='global'``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .order_ledger import parse_broker_time

log = logging.getLogger("kiwoom.watcher.triggers")

KST = ZoneInfo("Asia/Seoul")

ROLE_SELF = "self"            # tier 1 — code executes itself
ROLE_EVALUATOR = "evaluator"  # 투자 평가사
ROLE_SCREENER = "screener"    # 종목 스크리너
ROLE_PM = "pm"                # 포트폴리오 매니저
ROLE_RISK = "risk"            # 리스크 매니저


@dataclass(slots=True)
class TriggerEvent:
    """One trigger fired during a watcher tick."""

    trigger_type: str
    tier: int
    scope: str  # "stock" | "global"
    target_role: str
    stock_code: str | None
    stock_name: str | None
    snapshot: dict[str, Any]
    detected_at: datetime
    reason: str
    suggested_action: str | None = None  # tier-1 hint: "sell_market" | "cancel_order"
    metadata: dict[str, Any] = field(default_factory=dict)

    def scope_key(self) -> str:
        """Lock key for in-flight de-duplication."""

        if self.scope == "stock" and self.stock_code:
            return f"stock:{self.stock_code}"
        return f"global:{self.target_role}"

    def cooldown_key(self) -> str:
        """Key used to suppress re-fires of the same trigger."""

        return f"{self.scope_key()}|{self.trigger_type}"


def _to_float(value: Any) -> float | None:
    """Convert a Kiwoom numeric field to a float. Mirrors strategy._to_float."""

    if value in (None, ""):
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


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(KST)


# ---------------------------------------------------------------------------
# Tier 1 — code immediate execution
# ---------------------------------------------------------------------------


def detect_tier1_holding_rules(
    holdings: list[dict[str, Any]],
    *,
    stop_loss_pct: float,
    hard_take_profit_pct: float,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Return one trigger per holding that hit a hard exit threshold."""

    out: list[TriggerEvent] = []
    ts = _now(now)
    for holding in holdings:
        rate = _to_float(holding.get("profit_rate"))
        if rate is None:
            continue
        code = holding.get("stock_code") or ""
        name = holding.get("stock_name") or code
        snapshot = {
            "profit_rate": rate,
            "quantity": holding.get("quantity"),
            "current_price": holding.get("current_price"),
            "avg_price": holding.get("avg_price"),
        }
        if rate <= stop_loss_pct:
            out.append(
                TriggerEvent(
                    trigger_type="stop_loss",
                    tier=1,
                    scope="stock",
                    target_role=ROLE_SELF,
                    stock_code=code,
                    stock_name=name,
                    snapshot=snapshot,
                    detected_at=ts,
                    reason=f"손절선 hit ({rate:.2f}% <= {stop_loss_pct}%)",
                    suggested_action="sell_market",
                )
            )
        elif rate >= hard_take_profit_pct:
            out.append(
                TriggerEvent(
                    trigger_type="hard_take_profit",
                    tier=1,
                    scope="stock",
                    target_role=ROLE_SELF,
                    stock_code=code,
                    stock_name=name,
                    snapshot=snapshot,
                    detected_at=ts,
                    reason=f"하드 익절 hit ({rate:.2f}% >= {hard_take_profit_pct}%)",
                    suggested_action="sell_market",
                )
            )
    return out


def detect_tier1_position_overflow(
    holdings: list[dict[str, Any]],
    *,
    max_positions: int,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Trigger when current holdings exceed the configured cap.

    Picks the weakest performer to liquidate (lowest ``profit_rate``).
    """

    if len(holdings) <= max_positions:
        return []

    sortable: list[tuple[float, dict[str, Any]]] = []
    for h in holdings:
        rate = _to_float(h.get("profit_rate"))
        sortable.append((rate if rate is not None else 0.0, h))
    sortable.sort(key=lambda item: item[0])

    weakest = sortable[0][1]
    code = weakest.get("stock_code") or ""
    name = weakest.get("stock_name") or code
    return [
        TriggerEvent(
            trigger_type="max_positions_overflow",
            tier=1,
            scope="stock",
            target_role=ROLE_SELF,
            stock_code=code,
            stock_name=name,
            snapshot={
                "profit_rate": _to_float(weakest.get("profit_rate")),
                "quantity": weakest.get("quantity"),
                "holding_count": len(holdings),
                "max_positions": max_positions,
            },
            detected_at=_now(now),
            reason=(
                f"보유 {len(holdings)}개 > max_positions {max_positions} — "
                f"약체 종목 정리"
            ),
            suggested_action="sell_market",
        )
    ]


def detect_tier1_stale_orders(
    open_orders: list[dict[str, Any]],
    *,
    stale_minutes: int,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Trigger cancellation for orders open longer than ``stale_minutes``.

    Timestamps come from ``order_ledger.parse_broker_time``, the one parser
    that already knows what each query actually sends. This used to read
    ``ord_tm``/``ord_tmd`` directly and ka10075 sends neither -- its rows
    carry ``tm`` (documented as such in ``kiwoom_api_spec.md``). So every
    real open order failed to parse and was skipped in silence, and this
    Tier-1 rule had never once fired in production: on 2026-09-04 a limit
    buy rested from 15:22 and the loop ran past the 5-minute threshold until
    15:29, yet nothing cancelled it -- the exchange did, at the close.

    The unit tests missed it because their fixtures used the field names the
    parser looked for rather than the ones the broker sends.
    """

    if stale_minutes <= 0:
        return []

    ts = _now(now)
    today = ts.date()
    out: list[TriggerEvent] = []
    for row in open_orders or []:
        if not isinstance(row, dict):
            continue
        order_no = str(row.get("ord_no") or row.get("orig_ord_no") or "").strip()
        if not order_no:
            continue
        code = str(row.get("stk_cd") or row.get("code") or "").strip()
        name = str(row.get("stk_nm") or row.get("item_nm") or code).strip()
        order_dt, _day = parse_broker_time(row, reference_day=today)
        if order_dt is None:
            # Unreadable time means unknown age. Cancelling on a guess is the
            # worse error, so the order is left alone -- but say so, because
            # this branch is how the rule stayed silently dead for months.
            log.warning(
                "stale-order check skipped %s (%s): no readable order time in %s",
                order_no,
                code or "?",
                sorted(row),
            )
            continue
        age = (ts - order_dt).total_seconds() / 60.0
        if age < stale_minutes:
            continue
        out.append(
            TriggerEvent(
                trigger_type="stale_unfilled_order",
                tier=1,
                scope="stock",
                target_role=ROLE_SELF,
                stock_code=code or None,
                stock_name=name,
                snapshot={
                    "order_no": order_no,
                    "stock_code": code,
                    "age_minutes": round(age, 1),
                    "qty": row.get("ord_qty") or row.get("oso_qty"),
                    "price": row.get("ord_uv") or row.get("oso_uv"),
                },
                detected_at=ts,
                reason=f"미체결 {age:.1f}분 (>= {stale_minutes}분) — 자동 취소",
                suggested_action="cancel_order",
                metadata={"order_no": order_no},
            )
        )
    return out


# ---------------------------------------------------------------------------
# Tier 2 — agent consult (per stock)
# ---------------------------------------------------------------------------


def detect_tier2_holding_swings(
    holdings: list[dict[str, Any]],
    prev_holdings: dict[str, dict[str, Any]],
    *,
    swing_pct: float,
    high_drop_pct: float,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Holdings that swung >= ``swing_pct`` since the last tick or that
    fell ``high_drop_pct`` below their intraday high."""

    out: list[TriggerEvent] = []
    ts = _now(now)
    for holding in holdings:
        code = holding.get("stock_code") or ""
        name = holding.get("stock_name") or code
        if not code:
            continue
        cur = _to_float(holding.get("current_price"))
        if cur is None:
            continue

        prev = prev_holdings.get(code) or {}
        prev_price = _to_float(prev.get("current_price"))
        delta_pct: float | None = None
        if prev_price and prev_price > 0:
            delta_pct = (cur - prev_price) / prev_price * 100

        # Intraday-high drop is computed from the high price the watcher
        # is currently observing — pulled from the watcher snapshot.
        high = _to_float(holding.get("intraday_high"))
        drop_from_high_pct: float | None = None
        if high and high > 0:
            drop_from_high_pct = (high - cur) / high * 100

        reason_bits: list[str] = []
        if delta_pct is not None and abs(delta_pct) >= swing_pct:
            reason_bits.append(f"틱 변동 {delta_pct:+.2f}%")
        if drop_from_high_pct is not None and drop_from_high_pct >= high_drop_pct:
            reason_bits.append(
                f"고점 이탈 -{drop_from_high_pct:.2f}% (>= {high_drop_pct}%)"
            )
        if not reason_bits:
            continue

        out.append(
            TriggerEvent(
                trigger_type="holding_swing",
                tier=2,
                scope="stock",
                target_role=ROLE_EVALUATOR,
                stock_code=code,
                stock_name=name,
                snapshot={
                    "current_price": cur,
                    "prev_price": prev_price,
                    "delta_pct": delta_pct,
                    "intraday_high": high,
                    "drop_from_high_pct": drop_from_high_pct,
                    "profit_rate": _to_float(holding.get("profit_rate")),
                    "quantity": holding.get("quantity"),
                },
                detected_at=ts,
                reason=" / ".join(reason_bits),
            )
        )
    return out


def detect_tier2_new_candidates(
    candidate_rows: list[dict[str, Any]],
    prev_codes: set[str],
    *,
    min_score: int,
    available_slots: int,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Newly-qualifying candidates with score >= threshold, up to slot budget.

    A candidate is "new" if it wasn't in ``prev_codes`` last tick. The caller
    passes the codes that *qualified* last tick, not the ones it scanned:
    with a fixed roster universe every code is scanned on every tick, so a
    scanned-set would mark all of them un-new after the first tick and this
    detector would never fire again. Re-fire spacing is the per-stock
    cooldown's responsibility, not this set's.

    We cap the number emitted by ``available_slots`` so the screener isn't
    consulted about names we cannot buy anyway.
    """

    if available_slots <= 0:
        return []

    ts = _now(now)
    out: list[TriggerEvent] = []
    eligible_rows = [
        row
        for row in candidate_rows or []
        if isinstance(row, dict)
        and row.get("eligible")
        and (row.get("score") or 0) >= min_score
    ]
    eligible_rows.sort(key=lambda row: -(row.get("score") or 0))
    for row in eligible_rows[:available_slots]:
        code = row.get("stock_code") or ""
        if not code or code in prev_codes:
            continue
        out.append(
            TriggerEvent(
                trigger_type="new_candidate",
                tier=2,
                scope="stock",
                target_role=ROLE_SCREENER,
                stock_code=code,
                stock_name=row.get("stock_name") or code,
                snapshot=_candidate_snapshot(row),
                detected_at=ts,
                reason=_candidate_reason(row),
            )
        )
    return out


def _candidate_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    """What the screener sees about a candidate — and what the buy path reads back.

    `score`, `sources`, `current_price` and `entry_*` are not only for the
    agent: the watcher rescores from this dict right before buying (sources
    carry the source bonus) and prices the stale check off `current_price`.

    The below_ma fields are the entry thesis itself. The snapshot used to
    carry momentum-era `breakout`/`high_price` instead and drop `ma_dip_pct`,
    so the screener was asked to judge a MA20 pullback without the MA20 and
    kept deferring for lack of evidence (2026-09-10, 09-15, 09-21).
    """

    return {
        "score": row.get("score"),
        "ma_dip_pct": row.get("ma_dip_pct"),
        "ma_period": row.get("ma_period"),
        "ma_value": row.get("ma_value"),
        "volume_ratio_20d": row.get("volume_ratio_20d"),
        "upper_limit_distance_pct": row.get("upper_limit_distance_pct"),
        "market_cap_krw": row.get("market_cap_krw"),
        "day_change_pct": row.get("day_change_pct"),
        "orderbook_ratio": row.get("orderbook_ratio"),
        "spread_pct": row.get("spread_pct"),
        "current_price": row.get("current_price"),
        "sources": row.get("sources"),
        "entry_order_type_code": row.get("entry_order_type_code"),
        "entry_price": row.get("entry_price"),
    }


def _candidate_reason(row: dict[str, Any]) -> str:
    dip = row.get("ma_dip_pct")
    if isinstance(dip, (int, float)):
        where = f"MA{row.get('ma_period') or 20} {dip:.2f}% 하회"
    else:
        where = f"day_change={row.get('day_change_pct')}%"
    return f"신규 강한 후보 (score={row.get('score')}, {where})"


# ---------------------------------------------------------------------------
# Tier 2 — agent consult (global)
# ---------------------------------------------------------------------------


def _regime_is_confident(regime: dict[str, Any] | None) -> bool:
    """True when the regime rests on a complete index read.

    Defaults to True for regimes built before this flag existed (and for the
    hand-built dicts in tests), so absence never silences a trigger.
    """

    return bool((regime or {}).get("market_data_complete", True))


def detect_tier2_regime_label_flip(
    regime: dict[str, Any],
    prev_stable_regime: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Fire when the regime label transitions away from a stable baseline.

    The watcher passes ``prev_stable_regime=None`` while the new label is
    still being debounced; once the label has held across the configured
    stability window the watcher passes the prior stable regime here and
    we emit. extreme_risk_off transitions are handled separately because
    they need to fire immediately without waiting for debounce.
    """

    ts = _now(now)
    out: list[TriggerEvent] = []
    if not _regime_is_confident(regime):
        # A zeroed index read lands on "risk_off", so dispatching here would
        # page the PM squad about a market move that never happened.
        return out
    cur_label = (regime or {}).get("regime")
    prev_label = (prev_stable_regime or {}).get("regime") if prev_stable_regime else None
    if prev_label and cur_label and prev_label != cur_label:
        out.append(
            TriggerEvent(
                trigger_type="regime_flip",
                tier=2,
                scope="global",
                target_role=ROLE_PM,
                stock_code=None,
                stock_name=None,
                snapshot={"regime": regime, "prev_stable_regime": prev_stable_regime},
                detected_at=ts,
                reason=f"regime {prev_label} -> {cur_label}",
            )
        )
    return out


def _was_extreme(regime: dict[str, Any] | None) -> bool:
    """Was this regime extreme, counting the hysteresis band as still extreme.

    ``extreme_risk_off_sticky`` is evaluated at the exit thresholds, so a tick
    inside the band reports False for the entry flag and True here. Absent —
    regimes built before the flag, and the hand-built dicts in tests — it
    falls back to the plain flag, so behaviour is unchanged where it is not
    published.
    """

    if not regime:
        return False
    if "extreme_risk_off_sticky" in regime:
        return bool(regime["extreme_risk_off_sticky"]) or bool(
            regime.get("extreme_risk_off")
        )
    return bool(regime.get("extreme_risk_off"))


def detect_tier2_extreme_risk_off(
    regime: dict[str, Any],
    prev_regime: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Fire on the rising edge of extreme_risk_off, with exit hysteresis.

    No debounce on the way *in* — a crash signal must be delivered the cycle
    it appears. Requires a complete index read: `extreme_risk_off` is
    deliberately also set by a failed read so new entries stay vetoed, but
    that flavour is a data outage, not a crash, and must not page the PM
    squad (2026-07-29/30). The entry veto is unaffected — it does not run
    through this detector.

    The edge is armed again only once the market clears the *exit* band, not
    merely the entry line. A metric parked on the threshold otherwise pages
    the squad every time it wobbles across: on 2026-09-02 primary_breadth sat
    at 0.19 against a 0.20 threshold and produced 8 rising edges in a
    session, each one appending to a day-scoped issue that every later run
    re-read, which is what exhausted the codex quota. Sticky readings are
    still extreme for every other purpose — they just are not *new*.
    """

    ts = _now(now)
    if not _regime_is_confident(regime):
        return []
    cur_extreme = bool((regime or {}).get("extreme_risk_off"))
    # Only a *confident* prior suppresses the edge. A degraded tick sets
    # extreme_risk_off for the entry veto; letting it stand as the baseline
    # would swallow the first real crash that follows an outage. Re-paging an
    # ongoing crash is the safe direction, and the watcher's per-trigger
    # cooldown drops the duplicate anyway.
    #
    # The prior counts as still-extreme when it was extreme by *either* band:
    # the sticky flag is what holds the state through the hysteresis band, and
    # falling back to the plain flag keeps older regimes (and hand-built test
    # dicts) working exactly as before.
    prev_extreme = _regime_is_confident(prev_regime) and _was_extreme(prev_regime)
    if not (cur_extreme and not prev_extreme):
        return []
    return [
        TriggerEvent(
            trigger_type="extreme_risk_off",
            tier=2,
            scope="global",
            target_role=ROLE_PM,
            stock_code=None,
            stock_name=None,
            snapshot={"regime": regime, "prev_regime": prev_regime},
            detected_at=ts,
            reason="극단적 시장 약세 진입",
        )
    ]


# Backward-compat alias — callers that still want the combined behavior.
def detect_tier2_regime_flip(
    regime: dict[str, Any],
    prev_regime: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Combined label-flip + extreme-risk-off detection (legacy callers)."""

    return (
        detect_tier2_regime_label_flip(regime, prev_regime, now=now)
        + detect_tier2_extreme_risk_off(regime, prev_regime, now=now)
    )


def detect_tier2_global_health(
    *,
    api_failure_count: int,
    open_order_count: int,
    api_failure_threshold: int,
    unfilled_threshold: int,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Infra-health triggers: consecutive API failures, unfilled order
    pile-up. Both routed to the risk manager agent."""

    ts = _now(now)
    out: list[TriggerEvent] = []
    if api_failure_count >= api_failure_threshold:
        out.append(
            TriggerEvent(
                trigger_type="api_failures",
                tier=2,
                scope="global",
                target_role=ROLE_RISK,
                stock_code=None,
                stock_name=None,
                snapshot={"api_failure_count": api_failure_count},
                detected_at=ts,
                reason=(
                    f"API 실패 {api_failure_count}회 연속 "
                    f"(>= {api_failure_threshold})"
                ),
            )
        )
    if open_order_count >= unfilled_threshold:
        out.append(
            TriggerEvent(
                trigger_type="unfilled_overflow",
                tier=2,
                scope="global",
                target_role=ROLE_RISK,
                stock_code=None,
                stock_name=None,
                snapshot={"open_order_count": open_order_count},
                detected_at=ts,
                reason=f"미체결 {open_order_count}건 누적 (>= {unfilled_threshold})",
            )
        )
    return out


def detect_tier2_periodic_review(
    last_review_at: datetime | None,
    *,
    interval_minutes: int,
    now: datetime | None = None,
) -> list[TriggerEvent]:
    """Safety-net periodic PM review fires every ``interval_minutes``.

    Returns the trigger when the elapsed wall-clock since the last
    periodic review meets the interval. The watcher is responsible for
    updating ``last_review_at`` after dispatch.
    """

    ts = _now(now)
    if last_review_at is not None:
        if ts - last_review_at < timedelta(minutes=interval_minutes):
            return []
    return [
        TriggerEvent(
            trigger_type="periodic_review",
            tier=2,
            scope="global",
            target_role=ROLE_PM,
            stock_code=None,
            stock_name=None,
            snapshot={"interval_minutes": interval_minutes},
            detected_at=ts,
            reason=f"{interval_minutes}분 정기 점검",
        )
    ]


__all__ = [
    "ROLE_EVALUATOR",
    "ROLE_PM",
    "ROLE_RISK",
    "ROLE_SCREENER",
    "ROLE_SELF",
    "TriggerEvent",
    "detect_tier1_holding_rules",
    "detect_tier1_position_overflow",
    "detect_tier1_stale_orders",
    "detect_tier2_extreme_risk_off",
    "detect_tier2_global_health",
    "detect_tier2_holding_swings",
    "detect_tier2_new_candidates",
    "detect_tier2_periodic_review",
    "detect_tier2_regime_flip",
    "detect_tier2_regime_label_flip",
]
