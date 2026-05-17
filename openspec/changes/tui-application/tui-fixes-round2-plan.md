# Prism TUI Fixes — Round 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix layout, command mode typing, and F2 wizard bugs in prism-tui.

**Architecture:** Three independent bug categories in two files — `app.py` (layout + CSS) and `command_mode.py` (wizard + notify). Each task is self-contained with no cross-dependencies except Task 2 (test updates) must follow Task 1 (class rename).

**Tech Stack:** Python 3.11+, Textual 1.0+, prism-core

---

### Task 1: Restructure layout + rename command-input CSS class

**Files:**
- Modify: `prism-tui/prism_tui/app.py` (CSS block, `compose()`, `_enter_command_mode()`, `_exit_command_mode()`)

- [ ] **Step 1: Replace app CSS**

Replace the entire `CSS` block in `PrismTui`:

```python
CSS = """
#main-content {
    height: 1fr;
}

TabbedContent {
    height: 1fr;
}

#command-input {
    display: none;
    height: 1;
    margin: 0 0;
}

#command-input.active {
    display: block;
}

CommandBar {
    height: 3;
    dock: bottom;
    background: $surface;
    border-top: solid $primary;
}
"""
```

Changes from current:
- Removed `Screen { layers: base overlay; }` (unused)
- Added `#main-content { height: 1fr; }` for the wrapper
- Changed `#command-input.-active` → `#command-input.active`
- Moved `CommandBar` CSS from widget-level to App-level for reliable docking

- [ ] **Step 2: Restructure `compose()` with Vertical wrapper**

Change `compose()` to:

```python
def compose(self) -> ComposeResult:
    yield Header()
    with Vertical(id="main-content"):
        with TabbedContent(initial="tab-browser", id="tab-container"):
            with TabPane("Browser", id="tab-browser"):
                yield BrowserTab(vault=self._vault)
            with TabPane("Graph", id="tab-graph"):
                yield GraphTab(vault=self._vault)
            with TabPane("Tag Cloud", id="tab-tags"):
                yield TagCloudTab(vault=self._vault)
            with TabPane("Query", id="tab-query"):
                yield QueryBuilderTab(vault=self._vault)
        yield Input(id="command-input", placeholder=": ")
    yield CommandBar(vault=self._vault)
```

Changes: `TabbedContent` and `Input` are now inside `Vertical(id="main-content")`, `CommandBar` is outside it.

- [ ] **Step 3: Rename `-active` class to `active` in `_enter_command_mode` and `_exit_command_mode`**

In `_enter_command_mode()`:
```python
def _enter_command_mode(self) -> None:
    self._in_command_mode = True
    cmd_input = self.query_one("#command-input", Input)
    cmd_input.add_class("active")
    cmd_input.value = ""
    cmd_input.focus()
```

In `_exit_command_mode()`:
```python
def _exit_command_mode(self) -> None:
    self._in_command_mode = False
    cmd_input = self.query_one("#command-input", Input)
    cmd_input.remove_class("active")
```

- [ ] **Step 4: Remove CommandBar CSS from widget-level**

In `prism-tui/prism_tui/command_bar.py`, remove the CSS block entirely (the `CommandBar` CSS is now in App-level CSS from Step 1):

Delete the entire `CSS = """..."""` block from `CommandBar` class (lines 9-26).

- [ ] **Step 5: Run existing tests**

```bash
cd /home/developer/src/prism && .venv/bin/pytest prism-tui/tests/ -v 2>&1 | head -60
```

Expect: some tests may fail because they reference `-active` class — that's expected and fixed in Task 2.

- [ ] **Step 6: Commit**

```bash
git add prism-tui/prism_tui/app.py prism-tui/prism_tui/command_bar.py
git commit -m "fix(tui): restructure layout and rename -active CSS class to active"
```

---

### Task 2: Update pilot tests for class rename

**Files:**
- Modify: `prism-tui/tests/test_pilot.py`

- [ ] **Step 1: Replace all `-active` class references with `active`**

Three test functions reference `-active`:

1. `test_colon_via_shift_semicolon_enters_command_mode`:
   ```python
   assert not cmd_input.has_class("-active")     # → "active"
   assert cmd_input.has_class("-active")         # → "active"
   ```

2. `test_escape_exits_command_mode`:
   ```python
   assert cmd_input.has_class("-active")         # → "active"
   assert not cmd_input.has_class("-active")     # → "active"
   ```

3. `test_q_does_not_quit_when_focused_in_input`:
   ```python
   cmd_input.add_class("-active")                # → "active"
   ```

- [ ] **Step 2: Run tests to verify**

```bash
cd /home/developer/src/prism && .venv/bin/pytest prism-tui/tests/ -v 2>&1
```

Expect: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add prism-tui/tests/test_pilot.py
git commit -m "fix(tui): update test class references from -active to active"
```

---

### Task 3: Fix notify TypeError + remove dead code

**Files:**
- Modify: `prism-tui/prism_tui/command_mode.py`

- [ ] **Step 1: Fix `_on_new_node_result` notify call**

Line 275, change:
```python
notify(f"Created {result['type']} node: {node.uuid[:8]}", "success")
```
to:
```python
notify(f"Created {result['type']} node: {node.uuid[:8]}", severity="success")
```

- [ ] **Step 2: Fix `_on_link_result` notify call**

Line 286, change:
```python
notify(f"Linked {result['source'][:8]} -> {result['target'][:8]}", "success")
```
to:
```python
notify(f"Linked {result['source'][:8]} -> {result['target'][:8]}", severity="success")
```

- [ ] **Step 3: Fix `_on_tag_result` notify calls**

Lines 305 and 307, change:
```python
notify(f"Tag: {tag}", "information")
notify(str(e), "error")
```
to:
```python
notify(f"Tag: {tag}", severity="information")
notify(str(e), severity="error")
```

- [ ] **Step 4: Fix `execute_command` type hint**

Line 206, change:
```python
notify: Callable[[str, str], object],
```
to:
```python
notify: Callable[..., object],
```

- [ ] **Step 5: Remove dead code**

Line 254, remove the unreachable return:
```python
            return f"Added tags to {uuid[:8]}"
```
Delete that entire line.

- [ ] **Step 6: Run command dispatch tests**

```bash
cd /home/developer/src/prism && .venv/bin/pytest prism-tui/tests/test_command_dispatch.py -v
```

Expect: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add prism-tui/prism_tui/command_mode.py
git commit -m "fix(tui): fix notify TypeError and remove dead code"
```

---

### Task 4: Add dynamic type-specific fields to NewNodeWizard

**Files:**
- Modify: `prism-tui/prism_tui/command_mode.py` (`NewNodeWizard` class, `_on_new_node_result`)
- Verify: `prism-core/prism/node/manager.py` (already accepts `fields` param, no changes needed)

- [ ] **Step 1: Add type schema loading and dynamic field container to wizard**

In `NewNodeWizard.__init__`, load and store type schemas:
```python
def __init__(self, vault: Vault) -> None:
    super().__init__()
    self._vault = vault
    types_dir = os.path.join(vault.path, ".metadata", "types")
    type_loader = TypeLoader(types_dir)
    self._schemas = type_loader.load_all()
```

In `NewNodeWizard.compose`, add a dynamic field container after tags input:
```python
yield Input(placeholder="tag1, tag2, ...", id="tags-input")
yield Vertical(id="type-fields")       # ← add this line
```

The `TypeLoader` and `Vertical` imports are already present.

- [ ] **Step 2: Add `on_select_changed` handler for dynamic fields**

Add this method to `NewNodeWizard`:

```python
def on_select_changed(self, event: Select.Changed) -> None:
    if event.select.id == "type-select":
        type_name = event.value
        container = self.query_one("#type-fields", Vertical)
        container.remove_children()
        if type_name is None or type_name not in self._schemas:
            return
        schema = self._schemas[type_name]
        for field in schema.fields:
            if field.name in ("title", "tags"):
                continue
            label = Label(field.name.capitalize())
            label.classes = "field-label"
            inp = Input(placeholder=field.name, id=f"field-{field.name}")
            container.mount(label)
            container.mount(inp)
```

Add CSS for field labels:
```python
CSS = """
NewNodeWizard {
    align: center middle;
}

#dialog {
    width: 60;
    height: auto;
    padding: 2 3;
    border: thick $primary;
    background: $surface;
}

Label {
    margin-top: 1;
}

.field-label {
    margin-top: 1;
}

Input, Select {
    width: 100%;
}

#wizard-buttons {
    height: 3;
    margin-top: 1;
}

Button {
    width: 50%;
}
"""
```

- [ ] **Step 3: Update submit handler to collect dynamic field values**

In `on_button_pressed`, after collecting tags, add field collection:

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "cancel-btn":
        self.dismiss(None)
    elif event.button.id == "create-btn":
        type_name = self.query_one("#type-select", Select).value
        title = self.query_one("#title-input", Input).value.strip()
        tags_str = self.query_one("#tags-input", Input).value.strip()
        if not type_name or type_name is None:
            self.notify("Please select a type", severity="error")
            return
        if not title:
            self.notify("Please enter a title", severity="error")
            return
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        fields: dict[str, str] = {}
        for widget in self.query("#type-fields Input"):
            if isinstance(widget, Input) and widget.id and widget.id.startswith("field-"):
                field_name = widget.id.replace("field-", "", 1)
                val = widget.value.strip()
                if val:
                    fields[field_name] = val

        self.dismiss({
            "type": type_name,
            "title": title,
            "tags": tags,
            "fields": fields,
        })
```

- [ ] **Step 4: Update `_on_new_node_result` to pass fields to create_node**

```python
def _on_new_node_result(result: dict | None, vault: Vault, notify: Callable) -> None:
    if result is None:
        return
    try:
        manager = NodeManager(vault.path)
        node = manager.create_node(
            result["type"],
            title=result["title"],
            tags=result["tags"] or None,
            fields=result.get("fields"),
        )
        notify(f"Created {result['type']} node: {node.uuid[:8]}", severity="success")
    except Exception as e:
        notify(str(e), severity="error")
```

- [ ] **Step 5: Run all tests**

```bash
cd /home/developer/src/prism && .venv/bin/pytest prism-tui/tests/ -v
```

Expect: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add prism-tui/prism_tui/command_mode.py
git commit -m "feat(tui): add type-specific dynamic fields to NewNodeWizard"
```
