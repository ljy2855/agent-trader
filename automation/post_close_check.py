#!/usr/bin/env python3
"""Read-only post-close check of one KRX trading day, run from an operator shell.

The 16:00 digest (``daily_ops_digest.py``) grades the watcher's own ``/state``
from inside the cluster. A person checking a day afterwards also needs the
things the digest does not read: whether every CronJob ran, what the watcher
logged (HTTP 429s and whether each was retried, warnings, minutes without a
tick), the ledger's intents for that day, the broker's view of holdings, MCP
calls that came back empty, and the agent host's daemon and codex state.
Gathering those by hand meant re-deriving a dozen commands every time, so this
script does it in one pass and prints a graded summary.

It only reads. It calls ``kubectl get``, ``kubectl get --raw`` (watcher
``/state`` and ``/ledger``, MCP ``/api/dashboard``) and ``kubectl logs``, and,
when ``--agent-host`` is given, runs a fixed read-only probe over ssh. It never
places, cancels or changes orders, workloads, config or secrets, and it never
sends anything anywhere: the operator writes the message and sends it.

The dashboard reads the account through the same app key the watcher uses and
some of those reads are limited to one a second, so the script will not fetch
it while the session is open unless ``--allow-session-reads`` is passed.

Kubelet log timestamps carry the node's offset; they are converted to KST.
The watcher's own log text is UTC, ``/state`` and the ledger are KST.

Usage::

    python automation/post_close_check.py                 # last trading day
    python automation/post_close_check.py --date 2026-11-20 \\
        --agent-host "$OPS_AGENT_HOST" --json /tmp/check.json

Site-specific values come from arguments or the environment, never from this
file: ``OPS_AGENT_HOST`` (ssh target of the agent runtime host),
``MULTICA_PROJECT``, ``OPS_INGRESS_NAMESPACE`` / ``OPS_INGRESS_DEPLOYMENT``
(the ingress whose access log shows MCP responses).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.krx_calendar import (  # noqa: E402
    is_krx_trading_day,
    krx_regular_session_status,
)

KST = timezone(timedelta(hours=9))

OK, WARN, ALERT, INFO = "🟢", "🟡", "🔴", "ℹ️"
_GRADE_ORDER = {OK: 0, INFO: 0, WARN: 1, ALERT: 2}

TERMINAL_LEDGER_STATES = frozenset({"FILLED", "CANCELLED", "REJECTED", "RELEASED"})

# How soon a 429'd read must be answered by the same endpoint to count as
# retried. The client waits 1.2 s (paced account reads) or 0.75 s (market
# reads) before asking again.
RETRY_WINDOW_SECONDS = 3.0
# How many times in a row one read can be refused before the client gives up.
# Market reads ask up to three times (waiting 0.75 s, then 1.5 s), so a retry
# can itself be refused and the third ask still get through.
MAX_ATTEMPTS = 3

# Warnings the watcher prints on healthy days. Each is still counted; it is
# graded as information rather than a finding.
#: The open tick reads indices before Kiwoom has the day's breadth, so the
#: first tick or two of a session report an incomplete regime.
OPEN_TICK_WARNINGS = (
    re.compile(r"planner degraded.*지수·등락 종목 수 불완전"),
    re.compile(r"cycle data path degraded \(1 consecutive\)"),
)
OPEN_TICK_GRACE = timedelta(minutes=2)
#: The broker closes the realtime socket each morning and whenever another
#: process on the same app key is issued a token; the stream reconnects. Only
#: a day with more drops than this is worth a look.
REALTIME_DROP = re.compile(r"realtime stream error")
REALTIME_DROPS_WARN = 10

_KUBELET_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})\s(.*)$")
_HTTP_LINE = re.compile(r'HTTP Request: (?:GET|POST) \S+/(?P<endpoint>[^/\s"]+) "HTTP/1\.1 (?P<status>\d{3})')
_LEVEL = re.compile(r"\s(WARNING|ERROR|CRITICAL)\s")
_INGRESS_EMPTY_MCP = re.compile(r'"POST /mcp HTTP/1\.1" 200 0 .*?(\d+)ms\s*$')


@dataclass
class Finding:
    grade: str
    section: str
    text: str


@dataclass
class Report:
    day: date
    findings: list[Finding] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def add(self, grade: str, section: str, text: str) -> None:
        self.findings.append(Finding(grade, section, text))

    @property
    def verdict(self) -> str:
        worst = max((_GRADE_ORDER[f.grade] for f in self.findings), default=0)
        return {0: "정상", 1: "주의", 2: "이상"}[worst]


# --------------------------------------------------------------------------
# pure helpers (unit-tested)
# --------------------------------------------------------------------------


def default_check_day(now: datetime) -> date:
    """The most recent trading day whose session has closed by ``now``."""

    now = now.astimezone(KST)
    day = now.date()
    for _ in range(15):
        if is_krx_trading_day(day):
            closes = session_hours(day)[1]
            if day < now.date() or now >= closes + timedelta(minutes=5):
                return day
        day -= timedelta(days=1)
    raise RuntimeError("no trading day within the last two weeks")


def session_hours(day: date) -> tuple[datetime, datetime]:
    """Regular-session open and close of ``day`` in KST (special sessions included)."""

    status = krx_regular_session_status(datetime.combine(day, time(12, 0), KST))
    opens = status.opens_at or time(9, 0)
    closes = status.closes_at or time(15, 30)
    return datetime.combine(day, opens, KST), datetime.combine(day, closes, KST)


def to_kst(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def cron_field_matches(spec: str, value: int) -> bool:
    """Match one cron field (``*``, ``a``, ``a-b``, ``*/n``, ``a-b/n``, lists)."""

    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step_text = part.split("/", 1)
            step = int(step_text)
        if part == "*":
            low, high = 0, 10_000
        elif "-" in part:
            low_text, high_text = part.split("-", 1)
            low, high = int(low_text), int(high_text)
        else:
            low = high = int(part)
        if low <= value <= high and (value - low) % step == 0:
            return True
    return False


def cron_due_on(schedule: str, day: date) -> bool:
    """Whether a 5-field cron schedule fires at least once on ``day``."""

    fields = schedule.split()
    if len(fields) != 5:
        return True  # unknown form: assume due, so a miss is not hidden
    _minute, _hour, dom, month, dow = fields
    cron_dow = (day.weekday() + 1) % 7  # cron: 0=Sunday
    dow_ok = cron_field_matches(dow, cron_dow) or (cron_dow == 0 and cron_field_matches(dow, 7))
    dom_ok = cron_field_matches(dom, day.day)
    if not cron_field_matches(month, day.month):
        return False
    if dom != "*" and dow != "*":
        return dom_ok or dow_ok  # cron ORs the two day fields when both are set
    return dom_ok and dow_ok


def grade_cronjob(item: dict[str, Any], day: date, jobs: list[dict[str, Any]]) -> tuple[str, str]:
    """Grade one CronJob for ``day`` from its status and any Jobs still kept."""

    name = item["metadata"]["name"]
    spec = item.get("spec", {})
    schedule = spec.get("schedule", "")
    status = item.get("status", {})
    last_scheduled = to_kst(status.get("lastScheduleTime"))
    last_success = to_kst(status.get("lastSuccessfulTime"))
    if spec.get("suspend"):
        return WARN, f"{name}: suspended"
    if not cron_due_on(schedule, day):
        return INFO, f"{name}: not due on {day} ({schedule})"

    mine = [j for j in jobs if _job_owner(j) == name and (to_kst(j.get("status", {}).get("startTime")) or datetime.min.replace(tzinfo=KST)).date() == day]
    if mine:
        failed = [j["metadata"]["name"] for j in mine if j.get("status", {}).get("failed")]
        done = [j for j in mine if j.get("status", {}).get("succeeded")]
        if failed:
            return ALERT, f"{name}: {len(failed)} failed job(s) on {day}: {', '.join(failed)}"
        return OK, f"{name}: {len(done)}/{len(mine)} job(s) succeeded on {day}"

    when = lambda t: t.strftime("%m-%d %H:%M") if t else "never"  # noqa: E731
    if last_scheduled is None or last_scheduled.date() < day:
        return ALERT, f"{name}: no run on {day} (last scheduled {when(last_scheduled)})"
    if last_scheduled.date() > day:
        return INFO, (
            f"{name}: jobs from {day} already expired (TTL); latest run "
            f"{when(last_scheduled)}, last success {when(last_success)}"
        )
    if last_success is None or last_success < last_scheduled:
        return ALERT, f"{name}: last run {when(last_scheduled)} has no success (last success {when(last_success)})"
    return OK, f"{name}: last run {when(last_scheduled)} succeeded {when(last_success)}"


def _job_owner(job: dict[str, Any]) -> str | None:
    for ref in job.get("metadata", {}).get("ownerReferences", []) or []:
        if ref.get("kind") == "CronJob":
            return ref.get("name")
    return None


@dataclass
class LogLine:
    at: datetime
    text: str


def parse_kubelet_lines(lines: Iterable[str], day: date) -> list[LogLine]:
    """Keep the ``kubectl logs --timestamps`` lines whose KST date is ``day``."""

    kept: list[LogLine] = []
    for raw in lines:
        match = _KUBELET_LINE.match(raw.rstrip("\n"))
        if not match:
            continue
        stamp, fraction, offset, text = match.groups()
        micro = (fraction or ".0")[1:7].ljust(6, "0")
        tz = timezone.utc if offset == "Z" else _offset(offset)
        at = datetime.fromisoformat(stamp).replace(microsecond=int(micro), tzinfo=tz).astimezone(KST)
        if at.date() == day:
            kept.append(LogLine(at, text))
    return kept


def _offset(text: str) -> timezone:
    sign = 1 if text[0] == "+" else -1
    hours, minutes = int(text[1:3]), int(text[4:6])
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def _pair_rate_limited(http: list[tuple[datetime, str, int]]) -> tuple[int, list[str]]:
    """Count the 429s that a retry got past, and list the ones none did.

    A refused read is asked again a moment later, and that retry can be refused
    too. So the 429s of one endpoint are followed as a run: each next answer of
    that endpoint has to come within the window of the one before. A run that
    ends in a 200 was retried, every 429 in it; a run that ends any other way,
    or reaches ``MAX_ATTEMPTS`` refusals, means the client gave up.
    """

    retried = 0
    unrecovered: list[str] = []
    runs: dict[str, list[datetime]] = {}

    def give_up(endpoint: str) -> None:
        unrecovered.extend(f"{at:%H:%M:%S} {endpoint}" for at in runs.pop(endpoint))

    for at, endpoint, status in http:
        run = runs.get(endpoint)
        if run and (at - run[-1]).total_seconds() > RETRY_WINDOW_SECONDS:
            give_up(endpoint)
            run = None
        if status == 429:
            runs.setdefault(endpoint, []).append(at)
            if len(runs[endpoint]) >= MAX_ATTEMPTS:
                give_up(endpoint)
        elif run:
            if status == 200:
                retried += len(runs.pop(endpoint))
            else:
                give_up(endpoint)
    for endpoint in list(runs):
        give_up(endpoint)
    unrecovered.sort()
    return retried, unrecovered


def summarize_watcher_log(lines: list[LogLine], opens: datetime, closes: datetime) -> dict[str, Any]:
    """HTTP status counts, 429 retries, warnings and session coverage."""

    http: list[tuple[datetime, str, int]] = []
    warnings: Counter[str] = Counter()
    expected: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    realtime_drops = 0
    for line in lines:
        match = _HTTP_LINE.search(line.text)
        if match:
            http.append((line.at, match["endpoint"], int(match["status"])))
            continue
        level = _LEVEL.search(line.text)
        if "Traceback" in line.text:
            errors["Traceback"] += 1
            continue
        if not level:
            continue
        message = line.text[level.end():].strip()
        key = re.sub(r"\d+(\.\d+)?", "N", message)[:160]
        if level.group(1) != "WARNING":
            errors[key] += 1
        elif REALTIME_DROP.search(message):
            realtime_drops += 1
            expected[key] += 1
        elif opens <= line.at <= opens + OPEN_TICK_GRACE and any(p.search(message) for p in OPEN_TICK_WARNINGS):
            expected[key] += 1
        else:
            warnings[key] += 1

    statuses = Counter(f"{endpoint} {status}" for _, endpoint, status in http)
    retried, unrecovered = _pair_rate_limited(http)
    other_errors = [f"{at:%H:%M:%S} {e} {s}" for at, e, s in http if s not in (200, 429)]

    session_minutes = int((closes - opens).total_seconds() // 60)
    covered = {at.replace(second=0, microsecond=0) for at, _, _ in http if opens <= at < closes}
    return {
        "http_status_counts": dict(sorted(statuses.items())),
        "rate_limited": sum(1 for *_, s in http if s == 429),
        "rate_limited_retried": retried,
        "rate_limited_unrecovered": unrecovered,
        "http_errors": other_errors,
        "warnings": dict(warnings.most_common()),
        "expected_warnings": dict(expected.most_common()),
        "realtime_drops": realtime_drops,
        "errors": dict(errors.most_common()),
        "session_minutes": session_minutes,
        "session_minutes_with_reads": len(covered),
    }


def empty_mcp_responses(lines: list[LogLine]) -> list[str]:
    """Ingress access-log lines where ``POST /mcp`` answered 200 with no body.

    The agent's curl then fails with ``(18) transfer closed with outstanding
    read data remaining``; a response that took the client's whole timeout is
    the client giving up instead.
    """

    hits = []
    for line in lines:
        match = _INGRESS_EMPTY_MCP.search(line.text)
        if match:
            hits.append(f"{line.at:%H:%M:%S} ({match.group(1)}ms)")
    return hits


def ledger_day_intents(ledger: dict[str, Any], day: date) -> list[dict[str, Any]]:
    return [row for row in ledger.get("recent") or [] if row.get("trading_day") == day.isoformat()]


# --------------------------------------------------------------------------
# collection (shells out; not unit-tested)
# --------------------------------------------------------------------------


class Kube:
    def __init__(self, kubectl: str, namespace: str):
        self.kubectl = kubectl
        self.namespace = namespace

    def _run(self, args: list[str], timeout: int = 120) -> str:
        done = subprocess.run([self.kubectl, *args], capture_output=True, text=True, timeout=timeout)
        if done.returncode != 0:
            raise RuntimeError(done.stderr.strip() or f"kubectl {' '.join(args)} failed")
        return done.stdout

    def json(self, *args: str) -> dict[str, Any]:
        return json.loads(self._run([*args, "-o", "json"]))

    def raw(self, service_port: str, path: str) -> dict[str, Any]:
        url = f"/api/v1/namespaces/{self.namespace}/services/{service_port}/proxy{path}"
        return json.loads(self._run(["get", "--raw", url]))

    def logs(self, target: str, since: datetime, namespace: str | None = None) -> list[str]:
        out = self._run(
            [
                "-n", namespace or self.namespace, "logs", target, "--timestamps",
                f"--since-time={since.astimezone(timezone.utc):%Y-%m-%dT%H:%M:%SZ}",
            ],
            timeout=300,
        )
        return out.splitlines()


def check_cronjobs(kube: Kube, report: Report) -> None:
    cronjobs = kube.json("-n", kube.namespace, "get", "cronjobs").get("items", [])
    jobs = kube.json("-n", kube.namespace, "get", "jobs").get("items", [])
    for item in sorted(cronjobs, key=lambda c: c["metadata"]["name"]):
        grade, text = grade_cronjob(item, report.day, jobs)
        report.add(grade, "cronjobs", text)


def check_watcher(kube: Kube, report: Report, opens: datetime, closes: datetime) -> None:
    pods = kube.json("-n", kube.namespace, "get", "pods", "-l", "app=kiwoom-watcher").get("items", [])
    for pod in pods:
        restarts = sum(c.get("restartCount", 0) for c in pod.get("status", {}).get("containerStatuses", []))
        grade = WARN if restarts else OK
        report.add(grade, "watcher", f"pod {pod['metadata']['name']}: restarts {restarts}")

    state = kube.raw("kiwoom-watcher:8001", "/state")
    report.data["watcher_state"] = {k: state.get(k) for k in (
        "started_at", "mode", "execute_orders", "last_tick_at", "last_error", "api_failure_count",
        "failures", "daily_entry_breaker", "regime", "portfolio", "close_auction_entries",
        "in_flight", "agent_pause",
    )}
    started = to_kst(state.get("started_at"))
    if started and opens <= started <= closes:
        report.add(WARN, "watcher", f"watcher restarted during the session at {started:%H:%M:%S}")
    last_tick = to_kst(state.get("last_tick_at"))
    if last_tick is None or last_tick.date() < report.day:
        report.add(ALERT, "watcher", f"no tick on {report.day} (last tick {last_tick})")
    elif last_tick.date() == report.day and last_tick < closes - timedelta(minutes=2):
        report.add(ALERT, "watcher", f"last tick {last_tick:%H:%M:%S} is before the close {closes:%H:%M}")
    else:
        report.add(OK, "watcher", f"last tick {last_tick:%Y-%m-%d %H:%M:%S}, mode {state.get('mode')}, execute_orders {state.get('execute_orders')}")
    if state.get("last_error"):
        report.add(WARN, "watcher", f"last_error: {state['last_error']}")
    if state.get("in_flight"):
        report.add(WARN, "watcher", f"in_flight: {state['in_flight']}")
    if state.get("agent_pause"):
        report.add(WARN, "watcher", f"agent_pause: {state['agent_pause']}")
    breaker = state.get("daily_entry_breaker") or {}
    if breaker.get("trading_day") == report.day.isoformat():
        grade = WARN if breaker.get("tripped") else OK
        report.add(grade, "watcher", f"entry breaker tripped={breaker.get('tripped')} new_entries={breaker.get('new_entries')}")
    regime = state.get("regime") or {}
    if regime:
        report.add(INFO, "watcher", (
            f"regime at last tick: {regime.get('regime')} KOSPI {regime.get('kospi_change_pct')}% "
            f"KOSDAQ {regime.get('kosdaq_change_pct')}% extreme_risk_off={regime.get('extreme_risk_off')}"
        ))
    for category, failure in (state.get("failures") or {}).items():
        at = to_kst((failure or {}).get("last_at"))
        if at and at.date() == report.day:
            report.add(INFO, "watcher", f"failure '{category}' last at {at:%H:%M:%S}: {failure.get('last_detail')}")

    ledger = kube.raw("kiwoom-watcher:8001", "/ledger?limit=50")
    safety = (ledger.get("storage_safety") or {}).get("state")
    report.add(OK if safety == "local" else ALERT, "ledger", f"storage_safety {safety}")
    unresolved = ledger.get("unresolved_count")
    report.add(OK if unresolved == 0 else ALERT, "ledger", f"unresolved intents {unresolved}")
    intents = ledger_day_intents(ledger, report.day)
    report.data["ledger_intents"] = intents
    if not intents:
        report.add(INFO, "ledger", f"no order intents on {report.day}")
    for row in intents:
        grade = OK if row.get("state") in TERMINAL_LEDGER_STATES else WARN
        report.add(grade, "ledger", (
            f"{row.get('created_at', '')[11:19]} {row.get('side')} {row.get('stock_code')} x{row.get('quantity')} "
            f"→ {row.get('state')} filled {row.get('filled_quantity')} ({row.get('origin')})"
        ))

    lines = parse_kubelet_lines(kube.logs("deploy/kiwoom-watcher", datetime.combine(report.day, time(0), KST)), report.day)
    summary = summarize_watcher_log(lines, opens, closes)
    report.data["watcher_log"] = summary
    coverage = summary["session_minutes_with_reads"]
    report.add(
        OK if coverage >= summary["session_minutes"] * 0.95 else ALERT, "watcher-log",
        f"session minutes with Kiwoom reads {coverage}/{summary['session_minutes']}",
    )
    report.add(INFO, "watcher-log", f"HTTP {summary['http_status_counts']}")
    if summary["rate_limited"]:
        grade = WARN if summary["rate_limited_unrecovered"] else INFO
        report.add(grade, "watcher-log", (
            f"429 {summary['rate_limited']} (retried to 200: {summary['rate_limited_retried']}, "
            f"unrecovered: {summary['rate_limited_unrecovered'] or 0})"
        ))
    for item in summary["http_errors"]:
        report.add(ALERT, "watcher-log", f"HTTP error {item}")
    for message, count in summary["errors"].items():
        report.add(ALERT, "watcher-log", f"x{count} {message}")
    for message, count in summary["warnings"].items():
        report.add(WARN, "watcher-log", f"x{count} {message}")
    for message, count in summary["expected_warnings"].items():
        report.add(INFO, "watcher-log", f"x{count} (expected) {message}")
    if summary["realtime_drops"] > REALTIME_DROPS_WARN:
        report.add(WARN, "watcher-log", f"realtime stream dropped {summary['realtime_drops']} times")


def check_dashboard(kube: Kube, report: Report) -> None:
    ymd = f"{report.day:%Y%m%d}"
    dashboard = kube.raw("kiwoom-mcp:8000", f"/api/dashboard?start_date={ymd}&end_date={ymd}")
    overview = dashboard.get("overview") or {}
    report.data["dashboard_overview"] = overview
    report.add(INFO, "broker", (
        f"holdings {overview.get('holdings_count')}, open orders {overview.get('active_orders_count')}, "
        f"trade history rows {overview.get('trade_history_count')} (today-only sources such as "
        "executions and open orders describe the day the check runs)"
    ))
    if overview.get("active_orders_count"):
        report.add(WARN, "broker", f"open orders at the broker: {overview['active_orders_count']}")
    holdings = ((dashboard.get("tables") or {}).get("holdings") or {}).get("rows") or []
    report.data["holdings"] = [
        {"code": row.get("stock_code"), "name": row.get("stock_name"), "quantity": _int(row.get("quantity"))}
        for row in holdings
    ]
    if holdings:
        report.add(INFO, "broker", "holdings " + ", ".join(
            f"{row.get('stock_name')} {_int(row.get('quantity'))}" for row in holdings
        ))
    for source in dashboard.get("sources") or []:
        if source.get("status") not in ("ok", "empty"):
            report.add(WARN, "broker", f"source {source.get('api_id')} {source.get('status')}: {source.get('message')}")


def _int(value: Any) -> int | None:
    try:
        return int(str(value).strip() or 0)
    except ValueError:
        return None


def check_ingress(kube: Kube, report: Report, namespace: str, deployment: str) -> None:
    since = datetime.combine(report.day, time(0), KST)
    lines = [line for line in parse_kubelet_lines(kube.logs(f"deploy/{deployment}", since, namespace), report.day)
             if "kiwoom-mcp" in line.text]
    hits = empty_mcp_responses(lines)
    report.data["empty_mcp_responses"] = hits
    report.add(WARN if hits else OK, "mcp", f"POST /mcp answered 200 with an empty body: {len(hits)} {hits}")


# Runs on the agent host through ``ssh <host> python3 - <day> <project>``.
# Read-only: it lists files, reads the daemon log and asks multica for issues.
AGENT_HOST_PROBE = r'''
import json, os, re, shutil, subprocess, sys
day, project = sys.argv[1], sys.argv[2]
home = os.path.expanduser("~")
out = {}
standalone = os.path.join(home, ".codex", "packages", "standalone")
current = os.path.join(standalone, "current")
out["codex_current"] = os.path.basename(os.path.realpath(current)) if os.path.lexists(current) else None
releases = os.path.join(standalone, "releases")
out["codex_releases"] = sorted(os.listdir(releases)) if os.path.isdir(releases) else []
try:
    with open(os.path.join(home, ".codex", "version.json")) as fh:
        out["codex_update_check"] = json.load(fh)
except Exception as error:
    out["codex_update_check"] = {"error": str(error)}
detected = None
try:
    with open(os.path.join(home, ".multica", "daemon.log"), errors="replace") as fh:
        for line in fh:
            if "agent version detected" in line and "name=codex" in line:
                detected = line
except Exception as error:
    out["daemon_log_error"] = str(error)
if detected:
    path = re.search(r"path=(\S+)", detected)
    version = re.search(r'version="([^"]+)"', detected)
    out["daemon_codex_path"] = path.group(1) if path else None
    out["daemon_codex_version"] = version.group(1) if version else None
    out["daemon_codex_path_exists"] = bool(path) and os.path.exists(path.group(1))
ps = subprocess.run(["ps", "-eo", "pid,lstart,args"], capture_output=True, text=True).stdout
out["daemon_processes"] = [l.strip() for l in ps.splitlines() if "multica daemon start" in l and "grep" not in l]
multica = shutil.which("multica") or "/usr/local/bin/multica"
issues = []
if project:
    search = subprocess.run([multica, "issue", "search", day, "--project", project, "--include-closed",
                             "--limit", "50", "--output", "json"], capture_output=True, text=True)
    try:
        found = json.loads(search.stdout).get("issues", [])
    except Exception:
        found, out["issue_search_error"] = [], (search.stderr or search.stdout)[:300]
    for issue in found:
        runs = subprocess.run([multica, "issue", "runs", issue["identifier"], "--output", "json"],
                              capture_output=True, text=True)
        try:
            run_rows = json.loads(runs.stdout)
        except Exception:
            run_rows = []
        issues.append({
            "identifier": issue.get("identifier"), "title": issue.get("title"), "status": issue.get("status"),
            "runs": [{"status": r.get("status"), "error": r.get("error"), "started_at": r.get("started_at"),
                      "completed_at": r.get("completed_at")} for r in run_rows],
        })
out["issues"] = issues
print(json.dumps(out, ensure_ascii=False))
'''


def check_agent_host(report: Report, host: str, project: str) -> None:
    # ssh joins its arguments into one remote command line, so quote them;
    # an empty project would otherwise vanish instead of arriving as "".
    remote = " ".join(["python3", "-", shlex.quote(report.day.isoformat()), shlex.quote(project)])
    done = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, remote],
        input=AGENT_HOST_PROBE, capture_output=True, text=True, timeout=180,
    )
    if done.returncode != 0:
        report.add(WARN, "agents", f"agent host probe failed: {done.stderr.strip()[:200]}")
        return
    probe = json.loads(done.stdout)
    report.data["agent_host"] = probe
    grade_agent_host(report, probe)


def grade_agent_host(report: Report, probe: dict[str, Any]) -> None:
    path_exists = probe.get("daemon_codex_path_exists")
    daemon_path = probe.get("daemon_codex_path") or ""
    current = probe.get("codex_current") or ""
    if path_exists is False:
        report.add(ALERT, "agents", f"daemon's codex binary is gone: {daemon_path}")
    elif "/releases/" in daemon_path and current and current not in daemon_path:
        report.add(WARN, "agents", (
            f"daemon runs {probe.get('daemon_codex_version')} but codex 'current' is {current}; "
            f"releases kept: {probe.get('codex_releases')} — the next auto-update may remove the daemon's binary"
        ))
    else:
        report.add(OK, "agents", f"daemon codex {probe.get('daemon_codex_version')} = current {current}")
    check = probe.get("codex_update_check") or {}
    if check.get("last_checked_at"):
        report.add(INFO, "agents", f"codex update check: latest {check.get('latest_version')} at {check.get('last_checked_at')}")
    if len(probe.get("daemon_processes") or []) != 1:
        report.add(WARN, "agents", f"multica daemon processes: {probe.get('daemon_processes')}")
    for issue in probe.get("issues") or []:
        runs = issue.get("runs") or []
        failed = [r for r in runs if r.get("status") not in ("completed",)]
        grade = ALERT if failed else OK
        report.add(grade, "agents", (
            f"{issue.get('identifier')} [{issue.get('status')}] {issue.get('title')}: "
            f"runs {[r.get('status') for r in runs]}" + (f" errors {[r.get('error') for r in failed]}" if failed else "")
        ))


# --------------------------------------------------------------------------


def render(report: Report) -> str:
    lines = [f"# kiwoom post-close check {report.day} — {report.verdict}"]
    section = None
    for finding in report.findings:
        if finding.section != section:
            section = finding.section
            lines.append(f"\n[{section}]")
        lines.append(f"{finding.grade} {finding.text}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", help="trading day YYYY-MM-DD (default: last closed trading day)")
    parser.add_argument("--namespace", default="tools")
    parser.add_argument("--kubectl", default="kubectl")
    parser.add_argument("--agent-host", default=os.environ.get("OPS_AGENT_HOST", ""))
    parser.add_argument("--multica-project", default=os.environ.get("MULTICA_PROJECT", ""))
    parser.add_argument("--ingress-namespace", default=os.environ.get("OPS_INGRESS_NAMESPACE", ""))
    parser.add_argument("--ingress-deployment", default=os.environ.get("OPS_INGRESS_DEPLOYMENT", ""))
    parser.add_argument("--skip-dashboard", action="store_true")
    parser.add_argument("--allow-session-reads", action="store_true",
                        help="fetch the dashboard even while the session is open")
    parser.add_argument("--json", help="also write the collected data and findings here")
    args = parser.parse_args(argv)

    now = datetime.now(KST)
    day = date.fromisoformat(args.date) if args.date else default_check_day(now)
    report = Report(day)
    if not is_krx_trading_day(day):
        report.add(WARN, "calendar", f"{day} is not a verified KRX trading day")
    opens, closes = session_hours(day)
    report.add(INFO, "calendar", f"session {opens:%H:%M}–{closes:%H:%M} KST")
    kube = Kube(args.kubectl, args.namespace)

    steps: list[tuple[str, Any]] = [
        ("cronjobs", lambda: check_cronjobs(kube, report)),
        ("watcher", lambda: check_watcher(kube, report, opens, closes)),
    ]
    session_open = krx_regular_session_status(now).is_open
    if args.skip_dashboard:
        pass
    elif session_open and not args.allow_session_reads:
        report.add(INFO, "broker", "dashboard skipped: the session is open (pass --allow-session-reads)")
    else:
        steps.append(("broker", lambda: check_dashboard(kube, report)))
    if args.ingress_namespace and args.ingress_deployment:
        steps.append(("mcp", lambda: check_ingress(kube, report, args.ingress_namespace, args.ingress_deployment)))
    if args.agent_host:
        steps.append(("agents", lambda: check_agent_host(report, args.agent_host, args.multica_project)))

    for name, step in steps:
        try:
            step()
        except Exception as error:  # one unreachable source must not hide the rest
            report.add(WARN, name, f"check failed: {type(error).__name__}: {str(error)[:200]}")

    print(render(report))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(
                {"day": day.isoformat(), "verdict": report.verdict,
                 "findings": [f.__dict__ for f in report.findings], "data": report.data},
                fh, ensure_ascii=False, indent=2, default=str,
            )
    return {"정상": 0, "주의": 1, "이상": 2}[report.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
