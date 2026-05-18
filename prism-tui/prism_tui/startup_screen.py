from __future__ import annotations

import os
from pathlib import Path

from prism.vault.vault import Vault
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

from prism_tui.widgets.path_input import PathInput


def _path_is_vault(path_str: str) -> bool:
    """Check if a path contains a Prism vault (.metadata/vault.toml)."""
    return (Path(path_str).resolve() / ".metadata" / "vault.toml").is_file()


_DEFAULT_VAULT_PATH = os.path.expanduser("~/.local/share/prism/vaults/default")


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
            path_str = _DEFAULT_VAULT_PATH
        if _path_is_vault(path_str):
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
