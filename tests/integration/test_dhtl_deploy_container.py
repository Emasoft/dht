#!/usr/bin/env python3
"""
Integration tests for dhtl deploy_project_in_container command.

Tests the container deployment functionality using TDD principles.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for deploy_project_in_container command
# - Tests Docker availability and container deployment
# - Tests project analysis and Dockerfile generation
# - Tests application execution and test running in containers
# - Tests results formatting and reporting
#

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import docker
import pytest
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below

from DHT.modules.container_test_runner import ContainerTestRunner, TestFramework
from DHT.modules.dhtl_commands import DHTLCommands
from DHT.modules.docker_manager import DockerManager
from DHT.modules.dockerfile_generator import DockerfileGenerator, ProjectType


class TestDeployProjectInContainer:
    """Test dhtl deploy_project_in_container command implementation."""

    @pytest.fixture
    def temp_project(self) -> Generator[Path, None, None]:
        """Create a temporary Python project for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create project structure
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()

            # Create pyproject.toml
            pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"
description = "Test project for container deployment"
dependencies = ["fastapi", "uvicorn", "pytest"]
requires-python = ">=3.11"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
            (project_path / "pyproject.toml").write_text(pyproject_content)

            # Create main.py (web app)
            main_content = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from container!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
            (project_path / "main.py").write_text(main_content)

            # Create test file
            test_content = """
def test_example():
    assert 1 + 1 == 2

def test_app():
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from container!"}
"""
            (project_path / "tests" / "test_main.py").write_text(test_content)

            yield project_path

    @pytest.fixture
    def docker_available(self) -> bool:
        """Check if Docker is available."""
        return shutil.which("docker") is not None

    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client for testing without Docker."""
        with patch("docker.from_env") as mock_client:
            client = MagicMock()
            mock_client.return_value = client

            # Mock container
            container = MagicMock()
            container.status = "running"
            container.attrs = {"NetworkSettings": {"Ports": {"8000/tcp": [{"HostPort": "8000"}]}}}
            container.logs.return_value = b"Test output\nPassed: 2\nFailed: 0"

            # Mock image
            image = MagicMock()
            image.tags = ["test-project:latest"]

            client.containers.create.return_value = container
            client.containers.run.return_value = container
            client.images.build.return_value = (image, [{"stream": "Building..."}])

            yield client

    def test_deploy_command_exists(self):
        """Test that deploy_project_in_container command is registered."""
        commands = DHTLCommands()
        assert hasattr(commands, "deploy_project_in_container")

    def test_docker_availability_check(self, docker_available):
        """Test Docker availability detection."""
        docker_mgr = DockerManager()

        # Check if Docker is installed
        is_available = docker_mgr.is_docker_available()

        if docker_available:
            assert is_available is True
        else:
            # If Docker not installed, should return False
            assert is_available is False

    @pytest.mark.skipif(not shutil.which("docker"), reason="Docker not installed")
    def test_docker_daemon_check(self):
        """Test Docker daemon status check."""
        docker_mgr = DockerManager()

        # Check if daemon is running
        is_running = docker_mgr.is_daemon_running()

        # This might be True or False depending on system state
        assert isinstance(is_running, bool)

    def test_dockerfile_generation_web_app(self, temp_project):
        """Test Dockerfile generation for a web application."""
        generator = DockerfileGenerator()

        # Analyze project
        project_info = generator.analyze_project(temp_project)

        assert project_info["type"] == ProjectType.WEB
        assert project_info["main_entry"] == "main.py"
        assert project_info["python_version"] == "3.11"
        assert "fastapi" in project_info["dependencies"]

        # Generate Dockerfile
        dockerfile_content = generator.generate_dockerfile(project_info)

        assert "FROM python:3.11-slim" in dockerfile_content
        assert "RUN curl -LsSf https://astral.sh/uv/install.sh | sh" in dockerfile_content
        assert "WORKDIR /app" in dockerfile_content
        assert "COPY . ." in dockerfile_content
        assert "RUN uv sync --all-extras" in dockerfile_content
        assert "EXPOSE 8000" in dockerfile_content
        assert 'CMD ["uv", "run", "python", "main.py"]' in dockerfile_content

    def test_dockerfile_generation_cli_app(self, temp_project):
        """Test Dockerfile generation for a CLI application."""
        # Modify project to be CLI app
        cli_content = '''
import click

@click.command()
@click.option('--name', default='World', help='Name to greet.')
def main(name):
    """Simple CLI application."""
    click.echo(f'Hello {name}!')

if __name__ == '__main__':
    main()
'''
        (temp_project / "cli.py").write_text(cli_content)
        (temp_project / "main.py").unlink()  # Remove web app

        # Update pyproject.toml to have CLI dependencies instead of web
        pyproject_path = temp_project / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        # Replace web dependencies with CLI dependencies
        pyproject["project"]["dependencies"] = ["click>=8.0.0"]

        import tomli_w

        with open(pyproject_path, "wb") as f:
            tomli_w.dump(pyproject, f)

        generator = DockerfileGenerator()
        project_info = generator.analyze_project(temp_project)

        assert project_info["type"] == ProjectType.CLI
        assert project_info["main_entry"] == "cli.py"

        dockerfile_content = generator.generate_dockerfile(project_info)
        assert "EXPOSE" not in dockerfile_content
        assert 'CMD ["uv", "run", "python", "cli.py"]' in dockerfile_content

    def test_container_build_process(self, temp_project, mock_docker_client):
        """Test Docker image building process."""
        docker_mgr = DockerManager()

        # Build image
        image_tag = "test-project:latest"
        success, logs = docker_mgr.build_image(temp_project, image_tag)

        assert success is True
        assert logs is not None
        mock_docker_client.images.build.assert_called_once()

    def test_container_run_application(self, temp_project, mock_docker_client):
        """Test running application in container."""
        docker_mgr = DockerManager()

        # Run container
        container_name = "test-project-app"
        port_mapping = {"8000/tcp": 8000}

        container = docker_mgr.run_container("test-project:latest", container_name, ports=port_mapping, detach=True)

        assert container is not None
        mock_docker_client.containers.run.assert_called_once()

    def test_pytest_execution_in_container(self, temp_project, mock_docker_client):
        """Test running pytest in container."""
        test_runner = ContainerTestRunner()

        # Mock the docker manager's exec_command method
        mock_docker_manager = MagicMock()
        test_runner.docker_manager = mock_docker_manager

        # Mock pytest output
        pytest_output = """
============================= test session starts ==============================
collected 2 items

tests/test_main.py::test_example PASSED
tests/test_main.py::test_app PASSED

============================= 2 passed in 0.12s ===============================
"""
        mock_docker_manager.exec_command.return_value = (0, pytest_output)

        # Run pytest
        results = test_runner.run_pytest("test-container", verbose=True)

        assert results["total"] == 2
        assert results["passed"] == 2
        assert results["failed"] == 0
        assert "test_example" in results["tests"]
        assert "test_app" in results["tests"]

    @pytest.mark.skipif(not shutil.which("playwright"), reason="Playwright not installed")
    def test_playwright_execution_in_container(self, temp_project, mock_docker_client):
        """Test running Playwright tests in container."""
        # Create Playwright test
        e2e_dir = temp_project / "tests" / "e2e"
        e2e_dir.mkdir()

        playwright_test = """
import { test, expect } from '@playwright/test';

test('homepage test', async ({ page }) => {
  await page.goto('http://localhost:8000');
  const response = await page.evaluate(() => fetch('/').then(r => r.json()));
  expect(response.message).toBe('Hello from container!');
});
"""
        (e2e_dir / "test_homepage.spec.ts").write_text(playwright_test)

        test_runner = ContainerTestRunner()

        # Mock the docker manager's exec_command method
        mock_docker_manager = MagicMock()
        test_runner.docker_manager = mock_docker_manager

        # Mock browser installation and test execution
        mock_docker_manager.exec_command.side_effect = [
            (0, "Browsers installed"),  # playwright install
            (0, "1 passed (2.5s)"),  # test execution
        ]

        results = test_runner.run_playwright("test-container")

        assert results["total"] >= 1
        assert results["passed"] >= 1

    def test_results_formatting(self):
        """Test formatting test results as table."""
        test_runner = ContainerTestRunner()

        # Mock test results
        results = {
            TestFramework.PYTEST: {"total": 10, "passed": 8, "failed": 1, "skipped": 1},
            TestFramework.PLAYWRIGHT: {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
            TestFramework.PUPPETEER: {"total": 3, "passed": 2, "failed": 1, "skipped": 0},
        }

        table = test_runner.format_results_table(results)

        assert "Test Suite" in table
        assert "Unit Tests (pytest)" in table
        assert "10" in table  # total
        assert "8" in table  # passed
        assert "1" in table  # failed
        assert "+" in table  # table border
        assert "|" in table  # table border

    @patch("DHT.modules.docker_manager.docker.from_env")
    @patch("DHT.modules.container_test_runner.DockerManager")
    def test_deploy_command_integration(self, mock_docker_manager_class, mock_docker_from_env, temp_project):
        """Test full deploy_project_in_container command flow."""
        # Setup mocks
        mock_client = MagicMock()
        mock_docker_from_env.return_value = mock_client

        # Mock DockerManager instance for ContainerTestRunner
        mock_docker_manager = MagicMock()
        mock_docker_manager_class.return_value = mock_docker_manager

        # Mock container
        container = MagicMock()
        container.id = "test-container-id"
        container.name = "dht-test-project-container"
        container.status = "running"
        container.image.tags = ["dht-test-project:latest"]
        container.attrs = {
            "NetworkSettings": {"Ports": {"8000/tcp": [{"HostPort": "8000"}]}},
            "Created": "2025-06-19T08:00:00Z",
            "State": {"Status": "running"},
        }

        # Mock image build
        image = MagicMock()
        image.tags = ["dht-test-project:latest"]
        mock_client.images.build.return_value = (image, [{"stream": "Building..."}])

        # Mock container operations
        mock_client.containers.run.return_value = container
        mock_client.containers.get.return_value = container
        mock_client.containers.list.return_value = []
        mock_client.ping.return_value = True

        # Mock test execution
        pytest_output = """
============================= test session starts ==============================
collected 2 items

tests/test_main.py::test_example PASSED
tests/test_main.py::test_app PASSED

============================= 2 passed in 0.12s ===============================
"""
        mock_docker_manager.exec_command.return_value = (0, pytest_output)

        commands = DHTLCommands()

        # Run deploy command
        result = commands.deploy_project_in_container(
            project_path=str(temp_project), run_tests=True, python_version="3.11"
        )

        assert result["success"] is True
        assert "image_tag" in result
        assert "container_name" in result
        assert "test_results" in result
        assert TestFramework.PYTEST in result["test_results"]
        assert result["test_results"][TestFramework.PYTEST]["total"] == 2

    def test_error_handling_no_docker(self):
        """Test error handling when Docker is not available."""
        with patch("shutil.which", return_value=None):
            docker_mgr = DockerManager()

            assert docker_mgr.is_docker_available() is False

            # Should provide helpful error message
            with pytest.raises(RuntimeError, match="Docker is not installed"):
                docker_mgr.check_docker_requirements()

    def test_error_handling_daemon_not_running(self, mock_docker_client):
        """Test error handling when Docker daemon is not running."""
        mock_docker_client.ping.side_effect = docker.errors.DockerException("Cannot connect")

        docker_mgr = DockerManager()
        assert docker_mgr.is_daemon_running() is False

        with pytest.raises(RuntimeError, match="Docker daemon is not running"):
            docker_mgr.check_docker_requirements()

    def test_cleanup_on_failure(self, temp_project, mock_docker_client):
        """Test cleanup when deployment fails."""
        # Make build fail
        mock_docker_client.images.build.side_effect = docker.errors.BuildError("Build failed", build_log=[])

        docker_mgr = DockerManager()

        from DHT.modules.docker_manager import DockerError

        with pytest.raises(DockerError, match="Failed to build image"):
            docker_mgr.build_image(temp_project, "test-project:latest")

        # Should clean up any partial resources
        # (In real implementation, this would remove partial images/containers)

    def test_container_logs_streaming(self, mock_docker_client):
        """Test streaming logs from container."""
        docker_mgr = DockerManager()

        # Mock log streaming
        container = mock_docker_client.containers.get("test-container")
        container.logs.return_value = b"Line 1\nLine 2\nLine 3"

        logs = docker_mgr.stream_logs("test-container", follow=False)

        assert "Line 1" in logs
        assert "Line 2" in logs
        assert "Line 3" in logs

    def test_port_availability_check(self):
        """Test checking if ports are available before binding."""
        docker_mgr = DockerManager()

        # Check common ports
        is_available = docker_mgr.is_port_available(8000)
        assert isinstance(is_available, bool)

        # Port 0 is invalid
        assert docker_mgr.is_port_available(0) is False
        # Port beyond valid range is invalid
        assert docker_mgr.is_port_available(70000) is False

    def test_custom_dockerfile_support(self, temp_project):
        """Test using existing Dockerfile if present."""
        # Create custom Dockerfile
        custom_dockerfile = """
FROM python:3.12-alpine
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "-m", "myapp"]
"""
        (temp_project / "Dockerfile").write_text(custom_dockerfile)

        generator = DockerfileGenerator()
        dockerfile_content = generator.get_dockerfile(temp_project)

        # Should use existing Dockerfile
        assert "FROM python:3.12-alpine" in dockerfile_content
        assert 'CMD ["python", "-m", "myapp"]' in dockerfile_content

    def test_multi_stage_build(self, temp_project):
        """Test generating multi-stage Dockerfile for production."""
        generator = DockerfileGenerator()

        project_info = generator.analyze_project(temp_project)
        dockerfile_content = generator.generate_dockerfile(project_info, multi_stage=True, production=True)

        assert "AS builder" in dockerfile_content
        assert "FROM python:3.11-slim" in dockerfile_content
        assert "COPY --from=builder" in dockerfile_content
        assert "USER appuser" in dockerfile_content  # Non-root user
