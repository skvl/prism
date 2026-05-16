## ADDED Requirements

### Requirement: Description integrity verification

The system SHALL verify the integrity of description files using SHA-256, following the same pattern as blob verification.

#### Scenario: Verify description on verify
- **WHEN** user runs `prism verify <uuid>` and the node has a description
- **THEN** the system SHALL recompute the SHA-256 hash of `description.md`
- **THEN** the system SHALL compare with the stored `desc_sha256`
- **THEN** the system SHALL output the result (description status alongside blob status)

#### Scenario: Verify node without description
- **WHEN** user runs `prism verify <uuid>` and the node has no description
- **THEN** the system SHALL skip description verification (no error, no output for description)
