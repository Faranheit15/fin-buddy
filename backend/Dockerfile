# syntax=docker/dockerfile:1.7
# Production image for Fin Buddy API (FastAPI + Uvicorn).

ARG PYTHON_VERSION=3.12

# -----------------------------------------------------------------------------
# Builder — install deps with uv into a project virtualenv
# -----------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer cache)
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Application source + Alembic
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# -----------------------------------------------------------------------------
# Runtime — slim image, non-root, no build tooling
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    # App defaults (override via compose / env)
    ENVIRONMENT=production \
    DEBUG=false \
    LOG_LEVEL=INFO \
    AUTO_MIGRATE=false \
    AUTO_SEED=false \
    STATEMENT_STORAGE_DIR=/data/statements \
    PORT=8000 \
    WEB_CONCURRENCY=2

WORKDIR /app

# curl for HEALTHCHECK; tini for signals; runuser to drop root after volume chown
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 finbuddy \
    && useradd --system --uid 10001 --gid finbuddy --home-dir /app --shell /usr/sbin/nologin finbuddy \
    && mkdir -p /data/statements \
    && chown -R finbuddy:finbuddy /app /data

COPY --from=builder --chown=finbuddy:finbuddy /app /app
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod 755 /app/docker-entrypoint.sh

# Start as root so entrypoint can chown the statement volume, then drops to finbuddy
USER root

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
