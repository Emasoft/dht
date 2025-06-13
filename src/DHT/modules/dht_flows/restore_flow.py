#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of restore_dependencies as a Prefect flow
# - Converted from dhtl_commands_1.sh shell script
# - Added proper error handling and resource management
#

"""
Restore Dependencies Flow - Prefect implementation of dependency restoration.

This module replaces the shell script restore_dependencies() function
with a modern Prefect flow that provides better error handling,
parallel execution, and resource management.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from prefect import flow, task, get_run_logger

from ..uv_manager import UVManager
from ..guardian_prefect import GuardianConfig, run_with_guardian
from .utils import (
    get_venv_python_path, 
    get_venv_pip_path, 
    get_default_resource_limits,
    validate_project_path
)


@task(name="find-project-root", retries=2)
def find_project_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the project root directory.
    
    Looks for common project markers like pyproject.toml, setup.py,
    requirements.txt, or .git directory.
    
    Args:
        start_path: Starting directory (defaults to current directory)
        
    Returns:
        Path to project root directory
        
    Raises:
        ValueError: If no project root can be found
    """
    logger = get_run_logger()
    current = Path(start_path or os.getcwd()).resolve()
    
    markers = ["pyproject.toml", "setup.py", "requirements.txt", ".git"]
    
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                logger.info(f"Found project root at {current} (marker: {marker})")
                return current
        current = current.parent
    
    raise ValueError(f"Could not find project root from {start_path or os.getcwd()}")


@task(name="detect-virtual-environment", retries=2)
def detect_virtual_environment(project_root: Path) -> Tuple[bool, Optional[Path]]:
    """
    Detect existing virtual environment or determine where to create one.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Tuple of (exists, path) where exists indicates if venv already exists
    """
    logger = get_run_logger()
    
    # Check for activated virtual environment
    if sys.prefix != sys.base_prefix:
        venv_path = Path(sys.prefix)
        logger.info(f"Using activated virtual environment: {venv_path}")
        return True, venv_path
    
    # Check common venv locations
    venv_names = [".venv", "venv", ".virtualenv", "virtualenv"]
    for name in venv_names:
        venv_path = project_root / name
        if venv_path.exists() and (venv_path / "bin" / "python").exists():
            logger.info(f"Found existing virtual environment: {venv_path}")
            return True, venv_path
    
    # No venv found, return path for new one
    venv_path = project_root / ".venv"
    logger.info(f"No virtual environment found, will create at: {venv_path}")
    return False, venv_path


@task(name="create-virtual-environment")
def create_virtual_environment(venv_path: Path, python_version: Optional[str] = None) -> Path:
    """
    Create a new virtual environment using UV.
    
    Args:
        venv_path: Path where virtual environment should be created
        python_version: Optional Python version to use
        
    Returns:
        Path to created virtual environment
    """
    logger = get_run_logger()
    
    try:
        uv_manager = UVManager()
    except Exception as e:
        logger.error(f"Failed to initialize UV manager: {e}")
        raise RuntimeError(
            "UV is required but not available. Please install UV first:\n"
            "curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
    
    # Ensure UV is available
    if not uv_manager.is_available:
        raise RuntimeError(
            "UV is not available. Please install UV first:\n"
            "curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
    
    # Create virtual environment
    logger.info(f"Creating virtual environment at {venv_path}")
    result = uv_manager.create_venv(
        path=venv_path,
        python_version=python_version
    )
    
    if not result["success"]:
        raise RuntimeError(f"Failed to create virtual environment: {result.get('error')}")
    
    return venv_path


@task(name="install-project-dependencies")
def install_dependencies(
    project_root: Path,
    venv_path: Path,
    extras: Optional[str] = None,
    upgrade: bool = False
) -> Dict[str, Any]:
    """
    Install project dependencies using UV.
    
    Args:
        project_root: Project root directory
        venv_path: Virtual environment path
        extras: Optional extras to install (e.g., "dev,test")
        upgrade: Whether to upgrade dependencies
        
    Returns:
        Installation result dictionary
    """
    logger = get_run_logger()
    
    try:
        uv_manager = UVManager()
    except Exception as e:
        logger.error(f"Failed to initialize UV manager: {e}")
        raise RuntimeError(
            "UV is required but not available. Please install UV first:\n"
            "curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
    
    # Check for lock file
    lock_file = project_root / "uv.lock"
    if lock_file.exists():
        logger.info("Found uv.lock, using UV sync")
        cmd_parts = ["sync"]
        if extras:
            cmd_parts.extend(["--extra", extras])
    else:
        # Check for requirements files
        if (project_root / "pyproject.toml").exists():
            logger.info("Found pyproject.toml, using UV pip install")
            cmd_parts = ["pip", "install", "-e", "."]
            if extras:
                cmd_parts[-1] = f".[{extras}]"
        elif (project_root / "requirements.txt").exists():
            logger.info("Found requirements.txt, using UV pip install")
            cmd_parts = ["pip", "install", "-r", "requirements.txt"]
        else:
            logger.warning("No dependency files found")
            return {"success": True, "message": "No dependencies to install"}
    
    if upgrade:
        cmd_parts.append("--upgrade")
    
    # Run installation with guardian limits
    default_limits = get_default_resource_limits()
    guardian_config = GuardianConfig(
        memory_limit_mb=default_limits["memory_limit_mb"],
        timeout_seconds=600,  # 10 minutes for installation
        check_interval=1.0
    )
    
    result = run_with_guardian(
        ["uv"] + cmd_parts,
        config=guardian_config,
        cwd=str(project_root),
        env={**os.environ, "VIRTUAL_ENV": str(venv_path)}
    )
    
    if result.return_code != 0:
        raise RuntimeError(f"Dependency installation failed: {result.stderr}")
    
    return {
        "success": True,
        "message": "Dependencies installed successfully",
        "stdout": result.stdout,
        "install_time": result.execution_time
    }


@task(name="install-dht-dependencies")
def install_dht_dependencies(venv_path: Path) -> Dict[str, Any]:
    """
    Install DHT-specific dependencies.
    
    Args:
        venv_path: Virtual environment path
        
    Returns:
        Installation result dictionary
    """
    logger = get_run_logger()
    
    # DHT core dependencies
    dht_deps = [
        "pyyaml>=6.0",
        "requests>=2.25.0",
        "click>=8.0.0",
        "rich>=10.0.0",
        "prefect>=2.0.0",
        "psutil>=5.8.0"
    ]
    
    try:
        pip_path = get_venv_pip_path(venv_path)
    except FileNotFoundError:
        logger.warning("pip not found in virtual environment")
        return {"success": False, "message": "pip not found"}
    
    cmd = [str(pip_path), "install"] + dht_deps
    
    guardian_config = GuardianConfig(
        memory_limit_mb=1024,
        timeout_seconds=300,
        check_interval=1.0
    )
    
    result = run_with_guardian(cmd, config=guardian_config)
    
    if result.return_code != 0:
        logger.warning(f"Some DHT dependencies failed to install: {result.stderr}")
    
    return {
        "success": result.return_code == 0,
        "message": "DHT dependencies installed",
        "install_time": result.execution_time
    }


@task(name="verify-installation")
def verify_installation(project_root: Path, venv_path: Path) -> Dict[str, Any]:
    """
    Verify that the installation was successful.
    
    Args:
        project_root: Project root directory
        venv_path: Virtual environment path
        
    Returns:
        Verification result dictionary
    """
    logger = get_run_logger()
    
    try:
        python_path = get_venv_python_path(venv_path)
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Python executable not found in virtual environment"
        }
    
    # Check Python version
    version_result = subprocess.run(
        [str(python_path), "--version"],
        capture_output=True,
        text=True
    )
    
    # Try to import key packages
    test_imports = []
    if (project_root / "pyproject.toml").exists():
        # Try to import the project itself
        project_name = project_root.name.replace("-", "_")
        test_imports.append(project_name)
    
    test_imports.extend(["prefect", "yaml", "requests"])
    
    import_results = {}
    for package in test_imports:
        result = subprocess.run(
            [str(python_path), "-c", f"import {package}"],
            capture_output=True
        )
        import_results[package] = result.returncode == 0
    
    all_imports_ok = all(import_results.values())
    
    return {
        "success": all_imports_ok,
        "python_version": version_result.stdout.strip(),
        "import_results": import_results,
        "venv_path": str(venv_path)
    }


@flow(
    name="restore-dependencies",
    description="Restore project dependencies using UV package manager",
    retries=1
)
def restore_dependencies_flow(
    project_path: Optional[str] = None,
    python_version: Optional[str] = None,
    extras: Optional[str] = None,
    upgrade: bool = False,
    install_dht_deps: bool = True
) -> Dict[str, Any]:
    """
    Main flow for restoring project dependencies.
    
    This flow:
    1. Finds the project root
    2. Detects or creates a virtual environment
    3. Installs project dependencies
    4. Optionally installs DHT dependencies
    5. Verifies the installation
    
    Args:
        project_path: Optional project path (defaults to current directory)
        python_version: Optional Python version for venv creation
        extras: Optional extras to install (e.g., "dev,test")
        upgrade: Whether to upgrade dependencies
        install_dht_deps: Whether to install DHT-specific dependencies
        
    Returns:
        Dictionary with installation results
    """
    logger = get_run_logger()
    logger.info("Starting dependency restoration flow")
    
    # Find project root
    start_path = Path(project_path) if project_path else None
    project_root = find_project_root(start_path)
    
    # Detect or create virtual environment
    venv_exists, venv_path = detect_virtual_environment(project_root)
    
    if not venv_exists and venv_path:
        venv_path = create_virtual_environment(venv_path, python_version)
    
    # Install project dependencies
    install_result = install_dependencies(
        project_root=project_root,
        venv_path=venv_path,
        extras=extras,
        upgrade=upgrade
    )
    
    # Install DHT dependencies if requested
    if install_dht_deps:
        dht_result = install_dht_dependencies(venv_path)
        install_result["dht_dependencies"] = dht_result
    
    # Verify installation
    verification = verify_installation(project_root, venv_path)
    
    # Compile results
    final_result = {
        "success": install_result["success"] and verification["success"],
        "project_root": str(project_root),
        "venv_path": str(venv_path),
        "install_result": install_result,
        "verification": verification
    }
    
    if final_result["success"]:
        logger.info("✅ Dependencies restored successfully")
        logger.info(f"   Project: {project_root}")
        logger.info(f"   Virtual environment: {venv_path}")
        logger.info(f"   Python version: {verification['python_version']}")
    else:
        logger.error("❌ Dependency restoration failed")
        logger.error(f"   Install success: {install_result['success']}")
        logger.error(f"   Verification success: {verification['success']}")
    
    return final_result


# Aliases for backward compatibility
restore_dependencies = restore_dependencies_flow
analyze_project = find_project_root
detect_project_type = find_project_root  # Simplified alias
check_lock_files = lambda root: (root / "uv.lock").exists()
check_uv_lock = check_lock_files
restore_from_lock_files = install_dependencies
restore_python_dependencies = install_dependencies


# CLI interface for backwards compatibility
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore project dependencies")
    parser.add_argument("--project-path", help="Project path")
    parser.add_argument("--python-version", help="Python version for venv")
    parser.add_argument("--extras", help="Extras to install")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade dependencies")
    parser.add_argument("--no-dht-deps", action="store_true", help="Skip DHT dependencies")
    
    args = parser.parse_args()
    
    result = restore_dependencies_flow(
        project_path=args.project_path,
        python_version=args.python_version,
        extras=args.extras,
        upgrade=args.upgrade,
        install_dht_deps=not args.no_dht_deps
    )
    
    sys.exit(0 if result["success"] else 1)