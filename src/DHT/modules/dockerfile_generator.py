#!/usr/bin/env python3
"""
Dockerfile Generator Module.  Analyzes Python projects and generates appropriate Dockerfiles based on project type, dependencies, and requirements.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Dockerfile Generator Module.

Analyzes Python projects and generates appropriate Dockerfiles
based on project type, dependencies, and requirements.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of DockerfileGenerator class
# - Implements project type detection (web, cli, library)
# - Implements Python version detection from project files
# - Implements Dockerfile generation with templates
# - Adds support for multi-stage builds
#

import logging
import re
from enum import Enum
from pathlib import Path
from typing import Any, cast

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below
from prefect import task


class ProjectType(Enum):
    """Enumeration of project types."""

    WEB = "web"
    CLI = "cli"
    LIBRARY = "library"
    UNKNOWN = "unknown"


class DockerfileGenerator:
    """Generates Dockerfiles based on project analysis."""

    def __init__(self) -> None:
        """Initialize DockerfileGenerator."""
        self.logger = logging.getLogger(__name__)
        self.templates = self._init_templates()

    def _init_templates(self) -> dict[str, str]:
        """Initialize Dockerfile templates."""
        return {
            "base": """FROM python:{python_version}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    {system_deps} \\
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN uv sync --all-extras

# Build project
RUN uv build

{expose_ports}

# Set entry point
CMD {cmd}
""",
            "multistage": """# Build stage
FROM python:{python_version}-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies and build
RUN uv sync --all-extras
RUN uv build

# Runtime stage
FROM python:{python_version}-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    {system_deps} \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy UV and built artifacts from builder
COPY --from=builder /root/.cargo /home/appuser/.cargo
COPY --from=builder /app /app

# Set ownership
RUN chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser
ENV PATH="/home/appuser/.cargo/bin:$PATH"

WORKDIR /app

{expose_ports}

# Set entry point
CMD {cmd}
""",
        }

    def analyze_project(self, project_path: Path) -> dict[str, Any]:
        """
        Analyze project to determine configuration.

        Args:
            project_path: Path to project

        Returns:
            Project information dict
        """
        self.logger.info(f"Analyzing project: {project_path}")

        project_info = {
            "path": project_path,
            "type": self.detect_project_type(project_path),
            "python_version": self.detect_python_version(project_path),
            "main_entry": None,
            "dependencies": [],
            "system_deps": [],
            "has_tests": self._has_tests(project_path),
            "has_frontend": self._has_frontend(project_path),
            "ports": [],
        }

        # Find main entry point
        entry_points = self.find_entry_points(project_path)
        if entry_points:
            project_info["main_entry"] = entry_points[0]

        # Get dependencies
        project_info["dependencies"] = self._get_dependencies(project_path)

        # Determine system dependencies
        project_info["system_deps"] = self._get_system_deps(project_info["dependencies"])

        # Determine ports for web apps
        if project_info["type"] == ProjectType.WEB:
            project_info["ports"] = self._detect_ports(project_path, project_info["main_entry"])

        return project_info

    def detect_project_type(self, project_path: Path) -> ProjectType:
        """
        Detect the type of Python project.

        Args:
            project_path: Path to project

        Returns:
            Project type
        """
        # Check for web frameworks
        web_indicators = ["fastapi", "flask", "django", "starlette", "aiohttp", "tornado", "bottle", "pyramid", "sanic"]

        # Check for CLI frameworks
        cli_indicators = ["click", "typer", "argparse", "fire"]

        # Check dependencies
        deps = self._get_dependencies(project_path)
        deps_lower = [d.lower() for d in deps]

        # Check for web app
        for indicator in web_indicators:
            if indicator in deps_lower:
                return ProjectType.WEB

        # Check file content
        for py_file in project_path.rglob("*.py"):
            if py_file.stat().st_size > 1_000_000:  # Skip large files
                continue

            try:
                content = py_file.read_text()

                # Web app patterns
                if any(
                    pattern in content
                    for pattern in [
                        "from fastapi import",
                        "from flask import",
                        "from django",
                        "app = FastAPI()",
                        "app = Flask(",
                    ]
                ):
                    return ProjectType.WEB

                # CLI patterns
                if any(
                    pattern in content
                    for pattern in [
                        "@click.command",
                        "@click.group",
                        "import click",
                        "from typer import",
                        "ArgumentParser()",
                    ]
                ):
                    return ProjectType.CLI

            except Exception:
                continue

        # Check for CLI in dependencies
        for indicator in cli_indicators:
            if indicator in deps_lower:
                return ProjectType.CLI

        # Check if it's a library (has setup.py or is installable)
        if (project_path / "setup.py").exists() or (project_path / "pyproject.toml").exists():
            # If no main entry, it's likely a library
            if not list(project_path.glob("main.py")) and not list(project_path.glob("app.py")):
                return ProjectType.LIBRARY

        return ProjectType.UNKNOWN

    def detect_python_version(self, project_path: Path) -> str:
        """
        Detect Python version requirement.

        Args:
            project_path: Path to project

        Returns:
            Python version string
        """
        # Check .python-version
        python_version_file = project_path / ".python-version"
        if python_version_file.exists():
            version = python_version_file.read_text().strip()
            # Extract major.minor
            match = re.match(r"(\d+\.\d+)", version)
            if match:
                return match.group(1)

        # Check pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                with open(pyproject_file, "rb") as f:
                    data = tomllib.load(f)

                # Check requires-python
                requires_python = data.get("project", {}).get("requires-python", "")
                if requires_python:
                    # Extract version from >=3.11, ==3.11, etc.
                    match = re.search(r"(\d+\.\d+)", requires_python)
                    if match:
                        return match.group(1)

            except Exception as e:
                self.logger.warning(f"Failed to parse pyproject.toml: {e}")

        # Default to Python 3.11
        return "3.11"

    def find_entry_points(self, project_path: Path) -> list[str]:
        """
        Find potential entry points in project.

        Args:
            project_path: Path to project

        Returns:
            List of entry point files
        """
        entry_points = []

        # Common entry point names
        common_names = ["main.py", "app.py", "cli.py", "run.py", "__main__.py"]

        for name in common_names:
            if (project_path / name).exists():
                entry_points.append(name)

        # Look for files with if __name__ == "__main__":
        for py_file in project_path.glob("*.py"):
            try:
                content = py_file.read_text()
                if 'if __name__ == "__main__":' in content or "if __name__ == '__main__':" in content:
                    if py_file.name not in entry_points:
                        entry_points.append(py_file.name)
            except Exception:
                continue

        return entry_points

    def _get_dependencies(self, project_path: Path) -> list[str]:
        """Get project dependencies."""
        deps = []

        # Check pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                with open(pyproject_file, "rb") as f:
                    data = tomllib.load(f)

                # Get dependencies
                project_deps = data.get("project", {}).get("dependencies", [])
                deps.extend(project_deps)

                # Get optional dependencies
                optional_deps = data.get("project", {}).get("optional-dependencies", {})
                for group_deps in optional_deps.values():
                    deps.extend(group_deps)

            except Exception as e:
                self.logger.warning(f"Failed to parse pyproject.toml: {e}")

        # Check requirements.txt
        req_file = project_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text()
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name
                        match = re.match(r"^([a-zA-Z0-9\-_.]+)", line)
                        if match:
                            deps.append(match.group(1))
            except Exception as e:
                self.logger.debug(f"Failed to parse requirements.txt: {e}")

        return deps

    def _get_system_deps(self, python_deps: list[str]) -> list[str]:
        """Determine system dependencies based on Python packages."""
        system_deps = []

        # Mapping of Python packages to system dependencies
        dep_map = {
            "psycopg2": ["libpq-dev"],
            "mysqlclient": ["default-libmysqlclient-dev"],
            "pillow": ["libjpeg-dev", "zlib1g-dev"],
            "lxml": ["libxml2-dev", "libxslt-dev"],
            "cryptography": ["libssl-dev", "libffi-dev"],
            "numpy": ["libblas-dev", "liblapack-dev"],
            "scipy": ["gfortran", "libblas-dev", "liblapack-dev"],
            "opencv-python": ["libglib2.0-0", "libsm6", "libxext6", "libxrender-dev", "libgomp1"],
        }

        for py_dep in python_deps:
            py_dep_lower = py_dep.lower()
            for key, sys_deps in dep_map.items():
                if key in py_dep_lower:
                    system_deps.extend(sys_deps)

        # Remove duplicates
        return list(set(system_deps))

    def _has_tests(self, project_path: Path) -> bool:
        """Check if project has tests."""
        test_dirs = ["tests", "test", "testing"]

        for test_dir in test_dirs:
            if (project_path / test_dir).is_dir():
                return True

        # Check for test files
        return bool(list(project_path.rglob("test_*.py")) or list(project_path.rglob("*_test.py")))

    def _has_frontend(self, project_path: Path) -> bool:
        """Check if project has frontend components."""
        frontend_indicators = ["package.json", "node_modules", "webpack.config.js", "tsconfig.json"]

        for indicator in frontend_indicators:
            if (project_path / indicator).exists():
                return True

        return False

    def _detect_ports(self, project_path: Path, main_entry: str | None) -> list[int]:
        """Detect ports used by web application."""
        ports = []

        if not main_entry:
            return [8000]  # Default

        try:
            content = (project_path / main_entry).read_text()

            # Look for port configurations
            port_patterns = [
                r"port\s*=\s*(\d+)",
                r"PORT\s*=\s*(\d+)",
                r'host=["\']0\.0\.0\.0["\']\s*,\s*port=(\d+)',
                r"app\.run\(.*port=(\d+)",
                r"uvicorn\.run\(.*port=(\d+)",
            ]

            for pattern in port_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    try:
                        port = int(match)
                        if 1 <= port <= 65535:
                            ports.append(port)
                    except ValueError:
                        self.logger.debug(f"Invalid port value: {match}")
                        continue

        except Exception as e:
            self.logger.debug(f"Failed to detect ports from {main_entry}: {e}")

        return ports if ports else [8000]  # Default to 8000

    def get_dockerfile(self, project_path: Path) -> str:
        """
        Get Dockerfile content for project.

        Args:
            project_path: Path to project

        Returns:
            Dockerfile content
        """
        # Check if Dockerfile exists
        dockerfile_path = project_path / "Dockerfile"
        if dockerfile_path.exists():
            self.logger.info("Using existing Dockerfile")
            return dockerfile_path.read_text()

        # Generate new Dockerfile
        project_info = self.analyze_project(project_path)
        return cast(str, self.generate_dockerfile(project_info))

    @task
    def generate_dockerfile(
        self, project_info: dict[str, Any], multi_stage: bool = False, production: bool = False
    ) -> str:
        """
        Generate Dockerfile based on project info.

        Args:
            project_info: Project information
            multi_stage: Use multi-stage build
            production: Production optimizations

        Returns:
            Dockerfile content
        """
        template_key = "multistage" if multi_stage else "base"
        template = self.templates[template_key]

        # Prepare substitutions
        python_version = project_info.get("python_version", "3.11")
        system_deps = " ".join(project_info.get("system_deps", []))

        # Prepare expose ports
        expose_ports = ""
        if project_info.get("ports"):
            for port in project_info["ports"]:
                expose_ports += f"EXPOSE {port}\n"

        # Prepare CMD
        if project_info.get("main_entry"):
            cmd = f'["uv", "run", "python", "{project_info["main_entry"]}"]'
        else:
            # Default for different project types
            if project_info["type"] == ProjectType.WEB:
                cmd = '["uv", "run", "python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]'
            elif project_info["type"] == ProjectType.CLI:
                cmd = '["uv", "run", "python", "-m", "app"]'
            else:
                cmd = '["uv", "run", "python"]'

        # Add test dependencies if needed
        if project_info.get("has_tests") and not production:
            system_deps += " chromium" if "playwright" in project_info.get("dependencies", []) else ""

        # Format Dockerfile
        dockerfile = template.format(
            python_version=python_version,
            system_deps=system_deps or "ca-certificates",
            expose_ports=expose_ports.strip(),
            cmd=cmd,
        )

        # Add frontend build steps if needed
        if project_info.get("has_frontend"):
            frontend_steps = """
# Install Node.js for frontend
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \\
    apt-get install -y nodejs

# Install frontend dependencies
RUN npm install
RUN npm run build
"""
            # Insert after copying files
            dockerfile = dockerfile.replace("COPY . .", f"COPY . .\n{frontend_steps}")

        return dockerfile

    def validate_dockerfile(self, dockerfile_content: str) -> list[str]:
        """
        Validate Dockerfile content.

        Args:
            dockerfile_content: Dockerfile content

        Returns:
            List of validation issues
        """
        issues = []

        lines = dockerfile_content.split("\n")

        # Check for FROM instruction
        if not any(line.strip().startswith("FROM") for line in lines):
            issues.append("Missing FROM instruction")

        # Check for WORKDIR
        if not any(line.strip().startswith("WORKDIR") for line in lines):
            issues.append("Missing WORKDIR instruction")

        # Check for security issues
        if any("--no-cache-dir" not in line and "pip install" in line for line in lines):
            issues.append("pip install should use --no-cache-dir")

        if any("apt-get install" in line and "rm -rf /var/lib/apt/lists/*" not in line for line in lines):
            issues.append("apt-get install should clean up package lists")

        # Check for running as root in production
        if "USER" not in dockerfile_content and "production" in dockerfile_content.lower():
            issues.append("Production container should not run as root")

        return issues
