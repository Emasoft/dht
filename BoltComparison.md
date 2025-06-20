# Bolt to DHT Command Mapping and Implementation Plan

This document tracks the implementation of Bolt-compatible commands in DHT, ensuring users familiar with Bolt can easily transition to DHT for Python projects.

## Command Mapping and Implementation Checklist

### Basic Commands

- [ ] **`dhtl` (no args)** → Should default to `dhtl install` (currently shows help)
  - **Current**: Shows help message
  - **Action**: Change default behavior to run `dhtl setup` (equivalent to install)
  - **Implementation**: Modify `dhtl.py` main function to detect no args and run setup

- [ ] **`dhtl [unknown command]`** → Should default to `dhtl run [unknown command]`
  - **Current**: Shows error for unknown command
  - **Action**: Catch unknown commands and pass to `dhtl run`
  - **Implementation**: Add fallback in command dispatcher

- [ ] **`dhtl help`** → Already exists ✅
  - **Current**: `dhtl --help` and `dhtl help`
  - **Action**: Ensure comprehensive help content

### Package Management Commands

- [ ] **`dhtl install`** → Add as alias for `dhtl setup`
  - **Current**: `dhtl setup` does this
  - **Action**: Add `install` as command alias
  - **Implementation**: Add @click.command(name='install') that calls setup

- [ ] **`dhtl add [package]`** → New command wrapping `uv add`
  - **Current**: Users must use `uv add` directly
  - **Action**: Create new command
  - **Implementation**:
    ```python
    @click.command(name='add')
    @click.argument('packages', nargs=-1, required=True)
    def add_command(packages):
        """Add dependencies to the project"""
        # Use uv add via subprocess
    ```

- [ ] **`dhtl upgrade [package]`** → New command wrapping `uv add --upgrade`
  - **Current**: `dhtl sync --upgrade` upgrades all
  - **Action**: Create new command for specific packages
  - **Implementation**: Similar to add but with --upgrade flag

- [ ] **`dhtl remove [package]`** → New command wrapping `uv remove`
  - **Current**: Users must use `uv remove` directly
  - **Action**: Create new command
  - **Implementation**: Wrap uv remove command

### Script and Development Commands

- [ ] **`dhtl run [script]`** → Already exists ✅
  - **Current**: `dhtl run` command exists
  - **Action**: Ensure it matches Bolt behavior (run scripts from pyproject.toml)

- [ ] **`dhtl build`** → Already exists ✅
  - **Current**: `dhtl build` builds Python packages
  - **Action**: None needed

- [ ] **`dhtl test`** → Already exists ✅
  - **Current**: `dhtl test` runs pytest
  - **Action**: None needed

- [ ] **`dhtl format` / `dhtl fmt`** → Already exists, add `fmt` alias
  - **Current**: `dhtl format` exists
  - **Action**: Add `fmt` as alias
  - **Implementation**: Add @click.command(name='fmt') that calls format

- [ ] **`dhtl lint`** → Already exists ✅
  - **Current**: `dhtl lint` runs linters
  - **Action**: None needed

- [ ] **`dhtl doc`** → New command for documentation generation
  - **Current**: Not implemented
  - **Action**: Create new command using Sphinx/mkdocs
  - **Implementation**:
    ```python
    @click.command(name='doc')
    def doc_command():
        """Generate project documentation"""
        # Use Sphinx or mkdocs
    ```

- [ ] **`dhtl check`** → Add as alias for type checking (part of lint)
  - **Current**: Type checking is part of `dhtl lint`
  - **Action**: Add standalone command for mypy
  - **Implementation**: Create command that runs mypy only

- [ ] **`dhtl bin`** → New command to show executable installation folder
  - **Current**: Not implemented
  - **Action**: Create command to show .venv/bin or Scripts path
  - **Implementation**: Print venv bin directory path

### Workspace Commands (Using UV Workspaces)

- [ ] **`dhtl workspaces run [script]` / `dhtl ws run [script]`** → Run script in all packages
  - **Current**: Not implemented
  - **Action**: Implement using UV workspace support
  - **Implementation**:
    ```python
    @click.command(name='workspaces')
    @click.argument('subcommand')
    @click.argument('script')
    def workspaces_command(subcommand, script):
        """Run commands across workspace packages"""
        # Use uv run with workspace iteration
    ```

- [ ] **`dhtl ws exec -- [cmd]`** → Execute shell command in every package
  - **Current**: Not implemented
  - **Action**: Implement workspace exec
  - **Implementation**: Iterate workspace members and execute command

- [ ] **`dhtl ws upgrade [dependency]`** → Upgrade dependency across all packages
  - **Current**: Not implemented
  - **Action**: Implement using UV workspace features
  - **Implementation**: Run uv add --upgrade in all workspace members

- [ ] **`dhtl ws remove [dependency]`** → Remove dependency across all packages
  - **Current**: Not implemented
  - **Action**: Implement workspace-wide removal
  - **Implementation**: Run uv remove in all workspace members

### Workspace Filtering Options

- [ ] **`--only [name glob]`** → Filter packages by name
  - **Implementation**: Add to workspace commands

- [ ] **`--ignore [name glob]`** → Exclude packages by name
  - **Implementation**: Add to workspace commands

- [ ] **`--only-fs [file glob]`** → Filter by file system glob
  - **Implementation**: Add to workspace commands

- [ ] **`--ignore-fs [file glob]`** → Exclude by file system glob
  - **Implementation**: Add to workspace commands

### Project/Workspace Specific Commands

- [ ] **`dhtl workspace [name] run [script]` / `dhtl w [name] run [script]`**
  - **Current**: Not implemented
  - **Action**: Run script in specific workspace package
  - **Implementation**: Target specific workspace member

- [ ] **`dhtl project run [script]` / `dhtl p run [script]`**
  - **Current**: Not implemented
  - **Action**: Run script in root project only
  - **Implementation**: Alias for current `dhtl run`

### Publishing Commands

- [ ] **`dhtl publish`** → Already exists ✅
  - **Current**: `dhtl publish` publishes to PyPI
  - **Action**: None needed

- [ ] **`dhtl publish-lock`** → Not applicable to PyPI
  - **Skip**: PyPI doesn't have npm-style locking

- [ ] **`dhtl publish-unlock`** → Not applicable to PyPI
  - **Skip**: PyPI doesn't have npm-style locking

## Implementation Plan

### Phase 1: Command Aliases and Simple Wrappers
1. [ ] Write tests for all new command behaviors
2. [ ] Add `install` as alias for `setup`
3. [ ] Add `fmt` as alias for `format`
4. [ ] Add `check` command for type checking only
5. [ ] Implement `add`, `remove`, `upgrade` commands wrapping uv
6. [ ] Implement `bin` command
7. [ ] Change default behavior when no command given
8. [ ] Implement unknown command fallback to `run`

### Phase 2: Documentation Command
1. [ ] Write tests for documentation generation
2. [ ] Implement `doc` command using Sphinx or mkdocs
3. [ ] Add configuration detection for doc tool
4. [ ] Support multiple documentation formats

### Phase 3: Workspace Commands
1. [ ] Study UV workspace documentation
2. [ ] Write tests for workspace commands
3. [ ] Implement workspace detection and iteration
4. [ ] Implement `workspaces run` / `ws run`
5. [ ] Implement `ws exec`
6. [ ] Implement `ws upgrade` and `ws remove`
7. [ ] Add filtering options (--only, --ignore, etc.)
8. [ ] Implement specific workspace/project targeting

### Phase 4: Documentation and Polish
1. [ ] Update README.md with Bolt-style command table
2. [ ] Add migration guide from Bolt to DHT
3. [ ] Update all command docstrings
4. [ ] Ensure help messages are comprehensive
5. [ ] Add examples for each command

## Testing Strategy

Each new command requires:
1. Unit tests for command parsing
2. Integration tests for actual functionality
3. Tests for error cases
4. Tests for workspace scenarios (where applicable)

## Technical Notes

- All commands must use Prefect with `max_concurrency=1` for safety
- Commands should detect if in workspace vs single project
- Error messages should be clear and helpful
- Maintain backwards compatibility with existing DHT commands
- Use UV's native workspace support where possible
- Ensure cross-platform compatibility (Windows, macOS, Linux)

## Progress Tracking

- Total Commands to Implement/Modify: 23
- Completed: 0
- In Progress: 0
- Remaining: 23

Last Updated: 2025-01-20
