from __future__ import annotations
from datetime import datetime
import pandas as pd

# 내부 모듈
from .. import kis_auth as kis


def _fetch_dataframe(
    url: str,
    tr_id: str,
    params: dict,
    output_attr: str = "output",
) -> pd.DataFrame | None:
    """
    내부 유틸: API 호출 후 응답 데이터를 pandas DataFrame으로 변환

    Parameters
    ----------
    url : str
        API 엔드포인트 경로
    tr_id : str
        요청 트랜잭션 ID
    params : dict
        API 요청 파라미터
    output_attr : str, default "output"
        응답 바디 속성 이름 (예: output, output2)

    Returns
    -------
    pd.DataFrame | None
        • 성공: DataFrame
        • 실패: None (콘솔에 오류 메시지 출력)
    """
    # API 호출
    response = kis._url_fetch(url, tr_id, "", params)
    body = response.getBody()

    # 정상 응답 코드 확인
    if str(body.rt_cd) == "0":
        data = getattr(body, output_attr, None)
        if data is None:
            print(f"⚠️ 응답 데이터({output_attr})가 없습니다.")
            return None

        # 단일 레코드일 경우 리스트로 변환
        if isinstance(data, dict):
            return pd.DataFrame([data])
        return pd.DataFrame(data)

    # 오류 발생 시 콘솔 출력
    print(f"⛔️ {body.msg_cd} — {body.msg1}")
    return None


def get_inquire_price(
    itm_no: str,
    *,
    div_code: str = "J",
    tr_cont: str = "",
) -> pd.DataFrame | None:
    """
    국내주식·ETF/ETN 현재가 조회

    Parameters
    ----------
    itm_no : str
        종목번호(6자리) (ETN은 'Q'로 시작)
    div_code : str, default "J"
        시장 분류 코드: "J"(주식/ETF/ETN), "W"(ELW)
    tr_cont : str, default ""
        연속 조회 구분 (공백 or 'N')

    Returns
    -------
    pd.DataFrame | None
        • 성공: 단일 행 DataFrame
        • 실패: None
    """
    if not itm_no:
        print("⚠️ 종목번호(itm_no)가 지정되지 않았습니다.")
        return None

    url = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"
    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD": itm_no,
    }
    return _fetch_dataframe(url, tr_id, params, output_attr="output")


def get_inquire_index_price(
    idx_code: str = "0001",
    *,
    div_code: str = "U",
    tr_cont: str = "",
) -> pd.DataFrame | None:
    """
    업종·지수 현재지수 조회

    Parameters
    ----------
    idx_code : str, default "0001"
        업종/지수 코드 (4자리: "0001"=코스피, "1001"=코스닥 등)
    div_code : str, default "U"
        시장 분류 코드 (고정 "U")
    tr_cont : str, default ""
        연속 조회 구분

    Returns
    -------
    pd.DataFrame | None
        • 성공: 단일 행 DataFrame
        • 실패: None
    """
    url = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
    tr_id = "FHPUP02100000"
    params = {
        "FID_COND_MRKT_DIV_CODE": div_code,
        "FID_INPUT_ISCD": idx_code,
    }
    return _fetch_dataframe(url, tr_id, params, output_attr="output")


def get_inquire_daily_chartprice(
    excd: str,
    symb: str,
    *,
    gubn: str = "D",
    bymd: str | None = None,
    modp: str = "0",
    tr_cont: str = "",
) -> pd.DataFrame | None:
    """
    해외주식/지수 기간별 시세 조회

    Parameters
    ----------
    excd : str
        거래소 코드 (e.g., "NAS", "NYS")
    symb : str
        종목 심볼 (e.g., "AAPL", "COMP")
    gubn : str, default "D"
        기간 단위: "D"(일), "W"(주), "M"(월)
    bymd : str | None, default None
        조회 종료일 (YYYYMMDD), None이면 오늘 날짜
    modp : str, default "0"
        수정주가 반영 여부: "0"(미반영), "1"(반영)
    tr_cont : str, default ""
        연속 조회 구분

    Returns
    -------
    pd.DataFrame | None
        • 성공: 기간별 시세 DataFrame
        • 실패: None
    """
    if not excd or not symb:
        print("⚠️ 거래소 코드(excd)와 종목 심볼(symb)을 모두 지정해야 합니다.")
        return None

    if bymd is None:
        bymd = datetime.today().strftime("%Y%m%d")

    url = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"
    tr_id = "HHDFS76240000"
    params = {
        "AUTH": "",
        "EXCD": excd,
        "SYMB": symb,
        "GUBN": gubn,
        "BYMD": bymd,
        "MODP": modp,
    }
    return _fetch_dataframe(url, tr_id, params, output_attr="output2")
