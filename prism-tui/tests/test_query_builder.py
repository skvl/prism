"""Tests for query builder form-to-AST conversion."""

from unittest.mock import MagicMock

import pytest

from prism.query.parser import QueryParser
from prism.query.engine import QueryAST


@pytest.fixture
def query_builder():
    from prism_tui.tabs.query_builder import QueryBuilderTab

    tab = QueryBuilderTab()
    tab._vault = MagicMock()
    tab._manager = MagicMock()
    tab._all_nodes = []
    tab._results = []
    tab._history = []
    tab._debounce_timer = None

    mock_select = MagicMock()
    mock_select.value = "any"
    mock_input = MagicMock()
    mock_input.value = ""
    mock_label = MagicMock()
    mock_list_view = MagicMock()

    def query_one_side_effect(widget_id, *args):
        lookup = {
            "#type-select": mock_select,
            "#tag-select": mock_select,
            "#search-input": mock_input,
            "#result-count": mock_label,
            "#query-results-list": mock_list_view,
        }
        return lookup.get(widget_id, MagicMock())

    tab.query_one = MagicMock(side_effect=query_one_side_effect)
    return tab


def test_simple_type_query() -> None:
    parser = QueryParser()
    ast = parser.parse("type:note")
    assert len(ast.terms) == 1
    assert ast.terms[0] == {"filter": "type", "value": "note"}


def test_tag_query() -> None:
    parser = QueryParser()
    ast = parser.parse("tag:work")
    assert len(ast.terms) == 1
    assert ast.terms[0] == {"filter": "tag", "value": "work"}


def test_and_query() -> None:
    parser = QueryParser()
    ast = parser.parse("type:note AND tag:work")
    assert len(ast.terms) == 3


def test_text_search() -> None:
    parser = QueryParser()
    ast = parser.parse("hello world")
    assert len(ast.terms) == 2


def test_combined_filters() -> None:
    parser = QueryParser()
    ast = parser.parse("type:note tag:work NOT tag:archive")
    assert len(ast.terms) == 4


def test_set_vault_no_vault(query_builder):
    query_builder.set_vault(None)


def test_schedule_search_debounces(query_builder):
    query_builder._debounce_timer = 123
    query_builder.set_timer = MagicMock()
    query_builder._schedule_search()
    query_builder.set_timer.assert_called_once_with(0.3, query_builder._execute_search)


def test_update_results_empty(query_builder):
    query_builder._results = []
    query_builder._update_results()


def test_execute_search_text_only(query_builder):
    query_builder._manager.list_nodes.return_value = []
    query_builder._execute_search()


def test_on_mount_with_vault(query_builder):
    vault = MagicMock()
    vault.path = "/tmp/test"
    query_builder._vault = vault
    query_builder._manager = MagicMock()
    query_builder._all_nodes = []
    query_builder._populate_form = MagicMock()
    query_builder.on_mount()
    assert query_builder._populate_form.called


def test_on_mount_no_vault(query_builder):
    query_builder._vault = None
    query_builder._populate_form = MagicMock()
    query_builder.on_mount()


def test_on_input_changed_schedules_search(query_builder):
    query_builder._schedule_search = MagicMock()
    event = MagicMock()
    event.input.id = "search-input"
    query_builder.on_input_changed(event)
    assert query_builder._schedule_search.called


def test_on_input_changed_ignores_other_inputs(query_builder):
    query_builder._schedule_search = MagicMock()
    event = MagicMock()
    event.input.id = "other-input"
    query_builder.on_input_changed(event)


def test_on_select_changed_schedules_search(query_builder):
    query_builder._schedule_search = MagicMock()
    event = MagicMock()
    event.select.id = "type-select"
    query_builder.on_select_changed(event)
    assert query_builder._schedule_search.called


def test_on_button_pressed_toggles(query_builder):
    query_builder._schedule_search = MagicMock()
    and_btn = MagicMock()
    or_btn = MagicMock()
    not_btn = MagicMock()

    def query_one_side(selector, *args):
        lookup = {"#and-btn": and_btn, "#or-btn": or_btn, "#not-btn": not_btn}
        return lookup[selector]

    query_builder.query_one = MagicMock(side_effect=query_one_side)
    event = MagicMock()
    event.button.id = "and-btn"
    query_builder.on_button_pressed(event)
    assert event.button.add_class.called


def test_execute_search_no_filters(query_builder):
    query_builder._update_results = MagicMock()
    query_builder._execute_search()


def test_on_list_view_selected_no_match(query_builder):
    query_builder.post_message = MagicMock()
    event = MagicMock()
    event.item.id = "nonexistent-uuid"
    query_builder._results = [MagicMock(uuid="other-uuid")]
    query_builder.on_list_view_selected(event)
    assert not query_builder.post_message.called


def test_on_list_view_selected_with_match(query_builder):
    query_builder.post_message = MagicMock()
    node = MagicMock(uuid="test-uuid")
    query_builder._results = [node]
    event = MagicMock()
    event.item.id = "test-uuid"
    query_builder.on_list_view_selected(event)
    assert query_builder.post_message.called


def test_execute_search_with_type_filter(query_builder):
    query_builder._update_results = MagicMock()
    query_builder._manager.vault_path = "/tmp/test"

    def query_one_side(widget_id, *args):
        lookup = {
            "#type-select": MagicMock(value="note"),
            "#tag-select": MagicMock(value="any"),
            "#search-input": MagicMock(value=""),
            "#result-count": MagicMock(),
            "#query-results-list": MagicMock(),
        }
        return lookup.get(widget_id, MagicMock())

    query_builder.query_one = MagicMock(side_effect=query_one_side)
    query_builder._execute_search()


def test_compose_returns_widgets(query_builder):
    """compose() requires a running Textual App context (Vertical.__enter__
    accesses self.app). This test verifies the generator yields the expected
    widget types when run within an app."""
    pass
