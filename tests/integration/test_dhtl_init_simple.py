#!/usr/bin/env python3
"""
Simple test for dhtl init to debug issues.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Simple test for dhtl init to debug issues.
"""

import tempfile
from pathlib import Path
from typing import Any

from DHT.modules.dhtl_commands import DHTLCommands


def test_simple_init() -> Any:
    """Very simple test to see what's happening."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-project"

        commands = DHTLCommands()
        result = commands.init(path=str(project_path), name="test-project", python="3.11")

        print(f"Result: {result}")

        # Check what files were created
        if project_path.exists():
            print(f"Project path exists: {project_path}")
            for file in project_path.rglob("*"):
                if file.is_file():
                    print(f"  File: {file.relative_to(project_path)}")

        assert result["success"] is True
        assert project_path.exists()
        assert (project_path / "pyproject.toml").exists()


if __name__ == "__main__":
    test_simple_init()
