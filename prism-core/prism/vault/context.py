"""Vault context detection.

Walks up from a directory to find the nearest vault.
"""

import os
from pathlib import Path
from typing import Optional

from prism.vault.vault import Vault


def detect_vault(cwd: str, vault_flag: Optional[str] = None) -> Optional[Vault]:
    """Detect a vault by walking up from the given directory.

    Args:
        cwd: Current working directory to start searching from.
        vault_flag: Optional explicit vault path override.

    Returns:
        A Vault instance or None if no vault is found.
    """
    if vault_flag:
        return Vault.open(vault_flag)

    path = Path(cwd).resolve()
    for parent in [path] + list(path.parents):
        vault_toml = parent / ".metadata" / "vault.toml"
        if vault_toml.exists():
            return Vault.open(str(parent))

    return None
