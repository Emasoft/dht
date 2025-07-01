# Prefect Test Improvements

## Problem
The tests using Prefect were spawning multiple test servers (uvicorn processes) that were not being properly cleaned up. This led to:
- Resource exhaustion with 82+ Prefect server processes running
- Slow test execution
- Potential test failures due to port conflicts
- Memory and CPU waste

## Root Cause
The `setup_prefect` fixture in `test_uv_prefect_tasks.py` was using `autouse=True` at the function level, which meant:
1. A new Prefect server was started for each test method
2. The servers were not always properly cleaned up
3. Interrupted tests left zombie processes

## Solution
We implemented a multi-layered approach to ensure proper cleanup:

### 1. Class-Scoped Fixture
Changed the Prefect test fixture from function-scoped to class-scoped:
```python
@pytest.fixture(autouse=True, scope="class")
def setup_prefect(self) -> Any:
    """Setup Prefect test harness for the entire test class."""
```

### 2. Process Cleanup Handlers
Added multiple cleanup mechanisms:
- `atexit` handler in test modules
- Session cleanup in `conftest.py`
- Dedicated `conftest_prefect.py` with process management

### 3. Smart Process Cleanup
The cleanup function:
- Uses `pgrep` to find Prefect/uvicorn processes
- Excludes the current process to avoid self-termination
- Sends SIGTERM first, then SIGKILL if needed
- Falls back to `pkill` if `pgrep` is not available

### 4. Better Test Harness
Created `safe_prefect_test_harness()` that:
- Tracks child processes spawned during tests
- Ensures cleanup even on test failure
- Uses process forking hooks to monitor spawned processes

## Benefits
- No more zombie Prefect processes
- Faster test execution (one server per class instead of per test)
- More reliable test runs
- Better resource utilization
- Cleaner test environment

## Usage
Tests using Prefect should now:
1. Use the class-scoped fixture for better performance
2. Import cleanup utilities from `conftest_prefect`
3. Ensure proper cleanup in their teardown
