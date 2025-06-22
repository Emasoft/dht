#!/usr/bin/env python3
"""
config_generators.py - Configuration file generators for different project types  This module contains functions to generate configuration files for various Python frameworks and project types.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
config_generators.py - Configuration file generators for different project types

This module contains functions to generate configuration files for various
Python frameworks and project types.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_type_detector.py to reduce file size
# - Contains all configuration generation functions
# - Organized by project type for clarity
#

from DHT.modules.project_analysis_models import ProjectAnalysis


def generate_django_configs(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate Django-specific configurations."""
    configs = {}

    # pyproject.toml
    configs["pyproject.toml"] = """[tool.django]
settings_module = "mysite.settings"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "mysite.settings"
python_files = ["test_*.py", "*_test.py", "tests.py"]
addopts = "--reuse-db --nomigrations"

[tool.coverage.run]
source = ["."]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/venv/*",
    "manage.py",
]

[tool.mypy]
plugins = ["mypy_django_plugin.main"]

[tool.djlint]
profile = "django"
"""

    # .env.example
    configs[".env.example"] = """# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis cache
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
"""

    # .pre-commit-config.yaml
    configs[".pre-commit-config.yaml"] = """repos:
  - repo: https://github.com/adamchainz/django-upgrade
    rev: 1.15.0
    hooks:
      - id: django-upgrade
        args: [--target-version, "4.2"]

  - repo: https://github.com/rtts/djhtml
    rev: 3.0.6
    hooks:
      - id: djhtml
      - id: djcss
      - id: djjs
"""

    return configs


def generate_fastapi_configs(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate FastAPI-specific configurations."""
    configs = {}

    # Dockerfile
    configs["Dockerfile"] = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    # docker-compose.yml
    configs["docker-compose.yml"] = """version: "3.9"

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
"""

    # alembic.ini
    configs["alembic.ini"] = """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
"""

    return configs


def generate_ml_configs(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate ML/Data Science configurations."""
    configs = {}

    # DVC config
    configs[".dvc/config"] = """[core]
    remote = storage
    autostage = true

['remote "storage"']
    url = s3://my-bucket/dvc-storage
"""

    # MLflow config
    configs["mlflow.yaml"] = """# MLflow configuration
artifact_location: ./mlruns
backend_store_uri: sqlite:///mlflow.db
default_artifact_root: ./mlruns
"""

    # Jupyter config
    configs[".jupyter/jupyter_notebook_config.py"] = """c.NotebookApp.token = ''
c.NotebookApp.password = ''
c.NotebookApp.open_browser = False
c.NotebookApp.port = 8888
"""

    return configs


def generate_library_configs(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate library project configurations."""
    configs = {}

    # setup.cfg
    configs["setup.cfg"] = """[metadata]
name = my-library
version = attr: my_library.__version__

[options]
packages = find:
python_requires = >=3.8

[options.packages.find]
where = src
"""

    # pyproject.toml for library
    configs["pyproject.toml"] = """[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "my-library"
dynamic = ["version"]
description = "A Python library"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    "ruff>=0.1",
]

[tool.setuptools_scm]
write_to = "src/my_library/_version.py"
"""

    return configs


def generate_cli_configs(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate CLI project configurations."""
    configs = {}

    # Add CLI-specific configs
    if "click" in analysis.cli_frameworks:
        configs["setup.py"] = """from setuptools import setup, find_packages

setup(
    name="my-cli",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mycli=cli:main',
        ],
    },
)
"""

    # pyproject.toml for CLI
    configs["pyproject.toml"] = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-cli"
version = "0.1.0"
description = "A command-line tool"
dependencies = [
    "click>=8.0",
]

[project.scripts]
mycli = "my_cli.main:cli"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
"""

    return configs


def generate_common_configs(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate common configuration files."""
    configs = {}

    # Common .gitignore
    if analysis.category.is_data_related():
        configs[".gitignore"] = """# Data files
*.csv
*.h5
*.pkl
*.model
data/
models/
mlruns/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/
"""
    else:
        configs[".gitignore"] = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.tox/
.coverage
.coverage.*
.cache
.pytest_cache/
htmlcov/

# Documentation
docs/_build/
"""

    # Common GitHub Actions workflow
    configs[".github/workflows/tests.yml"] = """name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
"""

    return configs
