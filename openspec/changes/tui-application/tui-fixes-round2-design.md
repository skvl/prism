## Context

The prism-tui application is built and functional but has three categories of bugs preventing basic interaction:

1. **Layout broken**: `CommandBar` appears right below the tab headers instead of at the terminal bottom, with empty space below it to the screen edge.

2. **Command mode typing broken**: Pressing `:` shows the command Input widget, but keystrokes don't register — the Input can't receive text input.

3. **F2 New Node wizard broken**: Selecting a type always shows the same fields (Title + Tags) regardless of type; pressing Enter to submit crashes with `TypeError: App.notify() takes 2 positional arguments but 3 were given`.

## Design

### 1. Layout restructure

**Root cause**: `TabbedContent` with `height: 1fr` and `CommandBar` with `dock: bottom` compete in the Screen's vertical layout. The `layers: base overlay` on Screen and the hidden `Input` widget between TabbedContent and CommandBar create layout artifacts — CommandBar docks within the flex context rather than to the true screen bottom.

**Fix**: Restructure `compose()` to wrap the content area in a `Vertical` container, move CommandBar outside it, and remove the unused `layers` rule.

**App CSS changes**:
- Remove `Screen { layers: base overlay; }` (unused — `StartupScreen` is a `ModalScreen`, not a layer-based overlay)
- Add `#main-content { height: 1fr; }` for the wrapper
- Move `CommandBar { height: 3; dock: bottom; }` to App-level CSS for reliability
- Keep `TabbedContent { height: 1fr; }` (works inside the wrapper)

**Compose restructure**:
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

This ensures: `Header` at top → `#main-content` fills 1fr (hosting tabs + command input) → `CommandBar` docked to bottom.

### 2. Command mode typing fix

**Root cause**: The CSS class `-active` starts with a hyphen, which is not a valid CSS identifier start character. Textual's CSS parser silently skips the `#command-input.-active` rule, so the Input stays `display: none` permanently. A `display: none` widget cannot receive focus, so `focus()` is a no-op.

**Fix**: Rename class from `-active` to `active` in both CSS and Python:

CSS change:
```css
/* Before: */
#command-input.-active { display: block; }

/* After: */
#command-input.active { display: block; }
```

Python changes in `app.py`:
- `_enter_command_mode()`: `cmd_input.add_class("active")`
- `_exit_command_mode()`: `cmd_input.remove_class("active")`

### 3. F2 New Node wizard fixes

#### 3a. Dynamic fields based on type

**Root cause**: The wizard hardcodes Title + Tags inputs regardless of the selected type. Each type schema (defined in `.metadata/types/<type>.toml`) defines its own fields — e.g. `bookmark` has a `url` field, `contact` has `name`/`email`/`phone`/`org`. These are never shown.

**Fix**: When the type selector changes, load the `TypeSchema` for that type from vault, iterate its `fields`, and dynamically render input widgets for each field (excluding `title` and `tags` which are handled separately).

Changes to `NewNodeWizard`:
1. Store loaded `dict[str, TypeSchema]` from `TypeLoader.load_all()` in `__init__`
2. Add empty `Vertical(id="type-fields")` container in `compose()` after tags input
3. Add `on_select_changed` handler:
   - Clear `#type-fields` children
   - Look up schema for selected type
   - For each `field` in `schema.fields` where `field.name not in ("title", "tags")`:
     - Yield `Label(field.name)` + `Input(placeholder=field.name)` inside `#type-fields`
4. On "Create" button press:
   - Collect field values from dynamic inputs
   - Pass as `"fields"` dict in the result object
5. `_on_new_node_result` passes `fields` to `NodeManager.create_node(...)` — `create_node` accepts a `fields` keyword argument.

Example: After selecting "bookmark", the wizard shows:
```
Type: [bookmark        ▾]
URL:  [___________________]
Title:[___________________]
Tags: [tag1, tag2, ...    ]
[Create] [Cancel]
```

#### 3b. Notify TypeError fix

**Root cause**: `App.notify()` has signature `notify(message, *, severity, timeout)` — `severity` is keyword-only. Three callbacks call it with a second positional argument:

- `_on_new_node_result`: `notify(msg, "success")`
- `_on_link_result`: `notify(msg, "success")`
- `_on_tag_result`: `notify(msg, "information")` and `notify(msg, "error")`

This causes `TypeError: App.notify() takes 2 positional arguments but 3 were given`.

**Fix**: Change all four callsites to use keyword argument:
- `notify(msg, severity="success")`
- `notify(msg, severity="information")`
- `notify(msg, severity="error")`

Also fix the `Callable` type hint in `execute_command` from `Callable[[str, str], object]` to `Callable[..., object]`.

#### 3c. Dead code removal

**Root cause**: `command_mode.py:254` has an unreachable `return` statement after an earlier `return` on line 253.

**Fix**: Remove the unreachable line:
```python
            return f"Added tags to {uid[:8]}"
            return f"Added tags to {uuid[:8]}"  # ← delete this line
```

### Files changed

| File | Changes |
|------|---------|
| `prism-tui/prism_tui/app.py` | Restructure compose, fix CSS class name, fix CSS rules |
| `prism-tui/prism_tui/command_mode.py` | Dynamic fields in wizard, notify keyword args, dead code removal |

### Testing

All changes are in the TUI layer:
- Notebook testing validates the layout restructure doesn't break the app
- The notify fix is observable via the wizard submit flow
- Dynamic fields can be verified by visually inspecting the wizard after selecting different types
