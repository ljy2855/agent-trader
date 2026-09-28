"""Multica issue/comment dispatch + ACTION polling for the watcher.

Wraps the ``multica`` CLI as in-process callable objects so the watcher
does not need to fork a subprocess for each tick.

Issue layout:

* Daily parent issue: ``YYYY-MM-DD <DAILY_ISSUE_SUFFIX>``  → portfolio manager
* Per-stock child issue: ``[NAME] (CODE) YYYY-MM-DD 보유 분석``  → evaluator
* Per-stock candidate child: ``[NAME] (CODE) YYYY-MM-DD 후보 평가``  → screener
* Global PM child: daily parent (re-used)
* Global risk child: ``[리스크] YYYY-MM-DD 리스크 알림``  → risk manager

The watcher posts trigger comments and waits asynchronously for the
agent's next *new* completed run, parsing the ``<!-- ACTION: ... -->``
tag from the run output.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

KST = timezone(timedelta(hours=9))

MULTICA_BIN = os.environ.get("MULTICA_BIN", "/opt/homebrew/bin/multica")
DEFAULT_PROJECT = os.environ.get("MULTICA_PROJECT", "")
DEFAULT_DAILY_SUFFIX = os.environ.get("DAILY_ISSUE_SUFFIX", "장중 실거래")
DEFAULT_COORDINATOR_AGENT = os.environ.get(
    "MULTICA_COORDINATOR_AGENT", "Kiwoom 에이전트 오케스트레이터"
)

ACTION_PATTERNS = (
    re.compile(r"<!--\s*ACTION:\s*([A-Z0-9_]+)", re.IGNORECASE),
    re.compile(r"\b(?:FINAL\s+)?ACTION\s*[:=]\s*`?([A-Z0-9_]+)`?", re.IGNORECASE),
    re.compile(r"\b최종\s+ACTION(?:은|는)?\s*`?([A-Z0-9_]+)`?", re.IGNORECASE),
)

VALID_ACTIONS = frozenset(
    {
        "HOLD",
        "TRIM",
        "TAKE_PROFIT",
        "CUT_LOSS",
        "ROTATE",
        "ACKNOWLEDGE",
        "ESCALATE",
        "MITIGATE",
        "TIER1",
        "TIER2",
        "REJECT",
        "WRAP_DONE",
        "BRIEF_DONE",
    }
)


# Squad-routed issue types: leader agent dynamically delegates to members
# inside the squad instead of the watcher running a fixed
# primary→peer→orchestrator chain. Other types (holding/incident/trade)
# keep the deterministic peer-review pipeline because their decision space
# is narrow enough that fixed cross-check is preferable to LLM-driven
# delegation.
SQUAD_ROUTED_ISSUE_TYPES = frozenset({"daily", "candidate"})


def _agent_for() -> dict[str, str]:
    """Resolve issue-type → assignee. Live (real-stock) is the only mode.

    "daily" and "candidate" route to squads (leader auto-runs on assign).
    """

    return {
        "daily": "PM 스쿼드 (실거래)",
        "holding": "투자 평가사 (실거래)",
        "candidate": "후보 스크리너 스쿼드 (실거래)",
        "incident": "리스크 매니저 (실거래)",
        "trade": "투자 평가사 (실거래)",
    }


def _peer_for() -> dict[str, str]:
    """Resolve issue-type -> cross-review agent (live only).

    Squad-routed types intentionally omitted — squad leaders handle
    cross-checking via member delegation rather than a fixed peer pass.

    Reviewers are a *different role* from the primary, not a different model:
    the Gemini variants these used to point at are unavailable since the
    subscription lapsed (2026-09-02). A same-model reviewer is a weaker check
    than a cross-vendor one — it can share the primary's blind spots — so the
    role split is what independence rests on now. The evaluator decides an
    exit; risk reviews it. The reviewer never executes, so the worst case is
    a second opinion that agrees too readily, which is what the arbitration
    step already handles.
    """

    return {
        "holding": "리스크 매니저 (실거래)",
        "incident": "투자 평가사 (실거래)",
        "trade": "리스크 매니저 (실거래)",
    }


# ACTIONs that move money. A no-op verdict is not worth a second agent run:
# reviewing a HOLD costs the same as reviewing a liquidation and changes
# nothing, and those runs are most of the volume (2026-09-02: 5 holding
# dispatches, 1 of them an exit). Cross-review is spent where an order
# actually follows.
CONSEQUENTIAL_ACTIONS = frozenset(
    {"TRIM", "TAKE_PROFIT", "CUT_LOSS", "ROTATE", "MITIGATE", "ESCALATE"}
)

# Comments after which a day-scoped issue rolls to a new part.
#
# An agent run reads the whole thread it is answering on, so a day-scoped
# issue makes cost grow with the square of the dispatch count, not linearly:
# the 28th run on 2026-09-02 re-read the 27 before it (59 comments, 36,681
# characters), and that is what exhausted the codex quota. Rolling over caps
# what any single run has to read while keeping the day's history intact and
# linked under the same parent.
#
# 24 is roughly a session's worth of triggers at the observed cadence -- high
# enough that an ordinary day never rolls, low enough that a storm is capped.
ISSUE_COMMENT_ROLLOVER = 24


def _today_str(now: datetime | None = None) -> str:
    return (now or datetime.now(KST)).strftime("%Y-%m-%d")


@dataclass(slots=True)
class ActionResponse:
    """Result of an agent run pull."""

    action: str
    output: str
    run_id: str | None
    completed_at: datetime | None


@dataclass(slots=True)
class IssueRef:
    """Minimal reference returned by issue-create / issue-find calls."""

    id: str
    title: str
    parent_id: str | None = None


def extract_parent_id(issue: dict[str, Any]) -> str | None:
    """Return the parent issue id regardless of which casing the API used.

    The Multica API actually returns ``parent_issue_id`` but several
    client snippets historically read ``parentId`` / ``parent_id``. Treat
    all three as aliases.
    """

    for key in ("parent_issue_id", "parentIssueId", "parent_id", "parentId"):
        value = issue.get(key)
        if value:
            return str(value)
    return None


class MulticaDispatcher:
    """Synchronous Multica CLI helpers wrapped in an async-friendly façade.

    The CLI is invoked via ``subprocess.run`` in a worker thread so
    ``asyncio.to_thread`` keeps the watcher loop responsive.
    """

    def __init__(
        self,
        *,
        project: str = DEFAULT_PROJECT,
        daily_suffix: str = DEFAULT_DAILY_SUFFIX,
        binary: str = MULTICA_BIN,
        coordinator_agent: str = DEFAULT_COORDINATOR_AGENT,
    ):
        self.project = project
        self.daily_suffix = daily_suffix
        self.binary = binary
        self.coordinator_agent = coordinator_agent
        self.agent_for = _agent_for()
        self.peer_for = _peer_for()
        self._issue_cache: dict[str, IssueRef] = {}
        # issue id -> comments this process has posted there, for rollover.
        self._comment_counts: dict[str, int] = {}

    # -- low-level CLI helpers ------------------------------------------------

    def _run(self, args: list[str], stdin: str | None = None) -> tuple[int, str, str]:
        proc = subprocess.run(
            [self.binary, *args],
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr

    async def _run_async(
        self, args: list[str], stdin: str | None = None
    ) -> tuple[int, str, str]:
        return await asyncio.to_thread(self._run, args, stdin)

    @staticmethod
    def _parse_json(text: str) -> Any:
        try:
            return json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return None

    # -- issue lookup / creation ---------------------------------------------

    async def _list_issues(self) -> list[dict[str, Any]]:
        rc, out, _err = await self._run_async(
            [
                "issue",
                "list",
                "--project",
                self.project,
                "--output",
                "json",
                "--limit",
                "200",
            ]
        )
        if rc != 0:
            return []
        data = self._parse_json(out)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("issues"), list):
            return data["issues"]
        return []

    async def _find_by_title(self, title: str) -> IssueRef | None:
        if title in self._issue_cache:
            return self._issue_cache[title]
        for issue in await self._list_issues():
            t = issue.get("title")
            if isinstance(t, str) and t == title:
                ref = IssueRef(
                    id=str(issue.get("id") or ""),
                    title=t,
                    parent_id=extract_parent_id(issue),
                )
                if ref.id:
                    self._issue_cache[title] = ref
                    return ref
        return None

    async def _create_issue(
        self,
        *,
        title: str,
        description: str,
        issue_type: str,
        parent_id: str | None = None,
        priority: str = "medium",
    ) -> IssueRef | None:
        assignee = self.agent_for.get(issue_type, self.agent_for["daily"])
        args = [
            "issue",
            "create",
            "--project",
            self.project,
            "--title",
            title,
            "--description",
            description,
            "--assignee",
            assignee,
            "--priority",
            priority,
            "--output",
            "json",
        ]
        if parent_id:
            args.extend(["--parent", parent_id])
        rc, out, _err = await self._run_async(args)
        if rc != 0:
            return None
        data = self._parse_json(out)
        if isinstance(data, dict) and data.get("id"):
            ref = IssueRef(id=str(data["id"]), title=title)
            self._issue_cache[title] = ref
            return ref
        return None

    async def ensure_daily_issue(self, *, now: datetime | None = None) -> IssueRef | None:
        title = f"{_today_str(now)} {self.daily_suffix}"
        existing = await self._find_by_title(title)
        if existing is not None:
            return existing
        desc = (
            "Watcher 트리거 기반 사이클 로그가 댓글로 누적됩니다. "
            "보유 종목별 개별 분석은 자식 이슈로 연결되며, "
            "포트폴리오 매니저가 사이클 판단 및 daily-wrap을 담당합니다."
        )
        return await self._create_issue(
            title=title, description=desc, issue_type="daily", priority="medium"
        )

    async def ensure_holding_issue(
        self, *, code: str, name: str, now: datetime | None = None
    ) -> IssueRef | None:
        daily = await self.ensure_daily_issue(now=now)
        if daily is None:
            return None
        desc = (
            f"종목: {name} ({code})\n일자: {_today_str(now)}\n\n"
            "Watcher가 트리거 발화 시 이 종목 댓글로 평가사 의견을 요청합니다. "
            "평가사는 ACTION 태그(HOLD/TRIM/TAKE_PROFIT/CUT_LOSS/ROTATE)로 응답합니다."
        )
        return await self._ensure_rolling_issue(
            base_title=f"[{name}] ({code}) {_today_str(now)} 보유 분석",
            description=desc,
            issue_type="holding",
            parent_id=daily.id,
        )

    async def ensure_candidate_issue(
        self, *, code: str, name: str, now: datetime | None = None
    ) -> IssueRef | None:
        daily = await self.ensure_daily_issue(now=now)
        if daily is None:
            return None
        title = f"[{name}] ({code}) {_today_str(now)} 후보 평가"
        existing = await self._find_by_title(title)
        if existing is not None:
            return existing
        desc = (
            f"종목: {name} ({code})\n일자: {_today_str(now)}\n\n"
            "Watcher가 신규 강한 후보를 감지하면 이 이슈에 코멘트로 의견을 요청합니다. "
            "스크리너는 ACTION 태그(TIER1/TIER2/REJECT)로 응답합니다."
        )
        return await self._create_issue(
            title=title,
            description=desc,
            issue_type="candidate",
            parent_id=daily.id,
            priority="medium",
        )

    async def ensure_pm_log_issue(self, *, now: datetime | None = None) -> IssueRef | None:
        """Per-day issue dedicated to the PM agent's global cycle comments.

        Splitting these out keeps the daily parent issue
        (``YYYY-MM-DD 장중 실거래``) readable as an audit trail rather than
        being buried under regime_flip / periodic_review comments.
        """

        daily = await self.ensure_daily_issue(now=now)
        if daily is None:
            return None
        desc = (
            "Watcher가 발화한 글로벌 PM 트리거(periodic_review · regime_flip · "
            "extreme_risk_off)에 대한 PM agent 코멘트를 누적합니다. "
            "informational 응답이 주이며, 자동 매매로 이어지지 않습니다."
        )
        return await self._ensure_rolling_issue(
            base_title=f"[PM 코멘트] {_today_str(now)} 사이클 점검",
            description=desc,
            issue_type="daily",
            parent_id=daily.id,
        )

    async def ensure_risk_issue(self, *, now: datetime | None = None) -> IssueRef | None:
        daily = await self.ensure_daily_issue(now=now)
        if daily is None:
            return None
        title = f"[리스크] {_today_str(now)} 리스크 알림"
        existing = await self._find_by_title(title)
        if existing is not None:
            return existing
        desc = (
            "Watcher가 인프라/체결/API 헬스 트리거를 감지할 때 "
            "이 이슈에 코멘트로 리스크 매니저 판단을 요청합니다. "
            "ACTION 태그(ACKNOWLEDGE/MITIGATE/ESCALATE)로 응답합니다."
        )
        return await self._create_issue(
            title=title,
            description=desc,
            issue_type="incident",
            parent_id=daily.id,
            priority="high",
        )

    # -- comments + run polling ---------------------------------------------

    async def add_comment(self, issue_id: str, content: str) -> bool:
        rc, _out, _err = await self._run_async(
            [
                "issue",
                "comment",
                "add",
                issue_id,
                "--content-stdin",
                "--output",
                "json",
            ],
            stdin=content,
        )
        if rc == 0:
            self._comment_counts[issue_id] = self._comment_counts.get(issue_id, 0) + 1
        return rc == 0

    async def _comment_count(self, ref: IssueRef) -> int:
        """Every comment on an issue, read from the broker each time it matters.

        The count has to cover the whole thread, because that is what an
        agent run re-reads — and roughly half of it is the agent's own
        replies. Trusting the local tally counted only the comments this
        process wrote, so on 2026-09-15 the PM thread reached 41 comments
        (21 ours, 20 the agent's) while the tally read 21 and the rollover
        at 24 never came close. Twenty-two runs re-read that thread and
        exhausted the codex daily limit for three and a half hours.

        Seeding from the broker only on first sight could not fix it: an
        issue this process created is never looked up, so its tally starts
        at zero and stays ours-only for the life of the process.

        One CLI call per rollover check, which is nothing next to the agent
        run it protects. A failed read falls back to the local tally and
        then to 0, keeping the issue in use rather than spawning parts on a
        transient error: over-long threads cost tokens, spurious parts lose
        history.
        """

        rc, out, _err = await self._run_async(
            ["issue", "comment", "list", ref.id, "--output", "json"]
        )
        if rc == 0:
            data = self._parse_json(out)
            items: Any = None
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("items") or data.get("comments")
            if isinstance(items, list):
                self._comment_counts[ref.id] = len(items)
                return len(items)
        return self._comment_counts.get(ref.id, 0)

    async def _needs_rollover(self, ref: IssueRef | None) -> bool:
        """Has this issue taken enough comments to warrant a fresh part?"""

        if ref is None:
            return False
        return await self._comment_count(ref) >= ISSUE_COMMENT_ROLLOVER

    async def _ensure_rolling_issue(
        self,
        *,
        base_title: str,
        description: str,
        issue_type: str,
        parent_id: str | None,
        priority: str = "medium",
    ) -> IssueRef | None:
        """Return today's issue for a title, opening a new part when it fills.

        Parts are titled ``<base> (2)``, ``(3)`` and so on. Lookup walks the
        existing parts in order and stops at the first one with room, so a
        restarted process re-attaches to the newest part instead of reopening
        part 1.
        """

        for part in range(1, 100):
            title = base_title if part == 1 else f"{base_title} ({part})"
            existing = await self._find_by_title(title)
            if existing is None:
                return await self._create_issue(
                    title=title,
                    description=description,
                    issue_type=issue_type,
                    parent_id=parent_id,
                    priority=priority,
                )
            if not await self._needs_rollover(existing):
                return existing
        return None

    async def update_assignee(self, issue_id: str, assignee: str) -> bool:
        rc, _out, _err = await self._run_async(
            [
                "issue",
                "update",
                issue_id,
                "--assignee",
                assignee,
                "--output",
                "json",
            ]
        )
        return rc == 0

    async def latest_completed_run(self, issue_id: str) -> dict[str, Any] | None:
        rc, out, _err = await self._run_async(
            ["issue", "runs", issue_id, "--output", "json"]
        )
        if rc != 0:
            return None
        data = self._parse_json(out)
        runs = data if isinstance(data, list) else (data or {}).get("runs", [])
        completed = [r for r in runs if isinstance(r, dict) and r.get("status") == "completed"]
        if not completed:
            return None
        completed.sort(key=lambda r: r.get("completed_at") or "", reverse=True)
        return completed[0]

    async def list_comments(self, issue_id: str) -> list[dict[str, Any]]:
        rc, out, _err = await self._run_async(
            ["issue", "comment", "list", issue_id, "--output", "json"]
        )
        if rc != 0:
            return []
        data = self._parse_json(out)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("comments"), list):
            return data["comments"]
        return []

    async def latest_action_comment(
        self, issue_id: str, *, since: str | None
    ) -> str | None:
        """Return content of the newest comment with a VALID ACTION tag.

        Squad leaders sometimes put the ACTION tag only in the issue
        comment, not in run.output (which holds narration like "Posted
        the ACTION comment..."). Scanning comments recovers the tag.

        Only accepts tags in VALID_ACTIONS — the watcher's own trigger
        template carries a literal `<!-- ACTION: XXX -->` placeholder, so
        a permissive match would surface "XXX?" from the template when an
        agent failed to post their own ACTION comment.
        """

        comments = await self.list_comments(issue_id)
        comments.sort(key=lambda c: c.get("created_at") or "", reverse=True)
        for c in comments:
            if not isinstance(c, dict):
                continue
            if since and (c.get("created_at") or "") < since:
                continue
            content = c.get("content") or c.get("body") or ""
            if isinstance(content, str) and extract_action_tag(content) in VALID_ACTIONS:
                return content
        return None

    async def wait_for_new_action(
        self,
        issue_id: str,
        *,
        prev_run_id: str | None,
        timeout_seconds: int,
        poll_seconds: int = 10,
    ) -> ActionResponse | None:
        """Poll runs/comments until a VALID_ACTION appears or timeout.

        A new completed run with output that has no ACTION tag is treated
        as a stub (e.g. agent emitted a status/thinking message before the
        real decision) — polling continues for either a newer run with
        VALID_ACTION or an ACTION comment posted after the first NO_TAG
        run started. The previous implementation returned on the first
        new run regardless of ACTION quality, dropping any later VALID
        response that fell within the timeout budget (2026-05-21 09:02
        regime_flip case: PM's ACKNOWLEDGE comment arrived 41s after the
        dispatcher had already given up with NO_TAG).

        Returns:
            - ActionResponse with action in VALID_ACTIONS if found.
            - ActionResponse with action="NO_TAG" if at least one new run
              completed but no VALID_ACTION appeared before the deadline.
            - None if no new run completed before the deadline.
        """

        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(timeout_seconds, 1)

        last_run_id = prev_run_id
        no_tag_response: ActionResponse | None = None
        no_tag_since: str | None = None

        while True:
            await asyncio.sleep(poll_seconds)

            top = await self.latest_completed_run(issue_id)
            if top and top.get("id") and top["id"] != last_run_id:
                output = (top.get("result") or {}).get("output") or ""
                completed_at_raw = top.get("completed_at")
                completed_at: datetime | None = None
                if completed_at_raw:
                    try:
                        completed_at = datetime.fromisoformat(
                            str(completed_at_raw).replace("Z", "+00:00")
                        )
                    except ValueError:
                        completed_at = None
                action = extract_action_tag(output)
                if action in VALID_ACTIONS:
                    return ActionResponse(
                        action=action,
                        output=output,
                        run_id=str(top["id"]),
                        completed_at=completed_at,
                    )
                last_run_id = str(top["id"])
                if no_tag_since is None:
                    no_tag_since = str(top.get("started_at") or "") or None
                no_tag_response = ActionResponse(
                    action=action,
                    output=output,
                    run_id=str(top["id"]),
                    completed_at=completed_at,
                )

            if no_tag_response is not None:
                fallback = await self.latest_action_comment(
                    issue_id,
                    since=no_tag_since,
                )
                if fallback is not None:
                    return ActionResponse(
                        action=extract_action_tag(fallback),
                        output=fallback,
                        run_id=no_tag_response.run_id,
                        completed_at=no_tag_response.completed_at,
                    )

            if loop.time() >= deadline:
                return no_tag_response

    async def request_peer_review(
        self,
        issue_id: str,
        *,
        issue_type: str,
        trigger_comment: str,
        primary_response: ActionResponse,
        timeout_seconds: int,
        poll_seconds: int = 10,
    ) -> ActionResponse | None:
        """Ask a peer agent to review the primary agent response.

        Multica issues support a single assignee, so peer review is done by
        briefly reassigning the issue to the reviewer, posting a review
        request, waiting for the next run, and then restoring the primary
        assignee. The primary ACTION remains the watcher's execution input;
        the peer response is recorded as a second opinion in the issue.

        Only consequential ACTIONs are reviewed. A HOLD costs a full agent
        run to confirm a decision that changes nothing, and those dominate
        the volume -- reviewing them is how one held position turned into 31
        runs on a single issue (2026-08-31).
        """

        if issue_type in SQUAD_ROUTED_ISSUE_TYPES:
            # Squad leader handles cross-checking internally via member
            # delegation; skip the deterministic peer pass.
            return None

        if primary_response.action not in CONSEQUENTIAL_ACTIONS:
            return None

        primary_assignee = self.agent_for.get(issue_type, self.agent_for["daily"])
        peer_assignee = self.peer_for.get(issue_type)
        if not peer_assignee or peer_assignee == primary_assignee:
            # A reviewer that is the primary would just re-run the same agent
            # on its own output -- no independence, double the cost.
            return None

        if not await self.update_assignee(issue_id, peer_assignee):
            return None

        try:
            before = await self.latest_completed_run(issue_id)
            prev_peer_run_id = str(before["id"]) if before and before.get("id") else None
            primary_output = (primary_response.output or "").strip()
            if len(primary_output) > 6000:
                primary_output = primary_output[:6000] + "\n\n[watcher] primary output truncated"
            review_comment = (
                "**[watcher] 교차검토 요청**\n\n"
                "아래 트리거와 1차 agent 응답을 독립적으로 검토해주세요. "
                "동의/반대 여부와 근거를 남기고 마지막 줄에는 당신의 ACTION 태그를 남겨주세요.\n\n"
                "## 원 트리거\n"
                f"{trigger_comment}\n\n"
                "## 1차 agent 응답\n"
                f"{primary_output or '(empty output)'}\n\n"
                f"1차 ACTION: `{primary_response.action}`"
            )
            if not await self.add_comment(issue_id, review_comment):
                return None
            return await self.wait_for_new_action(
                issue_id,
                prev_run_id=prev_peer_run_id,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
            )
        finally:
            await self.update_assignee(issue_id, primary_assignee)

    async def request_action_arbitration(
        self,
        issue_id: str,
        *,
        issue_type: str,
        trigger_comment: str,
        primary_response: ActionResponse,
        peer_response: ActionResponse,
        timeout_seconds: int,
        poll_seconds: int = 10,
    ) -> ActionResponse | None:
        """Ask the coordinator agent to arbitrate a primary/peer mismatch."""

        if issue_type in SQUAD_ROUTED_ISSUE_TYPES:
            # Squad leader already arbitrates internally — no orchestrator hop.
            return None

        primary_assignee = self.agent_for.get(issue_type, self.agent_for["daily"])
        if not self.coordinator_agent:
            return None
        if not await self.update_assignee(issue_id, self.coordinator_agent):
            return None

        try:
            before = await self.latest_completed_run(issue_id)
            prev_run_id = str(before["id"]) if before and before.get("id") else None
            primary_output = (primary_response.output or "").strip()
            peer_output = (peer_response.output or "").strip()
            if len(primary_output) > 5000:
                primary_output = primary_output[:5000] + "\n\n[watcher] primary output truncated"
            if len(peer_output) > 5000:
                peer_output = peer_output[:5000] + "\n\n[watcher] peer output truncated"
            comment = (
                "**[watcher] 오케스트레이터 중재 요청**\n\n"
                "1차 agent와 교차검토 agent의 ACTION이 다릅니다. "
                "아래 자료를 비교해 최종 ACTION을 결정해주세요. "
                "마지막 줄에는 최종 ACTION 태그를 남겨주세요.\n\n"
                "## 원 트리거\n"
                f"{trigger_comment}\n\n"
                "## Primary agent 응답\n"
                f"{primary_output or '(empty output)'}\n\n"
                "## 교차검토 응답\n"
                f"{peer_output or '(empty output)'}\n\n"
                f"Primary ACTION: `{primary_response.action}`\n"
                f"교차검토 ACTION: `{peer_response.action}`"
            )
            if not await self.add_comment(issue_id, comment):
                return None
            return await self.wait_for_new_action(
                issue_id,
                prev_run_id=prev_run_id,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
            )
        finally:
            await self.update_assignee(issue_id, primary_assignee)


def extract_action_tag(text: str | None) -> str:
    """Return the ACTION tag embedded in agent output, or ``NO_TAG``."""

    if not text:
        return "NO_TAG"
    for pattern in ACTION_PATTERNS:
        m = pattern.search(text)
        if m:
            tag = m.group(1).upper()
            return tag if tag in VALID_ACTIONS else f"{tag}?"
    return "NO_TAG"


__all__ = [
    "ActionResponse",
    "IssueRef",
    "MulticaDispatcher",
    "VALID_ACTIONS",
    "extract_action_tag",
    "extract_parent_id",
]
