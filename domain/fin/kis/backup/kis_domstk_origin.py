'''kis_domstk.py

모듈: 국내주식 주문/계좌 API 호출 함수 모음
설명: 한국투자증권 UAPI를 통해 현금주문, 정정/취소, 조회 등 기능을 제공.
      반환형: pandas.DataFrame 또는 None
'''  

# 표준 라이브러리
import time
import copy
import json
from datetime import datetime, timedelta
from collections import namedtuple

# 서드파티 라이브러리
import requests
import pandas as pd

# 내부 모듈
from .. import kis_auth as kis

##############################################################################################

# [국내주식] 주문/계좌 > 주식주문(현금) [v1_국내주식-001]
# 기능: 현금 주문 매수/매도 요청 후 DataFrame 반환
def get_order_cash(ord_dv="", itm_no="", qty=0, unpr=0, tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   ord_dv    str   주문 구분 ("buy": 매수, "sell": 매도)
    #   itm_no    str   종목코드 (6자리, ETN은 'Q'로 시작)
    #   qty       int   주문 수량
    #   unpr      int   주문 단가
    #   tr_cont   str   거래 내용 (옵션)
    #   FK100     str   추가 파라미터 (옵션)
    #   NK100     str   추가 파라미터 (옵션)
    #   dataframe DataFrame | None  반환받을 데이터프레임 (옵션)
    # 반환:
    #   DataFrame | None  주문 성공 시 DataFrame, 실패 시 None
    url = '/uapi/domestic-stock/v1/trading/order-cash'

    # 주문 구분 확인
    if ord_dv == "buy":
        tr_id = "TTTC0802U"  # 현금 매수 주문
    elif ord_dv == "sell":
        tr_id = "TTTC0801U"  # 현금 매도 주문
    else:
        print("매수현금/매도현금 구분 확인 필요")
        return None

    # 필수 입력값 검증
    if not itm_no:
        print("주문 종목번호 확인 필요")
        return None
    if qty <= 0:
        print("주문 수량 확인 필요")
        return None
    if unpr <= 0:
        print("주문 단가 확인 필요")
        return None

    # 요청 파라미터 구성
    params = {
        "CANO":        kis.getTREnv().my_acct,   # 종합계좌번호 (8자리)
        "ACNT_PRDT_CD":kis.getTREnv().my_prod,   # 계좌상품코드 (2자리)
        "PDNO":        itm_no,                   # 종목코드
        "ORD_DVSN":    "00",                     # 지정가
        "ORD_QTY":     str(int(qty)),            # 주문 수량
        "ORD_UNPR":    str(int(unpr))            # 주문 단가
    }

    # API 호출
    res = kis._url_fetch(url, tr_id, tr_cont, params, postFlag=True)

    # 결과 처리
    if str(res.getBody().rt_cd) == "0":
        current_data = pd.DataFrame(res.getBody().output, index=[0])
        return current_data
    else:
        print(f"{res.getBody().msg_cd}, {res.getBody().msg1}")
        return None

##############################################################################################

# [국내주식] 주문/계좌 > 주식주문(정정취소) [v1_국내주식-003]
# 기능: 기존 주문 정정 또는 취소 요청 후 DataFrame 반환
def get_order_rvsecncl(ord_orgno="", orgn_odno="", ord_dvsn="", rvse_cncl_dvsn_cd="", ord_qty=0, ord_unpr=0, qty_all_ord_yn="", tr_cont="", dataframe=None):
    # 입력:
    #   ord_orgno           str   주문 조직 번호 (API 출력 odno)
    #   orgn_odno           str   원주문 번호 (주문번호)
    #   ord_dvsn            str   주문 구분 ("00": 지정가, "01": 시장가, "02": 조건부지정가)
    #   rvse_cncl_dvsn_cd   str   정정/취소 구분 코드 ("01": 정정, "02": 취소)
    #   ord_qty             int   정정/취소 수량
    #   ord_unpr            int   정정 주문 단가 (취소 시 0)
    #   qty_all_ord_yn      str   잔량 전부 주문 여부 ("Y": 전부, "N": 일부)
    #   tr_cont             str   거래 내용 (옵션)
    #   dataframe           DataFrame|None 반환받을 데이터프레임 (옵션)
    # 반환:
    #   DataFrame | None   성공 시 DataFrame, 실패 시 None
    url   = '/uapi/domestic-stock/v1/trading/order-rvsecncl'
    tr_id = "TTTC0803U"  # 정정/취소 주문

    # 필수 입력값 검증
    if not ord_orgno:
        print("주문 조직 번호 확인 필요")
        return None
    if not orgn_odno:
        print("원주문 번호 확인 필요")
        return None
    if not ord_dvsn:
        print("주문 구분 확인 필요")
        return None
    if rvse_cncl_dvsn_cd not in ("01", "02"):
        print("정정/취소 구분 코드 확인 필요")
        return None

    # 잔량 전부 취소 시 수량 0으로 강제 설정
    if qty_all_ord_yn == "Y":
        ord_qty = 0
    elif qty_all_ord_yn == "N" and ord_qty <= 0:
        print("취소/정정 수량 확인 필요")
        return None

    # 정정 주문인 경우 단가 확인
    if rvse_cncl_dvsn_cd == "01" and ord_unpr <= 0:
        print("정정 주문 단가 확인 필요")
        return None

    # 요청 파라미터 구성
    params = {
        "CANO":               kis.getTREnv().my_acct,   # 종합계좌번호
        "ACNT_PRDT_CD":       kis.getTREnv().my_prod,   # 계좌상품코드
        "KRX_FWDG_ORD_ORGNO": ord_orgno,                # 주문 조직 번호
        "ORGN_ODNO":          orgn_odno,               # 원주문 번호
        "ORD_DVSN":           ord_dvsn,                # 주문 구분
        "RVSE_CNCL_DVSN_CD":  rvse_cncl_dvsn_cd,        # 정정/취소 구분
        "ORD_QTY":            str(int(ord_qty)),        # 주문 수량
        "ORD_UNPR":           str(int(ord_unpr)),       # 주문 단가
        "QTY_ALL_ORD_YN":     qty_all_ord_yn            # 잔량 전부 여부
    }

    # API 호출
    res = kis._url_fetch(url, tr_id, tr_cont, params, postFlag=True)

    # 결과 처리 및 반환
    if str(res.getBody().rt_cd) == "0":
        return pd.DataFrame(res.getBody().output, index=[0])
    else:
        print(f"{res.getBody().msg_cd}, {res.getBody().msg1}")
        return None

##############################################################################################

# [국내주식] 주문/계좌 > 주식정정취소가능주문조회 [v1_국내주식-004]
# 기능: 정정/취소 가능 주문 리스트 조회 후 DataFrame 반환 (페이징 처리 포함)
def get_inquire_psbl_rvsecncl_lst(tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   tr_cont    str             조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100      str             CTX_AREA_FK100 (이전 조회 키)
    #   NK100      str             CTX_AREA_NK100 (이전 조회 키)
    #   dataframe  pd.DataFrame | None  누적된 DataFrame (첫 호출 None)
    # 반환:
    #   pd.DataFrame   조회된 주문 리스트
    url   = '/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl'
    tr_id = "TTTC8036R"

    params = {
        "CANO":             kis.getTREnv().my_acct,    # 종합계좌번호
        "ACNT_PRDT_CD":     kis.getTREnv().my_prod,    # 계좌상품코드
        "INQR_DVSN_1":      "1",                        # 정렬순서 (1: 주문순)
        "INQR_DVSN_2":      "0",                        # 조회구분 (0: 전체)
        "CTX_AREA_FK100":   FK100,                      # 페이징 키 FK100
        "CTX_AREA_NK100":   NK100                       # 페이징 키 NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)

    current_data = pd.DataFrame(res.getBody().output)
    dataframe = pd.concat([dataframe, current_data], ignore_index=True) if dataframe is not None else current_data

    tr_cont, FK100, NK100 = (
        res.getHeader().tr_cont,
        res.getBody().ctx_area_fk100,
        res.getBody().ctx_area_nk100
    )

    if tr_cont in ("D", "E"):   # 마지막 페이지
        return pd.DataFrame(dataframe)
    if tr_cont in ("F", "M"):   # 추가 페이지 존재
        return get_inquire_psbl_rvsecncl_lst("N", FK100, NK100, dataframe)

###############################################################################################

# [국내주식] 주문/계좌 > 주식일별주문체결조회
# 기능: 일별 주문 체결 내역 조회 후 DataFrame 반환
def get_inquire_daily_ccld_obj(dv="01", inqr_strt_dt=None, inqr_end_dt=None, tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   dv            str   기간 구분 ("01": 최근 3개월, "02": 3개월 이전)
    #   inqr_strt_dt  str   조회 시작 일자 ("YYYYMMDD"), 미입력 시 오늘
    #   inqr_end_dt   str   조회 종료 일자 ("YYYYMMDD"), 미입력 시 오늘
    #   tr_cont       str   조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100         str   페이징 키 FK100
    #   NK100         str   페이징 키 NK100
    #   dataframe     DataFrame|None  (미사용)
    # 반환:
    #   DataFrame     조회 결과 DataFrame
    url   = '/uapi/domestic-stock/v1/trading/inquire-daily-ccld'
    tr_id = "TTTC8001R" if dv == "01" else "CTSC9115R"

    today = datetime.today().strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or today
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "CANO":            kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":    kis.getTREnv().my_prod,
        "INQR_STRT_DT":    inqr_strt_dt,
        "INQR_END_DT":     inqr_end_dt,
        "SLL_BUY_DVSN_CD": "00",
        "INQR_DVSN":       "01",
        "PDNO":            "",
        "CCLD_DVSN":       "00",
        "ORD_GNO_BRNO":    "",
        "ODNO":            "",
        "INQR_DVSN_3":     "00",
        "INQR_DVSN_1":     "0",
        "CTX_AREA_FK100":  FK100,
        "CTX_AREA_NK100":  NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output2, index=[0])

##############################################################################################

# 주식일별주문체결조회 종목별 List를 DataFrame 으로 반환
def get_inquire_daily_ccld_lst(dv="01", inqr_strt_dt="", inqr_end_dt="", tr_cont="", FK100="", NK100="", dataframe=None):  # 국내주식주문 > 주식일별주문체결조회
    # Input: None (Option) 상세 Input값 변경이 필요한 경우 API문서 참조
    #        dv 기간구분 - 01:3개월 이내(TTTC8001R),  02:3개월 이전(CTSC9115R)
    # Output: DataFrame (Option) output1 API 문서 참조 등
    url = '/uapi/domestic-stock/v1/trading/inquire-daily-ccld'

    if dv == "01":
        tr_id = "TTTC8001R"  # 01:3개월 이내 국내주식체결내역 (월단위 ex: 2024.04.25 이면 2024.01월~04월조회)
    else:
        tr_id = "CTSC9115R"  # 02:3개월 이전 국내주식체결내역 (월단위 ex: 2024.04.25 이면 2024.01월이전)

    if inqr_strt_dt == "":
        inqr_strt_dt = datetime.today().strftime("%Y%m%d")   # 시작일자 값이 없으면 현재일자
    if inqr_end_dt == "":
        inqr_end_dt  = datetime.today().strftime("%Y%m%d")   # 종료일자 값이 없으면 현재일자

    params = {
        "CANO": kis.getTREnv().my_acct, # 종합계좌번호 8자리
        "ACNT_PRDT_CD": kis.getTREnv().my_prod, # 계좌상품코드 2자리
        "INQR_STRT_DT": inqr_strt_dt, # 조회시작일자
        "INQR_END_DT": inqr_end_dt,   # 조회종료일자
        "SLL_BUY_DVSN_CD": "00", # 매도매수구분코드 00:전체 01:매도, 02:매수
        "INQR_DVSN": "01", # 조회구분(정렬순서)  00:역순, 01:정순
        "PDNO": "", # 종목번호(6자리)
        "CCLD_DVSN": "00",  #체결구분 00:전체, 01:체결, 02:미체결
        "ORD_GNO_BRNO": "", # 사용안함
        "ODNO": "", #주문번호
        "INQR_DVSN_3": "00", # 조회구분3 00:전체, 01:현금, 02:융자, 03:대출, 04:대주
        "INQR_DVSN_1": "", # 조회구분1 공란 : 전체, 1 : ELW, 2 : 프리보드
        "CTX_AREA_FK100": FK100, # 공란 : 최초 조회시 이전 조회 Output CTX_AREA_FK100 값 : 다음페이지 조회시(2번째부터)
        "CTX_AREA_NK100": NK100  # 공란 : 최초 조회시 이전 조회 Output CTX_AREA_NK100 값 : 다음페이지 조회시(2번째부터)
    }
    res = kis._url_fetch(url, tr_id, tr_cont, params) # API 호출, kis_auth.py에 존재

    # Assuming 'output1' is a dictionary that you want to convert to a DataFrame
    current_data = pd.DataFrame(res.getBody().output1)

    # Append to the existing DataFrame if it exists
    if dataframe is not None:
        dataframe = pd.concat([dataframe, current_data], ignore_index=True)  #
    else:
        dataframe = current_data

    tr_cont, FK100, NK100 = res.getHeader().tr_cont, res.getBody().ctx_area_fk100, res.getBody().ctx_area_nk100 # 페이징 처리 getHeader(), getBody() kis_auth.py 존재
    # print(dv, tr_cont, FK100, NK100)

    if tr_cont == "D" or tr_cont == "E": # 마지막 페이지
        print("The End")
        return dataframe
    elif tr_cont == "F" or tr_cont == "M": # 다음 페이지 존재하는 경우 자기 호출 처리
        print('Call Next')
        return get_inquire_daily_ccld_lst(dv, inqr_strt_dt, inqr_end_dt, "N", FK100, NK100, dataframe)

##############################################################################################

# [국내주식] 주문/계좌 > 주식잔고조회(현재잔고) [v1_국내주식-005]
# 기능: 현재 주식 계좌 잔고 조회 후 DataFrame 반환
def get_inquire_balance_obj(tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   tr_cont    str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100      str               페이징 키 FK100
    #   NK100      str               페이징 키 NK100
    #   dataframe  pd.DataFrame|None  미사용
    # 반환:
    #   pd.DataFrame  현재 잔고 정보
    url   = '/uapi/domestic-stock/v1/trading/inquire-balance'
    tr_id = "TTTC8434R"

    params = {
        "CANO":                  kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":          kis.getTREnv().my_prod,
        "AFHR_FLPR_YN":          "N",
        "OFL_YN":                "",
        "INQR_DVSN":             "00",
        "UNPR_DVSN":             "01",
        "FUND_STTL_ICLD_YN":     "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN":             "00",
        "CTX_AREA_FK100":        FK100,
        "CTX_AREA_NK100":        NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output2)

##############################################################################################

# [국내주식] 주문/계좌 > 주식잔고조회(현재종목별 잔고) [v1_국내주식-006]
# 기능: 종목별 잔고 리스트 조회 후 DataFrame 반환 (페이징 처리)
def get_inquire_balance_lst(tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   tr_cont    str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100      str               페이징 키 FK100
    #   NK100      str               페이징 키 NK100
    #   dataframe  pd.DataFrame|None  누적 DataFrame
    # 반환:
    #   pd.DataFrame  종목별 잔고 정보
    url   = '/uapi/domestic-stock/v1/trading/inquire-balance'
    tr_id = "TTTC8434R"

    params = {
        "CANO":                  kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":          kis.getTREnv().my_prod,
        "AFHR_FLPR_YN":          "N",
        "OFL_YN":                "",
        "INQR_DVSN":             "00",
        "UNPR_DVSN":             "01",
        "FUND_STTL_ICLD_YN":     "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN":             "00",
        "CTX_AREA_FK100":        FK100,
        "CTX_AREA_NK100":        NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    current_data = pd.DataFrame(res.getBody().output1)

    if dataframe is not None:
        dataframe = pd.concat([dataframe, current_data], ignore_index=True)
    else:
        dataframe = current_data

    tr_cont, FK100, NK100 = (
        res.getHeader().tr_cont,
        res.getBody().ctx_area_fk100,
        res.getBody().ctx_area_nk100
    )

    if tr_cont in ("D", "E"):
        return dataframe
    if tr_cont in ("F", "M"):
        return get_inquire_balance_lst("N", FK100, NK100, dataframe)

##############################################################################################

# [국내주식] 주문/계좌 > 매수가능조회 [v1_국내주식-007]
# 기능: 종목별 매수 가능 현금·수량 조회 후 DataFrame 반환
def get_inquire_psbl_order(pdno="", ord_unpr=0, tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   pdno          str   종목번호 (6자리)
    #   ord_unpr      int   주문 단가 (시장가 조회 시 공란)
    #   tr_cont       str   조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100         str   페이징 키 FK100
    #   NK100         str   페이징 키 NK100
    #   dataframe     DataFrame|None  미사용
    # 반환:
    #   DataFrame    조회 결과
    url   = '/uapi/domestic-stock/v1/trading/inquire-psbl-order'
    tr_id = "TTTC8908R"

    params = {
        "CANO":               kis.getTREnv().my_acct,   # 종합계좌번호
        "ACNT_PRDT_CD":       kis.getTREnv().my_prod,   # 계좌상품코드
        "PDNO":               pdno,                     # 종목번호
        "ORD_UNPR":           ord_unpr,                 # 주문 단가
        "ORD_DVSN":           "00",                     # 지정가 조회
        "CMA_EVLU_AMT_ICLD_YN":"N",                     # CMA 평가금액 포함 여부
        "OVRS_ICLD_YN":       "Y"                       # 해외 포함 여부
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    if res.isOK():
        output_data = res.getBody().output
        if not isinstance(output_data, list):
            output_data = [output_data]
        return pd.DataFrame(output_data, index=[0])
    else:
        res.printError()
        return pd.DataFrame()

##############################################################################################

# [국내주식] 주문/계좌 > 주식예약주문 [v1_국내주식-017]
# 기능: 예약 매수/매도 주문 요청 후 결과 반환
def get_order_resv(ord_dv="", itm_no="", qty=0, unpr=0, ord_dvsn_cd="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   ord_dv          str               "buy": 예약매수, "sell": 예약매도
    #   itm_no          str               종목코드 (6자리, ETN Q로 시작)
    #   qty             int               주문 수량
    #   unpr            int               주문 단가
    #   ord_dvsn_cd     str               주문구분코드 (API 문서 참조)
    #   tr_cont         str               거래 컨텍스트 (옵션)
    #   FK100, NK100    str               페이징 키 (옵션)
    #   dataframe       pd.DataFrame|None  반환 DataFrame (옵션, 미사용)
    # 반환:
    #   dict | None      API 출력 객체 또는 None
    url   = '/uapi/domestic-stock/v1/trading/order-resv'
    tr_id = "CTSC0008U"

    # 매수/매도 구분
    if ord_dv == "buy":
        sll_buy_dvsn_cd = "02"
    elif ord_dv == "sell":
        sll_buy_dvsn_cd = "01"
    else:
        print("매도/매수 구분 확인 필요")
        return None

    # 필수 입력 검증
    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if qty <= 0:
        print("주문 수량 확인 필요")
        return None
    if unpr <= 0:
        print("주문 단가 확인 필요")
        return None
    if not ord_dvsn_cd:
        print("주문구분코드 확인 필요")
        return None

    ord_objt_cbcl_dvsn_cd = "10"  # 예약주문 목적 코드 (현금)

    params = {
        "CANO":                  kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":          kis.getTREnv().my_prod,
        "PDNO":                  itm_no,
        "ORD_QTY":               str(int(qty)),
        "ORD_UNPR":              str(int(unpr)),
        "SLL_BUY_DVSN_CD":       sll_buy_dvsn_cd,
        "ORD_DVSN_CD":           ord_dvsn_cd,
        "ORD_OBJT_CBLC_DVSN_CD": ord_objt_cbcl_dvsn_cd,
        "RSVN_ORD_END_DT":       ""  # 예약주문 종료일자 (YYYYMMDD)
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params, postFlag=True)
    if str(res.getBody().rt_cd) == "0":
        return res.getBody().output
    print(f"{res.getBody().msg_cd}, {res.getBody().msg1}")
    return None

##############################################################################################

# [국내주식] 주문/계좌 > 주식예약주문취소 [v1_국내주식-018/019]
# 기능: 예약 주문 취소 요청 후 결과 반환
def get_order_resv_cncl(rsvn_ord_seq="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   rsvn_ord_seq  str               예약주문순번
    #   tr_cont       str               거래 컨텍스트 (옵션)
    #   FK100, NK100  str               페이징 키 (옵션, 미사용)
    # 반환:
    #   dict | None    성공 시 API 출력 객체, 실패 시 None
    url   = '/uapi/domestic-stock/v1/trading/order-resv-rvsecncl'
    tr_id = "CTSC0009U"

    if not rsvn_ord_seq:
        print("예약주문순번 확인 필요")
        return None

    params = {
        "CANO":         kis.getTREnv().my_acct,        # 종합계좌번호
        "ACNT_PRDT_CD": kis.getTREnv().my_prod,        # 계좌상품코드
        "RSVN_ORD_SEQ": str(int(rsvn_ord_seq))         # 예약주문순번
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params, postFlag=True)
    if str(res.getBody().rt_cd) == "0":
        return res.getBody().output
    print(f"{res.getBody().msg_cd}, {res.getBody().msg1}")
    return None

##############################################################################################

# [국내주식] 주문/계좌 > 주식예약주문정정 [v1_국내주식-018/019]
# 기능: 예약주문 정정 요청 후 결과 반환
def get_order_resv_rvse(
    pdno="", ord_qty=0, ord_unpr=0,
    sll_buy_dvsn_cd="", ord_dvsn="",
    rsvn_ord_seq="", tr_cont="", FK100="", NK100="", dataframe=None
):
    # 입력:
    #   pdno                     str               종목코드 (6자리)
    #   ord_qty                  int               정정 주문 수량
    #   ord_unpr                 int               정정 단가
    #   sll_buy_dvsn_cd          str               매도/매수 구분 코드 ("01": 매도, "02": 매수)
    #   ord_dvsn                 str               주문구분코드 ("00": 지정가, "01": 시장가, "02": 조건부지정가, "05": 장전시간외)
    #   rsvn_ord_seq             str               예약주문순번
    #   기타 옵션 (tr_cont, FK100, NK100) 생략
    # 반환:
    #   dict | None             API 응답 객체 또는 None
    url   = '/uapi/domestic-stock/v1/trading/order-resv-rvsecncl'
    tr_id = "CTSC0013U"

    # 입력 검증
    if ord_qty <= 0:
        print("정정 주문 수량 확인 필요")
        return None
    if ord_unpr <= 0:
        print("정정 단가 확인 필요")
        return None
    if sll_buy_dvsn_cd not in ("01", "02"):
        print("매도/매수 구분 코드 확인 필요")
        return None
    if ord_dvsn not in ("00", "01", "02", "05"):
        print("주문구분코드 확인 필요")
        return None
    if not rsvn_ord_seq:
        print("예약주문순번 확인 필요")
        return None

    ord_objt_cblc_dvsn_cd = "10"  # 현금 기준

    params = {
        "CANO":                  kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":          kis.getTREnv().my_prod,
        "PDNO":                  pdno,
        "ORD_QTY":               str(int(ord_qty)),
        "ORD_UNPR":              str(int(ord_unpr)),
        "SLL_BUY_DVSN_CD":       sll_buy_dvsn_cd,
        "ORD_DVSN_CD":           ord_dvsn,
        "ORD_OBJT_CBLC_DVSN_CD": ord_objt_cblc_dvsn_cd,
        "RSVN_ORD_SEQ":          str(int(rsvn_ord_seq)),
        "LOAN_DT":               "",
        "RSVN_ORD_END_DT":       "",
        "CTAL_TLNO":             "",
        "RSVN_ORD_ORGNO":        "",
        "RSVN_ORD_ORD_DT":       ""
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params, postFlag=True)
    if str(res.getBody().rt_cd) == "0":
        return res.getBody().output
    print(f"{res.getBody().msg_cd}, {res.getBody().msg1}")
    return None

##############################################################################################

# [국내주식] 주문/계좌 > 주식예약주문조회 [v1_국내주식-020]
# 기능: 예약주문 조회 리스트 반환 (페이징 처리 포함)
def get_order_resv_ccnl(
    inqr_strt_dt=None,
    inqr_end_dt=None,
    ord_seq=0,
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
):
    # 입력:
    #   inqr_strt_dt  str               조회 시작 일자 ("YYYYMMDD"), 미입력 시 오늘
    #   inqr_end_dt   str               조회 종료 일자 ("YYYYMMDD"), 미입력 시 오늘
    #   ord_seq       int               예약주문순번 (0: 전체)
    #   tr_cont       str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100, NK100  str               페이징 키
    #   dataframe     pd.DataFrame|None  누적 DataFrame
    # 반환:
    #   pd.DataFrame  예약주문 내역 리스트
    url   = '/uapi/domestic-stock/v1/trading/order-resv-ccnl'
    tr_id = "CTSC0004R"
    today = datetime.today().strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or today
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "RSVN_ORD_ORD_DT":    inqr_strt_dt,
        "RSVN_ORD_END_DT":    inqr_end_dt,
        "RSVN_ORD_SEQ":       ord_seq,
        "TMNL_MDIA_KIND_CD":  "00",
        "CANO":               kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":       kis.getTREnv().my_prod,
        "PRCS_DVSN_CD":       "0",
        "CNCL_YN":            "",
        "PDNO":               "",
        "SLL_BUY_DVSN_CD":    "",
        "CTX_AREA_FK200":     FK100,
        "CTX_AREA_NK200":     NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    current_data = pd.DataFrame(res.getBody().output)
    dataframe = pd.concat([dataframe, current_data], ignore_index=True) if dataframe is not None else current_data

    tr_cont, FK100, NK100 = (
        res.getHeader().tr_cont,
        res.getBody().ctx_area_fk200,
        res.getBody().ctx_area_nk200
    )

    if tr_cont in ("D", "E"):
        return dataframe
    if tr_cont in ("F", "M"):
        return get_order_resv_ccnl(
            inqr_strt_dt,
            inqr_end_dt,
            ord_seq,
            "N",
            FK100,
            NK100,
            dataframe
        )

##############################################################################################

# [국내주식] 주문/계좌 > 주식잔고조회_실현손익 (잔고조회 Output2)
# 기능: 실현 손익 정보 단건 조회 후 DataFrame 반환
def get_inquire_balance_rlz_pl_obj(tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   tr_cont    str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100      str               페이징 키 FK100
    #   NK100      str               페이징 키 NK100
    # 반환:
    #   pd.DataFrame  종목별 실현 손익 정보
    url   = '/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl'
    tr_id = "TTTC8494R"

    params = {
        "CANO":                  kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":          kis.getTREnv().my_prod,
        "AFHR_FLPR_YN":          "N",
        "OFL_YN":                "",
        "INQR_DVSN":             "00",
        "UNPR_DVSN":             "01",
        "FUND_STTL_ICLD_YN":     "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN":             "00",
        "COST_ICLD_YN":          "N",
        "CTX_AREA_FK100":        FK100,
        "CTX_AREA_NK100":        NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output2)


# [국내주식] 주문/계좌 > 주식잔고조회_실현손익 (보유주식내역 Output1)
# 기능: 보유 주식별 실현 손익 리스트 조회 후 DataFrame 반환 (페이징 처리)
def get_inquire_balance_rlz_pl_lst(tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   tr_cont    str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100      str               페이징 키 FK100
    #   NK100      str               페이징 키 NK100
    # 반환:
    #   pd.DataFrame  보유 주식별 실현 손익 정보
    url   = '/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl'
    tr_id = "TTTC8494R"

    params = {
        "CANO":                  kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":          kis.getTREnv().my_prod,
        "AFHR_FLPR_YN":          "N",
        "OFL_YN":                "",
        "INQR_DVSN":             "00",
        "UNPR_DVSN":             "01",
        "FUND_STTL_ICLD_YN":     "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN":             "00",
        "COST_ICLD_YN":          "N",
        "CTX_AREA_FK100":        FK100,
        "CTX_AREA_NK100":        NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    current_data = pd.DataFrame(res.getBody().output1)
    dataframe = pd.concat([dataframe, current_data], ignore_index=True) if dataframe is not None else current_data

    tr_cont, FK100, NK100 = (
        res.getHeader().tr_cont,
        res.getBody().ctx_area_fk100,
        res.getBody().ctx_area_nk100
    )

    if tr_cont in ("D", "E"):
        return dataframe
    return get_inquire_balance_rlz_pl_lst("N", FK100, NK100, dataframe)


##############################################################################################

# [국내주식] 주문/계좌 > 신용매수가능조회 [v1_국내주식-008]
# 기능: 신용 매수 가능 금액 조회 후 DataFrame 반환
def get_inquire_credit_psamount(pdno="", ord_unpr="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   pdno        str               종목번호 (6자리)
    #   ord_unpr    str               주문 단가 (시장가 조회 시 공란 또는 "0")
    #   tr_cont     str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100, NK100 str              페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame                  조회 결과
    url   = '/uapi/domestic-stock/v1/trading/inquire-credit-psamount'
    tr_id = "TTTC8909R"

    params = {
        "CANO":                kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":        kis.getTREnv().my_prod,
        "PDNO":                pdno,
        "ORD_UNPR":            ord_unpr,
        "ORD_DVSN":            "00",
        "CRDT_TYPE":           "21",
        "CMA_EVLU_AMT_ICLD_YN":"N",
        "OVRS_ICLD_YN":        "N"
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output1)


##############################################################################################

# [국내주식] 주문/계좌 > 기간별매매손익현황조회 [v1_국내주식-8715R]
# 기능: 기간별 매매 손익 현황 단건 및 리스트 조회
#   get_inquire_period_trade_profit_obj: 합계 정보(Output2) 단건 조회
def get_inquire_period_trade_profit_obj(inqr_strt_dt=None, inqr_end_dt=None, tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   inqr_strt_dt  str   조회 시작 일자 ("YYYYMMDD"), None이면 오늘
    #   inqr_end_dt   str   조회 종료 일자 ("YYYYMMDD"), None이면 오늘
    #   tr_cont       str   조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100, NK100  str   페이징 키
    #   dataframe     DataFrame|None  누적 DataFrame (lst 전용)
    # 반환:
    #   DataFrame    조회 결과
    url   = '/uapi/domestic-stock/v1/trading/inquire-period-trade-profit'
    tr_id = "TTTC8715R"
    today = datetime.today().strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or today
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "CANO":             kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":     kis.getTREnv().my_prod,
        "SORT_DVSN":        "00",
        "PDNO":             "",
        "INQR_STRT_DT":     inqr_strt_dt,
        "INQR_END_DT":      inqr_end_dt,
        "CBLC_DVSN":        "00",
        "CTX_AREA_FK100":   FK100,
        "CTX_AREA_NK100":   NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output2, index=[0])

##############################################################################################

# [국내주식] 주문/계좌 > 기간별매매손익현황조회 [v1_국내주식-8715R]
# 기능: 기간별 매매 손익 현황 단건 및 리스트 조회
#   get_inquire_period_trade_profit_lst: 종목별 정보(Output1) 리스트 조회 (페이징 처리)
def get_inquire_period_trade_profit_lst(inqr_strt_dt=None, inqr_end_dt=None, tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   inqr_strt_dt  str   조회 시작 일자 ("YYYYMMDD"), None이면 오늘
    #   inqr_end_dt   str   조회 종료 일자 ("YYYYMMDD"), None이면 오늘
    #   tr_cont       str   조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100, NK100  str   페이징 키
    #   dataframe     DataFrame|None  누적 DataFrame (lst 전용)
    # 반환:
    #   DataFrame    조회 결과
    url   = '/uapi/domestic-stock/v1/trading/inquire-period-trade-profit'
    tr_id = "TTTC8715R"
    today = datetime.today().strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or today
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "CANO":             kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":     kis.getTREnv().my_prod,
        "SORT_DVSN":        "00",
        "PDNO":             "",
        "INQR_STRT_DT":     inqr_strt_dt,
        "INQR_END_DT":      inqr_end_dt,
        "CBLC_DVSN":        "00",
        "CTX_AREA_FK100":   FK100,
        "CTX_AREA_NK100":   NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    current_data = pd.DataFrame(res.getBody().output1)
    dataframe = pd.concat([dataframe, current_data], ignore_index=True) if dataframe is not None else current_data

    tr_cont, FK100, NK100 = (
        res.getHeader().tr_cont,
        res.getBody().ctx_area_fk100,
        res.getBody().ctx_area_nk100
    )

    if tr_cont in ("D", "E"):
        return dataframe
    return get_inquire_period_trade_profit_lst(inqr_strt_dt, inqr_end_dt, "N", FK100, NK100, dataframe)

##############################################################################################

# [국내주식] 주문/계좌 > 기간별손익일별합산조회 [v1_국내주식-8708R]
# 기능: 기간별 손익 일별 합산 정보 단건 조회 후 DataFrame 반환
def get_inquire_period_profit_obj(inqr_strt_dt=None, inqr_end_dt=None, tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   inqr_strt_dt  str               조회 시작 일자 ("YYYYMMDD"), None이면 오늘
    #   inqr_end_dt   str               조회 종료 일자 ("YYYYMMDD"), None이면 오늘
    #   tr_cont       str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100         str               페이징 키 FK100
    #   NK100         str               페이징 키 NK100
    # 반환:
    #   pd.DataFrame  기간별 손익 일별 합산 정보
    url   = '/uapi/domestic-stock/v1/trading/inquire-period-profit'
    tr_id = "TTTC8708R"

    today = datetime.today().strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or today
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "CANO":             kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":     kis.getTREnv().my_prod,
        "INQR_DVSN":        "00",
        "SORT_DVSN":        "00",
        "PDNO":             "",
        "INQR_STRT_DT":     inqr_strt_dt,
        "INQR_END_DT":      inqr_end_dt,
        "CBLC_DVSN":        "00",
        "CTX_AREA_FK100":   FK100,
        "CTX_AREA_NK100":   NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output2, index=[0])


#######################################################################################

# [국내주식] 주문/계좌 > 기간별손익일별합산조회 (output1) [v1_국내주식-8708R]
# 기능: 기간별 손익 일별 합산 정보 리스트 조회 후 DataFrame 반환 (페이징 처리)
def get_inquire_period_profit_lst(
    inqr_strt_dt=None,
    inqr_end_dt=None,
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
):
    # 입력:
    #   inqr_strt_dt  str               조회 시작 일자 ("YYYYMMDD"), None이면 오늘
    #   inqr_end_dt   str               조회 종료 일자 ("YYYYMMDD"), None이면 오늘
    #   tr_cont       str               조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100         str               페이징 키 FK100
    #   NK100         str               페이징 키 NK100
    #   dataframe     pd.DataFrame|None  누적 DataFrame
    # 반환:
    #   pd.DataFrame  기간별 손익 일별 합산 정보 리스트
    url   = '/uapi/domestic-stock/v1/trading/inquire-period-profit'
    tr_id = "TTTC8708R"
    today = datetime.today().strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or today
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "CANO":             kis.getTREnv().my_acct,
        "ACNT_PRDT_CD":     kis.getTREnv().my_prod,
        "INQR_DVSN":        "00",          # 조회구분
        "SORT_DVSN":        "00",          # 정렬구분
        "PDNO":             "",            # 상품번호 (공백 시 전체)
        "INQR_STRT_DT":     inqr_strt_dt,
        "INQR_END_DT":      inqr_end_dt,
        "CBLC_DVSN":        "00",          # 잔고구분
        "CTX_AREA_FK100":   FK100,
        "CTX_AREA_NK100":   NK100
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    current_data = pd.DataFrame(res.getBody().output1)
    dataframe = pd.concat([dataframe, current_data], ignore_index=True) if dataframe is not None else current_data

    tr_cont, FK100, NK100 = (
        res.getHeader().tr_cont,
        res.getBody().ctx_area_fk100,
        res.getBody().ctx_area_nk100
    )

    if tr_cont in ("D", "E"):
        return dataframe
    return get_inquire_period_profit_lst(inqr_strt_dt, inqr_end_dt, "N", FK100, NK100, dataframe)


#######################################################################################

#====|  [국내주식] 기본시세  |============================================================================================================================

#######################################################################################

# [국내주식] 기본시세 > 주식현재가 시세
# 기능: 종목 현재가 조회 후 DataFrame 반환
def get_inquire_price(div_code="J", itm_no="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   div_code  str               시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no    str               종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont   str               조회 구분 (옵션)
    #   FK100     str               페이징 키 (옵션, 미사용)
    #   NK100     str               페이징 키 (옵션, 미사용)
    # 반환:
    #   pd.DataFrame               조회 결과
    url   = '/uapi/domestic-stock/v1/quotations/inquire-price'
    tr_id = "FHKST01010100"

    if not itm_no:
        print("종목번호 확인 필요")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    if str(res.getBody().rt_cd) == "0":
        return pd.DataFrame(res.getBody().output, index=[0])
    print(f"{res.getBody().msg_cd}, {res.getBody().msg1}")
    return None


#######################################################################################

# [국내주식] 기본시세 > 주식현재가 체결
# 기능: 최근 체결 30건 조회 후 DataFrame 반환
def get_inquire_ccnl(div_code="J", itm_no="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   div_code  str               시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no    str               종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont   str               조회 구분 (옵션)
    #   FK100     str               페이징 키 (옵션)
    #   NK100     str               페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame               조회 결과
    url   = '/uapi/domestic-stock/v1/quotations/inquire-ccnl'
    tr_id = "FHKST01010300"

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output)


##############################################################################################

# [국내주식] 기본시세 > 주식현재가 일자별
# 기능: 일/주/월별 주가 조회 (최대 최근 30건)
def get_inquire_daily_price(div_code="J", itm_no="", period_code="D", adj_prc_code="1", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   div_code      str   시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no        str   종목번호 (6자리, ETN은 'Q'로 시작)
    #   period_code   str   기간분류코드 ("D": 일, "W": 주, "M": 월)
    #   adj_prc_code  str   수정주가코드 ("0": 수정주가반영, "1": 미반영)
    #   tr_cont       str   조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100, NK100  str   페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame       조회 결과
    url   = '/uapi/domestic-stock/v1/quotations/inquire-daily-price'
    tr_id = "FHKST01010400"

    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if period_code not in ("D", "W", "M"):
        print("기간분류코드 확인 필요")
        return None
    if adj_prc_code not in ("0", "1"):
        print("수정주가코드 확인 필요")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no,
        "FID_PERIOD_DIV_CODE":    period_code,
        "FID_ORG_ADJ_PRC":        adj_prc_code
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output)


##############################################################################################

# [국내주식] 기본시세 > 주식현재가 호가/예상체결
# 기능: 매수/매도 호가 또는 예상체결가 조회 후 DataFrame 반환
def get_inquire_asking_price_exp_ccn(output_dv="1", div_code="J", itm_no="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   output_dv   str               "1": 호가조회(output1), "2": 예상체결(output2)
    #   div_code    str               시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no      str               종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont     str               조회 구분 (옵션)
    #   FK100, NK100 str              페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame | None          조회 결과 또는 None
    url   = '/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn'
    tr_id = "FHKST01010200"

    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if output_dv not in ("1", "2"):
        print("output_dv 확인 필요: '1' 또는 '2'")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()

    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None

    if output_dv == "1":
        df = pd.DataFrame(body.output1, index=[0])
    else:
        df = pd.DataFrame(body.output2, index=[0])

    return df


##############################################################################################

# [국내주식] 기본시세 > 주식현재가 투자자
# 기능: 개인·외국인·기관 등 투자자별 매매 정보 조회 후 DataFrame 반환
def get_inquire_investor(div_code="J", itm_no="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   div_code    str               시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no      str               종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont     str               조회 구분 (옵션)
    #   FK100       str               페이징 키 (옵션)
    #   NK100       str               페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame                  조회 결과
    url   = '/uapi/domestic-stock/v1/quotations/inquire-investor'
    tr_id = "FHKST01010900"

    if not itm_no:
        print("종목번호 확인 필요")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None

    return pd.DataFrame(res.getBody().output)


##############################################################################################

# [국내주식] 기본시세 > 주식현재가 회원사
# 기능: 회원사별 투자 정보 조회 후 DataFrame 반환
def get_inquire_member(div_code="J", itm_no="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   div_code    str   시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no      str   종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont     str   조회 컨텍스트 (옵션)
    #   FK100       str   페이징 키 FK100 (옵션)
    #   NK100       str   페이징 키 NK100 (옵션)
    # 반환:
    #   pd.DataFrame | None   조회 결과 또는 None (실패/입력 오류)
    url   = '/uapi/domestic-stock/v1/quotations/inquire-member'
    tr_id = "FHKST01010600"

    if not itm_no:
        print("종목번호 확인 필요")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,  # 시장 분류 코드
        "FID_INPUT_ISCD":         itm_no     # 종목번호
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()

    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    return pd.DataFrame(body.output, index=[0])


##############################################################################################

# [국내주식] 기본시세 > 국내주식기간별시세(일/주/월/년) [v1_FHKST03010100]
# 기능: 지정 기간(일/주/월/년)별 시세 조회 후 DataFrame 반환
def get_inquire_daily_itemchartprice_temp(
    div_code="J",
    itm_no="",
    inqr_strt_dt=None,
    inqr_end_dt=None,
    period_code="D",
    adj_prc="1",
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
):
    # 입력:
    #   div_code        str   시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no          str   종목번호 (6자리, ETN은 'Q'로 시작)
    #   inqr_strt_dt    str   조회 시작 일자 ("YYYYMMDD"), None이면 14일 전
    #   inqr_end_dt     str   조회 종료 일자 ("YYYYMMDD"), None이면 오늘
    #   period_code     str   기간분류코드 ("D":일, "W":주, "M":월, "Y":년)
    #   adj_prc         str   수정주가코드 ("0":수정반영, "1":미반영)
    #   tr_cont         str   조회 구분 (첫 호출 공란, 이후 "N")
    #   FK100, NK100    str   페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame          조회 결과 (output1)
    url   = '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
    tr_id = "FHKST03010100"

    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if period_code not in ("D", "W", "M", "Y"):
        print("기간분류코드 확인 필요")
        return None
    if adj_prc not in ("0", "1"):
        print("수정주가코드 확인 필요")
        return None

    today = datetime.today().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=14)).strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or start
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no,
        "FID_INPUT_DATE_1":       inqr_strt_dt,
        "FID_INPUT_DATE_2":       inqr_end_dt,
        "FID_PERIOD_DIV_CODE":    period_code,
        "FID_ORG_ADJ_PRC":        adj_prc
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    return pd.DataFrame(res.getBody().output1, index=[0])


##############################################################################################

# [국내주식] 기본시세 > 국내주식기간별시세(일/주/월/년) [v1_FHKST03010100]
# 기능: 지정 기간(일/주/월/년)별 시세 조회 후 DataFrame 반환
def get_inquire_daily_itemchartprice(
    output_dv="1",
    div_code="J",
    itm_no="",
    inqr_strt_dt=None,
    inqr_end_dt=None,
    period_code="D",
    adj_prc="1",
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
):
    # 입력:
    #   output_dv     str   "1": output1 조회, "2": output2 조회
    #   div_code      str   시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no        str   종목번호 (6자리, ETN은 'Q'로 시작)
    #   inqr_strt_dt  str   조회 시작 일자 ("YYYYMMDD"), None이면 100일 전
    #   inqr_end_dt   str   조회 종료 일자 ("YYYYMMDD"), None이면 오늘
    #   period_code   str   기간분류코드 ("D": 일, "W": 주, "M": 월, "Y": 년)
    #   adj_prc       str   수정주가코드 ("0": 수정주가 반영, "1": 미반영)
    #   tr_cont       str   조회 구분 (옵션)
    #   FK100, NK100  str   페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame | None  조회 결과 혹은 None (입력 오류/조회 실패)
    url   = '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
    tr_id = "FHKST03010100"

    # 입력 검증
    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if output_dv not in ("1", "2"):
        print("output_dv 확인 필요 ('1' 또는 '2')")
        return None
    if period_code not in ("D", "W", "M", "Y"):
        print("기간분류코드 확인 필요 ('D', 'W', 'M', 'Y')")
        return None
    if adj_prc not in ("0", "1"):
        print("수정주가코드 확인 필요 ('0' 또는 '1')")
        return None

    # 기본 날짜 설정
    today = datetime.today().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")
    inqr_strt_dt = inqr_strt_dt or start
    inqr_end_dt  = inqr_end_dt  or today

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no,
        "FID_INPUT_DATE_1":       inqr_strt_dt,
        "FID_INPUT_DATE_2":       inqr_end_dt,
        "FID_PERIOD_DIV_CODE":    period_code,
        "FID_ORG_ADJ_PRC":        adj_prc
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()
    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    if output_dv == "1":
        return pd.DataFrame(body.output1, index=[0])
    return pd.DataFrame(body.output2)

##############################################################################################

# [국내주식] 기본시세 > 주식현재가 당일시간대별체결 [v1_FHPST01060000]
# 기능: 기준시각 이전 체결 내역(최대 30건) 조회 후 DataFrame 반환
def get_inquire_time_itemconclusion(
    output_dv="1",
    div_code="J",
    itm_no="",
    inqr_hour=None,
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
):
    # 입력:
    #   output_dv    str   "1": output1 조회, "2": output2 조회
    #   div_code     str   시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no       str   종목번호 (6자리, ETN은 'Q'로 시작)
    #   inqr_hour    str   기준시간 ("HHMMSS"), None이면 현재 시각
    #   tr_cont      str   조회 구분 (옵션)
    #   FK100, NK100 str   페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame | None 조회 결과 또는 None
    url   = '/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion'
    tr_id = "FHPST01060000"

    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if output_dv not in ("1", "2"):
        print("output_dv 확인 필요 ('1' 또는 '2')")
        return None

    if inqr_hour is None:
        inqr_hour = datetime.now().strftime("%H%M%S")

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no,
        "FID_INPUT_HOUR_1":       inqr_hour
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()
    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    if output_dv == "1":
        return pd.DataFrame(body.output1, index=[0])
    return pd.DataFrame(body.output2)

##############################################################################################

# [국내주식] 기본시세 > 주식현재가 시간외일자별주가 [v1_FHPST02320000]
# 기능: 시간외 현재가 및 시간외 일자별 주가 조회 후 DataFrame 반환
def get_inquire_daily_overtimeprice(
    output_dv="1",
    div_code="J",
    itm_no="",
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
    ):
    # 입력:
    #   output_dv   str   "1": 시간외 현재가(output1), "2": 일자별 시간외 주가(output2)
    #   div_code    str   시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no      str   종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont     str   조회 구분 (옵션)
    #   FK100, NK100 str  페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame | None  조회 결과 DataFrame 또는 None
    url   = '/uapi/domestic-stock/v1/quotations/inquire-daily-overtimeprice'
    tr_id = "FHPST02320000"

    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if output_dv not in ("1", "2"):
        print("output_dv 확인 필요: '1' 또는 '2'")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()

    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    if output_dv == "1":
        return pd.DataFrame(body.output1, index=[0])
    return pd.DataFrame(body.output2)

##############################################################################################

# [국내주식] 기본시세 > 주식당일분봉조회 [v1_FHKST03010200]
# 기능: 당일 분봉(최대 30건) 또는 업종 분봉 조회 후 DataFrame 반환
def get_inquire_time_itemchartprice(
    output_dv="1",
    div_code="J",
    itm_no="",
    inqr_hour=None,
    incu_yn="N",
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
):
    # 입력:
    #   output_dv      str               "1": output1(주식 분봉), "2": output2(시간별 분봉)
    #   div_code       str               시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no         str               종목번호 (6자리, ETN은 'Q'로 시작)
    #   inqr_hour      str               기준시간 "HHMMSS" (None이면 현재 시각)
    #   incu_yn        str               과거 데이터 포함 여부 ("Y"/"N", 업종 조회 시)
    #   tr_cont        str               조회 구분 (옵션)
    #   FK100, NK100   str               페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame | None  조회 결과 또는 None (입력 오류/조회 실패)
    url   = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
    tr_id = "FHKST03010200"

    # 입력 검증
    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if output_dv not in ("1", "2"):
        print("output_dv 확인 필요 ('1' 또는 '2')")
        return None

    # 기준시간 설정
    if inqr_hour is None:
        inqr_hour = datetime.now().strftime("%H%M%S")

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no,
        "FID_INPUT_HOUR_1":       inqr_hour,
        "FID_PW_DATA_INCU_YN":    incu_yn
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()

    # 응답 검증
    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    # DataFrame 변환 및 반환
    if output_dv == "1":
        return pd.DataFrame(body.output1, index=[0])
    return pd.DataFrame(body.output2)

##############################################################################################

# [국내주식] 기본시세 > 주식현재가 시세2 [v1_FHPST01010000]
# 기능: 종목 현재가 시세2 조회 후 DataFrame 반환
def get_inquire_daily_price_2(div_code="J", itm_no="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   div_code    str   시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no      str   종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont     str   조회 구분 (옵션)
    #   FK100, NK100 str   페이징 키 (옵션, 미사용)
    # 반환:
    #   pd.DataFrame | None  조회 결과 또는 None
    url   = '/uapi/domestic-stock/v1/quotations/inquire-price-2'
    tr_id = "FHPST01010000"

    if not itm_no:
        print("종목번호 확인 필요")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()
    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    return pd.DataFrame(body.output, index=[0])

##############################################################################################

# [국내주식] 기본시세 > ETF/ETN 현재가 [v1_FHPST02400000]
# 기능: ETF/ETN 현재가 조회 후 DataFrame 반환
def get_quotations_inquire_price(div_code="J", itm_no="", tr_cont="", FK100="", NK100="", dataframe=None):
    # 입력:
    #   div_code    str               시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no      str               종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont     str               조회 구분 (옵션)
    #   FK100, NK100 str               페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame | None           조회 결과 또는 None
    url   = '/uapi/etfetn/v1/quotations/inquire-price'
    tr_id = "FHPST02400000"

    if not itm_no:
        print("종목번호 확인 필요")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()

    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    return pd.DataFrame(body.output, index=[0])

##############################################################################################

# [국내주식] 기본시세 > NAV 비교추이(종목) [v1_FHPST02440000]
# 기능: ETF/ETN NAV 및 IIV 비교추이 조회 후 DataFrame 반환
def get_quotations_nav_comparison_trend(
    output_dv="1",
    div_code="J",
    itm_no="",
    tr_cont="",
    FK100="",
    NK100="",
    dataframe=None
):
    # 입력:
    #   output_dv   str               "1": output1 조회, "2": output2 조회
    #   div_code    str               시장 분류 코드 ("J": 주식/ETF/ETN, "W": ELW)
    #   itm_no      str               종목번호 (6자리, ETN은 'Q'로 시작)
    #   tr_cont     str               조회 구분 (옵션)
    #   FK100, NK100 str               페이징 키 (옵션)
    # 반환:
    #   pd.DataFrame | None           조회 결과 또는 None
    url   = '/uapi/etfetn/v1/quotations/nav-comparison-trend'
    tr_id = "FHPST02440000"

    if not itm_no:
        print("종목번호 확인 필요")
        return None
    if output_dv not in ("1", "2"):
        print("output_dv 확인 필요 ('1' 또는 '2')")
        return None

    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD":         itm_no
    }

    res = kis._url_fetch(url, tr_id, tr_cont, params)
    body = res.getBody()

    if hasattr(res, "isOK") and not res.isOK():
        res.printError()
        return None
    if hasattr(body, "rt_cd") and str(body.rt_cd) != "0":
        print(f"{body.msg_cd}, {body.msg1}")
        return None

    if output_dv == "1":
        return pd.DataFrame(body.output1, index=[0])
    return pd.DataFrame(body.output2, index=[0])

