#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# syntax=docker/dockerfile:1.4

# Multi-stage Dockerfile for DHT using uv
# Based on https://docs.astral.sh/uv/guides/integration/docker/

# Stage 1: Base image with uv
FROM ghcr.io/astral-sh/uv:latest AS uv

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
COPY --from=uv /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies
RUN uv venv && uv sync --frozen --no-install-project

# Copy the rest of the application
COPY . .

# Install the project
RUN uv sync --frozen

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
    && rm -rf /var/lib/apt/lists/*

# Install actionlint
RUN curl -s https://api.github.com/repos/rhysd/actionlint/releases/latest | \
    grep "browser_download_url.*linux_amd64" | \
    cut -d '"' -f 4 | \
    xargs curl -sL | \
    tar xz -C /usr/local/bin && \
    chmod +x /usr/local/bin/actionlint

# Copy uv for runtime usage
COPY --from=uv /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy the virtual environment and application from builder
COPY --from=builder --chown=1000:1000 /app /app

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash dhtuser

# Set environment variables
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV UV_SYSTEM_PYTHON=1
ENV DHT_IN_DOCKER=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER dhtuser

# Default command
CMD ["dhtl", "--help"]

# Stage 4: Development stage - includes dev dependencies
FROM runtime AS development

# Switch to root for installations
USER root

# Install development dependencies
RUN uv sync --frozen --all-extras

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    vim \
    less \
    htop \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set development environment variables
ENV DHT_ENV=development

# Switch back to non-root user
USER dhtuser

# Keep container running for development
CMD ["bash"]

# Stage 5: Test runner stage - optimized for running tests
FROM python:3.11-slim AS test-runner

# Install test runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    make \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy uv
COPY --from=uv /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy everything from builder with proper ownership
COPY --from=builder --chown=1000:1000 /app /app

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash dhtuser

# Fix Python paths before switching user
RUN python -m ensurepip --upgrade && \
    python -m pip install --upgrade pip setuptools wheel

# Set environment variables properly
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:/app:$PYTHONPATH"
ENV UV_SYSTEM_PYTHON=1
ENV DHT_IN_DOCKER=1
ENV DHT_TEST_MODE=1
ENV DHT_TEST_PROFILE=docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTEST_CACHE_DIR=/tmp/.pytest_cache
ENV HOME=/home/dhtuser

# Create directories and fix permissions for the virtual environment
RUN mkdir -p /app/test-results /tmp/.pytest_cache && \
    chown -R dhtuser:dhtuser /app /tmp/.pytest_cache && \
    chmod -R 755 /app/.venv && \
    find /app/.venv/bin -type f -exec chmod +x {} \;

# Switch to non-root user
USER dhtuser

# Verify Python setup and dhtl installation
RUN /app/.venv/bin/python --version && \
    /app/.venv/bin/python -c "import sys; print('Python executable:', sys.executable); print('Python path:', sys.path)" && \
    which dhtl && \
    dhtl --version

# Default to running all tests
CMD ["/app/.venv/bin/python", "-m", "pytest", "-v", "--tb=short"]
