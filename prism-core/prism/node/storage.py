import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

from prism.vault.vault import uuid_to_path


def sha256_file(path: str, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compute_storage_path(vault_path: str, uid: str) -> str:
    import uuid
    return os.path.join(vault_path, ".storage", uuid_to_path(uuid.UUID(uid)))


class StorageEngine:
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path

    def import_blob(self, source_path: str, uid: str) -> str:
        storage_dir = compute_storage_path(self.vault_path, uid)
        os.makedirs(storage_dir, exist_ok=True)
        ext = os.path.splitext(source_path)[1]
        dest = os.path.join(storage_dir, f"data{ext}")
        shutil.copy2(source_path, dest)
        return dest

    def delete_blob(self, uid: str) -> bool:
        storage_dir = compute_storage_path(self.vault_path, uid)
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)
            return True
        return False

    def read_blob(self, uid: str) -> Optional[bytes]:
        storage_dir = compute_storage_path(self.vault_path, uid)
        if not os.path.exists(storage_dir):
            return None
        for fname in os.listdir(storage_dir):
            if fname.startswith("data."):
                with open(os.path.join(storage_dir, fname), "rb") as f:
                    return f.read()
        return None

    def get_blob_path(self, uid: str) -> Optional[str]:
        storage_dir = compute_storage_path(self.vault_path, uid)
        if not os.path.exists(storage_dir):
            return None
        for fname in os.listdir(storage_dir):
            if fname.startswith("data."):
                return os.path.join(storage_dir, fname)
        return None

    def verify_integrity(self, uid: str, expected_hash: str) -> bool:
        blob_path = self.get_blob_path(uid)
        if blob_path is None:
            return False
        actual = sha256_file(blob_path)
        return actual == expected_hash
