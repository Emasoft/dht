#!/usr/bin/env python3
"""
reproduction_artifacts.py - Create Prefect artifacts for environment reproduction

This module handles creation of artifacts and documentation for environment
reproduction workflows.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains artifact creation and documentation generation
#

from __future__ import annotations

from pathlib import Path
from typing import Any

from prefect.artifacts import create_markdown_artifact, create_table_artifact

from DHT.modules.environment_snapshot_models import EnvironmentSnapshot


class ReproductionArtifactCreator:
    """Creates artifacts for environment reproduction."""

    def __init__(self, version_critical_tools: set):
        """Initialize the artifact creator."""
        self.version_critical_tools = version_critical_tools

    def create_reproduction_artifacts(self, snapshot: EnvironmentSnapshot, results: dict[str, Any], output_dir: Path):
        """Create Prefect artifacts with reproduction information."""
        # Create reproduction guide markdown
        guide = self._generate_reproduction_guide(snapshot, results)

        # Create markdown artifact (replace underscores with dashes for key)
        artifact_key = f"reproduction-guide-{snapshot.snapshot_id.replace('_', '-')}"
        create_markdown_artifact(
            key=artifact_key, markdown=guide, description=f"Environment reproduction guide for {snapshot.snapshot_id}"
        )

        # Create tool versions table
        tool_data = self._create_tool_versions_table(snapshot)

        # Replace underscores with dashes for key
        table_key = f"tool-versions-{snapshot.snapshot_id.replace('_', '-')}"
        create_table_artifact(
            key=table_key, table=tool_data, description=f"Tool versions for snapshot {snapshot.snapshot_id}"
        )

        # Save reproduction guide to file
        guide_file = output_dir / f"{snapshot.snapshot_id}_reproduction_guide.md"
        guide_file.write_text(guide, encoding="utf-8")

    def _generate_reproduction_guide(self, snapshot: EnvironmentSnapshot, results: dict[str, Any]) -> str:
        """Generate markdown reproduction guide."""
        guide = f"""# Environment Reproduction Guide

**Snapshot ID**: {snapshot.snapshot_id}
**Platform**: {snapshot.platform} ({snapshot.architecture})
**Python Version**: {snapshot.python_version}
**Timestamp**: {snapshot.timestamp}

## Quick Reproduction

### Prerequisites
"""

        for tool, version in snapshot.tool_versions.items():
            if tool in self.version_critical_tools:
                guide += f"- {tool} {version}\n"

        guide += "\n### Reproduction Steps\n"
        for i, step in enumerate(snapshot.reproduction_steps, 1):
            guide += f"{i}. {step}\n"

        if snapshot.platform_notes:
            guide += "\n### Platform-Specific Notes\n"
            for note in snapshot.platform_notes:
                guide += f"- {note}\n"

        # Add verification results if available
        if "verification" in results:
            guide += self._add_verification_results(results["verification"])

        return guide

    def _add_verification_results(self, verification: dict[str, Any]) -> str:
        """Add verification results to the guide."""
        section = "\n## Verification Results\n"
        section += f"**Status**: {'✅ Passed' if verification['success'] else '❌ Failed'}\n\n"

        if verification.get("version_mismatches"):
            section += "### Version Mismatches\n"
            for tool, (expected, actual) in verification["version_mismatches"].items():
                section += f"- {tool}: expected {expected}, found {actual}\n"

        if verification.get("missing_tools"):
            section += "### Missing Tools\n"
            for tool in verification["missing_tools"]:
                section += f"- {tool}\n"

        if verification.get("warnings"):
            section += "### Warnings\n"
            for warning in verification["warnings"]:
                section += f"- {warning}\n"

        return section

    def _create_tool_versions_table(self, snapshot: EnvironmentSnapshot) -> list[dict[str, str]]:
        """Create tool versions table data."""
        tool_data = []
        for tool, version in snapshot.tool_versions.items():
            path = snapshot.tool_paths.get(tool, "")
            critical = "Yes" if tool in self.version_critical_tools else "No"
            tool_data.append({"Tool": tool, "Version": version, "Path": path, "Critical": critical})
        return tool_data


# Export public API
__all__ = ["ReproductionArtifactCreator"]
