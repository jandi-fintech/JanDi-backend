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
    description = """
로그인한 사용자가 자신의 인터넷뱅킹 정보를 안전하게 등록합니다.

### 요청 바디
- `institution_code` (string, 4자리 숫자): 은행 기관 코드  
- `banking_id`       (string, 4~32자)   : 인터넷뱅킹 사용자 ID  
- `banking_password` (string, 8~64자)   : 인터넷뱅킹 비밀번호  

### 응답
- **204 No Content**: 등록 성공, 반환 바디 없음  

### 에러 응답
| HTTP  | 상황                                       | 설명                                   |
|-------|--------------------------------------------|----------------------------------------|
| 400   | 이미 등록된 인터넷뱅킹 정보                | 중복된 `banking_id`+`institution_code` |
| 401   | 인증 실패                                  | `access_token`가 없거나 유효하지 않음 |
| 500   | 서버 에러                                  | 내부 처리 중 예외 발생                |

> 프론트엔드:  
> 1. 요청 성공 시(204) "인터넷뱅킹 정보가 등록되었습니다." 토스트 표시  
> 2. 400 응답 시 "이미 등록된 인터넷뱅킹 정보입니다." 알림  
> 3. 기타 에러 시 적절한 에러 핸들링 적용
""",
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
    description    = """
로그인한 사용자가 계좌를 등록합니다.

### 요청 바디
- `institution_code` (string, 4자리 숫자): 은행 기관 코드  
- `account_number`  (string, 10~20자리 숫자): 등록할 계좌번호  
- `account_password` (string, 4~6자리 숫자): 계좌 비밀번호  

### 응답
- **201 Created**: 등록된 계좌 정보(`AccountOut`) 반환  

### 에러 응답
| HTTP  | 상황                   | 설명                                           |
|-------|------------------------|------------------------------------------------|
| 400   | 중복된 계좌번호        | 이미 등록된 `account_number`                   |
| 404   | 인터넷뱅킹 정보 미등록  | 해당 `institution_code`에 대한 인터넷뱅킹 정보 없음 |
| 401   | 인증 실패              | 로그인 필요 또는 토큰 만료                      |
| 500   | 서버 에러              | 내부 처리 중 예외 발생                          |

> 프론트엔드:
> 1. 201 응답 시 "계좌가 성공적으로 등록되었습니다." 토스트 표시  
> 2. 400 응답 시 "이미 등록된 계좌번호입니다." 알림  
> 3. 404 응답 시 "인터넷뱅킹 정보를 먼저 등록해주세요." 알림  
> 4. 기타 에러 시 적절한 에러 핸들링 적용
""",
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
    description     = """
로그인한 사용자가 등록한 **모든 계좌**를 반환합니다.

> 프론트: 계좌 카드/테이블로 렌더링하고, 클릭 시 `/detail/{account_number}` 로 이동하도록 구현하세요.
""",
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
    description     = """
특정 계좌 정보를 조회하고 **선택 기간**의 CODEF 거래내역을 함께 반환합니다.

### 경로·쿼리 파라미터
| 파라미터         | 위치       | 형식         | 설명                          |
|------------------|------------|-------------|-------------------------------|
| `account_number` | path(/url) | 숫자 10~20자  | 조회할 계좌번호               |
| `start`          | query(?)   | `YYYYMMDD`  | 조회 시작일 (선택)            |
| `end`            | query(?)   | `YYYYMMDD`  | 조회 종료일 (선택)            |

- `start`, `end` 미전달 시: `end = 오늘`, `start = end - 29일`(최근 30일)

### 응답/에러
| HTTP | 상황 | 설명                         |
|------|------|------------------------------|
| 200  | 성공 | 계좌 + 거래내역 반환         |
| 404  | 실패 | 계좌 미존재 또는 소유자 불일치 |
| 500  | 실패 | CODEF 호출 실패             |

> 프론트: `transactions` 배열을 무한스크롤·페이징 또는 필터링 UI에 연결해 주세요.
""",
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
