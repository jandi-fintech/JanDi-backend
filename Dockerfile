# syntax=docker/dockerfile:1.7
###########################
# 0) 공통 베이스 (런타임)
###########################
FROM python:3.11-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

###########################
# 1) 빌드 스테이지
###########################
FROM base AS builder
# 1-1) uv 단일 바이너리 복사
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 1-2) 작업 디렉터리 준비
WORKDIR /app
COPY pyproject.toml uv.lock ./

# 1-3) 의존성 설치 (캐시 유지)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 1-4) 애플리케이션 복사 + 설치
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

###########################
# 2) 런타임 스테이지
###########################
FROM base
WORKDIR /app
# 2-1) 빌드 산출물만 복사
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
