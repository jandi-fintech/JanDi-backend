# File: domain/open_api/codef_client.py
import time
import json
import base64
import urllib.parse
import logging
import httpx

from starlette.config import Config
from Crypto.PublicKey import RSA
from Crypto.Cipher    import PKCS1_v1_5

from models         import Account, InternetBanking
from ..utils.crypto import decrypt  # Fernet 복호화


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


# ───────────────────────────────────────────────────────────────────────────
# CODEF API 엔드포인트
TOKEN_URL = "https://oauth.codef.io/oauth/token"
FAST_URL  = "https://development.codef.io/v1/kr/bank/p/fast-account/transaction-list"

# CODEF 앱 자격 정보
CID          = config("CODEF_CLIENT_ID"     , default="")
CSECRET      = config("CODEF_CLIENT_SECRET" , default="")
PUBKEY       = config("CODEF_PUBLIC_KEY"    , default="")
CONNECTED_ID = config("CODEF_CONNECTED_ID"  , default="")

# RSA 암호 객체 (공개키)
_rsa_cipher = PKCS1_v1_5.new(
    RSA.import_key(base64.b64decode(PUBKEY))
)

# 메모리 내 액세스 토큰 캐시
_TOKEN = {"value": "", "exp": 0}


# ───────────────────────────────────────────────────────────────────────────
def rsa_encrypt(plain: str) -> str:
    """문자열을 RSA 공개키로 암호화하여 Base64 반환."""

    encrypted = _rsa_cipher.encrypt(plain.encode())
    result    = base64.b64encode(encrypted).decode()
    _debug("RSA", f"encrypted {plain[:4]}... -> {result[:8]}...")
    return result


# ───────────────────────────────────────────────────────────────────────────
async def _issue_token() -> str:
    """new 토큰 발급 (client_credentials)."""
    
    basic_auth = base64.b64encode(f"{CID}:{CSECRET}".encode()).decode()
    headers    = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type" : "application/x-www-form-urlencoded",
    }
    data       = {
        "grant_type": "client_credentials",
        "scope"     : "read",
    }
    _debug("TOKEN", "requesting new token")

    async with httpx.AsyncClient(timeout = 15) as client:
        resp = await client.post(TOKEN_URL, headers = headers, data = data)

    resp.raise_for_status()
    token = resp.json().get("access_token", "")
    _TOKEN.update(value = token, exp = time.time() + 50 * 60)  # 50분 유효
    _debug("TOKEN", f"issued token expires at {_TOKEN['exp']}")
    return token


# ───────────────────────────────────────────────────────────────────────────
async def _get_token() -> str:
    """유효한 토큰 반환, 없으면 발급."""

    if time.time() < _TOKEN["exp"]:
        _debug("TOKEN", "using cached token")
        return _TOKEN["value"]

    _debug("TOKEN", "cached token expired or missing")
    return await _issue_token()


# ───────────────────────────────────────────────────────────────────────────
async def fetch_transactions(
    start : str,
    end   : str,
    ib    : InternetBanking,
    acc   : Account,
):
    """ FAST 거래내역 조회 """
    
    # ── 인증 및 계좌 정보 준비 ───────────────────────────
    org_code       = ib.institution_code
    user_id        = ib.banking_id
    user_password  = rsa_encrypt(decrypt(ib.banking_password_enc))
    account_number = acc.account_number
    account_pass   = rsa_encrypt(decrypt(acc.account_password_enc))
    start_date     = start
    end_date       = end
    connected_id   = CONNECTED_ID

    body = {
        "organization"    : org_code,
        "fastId"          : "",
        "fastPassword"    : "",
        "id"              : user_id,
        "password"        : user_password,
        "account"         : account_number,
        "accountPassword" : account_pass,
        "startDate"       : start_date,
        "endDate"         : end_date,
        "orderBy"         : "0",
        "identity"        : "",
        "connectedId"     : connected_id,
    }
    _debug("FETCH", f"prepared body for account {account_number}")

    async def _post(token: str):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type" : "application/json",
        }
        payload = urllib.parse.quote(json.dumps(body, ensure_ascii = False))
        _debug("FETCH", f"posting to {FAST_URL} with token prefix {token[:6]}...")
        async with httpx.AsyncClient(timeout = 30) as client:
            return await client.post(FAST_URL, headers = headers, data = payload)

    # ── API 호출 ────────────────────────────────────────
    token    = await _get_token()
    response = await _post(token)

    # 토큰 만료 시 재발급 후 재시도
    if response.status_code == 401:
        _debug("FETCH", "token expired, reissuing and retrying")
        token    = await _issue_token()
        response = await _post(token)

    _debug("FETCH", f"response status {response.status_code}")
    response.raise_for_status()

    text = urllib.parse.unquote_plus(response.text)
    _debug("FETCH", f"response text (truncated): {text[:100]}...")
    return json.loads(text)
