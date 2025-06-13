#!/bin/bash
# User_interface module - Handles displaying help and potentially other UI elements.

# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of a modular system and cannot be executed directly." >&2
    echo "Please use the orchestrator script instead." >&2
    exit 1
fi

# Check if we're being sourced by the main script
if [[ -z "$DHTL_SESSION_ID" ]]; then
    echo "ERROR: This script is being sourced outside of dhtl. This is not supported." >&2
    return 1 2>/dev/null || exit 1
fi


# Display detailed help, potentially listing commands from modules.
# This is the canonical version. Relies on display_help_text in dhtl.sh for base.
show_help() {
    # Use the basic help text from dhtl.sh as a fallback or base
    if ! function_exists "display_help_text"; then
         echo "Usage: dhtl <command> [options]"
         echo "Run 'dhtl help' for more details (if modules loaded)."
         # Define a minimal basic help if display_help_text is missing
         echo "Basic Commands: init, setup, test_dht, help, version"
         return 0
    fi

    # Display the basic help first
    display_help_text

    # Add more details if needed, potentially by introspecting available functions
    # This part can be expanded later if dynamic command listing is desired.
    # For now, the basic help text in dhtl.sh is updated and sufficient.
    # Example of potential future expansion:
    # echo ""
    # echo "Detailed Commands (from loaded modules):"
    # compgen -A function | grep '_command$' | sed 's/_command$//' | grep -v '^_' | sort | while read cmd; do
    #    printf "  %-15s - (Description needed)\n" "$cmd"
    # done

    return 0
}

# NOTE: coverage_command removed (canonical version is in dhtl_commands_5.sh)

