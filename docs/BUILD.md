# Building DHT Toolkit

This document describes how to build the DHT toolkit using `uv`.

## Prerequisites

- Python 3.10 or higher
- uv installed (`pip install uv` or `brew install uv`)
- Git (for cloning the repository)

## Quick Build

```bash
# Clone the repository
git clone https://github.com/yourusername/dht.git
cd dht

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync --all-extras

# Build the project
uv build
```

## Build Commands

### Build Both Source and Wheel Distributions
```bash
uv build
```

### Build Only Source Distribution
```bash
uv build --sdist
```

### Build Only Wheel Distribution
```bash
uv build --wheel
```

### Build with Constraints (Reproducible Builds)
```bash
uv build --build-constraint build-constraints.txt
```

### Build with Hash Verification
```bash
uv build --build-constraint build-constraints.txt --require-hashes
```

## Using the Build Script

A convenience build script is provided that handles the entire build process:

```bash
./scripts/build.sh
```

This script will:
1. Clean previous builds
2. Activate the virtual environment
3. Sync dependencies
4. Run tests
5. Build both sdist and wheel with constraints
6. Verify the build output

## Build Configuration

The build is configured in `pyproject.toml`:

- **Build System**: Uses `hatchling` as the build backend
- **Package Sources**: Located in `src/DHT/`
- **Included Files**: Source code, tests, documentation, and configuration files
- **Excluded Files**: Cache directories, compiled files, and temporary files

### Key Configuration Sections

1. **[build-system]**: Defines the build backend
2. **[tool.hatch.build.targets.wheel]**: Wheel-specific configuration
3. **[tool.hatch.build.targets.sdist]**: Source distribution configuration
4. **[tool.uv]**: uv-specific settings for builds and dependencies

## Build Artifacts

After a successful build, you'll find:

- `dist/dht_toolkit-X.Y.Z-py3-none-any.whl` - Wheel distribution
- `dist/dht_toolkit-X.Y.Z.tar.gz` - Source distribution

## Installing the Built Package

### From Wheel
```bash
uv pip install dist/dht_toolkit-*.whl
```

### From Source Distribution
```bash
uv pip install dist/dht_toolkit-*.tar.gz
```

### Development Installation
```bash
uv pip install -e .
```

## Troubleshooting

### Build Fails with Missing Dependencies
```bash
# Ensure all dependencies are synced
uv sync --all-extras
```

### Build Isolation Issues
```bash
# Build without isolation (not recommended)
uv build --no-build-isolation
```

### Clean Build
```bash
# Remove all build artifacts
rm -rf dist/ build/ *.egg-info src/*.egg-info
```

## Continuous Integration

The project uses GitHub Actions for automated builds. See `.github/workflows/` for CI configuration.

## Publishing

To publish to PyPI:

```bash
# Build the distributions
uv build

# Upload to PyPI (requires credentials)
uv publish
```

For test uploads:
```bash
uv publish --repository testpypi
```
