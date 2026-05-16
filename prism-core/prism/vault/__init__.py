"""Vault lifecycle package.

Exports: Vault, generate_uuid, uuid_to_path, VaultRegistry, detect_vault.
"""

from prism.vault.context import detect_vault
from prism.vault.registry import VaultRegistry
from prism.vault.vault import Vault, generate_uuid, uuid_to_path

__all__ = ["Vault", "generate_uuid", "uuid_to_path", "VaultRegistry", "detect_vault"]
