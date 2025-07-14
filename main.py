# File: main.py 
import logging

from fastapi                   import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses       import FileResponse
from starlette.staticfiles     import StaticFiles
from starlette.config          import Config
from fastapi.openapi.utils     import get_openapi
from starlette.routing         import WebSocketRoute

from domain.user         import user_router
from domain.fin          import fin_router
from domain.account      import account_router
from domain.spare_change import spare_change_router
from domain.debug        import debug_router


# ────────────────────────── 설정값 ────────────────────────────
config     = Config('.env')
DEBUG_MODE = config('DEBUG_MODE', default="false").lower() == "true"

# ────────────────────────── 로깅 설정 ──────────────────────────
_log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
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


app = FastAPI()
logger.info("FastAPI app initializing")

# ────────────────────────── CORS 설정 ──────────────────────────
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.0.16:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://0.0.0.0:8000",
    "http://localhost:5173",
    "http://192.168.1.15:5173",
    "http://10.1.0.4:5173",
    "http://192.168.0.16:5173",
    "http://192.168.0.16:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)
_debug("CORS", f"origins set: {origins}")

# ────────────────────────── WS 설명 ──────────────────────────
WS_DESCRIPTIONS = {
    "/ws/investments": """
클라이언트 ↔ 서버 실시간 시세 스트림  
**보내기**: 종목코드 6자리 텍스트 (예: `005930`)  
**받기** (0.5초 간격):

```json
{
    "price": 84100,
    "change": -600
}
```""",
    # 필요하다면 다른 WebSocket 경로도 여기에 추가…
}


# ────────────────────────── Swagger OpenAPI 커스터마이징 ──────────────────────────
# OpenAPI 스키마에 WebSocket handshake 경로를 주입
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    _debug("OPENAPI", "Generating custom OpenAPI schema")
    schema = get_openapi(
        title       = app.title,
        version     = "1.0.0",
        description = app.description or "",
        routes      = app.routes,
    )

    # 모든 WebSocketRoute를 찾아 GET 엔드포인트로 추가
    for route in app.routes:
        if isinstance(route, WebSocketRoute):
            path = route.path
            _debug("OPENAPI", f"Injecting WS path: {path}")
            schema["paths"][path] = {
                "get": {
                    "summary"    : f"WebSocket – {path}",
                    "description": WS_DESCRIPTIONS.get(path, "WebSocket 채널"),
                    "responses"  : {"101": {"description": "Switching Protocols"}},
                }
            }

    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi
_debug("OPENAPI", "Custom OpenAPI configured")


# ────────────────────────── 라우터 등록 ──────────────────────────
app.include_router(user_router.router)
app.include_router(fin_router.router)
app.include_router(account_router.router)
app.include_router(spare_change_router.router)
app.include_router(debug_router.router)
_debug("ROUTER", "All routers included")


# ────────────────────────── 정적 파일 서빙 ──────────────────────────
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
_debug("STATIC", "Mounted /assets -> frontend/dist/assets")


@app.get("/")
def index():
    _debug("ROUTE", "Serving index.html")
    return FileResponse("frontend/dist/index.html")


logger.info("FastAPI app ready to serve")