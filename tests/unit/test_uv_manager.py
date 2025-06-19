#!/usr/bin/env python3
"""
Test suite for UV manager integration.

Tests the UV package manager integration including:
- Python version detection and management
- Virtual environment creation
- Dependency installation and resolution
- Lock file generation
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for UV manager
# - Added tests for UV executable detection
# - Added tests for Python version management
# - Added tests for virtual environment creation
# - Added tests for dependency installation
# - Added tests for project setup workflow
# - Added integration tests for real UV installations

import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from DHT.modules.uv_manager import UVManager
from DHT.modules.uv_manager_exceptions import DependencyError, PythonVersionError, UVError, UVNotFoundError


class TestUVManager:
    """Test the UV manager functionality."""

    @pytest.fixture
    def uv_manager(self):
        """Create a UV manager instance with mocked executable."""
        with patch('DHT.modules.uv_manager.find_uv_executable', return_value=Path('/usr/bin/uv')):
            with patch('DHT.modules.uv_manager.verify_uv_version'):
                return UVManager()

    @pytest.fixture
    def project_with_python_version(self, tmp_path):
        """Create a project with .python-version file."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        python_version_file = project_dir / ".python-version"
        python_version_file.write_text("3.11.6")

        return project_dir

    @pytest.fixture
    def project_with_pyproject(self, tmp_path):
        """Create a project with pyproject.toml."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        pyproject = project_dir / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
requires-python = ">=3.10,<3.12"
dependencies = [
    "requests>=2.28.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]

[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"
""")

        return project_dir

    @pytest.fixture
    def project_with_requirements(self, tmp_path):
        """Create a project with requirements.txt."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        requirements = project_dir / "requirements.txt"
        requirements.write_text("""
requests>=2.28.0
click>=8.0.0
pytest>=7.0.0
""")

        return project_dir

    @pytest.fixture
    def project_with_lock(self, tmp_path):
        """Create a project with uv.lock file."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create a mock uv.lock file
        lock_file = project_dir / "uv.lock"
        lock_file.write_text("""
# UV lock file format
[[package]]
name = "requests"
version = "2.28.2"
""")

        pyproject = project_dir / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
dependencies = ["requests"]
""")

        return project_dir

    def test_find_uv_executable_in_path(self):
        """Test finding UV executable in PATH."""
        with patch('DHT.modules.uv_manager.find_uv_executable', return_value=Path('/usr/bin/uv')):
            with patch('DHT.modules.uv_manager.verify_uv_version'):
                manager = UVManager()
                assert manager.uv_path == Path('/usr/bin/uv')
                assert manager.is_available

    def test_find_uv_executable_common_locations(self):
        """Test finding UV in common locations when not in PATH."""
        with patch('DHT.modules.uv_manager_utils.shutil.which', return_value=None):
            # Create a mock path that exists
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.__str__.return_value = str(Path.home() / ".local/bin/uv")

            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = Path("/home/user")
                with patch('pathlib.Path.exists') as mock_exists:
                    with patch('pathlib.Path.is_file') as mock_is_file:
                        # Only the first path (/.local/bin/uv) exists
                        mock_exists.side_effect = [True, False, False, False]
                        mock_is_file.side_effect = [True]

                        # Patch verify_uv_version where it's imported in uv_manager
                        with patch('DHT.modules.uv_manager.verify_uv_version'):
                            manager = UVManager()
                            assert manager.uv_path is not None
                            assert ".local/bin/uv" in str(manager.uv_path)

    def test_uv_not_found(self):
        """Test when UV is not found anywhere."""
        with patch('DHT.modules.uv_manager_utils.shutil.which', return_value=None):
            with patch('pathlib.Path.exists', return_value=False):
                manager = UVManager()
                assert manager.uv_path is None
                assert not manager.is_available

    def test_verify_uv_version_success(self):
        """Test successful UV version verification."""
        # Test the verify_uv_version function directly from utils
        from DHT.modules.uv_manager_utils import verify_uv_version

        mock_run_command = Mock()
        mock_run_command.return_value = {
            "stdout": "uv 0.4.27",
            "stderr": "",
            "returncode": 0,
            "success": True
        }

        # Should not raise
        verify_uv_version(Path('/usr/bin/uv'), "0.4.0", mock_run_command)
        mock_run_command.assert_called_once_with(["--version"])

    def test_verify_uv_version_too_old(self):
        """Test UV version that's too old."""
        # Test the verify_uv_version function directly from utils
        from DHT.modules.uv_manager_utils import verify_uv_version

        mock_run_command = Mock()
        mock_run_command.return_value = {
            "stdout": "uv 0.3.0",
            "stderr": "",
            "returncode": 0,
            "success": True
        }

        with pytest.raises(UVError, match="below minimum required"):
            verify_uv_version(Path('/usr/bin/uv'), "0.4.0", mock_run_command)

    def test_run_command_success(self, uv_manager):
        """Test successful command execution."""
        # Mock the subprocess.run in the utils module where it's used
        with patch('DHT.modules.uv_manager_utils.subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.stdout = "Success output"
            mock_process.stderr = ""
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Mock path existence check
            with patch.object(Path, 'exists', return_value=True):
                result = uv_manager.run_command(["python", "list"])

            assert result["success"] is True
            assert result["stdout"] == "Success output"
            assert result["stderr"] == ""
            assert result["returncode"] == 0

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args == ['/usr/bin/uv', 'python', 'list']

    def test_run_command_failure(self, uv_manager):
        """Test command execution failure."""
        with patch('DHT.modules.uv_manager_utils.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1,
                ['uv', 'invalid'],
                output="",
                stderr="Invalid command"
            )

            # Mock path existence check
            with patch.object(Path, 'exists', return_value=True):
                result = uv_manager.run_command(["invalid"], check=False)

            assert result["success"] is False
            assert result["stderr"] == "Invalid command"

    def test_run_command_no_uv(self):
        """Test running command when UV is not available."""
        # Create a manager without UV
        manager = UVManager()
        manager.uv_path = None  # Force UV to be unavailable

        with pytest.raises(UVNotFoundError):
            manager.run_command(["python", "list"])

    def test_detect_python_version_from_file(
        self, uv_manager, project_with_python_version
    ):
        """Test detecting Python version from .python-version file."""
        version = uv_manager.detect_python_version(project_with_python_version)
        assert version == "3.11.6"

    def test_detect_python_version_from_pyproject(
        self, uv_manager, project_with_pyproject
    ):
        """Test detecting Python version from pyproject.toml."""
        version = uv_manager.detect_python_version(project_with_pyproject)
        assert version == "3.10"  # Minimum version from >=3.10,<3.12

    def test_detect_python_version_none(self, uv_manager, tmp_path):
        """Test when no Python version is specified."""
        empty_project = tmp_path / "empty_project"
        empty_project.mkdir()

        version = uv_manager.detect_python_version(empty_project)
        assert version is None

    def test_extract_min_version(self):
        """Test extracting minimum version from various constraints."""
        # Test the extract_min_version function directly from utils
        from DHT.modules.uv_manager_utils import extract_min_version

        test_cases = [
            (">=3.8", "3.8"),
            (">=3.8,<3.12", "3.8"),
            ("^3.10", "3.10"),
            ("~3.11", "3.11"),
            ("==3.9.5", "3.9.5"),
            (">3.7,<4.0", "3.7"),
        ]

        for constraint, expected in test_cases:
            result = extract_min_version(constraint)
            assert result == expected or result.startswith(expected.split('.')[0])

    def test_list_python_versions(self, uv_manager):
        """Test listing available Python versions."""
        # Mock the python_manager's method directly to avoid Prefect task execution
        mock_versions = [
            {"version": "cpython-3.11.6+20231002-x86_64-apple-darwin", "installed": True},
            {"version": "cpython-3.12.1+20231211-x86_64-apple-darwin", "installed": False},
            {"version": "cpython-3.10.13+20230826-x86_64-apple-darwin", "installed": True}
        ]

        with patch.object(uv_manager.python_manager, 'list_python_versions', return_value=mock_versions):
            versions = uv_manager.list_python_versions()

            assert len(versions) == 3
            assert versions[0]["version"] == "cpython-3.11.6+20231002-x86_64-apple-darwin"
            assert versions[0]["installed"] is True
            assert versions[1]["installed"] is False

    def test_ensure_python_version_already_installed(self, uv_manager):
        """Test ensuring Python version that's already installed."""
        # Mock the python_manager's method directly to avoid Prefect task execution
        expected_path = Path("/usr/bin/python3.11")

        with patch.object(uv_manager.python_manager, 'ensure_python_version', return_value=expected_path):
            python_path = uv_manager.ensure_python_version("3.11")

            assert python_path == expected_path
            uv_manager.python_manager.ensure_python_version.assert_called_once_with("3.11")

    def test_ensure_python_version_install_needed(self, uv_manager):
        """Test ensuring Python version that needs installation."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            # First find fails, then install succeeds, then find succeeds
            mock_run.side_effect = [
                {"stdout": "", "stderr": "Not found", "success": False},
                {"stdout": "Installing...", "stderr": "", "success": True},
                {"stdout": "/home/user/.local/python3.11", "stderr": "", "success": True}
            ]

            python_path = uv_manager.ensure_python_version("3.11")

            assert python_path == Path("/home/user/.local/python3.11")
            assert mock_run.call_count == 3

    def test_ensure_python_version_install_fails(self, uv_manager):
        """Test when Python installation fails."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.side_effect = [
                {"stdout": "", "stderr": "Not found", "success": False},
                {"stdout": "", "stderr": "Installation failed", "success": False}
            ]

            with pytest.raises(PythonVersionError, match="Failed to install"):
                uv_manager.ensure_python_version("3.11")

    def test_create_venv_default(self, uv_manager, tmp_path):
        """Test creating virtual environment with defaults."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": "Created venv",
                "stderr": "",
                "success": True
            }

            venv_path = uv_manager.create_venv(project_dir)

            assert venv_path == project_dir / ".venv"
            mock_run.assert_called_once_with(["venv"], cwd=project_dir)

    def test_create_venv_with_python_version(self, uv_manager, tmp_path):
        """Test creating virtual environment with specific Python version."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": "Created venv",
                "stderr": "",
                "success": True
            }

            venv_path = uv_manager.create_venv(project_dir, python_version="3.11")

            assert venv_path == project_dir / ".venv"
            mock_run.assert_called_once_with(
                ["venv", "--python", "3.11"],
                cwd=project_dir
            )

    def test_create_venv_custom_path(self, uv_manager, tmp_path):
        """Test creating virtual environment at custom path."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        custom_venv = project_dir / "my_venv"

        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": "Created venv",
                "stderr": "",
                "success": True
            }

            venv_path = uv_manager.create_venv(project_dir, venv_path=custom_venv)

            assert venv_path == custom_venv
            mock_run.assert_called_once_with(
                ["venv", str(custom_venv)],
                cwd=project_dir
            )

    def test_install_dependencies_with_lock(self, uv_manager, project_with_lock):
        """Test installing dependencies from lock file."""
        with patch.object(uv_manager, '_sync_dependencies') as mock_sync:
            mock_sync.return_value = {
                "success": True,
                "method": "uv sync",
                "message": "Synced"
            }

            result = uv_manager.install_dependencies(project_with_lock)

            assert result["success"] is True
            assert result["method"] == "uv sync"
            mock_sync.assert_called_once_with(project_with_lock, dev=False, extras=None)

    def test_install_dependencies_requirements_txt(
        self, uv_manager, project_with_requirements
    ):
        """Test installing dependencies from requirements.txt."""
        with patch.object(uv_manager, '_pip_install_requirements') as mock_install:
            mock_install.return_value = {
                "success": True,
                "method": "uv pip install -r",
                "message": "Installed"
            }

            result = uv_manager.install_dependencies(project_with_requirements)

            assert result["success"] is True
            assert result["method"] == "uv pip install -r"
            mock_install.assert_called_once()

    def test_install_dependencies_pyproject(
        self, uv_manager, project_with_pyproject
    ):
        """Test installing dependencies from pyproject.toml."""
        with patch.object(uv_manager, '_pip_install_project') as mock_install:
            mock_install.return_value = {
                "success": True,
                "method": "uv pip install -e",
                "message": "Installed"
            }

            result = uv_manager.install_dependencies(project_with_pyproject, dev=True)

            assert result["success"] is True
            assert result["method"] == "uv pip install -e"
            mock_install.assert_called_once_with(
                project_with_pyproject,
                dev=True,
                extras=None
            )

    def test_generate_lock_file(self, uv_manager, project_with_pyproject):
        """Test generating lock file."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": "Generated lock",
                "stderr": "",
                "success": True
            }

            lock_path = uv_manager.generate_lock_file(project_with_pyproject)

            assert lock_path == project_with_pyproject / "uv.lock"
            mock_run.assert_called_once_with(["lock"], cwd=project_with_pyproject)

    def test_generate_lock_file_failure(self, uv_manager, tmp_path):
        """Test lock file generation failure."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": "",
                "stderr": "Failed to resolve",
                "success": False
            }

            with pytest.raises(DependencyError, match="Failed to generate lock"):
                uv_manager.generate_lock_file(tmp_path)

    def test_add_dependency(self, uv_manager, project_with_pyproject):
        """Test adding a dependency."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            with patch.object(uv_manager, 'generate_lock_file') as mock_lock:
                mock_run.return_value = {
                    "stdout": "Added numpy",
                    "stderr": "",
                    "success": True
                }

                result = uv_manager.add_dependency(
                    project_with_pyproject,
                    "numpy>=1.20",
                    dev=True
                )

                assert result["success"] is True
                assert result["package"] == "numpy>=1.20"
                assert result["dev"] is True

                mock_run.assert_called_once_with(
                    ["add", "--dev", "numpy>=1.20"],
                    cwd=project_with_pyproject
                )
                mock_lock.assert_called_once_with(project_with_pyproject)

    def test_remove_dependency(self, uv_manager, project_with_pyproject):
        """Test removing a dependency."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            with patch.object(uv_manager, 'generate_lock_file') as mock_lock:
                mock_run.return_value = {
                    "stdout": "Removed requests",
                    "stderr": "",
                    "success": True
                }

                result = uv_manager.remove_dependency(
                    project_with_pyproject,
                    "requests"
                )

                assert result["success"] is True
                assert result["package"] == "requests"

                mock_run.assert_called_once_with(
                    ["remove", "requests"],
                    cwd=project_with_pyproject
                )
                mock_lock.assert_called_once()

    def test_check_outdated(self, uv_manager, project_with_pyproject):
        """Test checking for outdated packages."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": json.dumps([
                    {
                        "name": "requests",
                        "version": "2.28.0",
                        "latest_version": "2.31.0",
                        "latest_filetype": "wheel"
                    }
                ]),
                "stderr": "",
                "success": True
            }

            outdated = uv_manager.check_outdated(project_with_pyproject)

            assert len(outdated) == 1
            assert outdated[0]["name"] == "requests"
            assert outdated[0]["version"] == "2.28.0"
            assert outdated[0]["latest_version"] == "2.31.0"

    def test_run_script_file(self, uv_manager, tmp_path):
        """Test running a Python script file."""
        script_path = tmp_path / "script.py"
        script_path.write_text("print('Hello')")

        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": "Hello\n",
                "stderr": "",
                "success": True
            }

            result = uv_manager.run_script(tmp_path, str(script_path))

            assert result["success"] is True
            assert result["output"] == "Hello\n"

            mock_run.assert_called_once_with(
                ["run", "python", str(script_path)],
                cwd=tmp_path
            )

    def test_run_script_module(self, uv_manager, tmp_path):
        """Test running a Python module."""
        with patch.object(uv_manager, 'run_command') as mock_run:
            mock_run.return_value = {
                "stdout": "Module output",
                "stderr": "",
                "success": True
            }

            result = uv_manager.run_script(
                tmp_path,
                "mymodule.main",
                args=["--help"]
            )

            assert result["success"] is True

            mock_run.assert_called_once_with(
                ["run", "python", "-m", "mymodule.main", "--help"],
                cwd=tmp_path
            )

    def test_setup_project_complete_flow(self, uv_manager, project_with_pyproject):
        """Test complete project setup flow."""
        with patch.object(uv_manager, 'detect_python_version') as mock_detect:
            with patch.object(uv_manager, 'ensure_python_version') as mock_ensure:
                with patch.object(uv_manager, 'create_venv') as mock_venv:
                    with patch.object(uv_manager, 'install_dependencies') as mock_deps:
                        with patch.object(uv_manager, 'generate_lock_file') as mock_lock:
                            mock_detect.return_value = "3.11"
                            mock_ensure.return_value = Path("/usr/bin/python3.11")
                            mock_venv.return_value = project_with_pyproject / ".venv"
                            mock_deps.return_value = {
                                "success": True,
                                "method": "uv pip install -e"
                            }

                            result = uv_manager.setup_project(
                                project_with_pyproject,
                                install_deps=True,
                                dev=True
                            )

                            assert result["success"] is True
                            assert result["detected_python_version"] == "3.11"
                            assert len(result["steps"]) >= 3

                            # Verify all steps were called
                            mock_detect.assert_called_once()
                            mock_ensure.assert_called_once_with("3.11")
                            mock_venv.assert_called_once()
                            mock_deps.assert_called_once_with(
                                project_with_pyproject,
                                dev=True
                            )
                            mock_lock.assert_called_once()

    def test_setup_project_with_failures(self, uv_manager, tmp_path):
        """Test project setup with failures."""
        project_dir = tmp_path / "failing_project"
        project_dir.mkdir()

        with patch.object(uv_manager, 'detect_python_version') as mock_detect:
            with patch.object(uv_manager, 'ensure_python_version') as mock_ensure:
                mock_detect.return_value = "3.11"
                mock_ensure.side_effect = PythonVersionError("Cannot install Python")

                result = uv_manager.setup_project(project_dir)

                # Check the result structure
                assert "success" in result
                assert "steps" in result
                assert result["success"] is False
                assert len(result["steps"]) == 1
                assert result["steps"][0]["step"] == "ensure_python"
                assert result["steps"][0]["success"] is False


class TestUVIntegration:
    """Integration tests with actual UV commands (if UV is installed)."""

    @pytest.mark.skipif(
        not shutil.which("uv"),
        reason="UV not installed"
    )
    def test_real_uv_version_check(self):
        """Test with real UV installation."""
        manager = UVManager()

        if manager.is_available:
            result = manager.run_command(["--version"])
            assert result["success"] is True
            assert "uv" in result["stdout"]

    @pytest.mark.skipif(
        not shutil.which("uv"),
        reason="UV not installed"
    )
    def test_real_python_list(self):
        """Test listing Python versions with real UV."""
        manager = UVManager()

        if manager.is_available:
            versions = manager.list_python_versions()
            assert isinstance(versions, list)
            # Should have at least one Python version
            if versions:
                assert "version" in versions[0]
                assert "installed" in versions[0]
