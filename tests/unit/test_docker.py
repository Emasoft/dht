#!/usr/bin/env python3
"""
Tests for DHT Docker integration.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.DHT.modules.dhtl_docker import DockerManager, docker_build_task, docker_test_task


class TestDockerManager:
    """Test Docker manager functionality."""

    def test_find_docker_command(self, tmp_path: Path) -> None:
        """Test finding Docker or Podman command."""
        # Mock shutil.which
        with patch("src.DHT.modules.dhtl_docker.shutil.which") as mock_which:
            # Test Docker found
            mock_which.side_effect = lambda cmd: cmd == "docker"
            manager = DockerManager(tmp_path)
            assert manager.docker_cmd == "docker"

            # Test Podman found
            mock_which.side_effect = lambda cmd: cmd == "podman"
            manager = DockerManager(tmp_path)
            assert manager.docker_cmd == "podman"

            # Test neither found
            mock_which.side_effect = lambda cmd: None
            manager = DockerManager(tmp_path)
            assert manager.docker_cmd is None

    def test_is_docker_available(self, tmp_path: Path) -> None:
        """Test checking Docker availability."""
        manager = DockerManager(tmp_path)

        with patch.object(manager, "docker_cmd", "docker"):
            with patch("subprocess.run") as mock_run:
                # Test Docker available
                mock_run.return_value = MagicMock(returncode=0)
                assert manager.is_docker_available() is True

                # Test Docker not available
                mock_run.return_value = MagicMock(returncode=1)
                assert manager.is_docker_available() is False

                # Test exception
                mock_run.side_effect = Exception("Docker error")
                assert manager.is_docker_available() is False

    def test_check_docker_compose(self, tmp_path: Path) -> None:
        """Test checking docker-compose availability."""
        manager = DockerManager(tmp_path)

        with patch("subprocess.run") as mock_run:
            with patch("src.DHT.modules.dhtl_docker.shutil.which") as mock_which:
                # Test docker compose v2
                manager.docker_cmd = "docker"
                mock_run.return_value = MagicMock(returncode=0)
                assert manager.check_docker_compose() is True

                # Test standalone docker-compose
                mock_run.return_value = MagicMock(returncode=1)
                mock_which.side_effect = lambda cmd: cmd == "docker-compose"
                assert manager.check_docker_compose() is True

                # Test podman-compose
                manager.docker_cmd = "podman"
                mock_which.side_effect = lambda cmd: cmd == "podman-compose"
                assert manager.check_docker_compose() is True

                # Test none available
                manager.docker_cmd = "docker"
                mock_run.return_value = MagicMock(returncode=1)
                mock_which.side_effect = lambda cmd: False
                assert manager.check_docker_compose() is False

    def test_get_compose_command(self, tmp_path: Path) -> None:
        """Test getting docker-compose command."""
        manager = DockerManager(tmp_path)

        with patch("subprocess.run") as mock_run:
            with patch("src.DHT.modules.dhtl_docker.shutil.which") as mock_which:
                # Test docker compose v2
                manager.docker_cmd = "docker"
                mock_run.return_value = MagicMock(returncode=0)
                assert manager.get_compose_command() == ["docker", "compose"]

                # Test standalone docker-compose
                mock_run.return_value = MagicMock(returncode=1)
                mock_which.side_effect = lambda cmd: cmd == "docker-compose"
                assert manager.get_compose_command() == ["docker-compose"]

                # Test podman-compose
                manager.docker_cmd = "podman"
                mock_which.side_effect = lambda cmd: cmd == "podman-compose"
                assert manager.get_compose_command() == ["podman-compose"]

    def test_build_image(self, tmp_path: Path) -> None:
        """Test building Docker image."""
        # Create mock Dockerfile
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.11-slim\n")

        manager = DockerManager(tmp_path)
        manager.docker_cmd = "docker"

        with patch("subprocess.Popen") as mock_popen:
            # Mock successful build
            mock_process = MagicMock()
            mock_process.stdout = ["Step 1/1 : FROM python:3.11-slim\n", "Successfully built abc123\n"]
            mock_process.wait.return_value = None
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            result = manager.build_image("runtime", "test:latest")
            assert result is True

            # Verify command
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            assert args[0] == "docker"
            assert args[1] == "build"
            assert "--target" in args
            assert "runtime" in args
            assert "-t" in args
            assert "test:latest" in args

    def test_run_container(self, tmp_path: Path) -> None:
        """Test running Docker container."""
        manager = DockerManager(tmp_path)
        manager.docker_cmd = "docker"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Test basic run
            result = manager.run_container(
                image="test:latest",
                command=["echo", "hello"],
                volumes={"/host": "/container"},
                environment={"FOO": "bar"},
                interactive=True,
                remove=True,
            )
            assert result == 0

            # Verify command
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "docker"
            assert args[1] == "run"
            assert "--rm" in args
            assert "-it" in args
            assert "-v" in args
            assert "/host:/container" in args
            assert "-e" in args
            assert "FOO=bar" in args
            assert "test:latest" in args
            assert "echo" in args
            assert "hello" in args


class TestDockerTasks:
    """Test Docker Prefect tasks."""

    def test_docker_build_task(self, tmp_path: Path) -> None:
        """Test docker build task."""
        with patch("src.DHT.modules.dhtl_docker.DockerManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.is_docker_available.return_value = True
            mock_manager.build_image.return_value = True
            mock_manager_class.return_value = mock_manager

            # Test successful build
            result = docker_build_task.fn("runtime", "test:latest")
            assert result is True
            mock_manager.build_image.assert_called_once_with("runtime", "test:latest")

            # Test Docker not available
            mock_manager.is_docker_available.return_value = False
            result = docker_build_task.fn("runtime")
            assert result is False

    def test_docker_test_task(self, tmp_path: Path) -> None:
        """Test docker test task."""
        with patch("src.DHT.modules.dhtl_docker.DockerManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.is_docker_available.return_value = True
            mock_manager.build_image.return_value = True
            mock_manager.run_container.return_value = 0
            mock_manager.project_root = tmp_path
            mock_manager_class.return_value = mock_manager

            # Test successful test run
            result = docker_test_task.fn(["-k", "test_something"], coverage=True)
            assert result == 0

            # Verify build was called
            mock_manager.build_image.assert_called_once_with("test-runner", "dht:test")

            # Verify run was called with correct args
            mock_manager.run_container.assert_called_once()
            call_args = mock_manager.run_container.call_args
            assert call_args[1]["image"] == "dht:test"
            assert "-k" in call_args[1]["command"]
            assert "test_something" in call_args[1]["command"]
            assert "--cov=src" in call_args[1]["command"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
