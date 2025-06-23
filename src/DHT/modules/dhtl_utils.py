#!/usr/bin/env python3
from typing import Any

"""
Dhtl Utils module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_utils.sh
# - Contains utility functions like linting
# - Maintains compatibility with existing functionality
# - Uses error handling from dhtl_error_handling.py
#

"""
DHT Utils Module.

Contains utility functions for DHT including file searching and linting.
"""

import os
import shutil
from pathlib import Path

# Import from our error handling module
from .dhtl_error_handling import log_error, log_info, log_success, log_warning


def file_exists_in_tree(directory: str, filename: str, max_depth: int = 4) -> bool:
    """
    Check if a file exists anywhere within a directory tree up to a certain depth.

    Args:
        directory: The directory to search in
        filename: The filename to search for
        max_depth: Maximum depth to search (default: 4)

    Returns:
        True if file found, False otherwise

    Example:
        file_exists_in_tree("/project/root", "pyproject.toml", 2)
    """
    dir_path = Path(directory)

    if not dir_path.is_dir():
        log_warning(f"file_exists_in_tree: Directory '{directory}' not found.")
        return False

    if not filename:
        log_warning("file_exists_in_tree: Filename not provided.")
        return False

    # Search for the file up to max_depth
    for depth in range(max_depth + 1):
        # Use glob pattern to search at specific depth
        pattern = "/".join(["*"] * depth) + f"/{filename}" if depth > 0 else filename
        matches = list(dir_path.glob(pattern))

        # Filter to only files (not directories)
        file_matches = [m for m in matches if m.is_file()]

        if file_matches:
            return True

    return False


class LintCommand:
    """Handler for the lint command."""

    def __init__(self) -> None:
        """Initialize the lint command handler."""
        # Import these here to avoid circular imports
        from .dhtl_environment_utils import find_project_root, find_virtual_env
        from .dhtl_guardian_utils import run_with_guardian

        self.find_project_root = find_project_root
        self.find_virtual_env = find_virtual_env
        self.run_with_guardian = run_with_guardian

        # Get memory limits from environment
        self.python_mem_limit = int(os.environ.get("PYTHON_MEM_LIMIT", "2048"))
        self.default_mem_limit = int(os.environ.get("DEFAULT_MEM_LIMIT", "2048"))

    def run(self) -> int:
        """
        Run linters on the project (Python, Shell). Prioritizes pre-commit if configured.

        Returns:
            0 if all checks pass, 1 if any fail
        """
        log_info("🔍 Running linters on project...")

        # Find project root
        project_root = self.find_project_root()

        # Find virtual environment
        venv_dir = self.find_virtual_env(project_root)
        if not venv_dir:
            venv_dir = Path(os.environ.get("DEFAULT_VENV_DIR", ".venv"))

        venv_dir = Path(venv_dir)
        venv_bin_path = venv_dir / "bin"
        venv_scripts_path = venv_dir / "Scripts"  # For Windows

        # Check tool availability
        tools = self._check_tools(project_root, venv_bin_path, venv_scripts_path)

        # Execute linting
        if tools["use_precommit"]:
            return self._run_precommit(tools["precommit_cmd"])
        else:
            return self._run_individual_linters(project_root, tools)

    def _check_tools(self, project_root: Path, venv_bin_path: Path, venv_scripts_path: Path) -> dict[str, Any]:
        """Check which linting tools are available."""
        tools = {
            "use_precommit": False,
            "use_ruff": False,
            "use_black": False,
            "use_mypy": False,
            "use_shellcheck": False,
            "precommit_cmd": "",
            "ruff_cmd": "",
            "black_cmd": "",
            "mypy_cmd": "",
            "shellcheck_cmd": "",
        }

        # Check pre-commit first (preferred method)
        if (project_root / ".pre-commit-config.yaml").exists():
            if (venv_bin_path / "pre-commit").exists():
                tools["precommit_cmd"] = str(venv_bin_path / "pre-commit")
                tools["use_precommit"] = True
            elif (venv_scripts_path / "pre-commit.exe").exists():
                tools["precommit_cmd"] = str(venv_scripts_path / "pre-commit.exe")
                tools["use_precommit"] = True
            elif shutil.which("pre-commit"):
                tools["precommit_cmd"] = "pre-commit"
                tools["use_precommit"] = True
                log_warning("Using global pre-commit.")
            else:
                log_warning(
                    ".pre-commit-config.yaml found, but pre-commit command not found. "
                    "Install it ('dhtl setup' or 'uv pip install pre-commit')."
                )

        # Check individual linters if pre-commit isn't used/available
        if not tools["use_precommit"]:
            # Check ruff
            if (venv_bin_path / "ruff").exists():
                tools["ruff_cmd"] = str(venv_bin_path / "ruff")
                tools["use_ruff"] = True
            elif (venv_scripts_path / "ruff.exe").exists():
                tools["ruff_cmd"] = str(venv_scripts_path / "ruff.exe")
                tools["use_ruff"] = True
            elif shutil.which("ruff"):
                tools["ruff_cmd"] = "ruff"
                tools["use_ruff"] = True
                log_warning("Using global ruff.")

            # Check black
            if (venv_bin_path / "black").exists():
                tools["black_cmd"] = str(venv_bin_path / "black")
                tools["use_black"] = True
            elif (venv_scripts_path / "black.exe").exists():
                tools["black_cmd"] = str(venv_scripts_path / "black.exe")
                tools["use_black"] = True
            elif shutil.which("black"):
                tools["black_cmd"] = "black"
                tools["use_black"] = True
                log_warning("Using global black.")

            # Check mypy
            if (venv_bin_path / "mypy").exists():
                tools["mypy_cmd"] = str(venv_bin_path / "mypy")
                tools["use_mypy"] = True
            elif (venv_scripts_path / "mypy.exe").exists():
                tools["mypy_cmd"] = str(venv_scripts_path / "mypy.exe")
                tools["use_mypy"] = True
            elif shutil.which("mypy"):
                tools["mypy_cmd"] = "mypy"
                tools["use_mypy"] = True
                log_warning("Using global mypy.")

            # Check shellcheck
            if shutil.which("shellcheck"):
                tools["shellcheck_cmd"] = "shellcheck"
                tools["use_shellcheck"] = True
            elif (venv_bin_path / "shellcheck").exists():
                tools["shellcheck_cmd"] = str(venv_bin_path / "shellcheck")
                tools["use_shellcheck"] = True
                log_info("Using shellcheck-py wrapper from venv.")
            elif (venv_scripts_path / "shellcheck.exe").exists():
                tools["shellcheck_cmd"] = str(venv_scripts_path / "shellcheck.exe")
                tools["use_shellcheck"] = True
                log_info("Using shellcheck-py wrapper from venv.")
            else:
                log_warning("shellcheck command not found globally or in venv. Skipping shell script linting.")

        return tools

    def _run_precommit(self, precommit_cmd: str) -> int:
        """Run pre-commit hooks."""
        log_info("🔄 Running pre-commit hooks (preferred method)...")

        # Run pre-commit with guardian
        exit_code = self.run_with_guardian(precommit_cmd, "precommit", self.python_mem_limit, "run", "--all-files")

        if exit_code != 0:
            log_error(f"Pre-commit checks failed with exit code {exit_code}.")
            log_error("Please fix the issues reported above.")
            return 1
        else:
            log_success("Pre-commit checks passed successfully.")
            return 0

    def _run_individual_linters(self, project_root: Path, tools: dict[str, Any]) -> int:
        """Run individual linters if pre-commit wasn't used."""
        log_info("No pre-commit config found or pre-commit command unavailable. Running individual linters...")

        lint_failed = False
        ran_any_linter = False

        # Ruff (Linter + Formatter Check)
        if tools["use_ruff"]:
            ran_any_linter = True

            # Run ruff check
            log_info("🔄 Running ruff check...")
            exit_code = self.run_with_guardian(
                tools["ruff_cmd"], "ruff", self.python_mem_limit, "check", str(project_root)
            )
            if exit_code != 0:
                lint_failed = True
                log_error("Ruff check found issues.")

            # Run ruff format check
            log_info("🔄 Running ruff format check...")
            exit_code = self.run_with_guardian(
                tools["ruff_cmd"], "ruff", self.python_mem_limit, "format", "--check", str(project_root)
            )
            if exit_code != 0:
                lint_failed = True
                log_error("Ruff format check found issues. Run 'dhtl format'.")

        # Black (Formatter Check - only if Ruff didn't run format check)
        if tools["use_black"] and not tools["use_ruff"]:
            ran_any_linter = True
            log_info("🔄 Running black format check...")

            exit_code = self.run_with_guardian(
                tools["black_cmd"], "black", self.python_mem_limit, "--check", str(project_root)
            )
            if exit_code != 0:
                lint_failed = True
                log_error("Black format check found issues. Run 'dhtl format'.")

        # MyPy (Type Checking)
        if tools["use_mypy"]:
            ran_any_linter = True
            log_info("🔄 Running mypy type check...")

            # Point mypy to the src directory or specific packages if configured
            mypy_target = project_root / "src"
            if not mypy_target.is_dir():
                mypy_target = project_root  # Fallback to root

            exit_code = self.run_with_guardian(tools["mypy_cmd"], "mypy", self.python_mem_limit, str(mypy_target))
            if exit_code != 0:
                lint_failed = True
                log_error("MyPy found type issues.")

        # ShellCheck
        if tools["use_shellcheck"]:
            ran_any_linter = True
            log_info("🔄 Running shellcheck...")

            # Find shell scripts, excluding venv and .git
            sh_files = self._find_shell_scripts(project_root)

            if sh_files:
                # Run shellcheck on all files at once
                exit_code = self.run_with_guardian(
                    tools["shellcheck_cmd"],
                    "shellcheck",
                    self.default_mem_limit,
                    "--severity=error",
                    "--external-sources",
                    *[str(f) for f in sh_files],
                )
                if exit_code != 0:
                    lint_failed = True
                    log_error("ShellCheck found issues.")
            else:
                log_info("No shell scripts found to check.")

        if not ran_any_linter:
            log_warning("No recognized linters (pre-commit, ruff, black, mypy, shellcheck) found or configured.")
            log_warning("Consider running 'dhtl setup' or installing linters manually.")

        # Final result
        if not lint_failed:
            log_success("All linting checks passed successfully.")
            return 0
        else:
            log_error("Linting failed. Please review the errors above.")
            return 1

    def _find_shell_scripts(self, project_root: Path) -> list[Path]:
        """Find all shell scripts in the project, excluding certain directories."""
        sh_files = []

        # Directories to exclude
        exclude_dirs = {".git", ".venv", ".venv_windows", "__pycache__", "node_modules", "dist", "build"}

        for root, dirs, files in os.walk(project_root):
            # Remove excluded directories from dirs list to prevent descending into them
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # Find .sh files in current directory
            for file in files:
                if file.endswith(".sh"):
                    sh_files.append(Path(root) / file)

        return sh_files


# Export the lint command function for compatibility
def lint_command() -> int:
    """Run linters on the project."""
    lint_cmd = LintCommand()
    return lint_cmd.run()
