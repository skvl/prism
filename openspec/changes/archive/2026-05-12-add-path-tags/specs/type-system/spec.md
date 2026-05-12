## ADDED Requirements

### Requirement: Path type schema

The system SHALL ship with a built-in `path` type schema defined in `.metadata/types/`.

#### Scenario: Path type definition
- **WHEN** the vault is initialized
- **THEN** `.metadata/types/path.toml` SHALL exist with fields: `name` (string, required)
- **THEN** the path type SHALL have `body_model: null` indicating no companion file
- **THEN** the path type SHALL NOT be creatable via `prism new path` (path nodes are managed by `prism path` subcommands)
