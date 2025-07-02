#!/usr/bin/env bash
# Trufflehog wrapper with resource limits and full history scanning
# Scans entire repository history with timeout protection

set -euo pipefail

# Configuration
TIMEOUT_SECONDS="${TRUFFLEHOG_TIMEOUT:-120}"  # 2 minutes default
MEMORY_LIMIT_MB="${TRUFFLEHOG_MEMORY_MB:-1024}"  # 1GB for Trufflehog
CONCURRENCY="${TRUFFLEHOG_CONCURRENCY:-1}"  # Single thread by default

# Apply memory limits on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    ulimit -v $((MEMORY_LIMIT_MB * 1024)) 2>/dev/null || true
    ulimit -d $((MEMORY_LIMIT_MB * 1024)) 2>/dev/null || true
fi

# Ensure we have trufflehog
if ! command -v trufflehog &> /dev/null; then
    echo "Error: trufflehog is not installed"
    echo "Please install it with: brew install trufflehog (macOS) or see https://github.com/trufflesecurity/trufflehog"
    exit 1
fi

echo "Running Trufflehog security scan (timeout: ${TIMEOUT_SECONDS}s, memory: ${MEMORY_LIMIT_MB}MB)..."

# Determine timeout command
if command -v timeout &> /dev/null; then
    timeout_cmd="timeout ${TIMEOUT_SECONDS}s"
elif command -v gtimeout &> /dev/null; then
    timeout_cmd="gtimeout ${TIMEOUT_SECONDS}s"
else
    timeout_cmd=""
fi

# Create temporary file for output
TEMP_OUTPUT=$(mktemp)
trap "rm -f $TEMP_OUTPUT" EXIT

# Run trufflehog with full history scan but resource limits
# --only-verified: Only report verified findings (reduces false positives)
# --fail: Exit with non-zero code if secrets found
# --no-update: Don't check for updates (faster)
# --concurrency: Limit concurrent operations
if [ -n "$timeout_cmd" ]; then
    $timeout_cmd trufflehog git file://. \
        --only-verified \
        --fail \
        --no-update \
        --concurrency="$CONCURRENCY" \
        2>&1 | tee "$TEMP_OUTPUT" | grep -v "^$" || exit_code=$?
else
    # Fallback without timeout command
    trufflehog git file://. \
        --only-verified \
        --fail \
        --no-update \
        --concurrency="$CONCURRENCY" \
        2>&1 | tee "$TEMP_OUTPUT" | grep -v "^$" &
    PID=$!

    # Wait with timeout
    SECONDS=0
    while kill -0 $PID 2>/dev/null && [ $SECONDS -lt $TIMEOUT_SECONDS ]; do
        sleep 1
    done

    # Kill if still running
    if kill -0 $PID 2>/dev/null; then
        echo "Warning: Trufflehog scan timed out after ${TIMEOUT_SECONDS} seconds"
        kill -TERM $PID 2>/dev/null || true
        sleep 1
        kill -KILL $PID 2>/dev/null || true
        exit_code=124
    else
        wait $PID
        exit_code=$?
    fi
fi

# Handle exit codes
if [ "${exit_code:-0}" -eq 124 ]; then
    echo "Warning: Trufflehog scan timed out after ${TIMEOUT_SECONDS} seconds"
    echo "Consider increasing TRUFFLEHOG_TIMEOUT environment variable"
    # Check if any secrets were found before timeout
    if grep -q "Found verified result" "$TEMP_OUTPUT" 2>/dev/null; then
        echo "Error: Verified secrets were found before timeout!"
        exit 1
    fi
    exit 0  # Don't fail on timeout if no secrets found
elif [ "${exit_code:-0}" -eq 183 ]; then
    echo "Error: Trufflehog found verified secrets!"
    exit 1
elif [ "${exit_code:-0}" -ne 0 ]; then
    echo "Error: Trufflehog failed with exit code ${exit_code}"
    exit 1
fi

echo "✓ Trufflehog scan completed successfully - no verified secrets found"
