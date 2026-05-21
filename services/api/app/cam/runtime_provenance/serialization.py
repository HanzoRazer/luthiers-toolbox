"""
Stable Serialization Helpers.

Sprint: MRP-5N
Status: PROTOTYPE

Provides deterministic serialization and hashing for runtime provenance.
These helpers ensure reproducible artifact hashing and trace comparison.

ARCHITECTURAL PRINCIPLE:
    Stable serialization is infrastructure.
    It must be deterministic and reproducible across runs.
"""

import hashlib
import json
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, Union
from uuid import UUID


def _default_serializer(obj: Any) -> Any:
    """
    Default serializer for non-JSON-native types.

    Handles common types that json.dumps cannot serialize natively.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, bytes):
        return obj.hex()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def stable_json_dumps(data: Any, indent: int = None) -> str:
    """
    Serialize data to canonical JSON string.

    Uses sorted keys and compact separators for deterministic output.
    The same input will always produce the same output string.

    Args:
        data: Data to serialize
        indent: Optional indentation for human readability (default: compact)

    Returns:
        Canonical JSON string
    """
    if indent is not None:
        return json.dumps(
            data,
            sort_keys=True,
            indent=indent,
            default=_default_serializer,
            ensure_ascii=False,
        )
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=_default_serializer,
        ensure_ascii=False,
    )


def stable_json_loads(json_str: str) -> Any:
    """
    Parse JSON string.

    Wrapper for json.loads for consistency with stable_json_dumps.
    """
    return json.loads(json_str)


def stable_hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """
    Compute hash of byte content.

    Args:
        data: Bytes to hash
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex digest of hash
    """
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(data).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(data).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def stable_hash_string(data: str, algorithm: str = "sha256") -> str:
    """
    Compute hash of string content.

    Encodes string as UTF-8 before hashing.

    Args:
        data: String to hash
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex digest of hash
    """
    return stable_hash_bytes(data.encode("utf-8"), algorithm)


def stable_hash_model(data: Any, algorithm: str = "sha256") -> str:
    """
    Compute hash of any serializable data.

    Serializes to canonical JSON, then hashes.

    Args:
        data: Data to hash (must be JSON-serializable)
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex digest of hash
    """
    json_str = stable_json_dumps(data)
    return stable_hash_string(json_str, algorithm)


def stable_hash_short(data: Any, length: int = 16) -> str:
    """
    Compute truncated hash for display/logging.

    Args:
        data: Data to hash
        length: Number of hex characters to return (default: 16)

    Returns:
        Truncated hex digest
    """
    full_hash = stable_hash_model(data)
    return full_hash[:length]


def stable_dict_from_object(obj: Any) -> Dict[str, Any]:
    """
    Convert object to stable dictionary representation.

    Handles objects with to_dict(), __dict__, or dict() methods.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation
    """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    raise TypeError(f"Cannot convert {type(obj).__name__} to dictionary")


def verify_hash_match(
    data: Union[bytes, str, Any],
    expected_hash: str,
    algorithm: str = "sha256",
) -> bool:
    """
    Verify that data matches expected hash.

    Args:
        data: Data to verify (bytes, string, or serializable object)
        expected_hash: Expected hash value
        algorithm: Hash algorithm (default: sha256)

    Returns:
        True if hashes match
    """
    if isinstance(data, bytes):
        actual_hash = stable_hash_bytes(data, algorithm)
    elif isinstance(data, str):
        actual_hash = stable_hash_string(data, algorithm)
    else:
        actual_hash = stable_hash_model(data, algorithm)

    return actual_hash == expected_hash
