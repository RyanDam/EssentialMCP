FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ src/

RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1
ENV TRANSPORT=streamable-http

EXPOSE 8642

CMD ["uv", "run", "web-mcp"]
