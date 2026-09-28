"""Pure entry rules shared by live scoring and daily-bar research."""

from math import isfinite

BELOW_MA_MAX_DIP_PCT = 5.0


def moving_average_discount(price: float | None, average: float | None) -> float | None:
    """Return the percentage below the MA, or None for untrustworthy inputs."""

    if price is None or average is None:
        return None
    if not isfinite(price) or not isfinite(average) or price <= 0 or average <= 0:
        return None
    return (average - price) / average * 100


def is_shallow_dip(
    price: float,
    average: float,
    *,
    minimum_pct: float = 0.0,
    maximum_pct: float = BELOW_MA_MAX_DIP_PCT,
) -> bool:
    """Require a positive, bounded discount rather than an unrestricted downtrend."""

    discount = moving_average_discount(price, average)
    return discount is not None and minimum_pct < discount <= maximum_pct
