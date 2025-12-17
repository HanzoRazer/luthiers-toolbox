#!/usr/bin/env python3
"""
AI Rosette → RMOS Adapter

Bridges the gap between:
- MatrixFormula (pattern visualization, BOM, assembly)
- RosetteParamSpec (RMOS feasibility scoring, toolpath generation)
- RunArtifacts (audit trail, drift detection)

This is the critical integration point between the AI pattern generator
and the existing RMOS manufacturing pipeline.

GOVERNANCE: This file lives in rmos/ (authoritative zone).
It may import from AI sandbox to receive data, but AI sandbox
must NOT import from this file.
"""

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
    """
    Rosette design parameters for RMOS feasibility scoring.
    
    This schema is what RMOS expects. The AI generates MatrixFormula,
    this adapter converts it to RosetteParamSpec.
    """
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
    """
    Convert a MatrixFormula dict to RosetteParamSpec for RMOS.
    
    The MatrixFormula describes the PATTERN (colors, arrangement).
    The RosetteParamSpec describes the GEOMETRY (dimensions for CNC).
    
    Args:
        formula: MatrixFormula dict from AI generator
        soundhole_diameter_mm: Soundhole diameter (default 90mm for classical)
        channel_depth_mm: Routing depth (default 1.5mm)
        ring_placement: Where pattern sits relative to soundhole
    
    Returns:
        RosetteParamSpec ready for RMOS feasibility scoring
    """
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
    """
    Complete output from AI rosette generation.
    
    Contains BOTH the pattern data (for visualization) AND
    the RMOS-compatible spec (for feasibility).
    """
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
    """
    Create a RunArtifact for an AI rosette generation.
    
    This provides audit trail for AI-generated designs.
    The artifact captures:
    - The prompt and generation parameters
    - The resulting formula and RMOS spec
    - Feasibility assessment
    - SVG preview as attachment
    
    Args:
        output: AIRosetteOutput from generation
        workflow_session_id: If part of a workflow session
        tool_id: Tool used for manufacturing
        material_id: Material spec
        machine_id: Target CNC machine
        event_type: Type of event (default: ai_rosette_generation)
    
    Returns:
        Persisted RunArtifact with attachments
    """
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
    """
    Finalize an AI rosette design by creating a RunArtifact.
    
    Call this when user confirms/selects a design for manufacturing.
    Creates immutable audit trail and returns updated output with run_id.
    
    Args:
        output: AIRosetteOutput to finalize
        tool_id: Tool selection
        material_id: Material selection  
        machine_id: Machine selection
    
    Returns:
        Updated AIRosetteOutput with run_id set
    """
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
    """
    Complete pipeline: Prompt → Pattern → Feasibility → (Optional) RunArtifact.
    
    This is the main integration function that:
    1. Generates pattern from AI prompt
    2. Converts to RMOS spec
    3. Scores feasibility
    4. Generates visualization
    5. (Optional) Creates RunArtifact for audit trail
    
    Args:
        prompt: Natural language description
        style: Pattern style (torres, hauser, etc.)
        complexity: Complexity level
        colors: Number of colors/materials
        soundhole_diameter_mm: Soundhole size
        tool_id: Tool for feasibility
        material_id: Material for feasibility
        create_run_artifact: If True, persists a RunArtifact
    
    Returns:
        AIRosetteOutput with everything needed
    """
    # Import AI generator (from experimental zone - allowed for data intake)
    try:
        from app._experimental.ai_graphics.rosette_generator import RosetteAIGenerator
    except ImportError:
        try:
            from _experimental.ai_graphics.rosette_generator import RosetteAIGenerator
        except ImportError:
            # Stub generator for testing
            RosetteAIGenerator = None
    
    # Generate pattern
    if RosetteAIGenerator:
        generator = RosetteAIGenerator()
        result = generator.generate(
            request=prompt,
            style=style,
            complexity=complexity,
            colors=colors,
        )
        
        if not result.success or not result.formula:
            raise ValueError(f"AI generation failed: {result.error}")
        
        formula = result.formula.to_pattern_generator_format()
    else:
        # Fallback stub formula for testing
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
    
    # Generate visualization
    svg = None
    try:
        from app._experimental.ai_graphics.services.pattern_visualizer import render_svg_pattern
        svg = render_svg_pattern(formula, scale=15)
    except ImportError:
        pass
    except Exception:
        pass
    
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
    except Exception as e:
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
    """
    Submit a finalized rosette design to the RMOS workflow.
    
    This creates:
    1. A workflow session
    2. Context with the rosette spec
    3. Approval request (if feasibility is GREEN)
    
    Args:
        output: AIRosetteOutput to submit
        tool_id: Tool for manufacturing
        material_id: Material selection
        machine_id: Target machine
        approved_by: User/operator name
    
    Returns:
        Dict with session_id, status, and any errors
    """
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
    except Exception as e:
        result["errors"].append(f"Workflow submission failed: {e}")
    
    return result


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demo the adapter with RunArtifact integration."""
    print("=" * 60)
    print("AI ROSETTE → RMOS ADAPTER DEMO")
    print("=" * 60)
    
    # Sample formula (Torres diamond)
    formula = {
        "name": "Torres Diamond",
        "rows": [
            {"black": 1, "white": 5},
            {"black": 2, "white": 4},
            {"black": 3, "white": 3},
            {"black": 4, "white": 2},
            {"black": 3, "white": 3},
            {"black": 2, "white": 4},
            {"black": 1, "white": 5},
        ],
        "column_sequence": [1, 2, 3, 4, 5, 6, 7, 6, 5],
        "strip_width_mm": 0.7,
        "strip_thickness_mm": 0.6,
        "chip_length_mm": 1.6,
    }
    
    print("\n--- Input: MatrixFormula ---")
    print(f"Name: {formula['name']}")
    print(f"Rows: {len(formula['rows'])}")
    print(f"Columns: {len(formula['column_sequence'])}")
    
    # Convert to RMOS spec
    spec = matrix_formula_to_rosette_spec(formula, soundhole_diameter_mm=85.0)
    
    print("\n--- Output: RosetteParamSpec ---")
    print(f"Version: {spec.version}")
    print(f"Outer diameter: {spec.outer_diameter_mm}mm")
    print(f"Inner diameter: {spec.inner_diameter_mm}mm")
    print(f"Soundhole: {spec.soundhole_diameter_mm}mm")
    print(f"Depth: {spec.depth_mm}mm")
    print(f"Ring count: {len(spec.ring_params)}")
    
    if spec.ring_params:
        ring = spec.ring_params[0]
        print(f"\nRing 0:")
        print(f"  Width: {ring.width_mm}mm")
        print(f"  Tile length: {ring.tile_length_mm}mm")
        print(f"  Pattern type: {ring.pattern_type}")
    
    print(f"\nNotes: {spec.notes}")
    
    print("\n--- Full Pipeline Test (with RunArtifact) ---")
    try:
        output = generate_rosette_with_feasibility(
            prompt="Torres diamond pattern with ebony and maple",
            style="torres",
            soundhole_diameter_mm=85.0,
            create_run_artifact=True,  # Creates audit trail
        )
        print(f"Generation ID: {output.generation_id}")
        print(f"Prompt: {output.prompt}")
        print(f"Style: {output.style}")
        print(f"Feasibility score: {output.feasibility_score}")
        print(f"Risk bucket: {output.risk_bucket}")
        print(f"SVG generated: {output.svg_preview is not None}")
        print(f"Run ID: {output.run_id}")
    except Exception as e:
        print(f"Pipeline test: {e}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    demo()
