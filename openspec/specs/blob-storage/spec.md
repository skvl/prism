## ADDED Requirements

### Requirement: Import file as blob

The system SHALL import a file into the vault's blob store, copying it into a UUID-partitioned path.

#### Scenario: Import file with automatic type detection
- **WHEN** user runs `prism add ~/Documents/report.pdf`
- **THEN** the system SHALL generate a new UUID
- **THEN** the system SHALL copy the file to `.storage/<uuid-partitioned>/data.pdf`
- **THEN** the system SHALL create `.storage/<uuid-partitioned>/metadata.toml` with type `file`, original filename, mtime, size, and SHA-256 hash
- **THEN** the system SHALL output the node UUID

#### Scenario: Import file with explicit type
- **WHEN** user runs `prism add ~/Documents/notes.md --type note`
- **THEN** the system SHALL import as a note node with the file content as the body
- **THEN** the system SHALL scan the body for existing `[[uuid]]` links and populate the links array

#### Scenario: Import duplicate file (same content)
- **WHEN** user imports a file whose SHA-256 hash matches an existing blob
- **THEN** the system SHALL warn: "File already exists as node <uuid>"
- **THEN** the system SHALL ask whether to create a second reference or skip

### Requirement: Path structure

The system SHALL store blobs in a UUID-partitioned directory tree to prevent directory bloat.

#### Scenario: UUID partitioning
- **WHEN** a node is created with UUID `a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d`
- **THEN** the blob SHALL be stored at `.storage/a1b2/c3d4/e5f6/a7b8c9d0e1f2/data.EXT`
- **THEN** the UUID dashes SHALL be removed, and the partitioned path SHALL use the first 4 hex chars per directory level, with the remainder as the final directory name

#### Scenario: Original extension preserved
- **WHEN** importing `photo.jpg`
- **THEN** the blob file SHALL be named `data.jpg`
- **THEN** the original extension SHALL be stored in metadata.toml as `blob_extension = "jpg"`

### Requirement: SHA-256 content hashing

The system SHALL compute and store SHA-256 hashes for all imported blobs.

#### Scenario: Hash on import
- **WHEN** a blob is imported
- **THEN** the system SHALL compute its SHA-256 hash
- **THEN** the hash SHALL be stored in metadata.toml as `blob_sha256`

#### Scenario: Verify integrity
- **WHEN** user runs `prism verify <uuid>`
- **THEN** the system SHALL recompute the SHA-256 hash of `data.*`
- **THEN** the system SHALL compare with the stored `blob_sha256`
- **THEN** the system SHALL output "OK" or "CORRUPTED" accordingly
