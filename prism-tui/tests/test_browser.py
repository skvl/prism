from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from prism_tui.tabs.browser import BrowserTab


@pytest.fixture
def browser_tab():
    tab = BrowserTab()
    tab._manager = MagicMock()
    tab._manager.storage.get_blob_path.return_value = None
    tab._resolver = MagicMock()
    tab._nodes_by_uuid = {}
    tab._current_path_uuid = None
    tab._current_node = None
    tab._active_column = 0
    tab._filter_tag = None
    tab._filter_type = None
    tab.query_one = MagicMock()
    return tab


def test_load_data_returns_when_no_manager(browser_tab):
    browser_tab._manager = None
    browser_tab._resolver = None
    browser_tab._load_data()
    assert browser_tab._nodes_by_uuid == {}


def test_refresh_node_list_returns_when_no_path(browser_tab):
    browser_tab._current_path_uuid = None
    browser_tab._refresh_node_list()


def test_show_preview_no_blob(browser_tab):
    browser_tab._manager = None
    node = MagicMock()
    node.uuid = "test-uuid"
    node.type = "note"
    node.tags = []
    node.fields = {}
    node.title = "Test"
    node.created_at = None
    node.updated_at = None
    browser_tab._show_preview(node)


def test_set_column_focus_path_tree(browser_tab):
    browser_tab._active_column = 0
    browser_tab._set_column_focus()


def test_set_column_focus_node_list(browser_tab):
    browser_tab._active_column = 1
    browser_tab._set_column_focus()


def test_on_edit_done_no_vault(browser_tab):
    browser_tab._vault = None
    browser_tab._on_edit_done(MagicMock())
