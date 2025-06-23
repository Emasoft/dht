#!/usr/bin/env python3
"""
Test suite for DHT Prefect flows.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for DHT Prefect flows
# - Tests for restore_dependencies_flow and test_command_flow
# - Using realistic fixtures and minimal mocking per TDD guidelines
#

"""
Test suite for DHT Prefect flows.

Tests the Prefect-based implementations of DHT actions with
realistic fixtures and minimal mocking.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

try:
    # Try relative import first (when run as module)
    from .test_helpers import (
        cleanup_temporary_project,
        create_psutil_virtual_memory_mock,
        create_temporary_project,
    )
except ImportError:
    # Fall back to direct import (when run directly)
    from test_helpers import (
        cleanup_temporary_project,
        create_psutil_virtual_memory_mock,
        create_temporary_project,
    )

# Import flows to test
from DHT.modules.dht_flows.restore_flow import (
    create_virtual_environment,
    detect_virtual_environment,
    find_project_root,
    install_dependencies,
    restore_dependencies_flow,
    verify_installation,
)
from DHT.modules.dht_flows.test_flow import (
    check_test_resources,
    discover_tests,
    parse_test_output,
    prepare_test_command,
)
from DHT.modules.dht_flows.test_flow import (
    test_command_flow as run_test_command_flow,  # Rename to avoid pytest picking it up
)


class TestRestoreFlow:
    """Test the restore dependencies Prefect flow."""

    def test_find_project_root_with_pyproject(self) -> Any:
        """Test finding project root with pyproject.toml."""
        project_path, metadata = create_temporary_project(project_type="simple", project_name="test_project")

        try:
            # Test from project root
            root = find_project_root(project_path)
            assert root.resolve() == project_path.resolve()

            # Test from subdirectory
            subdir = project_path / "src"
            root_from_subdir = find_project_root(subdir)
            assert root_from_subdir.resolve() == project_path.resolve()

        finally:
            cleanup_temporary_project(project_path)

    def test_find_project_root_with_git(self, tmp_path) -> Any:
        """Test finding project root with .git directory."""
        project_dir = tmp_path / "git_project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()

        root = find_project_root(project_dir)
        assert root == project_dir

    def test_find_project_root_not_found(self, tmp_path) -> Any:
        """Test error when project root cannot be found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ValueError, match="Could not find project root"):
            find_project_root(empty_dir)

    @patch("sys.prefix", "/tmp/test_venv")
    @patch("sys.base_prefix", "/usr/bin/python")
    def test_detect_virtual_environment_exists(self) -> Any:
        """Test detecting existing virtual environment."""
        project_path, _ = create_temporary_project("simple")

        try:
            # Test with activated venv (sys.prefix != sys.base_prefix)
            exists, detected_path = detect_virtual_environment(project_path)
            assert exists is True
            assert detected_path == Path("/tmp/test_venv")

        finally:
            cleanup_temporary_project(project_path)

    @patch("sys.prefix", sys.base_prefix)  # Make sure we're not in a venv
    def test_detect_virtual_environment_not_exists(self) -> Any:
        """Test detecting when no virtual environment exists."""
        project_path, _ = create_temporary_project("simple")

        try:
            exists, suggested_path = detect_virtual_environment(project_path)
            assert exists is False
            assert suggested_path == project_path / ".venv"

        finally:
            cleanup_temporary_project(project_path)

    @patch("DHT.modules.dht_flows.restore_flow.UVManager")
    def test_create_virtual_environment(self, mock_uv_manager_class) -> Any:
        """Test virtual environment creation."""
        # Mock UV manager
        mock_uv = MagicMock()
        mock_uv.is_available = True  # Property, not method
        mock_uv.create_venv.return_value = {"success": True}
        mock_uv_manager_class.return_value = mock_uv

        venv_path = Path("/tmp/test_venv")
        result = create_virtual_environment(venv_path, python_version="3.10")

        assert result == venv_path
        mock_uv_manager_class.assert_called_once()  # Check UVManager was instantiated
        mock_uv.create_venv.assert_called_once_with(path=venv_path, python_version="3.10")

    @patch("DHT.modules.dht_flows.restore_flow.run_with_guardian")
    @patch("DHT.modules.dht_flows.restore_flow.UVManager")
    def test_install_dependencies_with_lock(self, mock_uv_manager_class, mock_run) -> Any:
        """Test installing dependencies with uv.lock."""
        project_path, _ = create_temporary_project("simple")

        try:
            # Create uv.lock
            (project_path / "uv.lock").touch()

            # Mock UV manager
            mock_uv = MagicMock()
            mock_uv_manager_class.return_value = mock_uv

            # Mock guardian run
            mock_result = MagicMock()
            mock_result.return_code = 0
            mock_result.stdout = "Dependencies installed"
            mock_result.stderr = ""
            mock_result.execution_time = 5.5
            mock_run.return_value = mock_result

            result = install_dependencies(
                project_root=project_path, venv_path=project_path / ".venv", extras="dev", upgrade=False
            )

            assert result["success"] is True
            assert "Dependencies installed successfully" in result["message"]
            assert result["install_time"] == 5.5

            # Check UV sync was called with extras
            call_args = mock_run.call_args[0][0]
            assert call_args == ["uv", "sync", "--extra", "dev"]

        finally:
            cleanup_temporary_project(project_path)

    @patch("DHT.modules.dht_flows.restore_flow.subprocess.run")
    def test_verify_installation(self, mock_subprocess) -> Any:
        """Test installation verification."""
        project_path, _ = create_temporary_project("simple", project_name="my_app")

        try:
            venv_path = project_path / ".venv"
            venv_path.mkdir()
            (venv_path / "bin").mkdir()
            python_path = venv_path / "bin" / "python"
            python_path.touch()

            # Mock subprocess calls
            version_result = MagicMock()
            version_result.stdout = "Python 3.10.0"
            version_result.returncode = 0

            import_results = [
                MagicMock(returncode=0),  # my_app
                MagicMock(returncode=0),  # prefect
                MagicMock(returncode=0),  # yaml
                MagicMock(returncode=0),  # requests
            ]

            mock_subprocess.side_effect = [version_result] + import_results

            result = verify_installation(project_path, venv_path)

            assert result["success"] is True
            assert result["python_version"] == "Python 3.10.0"
            assert result["import_results"]["my_app"] is True
            assert result["import_results"]["prefect"] is True

        finally:
            cleanup_temporary_project(project_path)

    @patch("DHT.modules.dht_flows.restore_flow.find_project_root")
    @patch("DHT.modules.dht_flows.restore_flow.detect_virtual_environment")
    @patch("DHT.modules.dht_flows.restore_flow.create_virtual_environment")
    @patch("DHT.modules.dht_flows.restore_flow.install_dependencies")
    @patch("DHT.modules.dht_flows.restore_flow.install_dht_dependencies")
    @patch("DHT.modules.dht_flows.restore_flow.verify_installation")
    def test_restore_dependencies_flow_complete(
        self, mock_verify, mock_install_dht, mock_install_deps, mock_create_venv, mock_detect_venv, mock_find_root
    ) -> Any:
        """Test complete restore dependencies flow."""
        # Setup mocks
        project_root = Path("/tmp/test_project")
        venv_path = Path("/tmp/test_project/.venv")

        mock_find_root.return_value = project_root
        mock_detect_venv.return_value = (False, venv_path)
        mock_create_venv.return_value = venv_path
        mock_install_deps.return_value = {"success": True, "message": "Dependencies installed", "install_time": 10.5}
        mock_install_dht.return_value = {"success": True, "message": "DHT dependencies installed", "install_time": 5.0}
        mock_verify.return_value = {
            "success": True,
            "python_version": "Python 3.10.0",
            "import_results": {"my_app": True, "prefect": True},
        }

        # Run flow
        result = restore_dependencies_flow(
            project_path="/tmp/test_project",
            python_version="3.10",
            extras="dev,test",
            upgrade=True,
            install_dht_deps=True,
        )

        # Verify results
        assert result["success"] is True
        assert result["project_root"] == str(project_root)
        assert result["venv_path"] == str(venv_path)
        assert result["install_result"]["success"] is True
        assert result["verification"]["success"] is True

        # Verify calls
        mock_find_root.assert_called_once()
        mock_detect_venv.assert_called_once_with(project_root)
        mock_create_venv.assert_called_once_with(venv_path, "3.10")
        mock_install_deps.assert_called_once()
        mock_install_dht.assert_called_once()
        mock_verify.assert_called_once()


class TestTestFlow:
    """Test the test command Prefect flow."""

    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_count")
    @patch("psutil.cpu_percent")
    def test_check_test_resources(self, mock_cpu_percent, mock_cpu_count, mock_vm) -> Any:
        """Test resource checking."""
        # Mock system resources
        mock_vm.return_value = create_psutil_virtual_memory_mock(
            total=16 * 1024 * 1024 * 1024,  # 16GB
            available=8 * 1024 * 1024 * 1024,  # 8GB
            percent=50.0,
        )
        mock_cpu_count.return_value = 4
        mock_cpu_percent.return_value = 25.0

        result = check_test_resources()

        assert result["has_resources"] is True
        assert result["memory"]["available_mb"] > 7000
        assert result["memory"]["percent_used"] == 50.0
        assert result["cpu"]["count"] == 4
        assert result["cpu"]["percent_used"] == 25.0

    def test_discover_tests_pytest_project(self) -> Any:
        """Test discovering tests in a pytest project."""
        project_path, _ = create_temporary_project(project_type="simple", include_tests=True)

        try:
            result = discover_tests(project_path, test_pattern="utils")

            assert result["test_dirs"] == [str(project_path / "tests")]
            assert result["test_files_count"] >= 1
            assert result["has_pytest"] is True
            assert result["framework"] == "pytest"
            assert result["test_pattern"] == "utils"

        finally:
            cleanup_temporary_project(project_path)

    def test_discover_tests_no_tests(self) -> Any:
        """Test discovering when no tests exist."""
        project_path, _ = create_temporary_project(project_type="simple", include_tests=False)

        try:
            result = discover_tests(project_path)

            assert result["test_dirs"] == []
            assert result["test_files_count"] == 0
            assert result["has_pytest"] is True  # pyproject.toml exists

        finally:
            cleanup_temporary_project(project_path)

    def test_prepare_test_command_pytest(self, tmp_path) -> Any:
        """Test preparing pytest command."""
        venv_path = tmp_path / ".venv"
        venv_path.mkdir()
        (venv_path / "bin").mkdir()
        (venv_path / "bin" / "python").touch()

        discovery_info = {"framework": "pytest", "test_dirs": ["tests"], "test_pattern": "test_utils"}

        cmd = prepare_test_command(
            project_root=tmp_path,
            venv_path=venv_path,
            discovery_info=discovery_info,
            verbose=True,
            coverage=True,
            parallel=True,
            timeout=300,
        )

        assert str(venv_path / "bin" / "python") in cmd
        assert "-m" in cmd
        assert "coverage" in cmd
        assert "pytest" in cmd
        assert "-v" in cmd
        assert "-k" in cmd
        assert "test_utils" in cmd
        assert "-n" in cmd
        assert "auto" in cmd
        assert "--timeout" in cmd
        assert "300" in cmd

    def test_parse_test_output_pytest_success(self) -> Any:
        """Test parsing successful pytest output."""
        stdout = """
        ============================= test session starts ==============================
        collected 42 items

        tests/test_utils.py::test_one PASSED                                    [ 25%]
        tests/test_utils.py::test_two PASSED                                    [ 50%]
        tests/test_utils.py::test_three SKIPPED                                 [ 75%]
        tests/test_utils.py::test_four PASSED                                   [100%]

        ========================= 3 passed, 1 skipped in 0.05s =========================
        """

        summary = parse_test_output(stdout, "")

        assert summary["total"] == 4
        assert summary["passed"] == 3
        assert summary["skipped"] == 1
        assert summary["failed"] == 0
        assert summary["errors"] == 0

    def test_parse_test_output_pytest_failures(self) -> Any:
        """Test parsing pytest output with failures."""
        stdout = """
        ============================= test session starts ==============================
        collected 10 items

        tests/test_app.py::test_one PASSED                                      [ 20%]
        tests/test_app.py::test_two FAILED                                      [ 40%]
        tests/test_app.py::test_three ERROR                                     [ 60%]
        tests/test_app.py::test_four PASSED                                     [ 80%]
        tests/test_app.py::test_five FAILED                                     [100%]

        =================== 2 passed, 2 failed, 1 error in 0.12s ======================
        """

        summary = parse_test_output(stdout, "")

        assert summary["total"] == 5
        assert summary["passed"] == 2
        assert summary["failed"] == 2
        assert summary["errors"] == 1

    def test_parse_test_output_unittest(self) -> Any:
        """Test parsing unittest output."""
        stdout = """
        ...F.E.
        ======================================================================
        FAIL: test_something (test_module.TestCase)
        ----------------------------------------------------------------------
        Traceback (most recent call last):
          File "test.py", line 10, in test_something
            self.assertEqual(1, 2)
        AssertionError: 1 != 2

        ----------------------------------------------------------------------
        Ran 7 tests in 0.002s

        FAILED (failures=1, errors=1)
        """

        summary = parse_test_output(stdout, "")

        assert summary["total"] == 7
        assert summary["failed"] == 1
        assert summary["errors"] == 1

    @patch("DHT.modules.dht_flows.test_flow.check_test_resources")
    @patch("DHT.modules.dht_flows.test_flow.find_project_root")
    @patch("DHT.modules.dht_flows.test_flow.detect_virtual_environment")
    @patch("DHT.modules.dht_flows.test_flow.discover_tests")
    @patch("DHT.modules.dht_flows.test_flow.prepare_test_command")
    @patch("DHT.modules.dht_flows.test_flow.run_tests")
    @patch("DHT.modules.dht_flows.test_flow.generate_coverage_report")
    def test_test_command_flow_complete(
        self,
        mock_coverage,
        mock_run_tests,
        mock_prepare_cmd,
        mock_discover,
        mock_detect_venv,
        mock_find_root,
        mock_check_resources,
    ) -> Any:
        """Test complete test command flow."""
        # Setup mocks
        project_root = Path("/tmp/test_project")
        venv_path = Path("/tmp/test_project/.venv")

        mock_check_resources.return_value = {"has_resources": True, "memory": {"available_mb": 8192}}
        mock_find_root.return_value = project_root
        mock_detect_venv.return_value = (True, venv_path)
        mock_discover.return_value = {"test_files_count": 10, "test_dirs": ["tests"], "framework": "pytest"}
        mock_prepare_cmd.return_value = ["python", "-m", "pytest"]
        mock_run_tests.return_value = {
            "success": True,
            "return_code": 0,
            "execution_time": 5.5,
            "stdout": "10 passed",
            "stderr": "",
            "summary": {"total": 10, "passed": 10, "failed": 0, "errors": 0, "skipped": 0},
        }
        mock_coverage.return_value = {"has_coverage": True, "coverage_percent": 85, "report": "Coverage report..."}

        # Run flow
        result = run_test_command_flow(
            project_path="/tmp/test_project",
            test_pattern="test_",
            verbose=True,
            coverage=True,
            parallel=False,
            timeout=600,
            memory_limit_mb=2048,
        )

        # Verify results
        assert result["success"] is True
        assert result["project_root"] == str(project_root)
        assert result["test_result"]["success"] is True
        assert result["test_result"]["summary"]["passed"] == 10
        assert result["coverage"]["coverage_percent"] == 85

        # Verify calls
        mock_check_resources.assert_called_once()
        mock_find_root.assert_called_once()
        mock_detect_venv.assert_called_once()
        mock_discover.assert_called_once()
        mock_prepare_cmd.assert_called_once()
        mock_run_tests.assert_called_once()
        mock_coverage.assert_called_once()

    @patch("DHT.modules.dht_flows.test_flow.detect_virtual_environment")
    def test_test_command_flow_no_venv(self, mock_detect_venv) -> Any:
        """Test error when no virtual environment exists."""
        project_path, _ = create_temporary_project("simple")

        try:
            # Mock no venv found
            mock_detect_venv.return_value = (False, None)

            with pytest.raises(RuntimeError, match="No virtual environment found"):
                run_test_command_flow(project_path=str(project_path))

        finally:
            cleanup_temporary_project(project_path)
