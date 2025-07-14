from __future__ import annotations

import pandas as pd
from datetime import datetime

from . import kis_auth as kis

# — 국내 주식 현재가 조회 —
def get_inquire_price(
    itm_no: str,
    div_code: str = "J",
    tr_cont: str = "",
) -> pd.DataFrame | None:
    if not itm_no:
        print("⚠️ itm_no is 필요합니다.")
        return None

    res = kis._url_fetch(
        "/uapi/domestic-stock/v1/quotations/inquire-price",
        "FHKST01010100",
        tr_cont,
        {
            "FID_COND_MRKT_DIV_CODE": div_code,
            "FID_INPUT_ISCD": itm_no,
        },
    )
    body = res.getBody()

    # 성공 시 DataFrame 반환
    if str(body.rt_cd) == "0":
        return pd.DataFrame(body.output, index=[0])

    # 오류 메시지 출력 후 None 반환
    print(f"⛔ {body.msg_cd} — {body.msg1}")
    return None


# — 국내 지수 현재가 조회 —
def get_inquire_index_price(
    idx_code: str = "0001",
    div_code: str = "U",
    tr_cont: str = "",
) -> pd.DataFrame | None:
    res = kis._url_fetch(
        "/uapi/domestic-stock/v1/quotations/inquire-index-price",
        "FHPUP02100000",
        tr_cont,
        {
            "FID_COND_MRKT_DIV_CODE": div_code,
            "FID_INPUT_ISCD": idx_code,
        },
    )
    body = res.getBody()

    if str(body.rt_cd) == "0":
        return pd.DataFrame(body.output, index=[0])

    print(f"⛔ {body.msg_cd} — {body.msg1}")
    return None


# — 해외 주식 상세가 조회 —
def get_overseas_price_detail(
    symb: str,
    excd: str = "NAS",
    auth: str = "",
    tr_cont: str = "",
) -> pd.DataFrame | None:
    if not symb:
        print("⚠️ symb is 필요합니다.")
        return None

    res = kis._url_fetch(
        "/uapi/overseas-price/v1/quotations/price-detail",
        "HHDFS00000300",
        tr_cont,
        {
            "AUTH": auth,
            "EXCD": excd.upper(),
            "SYMB": symb.upper(),
        },
    )
    body = res.getBody()

    if str(body.rt_cd) == "0":
        data = body.output
        # 출력이 dict 일 경우 리스트로 감싸서 DataFrame 생성
        if isinstance(data, dict):
            return pd.DataFrame([data])
        return pd.DataFrame(data)

    print(f"⛔ {body.msg_cd} — {body.msg1}")
    return None

# — 해외 지수 조회 —
def get_overseas_index_price(
    symb: str = "IXIC",
    excd: str = "NAS",
    tr_cont: str = ""
    ):
    code = f"{excd}@{symb}".upper()
    resp = kis._url_fetch(
        "/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice",
        "FHKST03030200",
        tr_cont,
        {
            "FID_COND_MRKT_DIV_CODE": "N",
            "FID_INPUT_ISCD":  code,
            "FID_HOUR_CLS_CODE": "0",
            "FID_PW_DATA_INCU_YN": "Y",      # ★ 변경
        },
    )
    body = resp.getBody()
    print(body)
    if str(body.rt_cd) != "0":
        return None, body            # 실패

    # ① 분봉 데이터가 있는 경우
    if body.output2:
        df = pd.DataFrame(body.output2)
        df["optn_prpr"] = pd.to_numeric(df["optn_prpr"], errors="coerce")
        last_price = df.iloc[0]["optn_prpr"]
        prev_diff  = pd.to_numeric(body.output1["ovrs_nmix_prdy_vrss"],
                                   errors="coerce")
        return (last_price, prev_diff), body

    # ② 분봉이 없으면 스냅샷 사용
    last_price = float(body.output1["ovrs_nmix_prpr"])
    prev_diff  = float(body.output1["ovrs_nmix_prdy_vrss"])
    return (last_price, prev_diff), body
