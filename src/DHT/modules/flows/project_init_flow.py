#!/usr/bin/env python3
"""
DHT Project Initialization Flow.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created Prefect flow for project initialization
# - Orchestrates all tasks needed to create a new Python project
# - Includes git initialization and virtual environment setup
# - Supports both uv and pip/venv workflows
#

import shutil
import subprocess
from pathlib import Path

from prefect import flow, task
from prefect.task_runners import ThreadPoolTaskRunner

from ..dhtl_error_handling import log_error, log_info, log_success
from .template_tasks import (
    create_directory_task,
    generate_github_actions_task,
    generate_gitignore_task,
    generate_license_task,
    generate_pre_commit_config_task,
    generate_pyproject_toml_task,
    generate_readme_task,
    write_file_task,
)


@task(name="init_git_repo", description="Initialize git repository")
def init_git_repo_task(project_path: Path) -> bool:
    """Initialize a git repository.

    Args:
        project_path: Path to the project directory

    Returns:
        True if successful
    """
    try:
        if shutil.which("git"):
            result = subprocess.run(["git", "init"], cwd=project_path, capture_output=True, text=True)
            if result.returncode == 0:
                # Create initial commit
                subprocess.run(["git", "add", "."], cwd=project_path)
                subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_path)
                return True
        return False
    except Exception:
        return False


@task(name="create_virtual_env", description="Create Python virtual environment")
def create_virtual_env_task(project_path: Path, use_uv: bool = True) -> bool:
    """Create a Python virtual environment.

    Args:
        project_path: Path to the project directory
        use_uv: Whether to use uv or standard venv

    Returns:
        True if successful
    """
    try:
        if use_uv and shutil.which("uv"):
            result = subprocess.run(["uv", "venv"], cwd=project_path, capture_output=True, text=True)
            if result.returncode == 0:
                # Install dev dependencies
                subprocess.run(["uv", "sync", "--dev"], cwd=project_path)
                return True
            return False
        else:
            # Fallback to standard venv
            import sys

            result = subprocess.run(
                [sys.executable, "-m", "venv", ".venv"], cwd=project_path, capture_output=True, text=True
            )
            return result.returncode == 0
    except Exception:
        return False


@task(name="create_python_version_file", description="Create .python-version file")
def create_python_version_file_task(project_path: Path, python_version: str = "3.10") -> bool:
    """Create .python-version file for version management.

    Args:
        project_path: Path to the project directory
        python_version: Python version to pin

    Returns:
        True if successful
    """
    try:
        version_file = project_path / ".python-version"
        version_file.write_text(f"{python_version}\n")
        return True
    except Exception:
        return False


@flow(
    name="initialize_project",
    description="Initialize a new Python project with DHT",
    task_runner=ThreadPoolTaskRunner(),
)
def initialize_project_flow(
    project_path: Path,
    project_name: str,
    description: str = "A new Python project",
    author_name: str | None = None,
    author_email: str | None = None,
    license_type: str = "MIT",
    python_version: str = "3.10",
    use_uv: bool = True,
) -> bool:
    """Initialize a new Python project.

    Args:
        project_path: Path where to create the project
        project_name: Name of the project
        description: Project description
        author_name: Author name
        author_email: Author email
        license_type: License type (MIT or Apache)
        python_version: Python version to use
        use_uv: Whether to use uv for dependency management

    Returns:
        True if successful
    """
    log_info(f"🚀 Initializing new project: {project_name}")

    # Get author info from git config if not provided
    if not author_name:
        try:
            result = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                author_name = result.stdout.strip()
        except Exception:
            pass
        author_name = author_name or "Your Name"

    if not author_email:
        try:
            result = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                author_email = result.stdout.strip()
        except Exception:
            pass
        author_email = author_email or "your.email@example.com"

    # Create project directory
    project_dir = project_path / project_name
    if project_dir.exists():
        log_error(f"Directory {project_dir} already exists")
        return False

    # Create directory structure
    create_directory_task(project_dir)
    create_directory_task(project_dir / "src" / project_name)
    create_directory_task(project_dir / "tests")
    create_directory_task(project_dir / "docs")
    create_directory_task(project_dir / ".github" / "workflows")

    # Generate all templates
    log_info("📝 Generating project files...")

    # Core project files
    pyproject_content = generate_pyproject_toml_task(
        project_name=project_name,
        version="0.1.0",
        description=description,
        author_name=author_name,
        author_email=author_email,
        python_version=python_version,
    )
    write_file_task(project_dir / "pyproject.toml", pyproject_content)

    # Documentation
    readme_content = generate_readme_task(project_name=project_name, description=description, author_name=author_name)
    write_file_task(project_dir / "README.md", readme_content)

    # License
    license_content = generate_license_task(license_type=license_type, author_name=author_name)
    write_file_task(project_dir / "LICENSE", license_content)

    # Git and development files
    gitignore_content = generate_gitignore_task()
    write_file_task(project_dir / ".gitignore", gitignore_content)

    precommit_content = generate_pre_commit_config_task()
    write_file_task(project_dir / ".pre-commit-config.yaml", precommit_content)

    # CI/CD
    github_actions_content = generate_github_actions_task()
    write_file_task(project_dir / ".github" / "workflows" / "ci.yml", github_actions_content)

    # Python version file
    create_python_version_file_task(project_dir, python_version)

    # Create __init__.py files
    write_file_task(
        project_dir / "src" / project_name / "__init__.py",
        f'"""\\n{project_name} - {description}\\n"""\\n\\n__version__ = "0.1.0"\\n',
    )
    write_file_task(project_dir / "tests" / "__init__.py", '"""Tests for {project_name}."""\\n')

    # Create example test
    example_test = f'''"""Example test for {project_name}."""

import pytest

from {project_name} import __version__


def test_version():
    """Test that version is set correctly."""
    assert __version__ == "0.1.0"


def test_example():
    """Example test to demonstrate pytest."""
    assert 1 + 1 == 2
'''
    write_file_task(project_dir / "tests" / "test_example.py", example_test)

    # Create example module
    example_module = f'''"""Example module for {project_name}."""


def hello(name: str = "World") -> str:
    """Return a greeting.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {{name}}!"


if __name__ == "__main__":
    print(hello())
'''
    write_file_task(project_dir / "src" / project_name / "main.py", example_module)

    # Create .dhtconfig
    dhtconfig_content = f"""# DHT Configuration
project_name: {project_name}
project_type: python
python_version: {python_version}
created_with: dht
version: 1.0.0
"""
    write_file_task(project_dir / ".dhtconfig", dhtconfig_content)

    # Initialize git repository
    log_info("📚 Initializing git repository...")
    init_git_repo_task(project_dir)

    # Create virtual environment
    log_info("🐍 Creating virtual environment...")
    create_virtual_env_task(project_dir, use_uv=use_uv)

    log_success(f"✅ Project {project_name} initialized successfully!")
    log_info(f"📂 Project location: {project_dir}")
    log_info("📝 Next steps:")
    log_info(f"  cd {project_name}")
    if use_uv:
        log_info("  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
        log_info("  uv sync --dev")
    else:
        log_info("  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
        log_info("  pip install -e '.[dev]'")
    log_info("  pre-commit install")

    return True
