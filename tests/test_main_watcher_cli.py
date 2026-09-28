"""Tests for main_watcher.py CLI helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

import main_watcher  # noqa: E402


def test_parse_watchlist_arg_deduplicates_codes() -> None:
    """Watchlist parsing should trim whitespace and drop duplicates."""

    result = main_watcher.parse_watchlist_arg("005930, 000660,005930")

    assert result == ["005930", "000660"]


def test_parse_watchlist_arg_accepts_alphanumeric_specialty_tickers() -> None:
    """SPAC / M-class / other specialty KRX tickers embed letters but
    are still 6 chars total (e.g. 0088M0 메쥬)."""

    result = main_watcher.parse_watchlist_arg("0088M0,005930")
    assert result == ["0088M0", "005930"]


def test_parse_watchlist_arg_rejects_invalid_length() -> None:
    with pytest.raises(ValueError):
        main_watcher.parse_watchlist_arg("12345")


def test_parse_watchlist_arg_returns_none_on_empty() -> None:
    assert main_watcher.parse_watchlist_arg(None) is None
    assert main_watcher.parse_watchlist_arg("") is None
    assert main_watcher.parse_watchlist_arg(" , , ") is None


def test_exit_only_cli_keeps_order_execution_enabled():
    args = main_watcher._build_arg_parser().parse_args([
        "--execute-orders", "--disable-new-entries",
    ])
    config = main_watcher._build_config(args)
    assert config.execute_orders
    assert not config.new_entries_enabled


def test_regime_stability_ticks_reaches_the_watcher_config():
    """The flag must land in WatcherConfig, not just parse.

    2026-09-22: breadth sat on the 0.85 risk_off line and regime_flip woke
    the PM squad six times, every one an informational HOLD. The window is
    raised from the manifest, so a flag that parses but never reaches the
    config would leave the old 3-tick debounce running silently.
    """

    args = main_watcher._build_arg_parser().parse_args(
        ["--regime-stability-ticks", "10"]
    )
    assert main_watcher._build_config(args).regime_stability_ticks == 10


def test_regime_stability_ticks_default_is_unchanged():
    args = main_watcher._build_arg_parser().parse_args([])
    assert main_watcher._build_config(args).regime_stability_ticks == 3
