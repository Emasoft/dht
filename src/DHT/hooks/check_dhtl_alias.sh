#!/bin/bash
# check_dhtl_alias.sh - Pre-commit hook to enforce dhtl alias consistency
#
# This hook checks all shell scripts in the DHT directory to ensure they:
# 1. Have direct execution prevention blocks
# 2. Use the proper dhtl alias (not ./dhtl.sh) in all references
# 3. Have consistent error messages
#
# Usage: This script is called by pre-commit framework

set -eo pipefail

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
DHT_DIR="$PROJECT_ROOT/DHT"

# Initialize error counter
ERRORS=0

# ANSI color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NORMAL='\033[0m'

# Function to print error message and increment error counter
print_error() {
    echo -e "${RED}ERROR:${NORMAL} $1" >&2
    ERRORS=$((ERRORS + 1))
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}WARNING:${NORMAL} $1" >&2
}

# Function to print info message
print_info() {
    echo -e "${BLUE}INFO:${NORMAL} $1"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✅ SUCCESS:${NORMAL} $1"
}

# Check if a shell script has the execution prevention block
check_execution_prevention() {
    local script_path="$1"
    
    # Skip special scripts that should be executable
    if [[ "$script_path" == *"dhtl.sh" || "$script_path" == *"add_direct_execution_check.sh" || 
          "$script_path" == *"update_aliases"* || "$script_path" == *"hooks/"* ]]; then
        return 0
    fi
    
    # Check if the script has the prevention block
    if ! grep -q "# This script cannot be executed directly" "$script_path"; then
        print_error "Missing execution prevention block in '$script_path'"
        print_info "  To fix, run: dhtl run DHT/add_direct_execution_check.sh \"$script_path\""
        return 1
    fi
    
    # Ensure the error message is consistent with the dhtl alias pattern
    if ! grep -q "Please use the dhtl command instead" "$script_path"; then
        if grep -q "# This script cannot be executed directly" "$script_path"; then
            print_error "Incorrect error message in execution prevention block in '$script_path'"
            print_info "  Error message should guide users to use the 'dhtl' command"
            print_info "  To fix, run: dhtl run DHT/update_aliases_phase2.sh \"$script_path\""
            return 1
        fi
    fi
    
    return 0
}

# Check for improper references to ./dhtl.sh
check_dhtl_references() {
    local file_path="$1"
    local has_errors=0
    
    # Check for ./dhtl.sh
    if grep -q '\./dhtl\.sh' "$file_path"; then
        print_error "Found improper references to './dhtl.sh' in '$file_path'"
        grep -n '\./dhtl\.sh' "$file_path" | head -5 # Show up to 5 matches
        has_errors=1
    fi
    
    # Check for ./dhtl followed by space
    if grep -q '\./dhtl ' "$file_path"; then
        print_error "Found improper references to './dhtl ' in '$file_path'"
        grep -n '\./dhtl ' "$file_path" | head -5 # Show up to 5 matches
        has_errors=1
    fi
    
    # Check for usage examples
    if grep -q 'Usage: \./dhtl' "$file_path"; then
        print_error "Found improper usage examples in '$file_path'"
        grep -n 'Usage: \./dhtl' "$file_path" | head -5 # Show up to 5 matches
        has_errors=1
    fi
    
    if [ $has_errors -gt 0 ]; then
        print_info "  To fix all improper references, run: dhtl run DHT/update_aliases_phase2.sh \"$file_path\""
        return 1
    fi
    
    return 0
}

# Process a list of files
process_files() {
    local files=("$@")
    local files_processed=0
    
    for file in "${files[@]}"; do
        # Skip non-existent files
        if [ ! -f "$file" ]; then
            continue
        fi
        
        # Skip files outside the DHT directory or main launcher script
        if [[ "$file" != *"DHT/"* && "$file" != *"dhtl.sh" && "$file" != *"dhtl.bat" ]]; then
            continue
        fi
        
        files_processed=$((files_processed + 1))
        print_info "Checking file: $file"
        
        # For shell scripts, check execution prevention
        if [[ "$file" == *.sh ]]; then
            check_execution_prevention "$file"
        fi
        
        # For all files, check for improper references
        check_dhtl_references "$file"
    done
    
    return $files_processed
}

# Process all shell scripts in DHT directory
process_all_dht_scripts() {
    local files_processed=0
    
    print_info "Checking all shell scripts in DHT directory..."
    
    # Process shell scripts
    while IFS= read -r file; do
        files_processed=$((files_processed + 1))
        
        # Check execution prevention
        check_execution_prevention "$file"
        
        # Check references
        check_dhtl_references "$file"
    done < <(find "$DHT_DIR" -type f -name "*.sh" -not -path "*/.*")
    
    # Process markdown files
    while IFS= read -r file; do
        files_processed=$((files_processed + 1))
        
        # Only check references for markdown files
        check_dhtl_references "$file"
    done < <(find "$DHT_DIR" -type f -name "*.md" -not -path "*/.*")
    
    return $files_processed
}

# Main function
main() {
    local files_processed=0
    
    if [ $# -eq 0 ]; then
        # No files provided, check all DHT scripts
        process_all_dht_scripts
        files_processed=$?
    else
        # Process the files provided
        process_files "$@"
        files_processed=$?
    fi
    
    if [ $ERRORS -eq 0 ]; then
        if [ $files_processed -gt 0 ]; then
            print_success "All $files_processed files passed dhtl alias consistency checks"
        else
            print_info "No relevant files to check"
        fi
        exit 0
    else
        print_error "Found $ERRORS dhtl alias consistency issues"
        print_info "To fix all issues automatically, run: dhtl run DHT/update_aliases_phase2.sh"
        exit 1
    fi
}

# Run the main function
main "$@"