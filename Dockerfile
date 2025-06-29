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
COPY pyproject.toml uv.lock* README.md ./

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

# Create non-root user first
RUN useradd -m -u 1000 -s /bin/bash dhtuser

# Set working directory
WORKDIR /app

# Copy the virtual environment from builder to /opt/venv
COPY --from=builder /app/.venv /opt/venv
COPY --from=builder --chown=dhtuser:dhtuser /app /app

# Fix ownership
RUN chown -R dhtuser:dhtuser /opt/venv

# Set environment variables to use the copied venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV UV_SYSTEM_PYTHON=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
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

# Install development dependencies in the opt venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN cd /app && uv sync --frozen --all-extras

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    vim \
    less \
    htop \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set development environment variables
ENV DHT_ENV=development
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

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

# Create non-root user first
RUN useradd -m -u 1000 -s /bin/bash dhtuser

# Set working directory
WORKDIR /app

# Copy dependency files first as root
COPY pyproject.toml uv.lock* README.md ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
    UV_PROJECT_ENVIRONMENT=/opt/venv uv sync --frozen --all-extras

# Copy the rest of the application
COPY --chown=dhtuser:dhtuser . .

# Set ownership
RUN chown -R dhtuser:dhtuser /app /opt/venv

# Create cache directories with correct ownership
RUN mkdir -p /tmp/.cache/uv /tmp/.pytest_cache /app/test-results && \
    chown -R dhtuser:dhtuser /tmp/.cache /tmp/.pytest_cache /app/test-results

# Set environment to use venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PYTHONPATH="/app/src:/app:$PYTHONPATH"
ENV DHT_IN_DOCKER=1
ENV DHT_TEST_MODE=1
ENV DHT_TEST_PROFILE=docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTEST_CACHE_DIR=/tmp/.pytest_cache
ENV UV_CACHE_DIR=/tmp/.cache/uv
ENV HOME=/home/dhtuser

# Switch to non-root user
USER dhtuser

# Verify Python setup
RUN python --version && \
    python -c "import sys; print('Python executable:', sys.executable); print('Python path:', sys.path)" && \
    which pytest && \
    pytest --version

# Default to running all tests
CMD ["python", "-m", "pytest", "-v", "--tb=short"]
