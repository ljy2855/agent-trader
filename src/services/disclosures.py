"""Classify DART disclosures by what they say about a company's fundamentals.

The question this serves: did a price drop come with news about the company,
or did it happen without any? Studies of large price moves find the two
behave differently — moves with public information tend to continue, moves
without it tend to reverse (Chan 2003; Savor 2012).

A large cap files something every few days, and most of it is paperwork, so
"a disclosure exists" says nothing. The rules below were fixed from the
filing *names* alone, before any return was looked at — choosing them after
seeing returns would fit the categories to the answer.

Rules, applied in order to the name with whitespace removed:

1. A bracketed prefix (``[기재정정]``, ``[첨부추가]`` …) is a correction or an
   attachment; the original filing carried the information.
2. ``자회사의주요경영사항`` / ``종속회사의주요경영사항`` are about another entity,
   usually a holding company's routine filing for a subsidiary.
3. ``안내공시`` / ``공시예고`` / ``발표일정`` announce a schedule (IR day,
   results date) — "연간경영실적발표일정" is a date, not results.
4. ``실적`` / ``손익구조`` are earnings: preliminary results, guidance, and the
   mandatory notice of a 15%+ change in revenue or profit.
5. Buybacks, cancellations, dividends and value-up plans return capital; they
   are company decisions, not information about the business.
6. Events: financing and dilution, restructuring, contracts, litigation and
   misconduct, production stops and accidents, and answers to press rumours
   or exchange inquiries — the last two say outright that news is moving the
   stock.

Anything else is routine.
"""

from __future__ import annotations

import re

EARNINGS = "earnings"
EVENT = "event"
CAPITAL_RETURN = "capital_return"
ROUTINE = "routine"
SUBSIDIARY = "subsidiary"
CORRECTION = "correction"

NEWS_CATEGORIES = frozenset({EARNINGS, EVENT})

_SUBSIDIARY_MARKERS = ("자회사의주요경영사항", "종속회사의주요경영사항")
_SCHEDULE_MARKERS = ("안내공시", "공시예고", "발표일정")
_EARNINGS_MARKERS = ("실적", "손익구조")
_CAPITAL_RETURN_MARKERS = ("자기주식", "주식소각", "배당", "기업가치제고")
_EVENT_MARKERS = (
    # financing and dilution
    "유상증자결정",
    "사채권발행결정",
    "감자결정",
    "증권예탁증권",
    "해외증권시장주권등상장",
    # restructuring
    "합병결정",
    "분할결정",
    "주식교환",
    "영업양수",
    "영업양도",
    # business
    "공급계약",
    "투자판단관련주요경영사항",
    "장래사업",
    "수시공시의무관련사항",
    # trouble
    "소송",
    "횡령",
    "배임",
    "불성실공시",
    "회계처리기준위반",
    "매매거래정지",
    "생산중단",
    "중대재해",
    "손실발생",
    "해산사유",
    # the exchange or the press already says news is moving the stock
    "풍문",
    "조회공시",
)

_WHITESPACE = re.compile(r"\s+")


def classify_disclosure(report_name: str | None) -> str:
    """One category per filing name (see the module docstring for the rules)."""

    name = _WHITESPACE.sub("", report_name or "")
    if name.startswith("["):
        return CORRECTION
    if any(marker in name for marker in _SUBSIDIARY_MARKERS):
        return SUBSIDIARY
    if any(marker in name for marker in _SCHEDULE_MARKERS):
        return ROUTINE
    if any(marker in name for marker in _EARNINGS_MARKERS):
        return EARNINGS
    if any(marker in name for marker in _CAPITAL_RETURN_MARKERS):
        return CAPITAL_RETURN
    if any(marker in name for marker in _EVENT_MARKERS):
        return EVENT
    return ROUTINE


def is_news(report_name: str | None) -> bool:
    return classify_disclosure(report_name) in NEWS_CATEGORIES


__all__ = [
    "CAPITAL_RETURN",
    "CORRECTION",
    "EARNINGS",
    "EVENT",
    "NEWS_CATEGORIES",
    "ROUTINE",
    "SUBSIDIARY",
    "classify_disclosure",
    "is_news",
]
