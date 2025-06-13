# DHT Commands Reference

This document provides a comprehensive reference for all commands available in the Development Helper Toolkit (DHT).

## Table of Contents

1. [Environment Management](#environment-management)
   - [setup](#setup)
   - [env](#env)
   - [restore](#restore)
   - [clean](#clean)
   - [init](#init)

2. [Development Workflow](#development-workflow)
   - [test](#test)
   - [lint](#lint)
   - [format](#format)
   - [build](#build)
   - [publish](#publish)

3. [Process Management](#process-management)
   - [guardian](#guardian)
   - [python](#python)
   - [node](#node)
   - [run](#run)

4. [Version Management](#version-management)
   - [tag](#tag)
   - [bump](#bump)

5. [Project Testing](#project-testing)
   - [test_dht](#test_dht)
   - [verify](#verify)

6. [UV Integration](#uv-integration)
   - [uv setup](#uv-setup)
   - [uv venv](#uv-venv)
   - [uv sync](#uv-sync)
   - [uv tool](#uv-tool)
   - [uv build](#uv-build)

## Environment Management

### setup

Sets up the DHT toolkit for the current project.

```bash
dhtl setup
```

This command:
- Creates a virtual environment if it doesn't exist
- Installs required dependencies
- Sets up git hooks
- Initializes the DHT configuration

### env

Shows environment information.

```bash
dhtl env
```

This command displays:
- Platform information
- Python version
- Virtual environment status
- API keys (with values hidden)
- Available development tools

### restore

Restores cached dependencies from lock files.

```bash
dhtl restore
```

This command:
- Ensures virtual environment is set up
- Installs dependencies from lock files
- Installs critical development tools

### clean

Cleans temporary files and caches.

```bash
dhtl clean
```

This command:
- Removes temporary files and caches
- Removes compiled Python files
- Cleans build artifacts

### init

Initializes a new project with DHT.

```bash
dhtl init [target_directory]
```

- `target_directory`: The directory to initialize (defaults to current directory)

This command:
- Creates the DHT directory structure
- Copies essential modules
- Creates the launcher script
- Sets up a basic test framework
- Initializes git if not already initialized
- Creates initial project structure if it doesn't exist

## Development Workflow

### test

Runs tests for the project.

```bash
dhtl test [options]
```

Options:
- `--fast`: Run only critical tests
- `--pattern <pattern>`: Run tests matching the pattern
- `--coverage`: Generate a coverage report

### lint

Runs linters on the project code.

```bash
dhtl lint [options]
```

Options:
- `--fix`: Automatically fix issues where possible
- `--path <path>`: Lint only files in the specified path

### format

Formats the project code.

```bash
dhtl format [options]
```

Options:
- `--check`: Check if files are formatted, but don't change them
- `--path <path>`: Format only files in the specified path

### build

Builds the Python package.

```bash
dhtl build [options]
```

Options:
- `--no-checks`: Skip linting and testing before building
- `--clean`: Clean build artifacts before building

### publish

Publishes the package to GitHub.

```bash
dhtl publish [options]
```

Options:
- `--skip-tests`: Skip running tests locally
- `--skip-linters`: Skip running linters locally
- `--force`: Force push to repository
- `--dry-run`: Execute all steps except final GitHub push

## Process Management

### guardian

Manages the process guardian.

```bash
dhtl guardian <subcommand>
```

Subcommands:
- `status`: Show current status
- `start`: Start the process guardian
- `stop`: Stop the process guardian
- `restart`: Restart the process guardian

### python

Runs a Python script with resource management.

```bash
dhtl python <script> [args...]
```

This command:
- Runs the script with memory limits
- Monitors resource usage
- Provides graceful termination

### node

Runs a Node.js script with resource management.

```bash
dhtl node <script> [args...]
```

This command:
- Runs the script with memory limits
- Monitors resource usage
- Provides graceful termination

### run

Runs any command with resource management.

```bash
dhtl run <command> [args...]
```

This command:
- Runs the command with memory limits
- Monitors resource usage
- Provides graceful termination

## Version Management

### tag

Creates a git tag.

```bash
dhtl tag [options] [tag_name]
```

Options:
- `--name <tag_name>`: Tag name (can also be specified as first argument)
- `--message <message>`: Tag message
- `--lightweight`: Create a lightweight tag instead of an annotated one
- `--force`: Overwrite existing tag

If no tag name is provided, the command will attempt to extract the version from:
1. pyproject.toml
2. package.json
3. __init__.py files

### bump

Bumps the version number.

```bash
dhtl bump [version_part] [options]
```

Version parts:
- `major`: Bump major version (X.0.0)
- `minor`: Bump minor version (0.X.0) (default)
- `patch`: Bump patch version (0.0.X)
- `pre`: Bump pre-release version
- `release`: Finalize from pre-release
- `dev`: Bump development version
- `final`: Finalize version

Options:
- `--dry-run`: Show what would be done, but don't actually do it
- `--no-commit`: Don't create a git commit
- `--no-tag`: Don't create a git tag
- `--no-dirty`: Don't allow dirty working directory

## Project Testing

### test_dht

Runs tests for the DHT toolkit itself.

```bash
dhtl test_dht [options]
```

Options:
- `--unit`: Run only unit tests
- `--integration`: Run only integration tests
- `--pattern <pattern>`: Run tests matching the pattern
- `--path <path>`: Run tests in the specified path
- `--report`: Generate a coverage report

### verify

Verifies the DHT installation.

```bash
dhtl verify
```

This command:
- Checks the DHT directory structure
- Verifies essential modules
- Checks the launcher script
- Verifies the virtual environment
- Checks git integration

## UV Integration

### uv setup

Sets up UV for the project.

```bash
dhtl uv setup
```

This command:
- Installs UV if not already available
- Configures UV for the project

### uv venv

Creates a virtual environment using UV.

```bash
dhtl uv venv [path] [python_version]
```

- `path`: Path to the virtual environment (defaults to .venv)
- `python_version`: Python version to use (e.g., 3.10)

### uv sync

Syncs dependencies from lock file.

```bash
dhtl uv sync
```

This command:
- Syncs dependencies from uv.lock
- Creates uv.lock if it doesn't exist

### uv tool

Manages tools with UV.

```bash
dhtl uv tool <subcommand> [args...]
```

Subcommands:
- `run <tool> [args...]`: Run a tool
- `install <tool>`: Install a tool
- `list`: List installed tools

### uv build

Builds the package using UV.

```bash
dhtl uv build
```

This command:
- Builds the package using UV
- Creates wheel and sdist distributions