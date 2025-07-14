# ─── 표준 라이브러리 ──────────────────────────────────────────────────────────
import asyncio
import json
from typing import Any, Dict, List, Optional

# ─── 서드파티 ─────────────────────────────────────────────────────────────────
import pandas as pd
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ─── 내부 모듈 ─────────────────────────────────────────────────────────────────
from .codef.codef import fetch_transactions
from .kis import kis_domstk as kb
from .kis import kis_auth as ka

# 최초 1회 한국투자증권 토큰 발급
ka.auth()

# FastAPI 라우터 인스턴스 (tags 는 Swagger 카테고리 역할)
router = APIRouter(
    tags=["금융 데이터 API"],
    prefix="/api/fin",
)

# ─── 유틸리티 ─────────────────────────────────────────────────────────────────

def df_to_dicts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """DataFrame → list[dict] (UTF-8 한글 보존)

    Notes
    -----
    * `orient="records"` 옵션으로 행(row) 단위 리스트를 생성합니다.
    * `force_ascii=False` 로 한글 필드 값이 이스케이프되지 않도록 합니다.
    """
    return json.loads(df.to_json(orient="records", force_ascii=False))


def record_to_json(rec: Dict[str, Any]) -> JSONResponse:
    """단일 `dict` → FastAPI `JSONResponse`. Swagger 예시로 활용가능."""
    return JSONResponse(content=rec)


def list_to_json(lst: List[Dict[str, Any]]) -> JSONResponse:
    """`list[dict]` → FastAPI `JSONResponse`. Swagger 예시로 활용가능."""
    return JSONResponse(content=lst)

# ─── Pydantic 모델 (Swagger 모델 스키마) ─────────────────────────────────────

class Investment(BaseModel):
    """국내 종목 시세"""
    price:  int   = Field(..., description="현재가 (KRW)")
    change: int   = Field(..., description="전일 대비 (KRW)")

class IndexPrice(BaseModel):
    """국내 지수 시세"""
    price:  float = Field(..., description="현재 지수 값")
    change: float = Field(..., description="전일 대비")

class OverseasPrice(BaseModel):
    """해외 종목 시세"""
    price:  float = Field(..., description="현재가 (해당 통화)")
    change: float = Field(..., description="전일 대비")

class OverseasIndexPrice(BaseModel):
    """해외 지수 시세"""
    price:  float = Field(..., description="현재 지수 값")
    change: float = Field(..., description="전일 대비")

# ─── REST: 종목 현재가 ────────────────────────────────────────────────────────

@router.get(
    "/investments",
    response_model=Investment,
    summary="국내 종목 현재가 조회",
    description="한국투자증권 Open API 를 통해 **6자리 종목코드**의 현재가를 가져옵니다.",
)
async def get_investment(
    itm_no: str = Query(..., regex=r"^\d{6}$", description="종목코드 (6자리, 예: 005930)"),
):
    """단일 국내 종목 현재가 조회"""
    try:
        loop = asyncio.get_running_loop()
        df   = await loop.run_in_executor(None, kb.get_inquire_price, itm_no)
        rec  = df_to_dicts(df)[0]
        payload = {
            "price":  int(rec["stck_prpr"].replace(",", "")),
            "change": int(rec["prdy_vrss"].replace(",", "")),
        }
        return record_to_json(payload)
    except Exception as e:
        raise HTTPException(500, f"종목 조회 실패: {e}")

# ─── REST: 지수 현재가 ────────────────────────────────────────────────────────

@router.get(
    "/index",
    response_model=IndexPrice,
    summary="국내 지수 현재가 조회",
    description="국내 **4자리 지수 코드**(예: 0001 = KOSPI)의 현재 지수 값을 조회합니다.",
)
async def get_index_price(
    idx_code: str = Query(..., regex=r"^\d{4}$", description="지수코드 (4자리)"),
):
    """단일 국내 지수 현재가 조회"""
    try:
        loop = asyncio.get_running_loop()
        df   = await loop.run_in_executor(None, kb.get_inquire_index_price, idx_code)
        rec  = df_to_dicts(df)[0]
        payload = {
            "price":  float(rec["bstp_nmix_prpr"].replace(",", "")),
            "change": float(rec["bstp_nmix_prdy_vrss"].replace(",", "")),
        }
        return record_to_json(payload)
    except Exception as e:
        raise HTTPException(500, f"지수 조회 실패: {e}")

# ─── REST: 해외 주식 현재가 ────────────────────────────────────────────────────

@router.get(
    "/overseas",
    response_model=OverseasPrice,
    summary="해외 종목 현재가 조회",
    description="해외 **티커(symb)** 와 **거래소 코드(excd)** 로 현재가를 조회합니다.\n\n"
                "* `symb` 예: AAPL, MSFT\n"
                "* `excd` 예: NAS (NASDAQ)",
)
async def get_overseas_price(
    symb: str = Query(..., regex=r"^[A-Za-z.\-]{1,10}$", description="티커 (예: AAPL)"),
    excd: str = Query("NAS", regex=r"^[A-Z]{3}$", description="거래소 코드 (예: NAS)"),
):
    """단일 해외 종목 현재가 조회"""
    try:
        loop = asyncio.get_running_loop()
        df   = await loop.run_in_executor(None, kb.get_overseas_price_detail, symb, excd)
        rec  = df_to_dicts(df)[0]
        payload = {
            "price":  float(rec.get("last",  0)),
            "change": float(rec.get("diff",  0)),
        }
        return record_to_json(payload)
    except Exception as e:
        raise HTTPException(500, f"해외 종목 조회 실패: {e}")

# ---- (WebSocket 엔드포인트들은 Swagger UI 에 직접 노출되지는 않으므로 주석만 자세히 달아둡니다.)
#      필요 시 FastAPI "description" 매개변수를 사용하여 문서화할 수 있습니다.

# ─────────────────────────────────────────────────────────────────────────────
# WebSocket: 국내 종목 실시간 시세 스트림
# ---------------------------------------------------------------------------
@router.websocket("/ws/investments")
async def ws_investment(websocket: WebSocket):
    """클라이언트 → 종목코드(6자리) 전송 ↔ 서버 → 0.5초 간격 실시간 시세 JSON"""
    await websocket.accept()
    try:
        itm = await websocket.receive_text()
        if not (itm.isdigit() and len(itm) == 6):
            await websocket.close(code=1008, reason="종목코드 형식 오류")
            return

        loop = asyncio.get_running_loop()
        while True:
            df  = await loop.run_in_executor(None, kb.get_inquire_price, itm)
            rec = df_to_dicts(df)[0]
            await websocket.send_json({
                "price":  int(rec["stck_prpr"].replace(",", "")),
                "change": int(rec["prdy_vrss"].replace(",", "")),
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=1011, reason="서버 오류")

# ─────────────────────────────────────────────────────────────────────────────
# WebSocket: 국내 지수 실시간 시세 스트림
# ---------------------------------------------------------------------------
@router.websocket("/ws/index")
async def ws_index(websocket: WebSocket):
    """클라이언트 → 지수코드(4자리) 전송 ↔ 서버 → 0.5초 간격 실시간 지수 JSON"""
    await websocket.accept()
    try:
        idx = await websocket.receive_text()
        if not (idx.isdigit() and len(idx) == 4):
            await websocket.close(code=1008, reason="지수코드 형식 오류")
            return

        loop = asyncio.get_running_loop()
        while True:
            df  = await loop.run_in_executor(None, kb.get_inquire_index_price, idx)
            rec = df_to_dicts(df)[0]
            await websocket.send_json({
                "price":  float(rec["bstp_nmix_prpr"].replace(",", "")),
                "change": float(rec["bstp_nmix_prdy_vrss"].replace(",", "")),
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=1011, reason="서버 오류")

# ─────────────────────────────────────────────────────────────────────────────
# WebSocket: 해외 종목 실시간 시세 스트림
# ---------------------------------------------------------------------------
@router.websocket("/ws/overseas")
async def ws_overseas(websocket: WebSocket):
    """클라이언트 → "SYM|EXC" 형식 전송 ↔ 서버 → 1초 간격 실시간 시세 JSON"""
    await websocket.accept()
    try:
        raw = await websocket.receive_text()
        if "|" in raw:
            symb, excd = raw.split("|", 1)
            excd = excd.upper()
        else:
            symb, excd = raw, "NAS"

        if not symb.isascii():
            await websocket.close(code=1008, reason="티커 형식 오류")
            return

        loop = asyncio.get_running_loop()
        while True:
            df  = await loop.run_in_executor(None, kb.get_overseas_price_detail, symb, excd)
            rec = df_to_dicts(df)[0]
            await websocket.send_json({
                "price":  float(rec.get("last", 0)),
                "change": float(rec.get("diff", 0)),
            })
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=1011, reason="서버 오류")


