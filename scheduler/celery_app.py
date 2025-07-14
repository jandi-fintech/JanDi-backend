# scheduler/celery_app.py
import logging

from celery           import Celery
from starlette.config import Config

config      = Config('.env')
BROKER_URL  = config('REDIS_URL', default="redis://localhost:6379/0")
BACKEND_URL = config('REDIS_URL', default="redis://localhost:6379/1")
DEBUG_MODE  = config('DEBUG_MODE', default="false").lower() == "true"

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

# ────────────────────────── 초기화 로깅 ─────────────────────────
logger.info("\n")
logger.info("================== Celery app initializing ==================")
_debug("Celery Init", f"BROKER_URL  = {BROKER_URL}")
_debug("Celery Init", f"BACKEND_URL = {BACKEND_URL}")

# ────────────────────────── Celery 앱 초기화 ─────────────────────────
celery_app = Celery(
    "fin_scheduler",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=["scheduler.tasks"], # Task 모듈 import
)

celery_app.conf.timezone = "Asia/Seoul"

# ────────────────────────── Beat 스케줄 ─────────────────────────
celery_app.conf.beat_schedule = {
    "sync-transactions-12h": {
        "task"    : "tasks.sync_transactions",
        "schedule": 60 * 60 * 24,  # 24h
    },
}

logger.info("================== Celery app ready to serve ==================\n")