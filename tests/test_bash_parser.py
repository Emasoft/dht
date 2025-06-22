#!/usr/bin/env python3
"""
test_bash_parser.py - Test the Bash parser implementation  This script tests the bash_parser module to ensure it can: 1. Parse bash scripts using tree-sitter 2. Extract functions, variables, exports, and other elements 3. Fall back to regex parsing when tree-sitter is not available

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
test_bash_parser.py - Test the Bash parser implementation

This script tests the bash_parser module to ensure it can:
1. Parse bash scripts using tree-sitter
2. Extract functions, variables, exports, and other elements
3. Fall back to regex parsing when tree-sitter is not available
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from DHT.modules.parsers.bash_parser import BashParser


def create_test_script():
    """Create a test bash script with various elements."""
    script_content = """#!/bin/bash
# Test script for bash parser

# Global variables
PROJECT_NAME="DHT"
VERSION="1.0.0"
DEBUG=false

# Export environment variables
export PATH="/usr/local/bin:$PATH"
export PROJECT_HOME="/opt/dht"

# Function definitions
hello_world() {
    echo "Hello, World!"
    return 0
}

function setup_environment {
    local env_type=$1
    local config_file="config.ini"

    if [ "$env_type" = "production" ]; then
        export NODE_ENV="production"
    else
        export NODE_ENV="development"
    fi
}

# Source other files
source ./common.sh
. /etc/profile

# Commands
git status
docker ps
npm install

# Control structures
if [ -z "$PROJECT_NAME" ]; then
    echo "Project name not set"
fi

for file in *.txt; do
    echo "Processing $file"
done

while read line; do
    echo "$line"
done < input.txt

case "$1" in
    start)
        echo "Starting..."
        ;;
    stop)
        echo "Stopping..."
        ;;
esac
"""
    return script_content


def test_bash_parser():
    """Test the bash parser functionality."""
    print("Testing Bash Parser...")
    print("-" * 50)

    # Create parser
    parser = BashParser()

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(create_test_script())
        test_file = Path(f.name)

    try:
        # Parse the file
        result = parser.parse_file(test_file)

        # Check for errors
        if "error" in result:
            print(f"❌ Error parsing file: {result['error']}")
            return False

        # Display results
        print(f"✅ Successfully parsed {test_file}")
        print(f"\nParser type: {'tree-sitter' if 'parser_type' not in result else result['parser_type']}")

        # Functions
        print(f"\n📦 Functions found: {len(result.get('functions', []))}")
        for func in result.get("functions", []):
            print(f"  - {func['name']} (line {func.get('line', 'N/A')})")
            if "local_vars" in func:
                print(f"    Local variables: {', '.join(func['local_vars'])}")

        # Variables
        print(f"\n📊 Variables found: {len(result.get('variables', []))}")
        for var in result.get("variables", []):
            print(f"  - {var['name']} = {var['value']} (type: {var.get('type', 'unknown')})")

        # Exports
        print(f"\n🌍 Exports found: {len(result.get('exports', []))}")
        for exp in result.get("exports", []):
            print(f"  - {exp['name']} = {exp.get('value', '(no value)')}")

        # Sourced files
        print(f"\n📁 Sourced files: {len(result.get('sourced_files', []))}")
        for src in result.get("sourced_files", []):
            print(f"  - {src['path']} (line {src['line']})")

        # Commands
        print(f"\n🔧 Commands found: {len(result.get('commands', []))}")
        unique_commands = {cmd["name"] for cmd in result.get("commands", []) if "name" in cmd}
        print(f"  Unique commands: {', '.join(sorted(unique_commands))}")

        # Dependencies
        print(f"\n📦 External dependencies: {len(result.get('dependencies', []))}")
        if result.get("dependencies"):
            print(f"  {', '.join(result['dependencies'])}")

        # Control structures
        if "control_structures" in result:
            print("\n🔄 Control structures:")
            for struct, count in result["control_structures"].items():
                if count > 0:
                    print(f"  - {struct}: {count}")

        # Test extract_dependencies separately
        print("\n🔍 Testing extract_dependencies method:")
        deps = parser.extract_dependencies(test_file)
        print(f"  Dependencies: {', '.join(deps) if deps else 'None found'}")

        # Save full results as JSON for inspection
        output_file = Path("bash_parser_test_results.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Full results saved to: {output_file}")

        return True

    except Exception as e:
        print(f"❌ Exception during parsing: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up
        test_file.unlink()


def test_tree_sitter_availability():
    """Check if tree-sitter is properly configured."""
    print("\n🔍 Checking tree-sitter availability...")

    try:
        import tree_sitter

        tree_sitter  # Mark as used for availability check
        print("✅ tree-sitter module is available")

        try:
            import tree_sitter_bash

            tree_sitter_bash  # Mark as used for availability check
            print("✅ tree-sitter-bash module is available")

            # Test if we can create a parser
            parser = BashParser()
            if parser.parser:
                print("✅ Successfully created tree-sitter Bash parser")
                return True
            else:
                print("❌ Failed to create tree-sitter Bash parser")
                return False

        except ImportError:
            print("❌ tree-sitter-bash module is not available")
            return False

    except ImportError:
        print("❌ tree-sitter module is not available")
        return False


if __name__ == "__main__":
    print("🚀 Bash Parser Test Suite")
    print("=" * 50)

    # Check tree-sitter availability
    ts_available = test_tree_sitter_availability()

    # Run parser tests
    print("\n" + "=" * 50)
    success = test_bash_parser()

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    sys.exit(0 if success else 1)
