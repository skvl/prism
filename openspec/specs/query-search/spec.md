## Purpose

The query-search capability provides a powerful query language with tag, type, and path filters combined via AND/OR/NOT boolean operators, plus full-text search across node metadata and note bodies.
## Requirements
### Requirement: Tag-based filtering

The system SHALL support filtering nodes by tags with boolean operators.

#### Scenario: Filter by single tag
- **WHEN** user runs `prism query "tag:work"`
- **THEN** the system SHALL return all nodes whose `tags` array contains "work"

#### Scenario: AND filter
- **WHEN** user runs `prism query "tag:work AND tag:important"`
- **THEN** the system SHALL return nodes that have BOTH "work" AND "important" tags

#### Scenario: OR filter
- **WHEN** user runs `prism query "tag:work OR tag:personal"`
- **THEN** the system SHALL return nodes that have EITHER "work" OR "personal"

#### Scenario: NOT filter
- **WHEN** user runs `prism query "tag:work AND NOT tag:archive"`
- **THEN** the system SHALL return nodes tagged "work" but NOT "archive"

### Requirement: Type-based filtering

The system SHALL support filtering by node type.

#### Scenario: Filter by type
- **WHEN** user runs `prism query "type:contact"`
- **THEN** the system SHALL return all contact nodes

#### Scenario: Combined type and tag
- **WHEN** user runs `prism query "type:note AND tag:meeting"`
- **THEN** the system SHALL return notes tagged "meeting"

### Requirement: Full-text search

The system SHALL support basic text search over note bodies and node descriptions.

#### Scenario: Search note body
- **WHEN** user runs `prism query "budget report"`
- **THEN** the system SHALL search for "budget" and "report" in note body text (grep-based)

#### Scenario: Search description text
- **WHEN** user runs `prism query "vacation"`
- **THEN** the system SHALL search for "vacation" in both `data.md` and `description.md` files

#### Scenario: Description-only match
- **WHEN** user runs `prism query "project roadmap"` and a node has "project roadmap" in its description but not its body
- **THEN** the system SHALL include that node in the results

#### Scenario: Search with tag and text
- **WHEN** user runs `prism query "meeting AND tag:q2"`
- **THEN** the system SHALL return nodes tagged "q2" whose bodies or descriptions mention "meeting"

### Requirement: Output formatting

Results SHALL be displayed in a consistent format.

#### Scenario: Default table output
- **WHEN** any query returns results
- **THEN** the system SHALL display a table with columns: UUID (short), type, title, tags, updated_at

#### Scenario: JSON output
- **WHEN** user runs `prism query "tag:work" --format json`
- **THEN** the system SHALL output a JSON array of matching nodes with all metadata

#### Scenario: No results
- **WHEN** a query matches no nodes
- **THEN** the system SHALL output "No results found" with exit code 0

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

