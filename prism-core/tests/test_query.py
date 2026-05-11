import pytest

from prism.query.parser import QueryParser


class TestQueryParser:
    @pytest.fixture
    def parser(self):
        return QueryParser()

    def test_tag_filter(self, parser):
        ast = parser.parse("tag:work")
        assert len(ast.terms) == 1
        assert ast.terms[0]["filter"] == "tag"
        assert ast.terms[0]["value"] == "work"

    def test_type_filter(self, parser):
        ast = parser.parse("type:note")
        assert ast.terms[0]["filter"] == "type"
        assert ast.terms[0]["value"] == "note"

    def test_and_operator(self, parser):
        ast = parser.parse("tag:work AND tag:important")
        assert len(ast.terms) == 3
        assert ast.terms[1]["op"] == "AND"

    def test_or_operator(self, parser):
        ast = parser.parse("tag:work OR tag:personal")
        assert ast.terms[1]["op"] == "OR"

    def test_not_operator(self, parser):
        ast = parser.parse("tag:work AND NOT tag:archive")
        ops = [t for t in ast.terms if "op" in t]
        assert any(t["op"] == "NOT" for t in ops)

    def test_free_text(self, parser):
        ast = parser.parse("budget report")
        assert any("text" in t for t in ast.terms)

    def test_quoted_text(self, parser):
        ast = parser.parse('"hello world"')
        assert any(t.get("text") == "hello world" for t in ast.terms)

    def test_empty_query(self, parser):
        ast = parser.parse("")
        assert len(ast.terms) == 0

    def test_combined_query(self, parser):
        ast = parser.parse('type:note AND tag:meeting AND "budget"')
        assert len(ast.terms) >= 5
