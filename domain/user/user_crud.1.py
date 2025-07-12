# File: domain/user/user_crud.py
"""
사용자 CRUD / 비즈니스 로직
"""

from typing                import Optional
from sqlalchemy.orm        import Session
from sqlalchemy.exc        import IntegrityError
from passlib.context       import CryptContext

from domain.user.user_schema import UserRegister, UserOut
from models                  import User


# bcrypt 해시 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(
    db    : Session,
    data  : UserRegister
) -> UserOut:
    """
    새로운 사용자 생성
    - 중복된 username 또는 email 시 예외 발생
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


def get_existing_user(
    db        : Session,
    data      : UserRegister
) -> Optional[User]:
    """
    주어진 username 또는 email 로 사용자 조회
    """
    return (
        db.query(User)
          .filter(
              (User.username == data.username)
              | (User.email    == data.email)
          )
          .first()
    )


def get_user_by_username(
    db       : Session,
    username : str
) -> Optional[User]:
    """
    username 으로 단일 사용자 조회
    """
    return (
        db.query(User)
          .filter_by(username = username)
          .first()
    )
