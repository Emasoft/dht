#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug Prefect Task wrapping."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.DHT.modules.dhtl_commands import DHTLCommands
from prefect import task

# Create an instance
cmds = DHTLCommands()

print("=== Checking setup attribute ===")
print(f"Type of cmds.setup: {type(cmds.setup)}")
print(f"Is it a Task? {hasattr(cmds.setup, 'fn')}")
print(f"Has __self__? {hasattr(cmds.setup, '__self__')}")

# Check if it's a Prefect task
if hasattr(cmds.setup, 'fn'):
    print(f"\nIt's a Prefect Task!")
    print(f"Wrapped function: {cmds.setup.fn}")
    print(f"Wrapped function type: {type(cmds.setup.fn)}")
    
    # Try calling the task
    print("\n=== Calling the task ===")
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        Path("pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")
        
        # Call the task directly
        result = cmds.setup(path=".")
        print(f"Direct call result type: {type(result)}")
        print(f"Is dict? {isinstance(result, dict)}")
        if isinstance(result, dict):
            print(f"Success? {result.get('success')}")

# Test how the dispatcher would handle it
print("\n=== Testing dispatcher logic ===")
handler = cmds.setup
print(f"Handler type: {type(handler)}")
print(f"Has __self__: {hasattr(handler, '__self__')}")
print(f"Has __func__: {hasattr(handler, '__func__')}")
print(f"Has fn: {hasattr(handler, 'fn')}")

# If it's a Prefect Task, we need to handle it differently
if hasattr(handler, 'fn'):
    print("\nHandler is a Prefect Task")
    # The actual function is in handler.fn
    actual_fn = handler.fn
    print(f"Actual function: {actual_fn}")
    print(f"Actual function __self__: {getattr(actual_fn, '__self__', 'Not found')}")