#!/usr/bin/env python3
"""
Test suite for test_helpers.py functionality.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial creation of test_test_helpers.py to verify helper functions
# - Tests for mock factories, project creation, and utilities
# - Comprehensive coverage of all project types

"""
Test suite for test_helpers.py functionality.

This module tests:
1. Mock factory functions
2. Project structure creation
3. Path resolution utilities
4. Temporary project management
"""

import tempfile

import pytest
from test_helpers import (
    assert_project_structure,
    cleanup_temporary_project,
    create_mock_pyproject_toml,
    create_platform_uname_mock,
    create_project_structure,
    create_psutil_process_mock,
    create_psutil_virtual_memory_mock,
    create_temporary_project,
    find_dht_modules_dir,
    find_dht_root,
)


class TestMockFactories:
    """Test mock factory functions."""

    def test_platform_uname_mock(self):
        """Test platform.uname() mock creation."""
        mock_uname = create_platform_uname_mock(
            system="Linux",
            node="test-linux",
            release="5.15.0",
            version="Linux version 5.15.0",
            machine="x86_64",
            processor="x86_64",
        )

        assert mock_uname.system == "Linux"
        assert mock_uname.node == "test-linux"
        assert mock_uname.release == "5.15.0"
        assert mock_uname.version == "Linux version 5.15.0"
        assert mock_uname.machine == "x86_64"
        assert mock_uname.processor == "x86_64"

        # Test default values
        default_mock = create_platform_uname_mock()
        assert default_mock.system == "Darwin"
        assert default_mock.node == "test-machine.local"

    def test_psutil_virtual_memory_mock(self):
        """Test psutil.virtual_memory() mock creation."""
        mock_vm = create_psutil_virtual_memory_mock(
            total=32 * 1024 * 1024 * 1024,  # 32GB
            available=16 * 1024 * 1024 * 1024,  # 16GB
            percent=50.0,
        )

        assert mock_vm.total == 32 * 1024 * 1024 * 1024
        assert mock_vm.available == 16 * 1024 * 1024 * 1024
        assert mock_vm.percent == 50.0

        # Test default values
        default_mock = create_psutil_virtual_memory_mock()
        assert default_mock.total == 16 * 1024 * 1024 * 1024
        assert default_mock.percent == 50.0

    def test_psutil_process_mock(self):
        """Test psutil.Process mock creation."""
        mock_process = create_psutil_process_mock(
            pid=5678,
            name="test_process",
            status="sleeping",
            cpu_percent=10.5,
            memory_percent=2.5,
        )

        assert mock_process.pid == 5678
        assert mock_process.name() == "test_process"
        assert mock_process.status() == "sleeping"
        assert mock_process.cpu_percent() == 10.5
        assert mock_process.memory_percent() == 2.5


class TestPathResolution:
    """Test path resolution utilities."""

    def test_find_dht_root(self):
        """Test finding DHT root directory."""
        dht_root = find_dht_root()
        assert dht_root.exists()
        assert (dht_root / "dhtl_entry.py").exists() or (dht_root / "pyproject.toml").exists()
        # Check for either old or new structure
        assert (dht_root / "DHT").is_dir() or (dht_root / "src" / "DHT").is_dir()

    def test_find_dht_modules_dir(self):
        """Test finding DHT modules directory."""
        modules_dir = find_dht_modules_dir()
        assert modules_dir.exists()
        assert modules_dir.is_dir()
        assert modules_dir.name == "modules"
        assert (modules_dir / "orchestrator.py").exists()


class TestProjectStructure:
    """Test project structure creation."""

    def test_create_simple_project(self, tmp_path):
        """Test creating a simple Python project."""
        metadata = create_project_structure(
            tmp_path,
            project_type="simple",
            project_name="test_simple",
            python_version="3.10",
        )

        project_dir = metadata["root"]
        assert project_dir.exists()
        assert metadata["type"] == "simple"
        assert metadata["name"] == "test_simple"
        assert metadata["python_version"] == "3.10"

        # Check base files
        assert_project_structure(
            project_dir,
            [
                "pyproject.toml",
                "README.md",
                ".gitignore",
                ".python-version",
                "src/__init__.py",
                "main.py",
                "src/utils.py",
            ],
        )

        # Check pyproject.toml content
        pyproject_content = (project_dir / "pyproject.toml").read_text()
        assert 'name = "test_simple"' in pyproject_content
        assert 'requires-python = ">=3.10"' in pyproject_content

    def test_create_django_project(self, tmp_path):
        """Test creating a Django project."""
        metadata = create_project_structure(
            tmp_path,
            project_type="django",
            project_name="test_django",
            include_tests=False,  # Skip test generation for faster testing
            include_docs=False,
            include_ci=False,
        )

        project_dir = metadata["root"]
        assert_project_structure(
            project_dir,
            [
                "manage.py",
                "test_django/settings.py",
                "test_django/urls.py",
                "test_django/wsgi.py",
                "api/models.py",
                "api/views.py",
                "api/serializers.py",
            ],
        )

        # Check Django-specific content
        settings_content = (project_dir / "test_django" / "settings.py").read_text()
        assert "django.contrib.admin" in settings_content
        assert "rest_framework" in settings_content

    def test_create_fastapi_project(self, tmp_path):
        """Test creating a FastAPI project."""
        metadata = create_project_structure(
            tmp_path,
            project_type="fastapi",
            project_name="test_fastapi",
            include_tests=False,
            include_docs=False,
            include_ci=False,
        )

        project_dir = metadata["root"]
        assert_project_structure(
            project_dir,
            [
                "main.py",
                "app/__init__.py",
                "app/core/config.py",
                "app/core/security.py",
                "app/db/base.py",
                "app/db/session.py",
                "app/api/v1/api.py",
            ],
        )

        # Check FastAPI-specific content
        main_content = (project_dir / "main.py").read_text()
        assert "from fastapi import FastAPI" in main_content
        assert "@app.get" in main_content

    def test_create_ml_project(self, tmp_path):
        """Test creating a machine learning project."""
        metadata = create_project_structure(
            tmp_path,
            project_type="ml",
            project_name="test_ml",
            include_tests=False,
            include_docs=False,
            include_ci=False,
        )

        project_dir = metadata["root"]
        assert_project_structure(
            project_dir,
            [
                "train.py",
                "src/models/factory.py",
                "src/models/resnet.py",
                "src/models/transformer.py",
                "src/datasets/factory.py",
                "src/trainers/trainer.py",
                "configs/config.yaml",
                "notebooks/exploration.ipynb",
            ],
        )

        # Check ML-specific content
        train_content = (project_dir / "train.py").read_text()
        assert "import torch" in train_content
        assert "@hydra.main" in train_content

    def test_create_library_project(self, tmp_path):
        """Test creating a library project."""
        metadata = create_project_structure(
            tmp_path,
            project_type="library",
            project_name="test_lib",
            include_tests=False,
            include_docs=False,
            include_ci=False,
        )

        project_dir = metadata["root"]
        assert_project_structure(
            project_dir,
            [
                "test_lib/__init__.py",
                "test_lib/version.py",
                "test_lib/core.py",
                "test_lib/cli.py",
                "test_lib/py.typed",
            ],
        )

        # Check library-specific content
        init_content = (project_dir / "test_lib" / "__init__.py").read_text()
        assert "__version__" in init_content
        assert "__all__" in init_content

    def test_create_fullstack_project(self, tmp_path):
        """Test creating a full-stack project."""
        metadata = create_project_structure(
            tmp_path,
            project_type="fullstack",
            project_name="test_fullstack",
            include_tests=False,
            include_docs=False,
            include_ci=False,
        )

        project_dir = metadata["root"]
        # Check backend (FastAPI)
        assert_project_structure(
            project_dir,
            [
                "main.py",
                "app/core/config.py",
            ],
        )

        # Check frontend
        assert_project_structure(
            project_dir,
            [
                "frontend/package.json",
                "frontend/tsconfig.json",
                "frontend/src/pages/_app.tsx",
                "frontend/src/pages/index.tsx",
            ],
        )

        # Check frontend package.json
        package_json = (project_dir / "frontend" / "package.json").read_text()
        assert '"next"' in package_json
        assert '"react"' in package_json

    def test_project_with_tests(self, tmp_path):
        """Test creating a project with test structure."""
        metadata = create_project_structure(
            tmp_path,
            project_type="simple",
            project_name="test_with_tests",
            include_tests=True,
            include_docs=False,
            include_ci=False,
        )

        project_dir = metadata["root"]
        assert_project_structure(
            project_dir,
            [
                "tests/__init__.py",
                "tests/conftest.py",
                "tests/test_utils.py",
            ],
        )

    def test_project_with_docs(self, tmp_path):
        """Test creating a project with documentation."""
        metadata = create_project_structure(
            tmp_path,
            project_type="simple",
            project_name="test_with_docs",
            include_tests=False,
            include_docs=True,
            include_ci=False,
        )

        project_dir = metadata["root"]
        assert_project_structure(
            project_dir,
            [
                "docs/index.md",
                "docs/api.md",
                "docs/contributing.md",
            ],
        )

    def test_project_with_ci(self, tmp_path):
        """Test creating a project with CI/CD configuration."""
        metadata = create_project_structure(
            tmp_path,
            project_type="simple",
            project_name="test_with_ci",
            python_version="3.11",
            include_tests=False,
            include_docs=False,
            include_ci=True,
        )

        project_dir = metadata["root"]
        assert_project_structure(
            project_dir,
            [
                ".github/workflows/tests.yml",
                ".github/workflows/lint.yml",
                ".pre-commit-config.yaml",
            ],
        )

        # Check CI content includes correct Python version
        tests_workflow = (project_dir / ".github" / "workflows" / "tests.yml").read_text()
        assert '"3.11"' in tests_workflow


class TestTemporaryProjects:
    """Test temporary project management."""

    def test_create_temporary_project(self):
        """Test creating and cleaning up temporary projects."""
        project_path, metadata = create_temporary_project(
            project_type="simple",
            project_name="temp_test",
        )

        try:
            assert project_path.exists()
            assert project_path.name == "temp_test"
            assert str(project_path).startswith(tempfile.gettempdir())
            assert metadata["type"] == "simple"
            assert metadata["name"] == "temp_test"

            # Check files were created
            assert (project_path / "pyproject.toml").exists()
            assert (project_path / "main.py").exists()
        finally:
            cleanup_temporary_project(project_path)

        # Verify cleanup
        assert not project_path.exists()

    def test_temporary_project_auto_name(self):
        """Test temporary project with auto-generated name."""
        project_path, metadata = create_temporary_project(project_type="django")

        try:
            assert project_path.exists()
            assert project_path.name == "test_django_project"
            assert metadata["name"] == "test_django_project"
        finally:
            cleanup_temporary_project(project_path)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_mock_pyproject_toml(self, tmp_path):
        """Test creating a mock pyproject.toml."""
        pyproject_path = create_mock_pyproject_toml(
            tmp_path,
            name="mock-project",
            version="1.2.3",
            python_version="3.12",
            dependencies=["requests>=2.28.0", "click>=8.0.0"],
            dev_dependencies=["pytest>=7.0.0", "mypy>=1.0.0"],
        )

        assert pyproject_path.exists()
        content = pyproject_path.read_text()
        assert 'name = "mock-project"' in content
        assert 'version = "1.2.3"' in content
        assert 'requires-python = ">=3.12"' in content
        assert '"requests>=2.28.0"' in content
        assert '"mypy>=1.0.0"' in content

    def test_invalid_project_type(self, tmp_path):
        """Test error handling for invalid project type."""
        with pytest.raises(ValueError, match="Unknown project type: invalid"):
            create_project_structure(
                tmp_path,
                project_type="invalid",
                project_name="test_invalid",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
