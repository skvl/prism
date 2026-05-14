# Testing

## ADDED Requirements

### Requirement: Path resolution resolves root and nested paths
The PathResolver SHALL resolve absolute path strings to UUIDs by traversing the path tree via `path-parent` links.

#### Scenario: Resolve root path
- **WHEN** `PathResolver.resolve("/")` is called on a vault with a configured path root
- **THEN** it SHALL return the root node's UUID

#### Scenario: Resolve single-segment path
- **WHEN** `PathResolver.resolve("/foo")` is called and a child node with name "foo" exists under root
- **THEN** it SHALL return that child node's UUID

#### Scenario: Resolve multi-segment path
- **WHEN** `PathResolver.resolve("/foo/bar/baz")` is called and the tree has nodes foo→bar→baz linked by `path-parent`
- **THEN** it SHALL return the baz node's UUID

#### Scenario: Resolve nonexistent path raises error
- **WHEN** `PathResolver.resolve("/nonexistent")` is called
- **THEN** it SHALL raise `ValueError`

#### Scenario: Resolve without leading slash raises error
- **WHEN** `PathResolver.resolve("foo")` is called without a leading `/`
- **THEN** it SHALL raise `ValueError`

### Requirement: Path resolution creates missing segments on demand
The `resolve_or_create` method SHALL create intermediate path nodes when they don't exist.

#### Scenario: Create missing path segments
- **WHEN** `PathResolver.resolve_or_create("/new/path")` is called on a vault with only root
- **THEN** it SHALL create nodes "new" and "path" linked by `path-parent` and return the leaf UUID

#### Scenario: Create with existing prefix
- **WHEN** `PathResolver.resolve_or_create("/foo/bar")` is called and "foo" already exists
- **THEN** it SHALL create only "bar" under the existing "foo" node

#### Scenario: Invalid segment characters raise error
- **WHEN** `PathResolver.resolve_or_create("/bad spaces/invalid!chars")` is called
- **THEN** it SHALL raise `ValueError`

### Requirement: Path resolution collects descendant UUIDs
The `collect_descendants` method SHALL return all UUIDs in the subtree below a given node.

#### Scenario: Collect descendants
- **WHEN** `collect_descendants(root_uuid)` is called on a tree with root→a→b and root→c
- **THEN** it SHALL return a list containing the UUIDs of a, b, and c

#### Scenario: Cycle detection prevents cycles
- **WHEN** attaching a node whose descendant would be the target parent
- **THEN** `_would_create_cycle` SHALL return `True`

### Requirement: Path completion suggests partial paths
The `complete` method SHALL return matching path completions for a prefix.

#### Scenario: Complete partial segment
- **WHEN** `complete("/fo")` is called and a node named "foo" exists under root
- **THEN** it SHALL return `["/foo"]`

#### Scenario: Complete with multiple matches
- **WHEN** `complete("/f")` is called and nodes "foo" and "bar" exist under root
- **THEN** it SHALL return `["/bar", "/foo"]` (sorted)

#### Scenario: Complete with no matches returns empty
- **WHEN** `complete("/z")` is called and no node starts with "z" under root
- **THEN** it SHALL return `[]`

### Requirement: UUID-to-path reverse resolution works
The `resolve_uuid_to_path` method SHALL return the absolute path string for a given node UUID by walking parent links to root.

#### Scenario: Resolve UUID to path
- **WHEN** `resolve_uuid_to_path(leaf_uuid)` is called on a tree root→foo→bar→baz
- **THEN** it SHALL return `"/foo/bar/baz"`

#### Scenario: Resolve root UUID returns "/"
- **WHEN** `resolve_uuid_to_path(root_uuid)` is called
- **THEN** it SHALL return `"/"`

#### Scenario: Unknown UUID returns empty string
- **WHEN** `resolve_uuid_to_path(nonexistent_uuid)` is called
- **THEN** it SHALL return `""`

### Requirement: Node manager delete handles non-interactive paths
The `delete_node` method SHALL handle force-delete and nonexistent UIDs correctly.

#### Scenario: Force delete ignores backlinks
- **WHEN** `delete_node(uid, force=True)` is called on a node with backlinks
- **THEN** it SHALL delete the node without prompting

#### Scenario: Delete nonexistent node returns False
- **WHEN** `delete_node(nonexistent_uid)` is called
- **THEN** it SHALL return `False`

### Requirement: Show node displays path assignments
The `show_node` method SHALL include path information when a node has paths assigned.

#### Scenario: Show node with path
- **WHEN** `show_node(uid)` is called on a node with an assigned path
- **THEN** the output SHALL contain the resolved path string

### Requirement: Query engine handles NOT and edge cases
The query engine SHALL correctly evaluate `NOT` negation and handle invalid field comparisons gracefully.

#### Scenario: NOT negation excludes matching nodes
- **WHEN** executing `NOT tag:foo` against nodes tagged with and without "foo"
- **THEN** only nodes without "foo" SHALL be returned

#### Scenario: Invalid field comparison returns empty
- **WHEN** executing a query comparing a nonexistent field
- **THEN** the result SHALL be empty (no match)

#### Scenario: Nested NOT with AND works
- **WHEN** executing `tag:foo AND NOT tag:bar`
- **THEN** nodes tagged "foo" but not "bar" SHALL be returned

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
