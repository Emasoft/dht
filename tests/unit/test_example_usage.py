#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Example demonstrating test_helpers.py usage in real tests
# - Shows different patterns for using the helpers effectively

"""
Example test module demonstrating test_helpers.py usage.

This shows how to use the test helpers in actual test scenarios.
"""

from unittest.mock import patch

import pytest

# Import helpers from our test_helpers module
from test_helpers import (
    cleanup_temporary_project,
    create_platform_uname_mock,
    create_project_structure,
    create_psutil_virtual_memory_mock,
    create_temporary_project,
)


class TestDHTDiagnosticScenarios:
    """Example tests using mock helpers for diagnostic scenarios."""

    @patch('platform.uname')
    @patch('psutil.virtual_memory')
    def test_system_diagnostics_macos(self, mock_vm, mock_platform):
        """Test system diagnostics on macOS."""
        # Use our helper to create proper mocks
        mock_platform.return_value = create_platform_uname_mock(
            system="Darwin",
            node="macbook-pro.local",
            release="23.1.0",
            version="Darwin Kernel Version 23.1.0",
            machine="arm64",
            processor="arm64",
        )

        mock_vm.return_value = create_psutil_virtual_memory_mock(
            total=32 * 1024 * 1024 * 1024,  # 32GB
            available=16 * 1024 * 1024 * 1024,  # 16GB
            percent=50.0,
        )

        # Now we can test code that uses platform.uname() and psutil.virtual_memory()
        import platform

        import psutil

        uname = platform.uname()
        assert uname.system == "Darwin"
        assert uname.machine == "arm64"

        vm = psutil.virtual_memory()
        assert vm.total == 32 * 1024 * 1024 * 1024
        assert vm.percent == 50.0

    @patch('platform.uname')
    def test_cross_platform_detection(self, mock_platform):
        """Test platform detection across different OSes."""
        test_cases = [
            ("Darwin", "macOS"),
            ("Linux", "Linux"),
            ("Windows", "Windows"),
        ]

        for system, _expected_name in test_cases:
            mock_platform.return_value = create_platform_uname_mock(system=system)

            import platform
            assert platform.uname().system == system


class TestDHTProjectInitialization:
    """Example tests for DHT project initialization."""

    def test_init_simple_python_project(self):
        """Test initializing a simple Python project."""
        project_path, metadata = create_temporary_project(
            project_type="simple",
            project_name="my_simple_app",
            python_version="3.11",
        )

        try:
            # Verify project structure
            assert project_path.exists()
            assert (project_path / "pyproject.toml").exists()
            assert (project_path / "main.py").exists()
            assert (project_path / ".python-version").exists()

            # Check Python version
            python_version = (project_path / ".python-version").read_text().strip()
            assert python_version == "3.11"

            # Simulate DHT operations on the project
            # This is where you'd test actual DHT functionality

        finally:
            cleanup_temporary_project(project_path)

    def test_init_django_project_with_full_setup(self):
        """Test initializing a Django project with all features."""
        project_path, metadata = create_temporary_project(
            project_type="django",
            project_name="my_django_site",
            python_version="3.10",
            include_tests=True,
            include_docs=True,
            include_ci=True,
        )

        try:
            # Verify Django-specific structure
            assert (project_path / "manage.py").exists()
            assert (project_path / "my_django_site" / "settings.py").exists()
            assert (project_path / "api" / "models.py").exists()

            # Verify additional features
            assert (project_path / "tests" / "test_api.py").exists()
            assert (project_path / "docs" / "index.md").exists()
            assert (project_path / ".github" / "workflows" / "tests.yml").exists()

            # Check Django settings
            settings_path = project_path / "my_django_site" / "settings.py"
            settings_content = settings_path.read_text()
            assert "SECRET_KEY" in settings_content
            assert "DATABASES" in settings_content
            assert "rest_framework" in settings_content

        finally:
            cleanup_temporary_project(project_path)


class TestDHTProjectAnalysis:
    """Example tests for DHT project analysis features."""

    def test_analyze_ml_project_structure(self, tmp_path):
        """Test analyzing a machine learning project."""
        # Create a realistic ML project
        metadata = create_project_structure(
            tmp_path,
            project_type="ml",
            project_name="image_classifier",
            python_version="3.10",
            include_tests=True,
        )

        project_dir = metadata["root"]

        # Simulate DHT's project analysis
        # Count Python files
        py_files = list(project_dir.rglob("*.py"))
        assert len(py_files) > 10  # ML projects have many Python files

        # Check for ML-specific patterns
        train_script = project_dir / "train.py"
        assert train_script.exists()
        train_content = train_script.read_text()
        assert "import torch" in train_content
        assert "import wandb" in train_content

        # Check configuration
        config_file = project_dir / "configs" / "config.yaml"
        assert config_file.exists()
        config_content = config_file.read_text()
        assert "model:" in config_content
        assert "dataset:" in config_content

    def test_analyze_fullstack_project_dependencies(self, tmp_path):
        """Test analyzing dependencies in a full-stack project."""
        metadata = create_project_structure(
            tmp_path,
            project_type="fullstack",
            project_name="saas_app",
        )

        project_dir = metadata["root"]

        # Check backend dependencies
        pyproject = project_dir / "pyproject.toml"
        pyproject_content = pyproject.read_text()
        assert "fastapi" in pyproject_content
        assert "sqlalchemy" in pyproject_content
        assert "pydantic" in pyproject_content

        # Check frontend dependencies
        package_json = project_dir / "frontend" / "package.json"
        package_json_content = package_json.read_text()
        assert '"next"' in package_json_content
        assert '"react"' in package_json_content
        assert '"typescript"' in package_json_content


class TestDHTEnvironmentSetup:
    """Example tests for DHT environment setup scenarios."""

    def test_setup_library_project_for_distribution(self):
        """Test setting up a library project for PyPI distribution."""
        project_path, metadata = create_temporary_project(
            project_type="library",
            project_name="my_awesome_lib",
            python_version="3.9",  # Test with older Python for compatibility
        )

        try:
            # Verify library structure
            lib_dir = project_path / "my_awesome_lib"
            assert lib_dir.exists()
            assert (lib_dir / "__init__.py").exists()
            assert (lib_dir / "version.py").exists()
            assert (lib_dir / "cli.py").exists()
            assert (lib_dir / "py.typed").exists()  # Type hints marker

            # Check package metadata
            pyproject = project_path / "pyproject.toml"
            content = pyproject.read_text()
            assert '[project.scripts]' in content
            assert 'my_awesome_lib = "my_awesome_lib.cli:main"' in content

            # Verify version management
            version_file = lib_dir / "version.py"
            version_content = version_file.read_text()
            assert '__version__ = "0.1.0"' in version_content

        finally:
            cleanup_temporary_project(project_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
