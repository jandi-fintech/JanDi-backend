# File: domain/debug/debug_router.py
import logging

from starlette.config import Config
from fastapi          import APIRouter, Depends, HTTPException, status

from domain.user.user_router import get_current_user
from models                  import User
from scheduler.tasks         import sync_transactions


# ────────────────────────── 설정값 & 로깅 ──────────────────────────
config     = Config(".env")
DEBUG_MODE = config("DEBUG_MODE", default="false").lower() == "true"
_log_level = logging.DEBUG if DEBUG_MODE else logging.WARNING

logging.basicConfig(
    level  = _log_level,
    format = "[%(levelname)s][%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


def _debug(category: str, message: str) -> None:
    """일관된 형식의 디버그 로그 기록"""

    if DEBUG_MODE:
        logger.debug(f"[{category}] {message}")


router = APIRouter(
    prefix = "/api/debug",
    tags   = ["Debug"],
)


@router.post(
    "/sync-now",
    status_code = status.HTTP_202_ACCEPTED,
    summary     = "거래·잔돈 즉시 동기화(DEBUG용)",
    description = """
관리자 권한으로 Celery 작업을 즉시 큐에 등록하여  
거래내역 및 잔돈 동기화를 실행합니다.  

- 응답 필드:
  • `detail`: 작업 등록 결과 메시지  
  • `task_id`: 큐에 등록된 Celery 태스크 ID  
""",
)
def sync_now(
    current_user: User = Depends(get_current_user)
):
    """Celery 워커에게 sync_transactions 태스크를 비동기 요청합니다."""

    _debug("DEBUG", f"sync_now called by user_id={current_user.id}")

    task = sync_transactions.delay() # Celery 워커에게 비동기 메시지 발행

    if not task:
        _debug("DEBUG", "Failed to enqueue sync_transactions")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail      = "거래 동기화 작업을 큐에 추가하는 데 실패했습니다.",
        )

    _debug("DEBUG", f"sync_transactions queued task_id={task.id}")
    return {"detail": "sync_transactions queued", "task_id": task.id}
