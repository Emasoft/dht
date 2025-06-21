#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created act container setup module
# - Provides container images with act pre-installed
# - Supports both Docker and Podman
# - Enables complete CI/CD isolation
#

"""
Act container setup for DHT.
Creates and manages container images with act pre-installed.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from prefect import flow, get_run_logger, task
from rich.console import Console

console = Console()


ACT_DOCKERFILE = """
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    sudo \
    ca-certificates \
    gnupg \
    lsb-release \
    jq \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for Docker-in-Docker)
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Install act
RUN curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | bash && \
    mv bin/act /usr/local/bin/act && \
    rm -rf bin

# Install gh CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

# Install actionlint
RUN wget -q https://github.com/rhysd/actionlint/releases/latest/download/actionlint_$(uname -s | tr '[:upper:]' '[:lower:]')_amd64.tar.gz && \
    tar xzf actionlint_*.tar.gz && \
    mv actionlint /usr/local/bin/ && \
    rm actionlint_*.tar.gz

# Create workspace directory
RUN mkdir -p /workspace
WORKDIR /workspace

# Set up environment
ENV DOCKER_HOST=unix:///var/run/docker.sock
ENV HOME=/root

# Entry point
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["act --help"]
"""


PODMAN_ACT_DOCKERFILE = """
FROM quay.io/podman/stable:latest

# Install additional tools
RUN dnf install -y \
    git \
    jq \
    wget \
    tar \
    && dnf clean all

# Install act
RUN curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | bash && \
    mv bin/act /usr/local/bin/act && \
    rm -rf bin

# Install actionlint
RUN wget -q https://github.com/rhysd/actionlint/releases/latest/download/actionlint_linux_amd64.tar.gz && \
    tar xzf actionlint_*.tar.gz && \
    mv actionlint /usr/local/bin/ && \
    rm actionlint_*.tar.gz

# Create workspace directory
RUN mkdir -p /workspace
WORKDIR /workspace

# Set up for rootless operation
ENV HOME=/root
ENV STORAGE_DRIVER=vfs

# Entry point
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["act --help"]
"""


@task(name="build_act_container")
def build_act_container(runtime: str, image_name: str = "dht-act", tag: str = "latest") -> dict[str, Any]:
    """Build container image with act pre-installed."""
    logger = get_run_logger()

    # Choose appropriate Dockerfile
    if runtime == "podman":
        dockerfile_content = PODMAN_ACT_DOCKERFILE
    else:
        dockerfile_content = ACT_DOCKERFILE

    # Create temporary directory for build
    with tempfile.TemporaryDirectory() as tmpdir:
        dockerfile_path = Path(tmpdir) / "Dockerfile"

        # Write Dockerfile
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        # Build image
        full_image_name = f"{image_name}:{tag}"
        logger.info(f"Building act container image: {full_image_name}")

        build_cmd = [runtime, "build", "-t", full_image_name, "-f", str(dockerfile_path), tmpdir]

        try:
            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
            )

            if result.returncode == 0:
                logger.info(f"✅ Successfully built {full_image_name}")
                return {"success": True, "image": full_image_name, "runtime": runtime}
            else:
                logger.error(f"Failed to build image: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except subprocess.TimeoutExpired:
            logger.error("Build timed out after 10 minutes")
            return {"success": False, "error": "Build timeout"}


@task(name="check_act_image")
def check_act_image(runtime: str, image_name: str = "dht-act:latest") -> bool:
    """Check if act container image exists."""
    try:
        result = subprocess.run([runtime, "image", "exists", image_name], capture_output=True)
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class ActContainerRunner:
    """Runs act inside containers for complete isolation."""

    def __init__(self, project_path: Path, runtime: str = "podman"):
        self.project_path = Path(project_path).resolve()
        self.runtime = runtime
        self.image_name = "dht-act:latest"

    def ensure_image(self) -> bool:
        """Ensure act container image is available."""
        if check_act_image(self.runtime, self.image_name):
            console.print("[green]✅ Act container image available[/green]")
            return True

        console.print("[yellow]🔨 Building act container image...[/yellow]")
        result = build_act_container(self.runtime)

        if result["success"]:
            console.print("[green]✅ Act container image built[/green]")
            return True
        else:
            console.print("[red]❌ Failed to build act image[/red]")
            return False

    def run_act(
        self,
        event: str = "push",
        job: str | None = None,
        secrets_file: Path | None = None,
        env_file: Path | None = None,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Run act inside a container."""
        if not self.ensure_image():
            return {"success": False, "error": "Act container image not available"}

        # Build container command
        cmd = [self.runtime, "run", "--rm", "-it"]

        # Mount project directory
        cmd.extend(["-v", f"{self.project_path}:/workspace:z"])

        # Mount Docker/Podman socket for nested containers
        if self.runtime == "docker":
            cmd.extend(["-v", "/var/run/docker.sock:/var/run/docker.sock"])
        else:
            # Podman socket location
            xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000")
            podman_sock = f"{xdg_runtime}/podman/podman.sock"
            if os.path.exists(podman_sock):
                cmd.extend(["-v", f"{podman_sock}:/var/run/docker.sock"])

        # Set working directory
        cmd.extend(["-w", "/workspace"])

        # Enable TTY and interactive mode
        cmd.extend(["--tty", "--interactive"])

        # Add privileged mode for Docker-in-Docker
        cmd.append("--privileged")

        # Use the act container image
        cmd.append(self.image_name)

        # Build act command
        act_cmd = ["act", event]

        if job:
            act_cmd.extend(["-j", job])

        if secrets_file and secrets_file.exists():
            # Copy secrets file into container
            cmd.extend(["-v", f"{secrets_file}:/tmp/.secrets:z"])
            act_cmd.extend(["--secret-file", "/tmp/.secrets"])

        if env_file and env_file.exists():
            # Copy env file into container
            cmd.extend(["-v", f"{env_file}:/tmp/.env:z"])
            act_cmd.extend(["--env-file", "/tmp/.env"])

        if verbose:
            act_cmd.append("-v")

        # Combine container and act commands
        cmd.extend(act_cmd)

        console.print("[cyan]🐳 Running act in container...[/cyan]")
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")

        # Run the command
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=not verbose,
                text=True,
                timeout=1800,  # 30 minutes
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout if not verbose else "",
                "stderr": result.stderr if not verbose else "",
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Workflow timed out after 30 minutes"}
        except Exception as e:
            return {"success": False, "error": str(e)}


@flow(name="act_container_workflow")
def act_container_workflow(
    project_path: str, event: str = "push", job: str | None = None, runtime: str = "podman"
) -> dict[str, Any]:
    """
    Run GitHub Actions in a fully isolated container.

    This provides the most accurate simulation of GitHub's
    CI/CD environment by running act inside a container.
    """
    logger = get_run_logger()
    project_path = Path(project_path).resolve()

    console.print("[bold blue]🐳 DHT Act Container Mode[/bold blue]")
    console.print(f"Project: {project_path.name}")
    console.print(f"Runtime: {runtime}")
    console.print(f"Event: {event}")

    # Create runner
    runner = ActContainerRunner(project_path, runtime)

    # Check for secrets and env files
    act_config_path = project_path / ".venv" / "dht-act"
    secrets_file = act_config_path / ".secrets"
    env_file = act_config_path / ".env"

    # Run act in container
    result = runner.run_act(
        event=event,
        job=job,
        secrets_file=secrets_file if secrets_file.exists() else None,
        env_file=env_file if env_file.exists() else None,
        verbose=True,
    )

    if result["success"]:
        console.print("\n[green]✅ Workflow completed successfully![/green]")
    else:
        console.print("\n[red]❌ Workflow failed![/red]")
        if result.get("error"):
            console.print(f"Error: {result['error']}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DHT Act Container Runner")
    parser.add_argument("path", nargs="?", default=".", help="Project path")
    parser.add_argument("-e", "--event", default="push", help="GitHub event")
    parser.add_argument("-j", "--job", help="Specific job to run")
    parser.add_argument("--runtime", default="podman", choices=["docker", "podman"])

    args = parser.parse_args()

    result = act_container_workflow(project_path=args.path, event=args.event, job=args.job, runtime=args.runtime)

    import sys

    sys.exit(0 if result["success"] else 1)
