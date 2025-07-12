# File: domain/spare_change/spare_change_crud.py
"""
잔돈(라운드-업) 관련 CRUD / 비즈니스 로직 (유저 테이블에 round_up_unit 컬럼 통합 버전)
"""

from datetime        import datetime
from decimal         import Decimal
from math            import ceil
from typing          import List, Optional

from sqlalchemy      import func, and_
from sqlalchemy.exc  import IntegrityError
from sqlalchemy.orm  import Session

from models          import User, SpareChange            # RoundUpConfig 제거
from .               import spare_change_schema as schema


# ───────────────────────────────────────────────────────────────
# 시스템 기본 라운드-업 단위 (유저 컬럼이 NULL·0 인 경우)
# ───────────────────────────────────────────────────────────────
DEFAULT_UNIT = 100


def _get_round_unit(db: Session, user_id: int) -> int:
    """
    사용자 round_up_unit 컬럼을 가져오고,
    없으면 시스템 기본값(DEFAULT_UNIT) 반환
    """
    unit = (
        db.query(User.round_up_unit)
          .filter(User.id == user_id)
          .scalar()
    )
    # None, 0, 음수 등 방어
    return unit if unit and unit > 0 else DEFAULT_UNIT


# ───────────────────────────────────────────────────────────────
# round_up_unit (설정) 업데이트
# ───────────────────────────────────────────────────────────────
def update_round_up_unit(
    db: Session,
    user_id: int,
    unit: int
) -> int:
    """
    사용자 라운드-업 단위 변경 (한 유저 = 하나의 단위)
    반환 값: 최종 저장된 단위
    """
    if unit <= 0:
        raise ValueError("unit must be a positive integer.")

    user = db.query(User).get(user_id)
    if user is None:
        raise ValueError("User not found.")

    user.round_up_unit = unit
    db.commit()
    db.refresh(user)
    return user.round_up_unit


# ───────────────────────────────────────────────────────────────
# SpareChange CRUD
# ───────────────────────────────────────────────────────────────
def create_spare_change(
    db: Session,
    payload: schema.SpareChangeCreate
) -> schema.SpareChangeOut:
    """
    거래별 잔돈 생성
    - amount 로 round_up 계산 후 저장
    - (user_id, tx_id) 중복 시 IntegrityError
    """
    # 1) 단위 조회
    unit   = _get_round_unit(db, payload.user_id)

    # 2) 라운드-업 계산: ceil(amount / unit) * unit − amount
    amount    = Decimal(payload.amount)
    raw_delta = Decimal(ceil(amount / unit)) * unit - amount
    round_up  = raw_delta.quantize(Decimal("0.01"))   # 소수점 둘째 자리 고정

    # 3) DB 저장
    instance = SpareChange(
        user_id  = payload.user_id,
        tx_id    = payload.tx_id,
        round_up = round_up
    )
    db.add(instance)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Duplicated spare_change entry.")
    db.refresh(instance)
    return schema.SpareChangeOut.from_orm(instance)


def get_spare_changes_by_user(
    db: Session,
    user_id: int
) -> List[schema.SpareChangeOut]:
    """
    특정 사용자의 모든 잔돈 내역 반환
    """
    rows = (
        db.query(SpareChange)
          .filter(SpareChange.user_id == user_id)
          .order_by(SpareChange.created_at.desc())
          .all()
    )
    return [schema.SpareChangeOut.from_orm(r) for r in rows]


def get_spare_change_summary(
    db: Session,
    user_id: int,
    period_start: datetime,
    period_end:   datetime
) -> schema.SpareChangeSummary:
    """
    기간별 잔돈 합계 계산
    """
    total: Optional[Decimal] = (
        db.query(func.coalesce(func.sum(SpareChange.round_up), 0))
          .filter(
              and_(
                  SpareChange.user_id    == user_id,
                  SpareChange.created_at >= period_start,
                  SpareChange.created_at <  period_end
              )
          )
          .scalar()
    )
    return schema.SpareChangeSummary(
        total_round_up = total,
        period_start   = period_start,
        period_end     = period_end
    )
