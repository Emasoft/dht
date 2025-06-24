#!/usr/bin/env python3
from __future__ import annotations

"""
project_file_generators.py - Project file generators  This module generates project files like gitignore, Dockerfile, and CI workflows.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
project_file_generators.py - Project file generators

This module generates project files like gitignore, Dockerfile, and CI workflows.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_configurator.py to reduce file size
# - Contains generators for gitignore, Dockerfile, GitHub workflows, and env files
#


from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from DHT.modules.environment_config_models import EnvironmentConfig


def generate_gitignore(project_path: Path, project_type: str) -> None:
    """Generate appropriate .gitignore file."""
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
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
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# UV
uv.lock
"""

    if project_type == "nodejs":
        gitignore_content += """
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache
"""

    gitignore_file = project_path / ".gitignore"
    gitignore_file.write_text(gitignore_content)


def generate_dockerfile(config: EnvironmentConfig) -> None:
    """Generate Dockerfile from container configuration."""
    if not config.container_config:
        return

    container_config = config.container_config

    dockerfile_content = f"""FROM {container_config["base_image"]}

# Set working directory
WORKDIR {container_config["working_dir"]}

# Install system dependencies
"""

    if container_config["system_packages"]:
        if "ubuntu" in container_config["base_image"] or "debian" in container_config["base_image"]:
            dockerfile_content += f"""RUN apt-get update && apt-get install -y \\
    {" ".join(container_config["system_packages"])} \\
    && rm -rf /var/lib/apt/lists/*

"""

    if config.project_type == "python":
        dockerfile_content += """# Copy requirements first for better caching
COPY requirements.txt* pyproject.toml* uv.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || \\
    pip install --no-cache-dir -e . || \\
    echo "No requirements file found"

# Copy project files
COPY . .

"""

    if container_config.get("exposed_ports"):
        for port in container_config["exposed_ports"]:
            dockerfile_content += f"EXPOSE {port}\n"

    dockerfile_content += """
# Default command
CMD ["python", "-m", "your_module"]
"""

    dockerfile_path = config.project_path / "Dockerfile"
    dockerfile_path.write_text(dockerfile_content)


def generate_dockerignore(project_path: Path) -> None:
    """Generate .dockerignore file."""
    dockerignore_content = """# Git
.git/
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/
env/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Project specific
.env
*.log
"""

    dockerignore_file = project_path / ".dockerignore"
    dockerignore_file.write_text(dockerignore_content)


def generate_github_workflow(config: EnvironmentConfig) -> None:
    """Generate GitHub Actions workflow."""
    if not config.ci_config:
        return

    ci_config = config.ci_config

    workflow = {
        "name": "CI",
        "on": {"push": {"branches": ["main", "develop"]}, "pull_request": {"branches": ["main"]}},
        "jobs": {
            "test": {
                "runs-on": "${{ matrix.os }}",
                "strategy": {
                    "matrix": {
                        "os": ci_config.get("os_matrix", ["ubuntu-latest"]),
                        "python-version": ci_config.get("python_versions", ["3.11"]),
                    }
                },
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {
                        "name": "Set up Python ${{ matrix.python-version }}",
                        "uses": "actions/setup-python@v4",
                        "with": {"python-version": "${{ matrix.python-version }}"},
                    },
                    {"name": "Install UV", "run": "pip install uv"},
                    {"name": "Install dependencies", "run": "uv sync --all-extras"},
                ],
            }
        },
    }

    # Add workflow-specific steps
    workflows = ci_config.get("workflows", [])
    workflows = list(workflows) if workflows else []
    if isinstance(workflows, list) and "test" in workflows:
        workflow["jobs"]["test"]["steps"].append({"name": "Run tests", "run": "pytest"})

    if isinstance(workflows, list) and "lint" in workflows:
        workflow["jobs"]["test"]["steps"].extend(
            [
                {"name": "Run linting", "run": "ruff check ."},
                {"name": "Check formatting", "run": "black --check ."},
                {"name": "Type checking", "run": "mypy ."},
            ]
        )

    if isinstance(workflows, list) and "build" in workflows:
        workflow["jobs"]["test"]["steps"].append({"name": "Build package", "run": "uv build"})

    # Ensure .github/workflows directory exists
    workflows_dir = config.project_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    workflow_file = workflows_dir / "ci.yml"
    with open(workflow_file, "w") as f:
        yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)


def generate_gitlab_ci(config: EnvironmentConfig) -> None:
    """Generate GitLab CI configuration."""
    if not config.ci_config:
        return

    gitlab_ci = {
        "stages": ["test", "build", "deploy"],
        "variables": {"PIP_CACHE_DIR": "$CI_PROJECT_DIR/.cache/pip"},
        "cache": {"paths": [".cache/pip", ".venv/"]},
        "test": {
            "stage": "test",
            "image": f"python:{config.python_version or '3.11'}",
            "before_script": ["pip install uv", "uv venv", "source .venv/bin/activate", "uv sync --all-extras"],
            "script": ["pytest", "ruff check .", "black --check .", "mypy ."],
        },
    }

    gitlab_ci_file = config.project_path / ".gitlab-ci.yml"
    with open(gitlab_ci_file, "w") as f:
        yaml.dump(gitlab_ci, f, default_flow_style=False, sort_keys=False)


def generate_env_file(config: EnvironmentConfig) -> None:
    """Generate .env.example file."""
    env_content = "# Environment Variables\n"
    env_content += "# Copy this file to .env and fill in the values\n\n"

    # Default environment variables
    default_vars = {
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "postgresql://user:pass@localhost/dbname",
        "SECRET_KEY": "your-secret-key-here",
        "REDIS_URL": "redis://localhost:6379/0",
    }

    # Merge with config environment variables
    all_vars = {**default_vars, **config.environment_variables}

    for key, value in all_vars.items():
        env_content += f"{key}={value}\n"

    env_file = config.project_path / ".env.example"
    env_file.write_text(env_content)


def generate_makefile(config: EnvironmentConfig) -> None:
    """Generate Makefile with common commands."""
    makefile_content = """# Makefile for project automation

.PHONY: help install test lint format clean build

help:  ## Show this help
\t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

install:  ## Install dependencies
\tuv venv
\tuv sync --all-extras

test:  ## Run tests
\tpytest

lint:  ## Run linters
\truff check .
\tmypy .

format:  ## Format code
\truff format .
\tblack .

clean:  ## Clean build artifacts
\trm -rf build/ dist/ *.egg-info/
\tfind . -type d -name __pycache__ -exec rm -rf {} +
\tfind . -type f -name "*.pyc" -delete

build:  ## Build package
\tuv build

dev:  ## Run development server
\tpython -m your_module

docker-build:  ## Build Docker image
\tdocker build -t $(PROJECT_NAME) .

docker-run:  ## Run Docker container
\tdocker run -it --rm -p 8000:8000 $(PROJECT_NAME)
"""

    makefile = config.project_path / "Makefile"
    makefile.write_text(makefile_content)
