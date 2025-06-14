#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created container build handler for Docker/Podman projects
# - Supports rootless container builds
# - Stores container configs in project .venv
# 

"""
Container build handler for DHT.
Handles Docker and Podman builds with project-local configuration.
"""

from pathlib import Path
from typing import Dict, Optional, List
import subprocess
import os
import json
import yaml


class ContainerBuildHandler:
    """Handles container builds for DHT projects."""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.venv_path = self.project_path / ".venv"
        self.container_config_path = self.venv_path / "dht-container"
        
    def setup_container_config(self):
        """Set up project-local container configuration."""
        self.container_config_path.mkdir(parents=True, exist_ok=True)
        
        # Create container build config
        config = {
            "builder": self.detect_container_builder(),
            "project_name": self.project_path.name,
            "build_context": ".",
            "dockerfile": "Dockerfile",
            "compose_files": self.find_compose_files(),
            "build_args": {},
            "labels": {
                "dht.project": self.project_path.name,
                "dht.builder": "container_build_handler"
            }
        }
        
        config_file = self.container_config_path / "build-config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
        return config
    
    def detect_container_builder(self) -> Optional[str]:
        """Detect available container builder."""
        # Check for Podman first (rootless by default)
        if self._command_exists("podman"):
            return "podman"
        
        # Check for Docker
        if self._command_exists("docker"):
            # Check if Docker daemon is running
            try:
                result = subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return "docker"
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Check for buildah (another rootless option)
        if self._command_exists("buildah"):
            return "buildah"
        
        return None
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists."""
        try:
            subprocess.run(
                ["which", cmd],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def find_compose_files(self) -> List[str]:
        """Find docker-compose files in the project."""
        compose_patterns = [
            "docker-compose.yml",
            "docker-compose.yaml", 
            "compose.yml",
            "compose.yaml",
            "docker-compose.*.yml",
            "docker-compose.*.yaml"
        ]
        
        files = []
        for pattern in compose_patterns:
            files.extend([str(f.relative_to(self.project_path)) 
                         for f in self.project_path.glob(pattern)])
        
        return sorted(files)
    
    def get_build_commands(self) -> List[str]:
        """Get container build commands based on available tools."""
        builder = self.detect_container_builder()
        
        if not builder:
            return []
        
        # Check if it's a compose project
        compose_files = self.find_compose_files()
        if compose_files:
            if builder == "podman":
                return [f"podman-compose -f {compose_files[0]} build"]
            elif builder == "docker":
                return [f"docker compose -f {compose_files[0]} build"]
        
        # Single container build
        image_name = self.project_path.name.lower().replace("_", "-")
        
        if builder == "podman":
            return [f"podman build -t {image_name} ."]
        elif builder == "docker":
            return [f"docker build -t {image_name} ."]
        elif builder == "buildah":
            return [f"buildah bud -t {image_name} ."]
        
        return []
    
    def install_container_tools(self) -> Dict[str, str]:
        """
        Provide instructions for installing container tools.
        Cannot install system-level tools in venv.
        """
        instructions = {
            "podman": {
                "macos": "brew install podman",
                "linux": "sudo apt-get install podman || sudo dnf install podman",
                "info": "Podman is a daemonless, rootless container engine"
            },
            "docker": {
                "macos": "Install Docker Desktop from docker.com",
                "linux": "curl -fsSL https://get.docker.com | sh",
                "info": "Docker requires a daemon and usually root access"
            },
            "buildah": {
                "macos": "brew install buildah",
                "linux": "sudo apt-get install buildah || sudo dnf install buildah",
                "info": "Buildah is a tool for building OCI container images"
            }
        }
        
        return instructions
    
    def create_rootless_config(self):
        """Create configuration for rootless container builds."""
        config_dir = self.container_config_path / "rootless"
        config_dir.mkdir(exist_ok=True)
        
        # Podman rootless config
        podman_config = {
            "containers": {
                "rootless_networking": "slirp4netns",
                "cgroup_manager": "cgroupfs"
            }
        }
        
        with open(config_dir / "containers.conf", "w") as f:
            for section, values in podman_config.items():
                f.write(f"[{section}]\n")
                for key, value in values.items():
                    f.write(f"{key} = \"{value}\"\n")
                f.write("\n")
        
        # Create storage config for rootless
        storage_config = {
            "storage": {
                "driver": "overlay",
                "runroot": str(self.container_config_path / "runroot"),
                "graphroot": str(self.container_config_path / "storage")
            }
        }
        
        with open(config_dir / "storage.conf", "w") as f:
            for section, values in storage_config.items():
                f.write(f"[{section}]\n")
                for key, value in values.items():
                    f.write(f"{key} = \"{value}\"\n")
                f.write("\n")
        
        return config_dir
    
    def get_container_env(self) -> Dict[str, str]:
        """Get environment variables for container builds."""
        env = os.environ.copy()
        
        # Set container config paths
        config_dir = self.create_rootless_config()
        
        # Podman-specific environment
        env["CONTAINERS_CONF"] = str(config_dir / "containers.conf")
        env["CONTAINERS_STORAGE_CONF"] = str(config_dir / "storage.conf")
        
        # Set runtime directory in project
        env["XDG_RUNTIME_DIR"] = str(self.container_config_path / "runtime")
        os.makedirs(env["XDG_RUNTIME_DIR"], exist_ok=True)
        
        return env


def get_container_build_info(project_path: Path) -> Dict[str, any]:
    """Get container build information for a project."""
    handler = ContainerBuildHandler(project_path)
    
    builder = handler.detect_container_builder()
    if not builder:
        instructions = handler.install_container_tools()
        return {
            "can_build": False,
            "reason": "No container runtime found",
            "install_instructions": instructions,
            "recommendation": "Install Podman for rootless container builds"
        }
    
    commands = handler.get_build_commands()
    config = handler.setup_container_config()
    
    return {
        "can_build": True,
        "builder": builder,
        "commands": commands,
        "config_path": str(handler.container_config_path),
        "compose_files": config["compose_files"],
        "rootless": builder in ["podman", "buildah"]
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()
    
    info = get_container_build_info(project_path)
    
    print(f"Container Build Info for: {project_path}")
    print("=" * 60)
    
    if info["can_build"]:
        print(f"✅ Container build possible!")
        print(f"Builder: {info['builder']}")
        print(f"Rootless: {info['rootless']}")
        print(f"Commands: {info['commands']}")
        if info["compose_files"]:
            print(f"Compose files: {', '.join(info['compose_files'])}")
    else:
        print(f"❌ {info['reason']}")
        print("\nInstallation instructions:")
        for tool, instructions in info["install_instructions"].items():
            print(f"\n{tool}:")
            print(f"  Info: {instructions['info']}")
            print(f"  macOS: {instructions['macos']}")
            print(f"  Linux: {instructions['linux']}")
        print(f"\n💡 {info['recommendation']}")