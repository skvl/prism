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

    def _dismiss_popup(self) -> None:
        if self._popup is not None:
            self._popup.remove()
            self._popup = None
        self._matches = []
        self._match_index = 0

    def _update_popup_highlight(self) -> None:
        if self._popup is not None:
            self._popup.index = self._match_index
