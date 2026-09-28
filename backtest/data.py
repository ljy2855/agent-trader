"""Fetch + cache daily bars for the backtest universe.

Run this once (in-cluster, where the Kiwoom API is reachable) to populate
``backtest/cache/<code>.json``; the engine then runs offline against the
cache so parameter sweeps don't re-hit the API.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CACHE_DIR = Path(__file__).parent / "cache"
KST = ZoneInfo("Asia/Seoul")

# The roster lives in src/ so the live watcher (which does not ship
# backtest/) and this harness scan the same names — otherwise the
# backtest measures a strategy live never runs. See that module for
# why a movers leaderboard is the wrong universe for below_ma.
from src.constants.universe import KOSPI_LARGECAP  # noqa: E402


async def fetch_universe(client, base_date: str | None = None) -> dict[str, list[dict]]:
    """Fetch ka10081 daily charts for the universe and cache them."""
    from src.services.market import get_stock_daily_chart

    base = base_date or datetime.now(KST).strftime("%Y%m%d")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    series: dict[str, list[dict]] = {}
    for code, name in KOSPI_LARGECAP.items():
        try:
            r = await get_stock_daily_chart(client, stock_code=code, base_date=base)
            bars = r.get("daily_chart") or []
            if bars:
                (CACHE_DIR / f"{code}.json").write_text(
                    json.dumps(bars, ensure_ascii=False)
                )
                series[code] = bars
                print(f"  {name}({code}): {len(bars)} bars cached")
            else:
                print(f"  {name}({code}): no data")
        except Exception as e:  # noqa: BLE001 - best-effort fetch
            print(f"  {name}({code}): ERROR {str(e)[:60]}")
    return series


def load_cache() -> dict[str, list[dict]]:
    """Load all cached daily-bar series (offline; for sweeps)."""
    series: dict[str, list[dict]] = {}
    if not CACHE_DIR.exists():
        return series
    for f in CACHE_DIR.glob("*.json"):
        if f.stem.endswith("_supply"):
            continue
        series[f.stem] = json.loads(f.read_text())
    return series


SUPPLY_DIR = CACHE_DIR  # supply cached as <code>_supply.json alongside bars


async def fetch_supply(client, base_date: str | None = None) -> dict[str, list[dict]]:
    """Fetch ka10060 investor net-buy charts for the universe and cache them."""
    from src.services.market import get_investor_supply_chart

    base = base_date or datetime.now(KST).strftime("%Y%m%d")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, list[dict]] = {}
    for code, name in KOSPI_LARGECAP.items():
        try:
            r = await get_investor_supply_chart(client, stock_code=code, base_date=base)
            rows = r.get("supply_chart") or []
            if rows:
                (CACHE_DIR / f"{code}_supply.json").write_text(json.dumps(rows, ensure_ascii=False))
                out[code] = rows
                print(f"  {name}({code}): {len(rows)} supply rows cached")
            else:
                print(f"  {name}({code}): no supply data")
        except Exception as e:  # noqa: BLE001
            print(f"  {name}({code}): ERROR {str(e)[:60]}")
    return out


def load_supply_cache() -> dict[str, dict[str, dict]]:
    """Load cached supply series, keyed code → {date: row}."""
    out: dict[str, dict[str, dict]] = {}
    if not CACHE_DIR.exists():
        return out
    for f in CACHE_DIR.glob("*_supply.json"):
        code = f.stem[: -len("_supply")]
        rows = json.loads(f.read_text())
        out[code] = {str(r.get("dt")): r for r in rows if r.get("dt")}
    return out
