"""Append-only id ledger.

Publication writes an exclusive file per identifier. An aborted package write
still leaves the id burned, so a later call cannot reuse it.
"""

from __future__ import annotations

import os
from pathlib import Path


class LedgerError(Exception):
    """The ledger refused the identifier. Nothing was published."""


class WitnessRepository:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def burn(self, identifier: str) -> None:
        self._exclusive(self.root / "burned" / identifier)

    def publish(self, identifier: str, package: Path, supersedes: str | None) -> None:
        burned = self.root / "burned" / identifier
        if not burned.is_file():
            raise LedgerError(f"identifier was not burned before publication: {identifier}")
        body = f"package={package}\nsupersedes={supersedes or ''}\n"
        self._exclusive(self.root / "published" / identifier, body)

    def published_path(self, identifier: str) -> Path | None:
        path = self.root / "published" / identifier
        if not path.is_file():
            return None
        return path

    def _exclusive(self, path: Path, body: str = "") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise LedgerError(f"identifier already used: {path.name}") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
