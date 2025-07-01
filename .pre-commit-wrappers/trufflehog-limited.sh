#!/usr/bin/env bash
# Limited Trufflehog execution wrapper
# Reduces scan depth and adds timeout to prevent resource exhaustion

set -euo pipefail

echo "🔍 Running Trufflehog with resource limits..."

# Set a timeout of 30 seconds and limit scan depth
# Also limit memory usage
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Use gtimeout if available (from coreutils), otherwise use a simple background process
    if command -v gtimeout &> /dev/null; then
        gtimeout 30s trufflehog git file://. --since-commit HEAD~3 --only-verified --fail --no-update
    else
        # Fallback: run in background and kill after timeout
        trufflehog git file://. --since-commit HEAD~3 --only-verified --fail --no-update &
        PID=$!

        # Wait up to 30 seconds
        SECONDS=0
        while kill -0 $PID 2>/dev/null && [ $SECONDS -lt 30 ]; do
            sleep 1
        done

        # Kill if still running
        if kill -0 $PID 2>/dev/null; then
            echo "⏱️  Trufflehog timeout after 30 seconds"
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
    timeout 30s trufflehog git file://. --since-commit HEAD~3 --only-verified --fail --no-update
fi

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ No verified secrets detected"
else
    echo "❌ Trufflehog check failed"
fi

exit $RESULT
