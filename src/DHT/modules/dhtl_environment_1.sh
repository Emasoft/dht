#!/bin/bash
# dhtl_environment_1.sh - Environment_1 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to environment_1 functionality.
# It is sourced by the main dhtl.sh orchestrator and should not be modified manually.
# To make changes, modify the original dhtl.sh and regenerate the modules.
#
# DO NOT execute this file directly.


# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of dhtl and cannot be executed directly." >&2
    echo "Please use the main dhtl.sh script instead." >&2
    exit 1
fi

# Check if we're being sourced by the main script
if [[ -z "$DHTL_SESSION_ID" ]]; then
    echo "ERROR: This script is being sourced outside of dhtl. This is not supported." >&2
    return 1 2>/dev/null || exit 1
fi


# ===== Functions =====

# Find the project root directory
find_project_root() {
    # Start from the current directory
    local dir="${PWD}"
    
    # Traverse up the directory tree looking for common project markers
    while [[ "$dir" != "/" ]]; do
        # Check for common project markers
        if [[ -d "$dir/.git" || -f "$dir/package.json" || -f "$dir/pyproject.toml" || 
              -f "$dir/setup.py" || -f "$dir/Cargo.toml" || -f "$dir/go.mod" ]]; then
            echo "$dir"
            return 0
        fi
        
        # Move up one directory
        dir="$(dirname "$dir")"
    done
    
    # If no project root found, use the current directory
    echo "${PWD}"
    return 0
}

setup_project_command() {
    log_info "📝 Creating project configuration files..."
    PROJECT_ROOT=$(find_project_root)
    
    # Create pyproject.toml if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
        log_info "Creating pyproject.toml..."
        
        # Get the package name from the directory name
        local package_name
        package_name=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
        
        # Create pyproject.toml with basic structure
        cat > "$PROJECT_ROOT/pyproject.toml" << EOF
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "$package_name"
version = "0.1.0"  # Managed by bump-my-version
description = "Description of your project"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
readme = "README.md"
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
"Homepage" = "https://github.com/yourusername/$package_name"
"Bug Tracker" = "https://github.com/yourusername/$package_name/issues"

[tool.setuptools]
package-dir = {"" = "src"}

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
        
        log_success "Created pyproject.toml"
    else
        log_warning "pyproject.toml already exists. Skipping."
    fi
    
    # Create .bumpversion.toml if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.bumpversion.toml" ]; then
        log_info "Creating .bumpversion.toml..."
        
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
        
        log_success "Created .bumpversion.toml"
    else
        log_warning ".bumpversion.toml already exists. Skipping."
    fi
    
    # Create .pre-commit-config.yaml if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]; then
        log_info "Creating .pre-commit-config.yaml..."
        
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
    rev: v0.0.262 # Consider updating to a newer ruff version
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
        
        log_success "Created .pre-commit-config.yaml"
    else
        log_warning ".pre-commit-config.yaml already exists. Skipping."
    fi
    
    # Create README.md if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/README.md" ]; then
        log_info "Creating README.md..."
        
        local package_name_readme
        package_name_readme=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
        local display_name_readme
        display_name_readme=$(basename "$PROJECT_ROOT" | tr '_' ' ' | sed -e 's/\b\(.\)/\u\1/g')
        
        # Create README.md with basic structure
        cat > "$PROJECT_ROOT/README.md" << EOF
# $display_name_readme

[![PyPI Version](https://img.shields.io/pypi/v/$package_name_readme)](https://pypi.org/project/$package_name_readme)
[![Python Versions](https://img.shields.io/pypi/pyversions/$package_name_readme)](https://pypi.org/project/$package_name_readme)
[![License](https://img.shields.io/pypi/l/$package_name_readme)](https://github.com/yourusername/$package_name_readme/blob/main/LICENSE)

A brief description of your project.

## Installation

\`\`\`bash
pip install $package_name_readme
\`\`\`

## Usage

\`\`\`python
import $package_name_readme

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
        
        log_success "Created README.md"
    else
        log_warning "README.md already exists. Skipping."
    fi
    
    # Create LICENSE if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/LICENSE" ]; then
        log_info "Creating LICENSE (MIT)..."
        
        # Get current year
        local current_year
        current_year=$(date +%Y)
        
        # Create LICENSE with MIT license
        cat > "$PROJECT_ROOT/LICENSE" << EOF
MIT License

Copyright (c) $current_year

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
        
        log_success "Created LICENSE (MIT)"
    else
        log_warning "LICENSE already exists. Skipping."
    fi
    
    # Create basic project structure if src directory doesn't exist
    if [ ! -d "$PROJECT_ROOT/src" ]; then
        log_info "Creating basic project structure..."
        
        local package_name_src
        package_name_src=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
        
        # Create directories
        mkdir -p "$PROJECT_ROOT/src/$package_name_src"
        mkdir -p "$PROJECT_ROOT/tests"
        
        # Create __init__.py with version
        cat > "$PROJECT_ROOT/src/$package_name_src/__init__.py" << EOF
"""$package_name_src package."""

__version__ = "0.1.0"
EOF
        
        # Create empty __init__.py for tests
        touch "$PROJECT_ROOT/tests/__init__.py"
        
        # Create a simple test file
        cat > "$PROJECT_ROOT/tests/test_version.py" << EOF
"""Test version is correctly defined."""

import $package_name_src


def test_version():
    """Test that version is a string."""
    assert isinstance($package_name_src.__version__, str)
EOF
        
        log_success "Created basic project structure"
    else
        log_warning "src directory already exists. Skipping project structure creation."
    fi
    
    log_success "Project configuration setup complete."
    log_info "You may need to review and customize the generated files."
    
    return 0
}
