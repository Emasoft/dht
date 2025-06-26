#!/usr/bin/env python3
"""
Tests for DHT Project Generator Flow.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created comprehensive test suite for project generator flow
# - Tests all template generation tasks
# - Tests project detection and orchestration
#

import tempfile
from pathlib import Path

from src.DHT.modules.flows.project_generator_flow import (
    detect_project_requirements_task,
    generate_project_flow,
)


class TestProjectRequirementsDetection:
    """Test project requirements detection logic."""

    def test_detect_django_requirements(self):
        """Test Django project requirements are detected correctly."""
        requirements = detect_project_requirements_task("django", ["api", "celery"])

        assert requirements["use_docker"] is True
        assert requirements["use_postgres"] is True
        assert requirements["use_celery"] is True
        assert requirements["django_rest"] is True
        assert requirements["django_admin"] is True
        assert requirements["use_migrations"] is True

    def test_detect_fastapi_requirements(self):
        """Test FastAPI project requirements are detected correctly."""
        requirements = detect_project_requirements_task("fastapi", ["redis"])

        assert requirements["use_docker"] is True
        assert requirements["use_postgres"] is True
        assert requirements["use_redis"] is True
        assert requirements["use_alembic"] is True
        assert requirements["async_support"] is True
        assert requirements["api_docs"] is True
        assert requirements["use_pydantic"] is True

    def test_detect_cli_requirements(self):
        """Test CLI project requirements are detected correctly."""
        requirements = detect_project_requirements_task("cli", [])

        assert requirements["use_docker"] is False
        assert requirements["use_postgres"] is False
        assert requirements["use_redis"] is False
        assert requirements["use_pytest"] is True

    def test_detect_library_requirements(self):
        """Test library project requirements are detected correctly."""
        requirements = detect_project_requirements_task("library", ["mongodb"])

        assert requirements["use_docker"] is False
        assert requirements["use_postgres"] is False
        assert requirements["use_mongodb"] is True
        assert requirements["use_pytest"] is True


class TestProjectGeneratorFlow:
    """Test complete project generation flow."""

    def test_generate_fastapi_project(self):
        """Test generating a complete FastAPI project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = generate_project_flow(
                project_path=project_path,
                project_name="test_api",
                project_type="fastapi",
                description="Test FastAPI project",
                author_name="Test Author",
                author_email="test@example.com",
                python_version="3.11",
                features=["redis"],
                port=8000,
            )

            assert result is True

            # Check project structure
            project_dir = project_path / "test_api"
            assert project_dir.exists()
            assert (project_dir / "src" / "test_api").exists()
            assert (project_dir / "tests").exists()

            # Check generated files
            assert (project_dir / ".gitignore").exists()
            assert (project_dir / "LICENSE").exists()
            assert (project_dir / "README.md").exists()
            assert (project_dir / "pyproject.toml").exists()
            assert (project_dir / "Makefile").exists()
            assert (project_dir / ".env.example").exists()

            # Check FastAPI specific files
            assert (project_dir / "src" / "test_api" / "main.py").exists()
            assert (project_dir / "src" / "test_api" / "database.py").exists()
            assert (project_dir / "src" / "test_api" / "redis_client.py").exists()

            # Check Docker files
            assert (project_dir / "Dockerfile").exists()
            assert (project_dir / "docker-compose.yml").exists()
            assert (project_dir / ".dockerignore").exists()

            # Check testing configuration
            assert (project_dir / "pytest.ini").exists()
            assert (project_dir / "tests" / "conftest.py").exists()
            assert (project_dir / ".coveragerc").exists()

            # Check CI/CD
            assert (project_dir / ".github" / "workflows" / "ci.yml").exists()
            assert (project_dir / ".pre-commit-config.yaml").exists()

    def test_generate_django_project(self):
        """Test generating a complete Django project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = generate_project_flow(
                project_path=project_path,
                project_name="test_django",
                project_type="django",
                description="Test Django project",
                author_name="Test Author",
                python_version="3.11",
                features=["api", "celery"],
            )

            assert result is True

            # Check Django specific structure
            project_dir = project_path / "test_django"
            django_dir = project_dir / "src" / "test_django"

            assert (django_dir / "apps").exists()
            assert (django_dir / "static").exists()
            assert (django_dir / "templates").exists()
            assert (django_dir / "settings.py").exists()

    def test_generate_cli_project(self):
        """Test generating a CLI project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = generate_project_flow(
                project_path=project_path,
                project_name="test_cli",
                project_type="cli",
                description="Test CLI tool",
                license_type="Apache",
            )

            assert result is True

            # Check CLI specific configuration
            project_dir = project_path / "test_cli"

            # Should not have web-specific files
            assert not (project_dir / "docker-compose.yml").exists()
            assert (project_dir / "Dockerfile").exists()  # CLI projects can still be containerized

    def test_project_with_custom_features(self):
        """Test project generation with custom features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            result = generate_project_flow(
                project_path=project_path,
                project_name="test_custom",
                project_type="fastapi",
                features=["mongodb", "redis", "docker"],
            )

            assert result is True

            # Check MongoDB configuration was generated
            project_dir = project_path / "test_custom"
            assert (project_dir / "src" / "test_custom" / "mongodb_client.py").exists()
            assert (project_dir / "src" / "test_custom" / "redis_client.py").exists()
