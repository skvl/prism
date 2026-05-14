## 1. Core Library — NodeManager methods

- [x] 1.1 Add `add_tag(uuid: str, tag: str) -> bool` — validates tag, appends to node's tags list if absent, saves metadata, returns True if changed
- [x] 1.2 Add `remove_tag(uuid: str, tag: str) -> bool` — removes tag from node's tags list if present, saves metadata, returns True if changed
- [x] 1.3 Add `list_tags() -> dict[str, int]` — walks all nodes, collects unique tags with node counts, returns sorted dict
- [x] 1.4 Add `rename_tag(old_tag: str, new_tag: str) -> int` — validates new tag, iterates all nodes, replaces old with new (deduplicating), saves each changed node, returns count of affected nodes

## 2. CLI — tag command group

- [x] 2.1 Create `tag` Click group in `main.py` (following `path_cmd` pattern)
- [x] 2.2 Implement `prism tag add <uuid> <tag> [<tag>...]` — accepts multiple tags, calls `add_tag` for each, reports results
- [x] 2.3 Implement `prism tag rm <uuid> <tag> [<tag>...]` — accepts multiple tags, calls `remove_tag` for each, reports results
- [x] 2.4 Implement `prism tag list [--count]` — calls `list_tags`, formats output per design (sorted, optional `tagname (N)`)
- [x] 2.5 Implement `prism tag rename <old-tag> <new-tag>` — validates args, calls `rename_tag`, reports affected node count

## 3. REPL — tag command support

- [x] 3.1 Add `_cmd_tag` dispatch method in `Repl` that routes to `_cmd_tag_add`, `_cmd_tag_rm`, `_cmd_tag_list`, `_cmd_tag_rename`
- [x] 3.2 Implement `_cmd_tag_add` — parses UUID + tags, calls `manager.add_tag`
- [x] 3.3 Implement `_cmd_tag_rm` — parses UUID + tags, calls `manager.remove_tag`
- [x] 3.4 Implement `_cmd_tag_list` — parses `--count`, calls `manager.list_tags`, displays output
- [x] 3.5 Implement `_cmd_tag_rename` — parses old/new, calls `manager.rename_tag`
- [x] 3.6 Add tab completion: UUIDs for `tag add`/`tag rm`, tag names for `tag rm`/`tag rename`
- [x] 3.7 Add `tag` to help text and command listing

## 4. Tutor — Lesson 7: Tag Management

- [x] 4.1 Create new Lesson 7 with tag management steps (add/rm/list/rename)
- [x] 4.2 Bump current Lesson 7→8, update `TOTAL_LESSONS` to 8
- [x] 4.3 Update `_show_final_summary` to include tag management skills
- [x] 4.4 Add verification helpers if needed (e.g., `_verify_tag_count`)

## 5. README

- [x] 5.1 Add `prism tag add`, `rm`, `list`, `rename` to the Commands table
- [x] 5.2 Add tag management examples to Quick Start section

## 6. Tests

- [x] 6.1 Unit tests for `NodeManager.add_tag`, `remove_tag`, `list_tags`, `rename_tag` in `prism-core/tests/test_manager.py`
- [x] 6.2 CLI integration tests for `prism tag *` commands in `prism-cli/tests/test_main.py`
- [x] 6.3 REPL tests for `tag *` commands in `prism-core/tests/test_repl.py`
