## ADDED Requirements

### Requirement: CmdResult return protocol

Shared command functions SHALL return a `CmdResult` dataclass with fields `ok: bool`, `error: str`, `code: str`, and `data: dict`.

#### Scenario: Successful command returns ok=True
- **WHEN** a command function executes successfully
- **THEN** `result.ok` SHALL be `True`
- **THEN** `result.error` SHALL be an empty string
- **THEN** `result.data` SHALL contain command-specific result fields

#### Scenario: Failed command returns ok=False with error info
- **WHEN** a command function encounters an error
- **THEN** `result.ok` SHALL be `False`
- **THEN** `result.error` SHALL contain a human-readable error message
- **THEN** `result.code` SHALL contain a machine-readable error code (e.g., `"NOT_FOUND"`, `"VALIDATION_ERROR"`, `"ALREADY_EXISTS"`)

### Requirement: Shared command functions

The system SHALL provide the following shared command functions in `commands.py`, each accepting a vault and command-specific parameters and returning `CmdResult`:

- `init_vault(path)` — Initialize a new vault at the given path
- `open_vault(path)` — Open an existing vault
- `create_node(vault, type_name, title, fields, tags, add_path)` — Create a typed node
- `show_node(vault, uuid)` — Display node details
- `edit_node(vault, uuid, add_path, remove_path)` — Edit a node's path associations
- `edit_node_body(vault, uuid)` — Edit a node's markdown body (returns body info for external editor)
- `edit_node_fields(vault, uuid)` — Edit a node's structured fields
- `delete_node(vault, uuid)` — Delete a node
- `link_nodes(vault, source_uuid, target_uuid)` — Create a directed link
- `list_backlinks(vault, uuid)` — List nodes linking to the given UUID
- `export_graph(vault, output_format, include_paths)` — Export the node graph
- `query_nodes(vault, query_str)` — Execute a query
- `vault_status(vault)` — Show vault change status
- `verify_node(vault, uuid)` — Verify blob integrity
- `import_file(vault, source_path, type_name)` — Import a file
- `manage_tags(vault, action, uuid, tags)` — Tag add/rm/list/rename operations
- `manage_paths(vault, action, path_str)` — Path create/rm/tree operations

#### Scenario: Each function returns CmdResult
- **WHEN** any shared command function is called
- **THEN** it SHALL return a `CmdResult` instance
- **THEN** it SHALL NOT call `click.echo`, `sys.exit`, `self._p`, or any I/O

### Requirement: Shared helper functions

The `commands.py` module SHALL also contain shared helper functions:

- `write_builtin_types(vault)` — Write built-in type TOML files (replaces duplicated copies in main.py and repl.py)
- `find_by_hash(manager, file_hash)` — Find a node by blob SHA-256 (moved from main.py)

#### Scenario: Helper functions produce same results as originals
- **WHEN** `write_builtin_types(vault)` is called
- **THEN** it SHALL create type files identical to the current implementation
- **WHEN** `find_by_hash(manager, hash)` is called
- **THEN** it SHALL return the same result as the current `_find_by_hash` in main.py
