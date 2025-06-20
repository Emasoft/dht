# Tree-Sitter Usage in DHT

## Overview
DHT uses tree-sitter-bash for advanced Bash script parsing capabilities. The tree-sitter-bash directory is dynamically downloaded and should not be tracked in git.

## Setup Process
The `src/DHT/setup_tree_sitter.py` script handles the setup:
1. Installs the tree-sitter Python package
2. Clones tree-sitter-bash from GitHub to `./tree-sitter-bash/`
3. Builds the language library
4. Tests the parsing functionality

## Files That Use Tree-Sitter

### Core Parser Implementation
- `src/DHT/modules/parsers/bash_parser_tree_sitter.py` - Main tree-sitter parser implementation
- `src/DHT/modules/parsers/bash_parser.py` - Orchestrates parsing, falls back to regex if tree-sitter unavailable

### Setup and Configuration
- `src/DHT/setup_tree_sitter.py` - Setup script that clones and builds tree-sitter-bash
- `pyproject.toml` - Declares tree-sitter dependencies
- `requirements/tree-sitter.in` - Pins specific versions

### Testing
- `tests/test_bash_parser.py` - Tests Bash parsing functionality
- `tests/unit/test_comprehensive_verification.py` - Excludes tree-sitter-bash from checks

### Distribution
- `MANIFEST.in` - Excludes tree-sitter-bash directory from package distribution
- `.gitignore` - Excludes tree-sitter-bash directory from git tracking

## Why Not Track tree-sitter-bash?
1. It's platform-specific (contains compiled binaries)
2. It's downloaded from an external repository
3. It's rebuilt locally based on the system
4. The setup script handles installation automatically

## Usage
When tree-sitter is available, the Bash parser can extract:
- Function definitions with full AST analysis
- Variable declarations and exports
- Sourced files
- Commands and their arguments
- Comments and documentation
- Control structures (if/for/while/case)

If tree-sitter is not available, the parser falls back to regex-based parsing with reduced accuracy.
