"""Ops digest tests — the failure-rate grading that catches slow bleed."""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
digest = importlib.import_module("daily_ops_digest")


def _levels(lines):
    return [level for level, _ in lines]


def test_healthy_watcher_reports_nothing():
    assert digest._failure_rate_lines({}, 1200) == []


def test_zero_count_categories_are_ignored():
    """The registry can hold a category that has since recovered."""

    assert digest._failure_rate_lines({"planner": {"count": 0}}, 1200) == []


def test_intermittent_fault_is_caught_where_the_consecutive_counter_is_blind():
    """The 2026-07-29 DNS shape: ~10% of cycles, never 10 in a row.

    api_failure_count sat at 0 through this because a success landed between
    nearly every pair of failures, so the digest said nothing for two days.
    """

    lines = digest._failure_rate_lines(
        {"planner": {"count": 140, "last_detail": "planner degraded — kospi ka10027"}},
        1400,
    )
    assert _levels(lines) == ["alert"]
    assert "140건 / 1400 사이클 (10.0%)" in lines[0][1]
    assert "kospi ka10027" in lines[0][1], "the detail is the diagnosable part"


def test_low_rate_noise_stays_quiet():
    """A handful of transient failures must not page anyone."""

    assert digest._failure_rate_lines({"market": {"count": 5}}, 1400) == []


def test_warn_and_alert_bands_are_graded():
    lines = digest._failure_rate_lines(
        {
            "market": {"count": 42},  # 3% -> warn
            "planner": {"count": 210},  # 15% -> alert
        },
        1400,
    )
    assert _levels(lines) == ["alert", "warn"], "worst first"
    assert lines[0][1].startswith("planner")


def test_rate_is_normalised_so_a_long_uptime_is_not_punished():
    """Absolute counts grow with uptime; the same 20 failures mean
    different things over 200 cycles and over 20000."""

    burst = digest._failure_rate_lines({"order": {"count": 20}}, 200)
    spread = digest._failure_rate_lines({"order": {"count": 20}}, 20000)
    assert _levels(burst) == ["alert"]
    assert spread == []


def test_zero_cycles_does_not_divide_by_zero():
    """A watcher that failed before completing its first cycle."""

    lines = digest._failure_rate_lines({"planner": {"count": 3}}, 0)
    assert _levels(lines) == ["alert"]


def test_malformed_bucket_is_skipped_not_crashed():
    """The digest must never die on an unexpected /state shape."""

    lines = digest._failure_rate_lines(
        {"planner": "not-a-dict", "account": {"count": 300}}, 1000
    )
    assert _levels(lines) == ["alert"]
    assert lines[0][1].startswith("account")


# --- failed-run grading -----------------------------------------------------
#
# A failed run is two events under one status. The four cases below are the
# real ones this repo has seen, graded the way an operator would want.

CAPACITY = "Selected model is at capacity. Please try a different model."
QUOTA = (
    "You've hit your usage limit. Upgrade to Pro "
    "(https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings"
)


def test_a_single_capacity_blip_is_yellow_not_red():
    """09-17, 09-18, 09-22: one run failed, the next succeeded minutes later.

    Each one raised a red [점검 필요] handoff that had to be waved off by hand.
    """

    alert, warn = digest.grade_failed_runs(
        {"[PM 코멘트] 2026-09-22 사이클 점검 (2)": [CAPACITY]}
    )
    assert alert is None
    assert warn is not None and "일시 실패 run 1건" in warn
    # Still reported, with its reason, so a rising trend cannot hide.
    assert "Selected model is at capacity" in warn


def test_quota_exhaustion_is_red_even_from_one_run():
    """The message itself is the signal: the quota being gone is not transient."""

    alert, warn = digest.grade_failed_runs({"[PM 코멘트]": [QUOTA]})
    assert alert is not None and "사용 한도 소진" in alert
    assert warn is None


def test_the_september_15_outage_stays_red():
    """Eleven quota failures across 3.5 hours — the case grading must not lose."""

    alert, _ = digest.grade_failed_runs(
        {"[PM 코멘트] 2026-09-15 사이클 점검": [QUOTA] * 10, "[위임] 기타": [QUOTA]}
    )
    assert alert is not None
    assert "11건" in alert


def test_repeated_transient_failures_escalate_to_red():
    """Three blips is no longer a blip, whatever each message says."""

    alert, warn = digest.grade_failed_runs(
        {"[PM 코멘트]": [CAPACITY, CAPACITY], "[LG화학] 보유 분석": [CAPACITY]}
    )
    assert alert is not None and "반복 실패" in alert
    assert warn is None


def test_no_failed_runs_raise_nothing():
    assert digest.grade_failed_runs({}) == (None, None)
