#!/usr/bin/env python3
"""
DHT Project Setup Flow.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created Prefect flow for setting up existing projects
# - Analyzes project structure and adds missing components
# - Supports upgrading projects to use DHT standards
# - Handles both Python and multi-language projects
#

import shutil
import subprocess
from pathlib import Path
from typing import Any

from prefect import flow, task
from prefect.task_runners import ThreadPoolTaskRunner

from ..common_utils import find_project_root
from ..dhtl_error_handling import log_error, log_info, log_success, log_warning
from .template_tasks import (
    generate_github_actions_task,
    generate_gitignore_task,
    generate_pre_commit_config_task,
    write_file_task,
)


@task(name="analyze_project", description="Analyze existing project structure")
def analyze_project_task(project_path: Path) -> dict[str, Any]:
    """Analyze an existing project to determine what's needed.

    Args:
        project_path: Path to the project

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "has_git": (project_path / ".git").exists(),
        "has_pyproject": (project_path / "pyproject.toml").exists(),
        "has_setup_py": (project_path / "setup.py").exists(),
        "has_requirements": (project_path / "requirements.txt").exists(),
        "has_package_json": (project_path / "package.json").exists(),
        "has_gitignore": (project_path / ".gitignore").exists(),
        "has_precommit": (project_path / ".pre-commit-config.yaml").exists(),
        "has_github_actions": (project_path / ".github" / "workflows").exists(),
        "has_venv": any((project_path / name).exists() for name in [".venv", "venv", "env"]),
        "has_dhtconfig": (project_path / ".dhtconfig").exists(),
        "python_files": list(project_path.rglob("*.py")),
        "is_python_project": False,
        "is_node_project": False,
        "project_type": "unknown",
    }

    # Determine project type
    if (
        analysis["has_pyproject"]
        or analysis["has_setup_py"]
        or analysis["has_requirements"]
        or analysis["python_files"]
    ):
        analysis["is_python_project"] = True
        analysis["project_type"] = "python"

    if analysis["has_package_json"]:
        analysis["is_node_project"] = True
        if analysis["is_python_project"]:
            analysis["project_type"] = "mixed"
        else:
            analysis["project_type"] = "node"

    return analysis


@task(name="detect_python_version", description="Detect Python version for project")
def detect_python_version_task(project_path: Path) -> str:
    """Detect the Python version used in the project.

    Args:
        project_path: Path to the project

    Returns:
        Python version string
    """
    # Check .python-version file
    python_version_file = project_path / ".python-version"
    if python_version_file.exists():
        return python_version_file.read_text().strip()

    # Check pyproject.toml
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib

            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
                requires_python = data.get("project", {}).get("requires-python", "")
                if requires_python:
                    # Extract version from >=3.10 format
                    if ">=" in requires_python:
                        return str(requires_python.split(">=")[1].strip())
        except Exception:
            pass

    # Default to current Python version
    import sys

    return f"{sys.version_info.major}.{sys.version_info.minor}"


@task(name="create_dhtconfig", description="Create .dhtconfig file")
def create_dhtconfig_task(
    project_path: Path, project_name: str, project_type: str, python_version: str | None = None
) -> bool:
    """Create .dhtconfig file for project.

    Args:
        project_path: Path to the project
        project_name: Name of the project
        project_type: Type of project (python, node, mixed)
        python_version: Python version (if applicable)

    Returns:
        True if successful
    """
    config_content = f"""# DHT Configuration
project_name: {project_name}
project_type: {project_type}
"""

    if python_version and project_type in ["python", "mixed"]:
        config_content += f"python_version: {python_version}\n"

    config_content += """created_with: dht
version: 1.0.0
"""

    try:
        config_file = project_path / ".dhtconfig"
        config_file.write_text(config_content)
        return True
    except Exception as e:
        log_error(f"Failed to create .dhtconfig: {e}")
        return False


@task(name="upgrade_gitignore", description="Upgrade or create .gitignore")
def upgrade_gitignore_task(project_path: Path, project_type: str) -> bool:
    """Upgrade or create .gitignore file.

    Args:
        project_path: Path to the project
        project_type: Type of project

    Returns:
        True if successful
    """
    gitignore_path = project_path / ".gitignore"

    # Read existing content if any
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text()

    # Generate new content based on project type
    new_sections = []

    if project_type in ["python", "mixed"]:
        python_gitignore = generate_gitignore_task()
        if "# Python" not in existing_content and "__pycache__" not in existing_content:
            new_sections.append("# Python\n" + python_gitignore)

    if project_type in ["node", "mixed"]:
        node_gitignore = """# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn/cache
.yarn/unplugged
.yarn/build-state.yml
.pnp.*
"""
        if "node_modules" not in existing_content:
            new_sections.append(node_gitignore)

    # Add DHT-specific ignores
    dht_ignores = """# DHT
.dht/
.dhtcache/
"""
    if ".dht/" not in existing_content:
        new_sections.append(dht_ignores)

    # Combine content
    if new_sections:
        if existing_content and not existing_content.endswith("\n"):
            existing_content += "\n"

        final_content = existing_content + "\n".join(new_sections)

        try:
            gitignore_path.write_text(final_content)
            return True
        except Exception as e:
            log_error(f"Failed to update .gitignore: {e}")
            return False

    return True


@flow(name="setup_project", description="Setup DHT for an existing project", task_runner=ThreadPoolTaskRunner())
def setup_project_flow(project_path: Path | None = None, force: bool = False) -> bool:
    """Setup DHT for an existing project.

    Args:
        project_path: Path to the project (uses current directory if None)
        force: Force setup even if .dhtconfig exists

    Returns:
        True if successful
    """
    # Find project root
    if project_path is None:
        project_path = find_project_root()
    else:
        project_path = Path(project_path).resolve()

    log_info(f"🔧 Setting up DHT for project at: {project_path}")

    # Analyze project
    analysis = analyze_project_task(project_path)

    # Check if already setup
    if analysis["has_dhtconfig"] and not force:
        log_warning("Project already has .dhtconfig file")
        log_info("Use --force to reconfigure")
        return False

    # Determine project name
    project_name = project_path.name

    # Get project type
    project_type = analysis["project_type"]
    if project_type == "unknown":
        log_error("Unable to determine project type")
        log_info("Please ensure project has recognizable structure (pyproject.toml, package.json, etc.)")
        return False

    log_info(f"📊 Detected project type: {project_type}")

    # Setup based on project type
    python_version = None
    if project_type in ["python", "mixed"]:
        python_version = detect_python_version_task(project_path)
        log_info(f"🐍 Python version: {python_version}")

        # Create virtual environment if needed
        if not analysis["has_venv"]:
            log_info("Creating virtual environment...")
            if shutil.which("uv"):
                subprocess.run(["uv", "venv"], cwd=project_path)
            else:
                import sys

                subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=project_path)

    # Create .dhtconfig
    log_info("📝 Creating .dhtconfig...")
    create_dhtconfig_task(project_path, project_name, project_type, python_version)

    # Upgrade .gitignore
    log_info("📄 Updating .gitignore...")
    upgrade_gitignore_task(project_path, project_type)

    # Add pre-commit if missing
    if not analysis["has_precommit"] and project_type in ["python", "mixed"]:
        log_info("🔧 Adding pre-commit configuration...")
        precommit_content = generate_pre_commit_config_task()
        write_file_task(project_path / ".pre-commit-config.yaml", precommit_content)

    # Add GitHub Actions if missing
    if not analysis["has_github_actions"] and analysis["has_git"]:
        log_info("🚀 Adding GitHub Actions workflow...")
        (project_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        ci_content = generate_github_actions_task()
        write_file_task(project_path / ".github" / "workflows" / "ci.yml", ci_content)

    # Initialize git if needed
    if not analysis["has_git"]:
        log_info("📚 Initializing git repository...")
        subprocess.run(["git", "init"], cwd=project_path)

    log_success("✅ DHT setup completed successfully!")
    log_info("📝 Next steps:")

    if project_type in ["python", "mixed"]:
        log_info("  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
        if shutil.which("uv"):
            log_info("  uv sync --dev")
        else:
            log_info("  pip install -r requirements.txt")
        log_info("  pre-commit install")

    log_info("  dhtl test    # Run tests")
    log_info("  dhtl lint    # Check code quality")
    log_info("  dhtl build   # Build project")

    return True
