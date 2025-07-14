# File: domain/spare_change/spare_change_schema.py
from datetime import datetime
from decimal  import Decimal
from typing   import Optional, Annotated, Self

from pydantic import (
    BaseModel, Field,
    ConfigDict, field_validator,
    model_validator, FieldValidationInfo,
)

# ───────────────────────────────────────────────────────────────
class TimestampMixin(BaseModel):
    """공통 created_at 필드"""

    created_at: Annotated[
        datetime,
        Field(..., description="생성 일시")
    ]

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────────────────────
class RoundUpUnitOut(BaseModel):
    """사용자의 현재 라운드-업 단위 응답 DTO"""

    round_up_unit: Annotated[
        int,
        Field(..., description="현재 라운드-업 단위 (원 단위)")
    ]

    model_config = ConfigDict(from_attributes=True)


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
    tx_id: Annotated[
        str,
        Field(..., description="거래 고유 ID")
    ]
    amount: Annotated[
        Decimal,
        Field(..., description="원 단위 거래 금액")
    ]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tx_id")
    def validate_tx_id_not_empty(cls, v: str, info: FieldValidationInfo) -> str:
        if not v.strip():
            raise ValueError("tx_id는 빈 값일 수 없습니다.")
        return v

    @field_validator("amount")
    def validate_amount_non_negative(cls, v: Decimal, info: FieldValidationInfo) -> Decimal:
        if v < 0:
            raise ValueError("amount는 음수일 수 없습니다.")
        return v

# ───────────────────────────────────────────────────────────────
class SpareChangeOut(BaseModel):
    """거래 잔돈 조회 응답"""

    user_id: Annotated[
        int,
        Field(..., description="사용자 ID")
    ]
    tx_id: Annotated[
        str,
        Field(..., description="거래 고유 ID")
    ]
    round_up: Annotated[
        Decimal,
        Field(..., description="라운드-업된 금액")
    ]
    created_at: Annotated[
        datetime,
        Field(..., description="생성 일시")
    ]

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────────────────────
class SpareChangeSummary(BaseModel):
    """기간별 잔돈 합계 응답 DTO"""

    total_round_up: Annotated[
        Decimal,
        Field(..., description="기간별 잔돈 합계")
    ]
    period_start: Annotated[
        datetime,
        Field(..., description="기간 시작일시")
    ]
    period_end: Annotated[
        datetime,
        Field(..., description="기간 종료일시")
    ]

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def check_period_order(self) -> Self:
        if self.period_start > self.period_end:
            raise ValueError("period_start는 period_end 이전이어야 합니다.")
        return self


# ───────────────────────────────────────────────────────────────
class TransactionIn(BaseModel):
    """
    외부(API·크롤러 등)에서 받아온 “원시 거래” DTO
    - DB에 저장되지 않으므로 created_at 없음
    """
    tx_id: Annotated[
        str,
        Field(..., description="거래 고유 ID")
    ]
    account_id: Annotated[
        int,
        Field(..., description="계좌 ID")
    ]
    amount: Annotated[
        Decimal,
        Field(..., description="거래 금액")
    ]
    tx_type: Annotated[
        str,
        Field(..., description="거래 유형 ('withdraw' / 'deposit')")
    ]
    memo: Annotated[
        Optional[str],
        Field(None, description="메모")
    ]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tx_id")
    def validate_tx_id_not_empty(cls, v: str, info: FieldValidationInfo) -> str:
        if not v.strip():
            raise ValueError("tx_id는 빈 값일 수 없습니다.")
        return v

    @field_validator("amount")
    def validate_amount_non_negative(cls, v: Decimal, info: FieldValidationInfo) -> Decimal:
        if v < 0:
            raise ValueError("amount는 음수일 수 없습니다.")
        return v

    @field_validator("tx_type")
    def validate_tx_type(cls, v: str, info: FieldValidationInfo) -> str:
        allowed = {"withdraw", "deposit"}
        if v not in allowed:
            raise ValueError(f"tx_type은 {allowed} 중 하나여야 합니다.")
        return v
