#!/bin/bash
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Restored original shell-based entry point for DHT
# - Maintains compatibility with existing workflows
# - Properly delegates to Python launcher when installed
# - Follows UV-compatible architecture
# 

set -euo pipefail

# DHT Main Entry Point (Shell Script)
# This is the primary entry point for DHT on Unix-like systems
# It delegates to the Python launcher while maintaining shell-based architecture

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DHT_ROOT="$SCRIPT_DIR"

# Check if we're in development mode (src/ structure) or installed mode
if [[ -f "$DHT_ROOT/src/DHT/dhtl.py" ]]; then
    # Development mode - use src structure
    DHTL_PYTHON="$DHT_ROOT/src/DHT/dhtl.py"
    export DHTL_DEV_MODE=1
elif [[ -f "$DHT_ROOT/DHT/dhtl.py" ]]; then
    # Legacy mode - direct structure
    DHTL_PYTHON="$DHT_ROOT/DHT/dhtl.py"
    export DHTL_DEV_MODE=1
else
    # Try installed dhtl command
    if command -v dhtl &> /dev/null; then
        exec dhtl "$@"
    else
        echo "❌ Error: DHT launcher not found" >&2
        echo "Please ensure DHT is properly installed or run from the correct directory" >&2
        exit 1
    fi
fi

# Set environment variables for shell modules
export DHT_ROOT
export SCRIPT_DIR
export DHTL_SHELL_ENTRY=1

# Use Python to run the launcher
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    # Use activated virtual environment
    exec python "$DHTL_PYTHON" "$@"
elif command -v python3 &> /dev/null; then
    exec python3 "$DHTL_PYTHON" "$@"
elif command -v python &> /dev/null; then
    exec python "$DHTL_PYTHON" "$@"
else
    echo "❌ Error: Python not found" >&2
    echo "Please install Python 3.10+ or activate a virtual environment" >&2
    exit 1
fi