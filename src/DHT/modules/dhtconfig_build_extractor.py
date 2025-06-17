#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dhtconfig_build_extractor.py - Build configuration extraction for DHT configuration

This module handles extraction of build configuration from project analysis.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains build configuration extraction logic
#

from __future__ import annotations

from typing import Any, Dict


class BuildConfigExtractor:
    """Extracts build configuration from project analysis."""
    
    def extract_build_config(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract build configuration from project analysis."""
        build = {
            "pre_install": [],
            "post_install": [],
            "build_commands": [],
            "test_commands": []
        }
        
        configs = project_info.get("configurations", {})
        
        # Python project build commands
        if project_info.get("project_type") == "python":
            if configs.get("has_setup_py"):
                build["build_commands"].append("python setup.py build")
            elif configs.get("has_pyproject"):
                build["build_commands"].append("python -m build")
            
            # Test commands
            if configs.get("has_pytest"):
                build["test_commands"].append("pytest")
            elif configs.get("has_unittest"):
                build["test_commands"].append("python -m unittest discover")
        
        # Makefile commands
        if configs.get("has_makefile"):
            build["build_commands"].append("make")
            build["test_commands"].append("make test")
        
        return build


# Export public API
__all__ = ["BuildConfigExtractor"]