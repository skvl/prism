## ADDED Requirements

### Requirement: CLI commands have full test coverage
The prism-cli SHALL have tests covering all CLI commands defined in `main.py`, including path subcommands, tag subcommands, and error branches.

#### Scenario: Path create succeeds
- **WHEN** `prism path create "/foo/bar"` is run against a vault
- **THEN** the system SHALL exit with code 0
- **THEN** the output SHALL contain "Path created"

#### Scenario: Path rm succeeds
- **WHEN** `prism path rm "/foo/bar" --yes` is run against a vault with an existing path
- **THEN** the system SHALL exit with code 0
- **THEN** the output SHALL contain "Removed path"

#### Scenario: Path tree displays hierarchy
- **WHEN** `prism path tree` is run against a vault with paths
- **THEN** the system SHALL exit with code 0
- **THEN** the output SHALL contain tree connector characters (├──, └──)

#### Scenario: Edit with add-path option
- **WHEN** `prism edit <uuid> --add-path /foo` is run against a vault with path /foo
- **THEN** the system SHALL exit with code 0
- **THEN** the output SHALL contain "Added path"

#### Scenario: No vault detected returns error
- **WHEN** any command is run outside a vault directory and without `--vault`
- **THEN** the system SHALL exit with code 1
- **THEN** the stderr SHALL contain "No vault found"

### Requirement: REPL is testable via I/O streams
The Repl class SHALL accept configurable input and output streams so tests can simulate interactive sessions.

#### Scenario: Repl reads from input stream
- **WHEN** `Repl(input_stream=io.StringIO("exit\n"))` is constructed
- **THEN** the REPL SHALL read commands from the provided stream
- **THEN** the REPL SHALL process the "exit" command and terminate

#### Scenario: Repl writes to output stream
- **WHEN** `Repl(output_stream=io.StringIO())` is constructed
- **THEN** the REPL SHALL write all output to the provided stream
- **THEN** no output SHALL appear on stdout

#### Scenario: Repl with vault detects it
- **WHEN** `Repl(vault=vault, input_stream=..., output_stream=...)` is constructed with a connected vault
- **THEN** the welcome message SHALL include "Connected to vault:"

#### Scenario: Repl without vault shows degraded message
- **WHEN** `Repl(input_stream=..., output_stream=...)` is constructed without a vault
- **THEN** the welcome message SHALL include "No vault connected"

### Requirement: REPL commands produce correct output
Each REPL command SHALL produce the same output as its CLI equivalent when given the same input.

#### Scenario: Repl new command creates a node
- **WHEN** `Repl(vault=vault, input_stream=io.StringIO("new note \"Test Title\"\nexit\n"), output_stream=io.StringIO())` is run
- **THEN** the output SHALL contain "Created note node:"

#### Scenario: Repl show command displays node
- **WHEN** a node exists and `Repl` receives `show <uuid>` followed by exit
- **THEN** the output SHALL contain the node's title

#### Scenario: Repl link command creates link
- **WHEN** two nodes exist and `Repl` receives `link <source> <target>` followed by exit
- **THEN** the output SHALL contain "Linked"

#### Scenario: Repl query command finds nodes
- **WHEN** a node with a tag exists and `Repl` receives `query tag:<tag>` followed by exit
- **THEN** the output SHALL contain the node's title

#### Scenario: Repl backlinks command shows backlinks
- **WHEN** a link exists from source to target and `Repl` receives `backlinks <target>` followed by exit
- **THEN** the output SHALL contain the source node's title

#### Scenario: Repl status command shows vault status
- **WHEN** `Repl` receives `status` followed by exit against a clean vault
- **THEN** the output SHALL contain "Vault is clean."

#### Scenario: Repl add-file command imports a file
- **WHEN** a file exists and `Repl` receives `add-file <path>` followed by exit
- **THEN** the output SHALL contain "Imported as node"

#### Scenario: Repl verify command checks integrity
- **WHEN** a node exists and `Repl` receives `verify <uuid>` followed by exit
- **THEN** the output SHALL contain "OK"

#### Scenario: Repl tag add/rm/list/rename work
- **WHEN** a node exists and `Repl` receives `tag add <uuid> work` then `tag list` then exit
- **THEN** the output SHALL contain "Added tag:" and "work"

#### Scenario: Repl path create/rm/tree work
- **WHEN** a vault has paths and `Repl` receives `path create /foo` then `path tree` then exit
- **THEN** the output SHALL contain "Path created" and tree content

#### Scenario: Repl alias resolution works
- **WHEN** `Repl` receives `n note "Alias Test"` then `s _` then exit
- **THEN** the output SHALL contain "Created note node:" and "Alias Test"

#### Scenario: Repl exit command saves history and terminates
- **WHEN** `Repl` receives `exit`
- **THEN** the `run` method SHALL return
- **THEN** history SHALL be persisted

#### Scenario: Repl quit command terminates
- **WHEN** `Repl` receives `quit`
- **THEN** the `run` method SHALL return

#### Scenario: Repl Ctrl+D terminates
- **WHEN** the input stream is exhausted (returns empty string)
- **THEN** the `run` method SHALL catch EOFError and return

#### Scenario: Repl unknown command shows error
- **WHEN** `Repl` receives `nonexistent_command` followed by exit
- **THEN** the output SHALL contain "Unknown command:"

#### Scenario: Repl degraded mode rejects vault commands
- **WHEN** `Repl` receives a vault command (e.g. `new`) without a connected vault
- **THEN** the output SHALL contain "No vault connected. Use 'init' or 'open' first."

#### Scenario: Repl init creates and connects to vault
- **WHEN** `Repl` receives `init /tmp/test-vault` in degraded mode
- **THEN** the output SHALL contain "Vault initialized at"
- **THEN** the REPL SHALL transition to full mode

#### Scenario: Repl open connects to existing vault
- **WHEN** `Repl` receives `open /path/to/vault` in degraded mode and a vault exists at that path
- **THEN** the output SHALL contain "Connected to vault:"

#### Scenario: Repl rm command deletes a node
- **WHEN** a node exists and `Repl` receives `rm <uuid>` followed by exit
- **THEN** the output SHALL contain "Deleted node"

#### Scenario: Repl graph command exports
- **WHEN** a node exists and `Repl` receives `graph` followed by exit
- **THEN** the output SHALL contain "digraph" (DOT format default)

#### Scenario: Repl help shows available commands
- **WHEN** `Repl` receives `help` followed by exit
- **THEN** the output SHALL contain "Available commands:"

#### Scenario: Repl help <command> shows specific help
- **WHEN** `Repl` receives `help new` followed by exit
- **THEN** the output SHALL contain "Create a new typed node."

#### Scenario: Repl tutor command shows error
- **WHEN** `Repl` receives `tutor` followed by exit
- **THEN** the output SHALL contain "The tutor command cannot run inside the REPL"

#### Scenario: Repl underscore references last UUID
- **WHEN** a node is created with `new` and the next command uses `_` as UUID
- **THEN** the system SHALL resolve `_` to the last created UUID

### Requirement: Tutor verification helpers are correct
The Tutor's verification methods SHALL be tested as isolated unit functions.

#### Scenario: Verify vault init detects vault.toml
- **WHEN** `_verify_vault_init(vault)` is called on an initialized vault
- **THEN** it SHALL return True
- **WHEN** called on a non-initialized directory
- **THEN** it SHALL return False

#### Scenario: Verify node count matches by type
- **WHEN** `_verify_node_count(vault, 1, "note")` is called on a vault with one note
- **THEN** it SHALL return True

#### Scenario: Verify node has tag works
- **WHEN** `_verify_node_has_tag(vault, uuid, "work")` is called on a node with tag "work"
- **THEN** it SHALL return True
- **WHEN** the tag doesn't exist
- **THEN** it SHALL return False

#### Scenario: Verify link exists between nodes
- **WHEN** `_verify_link_exists(vault, source_uuid, target_uuid)` is called on linked nodes
- **THEN** it SHALL return True

#### Scenario: Verify backlink detected
- **WHEN** `_verify_backlink(vault, target_uuid, source_uuid)` is called on linked nodes
- **THEN** it SHALL return True

#### Scenario: Verify query result finds expected node
- **WHEN** `_verify_query_result(vault, "tag:test", expected_uuid)` is called
- **THEN** it SHALL return True

#### Scenario: Verify file imported by hash
- **WHEN** `_verify_file_imported(vault, sha256_hash)` is called with a hash of an imported file
- **THEN** it SHALL return True

#### Scenario: Verify blob integrity passes for clean nodes
- **WHEN** `_verify_blob_integrity(vault, uuid)` is called on a node with matching hash
- **THEN** it SHALL return True

#### Scenario: Verify change detection finds modified nodes
- **WHEN** `_verify_change_detected(vault)` is called on a vault with a dirty node
- **THEN** it SHALL return True

#### Scenario: Verify tag count meets threshold
- **WHEN** `_verify_tag_count(vault, 2)` is called on a vault with 2+ tags
- **THEN** it SHALL return True

#### Scenario: Verify tag renamed updates tags dict
- **WHEN** `_verify_tag_renamed(vault, "old", "new")` is called after renaming
- **THEN** it SHALL return True

#### Scenario: Capture UUID stores short and full UUIDs
- **WHEN** `_capture_uuid("Title", "key")` is called on a vault with a node titled "Title"
- **THEN** `self._fmt["key"]` SHALL be the first 8 chars of the UUID
- **THEN** `self._fmt["_full_key"]` SHALL be the full UUID

#### Scenario: Resolve UUID returns full UUID for key
- **WHEN** `_resolve_uuid("key")` is called after `_capture_uuid`
- **THEN** it SHALL return the full UUID
- **WHEN** `_resolve_uuid("some-uuid")` is called without matching key
- **THEN** it SHALL return "some-uuid" unchanged

#### Scenario: SHA256 computes correct hash
- **WHEN** `_sha256(path)` is called on a file
- **THEN** it SHALL return the correct SHA-256 hex digest
