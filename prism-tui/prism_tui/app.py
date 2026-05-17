from __future__ import annotations

import argparse
import os

from prism.vault.context import detect_vault
from prism.vault.vault import Vault
from textual.app import App, ComposeResult
from textual.events import Key
from textual.widgets import Header, Input, TabbedContent, TabPane

from .command_bar import CommandBar
from .command_mode import execute_command
from .messages import SelectNode
from .startup_screen import StartupScreen
from .tabs.browser import BrowserTab
from .tabs.graph import GraphTab
from .tabs.query_builder import QueryBuilderTab
from .tabs.tag_cloud import TagCloudTab


class PrismTui(App):
    TITLE = "Prism"
    SUB_TITLE = "Personal Knowledge Manager"

    CSS = """
    Screen {
        layers: base overlay;
    }

    TabbedContent {
        height: 1fr;
    }

    #command-input {
        display: none;
        height: 1;
        margin: 0 0;
    }

    #command-input.-active {
        display: block;
    }
    """

    BINDINGS = [
        ("f1", "show_help", "Help"),
        ("f2", "new_node", "New"),
        ("f3", "edit_node", "Edit"),
        ("f4", "link_nodes", "Link"),
        ("f5", "tag_node", "Tag"),
        ("f6", "delete_node", "Delete"),
        ("f7", "refresh", "Refresh"),
        ("f8", "show_menu", "Menu"),
        (":", "enter_command_mode", "Command"),
        ("shift+semicolon", "enter_command_mode", None),
    ]

    def __init__(self, vault: Vault | None = None) -> None:
        super().__init__()
        self._vault = vault
        self._in_command_mode = False

    def compose(self) -> ComposeResult:
        yield Header()
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

    def on_mount(self) -> None:
        if self._vault is None:
            self.push_screen(StartupScreen(), self._on_vault_selected)

    def _on_vault_selected(self, vault: Vault | None) -> None:
        if vault is None:
            self.exit()
            return
        self._vault = vault
        self._update_tabs_vault(vault)
        command_bar = self.query_one(CommandBar)
        command_bar.set_vault(vault)

    def _update_tabs_vault(self, vault: Vault) -> None:
        tab_container = self.query_one("#tab-container", TabbedContent)
        for pane in tab_container.query(TabPane):
            for child in pane.children:
                if hasattr(child, "set_vault"):
                    child.set_vault(vault)

    def on_key(self, event: Key) -> None:
        if event.key == "q" and not isinstance(self.focused, Input):
            self.exit()
            event.stop()
        elif event.key == "escape" and self._in_command_mode:
            self._exit_command_mode()
            event.stop()

    def _enter_command_mode(self) -> None:
        self._in_command_mode = True
        cmd_input = self.query_one("#command-input", Input)
        cmd_input.add_class("-active")
        cmd_input.value = ""
        cmd_input.focus()

    def _exit_command_mode(self) -> None:
        self._in_command_mode = False
        cmd_input = self.query_one("#command-input", Input)
        cmd_input.remove_class("-active")

    def action_enter_command_mode(self) -> None:
        self._enter_command_mode()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "command-input":
            self._exit_command_mode()
            if self._vault is None:
                self.notify("No vault open", severity="error")
                return
            result = execute_command(
                event.value, self._vault, self.notify, self.push_screen
            )
            if result:
                self.notify(result)

    def action_show_help(self) -> None:
        self.notify("Commands: new, link, tag, help, quit", timeout=5)

    def action_new_node(self) -> None:
        if self._vault is None:
            self.notify("No vault open", severity="error")
            return
        execute_command("new", self._vault, self.notify, self.push_screen)

    def action_edit_node(self) -> None:
        browser = self.query_one(BrowserTab)
        if browser._current_node is not None:
            browser._edit_node()
        else:
            self.notify("No node selected", severity="warning")

    def action_link_nodes(self) -> None:
        if self._vault is None:
            self.notify("No vault open", severity="error")
            return
        execute_command("link", self._vault, self.notify, self.push_screen)

    def action_tag_node(self) -> None:
        if self._vault is None:
            self.notify("No vault open", severity="error")
            return
        execute_command("tag", self._vault, self.notify, self.push_screen)

    def action_delete_node(self) -> None:
        self.notify("Delete: not yet implemented", timeout=2)

    def action_refresh(self) -> None:
        if self._vault:
            self._update_tabs_vault(self._vault)
        self.notify("Refreshed", timeout=1)

    def action_menu(self) -> None:
        self.notify("Menu: not yet implemented", timeout=2)

    def on_select_node(self, message: SelectNode) -> None:
        tab_container = self.query_one("#tab-container", TabbedContent)
        tab_container.active = "tab-browser"
        browser = self.query_one(BrowserTab)
        if hasattr(browser, "set_vault") and self._vault:
            browser.set_vault(self._vault)
        self.notify(f"Selected: {message.node.title}", timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prism TUI")
    parser.add_argument("--vault", "-v", default=None, help="Path to vault directory")
    args = parser.parse_args()

    vault = None
    if args.vault:
        vault = Vault.open(args.vault)
    else:
        vault = detect_vault(os.getcwd())

    app = PrismTui(vault=vault)
    app.run()


if __name__ == "__main__":
    main()
