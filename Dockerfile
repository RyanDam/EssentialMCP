# --- Stage 1: Build ---
FROM ubuntu:22.04 AS builder

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

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ src/

# Create venv with system Python and install dependencies + project
RUN python3.10 -m venv /app/.venv && \
    VIRTUAL_ENV=/app/.venv uv sync --frozen --no-dev

# --- Stage 2: Runtime ---
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    libgcc-s1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get autoremove -y

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY src/ src/

# Create Docker entrypoint that patches host to 0.0.0.0
RUN cat > /app/docker_entrypoint.py << 'ENTRYPOINT'
import os
import sys

# Patch FastMCP to use 0.0.0.0 host
from mcp.server.fastmcp import FastMCP
original_init = FastMCP.__init__

def patched_init(self, *args, **kwargs):
    kwargs.setdefault("host", os.environ.get("FASTMCP_HOST", "0.0.0.0"))
    kwargs.setdefault("port", int(os.environ.get("FASTMCP_PORT", "8642")))
    original_init(self, *args, **kwargs)

FastMCP.__init__ = patched_init

# Now run the original main
from src.server import main
main()
ENTRYPOINT

EXPOSE 8642

ENTRYPOINT ["python", "/app/docker_entrypoint.py"]
