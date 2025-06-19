#!/usr/bin/env python3
"""
act_linter.py - GitHub Actions workflow linting functionality

This module provides linting capabilities for GitHub Actions workflows
using actionlint, with support for both native and Docker-based execution.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from act_integration.py to reduce file size
# - Contains workflow linting functionality
#

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class ActLinter:
    """Handles linting of GitHub Actions workflows."""

    def __init__(self, project_path: Path):
        """Initialize linter.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path).resolve()
        self.workflows_path = self.project_path / ".github" / "workflows"

    def lint_workflows(self, use_docker: bool = False) -> dict[str, Any]:
        """Lint GitHub Actions workflows using actionlint.

        Args:
            use_docker: Use Docker container for linting

        Returns:
            Dict with linting results
        """
        result = {
            "success": True,
            "method": "docker" if use_docker else "native",
            "errors": [],
            "warnings": [],
            "linted_files": []
        }

        if not self.workflows_path.exists():
            result["success"] = False
            result["errors"].append("No .github/workflows directory found")
            return result

        # Check if actionlint is available
        if not use_docker and not shutil.which("actionlint"):
            result["success"] = False
            result["errors"].append("actionlint not found. Install with: brew install actionlint")
            return result

        # Get workflow files
        workflow_files = list(self.workflows_path.glob("*.y*ml"))
        if not workflow_files:
            result["warnings"].append("No workflow files found")
            return result

        if use_docker:
            return self.lint_with_docker()
        else:
            return self._lint_native(workflow_files, result)

    def _lint_native(self, workflow_files: list[Path], result: dict[str, Any]) -> dict[str, Any]:
        """Lint workflows using native actionlint.

        Args:
            workflow_files: List of workflow files
            result: Result dictionary to populate

        Returns:
            Updated result dictionary
        """
        for workflow_file in workflow_files:
            result["linted_files"].append(str(workflow_file.name))

            try:
                # Run actionlint
                proc = subprocess.run(
                    ["actionlint", str(workflow_file)],
                    capture_output=True,
                    text=True
                )

                if proc.returncode != 0:
                    result["success"] = False
                    self._parse_actionlint_output(proc.stdout, result)

            except Exception as e:
                result["success"] = False
                result["errors"].append(f"Failed to lint {workflow_file.name}: {str(e)}")

        return result

    def lint_with_docker(self, tag: str = "latest", color: bool = True) -> dict[str, Any]:
        """Lint workflows using actionlint in Docker.

        Args:
            tag: Docker image tag to use
            color: Enable colored output

        Returns:
            Dict with linting results
        """
        result = {
            "success": True,
            "method": "docker",
            "errors": [],
            "warnings": [],
            "linted_files": [],
            "docker_image": f"rhysd/actionlint:{tag}"
        }

        if not self._check_docker_available():
            result["success"] = False
            result["errors"].append("Docker is not available")
            return result

        # Create temporary directory for Docker mount
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tmp_workflows = tmp_path / ".github" / "workflows"
            tmp_workflows.mkdir(parents=True)

            # Copy workflow files
            workflow_files = list(self.workflows_path.glob("*.y*ml"))
            for wf in workflow_files:
                (tmp_workflows / wf.name).write_text(wf.read_text())
                result["linted_files"].append(wf.name)

            # Build Docker command
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{tmp_path}:/work",
                "-w", "/work",
                f"rhysd/actionlint:{tag}"
            ]

            if color:
                cmd.append("-color")

            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)

                if proc.returncode != 0:
                    result["success"] = False
                    self._parse_actionlint_output(proc.stdout, result)

                if proc.stderr:
                    result["warnings"].append(f"Docker stderr: {proc.stderr}")

            except Exception as e:
                result["success"] = False
                result["errors"].append(f"Docker execution failed: {str(e)}")

        return result

    def _parse_actionlint_output(self, output: str, results: dict[str, Any]) -> None:
        """Parse actionlint output and extract errors.

        Args:
            output: Raw actionlint output
            results: Results dict to populate
        """
        for line in output.strip().split('\n'):
            if not line:
                continue

            # Parse actionlint output format: file:line:col: message
            parts = line.split(':', 3)
            if len(parts) >= 4:
                error = {
                    "file": Path(parts[0]).name,
                    "line": parts[1],
                    "column": parts[2],
                    "message": parts[3].strip()
                }
                results["errors"].append(error)
            else:
                # Fallback for unparseable lines
                results["errors"].append({"message": line})

    def _check_docker_available(self) -> bool:
        """Check if Docker is available.

        Returns:
            True if Docker is available
        """
        try:
            subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
