# File: domain/user/user_router.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.config import Config

from database import get_db
from domain.user.user_crud import create_user, get_existing_user, get_username, pwd_context
from domain.user.user_schema import UserRegister, Token, LoginCheckOut


# ────────────────────────────────────────────────────────────────────────────
# JWT 환경 변수 로드
config                           = Config(".env")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))  
SECRET_KEY: str                  = config("SECRET_KEY")                        
ALGORITHM: str                   = config("ALGORITHM")                        

# OAuth2 스킴 설정 (헤더 기반 인증)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl   = "/api/user/login",
    auto_error = False,
)

router = APIRouter(
    prefix = "/api/user",      
    tags   = ["로그인 회원가입"],   
)


# ────────────────────────────────────────────────────────────────────────────
@router.post(
    "/create",
    status_code = status.HTTP_204_NO_CONTENT,
    description = "사용자 회원가입",
)
def user_create(
    user_data : UserRegister,
    db        : Session = Depends(get_db),
):
    """
    신규 사용자 등록 (중복 검사 후 204 반환)
    """
    if get_existing_user(db, user_data):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail      = "이미 존재하는 사용자입니다.",
        )

    create_user(db, user_data)


# ────────────────────────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model = Token,
    description    = "사용자 로그인 (토큰+쿠키 동시 반환)",
)
def login_for_access_token(
    form_data : OAuth2PasswordRequestForm = Depends(),
    db        : Session                   = Depends(get_db),
):
    """
    인증 후 JWT 발급 및 HttpOnly 쿠키 설정
    """
    # 1) 사용자 조회 및 비밀번호 검증
    user = get_username(db, form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "아이디 또는 비밀번호가 올바르지 않습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )
    
    # 2) 토큰 생성
    expire       = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload      = {"sub": user.username, "exp": expire}
    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # 3) 응답 및 쿠키 설정
    response = JSONResponse(content={
        "access_token": access_token,
        "token_type"  : "bearer",
        "username"    : user.username,
    })
    response.set_cookie(
        key      = "access_token",
        value    = access_token,
        httponly = True,
        secure   = True,
        samesite = "lax",
        max_age  = ACCESS_TOKEN_EXPIRE_MINUTES * 60, # 초 단위환산을 위한 * 60
        path     = "/",
    )
    return response


# ────────────────────────────────────────────────────────────────────────────
def get_current_user(
    token       : str        = Depends(oauth2_scheme),
    cookie_token: str | None = Cookie(None, alias="access_token"),
    db          : Session    = Depends(get_db),
):
    """
    헤더 또는 쿠키에서 JWT 추출·검증 후 사용자 반환
    """
    # 1) 토큰 확보
    token = token or cookie_token
    if not token:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "자격 증명을 확인할 수 없습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )
    
    # 2) 토큰 디코드 및 사용자명 추출
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub") or ""
    except JWTError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "자격 증명을 확인할 수 없습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )
    
    # 3) 사용자 조회
    user = get_username(db, username)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "자격 증명을 확인할 수 없습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )
    return user


# ────────────────────────────────────────────────────────────────────────────
@router.get(
    "/check_login",
    response_model = LoginCheckOut,
    status_code    = status.HTTP_200_OK,
    summary        = "로그인 상태 확인",
    description    = "JWT를 검사해 로그인 여부를 반환합니다.",
)
def login_check(
    current_user = Depends(get_current_user),
):
    """
    로그인 검증 후 {username, is_logged_in: True} 반환
    """
    return {
        "username"     : current_user.username,
        "is_logged_in" : True,
    }
