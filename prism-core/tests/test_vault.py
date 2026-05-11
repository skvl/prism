import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

from prism.vault.vault import Vault, generate_uuid, uuid_to_path


class TestVaultLifecycle:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_generate_uuid(self):
        uid = generate_uuid()
        assert isinstance(uid, uuid.UUID)

    def test_uuid_to_path(self):
        uid = uuid.UUID("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
        path = uuid_to_path(uid)
        assert path == os.path.join("a1b2", "c3d4", "e5f6", "4a7b8c9d0e1f2a3b4c5d")

    def test_init_vault(self, temp_dir):
        vault = Vault.init(temp_dir)
        assert os.path.exists(os.path.join(temp_dir, ".storage"))
        assert os.path.exists(os.path.join(temp_dir, ".metadata"))
        assert os.path.exists(os.path.join(temp_dir, ".metadata", "types"))
        assert os.path.exists(os.path.join(temp_dir, ".metadata", "index.txt"))
        assert os.path.exists(os.path.join(temp_dir, ".metadata", "vault.toml"))
        assert vault.vault_uuid

    def test_open_vault(self, temp_dir):
        vault = Vault.init(temp_dir)
        opened = Vault.open(temp_dir)
        assert opened.vault_uuid == vault.vault_uuid
        assert opened.schema_version == vault.schema_version

    def test_open_invalid_vault(self):
        with pytest.raises(FileNotFoundError):
            Vault.open("/nonexistent/path")

    def test_validate_vault(self, temp_dir):
        vault = Vault.init(temp_dir)
        issues = vault.validate()
        assert issues == []

    def test_vault_already_exists(self, temp_dir):
        Vault.init(temp_dir)
        with pytest.raises(FileExistsError):
            Vault.init(temp_dir)


class TestVaultRegistry:
    @pytest.fixture
    def registry(self, monkeypatch):
        tmp = tempfile.mkdtemp()
        reg_path = Path(tmp) / "vaults.toml"
        monkeypatch.setattr("prism.vault.registry.REGISTRY_PATH", reg_path)
        from prism.vault.registry import VaultRegistry
        return VaultRegistry()

    def test_add_and_list(self, registry):
        registry.add("uuid-1", "/path/to/vault1")
        registry.add("uuid-2", "/path/to/vault2", name="my vault")
        vaults = registry.list()
        assert len(vaults) == 2

    def test_remove(self, registry):
        registry.add("uuid-1", "/path/to/vault1")
        assert registry.remove("/path/to/vault1") is True
        assert registry.remove("/nonexistent") is False
        assert len(registry.list()) == 0

    def test_get_by_uuid(self, registry):
        registry.add("test-uuid", "/path")
        result = registry.get_by_uuid("test-uuid")
        assert result is not None
        assert result["uuid"] == "test-uuid"

    def test_get_by_path(self, registry):
        registry.add("test-uuid", "/my/path")
        result = registry.get_by_path("/my/path")
        assert result is not None
        assert result["path"] == "/my/path"
