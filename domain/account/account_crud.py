# File: domain/account/account_crud.py
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from domain.account.account_schema import (
    InternetBankingCreate,
    InternetBankingOut,
    AccountCreate,
    AccountOut,
)
from models import InternetBanking, Account
from ..utils.crypto import encrypt


# ───────────────────────────────────────────────────────────────────────────
def create_IB(
    db        : Session,
    user_id   : int,
    data      : InternetBankingCreate
) -> InternetBankingCreate:
    """
    인터넷뱅킹 정보 생성 및 저장
    """
    new_ib = InternetBanking(
        user_id              = user_id,
        institution_code     = data.institution_code,
        banking_id           = data.banking_id,
        banking_password_enc = encrypt(data.banking_password),
    )
    db.add(new_ib)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("중복된 인터넷뱅킹 정보입니다.")

    db.refresh(new_ib)
    return InternetBankingOut.from_orm(new_ib)


# ───────────────────────────────────────────────────────────────────────────
def get_existing_IB(
    db        : Session,
    user_id   : int,
    data      : InternetBankingCreate,
) -> Optional[InternetBankingCreate]:
    """
    사용자별 중복 인터넷뱅킹 정보 조회
    """
    ib = (
        db.query(InternetBanking)
        .filter_by(
            user_id          = user_id,
            banking_id       = data.banking_id,
            institution_code = data.institution_code,
        )
        .first()
    )
    return InternetBankingOut.from_orm(ib) if ib else None


# ───────────────────────────────────────────────────────────────────────────
def find_IB_by_user_and_institution(
    db        : Session,
    user_id   : int,
    acc       : AccountCreate,
) -> Optional[InternetBankingCreate]:
    """
    사용자별 특정 금융기관의 인터넷뱅킹 정보 조회
    """
    ib_list = (
        db.query(InternetBanking)
        .filter_by(
            user_id          = user_id,
            institution_code = acc.institution_code
        )
        .first()
    )
    return InternetBankingOut.from_orm(ib_list) if ib_list else None


# ───────────────────────────────────────────────────────────────────────────
def get_IB_list(
    db      : Session,
    user_id : int,
) -> list[InternetBanking]:
    """
    해당 사용자에 등록된 인터넷뱅킹 정보 목록 조회
    """
    return (
        db.query(InternetBanking)
        .filter_by(user_id = user_id)
        .all()
    )


# ───────────────────────────────────────────────────────────────────────────
def create_account(
    db        : Session,
    user_id   : int,
    data      : AccountCreate
) -> AccountCreate:
    """
    계좌 정보 생성 및 저장
    """
    new_acc = Account(
        user_id              = user_id,
        institution_code     = data.institution_code,
        account_number       = data.account_number,
        account_password_enc = encrypt(data.account_password),
    )
    db.add(new_acc)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("중복된 계좌번호입니다.")

    db.refresh(new_acc)
    return AccountOut.from_orm(new_acc)


# ───────────────────────────────────────────────────────────────────────────
def get_existing_account(
    db              : Session,
    user_id         : int,
    account_number  : str
) -> Optional[AccountCreate]:
    """
    특정 사용자의 단일 계좌 조회
    """
    acc = (
        db.query(Account)
        .filter_by(
            user_id        = user_id,
            account_number = account_number
        )
        .first()
    )
    return AccountOut.from_orm(acc) if acc else None


# ───────────────────────────────────────────────────────────────────────────
def get_account_list(
    db      : Session,
    user_id : int,
) -> List[Account]:
    """
    사용자 ID에 연관된 모든 계좌 조회
    """
    acc_list = (
        db.query(Account)
        .filter_by(user_id = user_id)
        .all()
    )
    return [AccountOut.from_orm(acc) for acc in acc_list]
