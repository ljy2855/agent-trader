"""Fetch and cache OpenDART disclosure lists for the roster (offline research).

The watcher does not read these files. The key comes from the environment
(``DART_API_KEY``) and never reaches the cache, a log line, or an exception:
httpx errors carry the request URL, and the URL carries the key, so every
transport failure is re-raised with the URL stripped.

Only two of DART's disclosure types are fetched. B 주요사항보고 and
I 거래소공시 are where company events land (earnings, contracts, financing,
litigation, buybacks). The others — 정기공시, 발행공시, 지분공시, 외부감사,
공정위 — are schedules and paperwork, and for a large cap they arrive every
few days whatever the stock is doing.
"""

from __future__ import annotations

import io
import json
import os
import time
import zipfile
from xml.etree import ElementTree

import httpx

from .data import CACHE_DIR, KOSPI_LARGECAP

DART_DIR = CACHE_DIR / "dart"
DART_API = "https://opendart.fss.or.kr/api"
DISCLOSURE_TYPES = ("B", "I")
_PAGE_SIZE = 100
_NO_DATA = "013"  # 조회된 데이터가 없습니다


def api_key() -> str:
    key = os.environ.get("DART_API_KEY", "").strip()
    if not key:
        raise SystemExit("DART_API_KEY 환경변수가 없다 (.env 값을 export 할 것)")
    return key


def _get(client: httpx.Client, path: str, params: dict) -> httpx.Response:
    try:
        response = client.get(f"{DART_API}/{path}", params=params)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"DART {path} 요청 실패: {type(exc).__name__}") from None
    if response.status_code != 200:
        raise RuntimeError(f"DART {path} HTTP {response.status_code}")
    return response


def fetch_corp_codes(client: httpx.Client, key: str) -> dict[str, str]:
    """Listed stock code → DART corp_code, from the full registry download."""

    response = _get(client, "corpCode.xml", {"crtfc_key": key})
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        xml = archive.read(archive.namelist()[0])
    codes: dict[str, str] = {}
    for node in ElementTree.fromstring(xml).iter("list"):
        stock = (node.findtext("stock_code") or "").strip()
        corp = (node.findtext("corp_code") or "").strip()
        if stock and corp:
            codes[stock] = corp
    return codes


def fetch_disclosures(
    client: httpx.Client, key: str, corp_code: str, *, begin: str, end: str, kind: str
) -> list[dict]:
    """Every disclosure of one DART type for one company, all pages."""

    rows: list[dict] = []
    page = 1
    while True:
        body = _get(
            client,
            "list.json",
            {
                "crtfc_key": key,
                "corp_code": corp_code,
                "bgn_de": begin,
                "end_de": end,
                "pblntf_ty": kind,
                "page_no": page,
                "page_count": _PAGE_SIZE,
            },
        ).json()
        status = body.get("status")
        if status == _NO_DATA:
            return rows
        if status != "000":
            raise RuntimeError(f"DART list.json {status}: {body.get('message')}")
        rows.extend(body.get("list") or [])
        if page >= int(body.get("total_page") or 1):
            return rows
        page += 1
        time.sleep(0.1)  # well inside DART's 20,000 calls/day; be polite anyway


def fetch_roster(begin: str, end: str) -> dict[str, list[dict]]:
    """Fetch B/I disclosures for every roster name and cache one file per code."""

    key = api_key()
    DART_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, list[dict]] = {}
    with httpx.Client(timeout=30) as client:
        corp_codes = fetch_corp_codes(client, key)
        for code, name in KOSPI_LARGECAP.items():
            corp = corp_codes.get(code)
            if corp is None:
                print(f"  {name}({code}): DART corp_code 없음 — 건너뜀")
                continue
            rows = [
                {**row, "pblntf_ty": kind}
                for kind in DISCLOSURE_TYPES
                for row in fetch_disclosures(
                    client, key, corp, begin=begin, end=end, kind=kind
                )
            ]
            (DART_DIR / f"{code}.json").write_text(json.dumps(rows, ensure_ascii=False))
            out[code] = rows
            print(f"  {name}({code}): {len(rows)}건")
    return out


def load_disclosures() -> dict[str, list[dict]]:
    """Cached disclosures keyed by stock code (offline)."""

    if not DART_DIR.exists():
        return {}
    return {
        path.stem: json.loads(path.read_text())
        for path in sorted(DART_DIR.glob("*.json"))
    }


__all__ = [
    "DISCLOSURE_TYPES",
    "fetch_corp_codes",
    "fetch_disclosures",
    "fetch_roster",
    "load_disclosures",
]
