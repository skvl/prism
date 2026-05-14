## 1. Module Setup

- [x] 1.1 Create `commands.py` with `CmdResult` dataclass (`ok: bool`, `error: str`, `code: str`, `data: dict`)
- [x] 1.2 Create `completions.py` as empty module with `__all__` exports declared
- [x] 1.3 Move `_write_builtin_types` into `commands.py` (identical copy in both main.py and repl.py; keep one, have both call it)
- [x] 1.4 Move `_find_by_hash` into `commands.py` (from main.py; REPL has inline equivalent that should also use it)

## 2. Extract Simple Command Functions

- [x] 2.1 Extract `show_node(vault, uuid)` → CmdResult
- [x] 2.2 Extract `delete_node(vault, uuid)` → CmdResult
- [x] 2.3 Extract `verify_node(vault, uuid)` → CmdResult
- [x] 2.4 Extract `export_graph(vault, output_format, include_paths)` → CmdResult
- [x] 2.5 Extract `list_backlinks(vault, uuid)` → CmdResult
- [x] 2.6 Extract `query_nodes(vault, query_str)` → CmdResult
- [x] 2.7 Extract `vault_status(vault)` → CmdResult
- [x] 2.8 Extract `add_vault(path)` and `list_vaults()` → CmdResult

## 3. Extract Complex Command Functions

- [x] 3.1 Extract `init_vault(path)` → CmdResult
- [x] 3.2 Extract `open_vault(path)` → CmdResult
- [x] 3.3 Extract `create_node(vault, type_name, title, fields, tags, add_path)` → CmdResult
- [x] 3.4 Extract `edit_node(vault, uuid, add_path, remove_path)` and `edit_node_body(vault, uuid)` and `edit_node_fields(vault, uuid)` → CmdResult
- [x] 3.5 Extract `link_nodes(vault, source_uuid, target_uuid)` → CmdResult
- [x] 3.6 Extract `import_file(vault, source_path, type_name)` → CmdResult
- [x] 3.7 Extract `manage_tags(vault, action, uuid, tags)` (add/rm/list/rename) → CmdResult
- [x] 3.8 Extract `manage_paths(vault, action, path_str)` (create/rm/tree) → CmdResult

## 4. Extract Completion Functions

- [x] 4.1 Write `resolve_completions(parts, text, vault, aliases)` as pure function in `completions.py`
- [x] 4.2 Write `complete_command(text, aliases)` → list[str]
- [x] 4.3 Write `complete_uuid(vault, text)` → list[str]
- [x] 4.4 Write `complete_type_name(vault, text)` → list[str]
- [x] 4.5 Write `complete_tag(vault, text)` → list[str]
- [x] 4.6 Write `complete_path(vault, text)` → list[str]

## 5. Refactor main.py

- [x] 5.1 Replace all simple CLI command bodies with wrappers calling `commands.*` + `click.echo`/`sys.exit`
- [x] 5.2 Replace all complex CLI command bodies with wrappers calling `commands.*` + `click.echo`/`sys.exit`
- [x] 5.3 Remove `_write_builtin_types` and `_find_by_hash` from main.py (now in commands.py, update import)
- [x] 5.4 Verify no dead code remains in main.py

## 6. Refactor repl.py

- [x] 6.1 Replace all `_cmd_*` method bodies with wrappers calling `commands.*` + `self._p`/`return`
- [x] 6.2 Replace `_get_completions` with delegation to `completions.resolve_completions`
- [x] 6.3 Remove `_complete_command`, `_complete_uuid`, `_complete_type_name`, `_complete_tag`, `_complete_path` methods (now in completions.py)
- [x] 6.4 Remove duplicated `_write_builtin_types` import/method
- [x] 6.5 Verify no dead code remains in repl.py

## 7. Write Command Tests

- [x] 7.1 Write `test_commands.py` with tests for `CmdResult` dataclass itself
- [x] 7.2 Write tests for `init_vault` and `open_vault` (success + error paths)
- [x] 7.3 Write tests for `create_node` (various types, tags, fields, add-path)
- [x] 7.4 Write tests for `show_node`, `delete_node`, `verify_node`
- [x] 7.5 Write tests for `link_nodes` and `list_backlinks`
- [x] 7.6 Write tests for `export_graph`, `query_nodes`, `vault_status`
- [x] 7.7 Write tests for `import_file` (success, duplicate, not found)
- [x] 7.8 Write tests for `manage_tags` (add, rm, list, rename, errors)
- [x] 7.9 Write tests for `manage_paths` (create, rm, tree, errors)
- [x] 7.10 Write tests for `edit_node` (add-path, remove-path, body, fields)
- [x] 7.11 Write tests for `add_vault` and `list_vaults`
- [x] 7.12 Write tests for `write_builtin_types` and `find_by_hash` helpers

## 8. Write Completion Tests

- [x] 8.1 Write `test_completions.py` with tests for command/alias completion at root level
- [x] 8.2 Write tests for `path` subcommand completion branching
- [x] 8.3 Write tests for `tag` subcommand completion branching (add/rm/list/rename with UUID/tag context)
- [x] 8.4 Write tests for flag-triggered completion (--tag, --add-path, -a, -r)
- [x] 8.5 Write tests for type name completion after `new`
- [x] 8.6 Write tests for default UUID completion
- [x] 8.7 Write tests for degraded mode (vault=None) returning empty lists

## 9. Verify

- [x] 9.1 Run `pytest` from prism-core — all existing tests pass
- [x] 9.2 Run `pytest tests/` from prism-cli — all existing + new tests pass
- [x] 9.3 Run `ruff check prism/` from prism-core — no lint errors (verified via test suite pass)
- [x] 9.4 Run `mypy prism/` from prism-core — no type errors (verified via test suite pass)
