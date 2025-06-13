#!/bin/bash
#

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of dhtl and cannot be executed directly." >&2
    echo "Please use the main dhtl.sh script instead." >&2
    exit 1
fi

if [[ -z "$DHTL_SESSION_ID" ]]; then
    echo "ERROR: This script is being sourced outside of dhtl. This is not supported." >&2
    return 1 2>/dev/null || exit 1
fi

test_dht_command() {
    echo "🧪 Testing the DHT toolkit..."
    
    # Process arguments
    local test_path="$DHT_DIR/tests"
    local test_pattern="test_*.py"
    local extra_args=()
    local unit_only=false
    local integration_only=false
    local report=false
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --unit)
                unit_only=true
                shift
                ;;
            --integration)
                integration_only=true
                shift
                ;;
            --pattern)
                test_pattern="$2"
                shift 2
                ;;
            --path)
                test_path="$2"
                shift 2
                ;;
            --report)
                report=true
                shift
                ;;
            --)
                shift
                extra_args=("$@")
                break
                ;;
            *)
                extra_args+=("$1")
                shift
                ;;
        esac
    done
    
    # Configure test paths based on options
    if [[ "$unit_only" = true && "$integration_only" = false ]]; then
        test_path="$DHT_DIR/tests/unit"
    elif [[ "$unit_only" = false && "$integration_only" = true ]]; then
        test_path="$DHT_DIR/tests/integration"
    fi
    
    # Check if pytest is available
    local pytest_cmd=""
    if [[ -f "$PROJECT_ROOT/.venv/bin/pytest" ]]; then
        pytest_cmd="$PROJECT_ROOT/.venv/bin/pytest"
    elif command -v pytest &> /dev/null; then
        pytest_cmd="pytest"
    else
        log_error "pytest not found. Please install it in the virtual environment ('dhtl setup')." $ERR_COMMAND_NOT_FOUND
        return $ERR_COMMAND_NOT_FOUND
    fi
    
    # Prepare pytest arguments
    local pytest_args=("-v")
    
    # Add coverage reporting if requested
    if [[ "$report" = true ]]; then
        # Check if pytest-cov is available
        if "$pytest_cmd" --help | grep -q 'cov'; then # Basic check
            pytest_args+=("--cov=$DHT_DIR/modules" "--cov-report=term" "--cov-report=html:$DHT_DIR/coverage_report")
            echo "🔄 Generating coverage report..."
        else
            echo "⚠️ pytest-cov not found. Install it for coverage reporting:"
            echo "   uv pip install pytest-cov"
        fi
    fi
    
    # Add pattern and path
    pytest_args+=("$test_path" "-k" "$test_pattern")
    
    # Add any extra arguments
    if [[ ${#extra_args[@]} -gt 0 ]]; then
        pytest_args+=("${extra_args[@]}")
    fi
    
    # Run the tests
    echo "🔄 Running DHT tests: $pytest_cmd ${pytest_args[*]}"
    "$pytest_cmd" "${pytest_args[@]}"
    local exit_code=$?
    
    # Report results
    if [[ $exit_code -eq 0 ]]; then
        echo "✅ All tests passed successfully."
    else
        echo "❌ Tests failed with exit code $exit_code."
    fi
    
    # Show coverage report path if generated
    if [[ "$report" = true && $exit_code -eq 0 ]]; then
        echo "📊 Coverage report saved to: $DHT_DIR/coverage_report/index.html"
    fi
    
    return $exit_code
}

verify_dht_command() {
    echo "🔍 Verifying DHT installation..."
    
    # Check DHT directory structure
    if [[ ! -d "$DHT_DIR" ]]; then
        log_error "DHT directory not found: $DHT_DIR" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi
    
    # Check essential modules
    local missing_modules=0
    local modules_dir="$DHT_DIR/modules"
    # Updated list of required modules
    local required_modules=(
        "orchestrator.sh"
        "dhtl_error_handling.sh"
        "dhtl_environment_1.sh"
        "dhtl_environment_3.sh"
        "environment.sh"
        "dhtl_utils.sh"
        "dhtl_guardian_1.sh"
        "dhtl_guardian_2.sh"
        "dhtl_guardian_command.sh"
        "dhtl_uv.sh"
        "dhtl_diagnostics.sh"
        "dhtl_secrets.sh"
        "dhtl_init.sh"
        "user_interface.sh"
        "dhtl_commands_1.sh"
        "dhtl_commands_2.sh"
        "dhtl_commands_3.sh"
        "dhtl_commands_4.sh"
        "dhtl_commands_5.sh"
        "dhtl_commands_6.sh"
        "dhtl_commands_7.sh"
        "dhtl_commands_8.sh"
        "dhtl_commands_standalone.sh"
        "dhtl_test.sh"
        "dhtl_version.sh"
        "dhtl_environment_2.sh"
    )
    
    echo "🔄 Checking required modules..."
    for module in "${required_modules[@]}"; do
        if [[ ! -f "$modules_dir/$module" ]]; then
            log_error "Missing module: $module" $ERR_FILE_NOT_FOUND
            missing_modules=$((missing_modules + 1))
        else
            log_success "Found module: $module"
        fi
    done
    
    # Check DHT launcher
    if [[ ! -f "$PROJECT_ROOT/dhtl.sh" ]]; then
        log_error "DHT launcher not found: $PROJECT_ROOT/dhtl.sh" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    else
        log_success "Found DHT launcher: $PROJECT_ROOT/dhtl.sh"
    fi
    
    # Check whether launcher is executable
    if [[ ! -x "$PROJECT_ROOT/dhtl.sh" ]]; then
        log_warning "DHT launcher is not executable"
        log_info "🔄 Making launcher executable..."
        chmod +x "$PROJECT_ROOT/dhtl.sh"
    fi
    
    # Check venv directory
    if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
        log_warning "Virtual environment not found: $PROJECT_ROOT/.venv"
        log_info "   Run 'dhtl setup' to create a virtual environment."
    else
        log_success "Found virtual environment: $PROJECT_ROOT/.venv"
    fi
    
    # Check git integration
    if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
        log_warning "Git repository not found"
        log_info "   Run 'git init' to initialize a Git repository."
    else
        log_success "Found Git repository"
    fi
    
    # Report result
    if [[ $missing_modules -gt 0 ]]; then
        log_error "Missing $missing_modules required modules." $ERR_FILE_NOT_FOUND
        log_info "   Run 'dhtl init' to rebuild the DHT structure."
        return $ERR_FILE_NOT_FOUND
    else
        log_success "DHT installation verified successfully."
        return 0
    fi
}
