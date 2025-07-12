# File: domain/open_api/codef_client.py
import os
import time
import json
import base64
import urllib.parse

from dotenv import load_dotenv
import httpx
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

from models import Account, InternetBanking
from ..utils.crypto import decrypt  # Fernet 복호화


# ───────────────────────────────────────────────────────────────────────────
load_dotenv()

# CODEF API 엔드포인트
TOKEN_URL = "https://oauth.codef.io/oauth/token"
FAST_URL  = "https://development.codef.io/v1/kr/bank/p/fast-account/transaction-list"

# CODEF 앱 자격 정보
CID          = os.getenv("CODEF_CLIENT_ID")
CSECRET      = os.getenv("CODEF_CLIENT_SECRET")
PUBKEY       = os.getenv("CODEF_PUBLIC_KEY") # Base64-DER 포맷
CONNECTED_ID = os.getenv("CODEF_CONNECTED_ID")

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
    return base64.b64encode(encrypted).decode()


# ───────────────────────────────────────────────────────────────────────────
async def _issue_token() -> str:
    
    """new 토큰 발급 (client_credentials)."""
    
    basic_auth = base64.b64encode(f"{CID}:{CSECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type" : "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials", 
        "scope"     : "read"
    }

    async with httpx.AsyncClient(timeout = 15) as client:
        resp = await client.post(TOKEN_URL, headers = headers, data = data)
        resp.raise_for_status()

    token = resp.json()["access_token"]
    _TOKEN.update(value = token, exp = time.time() + 50 * 60) # 50분 유효
    return token


# ───────────────────────────────────────────────────────────────────────────
async def _get_token() -> str:
    
    """유효한 토큰 반환, 없으면 발급."""
    
    if time.time() < _TOKEN["exp"]:
        return _TOKEN["value"]
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

    async def _post(token: str):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type" : "application/json",
        }
        payload = urllib.parse.quote(json.dumps(body, ensure_ascii = False))
        async with httpx.AsyncClient(timeout = 30) as client:
            return await client.post(FAST_URL, headers = headers, data = payload)

    # ── API 호출 ────────────────────────────────────────
    token    = await _get_token()
    response = await _post(token)

    # 토큰 만료 시 재발급 후 재시도
    if response.status_code == 401:
        token    = await _issue_token()
        response = await _post(token)

    response.raise_for_status()
    text = urllib.parse.unquote_plus(response.text)
    return json.loads(text)
