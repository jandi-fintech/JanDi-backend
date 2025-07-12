# File: domain/spare_change/spare_change_router.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db # 의존성 주입용 DB 세션
from models import User
from domain.user.user_router import get_current_user
from . import spare_change_schema as schema
from . import spare_change_crud  as crud


router = APIRouter(
    prefix = "/api/spare-change",
    tags   = ["잔돈"],
)


# ───────────────────────────────────────────────────────────────────────────
@router.post(
    "/round-up-config",
    response_model = schema.RoundUpConfig,
    status_code    = status.HTTP_201_CREATED,
    description    = """
### 기능
- 로그인된 사용자의 **라운드-업 단위(unit)** 를 새로 등록합니다.
- 동일 사용자-단위 조합이 이미 존재하면 400 - `Duplicated round-up config.` 오류 반환

### 비즈니스 규칙
1. `user_id` 는 액세스 토큰에서 추출되므로 요청 본문에 포함하지 않습니다.
2. 최근에 생성된 단위가 “현재 적용 단위”로 간주됩니다.

### 요청 예시
{
  "unit": 500          // 500원 단위로 반올림
}

### 응답 예시
{
  "id":         3,
  "user_id":    7,
  "unit":       500,
  "created_at": "2025-07-12T09:15:24.123Z"
}
""",
)
def create_round_up_config(
    payload      : schema.RoundUpConfigCreate,
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db)
):
    """
    라운드-업 단위 설정 생성
    유저 ID는 인증된 현재 사용자에서 가져옴
    """
    payload_data            = payload.dict()
    payload_data['user_id'] = current_user.id
    new_payload             = schema.RoundUpConfigCreate(**payload_data)
    try:
        return crud.create_round_up_config(db, new_payload)
    except ValueError as e:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = str(e)
        )


# ───────────────────────────────────────────────────────────────────────────
@router.get(
    "/round-up-config",
    response_model = List[schema.RoundUpConfig],
    description    = """
### 기능
- 로그인 사용자의 **라운드-업 단위 설정 목록**(최신순)을 반환합니다.

### 참고
- 배열이 비어 있으면 서버의 기본 단위(DEFAULT_UNIT, 보통 100원)가 적용됩니다.
""",
)
def list_round_up_configs(
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db)
):
    """
    인증된 사용자의 라운드-업 설정 조회
    """
    return crud.get_round_up_configs(db, current_user.id)


# ───────────────────────────────────────────────────────────────────────────
@router.post(
    "",
    response_model = schema.SpareChangeOut,
    status_code    = status.HTTP_201_CREATED,
    description    = """
### 기능
- 거래 금액(`amount`)과 거래 ID(`tx_id`)를 입력받아
  서버가 라운드-업 금액(`round_up`)을 계산하여 저장합니다.

### 라운드-업 공식
ceil(amount / unit) × unit − amount  
(소수점 둘째 자리까지 반올림)

### 에러
- 동일 `tx_id` 로 이미 등록돼 있으면 400 - `Duplicated spare_change entry.`

### 요청 예시
{
  "tx_id":  "TX20250712001",
  "amount": 12340
}

### 응답 예시
{
  "user_id":    7,
  "tx_id":      "TX20250712001",
  "round_up":   160,
  "amount":     12340,
  "created_at": "2025-07-12T09:17:05.456Z"
}
""",
)
def create_spare_change(
    payload      : schema.SpareChangeCreate,
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db)
):
    """
    거래별 잔돈 생성
    유저 ID는 인증된 현재 사용자에서 가져옴
    """
    payload = payload.copy(update={"user_id": current_user.id})
    return crud.create_spare_change(db, payload)


# ───────────────────────────────────────────────────────────────────────────
@router.get(
    "",
    response_model = List[schema.SpareChangeOut],
    description    = """
### 기능
- 로그인 사용자의 **모든 잔돈 내역**을 반환합니다.
- 필요에 따라 프론트엔드에서 날짜·금액 필터를 추가 구현하세요.
""",
)
def list_spare_changes(
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db)
):
    """
    인증된 사용자의 잔돈 내역 조회
    """
    return crud.get_spare_changes_by_user(db, current_user.id)


# ───────────────────────────────────────────────────────────────────────────
@router.get(
    "/summary",
    response_model = schema.SpareChangeSummary,
    description    = """
### 기능
- `period_start` ≤ `created_at` < `period_end` 범위의 `round_up` 합계(`total_round_up`)를 계산합니다.

### 파라미터
| 이름 | 타입 | 설명 |
|------|------|------|
| `period_start` | ISO 8601 datetime | 집계 시작(포함) |
| `period_end`   | ISO 8601 datetime | 집계 종료(미포함) |

> `period_end` 는 반드시 `period_start` 이후여야 하며, 그렇지 않으면 400 오류를 반환합니다.

### 응답 예시
{
  "total_round_up": 4520,
  "period_start":   "2025-07-01T00:00:00",
  "period_end":     "2025-08-01T00:00:00"
}
""",
)
def spare_change_summary(
    period_start : datetime,
    period_end   : datetime,
    current_user : User    = Depends(get_current_user),
    db           : Session = Depends(get_db)
):
    """
    기간별 잔돈 합계 조회
    유저 ID는 인증된 현재 사용자에서 가져옴
    """
    if period_end <= period_start:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "period_end must be after period_start."
        )
    return crud.get_spare_change_summary(db, current_user.id, period_start, period_end)
