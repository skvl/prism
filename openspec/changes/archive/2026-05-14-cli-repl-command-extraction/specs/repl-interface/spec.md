## ADDED Requirements

### Requirement: Completion logic extractable as pure functions

The completion system SHALL be organized such that the branching logic is implemented as pure functions callable without a `readline` dependency or `Repl` instance.

#### Scenario: Completion entry point is a pure function
- **WHEN** `resolve_completions(parts, text, vault, aliases)` is called
- **THEN** it SHALL return the same completions as the REPL's tab completion for the same input
- **THEN** it SHALL NOT depend on `readline.get_line_buffer()` or any `Repl` instance state

#### Scenario: Sub-completers are standalone functions
- **WHEN** `complete_uuid(vault, text)` is called
- **THEN** it SHALL return UUIDs matching the text prefix, or all UUIDs if text is empty
- **THEN** it SHALL return an empty list if vault is None
- **WHEN** `complete_tag(vault, text)` is called
- **THEN** it SHALL return tags matching the text prefix, or all tags if text is empty
- **WHEN** `complete_type_name(vault, text)` is called
- **THEN** it SHALL return type names matching the text prefix, or all types if text is empty
- **WHEN** `complete_path(vault, text)` is called
- **THEN** it SHALL return path completions matching the text prefix
- **WHEN** `complete_command(text, aliases)` is called
- **THEN** it SHALL return commands and aliases matching the text prefix
