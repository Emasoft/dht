# Subprocess Error Handling Migration Guide

## Overview

This guide explains how to migrate from direct `subprocess` usage to the new `subprocess_utils` module that provides enhanced error handling, retry logic, timeout management, and better resource cleanup.

## Benefits of Migration

1. **Comprehensive Error Handling**: Specific exception types for different error scenarios
2. **Automatic Retries**: Built-in retry logic for transient failures
3. **Resource Management**: Proper cleanup of subprocess resources
4. **Security Features**: Sensitive data masking in logs
5. **Timeout Handling**: Robust timeout management with process cleanup
6. **Context Managers**: Better resource management with context managers

## Basic Migration Examples

### Simple Command Execution

**Before:**
```python
import subprocess

result = subprocess.run(["echo", "hello"], capture_output=True, text=True)
if result.returncode == 0:
    print(result.stdout)
else:
    print(f"Error: {result.stderr}")
```

**After:**
```python
from DHT.modules.subprocess_utils import run_subprocess

result = run_subprocess(["echo", "hello"])
if result["success"]:
    print(result["stdout"])
else:
    print(f"Error: {result['stderr']}")
```

### Error Handling

**Before:**
```python
try:
    result = subprocess.run(["some-command"], check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    print(f"Command failed: {e.stderr}")
except FileNotFoundError:
    print("Command not found")
```

**After:**
```python
from DHT.modules.subprocess_utils import run_subprocess, ProcessNotFoundError, ProcessExecutionError

try:
    result = run_subprocess(["some-command"])
except ProcessNotFoundError as e:
    print(f"Command not found: {e.command}")
except ProcessExecutionError as e:
    print(f"Command failed with code {e.returncode}: {e.stderr}")
```

### Timeout Handling

**Before:**
```python
try:
    result = subprocess.run(["long-running-command"], timeout=30)
except subprocess.TimeoutExpired:
    print("Command timed out")
```

**After:**
```python
from DHT.modules.subprocess_utils import run_subprocess, CommandTimeoutError

try:
    result = run_subprocess(["long-running-command"], timeout=30)
except CommandTimeoutError as e:
    print(f"Command timed out after {e.timeout} seconds")
```

### With Retry Logic

**Before:**
```python
max_retries = 3
for attempt in range(max_retries):
    try:
        result = subprocess.run(["flaky-command"], check=True)
        break
    except subprocess.CalledProcessError:
        if attempt < max_retries - 1:
            time.sleep(1)
            continue
        raise
```

**After:**
```python
result = run_subprocess(
    ["flaky-command"],
    retry_count=2,  # Will try 3 times total
    retry_delay=1.0
)
```

### Working Directory and Environment

**Before:**
```python
env = os.environ.copy()
env["MY_VAR"] = "value"
result = subprocess.run(["command"], cwd="/path/to/dir", env=env)
```

**After:**
```python
result = run_subprocess(
    ["command"],
    cwd=Path("/path/to/dir"),
    env={"MY_VAR": "value", **os.environ}
)
```

### Handling Large Output

**Before:**
```python
# No built-in protection against large output
result = subprocess.run(["command-with-large-output"], capture_output=True)
# Could consume excessive memory
```

**After:**
```python
result = run_subprocess(
    ["command-with-large-output"],
    max_output_size=10 * 1024 * 1024  # 10MB limit
)
if result["output_truncated"]:
    print("Warning: Output was truncated")
```

### Sensitive Data Protection

**Before:**
```python
# Password visible in logs
cmd = ["mysql", "-u", "root", "-p", password]
logging.debug(f"Running: {' '.join(cmd)}")
subprocess.run(cmd)
```

**After:**
```python
result = run_subprocess(
    ["mysql", "-u", "root", "-p", password],
    sensitive_args=[password],
    log_command=True  # Password will be masked as ***
)
```

### Context Manager for Multiple Commands

**Before:**
```python
# No coordinated cleanup
proc1 = subprocess.Popen(["command1"])
proc2 = subprocess.Popen(["command2"])
# If error occurs, processes might not be cleaned up
```

**After:**
```python
from DHT.modules.subprocess_utils import SubprocessContext

with SubprocessContext() as ctx:
    result1 = ctx.run(["command1"])
    result2 = ctx.run(["command2"])
    # All processes cleaned up automatically
```

## Advanced Features

### Custom Error Handlers

```python
def my_error_handler(error, context):
    # Log to external system
    logger.error(f"Command {context['command']} failed: {error}")
    # Return custom result
    return {"success": False, "handled": True}

result = run_subprocess(
    ["command"],
    error_handler=my_error_handler
)
```

### Process Groups (Better Cleanup)

```python
# Ensures child processes are also terminated
result = run_subprocess(
    ["parent-command-that-spawns-children"],
    create_process_group=True
)
```

### Binary Data Handling

```python
# For binary output
result = run_subprocess(
    ["command-with-binary-output"],
    text=False  # Returns bytes instead of str
)
binary_data = result["stdout"]  # bytes
```

## Migration Checklist

1. **Import the new module**:
   ```python
   from DHT.modules.subprocess_utils import run_subprocess
   ```

2. **Replace subprocess.run() calls** with run_subprocess()

3. **Update error handling** to use new exception types:
   - `ProcessNotFoundError` instead of `FileNotFoundError`
   - `ProcessExecutionError` instead of `CalledProcessError`
   - `CommandTimeoutError` instead of `TimeoutExpired`

4. **Update result access**:
   - Use `result["stdout"]` instead of `result.stdout`
   - Use `result["success"]` instead of checking `result.returncode == 0`

5. **Add retry logic** where appropriate for flaky commands

6. **Add sensitive data protection** for commands with passwords/tokens

7. **Consider using context managers** for multiple related commands

8. **Set appropriate timeouts** to prevent hanging

## Common Pitfalls

1. **Shell Commands**: If using shell=True, command must be a string, not a list
2. **Input Data**: Match text parameter with input data type (str for text=True, bytes for text=False)
3. **Working Directory**: Use Path objects for better cross-platform compatibility
4. **Environment Variables**: Remember to include existing environment if needed

## Testing

Always test migrated code thoroughly, especially:
- Error cases (command not found, non-zero exit)
- Timeout scenarios
- Large output handling
- Interrupt handling (Ctrl+C)

## Module Locations

- Implementation: `src/DHT/modules/subprocess_utils.py`
- Tests: `tests/unit/test_subprocess_utils.py`
- Examples: This guide and test files

## Support

For questions or issues with migration, consult the test file for comprehensive examples of all features.
