#!/usr/bin/env python3
"""
Final tests to reach 100% coverage for Docker deployment modules.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import docker.errors

from DHT.modules.container_test_runner import ContainerTestRunner, TestFramework
from DHT.modules.docker_manager import DockerManager
from DHT.modules.dockerfile_generator import DockerfileGenerator, ProjectType


class TestFinalCoverage:
    """Final tests to cover remaining lines."""

    # ContainerTestRunner missing lines: 62, 179, 232, 321-322
    def test_run_all_tests_default_frameworks(self):
        """Test run_all_tests with default frameworks (None)."""
        runner = ContainerTestRunner()

        # Mock docker manager
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.return_value = (0, "1 passed")

        # Call with None frameworks (should default to pytest)
        results = runner.run_all_tests("test-container", None)

        assert TestFramework.PYTEST in results
        assert len(results) == 1

    def test_run_playwright_with_test_path(self):
        """Test run_playwright with specific test path."""
        runner = ContainerTestRunner()

        # Mock docker manager
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.side_effect = [(0, "Browsers installed"), (0, "1 passed")]

        results = runner.run_playwright("test-container", test_path="tests/e2e/specific.spec.ts")

        # Check that test path was used
        call_args = mock_docker_manager.exec_command.call_args_list[1]
        assert "tests/e2e/specific.spec.ts" in call_args[0][1]

    def test_run_puppeteer_with_test_path(self):
        """Test run_puppeteer with specific test path."""
        runner = ContainerTestRunner()

        # Mock docker manager
        mock_docker_manager = MagicMock()
        runner.docker_manager = mock_docker_manager
        mock_docker_manager.exec_command.return_value = (0, "1 passed")

        results = runner.run_puppeteer("test-container", test_path="tests/puppeteer/test_ui.py")

        # Check that test path was used
        call_args = mock_docker_manager.exec_command.call_args
        assert "tests/puppeteer/test_ui.py" in call_args[0][1]

    def test_parse_playwright_output_zero_total(self):
        """Test parsing Playwright output when no pytest format and total is 0."""
        runner = ContainerTestRunner()

        # Output without pytest format and no matches
        output = "No tests found"

        results = runner._parse_playwright_output(output)

        # Should have zero tests
        assert results["total"] == 0

    # DockerManager missing lines: 134, 194-195
    def test_build_image_with_buildargs(self):
        """Test building image with build arguments."""
        manager = DockerManager()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.ping.return_value = True

            # Mock successful build
            mock_image = MagicMock()
            mock_logs = [{"stream": "Building..."}]
            mock_client.images.build.return_value = (mock_image, mock_logs)

            # Build with buildargs
            success, logs = manager.build_image(
                Path("/tmp/project"), "test:latest", buildargs={"ARG1": "value1", "ARG2": "value2"}
            )

            assert success is True

            # Check buildargs were passed
            call_args = mock_client.images.build.call_args
            assert call_args[1]["buildargs"] == {"ARG1": "value1", "ARG2": "value2"}

    def test_run_container_with_no_existing_container(self):
        """Test running container when get() raises NotFound."""
        manager = DockerManager()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.ping.return_value = True

            # Mock container not found (normal case)
            mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

            # Mock successful run
            new_container = MagicMock()
            mock_client.containers.run.return_value = new_container

            container = manager.run_container("test:latest", "new-container")

            assert container == new_container
            # Should not try to stop/remove non-existent container
            assert mock_client.containers.get.call_count == 1

    # DockerfileGenerator missing lines: 230, 329, 423-424, 448-449, 542
    def test_detect_cli_project_with_cli_dependency(self):
        """Test detecting CLI project with click in dependencies."""
        generator = DockerfileGenerator()

        tmp_path = Path("/tmp/test_cli_project")
        tmp_path.mkdir(exist_ok=True)

        try:
            # Create pyproject.toml with click dependency
            (tmp_path / "pyproject.toml").write_text("""
[project]
name = "cli-app"
dependencies = ["click>=8.0"]
""")

            # Create a main entry point to avoid library detection
            (tmp_path / "cli.py").write_text("""
import click

@click.command()
def main():
    pass
""")

            project_type = generator.detect_project_type(tmp_path)
            assert project_type == ProjectType.CLI
        finally:
            import shutil

            shutil.rmtree(tmp_path, ignore_errors=True)

    def test_get_dependencies_with_optional_deps(self):
        """Test getting dependencies including optional dependencies."""
        generator = DockerfileGenerator()

        tmp_path = Path("/tmp/test_optional_deps")
        tmp_path.mkdir(exist_ok=True)

        try:
            # Create pyproject.toml with optional dependencies
            (tmp_path / "pyproject.toml").write_text("""
[project]
name = "app"
dependencies = ["requests"]

[project.optional-dependencies]
dev = ["pytest", "black"]
docs = ["sphinx", "mkdocs"]
""")

            deps = generator._get_dependencies(tmp_path)

            # Should include all dependencies
            assert "requests" in deps
            assert "pytest" in deps
            assert "black" in deps
            assert "sphinx" in deps
            assert "mkdocs" in deps
        finally:
            import shutil

            shutil.rmtree(tmp_path, ignore_errors=True)

    def test_detect_ports_with_invalid_values(self):
        """Test port detection with invalid port values."""
        generator = DockerfileGenerator()

        tmp_path = Path("/tmp/test_ports")
        tmp_path.mkdir(exist_ok=True)

        try:
            # Create main.py with invalid ports
            (tmp_path / "main.py").write_text("""
PORT = "not_a_number"
port = 3.14
another_port = "8080"  # String, not int
valid_port = 3  # This will be found
""")

            ports = generator._detect_ports(tmp_path, "main.py")

            # Port 3 is valid (between 1-65535), so it will be found
            assert 3 in ports
        finally:
            import shutil

            shutil.rmtree(tmp_path, ignore_errors=True)

    def test_get_dockerfile_generates_new(self):
        """Test get_dockerfile when no existing Dockerfile."""
        generator = DockerfileGenerator()

        tmp_path = Path("/tmp/test_no_dockerfile")
        tmp_path.mkdir(exist_ok=True)

        try:
            # Create minimal project
            (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-app"
dependencies = []
""")
            (tmp_path / "main.py").write_text("print('Hello')")

            # Mock analyze_project to avoid complex setup
            with patch.object(generator, "analyze_project") as mock_analyze:
                mock_analyze.return_value = {
                    "type": ProjectType.CLI,
                    "python_version": "3.11",
                    "main_entry": "main.py",
                    "system_deps": [],
                    "has_tests": False,
                    "has_frontend": False,
                    "ports": [],
                }

                dockerfile = generator.get_dockerfile(tmp_path)

                assert "FROM python:3.11-slim" in dockerfile
                assert mock_analyze.called
        finally:
            import shutil

            shutil.rmtree(tmp_path, ignore_errors=True)

    def test_validate_dockerfile_valid(self):
        """Test validating a valid Dockerfile."""
        generator = DockerfileGenerator()

        valid_dockerfile = """
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
USER appuser
CMD ["python", "app.py"]
"""

        issues = generator.validate_dockerfile(valid_dockerfile)

        # Should have no issues
        assert len(issues) == 0
