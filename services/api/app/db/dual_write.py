from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DualWriteStore:
    """
    Writes to both SQLite (primary) and PostgreSQL (secondary).
    Reads always come from primary during dual-write period.
    PostgreSQL failures are logged but do not fail the request.

    Usage:
        store = DualWriteStore(sqlite_store, pg_store)
        await store.write(record)
        data = await store.read(key)  # reads from SQLite

    Cutover:
        Set store.primary = pg_store to switch reads to PostgreSQL.
        Keep dual-write running for 48 hours post-cutover.
    """

    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary
        self._dual_write_active = True

    async def write(self, record: Any) -> Any:
        result = await self.primary.write(record)
        if self._dual_write_active:
            try:
                await self.secondary.write(record)
            except Exception as e:
                logger.error(
                    "DualWrite: PostgreSQL write failed — "
                    "SQLite write succeeded. "
                    f"Record: {type(record).__name__}. "
                    f"Error: {e}",
                    exc_info=True,
                )
        return result

    async def read(self, key: Any) -> Any:
        return await self.primary.read(key)

    async def delete(self, key: Any) -> Any:
        result = await self.primary.delete(key)
        if self._dual_write_active:
            try:
                await self.secondary.delete(key)
            except Exception as e:
                logger.error(
                    f"DualWrite: PostgreSQL delete failed: {e}",
                    exc_info=True,
                )
        return result

    def switch_reads_to_secondary(self) -> None:
        """
        Call this after 5 days of verified dual-write parity.
        Switches reads to PostgreSQL while keeping dual-write active.
        """
        logger.warning(
            "DualWrite: Switching reads to PostgreSQL. "
            "SQLite writes continue for 48hr rollback window."
        )
        self.primary, self.secondary = self.secondary, self.primary

    def disable_dual_write(self) -> None:
        """
        Call after 48hr post-cutover verification.
        Disables secondary writes entirely.
        """
        logger.warning(
            "DualWrite: Disabling SQLite writes. "
            "PostgreSQL is now sole database."
        )
        self._dual_write_active = False


__all__ = ["DualWriteStore"]
