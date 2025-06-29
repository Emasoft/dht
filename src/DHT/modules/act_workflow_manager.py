#!/usr/bin/env python3
from __future__ import annotations

"""
act_workflow_manager.py - GitHub workflow discovery and management

This module handles discovery, parsing, and management of GitHub Actions workflows.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from act_integration.py to reduce file size
# - Contains workflow discovery and parsing functionality
#


from pathlib import Path
from typing import Any

import yaml

from DHT.modules.act_integration_models import WorkflowInfo


class ActWorkflowManager:
    """Manages GitHub Actions workflows."""

    def __init__(self, project_path: Path) -> None:
        """Initialize workflow manager.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path).resolve()
        self.workflows_path = self.project_path / ".github" / "workflows"

    def has_workflows(self) -> bool:
        """Check if project has GitHub workflows.

        Returns:
            True if workflows exist
        """
        return self.workflows_path.exists() and any(
            f.suffix in [".yml", ".yaml"] for f in self.workflows_path.iterdir() if f.is_file()
        )

    def get_workflows(self) -> list[WorkflowInfo]:
        """Get list of workflows with their metadata.

        Returns:
            List of WorkflowInfo objects
        """
        workflows: list[WorkflowInfo] = []

        if not self.has_workflows():
            return workflows

        for workflow_file in sorted(self.workflows_path.glob("*.y*ml")):
            try:
                with open(workflow_file) as f:
                    workflow_data = yaml.safe_load(f)

                workflows.append(
                    WorkflowInfo(
                        file=workflow_file.name,
                        name=workflow_data.get("name", workflow_file.stem),
                        on=workflow_data.get("on", {}),
                        jobs=list(workflow_data.get("jobs", {}).keys()),
                        path=str(workflow_file),
                    )
                )
            except Exception as e:
                workflows.append(
                    WorkflowInfo(
                        file=workflow_file.name,
                        name=workflow_file.stem,
                        path=str(workflow_file),
                        on={},
                        jobs=[],
                        error=str(e),
                    )
                )

        return workflows

    def list_workflows_and_jobs(self) -> dict[str, Any]:
        """List all workflows and their jobs.

        Returns:
            Dictionary with workflows and jobs information
        """
        result = {"workflows": {}, "total_workflows": 0, "total_jobs": 0}

        workflows = self.get_workflows()

        for workflow in workflows:
            if workflow.error:
                workflows_dict = result.get("workflows", {})
                workflows_dict[workflow.file] = {"name": workflow.name, "error": workflow.error}  # type: ignore[index]
            else:
                workflows_dict = result.get("workflows", {})
                workflows_dict[workflow.file] = {  # type: ignore[index]
                    "name": workflow.name,
                    "jobs": workflow.jobs,
                    "triggers": list(workflow.on.keys()) if isinstance(workflow.on, dict) else [workflow.on],
                }
                result["total_jobs"] = int(str(result.get("total_jobs", 0))) + len(workflow.jobs or [])

        result["total_workflows"] = len(workflows)
        return result

    def get_workflow_events(self) -> list[str]:
        """Get all unique events from workflows.

        Returns:
            List of unique event names
        """
        events: set[str] = set()
        workflows = self.get_workflows()

        for workflow in workflows:
            if not workflow.error and workflow.on:
                if isinstance(workflow.on, dict):
                    events.update(workflow.on.keys())
                elif isinstance(workflow.on, str):
                    events.add(workflow.on)
                elif isinstance(workflow.on, list):
                    events.update(workflow.on)

        return sorted(list(events))
