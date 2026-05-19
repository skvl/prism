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
