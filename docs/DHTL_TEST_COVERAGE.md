# DHTL Command Test Coverage

## Overview

This document describes the comprehensive test coverage for all dhtl commands in Docker containers. The tests ensure that every dhtl action works correctly in containerized environments with both LOCAL and REMOTE profiles.

## Test Organization

### Test Files

1. **`tests/docker/test_all_dhtl_actions.py`**
   - Main comprehensive test suite
   - Organized by command categories
   - Docker-aware implementations
   - Profile-specific test behavior

2. **`tests/docker/test_dhtl_commands_complete.py`**
   - Additional command coverage
   - Error handling tests
   - Edge case testing

### Test Categories

#### 1. Project Management (`TestDHTLProjectManagement`)
- **init**: Initialize new projects
- **setup**: Setup project environment with dependencies
- **clean**: Clean build artifacts and caches

#### 2. Development (`TestDHTLDevelopment`)
- **build**: Build Python packages
- **test**: Run project tests
- **lint**: Lint code with ruff
- **format**: Format code
- **coverage**: Run coverage analysis
- **sync**: Sync dependencies

#### 3. Version Control (`TestDHTLVersionControl`)
- **commit**: Create git commits
- **tag**: Create git tags
- **bump**: Bump project version

#### 4. Deployment (`TestDHTLDeployment`)
- **publish**: Publish packages (dry-run in tests)
- **docker**: Docker subcommands
- **workflows**: GitHub workflow management

#### 5. Utilities (`TestDHTLUtilities`)
- **env**: Show environment information
- **diagnostics**: Run system diagnostics
- **restore**: Restore dependencies from lock files

#### 6. Special Commands (`TestDHTLSpecialCommands`)
- **help**: Show help information
- **version**: Show DHT version
- **python**: Python command wrapper
- **run**: General command runner

#### 7. Integration (`TestDHTLIntegration`)
- Complete workflow tests
- Multi-command sequences
- Clone and setup tests

#### 8. Edge Cases (`TestDHTLEdgeCases`)
- Invalid command handling
- Missing project files
- Timeout handling

## Running the Tests

### Quick Test Run
```bash
# Run all dhtl action tests in Docker
python run_dhtl_action_tests.py

# Run with specific profile
python run_dhtl_action_tests.py --profile local
python run_dhtl_action_tests.py --profile remote

# Run by categories
python run_dhtl_action_tests.py --profile categories

# Show coverage report
python run_dhtl_action_tests.py --coverage
```

### Using Docker Compose
```bash
# Run in LOCAL profile
docker compose -f docker-compose.profiles.yml run --rm dht-test-local \
  python -m pytest -v tests/docker/test_all_dhtl_actions.py

# Run in REMOTE profile  
docker compose -f docker-compose.profiles.yml run --rm dht-test-remote \
  python -m pytest -v tests/docker/test_all_dhtl_actions.py
```

### Direct Docker Run
```bash
# Run specific test class
docker run --rm \
  -v $(pwd):/app:ro \
  -e DHT_TEST_PROFILE=docker \
  dht:test-simple \
  python -m pytest -v -k TestDHTLProjectManagement \
  tests/docker/test_all_dhtl_actions.py
```

## Command Coverage

### Tested Commands (25+)
✅ **Core**: init, setup, clean, build, sync
✅ **Development**: test, lint, format, coverage
✅ **Dependencies**: restore, install*, add*, remove*, upgrade*
✅ **Version Control**: commit, tag, bump
✅ **GitHub**: clone, fork*
✅ **Deployment**: publish, docker, workflows
✅ **Utilities**: env, diagnostics, guardian*
✅ **Special**: help, version, python, run

*Commands marked with asterisk have basic coverage but may need expanded tests

### Untested/Partial Coverage
- **Workspace**: workspace, workspaces, project (need multi-package setup)
- **Standalone**: node, script (wrapper commands)
- **Specialized**: act, deploy_project_in_container
- **Aliases**: fmt, check, doc, bin, ws, w, p

## Test Profiles

### LOCAL Profile Behavior
- Runs all tests including slow ones
- Allows network access for clone tests
- Longer timeouts (60s)
- More retries (10)
- Comprehensive error messages

### REMOTE Profile Behavior  
- Skips slow tests
- Restricted network access
- Short timeouts (5s)
- Fewer retries (2)
- Concise output

## Test Implementation Details

### Docker Environment Setup
Each test runs in a clean Docker container with:
- Python environment properly configured
- Virtual environment accessible
- Project mounted as read-only
- Profile-specific environment variables

### Test Fixtures
- `tester`: DHTLDockerTester instance for running commands
- `temp_dir`: Temporary directory for test projects
- `sample_project`: Pre-configured test project
- `git_project`: Git-initialized test project

### Assertions
Tests verify:
- Exit codes (0 for success)
- File creation/deletion
- Output content
- Error messages
- Side effects (commits, tags, builds)

## Best Practices

1. **Always test both success and failure cases**
2. **Use appropriate timeouts for commands**
3. **Clean up test artifacts**
4. **Test with minimal dependencies**
5. **Verify command output, not just exit codes**

## Adding New Tests

To add tests for new dhtl commands:

1. Add test method to appropriate test class
2. Use the `tester` fixture to run commands
3. Create minimal test projects as needed
4. Verify both output and side effects
5. Consider profile-specific behavior

Example:
```python
def test_new_command(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
    """Test new dhtl command."""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()
    
    code, out, err = tester.run_dhtl("new_command", ["--arg"], cwd=project_dir)
    
    assert code == 0, f"Command failed: {err}"
    assert "expected output" in out
    assert (project_dir / "expected_file").exists()
```

## Continuous Improvement

The test suite should be continuously updated to:
- Add tests for new commands
- Improve coverage of edge cases
- Test new features and options
- Ensure compatibility with new Docker images
- Validate profile-specific behaviors