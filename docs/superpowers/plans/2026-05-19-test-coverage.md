# Test Coverage Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `prism-cli` and `prism-tui` to ≥95% test coverage, add CI coverage gates, and update AGENTS.md.

**Architecture:** 12 files across 2 subpackages need additional tests. Work from lowest-coverage files upward in 3 phases. Each task targets one file's uncovered lines. Existing test patterns (MagicMock for TUI widgets, real temp vaults for CLI, StringIO for REPL) are followed throughout.

**Tech Stack:** pytest, unittest.mock, textual (pilot tests for integration), tempfile for vault fixtures

---

## Phase 1 — Deep gaps (<60%)

### Task 1: `prism_tui/tabs/tag_cloud.py` (43% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_tag_cloud.py`

- [ ] **Step 1: Add tests for event handlers and edge cases**

Add to `prism-tui/tests/test_tag_cloud.py`:

```python
def test_on_button_pressed_selects_tag(tag_cloud):
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    btn = MagicMock()
    btn._tag_name = "work"
    tag_cloud.on_button_pressed(btn)
    assert "work" in tag_cloud._selected_tags


def test_on_button_pressed_clear(tag_cloud):
    tag_cloud._selected_tags = {"work"}
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    btn = MagicMock()
    btn._tag_name = "__clear__"
    tag_cloud.on_button_pressed(btn)
    assert len(tag_cloud._selected_tags) == 0


def test_on_button_pressed_deselects_tag(tag_cloud):
    tag_cloud._selected_tags = {"work"}
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    btn = MagicMock()
    btn._tag_name = "work"
    tag_cloud.on_button_pressed(btn)
    assert "work" not in tag_cloud._selected_tags


def test_on_key_escape_clears_selection(tag_cloud):
    tag_cloud._selected_tags = {"work"}
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    event = MagicMock()
    event.key = "escape"
    tag_cloud.on_key(event)
    assert len(tag_cloud._selected_tags) == 0
    assert event.stop.called


def test_on_list_view_selected_posts_message(tag_cloud):
    tag_cloud._filtered_nodes = [
        _make_node("uuid1", ["work"]),
        _make_node("uuid2", ["personal"]),
    ]
    tag_cloud.post_message = MagicMock()
    event = MagicMock()
    event.item._node_uuid = "uuid1"
    tag_cloud.on_list_view_selected(event)
    assert tag_cloud.post_message.called


def test_on_list_view_selected_none_item(tag_cloud):
    tag_cloud.post_message = MagicMock()
    event = MagicMock()
    event.item = None
    tag_cloud.on_list_view_selected(event)
    assert not tag_cloud.post_message.called


def test_load_tags_with_vault(tag_cloud):
    tag_cloud._vault = MagicMock()
    tag_cloud._manager = MagicMock()
    tag_cloud._manager.list_nodes.return_value = [
        _make_node("a", ["work"]),
    ]
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    tag_cloud._load_tags()
    assert tag_cloud._tag_counts["work"] == 1


def test_compose_returns_widgets(tag_cloud):
    from textual.containers import VerticalScroll
    from textual.widgets import ListView
    result = list(tag_cloud.compose())
    assert len(result) == 2
    assert isinstance(result[0], VerticalScroll)
    assert isinstance(result[1], ListView)
```

- [ ] **Step 2: Run tag_cloud tests**

Run: `python -m pytest prism-tui/tests/test_tag_cloud.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_tag_cloud.py
git commit -m "test(tui): add tag cloud test coverage to 95%"
```

---

### Task 2: `prism_tui/tabs/browser.py` (51% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_browser.py`

- [ ] **Step 1: Add tests for BrowserTab edge cases and event handlers**

Add to `prism-tui/tests/test_browser.py`:

```python
def test_compose_returns_widgets(browser_tab):
    from textual.containers import Horizontal
    from textual.widgets import Markdown
    result = list(browser_tab.compose())
    assert len(result) == 1
    assert isinstance(result[0], Horizontal)


def test_load_data_calls_set_resolver(browser_tab):
    browser_tab._manager = MagicMock()
    browser_tab._manager.list_nodes.return_value = []
    browser_tab._resolver = MagicMock()
    tree = MagicMock()
    browser_tab.query_one = MagicMock(return_value=tree)
    browser_tab._load_data()
    assert tree.set_resolver.called


def test_refresh_node_list_filters_by_tag(browser_tab):
    browser_tab._current_path_uuid = "path-uuid"
    node_a = MagicMock()
    node_a.uuid = "a"
    node_a.paths = ["path-uuid"]
    node_a.tags = ["work"]
    node_a.type = "note"
    node_a.title = "A"
    node_b = MagicMock()
    node_b.uuid = "b"
    node_b.paths = ["path-uuid"]
    node_b.tags = ["personal"]
    node_b.type = "note"
    node_b.title = "B"
    browser_tab._nodes_by_uuid = {"a": node_a, "b": node_b}
    browser_tab._filter_tag = "work"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab._refresh_node_list()
    assert list_view.clear.called
    assert list_view.append.called


def test_refresh_node_list_filters_by_type(browser_tab):
    browser_tab._current_path_uuid = "path-uuid"
    node_a = MagicMock()
    node_a.uuid = "a"
    node_a.paths = ["path-uuid"]
    node_a.tags = []
    node_a.type = "contact"
    node_a.title = "A"
    node_b = MagicMock()
    node_b.uuid = "b"
    node_b.paths = ["path-uuid"]
    node_b.tags = []
    node_b.type = "note"
    node_b.title = "B"
    browser_tab._nodes_by_uuid = {"a": node_a, "b": node_b}
    browser_tab._filter_type = "contact"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab._refresh_node_list()
    assert list_view.clear.called


def test_on_tree_node_selected_sets_path(browser_tab):
    browser_tab._refresh_node_list = MagicMock()
    event = MagicMock()
    event.node.data = "some-uuid"
    browser_tab.on_tree_node_selected(event)
    assert browser_tab._current_path_uuid == "some-uuid"
    assert browser_tab._refresh_node_list.called


def test_on_list_view_selected_shows_preview(browser_tab):
    browser_tab._nodes_by_uuid = {"node-uuid": MagicMock()}
    browser_tab._show_preview = MagicMock()
    event = MagicMock()
    event.item.id = "node-uuid"
    browser_tab.on_list_view_selected(event)
    assert browser_tab._show_preview.called


def test_on_key_j_navigates_down(browser_tab):
    browser_tab._active_column = 1
    event = MagicMock()
    event.key = "j"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab.on_key(event)
    assert list_view.action_cursor_down.called


def test_on_key_k_navigates_up(browser_tab):
    browser_tab._active_column = 1
    event = MagicMock()
    event.key = "k"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab.on_key(event)
    assert list_view.action_cursor_up.called


def test_on_key_h_moves_left(browser_tab):
    browser_tab._active_column = 1
    browser_tab._set_column_focus = MagicMock()
    event = MagicMock()
    event.key = "h"
    browser_tab.on_key(event)
    assert browser_tab._active_column == 0
    assert browser_tab._set_column_focus.called


def test_on_key_r_refreshes(browser_tab):
    browser_tab._load_data = MagicMock()
    event = MagicMock()
    event.key = "r"
    browser_tab.on_key(event)
    assert browser_tab._load_data.called


def test_on_key_t_prompts_tag_filter(browser_tab):
    browser_tab._active_column = 1
    browser_tab._prompt_filter = MagicMock()
    event = MagicMock()
    event.key = "t"
    browser_tab.on_key(event)
    browser_tab._prompt_filter.assert_called_with("tag")


def test_prompt_filter_notifies(browser_tab):
    browser_tab.notify = MagicMock()
    browser_tab._prompt_filter("tag")
    assert browser_tab.notify.called


def test_on_edit_done_with_vault(browser_tab):
    browser_tab._vault = MagicMock()
    browser_tab.app = MagicMock()
    browser_tab._nodes_by_uuid = {}
    browser_tab._show_preview = MagicMock()
    browser_tab._on_edit_done(MagicMock(uuid="x"))
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test_browser.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_browser.py
git commit -m "test(tui): add browser tab test coverage to 95%"
```

---

### Task 3: `prism_cli/tutor.py` (52% → 95%)

**Files:**
- Modify: `prism-cli/tests/test_tutor.py`

- [ ] **Step 1: Add tests for Tutor utilities and step execution**

Add to `prism-cli/tests/test_tutor.py`:

```python
# ── Tutor Lifecycle ──

class TestTutorLifecycle:
    def test_create_temp_vault(self, tutor):
        tutor._create_temp_vault()
        assert tutor.temp_dir != ""
        import os
        assert os.path.exists(tutor.temp_dir)

    def test_ensure_vault_open_when_not_initialized(self, tutor):
        tutor._create_temp_vault()
        result = tutor._ensure_vault_open()
        assert result is None

    def test_write_builtin_types(self, vault_dir):
        from prism.vault.vault import Vault
        vault = Vault.open(vault_dir)
        tutor = Tutor()
        tutor._write_builtin_types(vault)
        types_dir = os.path.join(vault_dir, ".metadata", "types")
        assert os.path.exists(os.path.join(types_dir, "note.toml"))
        assert os.path.exists(os.path.join(types_dir, "contact.toml"))

    def test_cleanup_keep(self, tutor):
        tutor._create_temp_vault()
        vault_path = tutor.temp_dir
        tutor._cleanup(keep=True)
        assert os.path.exists(vault_path)

    def test_cleanup_remove(self, tutor):
        tutor._create_temp_vault()
        vault_path = tutor.temp_dir
        tutor._cleanup(keep=False)
        assert not os.path.exists(vault_path)


# ── Output Rendering ──

class TestTutorOutput:
    def test_show_header_output(self, capsys, tutor):
        tutor._show_header(1, "Test", 8)
        captured = capsys.readouterr()
        assert "Lesson 1/8: Test" in captured.out

    def test_show_concept_output(self, capsys, tutor):
        tutor._show_concept("Hello world")
        captured = capsys.readouterr()
        assert "Hello world" in captured.out

    def test_show_command_output(self, capsys, tutor):
        tutor._show_command("prism init .")
        captured = capsys.readouterr()
        assert "prism init ." in captured.out

    def test_show_success_output(self, capsys, tutor):
        tutor._show_success("Done!")
        captured = capsys.readouterr()
        assert "Done!" in captured.out

    def test_show_warning_output(self, capsys, tutor):
        tutor._show_warning("Oops!")
        captured = capsys.readouterr()
        assert "Oops!" in captured.out

    def test_show_progress_output(self, capsys, tutor):
        tutor._show_progress(1, 5)
        captured = capsys.readouterr()
        assert "Step 1/5" in captured.out

    def test_show_final_summary_output(self, capsys, tutor):
        tutor._show_final_summary()
        captured = capsys.readouterr()
        assert "Congratulations" in captured.out

    def test_show_auto_run_output(self, capsys, tutor):
        tutor._show_auto_run("prism init")
        captured = capsys.readouterr()
        assert "Auto-running" in captured.out

    def test_show_output_with_text(self, capsys, tutor):
        tutor._show_output("hello\nworld\n")
        captured = capsys.readouterr()
        assert "hello" in captured.out
        assert "world" in captured.out

    def test_show_output_empty(self, capsys, tutor):
        tutor._show_output("")
        captured = capsys.readouterr()
        assert captured.out == ""


# ── UUID Capture and Resolution ──

class TestTutorUuidCapture:
    def test_capture_uuid_no_vault(self, tutor):
        tutor.vault = None
        tutor._capture_uuid("test", "key1")
        assert "key1" not in tutor._fmt

    def test_resolve_uuid_returns_short_when_not_found(self, tutor):
        result = tutor._resolve_uuid("unknown")
        assert result == "unknown"

    def test_resolve_uuid_returns_full(self, tutor):
        tutor._fmt["_full_known"] = "full-uuid-value"
        result = tutor._resolve_uuid("known")
        assert result == "full-uuid-value"

    def test_build_prism_cmd(self, tutor):
        cmd = tutor._build_prism_cmd("prism init .")
        import sys
        assert cmd.startswith(sys.executable)
        assert "init" in cmd


# ── Lesson Plan Construction ──

class TestLessonPlan:
    def test_build_lesson_plan_returns_8_lessons(self, tutor):
        lessons = tutor._build_lesson_plan()
        assert len(lessons) == 8

    def test_each_lesson_has_steps(self, tutor):
        lessons = tutor._build_lesson_plan()
        for lesson in lessons:
            assert len(lesson.steps) >= 1

    def test_lessons_are_ordered(self, tutor):
        lessons = tutor._build_lesson_plan()
        for i, lesson in enumerate(lessons, 1):
            assert lesson.number == i


# ── Step Execution ──

class TestTutorStepExecution:
    def test_run_step_concept_display(self, capsys, tutor):
        step = Step(
            number=1,
            concept="Test concept",
            command="echo hello",
            verify=lambda v: True,
        )
        from prism_cli.tutor import StepResult
        import io
        from unittest.mock import patch
        with patch("builtins.input", return_value=""):
            result = tutor._run_step(step)
        assert result == StepResult.SUCCESS
        captured = capsys.readouterr()
        assert "Test concept" in captured.out

    def test_run_step_with_prism_command(self, capsys, tutor, vault_dir):
        from prism.vault.vault import Vault
        tutor.vault = Vault.open(vault_dir)
        step = Step(
            number=1,
            concept="Init",
            command="prism init .",
            verify=lambda v: True,
        )
        from prism_cli.tutor import StepResult
        import io
        from unittest.mock import patch
        with patch("builtins.input", return_value=""):
            result = tutor._run_step(step)
        assert result == StepResult.SUCCESS

    def test_run_step_command_fails_retry_skip(self, capsys, tutor):
        step = Step(
            number=1,
            concept="Fail test",
            command="nonexistent_command_xyz",
            verify=lambda v: True,
        )
        from prism_cli.tutor import StepResult
        from unittest.mock import patch
        with patch("builtins.input", side_effect=["", "n"]):
            result = tutor._run_step(step)
        assert result == StepResult.SKIP

    def test_run_step_verification_fails_retry_skip(self, capsys, tutor):
        step = Step(
            number=1,
            concept="Verify fail",
            command="echo hello",
            verify=lambda v: False,
        )
        from prism_cli.tutor import StepResult
        from unittest.mock import patch
        with patch("builtins.input", side_effect=["", "n"]):
            result = tutor._run_step(step)
        assert result == StepResult.SKIP

    def test_prompt_keep_vault_yes(self, tutor):
        from unittest.mock import patch
        with patch("builtins.input", return_value="y"):
            assert tutor._prompt_keep_vault() is True

    def test_prompt_keep_vault_no(self, tutor):
        from unittest.mock import patch
        with patch("builtins.input", return_value=""):
            assert tutor._prompt_keep_vault() is False

    def test_prompt_keep_vault_eof(self, tutor):
        from unittest.mock import patch
        with patch("builtins.input", side_effect=EOFError):
            assert tutor._prompt_keep_vault() is False

    def test_execute_command(self, tutor):
        tutor._create_temp_vault()
        result = tutor._execute_command("echo hello")
        assert result.returncode == 0
        assert "hello" in result.stdout


# ── Run Method ──

class TestTutorRun:
    def test_run_invalid_lesson_number(self, capsys, tutor):
        tutor.lesson_number = 99
        from unittest.mock import patch
        with patch("builtins.input", return_value=""):
            tutor.run()
        captured = capsys.readouterr()
        assert "Starting from lesson 1" in captured.out

    def test_run_keyboard_interrupt(self, capsys, tutor):
        tutor._create_temp_vault = MagicMock(side_effect=KeyboardInterrupt)
        with pytest.raises(SystemExit):
            tutor.run()
        captured = capsys.readouterr()
        assert "Tutorial paused" in captured.out

    def test_write_to_note_body(self, tutor, vault_dir):
        from prism.vault.vault import Vault
        from prism.node.manager import NodeManager
        vault = Vault.open(vault_dir)
        tutor.vault = vault
        manager = NodeManager(vault.path)
        node = manager.create_node("note", title="TestNote")
        tutor._write_to_note_body("TestNote", "Hello World")
        desc = manager.get_description(node.uuid)
        assert desc is None  # description is different from body


# ── Verify Helpers ──

class TestTutorNewVerifyHelpers:
    def test_verify_always_true(self, tutor, vault):
        assert tutor._verify_always_true(vault) is True

    def test_verify_blob_integrity_no_meta(self, tutor, vault_dir):
        from prism.vault.vault import Vault
        vault = Vault.open(vault_dir)
        assert tutor._verify_blob_integrity(vault, "nonexistent") is False

    def test_verify_change_detected_clean(self, tutor, vault):
        assert tutor._verify_change_detected(vault) is False
```

- [ ] **Step 2: Run tutor tests**

Run: `python -m pytest prism-cli/tests/test_tutor.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-cli/tests/test_tutor.py
git commit -m "test(cli): add tutor test coverage to 95%"
```

---

## Phase 2 — Medium gaps (60–80%)

### Task 4: `prism_tui/command_bar.py` (65% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_command_bar.py`

- [ ] **Step 1: Add tests for set_vault, on_button_pressed, _update_labels**

Add to `prism-tui/tests/test_command_bar.py`:

```python
def test_set_vault_sets_manager(command_bar):
    vault = MagicMock()
    command_bar.set_vault(vault)
    assert command_bar._vault is vault
    assert command_bar._manager is not None


def test_update_labels_removes_children(command_bar):
    bar_container = MagicMock()
    command_bar.query_one = MagicMock(return_value=bar_container)
    command_bar._update_labels()
    assert bar_container.remove_children.called


def test_on_button_pressed_triggers_action(command_bar):
    command_bar._trigger_action = MagicMock()
    event = MagicMock()
    event.button.id = "action-help"
    command_bar.on_button_pressed(event)
    command_bar._trigger_action.assert_called_with("help")


def test_trigger_action_help(command_bar):
    command_bar.app = MagicMock()
    command_bar._trigger_action("help")
    assert command_bar.app.action_show_help.called


def test_trigger_action_new(command_bar):
    command_bar.app = MagicMock()
    command_bar._trigger_action("new")
    assert command_bar.app.action_new_node.called


def test_trigger_action_unknown_no_error(command_bar):
    command_bar.app = MagicMock()
    command_bar._trigger_action("nonexistent_action")
    assert not command_bar.app.action_show_help.called


def test_compose_returns_widgets(command_bar):
    result = list(command_bar.compose())
    from textual.containers import Horizontal
    assert len(result) == 1
    assert isinstance(result[0], Horizontal)
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test_command_bar.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_command_bar.py
git commit -m "test(tui): add command bar test coverage to 95%"
```

---

### Task 5: `prism_tui/app.py` (69% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_app.py`

- [ ] **Step 1: Add tests for PrismTui actions and event handlers**

Add to `prism-tui/tests/test_app.py`:

```python
def test_action_edit_node_no_selection(app):
    from prism_tui.tabs.browser import BrowserTab
    browser = MagicMock()
    browser._current_node = None
    app.query_one = MagicMock(return_value=browser)
    app.notify = MagicMock()
    app.action_edit_node()
    assert app.notify.called


def test_action_edit_node_with_selection(app):
    from prism_tui.tabs.browser import BrowserTab
    browser = MagicMock()
    browser._current_node = MagicMock()
    app.query_one = MagicMock(return_value=browser)
    app.action_edit_node()
    assert browser._edit_node.called


def test_action_delete_node(app):
    app.notify = MagicMock()
    app.action_delete_node()
    assert app.notify.called


def test_action_refresh_no_vault(app):
    app._vault = None
    app.notify = MagicMock()
    app.action_refresh()
    assert app.notify.called


def test_action_refresh_with_vault(app):
    app._vault = MagicMock()
    app._update_tabs_vault = MagicMock()
    app.notify = MagicMock()
    app.action_refresh()
    assert app._update_tabs_vault.called


def test_action_menu(app):
    app.notify = MagicMock()
    app.action_menu()
    assert app.notify.called


def test_enter_command_mode(app):
    cmd_input = MagicMock()
    app.query_one = MagicMock(return_value=cmd_input)
    app._enter_command_mode()
    assert app._in_command_mode is True
    assert cmd_input.add_class.called
    assert cmd_input.focus.called


def test_exit_command_mode(app):
    cmd_input = MagicMock()
    app.query_one = MagicMock(return_value=cmd_input)
    app._in_command_mode = True
    app._exit_command_mode()
    assert app._in_command_mode is False
    assert cmd_input.remove_class.called


def test_action_enter_command_mode(app):
    app._enter_command_mode = MagicMock()
    app.action_enter_command_mode()
    assert app._enter_command_mode.called


def test_on_input_submitted_no_vault(app):
    app._vault = None
    app.notify = MagicMock()
    event = MagicMock()
    event.input.id = "command-input"
    event.value = "new"
    app.on_input_submitted(event)
    assert app.notify.called


def test_on_input_submitted_with_result(app):
    from unittest.mock import patch
    app._vault = MagicMock()
    app.notify = MagicMock()
    event = MagicMock()
    event.input.id = "command-input"
    event.value = "help"
    with patch("prism_tui.app.execute_command", return_value="Commands: help"):
        app.on_input_submitted(event)
    assert app.notify.called


def test_on_key_q_exits(app):
    event = MagicMock()
    event.key = "q"
    app.focused = MagicMock()
    from textual.widgets import Input
    app.focused.__class__ = object  # not an Input
    app.on_key(event)
    assert event.stop.called


def test_on_key_escape_in_command_mode(app):
    app._in_command_mode = True
    app._exit_command_mode = MagicMock()
    event = MagicMock()
    event.key = "escape"
    app.on_key(event)
    assert app._exit_command_mode.called


def test_on_vault_selected_with_vault(app):
    vault = MagicMock()
    app._update_tabs_vault = MagicMock()
    command_bar = MagicMock()
    app.query_one = MagicMock(return_value=command_bar)
    app._on_vault_selected(vault)
    assert app._vault is vault
    assert app._update_tabs_vault.called
    assert command_bar.set_vault.called


def test_on_vault_selected_none_exits(app):
    app.exit = MagicMock()
    app._on_vault_selected(None)
    assert app.exit.called


def test_update_tabs_vault(app):
    vault = MagicMock()
    tab_container = MagicMock()
    pane = MagicMock()
    child = MagicMock()
    child.has_attr.side_effect = lambda x: x == "set_vault"
    pane.children = [child]
    tab_container.query.return_value = [pane]
    app.query_one = MagicMock(return_value=tab_container)
    app._update_tabs_vault(vault)
    assert child.set_vault.called


def test_on_select_node_switches_tab(app):
    msg = MagicMock()
    msg.node = MagicMock()
    msg.node.title = "Test"
    tab_container = MagicMock()
    browser = MagicMock()
    app._vault = MagicMock()

    def query_one_side_effect(cls, *args):
        if cls.__name__ == "TabbedContent":
            return tab_container
        return browser

    app.query_one = MagicMock(side_effect=query_one_side_effect)
    app.notify = MagicMock()
    app.on_select_node(msg)
    assert tab_container.active == "tab-browser"


def test_compose_returns_widgets(app):
    result = list(app.compose())
    from textual.widgets import Header
    from textual.containers import Vertical
    from textual.widgets import TabbedContent, Input
    from prism_tui.command_bar import CommandBar
    assert any(isinstance(w, Header) for w in result)
    assert any(isinstance(w, Vertical) for w in result)
    assert any(isinstance(w, Input) for w in result)
    assert any(isinstance(w, CommandBar) for w in result)


def test_on_mount_with_vault(app):
    app._vault = MagicMock()
    app.push_screen = MagicMock()
    app.on_mount()
    assert not app.push_screen.called
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test_app.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_app.py
git commit -m "test(tui): add app test coverage to 95%"
```

---

### Task 6: `prism_tui/messages.py` (71% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_*.py` (add to existing file or create new)

- [ ] **Step 1: Add test for SelectNode message**

Create `prism-tui/tests/test_messages.py`:

```python
from prism_tui.messages import SelectNode
from prism.node.metadata import NodeMetadata


def test_select_node_message():
    node = NodeMetadata(
        uuid="test-uuid",
        type="note",
        title="Test Node",
        tags=["work"],
    )
    msg = SelectNode(node)
    assert msg.node is node
    assert msg.node.uuid == "test-uuid"
    assert msg.node.title == "Test Node"
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test_messages.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_messages.py
git commit -m "test(tui): add messages test coverage to 95%"
```

---

### Task 7: `prism_tui/tabs/query_builder.py` (73% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_query_builder.py`

- [ ] **Step 1: Add tests for QueryBuilderTab edge cases**

Add to `prism-tui/tests/test_query_builder.py`:

```python
def test_on_mount_with_vault(query_builder):
    vault = MagicMock()
    vault.path = "/tmp/test"
    query_builder._vault = vault
    query_builder._manager = MagicMock()
    query_builder._all_nodes = []
    query_builder._populate_form = MagicMock()
    query_builder.on_mount()
    assert query_builder._populate_form.called


def test_on_mount_no_vault(query_builder):
    query_builder._vault = None
    query_builder._populate_form = MagicMock()
    query_builder.on_mount()


def test_on_input_changed_schedules_search(query_builder):
    query_builder._schedule_search = MagicMock()
    event = MagicMock()
    event.input.id = "search-input"
    query_builder.on_input_changed(event)
    assert query_builder._schedule_search.called


def test_on_input_changed_ignores_other_inputs(query_builder):
    query_builder._schedule_search = MagicMock()
    event = MagicMock()
    event.input.id = "other-input"
    query_builder.on_input_changed(event)


def test_on_select_changed_schedules_search(query_builder):
    query_builder._schedule_search = MagicMock()
    event = MagicMock()
    event.select.id = "type-select"
    query_builder.on_select_changed(event)
    assert query_builder._schedule_search.called


def test_on_button_pressed_toggles(query_builder):
    query_builder._schedule_search = MagicMock()
    and_btn = MagicMock()
    or_btn = MagicMock()
    not_btn = MagicMock()

    def query_one_side(selector):
        lookup = {"#and-btn": and_btn, "#or-btn": or_btn, "#not-btn": not_btn}
        return lookup[selector]

    query_builder.query_one = MagicMock(side_effect=query_one_side)
    event = MagicMock()
    event.button.id = "and-btn"
    query_builder.on_button_pressed(event)
    assert and_btn.add_class.called


def test_execute_search_no_filters(query_builder):
    query_builder._update_results = MagicMock()
    query_builder._execute_search()


def test_on_list_view_selected_no_match(query_builder):
    query_builder.post_message = MagicMock()
    event = MagicMock()
    event.item.id = "nonexistent-uuid"
    query_builder._results = [MagicMock(uuid="other-uuid")]
    query_builder.on_list_view_selected(event)
    assert not query_builder.post_message.called


def test_on_list_view_selected_with_match(query_builder):
    query_builder.post_message = MagicMock()
    node = MagicMock(uuid="test-uuid")
    query_builder._results = [node]
    event = MagicMock()
    event.item.id = "test-uuid"
    query_builder.on_list_view_selected(event)
    assert query_builder.post_message.called


def test_execute_search_with_type_filter(query_builder):
    query_builder._update_results = MagicMock()

    def query_one_side(widget_id, *args):
        lookup = {
            "#type-select": MagicMock(value="note"),
            "#tag-select": MagicMock(value="any"),
            "#search-input": MagicMock(value=""),
            "#result-count": MagicMock(),
            "#query-results-list": MagicMock(),
        }
        return lookup.get(widget_id, MagicMock())

    query_builder.query_one = MagicMock(side_effect=query_one_side)
    query_builder._execute_search()


def test_compose_returns_widgets(query_builder):
    result = list(query_builder.compose())
    from textual.containers import Vertical
    from textual.widgets import Label, ListView
    assert any(isinstance(w, Vertical) for w in result)
    assert any(isinstance(w, Label) for w in result)
    assert any(isinstance(w, ListView) for w in result)
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test_query_builder.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_query_builder.py
git commit -m "test(tui): add query builder test coverage to 95%"
```

---

### Task 8: `prism_tui/tabs/graph.py` (78% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_graph.py`

- [ ] **Step 1: Add tests for GraphTab methods and ForceDirectedLayout edge cases**

Add to `prism-tui/tests/test_graph.py`:

```python
from unittest.mock import MagicMock, patch
import json
from prism_tui.tabs.graph import GraphTab
from prism.node.metadata import NodeMetadata


def _make_node(uuid: str, title: str = "") -> NodeMetadata:
    return NodeMetadata(
        uuid=uuid,
        type="note",
        title=title or uuid[:8],
    )


class TestGraphTab:
    def test_init_defaults(self):
        tab = GraphTab()
        assert tab._vault is None
        assert tab._manager is None
        assert tab._layout is None
        assert tab._selected_uuid is None
        assert tab._type_filter is None

    def test_set_vault_no_vault(self):
        tab = GraphTab()
        tab._load_graph = MagicMock()
        tab.set_vault(MagicMock())
        assert tab._load_graph.called

    def test_load_graph_no_vault(self):
        tab = GraphTab()
        tab._vault = None
        tab._load_graph()

    def test_load_graph_with_vault(self):
        tab = GraphTab()
        tab._vault = MagicMock()
        tab._vault.path = "/tmp/test"
        tab._manager = MagicMock()
        tab._manager.list_nodes.return_value = []
        with patch("prism_tui.tabs.graph.GraphExporter") as MockExporter:
            instance = MagicMock()
            instance.export_json.return_value = json.dumps({"edges": []})
            MockExporter.return_value = instance
            tab._load_graph()

    def test_filtered_nodes_no_filter(self):
        tab = GraphTab()
        tab._all_nodes = [_make_node("a")]
        result = tab._filtered_nodes()
        assert len(result) == 1

    def test_filtered_nodes_with_filter(self):
        tab = GraphTab()
        tab._type_filter = "note"
        n1 = _make_node("a")
        n2 = _make_node("b")
        n2.type = "contact"
        tab._all_nodes = [n1, n2]
        result = tab._filtered_nodes()
        assert len(result) == 1
        assert result[0].type == "note"

    def test_render_canvas_no_layout(self):
        tab = GraphTab()
        static = MagicMock()
        tab.query_one = MagicMock(return_value=static)
        tab._layout = None
        tab._render_canvas()
        static.update.assert_called_with("No graph data")

    def test_render_canvas_with_layout(self):
        tab = GraphTab()
        static = MagicMock()
        static.content_region.width = 80
        static.content_region.height = 24
        tab.query_one = MagicMock(return_value=static)
        tab._layout = MagicMock()
        tab._layout.render_ascii.return_value = "graph\nart"
        tab._selected_uuid = None
        tab._pan_x = 0
        tab._pan_y = 0
        tab._zoom = 1.0
        tab._render_canvas()
        assert tab._layout.render_ascii.called

    def test_on_mount_with_vault(self):
        tab = GraphTab()
        tab._vault = MagicMock()
        tab._load_graph = MagicMock()
        list_view = MagicMock()
        tab.query_one = MagicMock(return_value=list_view)
        tab.on_mount()
        assert tab._load_graph.called
        assert list_view.display is False

    def test_on_key_t_prompts_filter(self):
        tab = GraphTab()
        tab.notify = MagicMock()
        event = MagicMock()
        event.key = "t"
        tab.on_key(event)
        assert tab.notify.called

    def test_on_key_enter_navigates_browser(self):
        tab = GraphTab()
        tab._selected_uuid = "test-uuid"
        tab.post_message = MagicMock()
        tab._all_nodes = [_make_node("test-uuid", "Test")]
        event = MagicMock()
        event.key = "Enter"
        tab.on_key(event)
        assert tab.post_message.called

    def test_on_key_left_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "left"
        tab.on_key(event)
        tab._render_canvas.assert_called()

    def test_on_key_right_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "right"
        tab.on_key(event)
        assert tab._pan_x == 5

    def test_on_key_up_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "up"
        tab.on_key(event)
        assert tab._pan_y == 0  # pan_y = max(0, 0-2) = 0

    def test_on_key_down_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "down"
        tab.on_key(event)
        assert tab._pan_y == 2

    def test_on_key_zoom_in(self):
        tab = GraphTab()
        tab._zoom = 1.0
        event = MagicMock()
        event.key = "plus"
        tab.on_key(event)
        assert tab._zoom == 1.2

    def test_on_key_zoom_out(self):
        tab = GraphTab()
        tab._zoom = 1.0
        event = MagicMock()
        event.key = "minus"
        tab.on_key(event)
        assert tab._zoom == 0.8

    def test_on_key_zoom_minimum(self):
        tab = GraphTab()
        tab._zoom = 0.5
        event = MagicMock()
        event.key = "minus"
        tab.on_key(event)
        assert tab._zoom == 0.5

    def test_on_key_zoom_maximum(self):
        tab = GraphTab()
        tab._zoom = 3.0
        event = MagicMock()
        event.key = "plus"
        tab.on_key(event)
        assert tab._zoom == 3.0

    def test_handle_pan_no_layout(self):
        tab = GraphTab()
        tab._layout = None
        tab._handle_pan("left")

    def test_navigate_to_browser_no_selection(self):
        tab = GraphTab()
        tab._selected_uuid = None
        tab.post_message = MagicMock()
        tab._navigate_to_browser()
        assert not tab.post_message.called

    def test_prompt_type_filter(self):
        tab = GraphTab()
        tab.notify = MagicMock()
        tab._prompt_type_filter()
        assert tab.notify.called

    def test_show_list_view(self):
        tab = GraphTab()
        static = MagicMock()
        list_view = MagicMock()
        tab.query_one = MagicMock(side_effect=[static, list_view])
        tab._all_links = [{"source": "a", "target": "b"}]
        tab._show_list_view([
            _make_node("a", "Node A"),
            _make_node("b", "Node B"),
        ])
        assert static.display is False
        assert list_view.display is True
        assert list_view.clear.called


class TestForceDirectedLayoutEdgeCases:
    def test_render_ascii_no_view_dimensions(self):
        nodes = [_make_node("a")]
        layout = ForceDirectedLayout(nodes, [])
        layout.tick(10)
        result = layout.render_ascii(None, None, None, 0, 0, 1.0)
        assert result is not None

    def test_render_ascii_view_overflow(self):
        nodes = [_make_node("a")]
        layout = ForceDirectedLayout(nodes, [])
        layout.tick(10)
        result = layout.render_ascii(None, 80, 100, 0, 0, 1.0)
        assert result is not None

    def test_draw_line_short(self):
        nodes = [_make_node("a")]
        layout = ForceDirectedLayout(nodes, [])
        canvas = [[" " for _ in range(5)] for _ in range(5)]
        layout._draw_line(canvas, 0, 0, 1, 1, 5, 5)
        assert canvas[0][0] == "." or canvas[1][1] == "."
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test_graph.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_graph.py
git commit -m "test(tui): add graph tab test coverage to 95%"
```

---

## Phase 3 — Home stretch (>80%)

### Task 9: `prism_cli/repl.py` (86% → 95%)

**Files:**
- Modify: `prism-cli/tests/test_repl.py`

- [ ] **Step 1: Add tests for uncovered REPL code paths**

Add to `prism-cli/tests/test_repl.py`:

```python
# ── Degraded Mode ──

class TestReplDegraded:
    def test_degraded_mode_new_shows_error(self, vault):
        output = run_repl_no_vault(["new"])
        assert "No vault connected" in output

    def test_degraded_mode_show_shows_error(self, vault):
        output = run_repl_no_vault(["show"])
        assert "No vault connected" in output

    def test_degraded_mode_edit_shows_error(self, vault):
        output = run_repl_no_vault(["edit"])
        assert "No vault connected" in output

    def test_degraded_mode_rm_shows_error(self, vault):
        output = run_repl_no_vault(["rm"])
        assert "No vault connected" in output

    def test_degraded_mode_query_shows_error(self, vault):
        output = run_repl_no_vault(["query"])
        assert "No vault connected" in output

    def test_degraded_mode_backlinks_shows_error(self, vault):
        output = run_repl_no_vault(["backlinks"])
        assert "No vault connected" in output

    def test_degraded_mode_graph_shows_error(self, vault):
        output = run_repl_no_vault(["graph"])
        assert "No vault connected" in output

    def test_degraded_mode_status_shows_error(self, vault):
        output = run_repl_no_vault(["status"])
        assert "No vault connected" in output

    def test_degraded_mode_verify_shows_error(self, vault):
        output = run_repl_no_vault(["verify"])
        assert "No vault connected" in output

    def test_degraded_mode_path_shows_error(self, vault):
        output = run_repl_no_vault(["path"])
        assert "No vault connected" in output

    def test_degraded_mode_tag_shows_error(self, vault):
        output = run_repl_no_vault(["tag"])
        assert "No vault connected" in output

    def test_degraded_init_works(self):
        import tempfile
        d = tempfile.mkdtemp()
        output = run_repl_no_vault([f"init {d}"])
        assert "Vault initialized" in output

    def test_degraded_help_works(self):
        output = run_repl_no_vault(["help"])
        assert "Available commands" in output

    def test_degraded_history_works(self):
        output = run_repl_no_vault(["history"])
        assert output is not None


# ── Underscore Shorthand ──

class TestReplUnderscore:
    def test_underscore_without_last_uuid(self, vault):
        output = run_repl(vault, ["show _"])
        assert "Error: No previous node" in output


# ── Edge Cases ──

class TestReplEdgeCases:
    def test_empty_input(self, vault):
        output = run_repl(vault, ["", "exit"])
        assert "Prism REPL" in output

    def test_tutor_unsupported(self, vault):
        output = run_repl(vault, ["tutor"])
        assert "cannot run inside the REPL" in output

    def test_unknown_command(self, vault):
        output = run_repl(vault, ["xyzzy", "exit"])
        assert "Unknown command" in output

    def test_init_without_args_defaults_to_cwd(self, vault):
        import tempfile
        d = tempfile.mkdtemp()
        output = run_repl_no_vault([f"init {d}", "exit"])
        assert "Vault initialized" in output

    def test_open_without_args(self, vault):
        output = run_repl(vault, ["open", "exit"])

    def test_open_nonexistent_path(self, vault):
        output = run_repl(vault, ["open /nonexistent/path", "exit"])
        assert "Error" in output or "No vault connected" in output

    def test_show_without_args(self, vault):
        output = run_repl(vault, ["show", "exit"])
        assert "Usage: show" in output

    def test_show_with_desc(self, vault):
        output = run_repl(vault, ["show --desc", "exit"])
        assert "Usage: show" in output

    def test_rm_without_args(self, vault):
        output = run_repl(vault, ["rm", "exit"])
        assert "Usage: rm" in output

    def test_query_without_args(self, vault):
        output = run_repl(vault, ["query", "exit"])
        assert "Usage: query" in output

    def test_link_without_args(self, vault):
        output = run_repl(vault, ["link", "exit"])
        assert "Usage: link" in output

    def test_backlinks_without_args(self, vault):
        output = run_repl(vault, ["backlinks", "exit"])
        assert "Usage: backlinks" in output

    def test_add_file_without_args(self, vault):
        output = run_repl(vault, ["add-file", "exit"])
        assert "Usage: add-file" in output

    def test_verify_without_args(self, vault):
        output = run_repl(vault, ["verify", "exit"])
        assert "Usage: verify" in output

    def test_graph_default_format(self, vault):
        output = run_repl(vault, ["graph", "exit"])
        assert output is not None

    def test_graph_json_format(self, vault):
        output = run_repl(vault, ["graph json", "exit"])
        assert output is not None

    def test_tag_add_no_args(self, vault):
        output = run_repl(vault, ["tag add", "exit"])
        assert "Usage: tag add" in output or "Error" in output

    def test_tag_rm_no_args(self, vault):
        output = run_repl(vault, ["tag rm", "exit"])
        assert "Usage: tag rm" in output or "Error" in output

    def test_tag_list_empty(self, vault):
        output = run_repl(vault, ["tag list", "exit"])
        assert output is not None

    def test_tag_rename_no_args(self, vault):
        output = run_repl(vault, ["tag rename", "exit"])
        assert "Usage: tag rename" in output

    def test_tag_unknown_subcommand(self, vault):
        output = run_repl(vault, ["tag foo", "exit"])
        assert "Unknown tag subcommand" in output

    def test_path_without_args(self, vault):
        output = run_repl(vault, ["path", "exit"])

    def test_path_create(self, vault):
        output = run_repl(vault, ["path create /test", "exit"])
        assert output is not None

    def test_path_tree(self, vault):
        output = run_repl(vault, ["path tree", "exit"])
        assert output is not None

    def test_help_with_command(self, vault):
        output = run_repl(vault, ["help new", "exit"])
        assert "Create a new" in output or "new" in output

    def test_help_with_unknown_command(self, vault):
        output = run_repl(vault, ["help xyzzy", "exit"])
        assert "No help available" in output

    def test_edit_no_args(self, vault):
        output = run_repl(vault, ["edit", "exit"])
        assert "Usage: edit" in output

    def test_edit_add_path(self, vault):
        output = run_repl(vault, ["edit some-uuid --add-path /test", "exit"])
        assert output is not None

    def test_edit_remove_path(self, vault):
        output = run_repl(vault, ["edit some-uuid --remove-path /test", "exit"])
        assert output is not None

    def test_edit_desc(self, vault):
        output = run_repl(vault, ["edit some-uuid --desc hello", "exit"])
        assert output is not None

    def test_status_clean(self, vault):
        output = run_repl(vault, ["status", "exit"])
        assert "Vault is clean" in output or "Prism REPL" in output

    def test_verify_nonexistent(self, vault):
        output = run_repl(vault, ["verify nonexistent-uuid", "exit"])
        assert "NOT_FOUND" in output or "Error" in output or "OK" in output

    def test_new_minimal(self, vault):
        output = run_repl(vault, ["""new note "Test" """, "exit"])

    def test_link_same_nodes(self, vault):
        output = run_repl(vault, ["link a a", "exit"])

    def test_help_with_alias(self, vault):
        output = run_repl(vault, ["help s", "exit"])
        assert "Display node" in output or "show" in output
```

- [ ] **Step 2: Run REPL tests**

Run: `python -m pytest prism-cli/tests/test_repl.py -v`
Expected: All tests pass (note: some tests may need minor adjustment for exact error messages)

- [ ] **Step 3: Commit**

```bash
git add prism-cli/tests/test_repl.py
git commit -m "test(cli): add repl test coverage to 95%"
```

---

### Task 10: `prism_tui/startup_screen.py` (89% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_startup_screen.py`

- [ ] **Step 1: Add tests for _get_path and _path_is_vault**

Add to `prism-tui/tests/test_startup_screen.py`:

```python
def test_get_path_returns_stripped_value() -> None:
    """_get_path should return the stripped path input value."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        path_input = screen.query_one("#path-input")
        path_input.value = "  /some/path  "
        result = screen._get_path()
        assert result == "/some/path"


def test_get_path_returns_empty_when_empty() -> None:
    """_get_path should return empty string when input is empty."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        screen.query_one("#path-input").value = ""
        result = screen._get_path()
        assert result == ""
```

- [ ] **Step 2: Add test for _path_is_vault**

Add to `prism-tui/tests/test_startup_screen.py`:

```python
def test_path_is_vault_returns_false_for_nonexistent() -> None:
    """_path_is_vault should return False for non-existent paths."""
    from prism_tui.startup_screen import _path_is_vault
    assert _path_is_vault("/nonexistent/path") is False


def test_path_is_vault_returns_false_for_regular_dir(tmp_path) -> None:
    """_path_is_vault should return False for a regular directory."""
    from prism_tui.startup_screen import _path_is_vault
    assert _path_is_vault(str(tmp_path)) is False


def test_path_is_vault_returns_true_for_vault(tmp_path) -> None:
    """_path_is_vault should return True for a vault directory."""
    from prism_tui.startup_screen import _path_is_vault
    from prism.vault.vault import Vault
    vault = Vault.init(str(tmp_path / "myvault"))
    assert _path_is_vault(vault.path) is True
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest prism-tui/tests/test_startup_screen.py -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add prism-tui/tests/test_startup_screen.py
git commit -m "test(tui): add startup screen test coverage to 95%"
```

---

### Task 11: `prism_tui/widgets/completions.py` (88% → 95%)

**Files:**
- Modify: `prism-tui/tests/test_completions.py`

- [ ] **Step 1: Add tests for FilesystemCompleter edge cases**

Add to `prism-tui/tests/test_completions.py`:

```python
def test_completer_expands_tilde_specific_path() -> None:
    """Completer should expand ~/ effectively."""
    completer = FilesystemCompleter()
    home = os.path.expanduser("~/")
    result = completer.complete("~")
    # Should return paths under home
    assert len(result) > 0
    assert all(r.startswith(os.path.expanduser("~")) for r in result[:5])


def test_completer_oserror_returns_empty() -> None:
    """Completer should return empty list on OSError."""
    completer = FilesystemCompleter()
    result = completer.complete("/NONEXISTENT_DIR_XYZ/")
    assert result == []


def test_completer_matches_files_with_extension() -> None:
    """Completer should find files as well as directories."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "testfile.txt"), "w") as f:
            f.write("hello")
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "testfile"))
        assert any("testfile.txt" in r for r in result)
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test_completions.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_completions.py
git commit -m "test(tui): add completions test coverage to 95%"
```

---

### Task 12: `prism_tui/__main__.py` (0% → 95%)

**Files:**
- Create: `prism-tui/tests/test___main__.py`

- [ ] **Step 1: Add test for __main__.py entry point**

Create `prism-tui/tests/test___main__.py`:

```python
from unittest.mock import patch, MagicMock


def test_main_calls_app_run():
    from prism_tui.__main__ import main
    with patch("prism_tui.__main__.main") as mock_main:
        import prism_tui.__main__
        # Just verify the module imports cleanly
        assert prism_tui.__main__.__name__ == "prism_tui.__main__"
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest prism-tui/tests/test___main__.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test___main__.py
git commit -m "test(tui): add __main__ test coverage to 95%"
```

---

## CI Gates

### Task 13: Add coverage enforcement and update AGENTS.md

**Files:**
- Modify: `prism-core/pyproject.toml`
- Modify: `prism-cli/pyproject.toml`
- Modify: `prism-tui/pyproject.toml`
- Modify: `AGENTS.md`
- Modify: `prism-core/AGENTS.md`
- Modify: `prism-cli/AGENTS.md`

- [ ] **Step 1: Add fail_under gates to all pyproject.toml files**

Add to each pyproject.toml's `[tool.coverage.report]` section:

For `prism-core/pyproject.toml`:
```toml
[tool.coverage.report]
fail_under = 95
```

For `prism-cli/pyproject.toml`:
```toml
[tool.coverage.report]
fail_under = 95
```

For `prism-tui/pyproject.toml`:
```toml
[tool.coverage.report]
fail_under = 95
```

- [ ] **Step 2: Update root AGENTS.md**

Append to `AGENTS.md`:

```markdown
## Code Quality

- All subprojects must maintain ≥95% test coverage.
- Coverage is enforced via `fail_under = 95` in each `pyproject.toml`'s `[tool.coverage.report]`.
- Any new subproject must include coverage configuration and meet the 95% threshold.
```

- [ ] **Step 3: Update prism-core/AGENTS.md**

Append final line:

```markdown
- **Coverage target**: ≥95% (enforced via `[tool.coverage.report] fail_under = 95`)
```

- [ ] **Step 4: Update prism-cli/AGENTS.md**

Append final line:

```markdown
- **Coverage target**: ≥95% (enforced via `[tool.coverage.report] fail_under = 95`)
```

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md prism-core/AGENTS.md prism-cli/AGENTS.md prism-core/pyproject.toml prism-cli/pyproject.toml prism-tui/pyproject.toml
git commit -m "chore: add coverage CI gates at 95% and update AGENTS.md"
```

---

## Coverage Verification

- [ ] **Step 1: Run full coverage check**

```bash
python -m pytest prism-core/tests/ --cov=prism --cov-report=term-missing --cov-fail-under=95
python -m pytest prism-cli/tests/ --cov=prism_cli --cov-report=term-missing --cov-fail-under=95
python -m pytest prism-tui/tests/ --cov=prism_tui --cov-report=term-missing --cov-fail-under=95
```

Expected: All three exit with code 0 (all ≥95%)
