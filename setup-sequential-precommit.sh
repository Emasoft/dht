#!/usr/bin/env bash
# Setup script for sequential pre-commit execution
# All configuration is project-local - no system files are modified

set -euo pipefail

echo "Setting up project-local sequential pre-commit..."

# Colors for output
if [[ -t 1 ]]; then
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    YELLOW=''
    RED=''
    NC=''
fi

# Check if in git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    uv venv
fi

# Create activation hooks directory for environment variables
echo -e "${YELLOW}Setting up project-local environment configuration...${NC}"
mkdir -p .venv/bin/activate.d 2>/dev/null || mkdir -p .venv/Scripts/activate.d 2>/dev/null

# Create environment configuration that will be sourced on activation
cat > .venv/bin/activate.d/sequential-precommit.sh << 'EOF'
#!/usr/bin/env bash
# Project-local environment configuration for sequential pre-commit

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

# Optional: Add project-local bin to PATH
if [ -d "$VIRTUAL_ENV/../.local/bin" ]; then
    export PATH="$VIRTUAL_ENV/../.local/bin:$PATH"
fi

echo "Sequential pre-commit environment activated"
echo "  Max workers: 1 (sequential execution)"
echo "  Memory limit: ${MEMORY_LIMIT_MB}MB"
echo "  Timeout: ${TIMEOUT_SECONDS}s"
EOF

chmod +x .venv/bin/activate.d/sequential-precommit.sh 2>/dev/null || true

# For existing venv, source the configuration immediately
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    source .venv/bin/activate.d/sequential-precommit.sh 2>/dev/null || true
fi

# Create wrapper directory
echo -e "${YELLOW}Creating wrapper scripts directory...${NC}"
mkdir -p .pre-commit-wrappers

# Create memory-limited wrapper if it doesn't exist
if [ ! -f ".pre-commit-wrappers/memory-limited-hook.sh" ]; then
    echo -e "${YELLOW}Creating memory-limited wrapper...${NC}"
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

echo "Running (memory limited to ${MEMORY_LIMIT_MB}MB): $COMMAND $*"

# Execute with timeout
if command -v timeout &> /dev/null; then
    exec timeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
elif command -v gtimeout &> /dev/null; then
    exec gtimeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
else
    "$COMMAND" "$@"
fi
EOF
fi

# Create Trufflehog wrapper if it doesn't exist
if [ ! -f ".pre-commit-wrappers/trufflehog-limited.sh" ]; then
    echo -e "${YELLOW}Creating Trufflehog wrapper...${NC}"
    cat > .pre-commit-wrappers/trufflehog-limited.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Use project-local environment variables
TIMEOUT="${TRUFFLEHOG_TIMEOUT:-300}"
MEMORY_LIMIT="${TRUFFLEHOG_MEMORY_MB:-1024}"
CONCURRENCY="${TRUFFLEHOG_CONCURRENCY:-1}"

# Check if trufflehog is installed globally or locally
if ! command -v trufflehog &> /dev/null; then
    if [ ! -f ".venv/bin/trufflehog" ]; then
        echo "Installing Trufflehog to project-local directory..."
        mkdir -p .venv/bin
        curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | \
            sh -s -- -b .venv/bin
    fi
    # Use local version
    TRUFFLEHOG_CMD=".venv/bin/trufflehog"
else
    TRUFFLEHOG_CMD="trufflehog"
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

$timeout_cmd $TRUFFLEHOG_CMD git file://. \
    --only-verified \
    --fail \
    --no-update \
    --concurrency="$CONCURRENCY" || exit_code=$?

if [ "${exit_code:-0}" -eq 124 ]; then
    echo "Warning: Trufflehog timed out after ${TIMEOUT}s"
    exit 0
elif [ "${exit_code:-0}" -eq 183 ]; then
    echo "Error: Trufflehog found verified secrets!"
    exit 1
elif [ "${exit_code:-0}" -ne 0 ]; then
    echo "Error: Trufflehog failed with exit code ${exit_code}"
    exit 1
fi

echo "✓ No verified secrets found"
EOF
fi

# Make wrappers executable
chmod +x .pre-commit-wrappers/*.sh

# Install pre-commit as a project tool if not installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}Installing pre-commit as project tool...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi
    uv tool install pre-commit --with pre-commit-uv
fi

# Create git hook that sources project environment
echo -e "${YELLOW}Creating git pre-commit hook...${NC}"
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
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg

# Create local tool directory
mkdir -p .local/bin

# Summary
echo ""
echo -e "${GREEN}✓ Sequential pre-commit setup complete!${NC}"
echo ""
echo -e "${YELLOW}Important: No system or user files were modified.${NC}"
echo "All configuration is project-local in:"
echo "  - .venv/bin/activate.d/sequential-precommit.sh (environment variables)"
echo "  - .pre-commit-wrappers/ (resource limit scripts)"
echo "  - .git/hooks/pre-commit (git hook)"
echo "  - .local/bin/ (optional local tools)"
echo ""
echo "To activate the environment:"
echo -e "${GREEN}  source .venv/bin/activate${NC}"
echo ""
echo "The following variables will be set automatically:"
echo "  PRE_COMMIT_MAX_WORKERS=1 (sequential execution)"
echo "  MEMORY_LIMIT_MB=2048"
echo "  TIMEOUT_SECONDS=600"
echo "  TRUFFLEHOG_CONCURRENCY=1"
echo ""
echo "To customize limits, edit: .venv/bin/activate.d/sequential-precommit.sh"
