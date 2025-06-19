#!/usr/bin/env python3
"""
environment_snapshot_io.py - Environment snapshot I/O operations

This module handles saving and loading of environment snapshots to/from
various formats (JSON, YAML).
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains snapshot serialization and deserialization logic
#

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from prefect import get_run_logger, task

from DHT.modules.environment_snapshot_models import EnvironmentSnapshot


class EnvironmentSnapshotIO:
    """Handles environment snapshot I/O operations."""

    @task(
        name="save_environment_snapshot",
        description="Save environment snapshot to file"
    )
    def save_snapshot(
        self,
        snapshot: EnvironmentSnapshot,
        output_path: Path,
        format: str = "json"
    ) -> Path:
        """
        Save environment snapshot to file.

        Args:
            snapshot: Environment snapshot to save
            output_path: Path to save the snapshot
            format: Output format ('json' or 'yaml')

        Returns:
            Path to saved snapshot file
        """
        logger = get_run_logger()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert snapshot to dictionary
        snapshot_dict = self._snapshot_to_dict(snapshot)

        # Save in requested format
        if format.lower() == "yaml":
            with open(output_path, 'w') as f:
                yaml.dump(snapshot_dict, f, default_flow_style=False, sort_keys=False)
        else:
            with open(output_path, 'w') as f:
                json.dump(snapshot_dict, f, indent=2, sort_keys=True)

        logger.info(f"Environment snapshot saved to {output_path}")
        return output_path

    @task(
        name="load_environment_snapshot",
        description="Load environment snapshot from file"
    )
    def load_snapshot(self, snapshot_path: Path) -> EnvironmentSnapshot:
        """
        Load environment snapshot from file.

        Args:
            snapshot_path: Path to snapshot file

        Returns:
            EnvironmentSnapshot object
        """
        snapshot_path = Path(snapshot_path)

        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

        # Determine format by extension
        if snapshot_path.suffix.lower() in ['.yaml', '.yml']:
            with open(snapshot_path) as f:
                data = yaml.safe_load(f)
        else:
            with open(snapshot_path) as f:
                data = json.load(f)

        # Reconstruct snapshot object
        return self._dict_to_snapshot(data)

    def _snapshot_to_dict(self, snapshot: EnvironmentSnapshot) -> dict[str, Any]:
        """Convert snapshot object to dictionary."""
        return {
            "metadata": {
                "timestamp": snapshot.timestamp,
                "platform": snapshot.platform,
                "architecture": snapshot.architecture,
                "dht_version": snapshot.dht_version,
                "snapshot_id": snapshot.snapshot_id
            },
            "environment": {
                "python_version": snapshot.python_version,
                "python_executable": snapshot.python_executable,
                "python_packages": snapshot.python_packages,
                "system_packages": snapshot.system_packages,
                "tool_versions": snapshot.tool_versions,
                "tool_paths": snapshot.tool_paths,
                "environment_variables": snapshot.environment_variables,
                "path_entries": snapshot.path_entries
            },
            "project": {
                "project_path": snapshot.project_path,
                "project_type": snapshot.project_type,
                "lock_files": snapshot.lock_files,
                "config_files": snapshot.config_files,
                "checksums": snapshot.checksums
            },
            "reproduction": {
                "steps": snapshot.reproduction_steps,
                "platform_notes": snapshot.platform_notes
            }
        }

    def _dict_to_snapshot(self, data: dict[str, Any]) -> EnvironmentSnapshot:
        """Convert dictionary to snapshot object."""
        metadata = data["metadata"]
        environment = data["environment"]
        project = data["project"]
        reproduction = data["reproduction"]

        return EnvironmentSnapshot(
            timestamp=metadata["timestamp"],
            platform=metadata["platform"],
            architecture=metadata["architecture"],
            dht_version=metadata["dht_version"],
            snapshot_id=metadata["snapshot_id"],
            python_version=environment["python_version"],
            python_executable=environment["python_executable"],
            python_packages=environment["python_packages"],
            system_packages=environment["system_packages"],
            tool_versions=environment["tool_versions"],
            tool_paths=environment["tool_paths"],
            environment_variables=environment["environment_variables"],
            path_entries=environment["path_entries"],
            project_path=project["project_path"],
            project_type=project["project_type"],
            lock_files=project["lock_files"],
            config_files=project["config_files"],
            checksums=project["checksums"],
            reproduction_steps=reproduction["steps"],
            platform_notes=reproduction["platform_notes"]
        )


# Export public API
__all__ = ["EnvironmentSnapshotIO"]
