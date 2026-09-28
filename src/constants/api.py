"""Hard-coded Kiwoom OpenAPI constant definitions."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, NamedTuple, Optional


class APIInfo(NamedTuple):
    """Metadata for a Kiwoom OpenAPI endpoint."""

    api_id: str
    name: str
    category: str
    subcategory: str
    url: str


class APICollection(dict):
    """Dictionary that supports attribute access with legacy aliases."""

    def __init__(self, entries: Dict[str, APIInfo], aliases: Optional[Dict[str, str]] = None):
        super().__init__(entries)
        self._aliases: Dict[str, str] = {}
        if aliases:
            for alias, api_id in aliases.items():
                if api_id in entries:
                    self._aliases[alias.upper()] = api_id

        for api_id, info in entries.items():
            attr = api_id.lower()
            if attr.isidentifier():
                self.__dict__.setdefault(attr, info)

        for alias_key, api_id in self._aliases.items():
            attr = alias_key.lower()
            if attr.isidentifier():
                self.__dict__.setdefault(attr, entries[api_id])

    def _resolve_key(self, key: str) -> str:
        if isinstance(key, str):
            alias_key = key.upper()
            if alias_key in self._aliases:
                return self._aliases[alias_key]
        return key

    def __getitem__(self, key: str) -> APIInfo:
        return super().__getitem__(self._resolve_key(key))

    def __getattr__(self, item: str) -> APIInfo:
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def get(self, key: str, default: Optional[APIInfo] = None) -> Optional[APIInfo]:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, APIInfo]:
        return dict(self)


ALL_API_DATA: Dict[str, APIInfo] = {
    "00": APIInfo(api_id="00", name="주문체결", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "04": APIInfo(api_id="04", name="잔고", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0A": APIInfo(api_id="0A", name="주식기세", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0B": APIInfo(api_id="0B", name="주식체결", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0C": APIInfo(api_id="0C", name="주식우선호가", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0D": APIInfo(api_id="0D", name="주식호가잔량", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0E": APIInfo(api_id="0E", name="주식시간외호가", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0F": APIInfo(api_id="0F", name="주식당일거래원", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0G": APIInfo(api_id="0G", name="ETF NAV", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0H": APIInfo(api_id="0H", name="주식예상체결", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0I": APIInfo(api_id="0I", name="국제금환산가격", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0J": APIInfo(api_id="0J", name="업종지수", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0U": APIInfo(api_id="0U", name="업종등락", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0g": APIInfo(api_id="0g", name="주식종목정보", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0m": APIInfo(api_id="0m", name="ELW 이론가", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0s": APIInfo(api_id="0s", name="장시작시간", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0u": APIInfo(api_id="0u", name="ELW 지표", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "0w": APIInfo(api_id="0w", name="종목프로그램매매", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "1h": APIInfo(api_id="1h", name="VI발동/해제", category="국내주식", subcategory="실시간시세", url="/api/dostk/websocket"),
    "au10001": APIInfo(api_id="au10001", name="접근토큰 발급", category="OAuth 인증", subcategory="접근토큰발급", url="/oauth2/token"),
    "au10002": APIInfo(api_id="au10002", name="접근토큰폐기", category="OAuth 인증", subcategory="접근토큰폐기", url="/oauth2/revoke"),
    "ka00198": APIInfo(api_id="ka00198", name="실시간종목조회순위", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka01690": APIInfo(api_id="ka01690", name="일별잔고수익률", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10001": APIInfo(api_id="ka10001", name="주식기본정보요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10002": APIInfo(api_id="ka10002", name="주식거래원요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10003": APIInfo(api_id="ka10003", name="체결정보요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10004": APIInfo(api_id="ka10004", name="주식호가요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10005": APIInfo(api_id="ka10005", name="주식일주월시분요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10006": APIInfo(api_id="ka10006", name="주식시분요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10007": APIInfo(api_id="ka10007", name="시세표성정보요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10008": APIInfo(api_id="ka10008", name="주식외국인종목별매매동향", category="국내주식", subcategory="기관/외국인", url="/api/dostk/frgnistt"),
    "ka10009": APIInfo(api_id="ka10009", name="주식기관요청", category="국내주식", subcategory="기관/외국인", url="/api/dostk/frgnistt"),
    "ka10010": APIInfo(api_id="ka10010", name="업종프로그램요청", category="국내주식", subcategory="업종", url="/api/dostk/sect"),
    "ka10011": APIInfo(api_id="ka10011", name="신주인수권전체시세요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10013": APIInfo(api_id="ka10013", name="신용매매동향요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10014": APIInfo(api_id="ka10014", name="공매도추이요청", category="국내주식", subcategory="공매도", url="/api/dostk/shsa"),
    "ka10015": APIInfo(api_id="ka10015", name="일별거래상세요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10016": APIInfo(api_id="ka10016", name="신고저가요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10017": APIInfo(api_id="ka10017", name="상하한가요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10018": APIInfo(api_id="ka10018", name="고저가근접요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10019": APIInfo(api_id="ka10019", name="가격급등락요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10020": APIInfo(api_id="ka10020", name="호가잔량상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10021": APIInfo(api_id="ka10021", name="호가잔량급증요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10022": APIInfo(api_id="ka10022", name="잔량율급증요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10023": APIInfo(api_id="ka10023", name="거래량급증요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10024": APIInfo(api_id="ka10024", name="거래량갱신요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10025": APIInfo(api_id="ka10025", name="매물대집중요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10026": APIInfo(api_id="ka10026", name="고저PER요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10027": APIInfo(api_id="ka10027", name="전일대비등락률상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10028": APIInfo(api_id="ka10028", name="시가대비등락률요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10029": APIInfo(api_id="ka10029", name="예상체결등락률상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10030": APIInfo(api_id="ka10030", name="당일거래량상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10031": APIInfo(api_id="ka10031", name="전일거래량상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10032": APIInfo(api_id="ka10032", name="거래대금상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10033": APIInfo(api_id="ka10033", name="신용비율상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10034": APIInfo(api_id="ka10034", name="외인기간별매매상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10035": APIInfo(api_id="ka10035", name="외인연속순매매상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10036": APIInfo(api_id="ka10036", name="외인한도소진율증가상위", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10037": APIInfo(api_id="ka10037", name="외국계창구매매상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10038": APIInfo(api_id="ka10038", name="종목별증권사순위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10039": APIInfo(api_id="ka10039", name="증권사별매매상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10040": APIInfo(api_id="ka10040", name="당일주요거래원요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10042": APIInfo(api_id="ka10042", name="순매수거래원순위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10043": APIInfo(api_id="ka10043", name="거래원매물대분석요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10044": APIInfo(api_id="ka10044", name="일별기관매매종목요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10045": APIInfo(api_id="ka10045", name="종목별기관매매추이요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10046": APIInfo(api_id="ka10046", name="체결강도추이시간별요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10047": APIInfo(api_id="ka10047", name="체결강도추이일별요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10048": APIInfo(api_id="ka10048", name="ELW일별민감도지표요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka10050": APIInfo(api_id="ka10050", name="ELW민감도지표요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka10051": APIInfo(api_id="ka10051", name="업종별투자자순매수요청", category="국내주식", subcategory="업종", url="/api/dostk/sect"),
    "ka10052": APIInfo(api_id="ka10052", name="거래원순간거래량요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10053": APIInfo(api_id="ka10053", name="당일상위이탈원요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10054": APIInfo(api_id="ka10054", name="변동성완화장치발동종목요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10055": APIInfo(api_id="ka10055", name="당일전일체결량요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10058": APIInfo(api_id="ka10058", name="투자자별일별매매종목요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10059": APIInfo(api_id="ka10059", name="종목별투자자기관별요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10060": APIInfo(api_id="ka10060", name="종목별투자자기관별차트요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10061": APIInfo(api_id="ka10061", name="종목별투자자기관별합계요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10062": APIInfo(api_id="ka10062", name="동일순매매순위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10063": APIInfo(api_id="ka10063", name="장중투자자별매매요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10064": APIInfo(api_id="ka10064", name="장중투자자별매매차트요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10065": APIInfo(api_id="ka10065", name="장중투자자별매매상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10066": APIInfo(api_id="ka10066", name="장마감후투자자별매매요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10068": APIInfo(api_id="ka10068", name="대차거래추이요청", category="국내주식", subcategory="대차거래", url="/api/dostk/slb"),
    "ka10069": APIInfo(api_id="ka10069", name="대차거래상위10종목요청", category="국내주식", subcategory="대차거래", url="/api/dostk/slb"),
    "ka10072": APIInfo(api_id="ka10072", name="일자별종목별실현손익요청_일자", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10073": APIInfo(api_id="ka10073", name="일자별종목별실현손익요청_기간", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10074": APIInfo(api_id="ka10074", name="일자별실현손익요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10075": APIInfo(api_id="ka10075", name="미체결요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10076": APIInfo(api_id="ka10076", name="체결요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10077": APIInfo(api_id="ka10077", name="당일실현손익상세요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10078": APIInfo(api_id="ka10078", name="증권사별종목매매동향요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10079": APIInfo(api_id="ka10079", name="주식틱차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10080": APIInfo(api_id="ka10080", name="주식분봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10081": APIInfo(api_id="ka10081", name="주식일봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10082": APIInfo(api_id="ka10082", name="주식주봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10083": APIInfo(api_id="ka10083", name="주식월봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10084": APIInfo(api_id="ka10084", name="당일전일체결요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10085": APIInfo(api_id="ka10085", name="계좌수익률요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10086": APIInfo(api_id="ka10086", name="일별주가요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10087": APIInfo(api_id="ka10087", name="시간외단일가요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka10088": APIInfo(api_id="ka10088", name="미체결 분할주문 상세", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10094": APIInfo(api_id="ka10094", name="주식년봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka10095": APIInfo(api_id="ka10095", name="관심종목정보요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10098": APIInfo(api_id="ka10098", name="시간외단일가등락율순위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka10099": APIInfo(api_id="ka10099", name="종목정보 리스트", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10100": APIInfo(api_id="ka10100", name="종목정보 조회", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10101": APIInfo(api_id="ka10101", name="업종코드 리스트", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10102": APIInfo(api_id="ka10102", name="회원사 리스트", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka10131": APIInfo(api_id="ka10131", name="기관외국인연속매매현황요청", category="국내주식", subcategory="기관/외국인", url="/api/dostk/frgnistt"),
    "ka10170": APIInfo(api_id="ka10170", name="당일매매일지요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "ka10171": APIInfo(api_id="ka10171", name="조건검색 목록조회", category="국내주식", subcategory="조건검색", url="/api/dostk/websocket"),
    "ka10172": APIInfo(api_id="ka10172", name="조건검색 요청 일반", category="국내주식", subcategory="조건검색", url="/api/dostk/websocket"),
    "ka10173": APIInfo(api_id="ka10173", name="조건검색 요청 실시간", category="국내주식", subcategory="조건검색", url="/api/dostk/websocket"),
    "ka10174": APIInfo(api_id="ka10174", name="조건검색 실시간 해제", category="국내주식", subcategory="조건검색", url="/api/dostk/websocket"),
    "ka20001": APIInfo(api_id="ka20001", name="업종현재가요청", category="국내주식", subcategory="업종", url="/api/dostk/sect"),
    "ka20002": APIInfo(api_id="ka20002", name="업종별주가요청", category="국내주식", subcategory="업종", url="/api/dostk/sect"),
    "ka20003": APIInfo(api_id="ka20003", name="전업종지수요청", category="국내주식", subcategory="업종", url="/api/dostk/sect"),
    "ka20004": APIInfo(api_id="ka20004", name="업종틱차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka20005": APIInfo(api_id="ka20005", name="업종분봉조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka20006": APIInfo(api_id="ka20006", name="업종일봉조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka20007": APIInfo(api_id="ka20007", name="업종주봉조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka20008": APIInfo(api_id="ka20008", name="업종월봉조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka20009": APIInfo(api_id="ka20009", name="업종현재가일별요청", category="국내주식", subcategory="업종", url="/api/dostk/sect"),
    "ka20019": APIInfo(api_id="ka20019", name="업종년봉조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka20068": APIInfo(api_id="ka20068", name="대차거래추이요청(종목별)", category="국내주식", subcategory="대차거래", url="/api/dostk/slb"),
    "ka30001": APIInfo(api_id="ka30001", name="ELW가격급등락요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30002": APIInfo(api_id="ka30002", name="거래원별ELW순매매상위요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30003": APIInfo(api_id="ka30003", name="ELWLP보유일별추이요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30004": APIInfo(api_id="ka30004", name="ELW괴리율요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30005": APIInfo(api_id="ka30005", name="ELW조건검색요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30009": APIInfo(api_id="ka30009", name="ELW등락율순위요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30010": APIInfo(api_id="ka30010", name="ELW잔량순위요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30011": APIInfo(api_id="ka30011", name="ELW근접율요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka30012": APIInfo(api_id="ka30012", name="ELW종목상세정보요청", category="국내주식", subcategory="ELW", url="/api/dostk/elw"),
    "ka40001": APIInfo(api_id="ka40001", name="ETF수익율요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40002": APIInfo(api_id="ka40002", name="ETF종목정보요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40003": APIInfo(api_id="ka40003", name="ETF일별추이요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40004": APIInfo(api_id="ka40004", name="ETF전체시세요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40006": APIInfo(api_id="ka40006", name="ETF시간대별추이요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40007": APIInfo(api_id="ka40007", name="ETF시간대별체결요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40008": APIInfo(api_id="ka40008", name="ETF일자별체결요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40009": APIInfo(api_id="ka40009", name="ETF시간대별체결요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka40010": APIInfo(api_id="ka40010", name="ETF시간대별추이요청", category="국내주식", subcategory="ETF", url="/api/dostk/etf"),
    "ka50010": APIInfo(api_id="ka50010", name="금현물체결추이", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka50012": APIInfo(api_id="ka50012", name="금현물일별추이", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka50079": APIInfo(api_id="ka50079", name="금현물틱차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka50080": APIInfo(api_id="ka50080", name="금현물분봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka50081": APIInfo(api_id="ka50081", name="금현물일봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka50082": APIInfo(api_id="ka50082", name="금현물주봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka50083": APIInfo(api_id="ka50083", name="금현물월봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka50087": APIInfo(api_id="ka50087", name="금현물예상체결", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka50091": APIInfo(api_id="ka50091", name="금현물당일틱차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka50092": APIInfo(api_id="ka50092", name="금현물당일분봉차트조회요청", category="국내주식", subcategory="차트", url="/api/dostk/chart"),
    "ka50100": APIInfo(api_id="ka50100", name="금현물 시세정보", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka50101": APIInfo(api_id="ka50101", name="금현물 호가", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka52301": APIInfo(api_id="ka52301", name="금현물투자자현황", category="국내주식", subcategory="기관/외국인", url="/api/dostk/frgnistt"),
    "ka90001": APIInfo(api_id="ka90001", name="테마그룹별요청", category="국내주식", subcategory="테마", url="/api/dostk/thme"),
    "ka90002": APIInfo(api_id="ka90002", name="테마구성종목요청", category="국내주식", subcategory="테마", url="/api/dostk/thme"),
    "ka90003": APIInfo(api_id="ka90003", name="프로그램순매수상위50요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka90004": APIInfo(api_id="ka90004", name="종목별프로그램매매현황요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "ka90005": APIInfo(api_id="ka90005", name="프로그램매매추이요청 시간대별", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka90006": APIInfo(api_id="ka90006", name="프로그램매매차익잔고추이요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka90007": APIInfo(api_id="ka90007", name="프로그램매매누적추이요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka90008": APIInfo(api_id="ka90008", name="종목시간별프로그램매매추이요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka90009": APIInfo(api_id="ka90009", name="외국인기관매매상위요청", category="국내주식", subcategory="순위정보", url="/api/dostk/rkinfo"),
    "ka90010": APIInfo(api_id="ka90010", name="프로그램매매추이요청 일자별", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "ka90012": APIInfo(api_id="ka90012", name="대차거래내역요청", category="국내주식", subcategory="대차거래", url="/api/dostk/slb"),
    "ka90013": APIInfo(api_id="ka90013", name="종목일별프로그램매매추이요청", category="국내주식", subcategory="시세", url="/api/dostk/mrkcond"),
    "kt00001": APIInfo(api_id="kt00001", name="예수금상세현황요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00002": APIInfo(api_id="kt00002", name="일별추정예탁자산현황요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00003": APIInfo(api_id="kt00003", name="추정자산조회요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00004": APIInfo(api_id="kt00004", name="계좌평가현황요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00005": APIInfo(api_id="kt00005", name="체결잔고요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00007": APIInfo(api_id="kt00007", name="계좌별주문체결내역상세요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00008": APIInfo(api_id="kt00008", name="계좌별익일결제예정내역요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00009": APIInfo(api_id="kt00009", name="계좌별주문체결현황요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00010": APIInfo(api_id="kt00010", name="주문인출가능금액요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00011": APIInfo(api_id="kt00011", name="증거금율별주문가능수량조회요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00012": APIInfo(api_id="kt00012", name="신용보증금율별주문가능수량조회요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00013": APIInfo(api_id="kt00013", name="증거금세부내역조회요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00015": APIInfo(api_id="kt00015", name="위탁종합거래내역요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00016": APIInfo(api_id="kt00016", name="일별계좌수익률상세현황요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00017": APIInfo(api_id="kt00017", name="계좌별당일현황요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt00018": APIInfo(api_id="kt00018", name="계좌평가잔고내역요청", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt10000": APIInfo(api_id="kt10000", name="주식 매수주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt10001": APIInfo(api_id="kt10001", name="주식 매도주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt10002": APIInfo(api_id="kt10002", name="주식 정정주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt10003": APIInfo(api_id="kt10003", name="주식 취소주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt10006": APIInfo(api_id="kt10006", name="신용 매수주문", category="국내주식", subcategory="신용주문", url="/api/dostk/crdordr"),
    "kt10007": APIInfo(api_id="kt10007", name="신용 매도주문", category="국내주식", subcategory="신용주문", url="/api/dostk/crdordr"),
    "kt10008": APIInfo(api_id="kt10008", name="신용 정정주문", category="국내주식", subcategory="신용주문", url="/api/dostk/crdordr"),
    "kt10009": APIInfo(api_id="kt10009", name="신용 취소주문", category="국내주식", subcategory="신용주문", url="/api/dostk/crdordr"),
    "kt20016": APIInfo(api_id="kt20016", name="신용융자 가능종목요청", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "kt20017": APIInfo(api_id="kt20017", name="신용융자 가능문의", category="국내주식", subcategory="종목정보", url="/api/dostk/stkinfo"),
    "kt50000": APIInfo(api_id="kt50000", name="금현물 매수주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt50001": APIInfo(api_id="kt50001", name="금현물 매도주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt50002": APIInfo(api_id="kt50002", name="금현물 정정주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt50003": APIInfo(api_id="kt50003", name="금현물 취소주문", category="국내주식", subcategory="주문", url="/api/dostk/ordr"),
    "kt50020": APIInfo(api_id="kt50020", name="금현물 잔고확인", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt50021": APIInfo(api_id="kt50021", name="금현물 예수금", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt50030": APIInfo(api_id="kt50030", name="금현물 주문체결전체조회", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt50031": APIInfo(api_id="kt50031", name="금현물 주문체결조회", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt50032": APIInfo(api_id="kt50032", name="금현물 거래내역조회", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
    "kt50075": APIInfo(api_id="kt50075", name="금현물 미체결조회", category="국내주식", subcategory="계좌", url="/api/dostk/acnt"),
}

LEGACY_ALIAS_MAP: Dict[str, str] = {
    "ACCOUNT_CURRENT_STATUS": "kt00017",
    "ACCOUNT_DAILY_STATUS": "kt00017",
    "ACCOUNT_EVALUATION": "kt00004",
    "ACCOUNT_EVALUATION_BALANCE": "kt00018",
    "ACCOUNT_PROFIT": "ka10081",
    "AFTER_HOURS_SINGLE": "ka10087",
    "BASIC_INFO": "ka10001",
    "BUY_ORDER": "kt10000",
    "CANCEL_ORDER": "kt10003",
    "COMMISSION_TRADING_HISTORY": "kt00015",
    "CREDIT_BUY_ORDER": "kt10006",
    "CREDIT_CANCEL_ORDER": "kt10009",
    "CREDIT_MARGIN_ORDERABLE": "kt00012",
    "CREDIT_MODIFY_ORDER": "kt10008",
    "CREDIT_SELL_ORDER": "kt10007",
    "CREDIT_TRADING_TREND": "ka10013",
    "DAILY_ACCOUNT_PROFIT_DETAIL": "kt00016",
    "DAILY_BALANCE_PROFIT": "ka01690",
    "DAILY_CHART": "ka10081",
    "DAILY_ESTIMATED_ASSET": "kt00002",
    "DAILY_PRICE": "ka10086",
    "DAILY_REALIZED_PROFIT": "ka10073",
    "DAILY_REALIZED_PROFIT_BY_STOCK": "ka10072",
    "DAILY_REALIZED_PROFIT_DETAIL": "ka10077",
    "DAILY_TRADING_JOURNAL": "ka10170",
    "DAILY_TRADING_DETAIL": "ka10015",
    "DAILY_TRADING_LOG": "ka10169",
    "DAILY_WEEKLY_MONTHLY": "ka10005",
    "DEPOSIT_DETAIL": "kt00001",
    "ESTIMATED_ASSET": "kt00003",
    "EXECUTED_BALANCE": "kt00005",
    "EXECUTION_INFO": "ka10003",
    "EXECUTION_STRENGTH_DAILY": "ka10047",
    "EXECUTION_STRENGTH_HOURLY": "ka10046",
    "HIGH_LOW_PER": "ka10026",
    "HIGH_LOW_PROXIMITY": "ka10018",
    "INSTITUTION_DAILY": "ka10044",
    "INSTITUTION_TREND_BY_STOCK": "ka10045",
    "INVESTOR_AFTER_CLOSE": "ka10066",
    "INVESTOR_DAILY_TRADING": "ka10058",
    "INVESTOR_INSTITUTION_BY_STOCK": "ka10059",
    "INVESTOR_INSTITUTION_CHART": "ka10056",
    "INVESTOR_INSTITUTION_TOTAL": "ka10061",
    "INVESTOR_INTRADAY": "ka10062",
    "INVESTOR_INTRADAY_CHART": "ka10060",
    "MARGIN_DETAIL": "kt00013",
    "MARGIN_RATE_ORDERABLE": "kt00011",
    "MARKET_STATUS": "ka10007",
    "MEMBER_COMPANY_LIST": "ka10102",
    "MEMBER_COMPANY_TREND": "ka10078",
    "MINUTE_CHART": "ka10080",
    "MODIFY_ORDER": "kt10002",
    "MONTHLY_CHART": "ka10083",
    "NEW_HIGH_LOW": "ka10016",
    "NEXT_DAY_SETTLEMENT": "kt00008",
    "OPEN_PRICE_RATIO": "ka10028",
    "ORDERABLE_AMOUNT": "kt00010",
    "ORDER_EXECUTION_DETAIL": "kt00007",
    "ORDER_EXECUTION_STATUS": "kt00009",
    "ORDER_WITHDRAWABLE": "kt00010",
    "PRICE_SURGE_DROP": "ka10019",
    "PROGRAM_ACCUMULATED_TREND": "ka90007",
    "PROGRAM_PROFIT_TREND": "ka90006",
    "PROGRAM_TRADING_BY_STOCK": "ka90004",
    "PROGRAM_TRADING_HOURLY": "ka90005",
    "PROGRAM_TRADING_TOP_50": "ka90003",
    "PROGRAM_TREND_BY_STOCK_DAILY": "ka90013",
    "PROGRAM_TREND_BY_STOCK_HOURLY": "ka90008",
    "PROGRAM_TREND_DAILY": "ka90010",
    "QUOTE": "ka10004",
    "REAL_TIME_RANKING": "ka00198",
    "SAME_DAY_TRADING": "ka10055",
    "SECTOR_CODE_LIST": "ka10101",
    "SELL_ORDER": "kt10001",
    "STOCK_INFO_DETAIL": "ka10100",
    "STOCK_INFO_LIST": "ka10099",
    "SUPPLY_CONCENTRATION": "ka10025",
    "TICK_CHART": "ka10079",
    "TIME_MINUTE": "ka10006",
    "TOKEN": "au10001",
    "TOKEN_ISSUE": "au10001",
    "TOKEN_REVOKE": "au10002",
    "TRADER_INFO": "ka10002",
    "TRADER_INSTANT_VOLUME": "ka10052",
    "UNEXECUTED": "ka10075",
    "UNEXECUTED_ORDERS": "ka10075",
    "UPPER_LOWER_LIMIT": "ka10017",
    "VOLATILITY_CIRCUIT_BREAKER": "ka10054",
    "VOLUME_RENEWAL": "ka10024",
    "WARRANT_ALL_QUOTE": "ka10011",
    "WATCHLIST_INFO": "ka10095",
    "WEEKLY_CHART": "ka10082",
    "YEARLY_CHART": "ka10091",
}

def _filter_aliases(entries: Dict[str, APIInfo]) -> Dict[str, str]:
    return {alias: api_id for alias, api_id in LEGACY_ALIAS_MAP.items() if api_id in entries}

ALL_APIS = APICollection(ALL_API_DATA, LEGACY_ALIAS_MAP)
API_BY_ID = ALL_APIS

_category_map: Dict[str, Dict[str, APIInfo]] = defaultdict(dict)
_subcategory_map: Dict[str, Dict[str, APIInfo]] = defaultdict(dict)
for api_id, info in ALL_API_DATA.items():
    _category_map[info.category][api_id] = info
    _subcategory_map[info.subcategory][api_id] = info

API_BY_CATEGORY: Dict[str, APICollection] = {
    category: APICollection(data, _filter_aliases(data))
    for category, data in _category_map.items()
}

API_BY_SUBCATEGORY: Dict[str, APICollection] = {
    subcategory: APICollection(data, _filter_aliases(data))
    for subcategory, data in _subcategory_map.items()
}

EMPTY_COLLECTION = APICollection({})

OAUTH_APIS = API_BY_CATEGORY.get("OAuth 인증", EMPTY_COLLECTION)
DOMESTIC_STOCK_APIS = API_BY_CATEGORY.get("국내주식", EMPTY_COLLECTION)

STOCK_INFO_APIS = API_BY_SUBCATEGORY.get("종목정보", EMPTY_COLLECTION)
MARKET_DATA_APIS = API_BY_SUBCATEGORY.get("시세", EMPTY_COLLECTION)
ACCOUNT_APIS = API_BY_SUBCATEGORY.get("계좌", EMPTY_COLLECTION)
ORDER_APIS = API_BY_SUBCATEGORY.get("주문", EMPTY_COLLECTION)
CREDIT_ORDER_APIS = API_BY_SUBCATEGORY.get("신용주문", EMPTY_COLLECTION)
CHART_APIS = API_BY_SUBCATEGORY.get("차트", EMPTY_COLLECTION)
REAL_TIME_MARKET_APIS = API_BY_SUBCATEGORY.get("실시간시세", EMPTY_COLLECTION)
RANKING_APIS = API_BY_SUBCATEGORY.get("순위정보", EMPTY_COLLECTION)
INSTITUTION_FOREIGN_APIS = API_BY_SUBCATEGORY.get("기관/외국인", EMPTY_COLLECTION)
SECTOR_APIS = API_BY_SUBCATEGORY.get("업종", EMPTY_COLLECTION)
SHORT_SELLING_APIS = API_BY_SUBCATEGORY.get("공매도", EMPTY_COLLECTION)
LENDING_APIS = API_BY_SUBCATEGORY.get("대차거래", EMPTY_COLLECTION)
THEME_APIS = API_BY_SUBCATEGORY.get("테마", EMPTY_COLLECTION)
ELW_APIS = API_BY_SUBCATEGORY.get("ELW", EMPTY_COLLECTION)
ETF_APIS = API_BY_SUBCATEGORY.get("ETF", EMPTY_COLLECTION)
CONDITION_SEARCH_APIS = API_BY_SUBCATEGORY.get("조건검색", EMPTY_COLLECTION)

def get_api_info(key: str) -> APIInfo:
    return ALL_APIS[key]

def get_api_by_id(api_id: str) -> APIInfo:
    return ALL_APIS[api_id]

def get_apis_by_category(category: str) -> APICollection:
    return API_BY_CATEGORY[category]

def get_apis_by_subcategory(subcategory: str) -> APICollection:
    return API_BY_SUBCATEGORY[subcategory]

__all__ = [
    "APIInfo",
    "APICollection",
    "ALL_APIS",
    "ALL_API_DATA",
    "API_BY_ID",
    "API_BY_CATEGORY",
    "API_BY_SUBCATEGORY",
    "OAUTH_APIS",
    "DOMESTIC_STOCK_APIS",
    "STOCK_INFO_APIS",
    "MARKET_DATA_APIS",
    "ACCOUNT_APIS",
    "ORDER_APIS",
    "CREDIT_ORDER_APIS",
    "CHART_APIS",
    "REAL_TIME_MARKET_APIS",
    "RANKING_APIS",
    "INSTITUTION_FOREIGN_APIS",
    "SECTOR_APIS",
    "SHORT_SELLING_APIS",
    "LENDING_APIS",
    "THEME_APIS",
    "ELW_APIS",
    "ETF_APIS",
    "CONDITION_SEARCH_APIS",
    "LEGACY_ALIAS_MAP",
    "get_api_info",
    "get_api_by_id",
    "get_apis_by_category",
    "get_apis_by_subcategory",
]
