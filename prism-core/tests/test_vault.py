import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest
import tomlkit
from prism.vault.context import detect_vault
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

    def test_validate_missing_dirs(self, temp_dir):
        vault = Vault(temp_dir, "some-uuid", 1, "2024-01-01")
        issues = vault.validate()
        assert len(issues) >= 5

    def test_validate_mismatched_uuid(self, temp_dir):
        vault = Vault.init(temp_dir)
        vault_toml = Path(temp_dir) / ".metadata" / "vault.toml"
        doc = tomlkit.loads(vault_toml.read_text())
        doc["vault_uuid"] = "different-uuid"
        vault_toml.write_text(tomlkit.dumps(doc))
        issues = vault.validate()
        assert any("vault_uuid mismatch" in i for i in issues)

    def test_validate_mismatched_schema(self, temp_dir):
        vault = Vault.init(temp_dir)
        vault_toml = Path(temp_dir) / ".metadata" / "vault.toml"
        doc = tomlkit.loads(vault_toml.read_text())
        doc["schema_version"] = 999
        vault_toml.write_text(tomlkit.dumps(doc))
        issues = vault.validate()
        assert any("schema_version mismatch" in i for i in issues)

    def test_validate_corrupt_toml(self, temp_dir):
        vault = Vault.init(temp_dir)
        vault_toml = Path(temp_dir) / ".metadata" / "vault.toml"
        vault_toml.write_text("not [[valid toml\n")
        issues = vault.validate()
        assert any("Failed to parse" in i for i in issues)

    def test_init_nonempty_directory(self, temp_dir):
        Path(temp_dir, "existing.txt").touch()
        Vault.init(temp_dir)
        assert os.path.exists(os.path.join(temp_dir, ".metadata"))

    def test_init_writes_builtin_types(self, temp_dir):
        Vault.init(temp_dir)
        types_dir = Path(temp_dir) / ".metadata" / "types"
        expected = {"note.toml", "contact.toml", "bookmark.toml", "file.toml"}
        actual = {f.name for f in types_dir.iterdir() if f.suffix == ".toml"}
        missing = expected - actual
        assert not missing, f"Missing builtin type files: {missing}"
        assert "path.toml" not in actual, "path type should not be written during init"
        for name in expected:
            content = (types_dir / name).read_text()
            assert "name" in content, f"{name} should contain 'name' key"

    def test_init_types_are_parseable(self, temp_dir):
        Vault.init(temp_dir)
        from prism.types.loader import TypeLoader

        loader = TypeLoader(str(Path(temp_dir) / ".metadata" / "types"))
        types = loader.load_all()
        assert "note" in types
        assert "contact" in types
        assert "bookmark" in types
        assert "file" in types
        assert "path" not in types


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

    def test_get_by_uuid_not_found(self, registry):
        result = registry.get_by_uuid("nonexistent")
        assert result is None

    def test_get_by_path_not_found(self, registry):
        result = registry.get_by_path("/nonexistent")
        assert result is None

    def test_add_duplicate_path(self, registry):
        registry.add("uuid-1", "/path/to/vault")
        registry.add("uuid-2", "/path/to/vault")
        vaults = registry.list()
        assert len(vaults) == 1


class TestVaultContext:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_detect_with_flag(self, temp_dir):
        vault = Vault.init(temp_dir)
        detected = detect_vault("/some/other/dir", vault_flag=temp_dir)
        assert detected is not None
        assert detected.vault_uuid == vault.vault_uuid

    def test_detect_by_walk(self, temp_dir):
        vault = Vault.init(temp_dir)
        subdir = os.path.join(temp_dir, "a", "b", "c")
        os.makedirs(subdir)
        detected = detect_vault(subdir)
        assert detected is not None
        assert detected.vault_uuid == vault.vault_uuid

    def test_detect_no_vault(self):
        d = tempfile.mkdtemp()
        try:
            detected = detect_vault(d)
            assert detected is None
        finally:
            shutil.rmtree(d)
