# 키움 REST API 상세 명세

## API 개요 목록

| No | API ID | API 명 | 대분류 | 중분류 | URL |
|---:|---|---|---|---|---|
| 1 | au10001 | 접근토큰 발급 | OAuth 인증 | 접근토큰발급 | `/oauth2/token` |
| 2 | au10002 | 접근토큰폐기 | OAuth 인증 | 접근토큰폐기 | `/oauth2/revoke` |
| 3 | ka00198 | 실시간종목조회순위 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 4 | ka01690 | 일별잔고수익률 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 5 | ka10001 | 주식기본정보요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 6 | ka10002 | 주식거래원요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 7 | ka10003 | 체결정보요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 8 | ka10004 | 주식호가요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 9 | ka10005 | 주식일주월시분요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 10 | ka10006 | 주식시분요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 11 | ka10007 | 시세표성정보요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 12 | ka10008 | 주식외국인종목별매매동향 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 13 | ka10009 | 주식기관요청 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 14 | ka10010 | 업종프로그램요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 15 | ka10011 | 신주인수권전체시세요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 16 | ka10013 | 신용매매동향요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 17 | ka10014 | 공매도추이요청 | 국내주식 | 공매도 | `/api/dostk/shsa` |
| 18 | ka10015 | 일별거래상세요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 19 | ka10016 | 신고저가요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 20 | ka10017 | 상하한가요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 21 | ka10018 | 고저가근접요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 22 | ka10019 | 가격급등락요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 23 | ka10020 | 호가잔량상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 24 | ka10021 | 호가잔량급증요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 25 | ka10022 | 잔량율급증요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 26 | ka10023 | 거래량급증요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 27 | ka10024 | 거래량갱신요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 28 | ka10025 | 매물대집중요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 29 | ka10026 | 고저PER요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 30 | ka10027 | 전일대비등락률상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 31 | ka10028 | 시가대비등락률요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 32 | ka10029 | 예상체결등락률상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 33 | ka10030 | 당일거래량상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 34 | ka10031 | 전일거래량상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 35 | ka10032 | 거래대금상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 36 | ka10033 | 신용비율상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 37 | ka10034 | 외인기간별매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 38 | ka10035 | 외인연속순매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 39 | ka10036 | 외인한도소진율증가상위 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 40 | ka10037 | 외국계창구매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 41 | ka10038 | 종목별증권사순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 42 | ka10039 | 증권사별매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 43 | ka10040 | 당일주요거래원요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 44 | ka10042 | 순매수거래원순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 45 | ka10043 | 거래원매물대분석요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 46 | ka10044 | 일별기관매매종목요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 47 | ka10045 | 종목별기관매매추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 48 | ka10046 | 체결강도추이시간별요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 49 | ka10047 | 체결강도추이일별요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 50 | ka10048 | ELW일별민감도지표요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 51 | ka10050 | ELW민감도지표요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 52 | ka10051 | 업종별투자자순매수요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 53 | ka10052 | 거래원순간거래량요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 54 | ka10053 | 당일상위이탈원요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 55 | ka10054 | 변동성완화장치발동종목요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 56 | ka10055 | 당일전일체결량요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 57 | ka10058 | 투자자별일별매매종목요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 58 | ka10059 | 종목별투자자기관별요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 59 | ka10060 | 종목별투자자기관별차트요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 60 | ka10061 | 종목별투자자기관별합계요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 61 | ka10062 | 동일순매매순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 62 | ka10063 | 장중투자자별매매요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 63 | ka10064 | 장중투자자별매매차트요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 64 | ka10065 | 장중투자자별매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 65 | ka10066 | 장마감후투자자별매매요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 66 | ka10068 | 대차거래추이요청 | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 67 | ka10069 | 대차거래상위10종목요청 | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 68 | ka10072 | 일자별종목별실현손익요청_일자 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 69 | ka10073 | 일자별종목별실현손익요청_기간 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 70 | ka10074 | 일자별실현손익요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 71 | ka10075 | 미체결요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 72 | ka10076 | 체결요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 73 | ka10077 | 당일실현손익상세요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 74 | ka10078 | 증권사별종목매매동향요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 75 | ka10079 | 주식틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 76 | ka10080 | 주식분봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 77 | ka10081 | 주식일봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 78 | ka10082 | 주식주봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 79 | ka10083 | 주식월봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 80 | ka10084 | 당일전일체결요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 81 | ka10085 | 계좌수익률요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 82 | ka10086 | 일별주가요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 83 | ka10087 | 시간외단일가요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 84 | ka10088 | 미체결 분할주문 상세 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 85 | ka10094 | 주식년봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 86 | ka10095 | 관심종목정보요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 87 | ka10098 | 시간외단일가등락율순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 88 | ka10099 | 종목정보 리스트 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 89 | ka10100 | 종목정보 조회 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 90 | ka10101 | 업종코드 리스트 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 91 | ka10102 | 회원사 리스트 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 92 | ka10131 | 기관외국인연속매매현황요청 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 93 | ka10170 | 당일매매일지요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 94 | ka10171 | 조건검색 목록조회 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 95 | ka10172 | 조건검색 요청 일반 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 96 | ka10173 | 조건검색 요청 실시간 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 97 | ka10174 | 조건검색 실시간 해제 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 98 | ka20001 | 업종현재가요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 99 | ka20002 | 업종별주가요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 100 | ka20003 | 전업종지수요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 101 | ka20004 | 업종틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 102 | ka20005 | 업종분봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 103 | ka20006 | 업종일봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 104 | ka20007 | 업종주봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 105 | ka20008 | 업종월봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 106 | ka20009 | 업종현재가일별요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 107 | ka20019 | 업종년봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 108 | ka20068 | 대차거래추이요청(종목별) | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 109 | ka30001 | ELW가격급등락요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 110 | ka30002 | 거래원별ELW순매매상위요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 111 | ka30003 | ELWLP보유일별추이요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 112 | ka30004 | ELW괴리율요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 113 | ka30005 | ELW조건검색요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 114 | ka30009 | ELW등락율순위요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 115 | ka30010 | ELW잔량순위요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 116 | ka30011 | ELW근접율요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 117 | ka30012 | ELW종목상세정보요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 118 | ka40001 | ETF수익율요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 119 | ka40002 | ETF종목정보요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 120 | ka40003 | ETF일별추이요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 121 | ka40004 | ETF전체시세요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 122 | ka40006 | ETF시간대별추이요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 123 | ka40007 | ETF시간대별체결요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 124 | ka40008 | ETF일자별체결요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 125 | ka40009 | ETF시간대별체결요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 126 | ka40010 | ETF시간대별추이요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 127 | ka50010 | 금현물체결추이 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 128 | ka50012 | 금현물일별추이 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 129 | ka50079 | 금현물틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 130 | ka50080 | 금현물분봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 131 | ka50081 | 금현물일봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 132 | ka50082 | 금현물주봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 133 | ka50083 | 금현물월봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 134 | ka50087 | 금현물예상체결 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 135 | ka50091 | 금현물당일틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 136 | ka50092 | 금현물당일분봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 137 | ka50100 | 금현물 시세정보 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 138 | ka50101 | 금현물 호가 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 139 | ka52301 | 금현물투자자현황 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 140 | ka90001 | 테마그룹별요청 | 국내주식 | 테마 | `/api/dostk/thme` |
| 141 | ka90002 | 테마구성종목요청 | 국내주식 | 테마 | `/api/dostk/thme` |
| 142 | ka90003 | 프로그램순매수상위50요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 143 | ka90004 | 종목별프로그램매매현황요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 144 | ka90005 | 프로그램매매추이요청 시간대별 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 145 | ka90006 | 프로그램매매차익잔고추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 146 | ka90007 | 프로그램매매누적추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 147 | ka90008 | 종목시간별프로그램매매추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 148 | ka90009 | 외국인기관매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 149 | ka90010 | 프로그램매매추이요청 일자별 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 150 | ka90012 | 대차거래내역요청 | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 151 | ka90013 | 종목일별프로그램매매추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 152 | kt00001 | 예수금상세현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 153 | kt00002 | 일별추정예탁자산현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 154 | kt00003 | 추정자산조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 155 | kt00004 | 계좌평가현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 156 | kt00005 | 체결잔고요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 157 | kt00007 | 계좌별주문체결내역상세요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 158 | kt00008 | 계좌별익일결제예정내역요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 159 | kt00009 | 계좌별주문체결현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 160 | kt00010 | 주문인출가능금액요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 161 | kt00011 | 증거금율별주문가능수량조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 162 | kt00012 | 신용보증금율별주문가능수량조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 163 | kt00013 | 증거금세부내역조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 164 | kt00015 | 위탁종합거래내역요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 165 | kt00016 | 일별계좌수익률상세현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 166 | kt00017 | 계좌별당일현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 167 | kt00018 | 계좌평가잔고내역요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 168 | kt10000 | 주식 매수주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 169 | kt10001 | 주식 매도주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 170 | kt10002 | 주식 정정주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 171 | kt10003 | 주식 취소주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 172 | kt10006 | 신용 매수주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 173 | kt10007 | 신용 매도주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 174 | kt10008 | 신용 정정주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 175 | kt10009 | 신용 취소주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 176 | kt20016 | 신용융자 가능종목요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 177 | kt20017 | 신용융자 가능문의 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 178 | kt50000 | 금현물 매수주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 179 | kt50001 | 금현물 매도주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 180 | kt50002 | 금현물 정정주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 181 | kt50003 | 금현물 취소주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 182 | kt50020 | 금현물 잔고확인 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 183 | kt50021 | 금현물 예수금 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 184 | kt50030 | 금현물 주문체결전체조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 185 | kt50031 | 금현물 주문체결조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 186 | kt50032 | 금현물 거래내역조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 187 | kt50075 | 금현물 미체결조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 188 | 00 | 주문체결 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 189 | 04 | 잔고 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 190 | 0A | 주식기세 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 191 | 0B | 주식체결 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 192 | 0C | 주식우선호가 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 193 | 0D | 주식호가잔량 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 194 | 0E | 주식시간외호가 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 195 | 0F | 주식당일거래원 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 196 | 0G | ETF NAV | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 197 | 0H | 주식예상체결 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 198 | 0I | 국제금환산가격 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 199 | 0J | 업종지수 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 200 | 0U | 업종등락 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 201 | 0g | 주식종목정보 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 202 | 0m | ELW 이론가 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 203 | 0s | 장시작시간 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 204 | 0u | ELW 지표 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 205 | 0w | 종목프로그램매매 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 206 | 1h | VI발동/해제 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 207 | 공통 | 오류코드 | nan | nan | `nan` |

---

## 접근토큰 발급 `au10001`

**Method**: `POST`  
**URL**: `/oauth2/token`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `appkey` | String | Y | 앱키 |  |  |
| `secretkey` | String | Y | 시크릿키 |  |  |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `token_type` | String | Y | 토큰타입 |  |  |
| `token` | String | Y | 접근토큰 |  |  |

---

## 접근토큰폐기 `au10002`

**Method**: `POST`  
**URL**: `/oauth2/revoke`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `secretkey` | String | Y | 시크릿키 |  |  |
| `token` | String | Y | 접근토큰 |  |  |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

---

## 실시간종목조회순위 `ka00198`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- bigd_rank` | String | N | 빅데이터 순위 |  | 20 |
| `- rank_chg` | String | N | 순위 등락 |  | 20 |
| `- rank_chg_sign` | String | N | 순위 등락 부호 |  | 20 |
| `- past_curr_prc` | String | N | 과거 현재가 |  | 20 |
| `- base_comp_sign` | String | N | 기준가 대비 부호 |  | 20 |
| `- base_comp_chgr` | String | N | 기준가 대비 등락율 |  | 20 |
| `- prev_base_sign` | String | N | 직전 기준 대비 부호 |  | 20 |
| `- prev_base_chgr` | String | N | 직전 기준 대비 등락율 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- tm` | String | N | 시간 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |

---

## 일별잔고수익률 `ka01690`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tot_buy_amt` | String | N | 총 매입가 |  | 20 |
| `tot_evlt_amt` | String | N | 총 평가금액 |  | 20 |
| `tot_evltv_prft` | String | N | 총 평가손익 |  | 20 |
| `tot_prft_rt` | String | N | 수익률 |  | 20 |
| `dbst_bal` | String | N | 예수금 |  | 20 |
| `day_stk_asst` | String | N | 추정자산 |  | 20 |
| `buy_wght` | String | N | 현금비중 |  | 20 |
| `day_bal_rt` | LIST | N | 일별잔고수익률 |  |  |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 20 |
| `- rmnd_qty` | String | N | 보유 수량 |  | 20 |
| `- buy_uv` | String | N | 매입 단가 |  | 20 |
| `- buy_wght` | String | N | 매수비중 |  | 20 |
| `- evltv_prft` | String | N | 평가손익 |  | 20 |
| `- prft_rt` | String | N | 수익률 |  | 20 |
| `- evlt_amt` | String | N | 평가금액 |  | 20 |
| `- evlt_wght` | String | N | 평가비중 |  | 20 |

---

## 주식기본정보요청 `ka10001`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_nm` | String | N | 종목명 |  | 40 |
| `setl_mm` | String | N | 결산월 |  | 20 |
| `fav` | String | N | 액면가 |  | 20 |
| `cap` | String | N | 자본금 |  | 20 |
| `flo_stk` | String | N | 상장주식 |  | 20 |
| `crd_rt` | String | N | 신용비율 |  | 20 |
| `oyr_hgst` | String | N | 연중최고 |  | 20 |
| `oyr_lwst` | String | N | 연중최저 |  | 20 |
| `mac` | String | N | 시가총액 |  | 20 |
| `mac_wght` | String | N | 시가총액비중 |  | 20 |
| `for_exh_rt` | String | N | 외인소진률 |  | 20 |
| `repl_pric` | String | N | 대용가 |  | 20 |
| `per` | String | N | PER | [ 주의 ] PER, ROE 값들은 외부벤더사에서 제공되는 데이터이며 일주일에 한번 또는 실적발표 시즌에 업데이트 됨 | 20 |
| `eps` | String | N | EPS |  | 20 |
| `roe` | String | N | ROE | [ 주의 ]  PER, ROE 값들은 외부벤더사에서 제공되는 데이터이며 일주일에 한번 또는 실적발표 시즌에 업데이트 됨 | 20 |
| `pbr` | String | N | PBR |  | 20 |
| `ev` | String | N | EV |  | 20 |
| `bps` | String | N | BPS |  | 20 |
| `sale_amt` | String | N | 매출액 |  | 20 |
| `bus_pro` | String | N | 영업이익 |  | 20 |
| `cup_nga` | String | N | 당기순이익 |  | 20 |
| `250hgst` | String | N | 250최고 |  | 20 |
| `250lwst` | String | N | 250최저 |  | 20 |
| `open_pric` | String | N | 시가 |  | 20 |
| `high_pric` | String | N | 고가 |  | 20 |
| `low_pric` | String | N | 저가 |  | 20 |
| `upl_pric` | String | N | 상한가 |  | 20 |
| `lst_pric` | String | N | 하한가 |  | 20 |
| `base_pric` | String | N | 기준가 |  | 20 |
| `exp_cntr_pric` | String | N | 예상체결가 |  | 20 |
| `exp_cntr_qty` | String | N | 예상체결수량 |  | 20 |
| `250hgst_pric_dt` | String | N | 250최고가일 |  | 20 |
| `250hgst_pric_pre_rt` | String | N | 250최고가대비율 |  | 20 |
| `250lwst_pric_dt` | String | N | 250최저가일 |  | 20 |
| `250lwst_pric_pre_rt` | String | N | 250최저가대비율 |  | 20 |
| `cur_prc` | String | N | 현재가 |  | 20 |
| `pre_sig` | String | N | 대비기호 |  | 20 |
| `pred_pre` | String | N | 전일대비 |  | 20 |
| `flu_rt` | String | N | 등락율 |  | 20 |
| `trde_qty` | String | N | 거래량 |  | 20 |
| `trde_pre` | String | N | 거래대비 |  | 20 |
| `fav_unit` | String | N | 액면가단위 |  | 20 |
| `dstr_stk` | String | N | 유통주식 |  | 20 |
| `dstr_rt` | String | N | 유통비율 |  | 20 |

---

## 주식거래원요청 `ka10002`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_nm` | String | N | 종목명 |  | 40 |
| `cur_prc` | String | N | 현재가 |  | 20 |
| `flu_smbol` | String | N | 등락부호 |  | 20 |
| `base_pric` | String | N | 기준가 |  | 20 |
| `pred_pre` | String | N | 전일대비 |  | 20 |
| `flu_rt` | String | N | 등락율 |  | 20 |
| `sel_trde_ori_nm_1` | String | N | 매도거래원명1 |  | 20 |
| `sel_trde_ori_1` | String | N | 매도거래원1 |  | 20 |
| `sel_trde_qty_1` | String | N | 매도거래량1 |  | 20 |
| `buy_trde_ori_nm_1` | String | N | 매수거래원명1 |  | 20 |
| `buy_trde_ori_1` | String | N | 매수거래원1 |  | 20 |
| `buy_trde_qty_1` | String | N | 매수거래량1 |  | 20 |
| `sel_trde_ori_nm_2` | String | N | 매도거래원명2 |  | 20 |
| `sel_trde_ori_2` | String | N | 매도거래원2 |  | 20 |
| `sel_trde_qty_2` | String | N | 매도거래량2 |  | 20 |
| `buy_trde_ori_nm_2` | String | N | 매수거래원명2 |  | 20 |
| `buy_trde_ori_2` | String | N | 매수거래원2 |  | 20 |
| `buy_trde_qty_2` | String | N | 매수거래량2 |  | 20 |
| `sel_trde_ori_nm_3` | String | N | 매도거래원명3 |  | 20 |
| `sel_trde_ori_3` | String | N | 매도거래원3 |  | 20 |
| `sel_trde_qty_3` | String | N | 매도거래량3 |  | 20 |
| `buy_trde_ori_nm_3` | String | N | 매수거래원명3 |  | 20 |
| `buy_trde_ori_3` | String | N | 매수거래원3 |  | 20 |
| `buy_trde_qty_3` | String | N | 매수거래량3 |  | 20 |
| `sel_trde_ori_nm_4` | String | N | 매도거래원명4 |  | 20 |
| `sel_trde_ori_4` | String | N | 매도거래원4 |  | 20 |
| `sel_trde_qty_4` | String | N | 매도거래량4 |  | 20 |
| `buy_trde_ori_nm_4` | String | N | 매수거래원명4 |  | 20 |
| `buy_trde_ori_4` | String | N | 매수거래원4 |  | 20 |
| `buy_trde_qty_4` | String | N | 매수거래량4 |  | 20 |
| `sel_trde_ori_nm_5` | String | N | 매도거래원명5 |  | 20 |
| `sel_trde_ori_5` | String | N | 매도거래원5 |  | 20 |
| `sel_trde_qty_5` | String | N | 매도거래량5 |  | 20 |
| `buy_trde_ori_nm_5` | String | N | 매수거래원명5 |  | 20 |
| `buy_trde_ori_5` | String | N | 매수거래원5 |  | 20 |
| `buy_trde_qty_5` | String | N | 매수거래량5 |  | 20 |

---

## 체결정보요청 `ka10003`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- tm` | String | N | 시간 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- pre_rt` | String | N | 대비율 |  | 20 |
| `- pri_sel_bid_unit` | String | N | 우선매도호가단위 |  | 20 |
| `- pri_buy_bid_unit` | String | N | 우선매수호가단위 |  | 20 |
| `- cntr_trde_qty` | String | N | 체결거래량 |  | 20 |
| `- sign` | String | N | sign |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | KRX , NXT , 통합 | 20 |

---

## 주식호가요청 `ka10004`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sel_10th_pre_req_pre` | String | N | 매도10차선잔량대비 | 매도호가직전대비10 | 20 |
| `sel_10th_pre_req` | String | N | 매도10차선잔량 | 매도호가수량10 | 20 |
| `sel_10th_pre_bid` | String | N | 매도10차선호가 | 매도호가10 | 20 |
| `sel_9th_pre_req_pre` | String | N | 매도9차선잔량대비 | 매도호가직전대비9 | 20 |
| `sel_9th_pre_req` | String | N | 매도9차선잔량 | 매도호가수량9 | 20 |
| `sel_9th_pre_bid` | String | N | 매도9차선호가 | 매도호가9 | 20 |
| `sel_8th_pre_req_pre` | String | N | 매도8차선잔량대비 | 매도호가직전대비8 | 20 |
| `sel_8th_pre_req` | String | N | 매도8차선잔량 | 매도호가수량8 | 20 |
| `sel_8th_pre_bid` | String | N | 매도8차선호가 | 매도호가8 | 20 |
| `sel_7th_pre_req_pre` | String | N | 매도7차선잔량대비 | 매도호가직전대비7 | 20 |
| `sel_7th_pre_req` | String | N | 매도7차선잔량 | 매도호가수량7 | 20 |
| `sel_7th_pre_bid` | String | N | 매도7차선호가 | 매도호가7 | 20 |
| `sel_6th_pre_req_pre` | String | N | 매도6차선잔량대비 | 매도호가직전대비6 | 20 |
| `sel_6th_pre_req` | String | N | 매도6차선잔량 | 매도호가수량6 | 20 |
| `sel_6th_pre_bid` | String | N | 매도6차선호가 | 매도호가6 | 20 |
| `sel_5th_pre_req_pre` | String | N | 매도5차선잔량대비 | 매도호가직전대비5 | 20 |
| `sel_5th_pre_req` | String | N | 매도5차선잔량 | 매도호가수량5 | 20 |
| `sel_5th_pre_bid` | String | N | 매도5차선호가 | 매도호가5 | 20 |
| `sel_4th_pre_req_pre` | String | N | 매도4차선잔량대비 | 매도호가직전대비4 | 20 |
| `sel_4th_pre_req` | String | N | 매도4차선잔량 | 매도호가수량4 | 20 |
| `sel_4th_pre_bid` | String | N | 매도4차선호가 | 매도호가4 | 20 |
| `sel_3th_pre_req_pre` | String | N | 매도3차선잔량대비 | 매도호가직전대비3 | 20 |
| `sel_3th_pre_req` | String | N | 매도3차선잔량 | 매도호가수량3 | 20 |
| `sel_3th_pre_bid` | String | N | 매도3차선호가 | 매도호가3 | 20 |
| `sel_2th_pre_req_pre` | String | N | 매도2차선잔량대비 | 매도호가직전대비2 | 20 |
| `sel_2th_pre_req` | String | N | 매도2차선잔량 | 매도호가수량2 | 20 |
| `sel_2th_pre_bid` | String | N | 매도2차선호가 | 매도호가2 | 20 |
| `sel_1th_pre_req_pre` | String | N | 매도1차선잔량대비 | 매도호가직전대비1 | 20 |
| `sel_fpr_req` | String | N | 매도최우선잔량 | 매도호가수량1 | 20 |
| `sel_fpr_bid` | String | N | 매도최우선호가 | 매도호가1 | 20 |
| `buy_fpr_bid` | String | N | 매수최우선호가 | 매수호가1 | 20 |
| `buy_fpr_req` | String | N | 매수최우선잔량 | 매수호가수량1 | 20 |
| `buy_1th_pre_req_pre` | String | N | 매수1차선잔량대비 | 매수호가직전대비1 | 20 |
| `buy_2th_pre_bid` | String | N | 매수2차선호가 | 매수호가2 | 20 |
| `buy_2th_pre_req` | String | N | 매수2차선잔량 | 매수호가수량2 | 20 |
| `buy_2th_pre_req_pre` | String | N | 매수2차선잔량대비 | 매수호가직전대비2 | 20 |
| `buy_3th_pre_bid` | String | N | 매수3차선호가 | 매수호가3 | 20 |
| `buy_3th_pre_req` | String | N | 매수3차선잔량 | 매수호가수량3 | 20 |
| `buy_3th_pre_req_pre` | String | N | 매수3차선잔량대비 | 매수호가직전대비3 | 20 |
| `buy_4th_pre_bid` | String | N | 매수4차선호가 | 매수호가4 | 20 |
| `buy_4th_pre_req` | String | N | 매수4차선잔량 | 매수호가수량4 | 20 |
| `buy_4th_pre_req_pre` | String | N | 매수4차선잔량대비 | 매수호가직전대비4 | 20 |
| `buy_5th_pre_bid` | String | N | 매수5차선호가 | 매수호가5 | 20 |
| `buy_5th_pre_req` | String | N | 매수5차선잔량 | 매수호가수량5 | 20 |
| `buy_5th_pre_req_pre` | String | N | 매수5차선잔량대비 | 매수호가직전대비5 | 20 |
| `buy_6th_pre_bid` | String | N | 매수6차선호가 | 매수호가6 | 20 |
| `buy_6th_pre_req` | String | N | 매수6차선잔량 | 매수호가수량6 | 20 |
| `buy_6th_pre_req_pre` | String | N | 매수6차선잔량대비 | 매수호가직전대비6 | 20 |
| `buy_7th_pre_bid` | String | N | 매수7차선호가 | 매수호가7 | 20 |
| `buy_7th_pre_req` | String | N | 매수7차선잔량 | 매수호가수량7 | 20 |
| `buy_7th_pre_req_pre` | String | N | 매수7차선잔량대비 | 매수호가직전대비7 | 20 |
| `buy_8th_pre_bid` | String | N | 매수8차선호가 | 매수호가8 | 20 |
| `buy_8th_pre_req` | String | N | 매수8차선잔량 | 매수호가수량8 | 20 |
| `buy_8th_pre_req_pre` | String | N | 매수8차선잔량대비 | 매수호가직전대비8 | 20 |
| `buy_9th_pre_bid` | String | N | 매수9차선호가 | 매수호가9 | 20 |
| `buy_9th_pre_req` | String | N | 매수9차선잔량 | 매수호가수량9 | 20 |
| `buy_9th_pre_req_pre` | String | N | 매수9차선잔량대비 | 매수호가직전대비9 | 20 |
| `buy_10th_pre_bid` | String | N | 매수10차선호가 | 매수호가10 | 20 |
| `buy_10th_pre_req` | String | N | 매수10차선잔량 | 매수호가수량10 | 20 |
| `buy_10th_pre_req_pre` | String | N | 매수10차선잔량대비 | 매수호가직전대비10 | 20 |
| `tot_sel_req_jub_pre` | String | N | 총매도잔량직전대비 | 매도호가총잔량직전대비 | 20 |
| `tot_sel_req` | String | N | 총매도잔량 | 매도호가총잔량 | 20 |
| `tot_buy_req` | String | N | 총매수잔량 | 매수호가총잔량 | 20 |
| `tot_buy_req_jub_pre` | String | N | 총매수잔량직전대비 | 매수호가총잔량직전대비 | 20 |
| `ovt_sel_req_pre` | String | N | 시간외매도잔량대비 | 시간외 매도호가 총잔량 직전대비 | 20 |
| `ovt_sel_req` | String | N | 시간외매도잔량 | 시간외 매도호가 총잔량 | 20 |
| `ovt_buy_req` | String | N | 시간외매수잔량 | 시간외 매수호가 총잔량 | 20 |
| `ovt_buy_req_pre` | String | N | 시간외매수잔량대비 | 시간외 매수호가 총잔량 직전대비 | 20 |

---

## 주식일주월시분요청 `ka10005`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- date` | String | N | 날짜 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pre` | String | N | 대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- for_poss` | String | N | 외인보유 |  | 20 |
| `- for_wght` | String | N | 외인비중 |  | 20 |
| `- for_netprps` | String | N | 외인순매수 |  | 20 |
| `- orgn_netprps` | String | N | 기관순매수 |  | 20 |
| `- ind_netprps` | String | N | 개인순매수 |  | 20 |
| `- frgn` | String | N | 외국계 |  | 20 |
| `- crd_remn_rt` | String | N | 신용잔고율 |  | 20 |
| `- prm` | String | N | 프로그램 |  | 20 |

---

## 주식시분요청 `ka10006`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `open_pric` | String | N | 시가 |  | 20 |
| `high_pric` | String | N | 고가 |  | 20 |
| `low_pric` | String | N | 저가 |  | 20 |
| `close_pric` | String | N | 종가 |  | 20 |
| `pre` | String | N | 대비 |  | 20 |
| `flu_rt` | String | N | 등락률 |  | 20 |
| `trde_qty` | String | N | 거래량 |  | 20 |
| `trde_prica` | String | N | 거래대금 |  | 20 |
| `cntr_str` | String | N | 체결강도 |  | 20 |

---

## 시세표성정보요청 `ka10007`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | N | 종목코드 |  | 6 |
| `date` | String | N | 날짜 |  | 20 |
| `tm` | String | N | 시간 |  | 20 |
| `pred_close_pric` | String | N | 전일종가 |  | 20 |
| `pred_trde_qty` | String | N | 전일거래량 |  | 20 |
| `upl_pric` | String | N | 상한가 |  | 20 |
| `lst_pric` | String | N | 하한가 |  | 20 |
| `pred_trde_prica` | String | N | 전일거래대금 |  | 20 |
| `flo_stkcnt` | String | N | 상장주식수 |  | 20 |
| `cur_prc` | String | N | 현재가 |  | 20 |
| `smbol` | String | N | 부호 |  | 20 |
| `flu_rt` | String | N | 등락률 |  | 20 |
| `pred_rt` | String | N | 전일비 |  | 20 |
| `open_pric` | String | N | 시가 |  | 20 |
| `high_pric` | String | N | 고가 |  | 20 |
| `low_pric` | String | N | 저가 |  | 20 |
| `cntr_qty` | String | N | 체결량 |  | 20 |
| `trde_qty` | String | N | 거래량 |  | 20 |
| `trde_prica` | String | N | 거래대금 |  | 20 |
| `exp_cntr_pric` | String | N | 예상체결가 |  | 20 |
| `exp_cntr_qty` | String | N | 예상체결량 |  | 20 |
| `exp_sel_pri_bid` | String | N | 예상매도우선호가 |  | 20 |
| `exp_buy_pri_bid` | String | N | 예상매수우선호가 |  | 20 |
| `trde_strt_dt` | String | N | 거래시작일 |  | 20 |
| `exec_pric` | String | N | 행사가격 |  | 20 |
| `hgst_pric` | String | N | 최고가 |  | 20 |
| `lwst_pric` | String | N | 최저가 |  | 20 |
| `hgst_pric_dt` | String | N | 최고가일 |  | 20 |
| `lwst_pric_dt` | String | N | 최저가일 |  | 20 |
| `sel_1bid` | String | N | 매도1호가 |  | 20 |
| `sel_2bid` | String | N | 매도2호가 |  | 20 |
| `sel_3bid` | String | N | 매도3호가 |  | 20 |
| `sel_4bid` | String | N | 매도4호가 |  | 20 |
| `sel_5bid` | String | N | 매도5호가 |  | 20 |
| `sel_6bid` | String | N | 매도6호가 |  | 20 |
| `sel_7bid` | String | N | 매도7호가 |  | 20 |
| `sel_8bid` | String | N | 매도8호가 |  | 20 |
| `sel_9bid` | String | N | 매도9호가 |  | 20 |
| `sel_10bid` | String | N | 매도10호가 |  | 20 |
| `buy_1bid` | String | N | 매수1호가 |  | 20 |
| `buy_2bid` | String | N | 매수2호가 |  | 20 |
| `buy_3bid` | String | N | 매수3호가 |  | 20 |
| `buy_4bid` | String | N | 매수4호가 |  | 20 |
| `buy_5bid` | String | N | 매수5호가 |  | 20 |
| `buy_6bid` | String | N | 매수6호가 |  | 20 |
| `buy_7bid` | String | N | 매수7호가 |  | 20 |
| `buy_8bid` | String | N | 매수8호가 |  | 20 |
| `buy_9bid` | String | N | 매수9호가 |  | 20 |
| `buy_10bid` | String | N | 매수10호가 |  | 20 |
| `sel_1bid_req` | String | N | 매도1호가잔량 |  | 20 |
| `sel_2bid_req` | String | N | 매도2호가잔량 |  | 20 |
| `sel_3bid_req` | String | N | 매도3호가잔량 |  | 20 |
| `sel_4bid_req` | String | N | 매도4호가잔량 |  | 20 |
| `sel_5bid_req` | String | N | 매도5호가잔량 |  | 20 |
| `sel_6bid_req` | String | N | 매도6호가잔량 |  | 20 |
| `sel_7bid_req` | String | N | 매도7호가잔량 |  | 20 |
| `sel_8bid_req` | String | N | 매도8호가잔량 |  | 20 |
| `sel_9bid_req` | String | N | 매도9호가잔량 |  | 20 |
| `sel_10bid_req` | String | N | 매도10호가잔량 |  | 20 |
| `buy_1bid_req` | String | N | 매수1호가잔량 |  | 20 |
| `buy_2bid_req` | String | N | 매수2호가잔량 |  | 20 |
| `buy_3bid_req` | String | N | 매수3호가잔량 |  | 20 |
| `buy_4bid_req` | String | N | 매수4호가잔량 |  | 20 |
| `buy_5bid_req` | String | N | 매수5호가잔량 |  | 20 |
| `buy_6bid_req` | String | N | 매수6호가잔량 |  | 20 |
| `buy_7bid_req` | String | N | 매수7호가잔량 |  | 20 |
| `buy_8bid_req` | String | N | 매수8호가잔량 |  | 20 |
| `buy_9bid_req` | String | N | 매수9호가잔량 |  | 20 |
| `buy_10bid_req` | String | N | 매수10호가잔량 |  | 20 |
| `sel_1bid_jub_pre` | String | N | 매도1호가직전대비 |  | 20 |
| `sel_2bid_jub_pre` | String | N | 매도2호가직전대비 |  | 20 |
| `sel_3bid_jub_pre` | String | N | 매도3호가직전대비 |  | 20 |
| `sel_4bid_jub_pre` | String | N | 매도4호가직전대비 |  | 20 |
| `sel_5bid_jub_pre` | String | N | 매도5호가직전대비 |  | 20 |
| `sel_6bid_jub_pre` | String | N | 매도6호가직전대비 |  | 20 |
| `sel_7bid_jub_pre` | String | N | 매도7호가직전대비 |  | 20 |
| `sel_8bid_jub_pre` | String | N | 매도8호가직전대비 |  | 20 |
| `sel_9bid_jub_pre` | String | N | 매도9호가직전대비 |  | 20 |
| `sel_10bid_jub_pre` | String | N | 매도10호가직전대비 |  | 20 |
| `buy_1bid_jub_pre` | String | N | 매수1호가직전대비 |  | 20 |
| `buy_2bid_jub_pre` | String | N | 매수2호가직전대비 |  | 20 |
| `buy_3bid_jub_pre` | String | N | 매수3호가직전대비 |  | 20 |
| `buy_4bid_jub_pre` | String | N | 매수4호가직전대비 |  | 20 |
| `buy_5bid_jub_pre` | String | N | 매수5호가직전대비 |  | 20 |
| `buy_6bid_jub_pre` | String | N | 매수6호가직전대비 |  | 20 |
| `buy_7bid_jub_pre` | String | N | 매수7호가직전대비 |  | 20 |
| `buy_8bid_jub_pre` | String | N | 매수8호가직전대비 |  | 20 |
| `buy_9bid_jub_pre` | String | N | 매수9호가직전대비 |  | 20 |
| `buy_10bid_jub_pre` | String | N | 매수10호가직전대비 |  | 20 |
| `sel_1bid_cnt` | String | N | 매도1호가건수 |  | 20 |
| `sel_2bid_cnt` | String | N | 매도2호가건수 |  | 20 |
| `sel_3bid_cnt` | String | N | 매도3호가건수 |  | 20 |
| `sel_4bid_cnt` | String | N | 매도4호가건수 |  | 20 |
| `sel_5bid_cnt` | String | N | 매도5호가건수 |  | 20 |
| `buy_1bid_cnt` | String | N | 매수1호가건수 |  | 20 |
| `buy_2bid_cnt` | String | N | 매수2호가건수 |  | 20 |
| `buy_3bid_cnt` | String | N | 매수3호가건수 |  | 20 |
| `buy_4bid_cnt` | String | N | 매수4호가건수 |  | 20 |
| `buy_5bid_cnt` | String | N | 매수5호가건수 |  | 20 |
| `lpsel_1bid_req` | String | N | LP매도1호가잔량 |  | 20 |
| `lpsel_2bid_req` | String | N | LP매도2호가잔량 |  | 20 |
| `lpsel_3bid_req` | String | N | LP매도3호가잔량 |  | 20 |
| `lpsel_4bid_req` | String | N | LP매도4호가잔량 |  | 20 |
| `lpsel_5bid_req` | String | N | LP매도5호가잔량 |  | 20 |
| `lpsel_6bid_req` | String | N | LP매도6호가잔량 |  | 20 |
| `lpsel_7bid_req` | String | N | LP매도7호가잔량 |  | 20 |
| `lpsel_8bid_req` | String | N | LP매도8호가잔량 |  | 20 |
| `lpsel_9bid_req` | String | N | LP매도9호가잔량 |  | 20 |
| `lpsel_10bid_req` | String | N | LP매도10호가잔량 |  | 20 |
| `lpbuy_1bid_req` | String | N | LP매수1호가잔량 |  | 20 |
| `lpbuy_2bid_req` | String | N | LP매수2호가잔량 |  | 20 |
| `lpbuy_3bid_req` | String | N | LP매수3호가잔량 |  | 20 |
| `lpbuy_4bid_req` | String | N | LP매수4호가잔량 |  | 20 |
| `lpbuy_5bid_req` | String | N | LP매수5호가잔량 |  | 20 |
| `lpbuy_6bid_req` | String | N | LP매수6호가잔량 |  | 20 |
| `lpbuy_7bid_req` | String | N | LP매수7호가잔량 |  | 20 |
| `lpbuy_8bid_req` | String | N | LP매수8호가잔량 |  | 20 |
| `lpbuy_9bid_req` | String | N | LP매수9호가잔량 |  | 20 |
| `lpbuy_10bid_req` | String | N | LP매수10호가잔량 |  | 20 |
| `tot_buy_req` | String | N | 총매수잔량 |  | 20 |
| `tot_sel_req` | String | N | 총매도잔량 |  | 20 |
| `tot_buy_cnt` | String | N | 총매수건수 |  | 20 |
| `tot_sel_cnt` | String | N | 총매도건수 |  | 20 |

---

## 주식외국인종목별매매동향 `ka10008`

**Method**: `POST`  
**URL**: `/api/dostk/frgnistt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- chg_qty` | String | N | 변동수량 |  | 20 |
| `- poss_stkcnt` | String | N | 보유주식수 |  | 20 |
| `- wght` | String | N | 비중 |  | 20 |
| `- gain_pos_stkcnt` | String | N | 취득가능주식수 |  | 20 |
| `- frgnr_limit` | String | N | 외국인한도 |  | 20 |
| `- frgnr_limit_irds` | String | N | 외국인한도증감 |  | 20 |
| `- limit_exh_rt` | String | N | 한도소진률 |  | 20 |

---

## 주식기관요청 `ka10009`

**Method**: `POST`  
**URL**: `/api/dostk/frgnistt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `close_pric` | String | N | 종가 |  | 20 |
| `pre` | String | N | 대비 |  | 20 |
| `orgn_dt_acc` | String | N | 기관기간누적 |  | 20 |
| `orgn_daly_nettrde` | String | N | 기관일별순매매 |  | 20 |
| `frgnr_daly_nettrde` | String | N | 외국인일별순매매 |  | 20 |
| `frgnr_qota_rt` | String | N | 외국인지분율 |  | 20 |

---

## 업종프로그램요청 `ka10010`

**Method**: `POST`  
**URL**: `/api/dostk/sect`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dfrt_trst_sell_amt` | String | N | 차익위탁매도금액 |  | 20 |
| `dfrt_trst_buy_qty` | String | N | 차익위탁매수수량 |  | 20 |
| `dfrt_trst_buy_amt` | String | N | 차익위탁매수금액 |  | 20 |
| `dfrt_trst_netprps_qty` | String | N | 차익위탁순매수수량 |  | 20 |
| `dfrt_trst_netprps_amt` | String | N | 차익위탁순매수금액 |  | 20 |
| `ndiffpro_trst_sell_qty` | String | N | 비차익위탁매도수량 |  | 20 |
| `ndiffpro_trst_sell_amt` | String | N | 비차익위탁매도금액 |  | 20 |
| `ndiffpro_trst_buy_qty` | String | N | 비차익위탁매수수량 |  | 20 |
| `ndiffpro_trst_buy_amt` | String | N | 비차익위탁매수금액 |  | 20 |
| `ndiffpro_trst_netprps_qty` | String | N | 비차익위탁순매수수량 |  | 20 |
| `ndiffpro_trst_netprps_amt` | String | N | 비차익위탁순매수금액 |  | 20 |
| `all_dfrt_trst_sell_qty` | String | N | 전체차익위탁매도수량 |  | 20 |
| `all_dfrt_trst_sell_amt` | String | N | 전체차익위탁매도금액 |  | 20 |
| `all_dfrt_trst_buy_qty` | String | N | 전체차익위탁매수수량 |  | 20 |
| `all_dfrt_trst_buy_amt` | String | N | 전체차익위탁매수금액 |  | 20 |
| `all_dfrt_trst_netprps_qty` | String | N | 전체차익위탁순매수수량 |  | 20 |
| `all_dfrt_trst_netprps_amt` | String | N | 전체차익위탁순매수금액 |  | 20 |

---

## 신주인수권전체시세요청 `ka10011`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- fpr_sel_bid` | String | N | 최우선매도호가 |  | 20 |
| `- fpr_buy_bid` | String | N | 최우선매수호가 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |

---

## 신용매매동향요청 `ka10013`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dt` | String | Y | 일자 | YYYYMMDD | 8 |
| `qry_tp` | String | Y | 조회구분 | 1:융자, 2:대주 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- new` | String | N | 신규 |  | 20 |
| `- rpya` | String | N | 상환 |  | 20 |
| `- remn` | String | N | 잔고 |  | 20 |
| `- amt` | String | N | 금액 |  | 20 |
| `- pre` | String | N | 대비 |  | 20 |
| `- shr_rt` | String | N | 공여율 |  | 20 |
| `- remn_rt` | String | N | 잔고율 |  | 20 |

---

## 공매도추이요청 `ka10014`

**Method**: `POST`  
**URL**: `/api/dostk/shsa`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tm_tp` | String | N | 시간구분 | 0:시작일, 1:기간 | 1 |
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- shrts_qty` | String | N | 공매도량 |  | 20 |
| `- ovr_shrts_qty` | String | N | 누적공매도량 | 설정 기간의 공매도량 합산데이터 | 20 |
| `- trde_wght` | String | N | 매매비중 |  | 20 |
| `- shrts_trde_prica` | String | N | 공매도거래대금 |  | 20 |
| `- shrts_avg_pric` | String | N | 공매도평균가 |  | 20 |

---

## 일별거래상세요청 `ka10015`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- bf_mkrt_trde_qty` | String | N | 장전거래량 |  | 20 |
| `- bf_mkrt_trde_wght` | String | N | 장전거래비중 |  | 20 |
| `- opmr_trde_qty` | String | N | 장중거래량 |  | 20 |
| `- opmr_trde_wght` | String | N | 장중거래비중 |  | 20 |
| `- af_mkrt_trde_qty` | String | N | 장후거래량 |  | 20 |
| `- af_mkrt_trde_wght` | String | N | 장후거래비중 |  | 20 |
| `- tot_3` | String | N | 합계3 |  | 20 |
| `- prid_trde_qty` | String | N | 기간중거래량 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- for_poss` | String | N | 외인보유 |  | 20 |
| `- for_wght` | String | N | 외인비중 |  | 20 |
| `- for_netprps` | String | N | 외인순매수 |  | 20 |
| `- orgn_netprps` | String | N | 기관순매수 |  | 20 |
| `- ind_netprps` | String | N | 개인순매수 |  | 20 |
| `- frgn` | String | N | 외국계 |  | 20 |
| `- crd_remn_rt` | String | N | 신용잔고율 |  | 20 |
| `- prm` | String | N | 프로그램 |  | 20 |
| `- bf_mkrt_trde_prica` | String | N | 장전거래대금 |  | 20 |
| `- bf_mkrt_trde_prica_wght` | String | N | 장전거래대금비중 |  | 20 |
| `- opmr_trde_prica` | String | N | 장중거래대금 |  | 20 |
| `- opmr_trde_prica_wght` | String | N | 장중거래대금비중 |  | 20 |
| `- af_mkrt_trde_prica` | String | N | 장후거래대금 |  | 20 |
| `- af_mkrt_trde_prica_wght` | String | N | 장후거래대금비중 |  | 20 |

---

## 신고저가요청 `ka10016`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `ntl_tp` | String | Y | 신고저구분 | 1:신고가,2:신저가 | 1 |
| `high_low_close_tp` | String | Y | 고저종구분 | 1:고저기준, 2:종가기준 | 1 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기 | 1 |
| `trde_qty_tp` | String | Y | 거래량구분 | 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상 | 5 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `updown_incls` | String | Y | 상하한포함 | 0:미포함, 1:포함 | 1 |
| `dt` | String | Y | 기간 | 5:5일, 10:10일, 20:20일, 60:60일, 250:250일, 250일까지 입력가능 | 3 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- pred_trde_qty_pre_rt` | String | N | 전일거래량대비율 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |

---

## 상하한가요청 `ka10017`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `updown_tp` | String | Y | 상하한구분 | 1:상한, 2:상승, 3:보합, 4: 하한, 5:하락, 6:전일상한, 7:전일하한 | 1 |
| `sort_tp` | String | Y | 정렬구분 | 1:종목코드순, 2:연속횟수순(상위100개), 3:등락률순 | 1 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회,1:관리종목제외, 3:우선주제외, 4:우선주+관리종목제외, 5:증100제외, 6:증100만 보기, 7:증40만 보기, 8:증30만 보기, 9:증20만 보기, 10:우선주+관리종목+환기종목제외 | 1 |
| `trde_qty_tp` | String | Y | 거래량구분 | 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상 | 5 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `trde_gold_tp` | String | Y | 매매금구분 | 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~3천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_infr` | String | N | 종목정보 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- pred_trde_qty` | String | N | 전일거래량 |  | 20 |
| `- sel_req` | String | N | 매도잔량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- buy_req` | String | N | 매수잔량 |  | 20 |
| `- cnt` | String | N | 횟수 |  | 20 |

---

## 고저가근접요청 `ka10018`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `alacc_rt` | String | Y | 근접율 | 05:0.5 10:1.0, 15:1.5, 20:2.0. 25:2.5, 30:3.0 | 2 |
| `mrkt_tp` | String | Y | 시장구분 | 000:전체, 001:코스피, 101:코스닥 | 3 |
| `trde_qty_tp` | String | Y | 거래량구분 | 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상 | 5 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기 | 1 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- tdy_high_pric` | String | N | 당일고가 |  | 20 |
| `- tdy_low_pric` | String | N | 당일저가 |  | 20 |

---

## 가격급등락요청 `ka10019`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `flu_tp` | String | Y | 등락구분 | 1:급등, 2:급락 | 1 |
| `tm_tp` | String | Y | 시간구분 | 1:분전, 2:일전 | 1 |
| `tm` | String | Y | 시간 | 분 혹은 일입력 | 2 |
| `trde_qty_tp` | String | Y | 거래량구분 | 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상 | 4 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기 | 1 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `pric_cnd` | String | Y | 가격조건 | 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~3천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상 | 1 |
| `updown_incls` | String | Y | 상하한포함 | 0:미포함, 1:포함 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_cls` | String | N | 종목분류 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- base_pric` | String | N | 기준가 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- base_pre` | String | N | 기준대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- jmp_rt` | String | N | 급등률 |  | 20 |

---

## 호가잔량상위요청 `ka10020`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sort_tp` | String | Y | 정렬구분 | 1:순매수잔량순, 2:순매도잔량순, 3:매수비율순, 4:매도비율순 | 1 |
| `trde_qty_tp` | String | Y | 거래량구분 | 0000:장시작전(0주이상), 0010:만주이상, 0050:5만주이상, 00100:10만주이상 | 4 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기 | 1 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- tot_sel_req` | String | N | 총매도잔량 |  | 20 |
| `- tot_buy_req` | String | N | 총매수잔량 |  | 20 |
| `- netprps_req` | String | N | 순매수잔량 |  | 20 |
| `- buy_rt` | String | N | 매수비율 |  | 20 |

---

## 호가잔량급증요청 `ka10021`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_tp` | String | Y | 매매구분 | 1:매수잔량, 2:매도잔량 | 1 |
| `sort_tp` | String | Y | 정렬구분 | 1:급증량, 2:급증률 | 1 |
| `tm_tp` | String | Y | 시간구분 | 분 입력 | 2 |
| `trde_qty_tp` | String | Y | 거래량구분 | 1:천주이상, 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상 | 4 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- int` | String | N | 기준률 |  | 20 |
| `- now` | String | N | 현재 |  | 20 |
| `- sdnin_qty` | String | N | 급증수량 |  | 20 |
| `- sdnin_rt` | String | N | 급증률 |  | 20 |
| `- tot_buy_qty` | String | N | 총매수량 |  | 20 |

---

## 잔량율급증요청 `ka10022`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `rt_tp` | String | Y | 비율구분 | 1:매수/매도비율, 2:매도/매수비율 | 1 |
| `tm_tp` | String | Y | 시간구분 | 분 입력 | 2 |
| `trde_qty_tp` | String | Y | 거래량구분 | 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상 | 1 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- int` | String | N | 기준률 |  | 20 |
| `- now_rt` | String | N | 현재비율 |  | 20 |
| `- sdnin_rt` | String | N | 급증률 |  | 20 |
| `- tot_sel_req` | String | N | 총매도잔량 |  | 20 |
| `- tot_buy_req` | String | N | 총매수잔량 |  | 20 |

---

## 거래량급증요청 `ka10023`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sort_tp` | String | Y | 정렬구분 | 1:급증량, 2:급증률, 3:급감량, 4:급감률 | 1 |
| `tm_tp` | String | Y | 시간구분 | 1:분, 2:전일 | 1 |
| `trde_qty_tp` | String | Y | 거래량구분 | 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상 | 1 |
| `tm` | String | N | 시간 | 분 입력 | 2 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 3:우선주제외, 11:정리매매종목제외, 4:관리종목,우선주제외, 5:증100제외, 6:증100만보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 17:ETN제외, 14:ETF제외, 18:ETF+ETN제외, 15:스팩제외, 20:ETF+ETN+스팩제외 | 1 |
| `pric_tp` | String | Y | 가격구분 | 0:전체조회, 2:5만원이상, 5:1만원이상, 6:5천원이상, 8:1천원이상, 9:10만원이상 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- prev_trde_qty` | String | N | 이전거래량 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- sdnin_qty` | String | N | 급증량 |  | 20 |
| `- sdnin_rt` | String | N | 급증률 |  | 20 |

---

## 거래량갱신요청 `ka10024`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cycle_tp` | String | Y | 주기구분 | 5:5일, 10:10일, 20:20일, 60:60일, 250:250일 | 1 |
| `trde_qty_tp` | String | Y | 거래량구분 | 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- prev_trde_qty` | String | N | 이전거래량 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |

---

## 매물대집중요청 `ka10025`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `prps_cnctr_rt` | String | Y | 매물집중비율 | 0~100 입력 | 3 |
| `cur_prc_entry` | String | Y | 현재가진입 | 0:현재가 매물대 진입 포함안함, 1:현재가 매물대 진입포함 | 1 |
| `prpscnt` | String | Y | 매물대수 | 숫자입력 | 2 |
| `cycle_tp` | String | Y | 주기구분 | 50:50일, 100:100일, 150:150일, 200:200일, 250:250일, 300:300일 | 2 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- pric_strt` | String | N | 가격대시작 |  | 20 |
| `- pric_end` | String | N | 가격대끝 |  | 20 |
| `- prps_qty` | String | N | 매물량 |  | 20 |
| `- prps_rt` | String | N | 매물비 |  | 20 |

---

## 고저PER요청 `ka10026`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- per` | String | N | PER |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |

---

## 전일대비등락률상위요청 `ka10027`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sort_tp` | String | Y | 정렬구분 | 1:상승률, 2:상승폭, 3:하락률, 4:하락폭, 5:보합 | 1 |
| `trde_qty_cnd` | String | Y | 거래량조건 | 0000:전체조회, 0010:만주이상, 0050:5만주이상, 0100:10만주이상, 0150:15만주이상, 0200:20만주이상, 0300:30만주이상, 0500:50만주이상, 1000:백만주이상 | 5 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 4:우선주+관리주제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 11:정리매매종목제외, 12:증50만보기, 13:증60만보기, 14:ETF제외, 15:스펙제외, 16:ETF+ETN제외 | 2 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `updown_incls` | String | Y | 상하한포함 | 0:불 포함, 1:포함 | 2 |
| `pric_cnd` | String | Y | 가격조건 | 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~5천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상, 10: 1만원미만 | 2 |
| `trde_prica_cnd` | String | Y | 거래대금조건 | 0:전체조회, 3:3천만원이상, 5:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상 | 4 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cls` | String | N | 종목분류 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- sel_req` | String | N | 매도잔량 |  | 20 |
| `- buy_req` | String | N | 매수잔량 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- cnt` | String | N | 횟수 |  | 20 |

---

## 시가대비등락률요청 `ka10028`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_qty_cnd` | String | Y | 거래량조건 | 0000:전체조회, 0010:만주이상, 0050:5만주이상, 0100:10만주이상, 0500:50만주이상, 1000:백만주이상 | 4 |
| `mrkt_tp` | String | Y | 시장구분 | 000:전체, 001:코스피, 101:코스닥 | 3 |
| `updown_incls` | String | Y | 상하한포함 | 0:불 포함, 1:포함 | 1 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 4:우선주+관리주제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기 | 2 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `trde_prica_cnd` | String | Y | 거래대금조건 | 0:전체조회, 3:3천만원이상, 5:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상 | 4 |
| `flu_cnd` | String | Y | 등락조건 | 1:상위, 2:하위 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- open_pric_pre` | String | N | 시가대비 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |

---

## 예상체결등락률상위요청 `ka10029`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sort_tp` | String | Y | 정렬구분 | 1:상승률, 2:상승폭, 3:보합, 4:하락률, 5:하락폭, 6:체결량, 7:상한, 8:하한 | 1 |
| `trde_qty_cnd` | String | Y | 거래량조건 | 0:전체조회, 1;천주이상, 3:3천주, 5:5천주, 10:만주이상, 50:5만주이상, 100:10만주이상 | 5 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 3:우선주제외, 4:관리종목,우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 11:정리매매종목제외, 12:증50만보기, 13:증60만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외 | 2 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 5:신용한도초과제외, 7:신용융자E군, 8:신용대주, 9:신용융자전체 | 1 |
| `pric_cnd` | String | Y | 가격조건 | 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~5천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상, 10:1만원미만 | 2 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- exp_cntr_pric` | String | N | 예상체결가 |  | 20 |
| `- base_pric` | String | N | 기준가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- exp_cntr_qty` | String | N | 예상체결량 |  | 20 |
| `- sel_req` | String | N | 매도잔량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- buy_req` | String | N | 매수잔량 |  | 20 |

---

## 당일거래량상위요청 `ka10030`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sort_tp` | String | Y | 정렬구분 | 1:거래량, 2:거래회전율, 3:거래대금 | 1 |
| `mang_stk_incls` | String | Y | 관리종목포함 | 0:관리종목 포함, 1:관리종목 미포함, 3:우선주제외, 11:정리매매종목제외, 4:관리종목, 우선주제외, 5:증100제외, 6:증100마나보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외 | 1 |
| `crd_tp` | String | Y | 신용구분 | 0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 8:신용대주 | 1 |
| `trde_qty_tp` | String | Y | 거래량구분 | 0:전체조회, 5:5천주이상, 10:1만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:500만주이상, 1000:백만주이상 | 1 |
| `pric_tp` | String | Y | 가격구분 | 0:전체조회, 1:1천원미만, 2:1천원이상, 3:1천원~2천원, 4:2천원~5천원, 5:5천원이상, 6:5천원~1만원, 10:1만원미만, 7:1만원이상, 8:5만원이상, 9:10만원이상 | 1 |
| `trde_prica_tp` | String | Y | 거래대금구분 | 0:전체조회, 1:1천만원이상, 3:3천만원이상, 4:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상 | 1 |
| `mrkt_open_tp` | String | Y | 장운영구분 | 0:전체조회, 1:장중, 2:장전시간외, 3:장후시간외 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- pred_rt` | String | N | 전일비 |  | 20 |
| `- trde_tern_rt` | String | N | 거래회전율 |  | 20 |
| `- trde_amt` | String | N | 거래금액 |  | 20 |
| `- opmr_trde_qty` | String | N | 장중거래량 |  | 20 |
| `- opmr_pred_rt` | String | N | 장중전일비 |  | 20 |
| `- opmr_trde_rt` | String | N | 장중거래회전율 |  | 20 |
| `- opmr_trde_amt` | String | N | 장중거래금액 |  | 20 |
| `- af_mkrt_trde_qty` | String | N | 장후거래량 |  | 20 |
| `- af_mkrt_pred_rt` | String | N | 장후전일비 |  | 20 |
| `- af_mkrt_trde_rt` | String | N | 장후거래회전율 |  | 20 |
| `- af_mkrt_trde_amt` | String | N | 장후거래금액 |  | 20 |
| `- bf_mkrt_trde_qty` | String | N | 장전거래량 |  | 20 |
| `- bf_mkrt_pred_rt` | String | N | 장전전일비 |  | 20 |
| `- bf_mkrt_trde_rt` | String | N | 장전거래회전율 |  | 20 |
| `- bf_mkrt_trde_amt` | String | N | 장전거래금액 |  | 20 |

---

## 전일거래량상위요청 `ka10031`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `qry_tp` | String | Y | 조회구분 | 1:전일거래량 상위100종목, 2:전일거래대금 상위100종목 | 1 |
| `rank_strt` | String | Y | 순위시작 | 0 ~ 100 값 중에  조회를 원하는 순위 시작값 | 3 |
| `rank_end` | String | Y | 순위끝 | 0 ~ 100 값 중에  조회를 원하는 순위 끝값 | 3 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |

---

## 거래대금상위요청 `ka10032`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `mang_stk_incls` | String | Y | 관리종목포함 | 0:관리종목 미포함, 1:관리종목 포함 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- now_rank` | String | N | 현재순위 |  | 20 |
| `- pred_rank` | String | N | 전일순위 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- pred_trde_qty` | String | N | 전일거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## 신용비율상위요청 `ka10033`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_qty_tp` | String | Y | 거래량구분 | 0:전체조회, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상 | 3 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기 | 1 |
| `updown_incls` | String | Y | 상하한포함 | 0:상하한 미포함, 1:상하한포함 | 1 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_infr` | String | N | 종목정보 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- crd_rt` | String | N | 신용비율 |  | 20 |
| `- sel_req` | String | N | 매도잔량 |  | 20 |
| `- buy_req` | String | N | 매수잔량 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |

---

## 외인기간별매매상위요청 `ka10034`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_tp` | String | Y | 매매구분 | 1:순매도, 2:순매수, 3:순매매 | 1 |
| `dt` | String | Y | 기간 | 0:당일, 1:전일, 5:5일, 10;10일, 20:20일, 60:60일 | 2 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- netprps_qty` | String | N | 순매수량 |  | 20 |
| `- gain_pos_stkcnt` | String | N | 취득가능주식수 |  | 20 |

---

## 외인연속순매매상위요청 `ka10035`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_tp` | String | Y | 매매구분 | 1:연속순매도, 2:연속순매수 | 1 |
| `base_dt_tp` | String | Y | 기준일구분 | 0:당일기준, 1:전일기준 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- dm1` | String | N | D-1 |  | 20 |
| `- dm2` | String | N | D-2 |  | 20 |
| `- dm3` | String | N | D-3 |  | 20 |
| `- tot` | String | N | 합계 |  | 20 |
| `- limit_exh_rt` | String | N | 한도소진율 |  | 20 |
| `- pred_pre_1` | String | N | 전일대비1 |  | 20 |
| `- pred_pre_2` | String | N | 전일대비2 |  | 20 |
| `- pred_pre_3` | String | N | 전일대비3 |  | 20 |

---

## 외인한도소진율증가상위 `ka10036`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dt` | String | Y | 기간 | 0:당일, 1:전일, 5:5일, 10;10일, 20:20일, 60:60일 | 2 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- poss_stkcnt` | String | N | 보유주식수 |  | 20 |
| `- gain_pos_stkcnt` | String | N | 취득가능주식수 |  | 20 |
| `- base_limit_exh_rt` | String | N | 기준한도소진율 |  | 20 |
| `- limit_exh_rt` | String | N | 한도소진율 |  | 20 |
| `- exh_rt_incrs` | String | N | 소진율증가 |  | 20 |

---

## 외국계창구매매상위요청 `ka10037`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dt` | String | Y | 기간 | 0:당일, 1:전일, 5:5일, 10;10일, 20:20일, 60:60일 | 2 |
| `trde_tp` | String | Y | 매매구분 | 1:순매수, 2:순매도, 3:매수, 4:매도 | 1 |
| `sort_tp` | String | Y | 정렬구분 | 1:금액, 2:수량 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- sel_trde_qty` | String | N | 매도거래량 |  | 20 |
| `- buy_trde_qty` | String | N | 매수거래량 |  | 20 |
| `- netprps_trde_qty` | String | N | 순매수거래량 |  | 20 |
| `- netprps_prica` | String | N | 순매수대금 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## 종목별증권사순위요청 `ka10038`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD
(연도4자리, 월 2자리, 일 2자리 형식) | 8 |
| `end_dt` | String | Y | 종료일자 | YYYYMMDD
(연도4자리, 월 2자리, 일 2자리 형식) | 8 |
| `qry_tp` | String | Y | 조회구분 | 1:순매도순위정렬, 2:순매수순위정렬 | 1 |
| `dt` | String | Y | 기간 | 1:전일, 4:5일, 9:10일, 19:20일, 39:40일, 59:60일, 119:120일 | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `rank_2` | String | N | 순위2 |  | 20 |
| `rank_3` | String | N | 순위3 |  | 20 |
| `prid_trde_qty` | String | N | 기간중거래량 |  | 20 |
| `stk_sec_rank` | LIST | N | 종목별증권사순위 |  |  |
| `- rank` | String | N | 순위 |  | 20 |
| `- mmcm_nm` | String | N | 회원사명 |  | 20 |
| `- buy_qty` | String | N | 매수수량 |  | 20 |
| `- sell_qty` | String | N | 매도수량 |  | 20 |
| `- acc_netprps_qty` | String | N | 누적순매수수량 |  | 20 |

---

## 증권사별매매상위요청 `ka10039`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_qty_tp` | String | Y | 거래량구분 | 0:전체, 5:5000주, 10:1만주, 50:5만주, 100:10만주, 500:50만주, 1000: 100만주 | 4 |
| `trde_tp` | String | Y | 매매구분 | 1:순매수, 2:순매도 | 2 |
| `dt` | String | Y | 기간 | 1:전일, 5:5일, 10:10일, 60:60일 | 2 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- prid_stkpc_flu` | String | N | 기간중주가등락 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- prid_trde_qty` | String | N | 기간중거래량 |  | 20 |
| `- netprps` | String | N | 순매수 |  | 20 |
| `- buy_trde_qty` | String | N | 매수거래량 |  | 20 |
| `- sel_trde_qty` | String | N | 매도거래량 |  | 20 |
| `- netprps_amt` | String | N | 순매수금액 |  | 20 |
| `- buy_amt` | String | N | 매수금액 |  | 20 |
| `- sell_amt` | String | N | 매도금액 |  | 20 |

---

## 당일주요거래원요청 `ka10040`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sel_trde_ori_qty_1` | String | N | 매도거래원수량1 |  |  |
| `sel_trde_ori_1` | String | N | 매도거래원1 |  |  |
| `sel_trde_ori_cd_1` | String | N | 매도거래원코드1 |  |  |
| `buy_trde_ori_1` | String | N | 매수거래원1 |  |  |
| `buy_trde_ori_cd_1` | String | N | 매수거래원코드1 |  |  |
| `buy_trde_ori_qty_1` | String | N | 매수거래원수량1 |  |  |
| `buy_trde_ori_irds_1` | String | N | 매수거래원별증감1 |  |  |
| `sel_trde_ori_irds_2` | String | N | 매도거래원별증감2 |  |  |
| `sel_trde_ori_qty_2` | String | N | 매도거래원수량2 |  |  |
| `sel_trde_ori_2` | String | N | 매도거래원2 |  |  |
| `sel_trde_ori_cd_2` | String | N | 매도거래원코드2 |  |  |
| `buy_trde_ori_2` | String | N | 매수거래원2 |  |  |
| `buy_trde_ori_cd_2` | String | N | 매수거래원코드2 |  |  |
| `buy_trde_ori_qty_2` | String | N | 매수거래원수량2 |  |  |
| `buy_trde_ori_irds_2` | String | N | 매수거래원별증감2 |  |  |
| `sel_trde_ori_irds_3` | String | N | 매도거래원별증감3 |  |  |
| `sel_trde_ori_qty_3` | String | N | 매도거래원수량3 |  |  |
| `sel_trde_ori_3` | String | N | 매도거래원3 |  |  |
| `sel_trde_ori_cd_3` | String | N | 매도거래원코드3 |  |  |
| `buy_trde_ori_3` | String | N | 매수거래원3 |  |  |
| `buy_trde_ori_cd_3` | String | N | 매수거래원코드3 |  |  |
| `buy_trde_ori_qty_3` | String | N | 매수거래원수량3 |  |  |
| `buy_trde_ori_irds_3` | String | N | 매수거래원별증감3 |  |  |
| `sel_trde_ori_irds_4` | String | N | 매도거래원별증감4 |  |  |
| `sel_trde_ori_qty_4` | String | N | 매도거래원수량4 |  |  |
| `sel_trde_ori_4` | String | N | 매도거래원4 |  |  |
| `sel_trde_ori_cd_4` | String | N | 매도거래원코드4 |  |  |
| `buy_trde_ori_4` | String | N | 매수거래원4 |  |  |
| `buy_trde_ori_cd_4` | String | N | 매수거래원코드4 |  |  |
| `buy_trde_ori_qty_4` | String | N | 매수거래원수량4 |  |  |
| `buy_trde_ori_irds_4` | String | N | 매수거래원별증감4 |  |  |
| `sel_trde_ori_irds_5` | String | N | 매도거래원별증감5 |  |  |
| `sel_trde_ori_qty_5` | String | N | 매도거래원수량5 |  |  |
| `sel_trde_ori_5` | String | N | 매도거래원5 |  |  |
| `sel_trde_ori_cd_5` | String | N | 매도거래원코드5 |  |  |
| `buy_trde_ori_5` | String | N | 매수거래원5 |  |  |
| `buy_trde_ori_cd_5` | String | N | 매수거래원코드5 |  |  |
| `buy_trde_ori_qty_5` | String | N | 매수거래원수량5 |  |  |
| `buy_trde_ori_irds_5` | String | N | 매수거래원별증감5 |  |  |
| `frgn_sel_prsm_sum_chang` | String | N | 외국계매도추정합변동 |  |  |
| `frgn_sel_prsm_sum` | String | N | 외국계매도추정합 |  |  |
| `frgn_buy_prsm_sum` | String | N | 외국계매수추정합 |  |  |
| `frgn_buy_prsm_sum_chang` | String | N | 외국계매수추정합변동 |  |  |
| `tdy_main_trde_ori` | LIST | N | 당일주요거래원 |  |  |
| `- sel_scesn_tm` | String | N | 매도이탈시간 |  | 20 |
| `- sell_qty` | String | N | 매도수량 |  | 20 |
| `- sel_upper_scesn_ori` | String | N | 매도상위이탈원 |  | 20 |
| `- buy_scesn_tm` | String | N | 매수이탈시간 |  | 20 |
| `- buy_qty` | String | N | 매수수량 |  | 20 |
| `- buy_upper_scesn_ori` | String | N | 매수상위이탈원 |  | 20 |
| `- qry_dt` | String | N | 조회일자 |  | 20 |
| `- qry_tm` | String | N | 조회시간 |  | 20 |

---

## 순매수거래원순위요청 `ka10042`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | N | 시작일자 | YYYYMMDD
(연도4자리, 월 2자리, 일 2자리 형식) | 8 |
| `end_dt` | String | N | 종료일자 | YYYYMMDD
(연도4자리, 월 2자리, 일 2자리 형식) | 8 |
| `qry_dt_tp` | String | Y | 조회기간구분 | 0:기간으로 조회, 1:시작일자, 종료일자로 조회 | 1 |
| `pot_tp` | String | Y | 시점구분 | 0:당일, 1:전일 | 1 |
| `dt` | String | N | 기간 | 5:5일, 10:10일, 20:20일, 40:40일, 60:60일, 120:120일 | 4 |
| `sort_base` | String | Y | 정렬기준 | 1:종가순, 2:날짜순 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- mmcm_cd` | String | N | 회원사코드 |  | 20 |
| `- mmcm_nm` | String | N | 회원사명 |  | 20 |

---

## 거래원매물대분석요청 `ka10043`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |
| `qry_dt_tp` | String | Y | 조회기간구분 | 0:기간으로 조회, 1:시작일자, 종료일자로 조회 | 1 |
| `pot_tp` | String | Y | 시점구분 | 0:당일, 1:전일 | 1 |
| `dt` | String | Y | 기간 | 5:5일, 10:10일, 20:20일, 40:40일, 60:60일, 120:120일 | 4 |
| `sort_base` | String | Y | 정렬기준 | 1:종가순, 2:날짜순 | 1 |
| `mmcm_cd` | String | Y | 회원사코드 | 회원사 코드는 ka10102 조회 | 3 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- sel_qty` | String | N | 매도량 |  | 20 |
| `- buy_qty` | String | N | 매수량 |  | 20 |
| `- netprps_qty` | String | N | 순매수수량 |  | 20 |
| `- trde_qty_sum` | String | N | 거래량합 |  | 20 |
| `- trde_wght` | String | N | 거래비중 |  | 20 |

---

## 일별기관매매종목요청 `ka10044`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |
| `trde_tp` | String | Y | 매매구분 | 1:순매도, 2:순매수 | 1 |
| `mrkt_tp` | String | Y | 시장구분 | 001:코스피, 101:코스닥 | 3 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- netprps_qty` | String | N | 순매수수량 |  | 20 |
| `- netprps_amt` | String | N | 순매수금액 |  | 20 |

---

## 종목별기관매매추이요청 `ka10045`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |
| `orgn_prsm_unp_tp` | String | Y | 기관추정단가구분 | 1:매수단가, 2:매도단가 | 1 |
| `for_prsm_unp_tp` | String | Y | 외인추정단가구분 | 1:매수단가, 2:매도단가 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `for_prsm_avg_pric` | String | N | 외인추정평균가 |  |  |
| `stk_orgn_trde_trnsn` | LIST | N | 종목별기관매매추이 |  |  |
| `- dt` | String | N | 일자 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- orgn_dt_acc` | String | N | 기관기간누적 |  | 20 |
| `- orgn_daly_nettrde_qty` | String | N | 기관일별순매매수량 |  | 20 |
| `- for_dt_acc` | String | N | 외인기간누적 |  | 20 |
| `- for_daly_nettrde_qty` | String | N | 외인일별순매매수량 |  | 20 |
| `- limit_exh_rt` | String | N | 한도소진율 |  | 20 |

---

## 체결강도추이시간별요청 `ka10046`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- cntr_str_5min` | String | N | 체결강도5분 |  | 20 |
| `- cntr_str_20min` | String | N | 체결강도20분 |  | 20 |
| `- cntr_str_60min` | String | N | 체결강도60분 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 |  | 20 |

---

## 체결강도추이일별요청 `ka10047`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- cntr_str_5min` | String | N | 체결강도5일 |  | 20 |
| `- cntr_str_20min` | String | N | 체결강도20일 |  | 20 |
| `- cntr_str_60min` | String | N | 체결강도60일 |  | 20 |

---

## ELW일별민감도지표요청 `ka10048`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- iv` | String | N | IV |  | 20 |
| `- delta` | String | N | 델타 |  | 20 |
| `- gam` | String | N | 감마 |  | 20 |
| `- theta` | String | N | 쎄타 |  | 20 |
| `- vega` | String | N | 베가 |  | 20 |
| `- law` | String | N | 로 |  | 20 |
| `- lp` | String | N | LP |  | 20 |

---

## ELW민감도지표요청 `ka10050`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- elwtheory_pric` | String | N | ELW이론가 |  | 20 |
| `- iv` | String | N | IV |  | 20 |
| `- delta` | String | N | 델타 |  | 20 |
| `- gam` | String | N | 감마 |  | 20 |
| `- theta` | String | N | 쎄타 |  | 20 |
| `- vega` | String | N | 베가 |  | 20 |
| `- law` | String | N | 로 |  | 20 |
| `- lp` | String | N | LP |  | 20 |

---

## 업종별투자자순매수요청 `ka10051`

**Method**: `POST`  
**URL**: `/api/dostk/sect`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 금액:0, 수량:1 | 1 |
| `base_dt` | String | N | 기준일자 | YYYYMMDD | 8 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- inds_cd` | String | N | 업종코드 |  | 20 |
| `- inds_nm` | String | N | 업종명 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_smbol` | String | N | 대비부호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- sc_netprps` | String | N | 증권순매수 |  | 20 |
| `- insrnc_netprps` | String | N | 보험순매수 |  | 20 |
| `- invtrt_netprps` | String | N | 투신순매수 |  | 20 |
| `- bank_netprps` | String | N | 은행순매수 |  | 20 |
| `- jnsinkm_netprps` | String | N | 종신금순매수 |  | 20 |
| `- endw_netprps` | String | N | 기금순매수 |  | 20 |
| `- etc_corp_netprps` | String | N | 기타법인순매수 |  | 20 |
| `- ind_netprps` | String | N | 개인순매수 |  | 20 |
| `- frgnr_netprps` | String | N | 외국인순매수 |  | 20 |
| `- native_trmt_frgnr_netprps` | String | N | 내국인대우외국인순매수 |  | 20 |
| `- natn_netprps` | String | N | 국가순매수 |  | 20 |
| `- samo_fund_netprps` | String | N | 사모펀드순매수 |  | 20 |
| `- orgn_netprps` | String | N | 기관계순매수 |  | 20 |

---

## 거래원순간거래량요청 `ka10052`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | N | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 20 |
| `mrkt_tp` | String | Y | 시장구분 | 0:전체, 1:코스피, 2:코스닥, 3:종목 | 1 |
| `qty_tp` | String | Y | 수량구분 | 0:전체, 1:1000주, 2:2000주, 3:, 5:, 10:10000주, 30: 30000주, 50: 50000주, 100: 100000주 | 3 |
| `pric_tp` | String | Y | 가격구분 | 0:전체, 1:1천원 미만, 8:1천원 이상, 2:1천원 ~ 2천원, 3:2천원 ~ 5천원, 4:5천원 ~ 1만원, 5:1만원 이상 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- tm` | String | N | 시간 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 20 |
| `- trde_ori_nm` | String | N | 거래원명 |  | 20 |
| `- tp` | String | N | 구분 |  | 20 |
| `- mont_trde_qty` | String | N | 순간거래량 |  | 20 |
| `- acc_netprps` | String | N | 누적순매수 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |

---

## 당일상위이탈원요청 `ka10053`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- sel_scesn_tm` | String | N | 매도이탈시간 |  | 20 |
| `- sell_qty` | String | N | 매도수량 |  | 20 |
| `- sel_upper_scesn_ori` | String | N | 매도상위이탈원 |  | 20 |
| `- buy_scesn_tm` | String | N | 매수이탈시간 |  | 20 |
| `- buy_qty` | String | N | 매수수량 |  | 20 |
| `- buy_upper_scesn_ori` | String | N | 매수상위이탈원 |  | 20 |
| `- qry_dt` | String | N | 조회일자 |  | 20 |
| `- qry_tm` | String | N | 조회시간 |  | 20 |

---

## 변동성완화장치발동종목요청 `ka10054`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `bf_mkrt_tp` | String | Y | 장전구분 | 0:전체, 1:정규시장,2:시간외단일가 | 1 |
| `stk_cd` | String | N | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL)
 공백입력시 시장구분으로 설정한 전체종목조회 | 20 |
| `motn_tp` | String | Y | 발동구분 | 0:전체, 1:정적VI, 2:동적VI, 3:동적VI + 정적VI | 1 |
| `skip_stk` | String | Y | 제외종목 | 전종목포함 조회시 9개 0으로 설정(000000000),전종목제외 조회시 9개 1으로 설정(111111111),9개 종목조회여부를 조회포함(0), 조회제외(1)로 설정하며 종목순서는 우선주,관리종목,투자경고/위험,투자주의,환기종목,단기과열종목,증거금100%,ETF,ETN가 됨.우선주만 조회시"011111111"", 관리종목만 조회시 ""101111111"" 설정" | 9 |
| `trde_qty_tp` | String | Y | 거래량구분 | 0:사용안함, 1:사용 | 1 |
| `min_trde_qty` | String | Y | 최소거래량 | 0 주 이상, 거래량구분이 1일때만 입력(공백허용) | 12 |
| `max_trde_qty` | String | Y | 최대거래량 | 100000000 주 이하, 거래량구분이 1일때만 입력(공백허용) | 12 |
| `trde_prica_tp` | String | Y | 거래대금구분 | 0:사용안함, 1:사용 | 1 |
| `min_trde_prica` | String | Y | 최소거래대금 | 0 백만원 이상, 거래대금구분 1일때만 입력(공백허용) | 10 |
| `max_trde_prica` | String | Y | 최대거래대금 | 100000000 백만원 이하, 거래대금구분 1일때만 입력(공백허용) | 10 |
| `motn_drc` | String | Y | 발동방향 | 0:전체, 1:상승, 2:하락 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- motn_pric` | String | N | 발동가격 |  | 20 |
| `- dynm_dispty_rt` | String | N | 동적괴리율 |  | 20 |
| `- trde_cntr_proc_time` | String | N | 매매체결처리시각 |  | 20 |
| `- virelis_time` | String | N | VI해제시각 |  | 20 |
| `- viaplc_tp` | String | N | VI적용구분 |  | 20 |
| `- dynm_stdpc` | String | N | 동적기준가격 |  | 20 |
| `- static_stdpc` | String | N | 정적기준가격 |  | 20 |
| `- static_dispty_rt` | String | N | 정적괴리율 |  | 20 |
| `- open_pric_pre_flu_rt` | String | N | 시가대비등락률 |  | 20 |
| `- vimotn_cnt` | String | N | VI발동횟수 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 |  | 20 |

---

## 당일전일체결량요청 `ka10055`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tdy_pred` | String | Y | 당일전일 | 1:당일, 2:전일 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |

---

## 투자자별일별매매종목요청 `ka10058`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |
| `trde_tp` | String | Y | 매매구분 | 순매도:1, 순매수:2 | 1 |
| `mrkt_tp` | String | Y | 시장구분 | 001:코스피, 101:코스닥 | 3 |
| `invsr_tp` | String | Y | 투자자구분 | 8000:개인, 9000:외국인, 1000:금융투자, 3000:투신, 5000:기타금융, 4000:은행, 2000:보험, 6000:연기금, 7000:국가, 7100:기타법인, 9999:기관계 | 4 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- netslmt_qty` | String | N | 순매도수량 |  | 20 |
| `- netslmt_amt` | String | N | 순매도금액 |  | 20 |
| `- prsm_avg_pric` | String | N | 추정평균가 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- avg_pric_pre` | String | N | 평균가대비 |  | 20 |
| `- pre_rt` | String | N | 대비율 |  | 20 |
| `- dt_trde_qty` | String | N | 기간거래량 |  | 20 |

---

## 종목별투자자기관별요청 `ka10059`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 20 |
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액, 2:수량 | 1 |
| `trde_tp` | String | Y | 매매구분 | 0:순매수, 1:매수, 2:매도 | 1 |
| `unit_tp` | String | Y | 단위구분 | 1000:천주, 1:단주 | 4 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 | 우측 2자리 소수점자리수 | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- ind_invsr` | String | N | 개인투자자 |  | 20 |
| `- frgnr_invsr` | String | N | 외국인투자자 |  | 20 |
| `- orgn` | String | N | 기관계 |  | 20 |
| `- fnnc_invt` | String | N | 금융투자 |  | 20 |
| `- insrnc` | String | N | 보험 |  | 20 |
| `- invtrt` | String | N | 투신 |  | 20 |
| `- etc_fnnc` | String | N | 기타금융 |  | 20 |
| `- bank` | String | N | 은행 |  | 20 |
| `- penfnd_etc` | String | N | 연기금등 |  | 20 |
| `- samo_fund` | String | N | 사모펀드 |  | 20 |
| `- natn` | String | N | 국가 |  | 20 |
| `- etc_corp` | String | N | 기타법인 |  | 20 |
| `- natfor` | String | N | 내외국인 |  | 20 |

---

## 종목별투자자기관별차트요청 `ka10060`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 20 |
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액, 2:수량 | 1 |
| `trde_tp` | String | Y | 매매구분 | 0:순매수, 1:매수, 2:매도 | 1 |
| `unit_tp` | String | Y | 단위구분 | 1000:천주, 1:단주 | 4 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- ind_invsr` | String | N | 개인투자자 |  | 20 |
| `- frgnr_invsr` | String | N | 외국인투자자 |  | 20 |
| `- orgn` | String | N | 기관계 |  | 20 |
| `- fnnc_invt` | String | N | 금융투자 |  | 20 |
| `- insrnc` | String | N | 보험 |  | 20 |
| `- invtrt` | String | N | 투신 |  | 20 |
| `- etc_fnnc` | String | N | 기타금융 |  | 20 |
| `- bank` | String | N | 은행 |  | 20 |
| `- penfnd_etc` | String | N | 연기금등 |  | 20 |
| `- samo_fund` | String | N | 사모펀드 |  | 20 |
| `- natn` | String | N | 국가 |  | 20 |
| `- etc_corp` | String | N | 기타법인 |  | 20 |
| `- natfor` | String | N | 내외국인 |  | 20 |

---

## 종목별투자자기관별합계요청 `ka10061`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액, 2:수량 | 1 |
| `trde_tp` | String | Y | 매매구분 | 0:순매수 | 1 |
| `unit_tp` | String | Y | 단위구분 | 1000:천주, 1:단주 | 4 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- ind_invsr` | String | N | 개인투자자 |  | 20 |
| `- frgnr_invsr` | String | N | 외국인투자자 |  | 20 |
| `- orgn` | String | N | 기관계 |  | 20 |
| `- fnnc_invt` | String | N | 금융투자 |  | 20 |
| `- insrnc` | String | N | 보험 |  | 20 |
| `- invtrt` | String | N | 투신 |  | 20 |
| `- etc_fnnc` | String | N | 기타금융 |  | 20 |
| `- bank` | String | N | 은행 |  | 20 |
| `- penfnd_etc` | String | N | 연기금등 |  | 20 |
| `- samo_fund` | String | N | 사모펀드 |  | 20 |
| `- natn` | String | N | 국가 |  | 20 |
| `- etc_corp` | String | N | 기타법인 |  | 20 |
| `- natfor` | String | N | 내외국인 |  | 20 |

---

## 동일순매매순위요청 `ka10062`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | N | 종료일자 | YYYYMMDD
(연도4자리, 월 2자리, 일 2자리 형식) | 8 |
| `mrkt_tp` | String | Y | 시장구분 | 000:전체, 001: 코스피, 101:코스닥 | 3 |
| `trde_tp` | String | Y | 매매구분 | 1:순매수, 2:순매도 | 1 |
| `sort_cnd` | String | Y | 정렬조건 | 1:수량, 2:금액 | 1 |
| `unit_tp` | String | Y | 단위구분 | 1:단주, 1000:천주 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- orgn_nettrde_qty` | String | N | 기관순매매수량 |  | 20 |
| `- orgn_nettrde_amt` | String | N | 기관순매매금액 |  | 20 |
| `- orgn_nettrde_avg_pric` | String | N | 기관순매매평균가 |  | 20 |
| `- for_nettrde_qty` | String | N | 외인순매매수량 |  | 20 |
| `- for_nettrde_amt` | String | N | 외인순매매금액 |  | 20 |
| `- for_nettrde_avg_pric` | String | N | 외인순매매평균가 |  | 20 |
| `- nettrde_qty` | String | N | 순매매수량 |  | 20 |
| `- nettrde_amt` | String | N | 순매매금액 |  | 20 |

---

## 장중투자자별매매요청 `ka10063`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1: 금액&수량 | 1 |
| `invsr` | String | Y | 투자자별 | 6:외국인, 7:기관계, 1:투신, 0:보험, 2:은행, 3:연기금, 4:국가, 5:기타법인 | 1 |
| `frgn_all` | String | Y | 외국계전체 | 1:체크, 0:미체크 | 1 |
| `smtm_netprps_tp` | String | Y | 동시순매수구분 | 1:체크, 0:미체크 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- netprps_amt` | String | N | 순매수금액 |  | 20 |
| `- prev_netprps_amt` | String | N | 이전순매수금액 |  | 20 |
| `- buy_amt` | String | N | 매수금액 |  | 20 |
| `- netprps_amt_irds` | String | N | 순매수금액증감 |  | 20 |
| `- buy_amt_irds` | String | N | 매수금액증감 |  | 20 |
| `- sell_amt` | String | N | 매도금액 |  | 20 |
| `- sell_amt_irds` | String | N | 매도금액증감 |  | 20 |
| `- netprps_qty` | String | N | 순매수수량 |  | 20 |
| `- prev_pot_netprps_qty` | String | N | 이전시점순매수수량 |  | 20 |
| `- netprps_irds` | String | N | 순매수증감 |  | 20 |
| `- buy_qty` | String | N | 매수수량 |  | 20 |
| `- buy_qty_irds` | String | N | 매수수량증감 |  | 20 |
| `- sell_qty` | String | N | 매도수량 |  | 20 |
| `- sell_qty_irds` | String | N | 매도수량증감 |  | 20 |

---

## 장중투자자별매매차트요청 `ka10064`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액, 2:수량 | 1 |
| `trde_tp` | String | Y | 매매구분 | 0:순매수, 1:매수, 2:매도 | 1 |
| `stk_cd` | String | Y | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 20 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- tm` | String | N | 시간 |  | 20 |
| `- frgnr_invsr` | String | N | 외국인투자자 |  | 20 |
| `- orgn` | String | N | 기관계 |  | 20 |
| `- invtrt` | String | N | 투신 |  | 20 |
| `- insrnc` | String | N | 보험 |  | 20 |
| `- bank` | String | N | 은행 |  | 20 |
| `- penfnd_etc` | String | N | 연기금등 |  | 20 |
| `- etc_corp` | String | N | 기타법인 |  | 20 |
| `- natn` | String | N | 국가 |  | 20 |

---

## 장중투자자별매매상위요청 `ka10065`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `mrkt_tp` | String | Y | 시장구분 | 000:전체, 001:코스피, 101:코스닥 | 3 |
| `orgn_tp` | String | Y | 기관구분 | 9000:외국인, 9100:외국계, 1000:금융투자, 3000:투신, 5000:기타금융, 4000:은행, 2000:보험, 6000:연기금, 7000:국가, 7100:기타법인, 9999:기관계 | 4 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- sel_qty` | String | N | 매도량 |  | 20 |
| `- buy_qty` | String | N | 매수량 |  | 20 |
| `- netslmt` | String | N | 순매도 |  | 20 |

---

## 장마감후투자자별매매요청 `ka10066`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액, 2:수량 | 1 |
| `trde_tp` | String | Y | 매매구분 | 0:순매수, 1:매수, 2:매도 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- ind_invsr` | String | N | 개인투자자 |  | 20 |
| `- frgnr_invsr` | String | N | 외국인투자자 |  | 20 |
| `- orgn` | String | N | 기관계 |  | 20 |
| `- fnnc_invt` | String | N | 금융투자 |  | 20 |
| `- insrnc` | String | N | 보험 |  | 20 |
| `- invtrt` | String | N | 투신 |  | 20 |
| `- etc_fnnc` | String | N | 기타금융 |  | 20 |
| `- bank` | String | N | 은행 |  | 20 |
| `- penfnd_etc` | String | N | 연기금등 |  | 20 |
| `- samo_fund` | String | N | 사모펀드 |  | 20 |
| `- natn` | String | N | 국가 |  | 20 |
| `- etc_corp` | String | N | 기타법인 |  | 20 |

---

## 대차거래추이요청 `ka10068`

**Method**: `POST`  
**URL**: `/api/dostk/slb`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | N | 종료일자 | YYYYMMDD | 8 |
| `all_tp` | String | Y | 전체구분 | 1: 전체표시 | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 8 |
| `- dbrt_trde_cntrcnt` | String | N | 대차거래체결주수 |  | 12 |
| `- dbrt_trde_rpy` | String | N | 대차거래상환주수 |  | 18 |
| `- rmnd` | String | N | 잔고주수 |  | 18 |
| `- dbrt_trde_irds` | String | N | 대차거래증감 |  | 60 |
| `- remn_amt` | String | N | 잔고금액 |  | 18 |

---

## 대차거래상위10종목요청 `ka10069`

**Method**: `POST`  
**URL**: `/api/dostk/slb`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | N | 종료일자 | YYYYMMDD
(연도4자리, 월 2자리, 일 2자리 형식) | 8 |
| `mrkt_tp` | String | Y | 시장구분 | 001:코스피, 101:코스닥 | 3 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dbrt_trde_rpy_sum` | String | N | 대차거래상환주수합 |  |  |
| `rmnd_sum` | String | N | 잔고주수합 |  |  |
| `remn_amt_sum` | String | N | 잔고금액합 |  |  |
| `dbrt_trde_cntrcnt_rt` | String | N | 대차거래체결주수비율 |  |  |
| `dbrt_trde_rpy_rt` | String | N | 대차거래상환주수비율 |  |  |
| `rmnd_rt` | String | N | 잔고주수비율 |  |  |
| `remn_amt_rt` | String | N | 잔고금액비율 |  |  |
| `dbrt_trde_upper_10stk` | LIST | N | 대차거래상위10종목 |  |  |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- dbrt_trde_cntrcnt` | String | N | 대차거래체결주수 |  | 20 |
| `- dbrt_trde_rpy` | String | N | 대차거래상환주수 |  | 20 |
| `- rmnd` | String | N | 잔고주수 |  | 20 |
| `- remn_amt` | String | N | 잔고금액 |  | 20 |

---

## 일자별종목별실현손익요청_일자 `ka10072`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- buy_uv` | String | N | 매입단가 |  | 20 |
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- tdy_sel_pl` | String | N | 당일매도손익 |  | 20 |
| `- pl_rt` | String | N | 손익율 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- tdy_trde_cmsn` | String | N | 당일매매수수료 |  | 20 |
| `- tdy_trde_tax` | String | N | 당일매매세금 |  | 20 |
| `- wthd_alowa` | String | N | 인출가능금액 |  | 20 |
| `- loan_dt` | String | N | 대출일 |  | 20 |
| `- crd_tp` | String | N | 신용구분 |  | 20 |
| `- stk_cd_1` | String | N | 종목코드1 |  | 20 |
| `- tdy_sel_pl_1` | String | N | 당일매도손익1 |  | 20 |

---

## 일자별종목별실현손익요청_기간 `ka10073`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- tdy_htssel_cmsn` | String | N | 당일hts매도수수료 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- buy_uv` | String | N | 매입단가 |  | 20 |
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- tdy_sel_pl` | String | N | 당일매도손익 |  | 20 |
| `- pl_rt` | String | N | 손익율 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- tdy_trde_cmsn` | String | N | 당일매매수수료 |  | 20 |
| `- tdy_trde_tax` | String | N | 당일매매세금 |  | 20 |
| `- wthd_alowa` | String | N | 인출가능금액 |  | 20 |
| `- loan_dt` | String | N | 대출일 |  | 20 |
| `- crd_tp` | String | N | 신용구분 |  | 20 |

---

## 일자별실현손익요청 `ka10074`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | Y | 종료일자 |  | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tot_sell_amt` | String | N | 총매도금액 |  |  |
| `rlzt_pl` | String | N | 실현손익 |  |  |
| `trde_cmsn` | String | N | 매매수수료 |  |  |
| `trde_tax` | String | N | 매매세금 |  |  |
| `dt_rlzt_pl` | LIST | N | 일자별실현손익 |  |  |
| `- dt` | String | N | 일자 |  | 20 |
| `- buy_amt` | String | N | 매수금액 |  | 20 |
| `- sell_amt` | String | N | 매도금액 |  | 20 |
| `- tdy_sel_pl` | String | N | 당일매도손익 |  | 20 |
| `- tdy_trde_cmsn` | String | N | 당일매매수수료 |  | 20 |
| `- tdy_trde_tax` | String | N | 당일매매세금 |  | 20 |

---

## 미체결요청 `ka10075`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_tp` | String | Y | 매매구분 | 0:전체, 1:매도, 2:매수 | 1 |
| `stk_cd` | String | N | 종목코드 |  | 6 |
| `stex_tp` | String | Y | 거래소구분 | 0 : 통합, 1 : KRX, 2 : NXT | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- acnt_no` | String | N | 계좌번호 |  | 20 |
| `- ord_no` | String | N | 주문번호 |  | 20 |
| `- mang_empno` | String | N | 관리사번 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- tsk_tp` | String | N | 업무구분 |  | 20 |
| `- ord_stt` | String | N | 주문상태 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- ord_qty` | String | N | 주문수량 |  | 20 |
| `- ord_pric` | String | N | 주문가격 |  | 20 |
| `- oso_qty` | String | N | 미체결수량 |  | 20 |
| `- cntr_tot_amt` | String | N | 체결누계금액 |  | 20 |
| `- orig_ord_no` | String | N | 원주문번호 |  | 20 |
| `- io_tp_nm` | String | N | 주문구분 |  | 20 |
| `- trde_tp` | String | N | 매매구분 |  | 20 |
| `- tm` | String | N | 시간 |  | 20 |
| `- cntr_no` | String | N | 체결번호 |  | 20 |
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- unit_cntr_pric` | String | N | 단위체결가 |  | 20 |
| `- unit_cntr_qty` | String | N | 단위체결량 |  | 20 |
| `- tdy_trde_cmsn` | String | N | 당일매매수수료 |  | 20 |
| `- tdy_trde_tax` | String | N | 당일매매세금 |  | 20 |
| `- ind_invsr` | String | N | 개인투자자 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | 0 : 통합, 1 : KRX, 2 : NXT | 20 |
| `- stex_tp_txt` | String | N | 거래소구분텍스트 | 통합,KRX,NXT | 20 |
| `- sor_yn` | String | N | SOR 여부값 | Y,N | 20 |
| `- stop_pric` | String | N | 스톱가 | 스톱지정가주문 스톱가 | 20 |

---

## 체결요청 `ka10076`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `qry_tp` | String | Y | 조회구분 | 0:전체, 1:종목 | 1 |
| `sell_tp` | String | Y | 매도수구분 | 0:전체, 1:매도, 2:매수 | 1 |
| `ord_no` | String | N | 주문번호 | 검색 기준 값으로 입력한 주문번호 보다 과거에 체결된 내역이 조회됩니다. | 10 |
| `stex_tp` | String | Y | 거래소구분 | 0 : 통합, 1 : KRX, 2 : NXT | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- ord_no` | String | N | 주문번호 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- io_tp_nm` | String | N | 주문구분 |  | 20 |
| `- ord_pric` | String | N | 주문가격 |  | 20 |
| `- ord_qty` | String | N | 주문수량 |  | 20 |
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- oso_qty` | String | N | 미체결수량 |  | 20 |
| `- tdy_trde_cmsn` | String | N | 당일매매수수료 |  | 20 |
| `- tdy_trde_tax` | String | N | 당일매매세금 |  | 20 |
| `- ord_stt` | String | N | 주문상태 |  | 20 |
| `- trde_tp` | String | N | 매매구분 |  | 20 |
| `- orig_ord_no` | String | N | 원주문번호 |  | 20 |
| `- ord_tm` | String | N | 주문시간 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | 0 : 통합, 1 : KRX, 2 : NXT | 20 |
| `- stex_tp_txt` | String | N | 거래소구분텍스트 | 통합,KRX,NXT | 20 |
| `- sor_yn` | String | N | SOR 여부값 | Y,N | 20 |
| `- stop_pric` | String | N | 스톱가 | 스톱지정가주문 스톱가 | 20 |

---

## 당일실현손익상세요청 `ka10077`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tdy_rlzt_pl_dtl` | LIST | N | 당일실현손익상세 |  |  |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- buy_uv` | String | N | 매입단가 |  | 20 |
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- tdy_sel_pl` | String | N | 당일매도손익 |  | 20 |
| `- pl_rt` | String | N | 손익율 |  | 20 |
| `- tdy_trde_cmsn` | String | N | 당일매매수수료 |  | 20 |
| `- tdy_trde_tax` | String | N | 당일매매세금 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |

---

## 증권사별종목매매동향요청 `ka10078`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 20 |
| `strt_dt` | String | Y | 시작일자 | YYYYMMDD | 8 |
| `end_dt` | String | Y | 종료일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- netprps_qty` | String | N | 순매수수량 |  | 20 |
| `- buy_qty` | String | N | 매수수량 |  | 20 |
| `- sell_qty` | String | N | 매도수량 |  | 20 |

---

## 주식틱차트조회요청 `ka10079`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | 2 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `last_tic_cnt` | String | N | 마지막틱갯수 |  |  |
| `stk_tic_chart_qry` | LIST | N | 주식틱차트조회 |  |  |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 | 현재가 - 전일종가 | 20 |
| `- pred_pre_sig` | String | N | 전일대비 기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |
| `- cntr_dt` | String | N | 체결일 |  | 20 |

---

## 주식분봉차트조회요청 `ka10080`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분 | 2 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_min_pole_chart_qry` | LIST | N | 주식분봉차트조회 |  |  |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 | 현재가 - 전일종가 | 20 |
| `- pred_pre_sig` | String | N | 전일대비 기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |
| `- cntr_dt` | String | N | 체결일 |  | 20 |

---

## 주식일봉차트조회요청 `ka10081`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_dt_pole_chart_qry` | LIST | N | 주식일봉차트조회 |  |  |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 | 현재가 - 전일종가 | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |
| `- trde_tern_rt` | String | N | 거래회전율 |  | 20 |

---

## 주식주봉차트조회요청 `ka10082`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_stk_pole_chart_qry` | LIST | N | 주식주봉차트조회 |  |  |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 | 현재가 - 전일종가 | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |
| `- trde_tern_rt` | String | N | 거래회전율 |  | 20 |

---

## 주식월봉차트조회요청 `ka10083`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_mth_pole_chart_qry` | LIST | N | 주식월봉차트조회 |  |  |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 | 현재가 - 전일종가 | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |
| `- trde_tern_rt` | String | N | 거래회전율 |  | 20 |

---

## 당일전일체결요청 `ka10084`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tdy_pred` | String | Y | 당일전일 | 당일 : 1, 전일 : 2 | 1 |
| `tic_min` | String | Y | 틱분 | 0:틱, 1:분 | 1 |
| `tm` | String | N | 시간 | 조회시간 4자리, 오전 9시일 경우 0900, 오후 2시 30분일 경우 1430 | 4 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- tm` | String | N | 시간 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- pre_rt` | String | N | 대비율 |  | 20 |
| `- pri_sel_bid_unit` | String | N | 우선매도호가단위 |  | 20 |
| `- pri_buy_bid_unit` | String | N | 우선매수호가단위 |  | 20 |
| `- cntr_trde_qty` | String | N | 체결거래량 |  | 20 |
| `- sign` | String | N | 전일대비기호 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | KRX , NXT , 통합 | 20 |

---

## 계좌수익률요청 `ka10085`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pur_pric` | String | N | 매입가 |  | 20 |
| `- pur_amt` | String | N | 매입금액 |  | 20 |
| `- rmnd_qty` | String | N | 보유수량 |  | 20 |
| `- tdy_sel_pl` | String | N | 당일매도손익 |  | 20 |
| `- tdy_trde_cmsn` | String | N | 당일매매수수료 |  | 20 |
| `- tdy_trde_tax` | String | N | 당일매매세금 |  | 20 |
| `- crd_tp` | String | N | 신용구분 |  | 20 |
| `- loan_dt` | String | N | 대출일 |  | 20 |
| `- setl_remn` | String | N | 결제잔고 |  | 20 |
| `- clrn_alow_qty` | String | N | 청산가능수량 |  | 20 |
| `- crd_amt` | String | N | 신용금액 |  | 20 |
| `- crd_int` | String | N | 신용이자 |  | 20 |
| `- expr_dt` | String | N | 만기일 |  | 20 |

---

## 일별주가요청 `ka10086`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `qry_dt` | String | Y | 조회일자 | YYYYMMDD | 8 |
| `indc_tp` | String | Y | 표시구분 | 0:수량, 1:금액(백만원) | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- date` | String | N | 날짜 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pred_rt` | String | N | 전일비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- amt_mn` | String | N | 금액(백만) |  | 20 |
| `- crd_rt` | String | N | 신용비 |  | 20 |
| `- ind` | String | N | 개인 |  | 20 |
| `- orgn` | String | N | 기관 |  | 20 |
| `- for_qty` | String | N | 외인수량 |  | 20 |
| `- frgn` | String | N | 외국계 |  | 20 |
| `- prm` | String | N | 프로그램 |  | 20 |
| `- for_rt` | String | N | 외인비 |  | 20 |
| `- for_poss` | String | N | 외인보유 |  | 20 |
| `- for_wght` | String | N | 외인비중 |  | 20 |
| `- for_netprps` | String | N | 외인순매수 |  | 20 |
| `- orgn_netprps` | String | N | 기관순매수 |  | 20 |
| `- ind_netprps` | String | N | 개인순매수 |  | 20 |
| `- crd_remn_rt` | String | N | 신용잔고율 |  | 20 |

---

## 시간외단일가요청 `ka10087`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `ovt_sigpric_sel_bid_jub_pre_5` | String | N | 시간외단일가_매도호가직전대비5 |  |  |
| `ovt_sigpric_sel_bid_jub_pre_4` | String | N | 시간외단일가_매도호가직전대비4 |  |  |
| `ovt_sigpric_sel_bid_jub_pre_3` | String | N | 시간외단일가_매도호가직전대비3 |  |  |
| `ovt_sigpric_sel_bid_jub_pre_2` | String | N | 시간외단일가_매도호가직전대비2 |  |  |
| `ovt_sigpric_sel_bid_jub_pre_1` | String | N | 시간외단일가_매도호가직전대비1 |  |  |
| `ovt_sigpric_sel_bid_qty_5` | String | N | 시간외단일가_매도호가수량5 |  |  |
| `ovt_sigpric_sel_bid_qty_4` | String | N | 시간외단일가_매도호가수량4 |  |  |
| `ovt_sigpric_sel_bid_qty_3` | String | N | 시간외단일가_매도호가수량3 |  |  |
| `ovt_sigpric_sel_bid_qty_2` | String | N | 시간외단일가_매도호가수량2 |  |  |
| `ovt_sigpric_sel_bid_qty_1` | String | N | 시간외단일가_매도호가수량1 |  |  |
| `ovt_sigpric_sel_bid_5` | String | N | 시간외단일가_매도호가5 |  |  |
| `ovt_sigpric_sel_bid_4` | String | N | 시간외단일가_매도호가4 |  |  |
| `ovt_sigpric_sel_bid_3` | String | N | 시간외단일가_매도호가3 |  |  |
| `ovt_sigpric_sel_bid_2` | String | N | 시간외단일가_매도호가2 |  |  |
| `ovt_sigpric_sel_bid_1` | String | N | 시간외단일가_매도호가1 |  |  |
| `ovt_sigpric_buy_bid_1` | String | N | 시간외단일가_매수호가1 |  |  |
| `ovt_sigpric_buy_bid_2` | String | N | 시간외단일가_매수호가2 |  |  |
| `ovt_sigpric_buy_bid_3` | String | N | 시간외단일가_매수호가3 |  |  |
| `ovt_sigpric_buy_bid_4` | String | N | 시간외단일가_매수호가4 |  |  |
| `ovt_sigpric_buy_bid_5` | String | N | 시간외단일가_매수호가5 |  |  |
| `ovt_sigpric_buy_bid_qty_1` | String | N | 시간외단일가_매수호가수량1 |  |  |
| `ovt_sigpric_buy_bid_qty_2` | String | N | 시간외단일가_매수호가수량2 |  |  |
| `ovt_sigpric_buy_bid_qty_3` | String | N | 시간외단일가_매수호가수량3 |  |  |
| `ovt_sigpric_buy_bid_qty_4` | String | N | 시간외단일가_매수호가수량4 |  |  |
| `ovt_sigpric_buy_bid_qty_5` | String | N | 시간외단일가_매수호가수량5 |  |  |
| `ovt_sigpric_buy_bid_jub_pre_1` | String | N | 시간외단일가_매수호가직전대비1 |  |  |
| `ovt_sigpric_buy_bid_jub_pre_2` | String | N | 시간외단일가_매수호가직전대비2 |  |  |
| `ovt_sigpric_buy_bid_jub_pre_3` | String | N | 시간외단일가_매수호가직전대비3 |  |  |
| `ovt_sigpric_buy_bid_jub_pre_4` | String | N | 시간외단일가_매수호가직전대비4 |  |  |
| `ovt_sigpric_buy_bid_jub_pre_5` | String | N | 시간외단일가_매수호가직전대비5 |  |  |
| `ovt_sigpric_sel_bid_tot_req` | String | N | 시간외단일가_매도호가총잔량 |  |  |
| `ovt_sigpric_buy_bid_tot_req` | String | N | 시간외단일가_매수호가총잔량 |  |  |
| `sel_bid_tot_req_jub_pre` | String | N | 매도호가총잔량직전대비 |  |  |
| `sel_bid_tot_req` | String | N | 매도호가총잔량 |  |  |
| `buy_bid_tot_req` | String | N | 매수호가총잔량 |  |  |
| `buy_bid_tot_req_jub_pre` | String | N | 매수호가총잔량직전대비 |  |  |
| `ovt_sel_bid_tot_req_jub_pre` | String | N | 시간외매도호가총잔량직전대비 |  |  |
| `ovt_sel_bid_tot_req` | String | N | 시간외매도호가총잔량 |  |  |
| `ovt_buy_bid_tot_req` | String | N | 시간외매수호가총잔량 |  |  |
| `ovt_buy_bid_tot_req_jub_pre` | String | N | 시간외매수호가총잔량직전대비 |  |  |
| `ovt_sigpric_cur_prc` | String | N | 시간외단일가_현재가 |  |  |
| `ovt_sigpric_pred_pre_sig` | String | N | 시간외단일가_전일대비기호 |  |  |
| `ovt_sigpric_pred_pre` | String | N | 시간외단일가_전일대비 |  |  |
| `ovt_sigpric_flu_rt` | String | N | 시간외단일가_등락률 |  |  |
| `ovt_sigpric_acc_trde_qty` | String | N | 시간외단일가_누적거래량 |  |  |

---

## 미체결 분할주문 상세 `ka10088`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- ord_no` | String | N | 주문번호 |  | 20 |
| `- ord_qty` | String | N | 주문수량 |  | 20 |
| `- ord_pric` | String | N | 주문가격 |  | 20 |
| `- osop_qty` | String | N | 미체결수량 |  | 20 |
| `- io_tp_nm` | String | N | 주문구분 |  | 20 |
| `- trde_tp` | String | N | 매매구분 |  | 20 |
| `- sell_tp` | String | N | 매도/수 구분 |  | 20 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- ord_stt` | String | N | 주문상태 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | 0 : 통합, 1 : KRX, 2 : NXT | 20 |
| `- stex_tp_txt` | String | N | 거래소구분텍스트 | 통합,KRX,NXT | 20 |

---

## 주식년봉차트조회요청 `ka10094`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_yr_pole_chart_qry` | LIST | N | 주식년봉차트조회 |  |  |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |

---

## 관심종목정보요청 `ka10095`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- base_pric` | String | N | 기준가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- cntr_qty` | String | N | 체결량 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- pred_trde_qty_pre` | String | N | 전일거래량대비 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- sel_1th_bid` | String | N | 매도1차호가 |  | 20 |
| `- sel_2th_bid` | String | N | 매도2차호가 |  | 20 |
| `- sel_3th_bid` | String | N | 매도3차호가 |  | 20 |
| `- sel_4th_bid` | String | N | 매도4차호가 |  | 20 |
| `- sel_5th_bid` | String | N | 매도5차호가 |  | 20 |
| `- buy_1th_bid` | String | N | 매수1차호가 |  | 20 |
| `- buy_2th_bid` | String | N | 매수2차호가 |  | 20 |
| `- buy_3th_bid` | String | N | 매수3차호가 |  | 20 |
| `- buy_4th_bid` | String | N | 매수4차호가 |  | 20 |
| `- buy_5th_bid` | String | N | 매수5차호가 |  | 20 |
| `- upl_pric` | String | N | 상한가 |  | 20 |
| `- lst_pric` | String | N | 하한가 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- exp_cntr_pric` | String | N | 예상체결가 |  | 20 |
| `- exp_cntr_qty` | String | N | 예상체결량 |  | 20 |
| `- cap` | String | N | 자본금 |  | 20 |
| `- fav` | String | N | 액면가 |  | 20 |
| `- mac` | String | N | 시가총액 |  | 20 |
| `- stkcnt` | String | N | 주식수 |  | 20 |
| `- bid_tm` | String | N | 호가시간 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- pri_sel_req` | String | N | 우선매도잔량 |  | 20 |
| `- pri_buy_req` | String | N | 우선매수잔량 |  | 20 |
| `- pri_sel_cnt` | String | N | 우선매도건수 |  | 20 |
| `- pri_buy_cnt` | String | N | 우선매수건수 |  | 20 |
| `- tot_sel_req` | String | N | 총매도잔량 |  | 20 |
| `- tot_buy_req` | String | N | 총매수잔량 |  | 20 |
| `- tot_sel_cnt` | String | N | 총매도건수 |  | 20 |
| `- tot_buy_cnt` | String | N | 총매수건수 |  | 20 |
| `- prty` | String | N | 패리티 |  | 20 |
| `- gear` | String | N | 기어링 |  | 20 |
| `- pl_qutr` | String | N | 손익분기 |  | 20 |
| `- cap_support` | String | N | 자본지지 |  | 20 |
| `- elwexec_pric` | String | N | ELW행사가 |  | 20 |
| `- cnvt_rt` | String | N | 전환비율 |  | 20 |
| `- elwexpr_dt` | String | N | ELW만기일 |  | 20 |
| `- cntr_engg` | String | N | 미결제약정 |  | 20 |
| `- cntr_pred_pre` | String | N | 미결제전일대비 |  | 20 |
| `- theory_pric` | String | N | 이론가 |  | 20 |
| `- innr_vltl` | String | N | 내재변동성 |  | 20 |
| `- delta` | String | N | 델타 |  | 20 |
| `- gam` | String | N | 감마 |  | 20 |
| `- theta` | String | N | 쎄타 |  | 20 |
| `- vega` | String | N | 베가 |  | 20 |
| `- law` | String | N | 로 |  | 20 |

---

## 시간외단일가등락율순위요청 `ka10098`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `sort_base` | String | Y | 정렬기준 | 1:상승률, 2:상승폭, 3:하락률, 4:하락폭, 5:보합 | 1 |
| `stk_cnd` | String | Y | 종목조건 | 0:전체조회,1:관리종목제외,2:정리매매종목제외,3:우선주제외,4:관리종목우선주제외,5:증100제외,6:증100만보기,7:증40만보기,8:증30만보기,9:증20만보기,12:증50만보기,13:증60만보기,14:ETF제외,15:스팩제외,16:ETF+ETN제외,17:ETN제외 | 2 |
| `trde_qty_cnd` | String | Y | 거래량조건 | 0:전체조회, 10:백주이상,50:5백주이상,100;천주이상, 500:5천주이상, 1000:만주이상, 5000:5만주이상, 10000:10만주이상 | 5 |
| `crd_cnd` | String | Y | 신용조건 | 0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 8:신용대주, 5:신용한도초과제외 | 1 |
| `trde_prica` | String | Y | 거래대금 | 0:전체조회, 5:5백만원이상,10:1천만원이상, 30:3천만원이상, 50:5천만원이상, 100:1억원이상, 300:3억원이상, 500:5억원이상, 1000:10억원이상, 3000:30억원이상, 5000:50억원이상, 10000:100억원이상 | 5 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- sel_tot_req` | String | N | 매도총잔량 |  | 20 |
| `- buy_tot_req` | String | N | 매수총잔량 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- tdy_close_pric` | String | N | 당일종가 |  | 20 |
| `- tdy_close_pric_flu_rt` | String | N | 당일종가등락률 |  | 20 |

---

## 종목정보 리스트 `ka10099`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- code` | String | N | 종목코드 | 단축코드 | 20 |
| `- name` | String | N | 종목명 |  | 40 |
| `- listCount` | String | N | 상장주식수 |  | 20 |
| `- auditInfo` | String | N | 감리구분 |  | 20 |
| `- regDay` | String | N | 상장일 |  | 20 |
| `- lastPrice` | String | N | 전일종가 |  | 20 |
| `- state` | String | N | 종목상태 |  | 20 |
| `- marketCode` | String | N | 시장구분코드 |  | 20 |
| `- marketName` | String | N | 시장명 |  | 20 |
| `- upName` | String | N | 업종명 |  | 20 |
| `- upSizeName` | String | N | 회사크기분류 |  | 20 |
| `- orderWarning` | String | N | 투자유의종목여부 | 0: 해당없음, 2: 정리매매, 3: 단기과열, 4: 투자위험, 5: 투자경과, 1: ETF투자주의요망(ETF인 경우만 전달 | 20 |
| `- companyClassName` | String | N | 회사분류 | 코스닥만 존재함 | 20 |
| `- nxtEnable` | String | N | NXT가능여부 | Y: 가능 | 20 |

---

## 종목정보 조회 `ka10100`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `name` | String | N | 종목명 |  | 40 |
| `listCount` | String | N | 상장주식수 |  |  |
| `auditInfo` | String | N | 감리구분 |  |  |
| `regDay` | String | N | 상장일 |  |  |
| `lastPrice` | String | N | 전일종가 |  |  |
| `state` | String | N | 종목상태 |  |  |
| `marketCode` | String | N | 시장구분코드 |  |  |
| `marketName` | String | N | 시장명 |  |  |
| `upName` | String | N | 업종명 |  |  |
| `upSizeName` | String | N | 회사크기분류 |  |  |
| `companyClassName` | String | N | 회사분류 | 코스닥만 존재함 |  |
| `orderWarning` | String | N | 투자유의종목여부 | 0: 해당없음, 2: 정리매매, 3: 단기과열, 4: 투자위험, 5: 투자경과, 1: ETF투자주의요망(ETF인 경우만 전달 |  |
| `nxtEnable` | String | N | NXT가능여부 | Y: 가능 |  |

---

## 업종코드 리스트 `ka10101`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- marketCode` | LIST | N | 시장구분코드 |  |  |
| `- code` | String | N | 코드 |  |  |
| `- name` | String | N | 업종명 |  |  |
| `- group` | String | N | 그룹 |  |  |

---

## 회원사 리스트 `ka10102`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- code` | String | N | 코드 |  |  |
| `- name` | String | N | 업종명 |  |  |
| `- gb` | String | N | 구분 |  |  |

---

## 기관외국인연속매매현황요청 `ka10131`

**Method**: `POST`  
**URL**: `/api/dostk/frgnistt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `strt_dt` | String | N | 시작일자 | YYYYMMDD | 8 |
| `end_dt` | String | N | 종료일자 | YYYYMMDD | 8 |
| `mrkt_tp` | String | Y | 장구분 | 001:코스피, 101:코스닥 | 3 |
| `netslmt_tp` | String | Y | 순매도수구분 | 2:순매수(고정값) | 1 |
| `stk_inds_tp` | String | Y | 종목업종구분 | 0:종목(주식),1:업종 | 1 |
| `amt_qty_tp` | String | Y | 금액수량구분 | 0:금액, 1:수량 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 6 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- prid_stkpc_flu_rt` | String | N | 기간중주가등락률 |  |  |
| `- orgn_nettrde_amt` | String | N | 기관순매매금액 |  |  |
| `- orgn_nettrde_qty` | String | N | 기관순매매량 |  |  |
| `- orgn_cont_netprps_dys` | String | N | 기관계연속순매수일수 |  |  |
| `- orgn_cont_netprps_qty` | String | N | 기관계연속순매수량 |  |  |
| `- orgn_cont_netprps_amt` | String | N | 기관계연속순매수금액 |  |  |
| `- frgnr_nettrde_qty` | String | N | 외국인순매매량 |  |  |
| `- frgnr_nettrde_amt` | String | N | 외국인순매매액 |  |  |
| `- frgnr_cont_netprps_dys` | String | N | 외국인연속순매수일수 |  |  |
| `- frgnr_cont_netprps_qty` | String | N | 외국인연속순매수량 |  |  |
| `- frgnr_cont_netprps_amt` | String | N | 외국인연속순매수금액 |  |  |
| `- nettrde_qty` | String | N | 순매매량 |  |  |
| `- nettrde_amt` | String | N | 순매매액 |  |  |
| `- tot_cont_netprps_dys` | String | N | 합계연속순매수일수 |  |  |
| `- tot_cont_nettrde_qty` | String | N | 합계연속순매매수량 |  |  |
| `- tot_cont_netprps_amt` | String | N | 합계연속순매수금액 |  |  |

---

## 당일매매일지요청 `ka10170`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `ottks_tp` | String | Y | 단주구분 | 1:당일매수에 대한 당일매도,2:당일매도 전체 | 1 |
| `ch_crd_tp` | String | Y | 현금신용구분 | 0:전체, 1:현금매매만, 2:신용매매만 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tot_buy_amt` | String | N | 총매수금액 |  |  |
| `tot_cmsn_tax` | String | N | 총수수료_세금 |  |  |
| `tot_exct_amt` | String | N | 총정산금액 |  |  |
| `tot_pl_amt` | String | N | 총손익금액 |  |  |
| `tot_prft_rt` | String | N | 총수익률 |  |  |
| `tdy_trde_diary` | LIST | N | 당일매매일지 |  |  |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- buy_avg_pric` | String | N | 매수평균가 |  |  |
| `- buy_qty` | String | N | 매수수량 |  |  |
| `- sel_avg_pric` | String | N | 매도평균가 |  |  |
| `- sell_qty` | String | N | 매도수량 |  |  |
| `- cmsn_alm_tax` | String | N | 수수료_제세금 |  |  |
| `- pl_amt` | String | N | 손익금액 |  |  |
| `- sell_amt` | String | N | 매도금액 |  |  |
| `- buy_amt` | String | N | 매수금액 |  |  |
| `- prft_rt` | String | N | 수익률 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 6 |

---

## 조건검색 목록조회 `ka10171`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 정상인 경우는 메시지 없음 |  |
| `trnm` | String | N | 서비스명 | CNSRLST 고정값 | 7 |
| `data` | LIST | N | 조건검색식 목록 |  |  |
| `- seq` | String | N | 조건검색식 일련번호 |  |  |
| `- name` | String | N | 조건검색식 명 |  |  |

---

## 조건검색 요청 일반 `ka10172`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `seq` | String | Y | 조건검색식 일련번호 |  | 3 |
| `search_type` | String | Y | 조회타입 | 0:조건검색 |  |
| `stex_tp` | String | Y | 거래소구분 | K:KRX | 1 |
| `cont_yn` | String | N | 연속조회여부 | Y:연속조회요청,N:연속조회미요청 | 1 |
| `next_key` | String | N | 연속조회키 |  | 20 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 정상인 경우는 메시지 없음 |  |
| `trnm` | String | N | 서비스명 | CNSRREQ |  |
| `seq` | String | N | 조건검색식 일련번호 |  |  |
| `cont_yn` | String | N | 연속조회여부 | 연속 데이터가 존재하는경우 Y, 없으면 N |  |
| `next_key` | String | N | 연속조회키 | 연속조회여부가Y일경우 다음 조회시 필요한 조회값 |  |
| `data` | LIST | N | 검색결과데이터 |  |  |
| `- 9001` | String | N | 종목코드 |  |  |
| `- 302` | String | N | 종목명 |  |  |
| `- 10` | String | N | 현재가 |  |  |
| `- 25` | String | N | 전일대비기호 |  |  |
| `- 11` | String | N | 전일대비 |  |  |
| `- 12` | String | N | 등락율 |  |  |
| `- 13` | String | N | 누적거래량 |  |  |
| `- 16` | String | N | 시가 |  |  |
| `- 17` | String | N | 고가 |  |  |
| `- 18` | String | N | 저가 |  |  |

---

## 조건검색 요청 실시간 `ka10173`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `seq` | String | Y | 조건검색식 일련번호 |  | 3 |
| `search_type` | String | Y | 조회타입 | 1: 조건검색+실시간조건검색 | 1 |
| `stex_tp` | String | Y | 거래소구분 | K:KRX | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_code` | String | N | 결과코드 | 정상:0 나머지:에러 |  |
| `return_msg` | String | N | 결과메시지 | 정상인 경우는 메시지 없음 |  |
| `trnm` | String | N | 서비스명 | CNSRREQ |  |
| `seq` | String | N | 조건검색식 일련번호 |  |  |
| `data` | LIST | N | 검색결과데이터 |  |  |
| `- jmcode` | String | N | 종목코드 |  |  |
| `data` | LIST | Y | 검색결과데이터 |  |  |
| `trnm` | String | Y | 서비스명 | REAL |  |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |
| `- name` | String | Y | 실시간 항목명 | 종목코드 |  |
| `- values` | Object | Y | 실시간 수신 값 |  |  |
| `- - 841` | String | Y | 일련번호 |  |  |
| `- - 9001` | String | Y | 종목코드 |  |  |
| `- - 843` | String | Y | 삽입삭제 구분 | I: 삽입, D: 삭제 |  |
| `- - 20` | String | Y | 체결시간 |  |  |
| `- - 907` | String | Y | 매도/수 구분 |  |  |

---

## 조건검색 실시간 해제 `ka10174`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `seq` | String | Y | 조건검색식 일련번호 |  |  |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | Y | 결과메시지 | 정상인 경우는 메시지 없음 |  |
| `trnm` | String | Y | 서비스명 | CNSRCLR 고정값 |  |
| `seq` | String | Y | 조건검색식 일련번호 |  |  |

---

## 업종현재가요청 `ka20001`

**Method**: `POST`  
**URL**: `/api/dostk/sect`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_cd` | String | Y | 업종코드 | 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고 | 3 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `pred_pre` | String | N | 전일대비 |  | 20 |
| `flu_rt` | String | N | 등락률 |  | 20 |
| `trde_qty` | String | N | 거래량 |  | 20 |
| `trde_prica` | String | N | 거래대금 |  | 20 |
| `trde_frmatn_stk_num` | String | N | 거래형성종목수 |  | 20 |
| `trde_frmatn_rt` | String | N | 거래형성비율 |  | 20 |
| `open_pric` | String | N | 시가 |  | 20 |
| `high_pric` | String | N | 고가 |  | 20 |
| `low_pric` | String | N | 저가 |  | 20 |
| `upl` | String | N | 상한 |  | 20 |
| `rising` | String | N | 상승 |  | 20 |
| `stdns` | String | N | 보합 |  | 20 |
| `fall` | String | N | 하락 |  | 20 |
| `lst` | String | N | 하한 |  | 20 |
| `52wk_hgst_pric` | String | N | 52주최고가 |  | 20 |
| `52wk_hgst_pric_dt` | String | N | 52주최고가일 |  | 20 |
| `52wk_hgst_pric_pre_rt` | String | N | 52주최고가대비율 |  | 20 |
| `52wk_lwst_pric` | String | N | 52주최저가 |  | 20 |
| `52wk_lwst_pric_dt` | String | N | 52주최저가일 |  | 20 |
| `52wk_lwst_pric_pre_rt` | String | N | 52주최저가대비율 |  | 20 |
| `inds_cur_prc_tm` | LIST | N | 업종현재가_시간별 |  |  |
| `- tm_n` | String | N | 시간n |  | 20 |
| `- cur_prc_n` | String | N | 현재가n |  | 20 |
| `- pred_pre_sig_n` | String | N | 전일대비기호n |  | 20 |
| `- pred_pre_n` | String | N | 전일대비n |  | 20 |
| `- flu_rt_n` | String | N | 등락률n |  | 20 |
| `- trde_qty_n` | String | N | 거래량n |  | 20 |
| `- acc_trde_qty_n` | String | N | 누적거래량n |  | 20 |

---

## 업종별주가요청 `ka20002`

**Method**: `POST`  
**URL**: `/api/dostk/sect`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_cd` | String | Y | 업종코드 | 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고 | 3 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- now_trde_qty` | String | N | 현재거래량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |

---

## 전업종지수요청 `ka20003`

**Method**: `POST`  
**URL**: `/api/dostk/sect`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- wght` | String | N | 비중 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- upl` | String | N | 상한 |  | 20 |
| `- rising` | String | N | 상승 |  | 20 |
| `- stdns` | String | N | 보합 |  | 20 |
| `- fall` | String | N | 하락 |  | 20 |
| `- lst` | String | N | 하한 |  | 20 |
| `- flo_stk_num` | String | N | 상장종목수 |  | 20 |

---

## 업종틱차트조회요청 `ka20004`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_tic_chart_qry` | LIST | N | 업종틱차트조회 |  |  |
| `- cur_prc` | String | N | 현재가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- open_pric` | String | N | 시가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- high_pric` | String | N | 고가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- low_pric` | String | N | 저가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- pred_pre` | String | N | 전일대비 | 현재가 - 전일종가 | 20 |
| `- pred_pre_sig` | String | N | 전일대비 기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |
| `- cntr_dt` | String | N | 체결일 |  | 20 |

---

## 업종분봉조회요청 `ka20005`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_min_pole_qry` | LIST | N | 업종분봉조회 |  |  |
| `- cur_prc` | String | N | 현재가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- open_pric` | String | N | 시가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- high_pric` | String | N | 고가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- low_pric` | String | N | 저가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- pred_pre` | String | N | 전일대비 | 현재가 - 전일종가 | 20 |
| `- pred_pre_sig` | String | N | 전일대비 기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |

---

## 업종일봉조회요청 `ka20006`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_cd` | String | Y | 업종코드 | 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고 | 3 |
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |

> ⚠️ **`inds_cd` 없이 호출하면 거부된다** — `base_dt`만 보내면
> `[1511:필수입력 파라미터=inds_cd]`. 2026-09-21 실엔드포인트 확인.
> 이 표에 원래 `inds_cd`가 없었다(ka10075 `all_stk_tp`와 같은 누락).
> 키움 공식 스펙(`src/constants/vendor/kiwoom_request_fields.json`)에는
> 처음부터 `Required: Y`로 있었다 — **틀린 건 이 손으로 쓴 표였다.**


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_cd` | String | N | 업종코드 | 요청값 echo |  |
| `inds_dt_pole_qry` | LIST | N | 업종일봉조회 | 1회 약 600행 |  |
| `- cur_prc` | String | N | 현재가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- high_pric` | String | N | 고가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- low_pric` | String | N | 저가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## 업종주봉조회요청 `ka20007`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 3 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_stk_pole_qry` | LIST | N | 업종주봉조회 |  |  |
| `- cur_prc` | String | N | 현재가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- high_pric` | String | N | 고가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- low_pric` | String | N | 저가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## 업종월봉조회요청 `ka20008`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_mth_pole_qry` | LIST | N | 업종월봉조회 |  |  |
| `- cur_prc` | String | N | 현재가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- high_pric` | String | N | 고가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- low_pric` | String | N | 저가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## 업종현재가일별요청 `ka20009`

**Method**: `POST`  
**URL**: `/api/dostk/sect`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `mrkt_tp` | String | Y | 시장구분 | 0:코스피, 1:코스닥, 2:코스피200 | 20 |
| `inds_cd` | String | Y | 업종코드 | 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고 | 3 |

> ⚠️ **`mrkt_tp`도 필수다** — `inds_cd`만 보내면
> `[1511:필수입력 파라미터=mrkt_tp]`. 2026-09-21 실엔드포인트 확인.


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `pred_pre` | String | N | 전일대비 |  | 20 |
| `flu_rt` | String | N | 등락률 |  | 20 |
| `trde_qty` | String | N | 거래량 |  | 20 |
| `trde_prica` | String | N | 거래대금 |  | 20 |
| `trde_frmatn_stk_num` | String | N | 거래형성종목수 |  | 20 |
| `trde_frmatn_rt` | String | N | 거래형성비율 |  | 20 |
| `open_pric` | String | N | 시가 |  | 20 |
| `high_pric` | String | N | 고가 |  | 20 |
| `low_pric` | String | N | 저가 |  | 20 |
| `upl` | String | N | 상한 |  | 20 |
| `rising` | String | N | 상승 |  | 20 |
| `stdns` | String | N | 보합 |  | 20 |
| `fall` | String | N | 하락 |  | 20 |
| `lst` | String | N | 하한 |  | 20 |
| `52wk_hgst_pric` | String | N | 52주최고가 |  | 20 |
| `52wk_hgst_pric_dt` | String | N | 52주최고가일 |  | 20 |
| `52wk_hgst_pric_pre_rt` | String | N | 52주최고가대비율 |  | 20 |
| `52wk_lwst_pric` | String | N | 52주최저가 |  | 20 |
| `52wk_lwst_pric_dt` | String | N | 52주최저가일 |  | 20 |
| `52wk_lwst_pric_pre_rt` | String | N | 52주최저가대비율 |  | 20 |
| `inds_cur_prc_daly_rept` | LIST | N | 업종현재가_일별반복 |  |  |
| `- dt_n` | String | N | 일자n |  | 20 |
| `- cur_prc_n` | String | N | 현재가n |  | 20 |
| `- pred_pre_sig_n` | String | N | 전일대비기호n |  | 20 |
| `- pred_pre_n` | String | N | 전일대비n |  | 20 |
| `- flu_rt_n` | String | N | 등락률n |  | 20 |
| `- acc_trde_qty_n` | String | N | 누적거래량n |  | 20 |

---

## 업종년봉조회요청 `ka20019`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `inds_yr_pole_qry` | LIST | N | 업종년봉조회 |  |  |
| `- cur_prc` | String | N | 현재가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- open_pric` | String | N | 시가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- high_pric` | String | N | 고가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- low_pric` | String | N | 저가 | 지수 값은 소수점 제거 후 100배 값으로 반환 | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## 대차거래추이요청(종목별) `ka20068`

**Method**: `POST`  
**URL**: `/api/dostk/slb`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | N | 종료일자 | YYYYMMDD | 8 |
| `all_tp` | String | N | 전체구분 | 0:종목코드 입력종목만 표시 | 1 |
| `stk_cd` | String | Y | 종목코드 |  | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- dbrt_trde_cntrcnt` | String | N | 대차거래체결주수 |  | 20 |
| `- dbrt_trde_rpy` | String | N | 대차거래상환주수 |  | 20 |
| `- dbrt_trde_irds` | String | N | 대차거래증감 |  | 20 |
| `- rmnd` | String | N | 잔고주수 |  | 20 |
| `- remn_amt` | String | N | 잔고금액 |  | 20 |

---

## ELW가격급등락요청 `ka30001`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tm_tp` | String | Y | 시간구분 | 1:분전, 2:일전 | 1 |
| `tm` | String | Y | 시간 | 분 혹은 일입력 (예 1, 3, 5) | 2 |
| `trde_qty_tp` | String | Y | 거래량구분 | 0:전체, 10:만주이상, 50:5만주이상, 100:10만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상 | 4 |
| `isscomp_cd` | String | Y | 발행사코드 | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17 | 12 |
| `bsis_aset_cd` | String | Y | 기초자산코드 | 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200.. | 12 |
| `rght_tp` | String | Y | 권리구분 | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 005:EX, 006:조기종료콜, 007:조기종료풋 | 3 |
| `lpcd` | String | Y | LP코드 | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17 | 12 |
| `trde_end_elwskip` | String | Y | 거래종료ELW제외 | 0:포함, 1:제외 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `elwpric_jmpflu` | LIST | N | ELW가격급등락 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_end_elwbase_pric` | String | N | 거래종료ELW기준가 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- base_pre` | String | N | 기준대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- jmp_rt` | String | N | 급등율 |  | 20 |

---

## 거래원별ELW순매매상위요청 `ka30002`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trde_qty_tp` | String | Y | 거래량구분 | 0:전체, 5:5천주, 10:만주, 50:5만주, 100:10만주, 500:50만주, 1000:백만주 | 4 |
| `trde_tp` | String | Y | 매매구분 | 1:순매수, 2:순매도 | 1 |
| `dt` | String | Y | 기간 | 1:전일, 5:5일, 10:10일, 40:40일, 60:60일 | 2 |
| `trde_end_elwskip` | String | Y | 거래종료ELW제외 | 0:포함, 1:제외 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- stkpc_flu` | String | N | 주가등락 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- netprps` | String | N | 순매수 |  | 20 |
| `- buy_trde_qty` | String | N | 매수거래량 |  | 20 |
| `- sel_trde_qty` | String | N | 매도거래량 |  | 20 |

---

## ELWLP보유일별추이요청 `ka30003`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_tp` | String | N | 대비구분 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- chg_qty` | String | N | 변동수량 |  | 20 |
| `- lprmnd_qty` | String | N | LP보유수량 |  | 20 |
| `- wght` | String | N | 비중 |  | 20 |

---

## ELW괴리율요청 `ka30004`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `bsis_aset_cd` | String | Y | 기초자산코드 | 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200.. | 12 |
| `rght_tp` | String | Y | 권리구분 | 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 005: EX, 006: 조기종료콜, 007: 조기종료풋 | 3 |
| `lpcd` | String | Y | LP코드 | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17 | 12 |
| `trde_end_elwskip` | String | Y | 거래종료ELW제외 | 1:거래종료ELW제외, 0:거래종료ELW포함 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- isscomp_nm` | String | N | 발행사명 |  | 20 |
| `- sqnc` | String | N | 회차 |  | 20 |
| `- base_aset_nm` | String | N | 기초자산명 |  | 20 |
| `- rght_tp` | String | N | 권리구분 |  | 20 |
| `- dispty_rt` | String | N | 괴리율 |  | 20 |
| `- basis` | String | N | 베이시스 |  | 20 |
| `- srvive_dys` | String | N | 잔존일수 |  | 20 |
| `- theory_pric` | String | N | 이론가 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_tp` | String | N | 대비구분 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |

---

## ELW조건검색요청 `ka30005`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `bsis_aset_cd` | String | Y | 기초자산코드 | 전체일때만 12자리입력(전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼정전자:005930, KT:030200,,) | 12 |
| `rght_tp` | String | Y | 권리구분 | 0:전체, 1:콜, 2:풋, 3:DC, 4:DP, 5:EX, 6:조기종료콜, 7:조기종료풋 | 1 |
| `lpcd` | String | Y | LP코드 | 전체일때만 12자리입력(전체:000000000000, 한국투자증권:003, 미래대우:005, 신영:006, NK투자증권:012, KB증권:017) | 12 |
| `sort_tp` | String | Y | 정렬구분 | 0:정렬없음, 1:상승율순, 2:상승폭순, 3:하락율순, 4:하락폭순, 5:거래량순, 6:거래대금순, 7:잔존일순 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- isscomp_nm` | String | N | 발행사명 |  | 20 |
| `- sqnc` | String | N | 회차 |  | 20 |
| `- base_aset_nm` | String | N | 기초자산명 |  | 20 |
| `- rght_tp` | String | N | 권리구분 |  | 20 |
| `- expr_dt` | String | N | 만기일 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_tp` | String | N | 대비구분 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_qty_pre` | String | N | 거래량대비 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- pred_trde_qty` | String | N | 전일거래량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- prty` | String | N | 패리티 |  | 20 |
| `- gear_rt` | String | N | 기어링비율 |  | 20 |
| `- pl_qutr_rt` | String | N | 손익분기율 |  | 20 |
| `- cfp` | String | N | 자본지지점 |  | 20 |
| `- theory_pric` | String | N | 이론가 |  | 20 |
| `- innr_vltl` | String | N | 내재변동성 |  | 20 |
| `- delta` | String | N | 델타 |  | 20 |
| `- lvrg` | String | N | 레버리지 |  | 20 |
| `- exec_pric` | String | N | 행사가격 |  | 20 |
| `- cnvt_rt` | String | N | 전환비율 |  | 20 |
| `- lpposs_rt` | String | N | LP보유비율 |  | 20 |
| `- pl_qutr_pt` | String | N | 손익분기점 |  | 20 |
| `- fin_trde_dt` | String | N | 최종거래일 |  | 20 |
| `- flo_dt` | String | N | 상장일 |  | 20 |
| `- lpinitlast_suply_dt` | String | N | LP초종공급일 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- srvive_dys` | String | N | 잔존일수 |  | 20 |
| `- dispty_rt` | String | N | 괴리율 |  | 20 |
| `- lpmmcm_nm` | String | N | LP회원사명 |  | 20 |
| `- lpmmcm_nm_1` | String | N | LP회원사명1 |  | 20 |
| `- lpmmcm_nm_2` | String | N | LP회원사명2 |  | 20 |
| `- xraymont_cntr_qty_arng_trde_tp` | String | N | Xray순간체결량정리매매구분 |  | 20 |
| `- xraymont_cntr_qty_profa_100tp` | String | N | Xray순간체결량증거금100구분 |  | 20 |

---

## ELW등락율순위요청 `ka30009`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `rght_tp` | String | Y | 권리구분 | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 006:조기종료콜, 007:조기종료풋 | 3 |
| `trde_end_skip` | String | Y | 거래종료제외 | 1:거래종료제외, 0:거래종료포함 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- sel_req` | String | N | 매도잔량 |  | 20 |
| `- buy_req` | String | N | 매수잔량 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## ELW잔량순위요청 `ka30010`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `rght_tp` | String | Y | 권리구분 | 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 006: 조기종료콜, 007: 조기종료풋 | 3 |
| `trde_end_skip` | String | Y | 거래종료제외 | 1:거래종료제외, 0:거래종료포함 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락률 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- sel_req` | String | N | 매도잔량 |  | 20 |
| `- buy_req` | String | N | 매수잔량 |  | 20 |
| `- netprps_req` | String | N | 순매수잔량 |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |

---

## ELW근접율요청 `ka30011`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- alacc_rt` | String | N | 근접율 |  | 20 |

---

## ELW종목상세정보요청 `ka30012`

**Method**: `POST`  
**URL**: `/api/dostk/elw`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cur_prc` | String | N | 현재가 |  | 20 |
| `pred_pre_sig` | String | N | 전일대비기호 |  | 20 |
| `pred_pre` | String | N | 전일대비 |  | 20 |
| `flu_rt` | String | N | 등락율 |  | 20 |
| `lpmmcm_nm` | String | N | LP회원사명 |  | 20 |
| `lpmmcm_nm_1` | String | N | LP회원사명1 |  | 20 |
| `lpmmcm_nm_2` | String | N | LP회원사명2 |  | 20 |
| `elwrght_cntn` | String | N | ELW권리내용 |  | 20 |
| `elwexpr_evlt_pric` | String | N | ELW만기평가가격 |  | 20 |
| `elwtheory_pric` | String | N | ELW이론가 |  | 20 |
| `dispty_rt` | String | N | 괴리율 |  | 20 |
| `elwinnr_vltl` | String | N | ELW내재변동성 |  | 20 |
| `exp_rght_pric` | String | N | 예상권리가 |  | 20 |
| `elwpl_qutr_rt` | String | N | ELW손익분기율 |  | 20 |
| `elwexec_pric` | String | N | ELW행사가 |  | 20 |
| `elwcnvt_rt` | String | N | ELW전환비율 |  | 20 |
| `elwcmpn_rt` | String | N | ELW보상율 |  | 20 |
| `elwpric_rising_part_rt` | String | N | ELW가격상승참여율 |  | 20 |
| `elwrght_type` | String | N | ELW권리유형 |  | 20 |
| `elwsrvive_dys` | String | N | ELW잔존일수 |  | 20 |
| `stkcnt` | String | N | 주식수 |  | 20 |
| `elwlpord_pos` | String | N | ELWLP주문가능 |  | 20 |
| `lpposs_rt` | String | N | LP보유비율 |  | 20 |
| `lprmnd_qty` | String | N | LP보유수량 |  | 20 |
| `elwspread` | String | N | ELW스프레드 |  | 20 |
| `elwprty` | String | N | ELW패리티 |  | 20 |
| `elwgear` | String | N | ELW기어링 |  | 20 |
| `elwflo_dt` | String | N | ELW상장일 |  | 20 |
| `elwfin_trde_dt` | String | N | ELW최종거래일 |  | 20 |
| `expr_dt` | String | N | 만기일 |  | 20 |
| `exec_dt` | String | N | 행사일 |  | 20 |
| `lpsuply_end_dt` | String | N | LP공급종료일 |  | 20 |
| `elwpay_dt` | String | N | ELW지급일 |  | 20 |
| `elwinvt_ix_comput` | String | N | ELW투자지표산출 |  |  |
| `elwpay_agnt` | String | N | ELW지급대리인 |  |  |
| `elwappr_way` | String | N | ELW결재방법 |  |  |
| `elwrght_exec_way` | String | N | ELW권리행사방식 |  |  |
| `elwpblicte_orgn` | String | N | ELW발행기관 |  |  |
| `dcsn_pay_amt` | String | N | 확정지급액 |  |  |
| `kobarr` | String | N | KO베리어 |  |  |
| `iv` | String | N | IV |  |  |
| `clsprd_end_elwocr` | String | N | 종기종료ELW발생 |  |  |
| `bsis_aset_1` | String | N | 기초자산1 |  |  |
| `bsis_aset_comp_rt_1` | String | N | 기초자산구성비율1 |  |  |
| `bsis_aset_2` | String | N | 기초자산2 |  |  |
| `bsis_aset_comp_rt_2` | String | N | 기초자산구성비율2 |  |  |
| `bsis_aset_3` | String | N | 기초자산3 |  |  |
| `bsis_aset_comp_rt_3` | String | N | 기초자산구성비율3 |  |  |
| `bsis_aset_4` | String | N | 기초자산4 |  |  |
| `bsis_aset_comp_rt_4` | String | N | 기초자산구성비율4 |  |  |
| `bsis_aset_5` | String | N | 기초자산5 |  |  |
| `bsis_aset_comp_rt_5` | String | N | 기초자산구성비율5 |  |  |
| `fr_dt` | String | N | 평가시작일자 |  |  |
| `to_dt` | String | N | 평가종료일자 |  |  |
| `fr_tm` | String | N | 평가시작시간 |  |  |
| `evlt_end_tm` | String | N | 평가종료시간 |  |  |
| `evlt_pric` | String | N | 평가가격 |  |  |
| `evlt_fnsh_yn` | String | N | 평가완료여부 |  |  |
| `all_hgst_pric` | String | N | 전체최고가 |  |  |
| `all_lwst_pric` | String | N | 전체최저가 |  |  |
| `imaf_hgst_pric` | String | N | 직후최고가 |  |  |
| `imaf_lwst_pric` | String | N | 직후최저가 |  |  |
| `sndhalf_mrkt_hgst_pric` | String | N | 후반장최고가 |  |  |
| `sndhalf_mrkt_lwst_pric` | String | N | 후반장최저가 |  |  |

---

## ETF수익율요청 `ka40001`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `etfobjt_idex_cd` | String | Y | ETF대상지수코드 |  | 3 |
| `dt` | String | Y | 기간 | 0:1주, 1:1달, 2:6개월, 3:1년 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- etfprft_rt` | String | N | ETF수익률 |  | 20 |
| `- cntr_prft_rt` | String | N | 체결수익률 |  | 20 |
| `- for_netprps_qty` | String | N | 외인순매수수량 |  | 20 |
| `- orgn_netprps_qty` | String | N | 기관순매수수량 |  | 20 |

---

## ETF종목정보요청 `ka40002`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `etfobjt_idex_nm` | String | N | ETF대상지수명 |  | 20 |
| `wonju_pric` | String | N | 원주가격 |  | 20 |
| `etftxon_type` | String | N | ETF과세유형 |  | 20 |
| `etntxon_type` | String | N | ETN과세유형 |  | 20 |

---

## ETF일별추이요청 `ka40003`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_dt` | String | N | 체결일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- pre_rt` | String | N | 대비율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- nav` | String | N | NAV |  | 20 |
| `- acc_trde_prica` | String | N | 누적거래대금 |  | 20 |
| `- navidex_dispty_rt` | String | N | NAV/지수괴리율 |  | 20 |
| `- navetfdispty_rt` | String | N | NAV/ETF괴리율 |  | 20 |
| `- trace_eor_rt` | String | N | 추적오차율 |  | 20 |
| `- trace_cur_prc` | String | N | 추적현재가 |  | 20 |
| `- trace_pred_pre` | String | N | 추적전일대비 |  | 20 |
| `- trace_pre_sig` | String | N | 추적대비기호 |  | 20 |

---

## ETF전체시세요청 `ka40004`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `navpre` | String | Y | NAV대비 | 0:전체, 1:NAV > 전일종가, 2:NAV < 전일종가 | 1 |
| `mngmcomp` | String | Y | 운용사 | 0000:전체, 3020:KODEX(삼성), 3027:KOSEF(키움), 3191:TIGER(미래에셋), 3228:KINDEX(한국투자), 3023:KStar(KB), 3022:아리랑(한화), 9999:기타운용사 | 4 |
| `txon_yn` | String | Y | 과세여부 | 0:전체, 1:과세, 2:비과세 | 1 |
| `trace_idex` | String | Y | 추적지수 | 0:전체 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_cls` | String | N | 종목분류 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- pre_rt` | String | N | 대비율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- nav` | String | N | NAV |  | 20 |
| `- trace_eor_rt` | String | N | 추적오차율 |  | 20 |
| `- txbs` | String | N | 과표기준 |  | 20 |
| `- dvid_bf_base` | String | N | 배당전기준 |  | 20 |
| `- pred_dvida` | String | N | 전일배당금 |  | 20 |
| `- trace_idex_nm` | String | N | 추적지수명 |  | 20 |
| `- drng` | String | N | 배수 |  | 20 |
| `- trace_idex_cd` | String | N | 추적지수코드 |  | 20 |
| `- trace_idex` | String | N | 추적지수 |  | 20 |
| `- trace_flu_rt` | String | N | 추적등락율 |  | 20 |

---

## ETF시간대별추이요청 `ka40006`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `etfobjt_idex_nm` | String | N | ETF대상지수명 |  | 20 |
| `wonju_pric` | String | N | 원주가격 |  | 20 |
| `etftxon_type` | String | N | ETF과세유형 |  | 20 |
| `etntxon_type` | String | N | ETN과세유형 |  | 20 |
| `etftisl_trnsn` | LIST | N | ETF시간대별추이 |  |  |
| `- tm` | String | N | 시간 |  | 20 |
| `- close_pric` | String | N | 종가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- nav` | String | N | NAV |  | 20 |
| `- trde_prica` | String | N | 거래대금 |  | 20 |
| `- navidex` | String | N | NAV지수 |  | 20 |
| `- navetf` | String | N | NAVETF |  | 20 |
| `- trace` | String | N | 추적 |  | 20 |
| `- trace_idex` | String | N | 추적지수 |  | 20 |
| `- trace_idex_pred_pre` | String | N | 추적지수전일대비 |  | 20 |
| `- trace_idex_pred_pre_sig` | String | N | 추적지수전일대비기호 |  | 20 |

---

## ETF시간대별체결요청 `ka40007`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_nm` | String | N | 종목명 |  | 40 |
| `etfobjt_idex_nm` | String | N | ETF대상지수명 |  | 20 |
| `etfobjt_idex_cd` | String | N | ETF대상지수코드 |  | 20 |
| `objt_idex_pre_rt` | String | N | 대상지수대비율 |  | 20 |
| `wonju_pric` | String | N | 원주가격 |  | 20 |
| `etftisl_cntr_array` | LIST | N | ETF시간대별체결배열 |  |  |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | KRX , NXT , 통합 | 20 |

---

## ETF일자별체결요청 `ka40008`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cur_prc` | String | N | 현재가 |  | 20 |
| `pre_sig` | String | N | 대비기호 |  | 20 |
| `pred_pre` | String | N | 전일대비 |  | 20 |
| `trde_qty` | String | N | 거래량 |  | 20 |
| `etfnetprps_qty_array` | LIST | N | ETF순매수수량배열 |  |  |
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc_n` | String | N | 현재가n |  | 20 |
| `- pre_sig_n` | String | N | 대비기호n |  | 20 |
| `- pred_pre_n` | String | N | 전일대비n |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- for_netprps_qty` | String | N | 외인순매수수량 |  | 20 |
| `- orgn_netprps_qty` | String | N | 기관순매수수량 |  | 20 |

---

## ETF시간대별체결요청 `ka40009`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- nav` | String | N | NAV |  | 20 |
| `- navpred_pre` | String | N | NAV전일대비 |  | 20 |
| `- navflu_rt` | String | N | NAV등락율 |  | 20 |
| `- trace_eor_rt` | String | N | 추적오차율 |  | 20 |
| `- dispty_rt` | String | N | 괴리율 |  | 20 |
| `- stkcnt` | String | N | 주식수 |  | 20 |
| `- base_pric` | String | N | 기준가 |  | 20 |
| `- for_rmnd_qty` | String | N | 외인보유수량 |  | 20 |
| `- repl_pric` | String | N | 대용가 |  | 20 |
| `- conv_pric` | String | N | 환산가격 |  | 20 |
| `- drstk` | String | N | DR/주 |  | 20 |
| `- wonju_pric` | String | N | 원주가격 |  | 20 |

---

## ETF시간대별추이요청 `ka40010`

**Method**: `POST`  
**URL**: `/api/dostk/etf`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- for_netprps` | String | N | 외인순매수 |  | 20 |

---

## 금현물체결추이 `ka50010`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- pred_pre` | String | N | 전일 대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 누적 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적 거래대금 |  | 20 |
| `- cntr_trde_qty` | String | N | 거래량(체결량) |  | 20 |
| `- tm` | String | N | 체결시간 |  | 20 |
| `- pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pri_sel_bid_unit` | String | N | 매도호가 |  | 20 |
| `- pri_buy_bid_unit` | String | N | 매수호가 |  | 20 |
| `- trde_pre` | String | N | 전일 거래량 대비 비율 |  | 20 |
| `- trde_tern_rt` | String | N | 전일 거래량 대비 순간 거래량 비율 |  | 20 |
| `- cntr_str` | String | N | 체결강도 |  | 20 |

---

## 금현물일별추이 `ka50012`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cur_prc` | String | N | 종가 |  | 20 |
| `- pred_pre` | String | N | 전일 대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 누적 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적 거래대금(백만) |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- orgn_netprps` | String | N | 기관 순매수 수량 |  | 20 |
| `- for_netprps` | String | N | 외국인 순매수 수량 |  | 20 |
| `- ind_netprps` | String | N | 순매매량(개인) |  | 20 |

---

## 금현물틱차트조회요청 `ka50079`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | 2 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  |  |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |

---

## 금현물분봉차트조회요청 `ka50080`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분 | 3 |
| `upd_stkpc_tp` | String | N | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |

---

## 금현물일봉차트조회요청 `ka50081`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- acc_trde_qty` | String | N | 누적 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적 거래대금 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |

---

## 금현물주봉차트조회요청 `ka50082`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- acc_trde_qty` | String | N | 누적 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적 거래대금 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |

---

## 금현물월봉차트조회요청 `ka50083`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_dt` | String | Y | 기준일자 | YYYYMMDD | 8 |
| `upd_stkpc_tp` | String | Y | 수정주가구분 | 0 or 1 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- acc_trde_qty` | String | N | 누적 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적 거래대금 |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |

---

## 금현물예상체결 `ka50087`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- exp_cntr_pric` | String | N | 예상 체결가 |  | 20 |
| `- exp_pred_pre` | String | N | 예상 체결가 전일대비 |  | 20 |
| `- exp_flu_rt` | String | N | 예상 체결가 등락율 |  | 20 |
| `- exp_acc_trde_qty` | String | N | 예상 체결 수량(누적) |  | 20 |
| `- exp_cntr_trde_qty` | String | N | 예상 체결 수량 |  | 20 |
| `- exp_tm` | String | N | 예상 체결 시간 |  | 20 |
| `- exp_pre_sig` | String | N | 예상 체결가 전일대비기호 |  | 20 |
| `- stex_tp` | String | N | 거래소 구분 |  |  |

---

## 금현물당일틱차트조회요청 `ka50091`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- pred_pre` | String | N | 전일 대비(원) |  | 20 |
| `- trde_qty` | String | N | 거래량(체결량) |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |

---

## 금현물당일분봉차트조회요청 `ka50092`

**Method**: `POST`  
**URL**: `/api/dostk/chart`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- pred_pre` | String | N | 전일 대비(원) |  | 20 |
| `- acc_trde_qty` | String | N | 누적 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적 거래대금 |  | 20 |
| `- trde_qty` | String | N | 거래량(체결량) |  | 20 |
| `- open_pric` | String | N | 시가 |  | 20 |
| `- high_pric` | String | N | 고가 |  | 20 |
| `- low_pric` | String | N | 저가 |  | 20 |
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- dt` | String | N | 일자 |  | 20 |
| `- pred_pre_sig` | String | N | 전일대비기호 |  | 20 |

---

## 금현물 시세정보 `ka50100`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `pred_pre` | String | N | 전일대비 |  | 20 |
| `flu_rt` | String | N | 등락율 |  | 20 |
| `trde_qty` | String | N | 거래량 |  | 20 |
| `open_pric` | String | N | 시가 |  | 20 |
| `high_pric` | String | N | 고가 |  | 20 |
| `low_pric` | String | N | 저가 |  | 20 |
| `pred_rt` | String | N | 전일비 |  | 20 |
| `upl_pric` | String | N | 상한가 |  | 20 |
| `lst_pric` | String | N | 하한가 |  | 20 |
| `pred_close_pric` | String | N | 전일종가 |  | 20 |

---

## 금현물 호가 `ka50101`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tic_scope` | String | Y | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_pric` | String | N | 체결가 |  | 20 |
| `- pred_pre` | String | N | 전일 대비(원) |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 누적 거래량 |  | 20 |
| `- acc_trde_prica` | String | N | 누적 거래대금 |  | 20 |
| `- cntr_trde_qty` | String | N | 거래량(체결량) |  | 20 |
| `- tm` | String | N | 체결시간 |  | 20 |
| `- pre_sig` | String | N | 전일대비기호 |  | 20 |
| `- pri_sel_bid_unit` | String | N | 매도호가 |  | 20 |
| `- pri_buy_bid_unit` | String | N | 매수호가 |  | 20 |
| `- trde_pre` | String | N | 전일 거래량 대비 비율 |  | 20 |
| `- trde_tern_rt` | String | N | 전일 거래량 대비 순간 거래량 비율 |  |  |
| `- cntr_str` | String | N | 체결강도 |  | 20 |
| `- lpmmcm_nm_1` | String | N | K.O 접근도 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 |  | 20 |

---

## 금현물투자자현황 `ka52301`

**Method**: `POST`  
**URL**: `/api/dostk/frgnistt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- all_dfrt_trst_sell_qty` | String | N | 투자자별 매도 수량(천) |  | 20 |
| `- sell_qty_irds` | String | N | 투자자별 매도 수량 증감(천) |  | 20 |
| `- all_dfrt_trst_sell_amt` | String | N | 투자자별 매도 금액(억) |  | 20 |
| `- sell_amt_irds` | String | N | 투자자별 매도 금액 증감(억) |  | 20 |
| `- all_dfrt_trst_buy_qty` | String | N | 투자자별 매수 수량(천) |  | 20 |
| `- buy_qty_irds` | String | N | 투자자별 매수 수량 증감(천) |  | 20 |
| `- all_dfrt_trst_buy_amt` | String | N | 투자자별 매수 금액(억) |  | 20 |
| `- buy_amt_irds` | String | N | 투자자별 매수 금액 증감(억) |  | 20 |
| `- all_dfrt_trst_netprps_qty` | String | N | 투자자별 순매수 수량(천) |  | 20 |
| `- netprps_qty_irds` | String | N | 투자자별 순매수 수량 증감(천) |  | 20 |
| `- all_dfrt_trst_netprps_amt` | String | N | 투자자별 순매수 금액(억) |  | 20 |
| `- netprps_amt_irds` | String | N | 투자자별 순매수 금액 증감(억) |  | 20 |
| `- sell_uv` | String | N | 투자자별 매도 단가 |  | 20 |
| `- buy_uv` | String | N | 투자자별 매수 단가 |  | 20 |
| `- stk_nm` | String | N | 투자자 구분명 |  | 20 |
| `- acc_netprps_amt` | String | N | 누적 순매수 금액(억) |  | 20 |
| `- acc_netprps_qty` | String | N | 누적 순매수 수량(천) |  | 20 |
| `- stk_cd` | String | N | 투자자 코드 |  | 20 |

---

## 테마그룹별요청 `ka90001`

**Method**: `POST`  
**URL**: `/api/dostk/thme`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | N | 종목코드 | 검색하려는 종목코드 | 6 |
| `date_tp` | String | Y | 날짜구분 | n일전 (1일 ~ 99일 날짜입력) | 2 |
| `thema_nm` | String | N | 테마명 | 검색하려는 테마명 | 50 |
| `flu_pl_amt_tp` | String | Y | 등락수익구분 | 1:상위기간수익률, 2:하위기간수익률, 3:상위등락률, 4:하위등락률 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- thema_grp_cd` | String | N | 테마그룹코드 |  | 20 |
| `- thema_nm` | String | N | 테마명 |  | 20 |
| `- stk_num` | String | N | 종목수 |  | 20 |
| `- flu_sig` | String | N | 등락기호 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- rising_stk_num` | String | N | 상승종목수 |  | 20 |
| `- fall_stk_num` | String | N | 하락종목수 |  | 20 |
| `- dt_prft_rt` | String | N | 기간수익률 |  | 20 |
| `- main_stk` | String | N | 주요종목 |  | 20 |

---

## 테마구성종목요청 `ka90002`

**Method**: `POST`  
**URL**: `/api/dostk/thme`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `thema_grp_cd` | String | Y | 테마그룹코드 | 테마그룹코드 번호 | 6 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dt_prft_rt` | String | N | 기간수익률 |  | 20 |
| `thema_comp_stk` | LIST | N | 테마구성종목 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- flu_sig` | String | N | 등락기호 | 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락 | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- sel_bid` | String | N | 매도호가 |  | 20 |
| `- sel_req` | String | N | 매도잔량 |  | 20 |
| `- buy_bid` | String | N | 매수호가 |  | 20 |
| `- buy_req` | String | N | 매수잔량 |  | 20 |
| `- dt_prft_rt_n` | String | N | 기간수익률n |  | 20 |

---

## 프로그램순매수상위50요청 `ka90003`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액, 2:수량 | 2 |
| `mrkt_tp` | String | Y | 시장구분 | P00101:코스피, P10102:코스닥 | 10 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- rank` | String | N | 순위 |  | 20 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- flu_sig` | String | N | 등락기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- acc_trde_qty` | String | N | 누적거래량 |  | 20 |
| `- prm_sell_amt` | String | N | 프로그램매도금액 |  | 20 |
| `- prm_buy_amt` | String | N | 프로그램매수금액 |  | 20 |
| `- prm_netprps_amt` | String | N | 프로그램순매수금액 |  | 20 |

---

## 종목별프로그램매매현황요청 `ka90004`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `mrkt_tp` | String | Y | 시장구분 | P00101:코스피, P10102:코스닥 | 10 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tot_2` | String | N | 매수체결금액합계 |  | 20 |
| `tot_3` | String | N | 매도체결수량합계 |  | 20 |
| `tot_4` | String | N | 매도체결금액합계 |  | 20 |
| `tot_5` | String | N | 순매수대금합계 |  | 20 |
| `tot_6` | String | N | 합계6 |  | 20 |
| `stk_prm_trde_prst` | LIST | N | 종목별프로그램매매현황 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- flu_sig` | String | N | 등락기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- buy_cntr_qty` | String | N | 매수체결수량 |  | 20 |
| `- buy_cntr_amt` | String | N | 매수체결금액 |  | 20 |
| `- sel_cntr_qty` | String | N | 매도체결수량 |  | 20 |
| `- sel_cntr_amt` | String | N | 매도체결금액 |  | 20 |
| `- netprps_prica` | String | N | 순매수대금 |  | 20 |
| `- all_trde_rt` | String | N | 전체거래비율 |  | 20 |

---

## 프로그램매매추이요청 시간대별 `ka90005`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액(백만원), 2:수량(천주) | 1 |
| `mrkt_tp` | String | Y | 시장구분 | 코스피- 거래소구분값 1일경우:P00101, 2일경우:P001_NX01, 3일경우:P001_AL01
코스닥- 거래소구분값 1일경우:P10102, 2일경우:P101_NX02, 3일경우:P101_AL02 | 10 |
| `min_tic_tp` | String | Y | 분틱구분 | 0:틱, 1:분 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- dfrt_trde_sel` | String | N | 차익거래매도 |  | 20 |
| `- dfrt_trde_buy` | String | N | 차익거래매수 |  | 20 |
| `- dfrt_trde_netprps` | String | N | 차익거래순매수 |  | 20 |
| `- ndiffpro_trde_sel` | String | N | 비차익거래매도 |  | 20 |
| `- ndiffpro_trde_buy` | String | N | 비차익거래매수 |  | 20 |
| `- ndiffpro_trde_netprps` | String | N | 비차익거래순매수 |  | 20 |
| `- dfrt_trde_sell_qty` | String | N | 차익거래매도수량 |  | 20 |
| `- dfrt_trde_buy_qty` | String | N | 차익거래매수수량 |  | 20 |
| `- dfrt_trde_netprps_qty` | String | N | 차익거래순매수수량 |  | 20 |
| `- ndiffpro_trde_sell_qty` | String | N | 비차익거래매도수량 |  | 20 |
| `- ndiffpro_trde_buy_qty` | String | N | 비차익거래매수수량 |  | 20 |
| `- ndiffpro_trde_netprps_qty` | String | N | 비차익거래순매수수량 |  | 20 |
| `- all_sel` | String | N | 전체매도 |  | 20 |
| `- all_buy` | String | N | 전체매수 |  | 20 |
| `- all_netprps` | String | N | 전체순매수 |  | 20 |
| `- kospi200` | String | N | KOSPI200 |  | 20 |
| `- basis` | String | N | BASIS |  | 20 |

---

## 프로그램매매차익잔고추이요청 `ka90006`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- buy_dfrt_trde_qty` | String | N | 매수차익거래수량 |  | 20 |
| `- buy_dfrt_trde_amt` | String | N | 매수차익거래금액 |  | 20 |
| `- buy_dfrt_trde_irds_amt` | String | N | 매수차익거래증감액 |  | 20 |
| `- sel_dfrt_trde_qty` | String | N | 매도차익거래수량 |  | 20 |
| `- sel_dfrt_trde_amt` | String | N | 매도차익거래금액 |  | 20 |
| `- sel_dfrt_trde_irds_amt` | String | N | 매도차익거래증감액 |  | 20 |

---

## 프로그램매매누적추이요청 `ka90007`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액, 2:수량 | 1 |
| `mrkt_tp` | String | Y | 시장구분 | 0:코스피 , 1:코스닥 | 5 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- kospi200` | String | N | KOSPI200 |  | 20 |
| `- basis` | String | N | BASIS |  | 20 |
| `- dfrt_trde_tdy` | String | N | 차익거래당일 |  | 20 |
| `- dfrt_trde_acc` | String | N | 차익거래누적 |  | 20 |
| `- ndiffpro_trde_tdy` | String | N | 비차익거래당일 |  | 20 |
| `- ndiffpro_trde_acc` | String | N | 비차익거래누적 |  | 20 |
| `- all_tdy` | String | N | 전체당일 |  | 20 |
| `- all_acc` | String | N | 전체누적 |  | 20 |

---

## 종목시간별프로그램매매추이요청 `ka90008`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 6 |
| `date` | String | Y | 날짜 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- tm` | String | N | 시간 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- prm_sell_amt` | String | N | 프로그램매도금액 |  | 20 |
| `- prm_buy_amt` | String | N | 프로그램매수금액 |  | 20 |
| `- prm_netprps_amt` | String | N | 프로그램순매수금액 |  | 20 |
| `- prm_netprps_amt_irds` | String | N | 프로그램순매수금액증감 |  | 20 |
| `- prm_sell_qty` | String | N | 프로그램매도수량 |  | 20 |
| `- prm_buy_qty` | String | N | 프로그램매수수량 |  | 20 |
| `- prm_netprps_qty` | String | N | 프로그램순매수수량 |  | 20 |
| `- prm_netprps_qty_irds` | String | N | 프로그램순매수수량증감 |  | 20 |
| `- base_pric_tm` | String | N | 기준가시간 |  | 20 |
| `- dbrt_trde_rpy_sum` | String | N | 대차거래상환주수합 |  | 20 |
| `- remn_rcvord_sum` | String | N | 잔고수주합 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | KRX , NXT , 통합 | 20 |

---

## 외국인기관매매상위요청 `ka90009`

**Method**: `POST`  
**URL**: `/api/dostk/rkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액(천만), 2:수량(천) | 1 |
| `qry_dt_tp` | String | Y | 조회일자구분 | 0:조회일자 미포함, 1:조회일자 포함 | 1 |
| `date` | String | N | 날짜 | YYYYMMDD
(연도4자리, 월 2자리, 일 2자리 형식) | 8 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- for_netslmt_stk_cd` | String | N | 외인순매도종목코드 |  | 20 |
| `- for_netslmt_stk_nm` | String | N | 외인순매도종목명 |  | 20 |
| `- for_netslmt_amt` | String | N | 외인순매도금액 |  | 20 |
| `- for_netslmt_qty` | String | N | 외인순매도수량 |  | 20 |
| `- for_netprps_stk_cd` | String | N | 외인순매수종목코드 |  | 20 |
| `- for_netprps_stk_nm` | String | N | 외인순매수종목명 |  | 20 |
| `- for_netprps_amt` | String | N | 외인순매수금액 |  | 20 |
| `- for_netprps_qty` | String | N | 외인순매수수량 |  | 20 |
| `- orgn_netslmt_stk_cd` | String | N | 기관순매도종목코드 |  | 20 |
| `- orgn_netslmt_stk_nm` | String | N | 기관순매도종목명 |  | 20 |
| `- orgn_netslmt_amt` | String | N | 기관순매도금액 |  | 20 |
| `- orgn_netslmt_qty` | String | N | 기관순매도수량 |  | 20 |
| `- orgn_netprps_stk_cd` | String | N | 기관순매수종목코드 |  | 20 |
| `- orgn_netprps_stk_nm` | String | N | 기관순매수종목명 |  | 20 |
| `- orgn_netprps_amt` | String | N | 기관순매수금액 |  | 20 |
| `- orgn_netprps_qty` | String | N | 기관순매수수량 |  | 20 |

---

## 프로그램매매추이요청 일자별 `ka90010`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `amt_qty_tp` | String | Y | 금액수량구분 | 1:금액(백만원), 2:수량(천주) | 1 |
| `mrkt_tp` | String | Y | 시장구분 | 코스피- 거래소구분값 1일경우:P00101, 2일경우:P001_NX01, 3일경우:P001_AL01
코스닥- 거래소구분값 1일경우:P10102, 2일경우:P101_NX02, 3일경우:P001_AL02 | 10 |
| `min_tic_tp` | String | Y | 분틱구분 | 0:틱, 1:분 | 1 |
| `stex_tp` | String | Y | 거래소구분 | 1:KRX, 2:NXT 3.통합 | 1 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- cntr_tm` | String | N | 체결시간 |  | 20 |
| `- dfrt_trde_sel` | String | N | 차익거래매도 |  | 20 |
| `- dfrt_trde_buy` | String | N | 차익거래매수 |  | 20 |
| `- dfrt_trde_netprps` | String | N | 차익거래순매수 |  | 20 |
| `- ndiffpro_trde_sel` | String | N | 비차익거래매도 |  | 20 |
| `- ndiffpro_trde_buy` | String | N | 비차익거래매수 |  | 20 |
| `- ndiffpro_trde_netprps` | String | N | 비차익거래순매수 |  | 20 |
| `- dfrt_trde_sell_qty` | String | N | 차익거래매도수량 |  | 20 |
| `- dfrt_trde_buy_qty` | String | N | 차익거래매수수량 |  | 20 |
| `- dfrt_trde_netprps_qty` | String | N | 차익거래순매수수량 |  | 20 |
| `- ndiffpro_trde_sell_qty` | String | N | 비차익거래매도수량 |  | 20 |
| `- ndiffpro_trde_buy_qty` | String | N | 비차익거래매수수량 |  | 20 |
| `- ndiffpro_trde_netprps_qty` | String | N | 비차익거래순매수수량 |  | 20 |
| `- all_sel` | String | N | 전체매도 |  | 20 |
| `- all_buy` | String | N | 전체매수 |  | 20 |
| `- all_netprps` | String | N | 전체순매수 |  | 20 |
| `- kospi200` | String | N | KOSPI200 |  | 20 |
| `- basis` | String | N | BASIS |  | 20 |

---

## 대차거래내역요청 `ka90012`

**Method**: `POST`  
**URL**: `/api/dostk/slb`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `mrkt_tp` | String | Y | 시장구분 | 001:코스피, 101:코스닥 | 3 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- stk_cd` | String | N | 종목코드 |  | 20 |
| `- dbrt_trde_cntrcnt` | String | N | 대차거래체결주수 |  | 20 |
| `- dbrt_trde_rpy` | String | N | 대차거래상환주수 |  | 20 |
| `- rmnd` | String | N | 잔고주수 |  | 20 |
| `- remn_amt` | String | N | 잔고금액 |  | 20 |

---

## 종목일별프로그램매매추이요청 `ka90013`

**Method**: `POST`  
**URL**: `/api/dostk/mrkcond`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 20 |
| `date` | String | N | 날짜 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 20 |
| `- cur_prc` | String | N | 현재가 |  | 20 |
| `- pre_sig` | String | N | 대비기호 |  | 20 |
| `- pred_pre` | String | N | 전일대비 |  | 20 |
| `- flu_rt` | String | N | 등락율 |  | 20 |
| `- trde_qty` | String | N | 거래량 |  | 20 |
| `- prm_sell_amt` | String | N | 프로그램매도금액 |  | 20 |
| `- prm_buy_amt` | String | N | 프로그램매수금액 |  | 20 |
| `- prm_netprps_amt` | String | N | 프로그램순매수금액 |  | 20 |
| `- prm_netprps_amt_irds` | String | N | 프로그램순매수금액증감 |  | 20 |
| `- prm_sell_qty` | String | N | 프로그램매도수량 |  | 20 |
| `- prm_buy_qty` | String | N | 프로그램매수수량 |  | 20 |
| `- prm_netprps_qty` | String | N | 프로그램순매수수량 |  | 20 |
| `- prm_netprps_qty_irds` | String | N | 프로그램순매수수량증감 |  | 20 |
| `- base_pric_tm` | String | N | 기준가시간 |  | 20 |
| `- dbrt_trde_rpy_sum` | String | N | 대차거래상환주수합 |  | 20 |
| `- remn_rcvord_sum` | String | N | 잔고수주합 |  | 20 |
| `- stex_tp` | String | N | 거래소구분 | KRX , NXT , 통합 | 20 |

---

## 예수금상세현황요청 `kt00001`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `profa_ch` | String | N | 주식증거금현금 |  | 15 |
| `bncr_profa_ch` | String | N | 수익증권증거금현금 |  | 15 |
| `nxdy_bncr_sell_exct` | String | N | 익일수익증권매도정산대금 |  | 15 |
| `fc_stk_krw_repl_set_amt` | String | N | 해외주식원화대용설정금 |  | 15 |
| `crd_grnta_ch` | String | N | 신용보증금현금 |  | 15 |
| `crd_grnt_ch` | String | N | 신용담보금현금 |  | 15 |
| `add_grnt_ch` | String | N | 추가담보금현금 |  | 15 |
| `etc_profa` | String | N | 기타증거금 |  | 15 |
| `uncl_stk_amt` | String | N | 미수확보금 |  | 15 |
| `shrts_prica` | String | N | 공매도대금 |  | 15 |
| `crd_set_grnta` | String | N | 신용설정평가금 |  | 15 |
| `chck_ina_amt` | String | N | 수표입금액 |  | 15 |
| `etc_chck_ina_amt` | String | N | 기타수표입금액 |  | 15 |
| `crd_grnt_ruse` | String | N | 신용담보재사용 |  | 15 |
| `knx_asset_evltv` | String | N | 코넥스기본예탁금 |  | 15 |
| `elwdpst_evlta` | String | N | ELW예탁평가금 |  | 15 |
| `crd_ls_rght_frcs_amt` | String | N | 신용대주권리예정금액 |  | 15 |
| `lvlh_join_amt` | String | N | 생계형가입금액 |  | 15 |
| `lvlh_trns_alowa` | String | N | 생계형입금가능금액 |  | 15 |
| `repl_amt` | String | N | 대용금평가금액(합계) |  | 15 |
| `remn_repl_evlta` | String | N | 잔고대용평가금액 |  | 15 |
| `trst_remn_repl_evlta` | String | N | 위탁대용잔고평가금액 |  | 15 |
| `bncr_remn_repl_evlta` | String | N | 수익증권대용평가금액 |  | 15 |
| `profa_repl` | String | N | 위탁증거금대용 |  | 15 |
| `crd_grnta_repl` | String | N | 신용보증금대용 |  | 15 |
| `crd_grnt_repl` | String | N | 신용담보금대용 |  | 15 |
| `add_grnt_repl` | String | N | 추가담보금대용 |  | 15 |
| `rght_repl_amt` | String | N | 권리대용금 |  | 15 |
| `pymn_alow_amt` | String | N | 출금가능금액 |  | 15 |
| `wrap_pymn_alow_amt` | String | N | 랩출금가능금액 |  | 15 |
| `ord_alow_amt` | String | N | 주문가능금액 |  | 15 |
| `bncr_buy_alowa` | String | N | 수익증권매수가능금액 |  | 15 |
| `20stk_ord_alow_amt` | String | N | 20%종목주문가능금액 |  | 15 |
| `30stk_ord_alow_amt` | String | N | 30%종목주문가능금액 |  | 15 |
| `40stk_ord_alow_amt` | String | N | 40%종목주문가능금액 |  | 15 |
| `100stk_ord_alow_amt` | String | N | 100%종목주문가능금액 |  | 15 |
| `ch_uncla` | String | N | 현금미수금 |  | 15 |
| `ch_uncla_dlfe` | String | N | 현금미수연체료 |  | 15 |
| `ch_uncla_tot` | String | N | 현금미수금합계 |  | 15 |
| `crd_int_npay` | String | N | 신용이자미납 |  | 15 |
| `int_npay_amt_dlfe` | String | N | 신용이자미납연체료 |  | 15 |
| `int_npay_amt_tot` | String | N | 신용이자미납합계 |  | 15 |
| `etc_loana` | String | N | 기타대여금 |  | 15 |
| `etc_loana_dlfe` | String | N | 기타대여금연체료 |  | 15 |
| `etc_loan_tot` | String | N | 기타대여금합계 |  | 15 |
| `nrpy_loan` | String | N | 미상환융자금 |  | 15 |
| `loan_sum` | String | N | 융자금합계 |  | 15 |
| `ls_sum` | String | N | 대주금합계 |  | 15 |
| `crd_grnt_rt` | String | N | 신용담보비율 |  | 15 |
| `mdstrm_usfe` | String | N | 중도이용료 |  | 15 |
| `min_ord_alow_yn` | String | N | 최소주문가능금액 |  | 15 |
| `loan_remn_evlt_amt` | String | N | 대출총평가금액 |  | 15 |
| `dpst_grntl_remn` | String | N | 예탁담보대출잔고 |  | 15 |
| `sell_grntl_remn` | String | N | 매도담보대출잔고 |  | 15 |
| `d1_entra` | String | N | d+1추정예수금 |  | 15 |
| `d1_slby_exct_amt` | String | N | d+1매도매수정산금 |  | 15 |
| `d1_buy_exct_amt` | String | N | d+1매수정산금 |  | 15 |
| `d1_out_rep_mor` | String | N | d+1미수변제소요금 |  | 15 |
| `d1_sel_exct_amt` | String | N | d+1매도정산금 |  | 15 |
| `d1_pymn_alow_amt` | String | N | d+1출금가능금액 |  | 15 |
| `d2_entra` | String | N | d+2추정예수금 |  | 15 |
| `d2_slby_exct_amt` | String | N | d+2매도매수정산금 |  | 15 |
| `d2_buy_exct_amt` | String | N | d+2매수정산금 |  | 15 |
| `d2_out_rep_mor` | String | N | d+2미수변제소요금 |  | 15 |
| `d2_sel_exct_amt` | String | N | d+2매도정산금 |  | 15 |
| `d2_pymn_alow_amt` | String | N | d+2출금가능금액 |  | 15 |
| `50stk_ord_alow_amt` | String | N | 50%종목주문가능금액 |  | 15 |
| `60stk_ord_alow_amt` | String | N | 60%종목주문가능금액 |  | 15 |
| `stk_entr_prst` | LIST | N | 종목별예수금 |  |  |
| `- crnc_cd` | String | N | 통화코드 |  | 3 |
| `- fx_entr` | String | N | 외화예수금 |  | 15 |
| `- fc_krw_repl_evlta` | String | N | 원화대용평가금 |  | 15 |
| `- fc_trst_profa` | String | N | 해외주식증거금 |  | 15 |
| `- pymn_alow_amt` | String | N | 출금가능금액 |  | 15 |
| `- pymn_alow_amt_entr` | String | N | 출금가능금액(예수금) |  | 15 |
| `- ord_alow_amt_entr` | String | N | 주문가능금액(예수금) |  | 15 |
| `- fc_uncla` | String | N | 외화미수(합계) |  | 15 |
| `- fc_ch_uncla` | String | N | 외화현금미수금 |  | 15 |
| `- dly_amt` | String | N | 연체료 |  | 15 |
| `- d1_fx_entr` | String | N | d+1외화예수금 |  | 15 |
| `- d2_fx_entr` | String | N | d+2외화예수금 |  | 15 |
| `- d3_fx_entr` | String | N | d+3외화예수금 |  | 15 |
| `- d4_fx_entr` | String | N | d+4외화예수금 |  | 15 |

---

## 일별추정예탁자산현황요청 `kt00002`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | Y | 종료조회기간 | YYYYMMDD | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- dt` | String | N | 일자 |  | 8 |
| `- entr` | String | N | 예수금 |  | 12 |
| `- grnt_use_amt` | String | N | 담보대출금 |  | 12 |
| `- crd_loan` | String | N | 신용융자금 |  | 12 |
| `- ls_grnt` | String | N | 대주담보금 |  | 12 |
| `- repl_amt` | String | N | 대용금 |  | 12 |
| `- prsm_dpst_aset_amt` | String | N | 추정예탁자산 |  | 12 |
| `- prsm_dpst_aset_amt_bncr_skip` | String | N | 추정예탁자산수익증권제외 |  | 12 |

---

## 추정자산조회요청 `kt00003`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

---

## 계좌평가현황요청 `kt00004`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dmst_stex_tp` | String | Y | 국내거래소구분 | KRX:한국거래소,NXT:넥스트트레이드 | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `brch_nm` | String | N | 지점명 |  | 30 |
| `entr` | String | N | 예수금 |  | 12 |
| `d2_entra` | String | N | D+2추정예수금 |  | 12 |
| `tot_est_amt` | String | N | 유가잔고평가액 |  | 12 |
| `aset_evlt_amt` | String | N | 예탁자산평가액 |  | 12 |
| `tot_pur_amt` | String | N | 총매입금액 |  | 12 |
| `prsm_dpst_aset_amt` | String | N | 추정예탁자산 |  | 12 |
| `tot_grnt_sella` | String | N | 매도담보대출금 |  | 12 |
| `tdy_lspft_amt` | String | N | 당일투자원금 |  | 12 |
| `invt_bsamt` | String | N | 당월투자원금 |  | 12 |
| `lspft_amt` | String | N | 누적투자원금 |  | 12 |
| `tdy_lspft` | String | N | 당일투자손익 |  | 12 |
| `lspft2` | String | N | 당월투자손익 |  | 12 |
| `lspft` | String | N | 누적투자손익 |  | 12 |
| `tdy_lspft_rt` | String | N | 당일손익율 |  | 12 |
| `lspft_ratio` | String | N | 당월손익율 |  | 12 |
| `lspft_rt` | String | N | 누적손익율 |  | 12 |
| `stk_acnt_evlt_prst` | LIST | N | 종목별계좌평가현황 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 12 |
| `- stk_nm` | String | N | 종목명 |  | 30 |
| `- rmnd_qty` | String | N | 보유수량 |  | 12 |
| `- avg_prc` | String | N | 평균단가 |  | 12 |
| `- cur_prc` | String | N | 현재가 |  | 12 |
| `- evlt_amt` | String | N | 평가금액 |  | 12 |
| `- pl_amt` | String | N | 손익금액 |  | 12 |
| `- pl_rt` | String | N | 손익율 |  | 12 |
| `- loan_dt` | String | N | 대출일 |  | 10 |
| `- pur_amt` | String | N | 매입금액 |  | 12 |
| `- setl_remn` | String | N | 결제잔고 |  | 12 |
| `- pred_buyq` | String | N | 전일매수수량 |  | 12 |
| `- pred_sellq` | String | N | 전일매도수량 |  | 12 |
| `- tdy_buyq` | String | N | 금일매수수량 |  | 12 |
| `- tdy_sellq` | String | N | 금일매도수량 |  | 12 |

---

## 체결잔고요청 `kt00005`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `entr_d1` | String | N | 예수금D+1 |  | 12 |
| `entr_d2` | String | N | 예수금D+2 |  | 12 |
| `pymn_alow_amt` | String | N | 출금가능금액 |  | 12 |
| `uncl_stk_amt` | String | N | 미수확보금 |  | 12 |
| `repl_amt` | String | N | 대용금 |  | 12 |
| `rght_repl_amt` | String | N | 권리대용금 |  | 12 |
| `ord_alowa` | String | N | 주문가능현금 |  | 12 |
| `ch_uncla` | String | N | 현금미수금 |  | 12 |
| `crd_int_npay_gold` | String | N | 신용이자미납금 |  | 12 |
| `etc_loana` | String | N | 기타대여금 |  | 12 |
| `nrpy_loan` | String | N | 미상환융자금 |  | 12 |
| `profa_ch` | String | N | 증거금현금 |  | 12 |
| `repl_profa` | String | N | 증거금대용 |  | 12 |
| `stk_buy_tot_amt` | String | N | 주식매수총액 |  | 12 |
| `evlt_amt_tot` | String | N | 평가금액합계 |  | 12 |
| `tot_pl_tot` | String | N | 총손익합계 |  | 12 |
| `tot_pl_rt` | String | N | 총손익률 |  | 12 |
| `tot_re_buy_alowa` | String | N | 총재매수가능금액 |  | 12 |
| `20ord_alow_amt` | String | N | 20%주문가능금액 |  | 12 |
| `30ord_alow_amt` | String | N | 30%주문가능금액 |  | 12 |
| `40ord_alow_amt` | String | N | 40%주문가능금액 |  | 12 |
| `50ord_alow_amt` | String | N | 50%주문가능금액 |  | 12 |
| `60ord_alow_amt` | String | N | 60%주문가능금액 |  | 12 |
| `100ord_alow_amt` | String | N | 100%주문가능금액 |  | 12 |
| `crd_loan_tot` | String | N | 신용융자합계 |  | 12 |
| `crd_loan_ls_tot` | String | N | 신용융자대주합계 |  | 12 |
| `crd_grnt_rt` | String | N | 신용담보비율 |  | 12 |
| `dpst_grnt_use_amt_amt` | String | N | 예탁담보대출금액 |  | 12 |
| `grnt_loan_amt` | String | N | 매도담보대출금액 |  | 12 |
| `stk_cntr_remn` | LIST | N | 종목별체결잔고 |  |  |
| `- crd_tp` | String | N | 신용구분 |  | 2 |
| `- loan_dt` | String | N | 대출일 |  | 8 |
| `- expr_dt` | String | N | 만기일 |  | 8 |
| `- stk_cd` | String | N | 종목번호 |  | 12 |
| `- stk_nm` | String | N | 종목명 |  | 30 |
| `- setl_remn` | String | N | 결제잔고 |  | 12 |
| `- cur_qty` | String | N | 현재잔고 |  | 12 |
| `- cur_prc` | String | N | 현재가 |  | 12 |
| `- buy_uv` | String | N | 매입단가 |  | 12 |
| `- pur_amt` | String | N | 매입금액 |  | 12 |
| `- evlt_amt` | String | N | 평가금액 |  | 12 |
| `- evltv_prft` | String | N | 평가손익 |  | 12 |
| `- pl_rt` | String | N | 손익률 |  | 12 |

---

## 계좌별주문체결내역상세요청 `kt00007`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `qry_tp` | String | Y | 조회구분 | 1:주문순, 2:역순, 3:미체결, 4:체결내역만 | 1 |
| `stk_bond_tp` | String | Y | 주식채권구분 | 0:전체, 1:주식, 2:채권 | 1 |
| `sell_tp` | String | Y | 매도수구분 | 0:전체, 1:매도, 2:매수 | 1 |
| `stk_cd` | String | N | 종목코드 | 공백허용 (공백일때 전체종목) | 12 |
| `fr_ord_no` | String | N | 시작주문번호 | 공백허용 (공백일때 전체주문) | 7 |
| `dmst_stex_tp` | String | Y | 국내거래소구분 | %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행 | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- ord_no` | String | N | 주문번호 |  | 7 |
| `- stk_cd` | String | N | 종목번호 |  | 12 |
| `- trde_tp` | String | N | 매매구분 |  | 20 |
| `- crd_tp` | String | N | 신용구분 |  | 20 |
| `- ord_qty` | String | N | 주문수량 |  | 10 |
| `- ord_uv` | String | N | 주문단가 |  | 10 |
| `- cnfm_qty` | String | N | 확인수량 |  | 10 |
| `- acpt_tp` | String | N | 접수구분 |  | 20 |
| `- rsrv_tp` | String | N | 반대여부 |  | 20 |
| `- ord_tm` | String | N | 주문시간 |  | 8 |
| `- ori_ord` | String | N | 원주문 |  | 7 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- io_tp_nm` | String | N | 주문구분 |  | 20 |
| `- loan_dt` | String | N | 대출일 |  | 8 |
| `- cntr_qty` | String | N | 체결수량 |  | 10 |
| `- cntr_uv` | String | N | 체결단가 |  | 10 |
| `- ord_remnq` | String | N | 주문잔량 |  | 10 |
| `- comm_ord_tp` | String | N | 통신구분 |  | 20 |
| `- mdfy_cncl` | String | N | 정정취소 |  | 20 |
| `- cnfm_tm` | String | N | 확인시간 |  | 8 |
| `- dmst_stex_tp` | String | N | 국내거래소구분 |  | 8 |
| `- cond_uv` | String | N | 스톱가 |  | 10 |

---

## 계좌별익일결제예정내역요청 `kt00008`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `setl_dt` | String | N | 결제일자 |  | 8 |
| `sell_amt_sum` | String | N | 매도정산합 |  | 12 |
| `buy_amt_sum` | String | N | 매수정산합 |  | 12 |
| `acnt_nxdy_setl_frcs_prps_array` | LIST | N | 계좌별익일결제예정내역배열 |  |  |
| `- seq` | String | N | 일련번호 |  | 7 |
| `- stk_cd` | String | N | 종목번호 |  | 12 |
| `- loan_dt` | String | N | 대출일 |  | 8 |
| `- qty` | String | N | 수량 |  | 12 |
| `- engg_amt` | String | N | 약정금액 |  | 12 |
| `- cmsn` | String | N | 수수료 |  | 12 |
| `- incm_tax` | String | N | 소득세 |  | 12 |
| `- rstx` | String | N | 농특세 |  | 12 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- sell_tp` | String | N | 매도수구분 |  | 10 |
| `- unp` | String | N | 단가 |  | 12 |
| `- exct_amt` | String | N | 정산금액 |  | 12 |
| `- trde_tax` | String | N | 거래세 |  | 12 |
| `- resi_tax` | String | N | 주민세 |  | 12 |
| `- crd_tp` | String | N | 신용구분 |  | 20 |

---

## 계좌별주문체결현황요청 `kt00009`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_bond_tp` | String | Y | 주식채권구분 | 0:전체, 1:주식, 2:채권 | 1 |
| `mrkt_tp` | String | Y | 시장구분 | 0:전체, 1:코스피, 2:코스닥, 3:OTCBB, 4:ECN | 1 |
| `sell_tp` | String | Y | 매도수구분 | 0:전체, 1:매도, 2:매수 | 1 |
| `qry_tp` | String | Y | 조회구분 | 0:전체, 1:체결 | 1 |
| `stk_cd` | String | N | 종목코드 | 전문 조회할 종목코드 | 12 |
| `fr_ord_no` | String | N | 시작주문번호 |  | 7 |
| `dmst_stex_tp` | String | Y | 국내거래소구분 | %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행 | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `buy_engg_amt` | String | N | 매수약정금액 |  | 12 |
| `engg_amt` | String | N | 약정금액 |  | 12 |
| `acnt_ord_cntr_prst_array` | LIST | N | 계좌별주문체결현황배열 |  |  |
| `- stk_bond_tp` | String | N | 주식채권구분 |  | 1 |
| `- ord_no` | String | N | 주문번호 |  | 7 |
| `- stk_cd` | String | N | 종목번호 |  | 12 |
| `- trde_tp` | String | N | 매매구분 |  | 15 |
| `- io_tp_nm` | String | N | 주문유형구분 |  | 20 |
| `- ord_qty` | String | N | 주문수량 |  | 10 |
| `- ord_uv` | String | N | 주문단가 |  | 10 |
| `- cnfm_qty` | String | N | 확인수량 |  | 10 |
| `- rsrv_oppo` | String | N | 예약/반대 |  | 4 |
| `- cntr_no` | String | N | 체결번호 |  | 7 |
| `- acpt_tp` | String | N | 접수구분 |  | 8 |
| `- orig_ord_no` | String | N | 원주문번호 |  | 7 |
| `- stk_nm` | String | N | 종목명 |  | 20 |
| `- setl_tp` | String | N | 결제구분 |  | 8 |
| `- crd_deal_tp` | String | N | 신용거래구분 |  | 20 |
| `- cntr_qty` | String | N | 체결수량 |  | 10 |
| `- cntr_uv` | String | N | 체결단가 |  | 10 |
| `- comm_ord_tp` | String | N | 통신구분 |  | 8 |
| `- mdfy_cncl_tp` | String | N | 정정/취소구분 |  | 12 |
| `- cntr_tm` | String | N | 체결시간 |  | 8 |
| `- dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |
| `- cond_uv` | String | N | 스톱가 |  | 10 |

---

## 주문인출가능금액요청 `kt00010`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목번호 |  | 12 |
| `trde_tp` | String | Y | 매매구분 | 1:매도, 2:매수 | 1 |
| `trde_qty` | String | N | 매매수량 |  | 10 |
| `uv` | String | Y | 매수가격 |  | 10 |
| `exp_buy_unp` | String | N | 예상매수단가 |  | 10 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `profa_20ord_alowq` | String | N | 증거금20%주문가능수량 |  | 10 |
| `profa_30ord_alow_amt` | String | N | 증거금30%주문가능금액 |  | 12 |
| `profa_30ord_alowq` | String | N | 증거금30%주문가능수량 |  | 10 |
| `profa_40ord_alow_amt` | String | N | 증거금40%주문가능금액 |  | 12 |
| `profa_40ord_alowq` | String | N | 증거금40%주문가능수량 |  | 10 |
| `profa_50ord_alow_amt` | String | N | 증거금50%주문가능금액 |  | 12 |
| `profa_50ord_alowq` | String | N | 증거금50%주문가능수량 |  | 10 |
| `profa_60ord_alow_amt` | String | N | 증거금60%주문가능금액 |  | 12 |
| `profa_60ord_alowq` | String | N | 증거금60%주문가능수량 |  | 10 |
| `profa_rdex_60ord_alow_amt` | String | N | 증거금감면60%주문가능금 |  | 12 |
| `profa_rdex_60ord_alowq` | String | N | 증거금감면60%주문가능수 |  | 10 |
| `profa_100ord_alow_amt` | String | N | 증거금100%주문가능금액 |  | 12 |
| `profa_100ord_alowq` | String | N | 증거금100%주문가능수량 |  | 10 |
| `pred_reu_alowa` | String | N | 전일재사용가능금액 |  | 12 |
| `tdy_reu_alowa` | String | N | 금일재사용가능금액 |  | 12 |
| `entr` | String | N | 예수금 |  | 12 |
| `repl_amt` | String | N | 대용금 |  | 12 |
| `uncla` | String | N | 미수금 |  | 12 |
| `ord_pos_repl` | String | N | 주문가능대용 |  | 12 |
| `ord_alowa` | String | N | 주문가능현금 |  | 12 |
| `wthd_alowa` | String | N | 인출가능금액 |  | 12 |
| `nxdy_wthd_alowa` | String | N | 익일인출가능금액 |  | 12 |
| `pur_amt` | String | N | 매입금액 |  | 12 |
| `cmsn` | String | N | 수수료 |  | 12 |
| `pur_exct_amt` | String | N | 매입정산금 |  | 12 |
| `d2entra` | String | N | D2추정예수금 |  | 12 |
| `profa_rdex_aplc_tp` | String | N | 증거금감면적용구분 | 0:일반,1:60%감면 | 1 |

---

## 증거금율별주문가능수량조회요청 `kt00011`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `uv` | String | N | 매수가격 |  | 10 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `profa_rt` | String | N | 계좌증거금율 |  | 15 |
| `aplc_rt` | String | N | 적용증거금율 |  | 15 |
| `profa_20ord_alow_amt` | String | N | 증거금20%주문가능금액 |  | 12 |
| `profa_20ord_alowq` | String | N | 증거금20%주문가능수량 |  | 12 |
| `profa_20pred_reu_amt` | String | N | 증거금20%전일재사용금액 |  | 12 |
| `profa_20tdy_reu_amt` | String | N | 증거금20%금일재사용금액 |  | 12 |
| `profa_30ord_alow_amt` | String | N | 증거금30%주문가능금액 |  | 12 |
| `profa_30ord_alowq` | String | N | 증거금30%주문가능수량 |  | 12 |
| `profa_30pred_reu_amt` | String | N | 증거금30%전일재사용금액 |  | 12 |
| `profa_30tdy_reu_amt` | String | N | 증거금30%금일재사용금액 |  | 12 |
| `profa_40ord_alow_amt` | String | N | 증거금40%주문가능금액 |  | 12 |
| `profa_40ord_alowq` | String | N | 증거금40%주문가능수량 |  | 12 |
| `profa_40pred_reu_amt` | String | N | 증거금40전일재사용금액 |  | 12 |
| `profa_40tdy_reu_amt` | String | N | 증거금40%금일재사용금액 |  | 12 |
| `profa_50ord_alow_amt` | String | N | 증거금50%주문가능금액 |  | 12 |
| `profa_50ord_alowq` | String | N | 증거금50%주문가능수량 |  | 12 |
| `profa_50pred_reu_amt` | String | N | 증거금50%전일재사용금액 |  | 12 |
| `profa_50tdy_reu_amt` | String | N | 증거금50%금일재사용금액 |  | 12 |
| `profa_60ord_alow_amt` | String | N | 증거금60%주문가능금액 |  | 12 |
| `profa_60ord_alowq` | String | N | 증거금60%주문가능수량 |  | 12 |
| `profa_60pred_reu_amt` | String | N | 증거금60%전일재사용금액 |  | 12 |
| `profa_60tdy_reu_amt` | String | N | 증거금60%금일재사용금액 |  | 12 |
| `profa_100ord_alow_amt` | String | N | 증거금100%주문가능금액 |  | 12 |
| `profa_100ord_alowq` | String | N | 증거금100%주문가능수량 |  | 12 |
| `profa_100pred_reu_amt` | String | N | 증거금100%전일재사용금액 |  | 12 |
| `profa_100tdy_reu_amt` | String | N | 증거금100%금일재사용금액 |  | 12 |
| `min_ord_alow_amt` | String | N | 미수불가주문가능금액 |  | 12 |
| `min_ord_alowq` | String | N | 미수불가주문가능수량 |  | 12 |
| `min_pred_reu_amt` | String | N | 미수불가전일재사용금액 |  | 12 |
| `min_tdy_reu_amt` | String | N | 미수불가금일재사용금액 |  | 12 |
| `entr` | String | N | 예수금 |  | 12 |
| `repl_amt` | String | N | 대용금 |  | 12 |
| `uncla` | String | N | 미수금 |  | 12 |
| `ord_pos_repl` | String | N | 주문가능대용 |  | 12 |
| `ord_alowa` | String | N | 주문가능현금 |  | 12 |

---

## 신용보증금율별주문가능수량조회요청 `kt00012`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `uv` | String | N | 매수가격 |  | 10 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_assr_rt_nm` | String | N | 종목보증금율명 |  | 4 |
| `assr_30ord_alow_amt` | String | N | 보증금30%주문가능금액 |  | 12 |
| `assr_30ord_alowq` | String | N | 보증금30%주문가능수량 |  | 12 |
| `assr_30pred_reu_amt` | String | N | 보증금30%전일재사용금액 |  | 12 |
| `assr_30tdy_reu_amt` | String | N | 보증금30%금일재사용금액 |  | 12 |
| `assr_40ord_alow_amt` | String | N | 보증금40%주문가능금액 |  | 12 |
| `assr_40ord_alowq` | String | N | 보증금40%주문가능수량 |  | 12 |
| `assr_40pred_reu_amt` | String | N | 보증금40%전일재사용금액 |  | 12 |
| `assr_40tdy_reu_amt` | String | N | 보증금40%금일재사용금액 |  | 12 |
| `assr_50ord_alow_amt` | String | N | 보증금50%주문가능금액 |  | 12 |
| `assr_50ord_alowq` | String | N | 보증금50%주문가능수량 |  | 12 |
| `assr_50pred_reu_amt` | String | N | 보증금50%전일재사용금액 |  | 12 |
| `assr_50tdy_reu_amt` | String | N | 보증금50%금일재사용금액 |  | 12 |
| `assr_60ord_alow_amt` | String | N | 보증금60%주문가능금액 |  | 12 |
| `assr_60ord_alowq` | String | N | 보증금60%주문가능수량 |  | 12 |
| `assr_60pred_reu_amt` | String | N | 보증금60%전일재사용금액 |  | 12 |
| `assr_60tdy_reu_amt` | String | N | 보증금60%금일재사용금액 |  | 12 |
| `entr` | String | N | 예수금 |  | 12 |
| `repl_amt` | String | N | 대용금 |  | 12 |
| `uncla` | String | N | 미수금 |  | 12 |
| `ord_pos_repl` | String | N | 주문가능대용 |  | 12 |
| `ord_alowa` | String | N | 주문가능현금 |  | 12 |
| `out_alowa` | String | N | 미수가능금액 |  | 12 |
| `out_pos_qty` | String | N | 미수가능수량 |  | 12 |
| `min_amt` | String | N | 미수불가금액 |  | 12 |
| `min_qty` | String | N | 미수불가수량 |  | 12 |

---

## 증거금세부내역조회요청 `kt00013`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tdy_reu_use_amt` | String | N | 금일재사용사용금액 |  | 15 |
| `tdy_reu_alowa` | String | N | 금일재사용가능금액 |  | 15 |
| `tdy_reu_lmtt_amt` | String | N | 금일재사용제한금액 |  | 15 |
| `tdy_reu_alowa_fin` | String | N | 금일재사용가능금액최종 |  | 15 |
| `pred_reu_objt_amt` | String | N | 전일재사용대상금액 |  | 15 |
| `pred_reu_use_amt` | String | N | 전일재사용사용금액 |  | 15 |
| `pred_reu_alowa` | String | N | 전일재사용가능금액 |  | 15 |
| `pred_reu_lmtt_amt` | String | N | 전일재사용제한금액 |  | 15 |
| `pred_reu_alowa_fin` | String | N | 전일재사용가능금액최종 |  | 15 |
| `ch_amt` | String | N | 현금금액 |  | 15 |
| `ch_profa` | String | N | 현금증거금 |  | 15 |
| `use_pos_ch` | String | N | 사용가능현금 |  | 15 |
| `ch_use_lmtt_amt` | String | N | 현금사용제한금액 |  | 15 |
| `use_pos_ch_fin` | String | N | 사용가능현금최종 |  | 15 |
| `repl_amt_amt` | String | N | 대용금액 |  | 15 |
| `repl_profa` | String | N | 대용증거금 |  | 15 |
| `use_pos_repl` | String | N | 사용가능대용 |  | 15 |
| `repl_use_lmtt_amt` | String | N | 대용사용제한금액 |  | 15 |
| `use_pos_repl_fin` | String | N | 사용가능대용최종 |  | 15 |
| `crd_grnta_ch` | String | N | 신용보증금현금 |  | 15 |
| `crd_grnta_repl` | String | N | 신용보증금대용 |  | 15 |
| `crd_grnt_ch` | String | N | 신용담보금현금 |  | 15 |
| `crd_grnt_repl` | String | N | 신용담보금대용 |  | 15 |
| `uncla` | String | N | 미수금 |  | 12 |
| `ls_grnt_reu_gold` | String | N | 대주담보금재사용금 |  | 15 |
| `20ord_alow_amt` | String | N | 20%주문가능금액 |  | 15 |
| `30ord_alow_amt` | String | N | 30%주문가능금액 |  | 15 |
| `40ord_alow_amt` | String | N | 40%주문가능금액 |  | 15 |
| `50ord_alow_amt` | String | N | 50%주문가능금액 |  | 15 |
| `60ord_alow_amt` | String | N | 60%주문가능금액 |  | 15 |
| `100ord_alow_amt` | String | N | 100%주문가능금액 |  | 15 |
| `tdy_crd_rpya_loss_amt` | String | N | 금일신용상환손실금액 |  | 15 |
| `pred_crd_rpya_loss_amt` | String | N | 전일신용상환손실금액 |  | 15 |
| `tdy_ls_rpya_loss_repl_profa` | String | N | 금일대주상환손실대용증거금 |  | 15 |
| `pred_ls_rpya_loss_repl_profa` | String | N | 전일대주상환손실대용증거금 |  | 15 |
| `evlt_repl_amt_spg_use_skip` | String | N | 평가대용금(현물사용제외) |  | 15 |
| `evlt_repl_rt` | String | N | 평가대용비율 |  | 15 |
| `crd_repl_profa` | String | N | 신용대용증거금 |  | 15 |
| `ch_ord_repl_profa` | String | N | 현금주문대용증거금 |  | 15 |
| `crd_ord_repl_profa` | String | N | 신용주문대용증거금 |  | 15 |
| `crd_repl_conv_gold` | String | N | 신용대용환산금 |  | 15 |
| `repl_alowa` | String | N | 대용가능금액(현금제한) |  | 15 |
| `repl_alowa_2` | String | N | 대용가능금액2(신용제한) |  | 15 |
| `ch_repl_lck_gold` | String | N | 현금대용부족금 |  | 15 |
| `crd_repl_lck_gold` | String | N | 신용대용부족금 |  | 15 |
| `ch_ord_alow_repla` | String | N | 현금주문가능대용금 |  | 15 |
| `crd_ord_alow_repla` | String | N | 신용주문가능대용금 |  | 15 |
| `d2vexct_entr` | String | N | D2가정산예수금 |  | 15 |
| `d2ch_ord_alow_amt` | String | N | D2현금주문가능금액 |  | 15 |

---

## 위탁종합거래내역요청 `kt00015`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | Y | 종료일자 |  | 8 |
| `tp` | String | Y | 구분 | 0:전체,1:입출금,2:입출고,3:매매,4:매수,5:매도,6:입금,7:출금,A:예탁담보대출입금,B:매도담보대출입금,C:현금상환(융자,담보상환),F:환전,M:입출금+환전,G:외화매수,H:외화매도,I:환전정산입금,J:환전정산출금 | 1 |
| `stk_cd` | String | N | 종목코드 |  | 12 |
| `crnc_cd` | String | N | 통화코드 |  | 3 |
| `gds_tp` | String | Y | 상품구분 | 0:전체, 1:국내주식, 2:수익증권, 3:해외주식, 4:금융상품 | 1 |
| `frgn_stex_code` | String | N | 해외거래소코드 |  | 10 |
| `dmst_stex_tp` | String | Y | 국내거래소구분 | %:(전체),KRX:한국거래소,NXT:넥스트트레이드 | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- trde_dt` | String | N | 거래일자 |  | 8 |
| `- trde_no` | String | N | 거래번호 |  | 9 |
| `- rmrk_nm` | String | N | 적요명 |  | 60 |
| `- crd_deal_tp_nm` | String | N | 신용거래구분명 |  | 20 |
| `- exct_amt` | String | N | 정산금액 |  | 15 |
| `- loan_amt_rpya` | String | N | 대출금상환 |  | 15 |
| `- fc_trde_amt` | String | N | 거래금액(외) |  | 15 |
| `- fc_exct_amt` | String | N | 정산금액(외) |  | 15 |
| `- entra_remn` | String | N | 예수금잔고 |  | 15 |
| `- crnc_cd` | String | N | 통화코드 |  | 3 |
| `- trde_ocr_tp` | String | N | 거래종류구분 | 1:입출금, 2:펀드, 3:ELS, 4:채권, 5:해외채권, 6:외화RP, 7:외화발행어음 | 2 |
| `- trde_kind_nm` | String | N | 거래종류명 |  | 20 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- trde_amt` | String | N | 거래금액 |  | 15 |
| `- trde_agri_tax` | String | N | 거래및농특세 |  | 15 |
| `- rpy_diffa` | String | N | 상환차금 |  | 15 |
| `- fc_trde_tax` | String | N | 거래세(외) |  | 15 |
| `- dly_sum` | String | N | 연체합 |  | 15 |
| `- fc_entra` | String | N | 외화예수금잔고 |  | 15 |
| `- mdia_tp_nm` | String | N | 매체구분명 |  | 20 |
| `- io_tp` | String | N | 입출구분 |  | 1 |
| `- io_tp_nm` | String | N | 입출구분명 |  | 10 |
| `- orig_deal_no` | String | N | 원거래번호 |  | 9 |
| `- stk_cd` | String | N | 종목코드 |  | 12 |
| `- trde_qty_jwa_cnt` | String | N | 거래수량/좌수 |  | 30 |
| `- cmsn` | String | N | 수수료 |  | 15 |
| `- int_ls_usfe` | String | N | 이자/대주이용 |  | 15 |
| `- fc_cmsn` | String | N | 수수료(외) |  | 15 |
| `- fc_dly_sum` | String | N | 연체합(외) |  | 15 |
| `- vlbl_nowrm` | String | N | 유가금잔 |  | 30 |
| `- proc_tm` | String | N | 처리시간 |  | 111 |
| `- isin_cd` | String | N | ISIN코드 |  | 12 |
| `- stex_cd` | String | N | 거래소코드 |  | 10 |
| `- stex_nm` | String | N | 거래소명 |  | 20 |
| `- trde_unit` | String | N | 거래단가/환율 |  | 20 |
| `- incm_resi_tax` | String | N | 소득/주민세 |  | 15 |
| `- loan_dt` | String | N | 대출일 |  | 8 |
| `- uncl_ocr` | String | N | 미수(원/주) |  | 30 |
| `- rpym_sum` | String | N | 변제합 |  | 30 |
| `- cntr_dt` | String | N | 체결일 |  | 8 |
| `- rcpy_no` | String | N | 출납번호 |  | 20 |
| `- prcsr` | String | N | 처리자 |  | 20 |
| `- proc_brch` | String | N | 처리점 |  | 20 |
| `- trde_stle` | String | N | 매매형태 |  | 40 |
| `- txon_base_pric` | String | N | 과세기준가 |  | 15 |
| `- tax_sum_cmsn` | String | N | 세금수수료합 |  | 15 |
| `- frgn_pay_txam` | String | N | 외국납부세액(외) |  | 15 |
| `- fc_uncl_ocr` | String | N | 미수(외) |  | 15 |
| `- rpym_sum_fr` | String | N | 변제합(외) |  | 30 |
| `- rcpmnyer` | String | N | 입금자 |  | 20 |
| `- trde_prtc_tp` | String | N | 거래내역구분 |  | 2 |

---

## 일별계좌수익률상세현황요청 `kt00016`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `to_dt` | String | Y | 평가종료일 |  | 8 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `mngr_nm` | String | N | 관리자명 |  | 8 |
| `dept_nm` | String | N | 관리자지점 |  | 30 |
| `entr_fr` | String | N | 예수금_초 |  | 30 |
| `entr_to` | String | N | 예수금_말 |  | 12 |
| `scrt_evlt_amt_fr` | String | N | 유가증권평가금액_초 |  | 12 |
| `scrt_evlt_amt_to` | String | N | 유가증권평가금액_말 |  | 12 |
| `ls_grnt_fr` | String | N | 대주담보금_초 |  | 12 |
| `ls_grnt_to` | String | N | 대주담보금_말 |  | 12 |
| `crd_loan_fr` | String | N | 신용융자금_초 |  | 12 |
| `crd_loan_to` | String | N | 신용융자금_말 |  | 12 |
| `ch_uncla_fr` | String | N | 현금미수금_초 |  | 12 |
| `ch_uncla_to` | String | N | 현금미수금_말 |  | 12 |
| `krw_asgna_fr` | String | N | 원화대용금_초 |  | 12 |
| `krw_asgna_to` | String | N | 원화대용금_말 |  | 12 |
| `ls_evlta_fr` | String | N | 대주평가금_초 |  | 12 |
| `ls_evlta_to` | String | N | 대주평가금_말 |  | 12 |
| `rght_evlta_fr` | String | N | 권리평가금_초 |  | 12 |
| `rght_evlta_to` | String | N | 권리평가금_말 |  | 12 |
| `loan_amt_fr` | String | N | 대출금_초 |  | 12 |
| `loan_amt_to` | String | N | 대출금_말 |  | 12 |
| `etc_loana_fr` | String | N | 기타대여금_초 |  | 12 |
| `etc_loana_to` | String | N | 기타대여금_말 |  | 12 |
| `crd_int_npay_gold_fr` | String | N | 신용이자미납금_초 |  | 12 |
| `crd_int_npay_gold_to` | String | N | 신용이자미납금_말 |  | 12 |
| `crd_int_fr` | String | N | 신용이자_초 |  | 12 |
| `crd_int_to` | String | N | 신용이자_말 |  | 12 |
| `tot_amt_fr` | String | N | 순자산액계_초 |  | 12 |
| `tot_amt_to` | String | N | 순자산액계_말 |  | 12 |
| `invt_bsamt` | String | N | 투자원금평잔 |  | 12 |
| `evltv_prft` | String | N | 평가손익 |  | 12 |
| `prft_rt` | String | N | 수익률 |  | 12 |
| `tern_rt` | String | N | 회전율 |  | 12 |
| `termin_tot_trns` | String | N | 기간내총입금 |  | 12 |
| `termin_tot_pymn` | String | N | 기간내총출금 |  | 12 |
| `termin_tot_inq` | String | N | 기간내총입고 |  | 12 |
| `termin_tot_outq` | String | N | 기간내총출고 |  | 12 |
| `futr_repl_sella` | String | N | 선물대용매도금액 |  | 12 |
| `trst_repl_sella` | String | N | 위탁대용매도금액 |  | 12 |

---

## 계좌별당일현황요청 `kt00017`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `crd_int_npay_gold` | String | N | 신용이자미납금 |  | 12 |
| `etc_loana` | String | N | 기타대여금 |  | 12 |
| `gnrl_stk_evlt_amt_d2` | String | N | 일반주식평가금액D+2 |  | 12 |
| `dpst_grnt_use_amt_d2` | String | N | 예탁담보대출금D+2 |  | 12 |
| `crd_stk_evlt_amt_d2` | String | N | 예탁담보주식평가금액D+2 |  | 12 |
| `crd_loan_d2` | String | N | 신용융자금D+2 |  | 12 |
| `crd_loan_evlta_d2` | String | N | 신용융자평가금D+2 |  | 12 |
| `crd_ls_grnt_d2` | String | N | 신용대주담보금D+2 |  | 12 |
| `crd_ls_evlta_d2` | String | N | 신용대주평가금D+2 |  | 12 |
| `ina_amt` | String | N | 입금금액 |  | 12 |
| `outa` | String | N | 출금금액 |  | 12 |
| `inq_amt` | String | N | 입고금액 |  | 12 |
| `outq_amt` | String | N | 출고금액 |  | 12 |
| `sell_amt` | String | N | 매도금액 |  | 12 |
| `buy_amt` | String | N | 매수금액 |  | 12 |
| `cmsn` | String | N | 수수료 |  | 12 |
| `tax` | String | N | 세금 |  | 12 |
| `stk_pur_cptal_loan_amt` | String | N | 주식매입자금대출금 |  | 12 |
| `rp_evlt_amt` | String | N | RP평가금액 |  | 12 |
| `bd_evlt_amt` | String | N | 채권평가금액 |  | 12 |
| `elsevlt_amt` | String | N | ELS평가금액 |  | 12 |
| `crd_int_amt` | String | N | 신용이자금액 |  | 12 |
| `sel_prica_grnt_loan_int_amt_amt` | String | N | 매도대금담보대출이자금액 |  | 12 |
| `dvida_amt` | String | N | 배당금액 |  | 12 |

---

## 계좌평가잔고내역요청 `kt00018`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dmst_stex_tp` | String | Y | 국내거래소구분 | KRX:한국거래소,NXT:넥스트트레이드 | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `tot_evlt_amt` | String | N | 총평가금액 |  | 15 |
| `tot_evlt_pl` | String | N | 총평가손익금액 |  | 15 |
| `tot_prft_rt` | String | N | 총수익률(%) |  | 12 |
| `prsm_dpst_aset_amt` | String | N | 추정예탁자산 |  | 15 |
| `tot_loan_amt` | String | N | 총대출금 |  | 15 |
| `tot_crd_loan_amt` | String | N | 총융자금액 |  | 15 |
| `tot_crd_ls_amt` | String | N | 총대주금액 |  | 15 |
| `acnt_evlt_remn_indv_tot` | LIST | N | 계좌평가잔고개별합산 |  |  |
| `- stk_cd` | String | N | 종목번호 |  | 12 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- evltv_prft` | String | N | 평가손익 |  | 15 |
| `- prft_rt` | String | N | 수익률(%) |  | 12 |
| `- pur_pric` | String | N | 매입가 |  | 15 |
| `- pred_close_pric` | String | N | 전일종가 |  | 12 |
| `- rmnd_qty` | String | N | 보유수량 |  | 15 |
| `- trde_able_qty` | String | N | 매매가능수량 |  | 15 |
| `- cur_prc` | String | N | 현재가 |  | 12 |
| `- pred_buyq` | String | N | 전일매수수량 |  | 15 |
| `- pred_sellq` | String | N | 전일매도수량 |  | 15 |
| `- tdy_buyq` | String | N | 금일매수수량 |  | 15 |
| `- tdy_sellq` | String | N | 금일매도수량 |  | 15 |
| `- pur_amt` | String | N | 매입금액 |  | 15 |
| `- pur_cmsn` | String | N | 매입수수료 |  | 15 |
| `- evlt_amt` | String | N | 평가금액 |  | 15 |
| `- sell_cmsn` | String | N | 평가수수료 |  | 15 |
| `- tax` | String | N | 세금 |  | 15 |
| `- sum_cmsn` | String | N | 수수료합 | 매입수수료 + 평가수수료 | 15 |
| `- poss_rt` | String | N | 보유비중(%) |  | 12 |
| `- crd_tp` | String | N | 신용구분 |  | 2 |
| `- crd_tp_nm` | String | N | 신용구분명 |  | 4 |
| `- crd_loan_dt` | String | N | 대출일 |  | 8 |

---

## 주식 매수주문 `kt10000`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `ord_qty` | String | Y | 주문수량 |  | 12 |
| `ord_uv` | String | N | 주문단가 |  | 12 |
| `trde_tp` | String | Y | 매매구분 | 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK) | 2 |
| `cond_uv` | String | N | 조건단가 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |

---

## 주식 매도주문 `kt10001`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `ord_qty` | String | Y | 주문수량 |  | 12 |
| `ord_uv` | String | N | 주문단가 |  | 12 |
| `trde_tp` | String | Y | 매매구분 | 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK) | 2 |
| `cond_uv` | String | N | 조건단가 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |

---

## 주식 정정주문 `kt10002`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `orig_ord_no` | String | Y | 원주문번호 |  | 7 |
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `mdfy_qty` | String | Y | 정정수량 |  | 12 |
| `mdfy_uv` | String | Y | 정정단가 |  | 12 |
| `mdfy_cond_uv` | String | N | 정정조건단가 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_orig_ord_no` | String | N | 모주문번호 |  | 7 |
| `mdfy_qty` | String | N | 정정수량 |  | 12 |
| `dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |

---

## 주식 취소주문 `kt10003`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `orig_ord_no` | String | Y | 원주문번호 |  | 7 |
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `cncl_qty` | String | Y | 취소수량 | '0' 입력시 잔량 전부 취소 | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_orig_ord_no` | String | N | 모주문번호 |  | 7 |
| `cncl_qty` | String | N | 취소수량 |  | 12 |

---

## 신용 매수주문 `kt10006`

**Method**: `POST`  
**URL**: `/api/dostk/crdordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `ord_qty` | String | Y | 주문수량 |  | 12 |
| `ord_uv` | String | N | 주문단가 |  | 12 |
| `trde_tp` | String | Y | 매매구분 | 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK) | 2 |
| `cond_uv` | String | N | 조건단가 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |

---

## 신용 매도주문 `kt10007`

**Method**: `POST`  
**URL**: `/api/dostk/crdordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `ord_qty` | String | Y | 주문수량 |  | 12 |
| `ord_uv` | String | N | 주문단가 |  | 12 |
| `trde_tp` | String | Y | 매매구분 | 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK) | 2 |
| `crd_deal_tp` | String | Y | 신용거래구분 | 33:융자 , 99:융자합 | 2 |
| `crd_loan_dt` | String | N | 대출일 | YYYYMMDD(융자일경우필수) | 8 |
| `cond_uv` | String | N | 조건단가 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |

---

## 신용 정정주문 `kt10008`

**Method**: `POST`  
**URL**: `/api/dostk/crdordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `orig_ord_no` | String | Y | 원주문번호 |  | 7 |
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `mdfy_qty` | String | Y | 정정수량 |  | 12 |
| `mdfy_uv` | String | Y | 정정단가 |  | 12 |
| `mdfy_cond_uv` | String | N | 정정조건단가 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_orig_ord_no` | String | N | 모주문번호 |  | 7 |
| `mdfy_qty` | String | N | 정정수량 |  | 12 |
| `dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |

---

## 신용 취소주문 `kt10009`

**Method**: `POST`  
**URL**: `/api/dostk/crdordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `orig_ord_no` | String | Y | 원주문번호 |  | 7 |
| `stk_cd` | String | Y | 종목코드 |  | 12 |
| `cncl_qty` | String | Y | 취소수량 | '0' 입력시 잔량 전부 취소 | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_orig_ord_no` | String | N | 모주문번호 |  | 7 |
| `cncl_qty` | String | N | 취소수량 |  | 12 |

---

## 신용융자 가능종목요청 `kt20016`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `mrkt_deal_tp` | String | Y | 시장거래구분 | %:전체, 1:코스피, 0:코스닥 | 1 |
| `stk_cd` | String | N | 종목코드 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `crd_loan_pos_stk` | LIST | N | 신용융자가능종목 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 12 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- crd_assr_rt` | String | N | 신용보증금율 |  | 4 |
| `- repl_pric` | String | N | 대용가 |  | 12 |
| `- pred_close_pric` | String | N | 전일종가 |  | 12 |
| `- crd_limit_over_yn` | String | N | 신용한도초과여부 |  | 1 |
| `- crd_limit_over_txt` | String | N | 신용한도초과 | N:공란,Y:회사한도 초과 | 40 |

---

## 신용융자 가능문의 `kt20017`

**Method**: `POST`  
**URL**: `/api/dostk/stkinfo`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

---

## 금현물 매수주문 `kt50000`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `ord_qty` | String | Y | 주문수량 |  | 12 |
| `ord_uv` | String | N | 주문단가 |  | 12 |
| `trde_tp` | String | Y | 매매구분 | 00:보통, 10:보통(IOC), 20:보통(FOK) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

---

## 금현물 매도주문 `kt50001`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `ord_qty` | String | Y | 주문수량 |  | 12 |
| `ord_uv` | String | N | 주문단가 |  | 12 |
| `trde_tp` | String | Y | 매매구분 | 00:보통, 10:보통(IOC), 20:보통(FOK) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

---

## 금현물 정정주문 `kt50002`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `orig_ord_no` | String | Y | 원주문번호 |  | 7 |
| `mdfy_qty` | String | Y | 정정수량 |  | 12 |
| `mdfy_uv` | String | Y | 정정단가 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_orig_ord_no` | String | N | 모주문번호 |  | 7 |
| `mdfy_qty` | String | N | 정정수량 |  | 12 |

---

## 금현물 취소주문 `kt50003`

**Method**: `POST`  
**URL**: `/api/dostk/ordr`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `stk_cd` | String | Y | 종목코드 | M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g | 12 |
| `cncl_qty` | String | Y | 취소수량 | '0' 입력시 잔량 전부 취소 | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `base_orig_ord_no` | String | N | 모주문번호 |  | 7 |
| `cncl_qty` | String | N | 취소수량 |  | 12 |

---

## 금현물 잔고확인 `kt50020`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `net_entr` | String | N | 추정예수금 |  | 12 |
| `tot_est_amt` | String | N | 잔고평가액 |  | 12 |
| `net_amt` | String | N | 예탁자산평가액 |  | 12 |
| `tot_book_amt2` | String | N | 총매입금액 |  | 12 |
| `tot_dep_amt` | String | N | 추정예탁자산 |  | 12 |
| `paym_alowa` | String | N | 출금가능금액 |  | 12 |
| `pl_amt` | String | N | 실현손익 |  | 12 |
| `gold_acnt_evlt_prst` | LIST | N | 금현물계좌평가현황 |  |  |
| `- stk_cd` | String | N | 종목코드 |  | 30 |
| `- stk_nm` | String | N | 종목명 |  | 12 |
| `- real_qty` | String | N | 보유수량 |  | 12 |
| `- avg_prc` | String | N | 평균단가 |  | 12 |
| `- cur_prc` | String | N | 현재가 |  | 12 |
| `- est_amt` | String | N | 평가금액 |  | 12 |
| `- est_lspft` | String | N | 손익금액 |  | 12 |
| `- est_ratio` | String | N | 손익율 |  | 12 |
| `- cmsn` | String | N | 수수료 |  | 12 |
| `- vlad_tax` | String | N | 부가가치세 |  | 12 |
| `- book_amt2` | String | N | 매입금액 |  | 12 |
| `- pl_prch_prc` | String | N | 손익분기매입가 |  | 12 |
| `- qty` | String | N | 결제잔고 |  | 12 |
| `- buy_qty` | String | N | 매수수량 |  | 12 |
| `- sell_qty` | String | N | 매도수량 |  | 12 |
| `- able_qty` | String | N | 가능수량 |  | 12 |

---

## 금현물 예수금 `kt50021`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `profa_ch` | String | N | 증거금현금 |  | 15 |
| `chck_ina_amt` | String | N | 수표입금액 |  | 15 |
| `etc_loan` | String | N | 기타대여금 |  | 15 |
| `etc_loan_dlfe` | String | N | 기타대여금연체료 |  | 15 |
| `etc_loan_tot` | String | N | 기타대여금합계 |  | 15 |
| `prsm_entra` | String | N | 추정예수금 |  | 15 |
| `buy_exct_amt` | String | N | 매수정산금 |  | 15 |
| `sell_exct_amt` | String | N | 매도정산금 |  | 15 |
| `sell_buy_exct_amt` | String | N | 매도매수정산금 |  | 15 |
| `dly_amt` | String | N | 미수변제소요금 |  | 15 |
| `prsm_pymn_alow_amt` | String | N | 추정출금가능금액 |  | 15 |
| `pymn_alow_amt` | String | N | 출금가능금액 |  | 15 |
| `ord_alow_amt` | String | N | 주문가능금액 |  | 15 |

---

## 금현물 주문체결전체조회 `kt50030`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `qry_tp` | String | N | 조회구분 | 1: 주문순, 2: 역순 | 1 |
| `mrkt_deal_tp` | String | Y | 시장구분 |  | 1 |
| `stk_bond_tp` | String | Y | 주식채권구분 | 0:전체, 1:주식, 2:채권 | 1 |
| `slby_tp` | String | Y | 매도수구분 | 0:전체, 1:매도, 2:매수 | 1 |
| `stk_cd` | String | N | 종목코드 |  | 12 |
| `fr_ord_no` | String | N | 시작주문번호 |  | 7 |
| `dmst_stex_tp` | String | N | 국내거래소구분 | %:(전체), KRX, NXT, SOR | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_bond_tp` | String | N | 주식채권구분 |  | 1 |
| `- ord_no` | String | N | 주문번호 |  | 7 |
| `- stk_cd` | String | N | 상품코드 |  | 12 |
| `- trde_tp` | String | N | 매매구분 |  | 12 |
| `- io_tp_nm` | String | N | 주문유형구분 |  | 20 |
| `- ord_qty` | String | N | 주문수량 |  | 10 |
| `- ord_uv` | String | N | 주문단가 |  | 10 |
| `- cnfm_qty` | String | N | 확인수량 |  | 10 |
| `- data_send_end_tp` | String | N | 접수구분 |  | 12 |
| `- mrkt_deal_tp` | String | N | 시장구분 |  | 1 |
| `- rsrv_tp` | String | N | 예약/반대여부 |  | 4 |
| `- orig_ord_no` | String | N | 원주문번호 |  | 7 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- dcd_tp_nm` | String | N | 결제구분 |  | 4 |
| `- crd_deal_tp` | String | N | 신용거래구분 |  | 20 |
| `- cntr_qty` | String | N | 체결수량 |  | 10 |
| `- cntr_uv` | String | N | 체결단가 |  | 10 |
| `- ord_remnq` | String | N | 미체결수량 |  | 10 |
| `- comm_ord_tp` | String | N | 통신구분 |  | 10 |
| `- mdfy_cncl_tp` | String | N | 정정취소구분 |  | 20 |
| `- dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |
| `- cond_uv` | String | N | 스톱가 |  | 10 |

---

## 금현물 주문체결조회 `kt50031`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `qry_tp` | String | Y | 조회구분 | 1:주문순, 2:역순, 3:미체결, 4:체결내역만 | 1 |
| `stk_bond_tp` | String | Y | 주식채권구분 | 0:전체, 1:주식, 2:채권 | 1 |
| `sell_tp` | String | Y | 매도수구분 | 0:전체, 1:매도, 2:매수 | 1 |
| `stk_cd` | String | N | 종목코드 | 공백허용 (공백일때 전체종목) | 12 |
| `fr_ord_no` | String | N | 시작주문번호 | 공백허용 (공백일때 전체주문) | 7 |
| `dmst_stex_tp` | String | Y | 국내거래소구분 | %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행 | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- ord_no` | String | N | 주문번호 |  | 7 |
| `- stk_cd` | String | N | 종목번호 |  | 12 |
| `- trde_tp` | String | N | 매매구분 |  | 20 |
| `- crd_tp` | String | N | 신용구분 |  | 20 |
| `- ord_qty` | String | N | 주문수량 |  | 10 |
| `- ord_uv` | String | N | 주문단가 |  | 10 |
| `- cnfm_qty` | String | N | 확인수량 |  | 10 |
| `- acpt_tp` | String | N | 접수구분 |  | 20 |
| `- rsrv_tp` | String | N | 반대여부 |  | 20 |
| `- ord_tm` | String | N | 주문시간 |  | 8 |
| `- ori_ord` | String | N | 원주문 |  | 7 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- io_tp_nm` | String | N | 주문구분 |  | 20 |
| `- loan_dt` | String | N | 대출일 |  | 8 |
| `- cntr_qty` | String | N | 체결수량 |  | 10 |
| `- cntr_uv` | String | N | 체결단가 |  | 10 |
| `- ord_remnq` | String | N | 주문잔량 |  | 10 |
| `- comm_ord_tp` | String | N | 통신구분 |  | 20 |
| `- mdfy_cncl` | String | N | 정정취소 |  | 20 |
| `- cnfm_tm` | String | N | 확인시간 |  | 8 |
| `- dmst_stex_tp` | String | N | 국내거래소구분 |  | 8 |
| `- cond_uv` | String | N | 스톱가 |  | 10 |

---

## 금현물 거래내역조회 `kt50032`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `end_dt` | String | N | 종료일자 |  | 8 |
| `tp` | String | N | 구분 | 0:전체, 1:입출금, 2:출고, 3:매매, 4:매수, 5:매도, 6:입금, 7:출금 | 1 |
| `stk_cd` | String | N | 종목코드 |  | 12 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `gold_trde_hist` | LIST | N | 금현물거래내역 |  |  |
| `- deal_dt` | String | N | 거래일자 |  |  |
| `- deal_no` | String | N | 거래번호 |  |  |
| `- rmrk_nm` | String | N | 적요명 |  |  |
| `- deal_qty` | String | N | 거래수량 |  |  |
| `- gold_spot_vat` | String | N | 금현물부가가치세 |  |  |
| `- exct_amt` | String | N | 정산금액 |  |  |
| `- dly_sum` | String | N | 연체합 |  |  |
| `- entra_remn` | String | N | 예수금잔고 |  |  |
| `- mdia_nm` | String | N | 메체구분명 |  |  |
| `- orig_deal_no` | String | N | 원거래번호 |  |  |
| `- stk_nm` | String | N | 종목명 |  |  |
| `- uv_exrt` | String | N | 거래단가 |  |  |
| `- cmsn` | String | N | 수수료 |  |  |
| `- uncl_ocr` | String | N | 미수(원/g) |  |  |
| `- rpym_sum` | String | N | 변제합 |  |  |
| `- spot_remn` | String | N | 현물잔고 |  |  |
| `- proc_time` | String | N | 처리시간 |  |  |
| `- rcpy_no` | String | N | 출납번호 |  |  |
| `- stk_cd` | String | N | 종목코드 |  |  |
| `- deal_amt` | String | N | 거래금액 |  |  |
| `- tax_tot_amt` | String | N | 소득/주민세 |  |  |
| `- cntr_dt` | String | N | 체결일 |  |  |
| `- proc_brch_nm` | String | N | 처리점 |  |  |
| `- prcsr` | String | N | 처리자 |  |  |

---

## 금현물 미체결조회 `kt50075`

**Method**: `POST`  
**URL**: `/api/dostk/acnt`  
**Domain**: `https://api.kiwoom.com`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `qry_tp` | String | N | 조회구분 | 1: 주문순, 2: 역순 | 1 |
| `mrkt_deal_tp` | String | Y | 시장구분 |  | 1 |
| `stk_bond_tp` | String | Y | 주식채권구분 | 0:전체, 1:주식, 2:채권 | 1 |
| `sell_tp` | String | Y | 매도수구분 | 0:전체, 1:매도, 2:매수 | 1 |
| `stk_cd` | String | N | 종목코드 |  | 12 |
| `fr_ord_no` | String | N | 시작주문번호 |  | 7 |
| `dmst_stex_tp` | String | N | 국내거래소구분 | %:(전체), KRX, NXT, SOR | 6 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `- stk_bond_tp` | String | N | 주식채권구분 |  | 1 |
| `- ord_no` | String | N | 주문번호 |  | 7 |
| `- stk_cd` | String | N | 상품코드 |  | 12 |
| `- trde_tp` | String | N | 매매구분 |  | 12 |
| `- io_tp_nm` | String | N | 주문유형구분 |  | 20 |
| `- ord_qty` | String | N | 주문수량 |  | 10 |
| `- ord_uv` | String | N | 주문단가 |  | 10 |
| `- cnfm_qty` | String | N | 확인수량 |  | 10 |
| `- data_send_end_tp` | String | N | 접수구분 |  | 12 |
| `- mrkt_deal_tp` | String | N | 시장구분 |  | 1 |
| `- rsrv_tp` | String | N | 예약/반대여부 |  | 4 |
| `- orig_ord_no` | String | N | 원주문번호 |  | 7 |
| `- stk_nm` | String | N | 종목명 |  | 40 |
| `- dcd_tp_nm` | String | N | 결제구분 |  | 4 |
| `- crd_deal_tp` | String | N | 신용거래구분 |  | 20 |
| `- cntr_qty` | String | N | 체결수량 |  | 10 |
| `- cntr_uv` | String | N | 체결단가 |  | 10 |
| `- ord_remnq` | String | N | 미체결수량 |  | 10 |
| `- comm_ord_tp` | String | N | 통신구분 |  | 10 |
| `- mdfy_cncl_tp` | String | N | 정정취소구분 |  | 20 |
| `- dmst_stex_tp` | String | N | 국내거래소구분 |  | 6 |
| `- cond_uv` | String | N | 스톱가 |  | 10 |

---

## 주문체결 `00`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시

0:기존유지안함 1:기존유지(Default)

0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지

해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 |  | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 9201` | String | N | 계좌번호 |  |  |
| `- - 9203` | String | N | 주문번호 |  |  |
| `- - 9205` | String | N | 관리자사번 |  |  |
| `- - 9001` | String | N | 종목코드,업종코드 |  |  |
| `- - 912` | String | N | 주문업무분류 |  |  |
| `- - 913` | String | N | 주문상태 | 접수, 체결, 확인, 취소, 거부 |  |
| `- - 302` | String | N | 종목명 |  |  |
| `- - 900` | String | N | 주문수량 |  |  |
| `- - 901` | String | N | 주문가격 |  |  |
| `- - 902` | String | N | 미체결수량 |  |  |
| `- - 903` | String | N | 체결누계금액 |  |  |
| `- - 904` | String | N | 원주문번호 |  |  |
| `- - 905` | String | N | 주문구분 | "+/-", 매도, 매수, 매도정정, 매수정정, 매수취소, 매도취소


※ 영웅문4에서 적색으로 표기되어있으면 +가, 청색으로 표기되어있으면 -가 앞에 기재됩니다 |  |
| `- - 906` | String | N | 매매구분 | 보통, 시장가, 조건부지정가, 최유리지정가, 최우선지정가, 보통(IOC), 시장가(IOC), 최유리(IOC), 보통(FOK), 시장가(FOK), 최유리(FOK), 스톰지정가, 중간가, 중간가(IOC), 중간가(FOK), 장전시간외, 장후시간외, 시간외대량, 시간외바스켓, 시간외자사주, 시간외단일가 |  |
| `- - 907` | String | N | 매도수구분 | 1:매도, 2:매수 |  |
| `- - 908` | String | N | 주문/체결시간 |  |  |
| `- - 909` | String | N | 체결번호 |  |  |
| `- - 910` | String | N | 체결가 |  |  |
| `- - 911` | String | N | 체결량 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 27` | String | N | (최우선)매도호가 |  |  |
| `- - 28` | String | N | (최우선)매수호가 |  |  |
| `- - 914` | String | N | 단위체결가 |  |  |
| `- - 915` | String | N | 단위체결량 |  |  |
| `- - 938` | String | N | 당일매매수수료 |  |  |
| `- - 939` | String | N | 당일매매세금 |  |  |
| `- - 919` | String | N | 거부사유 |  |  |
| `- - 920` | String | N | 화면번호 |  |  |
| `- - 921` | String | N | 터미널번호 |  |  |
| `- - 922` | String | N | 신용구분 | 실시간 체결용 |  |
| `- - 923` | String | N | 대출일 | 실시간 체결용 |  |
| `- - 10010` | String | N | 시간외단일가_현재가 |  |  |
| `- - 2134` | String | N | 거래소구분 | 0:통합,1:KRX,2:NXT |  |
| `- - 2135` | String | N | 거래소구분명 | 통합,KRX,NXT |  |
| `- - 2136` | String | N | SOR여부 | Y,N |  |

---

## 잔고 `04`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
 
0:기존유지안함 1:기존유지(Default)

0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지

해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 |  | 104 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 9201` | String | N | 계좌번호 |  |  |
| `- - 9001` | String | N | 종목코드,업종코드 |  |  |
| `- - 917` | String | N | 신용구분 |  |  |
| `- - 916` | String | N | 대출일 |  |  |
| `- - 302` | String | N | 종목명 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 930` | String | N | 보유수량 |  |  |
| `- - 931` | String | N | 매입단가 |  |  |
| `- - 932` | String | N | 총매입가(당일누적) |  |  |
| `- - 933` | String | N | 주문가능수량 |  |  |
| `- - 945` | String | N | 당일순매수량 |  |  |
| `- - 946` | String | N | 매도/매수구분 | 계약,주 |  |
| `- - 950` | String | N | 당일총매도손익 |  |  |
| `- - 951` | String | N | Extra Item |  |  |
| `- - 27` | String | N | (최우선)매도호가 |  |  |
| `- - 28` | String | N | (최우선)매수호가 |  |  |
| `- - 307` | String | N | 기준가 |  |  |
| `- - 8019` | String | N | 손익률(실현손익) |  |  |
| `- - 957` | String | N | 신용금액 |  |  |
| `- - 958` | String | N | 신용이자 |  |  |
| `- - 918` | String | N | 만기일 |  |  |
| `- - 990` | String | N | 당일실현손익(유가) |  |  |
| `- - 991` | String | N | 당일실현손익율(유가) |  |  |
| `- - 992` | String | N | 당일실현손익(신용) |  |  |
| `- - 993` | String | N | 당일실현손익율(신용) |  |  |
| `- - 959` | String | N | 담보대출수량 |  |  |
| `- - 924` | String | N | Extra Item |  |  |

---

## 주식기세 `0A`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시

0:기존유지안함 1:기존유지(Default)

0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지

해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지(등록,해지시에만 값 전송,데이터 실시간 수신시 미전송) |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |
| `- - 27` | String | N | (최우선)매도호가 |  |  |
| `- - 28` | String | N | (최우선)매수호가 |  |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 14` | String | N | 누적거래대금 |  |  |
| `- - 16` | String | N | 시가 |  |  |
| `- - 17` | String | N | 고가 |  |  |
| `- - 18` | String | N | 저가 |  |  |
| `- - 25` | String | N | 전일대비기호 |  |  |
| `- - 26` | String | N | 전일거래량대비(계약,주) |  |  |
| `- - 29` | String | N | 거래대금증감 |  |  |
| `- - 30` | String | N | 전일거래량대비(비율) |  |  |
| `- - 31` | String | N | 거래회전율 |  |  |
| `- - 32` | String | N | 거래비용 |  |  |
| `- - 311` | String | N | 시가총액(억) |  |  |
| `- - 567` | String | N | 상한가발생시간 |  |  |
| `- - 568` | String | N | 하한가발생시간 |  |  |

---

## 주식체결 `0B`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0B,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |
| `- - 27` | String | N | (최우선)매도호가 |  |  |
| `- - 28` | String | N | (최우선)매수호가 |  |  |
| `- - 15` | String | N | 거래량 | +는 매수체결,-는 매도체결 |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 14` | String | N | 누적거래대금 |  |  |
| `- - 16` | String | N | 시가 |  |  |
| `- - 17` | String | N | 고가 |  |  |
| `- - 18` | String | N | 저가 |  |  |
| `- - 25` | String | N | 전일대비기호 |  |  |
| `- - 26` | String | N | 전일거래량대비(계약,주) |  |  |
| `- - 29` | String | N | 거래대금증감 |  |  |
| `- - 30` | String | N | 전일거래량대비(비율) |  |  |
| `- - 31` | String | N | 거래회전율 |  |  |
| `- - 32` | String | N | 거래비용 |  |  |
| `- - 228` | String | N | 체결강도 |  |  |
| `- - 311` | String | N | 시가총액(억) |  |  |
| `- - 290` | String | N | 장구분 | 1: 장전 시간외 , 2: 장중 , 3: 장후 시간외 |  |
| `- - 691` | String | N | K.O 접근도 |  |  |
| `- - 567` | String | N | 상한가발생시간 |  |  |
| `- - 568` | String | N | 하한가발생시간 |  |  |
| `- - 851` | String | N | 전일 동시간 거래량 비율 |  |  |
| `- - 1890` | String | N | 시가시간 |  |  |
| `- - 1891` | String | N | 고가시간 |  |  |
| `- - 1892` | String | N | 저가시간 |  |  |
| `- - 1030` | String | N | 매도체결량 |  |  |
| `- - 1031` | String | N | 매수체결량 |  |  |
| `- - 1032` | String | N | 매수비율 |  |  |
| `- - 1071` | String | N | 매도체결건수 |  |  |
| `- - 1072` | String | N | 매수체결건수 |  |  |
| `- - 1313` | String | N | 순간거래대금 |  |  |
| `- - 1315` | String | N | 매도체결량_단건 |  |  |
| `- - 1316` | String | N | 매수체결량_단건 |  |  |
| `- - 1314` | String | N | 순매수체결량 |  |  |
| `- - 1497` | String | N | CFD증거금 |  |  |
| `- - 1498` | String | N | 유지증거금 |  |  |
| `- - 620` | String | N | 당일거래평균가 |  |  |
| `- - 732` | String | N | CFD거래비용 |  |  |
| `- - 852` | String | N | 대주거래비용 |  |  |
| `- - 9081` | String | N | 거래소구분 |  |  |

---

## 주식우선호가 `0C`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 27` | String | N | (최우선)매도호가 |  |  |
| `- - 28` | String | N | (최우선)매수호가 |  |  |

---

## 주식호가잔량 `0D`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 21` | String | N | 호가시간 |  |  |
| `- - 41` | String | N | 매도호가1 |  |  |
| `- - 61` | String | N | 매도호가수량1 |  |  |
| `- - 81` | String | N | 매도호가직전대비1 |  |  |
| `- - 51` | String | N | 매수호가1 |  |  |
| `- - 71` | String | N | 매수호가수량1 |  |  |
| `- - 91` | String | N | 매수호가직전대비1 |  |  |
| `- - 42` | String | N | 매도호가2 |  |  |
| `- - 62` | String | N | 매도호가수량2 |  |  |
| `- - 82` | String | N | 매도호가직전대비2 |  |  |
| `- - 52` | String | N | 매수호가2 |  |  |
| `- - 72` | String | N | 매수호가수량2 |  |  |
| `- - 92` | String | N | 매수호가직전대비2 |  |  |
| `- - 43` | String | N | 매도호가3 |  |  |
| `- - 63` | String | N | 매도호가수량3 |  |  |
| `- - 83` | String | N | 매도호가직전대비3 |  |  |
| `- - 53` | String | N | 매수호가3 |  |  |
| `- - 73` | String | N | 매수호가수량3 |  |  |
| `- - 93` | String | N | 매수호가직전대비3 |  |  |
| `- - 44` | String | N | 매도호가4 |  |  |
| `- - 64` | String | N | 매도호가수량4 |  |  |
| `- - 84` | String | N | 매도호가직전대비4 |  |  |
| `- - 54` | String | N | 매수호가4 |  |  |
| `- - 74` | String | N | 매수호가수량4 |  |  |
| `- - 94` | String | N | 매수호가직전대비4 |  |  |
| `- - 45` | String | N | 매도호가5 |  |  |
| `- - 65` | String | N | 매도호가수량5 |  |  |
| `- - 85` | String | N | 매도호가직전대비5 |  |  |
| `- - 55` | String | N | 매수호가5 |  |  |
| `- - 75` | String | N | 매수호가수량5 |  |  |
| `- - 95` | String | N | 매수호가직전대비5 |  |  |
| `- - 46` | String | N | 매도호가6 |  |  |
| `- - 66` | String | N | 매도호가수량6 |  |  |
| `- - 86` | String | N | 매도호가직전대비6 |  |  |
| `- - 56` | String | N | 매수호가6 |  |  |
| `- - 76` | String | N | 매수호가수량6 |  |  |
| `- - 96` | String | N | 매수호가직전대비6 |  |  |
| `- - 47` | String | N | 매도호가7 |  |  |
| `- - 67` | String | N | 매도호가수량7 |  |  |
| `- - 87` | String | N | 매도호가직전대비7 |  |  |
| `- - 57` | String | N | 매수호가7 |  |  |
| `- - 77` | String | N | 매수호가수량7 |  |  |
| `- - 97` | String | N | 매수호가직전대비7 |  |  |
| `- - 48` | String | N | 매도호가8 |  |  |
| `- - 68` | String | N | 매도호가수량8 |  |  |
| `- - 88` | String | N | 매도호가직전대비8 |  |  |
| `- - 58` | String | N | 매수호가8 |  |  |
| `- - 78` | String | N | 매수호가수량8 |  |  |
| `- - 98` | String | N | 매수호가직전대비8 |  |  |
| `- - 49` | String | N | 매도호가9 |  |  |
| `- - 69` | String | N | 매도호가수량9 |  |  |
| `- - 89` | String | N | 매도호가직전대비9 |  |  |
| `- - 59` | String | N | 매수호가9 |  |  |
| `- - 79` | String | N | 매수호가수량9 |  |  |
| `- - 99` | String | N | 매수호가직전대비9 |  |  |
| `- - 50` | String | N | 매도호가10 |  |  |
| `- - 70` | String | N | 매도호가수량10 |  |  |
| `- - 60` | String | N | 매수호가10 |  |  |
| `- - 90` | String | N | 매도호가직전대비10 |  |  |
| `- - 80` | String | N | 매수호가수량10 |  |  |
| `- - 100` | String | N | 매수호가직전대비10 |  |  |
| `- - 121` | String | N | 매도호가총잔량 |  |  |
| `- - 122` | String | N | 매도호가총잔량직전대비 |  |  |
| `- - 125` | String | N | 매수호가총잔량 |  |  |
| `- - 126` | String | N | 매수호가총잔량직전대비 |  |  |
| `- - 23` | String | N | 예상체결가 |  |  |
| `- - 24` | String | N | 예상체결수량 |  |  |
| `- - 128` | String | N | 순매수잔량 |  |  |
| `- - 129` | String | N | 매수비율 |  |  |
| `- - 138` | String | N | 순매도잔량 |  |  |
| `- - 139` | String | N | 매도비율 |  |  |
| `- - 200` | String | N | 예상체결가전일종가대비 |  |  |
| `- - 201` | String | N | 예상체결가전일종가대비등락율 |  |  |
| `- - 238` | String | N | 예상체결가전일종가대비기호 |  |  |
| `- - 291` | String | N | 예상체결가 | 예상체결 시간동안에만 유효한 값 |  |
| `- - 292` | String | N | 예상체결량 |  |  |
| `- - 293` | String | N | 예상체결가전일대비기호 |  |  |
| `- - 294` | String | N | 예상체결가전일대비 |  |  |
| `- - 295` | String | N | 예상체결가전일대비등락율 |  |  |
| `- - 621` | String | N | LP매도호가수량1 |  |  |
| `- - 631` | String | N | LP매수호가수량1 |  |  |
| `- - 622` | String | N | LP매도호가수량2 |  |  |
| `- - 632` | String | N | LP매수호가수량2 |  |  |
| `- - 623` | String | N | LP매도호가수량3 |  |  |
| `- - 633` | String | N | LP매수호가수량3 |  |  |
| `- - 624` | String | N | LP매도호가수량4 |  |  |
| `- - 634` | String | N | LP매수호가수량4 |  |  |
| `- - 625` | String | N | LP매도호가수량5 |  |  |
| `- - 635` | String | N | LP매수호가수량5 |  |  |
| `- - 626` | String | N | LP매도호가수량6 |  |  |
| `- - 636` | String | N | LP매수호가수량6 |  |  |
| `- - 627` | String | N | LP매도호가수량7 |  |  |
| `- - 637` | String | N | LP매수호가수량7 |  |  |
| `- - 628` | String | N | LP매도호가수량8 |  |  |
| `- - 638` | String | N | LP매수호가수량8 |  |  |
| `- - 629` | String | N | LP매도호가수량9 |  |  |
| `- - 639` | String | N | LP매수호가수량9 |  |  |
| `- - 630` | String | N | LP매도호가수량10 |  |  |
| `- - 640` | String | N | LP매수호가수량10 |  |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 299` | String | N | 전일거래량대비예상체결율 |  |  |
| `- - 215` | String | N | 장운영구분 |  |  |
| `- - 216` | String | N | 투자자별ticker |  |  |
| `- - 6044` | String | N | KRX 매도호가잔량1 |  |  |
| `- - 6045` | String | N | KRX 매도호가잔량2 |  |  |
| `- - 6046` | String | N | KRX 매도호가잔량3 |  |  |
| `- - 6047` | String | N | KRX 매도호가잔량4 |  |  |
| `- - 6048` | String | N | KRX 매도호가잔량5 |  |  |
| `- - 6049` | String | N | KRX 매도호가잔량6 |  |  |
| `- - 6050` | String | N | KRX 매도호가잔량7 |  |  |
| `- - 6051` | String | N | KRX 매도호가잔량8 |  |  |
| `- - 6052` | String | N | KRX 매도호가잔량9 |  |  |
| `- - 6053` | String | N | KRX 매도호가잔량10 |  |  |
| `- - 6054` | String | N | KRX 매수호가잔량1 |  |  |
| `- - 6055` | String | N | KRX 매수호가잔량2 |  |  |
| `- - 6056` | String | N | KRX 매수호가잔량3 |  |  |
| `- - 6057` | String | N | KRX 매수호가잔량4 |  |  |
| `- - 6058` | String | N | KRX 매수호가잔량5 |  |  |
| `- - 6059` | String | N | KRX 매수호가잔량6 |  |  |
| `- - 6060` | String | N | KRX 매수호가잔량7 |  |  |
| `- - 6061` | String | N | KRX 매수호가잔량8 |  |  |
| `- - 6062` | String | N | KRX 매수호가잔량9 |  |  |
| `- - 6063` | String | N | KRX 매수호가잔량10 |  |  |
| `- - 6064` | String | N | KRX 매도호가총잔량 |  |  |
| `- - 6065` | String | N | KRX 매수호가총잔량 |  |  |
| `- - 6066` | String | N | NXT 매도호가잔량1 |  |  |
| `- - 6067` | String | N | NXT 매도호가잔량2 |  |  |
| `- - 6068` | String | N | NXT 매도호가잔량3 |  |  |
| `- - 6069` | String | N | NXT 매도호가잔량4 |  |  |
| `- - 6070` | String | N | NXT 매도호가잔량5 |  |  |
| `- - 6071` | String | N | NXT 매도호가잔량6 |  |  |
| `- - 6072` | String | N | NXT 매도호가잔량7 |  |  |
| `- - 6073` | String | N | NXT 매도호가잔량8 |  |  |
| `- - 6074` | String | N | NXT 매도호가잔량9 |  |  |
| `- - 6075` | String | N | NXT 매도호가잔량10 |  |  |
| `- - 6076` | String | N | NXT 매수호가잔량1 |  |  |
| `- - 6077` | String | N | NXT 매수호가잔량2 |  |  |
| `- - 6078` | String | N | NXT 매수호가잔량3 |  |  |
| `- - 6079` | String | N | NXT 매수호가잔량4 |  |  |
| `- - 6080` | String | N | NXT 매수호가잔량5 |  |  |
| `- - 6081` | String | N | NXT 매수호가잔량6 |  |  |
| `- - 6082` | String | N | NXT 매수호가잔량7 |  |  |
| `- - 6083` | String | N | NXT 매수호가잔량8 |  |  |
| `- - 6084` | String | N | NXT 매수호가잔량9 |  |  |
| `- - 6085` | String | N | NXT 매수호가잔량10 |  |  |
| `- - 6086` | String | N | NXT 매도호가총잔량 |  |  |
| `- - 6087` | String | N | NXT 매수호가총잔량 |  |  |
| `- - 6100` | String | N | KRX 중간가 매도 총잔량 증감 |  |  |
| `- - 6101` | String | N | KRX 중간가 매도 총잔량 |  |  |
| `- - 6102` | String | N | KRX 중간가 |  |  |
| `- - 6103` | String | N | KRX 중간가 매수 총잔량 |  |  |
| `- - 6104` | String | N | KRX 중간가 매수 총잔량 증감 |  |  |
| `- - 6105` | String | N | NXT중간가 매도 총잔량 증감 |  |  |
| `- - 6106` | String | N | NXT중간가 매도 총잔량 |  |  |
| `- - 6107` | String | N | NXT중간가 |  |  |
| `- - 6108` | String | N | NXT중간가 매수 총잔량 |  |  |
| `- - 6109` | String | N | NXT중간가 매수 총잔량 증감 |  |  |
| `- - 6110` | String | N | KRX중간가대비 | 기준가대비 |  |
| `- - 6111` | String | N | KRX중간가대비 기호 | 기준가대비 |  |
| `- - 6112` | String | N | KRX중간가대비등락율 | 기준가대비 |  |
| `- - 6113` | String | N | NXT중간가대비 | 기준가대비 |  |
| `- - 6114` | String | N | NXT중간가대비 기호 | 기준가대비 |  |
| `- - 6115` | String | N | NXT중간가대비등락율 | 기준가대비 |  |

---

## 주식시간외호가 `0E`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 21` | String | N | 호가시간 |  |  |
| `- - 131` | String | N | 시간외매도호가총잔량 |  |  |
| `- - 132` | String | N | 시간외매도호가총잔량직전대비 |  |  |
| `- - 135` | String | N | 시간외매수호가총잔량 |  |  |
| `- - 136` | String | N | 시간외매수호가총잔량직전대비 |  |  |

---

## 주식당일거래원 `0F`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 141` | String | N | 매도거래원1 |  |  |
| `- - 161` | String | N | 매도거래원수량1 |  |  |
| `- - 166` | String | N | 매도거래원별증감1 |  |  |
| `- - 146` | String | N | 매도거래원코드1 |  |  |
| `- - 271` | String | N | 매도거래원색깔1 |  |  |
| `- - 151` | String | N | 매수거래원1 |  |  |
| `- - 171` | String | N | 매수거래원수량1 |  |  |
| `- - 176` | String | N | 매수거래원별증감1 |  |  |
| `- - 156` | String | N | 매수거래원코드1 |  |  |
| `- - 281` | String | N | 매수거래원색깔1 |  |  |
| `- - 142` | String | N | 매도거래원2 |  |  |
| `- - 162` | String | N | 매도거래원수량2 |  |  |
| `- - 167` | String | N | 매도거래원별증감2 |  |  |
| `- - 147` | String | N | 매도거래원코드2 |  |  |
| `- - 272` | String | N | 매도거래원색깔2 |  |  |
| `- - 152` | String | N | 매수거래원2 |  |  |
| `- - 172` | String | N | 매수거래원수량2 |  |  |
| `- - 177` | String | N | 매수거래원별증감2 |  |  |
| `- - 157` | String | N | 매수거래원코드2 |  |  |
| `- - 282` | String | N | 매수거래원색깔2 |  |  |
| `- - 143` | String | N | 매도거래원3 |  |  |
| `- - 163` | String | N | 매도거래원수량3 |  |  |
| `- - 168` | String | N | 매도거래원별증감3 |  |  |
| `- - 148` | String | N | 매도거래원코드3 |  |  |
| `- - 273` | String | N | 매도거래원색깔3 |  |  |
| `- - 153` | String | N | 매수거래원3 |  |  |
| `- - 173` | String | N | 매수거래원수량3 |  |  |
| `- - 178` | String | N | 매수거래원별증감3 |  |  |
| `- - 158` | String | N | 매수거래원코드3 |  |  |
| `- - 283` | String | N | 매수거래원색깔3 |  |  |
| `- - 144` | String | N | 매도거래원4 |  |  |
| `- - 164` | String | N | 매도거래원수량4 |  |  |
| `- - 169` | String | N | 매도거래원별증감4 |  |  |
| `- - 149` | String | N | 매도거래원코드4 |  |  |
| `- - 274` | String | N | 매도거래원색깔4 |  |  |
| `- - 154` | String | N | 매수거래원4 |  |  |
| `- - 174` | String | N | 매수거래원수량4 |  |  |
| `- - 179` | String | N | 매수거래원별증감4 |  |  |
| `- - 159` | String | N | 매수거래원코드4 |  |  |
| `- - 284` | String | N | 매수거래원색깔4 |  |  |
| `- - 145` | String | N | 매도거래원5 |  |  |
| `- - 165` | String | N | 매도거래원수량5 |  |  |
| `- - 170` | String | N | 매도거래원별증감5 |  |  |
| `- - 150` | String | N | 매도거래원코드5 |  |  |
| `- - 275` | String | N | 매도거래원색깔5 |  |  |
| `- - 155` | String | N | 매수거래원5 |  |  |
| `- - 175` | String | N | 매수거래원수량5 |  |  |
| `- - 180` | String | N | 매수거래원별증감5 |  |  |
| `- - 160` | String | N | 매수거래원코드5 |  |  |
| `- - 285` | String | N | 매수거래원색깔5 |  |  |
| `- - 261` | String | N | 외국계매도추정합 |  |  |
| `- - 262` | String | N | 외국계매도추정합변동 |  |  |
| `- - 263` | String | N | 외국계매수추정합 |  |  |
| `- - 264` | String | N | 외국계매수추정합변동 |  |  |
| `- - 267` | String | N | 외국계순매수추정합 |  |  |
| `- - 268` | String | N | 외국계순매수변동 |  |  |
| `- - 337` | String | N | 거래소구분 |  |  |

---

## ETF NAV `0G`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 36` | String | N | NAV |  |  |
| `- - 37` | String | N | NAV전일대비 |  |  |
| `- - 38` | String | N | NAV등락율 |  |  |
| `- - 39` | String | N | 추적오차율 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 25` | String | N | 전일대비기호 |  |  |
| `- - 667` | String | N | ELW기어링비율 |  |  |
| `- - 668` | String | N | ELW손익분기율 |  |  |
| `- - 669` | String | N | ELW자본지지점 |  |  |
| `- - 265` | String | N | NAV/지수괴리율 |  |  |
| `- - 266` | String | N | NAV/ETF괴리율 |  |  |

---

## 주식예상체결 `0H`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |
| `- - 15` | String | N | 거래량 | +는 매수체결, -는 매도체결 |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 25` | String | N | 전일대비기호 |  |  |

---

## 국제금환산가격 `0I`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST | N | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | MGD: 원/g, MGU: $/온스,소수점2자리 | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0B,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 25` | String | N | 전일대비기호 | 1:상한, 2:상승, 3:없음, 4:하한, 5:하락 |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |

---

## 업종지수 `0J`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |
| `- - 15` | String | N | 거래량 | +는 매수체결,-는 매도체결 |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 14` | String | N | 누적거래대금 |  |  |
| `- - 16` | String | N | 시가 |  |  |
| `- - 17` | String | N | 고가 |  |  |
| `- - 18` | String | N | 저가 |  |  |
| `- - 25` | String | N | 전일대비기호 |  |  |
| `- - 26` | String | N | 전일거래량대비 | 계약,주 |  |

---

## 업종등락 `0U`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 252` | String | N | 상승종목수 |  |  |
| `- - 251` | String | N | 상한종목수 |  |  |
| `- - 253` | String | N | 보합종목수 |  |  |
| `- - 255` | String | N | 하락종목수 |  |  |
| `- - 254` | String | N | 하한종목수 |  |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 14` | String | N | 누적거래대금 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |
| `- - 256` | String | N | 거래형성종목수 | 계약,주 |  |
| `- - 257` | String | N | 거래형성비율 |  |  |
| `- - 25` | String | N | 전일대비기호 |  |  |

---

## 주식종목정보 `0g`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 297` | String | N | 임의연장 |  |  |
| `- - 592` | String | N | 장전임의연장 |  |  |
| `- - 593` | String | N | 장후임의연장 |  |  |
| `- - 305` | String | N | 상한가 |  |  |
| `- - 306` | String | N | 하한가 |  |  |
| `- - 307` | String | N | 기준가 |  |  |
| `- - 689` | String | N | 조기종료ELW발생 |  |  |
| `- - 594` | String | N | 통화단위 |  |  |
| `- - 382` | String | N | 증거금율표시 |  |  |
| `- - 370` | String | N | 종목정보 |  |  |

---

## ELW 이론가 `0m`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 670` | String | N | ELW이론가 |  |  |
| `- - 671` | String | N | ELW내재변동성 |  |  |
| `- - 672` | String | N | ELW델타 |  |  |
| `- - 673` | String | N | ELW감마 |  |  |
| `- - 674` | String | N | ELW쎄타 |  |  |
| `- - 675` | String | N | ELW베가 |  |  |
| `- - 676` | String | N | ELW로 |  |  |
| `- - 706` | String | N | LP호가내재변동성 |  |  |

---

## 장시작시간 `0s`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 215` | String | N | 장운영구분 | 0:KRX장전,3:KRX장시작,P:NXT프리마켓개시,Q:NXT프리마켓종료,R:NXT메인마켓개시,S:NXT메인마켓 종료,T:NXT애프터마켓단일가개시,U:NXT애프터마켓개시,V:NXT종가매매종료,W:NXT애프터마켓종료 |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 214` | String | N | 장시작예상잔여시간 |  |  |

---

## ELW 지표 `0u`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 666` | String | N | ELW패리티 |  |  |
| `- - 1211` | String | N | ELW프리미엄 |  |  |
| `- - 667` | String | N | ELW기어링비율 |  |  |
| `- - 668` | String | N | ELW손익분기율 |  |  |
| `- - 669` | String | N | ELW자본지지점 |  |  |

---

## 종목프로그램매매 `0w`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 20` | String | N | 체결시간 |  |  |
| `- - 10` | String | N | 현재가 |  |  |
| `- - 25` | String | N | 전일대비기호 |  |  |
| `- - 11` | String | N | 전일대비 |  |  |
| `- - 12` | String | N | 등락율 |  |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 202` | String | N | 매도수량 |  |  |
| `- - 204` | String | N | 매도금액 |  |  |
| `- - 206` | String | N | 매수수량 |  |  |
| `- - 208` | String | N | 매수금액 |  |  |
| `- - 210` | String | N | 순매수수량 |  |  |
| `- - 211` | String | N | 순매수수량증감 | 계약,주 |  |
| `- - 212` | String | N | 순매수금액 |  |  |
| `- - 213` | String | N | 순매수금액증감 |  |  |
| `- - 214` | String | N | 장시작예상잔여시간 |  |  |
| `- - 215` | String | N | 장운영구분 |  |  |
| `- - 216` | String | N | 투자자별ticker |  |  |

---

## VI발동/해제 `1h`

**Method**: `POST`  
**URL**: `/api/dostk/websocket`  
**Domain**: `wss://api.kiwoom.com:10000`  
**Content-Type**: `application/json;charset=UTF-8`


### Request

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `authorization` | String | Y | 접근토큰 | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출 
 예) Bearer Egicyx... | 1000 |
| `cont-yn` | String | N | 연속조회여부 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅 | 1 |
| `next-key` | String | N | 연속조회키 | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `grp_no` | String | Y | 그룹번호 |  | 4 |
| `refresh` | String | Y | 기존등록유지여부 | 등록(REG)시
0:기존유지안함 1:기존유지(Default)
 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지
해지(REMOVE)시 값 불필요 | 1 |
| `data` | LIST |  | 실시간 등록 리스트 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 거래소별 종목코드, 업종코드
(KRX:039490,NXT:039490_NX,SOR:039490_AL) | 100 |
| `- type` | String | Y | 실시간 항목 | TR 명(0A,0B....) | 2 |


### Response

#### Header
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `cont-yn` | String | N | 연속조회여부 | 다음 데이터가 있을시 Y값 전달 | 1 |
| `next-key` | String | N | 연속조회키 | 다음 데이터가 있을시 다음 키값 전달 | 50 |

#### Body
| Name | Type | Required | Description | Example | Note |
|---|---|:---:|---|---|---|
| `return_msg` | String | N | 결과메시지 | 통신결과에대한메시지 |  |
| `trnm` | String | N | 서비스명 | 등록,해지요청시 요청값 반환 , 실시간수신시 REAL 반환 |  |
| `data` | LIST | N | 실시간 등록리스트 |  |  |
| `- type` | String | N | 실시간항목 | TR 명(0A,0B....) |  |
| `- name` | String | N | 실시간 항목명 |  |  |
| `- item` | String | N | 실시간 등록 요소 | 종목코드 |  |
| `- values` | LIST | N | 실시간 값 리스트 |  |  |
| `- - 9001` | String | N | 종목코드 |  |  |
| `- - 302` | String | N | 종목명 |  |  |
| `- - 13` | String | N | 누적거래량 |  |  |
| `- - 14` | String | N | 누적거래대금 |  |  |
| `- - 9068` | String | N | VI발동구분 |  |  |
| `- - 9008` | String | N | KOSPI,KOSDAQ,전체구분 |  |  |
| `- - 9075` | String | N | 장전구분 |  |  |
| `- - 1221` | String | N | VI발동가격 |  |  |
| `- - 1223` | String | N | 매매체결처리시각 |  |  |
| `- - 1224` | String | N | VI해제시각 |  |  |
| `- - 1225` | String | N | VI적용구분 | 정적/동적/동적+정적 |  |
| `- - 1236` | String | N | 기준가격 정적 | 계약,주 |  |
| `- - 1237` | String | N | 기준가격 동적 |  |  |
| `- - 1238` | String | N | 괴리율 정적 |  |  |
| `- - 1239` | String | N | 괴리율 동적 |  |  |
| `- - 1489` | String | N | VI발동가 등락율 |  |  |
| `- - 1490` | String | N | VI발동횟수 |  |  |
| `- - 9069` | String | N | 발동방향구분 |  |  |
| `- - 1279` | String | N | Extra Item |  |  |