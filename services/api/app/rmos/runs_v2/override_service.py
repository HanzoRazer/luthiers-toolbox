"""
RMOS Override Service - YELLOW Unlock Logic

Implements the override primitive for unlocking YELLOW-blocked runs.
RED override requires explicit environment flag.

Key invariants:
- Original decision.risk_level is NEVER modified (history authoritative)
- Override is content-addressed and immutable
- Every override creates an audit trail attachment
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4

from .schemas import RunArtifact
from .schemas_override import (
    OverrideRequest,
    OverrideRecord,
    OverrideMetaUpdate,
    OverrideResponse,
)
from .attachments import put_json_attachment
from .store import get_run, update_run


# =============================================================================
# Configuration
# =============================================================================

def _allow_red_override() -> bool:
    """Check if RED override is allowed via environment flag."""
    val = os.getenv("RMOS_ALLOW_RED_OVERRIDE", "").strip().lower()
    return val in ("1", "true", "yes")


# =============================================================================
# Error Classes
# =============================================================================

class OverrideError(Exception):
    """Base override error."""

    def __init__(self, message: str, code: str, **context):
        self.message = message
        self.code = code
        self.context = context
        super().__init__(message)


class RunNotFoundError(OverrideError):
    """Run does not exist."""

    def __init__(self, run_id: str):
        super().__init__(
            f"Run not found: {run_id}",
            "RUN_NOT_FOUND",
            run_id=run_id,
        )


class NotBlockedError(OverrideError):
    """Run is not blocked (nothing to override)."""

    def __init__(self, run_id: str, status: str):
        super().__init__(
            f"Run {run_id} is not blocked (status={status})",
            "NOT_BLOCKED",
            run_id=run_id,
            status=status,
        )


class AlreadyOverriddenError(OverrideError):
    """Run was already overridden."""

    def __init__(self, run_id: str, existing_override_id: str):
        super().__init__(
            f"Run {run_id} already has override: {existing_override_id}",
            "ALREADY_OVERRIDDEN",
            run_id=run_id,
            existing_override_id=existing_override_id,
        )


class RedOverrideNotAllowedError(OverrideError):
    """RED override attempted but not enabled."""

    def __init__(self, run_id: str):
        super().__init__(
            f"RED override not allowed for run {run_id}. Set RMOS_ALLOW_RED_OVERRIDE=1 to enable.",
            "RED_OVERRIDE_DISABLED",
            run_id=run_id,
        )


class RiskMismatchError(OverrideError):
    """Override scope doesn't match run risk level."""

    def __init__(self, run_id: str, scope: str, actual_risk: str):
        super().__init__(
            f"Override scope={scope} doesn't match risk_level={actual_risk}",
            "RISK_MISMATCH",
            run_id=run_id,
            scope=scope,
            actual_risk=actual_risk,
        )


class AcknowledgmentRequiredError(OverrideError):
    """RED override requires explicit acknowledgment."""

    def __init__(self, run_id: str):
        super().__init__(
            f"RED override for {run_id} requires acknowledge_risk=true",
            "ACKNOWLEDGMENT_REQUIRED",
            run_id=run_id,
        )


# =============================================================================
# Core Override Logic
# =============================================================================

def validate_override_preconditions(
    run: RunArtifact,
    request: OverrideRequest,
) -> None:
    """
    Validate that override can proceed.

    Raises:
        NotBlockedError: Run is not blocked
        AlreadyOverriddenError: Run already has an override
        RedOverrideNotAllowedError: RED override attempted without env flag
        RiskMismatchError: Scope doesn't match risk level
        AcknowledgmentRequiredError: RED override without acknowledgment
    """
    run_id = run.run_id
    risk_level = run.decision.risk_level.upper() if run.decision else "UNKNOWN"
    status = run.status.upper() if run.status else "UNKNOWN"

    # 1. Must be BLOCKED
    if status != "BLOCKED":
        raise NotBlockedError(run_id, status)

    # 2. Check for existing override
    existing_override = (run.meta or {}).get("override")
    if existing_override:
        raise AlreadyOverriddenError(run_id, existing_override.get("override_id", "unknown"))

    # 3. Scope must match risk level
    if request.scope == "YELLOW" and risk_level not in ("YELLOW", "UNKNOWN"):
        if risk_level == "RED":
            raise RiskMismatchError(run_id, "YELLOW", risk_level)
    if request.scope == "RED" and risk_level != "RED":
        raise RiskMismatchError(run_id, "RED", risk_level)

    # 4. RED override policy
    if request.scope == "RED":
        if not _allow_red_override():
            raise RedOverrideNotAllowedError(run_id)
        if not request.acknowledge_risk:
            raise AcknowledgmentRequiredError(run_id)


def create_override_record(
    run: RunArtifact,
    request: OverrideRequest,
    operator_id: str,
    operator_name: Optional[str] = None,
    request_id: Optional[str] = None,
) -> OverrideRecord:
    """Create the override record for content-addressed storage."""
    return OverrideRecord(
        override_id=uuid4().hex,
        run_id=run.run_id,
        operator_id=operator_id,
        operator_name=operator_name,
        scope=request.scope,
        reason=request.reason,
        acknowledged_risk=request.acknowledge_risk,
        original_risk_level=run.decision.risk_level if run.decision else "UNKNOWN",
        original_status=run.status,
        request_id=request_id,
    )


def apply_override(
    run_id: str,
    request: OverrideRequest,
    operator_id: str,
    operator_name: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Tuple[OverrideResponse, RunArtifact]:
    """
    Apply an override to a blocked run.

    Args:
        run_id: Run to override
        request: Override request with reason and scope
        operator_id: Who is performing the override
        operator_name: Display name (optional)
        request_id: Correlation ID for audit

    Returns:
        Tuple of (OverrideResponse, updated RunArtifact)

    Raises:
        RunNotFoundError: Run doesn't exist
        NotBlockedError: Run is not blocked
        AlreadyOverriddenError: Already has override
        RedOverrideNotAllowedError: RED override not enabled
        RiskMismatchError: Scope doesn't match risk
        AcknowledgmentRequiredError: RED without acknowledgment
    """
    # 1. Load run
    run = get_run(run_id)
    if not run:
        raise RunNotFoundError(run_id)

    # 2. Validate preconditions
    validate_override_preconditions(run, request)

    # 3. Create override record
    record = create_override_record(
        run=run,
        request=request,
        operator_id=operator_id,
        operator_name=operator_name,
        request_id=request_id,
    )

    # 4. Store as content-addressed attachment
    record_dict = record.model_dump(mode="json")
    record_dict["created_at_utc"] = record.created_at_utc.isoformat()

    attachment, attachment_path = put_json_attachment(
        data=record_dict,
        kind="override",
        filename=f"override_{record.override_id}.json",
        run_id=run_id,
    )

    # 5. Update run meta with override reference
    meta_update = OverrideMetaUpdate(
        override_id=record.override_id,
        by=operator_id,
        reason=request.reason,
        scope=request.scope,
        at_utc=record.created_at_utc.isoformat(),
        attachment_sha256=attachment.sha256,
    )

    # Determine new status
    # YELLOW overrides → OK
    # RED overrides → OK (if allowed)
    new_status = "OK"

    # Update the run
    # Note: We mutate meta only, preserving decision.risk_level
    updated_meta = dict(run.meta) if run.meta else {}
    updated_meta["override"] = meta_update.model_dump(mode="json")

    # Also append to attachments list
    attachments = list(run.attachments) if run.attachments else []
    attachments.append(attachment)

    # Create updated run (preserving all authoritative fields)
    run_copy = run.model_copy(
        update={
            "status": new_status,
            "meta": updated_meta,
            "attachments": attachments,
        }
    )

    # Persist
    update_run(run_copy)

    # 6. Return response
    response = OverrideResponse(
        run_id=run_id,
        override_id=record.override_id,
        new_status=new_status,
        attachment_sha256=attachment.sha256,
        message=f"Override applied: {request.scope} run unlocked by {operator_id}",
    )

    return response, run_copy


def get_override_info(run: RunArtifact) -> Optional[OverrideMetaUpdate]:
    """
    Get override info from a run if present.

    Returns None if run has no override.
    """
    if not run.meta:
        return None
    override_data = run.meta.get("override")
    if not override_data:
        return None
    try:
        return OverrideMetaUpdate.model_validate(override_data)
    except (ValueError, TypeError):  # WP-1: narrowed from except Exception
        return None


def is_overridden(run: RunArtifact) -> bool:
    """Check if a run has been overridden."""
    return get_override_info(run) is not None
