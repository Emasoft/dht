#!/bin/bash
# Environment_2 module

# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of a modular system and cannot be executed directly." >&2
    echo "Please use the orchestrator script instead." >&2
    exit 1
fi

setup_project_command() {
    log_info "📝 Creating project configuration files..." # Changed from echo
    PROJECT_ROOT=$(find_project_root)
    
    # Create pyproject.toml if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
        log_info "Creating pyproject.toml..." # Changed from echo
        
        # Get the package name from the directory name
        local PACKAGE_NAME # Made local
        PACKAGE_NAME=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
        
        # Create pyproject.toml with basic structure
        cat > "$PROJECT_ROOT/pyproject.toml" << EOF
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "$PACKAGE_NAME"
version = "0.1.0"  # Managed by bump-my-version
description = "Description of your project"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
readme = { file = "README.md", content-type = "text/markdown" } # Corrected readme
requires-python = ">=3.9"
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
dependencies = [
    "requests>=2.28.2",
    # Add your dependencies here
]

[project.optional-dependencies]
dev = [
    "pytest>=7.3.1",
    "pytest-cov>=4.1.0",
    "pytest-xdist>=3.3.1",
    "pytest-timeout>=2.1.0",
    "pytest-html>=3.2.0",
    "black>=23.3.0",
    "ruff>=0.0.262",
    "isort>=5.12.0",
    "pre-commit>=3.3.1",
    "bump-my-version>=0.0.3",
]

[project.urls]
"Homepage" = "https://github.com/yourusername/$PACKAGE_NAME"
"Bug Tracker" = "https://github.com/yourusername/$PACKAGE_NAME/issues"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find] # Added find table for packages
where = ["src"]

[tool.setuptools.dynamic] # Added dynamic table for version
version = {attr = "${PACKAGE_NAME}.__version__"}


[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311", "py312"]
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "I"]
ignore = []
EOF
        
        log_success "Created pyproject.toml" # Changed from echo
    else
        log_warning "pyproject.toml already exists. Skipping." # Changed from echo
    fi
    
    # Create .bumpversion.toml if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.bumpversion.toml" ]; then
        log_info "Creating .bumpversion.toml..." # Changed from echo
        
        # Create .bumpversion.toml with basic structure
        cat > "$PROJECT_ROOT/.bumpversion.toml" << EOF
[tool.bumpversion]
current_version = "0.1.0"
parse = "(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)"
serialize = ["{major}.{minor}.{patch}"]
search = "__version__ = \"{current_version}\""
replace = "__version__ = \"{new_version}\""
regex = false
ignore_missing_version = false
tag = true
sign_tags = false
tag_name = "v{new_version}"
tag_message = "Bump version: {current_version} → {new_version}"
allow_dirty = true
commit = true
message = "Bump version: {current_version} → {new_version}"
commit_args = ""
EOF
        
        log_success "Created .bumpversion.toml" # Changed from echo
    else
        log_warning ".bumpversion.toml already exists. Skipping." # Changed from echo
    fi
    
    # Create .pre-commit-config.yaml if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]; then
        log_info "Creating .pre-commit-config.yaml..." # Changed from echo
        
        # Create .pre-commit-config.yaml with basic structure
        cat > "$PROJECT_ROOT/.pre-commit-config.yaml" << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        name: isort (python)

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.262
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: local
    hooks:
      - id: bump-version
        name: Bump version
        entry: uv tool run bump-my-version bump patch --commit --tag
        language: system
        pass_filenames: false
        always_run: true

      - id: shellcheck
        name: ShellCheck
        entry: shellcheck
        language: system
        types: [shell]
        args: ["--severity=error", "--extended-analysis=true"]
EOF
        
        log_success "Created .pre-commit-config.yaml" # Changed from echo
    else
        log_warning ".pre-commit-config.yaml already exists. Skipping." # Changed from echo
    fi
    
    # Create README.md if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/README.md" ]; then
        log_info "Creating README.md..." # Changed from echo
        
        # Get the package name from the directory name
        local PACKAGE_NAME_README # Made local
        PACKAGE_NAME_README=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
        local DISPLAY_NAME_README # Made local
        DISPLAY_NAME_README=$(basename "$PROJECT_ROOT" | tr '_' ' ' | sed -e 's/\b\(.\)/\u\1/g')
        
        # Create README.md with basic structure
        cat > "$PROJECT_ROOT/README.md" << EOF
# $DISPLAY_NAME_README

[![PyPI Version](https://img.shields.io/pypi/v/$PACKAGE_NAME_README)](https://pypi.org/project/$PACKAGE_NAME_README)
[![Python Versions](https://img.shields.io/pypi/pyversions/$PACKAGE_NAME_README)](https://pypi.org/project/$PACKAGE_NAME_README)
[![License](https://img.shields.io/pypi/l/$PACKAGE_NAME_README)](https://github.com/yourusername/$PACKAGE_NAME_README/blob/main/LICENSE)

A brief description of your project.

## Installation

\`\`\`bash
pip install $PACKAGE_NAME_README
\`\`\`

## Usage

\`\`\`python
import $PACKAGE_NAME_README

# Example code here
\`\`\`

## Features

- Feature 1
- Feature 2
- Feature 3

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
EOF
        
        log_success "Created README.md" # Changed from echo
    else
        log_warning "README.md already exists. Skipping." # Changed from echo
    fi
    
    # Create LICENSE if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/LICENSE" ]; then
        log_info "Creating LICENSE (MIT)..." # Changed from echo
        
        # Get current year
        local YEAR # Made local
        YEAR=$(date +%Y)
        
        # Create LICENSE with MIT license
        cat > "$PROJECT_ROOT/LICENSE" << EOF
MIT License

Copyright (c) $YEAR

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
        
        log_success "Created LICENSE (MIT)" # Changed from echo
    else
        log_warning "LICENSE already exists. Skipping." # Changed from echo
    fi
    
    # Create basic project structure if src directory doesn't exist
    if [ ! -d "$PROJECT_ROOT/src" ]; then
        log_info "Creating basic project structure..." # Changed from echo
        
        # Get the package name from the directory name
        local PACKAGE_NAME_SRC # Made local
        PACKAGE_NAME_SRC=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
        
        # Create directories
        mkdir -p "$PROJECT_ROOT/src/$PACKAGE_NAME_SRC"
        mkdir -p "$PROJECT_ROOT/tests"
        
        # Create __init__.py with version
        cat > "$PROJECT_ROOT/src/$PACKAGE_NAME_SRC/__init__.py" << EOF
"""$PACKAGE_NAME_SRC package."""

__version__ = "0.1.0"
EOF
        
        # Create empty __init__.py for tests
        touch "$PROJECT_ROOT/tests/__init__.py"
        
        # Create a simple test file
        cat > "$PROJECT_ROOT/tests/test_version.py" << EOF
"""Test version is correctly defined."""

import $PACKAGE_NAME_SRC


def test_version():
    """Test that version is a string."""
    assert isinstance($PACKAGE_NAME_SRC.__version__, str)
EOF
        
        log_success "Created basic project structure" # Changed from echo
    else
        log_warning "src directory already exists. Skipping project structure creation." # Changed from echo
    fi
    
    log_success "Project configuration setup complete." # Changed from echo
    log_info "You may need to review and customize the generated files." # Changed from echo
    
    return 0
}

# Canonical version of env_command
env_command() {
    local report_file="$DHT_DIR/.dht_environment_report.json"

    # Ensure diagnostics run first to generate/update the report
    if ! run_diagnostics; then # Assumes run_diagnostics is available
        log_error "Failed to generate diagnostics report. Cannot display environment info." $ERR_GENERAL
        return $ERR_GENERAL
    fi

    if [[ ! -f "$report_file" ]]; then
        log_error "Diagnostics report file not found: $report_file" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi

    echo "📊 Development Helper Toolkit Environment Information (from report)"
    echo "================================================================="

    # Check if jq is available for pretty printing
    if command -v jq &>/dev/null; then
        # Use jq to format and display the report
        jq '.' "$report_file"
    else
        # Fallback to simple cat if jq is not available
        log_warning "jq command not found. Displaying raw JSON report."
        cat "$report_file"
    fi

    return 0
}
