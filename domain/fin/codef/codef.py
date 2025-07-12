"""
CODEF OAuth 토큰 발급·거래내역 조회 유틸리티
────────────────────────────────────────────
- client-credentials grant 로 Access Token 획득
- RSA 공개키로 민감 정보 암호화
- FAST 계좌 거래내역(국민은행) 조회
"""

import os
import time
import json
import base64
import urllib.parse

from dotenv import load_dotenv
import httpx
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# ─── 환경 변수 로드 ──────────────────────────────────────────────────────────
load_dotenv()  # .env 파일 읽어오기

# ─── API Endpoints ──────────────────────────────────────────────────────────
TOKEN_URL = "https://oauth.codef.io/oauth/token"
FAST_URL  = "https://development.codef.io/v1/kr/bank/p/fast-account/transaction-list"

# ─── 인증 정보 (.env) ───────────────────────────────────────────────────────
CID      = os.getenv("CODEF_CLIENT_ID")
CSECRET  = os.getenv("CODEF_CLIENT_SECRET")
PUBKEY   = os.getenv("CODEF_PUBLIC_KEY")          # Base64-DER
ACCT_NO  = os.getenv("MY_ACCOUNT_NO")             # 조회계좌
ACCT_PW  = os.getenv("MY_ACCOUNT_PWD")
IB_ID    = os.getenv("MY_IB_ID")                  # 인터넷뱅킹 ID
IB_PW    = os.getenv("MY_IB_PWD")

# ─── RSA 암호기 초기화 ───────────────────────────────────────────────────────
_rsa_cipher = PKCS1_v1_5.new(RSA.import_key(base64.b64decode(PUBKEY)))

# ─── Access Token 캐시 ──────────────────────────────────────────────────────
_TOKEN = {"value": "", "exp": 0}  # exp: 만료 시각(Unix time)

# ────────────────────────────────────────────────────────────────────────────
def rsa_encrypt(plain: str) -> str:
    """RSA 공개키로 평문을 암호화(Base64 인코딩)."""
    cipher = _rsa_cipher.encrypt(plain.encode())
    return base64.b64encode(cipher).decode()


async def _issue_token() -> str:
    """새 Access Token 발급(client-credentials grant)."""
    basic = base64.b64encode(f"{CID}:{CSECRET}".encode()).decode()
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="grant_type=client_credentials&scope=read",
        )
    res.raise_for_status()
    token = res.json().get("access_token")
    _TOKEN.update(value=token, exp=time.time() + 50 * 60)  # 50분 유효
    return token


async def _get_token() -> str:
    """캐시된 토큰 반환(만료 시 재발급)."""
    return _TOKEN["value"] if time.time() < _TOKEN["exp"] else await _issue_token()


async def fetch_transactions(start: str, end: str) -> dict:
    """
    FAST 거래내역 조회(YYYYMMDD).

    :param start: 조회 시작일
    :param end:   조회 종료일
    :return:      CODEF API 응답(JSON → dict)
    """
    body = {
        "organization": "0004",          # 국민은행
        "fastId": "",
        "fastPassword": "",
        "id": IB_ID,
        "password": rsa_encrypt(IB_PW),
        "account": ACCT_NO,
        "accountPassword": rsa_encrypt(ACCT_PW),
        "startDate": start,
        "endDate": end,
        "orderBy": "0",                  # 0: 최신→과거
        "identity": "",
        "connectedId": "byi1wYwD40k8hEIiXl6bRF",
    }

    async def _post(token: str):
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = urllib.parse.quote(json.dumps(body, ensure_ascii=False))
        async with httpx.AsyncClient(timeout=30) as client:
            return await client.post(FAST_URL, headers=headers, data=data)

    # 1차 시도
    token = await _get_token()
    res = await _post(token)

    # 토큰 만료 → 재발급 후 재시도
    if res.status_code == 401:
        token = await _issue_token()
        res = await _post(token)

    res.raise_for_status()
    decoded = urllib.parse.unquote_plus(res.text)  # URL-decode
    return json.loads(decoded)
