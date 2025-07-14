# File: domain/spare_change/spare_change_crud.py
import logging

from datetime import datetime
from decimal  import Decimal
from math     import ceil
from typing   import List, Optional

from sqlalchemy       import func, and_
from sqlalchemy.exc   import IntegrityError
from sqlalchemy.orm   import Session
from starlette.config import Config

from models import User, SpareChange           
from .      import spare_change_schema as schema


# ────────────────────────── 설정값 & 로깅 ──────────────────────────
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


# ───────────────────────────────────────────────────────────────
DEFAULT_UNIT = 0 # 기본 라운드-업 단위 


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
    result = unit if unit and unit > 0 else DEFAULT_UNIT # None, 0, 음수 등 방어
    _debug("ROUND_UNIT", f"user_id={user_id} -> unit={result}")
    return result


# ───────────────────────────────────────────────────────────────
def update_round_up_unit(
    db     : Session,
    user_id: int,
    unit   : int
) -> int:
    """
    사용자 라운드-업 단위 변경 (한 유저 = 하나의 단위)
    반환 값: 최종 저장된 단위
    """
    _debug("ROUND_UNIT", f"update request user_id={user_id} unit={unit}")
    if unit <= 0:
        _debug("ROUND_UNIT", f"invalid unit {unit}")
        raise ValueError("unit must be a positive integer.")

    user = db.query(User).get(user_id)
    if user is None:
        _debug("ROUND_UNIT", f"user not found user_id={user_id}")
        raise ValueError("User not found.")

    user.round_up_unit = unit
    db.commit()
    db.refresh(user)
    _debug("ROUND_UNIT", f"update success user_id={user_id} unit={user.round_up_unit}")
    return user.round_up_unit


# ───────────────────────────────────────────────────────────────
def create_spare_change(
    db     : Session,
    payload: schema.SpareChangeCreate
) -> schema.SpareChangeOut:
    """
    거래별 잔돈 생성
    - amount 로 round_up 계산 후 저장
    - (user_id, tx_id) 중복 시 IntegrityError
    """
    # 1) 단위 조회
    unit = _get_round_unit(db, payload.user_id)
    _debug(
        "SPARE_CHANGE",
        f"create request user_id={payload.user_id} "
        f"tx_id={payload.tx_id} amount={payload.amount} unit={unit}"
    )

    # 2) 라운드-업 계산: ceil(amount / unit) * unit − amount
    amount    = Decimal(payload.amount)
    raw_delta = Decimal(ceil(amount / unit)) * unit - amount
    round_up  = raw_delta.quantize(Decimal("0.01")) # 소수점 2자리로 반올림
    _debug("SPARE_CHANGE", f"calculated round_up={round_up}")

    # 3) DB 저장
    instance = SpareChange(
        user_id  = payload.user_id,
        tx_id    = payload.tx_id,
        round_up = round_up
    )
    db.add(instance)
    try:
        db.commit()
        _debug(
            "SPARE_CHANGE",
            f"saved user_id={payload.user_id} tx_id={payload.tx_id} round_up={round_up}"
        )
    except IntegrityError:
        db.rollback()
        _debug(
            "SPARE_CHANGE",
            f"duplicate entry user_id={payload.user_id} tx_id={payload.tx_id}"
        )
        raise ValueError("Duplicated spare_change entry.")
    db.refresh(instance)
    return schema.SpareChangeOut.from_orm(instance)


def get_spare_changes_by_user(
    db     : Session,
    user_id: int
) -> List[schema.SpareChangeOut]:
    """특정 사용자의 모든 잔돈 내역 반환"""

    rows = (
        db.query(SpareChange)
        .filter(SpareChange.user_id == user_id)
        .order_by(SpareChange.created_at.desc())
        .all()
    )
    _debug("SPARE_CHANGE", f"list user_id={user_id} count={len(rows)}")
    return [schema.SpareChangeOut.from_orm(r) for r in rows]


def get_spare_change_summary(
    db          : Session,
    user_id     : int,
    period_start: datetime,
    period_end  : datetime
) -> schema.SpareChangeSummary:
    """기간별 잔돈 합계 계산"""

    _debug(
        "SPARE_CHANGE",
        f"summary request user_id={user_id} "
        f"start={period_start.isoformat()} end={period_end.isoformat()}"
    )
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
    _debug("SPARE_CHANGE", f"summary result total={total}")
    return schema.SpareChangeSummary(
        total_round_up = total,
        period_start   = period_start,
        period_end     = period_end
    )
