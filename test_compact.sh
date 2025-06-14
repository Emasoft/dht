#!/bin/bash
# Compact test runner to avoid token limit issues

# Set environment for minimal output
export PREFECT_LOGGING_LEVEL=ERROR
export PYTHONWARNINGS=ignore
export PYTEST_CURRENT_TEST=""

# Function to run tests with compact output
run_compact_tests() {
    echo "Running tests with compact output..."
    echo "=================================="
    
    # Run pytest with minimal output
    python -m pytest \
        -q \
        --tb=no \
        --no-header \
        --disable-warnings \
        --capture=no \
        -p no:terminal \
        -p pytest_summary \
        --co -q 2>/dev/null | wc -l | xargs -I {} echo "Found {} tests"
    
    # Actually run the tests
    python -m pytest \
        -q \
        --tb=no \
        --no-header \
        --disable-warnings \
        --capture=no \
        -p no:terminal \
        -p pytest_summary \
        "$@" 2>&1 | grep -E "(PASSED|FAILED|SKIPPED|ERROR|DHT Test Summary|Total Tests|✅|❌|⏩|===)" || true
    
    # Check if error log has content
    if [ -f "test_errors.log" ] && [ -s "test_errors.log" ]; then
        echo ""
        echo "⚠️  Errors logged to test_errors.log ($(wc -l < test_errors.log) lines)"
    fi
}

# Run with any passed arguments
run_compact_tests "$@"