#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uv_manager_venv.py - Virtual environment management for UV Manager

This module contains virtual environment creation and management functionality.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_manager.py to reduce file size
# - Contains virtual environment creation and setup
#

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from prefect import task

from DHT.modules.uv_manager_exceptions import UVError


class VirtualEnvironmentManager:
    """Manages virtual environment operations for UV."""
    
    def __init__(self, run_command_func):
        """
        Initialize virtual environment manager.
        
        Args:
            run_command_func: Function to run UV commands
        """
        self.logger = logging.getLogger(__name__)
        self.run_command = run_command_func
    
    @task
    def create_venv(
        self, 
        project_path: Path, 
        python_version: Optional[str] = None,
        venv_path: Optional[Path] = None
    ) -> Path:
        """
        Create virtual environment for project.
        
        Args:
            project_path: Project root directory
            python_version: Specific Python version to use
            venv_path: Custom path for virtual environment
            
        Returns:
            Path to created virtual environment
        """
        project_path = Path(project_path)
        
        if venv_path is None:
            venv_path = project_path / ".venv"
        
        args = ["venv"]
        
        if python_version:
            args.extend(["--python", python_version])
        
        # Add path if not default
        if venv_path != project_path / ".venv":
            args.append(str(venv_path))
        
        result = self.run_command(args, cwd=project_path)
        
        if not result["success"]:
            raise UVError(f"Failed to create virtual environment: {result['stderr']}")
        
        self.logger.info(f"Created virtual environment at {venv_path}")
        return venv_path
    
    def setup_virtual_environment(
        self,
        project_path: Path,
        python_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set up virtual environment for project.
        
        Args:
            project_path: Project root directory
            python_version: Specific Python version
            
        Returns:
            Setup result information
        """
        try:
            venv_path = self.create_venv(project_path, python_version)
            
            return {
                "success": True,
                "venv_path": str(venv_path),
                "python_version": python_version,
                "message": f"Virtual environment created at {venv_path}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to set up virtual environment: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Virtual environment setup failed"
            }