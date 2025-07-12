# File: domain/spare_change/spare_change_crud.py
"""
잔돈(라운드-업) 관련 CRUD / 비즈니스 로직
"""
from datetime        import datetime
from typing          import List, Optional
from decimal         import Decimal
from math            import ceil

from sqlalchemy      import func, and_
from sqlalchemy.exc  import IntegrityError
from sqlalchemy.orm  import Session

from models          import RoundUpConfig, SpareChange
from .               import spare_change_schema as schema


# ───────────────────────────────────────────────────────────────
# 기본 라운드-업 단위 (시스템 설정이 없을 때 사용)
# ───────────────────────────────────────────────────────────────
DEFAULT_UNIT = 100


def _get_round_unit(db: Session, user_id: int) -> int:
    """
    사용자별 최신 단위 설정 또는 시스템 기본 단위 반환
    """
    cfg = (
        db.query(RoundUpConfig)
        .filter(RoundUpConfig.user_id == user_id)
        .order_by(RoundUpConfig.created_at.desc())
        .first()
    )
    return cfg.unit if cfg else DEFAULT_UNIT


# ───────────────────────────────────────────────────────────────
def create_round_up_config(
    db      : Session,
    payload : schema.RoundUpConfigCreate
) -> schema.RoundUpConfig:
    """
    라운드-업 단위 설정 생성
    - 동일 user_id + unit 중복 방지
    """
    instance = RoundUpConfig(
        user_id = payload.user_id,
        unit    = payload.unit
    )
    db.add(instance)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Duplicated round-up config.")
    db.refresh(instance)
    return schema.RoundUpConfig.from_orm(instance)


def get_round_up_configs(
    db      : Session,
    user_id : Optional[int] = None
) -> List[schema.RoundUpConfig]:
    """
    라운드-업 단위 설정 조회
    - user_id=None → 시스템 공용 설정
    """
    q = db.query(RoundUpConfig)
    if user_id is None:
        q = q.filter(RoundUpConfig.user_id.is_(None))
    else:
        q = q.filter(RoundUpConfig.user_id == user_id)
    return [schema.RoundUpConfig.from_orm(cfg) for cfg in q.all()]


# ───────────────────────────────────────────────────────────────
# SpareChange CRUD
# ───────────────────────────────────────────────────────────────
def create_spare_change(
    db: Session,
    payload: schema.SpareChangeCreate
) -> schema.SpareChangeOut:
    """
    거래별 잔돈 생성
    - 요청에 포함된 amount 로 round_up 계산 후 저장
    - (user_id, tx_id) 중복 시 IntegrityError 발생
    """
    # 1) 단위 조회
    unit   = _get_round_unit(db, payload.user_id)
    # 2) 잔돈 계산: ceil(amount / unit) * unit - amount
    amount = Decimal(payload.amount)
    raw    = Decimal(ceil(amount / unit)) * unit - amount
    # 3) 소수점 둘째 자리까지 반올림
    round_up = raw.quantize(Decimal("0.01"))

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
    q = db.query(SpareChange).filter(SpareChange.user_id == user_id)
    return [schema.SpareChangeOut.from_orm(sc) for sc in q.all()]


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
