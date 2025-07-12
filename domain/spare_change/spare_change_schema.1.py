# File: domain/spare_change/spare_change_schema.py
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


# ───────────────────────────────────────────────────────────────
class TimestampMixin(BaseModel):
    """
    created_at 공통 필드
    """
    created_at: datetime

    class Config:
        orm_mode = True


# ───────────────────────────────────────────────────────────────
class RoundUpConfigBase(BaseModel):
    unit: int  


class RoundUpConfigCreate(RoundUpConfigBase):
    user_id: Optional[int] = None


class RoundUpConfig(RoundUpConfigBase, TimestampMixin):
    id      : int
    user_id : Optional[int] = None


# ───────────────────────────────────────────────────────────────
class SpareChangeCreate(BaseModel):
    """
    거래 잔돈 생성 요청 스키마
    """
    tx_id  : str
    amount : Decimal

    class Config:
        orm_mode = True


class SpareChangeOut(BaseModel):
    """
    거래 잔돈 조회 응답 스키마
    """
    user_id    : int
    tx_id      : str
    round_up   : Decimal
    created_at : datetime

    class Config:
        orm_mode = True


# ───────────────────────────────────────────────────────────────
class SpareChangeSummary(BaseModel):
    """
    기간별 잔돈 합계 DTO
    """
    total_round_up : Decimal
    period_start   : datetime
    period_end     : datetime

    class Config:
        orm_mode = True
