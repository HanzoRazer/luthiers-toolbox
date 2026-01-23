"""
Advisory Request Service

Core business logic for the advisory request workflow.

Flow:
1. Validate AIContextPacket schema
2. Invoke ai-integrator CLI
3. Validate AdvisoryDraft schema
4. Create AdvisoryArtifact with provenance
5. Persist to ledger
6. Return advisory_id
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import ValidationError

from .exceptions import AiIntegratorError, AiIntegratorSchema
from .hashing import sha256_canonical_json
from .runner import run_ai_integrator_job
from .schemas import (
    AdvisoryArtifactEngine,
    AdvisoryArtifactGovernance,
    AdvisoryArtifactInput,
    AdvisoryArtifactV1,
    AdvisoryDraftV1,
    AdvisoryRequestResponse,
    AIContextPacketV1,
)
from .store import persist_advisory

logger = logging.getLogger(__name__)


def _utc_now_rfc3339() -> str:
    """Get current UTC time as RFC3339 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _create_advisory_id() -> str:
    """Generate a unique advisory ID."""
    return f"adv_{uuid.uuid4().hex[:16]}"


def request_advisory(
    packet: dict,
    *,
    user_id: Optional[str] = None,
) -> AdvisoryRequestResponse:
    """
    Process an advisory request from ToolBox.

    Args:
        packet: The AIContextPacket dict
        user_id: Optional requesting user ID for audit

    Returns:
        AdvisoryRequestResponse with advisory_id

    Raises:
        AiIntegratorSchema: If input/output schema validation fails
        AiIntegratorGovernance: If governance check fails
        AiIntegratorRuntime: If CLI execution fails
        AiIntegratorUnsupported: If job/template is unsupported
    """
    # 1. Validate input schema
    try:
        validated_packet = AIContextPacketV1.model_validate(packet)
    except ValidationError as e:
        logger.warning(f"Invalid AIContextPacket: {e}")
        raise AiIntegratorSchema(
            f"Invalid AIContextPacket schema: {e.error_count()} errors",
            exit_code=1,
        ) from e

    # Additional v1 constraint: only 'explanation' supported
    if validated_packet.request.kind != "explanation":
        raise AiIntegratorSchema(
            f"Unsupported request kind '{validated_packet.request.kind}' in v1. "
            "Only 'explanation' is supported.",
            exit_code=1,
        )

    # 2. Invoke ai-integrator CLI
    logger.info(
        f"Invoking ai-integrator for {validated_packet.request.kind} "
        f"template={validated_packet.request.template_id}"
    )

    draft_dict = run_ai_integrator_job(packet)

    # 3. Validate output schema
    try:
        draft = AdvisoryDraftV1.model_validate(draft_dict)
    except ValidationError as e:
        logger.error(f"ai-integrator produced invalid AdvisoryDraft: {e}")
        raise AiIntegratorSchema(
            f"Invalid AdvisoryDraft schema from ai-integrator: {e.error_count()} errors",
            exit_code=1,
        ) from e

    # 4. Create advisory artifact with provenance
    advisory_id = _create_advisory_id()
    created_at = _utc_now_rfc3339()

    # Compute provenance hashes
    context_packet_sha256 = sha256_canonical_json(packet)
    evidence_bundle_sha256 = validated_packet.evidence.bundle_sha256

    artifact = AdvisoryArtifactV1(
        schema_id="rmos_advisory_artifact_v1",
        advisory_id=advisory_id,
        created_at_utc=created_at,
        input=AdvisoryArtifactInput(
            context_packet_sha256=context_packet_sha256,
            evidence_bundle_sha256=evidence_bundle_sha256,
        ),
        engine=AdvisoryArtifactEngine(
            model_id=draft.model.id,
            template_id=draft.template.id,
            template_version=draft.template.version,
        ),
        draft=draft,
        governance=AdvisoryArtifactGovernance(
            status="draft",
            published_by=None,
            notes=f"Requested by user: {user_id}" if user_id else None,
        ),
    )

    # 5. Persist to ledger
    artifact_path = persist_advisory(artifact)
    logger.info(f"Persisted advisory artifact: {artifact_path}")

    # 6. Return handle
    return AdvisoryRequestResponse(
        ok=True,
        advisory_id=advisory_id,
        status="draft",
        message=None,
    )
