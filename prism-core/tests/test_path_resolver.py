import os
import shutil
import tempfile
import uuid

import pytest
import tomlkit

from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.path.resolver import PathResolver
from prism.vault.vault import Vault


class TestPathResolver:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        Vault.init(d)
        yield d
        shutil.rmtree(d)

    def _root_uuid(self, vault_dir):
        with open(os.path.join(vault_dir, ".metadata", "vault.toml")) as f:
            doc = tomlkit.load(f)
        return doc["path_root_uuid"]

    def _create_path(self, vault_dir, name, parent_uuid):
        uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, uid)
        os.makedirs(storage_dir, exist_ok=True)
        meta = NodeMetadata(
            uuid=uid,
            type="path",
            title=name,
            fields={"name": name},
            links=[{"target": parent_uuid, "type": "path-parent", "title": ".."}],
        )
        meta.save(NodeMetadata.metadata_path(storage_dir))
        return uid

    def test_resolve_root(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        assert resolver.resolve("/") == root_uuid

    def test_resolve_single_segment(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        foo_uuid = self._create_path(vault_dir, "foo", root_uuid)
        assert resolver.resolve("/foo") == foo_uuid

    def test_resolve_multi_segment(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        foo_uuid = self._create_path(vault_dir, "foo", root_uuid)
        bar_uuid = self._create_path(vault_dir, "bar", foo_uuid)
        baz_uuid = self._create_path(vault_dir, "baz", bar_uuid)
        assert resolver.resolve("/foo/bar/baz") == baz_uuid

    def test_resolve_nonexistent_raises(self, vault_dir):
        resolver = PathResolver(vault_dir)
        with pytest.raises(ValueError, match="Path segment not found"):
            resolver.resolve("/nonexistent")

    def test_resolve_without_leading_slash_raises(self, vault_dir):
        resolver = PathResolver(vault_dir)
        with pytest.raises(ValueError, match="Path must start with /"):
            resolver.resolve("foo")

    def test_resolve_or_create_missing(self, vault_dir):
        resolver = PathResolver(vault_dir)
        uid = resolver.resolve_or_create("/new/path")
        assert uid
        assert resolver.resolve("/new/path") == uid

    def test_resolve_or_create_existing_prefix(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        self._create_path(vault_dir, "foo", root_uuid)
        uid = resolver.resolve_or_create("/foo/bar")
        assert uid
        assert resolver.resolve("/foo/bar") == uid

    def test_resolve_or_create_invalid_segment(self, vault_dir):
        resolver = PathResolver(vault_dir)
        with pytest.raises(ValueError, match="Invalid path segment"):
            resolver.resolve_or_create("/bad\x00path")

    def test_collect_descendants(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        a_uuid = self._create_path(vault_dir, "a", root_uuid)
        b_uuid = self._create_path(vault_dir, "b", a_uuid)
        c_uuid = self._create_path(vault_dir, "c", root_uuid)
        descendants = resolver.collect_descendants(root_uuid)
        assert sorted(descendants) == sorted([a_uuid, b_uuid, c_uuid])

    def test_complete_matches(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        self._create_path(vault_dir, "foo", root_uuid)
        assert resolver.complete("/fo") == ["/foo"]
        assert resolver.complete("/f") == ["/foo"]

    def test_complete_no_matches(self, vault_dir):
        resolver = PathResolver(vault_dir)
        assert resolver.complete("/z") == []

    def test_resolve_uuid_to_path(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        foo_uuid = self._create_path(vault_dir, "foo", root_uuid)
        bar_uuid = self._create_path(vault_dir, "bar", foo_uuid)
        baz_uuid = self._create_path(vault_dir, "baz", bar_uuid)
        assert resolver.resolve_uuid_to_path(baz_uuid) == "/foo/bar/baz"

    def test_resolve_uuid_to_path_root(self, vault_dir):
        resolver = PathResolver(vault_dir)
        root_uuid = self._root_uuid(vault_dir)
        assert resolver.resolve_uuid_to_path(root_uuid) == "/"

    def test_resolve_uuid_to_path_unknown(self, vault_dir):
        resolver = PathResolver(vault_dir)
        assert resolver.resolve_uuid_to_path(str(uuid.uuid4())) == ""
