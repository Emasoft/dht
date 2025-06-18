# DHT Bash to Python Migration Checklist

## Overview
This document tracks the complete migration of DHT from a hybrid bash/Python architecture to a pure Python implementation. Every single .sh and .bat file must be converted to Python and the originals deleted.

## Migration Status Legend
- `[ ]` - Not started
- `[C]` - Converted to Python (original still exists)
- `[X]` - Converted and original deleted (COMPLETE)

## Critical Migration Rules
1. Convert EVERY .sh and .bat file to Python
2. Delete the original immediately after successful conversion
3. Update all tests to use Python versions
4. No shell scripts can remain - including templates, examples, or tests
5. Update all references in documentation and code

## Phase 1: Core Entry Points (2 files)
- [X] `/Users/emanuelesabetta/Code/DHT/dht/dhtl.sh` → `dhtl_entry.py`
- [X] `/Users/emanuelesabetta/Code/DHT/dht/dhtl.bat` → `dhtl_entry_windows.py`

## Phase 2: Module Scripts (36 files)
### Orchestration and Environment
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/orchestrator.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/environment.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/environment_2.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_environment_1.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_environment_2.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_environment_3.sh`

### Core Utilities
- [X] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_error_handling.sh` → `dhtl_error_handling.py`
- [X] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_utils.sh` → `dhtl_utils.py` (+ stub modules)
- [X] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/utils.sh` → `utils.py`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/user_interface.sh`

### Guardian System
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_guardian_1.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_guardian_2.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_guardian_command.sh`

### Command Modules
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_1.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_2.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_3.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_4.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_5.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_6.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_7.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_8.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_standalone.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_workflows.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_commands_act.sh`

### Feature Modules
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_init.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_uv.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_diagnostics.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_secrets.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_test.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_version.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_github.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/modules/dhtl_regenerate_poc.sh`

## Phase 3: Helper Scripts (5 files)
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/ensure_env.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/hooks/bump_version.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/src/DHT/hooks/check_dhtl_alias.sh`

## Phase 4: Test Scripts (2 files)
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/test_compact.sh`
- [ ] `/Users/emanuelesabetta/Code/DHT/dht/tests/test_dhtl_basic.sh`

## Migration Progress Summary
- Total Scripts to Convert: 45
- Scripts Converted: 5
- Scripts Deleted: 5
- Migration Complete: 11.1%

## Migration Strategy
1. Start with entry points (dhtl.sh/bat) to establish Python-based entry
2. Convert utility modules that other modules depend on
3. Convert command modules one by one
4. Convert feature modules
5. Update tests last

## Notes
- Each conversion must maintain 100% functionality
- All tests must pass after each conversion
- Document any behavioral changes
- Update all references in code and docs
- Some files don't exist (like python-wrapper.sh, install.sh) - removed from list