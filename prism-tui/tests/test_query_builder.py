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
