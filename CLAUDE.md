# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## General Development Guidelines and Rules
- *CRITICAL*: when reading the lines of the source files, do not read just few lines like you usually do. Instead always read all the lines of the file (until you reach the limit of available context memory). No matter what is the situation, searching or editing a file, ALWAYS OBEY TO THIS RULE!!!.
- *CRITICAL*: do not ever do unplanned things or take decisions without asking the user first. All non trivial changes to the code must be planned first, approved by the user, and added to the tasks_checklist.md first. Unless something was specifically instructed by the user, you must not do it. Do not make changes to the codebase without duscussing those with the user first and get those approved. Be conservative and act on a strict need-to-be-changed basis.
- *CRITICAL*: COMMIT AFTER EACH CHANGE TO THE CODE, NO MATTER HOW SMALL!!!
- *CRITICAL*: after receiving instructions from the user, before you proceed, confirm if you understand and tell the user your plan. If instead you do not understand something, or if there are choices to make, ask the user to clarify, then tell the user your plan. Do not proceed with the plan if the user does not approve it.
- *CRITICAL*: **Auto-Lint after changes**: Always run the linters (like ruff, shellcheck, mypy, yamllint, eslint, etc.) after any changes to the code files! ALWAYS DO IT BEFORE COMMITTING!!
- *CRITICAL*: **Ultrathink before acting**: always ultrathink! Your thinking capabilities are not just for show. USE THEM!!!
- *CRITICAL*: Never use GREP! Use RIPGREP instead!
- *CRITICAL*: Never use pip. Use `uv pip <commands>` instead. Consider pip deprecated in favor of uv pip.
- be extremely meticulous and accurate. always check twice any line of code for errors when you edit it.
- never output code that is abridged or with parts replaced by placeholder comments like `# ... rest of the code ...`, `# ... rest of the function as before ...`, `# ... rest of the code remains the same ...`, or similar. You are not chatting. The code you output is going to be saved and linted, so omitting parts of it will cause errors and broken files.
- Be conservative. only change the code that it is strictly necessary to change to implement a feature or fix an issue. Do not change anything else. You must report the user if there is a way to improve certain parts of the code, but do not attempt to do it unless the user explicitly asks you to.
- when fixing the code, if you find that there are multiple possible solutions, do not start immediately but first present the user all the options and ask him to choose the one to try. For trivial bugs you don't need to do this, of course.
- never remove unused code or variables unless they are wrong, since the program is a WIP and those unused parts are likely going to be developed and used in the future. The only exception is if the user explicitly tells you to do it.
- don't worry about functions imported from external modules, since those dependencies cannot be always included in the chat for your context limit. Do not remove them or implement them just because you can''t find the module or source file they are imported from. You just assume that the imported modules and imported functions work as expected. If you need to change them, ask the user to include them in the chat.
- Always update the project version after changes. Use semantic version format for updating the project version: `{major - breaking changes or features}.{minor - non breaking changes or features}.{patch - small changes/fixes}`.
- spend a long time thinking deeply to understand completely the code flow and inner working of the program before writing any code or making any change.
- if the user asks you to implement a feature or to make a change, always check the source code to ensure that the feature was not already implemented before or it is implemented in another form. Never start a task without checking if that task was already implemented or done somewhere in the codebase.
- if you must write a function, always check if there are already similar functions that can be extended or parametrized to do what new function need to do. Avoid writing duplicated or similar code by reusing the same flexible helper functions where is possible.
- keep the source files as small as possible. If you need to create new functions or classes, prefer creating them in new modules in new files and import them instead of putting them in the same source file that will use them. Small reusable modules are always preferable to big functions and spaghetti code.
- Always check for leaks of secrets in the git repo with `gitleaks git --verbose` and `gitleaks dir --verbose`.
- commit should be atomic, specific, and focus on WHAT changed in subject line with WHY explained in body when needed.
- use semantic commit messages following the format in the Git Commit Message Format memory
- Write only shippable, production ready code. If you wouldn’t ship it, don’t write it.
- Don't drastically change existing patterns without explicit instruction
- before you execute a terminal command, trigger the command line syntax help or use `cheat <command>` to learn the correct syntax and avoid failed commands.
- if you attempt to run a command and the command is not found, first check the path, and then install it using `brew install`.
- never take shortcuts to skirt around errors. fix them.
- If the solution to a problem is not obvious, take a step back and look at the bigger picture.
- If you are unsure, stop and ask the user for help or additional information.
- if something you are trying to implement or fix does not work, do not fallback to a simpler solution and do not use workarounds to avoid implement it. Do not give up or compromise with a lesser solution. You must always attempt to implement the original planned solution, and if after many attempts it still fails, ask the user for instructions.
- always use type annotations
- always keep the size of source code files below 10Kb. If writing new code in a source file will make the file size bigger than 10Kb, create a new source file , write the code there, and import it as a module. Refactor big files in multiple smaller modules.
- always preserve comments and add them when writing new code.
- always write the docstrings of all functions and improve the existing ones. Use Google-style docstrings with Args/Returns sections, but do not use markdown.
- never use markdown in comments.
- when using the Bash tool, always set the timeout parameter to 1800000 (30 minutes).
- always tabulate the tests result in a nice table.
- do not use mockup tests or mocked behaviours unless it is absolutely impossible to do otherwise. If you need to use a service, local or remote, do not mock it, just ask the user to activate it for the duration of the tests. Results of mocked tests are completely useless. Only real tests can discover issues with the codebase.
- always use a **Test-Driven Development (TDD)** methodology (write tests first, the implementation later) when implementing new features or change the existing ones. But first check that the existing tests are written correctly.
- always plan in advance your actions, and break down your plan into very small tasks. Save a file named `DEVELOPMENT_PLAN.md` and write all tasks inside it. Update it with the status of each tasks after any changes.
- Plan all the changes in detail first. Identify potential issues before starting, and revise the plan until it will not create issues before starting.
- When making changes, identify all files that would need import updates first
- After each change, check all type annotations for consistency
- Make all changes in a single, well-planned operation with surgical edits
- Always lint the file after making all the changes to it, but not before
- Always run the tests relevant to the changed files after making all the changes planned, but not before
- Do one comprehensive commit at the end of each operation if the code passes the tests
- If you make errors while implementing the changes, examine you errors, ultrathink about them and write the lessons learned from them into CLAUDE.md for future references, so you won't repeat the same errors in the future.
- Use Prefect for all scripted processing ( https://github.com/PrefectHQ/prefect/ ), with max_concurrency=1 for max safety.
- Install `https://github.com/fpgmaas/deptry/` and run it at every commit.
- Add deptry to the project pre-commit configuration following these instructions: `https://github.com/astral-sh/uv-pre-commit`.
- Add deptry to both the local and the remote github workflows actions, so it can be used in the CI/CD pipeline automatically at every push/release as instructed here: `https://docs.astral.sh/uv/guides/integration/github/`.
- Install and run yamllint and actionlint at each commit (add them to pre-commit both local and remote, run them with `uv run`).
- You can run the github yaml files locally with `act`. Install act and read the docs to configure it to work with uv: `https://github.com/nektos/act`.
- Since `act` requires Docker, follow these instructions to setup docker containers with uv: https://docs.astral.sh/uv/guides/integration/docker/
- do not create prototypes or sketched/abridged versions of the features you need to develop. That is only a waste of time. Instead break down the new features in its elemental components and functions, subdivide it in small autonomous modules with a specific function, and develop one module at time. When each module will be completed (passing the test for the module), then you will be able to implement the original feature easily just combining the modules. The modules can be helper functions, data structures, external librries, anything that is focused and reusable. Prefer functions at classes, but you can create small classes as specialized handlers for certain data and tasks, then also classes can be used as pieces for building the final feature.
- When commit, never mention Claude as the author of the commits or as a Co-author.
- when refactoring, enter thinking mode first, examine the program flow, be attentive to what you're changing, and how it subsequently affects the rest of the codebase as a matter of its blast radius, the codebase landscape, and possible regressions. Also bear in mind the existing type structures and interfaces that compose the makeup of the specific code you're changing.
- Generate complete, tested code on first attempt.
- Always anchor with date/time and available tools.
- Clearly label the 4 TDD phases (analysis --> tests implementation --> code implementation -> debugging).
- Implement concrete solutions, no placeholders or abridged versions.
- Batch related tool calls and parallelize where safe.
- Proactively handle all edge cases on first attempt.
- Before marking a todo as complete, always spawn a subagent that especially checks the edited test files for tampering, then lint both the edited tests files and the edited code files, and finally run the tests relative to that todo again. If the tests pass, mark the todo task as complete.
- always use `Emasoft` as the user name, author and committer name for the git repo.
- always use `713559+Emasoft@users.noreply.github.com` as the user email and git committer email for the git repo.
- always add the following shebang at the beginning of each python file:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
```
- always add a short changelog before the imports in of the source code to document all the changes you made to it.

```python
# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# <your changelog here…>
#
```

### Formatting Rules
- Use only ruff format for formatting python files. Read how here: https://docs.astral.sh/ruff/formatter/
- Set ruff format to allows line lenght up to 400 chars, using the `--line-length=400`
- Do not use pyproject.toml or ruff.toml to configure ruff, since there are too many variations of the command used in the workflows. Aleays run it in isolated mode with `--isolated` and set all options via cli.
- Use autofix to format pull-requests automatically. Read how here: https://autofix.ci/setup
- Use Prettier to format all other code files (except python and yaml).
- Use `pnpm run format` to run Prettier on node.js source files.
- Configure Prettier for github formatting actions following the instructions here: `https://prettier.io/docs/ci` and `https://autofix.ci/setup`.
- To format yaml files only use yamlfmt. Install yamlfmt with:
```
go install github.com/google/yamlfmt/cmd/yamlfmt@latest
```

Then create this configuration file (`.yamlfmt`):
```yaml
# .yamlfmt
formatter:
  indent: 2                      # Use 2-space indentation (standard in GitHub workflows)
  retain_line_breaks: true       # Preserve existing blank lines between blocks
  indentless_arrays: true        # Don’t add extra indent before each “-” list item
  scan_folded_as_literal: true   # Keep multi-line “>”-style blocks as-is, avoid collapsing
  trim_trailing_whitespace: true # Remove trailing spaces at end of lines
  eof_newline: true              # Ensure the file ends with exactly one newline
gitignore_excludes: true

```

To use yamlfmt:

```
# Format a single workflow file
yamlfmt -path .github/workflows/ci.yml

# Or format all workflow files
yamlfmt -path .github/workflows
```
- You should place the .yamlfmt file in the root directory of the project.
- You must check the .yamlfmt configuration file to see if you are using different settings (i.e. indent 2 or 4 spaces, etc.)
- Add yamlfmt to the git hooks/uv-pre-commit, so it is automatically executed at each commit.
- IMPORTANT: yamlfmt must not format all yaml files, but only those inside the .github subfolder, since it is configured for the github workflows formatting style. Other yaml files may exist outside the .github folder using different formatting styles. Do not format those files.



### Linting Rules
- Use `ruff check` and mypy for python
- Use autofix to lint pull-requests automatically. Read how here: https://autofix.ci/setup
- Do not use pyproject.toml or ruff.toml to configure `ruff check`, since there are too many variations of the command used in the workflows. Aleays run it in isolated mode with `--isolated` and set all options via cli.
- Use eslint for javascript
- Use shellcheck for bash
- Use actionlint snd yamllint for yaml
- Use jsonlint for json
- Run ruff using this command: `uv run ruff check --ignore E203,E402,E501,E266,W505,F841,F842,F401,W293,I001,UP015,C901,W291 --isolated --fix --output-format full`
- Run mypy using this command: `COLUMNS=400 uv run mypy --strict --show-error-context --pretty --install-types --no-color-output --non-interactive --show-error-codes --show-error-code-links --no-error-summary --follow-imports=normal <files to test or pattern...>`
- use shellcheck-py if you need to use shellcheck from a python script
- Use `pnpm run lint` to run eslint on node.js source files.
- Add git hooks that uses uv-pre-commit to run the linting at each commit, read the guide here: `https://docs.astral.sh/uv/guides/integration/pre-commit/`
- Use deptry to check the dependencies. To install deptry follow hese instructions: `https://github.com/fpgmaas/deptry/`
- Add deptry to the project pre-commit configuration following these instructions: https://github.com/astral-sh/uv-pre-commit .
- Add deptry to both the local and the remote github workflows/ actions, so it can be used in the CI/CD pipeline automatically at every push/release as instructed here: https://docs.astral.sh/uv/guides/integration/github/ .
- Install and run yamllint and actionlint at each commit (add them to pre-commit both local and remote, run them with `uv run`).
- If you need to, you can run the github yaml files locally with `act`. Install act and read the docs to configure it to work with uv: https://github.com/nektos/act





### Testing Rules
- Always use pytest and pytest-cov for testing
- Run tests with uv (`uv run pytest`) or `pnpm run tests`
- For coverage reports: `uv run pytest --cov=. --cov-report=html`
- Add git hooks that uses uv-pre-commit to run the tests at each commit, read the guide here: `https://docs.astral.sh/uv/guides/integration/pre-commit/`
- Always convert the xtests in normal tests. Negative tests are confusing. Just make the test explicitly check for the negative outcome instead, and if the outcome is negative, the test is passed.
- Always show a nicely color formatted table with the list of all tests (the functions, not the file) and the outcome (fail, success, skip, error).
- The table must use unicode border blocks to delimit the cells, thicker for the header row.
- The table should report not only the name of the function, but the description of the test function in the docstrings.
- All tests functions should include a meaningful one-line string that synthetically describes the test and its aim.
- If a test function lacks this description, add it to the source files of the tests.
- All test functions must have docstrings with a short description that will be used by the table to describe the test.
- Mark the slow tests (those usually skipped when running tests on GitHub, or that need some extra big dependencies installed) with the emoji of a snail 🐌. Be sure to account for the extra character in the table formatting.

## GITHUB WORKFLOWS AFTER PUSHING
- Use GH cli tool to interact with github
- Keep synching, linting, formatting, testing and building, releasing and publishing separated in different workflows.
    - synch.yml = update the dependency libraries and the dev tools to the version indicated in the configuration files (i.e. `pyproject.toml`, `package.json`, `requirements-dev.txt`, etc.). Use uv synch for python.
    - lint.yml = lint the code files (ruff, eslint, shellcheck, actionlint, yamllint, jsonlint, pnpm, etc.)
    - format.yml = format the code files (ruff, prettier, yamlfmt, pnpm, etc.)
    - test.yml = run the tests for all code files (pytest, pytest-cov, playwright, etc.)
    - build.yml = build the project packages with uv build
    - release.yml = add a new release to github from the latest build, bump the semantic version and update the changelog
    - publish.yml = publish the ladt release to PyPi and other online indexes
    - metrics.yml = compute varous code metrics and statistics to be used to define the health of the project, the coverage, the issues/bugs open, the repo tars, repo size, etc. to be used in the docs and in the README.md
    - docs.yml = update the README.md file and all the docs with the latest changes. Also update the PyPi package info page if available and up to date.
    - ci.yml = orchestrator for the whole CI pipeline (it calls: synch, lint, format, test, build, release, publish, docs)
    - prfix.yml = review and autofix fix pull requests
    - check.yml = only check the project (it calls: synch, lint, format, test, security).
    - generate.yml = only build the package (it calls: synch, lint, format, test, build)
    - security.yml = some custom security checks, but this is optional since github already checks security. Use it only for project specific checks not included in github controls.
- Do not setup cron jobs. Setup the workflows to be triggered when the code change or there are PR
- Setup the CI/CD pipeline and all workflows to use an uv environment. Read how here: `https://docs.astral.sh/uv/guides/integration/github/`
- Always use uv-pre-commit ( `https://github.com/astral-sh/uv-pre-commit` ). Read how here: `https://docs.astral.sh/uv/guides/integration/pre-commit/`
- Do not use Super-Linter, use a simpler lint workflow that runs tools directly
- Use shellcheck-py if you need to control shellcheck linter from python code.
- Ensure formatting consistency between local and github by using pre-commit hooks with identical commands for the lint workflow and the formatting workflow
- Let the tests autodetect the environment (local or remote/github)
- Make sure the tests have a configuration for remote run on github that is different from the local one. Make API tests flexible so they can use different parameters when run locally and remotely.
- Let the test retry counts and all retry logic in the code be configurable with different max values for local and remote for faster CI execution
- After committing and pushing the project to github, always check if the push passed the github actions and checks. Wait few seconds, according to the average time needed for the lint and tests to run, then use the following commands to retrieve the last logs of the last actions:
```
gh run list --limit <..max number of recent actions logs to list...>
gh run view <... run number ...> --log-failed
```
Example:
```
> gh run list --limit 10
> mkdir -p ./logs && gh run view 15801201757 --log-failed > ./logs/15801201757.log
etc..

```
Then examine the log files saved in the ./logs/ subdir. Think ultrahard to find the causes of the failures. Use actionlint, yamllint and act to test and verify the workflows issues. Then report the issues causing the failings.

## API Configuration
- The system uses OpenRouter API for both renaming and translation phases
- Set `OPENROUTER_API_KEY` environment variable with your OpenRouter API key
- OpenRouter provides unified cost tracking across all models
- Model names are automatically mapped (e.g., "gpt-4o-mini" → "openai/gpt-4o-mini")


### Key Principles for CI/CD Success:

1. **Avoid Super-Linter** - Use a simpler lint workflow that runs tools directly
   - Super-Linter has configuration path issues and is overly complex. Do not use it.
   - Direct tool execution is more transparent and easier to debug

2. **Ensure Local/CI Formatting Consistency** - Use pre-commit hooks in CI workflows
   - Run `uv run pre-commit run <hook> --all-files` in CI instead of direct tool commands
   - This ensures identical behavior between local development and CI

3. **Separate Concerns in Workflows**
   - Keep linting, testing, and building in different workflows
   - This makes failures easier to diagnose and workflows faster to run

4. **Environment-Aware Test Configuration**
   - Tests should detect if running locally vs on GitHub Actions
   - Use environment detection: `is_running_in_test()` function
   - Different retry counts: local (10 retries) vs CI (2 retries)
   - Different timeouts: local (60s max) vs CI (5s max)

5. **Flexible API Tests**
   - Make API tests accept various valid responses, parsing the right tags or the right code blocks and ignoring the remaining text as it is variable
   - If the AI model and the API service support structured json responses, make use of them to get deterministic responses. If you use Openrouter, read the following: `https://openrouter.ai/docs/features/structured-outputs`. You can find the list of models supporting structured output here: `https://openrouter.ai/models?fmt=table&order=context-high-to-low&supported_parameters=structured_outputs`.
   - Put in place boundaries and measures to prevent the risks of consuming too many tokens (and spending too much money) when running API requests during the tests.
   - If the model allows API configuration variations, set up 2 or 3 example configurations max, choosing the most significant ones. Do not attempt to tests all possible combinations of API options.
   - If the project supports both remote API services and local API services or models, do not run the tests for the local ones when on github, since local models are not available there.
   - Set two profiles for the tests, LOCAL and REMOTE-CI (github).

6. **Configurable Retry Logic**
   - Use constants like `DEFAULT_MAX_RETRIES` and `DEFAULT_MAX_RETRIES_TEST`
   - Check environment in retry decorators to use appropriate values
   - Reduces CI execution time from 10+ minutes to ~2 minutes

### Implementation Example:
```python
def is_running_in_test() -> bool:
    """Detect if code is running in a test environment."""
    return ("pytest" in sys.modules or
            os.environ.get("PYTEST_CURRENT_TEST") or
            os.environ.get("CI") or
            os.environ.get("GITHUB_ACTIONS"))
```

## pre-commit: install it with uv

It is recommended to install pre-commit using uv’s tool mechanism, using this command:

```
$ uv tool install pre-commit --with pre-commit-uv
```

Running it, you’ll see output describing the installation process:

```
$ uv tool install pre-commit --with pre-commit-uv
Resolved 11 packages in 1ms
Installed 11 packages in 8ms
...
Installed 1 executable: pre-commit
```

This will put the `pre-commit` executable in `~/.local/bin` or similar (per the documentation). You should then be able to run it from anywhere:

```
$ pre-commit --version
pre-commit 4.2.0 (pre-commit-uv=4.1.4, uv=0.7.2)
```

The install command also adds [pre-commit-uv](https://pypi.org/project/pre-commit-uv/), a plugin that patches pre-commit to use uv to install Python-based tools. This drastically speeds up using Python-based hooks, a common use case. (Unfortunately, it seems pre-commit itself won’t be adding uv support.)

With pre-commit installed globally, you can now install its Git hook in relevant repositories per usual:

```
$ cd myrepo

$ pre-commit install
pre-commit installed at .git/hooks/pre-commit

$ pre-commit run --all-files
[INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Using pre-commit with uv 0.7.2 via pre-commit-uv 4.1.4
check for added large files..............................................Passed
check for merge conflicts................................................Passed
trim trailing whitespace.................................................Passed
```

## Upgrade pre-commit

To upgrade pre-commit installed this way, run:

```
$ uv tool upgrade pre-commit
```

For example:

```
$ uv tool upgrade pre-commit
Updated pre-commit v4.1.0 -> v4.2.0
 - pre-commit==4.1.0
 + pre-commit==4.2.0
Installed 1 executable: pre-commit
```

This command upgrades pre-commit and all of its dependencies, in its managed environment.
For more information, read the uv tool upgrade documentation: `https://docs.astral.sh/uv/concepts/tools/`




## Project DHT Overview

DHT (Development Helper Toolkit) is a portable, project-independent toolkit that provides standardized development workflows, environment management, and project automation. It's primarily shell-script based with deep Python integration, designed to work across macOS, Linux, and Windows (Git Bash).

## Core Philosophy: Deterministic Builds Through Functional Equivalence

**"Identical behavior matters more than identical binaries"**

DHT ensures that code written on any platform will build and run identically everywhere else by focusing on:
1. **Version-based validation** over hash matching (same version = same behavior)
2. **Tool isolation** preventing version conflicts
3. **Platform normalization** abstracting OS differences
4. **Deterministic environments** with controlled conditions
5. **Strict verification** catching issues early

## Vision

DHT aims to be a comprehensive development automation tool that enables developers to:
- Set up new projects from scratch in minutes
- Clone/fork/unzip projects with automatic environment regeneration
- Dockerize any Python project with `dhtl dockerize` command
- Handle multi-language projects wrapped in Python (C++, Go, Rust, Node.js)
- Provide deterministic, relocatable environments across platforms
- Automate CI/CD, testing, documentation, and deployment workflows
- Manage tasks through a queue system (potentially using Prefect)

The goal is to eliminate repetitive setup tasks and provide intelligent project analysis that adapts to any codebase structure.


## GITHUB WORKFLOWS AFTER PUSHING
After commit and pushing the project to github, always check if the push passed the github actions and checks.
Wait few seconds, according to the average time needed for the lint and tests to run, then use the following commands to retrieve the last logs of the last actions:
```
gh run list --limit <..max number of recent actions logs to list...>
gh run view <... run number ...> --log-failed
```
Example:
```
> gh run list --limit 10
> mkdir -p ./logs && gh run view 15801201757 --log-failed > ./logs/15801201757.log
etc..

```
Then examine the log files saved in the ./logs/ subdir. Think ultrahard to find the causes. Use actionlint, yamllint and act to test and verify the workflows issues. Then report the issues causing the failings.



## Common Development Commands

- Use Prefect for all scripted processing ( https://github.com/PrefectHQ/prefect/ ), with max_concurrency=1 for max safety.

### Build and Package Management

# Build the Python package
dhtl build

# Build using uv (fast Python package management)
dhtl uv build


### Testing

# Run all tests (uses pytest with 15min timeout)
dhtl test

# Run specific tests using pytest -k pattern
dhtl test -k "test_cli_version or test_basic"

# Run tests with coverage
dhtl test --coverage

# Run DHT's internal self-tests
dhtl test_dht


## Frontend only
uv run pnpm run dev


### Testing

# All tests (if no dhtl present)
uv run bash runtests.sh

# Python tests only
uv run pytest .
uv run pytest ./tests/test_file.py         # Specific file
uv run pytest ./tests/test_file.py::test_function  # Specific test
uv run pytest -k "test_name"               # By test name pattern
uv run pytest -m "not slow"                # Skip slow tests

# Frontend E2E tests
uv run pnpm run e2e
uv run npx playwright test                        # Alternative
uv run npx playwright test --ui                   # With UI mode


### Code Quality

# Run all linters (pre-commit, ruff, black, mypy, shellcheck, yamllint)
dhtl lint

# Lint with automatic fixes
dhtl lint --fix

# Format all code (uses ruff format, black, isort)
dhtl format

# Check formatting without changes
dhtl format --check

### Code Quality

# Python formatting and linting commands syntax:
uv run ruff format       # format with ruff
uv run ruff check --ignore E203,E402,E501,E266,W505,F841,F842,F401,W293,I001,UP015,C901,W291 --isolated --fix --output-format full
COLUMNS=400 uv run mypy --strict --show-error-context --pretty --install-types --no-color-output --non-interactive --show-error-codes --show-error-code-links --no-error-summary --follow-imports=normal <files to test or pattern...>

# TypeScript/JavaScript formatting and linting commands syntax to use internally in dhtl:
uv run pnpm run lint            # ESLint
uv run pnpm run format          # Prettier
uv run pnpm run check           # Check formatting without fixing

# Bash scripts linting commands syntax to use internally in dhtl:
uv run shellcheck --severity=error --extended-analysis=true  # Shellcheck (always use severity=error!)

# YAML scripts linting
uv run yamllint
uv run actionlint

# Gitleaks and secrets preservation
gitleaks git --verbose
gitleaks dir --verbose


### Building and Packaging

# Frontend build
uv run pnpm run build

# Build Python package (includes Electron app)
uv run bash ./install.sh              # Full installation from source
uv init                   # Init package with uv, creating pyproject.toml file, git and others
uv init --python 3.10     # Init package with a specific python version
uv init --app             # Init package with app configuration
uv init --lib             # Init package with library module configuration
uv python install 3.10    # Download and install a specific version of Python runtime
uv python pin 3.10        # Change python version for current venv
uv add <..module..>       # Add module to pyproject.toml dependencies
uv add -r requirements.txt # Add requirements from requirements.txt to pyproject.toml
uv pip install -r requirements.txt # Install dependencies from requirements.txt
uv pip compile <..arguments..> # compile requirement file
uv build                  # Build with uv
uv run python -m build    # Build wheel only

# What uv init generates:
```
.
├── .venv
│   ├── bin
│   ├── lib
│   └── pyvenv.cfg
├── .python-version
├── README.md
├── main.py
├── pyproject.toml
└── uv.lock

```

# What pyproject.toml contains:

```
[project]
name = "hello-world"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
dependencies = []

```

# What the file .python-version contains
The .python-version file contains the project's default Python version. This file tells uv which Python version to use when creating the project's virtual environment.

# What the .venv folder contains
The .venv folder contains your project's virtual environment, a Python environment that is isolated from the rest of your system. This is where uv will install your project's dependencies and binaries.

# What the file uv.lock contains:
uv.lock is a cross-platform lockfile that contains exact information about your project's dependencies. Unlike the pyproject.toml which is used to specify the broad requirements of your project, the lockfile contains the exact resolved versions that are installed in the project environment. This file should be checked into version control, allowing for consistent and reproducible installations across machines.
uv.lock is a human-readable TOML file but is managed by uv and should not be edited manually.

# Install package
uv pip install dist/*.whl    # Install built wheel
uv pip install -e .         # Development install

# Install global uv tools
uv tools install ruff
uv tools install mypy
uv tools install yamllint
uv tools install bump_my_version
...etc.

# Execute globally installed uv tools
uv tools run ruff <..arguments..>
uv tools run mypy <..arguments..>
uv tools run yamllint <..arguments..>
uv tools run bump_my_version <..arguments..>
...etc.


## More detailed list of options for the uv venv command:
Create a virtual environment

Usage: uv venv [OPTIONS] [PATH]

Arguments:
  [PATH]  The path to the virtual environment to create

Options:
      --no-project                           Avoid discovering a project or workspace
      --seed                                 Install seed packages (one or more of: `pip`, `setuptools`, and `wheel`) into the virtual environment [env:
                                             UV_VENV_SEED=]
      --allow-existing                       Preserve any existing files or directories at the target path
      --prompt <PROMPT>                      Provide an alternative prompt prefix for the virtual environment.
      --system-site-packages                 Give the virtual environment access to the system site packages directory
      --relocatable                          Make the virtual environment relocatable
      --index-strategy <INDEX_STRATEGY>      The strategy to use when resolving against multiple index URLs [env: UV_INDEX_STRATEGY=] [possible values:
                                             first-index, unsafe-first-match, unsafe-best-match]
      --keyring-provider <KEYRING_PROVIDER>  Attempt to use `keyring` for authentication for index URLs [env: UV_KEYRING_PROVIDER=] [possible values: disabled,
                                             subprocess]
      --exclude-newer <EXCLUDE_NEWER>        Limit candidate packages to those that were uploaded prior to the given date [env: UV_EXCLUDE_NEWER=]
      --link-mode <LINK_MODE>                The method to use when installing packages from the global cache [env: UV_LINK_MODE=] [possible values: clone, copy,
                                             hardlink, symlink]

Python options:
  -p, --python <PYTHON>      The Python interpreter to use for the virtual environment. [env: UV_PYTHON=]
      --managed-python       Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
      --no-managed-python    Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
      --no-python-downloads  Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Index options:
      --index <INDEX>                      The URLs to use when resolving dependencies, in addition to the default index [env: UV_INDEX=]
      --default-index <DEFAULT_INDEX>      The URL of the default package index (by default: <https://pypi.org/simple>) [env: UV_DEFAULT_INDEX=]
  -i, --index-url <INDEX_URL>              (Deprecated: use `--default-index` instead) The URL of the Python package index (by default: <https://pypi.org/simple>)
                                           [env: UV_INDEX_URL=]
      --extra-index-url <EXTRA_INDEX_URL>  (Deprecated: use `--index` instead) Extra URLs of package indexes to use, in addition to `--index-url` [env:
                                           UV_EXTRA_INDEX_URL=]
  -f, --find-links <FIND_LINKS>            Locations to search for candidate distributions, in addition to those found in the registry indexes [env:
                                           UV_FIND_LINKS=]
      --no-index                           Ignore the registry index (e.g., PyPI), instead relying on direct URL dependencies and those provided via `--find-links`

Cache options:
      --refresh                            Refresh all cached data
  -n, --no-cache                           Avoid reading from or writing to the cache, instead using a temporary directory for the duration of the operation [env:
                                           UV_NO_CACHE=]
      --refresh-package <REFRESH_PACKAGE>  Refresh cached data for a specific package
      --cache-dir <CACHE_DIR>              Path to the cache directory [env: UV_CACHE_DIR=]

Global options:
  -q, --quiet...                                   Use quiet output
  -v, --verbose...                                 Use verbose output
      --color <COLOR_CHOICE>                       Control the use of color in output [possible values: auto, always, never]
      --native-tls                                 Whether to load TLS certificates from the platform's native certificate store [env: UV_NATIVE_TLS=]
      --offline                                    Disable network access [env: UV_OFFLINE=]
      --allow-insecure-host <ALLOW_INSECURE_HOST>  Allow insecure connections to a host [env: UV_INSECURE_HOST=]
      --no-progress                                Hide all progress outputs [env: UV_NO_PROGRESS=]
      --directory <DIRECTORY>                      Change to the given directory prior to running the command
      --project <PROJECT>                          Run the command within the given project directory [env: UV_PROJECT=]
      --config-file <CONFIG_FILE>                  The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
      --no-config                                  Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env: UV_NO_CONFIG=]
  -h, --help                                       Display the concise help for this command

Use `uv help venv` for more details.


## More detailed list of options for the uv init command:
Create a new project

Usage: uv init [OPTIONS] [PATH]

Arguments:
  [PATH]  The path to use for the project/script

Options:
      --name <NAME>                    The name of the project
      --bare                           Only create a `pyproject.toml`
      --package                        Set up the project to be built as a Python package
      --no-package                     Do not set up the project to be built as a Python package
      --app                            Create a project for an application
      --lib                            Create a project for a library
      --script                         Create a script
      --description <DESCRIPTION>      Set the project description
      --no-description                 Disable the description for the project
      --vcs <VCS>                      Initialize a version control system for the project [possible values: git, none]
      --build-backend <BUILD_BACKEND>  Initialize a build-backend of choice for the project [possible values: hatch, flit, pdm, poetry, setuptools, maturin,
                                       scikit]
      --no-readme                      Do not create a `README.md` file
      --author-from <AUTHOR_FROM>      Fill in the `authors` field in the `pyproject.toml` [possible values: auto, git, none]
      --no-pin-python                  Do not create a `.python-version` file for the project
      --no-workspace                   Avoid discovering a workspace and create a standalone project

Python options:
  -p, --python <PYTHON>      The Python interpreter to use to determine the minimum supported Python version. [env: UV_PYTHON=]
      --managed-python       Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
      --no-managed-python    Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
      --no-python-downloads  Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Cache options:
  -n, --no-cache               Avoid reading from or writing to the cache, instead using a temporary directory for the duration of the operation [env:
                               UV_NO_CACHE=]
      --cache-dir <CACHE_DIR>  Path to the cache directory [env: UV_CACHE_DIR=]

Global options:
  -q, --quiet...                                   Use quiet output
  -v, --verbose...                                 Use verbose output
      --color <COLOR_CHOICE>                       Control the use of color in output [possible values: auto, always, never]
      --native-tls                                 Whether to load TLS certificates from the platform's native certificate store [env: UV_NATIVE_TLS=]
      --offline                                    Disable network access [env: UV_OFFLINE=]
      --allow-insecure-host <ALLOW_INSECURE_HOST>  Allow insecure connections to a host [env: UV_INSECURE_HOST=]
      --no-progress                                Hide all progress outputs [env: UV_NO_PROGRESS=]
      --directory <DIRECTORY>                      Change to the given directory prior to running the command
      --project <PROJECT>                          Run the command within the given project directory [env: UV_PROJECT=]
      --config-file <CONFIG_FILE>                  The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
      --no-config                                  Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env: UV_NO_CONFIG=]
  -h, --help                                       Display the concise help for this command



## More detailed list of options for uv sync command:
Update the project's environment

Usage: uv sync [OPTIONS]

Options:
      --extra <EXTRA>                            Include optional dependencies from the specified extra name
      --all-extras                               Include all optional dependencies
      --no-extra <NO_EXTRA>                      Exclude the specified optional dependencies, if `--all-extras` is supplied
      --no-dev                                   Disable the development dependency group
      --only-dev                                 Only include the development dependency group
      --group <GROUP>                            Include dependencies from the specified dependency group
      --no-group <NO_GROUP>                      Disable the specified dependency group
      --no-default-groups                        Ignore the default dependency groups
      --only-group <ONLY_GROUP>                  Only include dependencies from the specified dependency group
      --all-groups                               Include dependencies from all dependency groups
      --no-editable                              Install any editable dependencies, including the project and any workspace members, as non-editable [env:
                                                 UV_NO_EDITABLE=]
      --inexact                                  Do not remove extraneous packages present in the environment
      --active                                   Sync dependencies to the active virtual environment
      --no-install-project                       Do not install the current project
      --no-install-workspace                     Do not install any workspace members, including the root project
      --no-install-package <NO_INSTALL_PACKAGE>  Do not install the given package(s)
      --locked                                   Assert that the `uv.lock` will remain unchanged [env: UV_LOCKED=]
      --frozen                                   Sync without updating the `uv.lock` file [env: UV_FROZEN=]
      --dry-run                                  Perform a dry run, without writing the lockfile or modifying the project environment
      --all-packages                             Sync all packages in the workspace
      --package <PACKAGE>                        Sync for a specific package in the workspace
      --script <SCRIPT>                          Sync the environment for a Python script, rather than the current project
      --check                                    Check if the Python environment is synchronized with the project

Index options:
      --index <INDEX>                        The URLs to use when resolving dependencies, in addition to the default index [env: UV_INDEX=]
      --default-index <DEFAULT_INDEX>        The URL of the default package index (by default: <https://pypi.org/simple>) [env: UV_DEFAULT_INDEX=]
  -i, --index-url <INDEX_URL>                (Deprecated: use `--default-index` instead) The URL of the Python package index (by default:
                                             <https://pypi.org/simple>) [env: UV_INDEX_URL=]
      --extra-index-url <EXTRA_INDEX_URL>    (Deprecated: use `--index` instead) Extra URLs of package indexes to use, in addition to `--index-url` [env:
                                             UV_EXTRA_INDEX_URL=]
  -f, --find-links <FIND_LINKS>              Locations to search for candidate distributions, in addition to those found in the registry indexes [env:
                                             UV_FIND_LINKS=]
      --no-index                             Ignore the registry index (e.g., PyPI), instead relying on direct URL dependencies and those provided via
                                             `--find-links`
      --index-strategy <INDEX_STRATEGY>      The strategy to use when resolving against multiple index URLs [env: UV_INDEX_STRATEGY=] [possible values:
                                             first-index, unsafe-first-match, unsafe-best-match]
      --keyring-provider <KEYRING_PROVIDER>  Attempt to use `keyring` for authentication for index URLs [env: UV_KEYRING_PROVIDER=] [possible values: disabled,
                                             subprocess]

Resolver options:
  -U, --upgrade                            Allow package upgrades, ignoring pinned versions in any existing output file. Implies `--refresh`
  -P, --upgrade-package <UPGRADE_PACKAGE>  Allow upgrades for a specific package, ignoring pinned versions in any existing output file. Implies `--refresh-package`
      --resolution <RESOLUTION>            The strategy to use when selecting between the different compatible versions for a given package requirement [env:
                                           UV_RESOLUTION=] [possible values: highest, lowest, lowest-direct]
      --prerelease <PRERELEASE>            The strategy to use when considering pre-release versions [env: UV_PRERELEASE=] [possible values: disallow, allow,
                                           if-necessary, explicit, if-necessary-or-explicit]
      --fork-strategy <FORK_STRATEGY>      The strategy to use when selecting multiple versions of a given package across Python versions and platforms [env:
                                           UV_FORK_STRATEGY=] [possible values: fewest, requires-python]
      --exclude-newer <EXCLUDE_NEWER>      Limit candidate packages to those that were uploaded prior to the given date [env: UV_EXCLUDE_NEWER=]
      --no-sources                         Ignore the `tool.uv.sources` table when resolving dependencies. Used to lock against the standards-compliant,
                                           publishable package metadata, as opposed to using any workspace, Git, URL, or local path sources

Installer options:
      --reinstall                              Reinstall all packages, regardless of whether they're already installed. Implies `--refresh`
      --reinstall-package <REINSTALL_PACKAGE>  Reinstall a specific package, regardless of whether it's already installed. Implies `--refresh-package`
      --link-mode <LINK_MODE>                  The method to use when installing packages from the global cache [env: UV_LINK_MODE=] [possible values: clone, copy,
                                               hardlink, symlink]
      --compile-bytecode                       Compile Python files to bytecode after installation [env: UV_COMPILE_BYTECODE=]

Build options:
  -C, --config-setting <CONFIG_SETTING>                          Settings to pass to the PEP 517 build backend, specified as `KEY=VALUE` pairs
      --no-build-isolation                                       Disable isolation when building source distributions [env: UV_NO_BUILD_ISOLATION=]
      --no-build-isolation-package <NO_BUILD_ISOLATION_PACKAGE>  Disable isolation when building source distributions for a specific package
      --no-build                                                 Don't build source distributions [env: UV_NO_BUILD=]
      --no-build-package <NO_BUILD_PACKAGE>                      Don't build source distributions for a specific package [env: UV_NO_BUILD_PACKAGE=]
      --no-binary                                                Don't install pre-built wheels [env: UV_NO_BINARY=]
      --no-binary-package <NO_BINARY_PACKAGE>                    Don't install pre-built wheels for a specific package [env: UV_NO_BINARY_PACKAGE=]

Cache options:
  -n, --no-cache                           Avoid reading from or writing to the cache, instead using a temporary directory for the duration of the operation [env:
                                           UV_NO_CACHE=]
      --cache-dir <CACHE_DIR>              Path to the cache directory [env: UV_CACHE_DIR=]
      --refresh                            Refresh all cached data
      --refresh-package <REFRESH_PACKAGE>  Refresh cached data for a specific package

Python options:
  -p, --python <PYTHON>      The Python interpreter to use for the project environment. [env: UV_PYTHON=]
      --managed-python       Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
      --no-managed-python    Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
      --no-python-downloads  Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Global options:
  -q, --quiet...                                   Use quiet output
  -v, --verbose...                                 Use verbose output
      --color <COLOR_CHOICE>                       Control the use of color in output [possible values: auto, always, never]
      --native-tls                                 Whether to load TLS certificates from the platform's native certificate store [env: UV_NATIVE_TLS=]
      --offline                                    Disable network access [env: UV_OFFLINE=]
      --allow-insecure-host <ALLOW_INSECURE_HOST>  Allow insecure connections to a host [env: UV_INSECURE_HOST=]
      --no-progress                                Hide all progress outputs [env: UV_NO_PROGRESS=]
      --directory <DIRECTORY>                      Change to the given directory prior to running the command
      --project <PROJECT>                          Run the command within the given project directory [env: UV_PROJECT=]
      --config-file <CONFIG_FILE>                  The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
      --no-config                                  Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env: UV_NO_CONFIG=]
  -h, --help                                       Display the concise help for this command

Use `uv help sync` for more details.


## More detailed list of options for the uv python command:
Manage Python versions and installations

Usage: uv python [OPTIONS] <COMMAND>

Commands:
  list       List the available Python installations
  install    Download and install Python versions
  find       Search for a Python installation
  pin        Pin to a specific Python version
  dir        Show the uv Python installation directory
  uninstall  Uninstall Python versions

Cache options:
  -n, --no-cache               Avoid reading from or writing to the cache, instead using a temporary directory for the duration of the operation [env:
                               UV_NO_CACHE=]
      --cache-dir <CACHE_DIR>  Path to the cache directory [env: UV_CACHE_DIR=]

Python options:
      --managed-python       Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
      --no-managed-python    Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
      --no-python-downloads  Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Global options:
  -q, --quiet...                                   Use quiet output
  -v, --verbose...                                 Use verbose output
      --color <COLOR_CHOICE>                       Control the use of color in output [possible values: auto, always, never]
      --native-tls                                 Whether to load TLS certificates from the platform's native certificate store [env: UV_NATIVE_TLS=]
      --offline                                    Disable network access [env: UV_OFFLINE=]
      --allow-insecure-host <ALLOW_INSECURE_HOST>  Allow insecure connections to a host [env: UV_INSECURE_HOST=]
      --no-progress                                Hide all progress outputs [env: UV_NO_PROGRESS=]
      --directory <DIRECTORY>                      Change to the given directory prior to running the command
      --project <PROJECT>                          Run the command within the given project directory [env: UV_PROJECT=]
      --config-file <CONFIG_FILE>                  The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
      --no-config                                  Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env: UV_NO_CONFIG=]
  -h, --help                                       Display the concise help for this command

Use `uv help python` for more details.


## More detailed list of options for the uv pip command:
Manage Python packages with a pip-compatible interface

Usage: uv pip [OPTIONS] <COMMAND>

Commands:
  compile    Compile a `requirements.in` file to a `requirements.txt` or `pylock.toml` file
  sync       Sync an environment with a `requirements.txt` or `pylock.toml` file
  install    Install packages into an environment
  uninstall  Uninstall packages from an environment
  freeze     List, in requirements format, packages installed in an environment
  list       List, in tabular format, packages installed in an environment
  show       Show information about one or more installed packages
  tree       Display the dependency tree for an environment
  check      Verify installed packages have compatible dependencies

Cache options:
  -n, --no-cache               Avoid reading from or writing to the cache, instead using a temporary directory for the duration of the operation [env:
                               UV_NO_CACHE=]
      --cache-dir <CACHE_DIR>  Path to the cache directory [env: UV_CACHE_DIR=]

Python options:
      --managed-python       Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
      --no-managed-python    Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
      --no-python-downloads  Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Global options:
  -q, --quiet...                                   Use quiet output
  -v, --verbose...                                 Use verbose output
      --color <COLOR_CHOICE>                       Control the use of color in output [possible values: auto, always, never]
      --native-tls                                 Whether to load TLS certificates from the platform's native certificate store [env: UV_NATIVE_TLS=]
      --offline                                    Disable network access [env: UV_OFFLINE=]
      --allow-insecure-host <ALLOW_INSECURE_HOST>  Allow insecure connections to a host [env: UV_INSECURE_HOST=]
      --no-progress                                Hide all progress outputs [env: UV_NO_PROGRESS=]
      --directory <DIRECTORY>                      Change to the given directory prior to running the command
      --project <PROJECT>                          Run the command within the given project directory [env: UV_PROJECT=]
      --config-file <CONFIG_FILE>                  The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
      --no-config                                  Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env: UV_NO_CONFIG=]
  -h, --help                                       Display the concise help for this command

Use `uv help pip` for more details.



## More detailed list of options for uv build command:
Build Python packages into source distributions and wheels

Usage: uv build [OPTIONS] [SRC]

Arguments:
  [SRC]  The directory from which distributions should be built, or a source distribution archive to build into a wheel

Options:
      --package <PACKAGE>                      Build a specific package in the workspace
      --all-packages                           Builds all packages in the workspace
  -o, --out-dir <OUT_DIR>                      The output directory to which distributions should be written
      --sdist                                  Build a source distribution ("sdist") from the given directory
      --wheel                                  Build a binary distribution ("wheel") from the given directory
      --no-build-logs                          Hide logs from the build backend
      --force-pep517                           Always build through PEP 517, don't use the fast path for the uv build backend
  -b, --build-constraints <BUILD_CONSTRAINTS>  Constrain build dependencies using the given requirements files when building distributions [env:
                                               UV_BUILD_CONSTRAINT=]
      --require-hashes                         Require a matching hash for each requirement [env: UV_REQUIRE_HASHES=]
      --no-verify-hashes                       Disable validation of hashes in the requirements file [env: UV_NO_VERIFY_HASHES=]

Python options:
  -p, --python <PYTHON>      The Python interpreter to use for the build environment. [env: UV_PYTHON=]
      --managed-python       Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
      --no-managed-python    Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
      --no-python-downloads  Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Index options:
      --index <INDEX>                        The URLs to use when resolving dependencies, in addition to the default index [env: UV_INDEX=]
      --default-index <DEFAULT_INDEX>        The URL of the default package index (by default: <https://pypi.org/simple>) [env: UV_DEFAULT_INDEX=]
  -i, --index-url <INDEX_URL>                (Deprecated: use `--default-index` instead) The URL of the Python package index (by default:
                                             <https://pypi.org/simple>) [env: UV_INDEX_URL=]
      --extra-index-url <EXTRA_INDEX_URL>    (Deprecated: use `--index` instead) Extra URLs of package indexes to use, in addition to `--index-url` [env:
                                             UV_EXTRA_INDEX_URL=]
  -f, --find-links <FIND_LINKS>              Locations to search for candidate distributions, in addition to those found in the registry indexes [env:
                                             UV_FIND_LINKS=]
      --no-index                             Ignore the registry index (e.g., PyPI), instead relying on direct URL dependencies and those provided via
                                             `--find-links`
      --index-strategy <INDEX_STRATEGY>      The strategy to use when resolving against multiple index URLs [env: UV_INDEX_STRATEGY=] [possible values:
                                             first-index, unsafe-first-match, unsafe-best-match]
      --keyring-provider <KEYRING_PROVIDER>  Attempt to use `keyring` for authentication for index URLs [env: UV_KEYRING_PROVIDER=] [possible values: disabled,
                                             subprocess]

Resolver options:
  -U, --upgrade                            Allow package upgrades, ignoring pinned versions in any existing output file. Implies `--refresh`
  -P, --upgrade-package <UPGRADE_PACKAGE>  Allow upgrades for a specific package, ignoring pinned versions in any existing output file. Implies `--refresh-package`
      --resolution <RESOLUTION>            The strategy to use when selecting between the different compatible versions for a given package requirement [env:
                                           UV_RESOLUTION=] [possible values: highest, lowest, lowest-direct]
      --prerelease <PRERELEASE>            The strategy to use when considering pre-release versions [env: UV_PRERELEASE=] [possible values: disallow, allow,
                                           if-necessary, explicit, if-necessary-or-explicit]
      --fork-strategy <FORK_STRATEGY>      The strategy to use when selecting multiple versions of a given package across Python versions and platforms [env:
                                           UV_FORK_STRATEGY=] [possible values: fewest, requires-python]
      --exclude-newer <EXCLUDE_NEWER>      Limit candidate packages to those that were uploaded prior to the given date [env: UV_EXCLUDE_NEWER=]
      --no-sources                         Ignore the `tool.uv.sources` table when resolving dependencies. Used to lock against the standards-compliant,
                                           publishable package metadata, as opposed to using any workspace, Git, URL, or local path sources

Build options:
  -C, --config-setting <CONFIG_SETTING>                          Settings to pass to the PEP 517 build backend, specified as `KEY=VALUE` pairs
      --no-build-isolation                                       Disable isolation when building source distributions [env: UV_NO_BUILD_ISOLATION=]
      --no-build-isolation-package <NO_BUILD_ISOLATION_PACKAGE>  Disable isolation when building source distributions for a specific package
      --no-build                                                 Don't build source distributions [env: UV_NO_BUILD=]
      --no-build-package <NO_BUILD_PACKAGE>                      Don't build source distributions for a specific package [env: UV_NO_BUILD_PACKAGE=]
      --no-binary                                                Don't install pre-built wheels [env: UV_NO_BINARY=]
      --no-binary-package <NO_BINARY_PACKAGE>                    Don't install pre-built wheels for a specific package [env: UV_NO_BINARY_PACKAGE=]

Installer options:
      --link-mode <LINK_MODE>  The method to use when installing packages from the global cache [env: UV_LINK_MODE=] [possible values: clone, copy, hardlink,
                               symlink]

Cache options:
  -n, --no-cache                           Avoid reading from or writing to the cache, instead using a temporary directory for the duration of the operation [env:
                                           UV_NO_CACHE=]
      --cache-dir <CACHE_DIR>              Path to the cache directory [env: UV_CACHE_DIR=]
      --refresh                            Refresh all cached data
      --refresh-package <REFRESH_PACKAGE>  Refresh cached data for a specific package

Global options:
  -q, --quiet...                                   Use quiet output
  -v, --verbose...                                 Use verbose output
      --color <COLOR_CHOICE>                       Control the use of color in output [possible values: auto, always, never]
      --native-tls                                 Whether to load TLS certificates from the platform's native certificate store [env: UV_NATIVE_TLS=]
      --offline                                    Disable network access [env: UV_OFFLINE=]
      --allow-insecure-host <ALLOW_INSECURE_HOST>  Allow insecure connections to a host [env: UV_INSECURE_HOST=]
      --no-progress                                Hide all progress outputs [env: UV_NO_PROGRESS=]
      --directory <DIRECTORY>                      Change to the given directory prior to running the command
      --project <PROJECT>                          Run the command within the given project directory [env: UV_PROJECT=]
      --config-file <CONFIG_FILE>                  The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
      --no-config                                  Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env: UV_NO_CONFIG=]
  -h, --help                                       Display the concise help for this command

Use `uv help build` for more details.


## More detailed list of options for the uv run command:
Run a command or script

Usage: uv run [OPTIONS] [COMMAND]

Options:
      --extra <EXTRA>                          Include optional dependencies from the specified extra name
      --all-extras                             Include all optional dependencies
      --no-extra <NO_EXTRA>                    Exclude the specified optional dependencies, if `--all-extras` is supplied
      --no-dev                                 Disable the development dependency group
      --group <GROUP>                          Include dependencies from the specified dependency group
      --no-group <NO_GROUP>                    Disable the specified dependency group
      --no-default-groups                      Ignore the default dependency groups
      --only-group <ONLY_GROUP>                Only include dependencies from the specified dependency group
      --all-groups                             Include dependencies from all dependency groups
  -m, --module                                 Run a Python module
      --only-dev                               Only include the development dependency group
      --no-editable                            Install any editable dependencies, including the project and any workspace members, as non-editable [env:
                                               UV_NO_EDITABLE=]
      --exact                                  Perform an exact sync, removing extraneous packages
      --env-file <ENV_FILE>                    Load environment variables from a `.env` file [env: UV_ENV_FILE=]
      --no-env-file                            Avoid reading environment variables from a `.env` file [env: UV_NO_ENV_FILE=]
      --with <WITH>                            Run with the given packages installed
      --with-editable <WITH_EDITABLE>          Run with the given packages installed in editable mode
      --with-requirements <WITH_REQUIREMENTS>  Run with all packages listed in the given `requirements.txt` files
      --isolated                               Run the command in an isolated virtual environment
      --active                                 Prefer the active virtual environment over the project's virtual environment
      --no-sync                                Avoid syncing the virtual environment [env: UV_NO_SYNC=]
      --locked                                 Assert that the `uv.lock` will remain unchanged [env: UV_LOCKED=]
      --frozen                                 Run without updating the `uv.lock` file [env: UV_FROZEN=]
  -s, --script                                 Run the given path as a Python script
      --gui-script                             Run the given path as a Python GUI script
      --all-packages                           Run the command with all workspace members installed
      --package <PACKAGE>                      Run the command in a specific package in the workspace
      --no-project                             Avoid discovering the project or workspace

Index options:
      --index <INDEX>                        The URLs to use when resolving dependencies, in addition to the default index [env: UV_INDEX=]
      --default-index <DEFAULT_INDEX>        The URL of the default package index (by default: <https://pypi.org/simple>) [env: UV_DEFAULT_INDEX=]
  -i, --index-url <INDEX_URL>                (Deprecated: use `--default-index` instead) The URL of the Python package index (by default:
                                             <https://pypi.org/simple>) [env: UV_INDEX_URL=]
      --extra-index-url <EXTRA_INDEX_URL>    (Deprecated: use `--index` instead) Extra URLs of package indexes to use, in addition to `--index-url` [env:
                                             UV_EXTRA_INDEX_URL=]
  -f, --find-links <FIND_LINKS>              Locations to search for candidate distributions, in addition to those found in the registry indexes [env:
                                             UV_FIND_LINKS=]
      --no-index                             Ignore the registry index (e.g., PyPI), instead relying on direct URL dependencies and those provided via
                                             `--find-links`
      --index-strategy <INDEX_STRATEGY>      The strategy to use when resolving against multiple index URLs [env: UV_INDEX_STRATEGY=] [possible values:
                                             first-index, unsafe-first-match, unsafe-best-match]
      --keyring-provider <KEYRING_PROVIDER>  Attempt to use `keyring` for authentication for index URLs [env: UV_KEYRING_PROVIDER=] [possible values: disabled,
                                             subprocess]

Resolver options:
  -U, --upgrade                            Allow package upgrades, ignoring pinned versions in any existing output file. Implies `--refresh`
  -P, --upgrade-package <UPGRADE_PACKAGE>  Allow upgrades for a specific package, ignoring pinned versions in any existing output file. Implies `--refresh-package`
      --resolution <RESOLUTION>            The strategy to use when selecting between the different compatible versions for a given package requirement [env:
                                           UV_RESOLUTION=] [possible values: highest, lowest, lowest-direct]
      --prerelease <PRERELEASE>            The strategy to use when considering pre-release versions [env: UV_PRERELEASE=] [possible values: disallow, allow,
                                           if-necessary, explicit, if-necessary-or-explicit]
      --fork-strategy <FORK_STRATEGY>      The strategy to use when selecting multiple versions of a given package across Python versions and platforms [env:
                                           UV_FORK_STRATEGY=] [possible values: fewest, requires-python]
      --exclude-newer <EXCLUDE_NEWER>      Limit candidate packages to those that were uploaded prior to the given date [env: UV_EXCLUDE_NEWER=]
      --no-sources                         Ignore the `tool.uv.sources` table when resolving dependencies. Used to lock against the standards-compliant,
                                           publishable package metadata, as opposed to using any workspace, Git, URL, or local path sources

Installer options:
      --reinstall                              Reinstall all packages, regardless of whether they're already installed. Implies `--refresh`
      --reinstall-package <REINSTALL_PACKAGE>  Reinstall a specific package, regardless of whether it's already installed. Implies `--refresh-package`
      --link-mode <LINK_MODE>                  The method to use when installing packages from the global cache [env: UV_LINK_MODE=] [possible values: clone, copy,
                                               hardlink, symlink]
      --compile-bytecode                       Compile Python files to bytecode after installation [env: UV_COMPILE_BYTECODE=]

Build options:
  -C, --config-setting <CONFIG_SETTING>                          Settings to pass to the PEP 517 build backend, specified as `KEY=VALUE` pairs
      --no-build-isolation                                       Disable isolation when building source distributions [env: UV_NO_BUILD_ISOLATION=]
      --no-build-isolation-package <NO_BUILD_ISOLATION_PACKAGE>  Disable isolation when building source distributions for a specific package
      --no-build                                                 Don't build source distributions [env: UV_NO_BUILD=]
      --no-build-package <NO_BUILD_PACKAGE>                      Don't build source distributions for a specific package [env: UV_NO_BUILD_PACKAGE=]
      --no-binary                                                Don't install pre-built wheels [env: UV_NO_BINARY=]
      --no-binary-package <NO_BINARY_PACKAGE>                    Don't install pre-built wheels for a specific package [env: UV_NO_BINARY_PACKAGE=]

Cache options:
  -n, --no-cache                           Avoid reading from or writing to the cache, instead using a temporary directory for the duration of the operation [env:
                                           UV_NO_CACHE=]
      --cache-dir <CACHE_DIR>              Path to the cache directory [env: UV_CACHE_DIR=]
      --refresh                            Refresh all cached data
      --refresh-package <REFRESH_PACKAGE>  Refresh cached data for a specific package

Python options:
  -p, --python <PYTHON>      The Python interpreter to use for the run environment. [env: UV_PYTHON=]
      --managed-python       Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
      --no-managed-python    Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
      --no-python-downloads  Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Global options:
  -q, --quiet...                                   Use quiet output
  -v, --verbose...                                 Use verbose output
      --color <COLOR_CHOICE>                       Control the use of color in output [possible values: auto, always, never]
      --native-tls                                 Whether to load TLS certificates from the platform's native certificate store [env: UV_NATIVE_TLS=]
      --offline                                    Disable network access [env: UV_OFFLINE=]
      --allow-insecure-host <ALLOW_INSECURE_HOST>  Allow insecure connections to a host [env: UV_INSECURE_HOST=]
      --no-progress                                Hide all progress outputs [env: UV_NO_PROGRESS=]
      --directory <DIRECTORY>                      Change to the given directory prior to running the command
      --project <PROJECT>                          Run the command within the given project directory [env: UV_PROJECT=]
      --config-file <CONFIG_FILE>                  The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
      --no-config                                  Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env: UV_NO_CONFIG=]
  -h, --help                                       Display the concise help for this command

Use `uv help run` for more details.


### Environment Setup

# Initial setup (creates venv, installs deps, sets up git hooks)
dhtl setup

# Initialize DHT in a new project
dhtl init

# Restore dependencies from lock files
dhtl restore


### Version Management

# Bump version (patch/minor/major)
dhtl bump patch
dhtl bump minor
dhtl bump major

# Create git tags
dhtl tag --name v1.0.0 --message "Release version 1.0.0"


## Examples Of Development Commands

### Environment Setup
# Python environment (using uv)
uv venv
source .venv/bin/activate  # Linux/macOS
.venv_windows\Scripts\activate     # Windows
uv sync --all-extras       # Install all dependencies

# Node.js dependencies
pnpm install


### Running the Application

# Full stack (frontend + backend)
pnpm run start-project            # macOS/Linux
pnpm run start-project:win        # Windows
pnpm run start-project:debug      # Debug mode

# Backend only
uv run python3 main.py            # or: python main.py on Windows
uv run python3 main.py --log-level debug  # Debug mode

----------------------------------------

TITLE: Creating Virtual Environment with Specific Python Version using uv (Console)
DESCRIPTION: Creates a virtual environment using a specific Python version (e.g., 3.11) with the `uv` tool. Requires the requested Python version to be available or downloadable by uv.
SOURCE: https://github.com/astral-sh/uv/blob/main/docs/pip/environments.md#_snippet_2

LANGUAGE: console
CODE:

$ uv venv --python 3.11


----------------------------------------

TITLE: Creating a Virtual Environment with uv
DESCRIPTION: This command creates a new virtual environment in the current directory using `uv venv`. It automatically detects the appropriate Python version and provides instructions for activating the environment.
SOURCE: https://github.com/astral-sh/uv/blob/main/README.md#_snippet_14

LANGUAGE: console
CODE:

$ uv venv
Using Python 3.12.3
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

------------------------------------------

## Managed and system Python installations with uv
Since it is common for a system to have an existing Python installation, uv supports discovering Python versions. However, uv also supports installing Python versions itself. To distinguish between these two types of Python installations, uv refers to Python versions it installs as managed Python installations and all other Python installations as system Python installations.

Note
uv does not distinguish between Python versions installed by the operating system vs those installed and managed by other tools. For example, if a Python installation is managed with pyenv, it would still be considered a system Python version in uv.


## Requesting a version
A specific Python version can be requested with the --python flag in most uv commands. For example, when creating a virtual environment:


$ uv venv --python 3.11.6

uv will ensure that Python 3.11.6 is available — downloading and installing it if necessary — then create the virtual environment with it.
The following Python version request formats are supported:

	•	<version> (e.g., 3, 3.12, 3.12.3)
	•	<version-specifier> (e.g., >=3.12,<3.13)
	•	<implementation> (e.g., cpython or cp)
	•	<implementation>@<version> (e.g., cpython@3.12)
	•	<implementation><version> (e.g., cpython3.12 or cp312)
	•	<implementation><version-specifier> (e.g., cpython>=3.12,<3.13)
	•	<implementation>-<version>-<os>-<arch>-<libc> (e.g., cpython-3.12.3-macos-aarch64-none)

Additionally, a specific system Python interpreter can be requested with:

	•	<executable-path> (e.g., /opt/homebrew/bin/python3)
	•	<executable-name> (e.g., mypython3)
	•	<install-dir> (e.g., /some/environment/)

By default, uv will automatically download Python versions if they cannot be found on the system. This behavior can be disabled with the python-downloads option.


## Python version files
The .python-version file can be used to create a default Python version request. uv searches for a .python-version file in the working directory and each of its parents. If none is found, uv will check the user-level configuration directory. Any of the request formats described above can be used, though use of a version number is recommended for interoperability with other tools.
A .python-version file can be created in the current directory with the uv python pin command:

## Change to use a specific Python version in the current directory

$ uv python pin 3.11

Pinned `.python-version` to `3.11`


A global .python-version file can be created in the user configuration directory with the uv python pin --global command. (not reccomended)

## Discovery of .python-version files can be disabled with --no-config.
uv will not search for .python-version files beyond project or workspace boundaries (with the exception of the user configuration directory).

## Installing a Python version
uv bundles a list of downloadable CPython and PyPy distributions for macOS, Linux, and Windows.

Tip
By default, Python versions are automatically downloaded as needed without using uv python install.

To install a Python version at a specific version:


$ uv python install 3.12.3

To install the latest patch version:


$ uv python install 3.12

To install a version that satisfies constraints:


$ uv python install '>=3.8,<3.10'

To install multiple versions:


$ uv python install 3.9 3.10 3.11

To install a specific implementation:


$ uv python install pypy

All of the Python version request formats are supported except those that are used for requesting local interpreters such as a file path.
By default uv python install will verify that a managed Python version is installed or install the latest version. If a .python-version file is present, uv will install the Python version listed in the file. A project that requires multiple Python versions may define a .python-versions file. If present, uv will install all of the Python versions listed in the file.

Important:
The available Python versions are frozen for each uv release. To install new Python versions, you may need upgrade uv.

## Installing Python executables

To install Python executables into your PATH, provide the --preview option:


$ uv python install 3.12 --preview
This will install a Python executable for the requested version into ~/.local/bin, e.g., as python3.12.

Tip
If ~/.local/bin is not in your PATH, you can add it with uv tool update-shell.

To install python and python3 executables, include the --default option:


$ uv python install 3.12 --default --preview

When installing Python executables, uv will only overwrite an existing executable if it is managed by uv — e.g., if ~/.local/bin/python3.12 exists already uv will not overwrite it without the --force flag.
uv will update executables that it manages. However, it will prefer the latest patch version of each Python minor version by default. For example:


$ uv python install 3.12.7 --preview  # Adds `python3.12` to `~/.local/bin`

$ uv python install 3.12.6 --preview  # Does not update `python3.12`

$ uv python install 3.12.8 --preview  # Updates `python3.12` to point to 3.12.8

## Project Python versions
uv will respect Python requirements defined in requires-python in the pyproject.toml file during project command invocations. The first Python version that is compatible with the requirement will be used, unless a version is otherwise requested, e.g., via a .python-version file or the --python flag.

## Viewing available Python versions
To list installed and available Python versions:


$ uv python list

To filter the Python versions, provide a request, e.g., to show all Python 3.13 interpreters:


$ uv python list 3.13

Or, to show all PyPy interpreters:


$ uv python list pypy

By default, downloads for other platforms and old patch versions are hidden.
To view all versions:


$ uv python list --all-versions

To view Python versions for other platforms:


$ uv python list --all-platforms

To exclude downloads and only show installed Python versions:


$ uv python list --only-installed

See the uv python list reference for more details.

## Finding a Python executable
To find a Python executable, use the uv python find command:

$ uv python find

By default, this will display the path to the first available Python executable. See the discovery rules for details about how executables are discovered.

This interface also supports many request formats, e.g., to find a Python executable that has a version of 3.11 or newer:

$ uv python find '>=3.11'

By default, uv python find will include Python versions from virtual environments. If a .venv directory is found in the working directory or any of the parent directories or the VIRTUAL_ENV environment variable is set, it will take precedence over any Python executables on the PATH.
To ignore virtual environments, use the --system flag:

$ uv python find --system

But it is not reccomended.

## Discovery of Python versions
When searching for a Python version, the following locations are checked:
	•	Managed Python installations in the UV_PYTHON_INSTALL_DIR.
	•	A Python interpreter on the PATH as python, python3, or python3.x on macOS and Linux, or python.exe on Windows.
	•	On Windows, the Python interpreters in the Windows registry and Microsoft Store Python interpreters (see py --list-paths) that match the requested version.

In some cases, uv allows using a Python version from a virtual environment. In this case, the virtual environment's interpreter will be checked for compatibility with the request before searching for an installation as described above. See the pip-compatible virtual environment discovery documentation for details.
When performing discovery, non-executable files will be ignored. Each discovered executable is queried for metadata to ensure it meets the requested Python version. If the query fails, the executable will be skipped. If the executable satisfies the request, it is used without inspecting additional executables.
When searching for a managed Python version, uv will prefer newer versions first. When searching for a system Python version, uv will use the first compatible version — not the newest version.
If a Python version cannot be found on the system, uv will check for a compatible managed Python version download.

## EXAMPLE OF INSTALLING A VERSION OF PYTHON AND CHANGING IT LATER WITH PIN:

## Install multiple Python versions:


$ uv python install 3.10 3.11 3.12

Searching for Python versions matching: Python 3.10

Searching for Python versions matching: Python 3.11

Searching for Python versions matching: Python 3.12

Installed 3 versions in 3.42s

 + cpython-3.10.14-macos-aarch64-none

 + cpython-3.11.9-macos-aarch64-none

 + cpython-3.12.4-macos-aarch64-none


## Download Python versions as needed:


$ uv venv --python 3.12.0

Using CPython 3.12.0

Creating virtual environment at: .venv

Activate with: source .venv/bin/activate


$ uv run --python pypy@3.8 -- python

Python 3.8.16 (a9dbdca6fc3286b0addd2240f11d97d8e8de187a, Dec 29 2022, 11:45:30)

[PyPy 7.3.11 with GCC Apple LLVM 13.1.6 (clang-1316.0.21.2.5)] on darwin

Type "help", "copyright", "credits" or "license" for more information.


## Change to use a specific Python version in the current directory:


$ uv python pin 3.11

Pinned `.python-version` to `3.11`


------------------------------------------

# Frontend only
pnpm run dev


### Testing

# Python tests only
uv run pytest .
uv run pytest ./tests/test_file.py         # Specific file
uv run pytest ./tests/test_file.py::test_function  # Specific test
uv run pytest -k "test_name"               # By test name pattern
uv run pytest -m "not slow"                # Skip slow tests

# Frontend E2E tests
pnpm run e2e
npx playwright test                        # Alternative
npx playwright test --ui                   # With UI mode


### Code Quality

# Python formatting and linting
just format              # or: uv run ruff format .
just lint                # or: uv run ruff check .
uv run ruff check --fix  # Auto-fix linting issues

# TypeScript/JavaScript
pnpm run lint            # ESLint
pnpm run format          # Prettier
pnpm run check           # Check formatting without fixing



### Building and Packaging

# Frontend build
pnpm run build

# Build Python package (includes Electron app)
./install.sh              # Full installation from source
uv run python -m build    # Build wheel only

# Install package
pip install dist/*.whl    # Install built wheel
pip install -e .         # Development install



## Architecture

### Directory Structure
- `dhtl.py` Main entry point (aliased to dhtl when installed as global cli command from a pip package created with `uv build`)
- `DHT/modules/`: Core functionality split into focused shell modules
  - `orchestrator.sh`: Loads all modules
  - `dhtl_commands_*.sh`: Command implementations (8 files)
  - `dhtl_environment_*.sh`: Environment detection and setup
  - `dhtl_uv.sh`: UV package manager integration
  - `dhtl_guardian_*.sh`: Process runner using Precept for queue and resource management
  - `dhtl_diagnostics.sh`: System diagnostics
  - `dhtl_error_handling.sh`: Error handling utilities

### Python Module Architecture (NEW)
To maintain code quality and adhere to the 10KB file size limit, large Python modules in `src/DHT/modules/` are refactored into smaller, focused modules using a delegation pattern:

#### Refactoring Pattern
When a Python file exceeds 10KB, it's split into:
1. **Main orchestrator file**: Retains the public API and core flow logic
2. **Data models module**: Contains dataclasses and type definitions (`*_models.py`)
3. **Helper modules**: Focused functionality grouped by concern
4. **Constants/Config module**: Shared constants and configuration (`*_helpers.py`)

#### Example: Environment Configurator Refactoring
Original: `environment_configurator.py` (48KB)
Refactored into:
- `environment_configurator.py` (18KB) - Main orchestrator with delegation
- `environment_config_models.py` - Data models (EnvironmentConfig, ConfigurationResult)
- `environment_analyzer.py` - Environment analysis and requirement detection
- `environment_installer.py` - Python environment and package installation
- `config_file_generators.py` - Tool configuration file generation (ruff, black, mypy, etc.)
- `project_file_generators.py` - Project file generation (Dockerfile, CI/CD, etc.)
- `environment_config_helpers.py` - Helper functions and constants

#### Example: Environment Reproducer Refactoring
Original: `environment_reproducer.py` (47KB)
Refactored into:
- `environment_reproducer.py` - Main orchestrator
- `environment_snapshot_models.py` - Snapshot data models
- `platform_normalizer.py` - Cross-platform compatibility utilities
- `lock_file_manager.py` - Lock file generation and parsing
- `environment_validator.py` - Environment validation utilities

#### Delegation Pattern Implementation
The main class maintains its public API but delegates to helper modules:
```python
class EnvironmentConfigurator:
    def __init__(self):
        self.env_analyzer = EnvironmentAnalyzer()
        self.env_installer = EnvironmentInstaller()
        # ... other helper instances

    def _detect_tools_from_project(self, project_path: Path, project_info: Dict[str, Any]) -> List[str]:
        """Delegate to environment analyzer."""
        return self.env_analyzer._detect_tools_from_project(project_path, project_info)
```

This pattern ensures:
- Backward compatibility (public API unchanged)
- Modular, testable components
- Clear separation of concerns
- Maintainable file sizes

### Testing Structure
- `/tests/`: pytest tests for individual components
- `/tests/fixtures/`: Fixtures for the tests
- Use pytest with comprehensive fixtures in `./tests/conftest.py`
- Tests for bash scripts are executed with: `./tests/test_dhtl_basic.sh`

### Key Implementation Details
- **UV-First**: Uses UV package manager for fast dependency management
- **Process Guardian**: All Python commands run with memory limits (default 4096MB) and timeout protection with Prefect
- **Cross-Platform**: Works on macOS, Linux, Windows (Git Bash/WSL)
- **Modular Design**: Functionality split into shell modules loaded by orchestrator
- **Environment Isolation**: Manages Python virtual environments automatically with uv

### Development Workflow
1. Commands are invoked via `dhtl` alias (when venv is active) or `./dhtl.sh`
2. The orchestrator loads required modules based on the command
3. Commands execute with resource limits via the process guardian
4. All Python operations ensure proper virtual environment activation

### Dependencies
- Core tools: pytest, mypy, ruff, flake8, black, pre-commit
- Package management: UV (modern Python package manager)
- Version management: bump-my-version, gitpython
- UI/CLI: click, rich
- AI/ML libraries: openai, litellm, google-generativeai (for certain features)

## Technical Implementation Strategy

### 1. Exact Version Tool Installation
```python
# Install with exact version and behavior verification
install_exact_tool_version("black", "23.7.0", mode="venv")
verify_tool_behavior("black", "23.7.0")  # Test formatting behavior
```
**Rationale**: Binary hashes differ across platforms, but same version ensures same behavior.

### 2. Cross-Platform Configuration Generation
```python
# Generate configs that work identically everywhere
config = {
    'pytest': {
        'addopts': '-p no:cacheprovider --import-mode=importlib',
        'cache_dir': '.pytest_cache',  # Local, not system
    }
}
```
**Rationale**: Eliminate platform defaults that cause test differences.

### 3. System Dependency Mapping
```python
PLATFORM_MAPPINGS = {
    'postgresql-client': {
        'ubuntu': 'postgresql-client-15',
        'macos': 'postgresql@15',
        'windows': 'postgresql15'
    }
}
```
**Rationale**: Same functionality, different package names per platform.

### 4. Test Environment Sandboxing
```python
# Complete isolation for deterministic tests
sandbox_env = {
    'PYTHONHASHSEED': '0',
    'TZ': 'UTC',
    'LC_ALL': 'C.UTF-8',
    'TMPDIR': '/tmp/test_sandbox'
}
```
**Rationale**: Eliminates non-deterministic test failures from environment variance.

### 5. Strict Mode Operation
```bash
dhtl regenerate --strict --no-fallbacks
```
**Rationale**: Better to fail explicitly than hide configuration problems.

### 6. Platform Normalization
- **File paths**: Always use forward slashes in configs
- **Line endings**: Force LF via .gitattributes
- **Commands**: Python wrappers instead of shell scripts
- **Output**: Normalize paths, timestamps, and addresses

## Key Technical Decisions

### Version-Based Validation Over Hash Matching
- **Problem**: `black==23.7.0` has different binary hashes on different platforms
- **Solution**: Verify version + behavior, not binary hash
- **Result**: Tools work identically despite binary differences

### Tool Isolation Strategy
- **UV tools**: Process isolation with `--from` flag
- **Venv installation**: Complete isolation from system
- **Wrapper scripts**: Ensure correct version always used

### Platform Abstraction Layer
- **Path handling**: Path objects handle separators automatically
- **System packages**: Mapping layer for package names
- **Binary tools**: Platform-specific downloads with common interface

### Deterministic Test Environments
- **Fixed seeds**: Random, numpy, and hash seeds controlled
- **Time mocking**: Fixed timestamps for reproducibility
- **Network isolation**: No external dependencies during tests
- **Output normalization**: Compare behavior, not platform details

## Development Workflow

### Setup Phase
1. Analyze project structure and dependencies
2. Generate .dhtconfig with minimal non-inferrable info
3. Install exact Python version via UV
4. Create normalized configurations
5. Install system dependencies with platform mapping
6. Setup development tools in isolation
7. Verify environment with checksums

### Regeneration Phase
1. Parse .dhtconfig
2. Install exact Python version
3. Install platform-specific system deps
4. Restore Python packages from lock files
5. Configure tools with normalized settings
6. Validate against expected checksums
7. Report any discrepancies

### Testing Phase
1. Create sandboxed test environment
2. Set deterministic environment variables
3. Mock time and randomness
4. Run tests with normalized output
5. Compare results across platforms

## Python Version Compatibility
DHT is built on Python 3.10 for maximum compatibility but must manage projects using Python 3.11-3.14+. UV handles multiple Python versions well, making this feasible. Key considerations:
- UV manages Python installations independently of DHT's runtime
- `uv python pin` handles project-specific Python versions
- Build tools are isolated in project virtual environments
- DHT acts as an orchestrator, not a runtime dependency
- Fallback to Docker containers for unsupported Python versions

## Enhanced Information Extraction System

### Overview
DHT includes a comprehensive information extraction system that discovers and catalogs all development tools and configurations on a system. The system uses a practical, use-case driven categorization that provides atomic access to every piece of information.

### Key Design Principles

1. **Platform-Aware**: Automatically detects the current platform (macOS, Linux, Windows) and only checks for tools that exist on that platform. No time wasted looking for `apt` on macOS or `brew` on Windows.

2. **Use-Case Driven Categories**: Tools are organized by what developers actually need them for:
   - `version_control` - Source code management (git, hg, svn)
   - `language_runtimes` - What can execute code (python, node, ruby, java)
   - `package_managers` - For installing dependencies (pip, npm, cargo, brew)
   - `build_tools` - For building projects (make, cmake, ninja)
   - `compilers` - For native code (gcc, clang, rustc)
   - `containers_virtualization` - Isolated environments (docker, podman, kubectl)
   - `cloud_tools` - Cloud deployment (aws, gcloud, terraform)
   - `archive_managers` - Compression tools (tar, zip, 7z)
   - `network_tools` - Debugging connectivity (curl, wget, openssl)
   - And more...

3. **Atomic Information Access**: Every piece of data has a clear, predictable path:
   ```yaml
   tools.build_tools.cmake.version              # "3.28.1"
   tools.build_tools.cmake.is_installed         # true
   tools.package_managers.language.python.pip.version  # "23.3.1"
   tools.containers_virtualization.docker.info.StorageDriver  # "overlay2"
   ```

4. **Standardized Fields**: All tools have consistent base fields:
   - `is_installed` - Boolean indicating if tool is available
   - `version` - Extracted version number
   - `install_path` - Where the tool is installed
   - Tool-specific fields based on actual command output

### Information Structure

```yaml
# System Information
system:
  platform: "macos"           # Normalized platform name
  architecture: "arm64"       # CPU architecture
  cpu.physical_cores: 8       # Hardware details
  memory.total_mb: 16384      # Memory information

# Tool Information (examples)
tools:
  version_control:
    git:
      is_installed: true
      version: "2.43.0"
      config_user_name: "John Doe"
      config_user_email: "john@example.com"

  build_tools:
    cmake:
      is_installed: true
      version: "3.28.1"
      system_info_c_compiler: "/usr/bin/clang"
      system_info_cxx_compiler: "/usr/bin/clang++"

  package_managers:
    language:
      python:
        pip:
          is_installed: true
          version: "23.3.1"
          inspect: {...}  # Full pip inspect output
```

### Implementation Architecture

1. **Modular Parsers**: Each file type has a dedicated parser:
   - `PythonParser` - AST-based Python analysis
   - `BashParser` - Tree-sitter based shell script parsing
   - `PyProjectParser` - TOML-based project file parsing
   - Package file parsers for various formats

2. **Prefect Integration**: All parsing operations run through Prefect tasks:
   - Parallel file processing
   - Resource management
   - Error handling and retries
   - Progress tracking

3. **Command Registry**: CLI commands are defined with expected output formats:
   ```python
   "cmake": {
       "commands": {
           "version": "cmake --version",
           "system_info": "cmake --system-information"
       },
       "category": "build_tools",
       "format": "auto"  # Automatic parsing
   }
   ```

4. **Smart Output Parsing**:
   - JSON detection and parsing
   - Version number extraction
   - Key-value pair parsing
   - Path normalization
   - Boolean detection

### Usage in DHT
Once the user execute `dhtl setup` the .venv is created, with the toml file and the directory tree is adjusted to be normalized according to the uv specifications.
At the end of the setup process, a file called `.dhtconfig` is created in the root of the project with the informations needed to regenerate the same configuration anywhere, with just this file and the repo files cloned. The file .dhtconfig must be tracked by git, so it must be added to git and not ignored. Any project with the .dhtconfig file will be able to be regenerated with the command `dhtl regenerate`.
DHT stores only the minimum informations in .dhtconfig file to restore the original repo status with config, tools and env settings.
All the other info are extracted from the codebase and from dot files and diagnostic tools that report system informations and installed tools/runtimes.
The information extraction system powers several DHT features:

1. **Environment Regeneration**: Captures exact tool versions for reproduction
2. **Dependency Detection**: Identifies all project dependencies automatically
3. **Dockerization**: Knows what system packages to install
4. **CI/CD Setup**: Configures appropriate build environments
5. **Project Analysis**: Understands project structure and requirements
6. **Deterministic builds**: Deterministic build and regeneration in any platform thanks to uv project build management, uv workflows and .dhtconfig

### Extending the System

To add new tools or information sources:

1. Add to `cli_commands_registry.py`:
   ```python
   "new_tool": {
       "commands": {
           "version": "new_tool --version",
           "config": "new_tool config list"
       },
       "category": "appropriate_category"
   }
   ```

2. The system automatically:
   - Checks installation status
   - Runs all defined commands
   - Parses output intelligently
   - Places data in the correct category
   - Makes it atomically accessible

### Benefits

1. **Fast Lookups**: Direct path to any information
2. **Cross-Platform**: Works identically on all platforms
3. **Extensible**: Easy to add new tools
4. **Comprehensive**: Captures both tools and their configurations
5. **Machine-Readable**: Clean YAML/JSON output for automation
