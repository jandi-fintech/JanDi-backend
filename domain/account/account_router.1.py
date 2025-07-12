# File: domain/account/account_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from domain.account.account_schema import (
    InternetBankingCreate,
    AccountCreate,
    AccountOut,
    AccountDetailParams,
    AccountDetailOut,
    TransactionOut,
)
from domain.account.account_crud import (
    create_IB,
    get_existing_IB,
    create_account,
    get_existing_account,
    get_account_list,
    find_IB_by_user_and_institution,
    get_IB_list,
)
from domain.user.user_router import get_current_user
from models import User
from ..open_api.codef_client import fetch_transactions


# ───────────────────────────────────────────────────────────────────────────
router = APIRouter(
    prefix = "/api/account",
    tags   = ["계좌"],
)


# ───────────────────────────────────────────────────────────────────────────
@router.post(
    "/register/ib",
    status_code = status.HTTP_201_CREATED,
    summary     = "인터넷뱅킹 등록",
)
def register_internet_banking(
    data         : InternetBankingCreate,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    새 인터넷뱅킹 정보 등록
    """
    if get_existing_IB(db, current_user.id, data):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "이미 등록된 인터넷뱅킹 정보입니다.",
        )

    create_IB(db, current_user.id, data)


# ───────────────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model = AccountOut,
    status_code    = status.HTTP_201_CREATED,
    summary        = "계좌 등록",
)
def register_account(
    data         : AccountCreate,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
) -> AccountOut:
    """
    계좌등록 전 인터넷뱅킹 정보 확인 및 중복 검사 후 새 계좌 등록
    """
    # 1) 인터넷뱅킹 정보 확인
    ib_list = get_IB_list(db, current_user.id)
    if not ib_list:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "인터넷뱅킹 정보를 먼저 등록해주세요.",
        )
    
    # 2) 계좌번호 중복 검사
    if get_existing_account(db, current_user.id, data.account_number):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "이미 등록된 계좌번호입니다.",
        )
        
    # 3) 새 계좌 생성 및 반환
    return create_account(db, current_user.id, data)


# ───────────────────────────────────────────────────────────────────────────
@router.get(
    "/list",
    response_model  = list[AccountOut],
    status_code     = status.HTTP_200_OK,
    summary         = "계좌 목록 조회",
)
def list_accounts(
    db          : Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
) -> list[AccountOut]:
    """
    사용자의 모든 계좌 조회.
    """
    return get_account_list(db, current_user.id)


# ───────────────────────────────────────────────────────────────────────────
@router.get(
    "/detail/{account_number}",
    response_model  = AccountDetailOut,
    status_code     = status.HTTP_200_OK,
    summary         = "단일 계좌 + 거래내역 조회",
)
async def get_account_detail(
    params       : AccountDetailParams = Depends(),
    db           : Session             = Depends(get_db),
    current_user : User                = Depends(get_current_user),
) -> AccountDetailOut:
    """
    계좌 소유자 검증 → 인터넷뱅킹 정보 조회 → CODEF 호출 → 응답 반환.
    """
    # 계좌 소유자 검증
    acc = get_existing_account(db, current_user.id, params.account_number)
    if not acc:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "해당 계좌를 찾을 수 없습니다.",
        )
    
    # 인터넷뱅킹 정보 조회
    ib = find_IB_by_user_and_institution(db, current_user.id, acc)
    if not ib:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "인터넷뱅킹 정보를 찾을 수 없습니다.",
        )
    
    # CODEF 거래내역 조회
    try:
        res = await fetch_transactions(params.start, params.end, ib, acc)
        txs: TransactionOut = res["data"]["resTrHistoryList"]
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail      = f"CODEF 호출 실패: {e}",
        )
    
    # 응답 반환
    return AccountDetailOut(
        account      = acc,
        transactions = txs,
    )
