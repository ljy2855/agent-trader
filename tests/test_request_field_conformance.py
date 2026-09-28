"""Every request we build must carry the fields the broker requires.

This is the test that would have caught the 2026-07-28 outage. Phase 0
dropped `all_stk_tp` from the ka10075 body because our hand-written
`kiwoom_api_spec.md` had no such field in its table, and every unit test
passed -- they all use a stub client that answers anything. The live
endpoint rejected every open-order read (`1511:필수입력 파라미터`), which
silently degraded the oversell guard, the stale-cancel path and the
UNKNOWN protective-sell release.

The reference data is Kiwoom's own published spec (see the vendor JSON's
`_source`), which does list `all_stk_tp` as required. It is not gospel --
the same file marks kt10001 `ord_uv` optional while the broker refuses a
보통 limit without it -- so this checks one direction only: a field the
vendor calls required must be present. Extra fields are fine, and a
vendor "optional" proves nothing.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services import account as account_service  # noqa: E402
from src.services import market as market_service  # noqa: E402
from src.services import order as order_service  # noqa: E402

SPEC_PATH = (
    Path(__file__).resolve().parents[1]
    / "src/constants/vendor/kiwoom_request_fields.json"
)
SPEC = json.loads(SPEC_PATH.read_text())


def required_fields(api_id: str) -> set[str]:
    api = SPEC["apis"][api_id]
    return {f["element"] for f in api["request_body"] if f["required"] == "Y"}


class RecordingClient:
    """Answers anything, remembers the body it was handed."""

    def __init__(self):
        self.bodies: list[dict] = []

    async def post(self, path, *, headers=None, params=None, json=None, data=None):
        self.bodies.append(dict(json or {}))

        class R:
            status_code = 200

            @staticmethod
            def json():
                return {"return_code": 0, "return_msg": "정상처리"}

            @property
            def headers(self):
                return {}

            def raise_for_status(self):
                return None

        return R()


def _body_for(call) -> dict:
    client = RecordingClient()
    asyncio.run(call(client))
    assert client.bodies, "no request was sent"
    return client.bodies[0]


# api_id -> a call that builds that API's request. Keyed by the id the
# service actually posts, not by what the function name suggests:
# `get_stock_daily_bars` calls ka10005, and ka10081 is `get_stock_daily_chart`.
CASES = {
    "ka10075": lambda c: account_service.get_unexecuted_orders(
        c, all_stk_tp="0", trde_tp="0", stex_tp="0"
    ),
    "ka10076": lambda c: account_service.get_execution_info(
        c, qry_tp="1", sell_tp="0", stex_tp="0"
    ),
    "ka10170": lambda c: account_service.get_daily_trading_journal(c),
    "kt00004": lambda c: account_service.get_account_evaluation(c),
    "kt10000": lambda c: order_service.place_stock_buy_order(
        c, stk_cd="005930", ord_qty="1", order_type_code="3"
    ),
    "kt10001": lambda c: order_service.place_stock_sell_order(
        c, stk_cd="005930", ord_qty="1", order_type_code="0", ord_uv="70000"
    ),
    "kt10003": lambda c: order_service.cancel_stock_order(
        c, orig_ord_no="1", stk_cd="005930", cncl_qty="1"
    ),
    "ka10081": lambda c: market_service.get_stock_daily_chart(
        c, stock_code="005930", base_date="20260831"
    ),
    "ka10004": lambda c: market_service.get_stock_orderbook(c, stock_code="005930"),
    "ka20001": lambda c: market_service.get_index_snapshot(
        c, inds_cd="001", mrkt_tp="0"
    ),
    "ka20006": lambda c: market_service.get_index_daily_bars(
        c, inds_cd="001", base_date="20260918"
    ),
}


@pytest.mark.parametrize("api_id", sorted(CASES))
def test_request_carries_every_vendor_required_field(api_id):
    body = _body_for(CASES[api_id])
    missing = required_fields(api_id) - set(body)
    assert not missing, (
        f"{api_id} request omits vendor-required {sorted(missing)}; "
        f"sent {sorted(body)}"
    )


def test_ka10075_all_stk_tp_is_pinned():
    """Named on its own because this exact field caused the outage."""

    assert "all_stk_tp" in required_fields("ka10075")
    assert "all_stk_tp" in _body_for(CASES["ka10075"])


def test_priced_limit_sell_carries_a_price():
    """The vendor marks ord_uv optional; the broker rejects 보통 without it.

    308003, 7 for 7 on 2026-08-31. The reference data cannot express this,
    so it is asserted directly.
    """

    body = _body_for(CASES["kt10001"])
    assert body["trde_tp"] == "0"
    assert body.get("ord_uv"), "a 보통 limit must carry ord_uv"


def test_market_sell_needs_no_price():
    body = _body_for(
        lambda c: order_service.place_stock_sell_order(
            c, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )
    assert body["trde_tp"] == "3"
    assert not body.get("ord_uv")
