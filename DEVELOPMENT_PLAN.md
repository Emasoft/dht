# DHT Shell-to-Python Transition Development Plan

## Overview
This plan outlines the complete transition of DHT from shell scripts to Python, including converting templates to Prefect flows/tasks and implementing all placeholder functions.

## Phase 1: Template Conversion Strategy (High Priority)

### 1.1 Identify Template Types
Currently, we have these template generators:
- **Project Templates** (`dhtl_project_templates.py`):
  - `.gitignore` template
  - License templates (MIT, Apache)
  - GitHub Actions CI/CD workflow

### 1.2 Convert Templates to Prefect Flows
Each template should be:
1. A Prefect task for individual file generation
2. Grouped into flows for project initialization workflows
3. Reusable across different commands (init, setup, regenerate)

**Proposed Architecture:**
```
flows/
  project_init_flow.py     - Initialize new project
  project_setup_flow.py    - Setup existing project
  ci_cd_setup_flow.py      - Setup CI/CD workflows
  regenerate_flow.py       - Regenerate project from .dhtconfig
```

## Phase 2: Command Module Implementation (High Priority)

### 2.1 Commands Status
- ✅ `dhtl_commands_1.py` - restore command (IMPLEMENTED)
- ✅ `dhtl_commands_2.py` - test command (IMPLEMENTED)
- ❌ `dhtl_commands_3.py` - PLACEHOLDER (needs implementation)
- ❌ `dhtl_commands_4.py` - PLACEHOLDER (needs implementation)
- ⚠️  `dhtl_commands_5.py` - coverage command (CHECK STATUS)
- ⚠️  `dhtl_commands_6.py` - commit command (CHECK STATUS)
- ⚠️  `dhtl_commands_7.py` - publish command (CHECK STATUS)
- ⚠️  `dhtl_commands_8.py` - clean command (CHECK STATUS)

### 2.2 Missing Command Implementations
Based on the registry, commands 3 & 4 are unused placeholders. We should:
1. Remove these unused modules
2. Focus on implementing actual missing functionality

## Phase 3: Placeholder Function Replacement (High Priority)

### 3.1 Critical Modules with Placeholders
1. **orchestrator.py** - Core module coordination
2. **dhtl_init.py** - Project initialization
3. **dhtl_uv.py** - UV package manager integration
4. **dhtl_secrets.py** - Secrets management
5. **dhtl_github.py** - GitHub operations
6. **dhtl_commands_workflows.py** - Workflow management
7. **dhtl_commands_act.py** - Act (GitHub Actions locally)
8. **dhtl_commands_standalone.py** - Standalone commands

### 3.2 Implementation Priority
1. **orchestrator.py** - Critical for module loading
2. **dhtl_init.py** - Essential for project creation
3. **dhtl_uv.py** - Core dependency management
4. **dhtl_github.py** - Clone/fork functionality

## Phase 4: Code Consolidation (Medium Priority)

### 4.1 Duplicate Environment Modules
Consolidate these into `environment_utils.py`:
- `environment.py`
- `environment_2.py`
- `dhtl_environment_1.py`
- `dhtl_environment_2.py`
- `dhtl_environment_3.py`

### 4.2 Common Utilities
Create shared modules:
- `subprocess_runner.py` - Unified subprocess execution
- `logging_config.py` - Centralized logging setup
- `exception_handlers.py` - Common error handling
- `path_utils.py` - Path manipulation utilities

## Phase 5: Error Handling Improvements (Medium Priority)

### 5.1 Replace Empty Exception Handlers
Files with empty `except: pass` blocks:
- guardian_prefect.py
- dhtconfig.py
- command_runner.py
- environment_capture_utils.py
- docker_manager.py
(30+ more files)

### 5.2 Implement Proper Error Handling
1. Create custom exception hierarchy
2. Add logging to all exception handlers
3. Provide meaningful error messages
4. Implement retry logic where appropriate

## Phase 6: Prefect Integration (High Priority)

### 6.1 Convert Templates to Tasks
```python
@task(name="generate_gitignore")
def generate_gitignore_task() -> str:
    """Generate Python .gitignore content."""
    return get_python_gitignore()

@task(name="generate_license")
def generate_license_task(license_type: str, author: str) -> str:
    """Generate license content."""
    if license_type == "MIT":
        return get_mit_license(author)
    elif license_type == "Apache":
        return get_apache_license(author)
```

### 6.2 Create Project Workflows
```python
@flow(name="initialize_project")
def initialize_project_flow(
    project_path: Path,
    project_name: str,
    author: str,
    license_type: str = "MIT"
):
    """Initialize a new DHT project."""
    # Create directory structure
    # Generate project files
    # Setup git repository
    # Create virtual environment
    # Install base dependencies
```

## Phase 7: Testing Strategy (High Priority)

### 7.1 Test Coverage for New Implementations
- Unit tests for each new function
- Integration tests for workflows
- Mock external dependencies (git, uv, etc.)
- Test error handling paths

### 7.2 Fix Existing Test Issues
- Fix path references in test files
- Remove hardcoded paths
- Ensure tests are platform-independent

## Implementation Order

1. **Week 1: Core Infrastructure**
   - Implement orchestrator.py
   - Create shared utilities
   - Setup Prefect task/flow structure

2. **Week 2: Essential Commands**
   - Implement dhtl_init.py
   - Implement dhtl_uv.py
   - Create project initialization flow

3. **Week 3: GitHub & Workflows**
   - Implement dhtl_github.py
   - Implement workflow commands
   - Create CI/CD setup flows

4. **Week 4: Cleanup & Testing**
   - Consolidate duplicate code
   - Fix error handling
   - Write comprehensive tests
   - Update documentation

## Success Criteria

1. All placeholder functions replaced with implementations
2. All shell script functionality converted to Python
3. Templates converted to reusable Prefect tasks/flows
4. 90%+ test coverage for new code
5. No empty exception handlers
6. No duplicate implementations
7. All commands working with Prefect orchestration

## Next Steps

1. Get user approval for this plan
2. Start with Phase 1: Template conversion
3. Implement in small, testable increments
4. Commit after each successful implementation
5. Run linters and tests after each change
