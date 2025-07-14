# File: scheduler/tasks.py
import logging
import asyncio

from datetime import datetime, timedelta, timezone, time
from decimal  import Decimal
from math     import ceil
from typing   import Iterable, Optional, List

from sqlalchemy.orm   import Session
from starlette.config import Config

from scheduler.celery_app         import celery_app
from database                     import SyncSessionLocal
from models                       import User, Account, Transaction, SpareChange, InternetBanking
from domain.open_api.codef_client import fetch_transactions


# ────────────────────────── 설정값 ────────────────────────────
config         = Config('.env')
KST            = timezone(timedelta(hours=9))
WITHDRAW_TYPES = {"withdraw", "payment"}  # 잔돈 대상 거래 유형
DEFAULT_UNIT   = 100                      # user.round_up_unit 가 비정상일 때 사용
DEBUG_MODE     = config('DEBUG_MODE', default="false").lower() == "true"
# ──────────────────────────────────────────────────────────────


# ────────────────────────── 로깅 설정 ──────────────────────────
_log_level = logging.DEBUG if DEBUG_MODE else logging.WARNING
logging.basicConfig(
    level=_log_level,
    format="[%(levelname)s][%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ────────────────────────── Debug 헬퍼 ─────────────────────────
def _debug(category: str, message: str) -> None:
    """일관된 형식의 디버그 로그 기록"""

    if DEBUG_MODE:
        logger.debug(f"[{category}] {message}")


# ────────────────────────── 유틸 함수 ─────────────────────────
def _date_range_yesterday() -> tuple[str, str]:
    """어제 02:00 ~ 오늘 02:00 (YYYYMMDD)"""

    today    = datetime.now(KST).date()
    start_dt = datetime.combine(today - timedelta(days=1), time(hour=2), tzinfo=KST)
    end_dt   = datetime.combine(today, time(hour=2), tzinfo=KST)
    
    start_str = start_dt.strftime("%Y%m%d")
    end_str   = end_dt.strftime("%Y%m%d")

    _debug("DATE", f"range: {start_str} → {end_str}")
    return start_str, end_str


def _get_unit(user: User) -> int:
    """User.round_up_unit (양수) → 없으면 DEFAULT_UNIT"""

    u = user.round_up_unit
    unit = u if isinstance(u, int) and u > 0 else DEFAULT_UNIT
    
    _debug("UNIT", f"user_id={user.id} round_up_unit={unit}")
    return unit


def _find_ib(
    db      : Session,
    user    : User,
    account : Account
) -> Optional[InternetBanking]:
    """사용자 + 기관코드 기반 InternetBanking 레코드 조회"""

    ib = (
        db.query(InternetBanking)
        .filter(
            InternetBanking.user_id          == user.id,
            InternetBanking.institution_code == account.institution_code,
        )
        .first()
    )
    status = "FOUND" if ib else "MISSING"
    _debug("IB", f"user_id={user.id} account_id={account.id} status={status}")
    return ib


def _find_accounts(
    db               : Session,
    user             : User,
    institution_code : str | None = None,
) -> List[Account]:
    """
    사용자의 계좌 목록 조회 헬퍼
    ────────────────────────────────────────────────
    • institution_code 를 주면 해당 기관 계좌만 반환  
    • 주지 않으면 사용자의 모든 계좌 반환
    """
    q = db.query(Account).filter(Account.user_id == user.id)

    if institution_code:
        q = q.filter(Account.institution_code == institution_code)

    return q.all()


# ────────────────────────── util: async → sync ──────────────────────────
def _run_async(coro):
    """Celery 워커 내부에서 비동기 함수를 동기 방식으로 호출"""

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    return loop.run_until_complete(coro)
# ─────────────────────────────────────────────────────────────────────────


# ────────────────────────── 트랜잭션 & 잔돈 처리 ─────────────────────────
def _upsert_tx_and_spare_change(
    db      : Session,
    user    : User,
    account : Account,
    item    : dict,
) -> None:
    """
    * Transaction 없으면 INSERT  
    * 출금 거래(resAccountOut)면 SpareChange 계산·삽입
    """
    # 1) 거래 ID: "계좌ID-YYYYMMDDHHMMSS"
    tx_id = f"{account.id}-{item['resAccountTrDate']}{item['resAccountTrTime']}"

    # 2) 금액/거래 타입 판단
    out_amt = item.get("resAccountOut") or "0"
    in_amt  = item.get("resAccountIn")  or "0"
    
    if out_amt != "0":
        amount  = Decimal(out_amt)
        tx_type = "withdraw"      # 출금 거래
    else:
        amount  = Decimal(in_amt)
        tx_type = "deposit"       # 입금 거래

    # 3) 메모(설명 1~4) 병합
    descs = [item.get(f"resAccountDesc{i}") for i in (1, 2, 3, 4)]
    memo  = ";".join(filter(None, descs)) or None

    _debug("TX", f"{tx_id} {tx_type.upper()} amount={amount}")

    # 4) Transaction UPSERT
    if db.get(Transaction, tx_id) is None:
        db.add(Transaction(
            id         = tx_id,
            user_id    = user.id,
            account_id = account.id,
            amount     = amount,
            tx_type    = tx_type,
            memo       = memo,
        ))
        db.flush()  # FK 확인 및 ID 고정
        _debug("TX", f"INSERT new Transaction {tx_id}")

    # 5) 출금 → SpareChange
    if tx_type in WITHDRAW_TYPES:
        sc_pk = (user.id, tx_id)
        if db.get(SpareChange, sc_pk) is None:
            unit     = _get_unit(user)
            raw_diff = Decimal(ceil(amount / unit)) * unit - amount
            round_up = raw_diff.quantize(Decimal("0.01"))
            
            db.add(SpareChange(
                user_id  = user.id,
                tx_id    = tx_id,
                round_up = round_up,
            ))
            
            _debug("SC", f"user_id={user.id} tx_id={tx_id} round_up={round_up}")


# ─────────────────────────── Celery Task ──────────────────────
@celery_app.task(name="tasks.sync_transactions")
def sync_transactions() -> str:
    """전 계좌 거래내역 동기화 + 잔돈 계산"""

    db : Session = SyncSessionLocal()
    start, end   = _date_range_yesterday()

    _debug("TASK", "=== START sync_transactions ===")
    try:
        users: Iterable[User] = db.query(User).all()
        _debug("TASK", f"total users={len(users)}")

        for user in users:
            _debug("TASK", f"user_id={user.id} accounts={len(user.accounts)}")
            accounts = _find_accounts(db, user)
            
            for acc in accounts:
                _debug("TASK", f"account_id={acc.id} ({acc.institution_code}-{acc.account_number})")

                ib = _find_ib(db, user, acc)
                _debug("TASK", f"IB exists={ib is not None}")

                if ib:
                    _debug("IB", f"institution_code={ib.institution_code} banking_id={ib.banking_id}")
                else:
                    _debug("IB", "missing InternetBanking record")

                _debug("TASK", f"fetching transactions from {start} to {end}")
                res         = _run_async(fetch_transactions(start, end, ib, acc)) # CODEF 호출
                res_message = res["result"]["message"]
                _debug("TASK", f"response message={res_message}")

                items = res["data"]["resTrHistoryList"]
                _debug("TASK", f"fetched items count={len(items)}")

                for item in items:
                    _upsert_tx_and_spare_change(db, user, acc, item)

        db.commit()
        _debug("TASK", "=== DONE sync_transactions (OK) ===")
        return "OK"

    except Exception as e:
        db.rollback()
        _debug("ERROR", f"sync_transactions error: {e}")
        raise

    finally:
        db.close()
