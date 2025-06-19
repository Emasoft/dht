#!/usr/bin/env python3
"""
Additional tests to reach 100% coverage for Docker deployment modules.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import docker.errors
import pytest

from DHT.modules.container_test_runner import ContainerTestRunner, TestFramework
from DHT.modules.docker_manager import DockerError, DockerManager
from DHT.modules.dockerfile_generator import DockerfileGenerator, ProjectType


class TestDockerManagerCoverage:
    """Additional tests for DockerManager coverage."""

    @patch("docker.from_env")
    def test_client_property_error(self, mock_docker):
        """Test client property when Docker connection fails."""
        mock_docker.side_effect = docker.errors.DockerException("Connection failed")

        manager = DockerManager()
        with pytest.raises(DockerError, match="Failed to connect to Docker"):
            _ = manager.client

    def test_is_port_available_invalid_ports(self):
        """Test port availability for invalid port numbers."""
        manager = DockerManager()

        # Test boundary conditions
        assert manager.is_port_available(-1) is False
        assert manager.is_port_available(0) is False
        assert manager.is_port_available(65536) is False
        assert manager.is_port_available(100000) is False

    def test_is_port_available_occupied(self):
        """Test port availability when port is occupied."""
        manager = DockerManager()

        # Create a real socket to occupy the port
        import socket

        occupied_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            occupied_socket.bind(("", 8899))
            occupied_socket.listen(1)

            # Now test that the port is not available
            assert manager.is_port_available(8899) is False
        finally:
            occupied_socket.close()

    @patch("docker.from_env")
    def test_build_image_with_dockerfile_content(self, mock_docker):
        """Test building image with Dockerfile content."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock successful build
        mock_image = MagicMock()
        mock_logs = [{"stream": "Step 1/5 : FROM python:3.11\n"}]
        mock_client.images.build.return_value = (mock_image, mock_logs)
        mock_client.ping.return_value = True

        # Build with Dockerfile content
        dockerfile_content = "FROM python:3.11\nWORKDIR /app"
        success, logs = manager.build_image(Path("/tmp/project"), "test:latest", dockerfile=dockerfile_content)

        assert success is True
        assert "Step 1/5" in logs

    @patch("docker.from_env")
    def test_build_image_unexpected_error(self, mock_docker):
        """Test build image with unexpected error."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_client.ping.return_value = True

        # Mock unexpected error
        mock_client.images.build.side_effect = Exception("Unexpected error")

        with pytest.raises(DockerError, match="Failed to build image"):
            manager.build_image(Path("/tmp"), "test:latest")

    @patch("docker.from_env")
    def test_run_container_image_not_found(self, mock_docker):
        """Test running container when image not found."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_client.ping.return_value = True

        # Mock image not found
        mock_client.containers.run.side_effect = docker.errors.ImageNotFound("Image not found")

        with pytest.raises(DockerError, match="Image not found"):
            manager.run_container("nonexistent:latest", "test-container")

    @patch("docker.from_env")
    def test_run_container_api_error(self, mock_docker):
        """Test running container with API error."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_client.ping.return_value = True

        # Mock API error
        mock_client.containers.run.side_effect = docker.errors.APIError("API error")

        with pytest.raises(DockerError, match="Failed to run container"):
            manager.run_container("test:latest", "test-container")

    @patch("docker.from_env")
    def test_run_container_unexpected_error(self, mock_docker):
        """Test running container with unexpected error."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_client.ping.return_value = True

        # Mock unexpected error
        mock_client.containers.run.side_effect = Exception("Unexpected")

        with pytest.raises(DockerError, match="Unexpected error running container"):
            manager.run_container("test:latest", "test-container")

    @patch("docker.from_env")
    def test_run_container_with_existing_container(self, mock_docker):
        """Test running container when container with same name exists."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_client.ping.return_value = True

        # Mock existing container
        existing_container = MagicMock()
        mock_client.containers.get.return_value = existing_container

        # Mock new container
        new_container = MagicMock()
        mock_client.containers.run.return_value = new_container

        container = manager.run_container("test:latest", "existing-container")

        # Should stop and remove existing container
        existing_container.stop.assert_called_once()
        existing_container.remove.assert_called_once()
        assert container == new_container

    @patch("docker.from_env")
    def test_stop_container_not_found(self, mock_docker):
        """Test stopping container that doesn't exist."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock container not found
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        # Should not raise, just log warning
        manager.stop_container("nonexistent")

    @patch("docker.from_env")
    def test_stop_container_error(self, mock_docker):
        """Test stopping container with error."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock container that fails to stop
        mock_container = MagicMock()
        mock_container.stop.side_effect = Exception("Stop failed")
        mock_client.containers.get.return_value = mock_container

        with pytest.raises(DockerError, match="Failed to stop container"):
            manager.stop_container("test-container")

    @patch("docker.from_env")
    def test_stream_logs_follow(self, mock_docker):
        """Test streaming logs with follow=True."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock container with streaming logs
        mock_container = MagicMock()
        mock_logs_generator = iter([b"Log line 1\n", b"Log line 2\n"])
        mock_container.logs.return_value = mock_logs_generator
        mock_client.containers.get.return_value = mock_container

        logs = manager.stream_logs("test-container", follow=True)

        # Should return generator
        assert logs == mock_logs_generator

    @patch("docker.from_env")
    def test_stream_logs_string_output(self, mock_docker):
        """Test streaming logs with string output."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock container with string logs
        mock_container = MagicMock()
        mock_container.logs.return_value = "String logs"
        mock_client.containers.get.return_value = mock_container

        logs = manager.stream_logs("test-container", follow=False)

        assert logs == "String logs"

    @patch("docker.from_env")
    def test_stream_logs_not_found(self, mock_docker):
        """Test streaming logs from non-existent container."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        with pytest.raises(DockerError, match="Container not found"):
            manager.stream_logs("nonexistent")

    @patch("docker.from_env")
    def test_stream_logs_error(self, mock_docker):
        """Test streaming logs with error."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.logs.side_effect = Exception("Logs failed")
        mock_client.containers.get.return_value = mock_container

        with pytest.raises(DockerError, match="Failed to get logs"):
            manager.stream_logs("test-container")

    @patch("docker.from_env")
    def test_exec_command_not_found(self, mock_docker):
        """Test executing command in non-existent container."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        with pytest.raises(DockerError, match="Container not found"):
            manager.exec_command("nonexistent", ["echo", "test"])

    @patch("docker.from_env")
    def test_exec_command_error(self, mock_docker):
        """Test executing command with error."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.exec_run.side_effect = Exception("Exec failed")
        mock_client.containers.get.return_value = mock_container

        with pytest.raises(DockerError, match="Failed to execute command"):
            manager.exec_command("test-container", ["echo", "test"])

    @patch("docker.from_env")
    def test_exec_command_no_output(self, mock_docker):
        """Test executing command with no output."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_result = MagicMock()
        mock_result.exit_code = 0
        mock_result.output = None
        mock_container.exec_run.return_value = mock_result
        mock_client.containers.get.return_value = mock_container

        exit_code, output = manager.exec_command("test-container", ["true"])

        assert exit_code == 0
        assert output == ""

    @patch("docker.from_env")
    def test_get_container_info_not_found(self, mock_docker):
        """Test getting info for non-existent container."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        with pytest.raises(DockerError, match="Container not found"):
            manager.get_container_info("nonexistent")

    @patch("docker.from_env")
    def test_get_container_info_error(self, mock_docker):
        """Test getting container info with error."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_client.containers.get.side_effect = Exception("Info failed")

        with pytest.raises(DockerError, match="Failed to get container info"):
            manager.get_container_info("test-container")

    @patch("docker.from_env")
    def test_cleanup_containers_with_errors(self, mock_docker):
        """Test cleanup containers with some failures."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock containers
        container1 = MagicMock()
        container1.name = "test-app-1"

        container2 = MagicMock()
        container2.name = "test-app-2"
        container2.stop.side_effect = Exception("Stop failed")

        container3 = MagicMock()
        container3.name = "other-app"

        mock_client.containers.list.return_value = [container1, container2, container3]

        cleaned = manager.cleanup_containers("test-app")

        # Should clean up container1 only (container2 failed, container3 doesn't match)
        assert cleaned == 1
        container1.stop.assert_called_once()
        container1.remove.assert_called_once()

    @patch("docker.from_env")
    def test_cleanup_containers_list_error(self, mock_docker):
        """Test cleanup containers when list fails."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_client.containers.list.side_effect = Exception("List failed")

        cleaned = manager.cleanup_containers("test-app")
        assert cleaned == 0

    @patch("docker.from_env")
    def test_cleanup_images_with_errors(self, mock_docker):
        """Test cleanup images with some failures."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Mock images
        image1 = MagicMock()
        image1.tags = ["test-app:v1", "test-app:latest"]
        image1.id = "img1"

        image2 = MagicMock()
        image2.tags = ["test-app:v2"]
        image2.id = "img2"

        image3 = MagicMock()
        image3.tags = ["other-app:latest"]
        image3.id = "img3"

        mock_client.images.list.return_value = [image1, image2, image3]
        mock_client.images.remove.side_effect = [None, Exception("Remove failed")]

        cleaned = manager.cleanup_images("test-app")

        # Should clean up image1 only (image2 failed, image3 doesn't match)
        assert cleaned == 1

    @patch("docker.from_env")
    def test_cleanup_images_list_error(self, mock_docker):
        """Test cleanup images when list fails."""
        manager = DockerManager()
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        mock_client.images.list.side_effect = Exception("List failed")

        cleaned = manager.cleanup_images("test-app")
        assert cleaned == 0


class TestDockerfileGeneratorCoverage:
    """Additional tests for DockerfileGenerator coverage."""

    def test_detect_web_project_by_file_content(self, tmp_path):
        """Test detecting web project by file content."""
        generator = DockerfileGenerator()

        # Create project without web dependencies in pyproject.toml
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
dependencies = []
""")

        # Create file with web framework imports
        (tmp_path / "app.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
""")

        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.WEB

    def test_detect_cli_project_by_file_content(self, tmp_path):
        """Test detecting CLI project by file content."""
        generator = DockerfileGenerator()

        # Create project without CLI dependencies
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-cli"
dependencies = []
""")

        # Create file with CLI framework usage
        (tmp_path / "cli.py").write_text("""
import click

@click.command()
def main():
    click.echo("Hello CLI!")
""")

        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.CLI

    def test_detect_library_project(self, tmp_path):
        """Test detecting library project."""
        generator = DockerfileGenerator()

        # Create library project structure
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "my-library"
dependencies = ["requests"]
""")

        # Create package structure
        lib_dir = tmp_path / "my_library"
        lib_dir.mkdir()
        (lib_dir / "__init__.py").write_text("__version__ = '1.0.0'")
        (lib_dir / "utils.py").write_text("def helper(): pass")

        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.LIBRARY

    def test_detect_unknown_project(self, tmp_path):
        """Test detecting unknown project type."""
        generator = DockerfileGenerator()

        # Create minimal project
        (tmp_path / "script.py").write_text("print('Hello')")

        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.UNKNOWN

    def test_skip_large_files(self, tmp_path):
        """Test skipping large files during detection."""
        generator = DockerfileGenerator()

        # Create large file (> 1MB)
        large_content = "x" * (1024 * 1024 + 1)
        (tmp_path / "large.py").write_text(large_content)

        # Should not raise exception
        project_type = generator.detect_project_type(tmp_path)
        assert project_type == ProjectType.UNKNOWN

    def test_handle_file_read_error(self, tmp_path):
        """Test handling file read errors."""
        generator = DockerfileGenerator()

        # Create file that we'll make unreadable
        test_file = tmp_path / "test.py"
        test_file.write_text("from flask import Flask")
        test_file.chmod(0o000)

        try:
            # Should handle gracefully
            project_type = generator.detect_project_type(tmp_path)
            # Type detection might fail but shouldn't crash
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    def test_detect_python_version_no_match(self, tmp_path):
        """Test Python version detection with no match."""
        generator = DockerfileGenerator()

        # Create .python-version with invalid format
        (tmp_path / ".python-version").write_text("python")

        version = generator.detect_python_version(tmp_path)
        assert version == "3.11"  # Default

    def test_detect_python_version_pyproject_error(self, tmp_path):
        """Test Python version detection with invalid pyproject.toml."""
        generator = DockerfileGenerator()

        # Create invalid pyproject.toml
        (tmp_path / "pyproject.toml").write_text("invalid toml {")

        version = generator.detect_python_version(tmp_path)
        assert version == "3.11"  # Default

    def test_find_entry_points_with_main_check(self, tmp_path):
        """Test finding entry points with __main__ check."""
        generator = DockerfileGenerator()

        # Create files with different __main__ patterns
        (tmp_path / "run.py").write_text("""
def main():
    print("Hello")

if __name__ == '__main__':
    main()
""")

        (tmp_path / "start.py").write_text("""
def start():
    print("Starting")

if __name__ == "__main__":
    start()
""")

        entry_points = generator.find_entry_points(tmp_path)
        assert "run.py" in entry_points
        assert "start.py" in entry_points

    def test_find_entry_points_with_error(self, tmp_path):
        """Test finding entry points with file read error."""
        generator = DockerfileGenerator()

        # Create unreadable file
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("content")
        bad_file.chmod(0o000)

        try:
            # Should handle gracefully
            entry_points = generator.find_entry_points(tmp_path)
            assert isinstance(entry_points, list)
        finally:
            bad_file.chmod(0o644)

    def test_get_dependencies_requirements_only(self, tmp_path):
        """Test getting dependencies from requirements.txt only."""
        generator = DockerfileGenerator()

        # Create requirements.txt
        (tmp_path / "requirements.txt").write_text("""
# Comment
requests==2.28.0
flask>=2.0.0

# Empty line above
pandas
""")

        deps = generator._get_dependencies(tmp_path)
        assert "requests" in deps
        assert "flask" in deps
        assert "pandas" in deps

    def test_get_dependencies_pyproject_error(self, tmp_path):
        """Test getting dependencies with pyproject.toml error."""
        generator = DockerfileGenerator()

        # Create invalid pyproject.toml
        (tmp_path / "pyproject.toml").write_text("invalid = {")

        # Create valid requirements.txt
        (tmp_path / "requirements.txt").write_text("requests")

        deps = generator._get_dependencies(tmp_path)
        assert "requests" in deps

    def test_get_dependencies_requirements_error(self, tmp_path):
        """Test getting dependencies with requirements.txt error."""
        generator = DockerfileGenerator()

        # Create unreadable requirements.txt
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests")
        req_file.chmod(0o000)

        try:
            deps = generator._get_dependencies(tmp_path)
            assert isinstance(deps, list)
        finally:
            req_file.chmod(0o644)

    def test_get_system_deps_all_mappings(self, tmp_path):
        """Test system dependencies for all mapped packages."""
        generator = DockerfileGenerator()

        # Test all mapped dependencies
        python_deps = [
            "psycopg2-binary",
            "mysqlclient",
            "pillow",
            "lxml",
            "cryptography",
            "numpy",
            "scipy",
            "opencv-python",
        ]

        system_deps = generator._get_system_deps(python_deps)

        # Check some expected mappings
        assert "libpq-dev" in system_deps
        assert "libxml2-dev" in system_deps
        assert "libjpeg-dev" in system_deps

    def test_has_tests_with_test_files(self, tmp_path):
        """Test detecting tests with test files."""
        generator = DockerfileGenerator()

        # Create test files
        (tmp_path / "test_main.py").write_text("def test_something(): pass")
        (tmp_path / "something_test.py").write_text("def test_other(): pass")

        assert generator._has_tests(tmp_path) is True

    def test_has_frontend_detection(self, tmp_path):
        """Test frontend detection."""
        generator = DockerfileGenerator()

        # No frontend
        assert generator._has_frontend(tmp_path) is False

        # With package.json
        (tmp_path / "package.json").write_text("{}")
        assert generator._has_frontend(tmp_path) is True

    def test_detect_ports_no_main_entry(self, tmp_path):
        """Test port detection with no main entry."""
        generator = DockerfileGenerator()

        ports = generator._detect_ports(tmp_path, None)
        assert ports == [8000]  # Default

    def test_detect_ports_various_patterns(self, tmp_path):
        """Test port detection with various patterns."""
        generator = DockerfileGenerator()

        # Create main.py with various port patterns
        (tmp_path / "main.py").write_text("""
import uvicorn

PORT = 3000
port = 5000

app.run(host='0.0.0.0', port=8080)
uvicorn.run(app, host="0.0.0.0", port=9000)

# Invalid ports
bad_port = 99999
negative = -1
""")

        ports = generator._detect_ports(tmp_path, "main.py")
        assert 3000 in ports
        assert 5000 in ports
        assert 8080 in ports
        assert 9000 in ports
        assert 99999 not in ports
        assert -1 not in ports

    def test_detect_ports_with_error(self, tmp_path):
        """Test port detection with file read error."""
        generator = DockerfileGenerator()

        # Create unreadable file
        main_file = tmp_path / "main.py"
        main_file.write_text("port = 8000")
        main_file.chmod(0o000)

        try:
            ports = generator._detect_ports(tmp_path, "main.py")
            assert ports == [8000]  # Default
        finally:
            main_file.chmod(0o644)

    def test_get_dockerfile_existing(self, tmp_path):
        """Test getting existing Dockerfile."""
        generator = DockerfileGenerator()

        # Create existing Dockerfile
        dockerfile_content = "FROM python:3.11\nWORKDIR /app"
        (tmp_path / "Dockerfile").write_text(dockerfile_content)

        result = generator.get_dockerfile(tmp_path)
        assert result == dockerfile_content

    def test_generate_dockerfile_cli_type(self):
        """Test Dockerfile generation for CLI type."""
        generator = DockerfileGenerator()

        project_info = {
            "type": ProjectType.CLI,
            "python_version": "3.12",
            "main_entry": None,
            "system_deps": [],
            "has_tests": False,
            "has_frontend": False,
            "ports": [],
        }

        dockerfile = generator.generate_dockerfile(project_info)
        assert "FROM python:3.12-slim" in dockerfile
        assert "EXPOSE" not in dockerfile
        assert 'CMD ["uv", "run", "python", "-m", "app"]' in dockerfile

    def test_generate_dockerfile_library_type(self):
        """Test Dockerfile generation for library type."""
        generator = DockerfileGenerator()

        project_info = {
            "type": ProjectType.LIBRARY,
            "python_version": "3.10",
            "main_entry": None,
            "system_deps": [],
            "has_tests": False,
            "has_frontend": False,
            "ports": [],
        }

        dockerfile = generator.generate_dockerfile(project_info)
        assert "FROM python:3.10-slim" in dockerfile
        assert 'CMD ["uv", "run", "python"]' in dockerfile

    def test_generate_dockerfile_with_tests_production(self):
        """Test Dockerfile generation with tests in production mode."""
        generator = DockerfileGenerator()

        project_info = {
            "type": ProjectType.WEB,
            "python_version": "3.11",
            "main_entry": None,
            "system_deps": [],
            "has_tests": True,
            "has_frontend": False,
            "ports": [8000],
            "dependencies": ["playwright"],
        }

        # Production mode should not include test dependencies
        dockerfile = generator.generate_dockerfile(project_info, production=True)
        assert "chromium" not in dockerfile

    def test_generate_dockerfile_with_frontend(self):
        """Test Dockerfile generation with frontend."""
        generator = DockerfileGenerator()

        project_info = {
            "type": ProjectType.WEB,
            "python_version": "3.11",
            "main_entry": "app.py",
            "system_deps": [],
            "has_tests": False,
            "has_frontend": True,
            "ports": [3000],
        }

        dockerfile = generator.generate_dockerfile(project_info)
        assert "Install Node.js" in dockerfile
        assert "npm install" in dockerfile
        assert "npm run build" in dockerfile

    def test_validate_dockerfile_all_issues(self):
        """Test Dockerfile validation finding all issues."""
        generator = DockerfileGenerator()

        # Dockerfile with multiple issues
        bad_dockerfile = """
WORKDIR /app
RUN pip install requests
RUN apt-get install -y curl
CMD ["python", "app.py"]
"""

        issues = generator.validate_dockerfile(bad_dockerfile)
        assert any("FROM" in issue for issue in issues)
        assert any("--no-cache-dir" in issue for issue in issues)
        assert any("apt-get" in issue for issue in issues)

    def test_validate_dockerfile_production_root(self):
        """Test Dockerfile validation for production without USER."""
        generator = DockerfileGenerator()

        production_dockerfile = """
FROM python:3.11-slim
WORKDIR /app
# Production build
RUN pip install --no-cache-dir requests
CMD ["python", "app.py"]
"""

        issues = generator.validate_dockerfile(production_dockerfile)
        assert any("root" in issue for issue in issues)


class TestContainerTestRunnerCoverage:
    """Additional tests for ContainerTestRunner coverage."""

    def test_run_all_tests_unknown_framework(self):
        """Test running tests with unknown framework."""
        runner = ContainerTestRunner()

        # Create fake framework
        fake_framework = MagicMock()
        fake_framework.value = "unknown"

        results = runner.run_all_tests("test-container", [fake_framework])
        assert fake_framework not in results

    def test_run_all_tests_all_frameworks(self):
        """Test running all supported frameworks."""
        runner = ContainerTestRunner()

        # Mock docker manager
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager

        # Mock outputs for each framework
        mock_docker_manager.exec_command.side_effect = [
            (0, "1 passed"),  # pytest
            (0, "Browsers installed"),  # playwright install
            (0, "2 passed"),  # playwright tests
            (0, "3 passed"),  # puppeteer
        ]

        results = runner.run_all_tests("test-container", list(TestFramework))

        assert TestFramework.PYTEST in results
        assert TestFramework.PLAYWRIGHT in results
        assert TestFramework.PUPPETEER in results

    def test_run_pytest_with_error(self):
        """Test pytest execution with Docker error."""
        runner = ContainerTestRunner()

        # Mock docker manager that raises error
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.side_effect = DockerError("Container error")

        results = runner.run_pytest("test-container")

        assert results["error"] == "Container error"
        assert results["exit_code"] == 1
        assert results["total"] == 0

    def test_run_pytest_with_coverage_disabled(self):
        """Test pytest execution without coverage."""
        runner = ContainerTestRunner()

        # Mock docker manager
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.return_value = (0, "1 passed")

        results = runner.run_pytest("test-container", coverage=False)

        # Check command didn't include coverage
        call_args = mock_docker_manager.exec_command.call_args
        assert "--cov" not in call_args[0][1]

    def test_run_pytest_with_specific_path(self):
        """Test pytest with specific test path."""
        runner = ContainerTestRunner()

        # Mock docker manager
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.return_value = (0, "1 passed")

        results = runner.run_pytest("test-container", test_path="tests/unit")

        # Check command included test path
        call_args = mock_docker_manager.exec_command.call_args
        assert "tests/unit" in call_args[0][1]

    def test_run_playwright_install_failure(self):
        """Test Playwright when browser installation fails."""
        runner = ContainerTestRunner()

        # Mock docker manager
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager

        # First call fails (browser install)
        mock_docker_manager.exec_command.side_effect = [(1, "Failed to install browsers"), (0, "1 passed")]

        results = runner.run_playwright("test-container")

        # Should still try to run tests
        assert results["exit_code"] == 0

    def test_run_playwright_with_error(self):
        """Test Playwright execution with Docker error."""
        runner = ContainerTestRunner()

        # Mock docker manager that raises error
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.side_effect = DockerError("Container error")

        results = runner.run_playwright("test-container")

        assert results["error"] == "Container error"
        assert results["exit_code"] == 1

    def test_run_puppeteer_with_error(self):
        """Test Puppeteer execution with Docker error."""
        runner = ContainerTestRunner()

        # Mock docker manager that raises error
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.side_effect = DockerError("Container error")

        results = runner.run_puppeteer("test-container")

        assert results["error"] == "Container error"
        assert results["exit_code"] == 1

    def test_parse_pytest_output_with_errors(self):
        """Test parsing pytest output with errors."""
        runner = ContainerTestRunner()

        output = """
============================= test session starts ==============================
collected 5 items

tests/test_main.py::test_one PASSED
tests/test_main.py::test_two FAILED
tests/test_main.py::test_three ERROR
tests/test_utils.py::test_helper SKIPPED

========================= 1 passed, 1 failed, 1 error, 1 skipped =========================
"""

        results = runner._parse_pytest_output(output)
        assert results["errors"] == 1
        assert results["total"] == 4  # passed + failed + skipped + errors

    def test_parse_pytest_output_with_coverage(self):
        """Test parsing pytest output with coverage."""
        runner = ContainerTestRunner()

        output = """
============================= test session starts ==============================
tests/test_main.py::test_example PASSED

---------- coverage: platform linux, python 3.11.0-final-0 -----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/__init__.py               0      0   100%
src/main.py                  15      2    87%
---------------------------------------------
TOTAL                        15      2    87%

============================= 1 passed in 0.5s ===============================
"""

        results = runner._parse_pytest_output(output)
        assert results["coverage"] == "87%"

    def test_parse_playwright_output_no_pytest_format(self):
        """Test parsing Playwright output without pytest format."""
        runner = ContainerTestRunner()

        # Playwright-specific output format
        output = """
Running 5 tests using 2 workers
  ✓ test/homepage.spec.ts:3:1 › homepage test (2.1s)
  ✓ test/login.spec.ts:5:1 › login test (1.5s)
  ✓ test/search.spec.ts:10:1 › search test (3.2s)

  3 passed (5.2s)
"""

        results = runner._parse_playwright_output(output)
        assert results["total"] == 3
        assert results["passed"] == 3

    def test_format_results_table_with_errors(self):
        """Test formatting table with error results."""
        runner = ContainerTestRunner()

        results = {
            TestFramework.PYTEST: {
                "error": "Failed to connect to Docker daemon. This is a very long error message that should be truncated"
            },
            TestFramework.PLAYWRIGHT: {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
        }

        table = runner.format_results_table(results)

        assert "ERROR" in table
        assert "Failed to connect" in table
        # Check that error is shown (truncation happens at 50 chars)
        assert "Failed to connect to Docker daemon" in table

    def test_format_results_table_no_tests(self):
        """Test formatting table with no tests found."""
        runner = ContainerTestRunner()

        results = {}

        table = runner.format_results_table(results)
        assert "No Tests Found" in table

    def test_format_results_table_with_coverage(self):
        """Test formatting table with coverage information."""
        runner = ContainerTestRunner()

        results = {
            TestFramework.PYTEST: {"total": 10, "passed": 10, "failed": 0, "skipped": 0, "coverage": "95%"},
            TestFramework.PLAYWRIGHT: {"total": 5, "passed": 5, "failed": 0, "skipped": 0, "coverage": "88%"},
        }

        table = runner.format_results_table(results)
        assert "Coverage (pytest): 95%" in table
        assert "Coverage (playwright): 88%" in table

    def test_format_detailed_results(self):
        """Test formatting detailed results."""
        runner = ContainerTestRunner()

        results = {
            TestFramework.PYTEST: {
                "total": 10,
                "passed": 8,
                "failed": 2,
                "skipped": 0,
                "coverage": "90%",
                "tests": {"test_one": "passed", "test_two": "passed", "test_three": "failed", "test_four": "failed"},
            },
            TestFramework.PLAYWRIGHT: {
                "error": "Docker connection failed",
                "error_output": "Very long error output that should be truncated " * 50,
            },
        }

        detailed = runner.format_detailed_results(results)

        # Check structure
        assert "PYTEST RESULTS" in detailed
        assert "PLAYWRIGHT RESULTS" in detailed
        assert "Failed Tests:" in detailed
        assert "test_three" in detailed
        assert "test_four" in detailed
        assert "Docker connection failed" in detailed
        # Check error output is present (truncation at 500 chars)
        assert "Very long error output" in detailed
        assert len(detailed) < 10000  # Ensure it's not unbounded

    def test_format_detailed_results_many_failures(self):
        """Test formatting detailed results with many failures."""
        runner = ContainerTestRunner()

        # Create many failed tests
        failed_tests = {f"test_{i}": "failed" for i in range(20)}
        failed_tests.update({f"test_pass_{i}": "passed" for i in range(5)})

        results = {TestFramework.PYTEST: {"total": 25, "passed": 5, "failed": 20, "skipped": 0, "tests": failed_tests}}

        detailed = runner.format_detailed_results(results)

        # Should show first 10 and indicate more
        assert "test_0" in detailed
        assert "test_9" in detailed
        assert "and 10 more" in detailed

    def test_save_results(self, tmp_path):
        """Test saving results to file."""
        runner = ContainerTestRunner()

        results = {
            TestFramework.PYTEST: {"total": 10, "passed": 8, "failed": 2, "skipped": 0},
            TestFramework.PLAYWRIGHT: {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
        }

        output_file = tmp_path / "results.json"
        runner.save_results(results, output_file)

        # Verify file was created and contains correct data
        assert output_file.exists()

        import json

        with open(output_file) as f:
            saved_data = json.load(f)

        assert "pytest" in saved_data
        assert "playwright" in saved_data
        assert saved_data["pytest"]["total"] == 10
