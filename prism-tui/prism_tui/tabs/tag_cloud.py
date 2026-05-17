from __future__ import annotations

from collections import Counter
from typing import Optional

from textual.containers import Horizontal, VerticalScroll
from textual.events import Key
from textual.message import Message
from textual.widgets import Button, Label, ListItem, ListView, Static

from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.vault.vault import Vault

from ..messages import SelectNode


class TagCloudTab(Static):
    CSS = """
    TagCloudTab {
        height: 1fr;
    }

    #tag-cloud-area {
        height: auto;
        max-height: 60%;
        border-bottom: solid $primary;
        padding: 1;
        wrap: true;
    }

    #tag-node-list {
        height: 1fr;
    }

    .tag-button {
        margin: 0 1;
        height: 1;
    }

    .tag-button-sm { min-width: 6; }
    .tag-button-md { min-width: 8; }
    .tag-button-lg { min-width: 10; }

    #clear-btn {
        width: 12;
        margin: 0 1;
    }
    """

    def __init__(self, vault: Vault | None = None) -> None:
        super().__init__()
        self._vault = vault
        self._manager: NodeManager | None = None
        self._tag_counts: Counter[str] = Counter()
        self._selected_tags: set[str] = set()
        self._tag_nodes: dict[str, list[NodeMetadata]] = {}
        self._filtered_nodes: list[NodeMetadata] = []

    def set_vault(self, vault: Vault) -> None:
        self._vault = vault
        self._load_tags()

    def _load_tags(self) -> None:
        if self._vault is None:
            return
        self._manager = NodeManager(self._vault.path)
        nodes = self._manager.list_nodes()
        self._tag_nodes.clear()
        counts: Counter[str] = Counter()
        for node in nodes:
            for tag in node.tags:
                counts[tag] += 1
                if tag not in self._tag_nodes:
                    self._tag_nodes[tag] = []
                self._tag_nodes[tag].append(node)
        self._tag_counts = counts
        self._render_cloud()

    def _render_cloud(self) -> None:
        area = self.query_one("#tag-cloud-area", VerticalScroll)
        area.remove_children()
        if not self._tag_counts:
            area.mount(Static("No tags found"))
            return
        max_count = max(self._tag_counts.values()) if self._tag_counts else 1
        sorted_tags = sorted(self._tag_counts.items(), key=lambda x: -x[1])
        for tag, count in sorted_tags:
            ratio = count / max_count
            if ratio > 0.7:
                style_class = "tag-button-lg"
            elif ratio > 0.4:
                style_class = "tag-button-md"
            else:
                style_class = "tag-button-sm"
            btn = Button(
                f"{tag} ({count})",
                id=f"tag-{tag}",
                classes=f"tag-button {style_class}",
            )
            if tag in self._selected_tags:
                btn.variant = "primary"
            area.mount(btn)
        btn = Button("Clear", id="clear-btn")
        area.mount(btn)

    def _update_node_list(self) -> None:
        list_view = self.query_one("#tag-node-list", ListView)
        list_view.clear()
        if self._selected_tags:
            matching: set[str] | None = None
            for tag in self._selected_tags:
                tag_node_uuids = {n.uuid for n in self._tag_nodes.get(tag, [])}
                if matching is None:
                    matching = tag_node_uuids
                else:
                    matching &= tag_node_uuids
            if matching:
                nodes = []
                for node in self._manager.list_nodes():
                    if node.uuid in matching:
                        nodes.append(node)
                self._filtered_nodes = nodes
                for node in nodes:
                    tags_str = ", ".join(node.tags) if node.tags else ""
                    label = f"{node.type} {node.title}  [{tags_str}]"
                    list_view.append(ListItem(Label(label), id=node.uuid))
        else:
            self._filtered_nodes = []
        self._highlight_co_occurring()

    def _highlight_co_occurring(self) -> None:
        if not self._selected_tags:
            return
        co_tags: Counter[str] = Counter()
        for tag in self._selected_tags:
            for node in self._tag_nodes.get(tag, []):
                for t in node.tags:
                    if t not in self._selected_tags:
                        co_tags[t] += 1
        area = self.query_one("#tag-cloud-area", VerticalScroll)
        for btn in area.query(Button):
            if btn.id == "clear-btn":
                continue
            tag_name = btn.id.replace("tag-", "", 1) if btn.id else ""
            if tag_name in self._selected_tags:
                continue
            if co_tags.get(tag_name, 0) > 0:
                btn.styles.border = ("solid", "yellow")

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="tag-cloud-area")
        yield ListView(id="tag-node-list")

    def on_mount(self) -> None:
        if self._vault is not None:
            self._load_tags()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear-btn":
            self._selected_tags.clear()
            self._render_cloud()
            self._update_node_list()
            return
        tag_name = event.button.id.replace("tag-", "", 1) if event.button.id else ""
        if tag_name in self._selected_tags:
            self._selected_tags.remove(tag_name)
        else:
            self._selected_tags.add(tag_name)
        self._render_cloud()
        self._update_node_list()

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self._selected_tags.clear()
            self._render_cloud()
            self._update_node_list()
            event.stop()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is None:
            return
        for node in self._filtered_nodes:
            if node.uuid == event.item.id:
                self.post_message(SelectNode(node))
                break
