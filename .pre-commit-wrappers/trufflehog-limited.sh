#!/usr/bin/env bash
# Trufflehog execution wrapper with timeout protection
# Maintains full security scanning while preventing infinite hangs

set -euo pipefail

echo "🔍 Running Trufflehog with timeout protection..."

# Set a timeout of 2 minutes for thorough scanning
# This allows full depth scanning while preventing infinite hangs
TIMEOUT_SECONDS=120

if [[ "$OSTYPE" == "darwin"* ]]; then
    # Use gtimeout if available (from coreutils), otherwise use a simple background process
    if command -v gtimeout &> /dev/null; then
        gtimeout ${TIMEOUT_SECONDS}s trufflehog git file://. --only-verified --fail --no-update
    else
        # Fallback: run in background and kill after timeout
        trufflehog git file://. --only-verified --fail --no-update &
        PID=$!

        # Wait up to timeout
        SECONDS=0
        while kill -0 $PID 2>/dev/null && [ $SECONDS -lt $TIMEOUT_SECONDS ]; do
            sleep 1
        done

        # Kill if still running
        if kill -0 $PID 2>/dev/null; then
            echo "⏱️  Trufflehog timeout after ${TIMEOUT_SECONDS} seconds"
            kill -TERM $PID 2>/dev/null || true
            sleep 1
            kill -KILL $PID 2>/dev/null || true
            exit 1
        fi

        # Get exit code
        wait $PID
    fi
else
    # Linux typically has timeout command
    timeout ${TIMEOUT_SECONDS}s trufflehog git file://. --only-verified --fail --no-update
fi

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ No verified secrets detected"
else
    echo "❌ Trufflehog check failed"
fi

exit $RESULT
