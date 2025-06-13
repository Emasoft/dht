#!/bin/bash
# dhtl_environment_2.sh - Environment_2 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to environment_2 functionality.
# It is sourced by the main dhtl.sh orchestrator and should not be modified manually.
# To make changes, modify the original dhtl.sh and regenerate the modules.
#
# DO NOT execute this file directly.


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

# Display environment information by reading the JSON report
# This is the canonical version of env_command.
env_command() {
    local report_file="$DHT_DIR/.dht_environment_report.json"

    # Ensure diagnostics run first to generate/update the report
    if ! run_diagnostics; then
        log_error "Failed to generate diagnostics report. Cannot display environment info." $ERR_GENERAL
        return $ERR_GENERAL
    fi

    if [[ ! -f "$report_file" ]]; then
        log_error "Diagnostics report file not found: $report_file" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi

    echo "📊 Development Helper Toolkit Environment Information (from report)"
    echo "================================================================="

    # Check if jq is available for pretty printing
    if command -v jq &>/dev/null; then
        # Use jq to format and display the report
        jq '.' "$report_file"
    else
        # Fallback to simple cat if jq is not available
        log_warning "jq command not found. Displaying raw JSON report."
        cat "$report_file"
    fi

    return 0
}

# NOTE: find_virtual_env removed. Canonical version is in environment.sh
# NOTE: setup_command removed. Canonical version is in dhtl_init.sh
# NOTE: setup_environment removed. Canonical logic is in dhtl_init.sh (setup_uv).
# NOTE: venv_command removed. Redundant with 'dhtl setup' or needs significant rework to use canonical functions.
