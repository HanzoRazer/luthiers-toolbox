"""Errors raised by the shop-operation record and its repository."""
from __future__ import annotations


class OperationRecordError(ValueError):
    """The record is not valid. Nothing was written.

    ``code`` is set when a refusal needs a stable name. Other failures leave it
    ``None`` and keep the message as the contract.
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class OperationRepositoryError(RuntimeError):
    """The store could not accept or reread a record."""


class OperationRecordNotFound(OperationRepositoryError):
    """No record with this id is stored."""


class DuplicateOperationRecord(OperationRepositoryError):
    """This record id is already stored with different bytes."""


class OperationSequenceError(OperationRepositoryError):
    """The event does not follow from the operation's stored history."""
