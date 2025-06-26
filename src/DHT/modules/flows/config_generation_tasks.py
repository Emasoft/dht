#!/usr/bin/env python3
"""
DHT Configuration Generation Tasks.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created comprehensive configuration generation tasks
# - All templates now accept parameters for full customization
# - Extracted reusable patterns as separate tasks
# - Added framework-specific configuration generators
#

from typing import Any

from prefect import task


@task(name="generate_django_settings", description="Generate Django settings.py")
def generate_django_settings_task(
    project_name: str,
    secret_key: str | None = None,
    debug: bool = True,
    allowed_hosts: list[str] | None = None,
    database_url: str | None = None,
) -> str:
    """Generate Django settings.py with proper configuration.

    Args:
        project_name: Django project name
        secret_key: Django secret key (generated if not provided)
        debug: Debug mode flag
        allowed_hosts: List of allowed hosts
        database_url: Database connection URL

    Returns:
        settings.py content
    """
    import secrets

    secret_key = secret_key or secrets.token_urlsafe(50)
    allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1"]
    database_url = database_url or f"postgresql://user:password@localhost:5432/{project_name}_db"

    hosts_str = ", ".join(f'"{host}"' for host in allowed_hosts)

    return f"""
import os
from pathlib import Path
import dj_database_url

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.environ.get("SECRET_KEY", "{secret_key}")
DEBUG = os.environ.get("DEBUG", "{str(debug)}").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "{",".join(allowed_hosts)}").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "{project_name}.urls"

# Database
DATABASES = {{
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "{database_url}")
    )
}}

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
"""


@task(name="generate_fastapi_main", description="Generate FastAPI main.py")
def generate_fastapi_main_task(
    app_name: str = "app",
    title: str = "FastAPI App",
    version: str = "0.1.0",
    description: str = "A FastAPI application",
) -> str:
    """Generate FastAPI main.py file.

    Args:
        app_name: Variable name for the FastAPI app
        title: API title
        version: API version
        description: API description

    Returns:
        main.py content
    """
    return f'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

{app_name} = FastAPI(
    title="{title}",
    version="{version}",
    description="{description}",
)

# Configure CORS
{app_name}.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@{app_name}.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {title}"}}


@{app_name}.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "version": "{version}"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("{app_name}:app", host="0.0.0.0", port=8000, reload=True)
'''


@task(name="generate_dockerfile", description="Generate optimized Dockerfile")
def generate_dockerfile_task(
    python_version: str = "3.11",
    project_type: str = "web",
    app_module: str = "main:app",
    port: int = 8000,
    system_deps: list[str] | None = None,
    use_uv: bool = True,
    non_root: bool = True,
) -> str:
    """Generate Dockerfile with best practices.

    Args:
        python_version: Python version to use
        project_type: Type of project (web, cli, library)
        app_module: Application module for web apps
        port: Port to expose for web apps
        system_deps: System dependencies to install
        use_uv: Use uv for dependency management
        non_root: Run as non-root user

    Returns:
        Dockerfile content
    """
    system_deps_str = " ".join(system_deps or [])

    # Base dockerfile parts
    base = f"""# Build stage
FROM python:{python_version}-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    build-essential \\
    {system_deps_str} \\
    && rm -rf /var/lib/apt/lists/*
"""

    if use_uv:
        base += """
# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Build the project
RUN uv build
"""
    else:
        base += """
WORKDIR /app

# Copy dependency files
COPY requirements.txt* pyproject.toml* ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
"""

    # Runtime stage
    runtime = f"""
# Runtime stage
FROM python:{python_version}-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    {system_deps_str} \\
    && rm -rf /var/lib/apt/lists/*
"""

    if non_root:
        runtime += """
# Create non-root user
RUN useradd -m -u 1000 appuser
"""

    if use_uv:
        runtime += """
# Copy UV and environment from builder
COPY --from=builder /root/.cargo /home/appuser/.cargo
COPY --from=builder /app /app
"""
    else:
        runtime += """
# Copy application from builder
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
"""

    if non_root:
        runtime += """
# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser
ENV PATH="/home/appuser/.cargo/bin:$PATH"
"""

    runtime += """
WORKDIR /app
"""

    # Add expose and CMD based on project type
    if project_type == "web":
        runtime += f"""
EXPOSE {port}

CMD ["uvicorn", "{app_module}", "--host", "0.0.0.0", "--port", "{port}"]
"""
    elif project_type == "cli":
        runtime += """
ENTRYPOINT ["python", "-m"]
CMD ["app"]
"""
    else:  # library
        runtime += """
CMD ["python"]
"""

    return base + runtime


@task(name="generate_docker_compose", description="Generate docker-compose.yml")
def generate_docker_compose_task(
    project_name: str,
    services: dict[str, dict[str, Any]] | None = None,
    use_postgres: bool = True,
    use_redis: bool = True,
    port: int = 8000,
) -> str:
    """Generate docker-compose.yml with common services.

    Args:
        project_name: Name of the project
        services: Additional services configuration
        use_postgres: Include PostgreSQL service
        use_redis: Include Redis service
        port: Port to expose for web service

    Returns:
        docker-compose.yml content
    """
    compose = f"""version: "3.9"

services:
  web:
    build: .
    ports:
      - "{port}:{port}"
    environment:"""

    if use_postgres:
        compose += f"""
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/{project_name}"""

    if use_redis:
        compose += """
      - REDIS_URL=redis://redis:6379"""

    compose += """
    volumes:
      - .:/app
    depends_on:"""

    if use_postgres:
        compose += """
      - db"""

    if use_redis:
        compose += """
      - redis"""

    compose += """
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

    if use_postgres:
        compose += f"""
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB={project_name}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
"""

    if use_redis:
        compose += """
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
"""

    # Add custom services
    if services:
        for service_name, config in services.items():
            compose += f"""
  {service_name}:
    image: {config.get("image", "alpine")}"""
            if "ports" in config:
                compose += f"""
    ports:
      - "{config["ports"]}" """
            if "environment" in config:
                compose += """
    environment:"""
                for key, value in config["environment"].items():
                    compose += f"""
      - {key}={value}"""

    compose += """
volumes:"""

    if use_postgres:
        compose += """
  postgres_data:"""

    if use_redis:
        compose += """
  redis_data:"""

    return compose


@task(name="generate_env_file", description="Generate .env.example file")
def generate_env_file_task(
    project_type: str = "web",
    database_type: str = "postgresql",
    include_secrets: bool = True,
    custom_vars: dict[str, str] | None = None,
) -> str:
    """Generate .env.example file with common variables.

    Args:
        project_type: Type of project
        database_type: Database type (postgresql, mysql, sqlite)
        include_secrets: Include secret generation examples
        custom_vars: Additional environment variables

    Returns:
        .env.example content
    """
    env_content = """# Application settings
DEBUG=True
LOG_LEVEL=INFO
"""

    if include_secrets:
        env_content += """
# Security
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
"""

    if project_type == "web":
        env_content += """
# Web server
HOST=0.0.0.0
PORT=8000
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
"""

    if database_type == "postgresql":
        env_content += """
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
"""
    elif database_type == "mysql":
        env_content += """
# Database
DATABASE_URL=mysql://user:password@localhost:3306/dbname
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
"""
    elif database_type == "sqlite":
        env_content += """
# Database
DATABASE_URL=sqlite:///./app.db
"""

    env_content += """
# Redis (cache/queue)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# External services
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
"""

    if custom_vars:
        env_content += "\n# Custom variables\n"
        for key, value in custom_vars.items():
            env_content += f"{key}={value}\n"

    return env_content


@task(name="generate_makefile", description="Generate Makefile with common commands")
def generate_makefile_task(
    use_uv: bool = True,
    use_docker: bool = True,
    test_framework: str = "pytest",
) -> str:
    """Generate Makefile with development commands.

    Args:
        use_uv: Include uv commands
        use_docker: Include Docker commands
        test_framework: Testing framework to use

    Returns:
        Makefile content
    """
    if use_uv:
        python_cmd = "uv run python"
        pip_cmd = "uv pip"
        install_cmd = "uv sync"
    else:
        python_cmd = "python"
        pip_cmd = "pip"
        install_cmd = "pip install -r requirements.txt"

    makefile = """.PHONY: help install test lint format clean

help:
\t@echo "Available commands:"
\t@echo "  make install    - Install dependencies"
\t@echo "  make test       - Run tests"
\t@echo "  make lint       - Run linters"
\t@echo "  make format     - Format code"
\t@echo "  make clean      - Clean build artifacts"
"""

    if use_docker:
        makefile += """\t@echo "  make docker-build - Build Docker image"
\t@echo "  make docker-run   - Run Docker container"
\t@echo "  make docker-stop  - Stop Docker containers"
"""

    makefile += f"""
install:
\t{install_cmd}

test:
\t{python_cmd} -m {test_framework}

test-cov:
\t{python_cmd} -m {test_framework} --cov=. --cov-report=html --cov-report=term

lint:
\t{python_cmd} -m ruff check .
\t{python_cmd} -m mypy .

format:
\t{python_cmd} -m ruff format .
\t{python_cmd} -m ruff check --fix .

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {{}} +
\tfind . -type f -name "*.pyc" -delete
\trm -rf .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache
\trm -rf build dist *.egg-info
"""

    if use_docker:
        makefile += """
docker-build:
\tdocker-compose build

docker-run:
\tdocker-compose up -d

docker-stop:
\tdocker-compose down

docker-logs:
\tdocker-compose logs -f
"""

    return makefile


@task(name="generate_github_workflow", description="Generate GitHub Actions workflow")
def generate_github_workflow_task(
    workflow_name: str = "CI",
    python_versions: list[str] | None = None,
    test_on_multiple_os: bool = False,
    use_uv: bool = True,
    deploy_on_tag: bool = False,
) -> str:
    """Generate GitHub Actions workflow with matrix testing.

    Args:
        workflow_name: Name of the workflow
        python_versions: Python versions to test
        test_on_multiple_os: Test on Windows, macOS, Linux
        use_uv: Use uv for dependency management
        deploy_on_tag: Add deployment job for tags

    Returns:
        GitHub Actions workflow YAML
    """
    python_versions = python_versions or ["3.10", "3.11", "3.12"]
    os_matrix = ["ubuntu-latest", "windows-latest", "macos-latest"] if test_on_multiple_os else ["ubuntu-latest"]

    workflow = f"""name: {workflow_name}

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{{{ matrix.os }}}}
    strategy:
      matrix:
        os: {os_matrix}
        python-version: {python_versions}

    steps:
    - uses: actions/checkout@v4
"""

    if use_uv:
        workflow += """
    - name: Install uv
      uses: astral-sh/setup-uv@v2

    - name: Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: uv sync --dev

    - name: Lint
      run: |
        uv run ruff check .
        uv run ruff format --check .

    - name: Type check
      run: uv run mypy .

    - name: Test
      run: uv run pytest --cov --cov-report=xml
"""
    else:
        workflow += """
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Lint
      run: |
        ruff check .
        ruff format --check .

    - name: Type check
      run: mypy .

    - name: Test
      run: pytest --cov --cov-report=xml
"""

    workflow += """
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
"""

    if deploy_on_tag:
        workflow += """
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    steps:
    - uses: actions/checkout@v4

    - name: Build package
      run: |
        uv build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        uv pip install twine
        uv run twine upload dist/*
"""

    return workflow


# Export all tasks
__all__ = [
    "generate_django_settings_task",
    "generate_fastapi_main_task",
    "generate_dockerfile_task",
    "generate_docker_compose_task",
    "generate_env_file_task",
    "generate_makefile_task",
    "generate_github_workflow_task",
]

