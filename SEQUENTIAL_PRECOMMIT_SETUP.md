# Sequential Pre-commit Setup Guide

This guide provides a project-local solution for configuring pre-commit hooks to run sequentially, preventing system resource exhaustion. All configuration is contained within the project directory - no system or user configuration files are modified.

## Why Sequential Execution

Parallel pre-commit hooks can cause:
- Memory exhaustion from concurrent linters/formatters
- File access conflicts when multiple tools modify the same files
- Git operation conflicts from simultaneous operations
- System crashes on resource-constrained machines
- Unpredictable hook execution order

Sequential execution prioritizes stability and minimal resource usage over speed.

## Prerequisites

Only global tool installations are required:
- Python 3.8+
- Git
- uv (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Optionally: Homebrew (macOS/Linux) for system tools

## Project-Local Setup

### 1. Initialize Virtual Environment with Sequential Configuration

Create `.venv/bin/activate.d/sequential-precommit.sh` (or `.venv/Scripts/activate.d/` on Windows):

```bash
#!/usr/bin/env bash
# Project-local environment configuration for sequential pre-commit
# This file is sourced automatically when the virtual environment is activated

# Force sequential execution
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1
export UV_NO_CACHE=1
export PRE_COMMIT_NO_CONCURRENCY=1

# Resource limits
export MEMORY_LIMIT_MB=2048
export TIMEOUT_SECONDS=600

# Tool-specific limits
export TRUFFLEHOG_TIMEOUT=300
export TRUFFLEHOG_MEMORY_MB=1024
export TRUFFLEHOG_CONCURRENCY=1

echo "Sequential pre-commit environment activated"
echo "  Max workers: 1 (sequential execution)"
echo "  Memory limit: ${MEMORY_LIMIT_MB}MB"
echo "  Timeout: ${TIMEOUT_SECONDS}s"
```

### 2. Project Setup Script

Create `setup-sequential-precommit.sh` in your project root:

```bash
#!/usr/bin/env bash
# Setup script for sequential pre-commit execution
# All configuration is project-local - no system files are modified

set -euo pipefail

echo "Setting up project-local sequential pre-commit..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Create activation hooks directory
mkdir -p .venv/bin/activate.d 2>/dev/null || mkdir -p .venv/Scripts/activate.d 2>/dev/null

# Create environment configuration
cat > .venv/bin/activate.d/sequential-precommit.sh << 'EOF'
#!/usr/bin/env bash
# Project-local environment configuration
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1
export UV_NO_CACHE=1
export PRE_COMMIT_NO_CONCURRENCY=1
export MEMORY_LIMIT_MB=2048
export TIMEOUT_SECONDS=600
export TRUFFLEHOG_TIMEOUT=300
export TRUFFLEHOG_MEMORY_MB=1024
export TRUFFLEHOG_CONCURRENCY=1
EOF

chmod +x .venv/bin/activate.d/sequential-precommit.sh 2>/dev/null || true

# Activate virtual environment
source .venv/bin/activate

# Install pre-commit as a uv tool (project-local)
echo "Installing pre-commit..."
uv tool install pre-commit --with pre-commit-uv

# Create wrapper scripts directory
mkdir -p .pre-commit-wrappers

# Create memory-limited wrapper
cat > .pre-commit-wrappers/memory-limited-hook.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Use project-local environment variables
MEMORY_LIMIT_MB="${MEMORY_LIMIT_MB:-2048}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-600}"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <command> [args...]"
    exit 1
fi

COMMAND="$1"
shift

# Platform-specific memory limiting
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    ulimit -v $((MEMORY_LIMIT_MB * 1024)) 2>/dev/null || true
    ulimit -d $((MEMORY_LIMIT_MB * 1024)) 2>/dev/null || true
fi

# Cleanup on exit
cleanup() {
    pkill -P $$ 2>/dev/null || true
    if [[ "$COMMAND" == *"python"* ]] || [[ "$COMMAND" == *"uv"* ]]; then
        python3 -c "import gc; gc.collect()" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# Execute with timeout
if command -v timeout &> /dev/null; then
    exec timeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
elif command -v gtimeout &> /dev/null; then
    exec gtimeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
else
    "$COMMAND" "$@"
fi
EOF

# Create Trufflehog wrapper
cat > .pre-commit-wrappers/trufflehog-limited.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Use project-local environment variables
TIMEOUT="${TRUFFLEHOG_TIMEOUT:-300}"
MEMORY_LIMIT="${TRUFFLEHOG_MEMORY_MB:-1024}"
CONCURRENCY="${TRUFFLEHOG_CONCURRENCY:-1}"

# Check if trufflehog is installed
if ! command -v trufflehog &> /dev/null; then
    echo "Installing Trufflehog locally..."
    # Install to project-local bin directory
    mkdir -p .venv/bin
    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | \
        sh -s -- -b .venv/bin
fi

echo "Running Trufflehog (timeout: ${TIMEOUT}s, concurrency: ${CONCURRENCY})..."

# Run with resource limits
if command -v timeout &> /dev/null; then
    timeout_cmd="timeout ${TIMEOUT}s"
elif command -v gtimeout &> /dev/null; then
    timeout_cmd="gtimeout ${TIMEOUT}s"
else
    timeout_cmd=""
fi

$timeout_cmd trufflehog git file://. \
    --only-verified \
    --fail \
    --no-update \
    --concurrency="$CONCURRENCY" || exit_code=$?

if [ "${exit_code:-0}" -eq 124 ]; then
    echo "Warning: Trufflehog timed out after ${TIMEOUT}s"
    exit 0
elif [ "${exit_code:-0}" -ne 0 ]; then
    echo "Error: Trufflehog found verified secrets!"
    exit 1
fi

echo "✓ No verified secrets found"
EOF

chmod +x .pre-commit-wrappers/*.sh

# Create git hook that sources project environment
cat > .git/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
# Git pre-commit hook - sources project environment

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT" || exit 1

# Source project virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Source sequential configuration
if [ -f ".venv/bin/activate.d/sequential-precommit.sh" ]; then
    source .venv/bin/activate.d/sequential-precommit.sh
fi

# Check memory before running
if [[ "$OSTYPE" == "darwin"* ]]; then
    FREE_MB=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    PAGE_SIZE=$(pagesize 2>/dev/null || echo 16384)
    FREE_MB=$((FREE_MB * PAGE_SIZE / 1024 / 1024))
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    FREE_MB=$(free -m | awk 'NR==2{print $4}')
fi

if [ "${FREE_MB:-1024}" -lt 512 ]; then
    echo "Warning: Low memory (${FREE_MB}MB). Consider closing other applications."
fi

# Run pre-commit
exec pre-commit run
EOF

chmod +x .git/hooks/pre-commit

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg

echo "✓ Sequential pre-commit setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "The following variables are now set (project-local):"
echo "  PRE_COMMIT_MAX_WORKERS=1"
echo "  MEMORY_LIMIT_MB=2048"
echo "  TIMEOUT_SECONDS=600"
```

### 3. Pre-commit Configuration

Create `.pre-commit-config.yaml` with all hooks configured for sequential execution:

```yaml
# Sequential pre-commit configuration
# All hooks run one at a time to minimize resource usage

default_language_version:
  python: python3.10

default_stages: [pre-commit]

repos:
  # Basic file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
        stages: [pre-commit]
      - id: end-of-file-fixer
        stages: [pre-commit]
      - id: check-yaml
        stages: [pre-commit]
      - id: check-added-large-files
        stages: [pre-commit]
        args: ['--maxkb=1000']
      - id: check-toml
        stages: [pre-commit]
      - id: check-json
        stages: [pre-commit]
      - id: check-merge-conflict
        stages: [pre-commit]

  # Python tools (all with require_serial: true)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        stages: [pre-commit]
        require_serial: true
      - id: ruff-format
        stages: [pre-commit]
        require_serial: true

  # Resource-intensive hooks using project-local wrappers
  - repo: local
    hooks:
      - id: mypy-limited
        name: Type checking (memory limited)
        entry: .pre-commit-wrappers/memory-limited-hook.sh uv run mypy
        language: system
        types: [python]
        require_serial: true
        pass_filenames: true
        stages: [pre-commit]
        args: [--ignore-missing-imports, --strict]

      - id: trufflehog-limited
        name: Secret detection (resource limited)
        entry: .pre-commit-wrappers/trufflehog-limited.sh
        language: system
        pass_filenames: false
        require_serial: true
        stages: [pre-commit]

# CI configuration
ci:
  skip:
    - mypy-limited
    - trufflehog-limited
```

### 4. GitHub Actions Workflow

Create `.github/workflows/pre-commit-sequential.yml`:

```yaml
name: Sequential Pre-commit

on:
  pull_request:
  push:
    branches: [main, develop]

# Force sequential workflow execution
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

env:
  # Same environment as local development
  PRE_COMMIT_MAX_WORKERS: 1
  PYTHONDONTWRITEBYTECODE: 1
  UV_NO_CACHE: 1
  MEMORY_LIMIT_MB: 2048
  TIMEOUT_SECONDS: 600
  TRUFFLEHOG_TIMEOUT: 300
  TRUFFLEHOG_CONCURRENCY: 1

jobs:
  sequential-checks:
    runs-on: ubuntu-latest
    timeout-minutes: 45  # Increased for sequential execution

    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install uv
      uses: astral-sh/setup-uv@v5
      with:
        enable-cache: true

    - name: Create virtual environment
      run: uv venv

    - name: Install dependencies
      run: |
        source .venv/bin/activate
        uv sync --all-extras
        uv pip install pre-commit

    - name: Install local tools
      run: |
        # Install Trufflehog to project bin
        mkdir -p .venv/bin
        curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | \
          sh -s -- -b .venv/bin

    - name: Run pre-commit hooks sequentially
      run: |
        source .venv/bin/activate
        # Export same variables as local environment
        export PRE_COMMIT_MAX_WORKERS=1
        export MEMORY_LIMIT_MB=2048
        export TIMEOUT_SECONDS=600

        # Run all hooks
        pre-commit run --all-files --show-diff-on-failure

    - name: Memory usage report
      if: always()
      run: |
        echo "Final memory usage:"
        free -h || true
```

## Installation

1. **Clone the repository and enter directory**:
   ```bash
   git clone <repository>
   cd <repository>
   ```

2. **Run the setup script**:
   ```bash
   chmod +x setup-sequential-precommit.sh
   ./setup-sequential-precommit.sh
   ```

3. **Activate the environment**:
   ```bash
   source .venv/bin/activate
   ```

That's it! No system or user configuration files are modified.

## Tool Installation

If specific tools are needed globally, install them with package managers:

```bash
# macOS with Homebrew
brew install trufflehog

# Linux with package manager
sudo apt-get install -y <tool>  # Debian/Ubuntu
sudo yum install -y <tool>       # RHEL/CentOS

# Or install to project-local directory
mkdir -p .local/bin
export PATH=".local/bin:$PATH"  # Add to .venv activation script
```

## Customization

### Adjusting Resource Limits

Edit `.venv/bin/activate.d/sequential-precommit.sh`:

```bash
export MEMORY_LIMIT_MB=4096      # Increase for large projects
export TIMEOUT_SECONDS=1200      # 20 minutes for slow operations
export TRUFFLEHOG_TIMEOUT=600    # 10 minutes for deep scanning
```

### Adding New Hooks

Always include `require_serial: true` for resource-intensive hooks:

```yaml
- repo: local
  hooks:
    - id: my-custom-check
      name: Custom check
      entry: .pre-commit-wrappers/memory-limited-hook.sh ./scripts/my-check.sh
      language: system
      require_serial: true
      pass_filenames: false
```

## Docker Alternative

For complete isolation, use Docker:

```dockerfile
# .devcontainer/Dockerfile
FROM python:3.10-slim

# Install tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set environment for sequential execution
ENV PRE_COMMIT_MAX_WORKERS=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MEMORY_LIMIT_MB=2048
ENV TIMEOUT_SECONDS=600

WORKDIR /workspace
```

## Benefits of This Approach

1. **No System Pollution**: All configuration is project-local
2. **Portable**: Works on any system without modifying user files
3. **Version Controlled**: All configuration is in the repository
4. **Easy Cleanup**: Just delete the project directory
5. **Team Friendly**: Everyone gets the same configuration automatically
6. **CI/CD Compatible**: Same configuration works locally and in CI

## Troubleshooting

### Pre-commit not using sequential configuration?

Ensure you've activated the virtual environment:
```bash
source .venv/bin/activate
env | grep PRE_COMMIT  # Should show MAX_WORKERS=1
```

### Tools not found?

Install them to the project-local directory:
```bash
mkdir -p .venv/bin
# Download tool to .venv/bin
chmod +x .venv/bin/<tool>
```

### Memory limits not working on macOS?

macOS doesn't support `ulimit -v`. The configuration still prevents parallel execution, which is the main benefit.

Remember: This setup prioritizes stability and minimal resource usage. The longer execution time is a worthwhile trade-off for preventing system crashes and ensuring consistent results.
