#!/usr/bin/env python3
"""
act_setup_manager.py - Act installation and setup management

This module handles installation, configuration, and availability checking
for act and related tools.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from act_integration.py to reduce file size
# - Contains act setup and availability checking functionality
#

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from DHT.modules.act_integration_models import ActCheckResult, ActConfig


class ActSetupManager:
    """Manages act installation and setup."""

    def __init__(self, project_path: Path):
        """Initialize setup manager.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path).resolve()
        self.venv_path = self.project_path / ".venv"
        self.act_config_path = self.venv_path / "dht-act"
        self.logger = logging.getLogger(__name__)

    def check_act_available(self) -> ActCheckResult:
        """Check if act is available via various methods.

        Returns:
            ActCheckResult with availability information
        """
        result = ActCheckResult(
            gh_cli_available=False,
            gh_cli_version=None,
            act_extension_installed=False,
            act_extension_version=None,
            standalone_act_available=False,
            standalone_act_version=None,
            act_available=False,
            preferred_method=None,
        )

        # Check gh CLI
        if shutil.which("gh"):
            result.gh_cli_available = True
            try:
                version_output = subprocess.run(["gh", "--version"], capture_output=True, text=True, check=True)
                # Parse version from "gh version X.Y.Z (YYYY-MM-DD)"
                version_line = version_output.stdout.strip().split("\n")[0]
                result.gh_cli_version = version_line.split()[2]
            except (subprocess.CalledProcessError, FileNotFoundError, OSError, IndexError) as e:
                self.logger.debug(f"Failed to get gh version: {e}")

            # Check if act extension is installed
            try:
                ext_list = subprocess.run(["gh", "extension", "list"], capture_output=True, text=True, check=True)
                if "nektos/gh-act" in ext_list.stdout:
                    result.act_extension_installed = True
                    # Try to get version
                    try:
                        act_version = subprocess.run(["gh", "act", "--version"], capture_output=True, text=True)
                        if act_version.returncode == 0:
                            result.act_extension_version = act_version.stdout.strip()
                    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
                        self.logger.debug(f"Failed to get act extension version: {e}")
            except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
                self.logger.debug(f"Failed to check act extension: {e}")

        # Check standalone act
        if shutil.which("act"):
            result.standalone_act_available = True
            try:
                version_output = subprocess.run(["act", "--version"], capture_output=True, text=True, check=True)
                result.standalone_act_version = version_output.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
                self.logger.debug(f"Failed to get standalone act version: {e}")

        # Determine availability and preferred method
        if result.act_extension_installed:
            result.act_available = True
            result.preferred_method = "gh-extension"
        elif result.standalone_act_available:
            result.act_available = True
            result.preferred_method = "standalone"

        return result

    def install_gh_act_extension(self) -> bool:
        """Install gh-act extension.

        Returns:
            True if installation successful
        """
        try:
            subprocess.run(["gh", "extension", "install", "nektos/gh-act"], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def setup_act_config(self, config: ActConfig | None = None) -> Path:
        """Setup act configuration.

        Args:
            config: ActConfig instance or None for defaults

        Returns:
            Path to config directory
        """
        if config is None:
            config = ActConfig()

        # Create config directory
        self.act_config_path.mkdir(parents=True, exist_ok=True)

        # Write act config
        act_json = {
            "-P": f"{config.platform}={config.runner_image}",
            "--container-architecture": "linux/amd64",
            "--container-daemon-socket": "-",  # Will be set dynamically
        }

        if config.artifact_server_path:
            act_json["--artifact-server-path"] = config.artifact_server_path

        if config.cache_server_path:
            act_json["--cache-server-path"] = config.cache_server_path

        if config.bind_workdir:
            act_json["--bind"] = ""

        if config.reuse_containers:
            act_json["--reuse"] = ""

        # Write config
        config_file = self.act_config_path / "act.json"
        with open(config_file, "w") as f:
            json.dump(act_json, f, indent=2)

        # Create secrets file template
        secrets_file = self.act_config_path / "secrets"
        if not secrets_file.exists():
            secrets_file.write_text("# Add secrets here in KEY=value format\n# GITHUB_TOKEN=your_token_here\n")

        # Create env file template
        env_file = self.act_config_path / "env"
        if not env_file.exists():
            env_file.write_text("# Add environment variables here in KEY=value format\n# CI=true\n")

        return self.act_config_path
