## ADDED Requirements

### Requirement: Command functions tested via CmdResult protocol

Each shared command function in `commands.py` SHALL have unit tests covering its success and failure paths via the `CmdResult` return protocol.

#### Scenario: Successful command tested via result.ok
- **WHEN** `commands.create_node(vault, "note", "Title")` is called
- **THEN** `result.ok` SHALL be `True`
- **THEN** `result.data` SHALL contain the created node's UUID and metadata

#### Scenario: Failed command tested via result.ok and result.error
- **WHEN** `commands.create_node(vault, "nonexistent-type", "Title")` is called
- **THEN** `result.ok` SHALL be `False`
- **THEN** `result.code` SHALL be `"VALIDATION_ERROR"` or equivalent
- **THEN** `result.error` SHALL contain a descriptive message

### Requirement: Completion functions tested via pure function calls

Each completion function in `completions.py` SHALL have unit tests covering all branching combinations without mocking `readline`.

#### Scenario: Command completion tested by parts input
- **WHEN** `resolve_completions([], "", vault)` is called
- **THEN** it SHALL return all available commands and aliases
- **WHEN** `resolve_completions(["n"], "n", vault)` is called with partial command text
- **THEN** it SHALL match the alias to the full command name

#### Scenario: Path subcommand completion branching
- **WHEN** `resolve_completions(["path"], "", vault)` is called
- **THEN** it SHALL return `["create", "rm", "tree"]`
- **WHEN** `resolve_completions(["path", "c"], "c", vault)` is called
- **THEN** it SHALL return `["create"]`

#### Scenario: Tag subcommand completion branching
- **WHEN** `resolve_completions(["tag"], "", vault)` is called
- **THEN** it SHALL return `["add", "rm", "list", "rename"]`
- **WHEN** `resolve_completions(["tag", "add", "abc"], "abc", vault)` is called
- **THEN** it SHALL complete UUIDs from the vault
- **WHEN** `resolve_completions(["tag", "rm", "abc", "wo"], "wo", vault)` is called
- **THEN** it SHALL complete tags from the vault
- **WHEN** `resolve_completions(["tag", "rename", "wo"], "wo", vault)` is called
- **THEN** it SHALL complete tags from the vault

#### Scenario: Flag-triggered completion
- **WHEN** `resolve_completions(["new", "note", "--tag"], "", vault)` is called
- **THEN** it SHALL complete tags from the vault
- **WHEN** `resolve_completions(["new", "note", "--add-path"], "", vault)` is called
- **THEN** it SHALL complete paths from the vault
- **WHEN** `resolve_completions(["edit", "uuid", "-a"], "", vault)` is called
- **THEN** it SHALL complete paths from the vault

#### Scenario: Type name completion
- **WHEN** `resolve_completions(["new"], "", vault)` is called with a vault having types
- **THEN** it SHALL complete type names from the vault
- **WHEN** `resolve_completions(["n", "n"], "n", vault)` is called
- **THEN** it SHALL match type names starting with "n" (e.g., "note")

#### Scenario: Default UUID completion
- **WHEN** `resolve_completions(["show"], "", vault)` is called with nodes in the vault
- **THEN** it SHALL return node UUIDs
- **WHEN** `resolve_completions(["show", "abc"], "abc", vault)` is called
- **THEN** it SHALL return UUIDs starting with "abc"

#### Scenario: Degraded mode returns empty for vault-dependent completions
- **WHEN** `resolve_completions(["show"], "", None)` is called without a vault
- **THEN** it SHALL return an empty list

### Requirement: Existing CLI and REPL tests remain passing

All existing integration tests in `test_main.py` and `test_repl.py` SHALL continue to pass after the refactor.

#### Scenario: CLI tests pass
- **WHEN** `pytest tests/test_main.py` is run
- **THEN** all existing tests SHALL pass

#### Scenario: REPL tests pass
- **WHEN** `pytest tests/test_repl.py` is run
- **THEN** all existing tests SHALL pass
