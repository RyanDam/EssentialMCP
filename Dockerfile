FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3.10-distutils \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ src/

RUN python3.10 -m venv /app/.venv && \
    VIRTUAL_ENV=/app/.venv uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN cat > /app/docker_entrypoint.py << 'ENTRYPOINT'
import os
from mcp.server.fastmcp import FastMCP

original_init = FastMCP.__init__

def patched_init(self, *args, **kwargs):
    kwargs.setdefault("host", os.environ.get("FASTMCP_HOST", "0.0.0.0"))
    kwargs.setdefault("port", int(os.environ.get("FASTMCP_PORT", "8642")))
    original_init(self, *args, **kwargs)

FastMCP.__init__ = patched_init

from src.server import main
main()
ENTRYPOINT

EXPOSE 8642

ENTRYPOINT ["python", "/app/docker_entrypoint.py"]
