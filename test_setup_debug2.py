#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug test for setup command - direct import."""

import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_setup_direct():
    """Test the setup command by direct import."""
    
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
        
        print(f"Working directory: {tmpdir_path}")
        
        try:
            # Import and run the command dispatcher directly
            from src.DHT.modules.command_dispatcher import CommandDispatcher
            
            dispatcher = CommandDispatcher()
            exit_code = dispatcher.dispatch("setup", [])
            
            print(f"\nDispatcher returned exit code: {exit_code}")
            
            return exit_code
            
        except Exception as e:
            print(f"Exception occurred: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    import os
    # Change to test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create minimal pyproject.toml
        Path("pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")
        
        exit_code = test_setup_direct()
        print(f"\nFinal exit code: {exit_code}")
        sys.exit(exit_code)