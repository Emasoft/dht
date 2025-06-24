#!/usr/bin/env python3
from __future__ import annotations

"""
act_container_manager.py - Container management for act integration

This module handles container runtime detection, setup, and management
for running act in containerized environments.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from act_integration.py to reduce file size
# - Contains container-related functionality for act
#


import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from DHT.modules.act_integration_models import ActConfig, ContainerSetupResult


class ActContainerManager:
    """Manages container environments for act."""

    def __init__(self, project_path: Path) -> None:
        """Initialize container manager.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path).resolve()
        self.venv_path = self.project_path / ".venv"
        self.act_config_path = self.venv_path / "dht-act"

    def _get_container_socket(self, runtime: str) -> str:
        """Get container runtime socket path.

        Args:
            runtime: Container runtime (docker/podman)

        Returns:
            Socket path
        """
        if runtime == "podman":
            # Check for rootless podman socket
            xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
            return f"{xdg_runtime}/podman/podman.sock"
        else:
            return "/var/run/docker.sock"

    def setup_container_environment(self) -> ContainerSetupResult:
        """Setup container environment for act.

        Returns:
            ContainerSetupResult with setup information
        """
        result = ContainerSetupResult(
            success=False, runtime_available=False, runtime=None, socket_path=None, volumes=[], environment={}
        )

        # Check available container runtimes
        for runtime in ["podman", "docker"]:
            if shutil.which(runtime):
                result.runtime_available = True
                result.runtime = runtime
                break

        if not result.runtime_available:
            result.error = "No container runtime found (docker or podman)"
            return result

        # Get socket path
        socket_path = self._get_container_socket(result.runtime)

        # Verify socket exists and is accessible
        if not Path(socket_path).exists():
            if result.runtime == "podman":
                # Try to start podman service
                try:
                    subprocess.Popen(
                        ["podman", "system", "service", "--time=0"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except (subprocess.SubprocessError, OSError, FileNotFoundError) as e:
                    result.error = f"Podman socket not found at {socket_path}: {str(e)}"
                    return result
            else:
                result.error = f"Docker socket not found at {socket_path}"
                return result

        result.socket_path = socket_path

        # Setup volumes
        result.volumes = [f"{self.project_path}:/workspace", f"{socket_path}:/var/run/docker.sock"]

        # Add cache volumes if they exist
        cache_dir = self.venv_path / "act-cache"
        if cache_dir.exists():
            result.volumes.append(f"{cache_dir}:/cache")

        # Setup environment
        result.environment = {
            "DOCKER_HOST": f"unix://{socket_path}",
            "ACT_CACHE_DIR": "/cache",
            "WORKSPACE": "/workspace",
        }

        result.success = True
        return result

    def _get_container_act_command(self, config: ActConfig) -> list[str]:
        """Get act command for container execution.

        Args:
            config: Act configuration

        Returns:
            List of command arguments
        """
        container_setup = self.setup_container_environment()
        if not container_setup.success:
            raise RuntimeError(f"Container setup failed: {container_setup.error}")

        cmd = [container_setup.runtime, "run", "--rm", "-it"]

        # Add volumes
        for volume in container_setup.volumes:
            cmd.extend(["-v", volume])

        # Add environment
        for key, value in container_setup.environment.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add working directory
        cmd.extend(["-w", "/workspace"])

        # Security options for rootless
        if container_setup.runtime == "podman":
            cmd.extend(["--security-opt", "label=disable"])
            cmd.extend(["--userns=keep-id"])

        # Add image
        cmd.append("nektos/act:latest")

        # Add act-specific arguments
        cmd.extend(
            ["-P", f"{config.platform}={config.runner_image}", "--container-daemon-socket", container_setup.socket_path]
        )

        return cmd

    def run_in_container(
        self, act_args: list[str], config: ActConfig | None = None
    ) -> subprocess.CompletedProcess[Any]:
        """Run act command in container.

        Args:
            act_args: Arguments to pass to act
            config: Act configuration

        Returns:
            Completed process result
        """
        if config is None:
            config = ActConfig()

        cmd = self._get_container_act_command(config)
        cmd.extend(act_args)

        return subprocess.run(cmd, cwd=self.project_path, text=True, capture_output=True)
