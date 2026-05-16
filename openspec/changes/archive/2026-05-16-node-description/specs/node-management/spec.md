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

#### Scenario: Create note with description
- **WHEN** user runs `prism new note "Beach" --desc "Photos from our vacation to the beach"`
- **THEN** the system SHALL create `description.md` in the node directory containing the description text
- **THEN** the system SHALL store `desc_sha256`, `desc_mtime`, and `desc_size` in `metadata.toml`

### Requirement: Edit node

The system SHALL allow editing node metadata fields, note body content, and description.

#### Scenario: Set description on node without one
- **WHEN** user runs `prism edit <uuid> --desc "New description text"`
- **THEN** the system SHALL create `description.md` with the given text
- **THEN** the system SHALL add `desc_sha256`, `desc_mtime`, `desc_size` to `metadata.toml`
- **THEN** the system SHALL set `sync_dirty = true`
- **THEN** the system SHALL update `updated_at`

#### Scenario: Update description on node with one
- **WHEN** user runs `prism edit <uuid> --desc "Updated description"`
- **THEN** the system SHALL overwrite `description.md` with the new text
- **THEN** the system SHALL update `desc_sha256`, `desc_mtime`, `desc_size` in `metadata.toml`
- **THEN** the system SHALL set `sync_dirty = true`

#### Scenario: Clear description
- **WHEN** user runs `prism edit <uuid> --desc ""`
- **THEN** the system SHALL delete `description.md`
- **THEN** the system SHALL remove `desc_sha256`, `desc_mtime`, `desc_size` from `metadata.toml`
- **THEN** the system SHALL set `sync_dirty = true`

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

### Requirement: Delete node

The system SHALL delete a node and its associated files.

#### Scenario: Delete blob node
- **WHEN** user runs `prism rm <uuid>` with confirmation `--yes`
- **THEN** the system SHALL remove the entire `.storage/<uuid-partitioned>/` directory (including `description.md` if present)
- **THEN** the system SHALL remove the entry from `.metadata/index.txt`
- **THEN** the system SHALL rebuild the index

#### Scenario: Delete with pending links
- **WHEN** user runs `prism rm <uuid>` and other nodes link to this node
- **THEN** the system SHALL warn: "X nodes link to this node. Links will become unresolved."
- **THEN** after confirmation, the system SHALL delete the node

### Requirement: Show node

The system SHALL display a node's metadata and content in a readable format.

#### Scenario: Show note with paths
- **WHEN** user runs `prism show <note-uuid>` and the node has associated paths
- **THEN** the system SHALL display the resolved path strings (e.g., `/photos/2026/02/vacations`) in a "Paths" section

#### Scenario: Show node with description
- **WHEN** user runs `prism show <uuid> --desc`
- **THEN** the system SHALL display the description text in a "Description" section

#### Scenario: Show node without description using --desc flag
- **WHEN** user runs `prism show <uuid> --desc` and the node has no description
- **THEN** the system SHALL display "(no description)" or equivalent

## ADDED Requirements

### Requirement: List nodes with descriptions

The system SHALL support displaying descriptions in node listings.

#### Scenario: List with description column
- **WHEN** user runs `prism list --desc`
- **THEN** the system SHALL include a "Description" column showing the first line or truncated text of each node's description
- **THEN** nodes without descriptions SHALL display an empty cell or "-"

#### Scenario: List --desc with JSON format
- **WHEN** user runs `prism list --desc --format json`
- **THEN** the JSON output SHALL include a `description` field containing the full description text (or null if absent)

### Requirement: Verify description integrity

The system SHALL verify the integrity of description files using SHA-256.

#### Scenario: Verify node with description
- **WHEN** user runs `prism verify <uuid>` and the node has a description
- **THEN** the system SHALL recompute the SHA-256 hash of `description.md`
- **THEN** the system SHALL compare with the stored `desc_sha256`
- **THEN** if they match, the system SHALL output "Description: OK"
- **THEN** if they differ, the system SHALL output "Description: CORRUPTED"

#### Scenario: Verify node without description
- **WHEN** user runs `prism verify <uuid>` and the node has no description
- **THEN** the system SHALL skip description verification (no error)
