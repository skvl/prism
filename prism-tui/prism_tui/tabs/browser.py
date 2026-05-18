import os
import subprocess

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import Key
from textual.message import Message
from textual.widgets import Label, ListItem, ListView, Markdown, Static, Tree
from textual.widgets._tree import TreeNode

from prism.graph.links import BacklinkIndex
from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.path.resolver import PathResolver
from prism.vault.vault import Vault

from ..command_mode import EditNodeWizard


class PathTree(Tree[str]):
    def __init__(self, **kwargs: object) -> None:
        super().__init__("", **kwargs)

    def set_resolver(
        self, resolver: PathResolver, all_nodes: list[NodeMetadata]
    ) -> None:
        self._resolver = resolver
        self._all_nodes = all_nodes
        self._loaded: set[str] = set()

    def refresh_paths(self) -> None:
        self.clear()
        self._loaded.clear()
        root_uuid = self._resolver._load_root_uuid()
        root = self.root
        root.data = root_uuid
        root.label = "/"
        root.expand()
        self._populate_children(root)

    def _populate_children(self, parent: TreeNode[str]) -> None:
        uuid = parent.data
        if uuid is None or uuid in self._loaded:
            return
        self._loaded.add(uuid)
        children = self._resolver.find_children(uuid, self._all_nodes)
        for child in sorted(
            children, key=lambda n: n.fields.get("name", n.title or "")
        ):
            name = child.fields.get("name", child.title or child.uuid[:8])
            node = parent.add_leaf(f"  {name}")
            node.data = child.uuid

    def on_tree_node_expanded(self, event: Tree.NodeExpanded[str]) -> None:
        if event.node.data:
            self._populate_children(event.node)


class BrowserTab(Static):
    CSS = """
    BrowserTab {
        height: 1fr;
    }

    #path-column {
        width: 20;
        min-width: 20;
        height: 1fr;
        border-right: solid $primary;
    }

    #node-column {
        width: 30;
        min-width: 20;
        height: 1fr;
        border-right: solid $primary;
    }

    #preview-column {
        width: 1fr;
        min-width: 30;
        height: 1fr;
    }

    .column-header {
        height: 1;
        padding: 0 1;
        background: $primary;
        color: $text;
        text-style: bold;
    }

    #path-tree {
        height: 1fr;
    }

    #node-list {
        height: 1fr;
    }

    #preview-content {
        height: 1fr;
        padding: 1;
    }
    """

    def __init__(self, vault: Vault | None = None) -> None:
        super().__init__()
        self._vault = vault
        self._manager: NodeManager | None = None
        self._resolver: PathResolver | None = None
        self._nodes_by_uuid: dict[str, NodeMetadata] = {}
        self._current_path_uuid: str | None = None
        self._current_node: NodeMetadata | None = None
        self._filter_tag: str | None = None
        self._filter_type: str | None = None
        self._active_column = 0

    def set_vault(self, vault: Vault) -> None:
        self._vault = vault
        self._manager = NodeManager(vault.path)
        self._resolver = PathResolver(vault.path)
        self._load_data()

    def _load_data(self) -> None:
        if self._manager is None or self._resolver is None:
            return
        nodes = self._manager.list_nodes()
        self._nodes_by_uuid = {n.uuid: n for n in nodes}
        tree = self.query_one("#path-tree", PathTree)
        tree.set_resolver(self._resolver, list(self._nodes_by_uuid.values()))
        tree.refresh_paths()
        self._refresh_node_list()

    def _refresh_node_list(self) -> None:
        list_view = self.query_one("#node-list", ListView)
        list_view.clear()
        if self._current_path_uuid is None:
            return
        nodes = [
            n
            for n in self._nodes_by_uuid.values()
            if self._current_path_uuid in n.paths
        ]
        if self._filter_tag:
            nodes = [n for n in nodes if self._filter_tag in n.tags]
        if self._filter_type:
            nodes = [n for n in nodes if n.type == self._filter_type]
        for node in nodes:
            tags = ", ".join(node.tags) if node.tags else ""
            label = f"{node.type} {node.title}  [{tags}]"
            item = ListItem(Label(label), id=node.uuid)
            list_view.append(item)
        if nodes:
            list_view.index = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            with VerticalScroll(id="path-column"):
                yield Label("Paths", classes="column-header")
                yield PathTree(id="path-tree")
            with VerticalScroll(id="node-column"):
                yield Label("Nodes", classes="column-header")
                yield ListView(id="node-list")
            with VerticalScroll(id="preview-column"):
                yield Label("Preview", classes="column-header")
                yield Markdown(
                    "# Welcome to Prism\n\nNo nodes yet. Press **F2** or type `:new` to create one.",
                    id="preview-content",
                )

    def on_mount(self) -> None:
        if self._vault is not None:
            self._manager = NodeManager(self._vault.path)
            self._resolver = PathResolver(self._vault.path)
            self._load_data()

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        uuid = event.node.data
        if uuid is not None:
            self._current_path_uuid = uuid
            self._refresh_node_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is None:
            return
        node = self._nodes_by_uuid.get(event.item.id or "")
        if node is not None:
            self._current_node = node
            self._show_preview(node)

    def _show_preview(self, node: NodeMetadata) -> None:
        md = self.query_one("#preview-content", Markdown)
        body = ""
        if self._manager is not None:
            blob_path = self._manager.storage.get_blob_path(node.uuid)
            if blob_path and os.path.exists(blob_path):
                with open(blob_path) as f:
                    body = f.read()
        if not body.strip():
            body = f"# {node.title}\n\n"
            if node.type == "contact":
                for key, val in node.fields.items():
                    body += f"- **{key}:** {val}\n"
            elif node.type == "bookmark":
                body += f"URL: {node.fields.get('url', '')}\n"
        meta_lines = []
        meta_lines.append(f"**Type:** {node.type}")
        if node.tags:
            meta_lines.append(f"**Tags:** {', '.join(node.tags)}")
        if node.created_at:
            meta_lines.append(f"**Created:** {node.created_at}")
        if node.updated_at:
            meta_lines.append(f"**Updated:** {node.updated_at}")
        if self._manager is not None:
            backlink_index = BacklinkIndex(self._manager.vault_path)
            backlink_count = len(backlink_index.get_backlinks(node.uuid))
            meta_lines.append(f"**Backlinks:** {backlink_count}")
        body += "\n\n---\n" + "\n\n".join(meta_lines)
        md.update(body)

    def on_key(self, event: Key) -> None:
        if event.key == "j":
            if self._active_column == 1:
                lv = self.query_one("#node-list", ListView)
                lv.action_cursor_down()
            event.stop()
        elif event.key == "k":
            if self._active_column == 1:
                lv = self.query_one("#node-list", ListView)
                lv.action_cursor_up()
            event.stop()
        elif event.key == "h":
            if self._active_column > 0:
                self._active_column -= 1
                self._set_column_focus()
            event.stop()
        elif event.key == "l":
            if self._active_column < 2:
                tree = self.query_one("#path-tree", PathTree)
                if self._active_column == 0 and tree.cursor_node is not None:
                    if tree.cursor_node.allow_expand:
                        return
                self._active_column += 1
                self._set_column_focus()
            event.stop()
        elif event.key == "gg":
            if self._active_column == 0:
                tree = self.query_one("#path-tree", PathTree)
                first = tree.root
                if first:
                    tree.select_node(first)
            elif self._active_column == 1:
                lv = self.query_one("#node-list", ListView)
                lv.index = 0
            event.stop()
        elif event.key == "G":
            if self._active_column == 1:
                lv = self.query_one("#node-list", ListView)
                lv.index = len(lv) - 1
            event.stop()
        elif event.key == "t" and self._active_column == 1:
            self._prompt_filter("tag")
            event.stop()
        elif event.key == "T" and self._active_column == 1:
            self._prompt_filter("type")
            event.stop()
        elif event.key == "e" and self._current_node is not None:
            self._edit_node()
            event.stop()
        elif event.key == "r":
            self._load_data()
            event.stop()

    def _set_column_focus(self) -> None:
        if self._active_column == 0:
            self.query_one("#path-tree", Tree).focus()
        elif self._active_column == 1:
            self.query_one("#node-list", ListView).focus()

    def _prompt_filter(self, kind: str) -> None:
        self.notify(
            f"Enter {kind} filter: (use :command mode)",
            severity="information",
            timeout=3,
        )

    def _edit_node(self) -> None:
        if self._manager is None or self._current_node is None:
            return
        blob_path = self._manager.storage.get_blob_path(self._current_node.uuid)
        if blob_path:
            editor = os.environ.get("EDITOR", "vi")
            original_mtime = os.stat(blob_path).st_mtime
            subprocess.call([editor, blob_path])
            new_mtime = os.stat(blob_path).st_mtime
            if new_mtime > original_mtime:
                self._show_preview(self._current_node)
            return
        node = self._current_node
        self.app.push_screen(
            EditNodeWizard(self._vault, node),
            lambda _: self._on_edit_done(node),
        )

    def _on_edit_done(self, node: NodeMetadata) -> None:
        if self._vault:
            self.app._update_tabs_vault(self._vault)
        updated = self._nodes_by_uuid.get(node.uuid)
        if updated is not None:
            self._current_node = updated
            self._show_preview(updated)
