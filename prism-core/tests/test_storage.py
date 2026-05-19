import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest
from prism.node.storage import StorageEngine, compute_storage_path, sha256_file


class TestStorageEngine:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, ".storage"), exist_ok=True)
        yield d
        shutil.rmtree(d)

    @pytest.fixture
    def engine(self, vault_dir):
        return StorageEngine(vault_dir)

    def test_import_blob(self, engine, vault_dir):
        src = os.path.join(vault_dir, "test.txt")
        with open(src, "w") as f:
            f.write("hello world")

        uid = str(uuid.uuid4())
        dest = engine.import_blob(src, uid)
        assert os.path.exists(dest)
        assert dest.endswith(".txt")

    def test_delete_blob(self, engine, vault_dir):
        src = os.path.join(vault_dir, "test.txt")
        with open(src, "w") as f:
            f.write("hello")

        uid = str(uuid.uuid4())
        engine.import_blob(src, uid)
        assert engine.delete_blob(uid) is True
        assert engine.delete_blob(uid) is False

    def test_read_blob(self, engine, vault_dir):
        src = os.path.join(vault_dir, "test.txt")
        with open(src, "w") as f:
            f.write("hello world")

        uid = str(uuid.uuid4())
        engine.import_blob(src, uid)
        data = engine.read_blob(uid)
        assert data == b"hello world"

    def test_verify_integrity(self, engine, vault_dir):
        src = os.path.join(vault_dir, "test.txt")
        with open(src, "w") as f:
            f.write("test content")

        uid = str(uuid.uuid4())
        engine.import_blob(src, uid)
        h = sha256_file(src)
        assert engine.verify_integrity(uid, h) is True
        assert engine.verify_integrity(uid, "wronghash") is False

    def test_read_blob_nonexistent(self, engine):
        result = engine.read_blob("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_read_blob_no_data_file(self, engine, vault_dir):
        uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(os.path.join(storage_dir, "metadata.toml"), "w") as f:
            f.write("")
        result = engine.read_blob(uid)
        assert result is None

    def test_get_blob_path(self, engine, vault_dir):
        src = os.path.join(vault_dir, "test.txt")
        with open(src, "w") as f:
            f.write("hello")
        uid = str(uuid.uuid4())
        engine.import_blob(src, uid)
        path = engine.get_blob_path(uid)
        assert path is not None
        assert path.endswith(".txt")

    def test_get_blob_path_nonexistent(self, engine):
        path = engine.get_blob_path("00000000-0000-0000-0000-000000000000")
        assert path is None

    def test_get_blob_path_no_data_file(self, engine, vault_dir):
        uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, uid)
        os.makedirs(storage_dir, exist_ok=True)
        path = engine.get_blob_path(uid)
        assert path is None

    def test_verify_integrity_no_blob(self, engine):
        assert engine.verify_integrity("00000000-0000-0000-0000-000000000000", "hash") is False

    def test_read_description_missing(self, engine):
        result = engine.read_description("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_delete_description_found(self, engine, vault_dir):
        uid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        storage_dir = compute_storage_path(vault_dir, uid)
        os.makedirs(storage_dir, exist_ok=True)
        desc_path = os.path.join(storage_dir, "description.md")
        Path(desc_path).write_text("test description")
        result = engine.delete_description(uid)
        assert result is True
        assert not os.path.exists(desc_path)

    def test_delete_description_not_found(self, engine):
        result = engine.delete_description("00000000-0000-0000-0000-000000000000")
        assert result is False

    def test_verify_description_integrity_empty_hash(self, engine, vault_dir):
        uid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        result = engine.verify_description_integrity(uid, "")
        assert result is True

    def test_verify_description_integrity_no_file(self, engine, vault_dir):
        uid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        result = engine.verify_description_integrity(uid, "abc123")
        assert result is False


class TestSha256:
    def test_sha256_file(self):
        tmp = tempfile.mkstemp()[1]
        try:
            with open(tmp, "wb") as f:
                f.write(b"test data")
            h = sha256_file(tmp)
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)
        finally:
            os.unlink(tmp)

    def test_chunked_reading(self):
        tmp = tempfile.mkstemp()[1]
        try:
            with open(tmp, "wb") as f:
                f.write(b"a" * 100000)
            h = sha256_file(tmp, chunk_size=1024)
            assert len(h) == 64
        finally:
            os.unlink(tmp)


class TestUuidToPath:
    def test_compute_storage_path(self):
        uid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        path = compute_storage_path("/vault", uid)
        assert "/vault/.storage/" in path
        assert "a1b2" in path
        assert "a7b8c9d0e1f2" in path
