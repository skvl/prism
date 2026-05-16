## MODIFIED Requirements

### Requirement: Full-text search

The system SHALL support basic text search over note bodies and node descriptions.

#### Scenario: Search note body
- **WHEN** user runs `prism query "budget report"`
- **THEN** the system SHALL search for "budget" and "report" in note body text (grep-based)

#### Scenario: Search description text
- **WHEN** user runs `prism query "vacation"`
- **THEN** the system SHALL search for "vacation" in both `data.md` and `description.md` files

#### Scenario: Search with tag and text
- **WHEN** user runs `prism query "meeting AND tag:q2"`
- **THEN** the system SHALL return nodes tagged "q2" whose bodies or descriptions mention "meeting"

#### Scenario: Description-only match
- **WHEN** user runs `prism query "project roadmap"` and a node has "project roadmap" in its description but not its body
- **THEN** the system SHALL include that node in the results

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
