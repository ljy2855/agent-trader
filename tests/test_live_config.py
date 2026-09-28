"""MCP strategy tools must default to what is deployed, not to this file.

Measured 2026-09-24, same client and same minute: the tool's own defaults
returned 카페24 13 / 레메디 13 / 프로티나 13 (KOSDAQ, +17~19% intraday) while
the live configuration returned 삼성전자 3 / SK하이닉스 2 / 기아 4, all
ineligible. Nothing meaningful overlapped. The defaults are the small-cap
momentum universe abandoned on 2026-06-24 after -54,790원 of losses, and they
came back scoring above the live TIER1 bar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services import live_config  # noqa: E402

CODE_DEFAULTS = {
    "entry_mode": "momentum",
    "universe_mode": "leaders",
    "min_market_cap_krw": 0,
    "auto_buy_min_score": 14,
    "stop_loss_pct": -3.0,
    "position_budget_pct": 10,
}

# The shape /state actually publishes (50 keys; only the relevant ones here).
LIVE = {
    "entry_mode": "below_ma",
    "universe_mode": "roster",
    "min_market_cap_krw": 3_000_000_000_000,
    "auto_buy_min_score": 8,
    "stop_loss_pct": -4.0,
    "position_budget_pct": 60,
    "poll_interval_seconds": 30,
}


def test_unset_arguments_come_from_the_deployment():
    resolved, source = live_config.merge_defaults({}, LIVE, CODE_DEFAULTS)

    assert resolved["entry_mode"] == "below_ma"
    assert resolved["universe_mode"] == "roster"
    assert resolved["min_market_cap_krw"] == 3_000_000_000_000
    assert resolved["auto_buy_min_score"] == 8
    assert source["source"] == "live-watcher"


def test_an_explicit_argument_still_wins():
    """Asking a what-if must stay possible, or the tool loses its purpose."""

    resolved, source = live_config.merge_defaults(
        {"entry_mode": "momentum"}, LIVE, CODE_DEFAULTS
    )

    assert resolved["entry_mode"] == "momentum"
    assert source["origin"]["entry_mode"] == "caller"
    # ... and only that one is overridden.
    assert resolved["universe_mode"] == "roster"
    assert source["origin"]["universe_mode"] == "live"


def test_the_live_budget_of_60_survives_the_merge():
    """The tool capped this at 50 until 2026-09-24, so the deployed value
    could not be expressed at all."""

    resolved, _ = live_config.merge_defaults({}, LIVE, CODE_DEFAULTS)
    assert resolved["position_budget_pct"] == 60


def test_an_unreachable_watcher_says_the_screen_is_the_wrong_strategy():
    """A quiet fallback is how this survived two months: the docstring warned,
    the behaviour did not change, and the agents kept reading the wrong list."""

    resolved, source = live_config.merge_defaults({}, None, CODE_DEFAULTS)

    assert resolved == CODE_DEFAULTS
    assert source["source"] == "code-defaults"
    assert "후보로 쓰지 말 것" in source["detail"]
    assert source["from_live"] == []


def test_keys_the_deployment_does_not_publish_fall_back_quietly():
    """A watcher that reports a partial config must not blank the rest."""

    resolved, source = live_config.merge_defaults(
        {}, {"entry_mode": "below_ma"}, CODE_DEFAULTS
    )

    assert resolved["entry_mode"] == "below_ma"
    assert resolved["auto_buy_min_score"] == 14
    assert source["origin"]["auto_buy_min_score"] == "default"
    # Still a live read overall — one missing key is not an outage.
    assert source["source"] == "live-watcher"


def test_provenance_is_reported_for_every_parameter():
    """The caller is an agent reasoning about the numbers; a screen is only
    interpretable next to the configuration that produced it."""

    resolved, source = live_config.merge_defaults(
        {"stop_loss_pct": -2.0}, LIVE, CODE_DEFAULTS
    )

    assert set(source["origin"]) == set(CODE_DEFAULTS)
    assert set(source["resolved"]) == set(resolved)
    assert set(source["origin"].values()) <= {"caller", "live", "default"}


# --- the fetch leg ----------------------------------------------------------


def test_fetch_returns_none_instead_of_raising_when_the_watcher_is_down():
    """The tools have to keep answering during a rollout."""

    assert live_config.fetch_live_config("http://127.0.0.1:1/state", timeout=0.2) is None


def test_fetch_reads_the_config_block(tmp_path, monkeypatch):
    payload = tmp_path / "state.json"
    payload.write_text(json.dumps({"config": LIVE, "cycle_count": 7}))

    got = live_config.fetch_live_config(payload.as_uri(), timeout=2.0)

    assert got is not None and got["entry_mode"] == "below_ma"


def test_a_state_response_without_a_config_block_is_treated_as_unreachable(tmp_path):
    """An empty config is not a configuration — falling back loudly beats
    resolving every parameter to a default while claiming it came from live."""

    payload = tmp_path / "state.json"
    payload.write_text(json.dumps({"cycle_count": 7, "config": {}}))

    assert live_config.fetch_live_config(payload.as_uri(), timeout=2.0) is None
