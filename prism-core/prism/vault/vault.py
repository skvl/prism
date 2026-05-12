import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import tomlkit

from prism import VERSION


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def uuid_to_path(uid: uuid.UUID) -> str:
    hex_str = uid.hex
    return os.path.join(hex_str[0:4], hex_str[4:8], hex_str[8:12], hex_str[12:])


VAULT_TOML_FIELDS = {
    "vault_uuid": {"type": "string", "required": True},
    "schema_version": {"type": "integer", "required": True},
    "created_at": {"type": "string", "required": True},
}


class Vault:
    def __init__(self, path: str, vault_uuid: str, schema_version: int, created_at: str, path_root_uuid: str = "") -> None:
        self.path = path
        self.vault_uuid = vault_uuid
        self.schema_version = schema_version
        self.created_at = created_at
        self.path_root_uuid = path_root_uuid

    @classmethod
    def init(cls, path: str) -> "Vault":
        vault_path = Path(path).resolve()
        metadata_dir = vault_path / ".metadata"
        storage_dir = vault_path / ".storage"

        vault_toml_path = metadata_dir / "vault.toml"
        if vault_toml_path.exists():
            raise FileExistsError("Vault already exists at this location")

        if vault_path.exists() and any(vault_path.iterdir()):
            print("Warning: directory is not empty. Existing files are not managed.")

        metadata_dir.mkdir(parents=True, exist_ok=True)
        (metadata_dir / "types").mkdir(parents=True, exist_ok=True)
        storage_dir.mkdir(parents=True, exist_ok=True)
        (metadata_dir / "index.txt").touch()

        vault_uuid = str(generate_uuid())
        now = datetime.now(timezone.utc).isoformat()
        doc = tomlkit.document()
        doc["vault_uuid"] = vault_uuid
        doc["schema_version"] = 1
        doc["created_at"] = now
        doc["prism_version"] = VERSION

        root_uid = str(generate_uuid())
        doc["path_root_uuid"] = root_uid

        with open(vault_toml_path, "w") as f:
            tomlkit.dump(doc, f)

        root_storage_dir = storage_dir / uuid_to_path(uuid.UUID(root_uid))
        root_storage_dir.mkdir(parents=True, exist_ok=True)
        root_meta = tomlkit.document()
        root_meta["uuid"] = root_uid
        root_meta["type"] = "path"
        root_meta["title"] = "/"
        root_meta["created_at"] = now
        root_meta["updated_at"] = now
        root_meta["sync_dirty"] = True
        fields_tbl = tomlkit.table()
        fields_tbl["name"] = "/"
        root_meta["fields"] = fields_tbl
        root_meta_path = root_storage_dir / "metadata.toml"
        with open(root_meta_path, "w") as f:
            tomlkit.dump(root_meta, f)

        return cls(str(vault_path), vault_uuid, 1, now, path_root_uuid=root_uid)

    @classmethod
    def open(cls, path: str) -> "Vault":
        vault_path = Path(path).resolve()
        vault_toml_path = vault_path / ".metadata" / "vault.toml"
        if not vault_toml_path.exists():
            raise FileNotFoundError("No vault found. Run `prism init` to create one.")

        with open(vault_toml_path) as f:
            doc = tomlkit.load(f)

        return cls(
            str(vault_path),
            doc["vault_uuid"],
            doc["schema_version"],
            doc["created_at"],
            path_root_uuid=doc.get("path_root_uuid", ""),
        )

    def validate(self) -> list[str]:
        issues: list[str] = []
        vault_path = Path(self.path)
        metadata_dir = vault_path / ".metadata"
        storage_dir = vault_path / ".storage"

        if not metadata_dir.exists():
            issues.append("Missing .metadata/ directory")
        if not storage_dir.exists():
            issues.append("Missing .storage/ directory")
        if not (metadata_dir / "types").exists():
            issues.append("Missing .metadata/types/ directory")
        if not (metadata_dir / "index.txt").exists():
            issues.append("Missing .metadata/index.txt")
        if not (metadata_dir / "vault.toml").exists():
            issues.append("Missing .metadata/vault.toml")
        else:
            try:
                with open(metadata_dir / "vault.toml") as f:
                    doc = tomlkit.load(f)
                if doc.get("vault_uuid") != self.vault_uuid:
                    issues.append("vault_uuid mismatch in vault.toml")
                if doc.get("schema_version") != self.schema_version:
                    issues.append("schema_version mismatch in vault.toml")
            except Exception:
                issues.append("Failed to parse vault.toml")

        return issues
