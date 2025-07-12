# File: domain/utils/crypto.py
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv


# ───────────────────────────────────────────────────────────────────────────
load_dotenv()

_FERNET = Fernet(os.getenv("FERNET_KEY"))  # 32-byte Base64 key (.env)


# ───────────────────────────────────────────────────────────────────────────
def encrypt(plain: str) -> str:
    """평문 → 대칭키 암호(Base64)."""
    return _FERNET.encrypt(plain.encode()).decode()


# ───────────────────────────────────────────────────────────────────────────
def decrypt(cipher_b64: str) -> str:
    """대칭키 암호(Base64) → 평문."""
    result = _FERNET.decrypt(cipher_b64.encode()).decode()
    return result
