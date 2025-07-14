# File: domain/user/user_crud.py
import logging

from typing import Optional

from sqlalchemy.orm   import Session
from sqlalchemy.exc   import IntegrityError
from passlib.context  import CryptContext
from starlette.config import Config

from domain.user.user_schema import UserRegister, UserOut
from models                  import User


# ────────────────────────── 설정값 ────────────────────────────
config     = Config('.env')
DEBUG_MODE = config('DEBUG_MODE', default="false").lower() == "true"


# ────────────────────────── 로깅 설정 ──────────────────────────
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


# bcrypt 해시 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ────────────────────────────────────────────────────────────────────────────
def get_username(
    db       : Session,
    username : str,
) -> Optional[User]:
    """사용자명 조회."""
    
    _debug("CRUD", f"get_username username={username}")
    result = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )
    _debug("CRUD", f"get_username result={'found' if result else 'none'}")
    return result


# ────────────────────────────────────────────────────────────────────────────
def get_user_email(
    db      : Session,
    email   : str,
) -> Optional[User]:
    """이메일로 사용자 조회."""
    
    _debug("CRUD", f"get_user_email email={email}")
    result = (
        db.query(User)
    .filter(User.email == email)
    .first()
    )
    _debug("CRUD", f"get_user_email result={'found' if result else 'none'}")
    return result


# ────────────────────────────────────────────────────────────────────────────
def get_existing_user(
    db        : Session,
    user_data : UserRegister,
) -> Optional[User]:
    """중복된 사용자명과 이메일 조회."""

    _debug("CRUD", f"get_existing_user username={user_data.username} email={user_data.email}")
    username_user = get_username(db, user_data.username)
    email_user    = get_user_email(db, user_data.email)
    existing      = username_user or email_user
    _debug("CRUD", f"get_existing_user existing={'found' if existing else 'none'}")
    return existing


# ────────────────────────────────────────────────────────────────────────────
def create_user(
    db    : Session,
    data  : UserRegister
) -> UserOut:
    """새로운 사용자 생성 및 저장."""
    _debug("CRUD", f"create_user username={data.username} email={data.email}")
    user = User(
        username = data.username,
        password = pwd_context.hash(data.password1),
        email    = data.email,
    )
    db.add(user)

    try:
        db.commit()
        _debug("CRUD", f"create_user commit success id={user.id}")
    except IntegrityError:
        db.rollback()
        _debug("CRUD", "create_user commit failed: duplicated username or email")
        raise ValueError("Duplicated username or email.")
    
    db.refresh(user)
    _debug("CRUD", f"create_user refreshed user id={user.id}")
    return UserOut.from_orm(user)





