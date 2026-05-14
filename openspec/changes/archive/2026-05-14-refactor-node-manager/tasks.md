## 1. Library — New Methods & Dead Code Removal

- [x] 1.1 Remove `_would_create_cycle()` method from `NodeManager`
- [x] 1.2 Add `get_body_info(uid) -> tuple[str, float] | None` to `NodeManager`
- [x] 1.3 Add `commit_body_edit(uid, mtime, size, sha256)` to `NodeManager` (with `LinkExtractor.extract_from_file` call for md blobs)
- [x] 1.4 Add `get_field_info(uid) -> tuple[TypeSchema, dict]` to `NodeManager`
- [x] 1.5 Add `update_node_fields(uid, changes: dict) -> bool` to `NodeManager`
- [x] 1.6 Refactor `delete_node(uid, force=False)` — remove `input()` call, raise `ValueError` when backlinks exist and `force=False`

## 2. Library — Path Operations

- [x] 2.1 Add `add_path_to_node(uid, path_str) -> bool` to `NodeManager`
- [x] 2.2 Add `remove_path_from_node(uid, path_str) -> bool` to `NodeManager`

## 3. CLI — Update `edit` Command

- [x] 3.1 Restructure body editing path in `main.py` to use `get_body_info` + `commit_body_edit`
- [x] 3.2 Restructure field editing path in `main.py` to use `get_field_info` + `update_node_fields`
- [x] 3.3 Replace inline path add/remove logic with `add_path_to_node` / `remove_path_from_node`
- [x] 3.4 Remove O(n) storage walk (`main.py:497-510`) in favor of `_resolve_uuid`-based lookups

## 4. CLI — Update `rm` Command

- [x] 4.1 Wrap `delete_node` call in try/except for the new `ValueError` on backlinks
- [x] 4.2 Add interactive confirmation in CLI when backlinks exist (moved from library)

## 5. Tests

- [x] 5.1 Add tests for `get_body_info`: existing body, no blob extension, nonexistent body file
- [x] 5.2 Add tests for `commit_body_edit`: md body with link extraction, non-md body, verify links updated
- [x] 5.3 Add tests for `get_field_info`: existing node, nonexistent type
- [x] 5.4 Add tests for `update_node_fields`: single field update, multiple fields, empty changes returns False
- [x] 5.5 Add tests for `delete_node` ValueError on backlinks without force
- [x] 5.6 Add tests for `add_path_to_node` and `remove_path_from_node`
- [x] 5.7 Remove tests for deleted methods (`edit_node_body`, `edit_node_fields`)
- [x] 5.8 Run `pytest`, `ruff`, `mypy` — all pass
