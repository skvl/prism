from prism.node.manager import NodeManager
from prism.vault.vault import Vault
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static


class CommandBar(Static):
    CSS = """
    CommandBar Horizontal {
        height: 3;
    }

    .action-btn {
        width: 12;
        height: 3;
        margin: 0 1;
    }
    """

    def __init__(self, vault: Vault | None = None) -> None:
        super().__init__()
        self._vault = vault
        self._manager = NodeManager(vault.path) if vault else None
        self._actions: list[dict[str, str]] = []
        self._current_tab = "browser"
        self._current_column = 0

    def set_vault(self, vault: Vault) -> None:
        self._vault = vault
        self._manager = NodeManager(vault.path)

    def set_context(self, tab: str, column: int = 0) -> None:
        self._current_tab = tab
        self._current_column = column
        self._update_labels()

    def _update_labels(self) -> None:
        labels = self._get_labels()
        self._actions = labels
        bar = self.query_one("#action-bar", Horizontal)
        bar.remove_children()
        for i, act in enumerate(labels):
            key = f"F{i + 1}"
            label = act["label"]
            btn = Button(f"{key} {label}", id=f"action-{act['id']}")
            btn.classes = "action-btn"
            bar.mount(btn)

    def _get_labels(self) -> list[dict[str, str]]:
        if self._current_tab == "browser":
            if self._current_column == 0:
                return [
                    {"id": "help", "label": "Help"},
                    {"id": "new", "label": "New"},
                    {"id": "edit", "label": "Edit"},
                    {"id": "link", "label": "Link"},
                    {"id": "tag", "label": "Tag"},
                    {"id": "delete", "label": "Delete"},
                    {"id": "refresh", "label": "Refresh"},
                    {"id": "menu", "label": "Menu"},
                ]
        return [
            {"id": "help", "label": "Help"},
            {"id": "new", "label": "New"},
            {"id": "edit", "label": "Edit"},
            {"id": "link", "label": "Link"},
            {"id": "tag", "label": "Tag"},
            {"id": "delete", "label": "Delete"},
            {"id": "refresh", "label": "Refresh"},
            {"id": "menu", "label": "Menu"},
        ]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        action = btn_id.replace("action-", "")
        self._trigger_action(action)

    def _trigger_action(self, action: str) -> None:
        action_map = {
            "help": "show_help",
            "new": "new_node",
            "edit": "edit_node",
            "link": "link_nodes",
            "tag": "tag_node",
            "delete": "delete_node",
            "refresh": "refresh",
            "menu": "menu",
        }
        action_name = action_map.get(action)
        if action_name:
            self.app.action(action_name)

    def compose(self) -> ComposeResult:
        with Horizontal(id="action-bar"):
            for i, act in enumerate(self._get_labels()):
                key = f"F{i + 1}"
                btn = Button(f"{key} {act['label']}", id=f"action-{act['id']}")
                btn.classes = "action-btn"
                yield btn
