# File: domain/utils/crypto.py
import logging

from cryptography.fernet    import Fernet
from starlette.config       import Config

# ────────────────────────── 설정값 & 로깅 ──────────────────────────
config     = Config('.env')
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


# ────────────────────────── 암호 객체 생성 ──────────────────────────
_FERNET = Fernet(config('FERNET_KEY', default=''))


# ────────────────────────── 암호화 함수 ──────────────────────────
def encrypt(plain: str) -> str:
    """평문 → 대칭키 암호(Base64)."""

    cipher = _FERNET.encrypt(plain.encode()).decode()
    _debug("CRYPTO", f"encrypt plain='{plain}' -> cipher='{cipher[:8]}...'")
    return cipher


# ────────────────────────── 복호화 함수 ──────────────────────────
def decrypt(cipher_b64: str) -> str:
    """대칭키 암호(Base64) → 평문."""

    plain = _FERNET.decrypt(cipher_b64.encode()).decode()
    _debug("CRYPTO", f"decrypt cipher='{cipher_b64[:8]}...' -> plain='{plain}'")
    return plain
