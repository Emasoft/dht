#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# UV Tool Management in DHT

## Overview

DHT leverages UV's powerful tool management capabilities to handle development tools globally, separate from project-specific dependencies. This provides a clean separation between:

1. **Global Development Tools**: Installed once, used across all projects
2. **Project Dependencies**: Specific to each project's virtual environment

## Installing Global Tools with UV

UV provides the `uv tool install` command to install Python tools globally in isolated environments:

```bash
# Install common development tools
uv tool install ruff              # Fast Python linter
uv tool install mypy              # Static type checker
uv tool install bump-my-version   # Version management
uv tool install yamllint          # YAML linter
uv tool install black             # Code formatter
uv tool install isort             # Import sorter
uv tool install flake8            # Style guide enforcer
uv tool install pytest            # Testing framework
uv tool install pre-commit        # Git hook framework
```

## Benefits of UV Tool Management

1. **Isolation**: Each tool runs in its own virtual environment
2. **No Conflicts**: Tools don't interfere with project dependencies
3. **Fast Installation**: UV's caching makes installations lightning fast
4. **Automatic Updates**: Easy to update tools independently
5. **Cross-Project Usage**: One installation works for all projects

## DHT Integration

DHT automatically detects and uses UV-installed tools when available:

```bash
# DHT commands that use global tools
dhtl lint      # Uses ruff, mypy, flake8, etc.
dhtl format    # Uses black, isort
dhtl test      # Uses pytest
dhtl bump      # Uses bump-my-version
```

## Tool Categories

### Linting and Formatting
- `ruff` - Fast Python linter and formatter
- `black` - Opinionated code formatter
- `isort` - Import statement sorter
- `flake8` - Style guide enforcer
- `mypy` - Static type checker
- `yamllint` - YAML file linter

### Testing
- `pytest` - Feature-rich testing framework
- `pytest-cov` - Coverage plugin for pytest
- `tox` - Test automation tool

### Development Utilities
- `bump-my-version` - Version bumping tool
- `pre-commit` - Git hook manager
- `pipx` - Install Python applications (alternative to uv tool)

### Documentation
- `sphinx` - Documentation generator
- `mkdocs` - Project documentation with Markdown

## Best Practices

1. **Install Tools Globally**: Use `uv tool install` for development tools
2. **Project Dependencies in Venv**: Keep runtime dependencies in project virtual environments
3. **Document Required Tools**: List required tools in project documentation
4. **Version Pinning**: Consider pinning tool versions for team consistency:
   ```bash
   uv tool install ruff==0.11.13
   ```

## DHT Tool Detection

DHT automatically detects available tools in this order:
1. UV-installed tools (via `uv tool`)
2. Virtual environment tools
3. System-wide installations

This ensures DHT always uses the most appropriate version of each tool.

## Managing Tool Environments

```bash
# List installed tools
uv tool list

# Update a tool
uv tool install --upgrade ruff

# Uninstall a tool
uv tool uninstall ruff

# Run a tool directly
uv tool run ruff check .
```

## Integration with DHT Commands

DHT commands automatically leverage UV tools:

```bash
# Uses UV-installed ruff if available
dhtl lint

# Falls back gracefully if tool not installed
# DHT will suggest: uv tool install ruff
```

## Tool Installation Script

DHT can install all recommended tools:

```bash
# Install all recommended development tools
dhtl install-dev-tools

# This runs:
# uv tool install ruff mypy black isort flake8 pytest bump-my-version pre-commit yamllint
```

## Conclusion

UV's tool management provides a clean, fast, and reliable way to manage development tools across all your projects. DHT fully embraces this approach, making it easy to maintain consistent development environments without polluting project-specific virtual environments.