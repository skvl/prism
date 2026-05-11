## ADDED Requirements

### Requirement: Create typed node

The system SHALL create a new node of a specified type with given fields.

#### Scenario: Create note node
- **WHEN** user runs `prism new note "Meeting Notes"`
- **THEN** the system SHALL create `.storage/<uuid-partitioned>/metadata.yaml` with type `note`, title "Meeting Notes", and current timestamp
- **THEN** the system SHALL create `.storage/<uuid-partitioned>/data.md` with the title as an H1 header and empty body
- **THEN** the system SHALL output the new node's UUID

#### Scenario: Create contact node
- **WHEN** user runs `prism new contact --name "Alice" --email alice@example.com`
- **THEN** the system SHALL create `.storage/<uuid-partitioned>/metadata.yaml` with type `contact`, name "Alice", email "alice@example.com"
- **THEN** the system SHALL NOT create any `data.*` file
- **THEN** the system SHALL output the new node's UUID

#### Scenario: Create bookmark node
- **WHEN** user runs `prism new bookmark "https://example.com" --title "Example"`
- **THEN** the system SHALL create `.storage/<uuid-partitioned>/metadata.yaml` with type `bookmark`, url "https://example.com", title "Example"
- **THEN** the system SHALL NOT create any `data.*` file

#### Scenario: Create node with missing required field
- **WHEN** user runs `prism new contact` without `--name`
- **THEN** the system SHALL display an error listing the required fields for type `contact`
- **THEN** the system SHALL exit with non-zero status

### Requirement: Edit node

The system SHALL allow editing node metadata fields and note body content.

#### Scenario: Edit note body
- **WHEN** user runs `prism edit <note-uuid>`
- **THEN** the system SHALL open `.storage/<uuid-partitioned>/data.md` in `$EDITOR`
- **THEN** after editor exits, the system SHALL detect changes via mtime comparison
- **THEN** the system SHALL re-extract `[[uuid]]` links from the body and update metadata.yaml links array
- **THEN** the system SHALL update `updated_at` and `blob_sha256` in metadata.yaml

#### Scenario: Edit structured field via dialog
- **WHEN** user runs `prism edit <contact-uuid>`
- **THEN** the system SHALL display an interactive dialog showing each field with current value
- **THEN** the system SHALL prompt "Enter new <field_name> or press ENTER to keep [current_value]"
- **THEN** the system SHALL update metadata.yaml with changed fields

#### Scenario: Cancel edit (no changes)
- **WHEN** user runs `prism edit <note-uuid>` and closes the editor without changes
- **THEN** the system SHALL detect that mtime has not changed
- **THEN** the system SHALL NOT update metadata.yaml
- **THEN** the system SHALL output "No changes detected"

### Requirement: Delete node

The system SHALL delete a node and its associated files.

#### Scenario: Delete blob node
- **WHEN** user runs `prism rm <uuid>` with confirmation `--yes`
- **THEN** the system SHALL remove the entire `.storage/<uuid-partitioned>/` directory
- **THEN** the system SHALL remove the entry from `.metadata/index.txt`
- **THEN** the system SHALL rebuild the index

#### Scenario: Delete with pending links
- **WHEN** user runs `prism rm <uuid>` and other nodes link to this node
- **THEN** the system SHALL warn: "X nodes link to this node. Links will become unresolved."
- **THEN** after confirmation, the system SHALL delete the node

### Requirement: Show node

The system SHALL display a node's metadata and content in a readable format.

#### Scenario: Show note node
- **WHEN** user runs `prism show <note-uuid>`
- **THEN** the system SHALL display: UUID, type, title, tags, links (with cached titles), created/updated timestamps, and first 20 lines of body

#### Scenario: Show contact node
- **WHEN** user runs `prism show <contact-uuid>`
- **THEN** the system SHALL display all contact fields (name, email, phone, etc.) in a formatted table
