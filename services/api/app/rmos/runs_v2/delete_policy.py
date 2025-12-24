"""
RMOS Delete Policy - H3.6 Safe Delete Modes

Provides policy enforcement for delete operations:
- Default mode (soft/hard) configurable via env
- Hard delete requires admin header + env allow
- Policy checks before any delete operation

Environment Variables:
    RMOS_DELETE_DEFAULT_MODE: soft|hard (default: soft)
    RMOS_DELETE_ALLOW_HARD: true|false (default: false)
    RMOS_DELETE_ADMIN_HEADER: header name (default: X-RMOS-Admin)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

DeleteMode = Literal["soft", "hard"]


@dataclass(frozen=True)
class DeletePolicy:
    """
    Delete policy configuration.

    Attributes:
        default_mode: Default delete mode when not specified
        allow_hard: Whether hard deletes are permitted at all
        admin_header_name: Header name for admin assertion
    """
    default_mode: DeleteMode
    allow_hard: bool
    admin_header_name: str


def _env_bool(name: str, default: bool) -> bool:
    """Parse boolean from environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "y")


def get_delete_policy() -> DeletePolicy:
    """
    Load delete policy from environment variables.

    Returns:
        DeletePolicy with safe defaults
    """
    default_mode = os.getenv("RMOS_DELETE_DEFAULT_MODE", "soft").strip().lower()
    if default_mode not in ("soft", "hard"):
        default_mode = "soft"

    allow_hard = _env_bool("RMOS_DELETE_ALLOW_HARD", False)
    admin_header = os.getenv("RMOS_DELETE_ADMIN_HEADER", "X-RMOS-Admin").strip()

    return DeletePolicy(
        default_mode=default_mode,  # type: ignore[arg-type]
        allow_hard=allow_hard,
        admin_header_name=admin_header or "X-RMOS-Admin",
    )


def is_admin_request(header_value: Optional[str]) -> bool:
    """
    Check if request has valid admin assertion.

    Args:
        header_value: Value of the admin header

    Returns:
        True if admin assertion is valid
    """
    if header_value is None:
        return False
    return header_value.strip().lower() in ("1", "true", "yes", "y", "admin")


def check_delete_allowed(
    mode: str,
    is_admin: bool,
    policy: DeletePolicy,
) -> Tuple[bool, str]:
    """
    Check if a delete operation is allowed by policy.

    Args:
        mode: Requested delete mode (soft/hard)
        is_admin: Whether request has admin header
        policy: Current delete policy

    Returns:
        Tuple of (allowed, reason). If allowed is False, reason explains why.
    """
    mode = mode.strip().lower()

    # Validate mode
    if mode not in ("soft", "hard"):
        return False, f"Invalid mode '{mode}'. Use 'soft' or 'hard'."

    # Soft delete is always allowed
    if mode == "soft":
        return True, ""

    # Hard delete requires both env allow and admin header
    if mode == "hard":
        if not policy.allow_hard:
            return False, "Hard delete disabled by policy (RMOS_DELETE_ALLOW_HARD=false)"
        if not is_admin:
            return False, f"Hard delete requires {policy.admin_header_name}: true header"
        return True, ""

    return False, "Unknown mode"


def resolve_effective_mode(
    requested_mode: Optional[str],
    policy: DeletePolicy,
) -> str:
    """
    Resolve the effective delete mode.

    Args:
        requested_mode: Mode from request (may be None)
        policy: Current delete policy

    Returns:
        Effective mode to use (soft or hard)
    """
    if requested_mode is None:
        return policy.default_mode

    mode = requested_mode.strip().lower()
    if mode in ("soft", "hard"):
        return mode

    return policy.default_mode
