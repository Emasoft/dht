#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_workflows.sh
# - Implements workflows command for GitHub Actions management
# - Creates, lists, and manages CI/CD workflows
# - Integrated with DHT command dispatcher
#

"""
DHT Workflows Commands Module.

Provides GitHub Actions workflow management functionality.
"""

import shutil
import subprocess
from pathlib import Path

import yaml

from .common_utils import find_project_root
from .dhtl_error_handling import log_error, log_info, log_success, log_warning


def workflows_command(*args, **kwargs) -> int:
    """Manage GitHub Actions workflows."""
    log_info("🔄 Managing GitHub Actions workflows...")

    # Parse subcommand
    if not args:
        return list_workflows()

    subcommand = args[0]
    remaining_args = args[1:] if len(args) > 1 else []

    if subcommand == "list":
        return list_workflows()
    elif subcommand == "create":
        return create_workflow(remaining_args)
    elif subcommand == "validate":
        return validate_workflows(remaining_args)
    elif subcommand == "enable":
        return enable_workflow(remaining_args)
    elif subcommand == "disable":
        return disable_workflow(remaining_args)
    else:
        log_error(f"Unknown workflows subcommand: {subcommand}")
        show_workflows_help()
        return 1


def show_workflows_help():
    """Show workflows command help."""
    print("""
Workflows Command - GitHub Actions management

Usage: dhtl workflows <subcommand> [options]

Subcommands:
  list                List all workflows
  create <type>       Create a new workflow
  validate [file]     Validate workflow syntax
  enable <workflow>   Enable a workflow
  disable <workflow>  Disable a workflow

Workflow types:
  python      Python CI workflow (test, lint, build)
  node        Node.js CI workflow
  docker      Docker build workflow
  release     Release automation workflow

Examples:
  dhtl workflows create python
  dhtl workflows validate
  dhtl workflows disable test.yml
""")


def list_workflows() -> int:
    """List all GitHub Actions workflows."""
    project_root = find_project_root()
    workflows_dir = project_root / ".github" / "workflows"

    if not workflows_dir.exists():
        log_warning("No .github/workflows directory found")
        return 0

    workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

    if not workflows:
        log_info("No workflows found")
        return 0

    log_info(f"Found {len(workflows)} workflow(s):")

    for workflow_path in sorted(workflows):
        # Check if disabled
        disabled = workflow_path.name.startswith("disabled-") or workflow_path.name.endswith(".disabled")

        # Try to read workflow name
        try:
            with open(workflow_path) as f:
                data = yaml.safe_load(f)
                name = data.get("name", workflow_path.stem)
        except Exception:
            name = workflow_path.stem

        status = "🔴 disabled" if disabled else "🟢 enabled"
        log_info(f"  {status} {workflow_path.name:<30} {name}")

    return 0


def create_workflow(args: list[str]) -> int:
    """Create a new workflow."""
    if not args:
        log_error("No workflow type specified")
        log_info("Available types: python, node, docker, release")
        return 1

    workflow_type = args[0]
    project_root = find_project_root()
    workflows_dir = project_root / ".github" / "workflows"

    # Create workflows directory
    workflows_dir.mkdir(parents=True, exist_ok=True)

    if workflow_type == "python":
        return create_python_workflow(workflows_dir)
    elif workflow_type == "node":
        return create_node_workflow(workflows_dir)
    elif workflow_type == "docker":
        return create_docker_workflow(workflows_dir)
    elif workflow_type == "release":
        return create_release_workflow(workflows_dir)
    else:
        log_error(f"Unknown workflow type: {workflow_type}")
        log_info("Available types: python, node, docker, release")
        return 1


def create_python_workflow(workflows_dir: Path) -> int:
    """Create a Python CI workflow."""
    workflow_path = workflows_dir / "python-ci.yml"

    if workflow_path.exists():
        log_warning(f"Workflow already exists: {workflow_path}")
        return 1

    workflow_content = """name: Python CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v4

    - name: Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        uv venv
        uv sync --all-extras --dev

    - name: Lint with ruff
      run: |
        uv run ruff check .
        uv run ruff format --check .

    - name: Type check with mypy
      run: uv run mypy .

    - name: Test with pytest
      run: uv run pytest tests/ -v --cov=. --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
"""

    workflow_path.write_text(workflow_content)
    log_success(f"Created Python CI workflow: {workflow_path}")
    return 0


def create_node_workflow(workflows_dir: Path) -> int:
    """Create a Node.js CI workflow."""
    workflow_path = workflows_dir / "node-ci.yml"

    if workflow_path.exists():
        log_warning(f"Workflow already exists: {workflow_path}")
        return 1

    workflow_content = """name: Node.js CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18.x, 20.x, 22.x]

    steps:
    - uses: actions/checkout@v4

    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Lint
      run: npm run lint

    - name: Test
      run: npm test

    - name: Build
      run: npm run build
"""

    workflow_path.write_text(workflow_content)
    log_success(f"Created Node.js CI workflow: {workflow_path}")
    return 0


def create_docker_workflow(workflows_dir: Path) -> int:
    """Create a Docker build workflow."""
    workflow_path = workflows_dir / "docker.yml"

    if workflow_path.exists():
        log_warning(f"Workflow already exists: {workflow_path}")
        return 1

    workflow_content = """name: Docker Build

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Log in to the Container registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
"""

    workflow_path.write_text(workflow_content)
    log_success(f"Created Docker build workflow: {workflow_path}")
    return 0


def create_release_workflow(workflows_dir: Path) -> int:
    """Create a release automation workflow."""
    workflow_path = workflows_dir / "release.yml"

    if workflow_path.exists():
        log_warning(f"Workflow already exists: {workflow_path}")
        return 1

    workflow_content = """name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v4

    - name: Build package
      run: |
        uv build

    - name: Create Release
      uses: softprops/action-gh-release@v2
      with:
        files: dist/*
        generate_release_notes: true
        draft: false
        prerelease: ${{ contains(github.ref, 'rc') || contains(github.ref, 'beta') || contains(github.ref, 'alpha') }}

    - name: Publish to PyPI
      env:
        UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        uv publish
"""

    workflow_path.write_text(workflow_content)
    log_success(f"Created release workflow: {workflow_path}")
    return 0


def validate_workflows(args: list[str]) -> int:
    """Validate workflow files."""
    project_root = find_project_root()
    workflows_dir = project_root / ".github" / "workflows"

    if not workflows_dir.exists():
        log_warning("No .github/workflows directory found")
        return 0

    # Check if actionlint is available
    if shutil.which("actionlint"):
        log_info("Using actionlint to validate workflows...")
        result = subprocess.run(["actionlint"], cwd=project_root)
        return result.returncode
    else:
        # Basic YAML validation
        log_info("actionlint not found, performing basic YAML validation...")

        workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        errors = 0

        for workflow_path in workflows:
            try:
                with open(workflow_path) as f:
                    yaml.safe_load(f)
                log_success(f"✓ {workflow_path.name}")
            except yaml.YAMLError as e:
                log_error(f"✗ {workflow_path.name}: {e}")
                errors += 1

        if errors == 0:
            log_success("All workflows have valid YAML syntax")
        else:
            log_error(f"Found {errors} workflow(s) with syntax errors")

        if not shutil.which("actionlint"):
            log_info("\nFor comprehensive validation, install actionlint:")
            log_info("  brew install actionlint  # macOS")
            log_info("  go install github.com/rhysd/actionlint/cmd/actionlint@latest  # Go")

        return 1 if errors > 0 else 0


def enable_workflow(args: list[str]) -> int:
    """Enable a disabled workflow."""
    if not args:
        log_error("No workflow specified")
        return 1

    workflow_name = args[0]
    project_root = find_project_root()
    workflows_dir = project_root / ".github" / "workflows"

    # Find disabled workflow
    disabled_path = None
    if (workflows_dir / f"disabled-{workflow_name}").exists():
        disabled_path = workflows_dir / f"disabled-{workflow_name}"
        enabled_path = workflows_dir / workflow_name
    elif (workflows_dir / f"{workflow_name}.disabled").exists():
        disabled_path = workflows_dir / f"{workflow_name}.disabled"
        enabled_path = workflows_dir / workflow_name.replace(".disabled", "")
    else:
        log_error(f"Disabled workflow not found: {workflow_name}")
        return 1

    # Rename to enable
    disabled_path.rename(enabled_path)
    log_success(f"Enabled workflow: {enabled_path.name}")
    return 0


def disable_workflow(args: list[str]) -> int:
    """Disable a workflow."""
    if not args:
        log_error("No workflow specified")
        return 1

    workflow_name = args[0]
    project_root = find_project_root()
    workflows_dir = project_root / ".github" / "workflows"

    # Find workflow
    workflow_path = workflows_dir / workflow_name
    if not workflow_path.exists():
        log_error(f"Workflow not found: {workflow_name}")
        return 1

    # Rename to disable
    disabled_path = workflows_dir / f"disabled-{workflow_name}"
    workflow_path.rename(disabled_path)
    log_success(f"Disabled workflow: {workflow_name}")
    return 0


# For backward compatibility
def placeholder_command(*args, **kwargs) -> int:
    """Placeholder command implementation."""
    return workflows_command(*args, **kwargs)


# Export command functions
__all__ = ["workflows_command", "placeholder_command"]
