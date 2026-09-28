"""Let the MCP strategy tools default to what is actually deployed.

The tools carry their own defaults — momentum entry, the movers leaderboards,
no market-cap floor, both markets — and the live watcher runs none of them.
2026-07-24 added the parameters and a docstring warning telling the caller to
go read `k8s/kiwoom-watcher.yaml` and pass the same values. The callers are
LLM agents, and they did not.

What that cost, measured 2026-09-24 at 09:4x on the same client and the same
minute:

    tool defaults : 카페24 13, 레메디 13, 프로티나 13   (KOSDAQ, +17~19% intraday)
    live config   : 삼성전자 3, SK하이닉스 2, 기아 4     (all ineligible)

Nothing overlapped except two names that scored far apart. The default list is
the small-cap momentum universe this account abandoned on 2026-06-24 after
-54,790원 of losses, and it comes back scoring above the live TIER1 bar, so an
agent asking "what should we buy" was being handed a screen from a strategy
that was deliberately switched off.

So the defaults are resolved from the deployment instead. `/state` already
publishes the effective config, and the MCP pod can reach the watcher Service
(the agent runtime, on a host outside the cluster DNS, cannot — which is the
reason this lives on the server side rather than in a skill).

A caller's explicit argument always wins. When the watcher cannot be read the
code defaults are used, but never silently: `config_source` says so, because a
quiet fallback is exactly how this survived two months.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

WATCHER_STATE_URL = os.getenv(
    "WATCHER_STATE_URL", "http://kiwoom-watcher:8001/state"
)

# tool parameter -> key under /state's `config`. Only entries that change which
# names the scan returns, or how big a position would be; timeouts and poll
# intervals are the watcher's business and have no meaning here.
LIVE_KEYS: dict[str, str] = {
    "entry_mode": "entry_mode",
    "ma_period": "ma_period",
    "universe_mode": "universe_mode",
    "min_market_cap_krw": "min_market_cap_krw",
    "leaders_market_tp": "leaders_market_tp",
    "day_change_min": "day_change_min",
    "day_change_max": "day_change_max",
    "auto_buy_min_score": "auto_buy_min_score",
    "stop_loss_pct": "stop_loss_pct",
    "hard_take_profit_pct": "hard_take_profit_pct",
    "max_positions": "max_positions",
    "max_new_positions": "max_new_positions",
    "position_budget_pct": "position_budget_pct",
    "leaders_limit": "leaders_limit",
    "candidate_limit": "candidate_limit",
}


def merge_defaults(
    explicit: dict[str, Any],
    live: dict[str, Any] | None,
    code_defaults: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve each parameter and report where every value came from.

    Precedence is caller > deployment > code default. The provenance map is
    returned rather than logged because the caller is an agent reasoning about
    the numbers: a screen is only interpretable next to the configuration that
    produced it.
    """

    resolved: dict[str, Any] = {}
    origin: dict[str, str] = {}

    for name, default in code_defaults.items():
        given = explicit.get(name)
        if given is not None:
            resolved[name] = given
            origin[name] = "caller"
            continue
        live_key = LIVE_KEYS.get(name)
        if live and live_key and live.get(live_key) is not None:
            resolved[name] = live[live_key]
            origin[name] = "live"
            continue
        resolved[name] = default
        origin[name] = "default"

    matched_live = sorted(k for k, v in origin.items() if v == "live")
    if live:
        source = {
            "source": "live-watcher",
            "detail": (
                f"배포된 watcher /state의 실효 설정 {len(matched_live)}개를 "
                "기본값으로 사용했다. 호출자가 명시한 인자는 그대로 우선한다."
            ),
            "from_live": matched_live,
        }
    else:
        # Say which way the screen is wrong, not just that it might be.
        source = {
            "source": "code-defaults",
            "detail": (
                "watcher /state를 읽지 못해 코드 기본값으로 조회했다. "
                "코드 기본값은 momentum·리더보드·시총 필터 없음이라 "
                "라이브(below_ma·로스터·시총 3조)와 다른 종목이 나온다 — "
                "이 결과를 매수 후보로 쓰지 말 것."
            ),
            "from_live": [],
        }
    source["resolved"] = resolved
    source["origin"] = origin
    return resolved, source


def fetch_live_config(
    url: str | None = None, timeout: float = 3.0
) -> dict[str, Any] | None:
    """Read the deployed watcher's effective config, or None if unreachable.

    Never raises: the strategy tools have to keep answering when the watcher
    is rolling, and `merge_defaults` already makes a None loud.
    """

    target = url or WATCHER_STATE_URL
    try:
        with urllib.request.urlopen(target, timeout=timeout) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None
    config = payload.get("config") if isinstance(payload, dict) else None
    return config if isinstance(config, dict) and config else None


__all__ = ["LIVE_KEYS", "WATCHER_STATE_URL", "fetch_live_config", "merge_defaults"]
