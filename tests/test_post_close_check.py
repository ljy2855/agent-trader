"""Post-close check: day selection, CronJob grading, log parsing, verdict."""

import importlib
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
pc = importlib.import_module("post_close_check")

KST = pc.KST


def _cronjob(name, schedule, last_scheduled=None, last_success=None, suspend=False):
    status = {}
    if last_scheduled:
        status["lastScheduleTime"] = last_scheduled
    if last_success:
        status["lastSuccessfulTime"] = last_success
    return {"metadata": {"name": name}, "spec": {"schedule": schedule, "suspend": suspend}, "status": status}


def _job(owner, start, *, succeeded=0, failed=0):
    return {
        "metadata": {"name": f"{owner}-1", "ownerReferences": [{"kind": "CronJob", "name": owner}]},
        "status": {"startTime": start, "succeeded": succeeded, "failed": failed},
    }


FRIDAY = date(2026, 11, 20)


# --- day selection ----------------------------------------------------------


def test_default_day_on_a_weekend_is_the_last_trading_day():
    sunday_night = datetime(2026, 11, 22, 22, 0, tzinfo=KST)
    assert pc.default_check_day(sunday_night) == FRIDAY


def test_default_day_waits_for_the_close_before_choosing_today():
    monday_noon = datetime(2026, 11, 23, 12, 0, tzinfo=KST)
    monday_evening = datetime(2026, 11, 23, 18, 0, tzinfo=KST)
    assert pc.default_check_day(monday_noon) == FRIDAY
    assert pc.default_check_day(monday_evening) == date(2026, 11, 23)


def test_session_hours_follow_the_regular_session():
    opens, closes = pc.session_hours(FRIDAY)
    assert (opens.hour, opens.minute, closes.hour, closes.minute) == (9, 0, 15, 30)


# --- cron schedules ---------------------------------------------------------


@pytest.mark.parametrize(
    "schedule,day,due",
    [
        ("45 15 * * 1-5", FRIDAY, True),
        ("45 15 * * 1-5", date(2026, 11, 22), False),  # Sunday
        ("*/10 9-15 * * 1-5", FRIDAY, True),
        ("21,36 15 1-7 12 *", FRIDAY, False),  # December 1-7 only
        ("21,36 15 1-7 12 *", date(2026, 12, 3), True),
        ("0 9 * * 0", date(2026, 11, 22), True),
        ("0 9 * * 7", date(2026, 11, 22), True),
    ],
)
def test_cron_due_on(schedule, day, due):
    assert pc.cron_due_on(schedule, day) is due


# --- CronJob grading --------------------------------------------------------


def test_cronjob_whose_last_run_that_day_succeeded_is_ok():
    item = _cronjob("journal", "45 15 * * 1-5", "2026-11-20T06:45:00Z", "2026-11-20T06:45:14Z")
    grade, text = pc.grade_cronjob(item, FRIDAY, [])
    assert grade == pc.OK
    assert "11-20 15:45" in text


def test_cronjob_without_a_run_that_day_is_an_alert():
    item = _cronjob("journal", "45 15 * * 1-5", "2026-11-19T06:45:00Z", "2026-11-19T06:45:14Z")
    grade, _ = pc.grade_cronjob(item, FRIDAY, [])
    assert grade == pc.ALERT


def test_cronjob_whose_last_run_has_no_success_is_an_alert():
    item = _cronjob("digest", "0 16 * * 1-5", "2026-11-20T07:00:00Z", "2026-11-19T07:00:10Z")
    grade, _ = pc.grade_cronjob(item, FRIDAY, [])
    assert grade == pc.ALERT


def test_cronjob_checked_after_a_later_run_says_the_day_is_no_longer_visible():
    item = _cronjob("digest", "0 16 * * 1-5", "2026-11-23T07:00:00Z", "2026-11-23T07:00:10Z")
    grade, text = pc.grade_cronjob(item, FRIDAY, [])
    assert grade == pc.INFO
    assert "expired" in text


def test_kept_failed_job_of_that_day_is_an_alert_even_if_a_later_one_succeeded():
    item = _cronjob("health", "*/10 9-15 * * 1-5", "2026-11-20T06:50:00Z", "2026-11-20T06:50:09Z")
    jobs = [
        _job("health", "2026-11-20T01:00:00Z", failed=1),
        _job("health", "2026-11-20T06:50:00Z", succeeded=1),
        _job("other", "2026-11-20T01:00:00Z", failed=1),
    ]
    grade, text = pc.grade_cronjob(item, FRIDAY, jobs)
    assert grade == pc.ALERT
    assert "1 failed" in text


def test_cronjob_not_due_that_day_is_information():
    item = _cronjob("trial", "21,36 15 1-7 12 *")
    assert pc.grade_cronjob(item, FRIDAY, [])[0] == pc.INFO


def test_suspended_cronjob_is_a_warning():
    item = _cronjob("brief", "40 8 * * 1-5", suspend=True)
    assert pc.grade_cronjob(item, FRIDAY, [])[0] == pc.WARN


# --- watcher log ------------------------------------------------------------


def _line(kst_clock, text, offset="+09:00"):
    return f"2026-11-20T{kst_clock}.123456789{offset} {text}"


def _http(clock, endpoint, status):
    phrase = "200 OK" if status == 200 else f"{status} null"
    return _line(clock, f'2026-11-20 00:00:00,000 INFO httpx: HTTP Request: POST https://api.example/api/dostk/{endpoint} "HTTP/1.1 {phrase}"')


def test_parse_keeps_only_that_days_lines_and_converts_to_kst():
    raw = [
        "2026-11-19T23:59:59.000000000+09:00 previous day",
        "2026-11-20T00:30:00.000000000Z utc line is 09:30 KST",
        "2026-11-20T23:59:00.000000000+09:00 same day",
        "not a kubelet line",
    ]
    kept = pc.parse_kubelet_lines(raw, FRIDAY)
    assert [line.text for line in kept] == ["utc line is 09:30 KST", "same day"]
    assert kept[0].at.hour == 9 and kept[0].at.minute == 30


def test_429_answered_by_the_same_endpoint_within_the_window_counts_as_retried():
    raw = [
        _http("10:00:00", "acnt", 429),
        _http("10:00:00", "mrkcond", 200),  # another endpoint does not count
        _http("10:00:01", "acnt", 200),
        _http("11:00:00", "mrkcond", 429),
        _http("11:00:05", "mrkcond", 200),  # too late
    ]
    opens, closes = pc.session_hours(FRIDAY)
    summary = pc.summarize_watcher_log(pc.parse_kubelet_lines(raw, FRIDAY), opens, closes)
    assert summary["rate_limited"] == 2
    assert summary["rate_limited_retried"] == 1
    assert summary["rate_limited_unrecovered"] == ["11:00:00 mrkcond"]
    assert summary["http_status_counts"]["acnt 429"] == 1


def test_a_refused_retry_that_gets_through_on_the_third_ask_counts_as_retried():
    # 11/23 10:58: a market read was refused, its retry 0.75 s later was
    # refused too, and the third ask 1.5 s after that was answered.
    raw = [
        _http("10:58:17", "mrkcond", 429),
        _http("10:58:18", "mrkcond", 429),
        _http("10:58:19", "mrkcond", 200),
        _http("10:58:19", "mrkcond", 200),
    ]
    opens, closes = pc.session_hours(FRIDAY)
    summary = pc.summarize_watcher_log(pc.parse_kubelet_lines(raw, FRIDAY), opens, closes)
    assert summary["rate_limited"] == 2
    assert summary["rate_limited_retried"] == 2
    assert summary["rate_limited_unrecovered"] == []


def test_three_refusals_in_a_row_mean_the_client_gave_up():
    raw = [
        _http("10:00:00", "mrkcond", 429),
        _http("10:00:01", "mrkcond", 429),
        _http("10:00:02", "mrkcond", 429),
        _http("10:00:02", "mrkcond", 200),  # the next read, not a retry
        _http("10:30:00", "acnt", 429),
        _http("10:30:01", "acnt", 500),  # answered, but not with the data
    ]
    opens, closes = pc.session_hours(FRIDAY)
    summary = pc.summarize_watcher_log(pc.parse_kubelet_lines(raw, FRIDAY), opens, closes)
    assert summary["rate_limited_retried"] == 0
    assert summary["rate_limited_unrecovered"] == [
        "10:00:00 mrkcond",
        "10:00:01 mrkcond",
        "10:00:02 mrkcond",
        "10:30:00 acnt",
    ]


def test_session_coverage_counts_minutes_with_any_read():
    raw = [_http(f"09:{minute:02d}:10", "sect", 200) for minute in range(0, 60)]
    opens, closes = pc.session_hours(FRIDAY)
    summary = pc.summarize_watcher_log(pc.parse_kubelet_lines(raw, FRIDAY), opens, closes)
    assert summary["session_minutes"] == 390
    assert summary["session_minutes_with_reads"] == 60


def test_open_tick_and_realtime_warnings_are_expected_but_others_are_not():
    raw = [
        _line("09:00:00", "2026-11-20 00:00:00,290 WARNING kiwoom.watcher: planner degraded: planner degraded — market_regime: 지수·등락 종목 수 불완전"),
        _line("09:00:00", "2026-11-20 00:00:00,709 WARNING kiwoom.watcher: cycle data path degraded (1 consecutive)"),
        _line("11:00:00", "2026-11-20 02:00:00,000 WARNING kiwoom.watcher: cycle data path degraded (1 consecutive)"),
        _line("15:45:26", "2026-11-20 06:45:26,103 WARNING kiwoom.watcher.realtime: realtime stream error (received 1000 (OK) Bye); reconnecting in 30s"),
        _line("12:00:00", "2026-11-20 03:00:00,000 ERROR kiwoom.watcher: tick failed"),
    ]
    opens, closes = pc.session_hours(FRIDAY)
    summary = pc.summarize_watcher_log(pc.parse_kubelet_lines(raw, FRIDAY), opens, closes)
    assert sum(summary["expected_warnings"].values()) == 3
    assert summary["warnings"] == {"kiwoom.watcher: cycle data path degraded (N consecutive)": 1}
    assert summary["errors"] == {"kiwoom.watcher: tick failed": 1}
    assert summary["realtime_drops"] == 1


# --- rotated kubelet log files ----------------------------------------------


def _cri(kst_clock, text, stream="stderr", tag="F", day="2026-11-20"):
    return f"{day}T{kst_clock}.123456789+09:00 {stream} {tag} {text}"


def test_cri_lines_become_kubectl_lines_and_split_lines_are_joined():
    raw = [
        _cri("10:00:00", "one"),
        _cri("10:00:01", "long ", tag="P"),
        _cri("10:00:01", "stdout line", stream="stdout"),
        _cri("10:00:02", "line", tag="F"),
        "not a log line",
    ]
    assert pc.parse_cri_lines(raw) == [
        "2026-11-20T10:00:00.123456789+09:00 one",
        "2026-11-20T10:00:01.123456789+09:00 stdout line",
        "2026-11-20T10:00:01.123456789+09:00 long line",
    ]


def test_rotated_log_files_skip_the_current_file_and_ones_rotated_long_before_the_day():
    listing = (
        '<a href="0.log">0.log</a> <a href="0.log.20261120-130303">x</a> '
        '<a href="0.log.20261119-020000.gz">x</a> <a href="0.log.20261110-090000.gz">x</a>'
    )
    since = datetime(2026, 11, 20, tzinfo=KST)
    assert pc.rotated_log_files(listing, since) == ["0.log.20261120-130303", "0.log.20261119-020000.gz"]


def test_rotated_logs_are_read_newest_first_until_one_starts_before_the_day():
    # 11/27: the kubelet rotated the watcher's log at 13:03, so `kubectl logs`
    # began at 13:03 and the check counted 147 of 390 session minutes.
    import gzip

    files = {
        "0.log.20261120-130303": "\n".join([
            _cri("09:00:00", "older file ends here"),
            _cri("13:02:55", "last line before rotation"),
        ]).encode(),
        "0.log.20261120-090000.gz": gzip.compress("\n".join([
            _cri("23:00:00", "previous day", day="2026-11-19"),
            _cri("08:59:59", "just before the first file"),
        ]).encode()),
        "0.log.20261119-210000.gz": b"never read",
    }
    read = []

    def fetch(name):
        read.append(name)
        return files[name]

    since = datetime(2026, 11, 20, tzinfo=KST)
    lines, done = pc.read_rotated_logs(list(files), fetch, since)
    assert done == read == ["0.log.20261120-130303", "0.log.20261120-090000.gz"]
    assert [line.text for line in pc.parse_kubelet_lines(lines, FRIDAY)] == [
        "just before the first file", "older file ends here", "last line before rotation",
    ]


def test_session_coverage_counts_the_rotated_file_too():
    rotated = [_cri(f"{9 + m // 60:02d}:{m % 60:02d}:10", 'x httpx: HTTP Request: POST https://api.example/api/dostk/sect "HTTP/1.1 200 OK"')
               for m in range(0, 243)]
    current = [_http(f"{9 + m // 60:02d}:{m % 60:02d}:10", "sect", 200) for m in range(243, 390)]
    lines, _ = pc.read_rotated_logs(["0.log.20261120-130303"], lambda name: "\n".join(rotated).encode(),
                                    datetime(2026, 11, 20, tzinfo=KST))
    opens, closes = pc.session_hours(FRIDAY)
    summary = pc.summarize_watcher_log(pc.parse_kubelet_lines(lines + current, FRIDAY), opens, closes)
    assert summary["session_minutes_with_reads"] == 390


# --- ingress, ledger, agents, verdict ---------------------------------------


def test_empty_mcp_responses_are_picked_from_the_ingress_log():
    raw = [
        _line("15:41:42", '192.0.2.1 - - [x] "POST /mcp HTTP/1.1" 200 0 "-" "-" 1 "router" "http://svc:8000" 11ms'),
        _line("15:41:43", '192.0.2.1 - - [x] "POST /mcp HTTP/1.1" 200 1197 "-" "-" 2 "router" "http://svc:8000" 36ms'),
        _line("15:41:44", '192.0.2.1 - - [x] "GET /api/dashboard HTTP/1.1" 200 0 "-" "-" 3 "router" "http://svc:8000" 5ms'),
    ]
    hits = pc.empty_mcp_responses(pc.parse_kubelet_lines(raw, FRIDAY))
    assert hits == ["15:41:42 (11ms)"]


def test_ledger_day_intents_filter_by_trading_day():
    ledger = {"recent": [{"trading_day": "2026-11-20", "state": "FILLED"}, {"trading_day": "2026-11-19"}]}
    assert pc.ledger_day_intents(ledger, FRIDAY) == [{"trading_day": "2026-11-20", "state": "FILLED"}]


def _probe(**overrides):
    probe = {
        "codex_current": "1.1.0-linux",
        "codex_releases": ["1.0.0-linux", "1.1.0-linux"],
        "daemon_codex_path": "/home/u/.codex/packages/standalone/releases/1.1.0-linux/bin/codex",
        "daemon_codex_version": "codex-cli 1.1.0",
        "daemon_codex_path_exists": True,
        "daemon_processes": ["1 Sat Nov 14 18:00:00 2026 multica daemon start --foreground"],
        "issues": [{"identifier": "X-1", "title": "wrap", "status": "in_review", "runs": [{"status": "completed"}]}],
    }
    probe.update(overrides)
    return probe


def _grades(probe):
    report = pc.Report(FRIDAY)
    pc.grade_agent_host(report, probe)
    return [f.grade for f in report.findings]


def test_agent_host_in_step_is_ok():
    assert pc.ALERT not in _grades(_probe()) and pc.WARN not in _grades(_probe())


def test_daemon_on_an_older_codex_than_current_is_a_warning():
    probe = _probe(daemon_codex_path="/home/u/.codex/packages/standalone/releases/1.0.0-linux/bin/codex",
                   daemon_codex_version="codex-cli 1.0.0")
    assert pc.WARN in _grades(probe)


def test_daemon_codex_binary_removed_is_an_alert():
    assert pc.ALERT in _grades(_probe(daemon_codex_path_exists=False))


def test_failed_agent_run_is_an_alert():
    issues = [{"identifier": "X-2", "title": "brief", "status": "todo", "runs": [{"status": "failed", "error": "quota"}]}]
    assert pc.ALERT in _grades(_probe(issues=issues))


def test_verdict_is_the_worst_grade():
    report = pc.Report(FRIDAY)
    assert report.verdict == "정상"
    report.add(pc.INFO, "s", "note")
    assert report.verdict == "정상"
    report.add(pc.WARN, "s", "warn")
    assert report.verdict == "주의"
    report.add(pc.ALERT, "s", "alert")
    assert report.verdict == "이상"
