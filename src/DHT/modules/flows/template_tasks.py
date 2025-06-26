#!/usr/bin/env python3
"""
DHT Template Generation Tasks.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created Prefect tasks for all template generation
# - Converted from dhtl_project_templates.py functions
# - Added additional templates for comprehensive project setup
# - All tasks return template content as strings
#

from pathlib import Path

from prefect import task

from ..dhtl_project_templates import (
    get_apache_license,
    get_github_actions_ci,
    get_mit_license,
    get_python_gitignore,
)


@task(name="generate_gitignore", description="Generate Python .gitignore file content")
def generate_gitignore_task() -> str:
    """Generate Python .gitignore content."""
    return get_python_gitignore()


@task(name="generate_license", description="Generate license file content")
def generate_license_task(license_type: str = "MIT", author_name: str | None = None) -> str:
    """Generate license content based on type.

    Args:
        license_type: Type of license (MIT or Apache)
        author_name: Name of the author/copyright holder

    Returns:
        License text content
    """
    if license_type.upper() == "MIT":
        return get_mit_license(author_name)
    elif license_type.upper() == "APACHE":
        return get_apache_license(author_name)
    else:
        raise ValueError(f"Unsupported license type: {license_type}")


@task(name="generate_github_actions", description="Generate GitHub Actions workflow")
def generate_github_actions_task() -> str:
    """Generate GitHub Actions CI/CD workflow."""
    return get_github_actions_ci()


@task(name="generate_pyproject_toml", description="Generate pyproject.toml file")
def generate_pyproject_toml_task(
    project_name: str,
    version: str = "0.1.0",
    description: str = "A new Python project",
    author_name: str | None = None,
    author_email: str | None = None,
    python_version: str = "3.10",
) -> str:
    """Generate pyproject.toml content.

    Args:
        project_name: Name of the project
        version: Initial version
        description: Project description
        author_name: Author name
        author_email: Author email
        python_version: Minimum Python version

    Returns:
        pyproject.toml content
    """
    author_name = author_name or "Your Name"
    author_email = author_email or "your.email@example.com"

    return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "{version}"
description = "{description}"
readme = "README.md"
requires-python = ">={python_version}"
license = {{text = "MIT"}}
authors = [
    {{name = "{author_name}", email = "{author_email}"}},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "pre-commit>=3.0.0",
]

[project.urls]
Homepage = "https://github.com/{author_name}/{project_name}"
Repository = "https://github.com/{author_name}/{project_name}"
Issues = "https://github.com/{author_name}/{project_name}/issues"

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "C90", "I", "N", "UP", "S", "B", "A", "C4", "T20", "PT"]
ignore = ["E501"]

[tool.mypy]
python_version = "{python_version}"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=src --cov-report=term-missing --cov-report=html"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
'''


@task(name="generate_readme", description="Generate README.md file")
def generate_readme_task(
    project_name: str, description: str = "A new Python project", author_name: str | None = None
) -> str:
    """Generate README.md content.

    Args:
        project_name: Name of the project
        description: Project description
        author_name: Author name

    Returns:
        README.md content
    """
    author_name = author_name or "Your Name"

    return f"""# {project_name}

{description}

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/{author_name}/{project_name}.git
cd {project_name}

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
uv sync
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/{author_name}/{project_name}.git
cd {project_name}

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
```

## Development

### Running tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test
uv run pytest tests/test_example.py
```

### Code quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy .
```

### Pre-commit hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all hooks manually
uv run pre-commit run --all-files
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

- {author_name}
"""


@task(name="generate_pre_commit_config", description="Generate .pre-commit-config.yaml")
def generate_pre_commit_config_task() -> str:
    """Generate .pre-commit-config.yaml content."""
    return """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-toml
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks
"""


@task(name="write_file", description="Write content to a file")
def write_file_task(file_path: Path, content: str) -> bool:
    """Write content to a file.

    Args:
        file_path: Path to write to
        content: Content to write

    Returns:
        True if successful
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}")
        return False


@task(name="create_directory", description="Create a directory")
def create_directory_task(dir_path: Path) -> bool:
    """Create a directory.

    Args:
        dir_path: Directory path to create

    Returns:
        True if successful
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {dir_path}: {e}")
        return False
