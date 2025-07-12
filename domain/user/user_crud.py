# File: domain/user/user_crud.py
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from domain.user.user_schema import UserRegister, UserOut
from models import User


# bcrypt 해시 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ────────────────────────────────────────────────────────────────────────────
def get_username(
    db       : Session,
    username : str,
) -> Optional[User]:
    """
    사용자명 조회.
    """
    return (
        db.query(User)
        .filter(User.username == username)
        .first()
    )


# ────────────────────────────────────────────────────────────────────────────
def get_user_email(
    db      : Session,
    email   : str,
) -> Optional[User]:
    """
    이메일로 사용자 조회.
    """
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


# ────────────────────────────────────────────────────────────────────────────
def get_existing_user(
    db        : Session,
    user_data : UserRegister,
) -> Optional[User]:
    """
    중복된 사용자명과 이메일 조회.
    """
    username = get_username(db, user_data.username)
    email    = get_user_email(db, user_data.email)
    
    return username or email


# ────────────────────────────────────────────────────────────────────────────
def create_user(
    db    : Session,
    data  : UserRegister
) -> UserOut:
    """
    새로운 사용자 생성 및 저장.
    """
    user = User(
        username = data.username,
        password = pwd_context.hash(data.password1),
        email    = data.email
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Duplicated username or email.")
    
    db.refresh(user)
    return UserOut.from_orm(user)





