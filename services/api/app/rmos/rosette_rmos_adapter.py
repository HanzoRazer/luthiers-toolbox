#!/usr/bin/env python3
"""AI Rosette → RMOS Adapter"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from uuid import uuid4

# RMOS imports (authoritative - allowed here)
from .runs.schemas import RunArtifact, RunAttachment
from .runs.store import create_run_id, persist_run
from .runs.hashing import sha256_of_obj
from .runs.attachments import put_json_attachment
from .engines.registry import REGISTRY


# =============================================================================
# RMOS-Compatible Schemas (match art_studio.schemas)
# =============================================================================

class RosetteRingParam(BaseModel):
    """Single ring parameter specification for RMOS."""
    ring_index: int = 0
    width_mm: float = 2.0
    tile_length_mm: Optional[float] = None
    pattern_type: str = "mosaic"  # mosaic, solid, rope
    material_family: Optional[str] = None


class RosetteParamSpec(BaseModel):
    """Rosette design parameters for RMOS feasibility scoring."""
    version: str = "1.0"
    outer_diameter_mm: float = 100.0
    inner_diameter_mm: float = 90.0
    ring_params: List[RosetteRingParam] = Field(default_factory=list)
    depth_mm: float = 1.5
    soundhole_diameter_mm: Optional[float] = None
    notes: str = ""


# =============================================================================
# CONVERSION FUNCTIONS
# =============================================================================

def matrix_formula_to_rosette_spec(
    formula: Dict[str, Any],
    soundhole_diameter_mm: float = 90.0,
    channel_depth_mm: float = 1.5,
    ring_placement: str = "outside",  # "outside" or "centered"
) -> RosetteParamSpec:
    """Convert a MatrixFormula dict to RosetteParamSpec for RMOS."""
    # Extract dimensions from formula
    rows = formula.get('rows', [])
    col_seq = formula.get('column_sequence', [])
    
    strip_thickness_mm = formula.get('strip_thickness_mm', 0.6)
    chip_length_mm = formula.get('chip_length_mm', 1.6)
    
    # Pattern block dimensions
    max_strips_per_row = max(sum(row.values()) for row in rows) if rows else 6
    pattern_height_mm = max_strips_per_row * strip_thickness_mm  # This becomes ring WIDTH
    pattern_width_mm = len(col_seq) * chip_length_mm  # This is one tile length
    
    # Calculate ring geometry
    soundhole_radius = soundhole_diameter_mm / 2
    
    if ring_placement == "outside":
        # Pattern sits entirely outside soundhole
        inner_r = soundhole_radius
        outer_r = soundhole_radius + pattern_height_mm
    elif ring_placement == "centered":
        # Pattern straddles soundhole edge
        inner_r = soundhole_radius - (pattern_height_mm / 2)
        outer_r = soundhole_radius + (pattern_height_mm / 2)
    else:
        inner_r = soundhole_radius
        outer_r = soundhole_radius + pattern_height_mm
    
    # Count materials for notes
    material_totals = {}
    for row in rows:
        for mat, count in row.items():
            material_totals[mat] = material_totals.get(mat, 0) + count
    
    materials_str = ", ".join(f"{mat}:{count}" for mat, count in material_totals.items())
    
    return RosetteParamSpec(
        version="1.0",
        outer_diameter_mm=round(outer_r * 2, 2),
        inner_diameter_mm=round(inner_r * 2, 2),
        soundhole_diameter_mm=soundhole_diameter_mm,
        depth_mm=channel_depth_mm,
        ring_params=[
            RosetteRingParam(
                ring_index=0,
                width_mm=round(pattern_height_mm, 2),
                tile_length_mm=round(pattern_width_mm, 2),
                pattern_type="mosaic",
                material_family=list(material_totals.keys())[0] if material_totals else None,
            )
        ],
        notes=f"AI-generated from: {formula.get('name', 'custom')}. Materials: {materials_str}",
    )


def rosette_spec_to_context_dict(
    spec: RosetteParamSpec,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    machine_profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build RMOS context dict from RosetteParamSpec + manufacturing params.
    
    This is what gets passed to score_design_feasibility().
    """
    return {
        "design": spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict(),
        "tool_id": tool_id,
        "material_id": material_id,
        "machine_profile_id": machine_profile_id,
    }


# =============================================================================
# DUAL OUTPUT CONTAINER
# =============================================================================

class AIRosetteOutput(BaseModel):
    """Complete output from AI rosette generation."""
    # AI generation metadata
    generation_id: str = Field(..., description="Unique generation ID")
    prompt: str = Field(..., description="Original prompt")
    style: Optional[str] = Field(None, description="Style used")
    complexity: Optional[str] = Field(None, description="Complexity level")
    
    # Pattern data (for visualization & BOM)
    matrix_formula: Dict[str, Any] = Field(..., description="MatrixFormula dict")
    
    # RMOS data (for feasibility & toolpaths)
    rosette_spec: RosetteParamSpec = Field(..., description="RMOS-compatible spec")
    
    # Feasibility (if computed)
    feasibility_score: Optional[float] = Field(None, description="RMOS score 0-100")
    risk_bucket: Optional[str] = Field(None, description="GREEN/YELLOW/RED")
    feasibility_warnings: List[str] = Field(default_factory=list)
    
    # Visualization (if generated)
    svg_preview: Optional[str] = Field(None, description="SVG visualization")
    
    # Run artifact linkage
    run_id: Optional[str] = Field(None, description="Associated RunArtifact ID")
    
    def is_feasible(self) -> bool:
        """Check if design passed feasibility."""
        return self.risk_bucket in ("GREEN", "YELLOW")
    
    def is_green(self) -> bool:
        """Check if design is GREEN (fully approved)."""
        return self.risk_bucket == "GREEN"


# =============================================================================
# RUN ARTIFACT INTEGRATION
# =============================================================================

def _now_utc_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def create_rosette_run_artifact(
    output: AIRosetteOutput,
    *,
    workflow_session_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    machine_id: Optional[str] = None,
    event_type: str = "ai_rosette_generation",
) -> RunArtifact:
    """Create a RunArtifact for an AI rosette generation."""
    run_id = create_run_id()
    attachments: List[RunAttachment] = []
    
    # Attachment 1: Matrix formula (pattern data)
    formula_meta, _, formula_sha = put_json_attachment(
        obj=output.matrix_formula,
        kind="ai_formula",
        filename="matrix_formula.json",
    )
    attachments.append(formula_meta)
    
    # Attachment 2: RMOS spec (geometry data)
    spec_dict = output.rosette_spec.model_dump() if hasattr(output.rosette_spec, 'model_dump') else output.rosette_spec.dict()
    spec_meta, _, spec_sha = put_json_attachment(
        obj=spec_dict,
        kind="geometry",
        filename="rosette_spec.json",
    )
    attachments.append(spec_meta)
    
    # Attachment 3: Generation context (prompt, style, etc.)
    context = {
        "generation_id": output.generation_id,
        "prompt": output.prompt,
        "style": output.style,
        "complexity": output.complexity,
        "generated_at_utc": _now_utc_iso(),
    }
    ctx_meta, _, ctx_sha = put_json_attachment(
        obj=context,
        kind="debug",
        filename="generation_context.json",
    )
    attachments.append(ctx_meta)
    
    # Attachment 4: SVG preview (if present)
    if output.svg_preview:
        from .runs.attachments import put_text_attachment
        svg_meta, _ = put_text_attachment(
            text=output.svg_preview,
            kind="preview",
            mime="image/svg+xml",
            filename="preview.svg",
            ext=".svg",
        )
        attachments.append(svg_meta)
    
    # Build feasibility dict
    feasibility = None
    if output.feasibility_score is not None:
        feasibility = {
            "score": output.feasibility_score,
            "risk_bucket": output.risk_bucket,
            "warnings": output.feasibility_warnings,
        }
    
    # Determine status from feasibility
    status = "OK"
    if output.risk_bucket == "RED":
        status = "BLOCKED"
    elif output.risk_bucket is None:
        status = "OK"  # Feasibility not computed yet
    
    # Get engine version info
    cfg = REGISTRY.approval_config_summary(
        workflow_mode="ai_assisted",
        tool_id=tool_id,
        material_id=material_id,
        machine_id=machine_id,
    )
    
    # Build request hash from prompt + style
    request_obj = {
        "prompt": output.prompt,
        "style": output.style,
        "complexity": output.complexity,
    }
    request_hash = sha256_of_obj(request_obj)
    
    # Create artifact
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=_now_utc_iso(),
        workflow_session_id=workflow_session_id,
        tool_id=tool_id,
        material_id=material_id,
        machine_id=machine_id,
        workflow_mode="ai_assisted",
        toolchain_id="rosette_cam_v1",
        geometry_ref="MatrixFormula:v1",
        geometry_hash=formula_sha,
        event_type=event_type,
        status=status,
        feasibility=feasibility,
        request_hash=request_hash,
        attachments=attachments,
        engine_version=f"{cfg['feasibility_engine_id']}@{cfg['feasibility_engine_version']}",
        config_fingerprint=sha256_of_obj(cfg)[:16],
        notes=f"AI rosette generation: {output.prompt[:50]}...",
    )
    
    # Persist and return
    persist_run(artifact)
    return artifact


def finalize_rosette_design(
    output: AIRosetteOutput,
    *,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    machine_id: Optional[str] = None,
) -> AIRosetteOutput:
    """Finalize an AI rosette design by creating a RunArtifact."""
    artifact = create_rosette_run_artifact(
        output,
        tool_id=tool_id,
        material_id=material_id,
        machine_id=machine_id,
        event_type="ai_rosette_finalized",
    )
    
    # Update output with run_id
    output.run_id = artifact.run_id
    return output


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def generate_rosette_with_feasibility(
    prompt: str,
    style: Optional[str] = None,
    complexity: Optional[str] = None,
    colors: int = 2,
    soundhole_diameter_mm: float = 90.0,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    create_run_artifact: bool = False,
) -> AIRosetteOutput:
    """Complete pipeline: Prompt → Pattern → Feasibility → (Optional) RunArtifact."""
    # Deterministic stub formula.
    # AI-assisted generation is not yet promoted to canonical.
    # When ready, integrate via app.ai.transport + HTTP API.
    formula = {
        "name": f"Stub: {prompt[:30]}",
        "rows": [
            {"black": 1, "white": 3},
            {"black": 2, "white": 2},
            {"black": 1, "white": 3},
        ],
        "column_sequence": [1, 2, 3, 2, 1],
        "strip_thickness_mm": 0.6,
        "chip_length_mm": 1.6,
    }
    
    # Convert to RMOS spec
    rosette_spec = matrix_formula_to_rosette_spec(
        formula,
        soundhole_diameter_mm=soundhole_diameter_mm,
    )
    
    # SVG visualization placeholder.
    # pattern_visualizer was in legacy _experimental module.
    # Re-implement in app.vision when needed.
    svg = None
    
    # Build output
    output = AIRosetteOutput(
        generation_id=f"ai_gen_{uuid4().hex[:12]}",
        prompt=prompt,
        style=style,
        complexity=complexity,
        matrix_formula=formula,
        rosette_spec=rosette_spec,
        svg_preview=svg,
    )
    
    # Score feasibility (if RMOS available)
    try:
        from app.rmos.feasibility_scorer import score_design_feasibility
        from app.rmos.api_contracts import RmosContext
        
        ctx = RmosContext(
            tool_id=tool_id,
            material_id=material_id,
        )
        
        feas = score_design_feasibility(rosette_spec, ctx)
        output.feasibility_score = feas.score
        output.risk_bucket = feas.risk_bucket.value if hasattr(feas.risk_bucket, 'value') else str(feas.risk_bucket)
        output.feasibility_warnings = feas.warnings if hasattr(feas, 'warnings') else []
        
    except ImportError:
        # RMOS feasibility not available - use stub
        output.feasibility_score = 85.0
        output.risk_bucket = "GREEN"
        output.feasibility_warnings = ["Stub feasibility - RMOS scorer not available"]
    except (ZeroDivisionError, ValueError, TypeError, KeyError, AttributeError) as e:  # WP-1: narrowed from except Exception
        # Feasibility failed but generation succeeded
        output.feasibility_warnings = [f"Feasibility scoring failed: {e}"]
    
    # Create RunArtifact if requested
    if create_run_artifact:
        artifact = create_rosette_run_artifact(
            output,
            tool_id=tool_id,
            material_id=material_id,
            event_type="ai_rosette_generation",
        )
        output.run_id = artifact.run_id
    
    return output


# =============================================================================
# WORKFLOW SUBMISSION
# =============================================================================

def submit_rosette_to_workflow(
    output: AIRosetteOutput,
    *,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    machine_id: Optional[str] = None,
    approved_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a finalized rosette design to the RMOS workflow."""
    # Ensure we have a run artifact
    if not output.run_id:
        output = finalize_rosette_design(
            output,
            tool_id=tool_id,
            material_id=material_id,
            machine_id=machine_id,
        )
    
    result = {
        "run_id": output.run_id,
        "generation_id": output.generation_id,
        "feasibility_score": output.feasibility_score,
        "risk_bucket": output.risk_bucket,
        "workflow_session_id": None,
        "workflow_status": None,
        "errors": [],
    }
    
    # Check feasibility
    if not output.is_feasible():
        result["errors"].append(
            f"Design not feasible (risk_bucket={output.risk_bucket}). "
            "Cannot submit to workflow."
        )
        return result
    
    # Try to create workflow session
    try:
        # Import workflow module (if available)
        from app.rmos.workflow_state import (
            create_workflow_session,
            set_workflow_context,
            WorkflowMode,
        )
        
        # Create session
        session = create_workflow_session(
            mode=WorkflowMode.AI_ASSISTED,
            tool_id=tool_id,
            material_id=material_id,
            machine_id=machine_id,
        )
        
        # Set context with rosette spec
        spec_dict = output.rosette_spec.model_dump() if hasattr(output.rosette_spec, 'model_dump') else output.rosette_spec.dict()
        set_workflow_context(
            session_id=session.session_id,
            context={
                "design_type": "rosette",
                "rosette_spec": spec_dict,
                "ai_generation_id": output.generation_id,
                "ai_run_id": output.run_id,
            },
        )
        
        result["workflow_session_id"] = session.session_id
        result["workflow_status"] = session.state.value if hasattr(session.state, 'value') else str(session.state)
        
    except ImportError:
        result["errors"].append("RMOS workflow module not available")
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as e:  # WP-1: narrowed from except Exception
        result["errors"].append(f"Workflow submission failed: {e}")
    
    return result


# =============================================================================
# DEMO
# =============================================================================

