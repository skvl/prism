## ADDED Requirements

### Requirement: REPL new command supports --desc

The REPL `new` command SHALL accept the `--desc` flag for setting a description during node creation.

#### Scenario: Create node with description in REPL
- **WHEN** user types `new note "Title" --desc "A brief description"` at the REPL prompt
- **THEN** the system SHALL create the node with the given description
- **THEN** the system SHALL create `description.md` and set tracking fields in metadata

#### Scenario: Create node without description in REPL
- **WHEN** user types `new note "Title"` at the REPL prompt (no `--desc`)
- **THEN** the system SHALL create the node without a description (no `description.md`)

### Requirement: REPL edit command supports --desc

The REPL `edit` command SHALL accept the `--desc` flag for setting, updating, or clearing a node's description.

#### Scenario: Set description in REPL
- **WHEN** user types `edit <uuid> --desc "New description"` at the REPL prompt
- **THEN** the system SHALL set the node's description

#### Scenario: Update description in REPL
- **WHEN** user types `edit _ --desc "Updated text"` at the REPL prompt
- **THEN** the system SHALL update the description of the last-created/modified node

#### Scenario: Clear description in REPL
- **WHEN** user types `edit <uuid> --desc ""` at the REPL prompt
- **THEN** the system SHALL delete `description.md` and clear tracking fields

### Requirement: REPL show command supports --desc

The REPL `show` command SHALL accept the `--desc` flag for displaying a node's description.

#### Scenario: Show node with description
- **WHEN** user types `show <uuid> --desc` at the REPL prompt
- **THEN** the system SHALL display the node's description text in a "Description" section

#### Scenario: Show node without description using --desc
- **WHEN** user types `show _ --desc` at the REPL prompt and the node has no description
- **THEN** the system SHALL display "(no description)" or equivalent
