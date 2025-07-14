# File: domain/account/account_schema.py
from __future__ import annotations

import logging

from typing   import Optional, List, Annotated
from datetime import datetime, timedelta

from starlette.config import Config
from fastapi          import Path, Query
from pydantic         import (
    BaseModel, Field,
    field_validator, model_validator,
    ConfigDict, FieldValidationInfo
)


# ────────────────────────── 설정값 & 로깅 ──────────────────────────
config     = Config('.env')
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


# ────────────────────────── 날짜 헬퍼 & 공통 Config ──────────────────────────
_DATE_FMT = "%Y%m%d"


def _today() -> str:
    """UTC 기준 오늘(YYYYMMDD)."""

    today = datetime.utcnow().strftime(_DATE_FMT)
    _debug("DATE_HELPER", f"today={today}")
    return today


def _recent_30_start() -> str:
    """UTC 기준 최근 30일 시작일(YYYYMMDD)."""

    start = (datetime.utcnow() - timedelta(days=29)).strftime(_DATE_FMT)
    _debug("DATE_HELPER", f"recent_30_start={start}")
    return start


class _OrmModel(BaseModel):
    """ORM ↔︎ Pydantic 변환 공통 설정."""

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. 요청 스키마(Request Schemas)
# ─────────────────────────────────────────────────────────────────────────────
class RegisterParams(BaseModel):
    """공통: 금융기관 코드(4자리)."""

    institution_code: Annotated[
        str,
        Field(
            ...,
            pattern=r"^\d{4}$",
            description="기관 코드 (4자리 숫자)"
        )
    ]

    @field_validator("*")
    def _not_empty(cls, v: str, info: FieldValidationInfo) -> str:
        field_name = info.field_name
        if not v.strip():
            _debug("VALIDATOR", f"{field_name} 빈 값 검증 실패")
            raise ValueError("빈 값은 허용되지 않습니다.")
        _debug("VALIDATOR", f"{field_name} 검증 통과: '{v}'")
        return v


# ───────────────────────────────────────────────────────────────────────────
class InternetBankingCreate(RegisterParams):
    """인터넷뱅킹 등록 요청 스키마"""

    banking_id: Annotated[
        str,
        Field(
            ...,
            min_length=4,
            max_length=32,
            description="인터넷뱅킹 아이디 (4~32자)"
        )
    ]
    banking_password: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            max_length=64,
            description="인터넷뱅킹 비밀번호 (8~64자)"
        )
    ]


# ───────────────────────────────────────────────────────────────────────────
class AccountCreate(RegisterParams):
    """계좌 등록 요청 스키마"""

    account_number: Annotated[
        str,
        Field(
            ...,
            pattern=r"^\d{10,20}$",
            description="계좌번호 (10~20자리 숫자)"
        )
    ]
    account_password: Annotated[
        str,
        Field(
            ...,
            min_length=4,
            max_length=6,
            description="계좌 비밀번호 (4~6자리 숫자)"
        )
    ]

    @field_validator("account_password")
    def account_pw_numeric(
        cls, v: str, info: FieldValidationInfo
    ) -> str:
        _debug("VALIDATOR", f"account_password 검증: '{v}'")
        if not v.isdigit():
            _debug("VALIDATOR", "account_password 숫자 검증 실패")
            raise ValueError("계좌 비밀번호는 숫자만 허용됩니다.")
        _debug("VALIDATOR", "account_password 검증 통과")
        return v



# ───────────────────────────────────────────────────────────────────────────
class AccountDetailParams(BaseModel):
    """단일 계좌 + 거래내역 조회(Path + Query) 요청 스키마"""

    account_number: Annotated[
        str,
        Field(
            ...,
            pattern=r"^\d{10,20}$",
            description="조회할 계좌번호 (10~20자리 숫자)"
        )
    ]
    start: Annotated[
        str,
        Query(
            default_factory=_recent_30_start,
            pattern=r"^\d{8}$",
            description="조회 시작일(YYYYMMDD), 기본: 최근 30일"
        )
    ]
    end: Annotated[
        str,
        Query(
            default_factory=_today,
            pattern=r"^\d{8}$",
            description="조회 종료일(YYYYMMDD), 기본: 오늘"
        )
    ]

    model_config = ConfigDict() # ORM 변환과 향후 확장성을 위해 명시

    @model_validator(mode="after")
    def check_date_range(self) -> AccountDetailParams:
        if self.start > self.end:
            _debug(
                "VALIDATOR",
                f"start({self.start}) > end({self.end}) 검증 실패"
            )
            raise ValueError("start 날짜는 end 날짜보다 이전이어야 합니다.")
        _debug(
            "VALIDATOR",
            f"date range 검증 통과: {self.start} <= {self.end}"
        )
        return self


# ─────────────────────────────────────────────────────────────────────────────
# 2. 응답 스키마(ResponseOut Schemas)
# ─────────────────────────────────────────────────────────────────────────────
class InternetBankingOut(_OrmModel):
    """인터넷뱅킹 정보."""

    institution_code     : str = Field(..., description="기관 코드")
    banking_id           : str = Field(..., description="인터넷뱅킹 아이디")
    banking_password_enc : str = Field(..., description="암호화된 인터넷뱅킹 비밀번호")


# ───────────────────────────────────────────────────────────────────────────
class AccountOut(_OrmModel):
    """계좌 정보"""

    institution_code     : str = Field(..., description="금융기관 코드")
    account_number       : str = Field(..., description="계좌번호")
    account_password_enc : str = Field(..., description="암호화된 계좌 비밀번호")


# ───────────────────────────────────────────────────────────────────────────
class TransactionOut(BaseModel):
    """거래내역"""

    resAccountTrDate    : str           = Field(...,  description="거래일자(YYYYMMDD)")
    resAccountTrTime    : str           = Field(...,  description="거래시간(HHMMSS)")
    resAccountOut       : str           = Field(...,  description="출금액")
    resAccountIn        : str           = Field(...,  description="입금액")
    resAccountDesc1     : Optional[str] = Field(None, description="거래내역 설명1")
    resAccountDesc2     : Optional[str] = Field(None, description="거래내역 설명2")
    resAccountDesc3     : Optional[str] = Field(None, description="거래내역 설명3")
    resAccountDesc4     : Optional[str] = Field(None, description="거래내역 설명4")
    resAfterTranBalance : str           = Field(...,  description="거래 후 잔액")


# ───────────────────────────────────────────────────────────────────────────
class AccountDetailOut(BaseModel):
    """단일 계좌 + 거래내역"""

    account      : AccountOut           = Field(..., description="계좌 정보")
    transactions : List[TransactionOut] = Field(..., description="거래내역 리스트")
