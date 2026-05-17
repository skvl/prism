## Context

The prism-tui application launches but has several bugs that prevent basic interaction:

1. **Layout overflow** — `TabbedContent` has no `height` constraint, and `Screen`'s default `overflow: auto` causes vertical scroll bars even in empty vaults. The `CommandBar` (docked bottom) gets pushed below the visible area.

2. **Command mode non-functional** — Pressing `:` sets a boolean flag and shows a notification but never creates an `Input` widget. The user cannot type commands. `execute_command()` is never called from the app.

3. **F-keys unbound** — The `CommandBar` renders buttons labeled `F1`–`F8`, but no actual keyboard handler captures F-key presses. Pressing `F2` does nothing.

4. **Command bar actions are no-ops** — `_trigger_action()` calls `self.app.action_notify()` which only shows a notification — no actual functionality for New/Edit/Link etc.

5. **`q` quits globally** — Pressing `q` in any context exits the app, including when focused inside an Input widget in a wizard.

## Design

### Layout fix

- Add `TabbedContent { height: 1fr; }` to app CSS
- Remove dead `#main-content { height: 1fr; }` CSS rule (id never used in compose)
- This ensures TabbedContent fills available space and CommandBar stays visible

### Command mode Input

- Add hidden `Input(id="command-input")` in `compose()`, positioned between `TabbedContent` and `CommandBar`, with `display: none`
- CSS: `dock: bottom`, `height: 1`, `layer: overlay`
- `_enter_command_mode()`: show Input, clear value, focus it
- `_exit_command_mode()`: hide Input
- `on_input_submitted()`: if `command-input` fired, call `execute_command(value)`, exit command mode

### F-key bindings

- Add `BINDINGS` class variable on `PrismTui` mapping `f1`–`f8` to action methods
- Implement `action_help()`, `action_new_node()`, `action_edit_node()`, `action_link_nodes()`, `action_tag_node()`, `action_delete_node()`, `action_refresh()`, `action_menu()`
- Actions push wizards or execute commands directly
- Wire `CommandBar._trigger_action()` to call `self.app.action_{name}()` instead of no-op

### `q` key guard

- In `on_key`, check `isinstance(self.focused, Input)` before quitting
- BINDINGS system (for F-keys) naturally avoids firing when Inputs are focused

### Tests

- Update existing pilot tests
- Add test: `:` press shows command Input
- Add test: command Input submit calls `execute_command`
- Add test: `q` does not quit when focused in Input
- Add test: `F2` triggers new-node action
