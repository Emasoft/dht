#!/usr/bin/env python3
"""
Docker Manager Module.  Handles Docker operations for container deployment including image building, container management, and log streaming.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Docker Manager Module.

Handles Docker operations for container deployment including
image building, container management, and log streaming.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of DockerManager class
# - Implements Docker availability and daemon checks
# - Implements image building and container management
# - Implements log streaming and port checking
# - Adds comprehensive error handling
#

import logging
import shutil
import socket
from contextlib import closing
from pathlib import Path
from typing import Any

import docker
import docker.errors
from docker.models.containers import Container
from prefect import task


class DockerError(Exception):
    """Custom exception for Docker-related errors."""

    pass


class DockerManager:
    """Manages Docker operations for container deployment."""

    def __init__(self):
        """Initialize DockerManager."""
        self.logger = logging.getLogger(__name__)
        self._client = None

    @property
    def client(self):
        """Get Docker client, creating if necessary."""
        if self._client is None:
            try:
                self._client = docker.from_env()
            except docker.errors.DockerException as e:
                self.logger.error(f"Failed to create Docker client: {e}")
                raise DockerError(f"Failed to connect to Docker: {e}") from e
        return self._client

    def is_docker_available(self) -> bool:
        """Check if Docker is installed on the system."""
        return shutil.which("docker") is not None

    def is_daemon_running(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            self.client.ping()
            return True
        except Exception as e:
            self.logger.debug(f"Docker daemon not running: {e}")
            return False

    def check_docker_requirements(self) -> None:
        """Check if Docker is available and daemon is running."""
        if not self.is_docker_available():
            raise RuntimeError("Docker is not installed. Please install Docker from https://docker.com")

        if not self.is_daemon_running():
            raise RuntimeError("Docker daemon is not running. Please start Docker Desktop or the Docker service.")

    def is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding."""
        if port <= 0 or port > 65535:
            return False

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(("", port))
                return True
            except OSError:
                return False

    @task
    def build_image(
        self, context_path: Path, tag: str, dockerfile: str | None = None, buildargs: dict[str, str] | None = None
    ) -> tuple[bool, str]:
        """
        Build Docker image from context.

        Args:
            context_path: Path to build context
            tag: Tag for the image
            dockerfile: Dockerfile content or path
            buildargs: Build arguments

        Returns:
            Tuple of (success, logs)
        """
        self.check_docker_requirements()

        try:
            self.logger.info(f"Building Docker image: {tag}")

            # Prepare build kwargs
            build_kwargs = {
                "path": str(context_path),
                "tag": tag,
                "rm": True,  # Remove intermediate containers
                "decode": True,  # Decode log messages
            }

            if dockerfile:
                if dockerfile.startswith("FROM"):
                    # Dockerfile content provided
                    build_kwargs["fileobj"] = dockerfile.encode()
                else:
                    # Dockerfile path provided
                    build_kwargs["dockerfile"] = dockerfile

            if buildargs:
                build_kwargs["buildargs"] = buildargs

            # Build image
            image, logs = self.client.images.build(**build_kwargs)

            # Collect log output
            log_output = []
            for log in logs:
                if "stream" in log:
                    log_output.append(log["stream"].strip())

            log_str = "\n".join(log_output)
            self.logger.info(f"Successfully built image: {tag}")

            return True, log_str

        except docker.errors.BuildError as e:
            self.logger.error(f"Build failed: {e}")
            raise DockerError(f"Failed to build image: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during build: {e}")
            raise DockerError(f"Failed to build image: {e}") from e

    @task
    def run_container(
        self,
        image: str,
        name: str,
        command: str | list[str] | None = None,
        ports: dict[str, int] | None = None,
        environment: dict[str, str] | None = None,
        volumes: dict[str, dict[str, str]] | None = None,
        detach: bool = True,
        remove: bool = False,
    ) -> Container:
        """
        Run a Docker container.

        Args:
            image: Image to run
            name: Container name
            command: Command to run
            ports: Port mapping
            environment: Environment variables
            volumes: Volume mapping
            detach: Run in background
            remove: Remove container when stopped

        Returns:
            Container object
        """
        self.check_docker_requirements()

        try:
            # Check if container with same name exists
            try:
                existing = self.client.containers.get(name)
                self.logger.warning(f"Container {name} already exists, removing...")
                existing.stop()
                existing.remove()
            except docker.errors.NotFound:
                self.logger.debug(f"Container {name} does not exist, proceeding with creation")

            self.logger.info(f"Running container: {name}")

            # Run container
            container = self.client.containers.run(
                image=image,
                name=name,
                command=command,
                ports=ports,
                environment=environment,
                volumes=volumes,
                detach=detach,
                auto_remove=remove,
            )

            self.logger.info(f"Container {name} started successfully")
            return container

        except docker.errors.ImageNotFound:
            raise DockerError(f"Image not found: {image}") from None
        except docker.errors.APIError as e:
            raise DockerError(f"Failed to run container: {e}") from e
        except Exception as e:
            raise DockerError(f"Unexpected error running container: {e}") from e

    def stop_container(self, name_or_id: str, timeout: int = 10) -> None:
        """
        Stop and remove a container.

        Args:
            name_or_id: Container name or ID
            timeout: Timeout for stopping
        """
        try:
            container = self.client.containers.get(name_or_id)
            self.logger.info(f"Stopping container: {name_or_id}")

            container.stop(timeout=timeout)
            container.remove()

            self.logger.info(f"Container {name_or_id} stopped and removed")

        except docker.errors.NotFound:
            self.logger.warning(f"Container not found: {name_or_id}")
        except Exception as e:
            self.logger.error(f"Failed to stop container: {e}")
            raise DockerError(f"Failed to stop container: {e}") from e

    def stream_logs(self, name_or_id: str, follow: bool = False, tail: int | None = None) -> str:
        """
        Stream logs from a container.

        Args:
            name_or_id: Container name or ID
            follow: Follow log output
            tail: Number of lines to tail

        Returns:
            Log output as string
        """
        try:
            container = self.client.containers.get(name_or_id)

            logs = container.logs(stream=follow, follow=follow, tail=tail if tail else "all")

            if follow:
                # Return generator for streaming
                return logs
            else:
                # Return decoded string
                if isinstance(logs, bytes):
                    return logs.decode("utf-8")
                return logs

        except docker.errors.NotFound:
            raise DockerError(f"Container not found: {name_or_id}") from None
        except Exception as e:
            raise DockerError(f"Failed to get logs: {e}") from e

    def exec_command(
        self,
        name_or_id: str,
        command: str | list[str],
        workdir: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> tuple[int, str]:
        """
        Execute command in running container.

        Args:
            name_or_id: Container name or ID
            command: Command to execute
            workdir: Working directory
            environment: Environment variables

        Returns:
            Tuple of (exit_code, output)
        """
        try:
            container = self.client.containers.get(name_or_id)

            exec_result = container.exec_run(cmd=command, workdir=workdir, environment=environment, demux=False)

            exit_code = exec_result.exit_code
            output = exec_result.output.decode("utf-8") if exec_result.output else ""

            return exit_code, output

        except docker.errors.NotFound:
            raise DockerError(f"Container not found: {name_or_id}") from None
        except Exception as e:
            raise DockerError(f"Failed to execute command: {e}") from e

    def get_container_info(self, name_or_id: str) -> dict[str, Any]:
        """
        Get container information.

        Args:
            name_or_id: Container name or ID

        Returns:
            Container information dict
        """
        try:
            container = self.client.containers.get(name_or_id)

            # Get port mappings
            ports = {}
            if container.attrs.get("NetworkSettings", {}).get("Ports"):
                for container_port, host_info in container.attrs["NetworkSettings"]["Ports"].items():
                    if host_info:
                        ports[container_port] = host_info[0]["HostPort"]

            return {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "ports": ports,
                "created": container.attrs.get("Created"),
                "state": container.attrs.get("State", {}),
            }

        except docker.errors.NotFound:
            raise DockerError(f"Container not found: {name_or_id}") from None
        except Exception as e:
            raise DockerError(f"Failed to get container info: {e}") from e

    def close(self) -> None:
        """Close Docker client connection."""
        if self._client:
            try:
                self._client.close()
                self._client = None
            except Exception as e:
                self.logger.debug(f"Error closing Docker client: {e}")

    def cleanup_containers(self, name_prefix: str) -> int:
        """
        Clean up containers with given name prefix.

        Args:
            name_prefix: Prefix of container names to clean up

        Returns:
            Number of containers cleaned up
        """
        cleaned = 0

        try:
            containers = self.client.containers.list(all=True)

            for container in containers:
                if container.name.startswith(name_prefix):
                    try:
                        self.logger.info(f"Cleaning up container: {container.name}")
                        container.stop(timeout=5)
                        container.remove()
                        cleaned += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up {container.name}: {e}")

            return cleaned

        except Exception as e:
            self.logger.error(f"Failed to cleanup containers: {e}")
            return cleaned

    def cleanup_images(self, tag_prefix: str) -> int:
        """
        Clean up images with given tag prefix.

        Args:
            tag_prefix: Prefix of image tags to clean up

        Returns:
            Number of images cleaned up
        """
        cleaned = 0

        try:
            images = self.client.images.list()

            for image in images:
                for tag in image.tags:
                    if tag.startswith(tag_prefix):
                        try:
                            self.logger.info(f"Cleaning up image: {tag}")
                            self.client.images.remove(image.id, force=True)
                            cleaned += 1
                            break
                        except Exception as e:
                            self.logger.warning(f"Failed to clean up {tag}: {e}")

            return cleaned

        except Exception as e:
            self.logger.error(f"Failed to cleanup images: {e}")
            return cleaned
