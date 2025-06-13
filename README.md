# DHT - Development Helper Toolkit

[![PyPI version](https://badge.fury.io/py/dht-toolkit.svg)](https://badge.fury.io/py/dht-toolkit)
[![Python Support](https://img.shields.io/pypi/pyversions/dht-toolkit.svg)](https://pypi.org/project/dht-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A universal development automation tool that provides standardized workflows, environment management, and project automation across different platforms and project types.

## Features

**Universal Project Support**
- Python, Node.js, Rust, Go, C++, Java, .NET
- Automatic project type detection
- Language-specific build commands

**Smart Environment Management**
- UV-based Python environment handling
- Automatic dependency installation
- Cross-platform compatibility

**GitHub Actions Integration**
- Lint workflows with `actionlint`
- Run workflows locally with `act`
- Container-based execution for isolation

**Build & Package Management**
- Universal build detection
- Container builds (Docker/Podman)
- Package publishing support

**Development Best Practices**
- Integrated linting and formatting
- Comprehensive testing framework
- Git hooks and CI/CD templates

## Installation

### Via pip (Recommended)

```bash
pip install dht-toolkit
```

This installs the `dhtl` command globally.

### Via UV (Fast)

```bash
uv pip install dht-toolkit
```

### From Source

```bash
git clone https://github.com/yourusername/dht.git
cd dht
pip install -e .
```

## Quick Start

### Initialize DHT in Your Project

```bash
cd your-project
dhtl init
```

This will:
- Detect your project type
- Set up appropriate configurations
- Create virtual environments
- Install dependencies

### Common Commands

```bash
# Set up development environment
dhtl setup

# Run linters
dhtl lint
dhtl lint --fix  # Auto-fix issues

# Format code
dhtl format

# Run tests
dhtl test

# Build project
dhtl build

# Manage GitHub workflows
dhtl workflows lint        # Check syntax
dhtl workflows run         # Execute locally
dhtl workflows test        # Full test suite
```

## Workflow Management

DHT provides comprehensive GitHub Actions integration:

```bash
# Lint workflows for syntax errors
dhtl workflows lint

# Run workflows locally with act
dhtl workflows run push
dhtl workflows run pull_request

# Run in isolated container
dhtl workflows run-in-container push

# List all workflows and jobs
dhtl workflows list
```

## Project Types Supported

DHT automatically detects and configures:

- **Python**: pyproject.toml, setup.py, requirements.txt
- **Node.js**: package.json, npm/yarn/pnpm
- **Rust**: Cargo.toml
- **Go**: go.mod
- **C++**: CMakeLists.txt, Makefile
- **Java**: pom.xml, build.gradle
- **.NET**: *.csproj, *.sln

## Advanced Features

### UV Integration

DHT uses UV for fast Python dependency management:

```bash
# Install dependencies
dhtl restore

# Add new dependency
dhtl uv add requests

# Build package
dhtl uv build
```

### Container Support

Build and run in containers:

```bash
# Build Docker image
dhtl docker build

# Run in container
dhtl docker run
```

### Version Management

```bash
# Bump version
dhtl bump patch  # 1.0.0 -> 1.0.1
dhtl bump minor  # 1.0.0 -> 1.1.0
dhtl bump major  # 1.0.0 -> 2.0.0

# Create git tag
dhtl tag v1.0.0 -m "Release version 1.0.0"
```

## Configuration

DHT uses minimal configuration. Most settings are auto-detected.

### .dhtconfig (Optional)

```yaml
# Only include non-inferrable settings
project:
  name: my-project
  
secrets:
  api_key: ${API_KEY}
  
deploy:
  target: production
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Issues: https://github.com/yourusername/dht/issues
- Documentation: https://github.com/yourusername/dht/wiki
- Discussions: https://github.com/yourusername/dht/discussions