import os
import shutil
import tempfile

import pytest

from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.query.engine import QueryEngine
from prism.query.parser import QueryParser
from prism.vault.vault import Vault


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


class TestQueryEngine:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        Vault.init(d)
        uid1 = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        uid2 = "f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f"
        for uid, type_name, title, tags in [
            (uid1, "note", "Work Notes", ["work", "important"]),
            (uid2, "contact", "John Doe", ["personal"]),
        ]:
            storage_dir = compute_storage_path(d, uid)
            os.makedirs(storage_dir, exist_ok=True)
            meta = NodeMetadata(uuid=uid, type=type_name, title=title, tags=tags)
            meta.save(NodeMetadata.metadata_path(storage_dir))
        yield d
        shutil.rmtree(d)

    def test_empty_ast_returns_all(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("")
        result = engine.execute(ast)
        assert len(result) == 3

    def test_tag_filter(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("tag:work")
        result = engine.execute(ast)
        assert len(result) == 1
        assert result[0].title == "Work Notes"

    def test_type_filter(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("type:contact")
        result = engine.execute(ast)
        assert len(result) == 1
        assert result[0].title == "John Doe"

    def test_and_query(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("tag:work AND tag:important")
        result = engine.execute(ast)
        assert len(result) == 1

    def test_or_query(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("tag:work OR tag:personal")
        result = engine.execute(ast)
        assert len(result) == 2

    def test_not_query(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("tag:work AND NOT tag:important")
        result = engine.execute(ast)
        assert len(result) == 0

    def test_text_match(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("John")
        result = engine.execute(ast)
        assert len(result) == 1
        assert result[0].title == "John Doe"

    def test_empty_vault(self):
        d = tempfile.mkdtemp()
        try:
            engine = QueryEngine(d)
            ast = QueryParser().parse("tag:work")
            result = engine.execute(ast)
            assert result == []
        finally:
            shutil.rmtree(d)

    def test_no_match(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("tag:nonexistent")
        result = engine.execute(ast)
        assert result == []

    def test_match_with_fields(self, vault_dir):
        uid3 = "b0b0b0b0-0000-0000-0000-000000000000"
        storage_dir = compute_storage_path(vault_dir, uid3)
        os.makedirs(storage_dir, exist_ok=True)
        meta = NodeMetadata(uuid=uid3, type="note", title="Budget Report", fields={"amount": "1000"})
        meta.save(NodeMetadata.metadata_path(storage_dir))
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("1000")
        result = engine.execute(ast)
        assert len(result) == 1

    def test_text_match_in_body(self, vault_dir):
        uid = "dddddddd-0000-0000-0000-000000000000"
        storage_dir = compute_storage_path(vault_dir, uid)
        os.makedirs(storage_dir, exist_ok=True)
        meta = NodeMetadata(uuid=uid, type="note", title="Quiet Title", blob_extension="md")
        meta.save(NodeMetadata.metadata_path(storage_dir))
        body_path = os.path.join(storage_dir, "data.md")
        with open(body_path, "w") as f:
            f.write("This body contains mundane_details")
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("mundane_details")
        result = engine.execute(ast)
        assert len(result) == 1

    def test_corrupt_metadata_skipped(self, vault_dir):
        bad_uid = "cccccccc-0000-0000-0000-000000000000"
        storage_dir = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(NodeMetadata.metadata_path(storage_dir), "w") as f:
            f.write("not [[valid toml\n")
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("")
        result = engine.execute(ast)
        assert len(result) == 3

    def test_not_standalone_excludes(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("NOT tag:work")
        result = engine.execute(ast)
        assert len(result) == 2
        uuids = {n.uuid for n in result}
        assert "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" not in uuids

    def test_and_not_nested(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("tag:personal AND NOT tag:nonexistent")
        result = engine.execute(ast)
        assert len(result) == 1
        assert result[0].title == "John Doe"

    def test_nonexistent_field_returns_empty(self, vault_dir):
        engine = QueryEngine(vault_dir)
        ast = QueryParser().parse("nonexistent:value")
        result = engine.execute(ast)
        assert result == []
