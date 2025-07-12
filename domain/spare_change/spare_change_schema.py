# File: domain/spare_change/spare_change_schema.py
"""
잔돈(라운드-업) 전용 Pydantic 스키마
- round_up_unit 컬럼(User 테이블) 사용 버전
"""

from datetime  import datetime
from decimal    import Decimal
from pydantic   import BaseModel


# ───────────────────────────────────────────────────────────────
class TimestampMixin(BaseModel):
    """공통 created_at 필드"""
    created_at: datetime

    class Config:
        orm_mode = True


# ───────────────────────────────────────────────────────────────
# round_up_unit (조회/응답용)
# ───────────────────────────────────────────────────────────────
class RoundUpUnitOut(BaseModel):
    """
    사용자의 현재 라운드-업 단위 응답 DTO
    """
    round_up_unit: int

    class Config:
        orm_mode = True


# ───────────────────────────────────────────────────────────────
# SpareChange
# ───────────────────────────────────────────────────────────────
class SpareChangeCreate(BaseModel):
    """
    거래 잔돈 생성 요청
    ───────────────────────────────────────
    필드 | 타입     | 설명
    -----|----------|----------------------------
    tx_id| str      | 거래 고유 ID
    amount| Decimal | 원 단위 거래 금액
    """
    tx_id:  str
    amount: Decimal

    class Config:
        orm_mode = True


class SpareChangeOut(BaseModel):
    """
    거래 잔돈 조회 응답
    """
    user_id:   int
    tx_id:     int
    round_up:  Decimal
    created_at: datetime

    class Config:
        orm_mode = True


# ───────────────────────────────────────────────────────────────
# Aggregation
# ───────────────────────────────────────────────────────────────
class SpareChangeSummary(BaseModel):
    """
    기간별 잔돈 합계 응답 DTO
    """
    total_round_up: Decimal
    period_start:   datetime
    period_end:     datetime

    class Config:
        orm_mode = True
