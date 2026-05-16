## Why

The project has linting, type-checking, testing, security scanning, and dependency auditing tools configured, but nothing enforces running them before commits. Commits can land with lint errors, broken tests, type errors, security holes, or vulnerable dependencies until CI catches them — wasting time and eroding codebase quality.

## What Changes

- Add `.pre-commit-config.yaml` at the project root with `local` hooks
- Configure hooks for both `prism-core` and `prism-cli`: ruff check (lint + fix), ruff format, pytest, pyright, bandit, pip-audit
- Add `[tool.ruff.format]` section to both `pyproject.toml` files with `quote-style = "double"`
- Each hook runs per-project using explicit `--config` flags for independent tool configuration
- Hook ordering: lint → format → tests → type check → security → audit

## Capabilities

### New Capabilities
- `pre-commit-integration`: Pre-commit hook configuration that runs ruff (lint+format), pytest, pyright, bandit, and pip-audit before every commit. All hooks run as `repo: local` using system-installed tools with per-project configuration.

### Modified Capabilities
- (none — no existing spec-level behavior changes; linting, testing, type-checking, security-scanning, and dependency-auditing requirements remain unchanged)

## Impact

- **New file**: `.pre-commit-config.yaml` at repo root
- **prism-core/pyproject.toml**: Add `[tool.ruff.format]` with `quote-style = "double"`
- **prism-cli/pyproject.toml**: Add `[tool.ruff.format]` with `quote-style = "double"`
- **package.json / pip**: No new dependencies — all tools are already declared in dev dependencies
