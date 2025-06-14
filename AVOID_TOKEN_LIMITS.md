# Avoiding Token Limit Issues in Claude Code

## Problem
When working with Claude Code, verbose command outputs can exceed the 200K token limit, causing timeouts or failures. This is especially problematic with:
- Test suite outputs (pytest can be very verbose)
- Large file listings
- Detailed error tracebacks
- Build/compilation outputs
- Log files

## Solutions Implemented

### 1. Compact Test Output
- **Custom pytest plugin** (`tests/pytest_summary.py`): Provides a concise table format
- **Modified pytest.ini**: Reduced verbosity settings
- **Test runners**:
  - `./test_compact.sh`: Bash script for minimal output
  - `python run_tests_compact.py`: Python script with output filtering

### 2. Error Logging
- Detailed errors are written to `test_errors.log` instead of console
- Only summary statistics are shown in the terminal
- First 10 lines of errors shown as preview

### 3. Usage Examples

```bash
# Run all tests with compact output
./test_compact.sh

# Run specific test file
python run_tests_compact.py tests/unit/test_project_type_detector.py

# Run tests matching pattern
python run_tests_compact.py -k "test_cli_detection"

# Traditional pytest (verbose - avoid this)
pytest -xvs  # DON'T USE - too verbose!
```

### 4. Other Strategies to Reduce Output

#### For File Operations
```bash
# Instead of: find . -name "*.py" -type f
# Use: find . -name "*.py" -type f | wc -l  # Just count

# Instead of: ls -la 
# Use: ls | wc -l  # Just count files

# Instead of: cat large_file.py
# Use: head -20 large_file.py  # First 20 lines only
```

#### For Build/Install Commands
```bash
# Redirect verbose output to files
pip install -r requirements.txt > install.log 2>&1 && echo "✅ Installation complete" || echo "❌ Installation failed - see install.log"

# Use quiet modes
pip install -q package_name
npm install --silent
```

#### For Git Operations
```bash
# Instead of: git log
# Use: git log --oneline -10  # Last 10 commits only

# Instead of: git diff
# Use: git diff --stat  # Summary only
```

### 5. Prefect/Flow Output Reduction

Set these environment variables:
```bash
export PREFECT_LOGGING_LEVEL=ERROR
export PREFECT_LOGGING_TO_API_ENABLED=False
```

Or in Python:
```python
import os
os.environ["PREFECT_LOGGING_LEVEL"] = "ERROR"
```

### 6. General Best Practices

1. **Use head/tail**: For long outputs, show only relevant portions
2. **Summarize results**: Create summary tables instead of full details  
3. **Log to files**: Write verbose output to log files, show only summaries
4. **Use counts**: Often a count is enough (e.g., "Found 47 Python files")
5. **Filter output**: Use grep/awk to show only relevant lines
6. **Paginate**: Break large outputs into smaller chunks

### 7. Token Usage Estimation

Rough estimates:
- 1 token ≈ 4 characters
- 200K tokens ≈ 800K characters
- Full pytest output for 100 tests ≈ 50K-500K characters (risky!)
- Compact summary for 100 tests ≈ 10K characters (safe)

### 8. When You Hit Limits

If you still hit token limits:
1. Start a new conversation (resets context)
2. Use more aggressive filtering
3. Process data in smaller batches
4. Offload to external tools and just show summaries

## Remember
The goal is to provide Claude with enough information to help you effectively while staying within token limits. Summary information is usually sufficient - detailed logs can always be examined separately when needed.