#!/usr/bin/env bash
# Memory-limited wrapper for resource-intensive pre-commit hooks
# Prevents individual hooks from consuming excessive system resources

set -euo pipefail

# Configuration
MEMORY_LIMIT_MB="${MEMORY_LIMIT_MB:-2048}"  # 2GB default
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"   # 5 minutes default

# Parse command line
if [ $# -lt 1 ]; then
    echo "Usage: $0 <command> [args...]"
    exit 1
fi

COMMAND="$1"
shift

# Platform-specific memory limiting
apply_memory_limit() {
    local limit_mb="$1"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux: use ulimit (works well)
        ulimit -v $((limit_mb * 1024)) 2>/dev/null || true
        ulimit -d $((limit_mb * 1024)) 2>/dev/null || true
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: ulimit -v doesn't work reliably, use stack size limit
        ulimit -s 8192 2>/dev/null || true  # 8MB stack
        # Also set data segment limit
        ulimit -d $((limit_mb * 1024)) 2>/dev/null || true
    fi
}

# Cleanup on exit
cleanup() {
    local exit_code=$?

    # Kill any child processes
    pkill -P $$ 2>/dev/null || true

    # Force Python garbage collection
    if [[ "$COMMAND" == *"python"* ]] || [[ "$COMMAND" == *"uv"* ]]; then
        python3 -c "import gc; gc.collect()" 2>/dev/null || true
    fi

    # Clear Python cache if needed
    if [ -d "__pycache__" ]; then
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    fi

    return $exit_code
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Apply memory limit
apply_memory_limit "$MEMORY_LIMIT_MB"

# Disable Python bytecode generation to save memory
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Report what we're running
echo "Running (memory limited to ${MEMORY_LIMIT_MB}MB): $COMMAND $*"

# Execute command with timeout
if command -v timeout &> /dev/null; then
    exec timeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
elif command -v gtimeout &> /dev/null; then
    # macOS with coreutils
    exec gtimeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
else
    # Fallback for systems without timeout
    "$COMMAND" "$@" &
    PID=$!

    SECONDS=0
    while kill -0 $PID 2>/dev/null; do
        if [ $SECONDS -ge $TIMEOUT_SECONDS ]; then
            echo "Error: Command timeout after ${TIMEOUT_SECONDS} seconds"
            kill -TERM $PID 2>/dev/null || true
            sleep 1
            kill -KILL $PID 2>/dev/null || true
            exit 124
        fi
        sleep 1
    done

    wait $PID
fi
