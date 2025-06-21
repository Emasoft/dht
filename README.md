# DHT - Development Helper Toolkit

[![PyPI version](https://badge.fury.io/py/dht-toolkit.svg)](https://badge.fury.io/py/dht-toolkit)
[![Python Support](https://img.shields.io/pypi/pyversions/dht-toolkit.svg)](https://pypi.org/project/dht-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> ⚡ The Python ecosystem's answer to JavaScript's Bolt - fast, reliable project management

DHT (Development Helper Toolkit) is a universal development automation tool that provides standardized workflows, environment management, and project automation. It's designed to be familiar to developers coming from JavaScript tooling while leveraging Python's powerful ecosystem.

## Why DHT?

- **Familiar Commands**: If you know Bolt/Yarn/npm, you already know DHT
- **UV-Powered**: Lightning-fast dependency management with UV
- **Workspace Support**: Manage monorepos with multiple packages
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **Fail-Safe Execution**: Prefect-based command runner prevents corruption
- **Deterministic Builds**: Same code produces same results everywhere
- **Platform Detection**: Automatically detects and adapts to your platform
- **Resource Management**: Built-in memory limits and timeout protection

## Installation

### Via pip (Recommended)
```bash
pip install dht-toolkit
```

### Via UV (Fastest)
```bash
uv pip install dht-toolkit
```

### From Source (Development)

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/dht.git
cd dht
```

2. **Create virtual environment with UV**:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies and DHT in development mode**:
```bash
uv sync --all-extras --dev
uv pip install -e .
```

4. **Verify installation**:
```bash
dhtl --help  # Should show the help screen
dhtl version  # Should show: Development Helper Toolkit (DHT) v1.0.0
```

5. **Set up pre-commit hooks** (for contributors):
```bash
uv run pre-commit install
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

## Full Command Reference (Help Screen)

This is the complete output from `dhtl help`, showing all available commands grouped by category:

```
Development Helper Toolkit (DHT) v1.0.0
=====================================

Usage: dhtl <command> [options]

Available commands:

Project Management:
  init           Initialize a new Python project
  setup          Setup project environment
  clean          Clean project

Development:
  build          Build Python package
  sync           Sync project dependencies
  test           Run project tests
  lint           Lint code
  format         Format code
  coverage       Run code coverage

Version Control:
  commit         Create git commit
  tag            Create git tag
  bump           Bump version
  clone          Clone repository
  fork           Fork repository

Deployment:
  publish        Publish package
  deploy_project_in_container  Deploy project in Docker container
  workflows      Manage workflows

Utilities:
  env            Show environment
  diagnostics    Run diagnostics
  restore        Restore dependencies
  guardian       Manage process guardian

Help:
  help           Show help
  version        Show version

For command-specific help: dhtl <command> --help
```

### Additional Commands (Complete List)

Beyond the categorized commands above, DHT provides these additional commands:

| Command | Description |
|---------|-------------|
| `dhtl act` | Run GitHub Actions locally with act |
| `dhtl bin` | Print executable files installation folder |
| `dhtl check` | Type check Python code |
| `dhtl coverage` | Run code coverage analysis |
| `dhtl doc` | Generate project documentation |
| `dhtl node [args]` | Run node command |
| `dhtl python [args]` | Run python command |
| `dhtl script [name]` | Run script |
| `dhtl test_dht` | Test DHT itself |
| `dhtl verify_dht` | Verify DHT installation |
| `dhtl p [command]` | Alias for `project` command |

### Global Options

These options can be used with any command:

- `--no-guardian` - Disable process guardian for this command
- `--quiet` - Reduce output verbosity
- `--debug` - Enable debug mode
- `--help` - Show command-specific help

### Environment Variables

DHT sets these environment variables during execution:

- `PROJECT_ROOT` - Path to the project root directory
- `DEFAULT_VENV_DIR` - Path to the default virtual environment
- `PLATFORM` - Detected platform (macos/linux/windows/windows_unix/bsd)
- `PYTHON_CMD` - Python command to use (python3/python)
- `DEFAULT_MEM_LIMIT` - Default memory limit in MB (2048)
- `PYTHON_MEM_LIMIT` - Python process memory limit in MB (2048)
- `QUIET_MODE` - Whether quiet mode is enabled (0/1)
- `DEBUG_MODE` - Whether debug mode is enabled (true/false)

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

DHT integrates seamlessly with GitHub Actions using UV for fast, reliable builds:

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Install UV for fast package management
      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      # Set up Python version
      - name: Set up Python
        run: uv python install 3.11

      # Install dependencies
      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      # Run tests
      - name: Run tests
        run: uv run pytest tests/ -v

      # Type check
      - name: Type check
        run: uv run mypy src/

      # Lint
      - name: Lint
        run: |
          uv run ruff check src/ tests/
          uv run ruff format --check src/ tests/
```

### Pre-commit Integration

DHT uses UV-powered pre-commit hooks to ensure code quality:

```yaml
# .pre-commit-config.yaml
repos:
  # UV for dependency management
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.7.13
    hooks:
      # Ensure uv.lock is up-to-date
      - id: uv-lock
        args: [--locked]
        files: pyproject.toml
      # Export requirements for compatibility
      - id: uv-export
        args: [--frozen, --no-hashes, --output-file=requirements.txt]
        files: pyproject.toml|uv.lock
```

To set up pre-commit hooks:
```bash
uv run pre-commit install
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

DHT uses a modular architecture designed for reliability and extensibility:

### Core Components

- **Command Runner**: Prefect-based execution with crash recovery and resource management
- **UV Integration**: Lightning-fast package management with deterministic builds
- **Workspace Support**: First-class monorepo support with advanced filtering
- **Platform Normalization**: Consistent behavior across macOS, Linux, and Windows
- **Process Guardian**: Memory limits and timeout protection for all operations
- **Environment Reproducer**: Capture and recreate exact development environments

### Directory Structure

```
dht/
├── src/DHT/
│   ├── modules/           # Core functionality modules
│   │   ├── commands/      # Individual command implementations
│   │   ├── parsers/       # File and language parsers
│   │   └── dht_flows/     # Prefect workflow definitions
│   ├── launcher.py        # Main DHT launcher
│   └── dhtl.py           # Entry point
├── tests/                 # Comprehensive test suite
├── .pre-commit-config.yaml # Pre-commit hooks with UV
├── pyproject.toml        # Project configuration
└── uv.lock              # Locked dependencies

```

### Key Features

1. **Deterministic Builds**: UV lock files ensure identical builds across all platforms
2. **Resource Protection**: All commands run with configurable memory limits
3. **Platform Detection**: Automatically adapts to your OS and environment
4. **Fail-Safe Operations**: Prefect ensures operations complete or rollback cleanly
5. **Comprehensive Tooling**: Built-in support for linting, formatting, testing, and more

### UV Integration

DHT leverages UV (by Astral) for:
- **Speed**: 10-100x faster than pip
- **Reliability**: Built-in resolver prevents conflicts
- **Reproducibility**: Lock files ensure consistent environments
- **Python Management**: Automatic Python version installation
- **Workspace Support**: Native monorepo capabilities

### Environment Configuration

DHT automatically creates a `.dhtconfig` file that captures:
- Python version requirements
- System dependencies
- Tool configurations
- Platform-specific settings

This allows any project to be regenerated with just:
```bash
dhtl regenerate
```

## Platform-Specific Notes

### macOS
- DHT automatically detects Homebrew installations
- Supports Apple Silicon (M1/M2) natively
- Uses `python3` by default

### Linux
- Works with all major distributions
- Detects system package managers (apt, yum, dnf, etc.)
- Supports both system and user Python installations

### Windows
- Full support via Git Bash or WSL
- Native Windows support for Python operations
- Automatic path normalization

## Troubleshooting

### Common Issues

1. **Command not found**:
   ```bash
   # Ensure DHT is in your PATH
   pip show dht-toolkit  # Check installation
   which dhtl           # Verify command availability
   ```

2. **Permission errors**:
   ```bash
   # Use --user flag for user installation
   pip install --user dht-toolkit
   ```

3. **UV not found**:
   ```bash
   # DHT will install UV automatically, or install manually:
   pip install uv
   ```

### Debug Mode

Run any command with `--debug` for verbose output:
```bash
dhtl --debug setup
dhtl --debug test
```

## Security

DHT includes built-in security features:

- **Gitleaks Integration**: Prevents secrets from being committed
- **Dependency Scanning**: Via deptry for unused/missing dependencies
- **Resource Limits**: Prevents runaway processes
- **Sandboxed Execution**: Commands run in isolated environments

## Performance

DHT is optimized for speed:

- **UV Package Manager**: 10-100x faster than pip
- **Parallel Operations**: Workspace commands run concurrently
- **Smart Caching**: Reuses previous builds when possible
- **Minimal Overhead**: Direct command execution without wrappers

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/dht.git
cd dht

# Create virtual environment with UV
uv venv
source .venv/bin/activate

# Install in development mode with all extras
uv sync --all-extras --dev
uv pip install -e .

# Set up pre-commit hooks
uv run pre-commit install

# Run tests to verify setup
uv run pytest tests/ -v

# Run linters
uv run ruff check src/ tests/
uv run mypy src/
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_specific.py

# Run with coverage
uv run pytest --cov=src/DHT --cov-report=html

# Run integration tests
uv run pytest tests/integration/ -v
```

### Code Style

DHT uses:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pre-commit** for automatic checks
- **Black-compatible** formatting

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [Bolt](https://github.com/boltpkg/bolt) for JavaScript
- Powered by [UV](https://github.com/astral-sh/uv) for fast Python package management
- Built with [Prefect](https://www.prefect.io/) for reliable task execution
- Uses [Gitleaks](https://github.com/zricethezav/gitleaks) for security scanning

## Related Projects

- [UV](https://github.com/astral-sh/uv) - An extremely fast Python package installer and resolver
- [Ruff](https://github.com/astral-sh/ruff) - An extremely fast Python linter
- [Prefect](https://www.prefect.io/) - Modern workflow orchestration
- [Bolt](https://github.com/boltpkg/bolt) - The JavaScript monorepo tool that inspired DHT

---

<p align="center">
  Made with ❤️ by the Python community<br>
  <a href="https://github.com/yourusername/dht">GitHub</a> •
  <a href="https://pypi.org/project/dht-toolkit/">PyPI</a> •
  <a href="https://github.com/yourusername/dht/issues">Issues</a> •
  <a href="https://github.com/yourusername/dht/discussions">Discussions</a>
</p>
