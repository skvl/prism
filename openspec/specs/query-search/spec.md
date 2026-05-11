## ADDED Requirements

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

The system SHALL support basic text search over note bodies.

#### Scenario: Search note body
- **WHEN** user runs `prism query "budget report"`
- **THEN** the system SHALL search for "budget" and "report" in note body text (grep-based)

#### Scenario: Search with tag and text
- **WHEN** user runs `prism query "meeting AND tag:q2"`
- **THEN** the system SHALL return nodes tagged "q2" whose bodies mention "meeting"

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
