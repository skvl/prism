from __future__ import annotations

import os
import shlex
from datetime import datetime, timezone
from typing import Callable

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

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

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault
        types_dir = os.path.join(vault.path, ".metadata", "types")
        type_loader = TypeLoader(types_dir)
        self._schemas = type_loader.load_all()

    def compose(self) -> ComposeResult:
        type_options = [(t.name, t.name) for t in self._schemas.values() if t.name != "path"]

        with Vertical(id="dialog"):
            yield Label("Create New Node", id="title")
            yield Label("Type:")
            yield Select(type_options, prompt="Select type...", id="type-select")
            yield Label("Title:")
            yield Input(placeholder="Node title", id="title-input")
            yield Label("Tags (comma separated):")
            yield Input(placeholder="tag1, tag2, ...", id="tags-input")
            yield Vertical(id="type-fields")
            with Horizontal(id="wizard-buttons"):
                yield Button("Create", variant="primary", id="create-btn")
                yield Button("Cancel", id="cancel-btn")

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
                "fields": fields or None,
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


class EditNodeWizard(ModalScreen[bool]):
    CSS = """
    EditNodeWizard {
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

    Input, TextArea {
        width: 100%;
    }

    #desc-input {
        height: 5;
    }

    #wizard-buttons {
        height: 3;
        margin-top: 1;
    }

    Button {
        width: 50%;
    }
    """

    def __init__(self, vault: Vault, node: NodeMetadata) -> None:
        super().__init__()
        self._vault = vault
        self._node = node
        self._manager = NodeManager(vault.path)
        self._schema = self._manager.type_loader.load(node.type)

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Edit {self._node.type}: {self._node.title}", id="title")
            yield Label("Title:")
            yield Input(value=self._node.title, id="title-input")
            yield Label("Tags (comma separated):")
            yield Input(value=", ".join(self._node.tags), id="tags-input")
            if self._schema:
                for field in self._schema.fields:
                    if field.name in ("title", "tags"):
                        continue
                    yield Label(field.name.capitalize() + ":")
                    value = self._node.fields.get(field.name, "")
                    yield Input(
                        value=str(value) if value is not None else "",
                        id=f"field-{field.name}",
                    )
            yield Label("Description:")
            yield TextArea(id="desc-input")
            with Horizontal(id="wizard-buttons"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        storage_dir = compute_storage_path(self._vault.path, self._node.uuid)
        desc_path = NodeMetadata.description_path(storage_dir)
        if os.path.exists(desc_path):
            with open(desc_path) as f:
                self.query_one("#desc-input", TextArea).text = f.read()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(False)
        elif event.button.id == "save-btn":
            self._save()
            self.dismiss(True)

    def _save(self) -> None:
        uid = self._node.uuid
        storage_dir = compute_storage_path(self._vault.path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)

        title = self.query_one("#title-input", Input).value.strip()
        tags_str = self.query_one("#tags-input", Input).value.strip()
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        meta.title = title
        meta.tags = tags

        if self._schema:
            for field in self._schema.fields:
                if field.name in ("title", "tags"):
                    continue
                input_id = f"field-{field.name}"
                widget = self.query_one(f"#{input_id}", Input)
                val = widget.value.strip()
                if val:
                    meta.fields[field.name] = val
                else:
                    meta.fields.pop(field.name, None)

        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)

        desc = self.query_one("#desc-input", TextArea).text
        self._manager.set_description(uid, desc)


def execute_command(
    cmd_str: str,
    vault: Vault,
    notify: Callable[..., object],
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
            result["type"],
            title=result["title"],
            tags=result["tags"] or None,
            fields=result.get("fields"),
        )
        notify(f"Created {result['type']} node: {node.uuid[:8]}", severity="success")
    except Exception as e:
        notify(str(e), severity="error")


def _on_link_result(result: dict | None, vault: Vault, notify: Callable) -> None:
    if result is None:
        return
    try:
        extractor = LinkExtractor(vault.path)
        extractor.add_link(result["source"], result["target"])
        notify(f"Linked {result['source'][:8]} -> {result['target'][:8]}", severity="success")
    except Exception as e:
        notify(str(e), severity="error")


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
            notify(f"Tag: {tag}", severity="information")
    except Exception as e:
        notify(str(e), severity="error")
