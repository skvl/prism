import os
from pathlib import Path
from typing import Optional

from prism.vault.vault import Vault


def detect_vault(cwd: str, vault_flag: Optional[str] = None) -> Optional[Vault]:
    if vault_flag:
        return Vault.open(vault_flag)

    path = Path(cwd).resolve()
    for parent in [path] + list(path.parents):
        vault_toml = parent / ".metadata" / "vault.toml"
        if vault_toml.exists():
            return Vault.open(str(parent))

    return None
