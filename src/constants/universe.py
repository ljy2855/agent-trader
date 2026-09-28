"""Fixed KOSPI large-cap roster used as a candidate universe.

The leaderboards (등락률·거래량·거래대금 상위) surface whatever *moved* today.
That is the right universe for a momentum entry and the wrong one for
`below_ma`, which wants names sitting quietly a few percent under their
moving average — almost the complement of a movers list. Measured on
2026-08-17: across 580 sessions at least one large cap sat inside the
`0 < dip <= 5%` band on 99% of them (median 9 names), yet the live watcher
surfaced zero eligible candidates on both sessions observed, because the
names in the band never reached the leaderboards.

This roster is also the universe `backtest/` has always measured, so live
and backtest describe the same strategy only when the watcher scans it.

No Kiwoom endpoint ranks by market cap (순위정보 is all momentum/flow
rankings), so the roster is maintained by hand. It is a fixed pool chosen
from today's large caps, which carries survivorship bias for *backtests* —
harmless when used forward as a live scan list, but the reason backtest
results over this pool should not be read as a clean historical estimate.
"""

from __future__ import annotations

# code -> name, roughly market-cap ordered. Names are for logs/readability;
# only the codes matter to the scanner.
KOSPI_LARGECAP: dict[str, str] = {
    "005930": "삼성전자", "000660": "SK하이닉스", "373220": "LG에너지솔루션",
    "207940": "삼성바이오로직스", "005380": "현대차", "000270": "기아",
    "068270": "셀트리온", "105560": "KB금융", "005490": "POSCO홀딩스",
    "035420": "NAVER", "012330": "현대모비스", "051910": "LG화학",
    "055550": "신한지주", "035720": "카카오", "006400": "삼성SDI",
    "028260": "삼성물산", "066570": "LG전자", "003670": "포스코퓨처엠",
    "096770": "SK이노베이션", "034730": "SK", "015760": "한국전력",
    "032830": "삼성생명", "017670": "SK텔레콤", "009150": "삼성전기",
    "316140": "우리금융지주", "086790": "하나금융지주", "010130": "고려아연",
    "011200": "HMM", "259960": "크래프톤", "012450": "한화에어로스페이스",
}

ROSTER_CODES: tuple[str, ...] = tuple(KOSPI_LARGECAP)

# Universe sources for the candidate scan.
UNIVERSE_LEADERS = "leaders"   # movers leaderboards only (momentum's universe)
UNIVERSE_ROSTER = "roster"     # the fixed large-cap roster only
UNIVERSE_BOTH = "both"         # roster first, then leaderboards
UNIVERSE_MODES = (UNIVERSE_LEADERS, UNIVERSE_ROSTER, UNIVERSE_BOTH)

__all__ = [
    "KOSPI_LARGECAP",
    "ROSTER_CODES",
    "UNIVERSE_LEADERS",
    "UNIVERSE_ROSTER",
    "UNIVERSE_BOTH",
    "UNIVERSE_MODES",
]
