# File: domain/spare_change/spare_change_router.py
"""
잔돈(라운드-업) 라우터 – **User 테이블에 round_up_unit 컬럼 통합 버전**

※ 변경 사항
1. RoundUpConfig 엔드포인트 제거
2. 사용자가 직접 단위를 조회·변경하는 **/round-up-unit** 엔드포인트 추가
3. Spare-change 로직은 current_user.round_up_unit 을 참조
"""

from datetime              import datetime
from typing                import List

from fastapi               import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm        import Session

from database              import get_db
from models                import User
from domain.user.user_router import get_current_user
from .                     import spare_change_schema as schema
from .                     import spare_change_crud   as crud

router = APIRouter(
    prefix="/api/spare-change",
    tags=["잔돈(라운드-업)"],
)

# ───────────────────────────────────────────────────────────────
# 1) round_up_unit 조회/수정
# ───────────────────────────────────────────────────────────────
@router.get(
    "/round-up-unit",
    response_model=schema.RoundUpUnitOut,
    summary="현재 라운드-업 단위 조회"
)
def get_round_up_unit(
    current_user: User = Depends(get_current_user)
):
    """로그인 사용자의 round_up_unit 값을 반환"""
    return {"round_up_unit": current_user.round_up_unit}


@router.patch(
    "/round-up-unit",
    response_model=schema.RoundUpUnitOut,
    status_code=status.HTTP_200_OK,
    summary="라운드-업 단위 변경"
)
def update_round_up_unit(
    unit: int = Body(..., embed=True, gt=0, description="새 라운드-업 단위(양의 정수)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 round_up_unit 컬럼을 업데이트"""
    try:
        new_unit = crud.update_round_up_unit(db, current_user.id, unit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"round_up_unit": new_unit}

# ───────────────────────────────────────────────────────────────
# 2) Spare-change 엔드포인트
# ───────────────────────────────────────────────────────────────
@router.post(
    "",
    response_model=schema.SpareChangeOut,
    status_code=status.HTTP_201_CREATED,
    summary="거래 잔돈 생성"
)
def create_spare_change(
    payload: schema.SpareChangeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """amount·tx_id 입력 → 서버가 round_up 계산 후 저장"""
    payload = payload.copy(update={"user_id": current_user.id})
    return crud.create_spare_change(db, payload)


@router.get(
    "",
    response_model=List[schema.SpareChangeOut],
    summary="사용자 잔돈 목록"
)
def list_spare_changes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """로그인 사용자의 잔돈 내역 반환"""
    return crud.get_spare_changes_by_user(db, current_user.id)


@router.get(
    "/summary",
    response_model=schema.SpareChangeSummary,
    summary="기간별 잔돈 합계"
)
def spare_change_summary(
    period_start: datetime,
    period_end:   datetime,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """period_start ≤ created_at < period_end 범위 합계"""
    if period_end <= period_start:
        raise HTTPException(400, "period_end must be after period_start.")
    return crud.get_spare_change_summary(db, current_user.id, period_start, period_end)
