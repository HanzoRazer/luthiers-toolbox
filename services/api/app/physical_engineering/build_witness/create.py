"""Create a blank witness package with exclusive ownership of the destination.

Sequence:

1. Refuse at once if the destination exists (fast path; not relied on).
2. Reserve the destination: ``os.mkdir`` of ``.<name>.reservation`` beside
   it. ``mkdir`` is atomic and exclusive, so exactly one creator holds it.
3. Holding the reservation, re-check that the destination does not exist,
   then burn the identifiers.
4. Write the blank package into a uniquely named staging directory.
5. Publish with one ``os.rename`` of the staging directory to the
   destination, still holding the reservation.
6. Always remove the staging directory and the reservation.

An existing destination is never written into or replaced, even if empty.
A reservation left by a crashed creator is not taken over: the next creator
fails with the reservation's path and the instruction to remove it once no
creator is running. An interrupted creator leaves no destination, so there
is nothing to publish.
"""

from __future__ import annotations

import os
import shutil
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from app.physical_engineering.build_witness import templates
from app.physical_engineering.build_witness.findings import PackageError
from app.physical_engineering.build_witness.ids import new_id
from app.physical_engineering.build_witness.repository import (
    LedgerError,
    WitnessRepository,
)

_INSTRUMENT = __import__("re").compile(r"^[a-z][a-z0-9_]{0,63}$")


def reservation_path(dest: Path) -> Path:
    return dest.with_name(f".{dest.name}.reservation")


def _after_destination_check() -> None:
    """Test hook: the point where two creators could both have seen no destination."""


def _after_reservation() -> None:
    """Test hook: the reservation is held and nothing has been written yet."""


def _before_publish(staging: Path) -> None:
    """Test hook: the staging package is complete and not yet published."""


def create_package(
    dest: Path,
    instrument_type: str,
    repository: WitnessRepository,
    *,
    clock: Callable[[], datetime] | None = None,
    factory: Callable[[], str] | None = None,
    supersedes: str | None = None,
) -> str:
    if not isinstance(instrument_type, str) or _INSTRUMENT.fullmatch(instrument_type) is None:
        raise PackageError("instrument type must be a lowercase token")
    dest = Path(dest)
    if dest.exists() or dest.is_symlink():
        raise PackageError("destination collision: the destination already exists")
    if _is_inside(repository.root, dest) or _is_inside(dest, repository.root):
        raise PackageError("the ledger and the package must be different directories")
    _after_destination_check()
    reservation = _reserve(dest)
    staging = dest.with_name(f".{dest.name}.staging-{uuid.uuid4().hex}")
    try:
        _after_reservation()
        if dest.exists() or dest.is_symlink():
            raise PackageError("destination collision: the destination already exists")
        witness_id = _stage(staging, instrument_type, repository, clock, factory, supersedes)
        _before_publish(staging)
        if dest.exists() or dest.is_symlink():
            raise PackageError("destination collision: the destination already exists")
        try:
            os.rename(staging, dest)
        except OSError as exc:
            raise PackageError("destination collision: the destination appeared during publication") from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(reservation, ignore_errors=True)
    try:
        repository.publish(witness_id, dest, supersedes)
    except LedgerError as exc:
        raise PackageError(str(exc)) from exc
    return witness_id


def _reserve(dest: Path) -> Path:
    reservation = reservation_path(dest)
    try:
        os.mkdir(reservation)
    except FileExistsError as exc:
        raise PackageError(
            f"destination collision: {reservation} is held by another creator. "
            "If no creator is running, a previous run was interrupted: confirm the destination "
            "does not exist, remove that reservation directory, and retry"
        ) from exc
    except OSError as exc:
        raise PackageError(f"cannot reserve the destination: {exc}", 3) from exc
    (reservation / "owner").write_text(f"pid={os.getpid()}\n", encoding="utf-8")
    return reservation


def _stage(
    staging: Path,
    instrument_type: str,
    repository: WitnessRepository,
    clock: Callable[[], datetime] | None,
    factory: Callable[[], str] | None,
    supersedes: str | None,
) -> str:
    """Burn the identifiers and write the blank package into ``staging``."""
    witness_id = new_id("witness", clock, factory)
    build_id = new_id("build", clock, factory)
    session_id = new_id("session", clock, factory)
    for identifier in (witness_id, build_id, session_id):
        try:
            repository.burn(identifier)
        except LedgerError as exc:
            raise PackageError(str(exc)) from exc
    record = templates.build_record(witness_id, build_id, session_id, instrument_type)
    record["supersedes_witness_id"] = supersedes
    staging.mkdir()
    templates.write_blank_tree(staging, record, templates.test_protocol(session_id), templates.equipment())
    return witness_id


def _is_inside(parent: Path, child: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True
