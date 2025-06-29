#!/usr/bin/env python3
"""
Doc command for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create doc command module for documentation generation
# - Supports Sphinx and mkdocs
# - Integrates with Prefect runner
#

"""
Doc command for DHT.

Generates project documentation using Sphinx or mkdocs,
automatically detecting which tool is configured.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, cast

from ..prefect_compat import task

logger = logging.getLogger(__name__)


class DocCommand:
    """Doc command implementation."""

    def __init__(self) -> None:
        """Initialize doc command."""
        self.logger = logging.getLogger(__name__)

    def detect_doc_tool(self, project_path: Path) -> str | None:
        """
        Detect which documentation tool is configured.

        Args:
            project_path: Project root path

        Returns:
            'sphinx', 'mkdocs', or None
        """
        # Check for Sphinx
        if (project_path / "docs" / "conf.py").exists() or (project_path / "docs" / "source" / "conf.py").exists():
            return "sphinx"

        # Check for mkdocs
        if (project_path / "mkdocs.yml").exists() or (project_path / "mkdocs.yaml").exists():
            return "mkdocs"

        return None

    @task(
        name="doc_command",
        description="Generate project documentation",
        tags=["dht", "doc", "documentation"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(self, path: str = ".", format: str | None = None, serve: bool = False, **kwargs: Any) -> dict[str, Any]:
        """
        Execute doc command to generate documentation.

        Args:
            path: Project path
            format: Documentation format (auto-detected if not specified)
            serve: Serve documentation locally after building
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"success": False, "error": f"Project path does not exist: {project_path}"}

        # Detect documentation tool if not specified
        if not format:
            format = self.detect_doc_tool(project_path)
            if not format:
                return {
                    "success": False,
                    "error": "No documentation configuration found. "
                    "Initialize with Sphinx (docs/conf.py) or mkdocs (mkdocs.yml)",
                }

        self.logger.info(f"Generating documentation using {format}")

        try:
            if format == "sphinx":
                return self._build_sphinx(project_path, serve)
            elif format == "mkdocs":
                return self._build_mkdocs(project_path, serve)
            else:
                return {"success": False, "error": f"Unknown documentation format: {format}"}

        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return {"success": False, "error": str(e)}

    def _build_sphinx(self, project_path: Path, serve: bool) -> dict[str, Any]:
        """Build Sphinx documentation."""
        # Find docs directory
        docs_dir = project_path / "docs"
        if not docs_dir.exists():
            docs_dir = project_path / "doc"

        if not docs_dir.exists():
            return {"success": False, "error": "Documentation directory not found (docs/ or doc/)"}

        # Build command
        cmd = ["uv", "run", "sphinx-build", "-b", "html"]

        # Determine source and build directories
        if (docs_dir / "source").exists():
            source_dir = docs_dir / "source"
            build_dir = docs_dir / "build" / "html"
        else:
            source_dir = docs_dir
            build_dir = docs_dir / "_build" / "html"

        cmd.extend([str(source_dir), str(build_dir)])

        # Execute sphinx-build
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,  # 5 minutes timeout
        )

        if result.returncode == 0:
            self.logger.info("Documentation built successfully")

            response = {
                "success": True,
                "message": "Documentation built successfully",
                "output_dir": str(build_dir),
                "output": result.stdout,
            }

            if serve:
                # Serve documentation
                serve_cmd = ["python", "-m", "http.server", "8000", "--directory", str(build_dir)]
                self.logger.info("Serving documentation at http://localhost:8000")
                response["serve_command"] = " ".join(serve_cmd)
                # Note: We don't actually start the server here as it would block

            return response
        else:
            return {
                "success": False,
                "error": "Sphinx build failed",
                "output": result.stderr or result.stdout,
                "returncode": result.returncode,
            }

    def _build_mkdocs(self, project_path: Path, serve: bool) -> dict[str, Any]:
        """Build mkdocs documentation."""
        # Change to project directory
        import os

        original_dir = os.getcwd()
        os.chdir(project_path)

        try:
            if serve:
                # Serve documentation (builds automatically)
                cmd = ["uv", "run", "mkdocs", "serve"]
                self.logger.info("Starting mkdocs server at http://localhost:8000")

                # Note: This would block, so we just return the command
                return {
                    "success": True,
                    "message": "Run the following command to serve documentation",
                    "serve_command": " ".join(cmd),
                }
            else:
                # Build documentation
                cmd = ["uv", "run", "mkdocs", "build"]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=300,  # 5 minutes timeout
                )

                if result.returncode == 0:
                    site_dir = project_path / "site"
                    self.logger.info("Documentation built successfully")

                    return {
                        "success": True,
                        "message": "Documentation built successfully",
                        "output_dir": str(site_dir),
                        "output": result.stdout,
                    }
                else:
                    return {
                        "success": False,
                        "error": "mkdocs build failed",
                        "output": result.stderr or result.stdout,
                        "returncode": result.returncode,
                    }
        finally:
            os.chdir(original_dir)


# Module-level function for command registry
def doc_command(**kwargs: Any) -> dict[str, Any]:
    """Execute doc command."""
    cmd = DocCommand()
    return cast(dict[str, Any], cmd.execute(**kwargs))
