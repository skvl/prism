## ADDED Requirements

### Requirement: Static type checking with pyright

The system SHALL run `pyright` on all Python source files in both packages with proper import resolution configured.

#### Scenario: Pyright configured with extraPaths for editable installs
- **WHEN** `pyright prism-core/prism/ prism-cli/prism_cli/` is run
- **THEN** it SHALL resolve imports from both `prism-core` and `prism-cli` packages

#### Scenario: Pyright catches type errors in source code
- **WHEN** there are type annotation violations
- **THEN** pyright SHALL report them as errors

### Requirement: Pyright configuration

The project SHALL include `[tool.pyright]` or `pyrightconfig.json` to configure import resolution for the monorepo structure.

#### Scenario: Configuration references editable installs
- **WHEN** pyright is invoked
- **THEN** it SHALL use `extraPaths` to find the editable-installed packages
