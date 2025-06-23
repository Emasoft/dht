#!/usr/bin/env python3
from __future__ import annotations

"""
dhtl_commands_build.py - Implementation of dhtl build command

This module implements the build command functionality extracted from dhtl_commands.py
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted build command from dhtl_commands.py to reduce file size
# - Maintains same functionality and interface
# - Part of refactoring to keep files under 10KB
#


import logging
import shutil
from pathlib import Path
from typing import Any

from prefect import task
from prefect.cache_policies import NO_CACHE

from DHT.modules.uv_manager import UVManager


class BuildCommand:
    """Implementation of dhtl build command."""

    def __init__(self) -> None:
        """Initialize build command."""
        self.logger = logging.getLogger(__name__)

    @task(name="dhtl_build", log_prints=True, cache_policy=NO_CACHE)  # type: ignore[misc]
    def build(
        self,
        uv_manager: UVManager,
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

            # Run ruff check
            ruff_result = uv_manager.run_command(["run", "ruff", "check", "."], cwd=project_path)
            if not ruff_result["success"]:
                self.logger.warning("Ruff check found issues")
                # Don't fail build for linting issues, just warn

            # Run tests if they exist
            test_dirs = [project_path / "tests", project_path / "test"]
            if any(d.exists() for d in test_dirs):
                test_result = uv_manager.run_command(["run", "pytest", "-q"], cwd=project_path)
                if not test_result["success"]:
                    return {"success": False, "error": "Tests failed. Use --no-checks to skip."}

            self.logger.info("Pre-build checks passed")

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
            result = uv_manager.run_command(["build"] + build_args, cwd=project_path)

            if not result["success"]:
                return {"success": False, "error": f"Build failed: {result.get('stderr', 'Unknown error')}"}

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


# Export the command class
__all__ = ["BuildCommand"]
