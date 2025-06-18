#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug test with logging enabled."""

import sys
import tempfile
import logging
from pathlib import Path

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.DHT.modules.command_dispatcher import CommandDispatcher

# Create a temporary directory
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir_path = Path(tmpdir)
    
    # Create a minimal pyproject.toml
    (tmpdir_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")
    
    # Change to test directory
    import os
    os.chdir(tmpdir_path)
    
    print(f"Working directory: {tmpdir_path}")
    
    # Create dispatcher and run command
    dispatcher = CommandDispatcher()
    
    print("\n=== Running dispatch ===")
    result = dispatcher.dispatch("setup", [])
    
    print(f"\nDispatch result type: {type(result)}")
    print(f"Dispatch result: {result}")