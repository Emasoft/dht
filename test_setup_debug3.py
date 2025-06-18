#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug test for command dispatcher."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.DHT.modules.command_dispatcher import CommandDispatcher
from src.DHT.modules.dhtl_commands import DHTLCommands

# Check what's in the registry
dispatcher = CommandDispatcher()

print("=== Checking command registry ===")
cmd = dispatcher.commands.get("setup")
if cmd:
    print(f"Setup command found: {cmd}")
    print(f"Handler type: {type(cmd['handler'])}")
    print(f"Has __self__: {hasattr(cmd['handler'], '__self__')}")
    if hasattr(cmd['handler'], '__self__'):
        print(f"__self__ type: {type(cmd['handler'].__self__)}")
        print(f"Is DHTLCommands instance: {isinstance(cmd['handler'].__self__, DHTLCommands)}")
else:
    print("Setup command not found!")

# Check the dispatch logic
print("\n=== Testing dispatch logic ===")

# Create a test handler that returns a dict
class TestCommands:
    def test_method(self, **kwargs):
        return {"success": True, "message": "Test"}

test_instance = TestCommands()
test_handler = test_instance.test_method

print(f"Test handler has __self__: {hasattr(test_handler, '__self__')}")
print(f"Test handler __self__ type: {type(test_handler.__self__)}")
print(f"Is TestCommands instance: {isinstance(test_handler.__self__, TestCommands)}")
print(f"Is DHTLCommands instance: {isinstance(test_handler.__self__, DHTLCommands)}")

# Test the actual dispatch
print("\n=== Running actual dispatch ===")
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    os.chdir(tmpdir)
    Path("pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")
    
    result = dispatcher.dispatch("setup", [])
    print(f"Dispatch result type: {type(result)}")
    print(f"Dispatch result: {result}")