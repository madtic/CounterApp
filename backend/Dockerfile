# syntax=docker/dockerfile:1

# =============================================================================
# BASIC / NAIVE IMAGE (for comparison only)
#
# * one single stage
# * huge general-purpose base image (~1 GB before dependencies)
# * build tools and uv stay in the final image
#
# Build:  docker build -t counter-backend:basic .
# =============================================================================
FROM python:3.13

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies first, so code changes do not invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]