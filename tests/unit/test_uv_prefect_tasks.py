#!/usr/bin/env python3
"""
Test Uv Prefect Tasks module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of UV Prefect tasks unit tests
# - Tests for UV availability checks
# - Tests for Python version detection
# - Tests for virtual environment creation
# - Tests for dependency installation
# - Tests for lock file generation
# - Tests for project setup flow
#

"""
Unit tests for the UV Prefect tasks module.
"""

import tempfile
from pathlib import Path
from unittest import mock

import pytest
from prefect.testing.utilities import prefect_test_harness

from DHT.modules.guardian_prefect import GuardianResult
from DHT.modules.uv_prefect_tasks import (
    add_dependency,
    build_project,
    check_uv_available,
    create_virtual_environment,
    detect_python_version,
    ensure_python_version,
    generate_lock_file,
    install_dependencies,
    list_python_versions,
    run_python_script,
    setup_project_environment,
)
from DHT.modules.uv_task_utils import (
    extract_min_python_version,
    find_uv_executable,
)


class TestUVPrefectTasks:
    """Test cases for UV Prefect tasks."""

    @pytest.fixture(autouse=True)
    def setup_prefect(self):
        """Setup Prefect test harness."""
        # Clear the LRU cache before each test
        find_uv_executable.cache_clear()

        with prefect_test_harness():
            yield

    def test_extract_min_python_version(self):
        """Test Python version extraction from constraints."""
        assert extract_min_python_version(">=3.8") == "3.8"
        assert extract_min_python_version(">=3.8,<3.12") == "3.8"
        assert extract_min_python_version("^3.8") == "3.8"
        assert extract_min_python_version("~3.8") == "3.8"
        assert extract_min_python_version("3.11.6") == "3.11.6"
        assert extract_min_python_version("python>=3.10") == "3.10"

    @mock.patch("DHT.modules.uv_python_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_python_tasks.run_with_guardian")
    def test_check_uv_available_success(self, mock_run, mock_find):
        """Test successful UV availability check."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        print(f"Mock find_uv_executable configured to return: {mock_find.return_value}")
        mock_run.return_value = GuardianResult(
            stdout="uv 0.4.27",
            stderr="",
            return_code=0,
            execution_time=0.1,
            peak_memory_mb=10.0,
            was_killed=False,
            kill_reason=None,
        )

        result = check_uv_available()

        assert result["available"] is True
        assert result["version"] == "0.4.27"
        assert result["path"] == "/usr/local/bin/uv"

    @mock.patch("DHT.modules.uv_python_tasks.find_uv_executable")
    def test_check_uv_available_not_found(self, mock_find):
        """Test UV not found."""
        mock_find.return_value = None

        result = check_uv_available()

        assert result["available"] is False
        assert "not found" in result["error"]

    def test_detect_python_version_from_file(self):
        """Test Python version detection from .python-version file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            version_file = project_path / ".python-version"
            version_file.write_text("3.11.6\n")

            version = detect_python_version(project_path)
            assert version == "3.11.6"

    def test_detect_python_version_from_pyproject(self):
        """Test Python version detection from pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            pyproject = project_path / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test"
requires-python = ">=3.11"
""")

            version = detect_python_version(project_path)
            assert version == "3.11"

    def test_detect_python_version_none(self):
        """Test Python version detection when no config found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            version = detect_python_version(project_path)
            assert version is None

    @mock.patch("DHT.modules.uv_python_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_python_tasks.run_with_guardian")
    def test_list_python_versions(self, mock_run, mock_find):
        """Test listing Python versions."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="""cpython-3.11.6-macos-aarch64-none
cpython-3.12.0-macos-aarch64-none     <download available>
cpython-3.10.13-macos-aarch64-none
pypy-3.9.18-macos-aarch64     <download available>""",
            stderr="",
            return_code=0,
            execution_time=0.5,
            peak_memory_mb=50.0,
            was_killed=False,
            kill_reason=None,
        )

        versions = list_python_versions()

        assert len(versions) == 4
        assert versions[0]["version"] == "cpython-3.11.6-macos-aarch64-none"
        assert versions[0]["installed"] is True
        assert versions[1]["version"] == "cpython-3.12.0-macos-aarch64-none"
        assert versions[1]["installed"] is False

    @mock.patch("pathlib.Path.exists")
    @mock.patch("DHT.modules.uv_python_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_python_tasks.run_with_guardian")
    def test_ensure_python_version_already_installed(self, mock_run, mock_find, mock_exists):
        """Test ensuring Python version that's already installed."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_exists.return_value = True  # Python path exists
        mock_run.return_value = GuardianResult(
            stdout="/usr/local/bin/python3.11",
            stderr="",
            return_code=0,
            execution_time=0.1,
            peak_memory_mb=10.0,
            was_killed=False,
            kill_reason=None,
        )

        python_path = ensure_python_version("3.11")

        assert python_path == Path("/usr/local/bin/python3.11")
        # Only one call for finding
        assert mock_run.call_count == 1

    @mock.patch("pathlib.Path.exists")
    @mock.patch("DHT.modules.uv_python_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_python_tasks.run_with_guardian")
    def test_ensure_python_version_install_needed(self, mock_run, mock_find, mock_exists):
        """Test ensuring Python version that needs installation."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        # Path doesn't exist initially, then exists after installation
        mock_exists.side_effect = [False, True]

        # Setup mock responses
        mock_run.side_effect = [
            # First find fails
            GuardianResult(
                stdout="",
                stderr="Python 3.11 not found",
                return_code=1,
                execution_time=0.1,
                peak_memory_mb=10.0,
                was_killed=False,
                kill_reason=None,
            ),
            # Install succeeds
            GuardianResult(
                stdout="Installed Python 3.11",
                stderr="",
                return_code=0,
                execution_time=30.0,
                peak_memory_mb=200.0,
                was_killed=False,
                kill_reason=None,
            ),
            # Second find succeeds
            GuardianResult(
                stdout="/usr/local/bin/python3.11",
                stderr="",
                return_code=0,
                execution_time=0.1,
                peak_memory_mb=10.0,
                was_killed=False,
                kill_reason=None,
            ),
        ]

        python_path = ensure_python_version("3.11")

        assert python_path == Path("/usr/local/bin/python3.11")
        assert mock_run.call_count == 3

    @mock.patch("DHT.modules.uv_environment_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_environment_tasks.run_with_guardian")
    def test_create_virtual_environment(self, mock_run, mock_find):
        """Test virtual environment creation."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Created virtual environment",
            stderr="",
            return_code=0,
            execution_time=5.0,
            peak_memory_mb=100.0,
            was_killed=False,
            kill_reason=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            result = create_virtual_environment(project_path, python_version="3.11")

            assert result["created"] is True
            assert result["path"] == str(project_path / ".venv")
            assert result["python_version"] == "3.11"
            mock_run.assert_called_once()
            # Check the command argument passed to run_with_guardian
            call_kwargs = mock_run.call_args.kwargs
            command = call_kwargs.get("command", [])
            assert "--python" in command
            assert "3.11" in command

    @mock.patch("DHT.modules.uv_dependency_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_dependency_tasks.run_with_guardian")
    def test_install_dependencies_with_lock(self, mock_run, mock_find):
        """Test dependency installation with lock file."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Synced dependencies",
            stderr="",
            return_code=0,
            execution_time=10.0,
            peak_memory_mb=500.0,
            was_killed=False,
            kill_reason=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create pyproject.toml to trigger sync method
            (project_path / "pyproject.toml").write_text("""[project]
name = "test"
version = "0.1.0"
""")
            # Create lock file
            (project_path / "uv.lock").touch()

            result = install_dependencies(project_path, dev=True)

            assert result["success"] is True
            assert result["method"] == "sync"
            mock_run.assert_called_once()
            # Check the command argument passed to run_with_guardian
            call_kwargs = mock_run.call_args.kwargs
            command = call_kwargs.get("command", [])
            assert "sync" in command
            assert "--dev" in command

    @mock.patch("DHT.modules.uv_dependency_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_dependency_tasks.run_with_guardian")
    def test_install_dependencies_with_requirements(self, mock_run, mock_find):
        """Test dependency installation with requirements.txt."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Installed packages",
            stderr="",
            return_code=0,
            execution_time=15.0,
            peak_memory_mb=600.0,
            was_killed=False,
            kill_reason=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create requirements file
            req_file = project_path / "requirements.txt"
            req_file.write_text("requests>=2.28\npytest>=7.0\n")

            result = install_dependencies(project_path)

            assert result["success"] is True
            assert result["method"] == "pip"
            mock_run.assert_called_once()
            # Check the command argument passed to run_with_guardian
            call_kwargs = mock_run.call_args.kwargs
            command = call_kwargs.get("command", [])
            assert "pip" in command
            assert "install" in command
            assert "-r" in command

    @mock.patch("DHT.modules.uv_dependency_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_dependency_tasks.run_with_guardian")
    def test_generate_lock_file(self, mock_run, mock_find):
        """Test lock file generation."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Generated lock file",
            stderr="",
            return_code=0,
            execution_time=20.0,
            peak_memory_mb=800.0,
            was_killed=False,
            kill_reason=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = generate_lock_file(project_path)

            assert result["success"] is True
            assert result["path"] == str(project_path / "uv.lock")
            mock_run.assert_called_once()
            # Check the command argument passed to run_with_guardian
            call_kwargs = mock_run.call_args.kwargs
            command = call_kwargs.get("command", [])
            assert "lock" in command

    @mock.patch("DHT.modules.uv_dependency_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_dependency_tasks.run_with_guardian")
    def test_add_dependency(self, mock_run, mock_find):
        """Test adding a dependency."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.side_effect = [
            # Add succeeds
            GuardianResult(
                stdout="Added requests",
                stderr="",
                return_code=0,
                execution_time=5.0,
                peak_memory_mb=200.0,
                was_killed=False,
                kill_reason=None,
            ),
            # Lock generation succeeds
            GuardianResult(
                stdout="Generated lock file",
                stderr="",
                return_code=0,
                execution_time=10.0,
                peak_memory_mb=400.0,
                was_killed=False,
                kill_reason=None,
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = add_dependency(project_path, "requests>=2.28", dev=True)

            assert result["success"] is True
            assert result["package"] == "requests>=2.28"
            assert result["dev"] is True

    @mock.patch("DHT.modules.uv_build_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_build_tasks.run_with_guardian")
    def test_build_project(self, mock_run, mock_find):
        """Test project building."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Built project-1.0.0-py3-none-any.whl",
            stderr="",
            return_code=0,
            execution_time=30.0,
            peak_memory_mb=1000.0,
            was_killed=False,
            kill_reason=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            dist_dir = project_path / "dist"
            dist_dir.mkdir()
            # Create fake artifacts
            (dist_dir / "project-1.0.0-py3-none-any.whl").touch()
            (dist_dir / "project-1.0.0.tar.gz").touch()

            result = build_project(project_path)

            assert result["success"] is True
            assert len(result["artifacts"]) == 2

    @mock.patch("DHT.modules.uv_script_tasks.find_uv_executable")
    @mock.patch("DHT.modules.uv_script_tasks.run_with_guardian")
    def test_run_python_script(self, mock_run, mock_find):
        """Test running Python scripts."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Hello, World!",
            stderr="",
            return_code=0,
            execution_time=1.5,
            peak_memory_mb=50.0,
            was_killed=False,
            kill_reason=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = run_python_script(project_path, "hello.py", args=["--name", "World"])

            assert result["success"] is True
            assert result["output"] == "Hello, World!"
            assert result["duration"] == 1.5
            assert result["peak_memory_mb"] == 50.0

    @mock.patch("DHT.modules.uv_prefect_tasks.check_uv_available")
    @mock.patch("DHT.modules.uv_prefect_tasks.detect_python_version")
    @mock.patch("DHT.modules.uv_prefect_tasks.ensure_python_version")
    @mock.patch("DHT.modules.uv_prefect_tasks.create_virtual_environment")
    @mock.patch("DHT.modules.uv_prefect_tasks.install_dependencies")
    @mock.patch("DHT.modules.uv_prefect_tasks.generate_lock_file")
    def test_setup_project_environment_flow(
        self, mock_gen_lock, mock_install, mock_create_venv, mock_ensure_py, mock_detect_py, mock_check_uv
    ):
        """Test complete project setup flow."""
        # Setup mocks
        mock_check_uv.return_value = {"available": True, "version": "0.4.27", "path": "/usr/local/bin/uv"}
        mock_detect_py.return_value = "3.11"
        mock_ensure_py.return_value = Path("/usr/local/bin/python3.11")
        mock_create_venv.return_value = {
            "created": True,
            "path": str(Path(".venv")),
            "python_version": "3.11",
            "output": "Created virtual environment",
        }
        mock_install.return_value = {"success": True, "method": "sync", "output": "Dependencies installed"}
        mock_gen_lock.return_value = {
            "success": True,
            "path": str(Path("uv.lock")),
            "exists": True,
            "output": "Generated lock file",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create pyproject.toml to trigger lock generation
            (project_path / "pyproject.toml").write_text("""[project]
name = "test"
version = "0.1.0"
""")

            result = setup_project_environment(project_path, install_deps=True)

            assert result["success"] is True
            assert result["steps"]["python_version"] == "3.11"
            assert "python" in result["steps"]["python_path"].lower()
            assert result["steps"]["venv_creation"]["path"] == str(project_path / ".venv")
            assert "dependencies" in result["steps"]
            assert result["steps"]["dependencies"]["success"] is True

    @mock.patch("DHT.modules.uv_environment_tasks.check_uv_available")
    def test_setup_project_environment_no_uv(self, mock_check_uv):
        """Test project setup when UV is not available."""
        mock_check_uv.return_value = {"available": False, "error": "UV not found"}

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = setup_project_environment(project_path)

            assert result["success"] is False
            assert "UV not available" in result["errors"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
