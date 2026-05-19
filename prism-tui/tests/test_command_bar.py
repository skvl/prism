from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

import pytest


@pytest.fixture
def command_bar():
    from prism_tui.command_bar import CommandBar
    bar = CommandBar()
    bar._vault = None
    bar._manager = None
    bar._current_tab = "browser"
    bar._current_column = 0
    return bar


def test_init_with_vault():
    from prism_tui.command_bar import CommandBar
    vault = MagicMock()
    bar = CommandBar(vault=vault)
    assert bar._manager is not None


def test_set_context_updates_labels(command_bar):
    command_bar._update_labels = MagicMock()
    command_bar.set_context("graph", column=1)
    assert command_bar._current_tab == "graph"
    assert command_bar._current_column == 1
    assert command_bar._update_labels.called


def test_get_labels_browser_tab(command_bar):
    labels = command_bar._get_labels()
    assert len(labels) == 8


def test_trigger_action_unknown(command_bar):
    command_bar._trigger_action("nonexistent_action")


def test_set_vault_sets_manager(command_bar):
    vault = MagicMock()
    command_bar.set_vault(vault)
    assert command_bar._vault is vault
    assert command_bar._manager is not None


def test_update_labels_removes_children(command_bar):
    bar_container = MagicMock()
    command_bar.query_one = MagicMock(return_value=bar_container)
    command_bar._update_labels()
    assert bar_container.remove_children.called


def test_on_button_pressed_triggers_action(command_bar):
    command_bar._trigger_action = MagicMock()
    event = MagicMock()
    event.button.id = "action-help"
    command_bar.on_button_pressed(event)
    command_bar._trigger_action.assert_called_with("help")


def test_trigger_action_help(command_bar):
    mock_app = MagicMock()
    with patch.object(type(command_bar), "app", new_callable=PropertyMock, return_value=mock_app):
        command_bar._trigger_action("help")
        assert mock_app.action_show_help.called


def test_trigger_action_new(command_bar):
    mock_app = MagicMock()
    with patch.object(type(command_bar), "app", new_callable=PropertyMock, return_value=mock_app):
        command_bar._trigger_action("new")
        assert mock_app.action_new_node.called


def test_trigger_action_unknown_no_error(command_bar):
    mock_app = MagicMock()
    with patch.object(type(command_bar), "app", new_callable=PropertyMock, return_value=mock_app):
        command_bar._trigger_action("nonexistent_action")
        assert not mock_app.action_show_help.called


def test_compose_returns_widgets(command_bar):
    from textual._context import active_app
    from textual.widgets import Button

    mock_app = MagicMock()
    mock_app._compose_stacks = [[]]
    token = active_app.set(mock_app)
    try:
        result = list(command_bar.compose())
    finally:
        active_app.reset(token)
    assert len(result) == 8
    for w in result:
        assert isinstance(w, Button)
    assert result[0].id == "action-help"
    assert result[1].id == "action-new"
