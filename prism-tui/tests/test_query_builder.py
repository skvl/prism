"""Tests for query builder form-to-AST conversion."""

from prism.query.parser import QueryParser
from prism.query.engine import QueryAST


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
