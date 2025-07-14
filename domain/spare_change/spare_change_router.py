# File: domain/spare_change/spare_change_router.py
import logging

from datetime import datetime
from typing   import List

from fastapi          import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm   import Session
from starlette.config import Config

from database                import get_db
from models                  import User
from domain.user.user_router import get_current_user
from .                       import spare_change_schema as schema
from .                       import spare_change_crud   as crud


# ────────────────────────── 설정값 & 로거 ──────────────────────────
config     = Config(".env")
DEBUG_MODE = config("DEBUG_MODE", default="false").lower() == "true"

_log_level = logging.DEBUG if DEBUG_MODE else logging.WARNING
logging.basicConfig(
    level  = _log_level,
    format = "[%(levelname)s][%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


def _debug(category: str, message: str) -> None:
    """일관된 형식의 디버그 로그 기록"""

    if DEBUG_MODE:
        logger.debug(f"[{category}] {message}")


router = APIRouter(
    prefix = "/api/spare-change",
    tags   = ["잔돈(라운드-업)"],
    responses = {
        401: {"description": "인증 실패 또는 토큰 만료"},
        400: {"description": "잘못된 요청 파라미터"},
    },
)


# ────────────────────────── Round-Up Unit 엔드포인트 ──────────────────────────
@router.get(
    "/round-up-unit",
    response_model = schema.RoundUpUnitOut,
    summary        = "현재 라운드-업 단위 조회",
    description    = """
로그인 사용자의 “라운드-업 단위(round_up_unit)”를 조회합니다.

✔ 라운드-업 단위란?
└─ 계좌 거래 금액을 지정된 최소 단위(예: 100원)로 올림(Round-Up) 할 때
   기준이 되는 값입니다.  
   예) 단위가 100원일 때 7 ,430원 → 7 ,500원으로 올림 → 잔돈 70원 적립

- 인증 필수: JWT(헤더 또는 HttpOnly 쿠키)
- 응답 필드
  • `round_up_unit` (int) : 현재 설정된 단위
""",
)
def get_round_up_unit(
    current_user: User = Depends(get_current_user)
):
    """로그인 사용자의 round_up_unit 값을 반환"""

    unit = current_user.round_up_unit
    _debug("ROUND_UNIT", f"조회 user_id={current_user.id} unit={unit}")
    return {"round_up_unit": unit}

@router.patch(
    "/round-up-unit",
    response_model = schema.RoundUpUnitOut,
    status_code    = status.HTTP_200_OK,
    summary        = "라운드-업 단위 변경",
    description    = """
사용자의 라운드-업 단위를 갱신합니다.

요청 본문(JSON, `application/json`)
{
  "unit": 500    // 양의 정수만 허용
}

동작 흐름
1. 서버가 unit 값 유효성(>0) 검증
2. DB의 user.round_up_unit 업데이트
3. 변경된 값 반환 → 이후 생성되는 잔돈 계산부터 즉시 적용

⚠ 주의
- 과거에 이미 계산·적립된 잔돈에는 소급 적용되지 않습니다.
- 동일 값으로 요청 시에도 200 OK가 반환됩니다.
""",
)
def update_round_up_unit(
    unit         : int     = Body(..., embed=True, gt=0, description="새 라운드-업 단위 (양의 정수)"),
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db),
):
    """사용자 round_up_unit 컬럼을 업데이트"""

    _debug("ROUND_UNIT", f"변경 요청 user_id={current_user.id} → {unit}")
    try:
        new_unit = crud.update_round_up_unit(db, current_user.id, unit)
    except ValueError as e:
        _debug("ROUND_UNIT", f"변경 실패 user_id={current_user.id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    _debug("ROUND_UNIT", f"변경 완료 user_id={current_user.id} → {new_unit}")
    return {"round_up_unit": new_unit}


# ────────────────────────── Spare-Change 엔드포인트 ──────────────────────────
@router.post(
    "",
    response_model = schema.SpareChangeOut,
    status_code    = status.HTTP_201_CREATED,
    summary        = "거래 잔돈 생성",
    description    = """
거래 1건의 ‘라운드-업 잔돈’을 계산하여 저장합니다.

요청 본문
{
  "tx_id" : "ACCT-123-20250713093010",  // 거래 고유 ID
  "amount": 7430.00                    // 거래 금액 (Decimal)
}

서버 처리
1. 로그인 사용자의 round_up_unit 조회
2. 올림 금액 계산
     ceil(amount / unit) * unit – amount
3. SpareChange 테이블에 (user_id, tx_id, round_up) 저장
4. 생성 결과 반환

응답 예시
{
  "user_id" : 17,
  "tx_id"   : "ACCT-123-20250713093010",
  "round_up": 70.00,
  "created_at": "2025-07-13T09:30:12+09:00"
}
""",
)
def create_spare_change(
    payload      : schema.SpareChangeCreate,
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db)
):
    """amount·tx_id 입력 → 서버가 round_up 계산 후 저장"""

    payload = payload.copy(update={"user_id": current_user.id})
    _debug("SPARE_CHANGE", f"생성 요청 user_id={current_user.id} tx_id={payload.tx_id}")
    return crud.create_spare_change(db, payload)


@router.get(
    "",
    response_model = List[schema.SpareChangeOut],
    summary        = "사용자 잔돈 목록",
    description    = """
로그인 사용자의 모든 라운드-업 잔돈 내역을 반환합니다.

정렬
- 최근 생성 순(created_at DESC)

응답 필드
- `user_id`     : 사용자 ID
- `tx_id`       : 거래 ID
- `round_up`    : 잔돈 금액
- `created_at`  : 생성 시각(KST ISO-8601)
""",
)
def list_spare_changes(
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db),
):
    """로그인 사용자의 잔돈 내역 반환"""

    _debug("SPARE_CHANGE", f"목록 조회 user_id={current_user.id}")
    return crud.get_spare_changes_by_user(db, current_user.id)


@router.get(
    "/summary",
    response_model = schema.SpareChangeSummary,
    summary        = "기간별 잔돈 합계",
    description    = """
지정 기간 동안 적립된 잔돈 총합을 계산합니다.

쿼리 파라미터
- `period_start` (ISO-8601) : 포함 시작
- `period_end`   (ISO-8601) : 미포함 끝 → start ≤ created_at < end

응답 예시
{
  "total_round_up": 12850.00,
  "count"        : 187,
  "period_start" : "2025-07-01T00:00:00+09:00",
  "period_end"   : "2025-08-01T00:00:00+09:00"
}

유효성
- `period_end` 은 `period_start` 보다 반드시 미래여야 합니다.
  그렇지 않으면 400 에러를 반환합니다.

""",
)
def spare_change_summary(
    period_start : datetime,
    period_end   : datetime,
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db),
):
    """period_start ≤ created_at < period_end 범위 합계"""

    if period_end <= period_start:
        raise HTTPException(400, "period_end must be after period_start.")
    _debug(
        "SPARE_CHANGE",
        f"요약 user_id={current_user.id} {period_start.isoformat()} → {period_end.isoformat()}",
    )
    return crud.get_spare_change_summary(db, current_user.id, period_start, period_end)
