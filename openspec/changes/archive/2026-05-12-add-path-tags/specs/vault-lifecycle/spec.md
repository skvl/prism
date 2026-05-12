## ADDED Requirements

### Requirement: Root path node on vault init

The system SHALL create a root path node when initializing a new vault.

#### Scenario: Root node created on init
- **WHEN** user runs `prism init /path/to/vault`
- **THEN** the system SHALL create `.storage/<root-uuid>/metadata.toml` with `type = "path"` and `fields.name = "/"` and no parent link
- **THEN** the system SHALL store the root path node UUID in `.metadata/vault.toml` as `path_root_uuid`
