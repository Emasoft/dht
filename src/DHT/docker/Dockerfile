FROM python:3.10-slim AS base

# Install system dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y build-essential git libportaudio2 pandoc && \
    rm -rf /var/lib/apt/lists/*

# Create app user with UID 1000
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Create virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Playwright browser settings
ENV PLAYWRIGHT_BROWSERS_PATH=/home/appuser/pw-browsers
ENV PLAYWRIGHT_SKIP_BROWSER_GC=1

# Create directories with proper permissions
RUN mkdir -p /home/appuser/.{REPO_NAME} /home/appuser/.cache /home/appuser/pw-browsers && \
    chown -R appuser:appuser /home/appuser /app /venv && \
    chmod -R 777 /home/appuser/.{REPO_NAME} /home/appuser/.cache /home/appuser/pw-browsers

# So git doesn't complain about unusual permissions
RUN git config --system --add safe.directory /app

# This puts the container's ~/.{REPO_NAME} into the host's project directory (usually host's cwd).
# That way caches, version checks, etc get stored in the host filesystem not
# simply discarded every time the container exits.
ENV HOME=/app

#########################
FROM base AS {REPO_NAME}-full

ENV {REPO_NAME}_DOCKER_IMAGE={AUTHOR_OR_REPO_OWNER}/{REPO_NAME}-full

COPY . /tmp/{REPO_NAME}

# Install dependencies as root
RUN /venv/bin/python -m pip install --upgrade --no-cache-dir pip && \
    /venv/bin/python -m pip install --no-cache-dir /tmp/{REPO_NAME}[help,browser,playwright] boto3 \
       --extra-index-url https://download.pytorch.org/whl/cpu && \
    rm -rf /tmp/{REPO_NAME}

# Install playwright browsers
RUN /venv/bin/python -m playwright install --with-deps chromium

# Fix site-packages permissions
RUN find /venv/lib/python3.10/site-packages \( -type d -exec chmod a+rwx {} + \) -o \( -type f -exec chmod a+rw {} + \)

# Switch to appuser
USER appuser

ENTRYPOINT ["/venv/bin/{REPO_NAME}"]

#########################
FROM base AS {REPO_NAME}

ENV {REPO_NAME}_DOCKER_IMAGE={AUTHOR_OR_REPO_OWNER}/{REPO_NAME}

COPY . /tmp/{REPO_NAME}

# Install dependencies as root
RUN /venv/bin/python -m pip install --upgrade --no-cache-dir pip && \
    /venv/bin/python -m pip install --no-cache-dir /tmp/{REPO_NAME}[playwright] boto3 google-cloud-aiplatform \
       --extra-index-url https://download.pytorch.org/whl/cpu && \
    rm -rf /tmp/{REPO_NAME}

# Install playwright browsers
RUN /venv/bin/python -m playwright install --with-deps chromium

# Fix site-packages permissions
RUN find /venv/lib/python3.10/site-packages \( -type d -exec chmod a+rwx {} + \) -o \( -type f -exec chmod a+rw {} + \)

# Switch to appuser
USER appuser

ENTRYPOINT ["/venv/bin/{REPO_NAME}"]
