#!/usr/bin/env python3
from __future__ import annotations

"""
reproduction_flow_utils.py - Utilities for reproduction flow orchestration  This module contains utilities for orchestrating the complete environment reproduction flow including snapshot creation, saving, and verification.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
reproduction_flow_utils.py - Utilities for reproduction flow orchestration

This module contains utilities for orchestrating the complete environment
reproduction flow including snapshot creation, saving, and verification.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains reproduction flow orchestration logic
#


import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from prefect import get_run_logger


class ReproductionFlowUtils:
    """Utilities for orchestrating reproduction flows."""

    def __init__(self, reproducer: Any) -> None:
        """Initialize flow utilities with reference to main reproducer."""
        self.reproducer = reproducer
        self.logger = None

    def _get_logger(self) -> Any:
        """Get logger with fallback."""
        if self.logger is None:
            try:
                self.logger = get_run_logger()
            except Exception:
                import logging

                self.logger = logging.getLogger(__name__)  # type: ignore[assignment]
        return self.logger

    def create_reproducible_environment(
        self,
        project_path: Path,
        output_dir: Path | None = None,
        include_system_info: bool = True,
        save_snapshot: bool = True,
        verify_reproduction: bool = True,
    ) -> dict[str, Any]:
        """
        Complete flow for creating reproducible environments.

        Args:
            project_path: Path to project to make reproducible
            output_dir: Directory to save snapshots and verification results
            include_system_info: Whether to include system information
            save_snapshot: Whether to save snapshot to file
            verify_reproduction: Whether to verify reproduction works

        Returns:
            Dictionary with flow results
        """
        start_time = time.time()

        logger = self._get_logger()
        project_path = Path(project_path)

        if output_dir is None:
            output_dir = project_path / ".dht" / "snapshots"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results: dict[str, Any] = {
            "project_path": str(project_path),
            "timestamp": datetime.now().isoformat(),
            "steps": [],
        }

        try:
            # Step 1: Capture environment snapshot
            logger.info("Capturing environment snapshot...")
            snapshot = self.reproducer._capture_environment_snapshot_impl(
                project_path=project_path, include_system_info=include_system_info
            )
            results["snapshot_id"] = snapshot.snapshot_id
            results["steps"].append("capture_snapshot")

            # Step 2: Save snapshot if requested
            if save_snapshot:
                snapshot_file = output_dir / f"{snapshot.snapshot_id}.json"
                saved_path = self.reproducer._save_environment_snapshot_impl(
                    snapshot=snapshot, output_path=snapshot_file
                )
                results["snapshot_file"] = str(saved_path)
                results["steps"].append("save_snapshot")
                logger.info(f"Snapshot saved to {saved_path}")

            # Step 3: Verify reproduction if requested
            if verify_reproduction:
                logger.info("Verifying environment reproduction...")

                # Create temporary directory for verification
                with tempfile.TemporaryDirectory() as temp_dir:
                    verification_result = self.reproducer._reproduce_environment_impl(
                        snapshot=snapshot,
                        target_path=Path(temp_dir) / "verification",
                        strict_mode=False,  # Use lenient mode for verification
                        auto_install=False,  # Don't auto-install during verification
                    )

                    results["verification"] = {
                        "success": verification_result.success,
                        "tools_verified": verification_result.tools_verified,
                        "version_mismatches": verification_result.version_mismatches,
                        "missing_tools": verification_result.missing_tools,
                        "warnings": verification_result.warnings,
                    }
                    results["steps"].append("verify_reproduction")

            # Step 4: Generate reproduction guide
            self.reproducer.artifact_creator.create_reproduction_artifacts(snapshot, results, output_dir)
            results["steps"].append("create_artifacts")

            results["success"] = True

        except Exception as e:
            logger.error(f"Reproducible environment creation failed: {e}")
            results["success"] = False
            results["error"] = str(e)

        results["execution_time"] = time.time() - start_time

        logger.info(f"Reproducible environment creation {'completed' if results['success'] else 'failed'}")
        return results


# Export public API
__all__ = ["ReproductionFlowUtils"]
