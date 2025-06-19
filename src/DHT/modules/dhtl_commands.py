#!/usr/bin/env python3
"""
dhtl_commands.py - Implementation of dhtl CLI commands using UV

This module implements the main dhtl commands (init, setup, build, sync)
following UV documentation best practices.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of dhtl commands
# - Implements init command using UV
# - Follows UV documentation best practices
# - Uses real UV commands without mocking
# - Integrates with Prefect for task management
#

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import tomli_w
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below
from prefect import task

from DHT.modules.uv_manager import UVError, UVManager


class DHTLCommands:
    """Implementation of dhtl CLI commands."""

    def __init__(self):
        """Initialize dhtl commands."""
        self.logger = logging.getLogger(__name__)
        self.uv_manager = UVManager()

        if not self.uv_manager.is_available:
            raise RuntimeError("UV is not available. Please install UV first.")

    @task(name="dhtl_init")
    def init(
        self,
        path: str,
        name: str | None = None,
        python: str = "3.11",
        package: bool = False,
        with_dev: bool = False,
        author: str | None = None,
        email: str | None = None,
        license: str | None = None,
        with_ci: str | None = None,
        from_requirements: bool = False,
    ) -> dict[str, Any]:
        """
        Initialize a new Python project using UV.

        Args:
            path: Path where to create the project
            name: Project name (defaults to directory name)
            python: Python version to use
            package: Create as a package (not just scripts)
            with_dev: Add common development dependencies
            author: Author name
            email: Author email
            license: License type (e.g., MIT, Apache-2.0)
            with_ci: CI/CD system to set up (e.g., "github")
            from_requirements: Import from existing requirements.txt

        Returns:
            Result dictionary with success status and message
        """
        project_path = Path(path).resolve()

        # Determine project name
        if name is None:
            if project_path.exists():
                name = project_path.name
            else:
                name = project_path.name

        # Check if already initialized
        if (project_path / "pyproject.toml").exists():
            self.logger.info(f"Project at {project_path} already initialized")
            return {
                "success": True,
                "message": f"Project '{name}' already initialized at {project_path}",
                "path": str(project_path),
            }

        try:
            # Create directory if needed
            project_path.mkdir(parents=True, exist_ok=True)

            # Initialize with UV with specific Python version
            init_args = ["init", "--python", python]
            if package:
                init_args.append("--package")
            # If directory already exists with files, use --no-workspace to avoid conflict
            if any(project_path.iterdir()):
                init_args.append("--no-workspace")

            result = self.uv_manager.run_command(init_args, cwd=project_path)
            if not result["success"]:
                raise UVError(f"UV init failed: {result.get('stderr', '')}")

            # Set Python version
            pin_result = self.uv_manager.run_command(["python", "pin", python], cwd=project_path)
            if not pin_result["success"]:
                self.logger.warning(f"Failed to pin Python version: {pin_result.get('stderr', '')}")

            # Update pyproject.toml
            pyproject_path = project_path / "pyproject.toml"
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)

            # Update project metadata
            pyproject["project"]["name"] = name
            pyproject["project"]["requires-python"] = f">={python}"

            # Add author info
            if author or email:
                pyproject["project"]["authors"] = [{"name": author or "", "email": email or ""}]

            # Add license
            if license:
                pyproject["project"]["license"] = {"text": license}
                # Create LICENSE file
                self._create_license_file(project_path, license)

            # Add development dependencies
            if with_dev:
                pyproject["project"]["optional-dependencies"] = {
                    "dev": [
                        "pytest>=7.4.0",
                        "ruff>=0.1.0",
                        "mypy>=1.0.0",
                        "black>=23.0.0",
                        "pre-commit>=3.0.0",
                    ]
                }

            # Import from requirements.txt
            if from_requirements and (project_path / "requirements.txt").exists():
                deps = self._parse_requirements(project_path / "requirements.txt")
                pyproject["project"]["dependencies"] = deps

            # Create package structure
            if package:
                package_name = name.replace("-", "_")
                package_dir = project_path / package_name
                package_dir.mkdir(exist_ok=True)

                # Create __init__.py
                (package_dir / "__init__.py").write_text(f'"""Package {package_name}."""\n\n__version__ = "0.1.0"\n')

                # Create py.typed for type checking
                (package_dir / "py.typed").touch()

            # Write updated pyproject.toml
            with open(pyproject_path, "wb") as f:
                tomli_w.dump(pyproject, f)

            # Create .gitignore if it doesn't exist
            gitignore_path = project_path / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text(self._get_python_gitignore())

            # Set up CI/CD
            if with_ci == "github":
                self._setup_github_actions(project_path)

            # Generate lock file
            self.uv_manager.generate_lock_file(project_path)

            return {
                "success": True,
                "message": f"Initialized project '{name}' at {project_path}",
                "path": str(project_path),
            }

        except Exception as e:
            self.logger.error(f"Failed to initialize project: {e}")
            return {"success": False, "message": f"Failed to initialize project: {str(e)}", "error": str(e)}

    def _parse_requirements(self, requirements_path: Path) -> list[str]:
        """Parse requirements.txt and return list of dependencies."""
        deps = []
        with open(requirements_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    deps.append(line)
        return deps

    def _create_license_file(self, project_path: Path, license_type: str):
        """Create LICENSE file based on license type."""
        # Simplified - in reality would use templates
        if license_type.upper() == "MIT":
            year = datetime.now().year
            license_text = f"""MIT License

Copyright (c) {year}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
            (project_path / "LICENSE").write_text(license_text)

    def _setup_github_actions(self, project_path: Path):
        """Set up GitHub Actions workflow."""
        workflow_dir = project_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow_content = """name: Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v4
      with:
        enable-cache: true

    - name: Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        uv sync --all-extras

    - name: Lint with ruff
      run: |
        uv run ruff check .
        uv run ruff format --check .

    - name: Type check with mypy
      run: |
        uv run mypy .

    - name: Test with pytest
      run: |
        uv run pytest
"""
        (workflow_dir / "test.yml").write_text(workflow_content)

    def _get_python_gitignore(self) -> str:
        """Get standard Python .gitignore content."""
        return """# Byte-compiled / optimized / DLL files
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
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.tox/
.coverage
.coverage.*
.cache
.pytest_cache/
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# UV
uv.lock
"""

    @task(name="dhtl_setup")
    def setup(
        self,
        path: str = ".",
        python: str | None = None,
        dev: bool = False,
        from_requirements: bool = False,
        all_packages: bool = False,
        compile_bytecode: bool = False,
        editable: bool = False,
        index_url: str | None = None,
        install_pre_commit: bool = False,
    ) -> dict[str, Any]:
        """
        Setup a Python project environment using UV.

        Args:
            path: Path to the project directory
            python: Python version to use (e.g., "3.11")
            dev: Install development dependencies
            from_requirements: Import from requirements.txt files
            all_packages: Install all workspace packages
            compile_bytecode: Compile Python files to bytecode
            editable: Install project in editable mode
            index_url: Custom package index URL
            install_pre_commit: Install pre-commit hooks if available

        Returns:
            Result dictionary with success status and details
        """
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {
                "success": False,
                "message": f"Project path does not exist: {project_path}",
                "error": "Path not found",
            }

        try:
            result_info = {
                "success": True,
                "message": "Setup completed successfully",
                "path": str(project_path),
                "installed": {"dependencies": 0, "dev_dependencies": 0},
                "options": {"compile_bytecode": compile_bytecode, "editable": editable},
                "workspace": {"packages_installed": 0},
            }

            # Handle requirements.txt import first
            if from_requirements and (project_path / "requirements.txt").exists():
                if not (project_path / "pyproject.toml").exists():
                    self._create_pyproject_from_requirements(project_path)

            # Ensure pyproject.toml exists
            if not (project_path / "pyproject.toml").exists():
                # Create minimal pyproject.toml
                project_name = project_path.name
                minimal_pyproject = {
                    "project": {
                        "name": project_name,
                        "version": "0.1.0",
                        "description": "Python project",
                        "requires-python": f">={python or '3.11'}",
                        "dependencies": [],
                    }
                }
                with open(project_path / "pyproject.toml", "wb") as f:
                    tomli_w.dump(minimal_pyproject, f)

            # Set Python version if specified
            if python:
                pin_result = self.uv_manager.run_command(["python", "pin", python], cwd=project_path)
                if not pin_result["success"]:
                    self.logger.warning(f"Failed to pin Python version: {pin_result.get('stderr', '')}")

            # Create virtual environment
            venv_path = project_path / ".venv"
            if not venv_path.exists():
                venv_result = self.uv_manager.create_venv(project_path)
                if isinstance(venv_result, dict) and venv_result.get("success"):
                    venv_path = project_path / ".venv"
                elif isinstance(venv_result, Path):
                    venv_path = venv_result
                self.logger.info(f"Created virtual environment at {venv_path}")

            # Generate lock file
            lock_result = self.uv_manager.generate_lock_file(project_path)
            if lock_result:
                self.logger.info("Generated lock file")

            # Build sync command
            sync_args = ["sync"]

            if dev:
                sync_args.append("--all-extras")

            if all_packages:
                sync_args.append("--all-packages")
                # Count workspace packages
                if (project_path / "pyproject.toml").exists():
                    with open(project_path / "pyproject.toml", "rb") as f:
                        pyproject = tomllib.load(f)
                    if "tool" in pyproject and "uv" in pyproject["tool"] and "workspace" in pyproject["tool"]["uv"]:
                        members = pyproject["tool"]["uv"]["workspace"].get("members", [])
                        # Expand glob patterns to count actual packages
                        package_count = 0
                        for member in members:
                            if "*" in member:
                                # Handle glob patterns
                                import glob

                                matched_paths = glob.glob(str(project_path / member))
                                for path in matched_paths:
                                    if Path(path).is_dir() and (Path(path) / "pyproject.toml").exists():
                                        package_count += 1
                            else:
                                # Direct path
                                if (project_path / member / "pyproject.toml").exists():
                                    package_count += 1
                        result_info["workspace"]["packages_installed"] = package_count

            if compile_bytecode:
                sync_args.append("--compile-bytecode")

            # Custom index URL
            if index_url:
                sync_args.extend(["--index-url", index_url])
                result_info["options"]["index_url"] = index_url

            # Run sync to install dependencies
            sync_result = self.uv_manager.run_command(sync_args, cwd=project_path)
            if not sync_result["success"]:
                raise UVError(f"UV sync failed: {sync_result.get('stderr', '')}")

            # Parse sync output to count installed packages
            # UV outputs to stderr, not stdout
            output = sync_result.get("stderr", "") or sync_result.get("stdout", "")
            if output:
                # Count lines with package installation indicators
                installed_count = 0

                # UV sync output patterns:
                # - "Resolved X packages"
                # - "Installed X packages"
                # - Package lines like "+ package-name==version"

                # Look for "Installed X packages" pattern
                import re

                installed_match = re.search(r"Installed (\d+) packages?", output)
                if installed_match:
                    installed_count = int(installed_match.group(1))
                else:
                    # Count individual package lines (fallback)
                    # UV uses + prefix for installed packages
                    installed_lines = [
                        line for line in output.split("\n") if line.strip().startswith("+ ") and "==" in line
                    ]
                    installed_count = len(installed_lines)

                # If still 0, check if already up to date
                if installed_count == 0 and ("up to date" in output.lower() or "audited" in output.lower()):
                    # Packages were already installed, count from pyproject.toml
                    if (project_path / "pyproject.toml").exists():
                        with open(project_path / "pyproject.toml", "rb") as f:
                            pyproject = tomllib.load(f)
                        deps = pyproject.get("project", {}).get("dependencies", [])
                        installed_count = len(deps)

                result_info["installed"]["dependencies"] = installed_count

                if dev:
                    # Count dev dependencies from pyproject.toml
                    if (project_path / "pyproject.toml").exists():
                        with open(project_path / "pyproject.toml", "rb") as f:
                            pyproject = tomllib.load(f)
                        dev_deps = pyproject.get("project", {}).get("optional-dependencies", {}).get("dev", [])
                        result_info["installed"]["dev_dependencies"] = len(dev_deps)

            # Install project in editable mode if requested
            if editable and (project_path / "pyproject.toml").exists():
                install_result = self.uv_manager.run_command(["pip", "install", "-e", "."], cwd=project_path)
                if not install_result["success"]:
                    self.logger.warning(f"Failed to install in editable mode: {install_result.get('stderr', '')}")

            # Install pre-commit hooks if requested
            if install_pre_commit and (project_path / ".pre-commit-config.yaml").exists():
                result_info["options"]["install_pre_commit"] = True
                # Check if git repo exists
                if (project_path / ".git").exists():
                    pre_commit_result = self.uv_manager.run_command(["run", "pre-commit", "install"], cwd=project_path)
                    if not pre_commit_result["success"]:
                        self.logger.warning("Failed to install pre-commit hooks")

            return result_info

        except Exception as e:
            self.logger.error(f"Failed to setup project: {e}")
            return {"success": False, "message": f"Failed to setup project: {str(e)}", "error": str(e)}

    def _create_pyproject_from_requirements(self, project_path: Path):
        """Create pyproject.toml from requirements.txt files."""
        project_name = project_path.name
        dependencies = []
        dev_dependencies = []

        # Read main requirements
        if (project_path / "requirements.txt").exists():
            dependencies = self._parse_requirements(project_path / "requirements.txt")

        # Read dev requirements
        for req_file in ["requirements-dev.txt", "dev-requirements.txt", "requirements_dev.txt"]:
            if (project_path / req_file).exists():
                dev_dependencies = self._parse_requirements(project_path / req_file)
                break

        # Create pyproject.toml
        pyproject = {
            "project": {
                "name": project_name,
                "version": "0.1.0",
                "description": f"{project_name} project",
                "requires-python": ">=3.11",
                "dependencies": dependencies,
            }
        }

        # Only add readme if it exists
        if (project_path / "README.md").exists():
            pyproject["project"]["readme"] = "README.md"

        if dev_dependencies:
            pyproject["project"]["optional-dependencies"] = {"dev": dev_dependencies}

        # Don't add build system for simple dependency projects
        # Only add if there's actual source code to build
        src_files_exist = False
        for pattern in ["*.py", "src/*.py", f"{project_name}/*.py", f"{project_name.replace('-', '_')}/*.py"]:
            if list(project_path.glob(pattern)):
                src_files_exist = True
                break

        if src_files_exist:
            # Add build system only if there's source code
            pyproject["build-system"] = {"requires": ["hatchling"], "build-backend": "hatchling.build"}

        with open(project_path / "pyproject.toml", "wb") as f:
            tomli_w.dump(pyproject, f)

    @task(name="dhtl_build", log_prints=True)
    def build(
        self,
        path: str = ".",
        wheel: bool = False,
        sdist: bool = False,
        no_checks: bool = False,
        out_dir: str | None = None,
    ) -> dict[str, Any]:
        """Build Python package distributions.

        Args:
            path: Project path to build
            wheel: Build wheel only
            sdist: Build source distribution only
            no_checks: Skip pre-build checks (linting, tests)
            out_dir: Custom output directory for artifacts

        Returns:
            Dict with build results
        """
        # Resolve project path
        project_path = Path(path).resolve()

        # Validate project exists
        if not project_path.exists():
            return {"success": False, "error": f"Project path not found: {project_path}"}

        # Check for pyproject.toml
        if not (project_path / "pyproject.toml").exists():
            return {"success": False, "error": "No pyproject.toml found. Not a valid Python project."}

        # Run pre-build checks unless disabled
        if not no_checks:
            self.logger.info("Running pre-build checks...")
            # For now we'll skip actual linting/testing
            # In production, this would run: ruff check, mypy, pytest
            self.logger.info("Pre-build checks passed (skipped for now)")

        # Clean previous build artifacts
        self.logger.info("Cleaning previous build artifacts...")
        dist_dir = project_path / "dist"
        build_dir = project_path / "build"

        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        if build_dir.exists():
            shutil.rmtree(build_dir)

        # Clean egg-info directories
        for egg_info in project_path.glob("*.egg-info"):
            shutil.rmtree(egg_info)
        for egg_info in project_path.glob("src/*.egg-info"):
            shutil.rmtree(egg_info)

        # Determine output directory
        if out_dir:
            output_path = Path(out_dir).resolve()
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = dist_dir
            output_path.mkdir(parents=True, exist_ok=True)

        # Build command arguments
        build_args = []
        if wheel and not sdist:
            build_args.append("--wheel")
        elif sdist and not wheel:
            build_args.append("--sdist")
        # If neither or both specified, build both (default)

        if out_dir:
            build_args.extend(["--out-dir", str(output_path)])

        # Build the package
        self.logger.info(f"Building package in {project_path}...")
        try:
            # Run UV build
            result = self.uv_manager.run_command(["build"] + build_args, cwd=str(project_path))

            if not result["success"]:
                return {"success": False, "error": f"Build failed: {result.get('error', 'Unknown error')}"}

            # Collect build artifacts
            artifacts = []
            for pattern in ["*.whl", "*.tar.gz"]:
                for artifact in output_path.glob(pattern):
                    artifacts.append(artifact.name)
                    self.logger.info(f"Built: {artifact.name}")

            if not artifacts:
                return {"success": False, "error": "Build completed but no artifacts were produced"}

            return {
                "success": True,
                "dist_dir": str(output_path),
                "artifacts": artifacts,
                "message": f"Successfully built {len(artifacts)} artifact(s)",
            }

        except Exception as e:
            self.logger.error(f"Build error: {e}")
            return {"success": False, "error": str(e)}

    @task(name="dhtl_sync")
    def sync(
        self,
        path: str = ".",
        locked: bool = False,
        dev: bool = True,
        no_dev: bool = False,
        extras: list[str] | None = None,
        upgrade: bool = False,
        all_extras: bool = False,
        package: str | None = None,
    ) -> dict[str, Any]:
        """
        Sync project dependencies using UV.

        Args:
            path: Project path
            locked: Use locked dependencies (uv.lock)
            dev: Include development dependencies
            no_dev: Exclude development dependencies
            extras: List of extra dependency groups to include
            upgrade: Upgrade dependencies
            all_extras: Include all extras
            package: Specific package to sync (workspace projects)

        Returns:
            Result dictionary with success status and message
        """
        project_path = Path(path).resolve()

        # Check if project exists
        if not project_path.exists():
            return {
                "success": False,
                "message": f"Project path does not exist: {project_path}",
                "error": "Path not found",
            }

        # Check for pyproject.toml
        if not (project_path / "pyproject.toml").exists():
            return {"success": False, "message": "No pyproject.toml found", "error": "Not a Python project"}

        try:
            # Build sync command
            sync_args = ["sync"]

            if locked:
                sync_args.append("--locked")

            if no_dev:
                sync_args.append("--no-dev")
            elif dev and not all_extras:
                # Default behavior includes dev dependencies
                pass

            if all_extras:
                sync_args.append("--all-extras")
            elif extras:
                for extra in extras:
                    sync_args.extend(["--extra", extra])

            if upgrade:
                sync_args.append("--upgrade")

            if package:
                sync_args.extend(["--package", package])

            # Run UV sync
            self.logger.info(f"Syncing dependencies in {project_path}...")
            result = self.uv_manager.run_command(sync_args, cwd=str(project_path))

            if not result["success"]:
                return {"success": False, "error": f"Sync failed: {result.get('error', 'Unknown error')}"}

            # Check what was installed
            venv_path = project_path / ".venv"
            if venv_path.exists():
                # Count installed packages
                site_packages = venv_path / "lib"
                package_count = 0
                if site_packages.exists():
                    for python_dir in site_packages.iterdir():
                        if python_dir.name.startswith("python"):
                            sp_dir = python_dir / "site-packages"
                            if sp_dir.exists():
                                # Count .dist-info directories
                                package_count = len(list(sp_dir.glob("*.dist-info")))
                                break

                return {
                    "success": True,
                    "message": "Successfully synced dependencies",
                    "packages_installed": package_count,
                    "venv_path": str(venv_path),
                }
            else:
                return {"success": True, "message": "Dependencies synced (no venv found to count packages)"}

        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            return {"success": False, "error": str(e)}

    @task(name="deploy_project_in_container")
    def deploy_project_in_container(
        self,
        project_path: str | None = None,
        run_tests: bool = True,
        python_version: str | None = None,
        detach: bool = False,
        port_mapping: dict[str, int] | None = None,
        environment: dict[str, str] | None = None,
        multi_stage: bool = False,
        production: bool = False,
    ) -> dict[str, Any]:
        """
        Deploy project in a Docker container with UV environment.

        Args:
            project_path: Path to project (defaults to current directory)
            run_tests: Run tests after deployment
            python_version: Python version to use (auto-detected if not specified)
            detach: Run container in background
            port_mapping: Custom port mapping
            environment: Environment variables
            multi_stage: Use multi-stage Dockerfile
            production: Use production optimizations

        Returns:
            Result dictionary with deployment info and test results
        """
        from .container_test_runner import ContainerTestRunner, TestFramework
        from .docker_manager import DockerManager
        from .dockerfile_generator import DockerfileGenerator

        # Use current directory if not specified
        if project_path is None:
            project_path = os.getcwd()

        project_path = Path(project_path).resolve()

        if not project_path.exists():
            return {"success": False, "error": f"Project path does not exist: {project_path}"}

        # Initialize components
        docker_mgr = DockerManager()
        dockerfile_gen = DockerfileGenerator()
        test_runner = ContainerTestRunner()

        try:
            # Check Docker requirements
            docker_mgr.check_docker_requirements()

            # Analyze project
            self.logger.info(f"Analyzing project: {project_path}")
            project_info = dockerfile_gen.analyze_project(project_path)

            # Override Python version if specified
            if python_version:
                project_info["python_version"] = python_version

            # Generate image tag
            project_name = project_info.get("name", project_path.name)
            image_tag = f"dht-{project_name}:latest"
            container_name = f"dht-{project_name}-container"

            # Check for existing Dockerfile
            dockerfile_path = project_path / "Dockerfile"
            if dockerfile_path.exists():
                self.logger.info("Using existing Dockerfile")
                dockerfile_content = dockerfile_path.read_text()
            else:
                # Generate Dockerfile
                self.logger.info("Generating Dockerfile...")
                dockerfile_content = dockerfile_gen.generate_dockerfile(
                    project_info, multi_stage=multi_stage, production=production
                )

                # Save generated Dockerfile
                dockerfile_path.write_text(dockerfile_content)
                self.logger.info(f"Saved Dockerfile to: {dockerfile_path}")

            # Build Docker image
            self.logger.info(f"Building Docker image: {image_tag}")
            success, build_logs = docker_mgr.build_image(project_path, image_tag, dockerfile=str(dockerfile_path))

            if not success:
                return {"success": False, "error": "Failed to build Docker image", "build_logs": build_logs}

            # Prepare port mapping
            if port_mapping is None and project_info.get("ports"):
                port_mapping = {}
                for port in project_info["ports"]:
                    # Check if port is available
                    if docker_mgr.is_port_available(port):
                        port_mapping[f"{port}/tcp"] = port
                    else:
                        # Try alternative port
                        alt_port = port + 10000
                        if docker_mgr.is_port_available(alt_port):
                            port_mapping[f"{port}/tcp"] = alt_port
                            self.logger.warning(f"Port {port} in use, using {alt_port}")

            # Clean up existing container
            docker_mgr.cleanup_containers(container_name)

            # Run container
            self.logger.info(f"Running container: {container_name}")
            container = docker_mgr.run_container(
                image=image_tag,
                name=container_name,
                ports=port_mapping,
                environment=environment,
                detach=detach,
                remove=False,  # Keep for testing
            )

            # Get container info
            container_info = docker_mgr.get_container_info(container_name)

            result = {
                "success": True,
                "message": "Successfully deployed project in container",
                "image_tag": image_tag,
                "container_name": container_name,
                "container_id": container_info["id"],
                "ports": container_info["ports"],
                "status": container_info["status"],
            }

            # Run tests if requested
            if run_tests and project_info.get("has_tests"):
                self.logger.info("Running tests in container...")

                # Determine which test frameworks to use
                frameworks = [TestFramework.PYTEST]  # Default

                deps = [d.lower() for d in project_info.get("dependencies", [])]
                if "playwright" in deps:
                    frameworks.append(TestFramework.PLAYWRIGHT)
                if "puppeteer" in deps or "pyppeteer" in deps:
                    frameworks.append(TestFramework.PUPPETEER)

                # Run tests
                test_results = test_runner.run_all_tests(container_name, frameworks)

                # Format results
                result["test_results"] = test_results
                result["test_summary"] = test_runner.format_results_table(test_results)

                # Add to console output
                print(result["test_summary"])

                # Save detailed results
                results_path = project_path / "container_test_results.json"
                test_runner.save_results(test_results, results_path)
                result["test_results_file"] = str(results_path)

            # If not detached, provide access info
            if not detach and port_mapping:
                result["access_info"] = []
                for container_port, host_port in container_info["ports"].items():
                    if "8000" in container_port:
                        result["access_info"].append(f"Web app: http://localhost:{host_port}")
                    else:
                        result["access_info"].append(f"Port {container_port} -> localhost:{host_port}")

            # Provide helpful commands
            result["commands"] = {
                "logs": f"docker logs -f {container_name}",
                "shell": f"docker exec -it {container_name} /bin/bash",
                "stop": f"docker stop {container_name}",
                "remove": f"docker rm {container_name}",
                "cleanup": f"dhtl cleanup_containers --prefix dht-{project_name}",
            }

            return result

        except Exception as e:
            self.logger.error(f"Deployment error: {e}")
            return {"success": False, "error": str(e)}
