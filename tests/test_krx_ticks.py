"""KRX stock tick table (2023-01-25 revision) and flooring onto it."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from src.services.krx_ticks import floor_to_stock_tick, stock_tick_size  # noqa: E402


@pytest.mark.parametrize(
    "price,tick",
    [
        (1, 1),
        (1_999, 1),
        (2_000, 5),
        (4_999, 5),
        (5_000, 10),
        (19_999, 10),
        (20_000, 50),
        (49_999, 50),
        (50_000, 100),
        (199_999, 100),
        (200_000, 500),
        (499_999, 500),
        (500_000, 1_000),
        (1_863_000, 1_000),
    ],
)
def test_tick_size_at_every_band_edge(price, tick):
    assert stock_tick_size(price) == tick


@pytest.mark.parametrize(
    "price,expected",
    [
        # 286,500 x 1.015 — the auction cap for a 삼성전자-priced entry.
        (290_797.5, 290_500),
        # Just under a band edge keeps the finer tick of its own band.
        (199_950, 199_900),
        # Just over it floors onto the coarser tick, landing on the edge.
        (200_300, 200_000),
        (21_249.9, 21_200),
        (1_891_000, 1_891_000),
        (4_999.99, 4_995),
    ],
)
def test_floor_lands_on_a_valid_price_at_or_below(price, expected):
    assert floor_to_stock_tick(price) == expected


def test_floor_is_valid_and_within_one_tick_across_the_whole_table():
    for price in range(1, 2_500_000, 997):
        for value in (price, price + 0.5):
            floored = floor_to_stock_tick(value)
            assert floored <= value
            assert floored % stock_tick_size(floored) == 0
            assert value - floored < stock_tick_size(math.floor(value))


@pytest.mark.parametrize("bad", [0, -100, 0.5, float("nan"), float("inf")])
def test_non_positive_or_non_finite_prices_are_refused(bad):
    with pytest.raises(ValueError):
        floor_to_stock_tick(bad)


def test_tick_size_refuses_non_positive_prices():
    with pytest.raises(ValueError):
        stock_tick_size(0)
