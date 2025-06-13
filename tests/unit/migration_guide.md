# Test Helpers Migration Guide

This guide shows how to update existing DHT tests to use the new test_helpers.py module.

## Overview

The `test_helpers.py` module provides:
- Realistic fixture generators for different project types
- Proper mock factories that return correct types
- Path resolution utilities for finding DHT modules
- Utilities for creating complete project structures

## Before and After Examples

### 1. Mocking platform.uname()

**Before (incorrect):**
```python
@patch('platform.uname')
def test_system_info(mock_uname):
    mock_uname.return_value = ('Darwin', 'host', '20.3.0', 'version', 'x86_64', 'x86_64')
    # This fails because platform.uname() returns a namedtuple, not a tuple
```

**After (correct):**
```python
from test_helpers import create_platform_uname_mock

@patch('platform.uname')
def test_system_info(mock_uname):
    mock_uname.return_value = create_platform_uname_mock(
        system='Darwin',
        node='host',
        release='20.3.0',
        version='version',
        machine='x86_64',
        processor='x86_64'
    )
    # Now it works correctly with namedtuple attributes
```

### 2. Creating Test Projects

**Before (manual):**
```python
def test_dht_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        
        # Manually create files
        (project_dir / "pyproject.toml").write_text("...")
        (project_dir / "README.md").write_text("...")
        (project_dir / "src").mkdir()
        # ... many more manual file creations
```

**After (using helpers):**
```python
from test_helpers import create_temporary_project, cleanup_temporary_project

def test_dht_init():
    project_path, metadata = create_temporary_project(
        project_type="django",
        project_name="test_django_app",
        python_version="3.10",
        include_tests=True,
        include_ci=True
    )
    
    try:
        # Your test code here - project is fully set up
        assert (project_path / "manage.py").exists()
    finally:
        cleanup_temporary_project(project_path)
```

### 3. Mock Memory Information

**Before:**
```python
@patch('psutil.virtual_memory')
def test_memory_check(mock_vm):
    mock_vm.return_value = MagicMock(
        total=16 * 1024 * 1024 * 1024,
        available=8 * 1024 * 1024 * 1024
    )
    # Missing other attributes like percent, used, free
```

**After:**
```python
from test_helpers import create_psutil_virtual_memory_mock

@patch('psutil.virtual_memory')
def test_memory_check(mock_vm):
    mock_vm.return_value = create_psutil_virtual_memory_mock(
        total=16 * 1024 * 1024 * 1024,
        available=8 * 1024 * 1024 * 1024,
        percent=50.0
    )
    # All attributes properly set
```

### 4. Finding DHT Modules

**Before:**
```python
def test_module_loading():
    # Hardcoded path - breaks if test is run from different directory
    modules_dir = Path(__file__).parent.parent.parent / "modules"
    assert modules_dir.exists()
```

**After:**
```python
from test_helpers import find_dht_modules_dir

def test_module_loading():
    modules_dir = find_dht_modules_dir()
    assert modules_dir.exists()
    # Works from any directory
```

## Project Type Options

When creating test projects, you can specify:
- `simple` - Basic Python script with main.py
- `django` - Full Django project with REST API
- `fastapi` - FastAPI with async support
- `ml` - Machine learning with PyTorch, configs
- `library` - Distributable package with CLI
- `fullstack` - FastAPI backend + Next.js frontend

## Best Practices

1. **Use temporary projects for integration tests:**
   ```python
   project_path, metadata = create_temporary_project(...)
   try:
       # Your tests
   finally:
       cleanup_temporary_project(project_path)
   ```

2. **Create minimal fixtures for unit tests:**
   ```python
   # Only create what you need
   metadata = create_project_structure(
       tmp_path,
       project_type="simple",
       include_tests=False,  # Skip if not needed
       include_docs=False,   # Skip if not needed
       include_ci=False      # Skip if not needed
   )
   ```

3. **Use metadata for assertions:**
   ```python
   project_path, metadata = create_temporary_project("ml")
   
   # metadata contains useful info
   assert metadata["type"] == "ml"
   assert metadata["python_version"] == "3.10"
   assert "train.py" in metadata["files"]
   ```

4. **Combine with existing fixtures:**
   ```python
   @pytest.fixture
   def django_project():
       project_path, metadata = create_temporary_project("django")
       yield project_path, metadata
       cleanup_temporary_project(project_path)
   
   def test_django_feature(django_project):
       project_path, metadata = django_project
       # Use in test
   ```

## Common Patterns

### Testing Cross-Platform Compatibility
```python
@pytest.mark.parametrize("system,expected", [
    ("Darwin", "macOS"),
    ("Linux", "Linux"),
    ("Windows", "Windows"),
])
@patch('platform.uname')
def test_platform_detection(mock_uname, system, expected):
    mock_uname.return_value = create_platform_uname_mock(system=system)
    # Test platform-specific behavior
```

### Testing Different Python Versions
```python
@pytest.mark.parametrize("python_version", ["3.9", "3.10", "3.11", "3.12"])
def test_python_compatibility(python_version):
    project_path, metadata = create_temporary_project(
        python_version=python_version
    )
    try:
        # Test Python version specific features
        version_file = project_path / ".python-version"
        assert version_file.read_text().strip() == python_version
    finally:
        cleanup_temporary_project(project_path)
```

### Testing Project Analysis
```python
def test_analyze_project_dependencies():
    # Create a complex project
    project_path, metadata = create_temporary_project(
        project_type="fullstack",
        include_tests=True,
        include_docs=True,
        include_ci=True
    )
    
    try:
        # Analyze backend
        pyproject = project_path / "pyproject.toml"
        assert "fastapi" in pyproject.read_text()
        
        # Analyze frontend
        package_json = project_path / "frontend" / "package.json"
        assert "react" in package_json.read_text()
    finally:
        cleanup_temporary_project(project_path)
```

## Tips

1. **Import what you need:** The module is designed for selective imports
2. **Use type hints:** All functions have proper type annotations
3. **Check generated content:** Projects have realistic, working code
4. **Leverage metadata:** The metadata dict tracks all created files
5. **Custom projects:** Use `create_project_structure()` for full control

## Module Location

The test helpers are located at:
```
DHT/tests/unit/test_helpers.py
```

Import in your tests:
```python
from test_helpers import (
    create_platform_uname_mock,
    create_temporary_project,
    cleanup_temporary_project,
    # ... other imports
)
```