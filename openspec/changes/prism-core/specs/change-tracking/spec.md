## ADDED Requirements

### Requirement: Per-node mtime tracking

Each node's metadata.toml SHALL store the mtime of its associated blob file for change detection.

#### Scenario: Store mtime on import
- **WHEN** a blob is imported or a note is created
- **THEN** metadata.toml SHALL store `blob_mtime` (filesystem mtime of `data.*`) and `blob_size` (file size in bytes)

#### Scenario: Update mtime on edit
- **WHEN** user edits a note via `prism edit`
- **THEN** after the editor exits, the system SHALL stat the `data.md` file
- **THEN** if `blob_mtime` differs from stored value, the system SHALL treat it as changed

### Requirement: Status command

The system SHALL report the state of the vault: changed nodes, new files, orphaned nodes.

#### Scenario: Show changed nodes
- **WHEN** user runs `prism status`
- **THEN** the system SHALL walk `.storage/`, stat each node directory, compare blob mtime with stored value
- **THEN** nodes with mismatched mtime SHALL be listed under "Changed nodes"

#### Scenario: Detect new files outside vault
- **WHEN** a file is added to the vault directory outside of Prism (e.g., `cp file.pdf vault/`)
- **THEN** `prism status` SHALL detect files not tracked in `.metadata/index.txt`
- **THEN** the system SHALL prompt: "New file detected: vault/file.pdf. Index it? [y/N/skip all]"

#### Scenario: Detect orphaned nodes
- **WHEN** a node's `.storage/<uuid>/` directory is deleted behind Prism's back
- **THEN** `prism status` SHALL detect the missing directory from the index
- **THEN** the system SHALL list them under "Missing nodes (index references deleted storage)"

### Requirement: Re-extract links on change

When a note's body changes, the system SHALL re-extract `[[uuid]]` links.

#### Scenario: Re-extract on status
- **WHEN** user runs `prism status` and a changed note is detected
- **THEN** the system SHALL offer: "Re-extract links from changed note <uuid>? [y/N]"
- **THEN** on confirmation, re-extract `[[uuid]]` patterns and update metadata.toml links array

#### Scenario: Auto-re-extract on edit
- **WHEN** user runs `prism edit` and saves changes
- **THEN** the system SHALL automatically re-extract links without prompting

### Requirement: Dirty flag for sync

The system SHALL maintain a dirty flag mechanism for future sync integration.

#### Scenario: Flag node as dirty
- **WHEN** a node's blob or metadata changes
- **THEN** the system SHALL set `sync_dirty = true` in metadata.toml
- **THEN** the system SHALL update `updated_at` to current timestamp
- **THEN** these two fields serve as the cursor for the future sync daemon
