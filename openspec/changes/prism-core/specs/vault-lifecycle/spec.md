## ADDED Requirements

### Requirement: Initialize vault

The system SHALL create a new vault at a given directory path with the required internal structure.

#### Scenario: Initialize empty directory
- **WHEN** user runs `prism init /path/to/vault` on an empty directory
- **THEN** the system creates `.storage/`, `.metadata/`, `.metadata/types/`, `.metadata/index.txt`, and `.metadata/vault.yaml`
- **THEN** the vault.yaml file SHALL contain a generated UUIDv7 vault identifier, creation timestamp, and schema version

#### Scenario: Initialize non-empty directory
- **WHEN** user runs `prism init /path/to/vault` on a non-empty directory
- **THEN** the system SHALL warn that existing files are not managed and ask for confirmation
- **THEN** on confirmation, the system creates the `.storage/` and `.metadata/` structure alongside existing files
- **THEN** the system SHALL NOT move or modify existing files

#### Scenario: Initialize already initialized vault
- **WHEN** user runs `prism init` on a directory that already has `.metadata/vault.yaml`
- **THEN** the system SHALL display an error: "Vault already exists at this location"
- **THEN** the system SHALL exit with non-zero status

### Requirement: Open and validate vault

The system SHALL open a vault by reading its `.metadata/vault.yaml` and verifying the internal structure.

#### Scenario: Open valid vault
- **WHEN** user runs any command in a valid vault directory
- **THEN** the system SHALL read `.metadata/vault.yaml` and confirm the vault is intact
- **THEN** commands SHALL operate within the vault context

#### Scenario: Open invalid or missing vault
- **WHEN** user runs a command outside a vault or in a corrupted vault
- **THEN** the system SHALL display: "No vault found. Run `prism init` to create one."
- **THEN** the system SHALL exit with non-zero status

### Requirement: Multiple vault registration

The system SHALL allow registering multiple vaults for unified operations.

#### Scenario: Register additional vault
- **WHEN** user runs `prism vault add /path/to/other-vault`
- **THEN** the system SHALL add the vault path and UUID to a vault registry file at `~/.config/prism/vaults.yaml`
- **THEN** queries and graph operations SHALL work across all registered vaults

#### Scenario: List registered vaults
- **WHEN** user runs `prism vault list`
- **THEN** the system SHALL display all registered vaults with their UUIDs, paths, and node counts
