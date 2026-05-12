## ADDED Requirements

### Requirement: Tab completion for paths

The system SHALL provide per-segment tab completion for path-like tags in the REPL.

#### Scenario: Complete path segment at root level
- **WHEN** user types `path:/pho` and presses Tab
- **THEN** the system SHALL complete to `path:/photos` if `/photos` exists
- **THEN** the system SHALL show matching completions if multiple exist (e.g., `/photos` and `/phone`)

#### Scenario: Complete nested path segment
- **WHEN** user types `path:/photos/202` and presses Tab
- **THEN** the system SHALL complete the segment after the last `/` using children of the parent path node

#### Scenario: Complete after `--add-path` flag
- **WHEN** user types `prism new note "Title" --add-path /pho` and presses Tab
- **THEN** the system SHALL complete the path using the same per-segment logic

#### Scenario: No match on path prefix
- **WHEN** user types `path:/zzz` and presses Tab
- **THEN** the system SHALL NOT provide completions
