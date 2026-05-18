# TUI Startup Screen Completion & ENTER Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TAB filesystem path completion and ENTER auto-detect to the TUI startup screen.

**Architecture:** A reusable `PathInput` widget (subclass of Textual `Input`) with a pluggable `FilesystemCompleter`, mounted as a popup `ListView` below the input. `StartupScreen` gets an `on_input_submitted` handler for ENTER auto-detect.

**Tech Stack:** Python 3.11+, Textual 8.2.6, pytest-asyncio, unittest.mock

---

### Task 1: Create `widgets` package and `completions.py`

**Files:**
- Create: `prism-tui/prism_tui/widgets/__init__.py` (empty)
- Create: `prism-tui/prism_tui/widgets/completions.py` (FilesystemCompleter)

- [ ] **Step 1: Create the widgets package**

```bash
mkdir -p /home/developer/src/prism/prism-tui/prism_tui/widgets
```

- [ ] **Step 2: Create empty `__init__.py`**

```python
```

- [ ] **Step 3: Write the failing test for `FilesystemCompleter`**

```python
# tests/test_completions.py
from __future__ import annotations

import os
import tempfile

from prism_tui.widgets.completions import FilesystemCompleter


def test_completer_single_match() -> None:
    """Completing a unique prefix returns that single path."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "myvault"))
        os.makedirs(os.path.join(tmp, "other"))
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "my"))
        assert result == [os.path.join(tmp, "myvault") + "/"]


def test_completer_multiple_matches() -> None:
    """Completing an ambiguous prefix returns all matches."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "al"))
        assert len(result) == 2
        assert all(r.startswith(os.path.join(tmp, "al")) for r in result)


def test_completer_no_match_returns_empty() -> None:
    """Completing a prefix with no matches returns empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "nonexistent"))
        assert result == []


def test_completer_expands_tilde() -> None:
    """Completer should expand ~ to home directory."""
    completer = FilesystemCompleter()
    home = os.path.expanduser("~")
    result = completer.complete("~")
    # Should return something under home
    assert any(r.startswith(home) for r in result)


def test_completer_appends_trailing_slash_for_dirs() -> None:
    """Completer should add trailing / for directory matches."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "adir"))
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "ad"))
        assert result[0].endswith("/")
```

Run: `python -m pytest prism-tui/tests/test_completions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'prism_tui.widgets.completions'`

- [ ] **Step 4: Implement `FilesystemCompleter`**

File: `prism-tui/prism_tui/widgets/completions.py`

```python
from __future__ import annotations

import os
from typing import Protocol


class PathCompleter(Protocol):
    """Protocol for path completion strategies."""

    def complete(self, partial: str) -> list[str]:
        """Return matching paths for the given partial input."""
        ...


class FilesystemCompleter:
    """Completes filesystem paths using os.listdir."""

    def complete(self, partial: str) -> list[str]:
        expanded = os.path.expanduser(partial)
        dirname, basename = os.path.split(expanded)
        if not dirname:
            dirname = "."
        try:
            entries = os.listdir(dirname)
        except OSError:
            return []
        matches: list[str] = []
        for entry in entries:
            if entry.startswith(basename):
                full = os.path.join(dirname, entry)
                if os.path.isdir(full):
                    matches.append(os.path.join(dirname, entry) + "/")
                else:
                    matches.append(os.path.join(dirname, entry))
        if partial.startswith("/"):
            return [os.path.normpath(m) for m in matches]
        return matches
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest prism-tui/tests/test_completions.py -v`
Expected: all 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add prism-tui/prism_tui/widgets/ prism-tui/tests/test_completions.py
git commit -m "feat(tui): add FilesystemCompleter for path completion"
```

---

### Task 2: Create `PathInput` widget

**Files:**
- Create: `prism-tui/prism_tui/widgets/path_input.py`
- Create: `prism-tui/tests/test_path_input.py`

- [ ] **Step 1: Write the failing test for PathInput**

```python
# tests/test_path_input.py
from __future__ import annotations

import os
import tempfile

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input

from prism_tui.widgets.path_input import PathInput


class _PathInputHarness(App[None]):
    """Test harness that mounts a PathInput."""

    def compose(self) -> ComposeResult:
        yield PathInput(id="test-path-input")


@pytest.mark.asyncio
async def test_path_input_is_subclass_of_input() -> None:
    """PathInput should be a widget that contains an Input."""
    app = _PathInputHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        pi = app.screen.query_one("#test-path-input", PathInput)
        assert isinstance(pi, PathInput)


@pytest.mark.asyncio
async def test_path_input_value_property() -> None:
    """PathInput should expose value property like Input."""
    app = _PathInputHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        pi = app.screen.query_one("#test-path-input", PathInput)
        pi.value = "/tmp/test"
        assert pi.value == "/tmp/test"


@pytest.mark.asyncio
async def test_tab_completes_single_match() -> None:
    """TAB on a unique prefix should complete the path inline."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "myvault"))
        os.makedirs(os.path.join(tmp, "other"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "my")
            pi.cursor_position = len(pi.value)
            await pilot.press("tab")
            await pilot.pause()
            expected = os.path.join(tmp, "myvault") + "/"
            assert pi.value == expected


@pytest.mark.asyncio
async def test_tab_with_empty_input_does_not_complete() -> None:
    """TAB with empty input should not affect the value."""
    app = _PathInputHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        pi = app.screen.query_one("#test-path-input", PathInput)
        assert pi.value == ""
        await pilot.press("tab")
        await pilot.pause()
        assert pi.value == ""
```

Run: `python -m pytest prism-tui/tests/test_path_input.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'prism_tui.widgets.path_input'`

- [ ] **Step 2: Implement `PathInput` widget**

File: `prism-tui/prism_tui/widgets/path_input.py`

```python
from __future__ import annotations

from textual.app import ComposeResult
from textual.events import Key
from textual.widgets import Input, Label, ListItem, ListView
from textual.widget import Widget

from prism_tui.widgets.completions import FilesystemCompleter, PathCompleter


class _PathField(Input):
    """Internal Input that dismisses PathInput's popup on user typing.

    Overrides ``_on_key`` to detect printable-character keystrokes
    (user typing) while a popup is visible. Programmatic value changes
    (during cycling) do NOT go through ``_on_key``, so the popup stays
    open during TAB cycling.
    """

    async def _on_key(self, event: Key) -> None:
        parent = self.parent
        if event.is_printable and isinstance(parent, PathInput) and parent._popup is not None:
            parent._dismiss_popup()
        await super()._on_key(event)


class PathInput(Widget):
    """Widget combining an Input with TAB-completion popup.

    Composes a ``_PathField`` child for text entry and optionally mounts
    a ``ListView`` popup below the input when multiple completions exist.
    TAB cycles through matches; ESC dismisses the popup; typing dismisses it.
    """

    DEFAULT_CSS = """
    PathInput {
        height: auto;
    }

    #path-field {
        margin-bottom: 0;
    }

    #completion-popup {
        height: auto;
        max-height: 10;
        border: solid $primary;
        background: $surface;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        completer: PathCompleter | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._completer = completer or FilesystemCompleter()
        self._popup: ListView | None = None
        self._matches: list[str] = []
        self._match_index: int = 0

    def compose(self) -> ComposeResult:
        yield _PathField(id="path-field")

    @property
    def value(self) -> str:
        return self.query_one("#path-field", Input).value

    @value.setter
    def value(self, val: str) -> None:
        self.query_one("#path-field", Input).value = val

    @property
    def cursor_position(self) -> int:
        return self.query_one("#path-field", Input).cursor_position

    @cursor_position.setter
    def cursor_position(self, pos: int) -> None:
        self.query_one("#path-field", Input).cursor_position = pos

    @property
    def placeholder(self) -> str:
        return self.query_one("#path-field", Input).placeholder

    @placeholder.setter
    def placeholder(self, val: str) -> None:
        self.query_one("#path-field", Input).placeholder = val

    def on_key(self, event: Key) -> None:
        if event.key == "tab":
            if self._popup:
                event.stop()
                self._cycle_match()
            elif self.value:
                event.stop()
                self._do_complete()
            return
        elif event.key == "escape" and self._popup:
            event.stop()
            self._dismiss_popup()
            return

    def _do_complete(self) -> None:
        matches = self._completer.complete(self.value)
        if not matches:
            return
        if len(matches) == 1:
            self.value = matches[0]
            self.cursor_position = len(self.value)
        else:
            self._matches = matches
            self._match_index = 0
            self.value = matches[0]
            self.cursor_position = len(matches[0])
            self._show_popup()

    def _cycle_match(self) -> None:
        if not self._matches:
            return
        self._match_index = (self._match_index + 1) % len(self._matches)
        self.value = self._matches[self._match_index]
        self.cursor_position = len(self._matches[self._match_index])
        self._update_popup_highlight()

    def _show_popup(self) -> None:
        items = [ListItem(Label(m)) for m in self._matches]
        popup = ListView(*items, id="completion-popup")
        self.mount(popup)
        self._popup = popup
        # Focus stays on input — popup is a visual reference only

    def _dismiss_popup(self) -> None:
        if self._popup is not None:
            self._popup.remove()
            self._popup = None
        self._matches = []
        self._match_index = 0

    def _update_popup_highlight(self) -> None:
        if self._popup is not None:
            self._popup.index = self._match_index
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `python -m pytest prism-tui/tests/test_path_input.py -v`
Expected: all 4 tests PASS

- [ ] **Step 4: Commit**

```bash
git add prism-tui/prism_tui/widgets/path_input.py prism-tui/tests/test_path_input.py
git commit -m "feat(tui): add PathInput widget with TAB completion"
```

---

### Task 3: Update `StartupScreen` with `PathInput` and ENTER handler

**Files:**
- Modify: `prism-tui/prism_tui/startup_screen.py`
- Modify: `prism-tui/tests/test_startup_screen.py`

- [ ] **Step 1: Write failing tests for new ENTER behavior**

Add these tests to `tests/test_startup_screen.py`:

```python
@pytest.mark.asyncio
async def test_enter_on_existing_vault_calls_open() -> None:
    """ENTER with a path to an existing vault should call Vault.open."""
    mock_vault = MagicMock(spec=Vault)
    with (
        patch("prism_tui.startup_screen.Vault.open", return_value=mock_vault) as mock_open,
        patch("prism_tui.startup_screen.Vault.exists", return_value=True),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            path_input = screen.query_one("#path-input")
            path_input.value = "/tmp/test-vault"
            await pilot.press("enter")
            await pilot.pause()
        mock_open.assert_called_once_with("/tmp/test-vault")
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_enter_on_new_path_calls_init() -> None:
    """ENTER with a path that doesn't exist should call Vault.init."""
    mock_vault = MagicMock(spec=Vault)
    with (
        patch("prism_tui.startup_screen.Vault.init", return_value=mock_vault) as mock_init,
        patch("prism_tui.startup_screen.Vault.exists", return_value=False),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            path_input = screen.query_one("#path-input")
            path_input.value = "/tmp/new-vault"
            await pilot.press("enter")
            await pilot.pause()
        mock_init.assert_called_once_with("/tmp/new-vault")
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_enter_empty_path_uses_default() -> None:
    """ENTER with empty path should try Vault.open at default location first."""
    mock_vault = MagicMock(spec=Vault)
    with (
        patch("prism_tui.startup_screen.Vault.open", return_value=mock_vault) as mock_open,
        patch("prism_tui.startup_screen.Vault.exists", return_value=True),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
        mock_open.assert_called_once()
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_startup_screen_uses_path_input() -> None:
    """StartupScreen should use PathInput widget."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        path_input = screen.query_one("#path-input")
        from prism_tui.widgets.path_input import PathInput
        assert isinstance(path_input, PathInput)
```

Run: `python -m pytest prism-tui/tests/test_startup_screen.py -v`
Expected: 4 new tests FAIL (the existing 7 tests should still PASS)

- [ ] **Step 2: Implement StartupScreen changes**

File: `prism-tui/prism_tui/startup_screen.py` — replace the `Input` import and add `on_input_submitted`:

```python
from __future__ import annotations

import os

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

from prism.vault.vault import Vault
from prism_tui.widgets.path_input import PathInput


class StartupScreen(ModalScreen[Vault | None]):
    CSS = """
    StartupScreen {
        align: center middle;
    }

    #dialog {
        width: 50;
        height: auto;
        padding: 2 3;
        border: thick $primary;
        background: $surface;
    }

    #title {
        text-style: bold;
        content-align: center middle;
        width: 100%;
        margin-bottom: 1;
    }

    #subtitle {
        content-align: center middle;
        width: 100%;
        margin-bottom: 2;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }

    #path-input {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Prism", id="title")
            yield Label("Personal Knowledge Manager", id="subtitle")
            yield PathInput(placeholder="Path to vault (optional)", id="path-input")
            yield Button("Open Existing Vault", id="open-btn", variant="primary")
            yield Button("Initialize New Vault", id="init-btn", variant="default")

    def _get_path(self) -> str:
        path_input = self.query_one("#path-input", PathInput)
        return path_input.value.strip()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        path_str = self._get_path()

        if event.button.id == "open-btn":
            if not path_str:
                path_str = os.getcwd()
            try:
                vault = Vault.open(path_str)
                self.dismiss(vault)
            except FileNotFoundError as e:
                self.notify(str(e), severity="error", timeout=5)
            except Exception as e:
                self.notify(str(e), severity="error", timeout=5)
        elif event.button.id == "init-btn":
            if not path_str:
                self.notify("Please enter a path for the new vault", severity="error", timeout=5)
                return
            try:
                vault = Vault.init(path_str)
                self.dismiss(vault)
            except Exception as e:
                self.notify(str(e), severity="error", timeout=5)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        path_str = self._get_path()
        if not path_str:
            path_str = os.path.expanduser("~/.local/share/prism/vaults/default")
        if Vault.exists(path_str):
            try:
                vault = Vault.open(path_str)
                self.dismiss(vault)
                return
            except Exception as e:
                self.notify(str(e), severity="error", timeout=5)
        else:
            try:
                vault = Vault.init(path_str)
                self.dismiss(vault)
            except Exception as e:
                self.notify(str(e), severity="error", timeout=5)
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `python -m pytest prism-tui/tests/test_startup_screen.py -v`
Expected: all 11 tests PASS

- [ ] **Step 4: Commit**

```bash
git add prism-tui/prism_tui/startup_screen.py prism-tui/tests/test_startup_screen.py
git commit -m "feat(tui): add ENTER auto-detect and PathInput to startup screen"
```

---

### Task 4: Verify `Vault.exists` exists and works

- [ ] **Step 1: Check that `Vault.exists` is available in `prism-core`**

```bash
cd /home/developer/src/prism && .venv/bin/python -c "from prism.vault.vault import Vault; print(hasattr(Vault, 'exists'))"
```

If `Vault.exists` doesn't exist, add a check in the startup screen that uses `os.path.isdir` + checking for a `.prism` marker file instead.

- [ ] **Step 2: If `Vault.exists` is missing, update the startup screen to use a fallback check**

```python
# In on_input_submitted, replace Vault.exists(path_str) with:
_path_is_existing_vault = os.path.isdir(path_str) and os.path.isfile(os.path.join(path_str, ".prism"))
```

- [ ] **Step 3: Run all TUI tests**

Run: `python -m pytest prism-tui/tests/ -v`
Expected: all tests PASS

- [ ] **Step 4: Final commit if changes needed**

```bash
git add -A
git commit -m "fix(tui): handle missing Vault.exists with fallback check"
```

---

### Self-Review Checklist

1. **Spec coverage**: Design doc requirements all covered:
   - [x] TAB filesystem completion with popup → Task 1 + Task 2
   - [x] ENTER auto-detect → Task 3
   - [x] Reusable PathInput → Task 2
   - [x] ~ expansion → FilesystemCompleter handles `os.path.expanduser`
   - [x] Hidden files excluded → `os.listdir` returns everything, but prefix filter naturally excludes dotfiles unless prefix starts with `.`

2. **Placeholder scan**: No "TBD", "TODO", "implement later" in any task. All code is explicit.

3. **Type consistency**: `FilesystemCompleter.complete` returns `list[str]`, `PathInput.value` is `str`, `StartupScreen._get_path` returns `str` — consistent throughout.

4. **Scope**: Focused on F1 only. No unrelated changes to other wizards or tabs.
