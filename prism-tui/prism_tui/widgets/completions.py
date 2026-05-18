from __future__ import annotations

import os
from typing import Protocol


class PathCompleter(Protocol):
    """Protocol for path completion strategies."""

    def complete(self, partial: str) -> list[str]:
        """Return matching paths for the given partial input."""
        ...


class FilesystemCompleter:
    """Completes filesystem paths using os.listdir."""

    def complete(self, partial: str) -> list[str]:
        expanded = os.path.expanduser(partial)
        dirname, basename = os.path.split(expanded)
        if not dirname:
            dirname = "."
        try:
            entries = os.listdir(dirname)
        except OSError:
            return []
        matches: list[str] = []
        for entry in entries:
            if entry.startswith(basename):
                full = os.path.join(dirname, entry)
                if os.path.isdir(full):
                    matches.append(os.path.join(dirname, entry) + "/")
                else:
                    matches.append(os.path.join(dirname, entry))
        if partial.startswith("/"):
            return [
                os.path.normpath(m) + "/" if m.endswith("/") else os.path.normpath(m)
                for m in matches
            ]
        return matches
