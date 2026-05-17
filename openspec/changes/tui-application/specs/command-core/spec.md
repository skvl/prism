## MODIFIED Requirements

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

### ADDED Requirements

### Requirement: TUI bridge command

The CLI SHALL provide a `prism tui` command that launches the prism-tui application as a subprocess.

#### Scenario: Bridge launches TUI with vault
- **WHEN** user runs `prism tui --vault /path/to/vault`
- **THEN** the system SHALL launch `sys.executable -m prism_tui --vault /path/to/vault` as a subprocess
- **THEN** the TUI SHALL inherit the current terminal

#### Scenario: Bridge launches TUI without vault
- **WHEN** user runs `prism tui` without `--vault`
- **THEN** the system SHALL launch `sys.executable -m prism_tui` as a subprocess
- **THEN** the TUI SHALL detect vault via context detection fallback

#### Scenario: Bridge returns TUI exit code
- **WHEN** the TUI subprocess exits
- **THEN** the CLI bridge SHALL return the same exit code
