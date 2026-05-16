"""Vault registry management.

Persistent registry of known vaults stored in ~/.config/prism/vaults.toml.
"""

from pathlib import Path
from typing import Optional

import tomlkit

REGISTRY_PATH = Path.home() / ".config" / "prism" / "vaults.toml"


class VaultRegistry:
    """Manages the persistent registry of known vaults.

    Stores vault entries in ~/.config/prism/vaults.toml with add,
    remove, list, and lookup operations.
    """
    def __init__(self) -> None:
        """Initialize the registry, ensuring the config directory exists."""
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
        """Register a vault in the registry.

        Args:
            vault_uuid: UUID of the vault.
            path: Filesystem path to the vault.
            name: Optional human-readable name.
        """
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
        """Remove a vault from the registry by path.

        Args:
            path: Filesystem path of the vault to remove.

        Returns:
            True if the vault was removed, False if not found.
        """
        self._load()
        before = len(self._vaults)
        self._vaults = [v for v in self._vaults if v["path"] != path]
        if len(self._vaults) < before:
            self._save()
            return True
        return False

    def list(self) -> list[dict[str, str]]:
        """List all registered vaults.

        Returns:
            List of vault dicts with uuid and path keys.
        """
        self._load()
        return list(self._vaults)

    def get_by_uuid(self, vault_uuid: str) -> Optional[dict[str, str]]:
        """Look up a vault by its UUID.

        Args:
            vault_uuid: UUID to search for.

        Returns:
            Vault dict or None if not found.
        """
        self._load()
        for v in self._vaults:
            if v["uuid"] == vault_uuid:
                return dict(v)
        return None

    def get_by_path(self, path: str) -> Optional[dict[str, str]]:
        """Look up a vault by its filesystem path.

        Args:
            path: Filesystem path to search for.

        Returns:
            Vault dict or None if not found.
        """
        self._load()
        for v in self._vaults:
            if v["path"] == path:
                return dict(v)
        return None
