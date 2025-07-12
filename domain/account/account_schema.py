# File: domain/account/account_schema.py
from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, constr, validator, root_validator
from fastapi import Path, Query


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼 ─ 날짜 계산 · 공통 Config
# ─────────────────────────────────────────────────────────────────────────────
_DATE_FMT = "%Y%m%d"


def _today() -> str:
    """UTC 기준 오늘(YYYYMMDD)."""
    return datetime.utcnow().strftime(_DATE_FMT)


def _recent_30_start() -> str:
    """UTC 기준 최근 30일 시작일(YYYYMMDD)."""
    return (datetime.utcnow() - timedelta(days=29)).strftime(_DATE_FMT)


class _OrmModel(BaseModel):
    """ORM ↔︎ Pydantic 변환 공통 설정."""
    class Config:
        orm_mode = True # ORM 모델을 Pydantic 모델로 변환할 때 사용


# ─────────────────────────────────────────────────────────────────────────────
# 1. 요청 스키마(Request Schemas)
# ─────────────────────────────────────────────────────────────────────────────
class RegisterParams(BaseModel):
    """
    공통: 금융기관 코드(4자리).
    """
    institution_code: constr(regex=r"^\d{4}$") = Field(
        ...,
        description="기관 코드 (4자리 숫자)",
    )

    @validator("*")
    def _not_empty(cls, v: str) -> str:  
        if not v.strip():
            raise ValueError("빈 값은 허용되지 않습니다.")
        return v


# ───────────────────────────────────────────────────────────────────────────
class InternetBankingCreate(RegisterParams):
    """
    인터넷뱅킹 등록 요청 스키마
    """
    banking_id       : constr(min_length=4, max_length=32) = Field(..., description="인터넷뱅킹 아이디 (4~32자)")
    banking_password : constr(min_length=8, max_length=64) = Field(..., description="인터넷뱅킹 비밀번호 (8~64자)")


# ───────────────────────────────────────────────────────────────────────────
class AccountCreate(RegisterParams):
    """
    계좌 등록 요청 스키마
    """
    account_number   : constr(regex=r"^\d{10,20}$")       = Field(..., description="계좌번호 (10~20자리 숫자)")
    account_password : constr(min_length=4, max_length=6) = Field(..., description="계좌 비밀번호 (4~6자리 숫자)")
    
    @validator("account_password")
    def account_pw_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("계좌 비밀번호는 숫자만 허용됩니다.")
        return value


# ───────────────────────────────────────────────────────────────────────────
class AccountDetailParams(BaseModel):
    
    """단일 계좌 + 거래내역 조회(Path + Query) 요청 스키마"""
    
    account_number : constr(regex=r"^\d{10,20}$") = Path(..., description="조회할 계좌번호 (10~20자리 숫자)")
    start: str = Query(
        default_factory=_recent_30_start,
        regex=r"^\d{8}$",
        description="조회 시작일(YYYYMMDD), 기본: 최근 30일",
    )
    end: str = Query(
        default_factory=_today,
        regex=r"^\d{8}$",
        description="조회 종료일(YYYYMMDD), 기본: 오늘",
    )

    @root_validator
    def check_date_range(cls, values):
        start, end = values.get("start"), values.get("end")
        if start and end and start > end:
            raise ValueError("start 날짜는 end 날짜보다 이전이어야 합니다.")
        return values


# ─────────────────────────────────────────────────────────────────────────────
# 2. 응답 스키마(ResponseOut Schemas)
# ─────────────────────────────────────────────────────────────────────────────
class InternetBankingOut(_OrmModel):
    """
    인터넷뱅킹 정보.
    """
    institution_code     : str = Field(..., description="기관 코드")
    banking_id           : str = Field(..., description="인터넷뱅킹 아이디")
    banking_password_enc : str = Field(..., description="암호화된 인터넷뱅킹 비밀번호")


# ───────────────────────────────────────────────────────────────────────────
class AccountOut(_OrmModel):
    """
    계좌 정보
    """
    institution_code     : str = Field(..., description="금융기관 코드")
    account_number       : str = Field(..., description="계좌번호")
    account_password_enc : str = Field(..., description="암호화된 계좌 비밀번호")


# ───────────────────────────────────────────────────────────────────────────
class TransactionOut(BaseModel):
    """
    거래내역
    """
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
    """
    단일 계좌 + 거래내역
    """
    account      : AccountOut           = Field(..., description="계좌 정보")
    transactions : List[TransactionOut] = Field(..., description="거래내역 리스트")
