from __future__ import annotations

from typing import Any

from .cbsp21_patch_adapter import CBSP21PacketError, validate_behavior_change_articulation
from .execution_planner import SUPPORTED_RISK_LEVELS
from .repository_proposal_evaluation import (
    EvaluationFinding,
    FINDING_CATEGORY_GOVERNANCE,
    FINDING_STATUS_FAIL,
    FINDING_STATUS_NOT_APPLICABLE,
    FINDING_STATUS_PASS,
)


def declared_risk_finding(packet: Any, packet_readable: bool) -> EvaluationFinding:
    if not packet_readable:
        return EvaluationFinding(
            check_id="governance.declared_risk_supported",
            category=FINDING_CATEGORY_GOVERNANCE,
            status=FINDING_STATUS_FAIL,
            detail="cbsp21_packet is not readable, so declared risk_level cannot be read",
        )

    declared_risk = str(packet.get("risk_level", "")).strip().lower()
    return EvaluationFinding(
        check_id="governance.declared_risk_supported",
        category=FINDING_CATEGORY_GOVERNANCE,
        status=FINDING_STATUS_PASS if declared_risk in SUPPORTED_RISK_LEVELS else FINDING_STATUS_FAIL,
        detail=f"declared risk_level={packet.get('risk_level')!r}; supported={list(SUPPORTED_RISK_LEVELS)}",
    )


def behavior_change_finding(packet: Any, packet_readable: bool) -> EvaluationFinding:
    if not packet_readable:
        return EvaluationFinding(
            check_id="governance.behavior_change_articulated",
            category=FINDING_CATEGORY_GOVERNANCE,
            status=FINDING_STATUS_NOT_APPLICABLE,
            detail="cbsp21_packet is not readable, so the articulation rule cannot be evaluated",
        )

    try:
        validate_behavior_change_articulation(packet)
    except CBSP21PacketError as exc:
        return EvaluationFinding(
            check_id="governance.behavior_change_articulated",
            category=FINDING_CATEGORY_GOVERNANCE,
            status=FINDING_STATUS_FAIL,
            detail=str(exc),
        )

    return EvaluationFinding(
        check_id="governance.behavior_change_articulated",
        category=FINDING_CATEGORY_GOVERNANCE,
        status=FINDING_STATUS_PASS,
        detail=f"behavior_change={packet.get('behavior_change')!r} is articulated per the CBSP21 rule",
    )
