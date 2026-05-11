import os
from pathlib import Path
from typing import Optional

import tomlkit


REGISTRY_PATH = Path.home() / ".config" / "prism" / "vaults.toml"


class VaultRegistry:
    def __init__(self) -> None:
        self._ensure_config_dir()
        self._vaults: list[dict[str, str]] = []
        self._load()

    def _ensure_config_dir(self) -> None:
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        if not REGISTRY_PATH.exists():
            self._vaults = []
            return
        with open(REGISTRY_PATH) as f:
            doc = tomlkit.load(f)
        self._vaults = list(doc.get("vault", []))

    def _save(self) -> None:
        doc = tomlkit.document()
        arr = tomlkit.array()
        for v in self._vaults:
            tbl = tomlkit.inline_table()
            tbl.update(v)
            arr.append(tbl)
        arr.multiline(True)
        doc["vault"] = arr
        with open(REGISTRY_PATH, "w") as f:
            tomlkit.dump(doc, f)

    def add(self, vault_uuid: str, path: str, name: Optional[str] = None) -> None:
        self._load()
        for v in self._vaults:
            if v["path"] == path:
                return
        entry: dict[str, str] = {"uuid": vault_uuid, "path": path}
        if name:
            entry["name"] = name
        self._vaults.append(entry)
        self._save()

    def remove(self, path: str) -> bool:
        self._load()
        before = len(self._vaults)
        self._vaults = [v for v in self._vaults if v["path"] != path]
        if len(self._vaults) < before:
            self._save()
            return True
        return False

    def list(self) -> list[dict[str, str]]:
        self._load()
        return list(self._vaults)

    def get_by_uuid(self, vault_uuid: str) -> Optional[dict[str, str]]:
        self._load()
        for v in self._vaults:
            if v["uuid"] == vault_uuid:
                return dict(v)
        return None

    def get_by_path(self, path: str) -> Optional[dict[str, str]]:
        self._load()
        for v in self._vaults:
            if v["path"] == path:
                return dict(v)
        return None
