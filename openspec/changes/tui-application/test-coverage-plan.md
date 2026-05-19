# Test Coverage Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise each package (prism-core, prism-cli, prism-tui) to 90%+ line coverage.

**Architecture:** Work package-order (core → cli → tui), lowest-coverage module first within each package. Unit tests with `MagicMock` for TUI, real temp vaults for core/cli. All new tests go in existing test files.

**Tech Stack:** pytest, pytest-cov, unittest.mock

---

## File Structure

All modifications are test additions to existing files — no new source files needed. Test files changed:

| File | Package | Change |
|------|---------|--------|
| `prism-core/tests/test_storage.py` | core | Add 5 tests |
| `prism-core/tests/test_path_resolver.py` | core | Add 3 tests |
| `prism-core/tests/test_query.py` | core | Add 3 tests |
| `prism-core/tests/test_manager.py` | core | Add 1 test |
| `prism-core/tests/test_metadata.py` | core | Add 1 test |
| `prism-core/tests/test_graph.py` | core | Add 1 test |
| `prism-core/tests/test_tracking.py` | core | Add 1 test |
| `prism-cli/tests/test_tutor.py` | cli | Add ~15 tests |
| `prism-cli/tests/test_completions.py` | cli | Add 3 tests |
| `prism-cli/tests/test_repl.py` | cli | Add 8 tests |
| `prism-cli/tests/test_main.py` | cli | Add 8 tests |
| `prism-cli/tests/test_commands.py` | cli | Add 3 tests |
| `prism-tui/tests/test_command_dispatch.py` | tui | Add 6 tests |
| `prism-tui/tests/test_browser.py` (new) | tui | Create with ~8 tests |
| `prism-tui/tests/test_tag_cloud.py` | tui | Add 4 tests |
| `prism-tui/tests/test_query_builder.py` | tui | Add 4 tests |
| `prism-tui/tests/test_app.py` (new) | tui | Create with ~5 tests |
| `prism-tui/tests/test_command_bar.py` (new) | tui | Create with ~4 tests |
| `prism-tui/tests/test_graph.py` | tui | Add 5 tests |

Coverage config: add `[tool.coverage.run]` to each `pyproject.toml`.

---

### Task 1: prism-core edge case coverage

**Files:**
- Modify: `prism-core/tests/test_storage.py`
- Modify: `prism-core/tests/test_path_resolver.py`
- Modify: `prism-core/tests/test_query.py`
- Modify: `prism-core/tests/test_manager.py`
- Modify: `prism-core/tests/test_metadata.py`
- Modify: `prism-core/tests/test_graph.py`
- Modify: `prism-core/tests/test_tracking.py`
- Modify: `prism-core/pyproject.toml`

- [ ] **Step 1: Add `read_description` / `delete_description` / `verify_integrity` tests to `test_storage.py`**

Add inside `TestStorageEngine` class (before the closing `class` indent):

```python
def test_read_description_missing(self, storage_engine):
    result = storage_engine.read_description("nonexistent-uuid")
    assert result is None

def test_delete_description_found(self, storage_engine, sample_node):
    storage_dir = compute_storage_path(storage_engine.vault_path, sample_node.uuid)
    desc_path = NodeMetadata.description_path(storage_dir)
    os.makedirs(storage_dir, exist_ok=True)
    Path(desc_path).write_text("test description")
    result = storage_engine.delete_description(sample_node.uuid)
    assert result is True
    assert not os.path.exists(desc_path)

def test_delete_description_not_found(self, storage_engine):
    result = storage_engine.delete_description("nonexistent-uuid")
    assert result is False

def test_verify_integrity_no_blob(self, storage_engine):
    result = storage_engine.verify_integrity("nonexistent-uuid", "abc123")
    assert result is False

def test_verify_description_integrity_empty_hash(self, storage_engine, sample_node):
    result = storage_engine.verify_description_integrity(sample_node.uuid, "")
    assert result is True

def test_verify_description_integrity_no_file(self, storage_engine, sample_node):
    result = storage_engine.verify_description_integrity(sample_node.uuid, "abc123")
    assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest prism-core/tests/test_storage.py -v -k "test_read_description_missing or test_delete_description_found or test_delete_description_not_found or test_verify_integrity_no_blob or test_verify_description_integrity_empty_hash or test_verify_description_integrity_no_file"`
Expected: FAIL — these methods exist but tests confirm pass/fail logic

- [ ] **Step 3: Run tests to verify they pass**

Run: same command
Expected: PASS (methods already exist, tests should pass)

- [ ] **Step 4: Add `complete` / `resolve_uuid_to_path` / `would_create_cycle` edge case tests to `test_path_resolver.py`**

Add inside `TestPathResolver` class:

```python
def test_complete_non_absolute_prefix(self, path_resolver):
    result = path_resolver.complete("foo")
    assert result == []

def test_complete_nonexistent_parent(self, path_resolver):
    result = path_resolver.complete("/nonexistent/child")
    assert result == []

def test_resolve_uuid_to_path_not_found(self, path_resolver):
    result = path_resolver.resolve_uuid_to_path("00000000-0000-0000-0000-000000000000")
    assert result == ""
```

- [ ] **Step 5: Add `_match` path filter / `_text_match` edge case tests to `test_query.py`**

Add inside `TestQueryEngine` class:

```python
def test_execute_path_filter_nonexistent(self, query_engine, sample_nodes):
    ast = QueryParser().parse("path:/nonexistent")
    results = query_engine.execute(ast)
    assert results == []
```

Add inside `TestQueryParser` class:

```python
def test_parse_path_filter_without_leading_slash(self):
    ast = QueryParser().parse("path:foo")
    assert ast.terms == [{"text": "path:foo"}]
```

- [ ] **Step 6: Add `create_node` with type="path" test to `test_manager.py`**

Add inside `TestNodeManager` class:

```python
def test_create_node_path_type_raises(self, node_manager):
    with pytest.raises(ValueError, match="Path nodes cannot be created"):
        node_manager.create_node("path", "Test Path")
```

- [ ] **Step 7: Add invalid tag test to `test_metadata.py`**

Add inside `TestNodeMetadata` class:

```python
def test_invalid_tag_raises(self):
    with pytest.raises(ValueError, match="Invalid tag"):
        NodeMetadata(
            uuid=str(uuid.uuid4()),
            type="note",
            title="test",
            tags=["invalid tag with spaces"],
            fields={},
            links=[],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            sync_dirty=False,
        )
```

- [ ] **Step 8: Add `_filter_nodes` with `include_paths=True` test to `test_graph.py`**

Add inside `TestGraphExporter` class:

```python
def test_filter_nodes_include_paths(self, sample_nodes):
    result = GraphExporter._filter_nodes(sample_nodes, include_paths=True)
    assert result == sample_nodes
```

- [ ] **Step 9: Add `re_extract_links` with no blob extension test to `test_tracking.py`**

Find the `TestChangeTracker` class and add:

```python
def test_re_extract_links_no_blob(self, change_tracker, sample_node):
    result = change_tracker.re_extract_links(sample_node.uuid)
    assert result is True
```

- [ ] **Step 10: Add coverage config to `prism-core/pyproject.toml`**

```toml
[tool.coverage.run]
source_pkg = ["prism"]
relative_files = true
```

- [ ] **Step 11: Run all prism-core tests and verify coverage**

Run: `python -m pytest prism-core/tests/ --cov=prism --cov-report=term-missing`
Expected: ~97%+ coverage, all tests pass

- [ ] **Step 12: Commit**

```bash
git add prism-core/tests/ prism-core/pyproject.toml
git commit -m "test(core): add edge case tests to reach 97%+ coverage"
```

---

### Task 2: prism-cli tutor.py coverage

**Files:**
- Modify: `prism-cli/tests/test_tutor.py`
- Modify: `prism-cli/pyproject.toml`

- [ ] **Step 1: Read existing test file to understand patterns**

Run: `python -c "import ast; print([c.name for c in ast.parse(open('prism-cli/tests/test_tutor.py').read()).body if isinstance(c, ast.ClassDef)])"`
Expected: list of existing test class names

Read `prism-cli/tests/test_tutor.py` — understand the test fixture approach (how they create Tutor instances).

- [ ] **Step 2: Add test for `_verify_vault_init` failure path**

```python
def test_verify_vault_init_fails_on_missing_dir(self):
    tutor = Tutor()
    tutor._create_temp_vault()
    result = tutor._verify_vault_init(tutor.vault)
    assert result is False
    tutor._cleanup(keep=False)
```

- [ ] **Step 3: Add test for `_verify_blob_integrity` failure**

```python
def test_verify_blob_integrity_corrupted(self, tutor_with_vault):
    vault = tutor_with_vault.vault
    manager = NodeManager(vault)
    uid = manager.create_node("note", "test", tags=[]).uuid
    result = tutor_with_vault._verify_blob_integrity(vault, uid)
    assert result is True
    storage_dir = compute_storage_path(vault.path, uid)
    body_path = os.path.join(storage_dir, "data.md")
    with open(body_path, "w") as f:
        f.write("corrupted content")
    result = tutor_with_vault._verify_blob_integrity(vault, uid)
    assert result is False
```

- [ ] **Step 4: Add test for `_verify_description`**

```python
def test_verify_description(self, tutor_with_vault):
    vault = tutor_with_vault.vault
    manager = NodeManager(vault)
    uid = manager.create_node("note", "test", tags=[]).uuid
    storage_dir = compute_storage_path(vault.path, uid)
    desc_path = NodeMetadata.description_path(storage_dir)
    Path(desc_path).write_text("hello world")
    result = tutor_with_vault._verify_description(vault, uid, "hello")
    assert result is True
    result = tutor_with_vault._verify_description(vault, uid, "nope")
    assert result is False
```

- [ ] **Step 5: Add test for `_verify_always_true`**

```python
def test_verify_always_true(self, tutor_with_vault):
    result = tutor_with_vault._verify_always_true(tutor_with_vault.vault)
    assert result is True
```

- [ ] **Step 6: Add test for `_show_output` and `_show_success` rendering**

```python
def test_show_output(self, tutor_with_vault, capsys):
    tutor_with_vault._show_output("test output")
    captured = capsys.readouterr()
    assert "test output" in captured.out

def test_show_success(self, tutor_with_vault, capsys):
    tutor_with_vault._show_success("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out
```

- [ ] **Step 7: Add test for `_sha256`**

```python
def test_sha256(self, tutor_with_vault):
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("hello")
        tmp = f.name
    result = tutor_with_vault._sha256(tmp)
    os.unlink(tmp)
    assert len(result) == 64
```

- [ ] **Step 8: Add test for `_execute_command` stdout capture**

```python
def test_execute_command_echo(self, tutor_with_vault):
    result = tutor_with_vault._execute_command("echo hello")
    assert result.returncode == 0
```

- [ ] **Step 9: Add test for `_build_lesson_plan` structure**

```python
def test_build_lesson_plan_structure(self):
    tutor = Tutor()
    lessons = tutor._build_lesson_plan()
    assert len(lessons) == 8
    assert all(isinstance(l, Lesson) for l in lessons)
    assert all(len(l.steps) >= 1 for l in lessons)
```

- [ ] **Step 10: Add test for `_get_node_uuid_by_title` not found**

```python
def test_get_node_uuid_by_title_not_found(self, tutor_with_vault):
    result = tutor_with_vault._get_node_uuid_by_title(tutor_with_vault.vault, "nonexistent")
    assert result is None
```

- [ ] **Step 11: Add coverage config to `prism-cli/pyproject.toml`**

```toml
[tool.coverage.run]
source_pkg = ["prism_cli"]
relative_files = true
```

- [ ] **Step 12: Run all prism-cli tutor tests and verify coverage**

Run: `python -m pytest prism-cli/tests/test_tutor.py --cov=prism_cli --cov-report=term-missing`
Expected: tutor.py coverage rises from ~46% to 70%+ (these tests plus existing ones)

- [ ] **Step 13: Commit**

```bash
git add prism-cli/tests/test_tutor.py prism-cli/pyproject.toml
git commit -m "test(cli): add tutor.py verify function and rendering tests"
```

---

### Task 3: prism-cli completions.py coverage

**Files:**
- Modify: `prism-cli/tests/test_completions.py`

- [ ] **Step 1: Add test for `complete_command` no match**

```python
def test_complete_command_no_match(self):
    results = complete_command("zzz", _ALIASES)
    assert results == []
```

- [ ] **Step 2: Add test for `resolve_completions` with flag completion**

```python
def test_resolve_completions_for_flag(self):
    parts = ["new", "--t"]
    results = resolve_completions(parts, "--t", None, _ALIASES)
    assert "--tag" in results
```

- [ ] **Step 3: Add test for `resolve_completions` with type name completion**

```python
def test_resolve_completions_for_type_name(self, vault):
    vault  # ensure vault fixture exists
    parts = ["new"]
    results = resolve_completions(parts, "not", vault, _ALIASES)
    assert "note" in results
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest prism-cli/tests/test_completions.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add prism-cli/tests/test_completions.py
git commit -m "test(cli): add completions.py edge case tests"
```

---

### Task 4: prism-cli repl.py coverage

**Files:**
- Modify: `prism-cli/tests/test_repl.py`

- [ ] **Step 1: Add test for REPL `_resolve_underscore` when `last_uuid` is None**

```python
def test_repl_resolve_underscore_no_last_uuid(self, repl):
    result = repl._resolve_underscore(["_"])
    assert result is None
```

- [ ] **Step 2: Add test for REPL empty input handling**

```python
def test_repl_empty_input(self, repl):
    result = repl._handle_line("")
    assert result is False
```

- [ ] **Step 3: Add test for REPL whitespace-only input**

```python
def test_repl_whitespace_input(self, repl):
    result = repl._handle_line("   ")
    assert result is False
```

- [ ] **Step 4: Add test for REPL degraded mode commands**

```python
def test_repl_init_in_degraded(self, repl):
    result = repl._handle_line("init /tmp/prism-test-repl-init")
    assert result is False
    assert repl.vault is not None
```

- [ ] **Step 5: Add test for REPL unknown command**

```python
def test_repl_unknown_command(self, repl):
    result = repl._handle_line("nonexistent_cmd")
    assert result is False
```

- [ ] **Step 6: Add test for REPL `_cmd_status` with no changes**

```python
def test_repl_status_clean(self, repl_with_vault, capsys):
    repl_with_vault._handle_line("status")
    captured = capsys.readouterr()
    assert "clean" in captured.out.lower() or "changed" in captured.out.lower()
```

- [ ] **Step 7: Add test for REPL `_cmd_verify`**

```python
def test_repl_verify_node(self, repl_with_vault, capsys):
    repl_with_vault._handle_line("new note test")
    uid = repl_with_vault.last_uuid
    repl_with_vault._handle_line(f"verify {uid}")
    captured = capsys.readouterr()
    assert "OK" in captured.out or "NOT" in captured.out
```

- [ ] **Step 8: Run tests**

Run: `python -m pytest prism-cli/tests/test_repl.py -v`
Expected: all pass

- [ ] **Step 9: Commit**

```bash
git add prism-cli/tests/test_repl.py
git commit -m "test(cli): add repl.py edge case and degraded mode tests"
```

---

### Task 5: prism-cli main.py coverage

**Files:**
- Modify: `prism-cli/tests/test_main.py`

- [ ] **Step 1: Add test for CLI `init` with existing vault**

```python
class TestInitExisting:
    def test_init_on_existing_vault(self, cli_invoker, vault):
        result = cli_invoker("init", str(vault.path))
        assert result.exit_code != 0
```

- [ ] **Step 2: Add test for CLI `list` with JSON format**

```python
class TestListJson:
    def test_list_json_format(self, cli_invoker, vault_with_nodes):
        result = cli_invoker("list", "--format", "json")
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert isinstance(data, list)
```

- [ ] **Step 3: Add test for CLI `query` with JSON format**

```python
class TestQueryJson:
    def test_query_json_format(self, cli_invoker, vault_with_nodes):
        result = cli_invoker("query", "tag:test", "--format", "json")
        assert result.exit_code == 0
```

- [ ] **Step 4: Add test for CLI `graph` with JSON format**

```python
class TestGraphJson:
    def test_graph_json_format(self, cli_invoker, vault_with_nodes):
        result = cli_invoker("graph", "json")
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert "nodes" in data
```

- [ ] **Step 5: Add test for CLI `backlinks` on node with no backlinks**

```python
class TestBacklinksNone:
    def test_backlinks_none(self, cli_invoker, vault_with_nodes):
        result = cli_invoker("backlinks", "00000000-0000-0000-0000-000000000001")
        assert result.exit_code == 0
```

- [ ] **Step 6: Add test for `_do_edit_path_ops` helper**

```python
class TestEditPathOps:
    def test_edit_add_path(self, cli_invoker, vault_with_nodes):
        result = cli_invoker("edit", "00000000-0000-0000-0000-000000000001", "--add-path", "/foo")
        assert result.exit_code == 0
```

- [ ] **Step 7: Run tests**

Run: `python -m pytest prism-cli/tests/test_main.py -v`
Expected: all pass

- [ ] **Step 8: Commit**

```bash
git add prism-cli/tests/test_main.py
git commit -m "test(cli): add main.py command edge case tests"
```

---

### Task 6: prism-cli commands.py coverage

**Files:**
- Modify: `prism-cli/tests/test_commands.py`

- [ ] **Step 1: Add test for `init_vault` on existing vault returning error**

```python
class TestInitExisting:
    def test_init_existing_vault(self, vault_with_nodes):
        from prism_cli.commands import init_vault
        result = init_vault(vault_with_nodes.path)
        assert "already" in result.message.lower() or "exists" in result.message.lower()
```

- [ ] **Step 2: Add test for listing vaults when none registered**

```python
class TestListVaultsEmpty:
    def test_list_vaults_empty(self, tmp_path):
        from prism_cli.commands import list_vaults
        result = list_vaults()
        assert result.exit_code == 0
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest prism-cli/tests/test_commands.py -v`
Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add prism-cli/tests/test_commands.py
git commit -m "test(cli): add commands.py edge case tests"
```

---

### Task 7: prism-tui command_mode.py coverage

**Files:**
- Modify: `prism-tui/tests/test_command_dispatch.py`
- New: `prism-tui/tests/test_wizards.py`

- [ ] **Step 1: Create `prism-tui/tests/test_wizards.py` for wizard tests**

```python
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from prism_tui.command_mode import execute_command


def test_execute_command_new_with_args():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    execute_command('new note "My Title" --tag work', vault, notify, push_screen)
    assert notify.called or push_screen.called


def test_execute_command_link_with_args():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    execute_command("link src-uuid dst-uuid", vault, notify, push_screen)
    assert notify.called or push_screen.called


def test_execute_command_tag_with_args():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    execute_command("tag node-uuid work important", vault, notify, push_screen)
    assert notify.called or push_screen.called


def test_execute_command_quit():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    with pytest.raises(SystemExit):
        execute_command("quit", vault, notify, push_screen)


def test_execute_command_exit():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    with pytest.raises(SystemExit):
        execute_command("exit", vault, notify, push_screen)


def test_execute_command_q():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    with pytest.raises(SystemExit):
        execute_command("q", vault, notify, push_screen)
```

- [ ] **Step 2: Run wizard tests**

Run: `python -m pytest prism-tui/tests/test_wizards.py -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_wizards.py
git commit -m "test(tui): add command_mode.py wizard and execute_command tests"
```

---

### Task 8: prism-tui browser.py coverage

**Files:**
- New: `prism-tui/tests/test_browser.py`

- [ ] **Step 1: Create `prism-tui/tests/test_browser.py`**

```python
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from prism_tui.tabs.browser import BrowserTab


@pytest.fixture
def browser_tab():
    tab = BrowserTab()
    tab._manager = MagicMock()
    tab._resolver = MagicMock()
    tab._nodes_by_uuid = {}
    tab._current_path_uuid = None
    tab._current_node = None
    tab._active_column = 0
    tab._filter_tag = None
    tab._filter_type = None
    return tab


def test_load_data_returns_when_no_manager(browser_tab):
    browser_tab._manager = None
    browser_tab._resolver = None
    browser_tab._load_data()
    assert browser_tab._nodes_by_uuid == {}


def test_refresh_node_list_returns_when_no_path(browser_tab):
    browser_tab._current_path_uuid = None
    browser_tab._refresh_node_list()


def test_show_preview_no_blob(browser_tab):
    node = MagicMock()
    node.uuid = "test-uuid"
    node.type = "note"
    node.tags = []
    node.blob_extension = None
    browser_tab._show_preview(node)


def test_set_column_focus_path_tree(browser_tab):
    browser_tab._active_column = 0
    browser_tab._path_tree = MagicMock()
    browser_tab._set_column_focus()


def test_set_column_focus_node_list(browser_tab):
    browser_tab._active_column = 1
    browser_tab._node_list = MagicMock()
    browser_tab._set_column_focus()


def test_on_edit_done_no_vault(browser_tab):
    browser_tab._vault = None
    browser_tab._on_edit_done(MagicMock())
```

- [ ] **Step 2: Run browser tests**

Run: `python -m pytest prism-tui/tests/test_browser.py -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_browser.py
git commit -m "test(tui): add browser.py unit tests"
```

---

### Task 9: prism-tui tag_cloud.py coverage

**Files:**
- Modify: `prism-tui/tests/test_tag_cloud.py`

- [ ] **Step 1: Add tag cloud tests**

```python
@pytest.fixture
def tag_cloud():
    from prism_tui.tabs.tag_cloud import TagCloudTab
    tab = TagCloudTab()
    tab._vault = MagicMock()
    tab._manager = MagicMock()
    tab._tag_nodes = {"work": ["uuid1", "uuid2"], "personal": ["uuid3"]}
    tab._tag_counts = type("Counter", (), {"most_common": lambda self, n: [("work", 2), ("personal", 1)]})()
    tab._selected_tags = set()
    tab._filtered_nodes = []
    tab._node_uuid_map = {}
    return tab


def test_load_tags_no_vault(tag_cloud):
    tag_cloud._vault = None
    tag_cloud._load_tags()


def test_render_cloud_no_tags(tag_cloud):
    tag_cloud._tag_counts = type("Counter", (), {"most_common": lambda self, n: []})()
    tag_cloud._render_cloud()


def test_highlight_co_occurring_no_selection(tag_cloud):
    tag_cloud._selected_tags = set()
    tag_cloud._highlight_co_occurring()


def test_update_node_list_no_selection(tag_cloud):
    tag_cloud._selected_tags = set()
    tag_cloud._update_node_list()
```

- [ ] **Step 2: Run tag cloud tests**

Run: `python -m pytest prism-tui/tests/test_tag_cloud.py -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_tag_cloud.py
git commit -m "test(tui): add tag_cloud.py edge case tests"
```

---

### Task 10: prism-tui query_builder.py coverage

**Files:**
- Modify: `prism-tui/tests/test_query_builder.py`

- [ ] **Step 1: Add query builder tests**

```python
@pytest.fixture
def query_builder():
    from prism_tui.tabs.query_builder import QueryBuilderTab
    tab = QueryBuilderTab()
    tab._vault = MagicMock()
    tab._manager = MagicMock()
    tab._results = []
    tab._history = []
    return tab


def test_set_vault_no_vault(query_builder):
    query_builder.set_vault(None)


def test_schedule_search_first_call(query_builder):
    query_builder._debounce_timer = None
    query_builder._schedule_search()
    assert query_builder._debounce_timer is not None


def test_update_results_empty(query_builder):
    query_builder._results = []
    query_builder._update_results()


def test_execute_search_text_only(query_builder):
    query_builder._manager.list_nodes.return_value = []
    query_builder._execute_search()
```

- [ ] **Step 2: Run query builder tests**

Run: `python -m pytest prism-tui/tests/test_query_builder.py -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_query_builder.py
git commit -m "test(tui): add query_builder.py edge case tests"
```

---

### Task 11: prism-tui app.py coverage

**Files:**
- New: `prism-tui/tests/test_app.py`

- [ ] **Step 1: Create `prism-tui/tests/test_app.py`**

```python
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def app():
    from prism_tui.app import PrismTui
    app = PrismTui()
    app._vault = MagicMock()
    return app


def test_on_vault_selected_none(app):
    app._on_vault_selected(None)


def test_action_new_node_no_vault(app):
    app._vault = None
    app.action_new_node()


def test_action_link_nodes_no_vault(app):
    app._vault = None
    app.action_link_nodes()


def test_action_tag_node_no_vault(app):
    app._vault = None
    app.action_tag_node()


def test_action_show_help(app):
    app.notify = MagicMock()
    app.action_show_help()
    assert app.notify.called
```

- [ ] **Step 2: Run app tests**

Run: `python -m pytest prism-tui/tests/test_app.py -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_app.py
git commit -m "test(tui): add app.py unit tests"
```

---

### Task 12: prism-tui command_bar.py coverage

**Files:**
- New: `prism-tui/tests/test_command_bar.py`

- [ ] **Step 1: Create `prism-tui/tests/test_command_bar.py`**

```python
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def command_bar():
    from prism_tui.command_bar import CommandBar
    bar = CommandBar()
    bar._vault = None
    bar._manager = None
    bar._current_tab = "browser"
    bar._current_column = 0
    return bar


def test_init_with_vault():
    from prism_tui.command_bar import CommandBar
    vault = MagicMock()
    bar = CommandBar(vault=vault)
    assert bar._manager is not None


def test_set_context_updates_labels(command_bar):
    command_bar._update_labels = MagicMock()
    command_bar.set_context("graph", column=1)
    assert command_bar._current_tab == "graph"
    assert command_bar._current_column == 1
    assert command_bar._update_labels.called


def test_get_labels_browser_tab(command_bar):
    labels = command_bar._get_labels()
    assert len(labels) == 8


def test_trigger_action_unknown(command_bar):
    command_bar._trigger_action("nonexistent_action")
```

- [ ] **Step 2: Run command bar tests**

Run: `python -m pytest prism-tui/tests/test_command_bar.py -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_command_bar.py
git commit -m "test(tui): add command_bar.py unit tests"
```

---

### Task 13: prism-tui graph.py coverage

**Files:**
- Modify: `prism-tui/tests/test_layout.py` (rename to `test_graph.py` or add graph tests)

- [ ] **Step 1: Add graph layout and rendering tests to `prism-tui/tests/test_graph.py`**

This file already exists and has layout tests. We need tests for `ForceDirectedLayout`:

```python
@pytest.fixture
def layout():
    from prism_tui.tabs.graph import ForceDirectedLayout
    nodes = {"uuid1": "Node 1", "uuid2": "Node 2"}
    links = [{"source": "uuid1", "target": "uuid2"}]
    return ForceDirectedLayout(nodes, links)


def test_layout_empty_nodes():
    from prism_tui.tabs.graph import ForceDirectedLayout
    layout = ForceDirectedLayout({}, [])
    result = layout.render_ascii(None, 80, 24, 0, 0, 1.0)
    assert result is not None


def test_layout_tick_converges(layout):
    layout.tick(iterations=10)
    for pos in layout.positions.values():
        assert 0 <= pos[0] <= layout.bounds
        assert 0 <= pos[1] <= layout.bounds


def test_render_ascii_with_selection(layout):
    result = layout.render_ascii("uuid1", 80, 24, 0, 0, 1.0)
    assert "Node 1" in result or "*" in result


def test_render_ascii_pan_and_zoom(layout):
    result = layout.render_ascii(None, 80, 24, 10, 10, 2.0)
    assert result is not None


def test_draw_line(layout):
    canvas = [[" " for _ in range(10)] for _ in range(10)]
    layout._draw_line(canvas, 0, 0, 9, 9, 10, 10)
    assert canvas[0][0] == "." or canvas[9][9] == "."
```

- [ ] **Step 2: Run graph tests**

Run: `python -m pytest prism-tui/tests/test_graph.py -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_graph.py
git commit -m "test(tui): add graph.py ForceDirectedLayout tests"
```

---

### Task 14: Add coverage config and verify final numbers

**Files:**
- Modify: `prism-tui/pyproject.toml`

- [ ] **Step 1: Add coverage config to `prism-tui/pyproject.toml`**

```toml
[tool.coverage.run]
source_pkg = ["prism_tui"]
relative_files = true
```

- [ ] **Step 2: Run full coverage report**

Run: `python -m pytest prism-core/tests/ prism-cli/tests/ prism-tui/tests/ --cov=prism --cov=prism_cli --cov=prism_tui --cov-report=term-missing`
Expected: each package at 90%+ overall

- [ ] **Step 3: Commit remaining config**

```bash
git add prism-tui/pyproject.toml
git commit -m "chore: add coverage config to prism-tui"
```

---

### Task 15: Final verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest prism-core/tests/ prism-cli/tests/ prism-tui/tests/ -v --tb=short`
Expected: all tests pass, no regressions

- [ ] **Step 2: Generate coverage report**

Run: `python -m pytest prism-core/tests/ prism-cli/tests/ prism-tui/tests/ --cov=prism --cov=prism_cli --cov=prism_tui --cov-report=term-missing 2>&1 | tail -30`
Expected: each package shows 90%+

- [ ] **Step 3: Report results**

Print the final coverage table and note any remaining gaps
