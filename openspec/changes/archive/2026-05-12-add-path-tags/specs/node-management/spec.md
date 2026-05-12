## MODIFIED Requirements

### Requirement: Create typed node

The system SHALL create a new node of a specified type with given fields.

#### Scenario: Create note node with path
- **WHEN** user runs `prism new note "Beach" --add-path /photos/2026/02/vacations`
- **THEN** the system SHALL create the node with the leaf segment UUID in its `paths` field

#### Scenario: Create note without path
- **WHEN** user runs `prism new note "Meeting Notes"`
- **THEN** the system SHALL create the node with an empty `paths` field
- **THEN** the `paths` field SHALL NOT appear in metadata.toml if empty

### Requirement: Edit node

The system SHALL allow editing node metadata fields and note body content.

#### Scenario: Add path to existing node
- **WHEN** user runs `prism edit <uuid> --add-path /photos/2026/02/vacations`
- **THEN** the system SHALL resolve the path to its leaf segment UUID
- **THEN** the system SHALL append the UUID to the node's `paths` field (if not already present)

#### Scenario: Remove path from existing node
- **WHEN** user runs `prism edit <uuid> --remove-path /photos/2026/02/vacations`
- **THEN** the system SHALL resolve the path to its leaf segment UUID
- **THEN** the system SHALL remove the UUID from the node's `paths` field

#### Scenario: Add non-existent path to node
- **WHEN** user runs `prism edit <uuid> --add-path /nonexistent/path`
- **THEN** the system SHALL display an error: "Path does not exist"
- **THEN** the system SHALL exit with non-zero status

### Requirement: Show node

The system SHALL display a node's metadata and content in a readable format.

#### Scenario: Show note with paths
- **WHEN** user runs `prism show <note-uuid>` and the node has associated paths
- **THEN** the system SHALL display the resolved path strings (e.g., `/photos/2026/02/vacations`) in a "Paths" section
