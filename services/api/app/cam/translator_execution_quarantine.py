"""
Translator Execution Quarantine + Governance Freeze Boundary

CAM Dev Order 7H: Execution quarantine semantics and governance freeze contracts.

This module formalizes the stopping point between:
  - Governed translator planning (7A-7G complete)
  - Future executable translator runtime work (prohibited until escalation)

7H creates:
  - Execution quarantine models
  - Governance freeze manifests
  - Runtime prohibition policies
  - Execution escalation requirements

7H does NOT create:
  - Execution runtime
  - DXF/SVG/G-code generation
  - Serializer invocation
  - Plugin execution
  - Machine output

7H invariants:
  - execution_runtime_present: always false
  - serializer_invocation_allowed: always false
  - subprocess_execution_allowed: always false
  - machine_output_allowed: always false
  - plugin_loading_allowed: always false
  - governance_escalation_required: always true
  - human_approval_required: always true

Guardrail:
  7H creates a freeze/quarantine evidence boundary.
  It does NOT create any execution pathway or approval workflow.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

QuarantineState = Literal[
    "execution_prohibited",        # Baseline: execution not allowed
    "governance_freeze",           # Stronger: deliberate stop boundary reached
    "future_escalation_required",  # Strongest: new governance escalation required
]

# Canonical required escalation layers
REQUIRED_ESCALATION_LAYERS: List[str] = [
    "governance_review",
    "translator_execution_architecture_review",
    "human_approval",
    "security_review",
    "artifact_generation_policy_review",
]

# Canonical prohibited actions in 7H
PROHIBITED_ACTIONS: List[str] = [
    "DXF_generation",
    "SVG_generation",
    "G-code_generation",
    "serializer_invocation",
    "runtime_translator_execution",
    "plugin_loading",
    "machine_output",
    "subprocess_execution",
]


# -----------------------------------------------------------------------------
# In-Memory Indexes
# -----------------------------------------------------------------------------

QUARANTINE_INDEX: Dict[str, "TranslatorExecutionQuarantine"] = {}
FREEZE_MANIFEST_INDEX: Dict[str, "TranslatorGovernanceFreezeManifest"] = {}


# -----------------------------------------------------------------------------
# Execution Quarantine Summary (for 7G integration)
# -----------------------------------------------------------------------------

class ExecutionQuarantineSummary(BaseModel):
    """
    Lightweight quarantine summary for 7G readiness integration.

    Contains only essential quarantine state — no detailed constraints.
    """

    quarantine_id: str = Field(..., description="Quarantine evaluation identifier")
    translator_id: str = Field(..., description="Translator identifier")
    quarantine_state: QuarantineState = Field(
        default="future_escalation_required",
        description="Current quarantine state"
    )

    # 7H invariants — always enforced
    governance_escalation_required: bool = Field(
        default=True,
        description="Always true — escalation required for execution"
    )
    execution_runtime_present: bool = Field(
        default=False,
        description="Always false — no execution runtime"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always false — no machine output"
    )


# -----------------------------------------------------------------------------
# Governance Freeze Manifest
# -----------------------------------------------------------------------------

class TranslatorGovernanceFreezeManifest(BaseModel):
    """
    Immutable governance freeze manifest.

    Captures the governance context at freeze evaluation time.
    Event-driven: new manifest created per quarantine evaluation.

    Formalizes the boundary between governed planning and future execution.
    """

    # --- Identity ---
    manifest_id: str = Field(
        default_factory=lambda: f"freeze-{uuid4().hex[:12]}",
        description="Unique manifest identifier"
    )
    translator_id: str = Field(..., description="Translator identifier")

    # --- Freeze Scope ---
    freeze_scope: List[str] = Field(
        default_factory=lambda: [
            "translator_execution",
            "artifact_generation",
            "serializer_invocation",
            "machine_output",
        ],
        description="Scope of governance freeze"
    )

    # --- Prohibited Actions ---
    prohibited_actions: List[str] = Field(
        default_factory=lambda: PROHIBITED_ACTIONS.copy(),
        description="Actions prohibited under freeze"
    )

    # --- Required Escalation ---
    required_escalation_layers: List[str] = Field(
        default_factory=lambda: REQUIRED_ESCALATION_LAYERS.copy(),
        description="Required escalation layers for execution"
    )

    # --- Source Hashes ---
    created_from_readiness_hash: str = Field(
        default="",
        description="Hash of readiness evaluation at freeze time"
    )
    created_from_provenance_hash: str = Field(
        default="",
        description="Hash of provenance lineage at freeze time"
    )

    # --- Timestamps ---
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Manifest creation timestamp"
    )

    # --- Immutability ---
    immutable: bool = Field(
        default=True,
        description="Always true — freeze manifests are immutable"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional manifest metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_immutability(self) -> "TranslatorGovernanceFreezeManifest":
        """Enforce freeze manifest immutability."""
        if not self.immutable:
            raise ValueError(
                f"Freeze manifest '{self.manifest_id}': immutable must be True — "
                f"freeze manifests are always immutable"
            )
        return self

    def compute_manifest_hash(self) -> str:
        """Compute deterministic hash of freeze manifest."""
        hash_input = {
            "translator_id": self.translator_id,
            "freeze_scope": sorted(self.freeze_scope),
            "prohibited_actions": sorted(self.prohibited_actions),
            "required_escalation_layers": sorted(self.required_escalation_layers),
            "created_from_readiness_hash": self.created_from_readiness_hash,
            "created_from_provenance_hash": self.created_from_provenance_hash,
        }
        canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Translator Execution Quarantine
# -----------------------------------------------------------------------------

class TranslatorExecutionQuarantine(BaseModel):
    """
    Translator execution quarantine evaluation.

    Formalizes that execution is structurally prohibited until
    governance escalation explicitly occurs.

    7H invariants (model-enforced):
      - execution_runtime_present: always false
      - serializer_invocation_allowed: always false
      - subprocess_execution_allowed: always false
      - machine_output_allowed: always false
      - plugin_loading_allowed: always false
      - governance_escalation_required: always true
      - human_approval_required: always true
    """

    # --- Identity ---
    quarantine_id: str = Field(
        default_factory=lambda: f"quarantine-{uuid4().hex[:12]}",
        description="Unique quarantine evaluation identifier"
    )
    translator_id: str = Field(..., description="Translator identifier")

    # --- Quarantine State ---
    quarantine_state: QuarantineState = Field(
        default="future_escalation_required",
        description="Current quarantine state (default: strongest)"
    )

    # --- 7H Invariants (Runtime Prohibition) ---
    execution_runtime_present: bool = Field(
        default=False,
        description="Always false — no execution runtime in 7H"
    )
    serializer_invocation_allowed: bool = Field(
        default=False,
        description="Always false — no serializer invocation"
    )
    subprocess_execution_allowed: bool = Field(
        default=False,
        description="Always false — no subprocess execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always false — no machine output"
    )
    plugin_loading_allowed: bool = Field(
        default=False,
        description="Always false — no plugin loading"
    )

    # --- Escalation Requirements ---
    governance_escalation_required: bool = Field(
        default=True,
        description="Always true — governance escalation required"
    )
    human_approval_required: bool = Field(
        default=True,
        description="Always true — human approval required"
    )

    # --- Constraints and Warnings ---
    blocking_constraints: List[str] = Field(
        default_factory=list,
        description="Constraints blocking execution"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    # --- Freeze Manifest Reference ---
    freeze_manifest_hash: str = Field(
        default="",
        description="Hash of associated freeze manifest"
    )
    freeze_manifest_id: str = Field(
        default="",
        description="ID of associated freeze manifest"
    )

    # --- Source References ---
    source_readiness_evaluation_id: str = Field(
        default="",
        description="ID of source readiness evaluation"
    )
    source_provenance_id: str = Field(
        default="",
        description="ID of source provenance"
    )

    # --- Timestamps ---
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Quarantine evaluation timestamp"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional quarantine metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7h_invariants(self) -> "TranslatorExecutionQuarantine":
        """
        Enforce 7H invariants:
        - All execution flags must be False
        - All escalation requirements must be True
        """
        if self.execution_runtime_present:
            raise ValueError(
                "execution_runtime_present must be False in 7H — "
                "no execution runtime"
            )

        if self.serializer_invocation_allowed:
            raise ValueError(
                "serializer_invocation_allowed must be False in 7H — "
                "no serializer invocation"
            )

        if self.subprocess_execution_allowed:
            raise ValueError(
                "subprocess_execution_allowed must be False in 7H — "
                "no subprocess execution"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "machine_output_allowed must be False in 7H — "
                "no machine output"
            )

        if self.plugin_loading_allowed:
            raise ValueError(
                "plugin_loading_allowed must be False in 7H — "
                "no plugin loading"
            )

        if not self.governance_escalation_required:
            raise ValueError(
                "governance_escalation_required must be True in 7H — "
                "escalation always required"
            )

        if not self.human_approval_required:
            raise ValueError(
                "human_approval_required must be True in 7H — "
                "human approval always required"
            )

        return self

    def to_summary(self) -> ExecutionQuarantineSummary:
        """Create lightweight summary for 7G readiness integration."""
        return ExecutionQuarantineSummary(
            quarantine_id=self.quarantine_id,
            translator_id=self.translator_id,
            quarantine_state=self.quarantine_state,
            governance_escalation_required=True,
            execution_runtime_present=False,
            machine_output_allowed=False,
        )


# -----------------------------------------------------------------------------
# Quarantine Index Operations
# -----------------------------------------------------------------------------

def register_quarantine(quarantine: TranslatorExecutionQuarantine) -> None:
    """Register quarantine evaluation in the in-memory index."""
    QUARANTINE_INDEX[quarantine.quarantine_id] = quarantine


def get_quarantine(quarantine_id: str) -> Optional[TranslatorExecutionQuarantine]:
    """Get quarantine by ID from the index."""
    return QUARANTINE_INDEX.get(quarantine_id)


def get_quarantine_by_translator(
    translator_id: str,
) -> List[TranslatorExecutionQuarantine]:
    """Get all quarantine evaluations for a translator."""
    return [
        q for q in QUARANTINE_INDEX.values()
        if q.translator_id == translator_id
    ]


def get_latest_quarantine(
    translator_id: str,
) -> Optional[TranslatorExecutionQuarantine]:
    """Get most recent quarantine evaluation for a translator."""
    quarantines = get_quarantine_by_translator(translator_id)
    if not quarantines:
        return None
    return max(quarantines, key=lambda q: q.evaluated_at)


def list_quarantines() -> List[TranslatorExecutionQuarantine]:
    """List all registered quarantine evaluations."""
    return list(QUARANTINE_INDEX.values())


def clear_quarantine_index() -> None:
    """Clear the quarantine index (for testing)."""
    QUARANTINE_INDEX.clear()


# -----------------------------------------------------------------------------
# Freeze Manifest Index Operations
# -----------------------------------------------------------------------------

def register_freeze_manifest(manifest: TranslatorGovernanceFreezeManifest) -> None:
    """Register freeze manifest in the in-memory index."""
    FREEZE_MANIFEST_INDEX[manifest.manifest_id] = manifest


def get_freeze_manifest(manifest_id: str) -> Optional[TranslatorGovernanceFreezeManifest]:
    """Get freeze manifest by ID from the index."""
    return FREEZE_MANIFEST_INDEX.get(manifest_id)


def get_freeze_manifests_by_translator(
    translator_id: str,
) -> List[TranslatorGovernanceFreezeManifest]:
    """Get all freeze manifests for a translator."""
    return [
        m for m in FREEZE_MANIFEST_INDEX.values()
        if m.translator_id == translator_id
    ]


def list_freeze_manifests() -> List[TranslatorGovernanceFreezeManifest]:
    """List all registered freeze manifests."""
    return list(FREEZE_MANIFEST_INDEX.values())


def clear_freeze_manifest_index() -> None:
    """Clear the freeze manifest index (for testing)."""
    FREEZE_MANIFEST_INDEX.clear()


# -----------------------------------------------------------------------------
# Quarantine Evaluator
# -----------------------------------------------------------------------------

def _compute_readiness_hash(readiness_evaluation: Any) -> str:
    """Compute hash from readiness evaluation for freeze manifest."""
    if readiness_evaluation is None:
        return ""
    try:
        if hasattr(readiness_evaluation, "model_dump"):
            data = readiness_evaluation.model_dump(mode="json")
        else:
            data = dict(readiness_evaluation)
        # Exclude timestamps for determinism
        data.pop("evaluated_at", None)
        data.pop("created_at", None)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return ""


def _compute_provenance_hash(provenance: Any) -> str:
    """Compute hash from provenance for freeze manifest."""
    if provenance is None:
        return ""
    try:
        if hasattr(provenance, "deterministic_lineage_hash"):
            return provenance.deterministic_lineage_hash[:16]
        if hasattr(provenance, "model_dump"):
            data = provenance.model_dump(mode="json")
        else:
            data = dict(provenance)
        data.pop("created_at", None)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return ""


def evaluate_execution_quarantine(
    translator_id: str,
    readiness_evaluation: Optional[Any] = None,
    provenance: Optional[Any] = None,
) -> TranslatorExecutionQuarantine:
    """
    Evaluate execution quarantine for a translator.

    This is QUARANTINE EVALUATION, not execution authorization.
    Creates freeze manifest and enforces runtime prohibition state.

    Args:
        translator_id: Translator identifier
        readiness_evaluation: Optional 7G readiness evaluation
        provenance: Optional 7F provenance

    Returns:
        TranslatorExecutionQuarantine with freeze manifest attached

    Guardrail:
        7H creates freeze/quarantine evidence boundary.
        It does NOT create any execution pathway.
    """
    blocking_constraints: List[str] = []
    warnings: List[str] = []

    # --- Constraint 1: Execution runtime not implemented ---
    blocking_constraints.append(
        "Execution runtime not implemented — requires governance escalation"
    )

    # --- Constraint 2: All serializers prohibited ---
    blocking_constraints.append(
        "Serializer invocation prohibited — requires artifact generation policy review"
    )

    # --- Constraint 3: Machine output prohibited ---
    blocking_constraints.append(
        "Machine output prohibited — requires security review"
    )

    # --- Constraint 4: Plugin loading prohibited ---
    blocking_constraints.append(
        "Plugin loading prohibited — requires translator execution architecture review"
    )

    # --- Constraint 5: Subprocess execution prohibited ---
    blocking_constraints.append(
        "Subprocess execution prohibited — requires governance review"
    )

    # --- Warning: 7A-7G complete, 7H is the boundary ---
    warnings.append(
        "7A-7G governance complete — 7H establishes execution quarantine boundary"
    )

    # --- Create freeze manifest ---
    readiness_hash = _compute_readiness_hash(readiness_evaluation)
    provenance_hash = _compute_provenance_hash(provenance)

    freeze_manifest = TranslatorGovernanceFreezeManifest(
        translator_id=translator_id,
        created_from_readiness_hash=readiness_hash,
        created_from_provenance_hash=provenance_hash,
        metadata={
            "dev_order": "7H",
            "boundary_type": "execution_quarantine",
            "created_by": "evaluate_execution_quarantine",
        },
    )

    # Register freeze manifest
    register_freeze_manifest(freeze_manifest)

    # --- Extract source IDs if available ---
    source_readiness_id = ""
    source_provenance_id = ""

    if readiness_evaluation and hasattr(readiness_evaluation, "evaluation_id"):
        source_readiness_id = readiness_evaluation.evaluation_id

    if provenance and hasattr(provenance, "provenance_id"):
        source_provenance_id = provenance.provenance_id

    # --- Create quarantine evaluation ---
    quarantine = TranslatorExecutionQuarantine(
        translator_id=translator_id,
        quarantine_state="future_escalation_required",
        execution_runtime_present=False,
        serializer_invocation_allowed=False,
        subprocess_execution_allowed=False,
        machine_output_allowed=False,
        plugin_loading_allowed=False,
        governance_escalation_required=True,
        human_approval_required=True,
        blocking_constraints=blocking_constraints,
        warnings=warnings,
        freeze_manifest_hash=freeze_manifest.compute_manifest_hash(),
        freeze_manifest_id=freeze_manifest.manifest_id,
        source_readiness_evaluation_id=source_readiness_id,
        source_provenance_id=source_provenance_id,
        metadata={
            "dev_order": "7H",
            "evaluation_type": "execution_quarantine",
            "quarantine_boundary": True,
        },
    )

    # Register quarantine
    register_quarantine(quarantine)

    return quarantine


# -----------------------------------------------------------------------------
# RMOS Persistence (Optional)
# -----------------------------------------------------------------------------

QUARANTINE_ARTIFACT_KIND = "translator_execution_quarantine_json"
FREEZE_MANIFEST_ARTIFACT_KIND = "translator_governance_freeze_manifest_json"


def persist_quarantine_to_rmos(
    quarantine: TranslatorExecutionQuarantine,
    run_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Persist quarantine to RMOS (optional).

    Returns artifact reference if successful, None otherwise.
    Supplemental to in-memory index.
    """
    try:
        from app.cam.export_rmos_artifacts import put_json_attachment

        quarantine_dict = quarantine.model_dump(mode="json")

        stat, path, sha256 = put_json_attachment(
            kind=QUARANTINE_ARTIFACT_KIND,
            obj=quarantine_dict,
            run_id=run_id,
        )

        return {
            "kind": QUARANTINE_ARTIFACT_KIND,
            "sha256": sha256,
            "bytes": stat.size_bytes if stat else 0,
            "path": path,
            "quarantine_id": quarantine.quarantine_id,
        }
    except ImportError:
        return None
    except Exception:
        return None


def persist_freeze_manifest_to_rmos(
    manifest: TranslatorGovernanceFreezeManifest,
    run_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Persist freeze manifest to RMOS (optional).

    Returns artifact reference if successful, None otherwise.
    Supplemental to in-memory index.
    """
    try:
        from app.cam.export_rmos_artifacts import put_json_attachment

        manifest_dict = manifest.model_dump(mode="json")

        stat, path, sha256 = put_json_attachment(
            kind=FREEZE_MANIFEST_ARTIFACT_KIND,
            obj=manifest_dict,
            run_id=run_id,
        )

        return {
            "kind": FREEZE_MANIFEST_ARTIFACT_KIND,
            "sha256": sha256,
            "bytes": stat.size_bytes if stat else 0,
            "path": path,
            "manifest_id": manifest.manifest_id,
        }
    except ImportError:
        return None
    except Exception:
        return None
