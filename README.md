# DHT - Development Helper Toolkit

[![PyPI version](https://badge.fury.io/py/dht-toolkit.svg)](https://badge.fury.io/py/dht-toolkit)
[![Python Support](https://img.shields.io/pypi/pyversions/dht-toolkit.svg)](https://pypi.org/project/dht-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> ⚡ The Python ecosystem's answer to JavaScript's Bolt - fast, reliable project management

DHT is a universal development automation tool that provides standardized workflows, environment management, and project automation. It's designed to be familiar to developers coming from JavaScript tooling while leveraging Python's powerful ecosystem.

## Why DHT?

- **Familiar Commands**: If you know Bolt/Yarn/npm, you already know DHT
- **UV-Powered**: Lightning-fast dependency management with UV
- **Workspace Support**: Manage monorepos with multiple packages
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **Fail-Safe Execution**: Prefect-based command runner prevents corruption
- **Deterministic Builds**: Same code produces same results everywhere

## Installation

```bash
# Via pip (Recommended)
pip install dht-toolkit

# Via UV (Fastest)
uv pip install dht-toolkit

# From source
git clone https://github.com/yourusername/dht.git
cd dht
pip install -e .
```

## Quick Start

```bash
# Initialize a new project
dhtl init

# Install dependencies (or just run 'dhtl')
dhtl install

# Add a dependency
dhtl add numpy pandas

# Run scripts
dhtl run test
dhtl run build
```

## Command Reference

### 📦 Package Management

| Command | Description |
|---------|-------------|
| `dhtl` | Install all dependencies (same as `dhtl install`) |
| `dhtl install` | Install project dependencies |
| `dhtl add [packages...]` | Add new dependencies |
| `dhtl remove [packages...]` | Remove dependencies |
| `dhtl upgrade [packages...]` | Upgrade specific packages |
| `dhtl upgrade` | Upgrade all dependencies |

### 🚀 Development Commands

| Command | Description |
|---------|-------------|
| `dhtl run [script]` | Run a script defined in pyproject.toml |
| `dhtl test` | Run tests (pytest) |
| `dhtl build` | Build the project |
| `dhtl lint` | Lint code (ruff, mypy, etc.) |
| `dhtl format` / `dhtl fmt` | Format code (black, ruff format) |
| `dhtl check` | Type check with mypy |
| `dhtl doc` | Generate documentation |

### 🏗️ Workspace Commands

| Command | Description |
|---------|-------------|
| `dhtl workspaces run [script]` | Run script in all workspace packages |
| `dhtl ws run [script]` | Short alias for workspaces run |
| `dhtl ws exec -- [command]` | Execute command in all packages |
| `dhtl workspace [name] run [script]` | Run in specific package |
| `dhtl w [name] run [script]` | Short alias |
| `dhtl project run [script]` | Run in root project only |

**Workspace Filtering:**
- `--only [pattern]` - Only packages matching pattern
- `--ignore [pattern]` - Skip packages matching pattern
- `--only-fs [glob]` - Only packages with matching files
- `--ignore-fs [glob]` - Skip packages with matching files

### 🔧 Project Management

| Command | Description |
|---------|-------------|
| `dhtl init` | Initialize a new project |
| `dhtl setup` | Setup development environment |
| `dhtl clean` | Clean build artifacts and caches |
| `dhtl sync` | Sync dependencies with lock file |

### 📚 Other Commands

| Command | Description |
|---------|-------------|
| `dhtl publish` | Publish to PyPI |
| `dhtl version` / `dhtl bump` | Version management |
| `dhtl bin` | Show path to executables |
| `dhtl help` | Show help |
| `dhtl [unknown]` | Runs as `dhtl run [unknown]` |

## Workspace Configuration

Create a monorepo with multiple packages:

```toml
# pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]
```

Directory structure:
```
my-project/
├── pyproject.toml
├── packages/
│   ├── core/
│   │   └── pyproject.toml
│   ├── cli/
│   │   └── pyproject.toml
│   └── web/
│       └── pyproject.toml
```

## Script Configuration

Define scripts in your `pyproject.toml`:

```toml
[project.scripts]
test = "pytest"
build = "python -m build"
dev = "python -m myapp --debug"
lint = "ruff check ."
typecheck = "mypy src"
```

Run them with:
```bash
dhtl run test
dhtl run build
# or for unknown commands, just:
dhtl test  # automatically runs 'dhtl run test'
```

## Examples

### Starting a New Project

```bash
# Create and initialize a project
mkdir my-awesome-project
cd my-awesome-project
dhtl init --name my-awesome-project --python 3.11

# Add dependencies
dhtl add flask sqlalchemy
dhtl add --dev pytest black mypy

# Run tests
dhtl test
```

### Working with Workspaces

```bash
# Run tests in all packages
dhtl ws run test

# Build only packages that have changed
dhtl ws run build --only "core" --only "cli"

# Execute custom command
dhtl ws exec -- git status

# Work on specific package
dhtl workspace cli run dev
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install DHT
        run: pip install dht-toolkit
      - name: Install dependencies
        run: dhtl install
      - name: Run tests
        run: dhtl test
      - name: Type check
        run: dhtl check
```

## Advanced Features

### Container Deployment

```bash
# Deploy project in container
dhtl deploy_project_in_container --port-mapping 8000:8000

# With Docker
dhtl deploy_project_in_container --docker

# With Podman
dhtl deploy_project_in_container --podman
```

### GitHub Integration

```bash
# Clone with proper setup
dhtl clone https://github.com/org/repo

# Fork and setup
dhtl fork https://github.com/org/repo
```

### Environment Management

DHT automatically:
- Creates virtual environments with UV
- Installs correct Python version
- Manages lock files
- Handles platform-specific dependencies

## Architecture

DHT uses a modular architecture:

- **Command Runner**: Prefect-based execution with crash recovery
- **UV Integration**: Fast, reliable package management
- **Workspace Support**: First-class monorepo support
- **Platform Normalization**: Consistent behavior across OS

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

```bash
# Setup development environment
git clone https://github.com/yourusername/dht.git
cd dht
dhtl setup --dev

# Run tests
dhtl test

# Make your changes and submit a PR!
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [Bolt](https://github.com/boltpkg/bolt) for JavaScript
- Powered by [UV](https://github.com/astral-sh/uv) for fast Python package management
- Built with [Prefect](https://www.prefect.io/) for reliable task execution

---

<p align="center">Made with ❤️ by the Python community</p>
