# Sequential Pre-commit Setup Guide

This guide explains how to configure pre-commit hooks to run sequentially, preventing system crashes from resource exhaustion during development.

## Problem Statement

When multiple pre-commit hooks run in parallel, they can cause:
- System memory exhaustion
- CPU overload from concurrent subprocesses
- Git operation conflicts
- System crashes on resource-constrained machines

## Solution Overview

Our sequential pre-commit setup ensures:
- Only one hook runs at a time
- Memory is cleared between hook executions
- Resource-intensive operations have memory limits
- Timeouts prevent infinite hangs

## Quick Setup

### Automatic Setup (Recommended)

1. Run the setup script:
   ```bash
   ./setup-sequential-precommit.sh
   ```

2. Add to your shell profile (~/.zshrc or ~/.bashrc):
   ```bash
   export PRE_COMMIT_MAX_WORKERS=1
   export PYTHONDONTWRITEBYTECODE=1
   ```

3. Reload your shell:
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

### Manual Setup

1. Copy the sequential configuration:
   ```bash
   cp .pre-commit-config-sequential.yaml .pre-commit-config.yaml
   ```

2. Create wrapper directory:
   ```bash
   mkdir -p .pre-commit-wrappers
   ```

3. Copy wrapper scripts:
   ```bash
   cp .pre-commit-wrappers/*.sh .pre-commit-wrappers/
   chmod +x .pre-commit-wrappers/*.sh
   ```

4. Install git hook:
   ```bash
   pre-commit install
   ```

## Configuration Details

### Environment Variables

Set these in your shell profile for permanent configuration:

```bash
# Force sequential execution
export PRE_COMMIT_MAX_WORKERS=1

# Prevent Python bytecode generation (saves memory)
export PYTHONDONTWRITEBYTECODE=1

# Disable UV cache during hooks (optional)
export UV_NO_CACHE=1
```

### Key Configuration Changes

The sequential configuration includes:

1. **`require_serial: true`** on all hooks
2. **Memory-limited wrappers** for resource-intensive tools
3. **Reduced Trufflehog scan depth** (HEAD~3 instead of HEAD~10)
4. **30-second timeout** on Trufflehog execution
5. **Local hooks** for mypy and deptry with memory management

### Wrapper Scripts

#### memory-limited-hook.sh
- Limits memory usage to 2GB per hook
- Forces garbage collection after Python operations
- Adds cleanup on exit

#### trufflehog-limited.sh
- 30-second execution timeout
- Reduced git history scan depth
- Graceful termination on timeout

## Usage

### Running Pre-commit

Normal commits automatically use sequential execution:
```bash
git commit -m "your message"
```

Manual execution:
```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run mypy --all-files

# Use wrapper script with additional memory management
./.pre-commit-sequential.sh run --all-files
```

### Monitoring Resource Usage

Check system resources during execution:
```bash
# macOS
vm_stat | grep -E "Pages free|Pages active"

# Linux
free -h
```

### Troubleshooting

If you still experience crashes:

1. **Further reduce parallelism:**
   ```bash
   export PRE_COMMIT_MAX_WORKERS=0  # Completely disable parallel execution
   ```

2. **Skip resource-intensive hooks locally:**
   ```bash
   SKIP=mypy,deptry git commit -m "message"
   ```

3. **Run hooks individually:**
   ```bash
   pre-commit run trailing-whitespace --all-files
   pre-commit run ruff --all-files
   # etc.
   ```

4. **Check for memory leaks:**
   ```bash
   # Monitor memory during hook execution
   while true; do vm_stat | grep "Pages free"; sleep 2; done
   ```

## Reverting to Parallel Execution

To restore the original parallel configuration:

```bash
# Restore original config
cp .pre-commit-config.yaml.backup .pre-commit-config.yaml

# Remove environment variables
unset PRE_COMMIT_MAX_WORKERS
unset PYTHONDONTWRITEBYTECODE
unset UV_NO_CACHE

# Reinstall hooks
pre-commit install
```

## CI/CD Considerations

The sequential configuration skips resource-intensive hooks in CI:
- mypy (run in separate CI job)
- deptry (run in separate CI job)
- trufflehog (run in security-specific workflow)

This prevents CI timeout issues while maintaining code quality checks.

## Performance Impact

Sequential execution increases commit time but provides:
- Stable, crash-free development experience
- Predictable resource usage
- Better error isolation (easier to identify which hook failed)

Typical timing differences:
- Parallel: 10-30 seconds (but may crash)
- Sequential: 30-60 seconds (stable)

## Advanced Configuration

### Custom Memory Limits

Edit `.pre-commit-wrappers/memory-limited-hook.sh`:
```bash
# Change from 2GB to 1GB
ulimit -v 1048576
```

### Hook-Specific Timeouts

Add timeout to any hook:
```yaml
- repo: local
  hooks:
    - id: custom-hook
      name: Custom Hook with Timeout
      entry: timeout 60s your-command
      language: system
```

### Selective Sequential Execution

Run only specific hooks sequentially:
```yaml
- id: resource-intensive-hook
  require_serial: true  # Only this hook runs serially
```

## Best Practices

1. **Close unnecessary applications** before large commits
2. **Commit frequently** with smaller changesets
3. **Use SKIP for temporary bypasses** rather than disabling hooks
4. **Monitor system resources** during initial setup
5. **Adjust memory limits** based on your system capacity

## Additional Resources

- [Pre-commit documentation](https://pre-commit.com/)
- [Resource management in Git hooks](https://git-scm.com/docs/githooks)
- [macOS memory management](https://support.apple.com/guide/activity-monitor/view-memory-usage)

## Support

If you continue experiencing issues:
1. Check system logs: `Console.app` on macOS
2. Review crash reports: `/Library/Logs/DiagnosticReports/`
3. Reduce concurrent operations in other tools (VS Code, browsers, etc.)
4. Consider upgrading system RAM if crashes persist

Remember: Sequential execution trades speed for stability, which is often worthwhile during active development.