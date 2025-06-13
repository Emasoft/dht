#!/bin/bash
# dhtl_diagnostics.sh - Diagnostics module for DHT Launcher
# Gathers system, project, and environment information by running the Python reporter script.

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

# --- Public Function ---

# Run all diagnostic checks and generate the report by executing the Python script.
# Saves report to DHT/.dht_environment_report.json
run_diagnostics() {
    echo "🩺 Running DHT Diagnostics via Python reporter..."
    local report_file="$DHT_DIR/.dht_environment_report.json"
    local reporter_script="$DHT_DIR/diagnostic_reporter.py"
    local venv_python="$DEFAULT_VENV_DIR/bin/python" # Use default venv path

    # Ensure DHT directory exists
    mkdir -p "$DHT_DIR"

    # Check if the Python reporter script exists
    if [[ ! -f "$reporter_script" ]]; then
        log_error "Diagnostic reporter script not found: $reporter_script" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi

    # Ensure the virtual environment Python exists
    if [[ ! -x "$venv_python" ]]; then
        if [[ -x "$DEFAULT_VENV_DIR/Scripts/python.exe" ]]; then # Windows Git Bash/WSL
            venv_python="$DEFAULT_VENV_DIR/Scripts/python.exe"
        else
            log_error "Python interpreter not found in virtual environment: $venv_python" $ERR_ENVIRONMENT
            log_error "Run 'dhtl setup' first."
            return $ERR_ENVIRONMENT
        fi
    fi

    # Prepare arguments for the Python script
    local reporter_args=("--output" "$report_file")
    if [[ "${DEBUG_MODE:-false}" == "true" ]]; then
        # Potentially add a debug flag to the python script later if needed
        : # No debug flag for reporter script yet
    fi
    # Add --include-secrets if needed (e.g., based on a dhtl flag)
    # For now, secrets are not included by default.

    # Execute the Python script using the virtual environment's Python
    # Use run_with_guardian to manage the Python process
    echo "🔄 Executing Python diagnostics reporter: $reporter_script"
    run_with_guardian "$venv_python" "python" "$PYTHON_MEM_LIMIT" "$reporter_script" "${reporter_args[@]}"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        if [[ -f "$report_file" ]]; then
            log_success "Diagnostics complete. Report saved to: $report_file"
            # Optionally, validate the JSON here using jq if available
            if command -v jq &>/dev/null; then
                if jq -e . "$report_file" > /dev/null; then
                    log_debug "JSON report validated successfully with jq."
                else
                    log_warning "Generated JSON report failed validation with jq."
                fi
            fi
            return 0
        else
            log_error "Python reporter script ran successfully but did not create the report file: $report_file" $ERR_UNEXPECTED
            return $ERR_UNEXPECTED
        fi
    else
        log_error "Python diagnostics reporter failed with exit code $exit_code." $ERR_UNEXPECTED
        return $exit_code
    fi
}

# Command alias for running diagnostics
diagnostics_command() {
    run_diagnostics
    return $?
}
