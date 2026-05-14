"""Blob storage engine and hash utilities.

Provides StorageEngine for importing, reading, verifying blobs,
plus sha256_file and compute_storage_path helpers.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

from prism.vault.vault import uuid_to_path


def sha256_file(path: str, chunk_size: int = 65536) -> str:
    """Compute the SHA-256 hash of a file.

    Args:
        path: Path to the file.
        chunk_size: Read chunk size in bytes.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compute_storage_path(vault_path: str, uid: str) -> str:
    """Compute the partitioned storage directory for a node.

    Args:
        vault_path: Root path of the vault.
        uid: UUID string of the node.

    Returns:
        Full path to the node's storage directory.
    """
    import uuid
    return os.path.join(vault_path, ".storage", uuid_to_path(uuid.UUID(uid)))


class StorageEngine:
    """Manages blob import, read, delete, and integrity verification."""

    def __init__(self, vault_path: str) -> None:
        """Initialize the storage engine.

        Args:
            vault_path: Root path of the vault.
        """
        self.vault_path = vault_path

    def import_blob(self, source_path: str, uid: str) -> str:
        """Import a file as a blob into the storage directory.

        Args:
            source_path: Path to the source file.
            uid: UUID of the destination node.

        Returns:
            Path to the imported blob.
        """
        storage_dir = compute_storage_path(self.vault_path, uid)
        os.makedirs(storage_dir, exist_ok=True)
        ext = os.path.splitext(source_path)[1]
        dest = os.path.join(storage_dir, f"data{ext}")
        shutil.copy2(source_path, dest)
        return dest

    def delete_blob(self, uid: str) -> bool:
        """Delete the blob storage directory for a node.

        Args:
            uid: UUID of the node.

        Returns:
            True if deleted, False if not found.
        """
        storage_dir = compute_storage_path(self.vault_path, uid)
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)
            return True
        return False

    def read_blob(self, uid: str) -> Optional[bytes]:
        """Read the blob data for a node.

        Args:
            uid: UUID of the node.

        Returns:
            Bytes of the blob, or None if not found.
        """
        storage_dir = compute_storage_path(self.vault_path, uid)
        if not os.path.exists(storage_dir):
            return None
        for fname in os.listdir(storage_dir):
            if fname.startswith("data."):
                with open(os.path.join(storage_dir, fname), "rb") as f:
                    return f.read()
        return None

    def get_blob_path(self, uid: str) -> Optional[str]:
        """Get the filesystem path to a node's blob.

        Args:
            uid: UUID of the node.

        Returns:
            Path to the blob file, or None if not found.
        """
        storage_dir = compute_storage_path(self.vault_path, uid)
        if not os.path.exists(storage_dir):
            return None
        for fname in os.listdir(storage_dir):
            if fname.startswith("data."):
                return os.path.join(storage_dir, fname)
        return None

    def verify_integrity(self, uid: str, expected_hash: str) -> bool:
        """Verify a blob's SHA-256 hash matches the expected value.

        Args:
            uid: UUID of the node.
            expected_hash: Expected SHA-256 digest.

        Returns:
            True if hash matches, False otherwise.
        """
        blob_path = self.get_blob_path(uid)
        if blob_path is None:
            return False
        actual = sha256_file(blob_path)
        return actual == expected_hash
