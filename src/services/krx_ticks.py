"""KRX stock tick sizes (호가가격단위), as revised on 2023-01-25.

KOSPI and KOSDAQ share one table since that revision. ETFs and ETNs follow a
different one (1원 under 2,000원, 5원 above).

Every band's lower bound is a multiple of that band's own tick, so flooring a
price inside its band always lands on a valid price.
"""

from __future__ import annotations

from math import floor, isfinite

# (exclusive upper bound, tick) in ascending order; prices at or above the
# last bound use `_TOP_TICK`.
_STOCK_TICK_BANDS: tuple[tuple[int, int], ...] = (
    (2_000, 1),
    (5_000, 5),
    (20_000, 10),
    (50_000, 50),
    (200_000, 100),
    (500_000, 500),
)
_TOP_TICK = 1_000


def stock_tick_size(price: int) -> int:
    """The tick that applies to an order priced at ``price`` KRW."""

    if price <= 0:
        raise ValueError(f"price must be positive: {price!r}")
    for bound, tick in _STOCK_TICK_BANDS:
        if price < bound:
            return tick
    return _TOP_TICK


def floor_to_stock_tick(price: float) -> int:
    """The highest valid stock order price at or below ``price``."""

    if not isfinite(price) or price < 1:
        raise ValueError(f"price must be at least 1 KRW: {price!r}")
    whole = floor(price)
    return whole - whole % stock_tick_size(whole)


def floor_to_etf_tick(price: float) -> int:
    """KRX ETF/ETN price units, distinct from the ordinary-stock table."""
    if not isfinite(price) or price < 1:
        raise ValueError(f"price must be at least 1 KRW: {price!r}")
    whole = floor(price)
    tick = 1 if whole < 2000 else 5
    return whole - whole % tick


__all__ = ["floor_to_stock_tick", "stock_tick_size", "floor_to_etf_tick"]
