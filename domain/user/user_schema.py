# File: domain/user/user_schema.py
from __future__ import annotations

import logging

from typing import Annotated

from starlette.config import Config
from pydantic         import (
    BaseModel, EmailStr, Field,
    ConfigDict, field_validator,
    model_validator, FieldValidationInfo,
)

# ────────────────────────── 설정값 ────────────────────────────
config     = Config(".env")
DEBUG_MODE = config("DEBUG_MODE", default="false").lower() == "true"
_log_level = logging.DEBUG if DEBUG_MODE else logging.WARNING

logging.basicConfig(
    level  = _log_level,
    format = "[%(levelname)s][%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ────────────────────────── Debug 헬퍼 ─────────────────────────
def _debug(category: str, message: str) -> None:
    """일관된 형식의 디버그 로그 기록"""

    if DEBUG_MODE:
        logger.debug(f"[{category}] {message}")


# ────────────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    """사용자 등록 요청 스키마"""
    
    username: Annotated[
        str,
        Field(
            ...,
            min_length=3,
            max_length=30,
            pattern=r"^[A-Za-z0-9_]+$",
            description="사용자명 (3~30자, 영문·숫자·밑줄)"
        )
    ]
    password1: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            max_length=128,
            description="비밀번호 (8~128자, 영문 대소문자·숫자·특수문자 포함)"
        )
    ]
    password2: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            max_length=128,
            description="비밀번호 확인 (password1과 동일)"
        )
    ]
    email: Annotated[
        EmailStr,
        Field(..., description="이메일 주소")
    ]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("username", "password1", "password2", "email")
    def not_empty(cls, v: str, info: FieldValidationInfo) -> str:
        """각 필드가 빈 값이 아닌지 검사"""

        field_name = info.field_name
        if not v or not v.strip():
            _debug("VALIDATOR", f"{field_name} 빈 값 검증 실패")
            raise ValueError("빈 값은 허용되지 않습니다.")
        _debug("VALIDATOR", f"{field_name} 검증 통과: '{v}'")
        return v

    @field_validator("password1")
    def password_complexity(cls, v: str, info: FieldValidationInfo) -> str:
        """비밀번호에 소문자, 대문자, 숫자, 특수문자가 모두 포함되었는지 검사"""

        has_lower = any(c.islower() for c in v)
        has_upper = any(c.isupper() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_symbol = any(not c.isalnum() for c in v)

        if not (has_lower and has_upper and has_digit and has_symbol):
            _debug("VALIDATOR", "password1 복잡도 검증 실패")
            raise ValueError(
                "비밀번호는 소문자, 대문자, 숫자, 특수문자를 모두 포함해야 합니다."
            )
        _debug("VALIDATOR", "password1 복잡도 검증 통과")
        return v

    @model_validator(mode="after")
    def passwords_match(cls, m: UserRegister) -> UserRegister:
        """password1, password2 일치 여부 검사"""

        if m.password1 != m.password2:
            _debug(
                "VALIDATOR",
                f"password mismatch: '{m.password1}' != '{m.password2}'"
            )
            raise ValueError("비밀번호가 일치하지 않습니다.")
        _debug("VALIDATOR", "passwords match")
        return m


# ────────────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    
    access_token: Annotated[
        str,
        Field(..., description="액세스 토큰")
    ]
    token_type: Annotated[
        str,
        Field(..., description="토큰 타입 (Bearer)")
    ]
    username: Annotated[
        str,
        Field(..., description="사용자명")
    ]


# ────────────────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    """사용자 정보 응답 스키마"""

    id: Annotated[
        int,
        Field(..., description="사용자 ID")
    ]
    username: Annotated[
        str,
        Field(..., description="사용자명")
    ]
    email: Annotated[
        str,
        Field(..., description="이메일 주소")
    ]

    model_config = ConfigDict(from_attributes=True)


# ────────────────────────────────────────────────────────────────────────────
class LoginCheckOut(BaseModel):
    """로그인 상태 응답 스키마"""
    
    username: Annotated[
        str,
        Field(..., description="사용자명")
    ]
    is_logged_in: Annotated[
        bool,
        Field(default=True, description="로그인 여부")
    ]