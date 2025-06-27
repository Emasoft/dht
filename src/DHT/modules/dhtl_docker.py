#!/usr/bin/env python3
"""
DHT Docker Integration Module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created Docker integration module for DHT
# - Implements Docker container management for tests and workflows
# - Supports multi-stage builds with uv
# - Provides commands for building, running, and managing containers
#

"""
DHT Docker Integration Module.

Provides Docker container support for running tests, workflows, and development
environments using uv for fast dependency management.
"""

import os
import shutil
import subprocess
from pathlib import Path

from prefect import flow, task
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .common_utils import find_project_root
from .dhtl_error_handling import log_debug, log_error, log_info, log_success

console = Console()


class DockerManager:
    """Manages Docker operations for DHT."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize Docker manager."""
        self.project_root = project_root or find_project_root()
        self.dockerfile_path = self.project_root / "Dockerfile"
        self.compose_path = self.project_root / "docker-compose.yml"
        self.docker_cmd = self._find_docker_command()

    def _find_docker_command(self) -> str | None:
        """Find available Docker or Podman command."""
        for cmd in ["docker", "podman"]:
            if shutil.which(cmd):
                return cmd
        return None

    def is_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        if not self.docker_cmd:
            return False

        try:
            result = subprocess.run(
                [self.docker_cmd, "version"],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_docker_compose(self) -> bool:
        """Check if docker-compose is available."""
        # Try docker compose (v2) first
        if self.docker_cmd == "docker":
            try:
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass

        # Try standalone docker-compose
        if shutil.which("docker-compose"):
            return True

        # Try podman-compose for Podman
        if self.docker_cmd == "podman" and shutil.which("podman-compose"):
            return True

        return False

    def get_compose_command(self) -> list[str]:
        """Get the appropriate docker-compose command."""
        if self.docker_cmd == "docker":
            # Try docker compose (v2) first
            try:
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    return ["docker", "compose"]
            except Exception:
                pass

        # Fallback to standalone commands
        if shutil.which("docker-compose"):
            return ["docker-compose"]
        elif self.docker_cmd == "podman" and shutil.which("podman-compose"):
            return ["podman-compose"]

        return []

    def build_image(self, target: str = "runtime", tag: str | None = None) -> bool:
        """Build Docker image for specified target."""
        if not self.docker_cmd:
            log_error("No Docker or Podman command found")
            return False

        if not self.dockerfile_path.exists():
            log_error(f"Dockerfile not found at {self.dockerfile_path}")
            return False

        # Default tag based on target
        if not tag:
            tag = f"dht:{target}"

        log_info(f"Building Docker image '{tag}' for target '{target}'...")

        cmd = [
            self.docker_cmd,
            "build",
            "-f",
            str(self.dockerfile_path),
            "--target",
            target,
            "-t",
            tag,
            ".",
        ]

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task_id = progress.add_task(f"Building {tag}...", total=None)

                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                output_lines = []
                for line in process.stdout:  # type: ignore
                    output_lines.append(line.strip())
                    progress.update(task_id, description=f"Building {tag}... {line.strip()[:50]}")

                process.wait()

                if process.returncode == 0:
                    log_success(f"Successfully built Docker image '{tag}'")
                    return True
                else:
                    log_error("Failed to build Docker image. Last output:")
                    for line in output_lines[-10:]:
                        console.print(f"  {line}", style="red")
                    return False

        except Exception as e:
            log_error(f"Error building Docker image: {e}")
            return False

    def run_container(
        self,
        image: str = "dht:runtime",
        command: list[str] | None = None,
        volumes: dict[str, str] | None = None,
        environment: dict[str, str] | None = None,
        interactive: bool = False,
        remove: bool = True,
    ) -> int:
        """Run a Docker container."""
        if not self.docker_cmd:
            log_error("No Docker or Podman command found")
            return 1

        cmd = [self.docker_cmd, "run"]

        if remove:
            cmd.append("--rm")

        if interactive:
            cmd.extend(["-it"])

        # Add volumes
        if volumes:
            for host_path, container_path in volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])

        # Add environment variables
        if environment:
            for key, value in environment.items():
                cmd.extend(["-e", f"{key}={value}"])

        # Add image
        cmd.append(image)

        # Add command
        if command:
            cmd.extend(command)

        try:
            log_debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=str(self.project_root), check=False)
            return result.returncode
        except Exception as e:
            log_error(f"Error running container: {e}")
            return 1

    def compose_up(self, service: str | None = None, detach: bool = False) -> int:
        """Start docker-compose services."""
        compose_cmd = self.get_compose_command()
        if not compose_cmd:
            log_error("Docker Compose not available")
            return 1

        if not self.compose_path.exists():
            log_error(f"docker-compose.yml not found at {self.compose_path}")
            return 1

        cmd = compose_cmd + ["up"]
        if detach:
            cmd.append("-d")
        if service:
            cmd.append(service)

        try:
            log_info("Starting Docker Compose services...")
            result = subprocess.run(cmd, cwd=str(self.project_root), check=False)
            return result.returncode
        except Exception as e:
            log_error(f"Error starting services: {e}")
            return 1

    def compose_down(self) -> int:
        """Stop docker-compose services."""
        compose_cmd = self.get_compose_command()
        if not compose_cmd:
            log_error("Docker Compose not available")
            return 1

        cmd = compose_cmd + ["down"]

        try:
            log_info("Stopping Docker Compose services...")
            result = subprocess.run(cmd, cwd=str(self.project_root), check=False)
            return result.returncode
        except Exception as e:
            log_error(f"Error stopping services: {e}")
            return 1


@task(name="docker_build", description="Build Docker images")
def docker_build_task(target: str = "runtime", tag: str | None = None) -> bool:
    """Build Docker image for DHT."""
    manager = DockerManager()

    if not manager.is_docker_available():
        log_error("Docker is not available. Please install Docker or Podman.")
        return False

    return manager.build_image(target, tag)


@task(name="docker_test", description="Run tests in Docker")
def docker_test_task(
    test_args: list[str] | None = None,
    coverage: bool = True,
) -> int:
    """Run tests in Docker container."""
    manager = DockerManager()

    if not manager.is_docker_available():
        log_error("Docker is not available. Please install Docker or Podman.")
        return 1

    # Build test image first
    if not manager.build_image("test-runner", "dht:test"):
        return 1

    # Prepare test command
    command = ["pytest", "-v", "--tb=short"]
    if coverage:
        command.extend(
            [
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-report=xml",
            ]
        )
    if test_args:
        command.extend(test_args)

    # Run tests
    volumes = {
        str(manager.project_root / "tests"): "/app/tests:ro",
        str(manager.project_root / "src"): "/app/src:ro",
    }

    environment = {
        "DHT_TEST_MODE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    log_info("Running tests in Docker container...")
    return manager.run_container(
        image="dht:test",
        command=command,
        volumes=volumes,
        environment=environment,
        interactive=False,
    )


@task(name="docker_lint", description="Run linting in Docker")
def docker_lint_task() -> int:
    """Run linting in Docker container."""
    manager = DockerManager()

    if not manager.is_docker_available():
        log_error("Docker is not available. Please install Docker or Podman.")
        return 1

    # Build dev image first
    if not manager.build_image("development", "dht:dev"):
        return 1

    # Run linting
    volumes = {
        str(manager.project_root): "/app:ro",
    }

    log_info("Running linting in Docker container...")
    return manager.run_container(
        image="dht:dev",
        command=["dhtl", "lint", "--all"],
        volumes=volumes,
        interactive=False,
    )


@task(name="docker_workflow", description="Run workflows in Docker")
def docker_workflow_task(event: str = "push", job: str | None = None) -> int:
    """Run GitHub workflows in Docker using act."""
    manager = DockerManager()

    if not manager.is_docker_available():
        log_error("Docker is not available. Please install Docker or Podman.")
        return 1

    # Build runtime image first
    if not manager.build_image("runtime", "dht:latest"):
        return 1

    # Prepare act command
    command = ["dhtl", "act", "--container", "-e", event]
    if job:
        command.extend(["-j", job])

    # Run workflows
    volumes = {
        str(manager.project_root): "/workspace",
        "/var/run/docker.sock": "/var/run/docker.sock:ro",
    }

    environment = {
        "DHT_ENV": "ci",
    }

    # Pass GitHub token if available
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        environment["GITHUB_TOKEN"] = github_token

    log_info("Running workflows in Docker container...")
    return manager.run_container(
        image="dht:latest",
        command=command,
        volumes=volumes,
        environment=environment,
        interactive=True,
    )


@flow(name="docker_operations")
def docker_operations_flow(
    operation: str,
    target: str | None = None,
    service: str | None = None,
    args: list[str] | None = None,
) -> int:
    """
    Manage Docker operations for DHT.

    Args:
        operation: The operation to perform (build, test, lint, workflow, up, down)
        target: Docker build target (for build operation)
        service: Docker Compose service name (for up operation)
        args: Additional arguments for the operation

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    console.print(
        Panel.fit(
            f"🐳 DHT Docker Operations\n"
            f"📦 Operation: {operation}\n\n"
            f"[dim]Using uv for fast dependency management[/dim]",
            style="bold blue",
        )
    )

    manager = DockerManager()

    # Check Docker availability
    if not manager.is_docker_available():
        console.print("[red]❌ Docker is not available![/red]")
        console.print("Please install Docker or Podman:")
        console.print("  - Docker: https://docs.docker.com/get-docker/")
        console.print("  - Podman: https://podman.io/getting-started/installation")
        return 1

    console.print(f"[green]✅ Using {manager.docker_cmd}[/green]")

    # Execute operation
    if operation == "build":
        target = target or "runtime"
        success = docker_build_task(target)
        return 0 if success else 1

    elif operation == "test":
        return docker_test_task(test_args=args)

    elif operation == "lint":
        return docker_lint_task()

    elif operation == "workflow":
        event = args[0] if args else "push"
        job = args[1] if args and len(args) > 1 else None
        return docker_workflow_task(event, job)

    elif operation == "up":
        if not manager.check_docker_compose():
            console.print("[red]❌ Docker Compose not available![/red]")
            return 1
        return manager.compose_up(service)

    elif operation == "down":
        if not manager.check_docker_compose():
            console.print("[red]❌ Docker Compose not available![/red]")
            return 1
        return manager.compose_down()

    elif operation == "shell":
        # Run interactive shell in development container
        if not manager.build_image("development", "dht:dev"):
            return 1

        volumes = {
            str(manager.project_root): "/app",
        }

        log_info("Starting interactive shell in Docker container...")
        return manager.run_container(
            image="dht:dev",
            command=["bash"],
            volumes=volumes,
            interactive=True,
        )

    else:
        log_error(f"Unknown operation: {operation}")
        console.print("\nAvailable operations:")
        console.print("  build   - Build Docker images")
        console.print("  test    - Run tests in Docker")
        console.print("  lint    - Run linting in Docker")
        console.print("  workflow - Run workflows with act in Docker")
        console.print("  shell   - Start interactive shell")
        console.print("  up      - Start Docker Compose services")
        console.print("  down    - Stop Docker Compose services")
        return 1


def docker_command(args: list[str]) -> int:
    """
    Docker command entry point.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    import argparse

    parser = argparse.ArgumentParser(description="DHT Docker operations")
    parser.add_argument(
        "operation",
        choices=["build", "test", "lint", "workflow", "shell", "up", "down"],
        help="Docker operation to perform",
    )
    parser.add_argument(
        "--target",
        choices=["runtime", "development", "test-runner"],
        default="runtime",
        help="Docker build target",
    )
    parser.add_argument(
        "--service",
        help="Docker Compose service name",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments for the operation",
    )

    parsed_args = parser.parse_args(args)

    return docker_operations_flow(
        operation=parsed_args.operation,
        target=parsed_args.target,
        service=parsed_args.service,
        args=parsed_args.args,
    )


# Export command function
__all__ = ["docker_command", "DockerManager", "docker_operations_flow"]
