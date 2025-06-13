# Act vs Actionlint: Understanding the Difference

## Overview

**Act** and **actionlint** are complementary tools for GitHub Actions, but they serve very different purposes:

### Actionlint
- **Purpose**: Static analysis and linting of GitHub Actions workflow files
- **What it does**: Validates YAML syntax, checks for configuration errors, and identifies potential issues
- **When to use**: Before committing workflow changes to catch syntax and logic errors
- **Output**: Error messages and warnings about workflow configuration

### Act
- **Purpose**: Runs GitHub Actions workflows locally
- **What it does**: Actually executes the jobs and steps defined in workflows
- **When to use**: To test if workflows will run successfully without pushing to GitHub
- **Output**: The actual output from running commands, tests, builds, etc.

## Key Differences

| Feature | Actionlint | Act |
|---------|------------|-----|
| **Function** | Linter (static analysis) | Runner (execution) |
| **Checks syntax** | ✅ Yes | ❌ No |
| **Executes workflows** | ❌ No | ✅ Yes |
| **Runs build commands** | ❌ No | ✅ Yes |
| **Needs Docker/Podman** | Optional | Required |
| **Speed** | Very fast (seconds) | Slower (minutes) |
| **Resource usage** | Minimal | High (runs containers) |

## When to Use Each

### Use Actionlint when you want to:
- Quickly validate workflow syntax
- Check for common mistakes in workflow files
- Integrate linting into pre-commit hooks
- Get immediate feedback on workflow structure

### Use Act when you want to:
- Test if your build/test commands actually work
- Debug failing CI/CD pipelines locally
- Verify workflow behavior before pushing
- Save GitHub Actions minutes

## Example Usage

### Actionlint (for validation)
```bash
# Check all workflows
actionlint

# Check specific workflow
actionlint .github/workflows/build.yml

# Using Docker
docker run --rm -v $(pwd):/repo --workdir /repo rhysd/actionlint:latest
```

### Act (for execution)
```bash
# Run push event workflows
act push

# Run specific job
act -j test

# List what would run
act -l
```

## DHT Integration

In DHT, we use both tools:

1. **Actionlint** is integrated for quick validation:
   - Runs during `dhtl act --lint`
   - Checks syntax before attempting to run workflows
   - Provides fast feedback

2. **Act** is integrated for actual testing:
   - Runs during `dhtl act`
   - Executes workflows in containers
   - Simulates GitHub's environment

## Best Practice Workflow

1. Write/modify workflow files
2. Run `actionlint` to validate syntax ✓
3. Run `act` to test execution ✓
4. Commit and push to GitHub ✓

This two-step approach catches both configuration errors (actionlint) and runtime errors (act) before they reach your repository.