## MODIFIED Requirements

### Requirement: Per-node mtime tracking

Each node's metadata.toml SHALL store the mtime of its associated blob file and description file for change detection.

#### Scenario: Store mtime on import
- **WHEN** a blob is imported or a note is created
- **THEN** metadata.toml SHALL store `blob_mtime` (filesystem mtime of `data.*`) and `blob_size` (file size in bytes)

#### Scenario: Store description mtime
- **WHEN** a node is created with `--desc` or an existing node receives a description via `prism edit --desc`
- **THEN** metadata.toml SHALL store `desc_mtime`, `desc_size`, and `desc_sha256` for `description.md`

#### Scenario: Clear description tracking fields
- **WHEN** a description is removed (`prism edit <uuid> --desc ""`)
- **THEN** `desc_mtime`, `desc_size`, and `desc_sha256` SHALL be removed from metadata.toml

#### Scenario: Update mtime on edit
- **WHEN** user edits a note via `prism edit`
- **THEN** after the editor exits, the system SHALL stat the `data.md` file
- **THEN** if `blob_mtime` differs from stored value, the system SHALL treat it as changed

### Requirement: Status command

The system SHALL report the state of the vault: changed nodes, new files, orphaned nodes.

#### Scenario: Show changed nodes
- **WHEN** user runs `prism status`
- **THEN** the system SHALL walk `.storage/`, stat each node directory, compare blob mtime with stored value
- **THEN** nodes with mismatched blob mtime SHALL be listed under "Changed nodes"

#### Scenario: Detect description changes
- **WHEN** user runs `prism status` and a node's `description.md` mtime differs from stored `desc_mtime`
- **THEN** the node SHALL be listed under "Changed nodes" with a note indicating the description changed

#### Scenario: Detect new description.md outside Prism
- **WHEN** a user manually creates `description.md` in a node directory
- **THEN** `prism status` SHALL detect the new file via mtime mismatch (no stored `desc_mtime`)
- **THEN** the node SHALL be listed under "Changed nodes"

#### Scenario: Detect new files outside vault
- **WHEN** a file is added to the vault directory outside of Prism (e.g., `cp file.pdf vault/`)
- **THEN** `prism status` SHALL detect files not tracked in `.metadata/index.txt`
- **THEN** the system SHALL prompt: "New file detected: vault/file.pdf. Index it? [y/N/skip all]"

#### Scenario: Detect orphaned nodes
- **WHEN** a node's `.storage/<uuid>/` directory is deleted behind Prism's back
- **THEN** `prism status` SHALL detect the missing directory from the index
- **THEN** the system SHALL list them under "Missing nodes (index references deleted storage)"

### Requirement: Re-extract links on change

When a note's body or description changes, the system SHALL re-extract `[[uuid]]` links from the changed content.

#### Scenario: Re-extract on status
- **WHEN** user runs `prism status` and a changed note is detected (body or description change)
- **THEN** the system SHALL offer: "Re-extract links from changed note <uuid>? [y/N]"
- **THEN** on confirmation, re-extract `[[uuid]]` patterns from both body and description, and update metadata.toml links array

#### Scenario: Auto-re-extract on edit
- **WHEN** user runs `prism edit` and saves body changes
- **THEN** the system SHALL automatically re-extract links without prompting

#### Scenario: Re-extract links on description edit
- **WHEN** user runs `prism edit <uuid> --desc "See [[abc-123]] for details"` without editing the body
- **THEN** the system SHALL update the description tracking fields
- **THEN** the system SHALL set `sync_dirty = true`
- **THEN** the system SHALL extract `[[uuid]]` links from the new description text
