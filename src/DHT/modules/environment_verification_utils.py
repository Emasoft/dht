#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
environment_verification_utils.py - Utilities for environment verification

This module contains utilities for verifying environment compatibility
including platform, Python version, and tool version verification.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains environment verification utilities
#

from __future__ import annotations

import platform
import shutil
import subprocess
import sys

from prefect import get_run_logger

from DHT.modules.environment_snapshot_models import EnvironmentSnapshot, ReproductionResult
from DHT.modules.platform_normalizer import verify_platform_compatibility, get_tool_command
from DHT.modules.tool_version_manager import ToolVersionManager
from DHT.modules.uv_prefect_tasks import check_uv_available, ensure_python_version


class EnvironmentVerificationUtils:
    """Utilities for verifying environment compatibility."""
    
    def __init__(self):
        """Initialize environment verification utilities."""
        self.logger = None
        self.tool_manager = ToolVersionManager()
    
    def _get_logger(self):
        """Get logger with fallback."""
        if self.logger is None:
            try:
                self.logger = get_run_logger()
            except Exception:
                import logging
                self.logger = logging.getLogger(__name__)
        return self.logger
    
    def verify_platform_compatibility(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult
    ):
        """Verify platform compatibility."""
        is_compatible, warnings = verify_platform_compatibility(
            snapshot.platform,
            platform.system().lower()
        )
        
        result.warnings.extend(warnings)
        
        if not is_compatible:
            result.actions_failed.append(
                f"Platform incompatibility: {snapshot.platform} -> {platform.system().lower()}"
            )
    
    def verify_python_version(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult,
        auto_install: bool
    ):
        """Verify Python version compatibility."""
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        expected_version = snapshot.python_version
        
        result.versions_verified["python"] = current_version == expected_version
        
        if not result.versions_verified["python"]:
            result.version_mismatches["python"] = (expected_version, current_version)
            
            # Check if version is compatible (same major.minor)
            expected_parts = expected_version.split(".")
            current_parts = current_version.split(".")
            
            if (len(expected_parts) >= 2 and len(current_parts) >= 2 and
                expected_parts[0] == current_parts[0] and
                expected_parts[1] == current_parts[1]):
                result.warnings.append(
                    f"Python version compatible: {current_version} vs {expected_version}"
                )
            else:
                if auto_install:
                    self._install_python_version(snapshot, result)
                else:
                    result.actions_failed.append(
                        f"Python version mismatch: need {expected_version}, have {current_version}"
                    )
    
    def _install_python_version(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult
    ):
        """Attempt to install the required Python version."""
        logger = self._get_logger()
        
        try:
            # Try using UV to install Python
            uv_check = check_uv_available()
            if uv_check["available"]:
                python_path = ensure_python_version(snapshot.python_version)
                result.actions_completed.append(
                    f"Installed Python {snapshot.python_version} via UV"
                )
                logger.info(f"Installed Python {snapshot.python_version} at {python_path}")
                return
                
        except Exception as e:
            logger.warning(f"Failed to install Python via UV: {e}")
        
        # Provide manual installation instructions
        result.warnings.append(
            f"Manual installation required: Python {snapshot.python_version}"
        )
        result.actions_failed.append(
            f"Could not auto-install Python {snapshot.python_version}"
        )
    
    def verify_tools(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult,
        strict_mode: bool,
        auto_install: bool
    ):
        """Verify tool versions."""
        for tool, expected_version in snapshot.tool_versions.items():
            # Check if tool is installed
            tool_path = shutil.which(tool)
            if not tool_path:
                result.missing_tools.append(tool)
                result.tools_verified[tool] = False
                
                if auto_install:
                    self._install_tool(tool, expected_version, result)
                continue
            
            # Get current version
            try:
                version_cmd = get_tool_command(tool)
                if version_cmd:
                    proc_result = subprocess.run(
                        version_cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if proc_result.returncode == 0:
                        current_version = self.tool_manager.extract_version_from_output(
                            proc_result.stdout + proc_result.stderr
                        )
                        
                        if current_version:
                            # Check version compatibility
                            versions_match = self.tool_manager.compare_versions(
                                expected_version, current_version, tool, strict_mode
                            )
                            
                            result.tools_verified[tool] = True
                            result.versions_verified[tool] = versions_match
                            
                            if not versions_match:
                                result.version_mismatches[tool] = (expected_version, current_version)
                        else:
                            result.tools_verified[tool] = True
                            result.versions_verified[tool] = False
                            result.warnings.append(f"Could not determine {tool} version")
                    else:
                        result.tools_verified[tool] = False
                        result.warnings.append(f"Failed to check {tool} version")
                        
            except Exception as e:
                result.tools_verified[tool] = False
                result.warnings.append(f"Error checking {tool}: {e}")
    
    def _install_tool(self, tool: str, version: str, result: ReproductionResult):
        """Attempt to install a missing tool."""
        logger = self._get_logger()
        
        install_cmd = self.tool_manager.get_installation_command(tool, version)
        
        if install_cmd:
            result.warnings.append(
                f"Manual installation suggested for {tool}: {install_cmd}"
            )
        else:
            result.warnings.append(
                f"No automatic installation available for {tool} on {platform.system().lower()}"
            )
        
        result.missing_tools.append(tool)


# Export public API
__all__ = ["EnvironmentVerificationUtils"]