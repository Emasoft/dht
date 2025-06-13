#!/bin/bash
# dhtl_commands_8.sh - Commands_8 module for DHT Launcher
# Contains clean, get_python_cmd.

# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of dhtl and cannot be executed directly." >&2
    echo "Please use the main dhtl.sh script instead." >&2
    exit 1
fi

# Check if we're being sourced by the main script
if [[ -z "$DHTL_SESSION_ID" ]]; then
    echo "ERROR: This script is being sourced outside of dhtl. This is not supported." >&2
    return 1 2>/dev/null || exit 1
fi


# ===== Functions =====

# Clean DHT caches and temporary files
# This is the canonical version.
clean_command() {
    echo "🧹 Cleaning Development Helper Toolkit caches and temporary files..."

    # Clean cache directory (defined globally as CACHE_DIR)
    if [ -d "$CACHE_DIR" ] && [ -n "${CACHE_DIR}" ]; then
        echo "🗑️ Removing cache directory: $CACHE_DIR"
        # Use a safer approach to avoid path expansion issues
        find "${CACHE_DIR:?}" -mindepth 1 -delete 2>/dev/null || rm -rf "${CACHE_DIR:?}"/*
        mkdir -p "$CACHE_DIR" # Recreate the directory
    else
         echo "ℹ️ Cache directory not found or not set: $CACHE_DIR"
    fi

    # Clean guardian logs (defined globally as DHT_DIR)
    local guardian_internal_dir="$DHT_DIR/.process_guardian"
    if [ -d "$guardian_internal_dir" ] && [ -n "${DHT_DIR}" ]; then
        echo "🗑️ Removing guardian logs: $guardian_internal_dir"
        find "${guardian_internal_dir:?}" -mindepth 1 -delete 2>/dev/null || rm -rf "${guardian_internal_dir:?}"/*
        # Do not recreate here, guardian watchdog will do it if needed
    else
        echo "ℹ️ Guardian log directory not found: $guardian_internal_dir"
    fi

    # Clean diagnostics report
    local report_file="$DHT_DIR/.dht_environment_report.json"
     if [ -f "$report_file" ]; then
        echo "🗑️ Removing diagnostics report: $report_file"
        rm -f "$report_file"
    fi

    echo "✅ Cleaning complete."
    return 0
}

# NOTE: find_project_root removed, canonical version is in dhtl_environment_1.sh

# Get the preferred Python command (python3 or python)
# This is the canonical version.
get_python_cmd() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        # Return empty string and error code if neither is found
        echo ""
        return 1
    fi
    return 0
}

# NOTE: run_node_command removed. Canonical version is in dhtl_commands_standalone.sh (as node_command).
