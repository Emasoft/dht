#!/bin/bash
# Orchestrator for dhtl.sh (basic version for new projects)

SCRIPT_DIR="$( cd -- "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Import essential modules (adjust list if essential_modules changes)
source "$SCRIPT_DIR/dhtl_error_handling.sh"
source "$SCRIPT_DIR/dhtl_environment_1.sh"
source "$SCRIPT_DIR/dhtl_environment_3.sh"
source "$SCRIPT_DIR/environment.sh"
source "$SCRIPT_DIR/dhtl_utils.sh"
source "$SCRIPT_DIR/dhtl_guardian_1.sh"
source "$SCRIPT_DIR/dhtl_guardian_2.sh"
source "$SCRIPT_DIR/dhtl_guardian_command.sh"
source "$SCRIPT_DIR/dhtl_uv.sh"
source "$SCRIPT_DIR/dhtl_diagnostics.sh"
source "$SCRIPT_DIR/dhtl_secrets.sh"
source "$SCRIPT_DIR/dhtl_init.sh"
source "$SCRIPT_DIR/user_interface.sh"
source "$SCRIPT_DIR/dhtl_commands_1.sh" # restore
source "$SCRIPT_DIR/dhtl_commands_8.sh" # clean
source "$SCRIPT_DIR/dhtl_environment_2.sh" # env
source "$SCRIPT_DIR/dhtl_commands_standalone.sh" # script, python, node, run
source "$SCRIPT_DIR/dhtl_test.sh" # test_dht, verify_dht
source "$SCRIPT_DIR/dhtl_version.sh" # tag, bump

# Add other command modules
source "$SCRIPT_DIR/dhtl_commands_2.sh" # test
source "$SCRIPT_DIR/dhtl_commands_3.sh" # lint
source "$SCRIPT_DIR/dhtl_commands_4.sh" # format
source "$SCRIPT_DIR/dhtl_commands_5.sh" # coverage
source "$SCRIPT_DIR/dhtl_commands_6.sh" # commit
source "$SCRIPT_DIR/dhtl_commands_7.sh" # build, publish

# GitHub integration
source "$SCRIPT_DIR/dhtl_github.sh" # clone, fork, GitHub operations
source "$SCRIPT_DIR/dhtl_commands_workflows.sh" # workflows lint, run, run-in-container - GitHub Actions testing
# Keep old act commands for compatibility
source "$SCRIPT_DIR/dhtl_commands_act.sh" # act - deprecated, use workflows command
