#!/usr/bin/env bash
# Wrapper to run hooks with memory limits and cleanup

set -euo pipefail

# Get the command to run
COMMAND="$1"
shift

# Function to cleanup before exit
cleanup() {
    # Force Python garbage collection if Python command
    if [[ "$COMMAND" == *"python"* ]] || [[ "$COMMAND" == *"uv"* ]]; then
        python3 -c "import gc; gc.collect()" 2>/dev/null || true
    fi
    
    # Small delay to allow memory reclamation
    sleep 0.5
}

# Set up cleanup trap
trap cleanup EXIT

# Report current memory usage
echo "Running: $COMMAND $*"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Set memory limit (2GB)
    ulimit -v 2097152 2>/dev/null || true
fi

# Execute the command
exec "$COMMAND" "$@"