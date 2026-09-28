"""Filing-name rules that tell company news from paperwork."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from src.services.disclosures import (  # noqa: E402
    CAPITAL_RETURN,
    CORRECTION,
    EARNINGS,
    EVENT,
    ROUTINE,
    SUBSIDIARY,
    classify_disclosure,
    is_news,
)


@pytest.mark.parametrize(
    "name,category",
    [
        ("연결재무제표기준영업(잠정)실적(공정공시)", EARNINGS),
        ("매출액또는손익구조30%(대규모법인은15%)이상변경", EARNINGS),
        ("연결재무제표기준영업실적등에대한전망(공정공시)", EARNINGS),
        # Dates of results, not results.
        ("결산실적공시예고(안내공시)", ROUTINE),
        ("기타경영사항(자율공시)(2026년연간경영실적발표일정)", ROUTINE),
        ("단일판매ㆍ공급계약체결", EVENT),
        ("풍문또는보도에대한해명(미확정)", EVENT),
        ("조회공시요구(풍문또는보도)", EVENT),
        ("주요사항보고서(유상증자결정)", EVENT),
        ("주요사항보고서(전환사채권발행결정)", EVENT),
        ("횡령ㆍ배임사실확인", EVENT),
        ("소송등의제기ㆍ신청(경영권분쟁소송)", EVENT),
        ("주요사항보고서(자기주식취득결정)", CAPITAL_RETURN),
        ("현금ㆍ현물배당결정", CAPITAL_RETURN),
        ("주식소각결정", CAPITAL_RETURN),
        ("기업설명회(IR)개최(안내공시)", ROUTINE),
        ("최대주주등소유주식변동신고서", ROUTINE),
        ("주요사항보고서(상각형조건부자본증권발행결정)", ROUTINE),
        ("유상증자결정(종속회사의주요경영사항)", SUBSIDIARY),
        ("연결재무제표기준영업(잠정)실적(공정공시)(자회사의주요경영사항)", SUBSIDIARY),
        ("[기재정정]단일판매ㆍ공급계약체결", CORRECTION),
        # DART pads names with spaces.
        ("영업(잠정)실적(공정공시)              ", EARNINGS),
        (None, ROUTINE),
    ],
)
def test_filing_names_map_to_one_category(name, category):
    assert classify_disclosure(name) == category


def test_only_earnings_and_events_count_as_news():
    assert is_news("영업(잠정)실적(공정공시)")
    assert is_news("소송등의판결ㆍ결정")
    assert not is_news("주식소각결정")
    assert not is_news("[기재정정]영업(잠정)실적(공정공시)")
    assert not is_news("유상증자결정(자회사의주요경영사항)")
