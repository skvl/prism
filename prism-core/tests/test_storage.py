import os
import shutil
import tempfile

import pytest

from prism.node.storage import sha256_file, compute_storage_path, StorageEngine
from prism.vault.vault import uuid_to_path
import uuid


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
