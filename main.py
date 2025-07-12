from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from starlette.routing import WebSocketRoute

from domain.user import user_router
from domain.fin import fin_router
from domain.account import account_router
from domain.spare_change import spare_change_router

app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.0.16:5173",
    "http://localhost:3000",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WS 설명을 경로별로 정의
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

# OpenAPI 스키마에 WebSocket handshake 경로를 주입
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description=app.description or "",
        routes=app.routes,
    )

    # 모든 WebSocketRoute를 찾아 GET 엔드포인트로 추가
    for route in app.routes:
        if isinstance(route, WebSocketRoute):
            path = route.path
            schema["paths"][path] = {
                "get": {
                    "summary": f"WebSocket – {path}",
                    "description": WS_DESCRIPTIONS.get(path, "WebSocket 채널"),
                    "responses": {
                        "101": {"description": "Switching Protocols"}
                    },
                }
            }

    app.openapi_schema = schema
    return app.openapi_schema

# 라우터 등록
app.include_router(user_router.router)
app.include_router(fin_router.router)
app.include_router(account_router.router)
app.include_router(spare_change_router.router)

# 정적 파일 서빙
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/")
def index():
    return FileResponse("frontend/dist/index.html")

# custom_openapi를 FastAPI에 할당
app.openapi = custom_openapi
