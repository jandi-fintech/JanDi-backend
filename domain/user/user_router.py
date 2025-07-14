# File: domain/user/user_router.py
import logging

from datetime import datetime, timedelta
from jose     import JWTError, jwt

from fastapi           import APIRouter, Depends, HTTPException, status, Cookie
from fastapi.responses import JSONResponse
from fastapi.security  import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm    import Session
from starlette.config  import Config

from database    import get_db
from domain.user import user_crud as crud
from domain.user import user_schema as schema


# ────────────────────────────────────────────────────────────────────────────
config        = Config(".env")
DEBUG_MODE    = config("DEBUG_MODE", default="false").lower() == "true"
COOKIE_DOMAIN = config("COOKIE_DOMAIN", default=None)  # 운영용 도메인만 .env에 입력

# JWT 환경 변수 로드
ACCESS_TOKEN_EXPIRE_MINUTES : int = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))
SECRET_KEY                  : str = config("SECRET_KEY")
ALGORITHM                   : str = config("ALGORITHM")

# OAuth2 스킴 설정 (헤더 기반 인증)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl   = "/api/user/login",
    auto_error = False,
)

router = APIRouter(
    prefix = "/api/user",
    tags   = ["로그인 회원가입"],
)


# ────────────────────────── 로거 설정 ──────────────────────────
_log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
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
@router.post(
    "/create",
    status_code = status.HTTP_204_NO_CONTENT,
    description = "사용자 회원가입",
)
def user_create(
    user_data: schema.UserRegister,
    db       : Session = Depends(get_db),
):
    """신규 사용자 등록 (중복 검사 후 204 반환)"""

    _debug("USER_CREATE", f"request data={user_data}")

    if crud.get_existing_user(db, user_data):
        logger.warning(f"회원가입 실패: 이미 존재하는 사용자 '{user_data.username}'")
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail      = "이미 존재하는 사용자입니다.",
        )

    crud.create_user(db, user_data)
    logger.info(f"회원가입 성공: 사용자 '{user_data.username}' 등록")


# ────────────────────────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model = schema.Token,
    description    = "사용자 로그인 (토큰+쿠키 동시 반환)",
)
def login_for_access_token(
    form_data : OAuth2PasswordRequestForm = Depends(),
    db        : Session                   = Depends(get_db),
):
    """인증 후 JWT 발급 및 HttpOnly 쿠키 설정"""

    _debug("LOGIN", f"attempt username='{form_data.username}'")

    # 1) 사용자 조회 및 비밀번호 검증
    user = crud.get_username(db, form_data.username)
    if not user or not crud.pwd_context.verify(form_data.password, user.password):
        logger.warning(f"로그인 실패: username='{form_data.username}'")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "아이디 또는 비밀번호가 올바르지 않습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )

    # 2) 토큰 생성
    expire    = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload   = {"sub": user.username, "exp": expire}
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    logger.info(f"로그인 성공: username='{user.username}'")
    response = JSONResponse(content={
        "access_token" : jwt_token,
        "token_type"   : "bearer",
        "username"     : user.username,
    })
    if DEBUG_MODE:
        # ───── 개발 / 내부망 ─────
        response.set_cookie(
            key      = "access_token",
            value    = jwt_token,
            httponly = True,
            secure   = False,      # HTTP 허용
            samesite = "lax",      # 크로스-사이트 아님 → OK
            path     = "/",
            max_age  = ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            # domain 미지정 → 192.168.x.x, localhost 모두 허용
        )
    else:
        # ───── 운영 / HTTPS ─────
        response.set_cookie(
            key      = "access_token",
            value    = jwt_token,
            httponly = True,
            secure   = True,       # HTTPS 전용
            samesite = "none",     # 크로스 서브도메인 허용
            domain   = COOKIE_DOMAIN,  # 예: "your-domain.com"
            path     = "/",
            max_age  = ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    return response


# ────────────────────────────────────────────────────────────────────────────
def get_current_user(
    token        : str        = Depends(oauth2_scheme),
    cookie_token : str | None = Cookie(None, alias="access_token"),
    db           : Session    = Depends(get_db),
):
    """헤더 또는 쿠키에서 JWT 추출·검증 후 사용자 반환"""

    # 1) 토큰 확보
    token = token or cookie_token
    if not token:
        logger.warning("토큰 누락: 인증 실패")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "자격 증명을 확인할 수 없습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )

    # 2) 토큰 디코드 및 사용자명 추출
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub") or ""
    except JWTError as e:
        _debug("JWT_ERROR", f"{e}")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "자격 증명을 확인할 수 없습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )

    # 3) 사용자 조회
    user = crud.get_username(db, username)
    if not user:
        logger.warning(f"사용자 조회 실패: '{username}' not found")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "자격 증명을 확인할 수 없습니다.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )

    _debug("AUTH", f"token valid for username='{username}'")
    return user


# ────────────────────────────────────────────────────────────────────────────
@router.get(
    "/check_login",
    response_model = schema.LoginCheckOut,
    status_code    = status.HTTP_200_OK,
    summary        = "로그인 상태 확인",
    description    = "JWT를 검사해 로그인 여부를 반환합니다.",
)
def login_check(
    current_user = Depends(get_current_user),
):
    """로그인 검증 후 {username, is_logged_in: True} 반환"""
    _debug("LOGIN_CHECK", f"username='{current_user.username}'")
    return {
        "username"     : current_user.username,
        "is_logged_in" : True,
    }
