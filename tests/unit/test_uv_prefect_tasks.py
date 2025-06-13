#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from prefect import flow
from prefect.testing.utilities import prefect_test_harness

from DHT.modules.uv_prefect_tasks import (
    check_uv_available,
    detect_python_version,
    list_python_versions,
    ensure_python_version,
    create_virtual_environment,
    install_dependencies,
    sync_dependencies,
    pip_install_requirements,
    pip_install_project,
    generate_lock_file,
    add_dependency,
    remove_dependency,
    build_project,
    run_python_script,
    setup_project_environment,
    extract_min_python_version,
    UVTaskError,
)
from DHT.modules.guardian_prefect import GuardianResult, ResourceLimits


class TestUVPrefectTasks:
    """Test cases for UV Prefect tasks."""
    
    @pytest.fixture(autouse=True)
    def setup_prefect(self):
        """Setup Prefect test harness."""
        # Clear the LRU cache before each test
        from DHT.modules.uv_prefect_tasks import find_uv_executable
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
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_check_uv_available_success(self, mock_run, mock_find):
        """Test successful UV availability check."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="uv 0.4.27",
            stderr="",
            return_code=0,
            execution_time=0.1,
            peak_memory_mb=10.0,
            was_killed=False
        )
        
        result = check_uv_available()
        
        assert result["available"] is True
        assert result["version"] == "0.4.27"
        assert result["path"] == "/usr/local/bin/uv"
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
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
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_list_python_versions(self, mock_run, mock_find):
        """Test listing Python versions."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="""cpython-3.11.6 (installed)
cpython-3.12.0
cpython-3.10.13 (installed)
pypy-3.9.18""",
            stderr="",
            return_code=0,
            execution_time=0.5,
            peak_memory_mb=50.0
        )
        
        versions = list_python_versions()
        
        assert len(versions) == 4
        assert versions[0]["version"] == "cpython-3.11.6"
        assert versions[0]["installed"] is True
        assert versions[1]["version"] == "cpython-3.12.0"
        assert versions[1]["installed"] is False
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_ensure_python_version_already_installed(self, mock_run, mock_find):
        """Test ensuring Python version that's already installed."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="/usr/local/bin/python3.11",
            stderr="",
            return_code=0,
            execution_time=0.1,
            peak_memory_mb=10.0
        )
        
        python_path = ensure_python_version("3.11")
        
        assert python_path == Path("/usr/local/bin/python3.11")
        # Only one call for finding
        assert mock_run.call_count == 1
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_ensure_python_version_install_needed(self, mock_run, mock_find):
        """Test ensuring Python version that needs installation."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        
        # Setup mock responses
        mock_run.side_effect = [
            # First find fails
            GuardianResult(
                stdout="",
                stderr="Python 3.11 not found",
                return_code=1,
            execution_time=0.1,
                peak_memory_mb=10.0
            ),
            # Install succeeds
            GuardianResult(
                stdout="Installed Python 3.11",
                stderr="",
                return_code=0,
                execution_time=30.0,
                peak_memory_mb=200.0
            ),
            # Second find succeeds
            GuardianResult(
                stdout="/usr/local/bin/python3.11",
                stderr="",
                return_code=0,
                execution_time=0.1,
                peak_memory_mb=10.0
            ),
        ]
        
        python_path = ensure_python_version("3.11")
        
        assert python_path == Path("/usr/local/bin/python3.11")
        assert mock_run.call_count == 3
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_create_virtual_environment(self, mock_run, mock_find):
        """Test virtual environment creation."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Created virtual environment",
            stderr="",
            return_code=0,
            execution_time=5.0,
            peak_memory_mb=100.0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            venv_path = create_virtual_environment(project_path, python_version="3.11")
            
            assert venv_path == project_path / ".venv"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "--python" in args
            assert "3.11" in args
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_install_dependencies_with_lock(self, mock_run, mock_find):
        """Test dependency installation with lock file."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Synced dependencies",
            stderr="",
            return_code=0,
            execution_time=10.0,
            peak_memory_mb=500.0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create lock file
            (project_path / "uv.lock").touch()
            
            result = install_dependencies(project_path, dev=True)
            
            assert result["success"] is True
            assert result["method"] == "uv sync"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "sync" in args
            assert "--dev" in args
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_install_dependencies_with_requirements(self, mock_run, mock_find):
        """Test dependency installation with requirements.txt."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Installed packages",
            stderr="",
            return_code=0,
            execution_time=15.0,
            peak_memory_mb=600.0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create requirements file
            req_file = project_path / "requirements.txt"
            req_file.write_text("requests>=2.28\npytest>=7.0\n")
            
            result = install_dependencies(project_path)
            
            assert result["success"] is True
            assert result["method"] == "uv pip install -r"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "pip" in args
            assert "install" in args
            assert "-r" in args
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_generate_lock_file(self, mock_run, mock_find):
        """Test lock file generation."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Generated lock file",
            stderr="",
            return_code=0,
            execution_time=20.0,
            peak_memory_mb=800.0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            lock_path = generate_lock_file(project_path)
            
            assert lock_path == project_path / "uv.lock"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "lock" in args
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
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
                peak_memory_mb=200.0
            ),
            # Lock generation succeeds
            GuardianResult(
                stdout="Generated lock file",
                stderr="",
                return_code=0,
                execution_time=10.0,
                peak_memory_mb=400.0
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            result = add_dependency(project_path, "requests>=2.28", dev=True)
            
            assert result["success"] is True
            assert result["package"] == "requests>=2.28"
            assert result["dev"] is True
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_build_project(self, mock_run, mock_find):
        """Test project building."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Built project-1.0.0-py3-none-any.whl",
            stderr="",
            return_code=0,
            execution_time=30.0,
            peak_memory_mb=1000.0
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
    
    @mock.patch('DHT.modules.uv_prefect_tasks.find_uv_executable')
    @mock.patch('DHT.modules.uv_prefect_tasks.run_with_guardian')
    def test_run_python_script(self, mock_run, mock_find):
        """Test running Python scripts."""
        mock_find.return_value = Path("/usr/local/bin/uv")
        mock_run.return_value = GuardianResult(
            stdout="Hello, World!",
            stderr="",
            return_code=0,
            execution_time=1.5,
            peak_memory_mb=50.0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            result = run_python_script(
                project_path,
                "hello.py",
                args=["--name", "World"]
            )
            
            assert result["success"] is True
            assert result["output"] == "Hello, World!"
            assert result["duration"] == 1.5
            assert result["peak_memory_mb"] == 50.0
    
    @mock.patch('DHT.modules.uv_prefect_tasks.check_uv_available')
    @mock.patch('DHT.modules.uv_prefect_tasks.detect_python_version')
    @mock.patch('DHT.modules.uv_prefect_tasks.ensure_python_version')
    @mock.patch('DHT.modules.uv_prefect_tasks.create_virtual_environment')
    @mock.patch('DHT.modules.uv_prefect_tasks.install_dependencies')
    @mock.patch('DHT.modules.uv_prefect_tasks.generate_lock_file')
    def test_setup_project_environment_flow(
        self,
        mock_gen_lock,
        mock_install,
        mock_create_venv,
        mock_ensure_py,
        mock_detect_py,
        mock_check_uv
    ):
        """Test complete project setup flow."""
        # Setup mocks
        mock_check_uv.return_value = {
            "available": True,
            "version": "0.4.27",
            "path": "/usr/local/bin/uv"
        }
        mock_detect_py.return_value = "3.11"
        mock_ensure_py.return_value = Path("/usr/local/bin/python3.11")
        mock_create_venv.return_value = Path(".venv")
        mock_install.return_value = {
            "success": True,
            "method": "uv sync",
            "message": "Dependencies installed"
        }
        mock_gen_lock.return_value = Path("uv.lock")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create pyproject.toml to trigger lock generation
            (project_path / "pyproject.toml").write_text("[project]\nname = 'test'")
            
            result = setup_project_environment(
                project_path,
                install_deps=True,
                dev=True,
                create_artifact=False  # Skip artifact creation in tests
            )
            
            assert result["success"] is True
            assert result["detected_python_version"] == "3.11"
            assert result["python_path"] == str(Path("/usr/local/bin/python3.11"))
            assert result["venv_path"] == str(Path(".venv"))
            assert len(result["steps"]) == 4  # ensure_python, create_venv, install_deps, generate_lock
            
            # Verify all steps succeeded
            for step in result["steps"]:
                assert step["success"] is True
    
    @mock.patch('DHT.modules.uv_prefect_tasks.check_uv_available')
    def test_setup_project_environment_no_uv(self, mock_check_uv):
        """Test project setup when UV is not available."""
        mock_check_uv.return_value = {
            "available": False,
            "error": "UV not found"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            result = setup_project_environment(
                project_path,
                create_artifact=False
            )
            
            assert result["success"] is False
            assert result["error"] == "UV is not available"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])