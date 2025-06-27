# DHT Docker Test Profiles

## Overview

DHT supports different test profiles optimized for specific workflows:

- **LOCAL**: Full development environment with debugging and comprehensive testing
- **REMOTE**: CI/CD optimized environment with fast execution and essential tests

## Profile Characteristics

### LOCAL Profile
- **Purpose**: Development, debugging, and comprehensive testing
- **Characteristics**:
  - High retry counts (10 retries)
  - Long timeouts (60 seconds)
  - Runs all tests including slow ones
  - Full network access allowed
  - Debugging enabled
  - Higher memory limits (4GB)
  - Read-write filesystem access
  - Detailed error messages

### REMOTE Profile
- **Purpose**: CI/CD pipelines, GitHub Actions
- **Characteristics**:
  - Low retry counts (2 retries)
  - Short timeouts (5 seconds)
  - Skips slow tests automatically
  - Restricted network access
  - Minimal debugging output
  - Lower memory limits (1GB)
  - Read-only filesystem where appropriate
  - Concise error reporting

## Running Profile Tests

### Using the Profile Test Runner

```bash
# Run LOCAL profile tests
python run_profile_tests.py local

# Run REMOTE profile tests
python run_profile_tests.py remote

# Run both profiles and compare
python run_profile_tests.py both

# Run comparison tests
python run_profile_tests.py compare

# Start development shell
python run_profile_tests.py shell
```

### Using Docker Compose Directly

```bash
# Run LOCAL profile tests
docker compose -f docker-compose.profiles.yml run --rm dht-test-local

# Run REMOTE profile tests
docker compose -f docker-compose.profiles.yml run --rm dht-test-remote

# Start LOCAL development environment
docker compose -f docker-compose.profiles.yml run --rm dht-dev-local

# Run CI simulation
docker compose -f docker-compose.profiles.yml run --rm dht-ci-runner
```

### Environment Variables

Set the profile using `DHT_TEST_PROFILE`:

```bash
# Run with LOCAL profile
DHT_TEST_PROFILE=local pytest tests/

# Run with REMOTE profile
DHT_TEST_PROFILE=remote pytest tests/
```

## Writing Profile-Aware Tests

### Skip Tests by Profile

```python
@pytest.mark.skipif(
    os.environ.get("DHT_TEST_PROFILE", "").lower() != "local",
    reason="LOCAL profile only"
)
def test_local_only_feature():
    """This test only runs in LOCAL profile."""
    pass

@pytest.mark.skipif(
    os.environ.get("DHT_TEST_PROFILE", "").lower() not in ["remote", "ci"],
    reason="REMOTE profile only"
)
def test_remote_only_feature():
    """This test only runs in REMOTE profile."""
    pass
```

### Use Profile Configuration

```python
def test_with_profile_config(test_config):
    """Test that adapts to profile configuration."""
    max_retries = test_config["max_retries"]
    timeout = test_config["timeout"]

    # Adjust test behavior based on profile
    if test_config["comprehensive_tests"]:
        # Run extensive tests in LOCAL
        run_comprehensive_suite()
    else:
        # Run essential tests in REMOTE
        run_essential_tests()
```

### Profile-Specific Markers

```python
# Mark slow tests (skipped in REMOTE)
@pytest.mark.slow
def test_performance_analysis():
    """This test is skipped in REMOTE profile."""
    pass

# Mark network tests
@pytest.mark.network
def test_api_integration():
    """Network test with profile-specific behavior."""
    pass

# Mark Docker tests
@pytest.mark.docker
def test_container_operations():
    """Docker-specific test."""
    pass
```

## Profile Comparison

When running both profiles, you'll see a comparison:

```
📊 PROFILE TEST SUMMARY
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Profile  ┃ Passed ┃ Failed ┃ Skipped ┃ Total    ┃ Duration  ┃ Status   ┃
┣━━━━━━━━━━╋━━━━━━━━╋━━━━━━━━╋━━━━━━━━━╋━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━━┫
┃ LOCAL    ┃     45 ┃      0 ┃       2 ┃       47 ┃    12.34s ┃ ✅ PASS  ┃
┃ REMOTE   ┃     38 ┃      0 ┃       9 ┃       47 ┃     3.21s ┃ ✅ PASS  ┃
┗━━━━━━━━━━┻━━━━━━━━┻━━━━━━━━┻━━━━━━━━━┻━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━━┛

📈 PROFILE DIFFERENCES:
• Test Coverage: LOCAL ran 47 tests, REMOTE ran 47 tests
• Skipped Tests: LOCAL skipped 2, REMOTE skipped 9
• Execution Time: LOCAL took 12.34s, REMOTE took 3.21s
• Speed: REMOTE was 9.13s faster (74.0% improvement)
• Coverage: LOCAL ran 7 more actual tests
```

## Best Practices

1. **Use LOCAL for Development**:
   - When debugging issues
   - When writing new tests
   - When need comprehensive coverage
   - When working with network-dependent features

2. **Use REMOTE for CI/CD**:
   - In GitHub Actions workflows
   - For quick validation
   - When speed is critical
   - For production deployments

3. **Write Profile-Aware Tests**:
   - Consider both profiles when writing tests
   - Use appropriate markers
   - Respect timeout and retry limits
   - Handle network restrictions gracefully

4. **Profile-Specific Resources**:
   - LOCAL: Can use more memory and CPU
   - REMOTE: Must be resource-efficient
   - Both: Should clean up after themselves

## Workflow Examples

### Local Development Workflow
```bash
# Start development shell
python run_profile_tests.py shell

# Inside the shell
dhtl init
dhtl setup
dhtl test
dhtl build
```

### CI/CD Workflow
```yaml
# GitHub Actions example
- name: Run tests
  run: |
    docker compose -f docker-compose.profiles.yml run --rm dht-test-remote
```

### Debugging Failed Tests
```bash
# Run with LOCAL profile for detailed output
DHT_TEST_PROFILE=local python -m pytest -vv --tb=long tests/failing_test.py

# Compare behavior between profiles
python run_profile_tests.py compare
```

## Troubleshooting

### Profile Not Detected
Ensure `DHT_TEST_PROFILE` is set:
```bash
echo $DHT_TEST_PROFILE
export DHT_TEST_PROFILE=local
```

### Tests Skipped Unexpectedly
Check profile configuration:
```python
from tests.conftest import TEST_CONFIGS, get_test_profile
print(f"Current profile: {get_test_profile()}")
print(f"Config: {TEST_CONFIGS[get_test_profile()]}")
```

### Different Results Between Profiles
This is expected! Profiles are optimized for different use cases:
- LOCAL: Comprehensive but slower
- REMOTE: Fast but may skip some tests

Use the comparison tool to understand differences:
```bash
python run_profile_tests.py both
```
