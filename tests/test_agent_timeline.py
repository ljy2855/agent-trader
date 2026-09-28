"""Tests for reconstructing the agent decision timeline.

Everything here is pure-function: no CLI, no HTTP. The fixtures below are trimmed
copies of real Multica comment bodies, so a change to
``watcher._build_trigger_comment`` that breaks the parser breaks these too — which
is the point, since that coupling is otherwise invisible.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.services.agent_timeline import (
    JOIN_TOLERANCE_SECONDS,
    build_rows,
    join_outcome,
    normalize_stock_code,
    parse_dispatch_comment,
    segment_thread,
)

KST = timezone(timedelta(hours=9))


# --- fixtures ---------------------------------------------------------------

STOCK_DISPATCH = """**[09:01:03 KST] [트리거: new_candidate]**

종목: 삼성전자 (005930)
사유: 신규 강한 후보 (score=9, day_change=1.67%)

## 포트폴리오 현황
- 보유: **0종목**
- 미체결: 0건
- 현금: 1,756,640원 · 총자산: 1,756,640원
- 후보 풀: 15건

```
{
  "score": 9,
  "day_change_pct": 1.67,
  "breakout": false
}
```

이 트리거에 대한 ACTION 결정을 **반드시 댓글로** 작성해 주세요.
옵션: TIER1 / TIER2 / REJECT

마지막 줄에 `<!-- ACTION: XXX -->` 형식으로 명시해주세요.
"""

GLOBAL_DISPATCH = """**[09:00:15 KST] [트리거: periodic_review]**

사유: 60분 정기 점검

```
{
  "interval_minutes": 60
}
```

옵션: HOLD / ACKNOWLEDGE
"""


def comment(content, *, author_type="agent", created_at="2026-08-04T00:01:53Z", parent_id=None):
    return {
        "content": content,
        "author_type": author_type,
        "created_at": created_at,
        "parent_id": parent_id,
    }


# --- parsing ----------------------------------------------------------------


def test_parses_stock_scoped_dispatch():
    info = parse_dispatch_comment(STOCK_DISPATCH, "2026-08-04T00:01:07Z")

    assert info is not None
    assert info.trigger_type == "new_candidate"
    assert info.scope == "stock"
    assert info.stock_code == "005930"
    assert info.stock_name == "삼성전자"
    assert info.reason == "신규 강한 후보 (score=9, day_change=1.67%)"
    assert info.snapshot == {"score": 9, "day_change_pct": 1.67, "breakout": False}
    assert info.snapshot_raw is None
    # Date from created_at (UTC→KST), clock time from the header.
    assert info.dispatched_at.strftime("%Y-%m-%d %H:%M:%S") == "2026-08-04 09:01:03"


def test_parses_global_dispatch_without_stock_line():
    info = parse_dispatch_comment(GLOBAL_DISPATCH, "2026-08-03T00:00:23Z")

    assert info is not None
    assert info.trigger_type == "periodic_review"
    assert info.scope == "global"
    assert info.stock_code is None
    assert info.stock_name is None
    assert info.snapshot == {"interval_minutes": 60}


def test_non_dispatch_comment_is_not_a_dispatch():
    assert parse_dispatch_comment("그냥 코멘트입니다", "2026-08-04T00:01:07Z") is None
    assert parse_dispatch_comment("", "2026-08-04T00:01:07Z") is None
    assert parse_dispatch_comment(None, "2026-08-04T00:01:07Z") is None


def test_watcher_followup_notices_do_not_open_a_segment():
    # Verbatim shapes from watcher._await_and_apply's timeout and stale branches.
    # They are authored as `member`, exactly like a dispatch.
    timeout = "**[watcher]** new_candidate 응답이 180초 내에 도착하지 않아 슬롯을 해제합니다."
    stale = "**[watcher]** ACTION=TIER2 폐기 — 트리거 이후 시세/포지션이 크게 변동."

    assert parse_dispatch_comment(timeout, "2026-08-04T00:05:00Z") is None
    assert parse_dispatch_comment(stale, "2026-08-04T00:05:00Z") is None


def test_reason_text_can_contain_bracketed_words_without_being_dropped():
    # The exclusion above must be anchored, not a substring search — an incident
    # reason mentioning an error is still a real dispatch.
    body = "**[09:01:03 KST] [트리거: api_failures]**\n\n사유: [오류] 연속 실패 3건 — **[watcher]** 로그 참조"
    info = parse_dispatch_comment(body, "2026-08-04T00:01:07Z")

    assert info is not None
    assert info.trigger_type == "api_failures"


def test_missing_reason_degrades_to_none_without_raising():
    body = "**[09:01:03 KST] [트리거: regime_flip]**\n\n```\n{\"a\": 1}\n```"
    info = parse_dispatch_comment(body, "2026-08-04T00:01:07Z")

    assert info is not None
    assert info.reason is None
    assert info.snapshot == {"a": 1}


def test_unparseable_snapshot_is_preserved_as_raw():
    body = "**[09:01:03 KST] [트리거: regime_flip]**\n\n사유: x\n\n```\n{not json,,,\n```"
    info = parse_dispatch_comment(body, "2026-08-04T00:01:07Z")

    assert info is not None
    assert info.snapshot is None
    assert info.snapshot_raw == "{not json,,,"


def test_snapshot_fence_has_no_info_string():
    # Regression guard: the producer writes a bare ``` fence. Keying the parser
    # on ```json would silently drop every snapshot.
    assert "```\n" in STOCK_DISPATCH
    assert "```json" not in STOCK_DISPATCH


def test_dispatch_near_midnight_takes_the_nearer_day():
    # Detected 23:59:58, comment posted three seconds later — the next KST day.
    info = parse_dispatch_comment(
        "**[23:59:58 KST] [트리거: periodic_review]**\n\n사유: x",
        "2026-08-13T15:00:01Z",  # = 2026-08-14 00:00:01 KST
    )

    assert info is not None
    assert info.dispatched_at.strftime("%Y-%m-%d %H:%M:%S") == "2026-08-13 23:59:58"


# --- stock code normalization ----------------------------------------------


def test_normalizes_both_account_and_market_code_shapes():
    # The account API returns A-prefixed codes and the market API does not; both
    # reach us, and an unnormalized join drops every holding trigger.
    assert normalize_stock_code("A018880") == "018880"
    assert normalize_stock_code("018880") == "018880"
    assert normalize_stock_code("5930") == "005930"
    assert normalize_stock_code(None) is None
    assert normalize_stock_code("") is None
    assert normalize_stock_code("없음") is None


# --- segmentation -----------------------------------------------------------


def test_thread_with_many_dispatches_yields_one_segment_each():
    # A PM cycle issue accumulates the whole day on one issue — SWO-690 had 15
    # dispatches across 32 comments.
    comments = []
    for i in range(15):
        comments.append(
            comment(
                f"**[{9 + i:02d}:00:00 KST] [트리거: periodic_review]**\n\n사유: 정기 {i}",
                author_type="member",
                created_at=f"2026-08-13T{i:02d}:00:05Z",
            )
        )
        comments.append(
            comment(
                f"판단 {i}\n\n<!-- ACTION: ACKNOWLEDGE -->",
                created_at=f"2026-08-13T{i:02d}:01:00Z",
            )
        )

    segments = segment_thread(comments)

    assert len(segments) == 15
    assert all(len(s.responses) == 1 for s in segments)
    assert all(s.final_action == "ACKNOWLEDGE" for s in segments)
    assert segments[3].dispatch.reason == "정기 3"


def test_system_comments_are_ignored():
    comments = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("All sub-issues are complete", author_type="system",
                created_at="2026-08-04T00:01:30Z"),
        comment("판단\n<!-- ACTION: REJECT -->", created_at="2026-08-04T00:01:53Z"),
    ]

    segments = segment_thread(comments)

    assert len(segments) == 1
    assert len(segments[0].responses) == 1
    assert segments[0].final_action == "REJECT"


def test_later_run_supersedes_an_earlier_one():
    # Multica re-runs a task whose first run ended without a usable tag; each run
    # posts its own comment, and the last verdict is the one the watcher applied.
    comments = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("1차 판단\n<!-- ACTION: TIER2 -->", created_at="2026-08-04T00:01:53Z"),
        comment("재검토\n<!-- ACTION: REJECT -->",
                created_at="2026-08-04T00:02:40Z", parent_id="c0"),
    ]

    segments = segment_thread(comments)

    assert len(segments[0].responses) == 2
    assert segments[0].final_action == "REJECT"
    assert segments[0].final_response.text.startswith("재검토")


def test_threaded_flag_is_descriptive_not_a_delegation_marker():
    # In a thread carrying a whole day of dispatches, an agent replies to the
    # dispatch comment purely to say which one it is answering. Treating that as
    # a squad delegation misreads every PM-cycle response.
    comments = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("판단\n<!-- ACTION: HOLD -->",
                created_at="2026-08-04T00:01:53Z", parent_id="c0"),
    ]

    segments = segment_thread(comments)

    assert segments[0].responses[0].threaded is True
    # It is still the answer, not a side note.
    assert segments[0].final_response is segments[0].responses[0]
    assert segments[0].final_action == "HOLD"


def test_agent_comments_before_any_dispatch_are_dropped():
    comments = [
        comment("고아 응답\n<!-- ACTION: HOLD -->", created_at="2026-08-04T00:00:01Z"),
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
    ]

    segments = segment_thread(comments)

    assert len(segments) == 1
    assert segments[0].responses == []
    assert segments[0].final_action is None


def test_comments_are_ordered_before_segmentation():
    comments = [
        comment("판단\n<!-- ACTION: REJECT -->", created_at="2026-08-04T00:01:53Z"),
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
    ]

    segments = segment_thread(comments)

    assert len(segments) == 1
    assert segments[0].final_action == "REJECT"


def test_no_tag_response_does_not_count_as_an_action():
    comments = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("처리 중입니다", created_at="2026-08-04T00:01:53Z"),
    ]

    segments = segment_thread(comments)

    assert segments[0].responses[0].action is None
    assert segments[0].final_action is None


# --- joining ----------------------------------------------------------------


def dispatch_at(seconds_from_nine, trigger="new_candidate", code="005930"):
    body = (
        f"**[09:{seconds_from_nine // 60:02d}:{seconds_from_nine % 60:02d} KST] "
        f"[트리거: {trigger}]**\n\n"
    )
    if code:
        body += f"종목: 종목명 ({code})\n"
    body += "사유: x"
    return parse_dispatch_comment(body, "2026-08-04T00:01:07Z")


def recent_entry(detected, *, trigger="new_candidate", code="005930", outcome="submitted"):
    return {
        "detected_at": detected.isoformat(),
        "trigger_type": trigger,
        "stock_code": code,
        "outcome": outcome,
        "action": "TIER2",
        "detail": "매수 주문 접수",
        "completed_at": detected.isoformat(),
        "tier": 2,
    }


def test_join_matches_on_trigger_code_and_time():
    info = dispatch_at(63)
    entry = recent_entry(info.dispatched_at - timedelta(seconds=4))

    outcome, source = join_outcome(info, [entry])

    assert source == "watcher"
    assert outcome["outcome"] == "submitted"


def test_join_normalizes_the_a_prefix():
    info = dispatch_at(63, trigger="holding_swing", code="A018880")
    entry = recent_entry(
        info.dispatched_at, trigger="holding_swing", code="018880", outcome="filled"
    )

    outcome, source = join_outcome(info, [entry])

    assert source == "watcher"
    assert outcome["outcome"] == "filled"


def test_join_respects_the_tolerance_boundary():
    info = dispatch_at(63)
    inside = recent_entry(
        info.dispatched_at - timedelta(seconds=JOIN_TOLERANCE_SECONDS - 1)
    )
    outside = recent_entry(
        info.dispatched_at - timedelta(seconds=JOIN_TOLERANCE_SECONDS + 1)
    )

    assert join_outcome(info, [inside])[1] == "watcher"
    assert join_outcome(info, [outside])[1] == "unmatched"


def test_join_refuses_to_guess_between_near_simultaneous_entries():
    info = dispatch_at(63)
    first = recent_entry(info.dispatched_at - timedelta(seconds=1))
    second = recent_entry(info.dispatched_at + timedelta(seconds=2))

    outcome, source = join_outcome(info, [first, second])

    # Attaching either one would put an unverified order result on a decision.
    assert source == "ambiguous"
    assert outcome is None


def test_join_does_not_cross_trigger_types_or_stocks():
    info = dispatch_at(63)
    wrong_trigger = recent_entry(info.dispatched_at, trigger="holding_swing")
    wrong_stock = recent_entry(info.dispatched_at, code="000660")

    assert join_outcome(info, [wrong_trigger, wrong_stock])[1] == "unmatched"


def test_global_dispatch_only_joins_global_entries():
    info = dispatch_at(15, trigger="periodic_review", code=None)
    stock_entry = recent_entry(
        info.dispatched_at, trigger="periodic_review", code="005930"
    )
    global_entry = recent_entry(
        info.dispatched_at, trigger="periodic_review", code=None
    )

    assert join_outcome(info, [stock_entry])[1] == "unmatched"
    assert join_outcome(info, [global_entry])[1] == "watcher"


# --- merged rows ------------------------------------------------------------


def test_rows_merge_tier1_and_sort_newest_first():
    thread = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("판단\n<!-- ACTION: REJECT -->", created_at="2026-08-04T00:01:53Z"),
    ]
    tier1 = {
        "detected_at": datetime(2026, 8, 4, 10, 30, tzinfo=KST).isoformat(),
        "trigger_type": "stop_loss",
        "tier": 1,
        "scope": "stock",
        "stock_code": "A018880",
        "stock_name": "한온시스템",
        "reason": "수익률 -4.2%",
        "outcome": "filled",
        "action": None,
        "detail": "전량 시장가 매도",
    }

    rows = build_rows([({"identifier": "SWO-658"}, thread)], [tier1])

    assert [r["kind"] for r in rows] == ["tier1", "tier2"]
    assert rows[0]["trigger_type"] == "stop_loss"
    assert rows[0]["stock_code"] == "018880"
    # Tier 1 runs in code with no agent round trip — no reasoning by design.
    assert rows[0]["responses"] == []
    assert rows[0]["outcome"]["outcome"] == "filled"
    assert rows[1]["final_action"] == "REJECT"


def test_empty_recent_marks_every_row_unavailable_not_unmatched():
    # A watcher restart empties the process-lifetime ring buffer. That is a
    # payload-level fact, not N separate reconciliation failures.
    thread = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("판단\n<!-- ACTION: REJECT -->", created_at="2026-08-04T00:01:53Z"),
    ]

    rows = build_rows([(None, thread)], [])

    assert len(rows) == 1
    assert rows[0]["outcome_source"] == "unavailable"
    assert rows[0]["outcome"] is None
    assert rows[0]["final_action"] == "REJECT"


def test_tier1_can_be_excluded_and_limit_applies():
    entries = [
        {
            "detected_at": datetime(2026, 8, 4, 10, i, tzinfo=KST).isoformat(),
            "trigger_type": "stop_loss",
            "tier": 1,
            "stock_code": "005930",
            "outcome": "filled",
        }
        for i in range(5)
    ]

    assert build_rows([], entries, include_tier1=False) == []
    assert len(build_rows([], entries, limit=3)) == 3


def test_rows_are_json_safe():
    thread = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("판단\n<!-- ACTION: REJECT -->", created_at="2026-08-04T00:01:53Z"),
    ]

    import json

    rows = build_rows([({"identifier": "SWO-658"}, thread)], [])
    json.dumps(rows)  # must not raise — this payload goes straight to JSONResponse


# --- squad delegation child issues ------------------------------------------


def test_delegation_child_issue_becomes_its_own_row():
    # Squad leaders delegate boundary cases as a *child issue*, which is the
    # cross-check standing in for Gemini peer review on squad-routed triggers.
    # Its reasoning never touches the parent thread, so without this it is
    # invisible.
    issue = {
        "id": "i1",
        "identifier": "SWO-692",
        "title": "[위임] 10:29 risk_off 전환 리스크 점검",
        "status": "done",
        "created_at": "2026-08-13T01:35:00Z",
    }
    comments = [comment("리스크 점검 결과…\n<!-- ACTION: ACKNOWLEDGE -->",
                        created_at="2026-08-13T01:35:00Z")]

    rows = build_rows([(issue, comments)], [])

    assert len(rows) == 1
    row = rows[0]
    assert row["kind"] == "delegation"
    assert row["final_action"] == "ACKNOWLEDGE"
    assert row["reason"] == "risk_off 전환 리스크 점검"
    assert row["issue"]["identifier"] == "SWO-692"
    # An opinion, not an order — nothing to reconcile against the broker.
    assert row["outcome_source"] == "not_applicable"
    # The title's clock time places it next to the decision it belongs to.
    assert row["dispatched_at"][11:16] == "10:29"


def test_delegation_without_a_time_falls_back_to_the_comment_timestamp():
    issue = {
        "id": "i2",
        "identifier": "SWO-470",
        "title": "[위임] 대우건설 (047040) 슬리피지 및 유동성 점검",
        "created_at": "2026-08-13T01:00:00Z",
    }
    comments = [comment("검토\n<!-- ACTION: MITIGATE -->",
                        created_at="2026-08-13T02:00:00Z")]

    rows = build_rows([(issue, comments)], [])

    assert rows[0]["kind"] == "delegation"
    assert rows[0]["dispatched_at"][11:16] == "11:00"


def test_delegation_issues_do_not_also_produce_dispatch_segments():
    issue = {"id": "i3", "identifier": "SWO-692", "title": "[위임] 10:29 점검"}
    # Even if a delegation thread somehow carried a dispatch header, it is
    # classified once — as a delegation — not counted twice.
    comments = [
        comment(GLOBAL_DISPATCH, author_type="member", created_at="2026-08-13T00:00:23Z"),
        comment("판단\n<!-- ACTION: HOLD -->", created_at="2026-08-13T00:01:00Z"),
    ]

    rows = build_rows([(issue, comments)], [])

    assert len(rows) == 1
    assert rows[0]["kind"] == "delegation"


def test_ordinary_issue_titles_are_not_treated_as_delegations():
    issue = {"id": "i4", "identifier": "SWO-691", "title": "[한국전력] (015760) 2026-08-13 후보 평가"}
    comments = [
        comment(STOCK_DISPATCH, author_type="member", created_at="2026-08-04T00:01:07Z"),
        comment("판단\n<!-- ACTION: REJECT -->", created_at="2026-08-04T00:01:53Z"),
    ]

    rows = build_rows([(issue, comments)], [])

    assert rows[0]["kind"] == "tier2"


def test_delegation_trigger_is_named_like_other_triggers():
    issue = {"id": "i5", "identifier": "SWO-692", "title": "[위임] 10:29 risk_off 점검"}
    rows = build_rows(
        [(issue, [comment("검토\n<!-- ACTION: ACKNOWLEDGE -->",
                          created_at="2026-08-13T01:35:00Z")])],
        [],
    )

    assert rows[0]["trigger_type"] == "squad_delegation"
