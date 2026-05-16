## ADDED Requirements

### Requirement: Pre-commit hooks enforce code quality before every commit

The system SHALL provide a `.pre-commit-config.yaml` at the repository root that runs linting, formatting, tests, type checking, security scanning, and dependency auditing before every commit using `repo: local` hooks.

#### Scenario: Hooks run in correct order
- **WHEN** `git commit` is triggered
- **THEN** hooks SHALL execute in this order: ruff lint (check --fix), ruff format, pytest, pyright, bandit, pip-audit

#### Scenario: Ruff lint fixes imports and catches errors
- **WHEN** a Python file with lint errors or unsorted imports is staged
- **THEN** ruff SHALL run `check --fix` and fail if unfixable errors remain

#### Scenario: Ruff format enforces style
- **WHEN** a Python file with formatting issues is staged
- **THEN** ruff SHALL format the file and fail if formatting changes were needed

#### Scenario: Pytest runs all tests before commit
- **WHEN** `git commit` is triggered
- **THEN** pytest SHALL run `prism-core/tests/` and `prism-cli/tests/` and fail if any test fails

#### Scenario: Pyright type-checks both packages
- **WHEN** `git commit` is triggered
- **THEN** pyright SHALL run with `--project prism-core/pyproject.toml` and `--project prism-cli/pyproject.toml` and fail if type errors are detected

#### Scenario: Bandit scans for security issues
- **WHEN** `git commit` is triggered
- **THEN** bandit SHALL scan staged files for security vulnerabilities and fail if high-severity issues are found

#### Scenario: Pip-audit checks for vulnerable dependencies
- **WHEN** `git commit` is triggered
- **THEN** pip-audit SHALL scan installed dependencies for known vulnerabilities and fail if any are found

### Requirement: Per-project configuration with explicit config paths

Each hook SHALL target a specific project in the monorepo using the `files:` pattern and explicit `--config` flags.

#### Scenario: Ruff uses per-project config
- **WHEN** ruff processes a file under `prism-core/`
- **THEN** it SHALL use `--config prism-core/pyproject.toml`
- **WHEN** ruff processes a file under `prism-cli/`
- **THEN** it SHALL use `--config prism-cli/pyproject.toml`

#### Scenario: Pyright uses per-project config
- **WHEN** pyright type-checks prism-core
- **THEN** it SHALL use `--project prism-core/pyproject.toml`
- **WHEN** pyright type-checks prism-cli
- **THEN** it SHALL use `--project prism-cli/pyproject.toml`

#### Scenario: Bandit uses per-project config
- **WHEN** bandit scans prism-core files
- **THEN** it SHALL use `-c prism-core/pyproject.toml`
- **WHEN** bandit scans prism-cli files
- **THEN** it SHALL use `-c prism-cli/pyproject.toml`

### Requirement: Ruff format configured for double quotes

The ruff formatter SHALL use double quotes to match the existing codebase style.

#### Scenario: Ruff format uses double quotes
- **WHEN** `[tool.ruff.format]` has `quote-style = "double"` in a project's `pyproject.toml`
- **THEN** ruff format SHALL rewrite single-quoted strings to double-quoted strings

### Requirement: Full-project hooks run on unchanged directories

Hooks that need to see the full project state SHALL run even when no files in their directory are staged.

#### Scenario: Pyright runs on every commit
- **WHEN** no prism-core files are staged but `git commit` is triggered
- **THEN** the pyright (prism-core) hook SHALL still run

#### Scenario: Pytest runs on every commit
- **WHEN** no prism-cli files are staged but `git commit` is triggered
- **THEN** the pytest (prism-cli) hook SHALL still run

#### Scenario: Pip-audit runs on every commit
- **WHEN** no files are staged but `git commit` is triggered
- **THEN** the pip-audit hook SHALL still run
