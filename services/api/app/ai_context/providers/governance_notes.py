"""
AI Context Adapter - Governance Notes Provider

Provides read-only governance context explaining why something is blocked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..schemas import (
    AdapterWarning,
    ContextAttachment,
    ContextRequest,
    ContextSource,
    RedactionPolicy,
    SourceKind,
    WarningCode,
)


# Built-in governance notes for common blockers
GOVERNANCE_NOTES: Dict[str, Dict[str, Any]] = {
    "feasibility_failed": {
        "title": "Feasibility Check Failed",
        "description": "The operation cannot proceed because feasibility checks did not pass.",
        "typical_causes": [
            "Tool diameter too large for feature",
            "Depth exceeds safe limits",
            "Material not compatible with operation",
            "Machine constraints violated",
        ],
        "suggested_actions": [
            "Review feasibility report for specific failures",
            "Adjust design parameters to meet constraints",
            "Select a different tool or operation type",
            "Consult OPERATION_EXECUTION_GOVERNANCE_v1.md",
        ],
    },
    "artifact_missing": {
        "title": "Required Artifact Missing",
        "description": "A required artifact is not present in the run.",
        "typical_causes": [
            "Previous workflow step was not completed",
            "Artifact was deleted or corrupted",
            "Run was created with incomplete data",
        ],
        "suggested_actions": [
            "Re-run the previous workflow step",
            "Check artifact persistence configuration",
            "Verify run creation completed successfully",
        ],
    },
    "boundary_violation": {
        "title": "Architectural Boundary Violation",
        "description": "The requested operation crosses an architectural boundary.",
        "typical_causes": [
            "Direct import between isolated domains",
            "Attempting to access analyzer code from toolbox",
            "Bypassing artifact contract patterns",
        ],
        "suggested_actions": [
            "Use artifact ingestion instead of direct imports",
            "Use HTTP API contracts for cross-domain communication",
            "Consult BOUNDARY_RULES.md and FENCE_REGISTRY.json",
        ],
    },
    "lane_governance": {
        "title": "Operation Lane Governance",
        "description": "The operation requires OPERATION lane governance.",
        "typical_causes": [
            "Machine-executing endpoint called without proper setup",
            "Missing feasibility gate in execution path",
            "Artifact persistence not configured",
        ],
        "suggested_actions": [
            "Use governed OPERATION lane endpoints",
            "Ensure feasibility check is performed first",
            "Follow CNC_SAW_LAB_DEVELOPER_GUIDE.md pattern",
        ],
    },
    "decision_required": {
        "title": "Decision Required",
        "description": "A human decision is required before proceeding.",
        "typical_causes": [
            "Risk level requires operator approval",
            "Multiple candidates require selection",
            "Override needed for constraint violation",
        ],
        "suggested_actions": [
            "Review the decision request details",
            "Approve or reject the pending operation",
            "Provide required parameters or selections",
        ],
    },
    "export_blocked": {
        "title": "Export Blocked",
        "description": "Export is blocked due to incomplete or invalid state.",
        "typical_causes": [
            "Run not in APPROVED state",
            "Missing required approvals",
            "Feasibility not yet checked",
            "CAM generation not yet completed",
        ],
        "suggested_actions": [
            "Complete all required workflow steps",
            "Ensure feasibility check passes",
            "Get required approvals",
            "Complete CAM generation before export",
        ],
    },
}


class GovernanceNotesProvider:
    """
    Provides governance_notes context explaining blockers and rules.
    
    Includes:
    - Why operations are blocked
    - Relevant governance rules
    - Suggested remediation steps
    
    This is documentation/explanation only, no actions.
    """
    
    @property
    def source_kind(self) -> SourceKind:
        return SourceKind.GOVERNANCE_NOTES
    
    def provide(
        self,
        req: ContextRequest,
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[ContextAttachment], List[AdapterWarning]]:
        """Provide governance notes context."""
        sources: List[ContextSource] = []
        attachments: List[ContextAttachment] = []
        warnings: List[AdapterWarning] = []
        
        # Extract topics from intent (simple keyword matching)
        topics = self._extract_topics(req.intent)
        
        if not topics:
            # Provide general governance overview
            topics = ["overview"]
        
        for topic in topics:
            notes = self._get_notes(topic)
            if notes:
                sources.append(ContextSource(
                    source_id=f"governance_{topic}",
                    kind=SourceKind.GOVERNANCE_NOTES,
                    content_type="application/json",
                    payload=notes,
                ))
        
        if not sources:
            warnings.append(AdapterWarning(
                code=WarningCode.SCOPE_NOT_FOUND,
                message="No relevant governance notes found for the intent",
            ))
        
        return sources, attachments, warnings
    
    def _extract_topics(self, intent: str) -> List[str]:
        """Extract governance topics from intent string."""
        topics: List[str] = []
        intent_lower = intent.lower()
        
        # Topic keyword mapping
        keyword_map = {
            "feasibility": "feasibility_failed",
            "blocked": "export_blocked",
            "export": "export_blocked",
            "artifact": "artifact_missing",
            "missing": "artifact_missing",
            "boundary": "boundary_violation",
            "violation": "boundary_violation",
            "lane": "lane_governance",
            "governance": "lane_governance",
            "decision": "decision_required",
            "approval": "decision_required",
            "approve": "decision_required",
        }
        
        for keyword, topic in keyword_map.items():
            if keyword in intent_lower and topic not in topics:
                topics.append(topic)
        
        return topics
    
    def _get_notes(self, topic: str) -> Dict[str, Any]:
        """Get governance notes for a topic."""
        if topic == "overview":
            return {
                "title": "Governance Overview",
                "description": "Luthier's ToolBox uses lane-based governance for machine operations.",
                "lanes": {
                    "OPERATION": "Full governance: artifacts, feasibility gate, audit trail",
                    "UTILITY": "Stateless/preview, no artifacts, for development use",
                },
                "key_concepts": [
                    "Feasibility gates prevent unsafe operations",
                    "Artifact persistence ensures traceability",
                    "Architectural boundaries enforce domain separation",
                ],
                "references": [
                    "OPERATION_EXECUTION_GOVERNANCE_v1.md",
                    "BOUNDARY_RULES.md",
                    "FENCE_REGISTRY.json",
                ],
            }
        
        return GOVERNANCE_NOTES.get(topic, {})


# Singleton instance
governance_notes_provider = GovernanceNotesProvider()
