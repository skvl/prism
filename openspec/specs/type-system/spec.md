## ADDED Requirements

### Requirement: Built-in type schemas

The system SHALL ship with four built-in type schemas defined in `.metadata/types/`.

#### Scenario: Note type schema
- **WHEN** the vault is initialized
- **THEN** `.metadata/types/note.toml` SHALL exist with fields: `title` (string, optional), `tags` (list of string, optional)
- **THEN** the note type SHALL have `body_model: file(markdown)` indicating the body lives in `data.md`

#### Scenario: Contact type schema
- **WHEN** the vault is initialized
- **THEN** `.metadata/types/contact.toml` SHALL exist with fields: `name` (string, required), `email` (string, optional), `phone` (string, optional), `org` (string, optional)
- **THEN** the contact type SHALL have `body_model: null` indicating no companion file

#### Scenario: Bookmark type schema
- **WHEN** the vault is initialized
- **THEN** `.metadata/types/bookmark.toml` SHALL exist with fields: `url` (url, required), `title` (string, optional), `tags` (list of string, optional)
- **THEN** the bookmark type SHALL have `body_model: null`

#### Scenario: File type schema
- **WHEN** the vault is initialized
- **THEN** `.metadata/types/file.toml` SHALL exist with no custom fields
- **THEN** the file type SHALL have `body_model: file(binary)` indicating the blob is opaque

### Requirement: Schema format

Type schemas SHALL follow a standard TOML format.

#### Scenario: Schema structure
- **WHEN** reading any type schema file
- **THEN** the schema SHALL contain: `name`, `icon` (optional emoji), `fields` (array of inline tables)
- **THEN** each field definition SHALL contain: `name`, `type` (`string`, `url`, `datetime`, `number`, `array`), `required` (boolean, default false)

#### Scenario: Contact schema TOML example
- **WHEN** the system reads `.metadata/types/contact.toml`
- **THEN** the content SHALL parse as valid YAML matching the schema format

### Requirement: Custom user types

The system SHALL allow users to define custom types by creating new files in `.metadata/types/`.

#### Scenario: Create custom type
- **WHEN** user creates `.metadata/types/movie.toml` with required fields
- **THEN** the system SHALL recognize `movie` as a valid type on next command
- **THEN** user can run `prism new movie --title "Inception" --year 2010`

#### Scenario: Invalid custom type
- **WHEN** user creates a type schema with missing `name` field
- **THEN** the system SHALL display a validation error and skip the type

### Requirement: Field validation on node creation

The system SHALL validate fields against the type schema when creating or editing nodes.

#### Scenario: Valid fields pass
- **WHEN** creating a contact with all required fields provided
- **THEN** the node SHALL be created successfully

#### Scenario: Missing required field
- **WHEN** creating a contact without the required `name` field
- **THEN** the system SHALL reject the operation with: "Field 'name' is required for type 'contact'"

#### Scenario: Unknown field ignored
- **WHEN** creating a contact with an undefined field `--favorite-color blue`
- **THEN** the system SHALL warn: "Unknown field 'favorite_color' for type 'contact'. It will be ignored."
- **THEN** the system SHALL proceed without including the unknown field
