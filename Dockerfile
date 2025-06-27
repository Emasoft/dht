#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# syntax=docker/dockerfile:1.4

# Multi-stage Dockerfile for DHT using uv
# Based on https://docs.astral.sh/uv/guides/integration/docker/

# Stage 1: Base image with uv
FROM python:3.11-slim AS uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Stage 2: Build stage - install dependencies
FROM python:3.11-slim AS builder

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from the uv stage
COPY --from=uv /bin/uv /bin/uv
COPY --from=uv /bin/uvx /bin/uvx

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY . .

# Install the project
RUN uv sync --frozen --no-dev

# Stage 3: Runtime stage - minimal image for running
FROM python:3.11-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    shellcheck \
    yamllint \
    nodejs \
    npm \
    docker.io \
    podman \
    && rm -rf /var/lib/apt/lists/*

# Install actionlint
RUN curl -s https://api.github.com/repos/rhysd/actionlint/releases/latest | \
    grep "browser_download_url.*linux_amd64" | \
    cut -d '"' -f 4 | \
    xargs curl -sL | \
    tar xz -C /usr/local/bin && \
    chmod +x /usr/local/bin/actionlint

# Copy uv for runtime usage
COPY --from=uv /bin/uv /bin/uv
COPY --from=uv /bin/uvx /bin/uvx

# Set working directory
WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application
COPY --from=builder /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV UV_SYSTEM_PYTHON=1
ENV DHT_IN_DOCKER=1

# Create non-root user
RUN useradd -m -s /bin/bash dhtuser && \
    chown -R dhtuser:dhtuser /app

# Switch to non-root user
USER dhtuser

# Default command
CMD ["dhtl", "--help"]

# Stage 4: Development stage - includes dev dependencies
FROM builder AS development

# Install development dependencies
RUN uv sync --frozen

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    vim \
    less \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Set development environment variables
ENV DHT_ENV=development
ENV PYTHONDONTWRITEBYTECODE=1

# Keep container running for development
CMD ["bash"]

# Stage 5: Test runner stage - optimized for running tests
FROM runtime AS test-runner

# Copy test files
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/.coverage* /app/
COPY --from=builder /app/pytest.ini /app/

# Install test dependencies
USER root
RUN uv pip install pytest pytest-cov pytest-asyncio
USER dhtuser

# Set test environment variables
ENV DHT_TEST_MODE=1
ENV PYTEST_CACHE_DIR=/tmp/.pytest_cache

# Default to running all tests
CMD ["pytest", "-v", "--tb=short"]
