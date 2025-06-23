#!/usr/bin/env python3
"""
Unit tests for Docker-related components.  Tests individual components of the container deployment system.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Unit tests for Docker-related components.

Tests individual components of the container deployment system.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial unit tests for Docker components
# - Tests for DockerManager, DockerfileGenerator, ContainerTestRunner
# - Tests error handling and edge cases
# - Tests configuration and customization options
#

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from DHT.modules.container_test_runner import ContainerTestRunner, TestFramework
from DHT.modules.docker_manager import DockerError, DockerManager
from DHT.modules.dockerfile_generator import DockerfileGenerator, ProjectType


class TestDockerManager:
    """Unit tests for DockerManager class."""

    def test_docker_manager_initialization(self) -> Any:
        """Test DockerManager initialization."""
        manager = DockerManager()
        assert manager is not None
        assert hasattr(manager, "client")
        assert hasattr(manager, "logger")

    @patch("shutil.which")
    def test_is_docker_available(self, mock_which) -> Any:
        """Test Docker availability check."""
        manager = DockerManager()

        # Docker available
        mock_which.return_value = "/usr/bin/docker"
        assert manager.is_docker_available() is True

        # Docker not available
        mock_which.return_value = None
        assert manager.is_docker_available() is False

    @patch("docker.from_env")
    def test_is_daemon_running(self, mock_docker) -> Any:
        """Test Docker daemon status check."""
        manager = DockerManager()

        # Daemon running
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_docker.return_value = mock_client

        assert manager.is_daemon_running() is True

        # Daemon not running
        mock_client.ping.side_effect = Exception("Connection failed")
        assert manager.is_daemon_running() is False

    def test_is_port_available(self) -> Any:
        """Test port availability check."""
        manager = DockerManager()

        # Test with likely available high port
        assert manager.is_port_available(59999) is True

        # Test with reserved port
        assert manager.is_port_available(0) is False

        # Test with negative port
        assert manager.is_port_available(-1) is False

        # Test with port out of range
        assert manager.is_port_available(70000) is False

    @patch("docker.from_env")
    def test_build_image_success(self, mock_docker) -> Any:
        """Test successful Docker image build."""
        manager = DockerManager()

        # Mock successful build
        mock_client = MagicMock()
        mock_image = MagicMock()
        mock_logs = [{"stream": "Step 1/5 : FROM python:3.11\n"}, {"stream": "Successfully built abc123\n"}]

        mock_client.images.build.return_value = (mock_image, mock_logs)
        mock_docker.return_value = mock_client

        success, logs = manager.build_image(Path("/test/project"), "test:latest")

        assert success is True
        assert "Successfully built" in logs
        mock_client.images.build.assert_called_once()

    @patch("docker.from_env")
    def test_build_image_failure(self, mock_docker) -> Any:
        """Test Docker image build failure."""
        manager = DockerManager()

        # Mock build failure
        mock_client = MagicMock()
        mock_client.images.build.side_effect = Exception("Build failed")
        mock_docker.return_value = mock_client

        with pytest.raises(DockerError, match="Failed to build image"):
            manager.build_image(Path("/test/project"), "test:latest")

    @patch("docker.from_env")
    def test_run_container(self, mock_docker) -> Any:
        """Test running a container."""
        manager = DockerManager()

        # Mock container run
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.status = "running"

        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client

        container = manager.run_container(
            image="test:latest",
            name="test-container",
            ports={"8000/tcp": 8000},
            environment={"ENV": "test"},
            detach=True,
        )

        assert container is not None
        assert container.id == "abc123"
        mock_client.containers.run.assert_called_once()

    @patch("docker.from_env")
    def test_stop_container(self, mock_docker) -> Any:
        """Test stopping a container."""
        manager = DockerManager()

        # Mock container stop
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client

        manager.stop_container("test-container")

        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()

    @patch("docker.from_env")
    def test_stream_logs(self, mock_docker) -> Any:
        """Test streaming container logs."""
        manager = DockerManager()

        # Mock log streaming
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.logs.return_value = b"Log line 1\nLog line 2\n"

        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client

        logs = manager.stream_logs("test-container", follow=False)

        assert "Log line 1" in logs
        assert "Log line 2" in logs
        mock_container.logs.assert_called_once()


class TestDockerfileGenerator:
    """Unit tests for DockerfileGenerator class."""

    def test_dockerfile_generator_initialization(self) -> Any:
        """Test DockerfileGenerator initialization."""
        generator = DockerfileGenerator()
        assert generator is not None
        assert hasattr(generator, "templates")

    def test_detect_project_type_web(self, tmp_path) -> Any:
        """Test detecting web application project."""
        generator = DockerfileGenerator()

        # Create web app indicators
        (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["fastapi"]')

        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.WEB

    def test_detect_project_type_cli(self, tmp_path) -> Any:
        """Test detecting CLI application project."""
        generator = DockerfileGenerator()

        # Create CLI app indicators
        (tmp_path / "cli.py").write_text("import click\n@click.command()\ndef main() -> Any: pass")
        (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["click"]')

        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.CLI

    def test_detect_project_type_library(self, tmp_path) -> Any:
        """Test detecting library project."""
        generator = DockerfileGenerator()

        # Create library indicators
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__init__.py").touch()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mylib"')

        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.LIBRARY

    def test_find_main_entry_points(self, tmp_path) -> Any:
        """Test finding main entry points."""
        generator = DockerfileGenerator()

        # Create multiple entry points
        (tmp_path / "main.py").write_text("if __name__ == '__main__': pass")
        (tmp_path / "app.py").write_text("app = Flask(__name__)")
        (tmp_path / "cli.py").write_text("def main() -> Any: pass")

        entry_points = generator.find_entry_points(tmp_path)

        assert "main.py" in entry_points
        assert "app.py" in entry_points
        assert "cli.py" in entry_points

    def test_detect_python_version(self, tmp_path) -> Any:
        """Test detecting Python version from project."""
        generator = DockerfileGenerator()

        # Test pyproject.toml
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"')
        version = generator.detect_python_version(tmp_path)
        assert version == "3.11"

        # Test .python-version
        (tmp_path / ".python-version").write_text("3.12.0")
        version = generator.detect_python_version(tmp_path)
        assert version == "3.12"

        # Test default
        (tmp_path / "pyproject.toml").unlink()
        (tmp_path / ".python-version").unlink()
        version = generator.detect_python_version(tmp_path)
        assert version == "3.11"  # Default

    def test_generate_basic_dockerfile(self) -> Any:
        """Test generating basic Dockerfile."""
        generator = DockerfileGenerator()

        project_info = {
            "type": ProjectType.WEB,
            "python_version": "3.11",
            "main_entry": "main.py",
            "dependencies": ["fastapi", "uvicorn"],
            "has_tests": True,
            "ports": [8000],  # Add ports for web project
        }

        dockerfile = generator.generate_dockerfile(project_info)

        assert "FROM python:3.11-slim" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert "RUN curl -LsSf https://astral.sh/uv/install.sh | sh" in dockerfile
        assert "COPY . ." in dockerfile
        assert "RUN uv sync" in dockerfile
        assert "EXPOSE 8000" in dockerfile
        assert 'CMD ["uv", "run", "python", "main.py"]' in dockerfile

    def test_generate_multistage_dockerfile(self) -> Any:
        """Test generating multi-stage Dockerfile."""
        generator = DockerfileGenerator()

        project_info = {"type": ProjectType.WEB, "python_version": "3.11", "main_entry": "main.py"}

        dockerfile = generator.generate_dockerfile(project_info, multi_stage=True, production=True)

        assert "AS builder" in dockerfile
        assert "FROM python:3.11-slim AS runtime" in dockerfile
        assert "COPY --from=builder" in dockerfile
        assert "RUN useradd" in dockerfile  # Non-root user
        assert "USER appuser" in dockerfile

    def test_handle_existing_dockerfile(self, tmp_path) -> Any:
        """Test handling existing Dockerfile."""
        generator = DockerfileGenerator()

        # Create existing Dockerfile
        existing = "FROM python:3.12\nCMD ['python', 'app.py']"
        (tmp_path / "Dockerfile").write_text(existing)

        dockerfile = generator.get_dockerfile(tmp_path)
        assert dockerfile == existing  # Should use existing


class TestContainerTestRunner:
    """Unit tests for ContainerTestRunner class."""

    def test_container_test_runner_initialization(self) -> Any:
        """Test ContainerTestRunner initialization."""
        runner = ContainerTestRunner()
        assert runner is not None
        assert hasattr(runner, "docker_manager")

    def test_run_pytest(self) -> Any:
        """Test running pytest in container."""
        runner = ContainerTestRunner()

        # Mock the docker manager's exec_command method
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager

        # Mock pytest output
        pytest_output = """
============================= test session starts ==============================
collected 5 items

tests/test_main.py::test_example PASSED
tests/test_main.py::test_app PASSED
tests/test_utils.py::test_helper PASSED
tests/test_utils.py::test_error FAILED
tests/test_integration.py::test_api SKIPPED

=========================== short test summary info ============================
FAILED tests/test_utils.py::test_error - AssertionError
========================= 3 passed, 1 failed, 1 skipped =========================
"""

        # Mock exec_command to return exit_code and output as string
        mock_docker_manager.exec_command.return_value = (1, pytest_output)

        results = runner.run_pytest("test-container")

        assert results["total"] == 5
        assert results["passed"] == 3
        assert results["failed"] == 1
        assert results["skipped"] == 1
        assert "test_example" in results["tests"]
        assert results["tests"]["test_example"] == "passed"
        assert results["tests"]["test_error"] == "failed"

    def test_run_playwright(self) -> Any:
        """Test running Playwright tests in container."""
        runner = ContainerTestRunner()

        # Mock the docker manager's exec_command method
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager

        # Mock browser installation and test execution
        mock_docker_manager.exec_command.side_effect = [
            (0, "Browsers installed"),  # playwright install
            (0, "3 passed (5s)"),  # test execution
        ]

        results = runner.run_playwright("test-container")

        assert results["total"] == 3
        assert results["passed"] == 3
        assert results["failed"] == 0

    def test_format_results_table(self) -> Any:
        """Test formatting results as table."""
        runner = ContainerTestRunner()

        results = {
            TestFramework.PYTEST: {"total": 10, "passed": 7, "failed": 2, "skipped": 1},
            TestFramework.PLAYWRIGHT: {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
        }

        table = runner.format_results_table(results)

        # Check table structure (grid format uses + and | characters)
        assert "+" in table
        assert "|" in table
        assert "-" in table

        # Check content
        assert "Test Suite" in table
        assert "Passed" in table
        assert "Failed" in table
        assert "Skipped" in table
        assert "Unit Tests (pytest)" in table
        assert "E2E Tests (Playwright)" in table
        assert "10" in table
        assert "7" in table
        assert "2" in table

    def test_handle_test_failures(self) -> Any:
        """Test handling test failures in container."""
        runner = ContainerTestRunner()

        # Mock the docker manager's exec_command method
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager

        # Mock failed test output
        failed_output = """
============================= test session starts ==============================
collected 1 item

tests/test_main.py::test_app FAILED

=========================== short test summary info ============================
FAILED tests/test_main.py::test_app - AssertionError
============================= 1 failed in 0.12s ===============================
"""
        mock_docker_manager.exec_command.return_value = (1, failed_output)

        results = runner.run_pytest("test-container")

        assert results["exit_code"] == 1
        assert results["failed"] == 1
        assert "error_output" in results
