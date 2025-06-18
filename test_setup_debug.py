#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug test for setup command."""

import subprocess
import sys
import tempfile
from pathlib import Path

def test_setup_command():
    """Test the setup command directly."""
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a minimal pyproject.toml
        pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"
"""
        (tmpdir_path / "pyproject.toml").write_text(pyproject_content)
        
        # Run the setup command
        cmd = [sys.executable, "-m", "src.DHT.dhtl", "setup"]
        
        print(f"Running command: {' '.join(cmd)}")
        print(f"Working directory: {tmpdir_path}")
        
        # Add project root to PYTHONPATH
        import os
        env = os.environ.copy()
        project_root = Path(__file__).parent
        env["PYTHONPATH"] = str(project_root)
        
        result = subprocess.run(
            cmd,
            cwd=tmpdir_path,
            capture_output=True,
            text=True,
            env=env
        )
        
        print(f"\nReturn code: {result.returncode}")
        print(f"\nSTDOUT:\n{result.stdout}")
        print(f"\nSTDERR:\n{result.stderr}")
        
        return result.returncode

if __name__ == "__main__":
    exit_code = test_setup_command()
    sys.exit(exit_code)