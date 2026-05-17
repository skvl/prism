from __future__ import annotations

import os
import shlex
from typing import Callable

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.types.loader import TypeLoader
from prism.vault.vault import Vault


class NewNodeWizard(ModalScreen[dict | None]):
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

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault

    def compose(self) -> ComposeResult:
        types_dir = os.path.join(self._vault.path, ".metadata", "types")
        type_loader = TypeLoader(types_dir)
        types = type_loader.load_all()
        type_options = [(t.name, t.name) for t in types.values() if t.name != "path"]

        with Vertical(id="dialog"):
            yield Label("Create New Node", id="title")
            yield Label("Type:")
            yield Select(type_options, prompt="Select type...", id="type-select")
            yield Label("Title:")
            yield Input(placeholder="Node title", id="title-input")
            yield Label("Tags (comma separated):")
            yield Input(placeholder="tag1, tag2, ...", id="tags-input")
            with Horizontal(id="wizard-buttons"):
                yield Button("Create", variant="primary", id="create-btn")
                yield Button("Cancel", id="cancel-btn")

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
            self.dismiss({
                "type": type_name,
                "title": title,
                "tags": tags,
            })


class LinkNodesWizard(ModalScreen[dict | None]):
    CSS = """
    LinkNodesWizard {
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

    Input {
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

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Link Nodes", id="title")
            yield Label("Source UUID:")
            yield Input(placeholder="Source node UUID", id="source-input")
            yield Label("Target UUID:")
            yield Input(placeholder="Target node UUID", id="target-input")
            with Horizontal(id="wizard-buttons"):
                yield Button("Link", variant="primary", id="link-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "link-btn":
            source = self.query_one("#source-input", Input).value.strip()
            target = self.query_one("#target-input", Input).value.strip()
            if not source or not target:
                self.notify("Both source and target UUIDs are required", severity="error")
                return
            self.dismiss({"source": source, "target": target})


class TagManageWizard(ModalScreen[dict | None]):
    CSS = """
    TagManageWizard {
        align: center middle;
    }

    #dialog {
        width: 50;
        height: auto;
        padding: 2 3;
        border: thick $primary;
        background: $surface;
    }

    Label {
        margin-top: 1;
    }

    Input {
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

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Manage Tags", id="title")
            yield Label("Comma-separated tags to add:")
            yield Input(placeholder="tag1, tag2, ...", id="tags-input")
            with Horizontal(id="wizard-buttons"):
                yield Button("Add", variant="primary", id="add-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "add-btn":
            tags_str = self.query_one("#tags-input", Input).value.strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
            self.dismiss({"tags": tags})


def execute_command(
    cmd_str: str,
    vault: Vault,
    notify: Callable[[str, str], object],
    push_screen: Callable,
) -> str | None:
    try:
        parts = shlex.split(cmd_str)
    except ValueError as e:
        return f"Invalid command: {e}"
    if not parts:
        return None
    cmd = parts[0]
    args = parts[1:]

    try:
        if cmd == "new":
            if not args:
                push_screen(NewNodeWizard(vault), lambda r: _on_new_node_result(r, vault, notify))
                return None
            type_name = args[0]
            title = ""
            tags: list[str] = []
            i = 1
            while i < len(args):
                if args[i] == "--tag" and i + 1 < len(args):
                    tags.append(args[i + 1])
                    i += 2
                elif not title:
                    title = args[i]
                    i += 1
                else:
                    i += 1
            manager = NodeManager(vault.path)
            node = manager.create_node(type_name, title=title, tags=tags or None)
            return f"Created {type_name} node: {node.uuid[:8]}"
        elif cmd == "link":
            if len(args) < 2:
                push_screen(LinkNodesWizard(vault), lambda r: _on_link_result(r, vault, notify))
                return None
            source, target = args[0], args[1]
            _add_link(vault.path, source, target)
            return f"Linked {source[:8]} -> {target[:8]}"
        elif cmd == "tag":
            if len(args) < 2:
                push_screen(TagManageWizard(vault), lambda r: _on_tag_result(r, vault, notify))
                return None
            uid = args[0]
            manager = NodeManager(vault.path)
            for tag in args[1:]:
                manager.add_tag(uid, tag)
            return f"Added tags to {uid[:8]}"
            return f"Added tags to {uuid[:8]}"
        elif cmd == "help":
            return "Commands: new, link, tag, help, quit"
        elif cmd in ("quit", "exit", "q"):
            from textual.app import App
            App.running_app.exit()
            return None
        else:
            return f"Unknown command: {cmd}"
    except Exception as e:
        return f"Error: {e}"


def _on_new_node_result(result: dict | None, vault: Vault, notify: Callable) -> None:
    if result is None:
        return
    try:
        manager = NodeManager(vault.path)
        node = manager.create_node(
            result["type"], title=result["title"], tags=result["tags"] or None
        )
        notify(f"Created {result['type']} node: {node.uuid[:8]}", "success")
    except Exception as e:
        notify(str(e), "error")


def _on_link_result(result: dict | None, vault: Vault, notify: Callable) -> None:
    if result is None:
        return
    try:
        extractor = LinkExtractor(vault.path)
        extractor.add_link(result["source"], result["target"])
        notify(f"Linked {result['source'][:8]} -> {result['target'][:8]}", "success")
    except Exception as e:
        notify(str(e), "error")


def _add_link(vault_path: str, source_uuid: str, target_uuid: str) -> None:
    source_dir = compute_storage_path(vault_path, source_uuid)
    source_meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(source_dir))
    source_meta.links.append({"target": target_uuid})
    source_meta.sync_dirty = True
    source_meta.save(NodeMetadata.metadata_path(source_dir))


def _on_tag_result(result: dict | None, vault: Vault, notify: Callable) -> None:
    if result is None:
        return
    try:
        manager = NodeManager(vault.path)
        for tag in result["tags"]:
            notify(f"Tag: {tag}", "information")
    except Exception as e:
        notify(str(e), "error")
