from __future__ import annotations

from unittest.mock import MagicMock

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
