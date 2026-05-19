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


def test_compose_returns_widgets(browser_tab):
    from unittest.mock import MagicMock, patch
    from textual.widgets import Markdown
    with patch("textual.message_pump.active_app") as mock_ctx:
        mock_app = MagicMock()
        mock_app._compose_stacks = [[]]
        mock_app._composed = [[]]
        mock_ctx.get.return_value = mock_app
        result = list(browser_tab.compose())
    assert len(result) == 6
    assert sum(1 for r in result if isinstance(r, Markdown)) == 1


def test_load_data_calls_set_resolver(browser_tab):
    browser_tab._manager = MagicMock()
    browser_tab._manager.list_nodes.return_value = []
    browser_tab._resolver = MagicMock()
    tree = MagicMock()
    browser_tab.query_one = MagicMock(return_value=tree)
    browser_tab._load_data()
    assert tree.set_resolver.called


def test_refresh_node_list_filters_by_tag(browser_tab):
    browser_tab._current_path_uuid = "path-uuid"
    node_a = MagicMock()
    node_a.uuid = "a"
    node_a.paths = ["path-uuid"]
    node_a.tags = ["work"]
    node_a.type = "note"
    node_a.title = "A"
    node_b = MagicMock()
    node_b.uuid = "b"
    node_b.paths = ["path-uuid"]
    node_b.tags = ["personal"]
    node_b.type = "note"
    node_b.title = "B"
    browser_tab._nodes_by_uuid = {"a": node_a, "b": node_b}
    browser_tab._filter_tag = "work"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab._refresh_node_list()
    assert list_view.clear.called
    assert list_view.append.called


def test_refresh_node_list_filters_by_type(browser_tab):
    browser_tab._current_path_uuid = "path-uuid"
    node_a = MagicMock()
    node_a.uuid = "a"
    node_a.paths = ["path-uuid"]
    node_a.tags = []
    node_a.type = "contact"
    node_a.title = "A"
    node_b = MagicMock()
    node_b.uuid = "b"
    node_b.paths = ["path-uuid"]
    node_b.tags = []
    node_b.type = "note"
    node_b.title = "B"
    browser_tab._nodes_by_uuid = {"a": node_a, "b": node_b}
    browser_tab._filter_type = "contact"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab._refresh_node_list()
    assert list_view.clear.called


def test_on_tree_node_selected_sets_path(browser_tab):
    browser_tab._refresh_node_list = MagicMock()
    event = MagicMock()
    event.node.data = "some-uuid"
    browser_tab.on_tree_node_selected(event)
    assert browser_tab._current_path_uuid == "some-uuid"
    assert browser_tab._refresh_node_list.called


def test_on_list_view_selected_shows_preview(browser_tab):
    browser_tab._nodes_by_uuid = {"node-uuid": MagicMock()}
    browser_tab._show_preview = MagicMock()
    event = MagicMock()
    event.item.id = "node-uuid"
    browser_tab.on_list_view_selected(event)
    assert browser_tab._show_preview.called


def test_on_key_j_navigates_down(browser_tab):
    browser_tab._active_column = 1
    event = MagicMock()
    event.key = "j"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab.on_key(event)
    assert list_view.action_cursor_down.called


def test_on_key_k_navigates_up(browser_tab):
    browser_tab._active_column = 1
    event = MagicMock()
    event.key = "k"
    list_view = MagicMock()
    browser_tab.query_one = MagicMock(return_value=list_view)
    browser_tab.on_key(event)
    assert list_view.action_cursor_up.called


def test_on_key_h_moves_left(browser_tab):
    browser_tab._active_column = 1
    browser_tab._set_column_focus = MagicMock()
    event = MagicMock()
    event.key = "h"
    browser_tab.on_key(event)
    assert browser_tab._active_column == 0
    assert browser_tab._set_column_focus.called


def test_on_key_r_refreshes(browser_tab):
    browser_tab._load_data = MagicMock()
    event = MagicMock()
    event.key = "r"
    browser_tab.on_key(event)
    assert browser_tab._load_data.called


def test_on_key_t_prompts_tag_filter(browser_tab):
    browser_tab._active_column = 1
    browser_tab._prompt_filter = MagicMock()
    event = MagicMock()
    event.key = "t"
    browser_tab.on_key(event)
    browser_tab._prompt_filter.assert_called_with("tag")


def test_prompt_filter_notifies(browser_tab):
    browser_tab.notify = MagicMock()
    browser_tab._prompt_filter("tag")
    assert browser_tab.notify.called


def test_on_edit_done_with_vault(browser_tab):
    from unittest.mock import PropertyMock, patch
    browser_tab._vault = MagicMock()
    with patch.object(BrowserTab, "app", new_callable=PropertyMock) as mock_app:
        mock_app.return_value = MagicMock()
        browser_tab._nodes_by_uuid = {}
        browser_tab._show_preview = MagicMock()
        browser_tab._on_edit_done(MagicMock(uuid="x"))
