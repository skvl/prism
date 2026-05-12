## ADDED Requirements

### Requirement: Path-based filtering

The system SHALL support filtering nodes by path association.

#### Scenario: Filter by exact path
- **WHEN** user runs `prism query "path:/photos/2026/02/vacations"`
- **THEN** the system SHALL return nodes whose `paths` array contains the leaf segment UUID of the given path
- **THEN** the system SHALL return an exact match only (no subtree expansion)

#### Scenario: Path with tag AND filter
- **WHEN** user runs `prism query "path:/photos AND tag:vacation"`
- **THEN** the system SHALL return nodes that are associated with `/photos` AND tagged "vacation"

#### Scenario: Path with tag OR filter
- **WHEN** user runs `prism query "path:/photos OR path:/projects"`
- **THEN** the system SHALL return nodes associated with either path

#### Scenario: Path with tag NOT filter
- **WHEN** user runs `prism query "path:/photos AND NOT tag:archive"`
- **THEN** the system SHALL return nodes associated with `/photos` but not tagged "archive"

#### Scenario: Non-existent path in query
- **WHEN** user runs `prism query "path:/nonexistent"`
- **THEN** the system SHALL return no results

#### Scenario: Invalid path syntax in query
- **WHEN** user runs `prism query "path:invalid"`
- **THEN** the system SHALL return a warning: "Paths must start with /"
- **THEN** the system SHALL treat it as a text search for "path:invalid"
