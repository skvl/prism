from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def app():
    from prism_tui.app import PrismTui
    app = PrismTui()
    app._vault = MagicMock()
    app.notify = MagicMock()
    return app


def test_on_vault_selected_none(app):
    app._on_vault_selected(None)


def test_action_new_node_no_vault(app):
    app._vault = None
    app.action_new_node()
    assert app.notify.called


def test_action_link_nodes_no_vault(app):
    app._vault = None
    app.action_link_nodes()
    assert app.notify.called


def test_action_tag_node_no_vault(app):
    app._vault = None
    app.action_tag_node()
    assert app.notify.called


def test_action_show_help(app):
    app.action_show_help()
    assert app.notify.called


def test_action_edit_node_no_selection(app):
    from prism_tui.tabs.browser import BrowserTab
    browser = MagicMock()
    browser._current_node = None
    app.query_one = MagicMock(return_value=browser)
    app.notify = MagicMock()
    app.action_edit_node()
    assert app.notify.called


def test_action_edit_node_with_selection(app):
    from prism_tui.tabs.browser import BrowserTab
    browser = MagicMock()
    browser._current_node = MagicMock()
    app.query_one = MagicMock(return_value=browser)
    app.action_edit_node()
    assert browser._edit_node.called


def test_action_delete_node(app):
    app.notify = MagicMock()
    app.action_delete_node()
    assert app.notify.called


def test_action_refresh_no_vault(app):
    app._vault = None
    app.notify = MagicMock()
    app.action_refresh()
    assert app.notify.called


def test_action_refresh_with_vault(app):
    app._vault = MagicMock()
    app._update_tabs_vault = MagicMock()
    app.notify = MagicMock()
    app.action_refresh()
    assert app._update_tabs_vault.called


def test_action_menu(app):
    app.notify = MagicMock()
    app.action_menu()
    assert app.notify.called


def test_enter_command_mode(app):
    cmd_input = MagicMock()
    app.query_one = MagicMock(return_value=cmd_input)
    app._enter_command_mode()
    assert app._in_command_mode is True
    assert cmd_input.add_class.called
    assert cmd_input.focus.called


def test_exit_command_mode(app):
    cmd_input = MagicMock()
    app.query_one = MagicMock(return_value=cmd_input)
    app._in_command_mode = True
    app._exit_command_mode()
    assert app._in_command_mode is False
    assert cmd_input.remove_class.called


def test_action_enter_command_mode(app):
    app._enter_command_mode = MagicMock()
    app.action_enter_command_mode()
    assert app._enter_command_mode.called


def test_on_input_submitted_no_vault(app):
    app._vault = None
    app._exit_command_mode = MagicMock()
    app.notify = MagicMock()
    event = MagicMock()
    event.input.id = "command-input"
    event.value = "new"
    app.on_input_submitted(event)
    assert app.notify.called


def test_on_input_submitted_with_result(app):
    from unittest.mock import patch
    app._vault = MagicMock()
    app._exit_command_mode = MagicMock()
    app.notify = MagicMock()
    event = MagicMock()
    event.input.id = "command-input"
    event.value = "help"
    with patch("prism_tui.app.execute_command", return_value="Commands: help"):
        app.on_input_submitted(event)
    assert app.notify.called


def test_on_key_q_exits(app):
    from unittest.mock import PropertyMock, patch
    from prism_tui.app import PrismTui
    event = MagicMock()
    event.key = "q"
    with patch.object(PrismTui, "focused", PropertyMock(return_value=None)):
        app.on_key(event)
    assert event.stop.called


def test_on_key_escape_in_command_mode(app):
    app._in_command_mode = True
    app._exit_command_mode = MagicMock()
    event = MagicMock()
    event.key = "escape"
    app.on_key(event)
    assert app._exit_command_mode.called


def test_on_vault_selected_with_vault(app):
    vault = MagicMock()
    app._update_tabs_vault = MagicMock()
    command_bar = MagicMock()
    app.query_one = MagicMock(return_value=command_bar)
    app._on_vault_selected(vault)
    assert app._vault is vault
    assert app._update_tabs_vault.called
    assert command_bar.set_vault.called


def test_on_vault_selected_none_exits(app):
    app.exit = MagicMock()
    app._on_vault_selected(None)
    assert app.exit.called


def test_update_tabs_vault(app):
    vault = MagicMock()
    tab_container = MagicMock()
    pane = MagicMock()
    child = MagicMock()
    child.has_attr.side_effect = lambda x: x == "set_vault"
    pane.children = [child]
    tab_container.query.return_value = [pane]
    app.query_one = MagicMock(return_value=tab_container)
    app._update_tabs_vault(vault)
    assert child.set_vault.called


def test_on_select_node_switches_tab(app):
    msg = MagicMock()
    msg.node = MagicMock()
    msg.node.title = "Test"
    tab_container = MagicMock()
    browser = MagicMock()
    app._vault = MagicMock()

    def query_one_side_effect(*args, **kwargs):
        if len(args) >= 2 and args[1].__name__ == "TabbedContent":
            return tab_container
        return browser

    app.query_one = MagicMock(side_effect=query_one_side_effect)
    app.notify = MagicMock()
    app.on_select_node(msg)
    assert tab_container.active == "tab-browser"


def test_compose_returns_widgets(app):
    from textual._context import active_app
    from textual.compose import compose
    token = active_app.set(app)
    try:
        result = compose(app)
    finally:
        active_app.reset(token)
    from textual.widgets import Header, Input
    from textual.containers import Vertical
    from prism_tui.command_bar import CommandBar
    assert any(isinstance(w, Header) for w in result)
    assert any(isinstance(w, Vertical) for w in result)
    assert any(isinstance(w, CommandBar) for w in result)
    vertical = next(w for w in result if isinstance(w, Vertical))
    assert any(isinstance(c, Input) for c in vertical._pending_children)


def test_on_mount_with_vault(app):
    app._vault = MagicMock()
    app.push_screen = MagicMock()
    app.on_mount()
    assert not app.push_screen.called


def test_action_link_nodes_with_vault(app):
    from unittest.mock import patch
    with patch("prism_tui.app.execute_command") as mock_exec:
        app.action_link_nodes()
    mock_exec.assert_called_once()


def test_action_tag_node_with_vault(app):
    from unittest.mock import patch
    with patch("prism_tui.app.execute_command") as mock_exec:
        app.action_tag_node()
    mock_exec.assert_called_once()


def test_main_creates_app_with_vault_path(app):
    import sys
    from unittest.mock import patch, MagicMock
    from prism_tui.app import main
    with patch("sys.argv", ["prism-tui", "--vault", "/tmp/test"]):
        with patch("prism_tui.app.Vault.open", return_value=MagicMock()):
            with patch("prism_tui.app.PrismTui") as mock_app:
                main()
    mock_app.assert_called_once()


def test_main_creates_app_without_vault(app):
    import sys
    from unittest.mock import patch, MagicMock
    from prism_tui.app import main
    with patch("sys.argv", ["prism-tui"]):
        with patch("prism_tui.app.detect_vault", return_value=MagicMock()):
            with patch("prism_tui.app.PrismTui") as mock_app:
                main()
    mock_app.assert_called_once()
