# Sequential Pre-commit Setup Guide

This guide provides a universal solution for configuring pre-commit hooks to run sequentially, preventing system resource exhaustion and conflicts in any Python project.

## Why Sequential Execution

Parallel pre-commit hooks can cause:
- Memory exhaustion from concurrent linters/formatters
- File access conflicts when multiple tools modify the same files
- Git operation conflicts from simultaneous operations
- System crashes on resource-constrained machines
- Unpredictable hook execution order

Sequential execution ensures predictable, stable operations at the cost of slightly longer commit times.

## Prerequisites

- Python 3.8+ with `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git repository initialized
- Basic understanding of pre-commit hooks

## Environment Setup

Set these environment variables in your shell profile (`~/.bashrc`, `~/.zshrc`, or equivalent):

```bash
# Force pre-commit to run hooks sequentially
export PRE_COMMIT_MAX_WORKERS=1

# Prevent Python bytecode generation to save memory
export PYTHONDONTWRITEBYTECODE=1

# Optional: Disable caching during hooks
export UV_NO_CACHE=1  # For uv operations
export PRE_COMMIT_NO_CONCURRENCY=1  # Additional safety
```

## Core Configuration Files

### 1. Pre-commit Configuration Template

Create `.pre-commit-config.yaml` with sequential execution enforced:

```yaml
# Sequential pre-commit configuration
# Prevents resource exhaustion by running hooks one at a time

# Set Python version (adjust as needed)
default_language_version:
  python: python3.10  # Change to your project's Python version

# Force sequential stages
default_stages: [pre-commit]

repos:
  # Basic file checks (lightweight, run first)
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0  # Check for latest version
    hooks:
      - id: trailing-whitespace
        stages: [pre-commit]
      - id: end-of-file-fixer
        stages: [pre-commit]
      - id: check-yaml
        stages: [pre-commit]
      - id: check-added-large-files
        stages: [pre-commit]
        args: ['--maxkb=1000']  # Adjust size limit as needed
      - id: check-toml
        stages: [pre-commit]
      - id: check-json
        stages: [pre-commit]
      - id: check-merge-conflict
        stages: [pre-commit]

  # Python-specific hooks (choose based on your project needs)
  
  # Option A: If using uv for dependency management
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.7.13  # Check for latest version
    hooks:
      - id: uv-lock
        args: [--locked]
        stages: [pre-commit]
        require_serial: true
        # Add this hook only if you use uv for dependencies

  # Option B: If using ruff for linting/formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.4  # Check for latest version
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        stages: [pre-commit]
        require_serial: true
      - id: ruff-format
        stages: [pre-commit]
        require_serial: true

  # Option C: If using black for formatting
  # - repo: https://github.com/psf/black
  #   rev: 24.10.0  # Check for latest version
  #   hooks:
  #     - id: black
  #       stages: [pre-commit]
  #       require_serial: true

  # Resource-intensive hooks with memory protection
  - repo: local
    hooks:
      # Type checking (if using mypy)
      - id: mypy-limited
        name: Type checking (memory limited)
        entry: bash -c 'ulimit -v 2097152 2>/dev/null; uv run mypy "$@"' --
        language: system
        types: [python]
        require_serial: true
        pass_filenames: true
        stages: [pre-commit]
        # Customize mypy args as needed
        args: [--ignore-missing-imports, --strict]

      # Custom project-specific checks
      - id: custom-checks
        name: Project-specific checks
        entry: bash -c 'YOUR_CUSTOM_SCRIPT_HERE'
        language: system
        require_serial: true
        stages: [pre-commit]
        # Replace YOUR_CUSTOM_SCRIPT_HERE with your checks

  # Security scanning (if needed)
  - repo: local
    hooks:
      - id: security-scan
        name: Security scanning
        # Option 1: Using bandit
        entry: bash -c 'timeout 60s uv run bandit -r . -ll'
        # Option 2: Using safety
        # entry: bash -c 'timeout 60s uv run safety check'
        language: system
        pass_filenames: false
        require_serial: true
        stages: [pre-commit]

# CI-specific configuration
ci:
  # Skip resource-intensive hooks in CI if needed
  skip:
    - mypy-limited  # Often run in separate CI job
    - security-scan  # Often run in security-specific workflow
```

### 2. Memory-Limited Wrapper Script

Create `.pre-commit-scripts/memory-limit-wrapper.sh`:

```bash
#!/usr/bin/env bash
# Universal memory-limited command wrapper
# Prevents individual hooks from consuming excessive resources

set -euo pipefail

# Configuration
DEFAULT_MEMORY_LIMIT_MB="${MEMORY_LIMIT_MB:-2048}"  # 2GB default
DEFAULT_TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"   # 5 minutes default

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <command> [args...]"
    exit 1
fi

COMMAND="$1"
shift

# Platform-specific memory limiting
limit_memory() {
    local limit_mb="$1"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux: use ulimit
        ulimit -v $((limit_mb * 1024)) 2>/dev/null || true
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: ulimit -v doesn't work well, use alternative
        # Note: This is informational only on macOS
        echo "Memory limit: ${limit_mb}MB (informational on macOS)"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows: Limited support
        echo "Memory limit: ${limit_mb}MB (limited support on Windows)"
    fi
}

# Cleanup function
cleanup() {
    # Kill any child processes
    pkill -P $$ 2>/dev/null || true
    
    # Force garbage collection if Python
    if [[ "$COMMAND" == *"python"* ]] || [[ "$COMMAND" == *"uv"* ]]; then
        python3 -c "import gc; gc.collect()" 2>/dev/null || true
    fi
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Apply memory limit
limit_memory "$DEFAULT_MEMORY_LIMIT_MB"

# Execute command with timeout
if command -v timeout &> /dev/null; then
    timeout "$DEFAULT_TIMEOUT_SECONDS" "$COMMAND" "$@"
else
    # Fallback for systems without timeout command
    "$COMMAND" "$@" &
    PID=$!
    
    # Simple timeout implementation
    SECONDS=0
    while kill -0 $PID 2>/dev/null; do
        if [ $SECONDS -ge $DEFAULT_TIMEOUT_SECONDS ]; then
            echo "Command timeout after ${DEFAULT_TIMEOUT_SECONDS} seconds"
            kill -TERM $PID 2>/dev/null || true
            sleep 1
            kill -KILL $PID 2>/dev/null || true
            exit 124
        fi
        sleep 1
    done
    
    wait $PID
fi
```

### 3. Sequential Execution Wrapper

Create `.pre-commit-scripts/sequential-wrapper.sh`:

```bash
#!/usr/bin/env bash
# Ensures truly sequential execution with resource cleanup between hooks

set -euo pipefail

# Colors for output (optional)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# System information
echo -e "${GREEN}Sequential pre-commit execution starting...${NC}"
echo "System: $(uname -s) $(uname -m)"
echo "Python: $(python3 --version 2>&1)"
echo "Git: $(git --version 2>&1)"

# Check available memory
check_memory() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        local free_pages=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        local page_size=$(pagesize)
        local free_mb=$((free_pages * page_size / 1024 / 1024))
        echo "Free memory: ${free_mb}MB"
        
        if [ "$free_mb" -lt 1024 ]; then
            echo -e "${YELLOW}Warning: Low memory available${NC}"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        local free_mb=$(free -m | awk 'NR==2{print $4}')
        echo "Free memory: ${free_mb}MB"
        
        if [ "$free_mb" -lt 1024 ]; then
            echo -e "${YELLOW}Warning: Low memory available${NC}"
        fi
    fi
}

# Clear system caches (platform-specific)
clear_caches() {
    echo -e "${YELLOW}Clearing caches...${NC}"
    
    # Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Force garbage collection
    python3 -c "import gc; gc.collect()" 2>/dev/null || true
    
    # Sync filesystem
    sync
    
    # Small delay for system cleanup
    sleep 1
}

# Main execution
check_memory
echo ""

# Set sequential environment
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1

# Run pre-commit with all arguments
echo -e "${GREEN}Running pre-commit hooks sequentially...${NC}"
pre-commit "$@"
RESULT=$?

# Cleanup
clear_caches
check_memory

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All hooks passed${NC}"
else
    echo -e "${RED}✗ Some hooks failed${NC}"
fi

exit $RESULT
```

### 4. Git Hook Installation

Create `.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
# Git pre-commit hook with sequential execution

# Determine project root
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT" || exit 1

# Use sequential wrapper if available, fallback to direct execution
if [ -x ".pre-commit-scripts/sequential-wrapper.sh" ]; then
    exec .pre-commit-scripts/sequential-wrapper.sh run
else
    # Fallback: direct execution with environment vars
    export PRE_COMMIT_MAX_WORKERS=1
    export PYTHONDONTWRITEBYTECODE=1
    exec pre-commit run
fi
```

## Installation Steps

1. **Install pre-commit via uv**:
   ```bash
   uv tool install pre-commit --with pre-commit-uv
   ```

2. **Create script directory**:
   ```bash
   mkdir -p .pre-commit-scripts
   chmod +x .pre-commit-scripts/*.sh
   ```

3. **Copy configuration files** from this guide to your project

4. **Make scripts executable**:
   ```bash
   chmod +x .pre-commit-scripts/*.sh
   chmod +x .git/hooks/pre-commit
   ```

5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Customization Guide

### Project-Specific Adjustments

1. **Python Version**: Update `default_language_version` in `.pre-commit-config.yaml`

2. **Memory Limits**: Adjust in wrapper scripts:
   ```bash
   export MEMORY_LIMIT_MB=4096  # 4GB for larger projects
   export TIMEOUT_SECONDS=600    # 10 minutes for complex checks
   ```

3. **Tool Selection**: Comment/uncomment hooks based on your toolchain:
   - Using `black` instead of `ruff-format`? Swap the configurations
   - Not using type checking? Remove the mypy hook
   - Need additional linters? Add them with `require_serial: true`

### Local vs CI Environments

For CI environments, modify `.pre-commit-config.yaml`:

```yaml
ci:
  # CI-specific settings
  skip:
    - mypy-limited      # Run in separate job
    - security-scan     # Run in security workflow
  
  # Or use different commands for CI
  # Example: lighter checks in CI
  autofix_prs: false    # Prevent automatic fixes in PRs
```

### Without GitHub Actions

If not using GitHub Actions, create a local test script:

```bash
#!/usr/bin/env bash
# run-checks.sh - Sequential checks without pre-commit

set -euo pipefail

echo "Running sequential checks..."

# Format check
echo "1. Formatting..."
uv run ruff format --check . || exit 1

# Lint
echo "2. Linting..."
uv run ruff check . || exit 1

# Type check
echo "3. Type checking..."
uv run mypy . || exit 1

# Tests
echo "4. Testing..."
uv run pytest || exit 1

echo "✓ All checks passed"
```

## Troubleshooting

### Still experiencing crashes?

1. **Further reduce parallelism**:
   ```bash
   export PRE_COMMIT_MAX_WORKERS=0  # Absolute sequential
   ```

2. **Skip heavy hooks locally**:
   ```bash
   SKIP=mypy,security-scan git commit -m "message"
   ```

3. **Run hooks individually**:
   ```bash
   pre-commit run trailing-whitespace --all-files
   pre-commit run ruff --all-files
   ```

### Platform-Specific Issues

- **macOS**: `ulimit -v` doesn't enforce hard limits. Monitor Activity Monitor during commits.
- **Windows**: Use WSL2 or Git Bash for better compatibility.
- **Linux**: May need to adjust `/etc/security/limits.conf` for ulimit to work.

## Performance Optimization

While sequential execution is slower, you can optimize:

1. **Run only on changed files** (default behavior)
2. **Use `.pre-commit-config.yaml` `files` patterns** to limit hook scope
3. **Cache tool installations** with uv's built-in caching
4. **Skip unchanged hooks** with `--no-verify` for emergency commits

## Migration from Parallel Setup

1. **Backup current configuration**:
   ```bash
   cp .pre-commit-config.yaml .pre-commit-config.yaml.parallel-backup
   ```

2. **Apply this guide's configuration**

3. **Test with a small commit** before large changes

4. **Revert if needed**:
   ```bash
   cp .pre-commit-config.yaml.parallel-backup .pre-commit-config.yaml
   pre-commit install --force
   ```

Remember: Sequential execution trades speed for stability. In most cases, the additional commit time (30-60s vs 10-30s) is worth the reliability gained.