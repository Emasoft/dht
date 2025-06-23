#!/usr/bin/env python3
"""
test_bash_parser.py - Unit tests for the Bash parser  This module tests the bash_parser module following TDD principles. Tests are written first to define the expected behavior, then the implementation will be created to make these tests pass.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
test_bash_parser.py - Unit tests for the Bash parser

This module tests the bash_parser module following TDD principles.
Tests are written first to define the expected behavior, then the
implementation will be created to make these tests pass.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest

from DHT.modules.parsers.bash_parser import BashParser


class TestBashParser:
    """Test suite for BashParser class."""

    @pytest.fixture
    def parser(self) -> Any:
        """Create a BashParser instance for testing."""
        return BashParser()

    @pytest.fixture
    def sample_bash_script(self) -> Any:
        """Create a sample bash script for testing."""
        return """#!/bin/bash
# Sample bash script for testing

# Global variables
PROJECT_NAME="DHT"
VERSION="1.0.0"
DEBUG=false
ARRAY=(one two three)

# Export environment variables
export PATH="/usr/local/bin:$PATH"
export PROJECT_HOME="/opt/dht"
export NODE_ENV

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
npm install --save-dev jest

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

    def test_parser_initialization(self, parser) -> Any:
        """Test that the parser initializes correctly."""
        assert parser is not None
        assert hasattr(parser, "parse_file")
        assert hasattr(parser, "extract_dependencies")

    def test_parse_file_with_invalid_path(self, parser) -> Any:
        """Test parsing with an invalid file path."""
        result = parser.parse_file(Path("/non/existent/file.sh"))
        assert "error" in result
        assert "Failed to read file" in result["error"]

    def test_parse_file_returns_expected_structure(self, parser, sample_bash_script) -> Any:
        """Test that parse_file returns the expected data structure."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            # Check basic structure
            assert isinstance(result, dict)
            assert "file_metadata" in result
            assert "functions" in result
            assert "variables" in result
            assert "exports" in result
            assert "sourced_files" in result
            assert "commands" in result
            assert "shebang" in result
            assert "comments" in result
            assert "dependencies" in result

            # Verify file metadata
            metadata = result["file_metadata"]
            assert metadata["name"] == temp_path.name
            assert metadata["extension"] == ".sh"
            assert metadata["size"] > 0

        finally:
            temp_path.unlink()

    def test_extract_shebang(self, parser, sample_bash_script) -> Any:
        """Test shebang extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            assert result["shebang"] == "#!/bin/bash"
        finally:
            temp_path.unlink()

    def test_extract_functions(self, parser, sample_bash_script) -> Any:
        """Test function extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            functions = result["functions"]

            # Should find 2 functions
            assert len(functions) == 2

            # Check hello_world function
            hello_func = next(f for f in functions if f["name"] == "hello_world")
            assert hello_func is not None
            assert 'echo "Hello, World!"' in hello_func["body"]
            assert hello_func.get("local_vars", []) == []

            # Check setup_environment function
            setup_func = next(f for f in functions if f["name"] == "setup_environment")
            assert setup_func is not None
            assert "env_type" in setup_func.get("local_vars", [])
            assert "config_file" in setup_func.get("local_vars", [])

        finally:
            temp_path.unlink()

    def test_extract_variables(self, parser, sample_bash_script) -> Any:
        """Test variable extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            variables = result["variables"]

            # Check for expected variables
            var_names = {v["name"] for v in variables}
            assert "PROJECT_NAME" in var_names
            assert "VERSION" in var_names
            assert "DEBUG" in var_names
            assert "ARRAY" in var_names

            # Check variable values and types
            project_var = next(v for v in variables if v["name"] == "PROJECT_NAME")
            assert project_var["value"] == "DHT"
            assert project_var["type"] == "string"

            debug_var = next(v for v in variables if v["name"] == "DEBUG")
            assert debug_var["value"] == "false"
            assert debug_var["type"] == "boolean"

            array_var = next(v for v in variables if v["name"] == "ARRAY")
            assert array_var["type"] == "array"

        finally:
            temp_path.unlink()

    def test_extract_exports(self, parser, sample_bash_script) -> Any:
        """Test export statement extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            exports = result["exports"]

            # Should find 3 exports
            assert len(exports) >= 3

            # Check PATH export
            path_export = next((e for e in exports if e["name"] == "PATH"), None)
            assert path_export is not None
            assert "/usr/local/bin:$PATH" in path_export["value"]

            # Check PROJECT_HOME export
            home_export = next((e for e in exports if e["name"] == "PROJECT_HOME"), None)
            assert home_export is not None
            assert home_export["value"] == "/opt/dht"

            # Check NODE_ENV export (without value)
            node_export = next((e for e in exports if e["name"] == "NODE_ENV"), None)
            assert node_export is not None
            assert node_export["value"] is None

        finally:
            temp_path.unlink()

    def test_extract_sourced_files(self, parser, sample_bash_script) -> Any:
        """Test sourced file extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            sources = result["sourced_files"]

            # Should find 2 sourced files
            assert len(sources) == 2

            # Check sourced paths
            paths = {s["path"] for s in sources}
            assert "./common.sh" in paths
            assert "/etc/profile" in paths

        finally:
            temp_path.unlink()

    def test_extract_commands(self, parser, sample_bash_script) -> Any:
        """Test command extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            commands = result["commands"]

            # Should find at least git, docker, npm
            cmd_names = {c["name"] for c in commands if "name" in c}
            assert "git" in cmd_names
            assert "docker" in cmd_names
            assert "npm" in cmd_names

            # Check command with arguments
            npm_cmd = next((c for c in commands if c.get("name") == "npm"), None)
            if npm_cmd and "args" in npm_cmd:
                assert "install" in npm_cmd["args"]

        finally:
            temp_path.unlink()

    def test_extract_dependencies(self, parser, sample_bash_script) -> Any:
        """Test dependency extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            # Test via parse_file
            result = parser.parse_file(temp_path)
            deps = result["dependencies"]
            assert "git" in deps["commands"]
            assert "docker" in deps["commands"]
            assert "npm" in deps["commands"]

            # Test direct method
            direct_deps = parser.extract_dependencies(temp_path)
            assert direct_deps == deps

        finally:
            temp_path.unlink()

    def test_extract_control_structures(self, parser, sample_bash_script) -> Any:
        """Test control structure extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(sample_bash_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            # If control_structures is present, check counts
            if "control_structures" in result:
                structures = result["control_structures"]
                assert structures["if_statements"] >= 2  # if in script + if in function
                assert structures["for_loops"] >= 1
                assert structures["while_loops"] >= 1
                assert structures["case_statements"] >= 1
                assert structures["functions"] == 2

        finally:
            temp_path.unlink()

    def test_parse_empty_file(self, parser) -> Any:
        """Test parsing an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            assert "error" not in result
            assert result["functions"] == []
            assert result["variables"] == []
            assert result["exports"] == []
            assert result["shebang"] is None

        finally:
            temp_path.unlink()

    def test_parse_file_with_syntax_errors(self, parser) -> Any:
        """Test parsing a file with bash syntax errors."""
        broken_script = """#!/bin/bash
# Broken script

function missing_closing_brace {
    echo "This function is broken"
# Missing closing brace

VAR=value without quotes containing spaces

if [ condition ]
    echo "Missing then"
fi
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(broken_script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            # Parser should still extract what it can
            assert "error" not in result
            assert result["shebang"] == "#!/bin/bash"
            # Should still find the variable
            var_names = {v["name"] for v in result["variables"]}
            assert "VAR" in var_names

        finally:
            temp_path.unlink()

    def test_variable_type_inference(self, parser) -> Any:
        """Test variable type inference."""
        script = """#!/bin/bash
STRING_VAR="hello"
NUMBER_VAR=42
NEGATIVE_NUM=-5
BOOL_TRUE=true
BOOL_FALSE=false
BOOL_ZERO=0
BOOL_ONE=1
PATH_VAR=/usr/local/bin
HOME_PATH=~/documents
ARRAY_VAR=(a b c)
CMD_SUB=$(date)
BACKTICK_SUB=`hostname`
VAR_REF=$OTHER_VAR
EMPTY_VAR=
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            variables = {v["name"]: v for v in result["variables"]}

            assert variables["STRING_VAR"]["type"] == "string"
            assert variables["NUMBER_VAR"]["type"] == "number"
            assert variables["NEGATIVE_NUM"]["type"] == "number"
            assert variables["BOOL_TRUE"]["type"] == "boolean"
            assert variables["BOOL_FALSE"]["type"] == "boolean"
            assert variables["BOOL_ZERO"]["type"] == "boolean"
            assert variables["BOOL_ONE"]["type"] == "boolean"
            assert variables["PATH_VAR"]["type"] == "path"
            assert variables["HOME_PATH"]["type"] == "path"
            assert variables["ARRAY_VAR"]["type"] == "array"
            assert variables["CMD_SUB"]["type"] == "command_substitution"
            assert variables["BACKTICK_SUB"]["type"] == "command_substitution"
            assert variables["VAR_REF"]["type"] == "variable_reference"
            assert variables["EMPTY_VAR"]["type"] == "string"

        finally:
            temp_path.unlink()

    def test_comments_extraction(self, parser) -> Any:
        """Test comment extraction."""
        script = """#!/bin/bash
# This is a header comment
# It spans multiple lines

# Function to do something
do_something() {
    # Implementation comment
    echo "doing"
}

# TODO: Add more features
# FIXME: Fix this bug
# NOTE: Important information
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            comments = result["comments"]

            # Should find multiple comments
            assert len(comments) > 0

            # Check shebang is identified
            shebang_comments = [c for c in comments if c.get("is_shebang", False)]
            assert len(shebang_comments) >= 1

            # Check comment text extraction
            comment_texts = [c["text"] for c in comments]
            assert any("header comment" in text for text in comment_texts)
            assert any("TODO" in text for text in comment_texts)
            assert any("FIXME" in text for text in comment_texts)

        finally:
            temp_path.unlink()

    def test_complex_function_parsing(self, parser) -> Any:
        """Test parsing of complex function definitions."""
        script = """#!/bin/bash

# Function with multiple parameters and complex logic
process_files() {
    local input_dir="$1"
    local output_dir="$2"
    local -a files=()
    local count=0

    # Find all files
    while IFS= read -r -d '' file; do
        files+=("$file")
        ((count++))
    done < <(find "$input_dir" -type f -name "*.txt" -print0)

    # Process each file
    for file in "${files[@]}"; do
        local basename=$(basename "$file")
        cp "$file" "$output_dir/$basename"
    done

    return $count
}

# Function using function keyword
function validate_args {
    [[ $# -eq 0 ]] && return 1
    return 0
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(script)
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)
            functions = result["functions"]

            assert len(functions) == 2

            # Check process_files function
            process_func = next(f for f in functions if f["name"] == "process_files")
            local_vars = process_func.get("local_vars", [])
            assert "input_dir" in local_vars
            assert "output_dir" in local_vars
            assert "files" in local_vars
            assert "count" in local_vars

        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
