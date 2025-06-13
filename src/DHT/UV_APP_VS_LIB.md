#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# UV Application vs Library Projects

## Overview

UV distinguishes between two types of Python projects:

1. **Applications (`--app`)**: Standalone programs meant to be run directly
2. **Libraries (`--lib`)**: Packages meant to be imported by other projects

## Key Differences

### Application Projects (`uv init --app`)

**Purpose**: Create standalone applications that users run directly

**Characteristics**:
- No package structure required
- Typically has `main.py`, `app.py`, or similar entry point
- Dependencies are locked for reproducibility
- Not meant to be pip-installed by others
- May include scripts, CLIs, web apps, etc.

**Generated Structure**:
```
my-app/
├── .venv/
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml       # Without package configuration
├── uv.lock             # Locked dependencies
└── main.py             # Or app.py, or similar
```

**pyproject.toml for Apps**:
```toml
[project]
name = "my-app"
version = "0.1.0"
description = "My application"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
]

[project.scripts]
my-app = "main:main"  # Optional CLI entry point
```

### Library Projects (`uv init --lib`)

**Purpose**: Create packages that other projects import

**Characteristics**:
- Has proper package structure with `__init__.py`
- Uses `src/` layout by default
- Meant to be distributed (PyPI, private index)
- Version management is important
- Should work with range of dependency versions

**Generated Structure**:
```
my-lib/
├── .venv/
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml       # With package configuration
├── uv.lock
├── src/
│   └── my_lib/
│       ├── __init__.py
│       └── core.py
└── tests/
    └── test_core.py
```

**pyproject.toml for Libraries**:
```toml
[project]
name = "my-lib"
version = "0.1.0"
description = "My library"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.28.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_lib"]
```

## How DHT Uses This Distinction

### Detection Heuristics

DHT's universal build detector uses these heuristics:

1. **Library Indicators**:
   - Has `src/` directory with packages
   - Has `packages` or `py-modules` in pyproject.toml
   - No main application file
   - Meant for distribution

2. **Application Indicators**:
   - Has `main.py`, `app.py`, or `__main__.py`
   - Has `scripts` defined but no packages
   - Docker/container configuration
   - Web framework setup (Django, Flask, FastAPI)

### Build Behavior

**For Libraries**:
```bash
dhtl build
# Runs: python -m build
# Creates: dist/*.whl and dist/*.tar.gz
```

**For Applications**:
```bash
dhtl build
# Message: "This is an application - no build artifacts needed"
# Suggests: Use 'dhtl run' or 'dhtl dockerize'
```

## Container Projects and DHT

### Why Containers Can't Be in Venv

Docker/Podman are system-level tools that:
- Require kernel features (namespaces, cgroups)
- Need privileged operations
- Run as system daemons

### DHT's Approach

1. **Detect Container Runtime**:
   - Prefer Podman (rootless by default)
   - Fall back to Docker if available
   - Suggest Buildah as alternative

2. **Project-Local Configuration**:
   ```
   .venv/
   └── dht-container/
       ├── build-config.json
       ├── rootless/
       │   ├── containers.conf
       │   └── storage.conf
       └── storage/          # Container layers
   ```

3. **Rootless Builds**:
   - Use Podman/Buildah when possible
   - Store container data in project
   - No system-wide configuration needed

## UV Tool Management for Development Tools

### Installing Tools Globally

```bash
# Install development tools with UV
uv tool install ruff
uv tool install mypy
uv tool install black
uv tool install pytest

# Container tools (system-level)
# macOS
brew install podman

# Linux
sudo apt-get install podman
```

### Tool Usage in DHT

DHT automatically detects and uses:
1. UV-installed tools (isolated, no conflicts)
2. Project venv tools
3. System tools (as fallback)

## Best Practices

### For New Projects

```bash
# Create an application
uv init --app my-webapp
cd my-webapp
dhtl setup

# Create a library  
uv init --lib my-package
cd my-package
dhtl setup
```

### For Existing Projects

DHT automatically detects project type:
```bash
dhtl init          # Detects and configures appropriately
dhtl build         # Knows whether to build artifacts or not
```

### Container Projects

```bash
# DHT detects Dockerfile/docker-compose.yml
dhtl build

# If no runtime available:
# - Suggests installing Podman (rootless)
# - Provides installation commands
# - Sets up project-local config

# With Podman installed:
dhtl build  # Runs: podman build -t project-name .
```

## Summary

- **Libraries**: Distributed packages → build creates wheels
- **Applications**: Standalone programs → no build artifacts
- **Containers**: System-level tools → use Podman for rootless
- **UV Tools**: Development tools → installed globally, used locally

DHT intelligently detects your project type and provides appropriate commands, making the development workflow seamless regardless of project type.