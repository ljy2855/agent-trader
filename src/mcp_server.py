"""MCP server implementation using FastMCP for Kiwoom OpenAPI integration."""

from __future__ import annotations

import asyncio

from datetime import datetime
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from .agent_overview import build_agent_overview, build_agent_timeline, fetch_watcher_ledger
from .config import get_settings
from .dashboard import (
    build_dashboard_snapshot,
    _default_start_date,
    _render_dashboard_page,
    _today_ymd,
    _validate_ymd,
)
from .services.kiwoom_client import KiwoomClient
from .services import account, live_config, market, order, stock_tools, strategy
from .trade_engine import BackgroundTradeEngine

DateYmd = Annotated[
    str,
    Field(description="YYYYMMDD 형식의 날짜. 예: 20260322", pattern=r"^\d{8}$"),
]
StockCode = Annotated[
    str,
    Field(description="6자리 종목코드. 예: 005930", pattern=r"^\d{6}$"),
]
OptionalStockCode = Annotated[
    str | None,
    Field(description="6자리 종목코드. 필요할 때만 입력", pattern=r"^\d{6}$"),
]
NumericText = Annotated[
    str,
    Field(description="숫자만 포함한 문자열", pattern=r"^\d+$"),
]
OptionalNumericText = Annotated[
    str | None,
    Field(description="필요할 때만 입력하는 숫자 문자열", pattern=r"^\d+$"),
]
OrderNumber = Annotated[
    str,
    Field(description="주문번호 또는 원주문번호. 숫자 문자열", pattern=r"^\d+$"),
]
ConfirmLiveOrder = Annotated[
    Literal[True],
    Field(description="실제 주문 실행 확인. 반드시 true여야만 실주문 요청을 전송합니다"),
]
ConfirmMockStrategyExecution = Annotated[
    Literal[True],
    Field(description="모의투자 전략 주문 실행 확인. KIWOOM_USE_MOCK=true일 때만 true로 주문을 전송합니다"),
]
OrderTypeCode = Annotated[
    Literal["0", "3", "5", "61", "62", "81", "6", "7", "10", "13", "16", "20", "23", "26", "28", "29", "30", "31"],
    Field(
        description=(
            "주문구분코드. 예: 0=보통(지정가), 3=시장가, 5=조건부지정가, "
            "61=장시작전시간외, 62=시간외단일가, 81=장마감후시간외"
        )
    ),
]
StrategyWatchlist = Annotated[
    list[StockCode] | None,
    Field(description="추가 감시 대상 6자리 종목코드 배열. 비우면 기본 관심종목과 보유종목을 사용"),
]
LeadersLimit = Annotated[
    int,
    Field(description="랭킹 기반 후보 수집 개수", ge=3, le=30),
]
StrategyCycleInterval = Annotated[
    int,
    Field(description="장중 전략 실행 주기(초)", ge=5, le=3600),
]
StrategyOffHoursInterval = Annotated[
    int,
    Field(description="장외 대기 주기(초)", ge=10, le=14400),
]
OptionalLeadersLimit = Annotated[
    int | None,
    Field(description="랭킹 기반 후보 수집 개수. 지정 시 3~30", ge=3, le=30),
]
OptionalCandidateLimit = Annotated[
    int | None,
    Field(description="상세 분석할 후보 최대 개수. 지정 시 1~10", ge=1, le=10),
]
OptionalMaxPositions = Annotated[
    int | None,
    Field(description="최대 동시 보유 종목 수. 지정 시 1~10", ge=1, le=10),
]
OptionalMaxNewPositions = Annotated[
    int | None,
    Field(description="한 번의 실행에서 새로 열 수 있는 최대 포지션 수. 지정 시 1~5", ge=1, le=5),
]
OptionalPositionBudgetPercent = Annotated[
    int | None,
    # Live has run 60 since 2026-09-10; a ceiling of 50 could not express the
    # deployed value at all, so the tool could not be asked to match it.
    Field(description="종목당 예산 비중(%). 지정 시 1~100", ge=1, le=100),
]

# Strategy-shaping parameters, all optional: left unset they resolve from the
# deployed watcher rather than from this file. See src/services/live_config.py.
OptionalEntryMode = Annotated[
    Literal["momentum", "below_ma"] | None,
    Field(
        description=(
            "진입 시그널. momentum=당일 상승률 추격, below_ma=이동평균 하회 "
            "눌림목. 미지정 시 배포된 watcher의 실효값을 따른다"
        )
    ),
]
OptionalMaPeriod = Annotated[
    int | None,
    Field(description="below_ma 이동평균 기간(일). 지정 시 5~60", ge=5, le=60),
]
OptionalUniverseMode = Annotated[
    Literal["leaders", "roster", "both"] | None,
    Field(
        description=(
            "후보 유니버스. leaders=등락률/거래대금 상위, roster=KOSPI 대형주 "
            "고정 로스터, both=둘 다. 미지정 시 배포값(라이브는 roster)"
        )
    ),
]
OptionalMinMarketCapKrw = Annotated[
    int | None,
    Field(description="시가총액 하한 필터(원). 0=끔. 미지정 시 배포값(라이브 3조)", ge=0),
]
OptionalLeadersMarketTp = Annotated[
    Literal["000", "001", "101"] | None,
    Field(description="리더보드 시장 범위. 000=전체, 001=KOSPI, 101=KOSDAQ. 미지정 시 배포값"),
]
OptionalDayChangeMin = Annotated[
    float | None,
    Field(description="당일 등락률 하한(%). 미지정 시 배포값"),
]
OptionalDayChangeMax = Annotated[
    float | None,
    Field(description="당일 등락률 상한(%). 미지정 시 배포값"),
]
OptionalAutoBuyMinScore = Annotated[
    int | None,
    Field(description="자동매수 허용 최소 점수. 미지정 시 배포값(라이브 8)", ge=0, le=30),
]
OptionalStopLossPct = Annotated[
    float | None,
    Field(
        description=(
            "손절 임계(%). holding_actions 계산 전용 — 실거래 Tier1 손절은 "
            "watcher가 별도 경로로 실행한다. 미지정 시 배포값"
        )
    ),
]
OptionalHardTakeProfitPct = Annotated[
    float | None,
    Field(description="익절 임계(%). holding_actions 계산 전용. 미지정 시 배포값"),
]
ConfirmLiveBackgroundTrading = Annotated[
    bool,
    Field(description="live 환경에서 background 주문 실행을 허용하려면 true"),
]


class KiwoomMCPServer:
    """MCP server that provides Kiwoom OpenAPI functionality."""

    def __init__(self):
        self.mcp = FastMCP("kiwoom-mcp")
        self._settings = get_settings()
        self._client = KiwoomClient(self._settings)
        self._trade_engine = BackgroundTradeEngine(self._settings)
        self._setup_resources()
        self._setup_dashboard_routes()
        self._setup_tools()

    def _setup_resources(self) -> None:
        """Setup MCP resources for configuration and status."""

    def _require_direct_order_permission(self) -> None:
        """Keep the live MCP process read-only unless the operator opts in."""

        if not self._settings.use_mock and not self._settings.allow_direct_live_orders:
            raise ValueError(
                "Direct live orders are disabled: use the watcher risk-managed path. "
                "Manual operation requires KIWOOM_ALLOW_DIRECT_LIVE_ORDERS=true "
                "and an isolated, authenticated MCP endpoint."
            )

    def _tool_when(self, listed: bool):
        """`@self.mcp.tool()` that registers only when ``listed`` holds.

        Deciding before registration rather than removing afterwards: the
        image resolves fastmcp unpinned (4.x in production) while tests run
        the locked 2.x, and `remove_tool` exists only in the latter — a
        2026-09-27 deploy crashed on it. `tool()` is common to both.
        """

        def decorate(fn):
            return self.mcp.tool()(fn) if listed else fn

        return decorate

    # Code defaults, used only when the watcher cannot be read. They are the
    # historical momentum settings and deliberately NOT the live ones — see
    # src/services/live_config.py for why keeping them honest matters more
    # than keeping them current.
    _STRATEGY_CODE_DEFAULTS: dict[str, Any] = {
        "leaders_limit": 10,
        "candidate_limit": 5,
        "max_positions": 3,
        "max_new_positions": 1,
        "position_budget_pct": 10,
        "entry_mode": "momentum",
        "ma_period": 20,
        "universe_mode": "leaders",
        "min_market_cap_krw": 0,
        "leaders_market_tp": "000",
        "day_change_min": 1.0,
        "day_change_max": 29.5,
        "auto_buy_min_score": 14,
        "stop_loss_pct": -3.0,
        "hard_take_profit_pct": 8.0,
    }

    async def _resolve_strategy_params(
        self, **explicit: Any
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Fill unset strategy arguments from the deployed watcher."""

        live = await asyncio.to_thread(live_config.fetch_live_config)
        return live_config.merge_defaults(
            explicit, live, self._STRATEGY_CODE_DEFAULTS
        )

    def _setup_dashboard_routes(self) -> None:
        """Register dashboard HTTP routes on the MCP server."""

        @self.mcp.custom_route("/", methods=["GET"])
        async def dashboard_page(request: Request) -> HTMLResponse:
            return HTMLResponse(
                _render_dashboard_page(
                    {
                        "start_date": _default_start_date(),
                        "end_date": _today_ymd(),
                    }
                )
            )

        @self.mcp.custom_route("/favicon.ico", methods=["GET"])
        async def favicon(request: Request) -> Response:
            return Response(status_code=204)

        @self.mcp.custom_route("/api/dashboard", methods=["GET"])
        async def dashboard_api(request: Request) -> JSONResponse:
            start_date = request.query_params.get("start_date", _default_start_date())
            end_date = request.query_params.get("end_date", _today_ymd())

            try:
                start_date = _validate_ymd(start_date, "start_date")
                end_date = _validate_ymd(end_date, "end_date")
            except ValueError as exc:
                return JSONResponse({"success": False, "error": str(exc)}, status_code=400)

            payload = await build_dashboard_snapshot(
                self._client,
                self._settings,
                start_date,
                end_date,
            )
            return JSONResponse(payload)

        @self.mcp.custom_route("/api/agent_overview", methods=["GET"])
        async def agent_overview_api(_: Request) -> JSONResponse:
            try:
                payload = await build_agent_overview()
                return JSONResponse(payload)
            except Exception as exc:
                return JSONResponse(
                    {"success": False, "error": f"agent_overview build 실패: {exc}"},
                    status_code=500,
                )

        # Separate from /api/agent_overview because the Multica comment fan-out
        # costs seconds; the overview above must stay fast enough to paint the
        # live status card immediately.
        @self.mcp.custom_route("/api/agent_timeline", methods=["GET"])
        async def agent_timeline_api(request: Request) -> JSONResponse:
            date = request.query_params.get("date")
            # ISO YYYY-MM-DD, not Kiwoom's YYYYMMDD — this date keys Multica
            # issue titles and comes straight from an <input type="date">.
            if date:
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    return JSONResponse(
                        {"success": False, "error": "date must be YYYY-MM-DD"},
                        status_code=400,
                    )
            try:
                limit = int(request.query_params.get("limit", "60"))
            except ValueError:
                limit = 60
            try:
                payload = await build_agent_timeline(date=date, limit=limit)
                return JSONResponse(payload)
            except Exception as exc:
                return JSONResponse(
                    {"success": False, "error": f"agent_timeline build 실패: {exc}"},
                    status_code=500,
                )

    def _setup_tools(self) -> None:
        """Setup MCP tools for Kiwoom OpenAPI operations."""

        # A live process without the direct-order opt-in refuses orders at call
        # time anyway. Listing those tools still cost something: the multica
        # agents read this list, and the legacy background engine's status — a
        # momentum dry-run inside this pod, not the watcher — reports
        # `execute_orders=false`. The risk manager and the PM took that for the
        # live system's state (2026-09-15, 09-16), the misdiagnosis the 09-15
        # wrap wrote down. Opted-in and mock processes still list them, and the
        # call-time guard below still checks.
        operator_tool = self._tool_when(
            self._settings.use_mock or self._settings.allow_direct_live_orders
        )
        mock_tool = self._tool_when(self._settings.use_mock)

        @self.mcp.tool()
        async def get_daily_realized_profit_by_stock(
            start_date: DateYmd,
            stock_code: Annotated[
                str | None,
                Field(
                    description="호환성용 종목코드. 현재 REST API는 start_date 기준으로 조회하며 이 값이 실질적으로 사용되지 않을 수 있음",
                    pattern=r"^\d{6}$",
                ),
            ] = None,
        ) -> dict[str, Any]:
            """
            API `ka10072` 일자별종목별실현손익요청_일자.

            특정 시작일 이후의 실현손익 내역을 조회합니다.
            현재 Kiwoom REST 응답은 `start_date` 기준 조회가 핵심이며, `stock_code`는 기존 인터페이스 호환용입니다.

            Use this tool when:
            - 계좌의 일자별/종목별 실현손익이 있는지 확인하고 싶을 때
            - 결과가 0건이어도 정상 응답인지 구분하고 싶을 때
            """
            return await account.get_daily_realized_profit_by_stock(
                self._client, stock_code or "", start_date
            )

        @self.mcp.tool()
        async def get_account_evaluation(
            qry_tp: Annotated[
                Literal["0", "1"],
                Field(description="상장폐지조회구분. 0=전체, 1=상장폐지종목 제외"),
            ] = "0",
            dmst_stex_tp: Annotated[
                Literal["KRX", "NXT"],
                Field(description="국내거래소구분. 일반적으로 KRX 사용"),
            ] = "KRX",
        ) -> dict[str, Any]:
            """
            API `kt00004` 계좌평가현황요청.

            보유 종목 평가금액, 손익, 예수금 추정자산 등을 조회합니다.
            기본값은 대부분의 경우 그대로 사용하면 됩니다.
            """
            return await account.get_account_evaluation(
                self._client, qry_tp, dmst_stex_tp
            )

        @self.mcp.tool()
        async def get_account_current_status(
        ) -> dict[str, Any]:
            """
            API `kt00017` 계좌별당일현황요청.

            추가 인자 없이 당일 계좌 현황을 조회합니다.
            D+2 추정예수금, 일반주식평가금액, 수수료/세금 등의 스냅샷이 필요할 때 사용합니다.
            """
            return await account.get_account_current_status(
                self._client
            )

        @self.mcp.tool()
        async def get_daily_account_profit_detail(
            fr_dt: DateYmd,
            to_dt: DateYmd,
        ) -> dict[str, Any]:
            """
            API `kt00016` 일별계좌수익률상세현황요청.

            기간별 계좌 수익률과 예수금/평가금액 변화를 조회합니다.
            `fr_dt`, `to_dt`는 반드시 YYYYMMDD 형식이어야 합니다.
            """
            return await account.get_daily_account_profit_detail(
                self._client, fr_dt, to_dt
            )

        @self.mcp.tool()
        async def get_orderable_amount(
            stk_cd: StockCode,
            trde_tp: Annotated[
                Literal["1", "2"],
                Field(description="매매구분. 1=매도, 2=매수"),
            ],
            uv: NumericText,
            trde_qty: OptionalNumericText = None,
            exp_buy_unp: OptionalNumericText = None,
        ) -> dict[str, Any]:
            """
            API `kt00010` 주문인출가능금액요청.

            특정 종목을 기준으로 주문 가능 금액/수량을 조회합니다.

            Important:
            - `uv`는 주문 단가를 숫자 문자열로 넣어야 합니다. 예: `"70000"`
            - 장이 닫혀 있으면 `success=false`와 함께 업무 오류 메시지가 반환될 수 있습니다
            """
            return await account.get_orderable_amount(
                self._client,
                stk_cd,
                trde_tp,
                uv,
                trde_qty=trde_qty or "",
                exp_buy_unp=exp_buy_unp or "",
            )

        @self.mcp.tool()
        async def get_execution_info(
            qry_tp: Annotated[
                Literal["0", "1"],
                Field(description="조회구분. 0=전체, 1=종목"),
            ],
            sell_tp: Annotated[
                Literal["0", "1", "2"],
                Field(description="매도수구분. 0=전체, 1=매도, 2=매수"),
            ],
            stex_tp: Annotated[
                Literal["0", "1", "2"],
                Field(description="거래소구분. 0=통합, 1=KRX, 2=NXT"),
            ],
            stk_cd: OptionalStockCode = None,
            ord_no: OptionalNumericText = None,
        ) -> dict[str, Any]:
            """
            API `ka10076` 체결요청.

            체결이 완료된 주문 내역만 조회합니다.

            Use this tool when:
            - 실제 체결된 주문 목록이 필요할 때
            - 미체결/접수 상태가 아니라 체결 결과만 보고 싶을 때

            If you need:
            - 주문/접수/확인/체결 현황 전체 스냅샷: use `get_order_execution_status`
            """
            return await account.get_execution_info(
                self._client,
                qry_tp,
                sell_tp,
                stex_tp,
                stk_cd or "",
                ord_no or "",
            )

        @self.mcp.tool()
        async def get_order_execution_status(
            stk_bond_tp: Annotated[
                Literal["0", "1", "2"],
                Field(description="주식채권구분. 0=전체, 1=주식, 2=채권"),
            ],
            mrkt_tp: Annotated[
                Literal["0", "1", "2", "3", "4"],
                Field(description="시장구분. 0=전체, 1=코스피, 2=코스닥, 3=OTCBB, 4=ECN"),
            ],
            sell_tp: Annotated[
                Literal["0", "1", "2"],
                Field(description="매도수구분. 0=전체, 1=매도, 2=매수"),
            ],
            qry_tp: Annotated[
                Literal["0", "1"],
                Field(description="조회구분. 0=전체, 1=체결"),
            ],
            dmst_stex_tp: Annotated[
                Literal["%", "KRX", "NXT", "SOR"],
                Field(description="국내거래소구분. %=전체, KRX=한국거래소, NXT=넥스트트레이드, SOR=최선집행"),
            ],
            stk_cd: OptionalStockCode = None,
            fr_ord_no: OptionalNumericText = None,
        ) -> dict[str, Any]:
            """
            API `kt00009` 계좌별주문체결현황요청.

            주문/접수/확인/체결 상태를 함께 보는 계좌별 주문 현황 조회입니다.
            `get_execution_info`와 다르게 체결 완료 내역만 보는 도구가 아닙니다.

            Use this tool when:
            - 주문 현황 전체 스냅샷이 필요할 때
            - 특정 주문번호 이후의 진행 상태를 이어서 조회할 때
            """
            return await account.get_order_execution_status(
                self._client,
                stk_bond_tp,
                mrkt_tp,
                sell_tp,
                qry_tp,
                dmst_stex_tp,
                stk_cd or "",
                fr_ord_no or "",
            )

        @self.mcp.tool()
        async def get_unexecuted_orders(
            all_stk_tp: Annotated[
                Literal["0", "1"],
                Field(description="전체종목구분. 0=전체, 1=종목"),
            ],
            trde_tp: Annotated[
                Literal["0", "1", "2"],
                Field(description="매매구분. 0=전체, 1=매도, 2=매수"),
            ],
            stex_tp: Annotated[
                Literal["0", "1", "2"],
                Field(description="거래소구분. 0=통합, 1=KRX, 2=NXT"),
            ],
            stk_cd: OptionalStockCode = None,
        ) -> dict[str, Any]:
            """
            API `ka10075` 미체결요청.

            현재 미체결 주문만 조회합니다.

            Important:
            - `all_stk_tp`는 실제 서버가 요구하는 필수값입니다
            - 결과가 0건이면 미체결 주문이 없다는 뜻일 수 있습니다
            """
            return await account.get_unexecuted_orders(
                self._client, all_stk_tp, trde_tp, stex_tp, stk_cd or ""
            )

        @self.mcp.tool()
        async def get_market_snapshot(
            watchlist: StrategyWatchlist = None,
            leaders_limit: LeadersLimit = 10,
        ) -> dict[str, Any]:
            """
            시장 데이터 집계 도구.

            KOSPI/KOSDAQ 지수, 업종 개요, 상승률/거래량/거래대금 상위, 감시 종목 상세 시세를 한 번에 조회합니다.

            Use this tool when:
            - automation 한 번의 실행에서 시장 전반 분위기를 빠르게 파악하고 싶을 때
            - 개별 종목보다 먼저 지수/업종/랭킹 데이터를 보고 싶을 때
            """
            return await market.get_market_snapshot(
                self._client,
                watchlist=watchlist,
                leaders_limit=leaders_limit,
            )

        # The next three are named after what the agents guessed when no tool
        # fit (`get_stock_quote`, `get_stock_daily_bars` among 13 attempts on
        # 2026-09-17), so the first name that comes to mind now works.

        @self.mcp.tool()
        async def get_stock_quote(stock_code: StockCode) -> dict[str, Any]:
            """
            API `ka10007` 한 종목의 현재가·5단계 호가·상하한가·시가총액 요약.

            Use this tool when:
            - 보유 종목이나 후보 한 종목의 지금 가격, 최우선 호가, 스프레드, 잔량 비율을 볼 때
            - 상한가/하한가까지 남은 거리나 시가총액이 필요할 때

            Notes:
            - 호출 1회. `orderbook_ratio`(매수잔량/매도잔량)는 watcher 채점과 같은 정의다
            - `volume_vs_prev_day_pct`는 전일 하루 전체 대비라 장 초반엔 낮게 나온다
            - 일봉·MA20·거래량 배수는 `get_stock_daily_bars`
            """
            result = await market.get_stock_quote(self._client, stock_code=stock_code)
            if not result.get("success"):
                return {
                    "success": False,
                    "api_id": "ka10007",
                    "stock_code": stock_code,
                    "error": result.get("error") or result.get("message"),
                }
            return {
                "success": True,
                "api_id": "ka10007",
                **stock_tools.summarize_quote(result.get("quote") or {}, stock_code=stock_code),
            }

        @self.mcp.tool()
        async def get_stock_daily_bars(
            stock_code: StockCode,
            limit: Annotated[
                int,
                Field(
                    description="최근 일봉 개수. MA20과 20일 평균 거래량에 21개 이상이 필요하다",
                    ge=21,
                    le=30,
                ),
            ] = 30,
        ) -> dict[str, Any]:
            """
            API `ka10005` 한 종목의 최근 일봉과 추세 판단 지표.

            `indicators`:
            - `ma`, `ma_dip_pct`: MA20과 최신 종가의 이격. **양수 = MA 아래로 그만큼 눌림.**
              watcher가 후보를 채점할 때 쓰는 것과 같은 함수·같은 부호다
            - `volume_ratio_20d`: 최신 봉 거래량 / 직전 20거래일 평균
            - `prior_20d_low`, `new_20d_low`: 직전 20거래일 최저가와 저점 갱신 여부
            장중에는 최신 봉이 오늘이라 종가가 곧 현재가이고 거래량은 누적 부분값이다.

            Use this tool when:
            - 보유 종목이 falling knife(이평 5%+ 하회, 저점 갱신, 거래 급감)인지 판단할 때
            - 후보의 눌림 깊이와 거래량 배수를 직접 확인할 때
            """
            result = await market.get_stock_daily_bars(
                self._client, stock_code=stock_code, limit=limit
            )
            if not result.get("success"):
                return {
                    "success": False,
                    "api_id": "ka10005",
                    "stock_code": stock_code,
                    "error": result.get("error") or result.get("message"),
                }
            return {
                "success": True,
                "api_id": "ka10005",
                **stock_tools.summarize_daily_bars(
                    result.get("daily_bars") or [], stock_code=stock_code
                ),
            }

        @self.mcp.tool()
        async def get_order_ledger(
            limit: Annotated[
                int, Field(description="최근 intent 개수", ge=1, le=200)
            ] = 50,
            trading_day: Annotated[
                str | None,
                Field(
                    description="거래일 YYYY-MM-DD. 지정하면 그날 intent만 (미종결은 항상 포함)",
                    pattern=r"^\d{4}-\d{2}-\d{2}$",
                ),
            ] = None,
        ) -> dict[str, Any]:
            """
            watcher 주문 intent 원장 (읽기 전용).

            watcher는 주문을 내기 전에 intent를 기록하고(INTENDED → SUBMITTED →
            FILLED/CANCELLED/REJECTED …) 브로커 조회로 대사한다. 응답:
            `unresolved`(신규 매수를 막고 있는 미종결), `recent`(최신순 intent,
            `decision_scope`=어떤 ACTION/트리거가 낸 주문인지), `recent_audit`,
            `storage_safety`.

            Use this tool when:
            - agent ACTION이 실제 주문으로 이어졌는지 확인할 때 (`decision_scope`, `state`, `order_no`)
            - 미종결 intent 때문에 매수가 막혔는지 볼 때
            - 장애 RCA에 주문 타임라인이 필요할 때 — watcher pod에 exec하지 말고 이걸 쓴다
            """
            return await fetch_watcher_ledger(limit=limit, trading_day=trading_day)

        @self.mcp.tool()
        async def plan_intraday_momentum_strategy(
            watchlist: StrategyWatchlist = None,
            leaders_limit: OptionalLeadersLimit = None,
            candidate_limit: OptionalCandidateLimit = None,
            max_positions: OptionalMaxPositions = None,
            max_new_positions: OptionalMaxNewPositions = None,
            position_budget_pct: OptionalPositionBudgetPercent = None,
            entry_mode: OptionalEntryMode = None,
            ma_period: OptionalMaPeriod = None,
            universe_mode: OptionalUniverseMode = None,
            min_market_cap_krw: OptionalMinMarketCapKrw = None,
            leaders_market_tp: OptionalLeadersMarketTp = None,
            day_change_min: OptionalDayChangeMin = None,
            day_change_max: OptionalDayChangeMax = None,
            auto_buy_min_score: OptionalAutoBuyMinScore = None,
            stop_loss_pct: OptionalStopLossPct = None,
            hard_take_profit_pct: OptionalHardTakeProfitPct = None,
        ) -> dict[str, Any]:
            """
            규칙 기반 장중 전략 계획 도구. 주문은 보내지 않습니다.

            **인자를 비워두면 배포된 실거래 watcher와 같은 조건으로 조회합니다**
            (`/state`의 실효 config에서 해석). 따라서 "지금 라이브가 보는 후보"를
            알고 싶으면 아무것도 넘기지 마세요. 명시한 인자는 그대로 우선합니다.

            응답의 `config_source`가 어떤 값이 어디서 왔는지(caller / live /
            default) 알려줍니다. watcher를 못 읽으면 코드 기본값으로 떨어지는데,
            그건 momentum·리더보드·시총 필터 없음이라 **라이브가 절대 사지 않는
            소형 급등주**가 나옵니다 — 그때는 `config_source.source`가
            `code-defaults`이므로 후보로 쓰지 마세요.

            손절/익절 인자는 이 도구의 holding_actions 계산에만 쓰이고, 실거래
            Tier1 손절/익절은 watcher가 별도 코드 경로로 독립 실행합니다.

            Strategy outline:
            - KOSPI/KOSDAQ breadth와 지수 수익률로 risk-on / neutral / risk-off 판정
            - entry_mode=momentum: 당일 상승률 밴드 내 유동성 높은 상승 종목 후보
            - entry_mode=below_ma: 이동평균(ma_period) 대비 얕은 눌림목 후보(평균회귀)
            - 손절(stop_loss_pct)/익절(hard_take_profit_pct)/약세장 디리스킹 규칙 적용
            """
            resolved, source = await self._resolve_strategy_params(
                leaders_limit=leaders_limit,
                candidate_limit=candidate_limit,
                max_positions=max_positions,
                max_new_positions=max_new_positions,
                position_budget_pct=position_budget_pct,
                entry_mode=entry_mode,
                ma_period=ma_period,
                universe_mode=universe_mode,
                min_market_cap_krw=min_market_cap_krw,
                leaders_market_tp=leaders_market_tp,
                day_change_min=day_change_min,
                day_change_max=day_change_max,
                auto_buy_min_score=auto_buy_min_score,
                stop_loss_pct=stop_loss_pct,
                hard_take_profit_pct=hard_take_profit_pct,
            )
            result = await strategy.plan_intraday_momentum_strategy(
                self._client,
                self._settings,
                watchlist=watchlist,
                **resolved,
            )
            if isinstance(result, dict):
                result["config_source"] = source
            return result

        @mock_tool
        async def run_mock_intraday_momentum_strategy(
            confirm_mock_strategy_execution: ConfirmMockStrategyExecution,
            watchlist: StrategyWatchlist = None,
            leaders_limit: OptionalLeadersLimit = None,
            candidate_limit: OptionalCandidateLimit = None,
            max_positions: OptionalMaxPositions = None,
            max_new_positions: OptionalMaxNewPositions = None,
            position_budget_pct: OptionalPositionBudgetPercent = None,
            entry_mode: OptionalEntryMode = None,
            ma_period: OptionalMaPeriod = None,
            universe_mode: OptionalUniverseMode = None,
            min_market_cap_krw: OptionalMinMarketCapKrw = None,
            leaders_market_tp: OptionalLeadersMarketTp = None,
            day_change_min: OptionalDayChangeMin = None,
            day_change_max: OptionalDayChangeMax = None,
            auto_buy_min_score: OptionalAutoBuyMinScore = None,
            stop_loss_pct: OptionalStopLossPct = None,
            hard_take_profit_pct: OptionalHardTakeProfitPct = None,
        ) -> dict[str, Any]:
            """
            MOCK ONLY: 규칙 기반 장중 전략 실행 도구.

            Important:
            - `KIWOOM_USE_MOCK=true`일 때만 주문을 전송합니다
            - 기본적으로 손절/익절/유동성 필터가 내장된 보수적 전략입니다
            - 수익을 보장하지 않으며, mock 검증용으로 사용해야 합니다
            - 인자를 비워두면 배포된 watcher의 실효 설정으로 조회합니다
              (`plan_intraday_momentum_strategy`와 동일, `config_source` 참고)
            """
            resolved, source = await self._resolve_strategy_params(
                leaders_limit=leaders_limit,
                candidate_limit=candidate_limit,
                max_positions=max_positions,
                max_new_positions=max_new_positions,
                position_budget_pct=position_budget_pct,
                entry_mode=entry_mode,
                ma_period=ma_period,
                universe_mode=universe_mode,
                min_market_cap_krw=min_market_cap_krw,
                leaders_market_tp=leaders_market_tp,
                day_change_min=day_change_min,
                day_change_max=day_change_max,
                auto_buy_min_score=auto_buy_min_score,
                stop_loss_pct=stop_loss_pct,
                hard_take_profit_pct=hard_take_profit_pct,
            )
            result = await strategy.plan_intraday_momentum_strategy(
                self._client,
                self._settings,
                watchlist=watchlist,
                execute_orders=True,
                confirm_mock_orders=confirm_mock_strategy_execution,
                **resolved,
            )
            if isinstance(result, dict):
                result["config_source"] = source
            return result

        @operator_tool
        async def get_background_trade_engine_status() -> dict[str, Any]:
            """
            Background trade engine 상태 조회 도구.

            현재 엔진 실행 여부, pause 상태, 마지막 전략 사이클 결과 요약, 현재 설정값을 반환합니다.
            """
            return self._trade_engine.status()

        @operator_tool
        async def update_background_trade_engine_config(
            watchlist: StrategyWatchlist = None,
            leaders_limit: OptionalLeadersLimit = None,
            candidate_limit: OptionalCandidateLimit = None,
            max_positions: OptionalMaxPositions = None,
            max_new_positions: OptionalMaxNewPositions = None,
            position_budget_pct: OptionalPositionBudgetPercent = None,
            cycle_interval_seconds: StrategyCycleInterval | None = None,
            off_hours_interval_seconds: StrategyOffHoursInterval | None = None,
            execute_orders: bool | None = None,
        ) -> dict[str, Any]:
            """
            Background trade engine 전략 설정 수정 도구.

            Use this tool when:
            - automation이 watchlist, 포지션 수, 실행 주기를 바꿔야 할 때
            - background 엔진이 다음 사이클부터 새 전략 파라미터를 사용해야 할 때

            Notes:
            - `watchlist=None`이면 기존 값을 유지합니다
            - `watchlist=[]`이면 수동 watchlist를 비웁니다
            """
            return await self._trade_engine.update_config(
                watchlist=watchlist,
                leaders_limit=leaders_limit,
                candidate_limit=candidate_limit,
                max_positions=max_positions,
                max_new_positions=max_new_positions,
                position_budget_pct=position_budget_pct,
                cycle_interval_seconds=cycle_interval_seconds,
                off_hours_interval_seconds=off_hours_interval_seconds,
                execute_orders=execute_orders,
            )

        @operator_tool
        async def start_background_trade_engine(
            execute_orders: bool | None = None,
            confirm_live_background_trading: ConfirmLiveBackgroundTrading = False,
        ) -> dict[str, Any]:
            """
            Background trade engine 시작 도구.

            엔진이 장중에 계속 전략 사이클을 반복 실행합니다.

            Important:
            - `execute_orders=true`면 전략이 실제 주문까지 전송합니다
            - live 환경에서 `execute_orders=true`를 쓰려면 `confirm_live_background_trading=true`가 필요합니다
            - mock 환경에서는 same-process background mock 주문 실행이 가능합니다
            """
            return await self._trade_engine.start(
                execute_orders=execute_orders,
                confirm_live_execution=confirm_live_background_trading,
            )

        @operator_tool
        async def pause_background_trade_engine() -> dict[str, Any]:
            """
            Background trade engine 일시정지 도구.

            프로세스는 유지하지만 신규 전략 사이클과 주문 실행을 멈춥니다.
            """
            return await self._trade_engine.pause()

        @operator_tool
        async def resume_background_trade_engine() -> dict[str, Any]:
            """
            Background trade engine 재개 도구.

            일시정지된 엔진을 다시 장중 반복 실행 상태로 되돌립니다.
            """
            return await self._trade_engine.resume()

        @operator_tool
        async def stop_background_trade_engine() -> dict[str, Any]:
            """
            Background trade engine 중지 도구.

            엔진 task를 종료하고 다음 시작 요청 전까지 전략 사이클을 돌리지 않습니다.
            """
            return await self._trade_engine.stop()

        @operator_tool
        async def place_stock_buy_order(
            confirm_live_order: ConfirmLiveOrder,
            stk_cd: StockCode,
            ord_qty: NumericText,
            order_type_code: OrderTypeCode,
            dmst_stex_tp: Annotated[
                Literal["KRX", "NXT"],
                Field(description="국내거래소구분. 기본값은 KRX"),
            ] = "KRX",
            ord_uv: OptionalNumericText = None,
            cond_uv: OptionalNumericText = None,
        ) -> dict[str, Any]:
            """
            ORDER SUBMISSION: API `kt10000` 주식 매수주문.

            현재 설정된 Kiwoom 환경으로 매수 주문을 전송합니다.

            Important:
            - `KIWOOM_USE_MOCK=true`면 모의투자 환경, 아니면 실거래 환경으로 전송됩니다
            - `confirm_live_order`는 반드시 `true`여야 합니다
            - `dmst_stex_tp`는 기본값 `KRX`를 사용합니다
            - 시장가 주문이면 `order_type_code="3"`를 사용하고 `ord_uv`는 비워둘 수 있습니다
            - 지정가 주문이면 `order_type_code="0"`와 `ord_uv`를 함께 넣으세요
            """
            self._require_direct_order_permission()
            return await order.place_stock_buy_order(
                self._client,
                stk_cd=stk_cd,
                ord_qty=ord_qty,
                order_type_code=order_type_code,
                dmst_stex_tp=dmst_stex_tp,
                ord_uv=ord_uv or "",
                cond_uv=cond_uv or "",
            )

        @operator_tool
        async def place_stock_sell_order(
            confirm_live_order: ConfirmLiveOrder,
            stk_cd: StockCode,
            ord_qty: NumericText,
            order_type_code: OrderTypeCode,
            dmst_stex_tp: Annotated[
                Literal["KRX", "NXT"],
                Field(description="국내거래소구분. 기본값은 KRX"),
            ] = "KRX",
            ord_uv: OptionalNumericText = None,
            cond_uv: OptionalNumericText = None,
        ) -> dict[str, Any]:
            """
            ORDER SUBMISSION: API `kt10001` 주식 매도주문.

            현재 설정된 Kiwoom 환경으로 매도 주문을 전송합니다.

            Important:
            - `KIWOOM_USE_MOCK=true`면 모의투자 환경, 아니면 실거래 환경으로 전송됩니다
            - `confirm_live_order`는 반드시 `true`여야 합니다
            - `dmst_stex_tp`는 기본값 `KRX`를 사용합니다
            - 시장가 주문이면 `order_type_code="3"`를 사용하고 `ord_uv`는 비워둘 수 있습니다
            - 지정가 주문이면 `order_type_code="0"`와 `ord_uv`를 함께 넣으세요
            """
            self._require_direct_order_permission()
            return await order.place_stock_sell_order(
                self._client,
                stk_cd=stk_cd,
                ord_qty=ord_qty,
                order_type_code=order_type_code,
                dmst_stex_tp=dmst_stex_tp,
                ord_uv=ord_uv or "",
                cond_uv=cond_uv or "",
            )

        @operator_tool
        async def modify_stock_order(
            confirm_live_order: ConfirmLiveOrder,
            orig_ord_no: OrderNumber,
            stk_cd: StockCode,
            mdfy_qty: NumericText,
            mdfy_uv: NumericText,
            dmst_stex_tp: Annotated[
                Literal["KRX", "NXT"],
                Field(description="국내거래소구분. 기본값은 KRX"),
            ] = "KRX",
            mdfy_cond_uv: OptionalNumericText = None,
        ) -> dict[str, Any]:
            """
            ORDER SUBMISSION: API `kt10002` 주식 정정주문.

            현재 설정된 Kiwoom 환경의 기존 주문을 정정합니다.

            Important:
            - `KIWOOM_USE_MOCK=true`면 모의투자 환경, 아니면 실거래 환경으로 전송됩니다
            - `confirm_live_order`는 반드시 `true`여야 합니다
            """
            self._require_direct_order_permission()
            return await order.modify_stock_order(
                self._client,
                orig_ord_no=orig_ord_no,
                stk_cd=stk_cd,
                mdfy_qty=mdfy_qty,
                mdfy_uv=mdfy_uv,
                dmst_stex_tp=dmst_stex_tp,
                mdfy_cond_uv=mdfy_cond_uv or "",
            )

        @operator_tool
        async def cancel_stock_order(
            confirm_live_order: ConfirmLiveOrder,
            orig_ord_no: OrderNumber,
            stk_cd: StockCode,
            cncl_qty: NumericText,
            dmst_stex_tp: Annotated[
                Literal["KRX", "NXT"],
                Field(description="국내거래소구분. 기본값은 KRX"),
            ] = "KRX",
        ) -> dict[str, Any]:
            """
            ORDER SUBMISSION: API `kt10003` 주식 취소주문.

            현재 설정된 Kiwoom 환경의 기존 주문을 취소합니다.

            Important:
            - `KIWOOM_USE_MOCK=true`면 모의투자 환경, 아니면 실거래 환경으로 전송됩니다
            - `confirm_live_order`는 반드시 `true`여야 합니다
            - `dmst_stex_tp`는 기본값 `KRX`를 사용합니다
            - `cncl_qty="0"`이면 잔량 전체 취소입니다
            """
            self._require_direct_order_permission()
            return await order.cancel_stock_order(
                self._client,
                orig_ord_no=orig_ord_no,
                stk_cd=stk_cd,
                cncl_qty=cncl_qty,
                dmst_stex_tp=dmst_stex_tp,
            )


    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self._trade_engine.close()
        await self._client.close()

    async def start_background_engine(
        self,
        *,
        execute_orders: bool | None = None,
        confirm_live_execution: bool = False,
    ) -> dict[str, Any]:
        """Start the background engine from non-tool entrypoints."""

        return await self._trade_engine.start(
            execute_orders=execute_orders,
            confirm_live_execution=confirm_live_execution,
        )

    def background_engine_status(self) -> dict[str, Any]:
        """Return the current background engine status."""

        return self._trade_engine.status()

    def run(self) -> None:
        """Run the MCP server."""
        self.mcp.run()


# Create global server instance
mcp_server = KiwoomMCPServer()


def create_mcp_server() -> KiwoomMCPServer:
    """Create and return a new MCP server instance."""
    return KiwoomMCPServer()


__all__ = ["KiwoomMCPServer", "mcp_server", "create_mcp_server"]
