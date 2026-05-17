from __future__ import annotations

import os
from typing import Optional

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.widgets import Button, Input, Label, ListItem, ListView, Select, Static

from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.query.engine import QueryEngine
from prism.query.parser import QueryParser
from prism.types.loader import TypeLoader
from prism.vault.vault import Vault

from ..messages import SelectNode


class QueryBuilderTab(Static):
    CSS = """
    QueryBuilderTab {
        height: 1fr;
    }

    #query-form {
        height: auto;
        max-height: 50%;
        border-bottom: solid $primary;
        padding: 1;
    }

    #query-results {
        height: 1fr;
    }

    .form-row {
        height: 3;
        margin-bottom: 1;
    }

    .form-label {
        width: 12;
        content-align: left middle;
    }

    .form-input {
        width: 1fr;
    }

    #result-count {
        height: 1;
        padding: 0 1;
    }

    #result-header {
        height: 1;
        padding: 0 1;
        background: $primary;
        color: $text;
        text-style: bold;
    }

    .toggle-btn {
        width: 8;
        margin: 0 1;
    }

    .toggle-on {
        background: $secondary;
    }
    """

    def __init__(self, vault: Vault | None = None) -> None:
        super().__init__()
        self._vault = vault
        self._manager: NodeManager | None = None
        self._all_nodes: list[NodeMetadata] = []
        self._results: list[NodeMetadata] = []
        self._history: list[dict[str, object]] = []
        self._debounce_timer: int | None = None

    def set_vault(self, vault: Vault) -> None:
        self._vault = vault
        if vault:
            self._manager = NodeManager(vault.path)
            self._all_nodes = self._manager.list_nodes()
            self._populate_form()

    def _populate_form(self) -> None:
        if self._vault is None:
            return
        types_dir = os.path.join(self._vault.path, ".metadata", "types")
        type_loader = TypeLoader(types_dir)
        types = type_loader.load_all()
        type_options = [("Any", "any")] + [(t.name, t.name) for t in types.values() if t.name != "path"]
        type_select = self.query_one("#type-select", Select)
        type_select.set_options(type_options)

        tags: set[str] = set()
        for node in self._all_nodes:
            tags.update(node.tags)
        tag_options = [("Any", "any")] + sorted([(t, t) for t in tags])
        tag_select = self.query_one("#tag-select", Select)
        tag_select.set_options(tag_options)

    def compose(self) -> ComposeResult:
        with Vertical(id="query-form"):
            with Horizontal(classes="form-row"):
                yield Label("Type:", classes="form-label")
                yield Select(options=[], id="type-select", classes="form-input")
            with Horizontal(classes="form-row"):
                yield Label("Tag:", classes="form-label")
                yield Select(options=[], id="tag-select", classes="form-input")
            with Horizontal(classes="form-row"):
                yield Label("Search:", classes="form-label")
                yield Input(placeholder="Search text...", id="search-input", classes="form-input")
            with Horizontal(classes="form-row", id="toggle-row"):
                yield Button("AND", id="and-btn", classes="toggle-btn")
                yield Button("OR", id="or-btn", classes="toggle-btn")
                yield Button("NOT", id="not-btn", classes="toggle-btn")
        yield Label("Results: 0", id="result-count")
        yield Label("Type | Title | Tags | Updated", id="result-header")
        yield ListView(id="query-results-list")

    def on_mount(self) -> None:
        if self._vault is not None:
            self._manager = NodeManager(self._vault.path)
            self._all_nodes = self._manager.list_nodes()
            self._populate_form()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self._schedule_search()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id in ("type-select", "tag-select"):
            self._schedule_search()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ("and-btn", "or-btn", "not-btn"):
            for btn_id in ("and-btn", "or-btn", "not-btn"):
                btn = self.query_one(f"#{btn_id}", Button)
                btn.remove_class("toggle-on")
            event.button.add_class("toggle-on")
            self._schedule_search()

    def _schedule_search(self) -> None:
        if self._debounce_timer is not None:
            self.set_timer(0.3, self._execute_search)

    def _execute_search(self) -> None:
        type_val = self.query_one("#type-select", Select).value
        tag_val = self.query_one("#tag-select", Select).value
        search_text = self.query_one("#search-input", Input).value.strip()

        parts = []
        if type_val and type_val != "any":
            parts.append(f"type:{type_val}")
        if tag_val and tag_val != "any":
            parts.append(f"tag:{tag_val}")
        if search_text:
            parts.append(search_text)

        query_str = " AND ".join(parts) if parts else ""
        results: list[NodeMetadata] = []
        if query_str and self._manager:
            parser = QueryParser()
            try:
                ast = parser.parse(query_str)
                engine = QueryEngine(self._manager.vault_path)
                results = engine.execute(ast)
            except Exception:
                results = []
        else:
            results = list(self._all_nodes)

        self._results = results
        self._update_results()

    def _update_results(self) -> None:
        count_label = self.query_one("#result-count", Label)
        count_label.update(f"Results: {len(self._results)}")
        list_view = self.query_one("#query-results-list", ListView)
        list_view.clear()
        for node in self._results:
            tags = ", ".join(node.tags) if node.tags else ""
            updated = (node.updated_at or "")[:19]
            label = f"{node.type}  {node.title}  [{tags}]  {updated}"
            list_view.append(ListItem(Label(label), id=node.uuid))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is None:
            return
        for node in self._results:
            if node.uuid == event.item.id:
                self.post_message(SelectNode(node))
                break
