"""Unified Presets Router - Single endpoint for CAM + Export + Neck presets"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..util.presets_store import (
    list_presets,
    get_preset,
    insert_preset,
    update_preset,
    delete_preset,
)
from ..util.template_engine import (
    validate_template,
    resolve_export_filename,
    resolve_template,
)

router = APIRouter(prefix="/presets", tags=["presets", "unified"])

PresetKind = Literal["cam", "export", "neck", "combo"]

class CamParams(BaseModel):
    """CAM operation parameters."""
    stepover: Optional[float] = None
    stepdown: Optional[float] = None
    strategy: Optional[str] = None
    margin: Optional[float] = None
    feed_xy: Optional[float] = None
    feed_z: Optional[float] = None
    safe_z: Optional[float] = None
    z_rough: Optional[float] = None

class ExportParams(BaseModel):
    """Export configuration parameters."""
    default_format: Optional[str] = Field(None, description="gcode, dxf, svg, etc.")
    filename_template: Optional[str] = Field(
        None, 
        description="Template with tokens: {preset}, {machine}, {neck_profile}, {date}, etc."
    )
    include_flags: Optional[Dict[str, bool]] = Field(
        None,
        description="Flags like include_baseline, include_candidate, include_diff_only"
    )
    default_directory: Optional[str] = None

class NeckSectionDefault(BaseModel):
    """Default dimensions for a neck section."""
    name: str
    width_mm: float
    thickness_mm: float

class NeckParams(BaseModel):
    """Neck profile parameters."""
    profile_id: Optional[str] = None
    profile_name: Optional[str] = None
    scale_length_mm: Optional[float] = None
    section_defaults: Optional[List[NeckSectionDefault]] = None

class PresetIn(BaseModel):
    """Request body for creating/updating presets."""
    name: str
    kind: PresetKind
    description: Optional[str] = ""
    tags: List[str] = Field(default_factory=list)
    
    # Machine/post associations (for CAM presets)
    machine_id: Optional[str] = None
    post_id: Optional[str] = None
    units: Optional[str] = Field(None, description="mm or inch")
    
    # Job lineage (B19, B20, B21 features)
    job_source_id: Optional[str] = Field(None, description="Source JobInt run ID for B19")
    source: Optional[str] = Field(None, description="manual | clone | import")
    
    # Domain-specific parameter blocks
    cam_params: Optional[Dict[str, Any]] = Field(None, description="CAM operation parameters")
    export_params: Optional[Dict[str, Any]] = Field(None, description="Export configuration")
    neck_params: Optional[Dict[str, Any]] = Field(None, description="Neck profile parameters")

class PresetOut(BaseModel):
    """Response schema for presets."""
    id: str
    name: str
    kind: PresetKind
    description: Optional[str]
    tags: List[str]
    machine_id: Optional[str]
    post_id: Optional[str]
    units: Optional[str]
    job_source_id: Optional[str]
    source: Optional[str]
    cam_params: Optional[Dict[str, Any]]
    export_params: Optional[Dict[str, Any]]
    neck_params: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    created_by: Optional[str] = None

@router.get("", response_model=List[Dict[str, Any]])
def get_presets(
    kind: Optional[PresetKind] = Query(None, description="Filter by preset kind"),
    tag: Optional[str] = Query(None, description="Filter by tag")
) -> List[Dict[str, Any]]:
    """List all presets with optional filters."""
    return list_presets(kind=kind, tag=tag)

@router.get("/{preset_id}", response_model=Dict[str, Any])
def get_preset_by_id(preset_id: str) -> Dict[str, Any]:
    """Get a single preset by ID."""
    preset = get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    return preset

@router.post("", response_model=Dict[str, Any])
def create_preset(payload: PresetIn) -> Dict[str, Any]:
    """Create a new preset."""
    now = datetime.now(timezone.utc).isoformat()
    
    preset = {
        "id": str(uuid4()),
        "name": payload.name,
        "kind": payload.kind,
        "description": payload.description or "",
        "tags": payload.tags,
        "machine_id": payload.machine_id,
        "post_id": payload.post_id,
        "units": payload.units,
        "job_source_id": payload.job_source_id,
        "source": payload.source or "manual",
        "cam_params": payload.cam_params or {},
        "export_params": payload.export_params or {},
        "neck_params": payload.neck_params or {},
        "created_at": now,
        "updated_at": now,
        "created_by": None,  # TODO: Add auth context
    }
    
    return insert_preset(preset)

@router.patch("/{preset_id}", response_model=Dict[str, Any])
def update_preset_by_id(preset_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing preset."""
    # Remove immutable fields from patch
    payload.pop("id", None)
    payload.pop("created_at", None)
    payload.pop("created_by", None)
    
    # Set updated_at
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    updated = update_preset(preset_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    
    return updated

@router.delete("/{preset_id}")
def delete_preset_by_id(preset_id: str) -> Dict[str, Any]:
    """Delete a preset."""
    success = delete_preset(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    
    return {"ok": True, "deleted": preset_id}

@router.post("/validate-template")
def validate_filename_template(body: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a filename template and return analysis."""
    template = body.get("template", "")
    
    if not template:
        raise HTTPException(status_code=400, detail="Template is required")
    
    # Validate template
    validation = validate_template(template)
    
    # Generate example filename
    example_context = {
        "preset": "Example_Preset",
        "machine": "CNC_Router_01",
        "post": "GRBL",
        "operation": "adaptive",
        "material": "Maple",
        "neck_profile": "Fender_Modern_C",
        "neck_section": "Fret_5",
        "compare_mode": "baseline",
        "job_id": "job_12345",
        "raw": "body_outline"
    }
    
    example = resolve_template(template, example_context)
    validation["example"] = example
    
    return validation

@router.post("/resolve-filename")
def resolve_filename(body: Dict[str, Any]) -> Dict[str, str]:
    """Resolve a filename template with provided context."""
    template = body.get("template")
    extension = body.get("extension", "nc")
    
    # Determine template
    preset_name = body.get("preset_name")
    neck_profile = body.get("neck_profile")
    neck_section = body.get("neck_section")
    compare_mode = body.get("compare_mode")
    operation = body.get("operation")
    
    if template is None:
        # Intelligent default
        if neck_profile or neck_section:
            template = "{preset}__{neck_profile}__{neck_section}__{date}"
        elif compare_mode:
            template = "{preset}__{compare_mode}__{post}__{date}"
        elif operation:
            template = "{preset}__{operation}__{post}__{date}"
        else:
            template = "{preset}__{post}__{date}"
    
    # Resolve filename
    filename = resolve_export_filename(
        preset_name=preset_name,
        machine_id=body.get("machine_id"),
        post_id=body.get("post_id"),
        operation=operation,
        material=body.get("material"),
        neck_profile=neck_profile,
        neck_section=neck_section,
        compare_mode=compare_mode,
        job_id=body.get("job_id"),
        raw=body.get("raw"),
        template=template,
        extension=extension
    )
    
    return {
        "filename": filename,
        "template_used": template
    }

# --- B21: Multi-Run Comparison ---

class ComparisonRunMetrics(BaseModel):
    """Performance metrics for a single run."""
    preset_id: str
    preset_name: str
    job_source_id: Optional[str] = None
    run_id: Optional[str] = None
    
    # Core metrics from job log
    sim_time_s: Optional[float] = None
    sim_energy_j: Optional[float] = None
    sim_move_count: Optional[int] = None
    sim_issue_count: Optional[int] = None
    sim_max_dev_pct: Optional[float] = None
    
    # CAM parameters
    stepover: Optional[float] = None
    feed_xy: Optional[float] = None
    strategy: Optional[str] = None
    
    # Computed scores
    efficiency_score: Optional[float] = Field(None, description="0-100 score based on time/energy/quality")
    
    created_at: Optional[str] = None

class ComparisonAnalysis(BaseModel):
    """Analysis results for multi-run comparison."""
    runs: List[ComparisonRunMetrics]
    
    # Statistical summary
    avg_time_s: Optional[float] = None
    min_time_s: Optional[float] = None
    max_time_s: Optional[float] = None
    
    avg_energy_j: Optional[float] = None
    avg_move_count: Optional[int] = None
    
    # Trends
    time_trend: Optional[str] = Field(None, description="improving | degrading | stable")
    energy_trend: Optional[str] = Field(None, description="improving | degrading | stable")
    
    # Recommendations
    best_run_id: Optional[str] = Field(None, description="Preset ID with highest efficiency score")
    worst_run_id: Optional[str] = Field(None, description="Preset ID with lowest efficiency score")
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Optimization suggestions based on historical data"
    )

class CompareRunsRequest(BaseModel):
    """Request to compare multiple preset runs."""
    preset_ids: List[str] = Field(..., min_items=2, description="At least 2 presets to compare")
    include_trends: bool = Field(True, description="Calculate trend analysis")
    include_recommendations: bool = Field(True, description="Generate optimization recommendations")

@router.post("/compare-runs", response_model=ComparisonAnalysis)
def compare_preset_runs(body: CompareRunsRequest) -> ComparisonAnalysis:
    """B21: Multi-Run Comparison"""
    from ..services.job_int_log import find_job_log_by_run_id
    
    if len(body.preset_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 presets required for comparison"
        )
    
    runs: List[ComparisonRunMetrics] = []
    
    # Fetch each preset and its associated job log
    for preset_id in body.preset_ids:
        preset_doc = get_preset(preset_id)
        if not preset_doc:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        # Extract job source ID (B19 lineage tracking)
        job_source_id = preset_doc.get("job_source_id")
        
        # Initialize metrics
        metrics = ComparisonRunMetrics(
            preset_id=preset_id,
            preset_name=preset_doc.get("name", "Unknown"),
            job_source_id=job_source_id,
            run_id=job_source_id,  # Same as source for now
            created_at=preset_doc.get("created_at")
        )
        
        # If preset was cloned from a job, fetch job log metrics
        if job_source_id:
            job_log = find_job_log_by_run_id(job_source_id)
            if job_log:
                metrics.sim_time_s = job_log.get("sim_time_s")
                metrics.sim_energy_j = job_log.get("sim_energy_j")
                metrics.sim_move_count = job_log.get("sim_move_count")
                metrics.sim_issue_count = job_log.get("sim_issue_count")
                metrics.sim_max_dev_pct = job_log.get("sim_max_dev_pct")
        
        # Extract CAM parameters from preset
        cam_params = preset_doc.get("cam_params") or {}
        metrics.stepover = cam_params.get("stepover")
        metrics.feed_xy = cam_params.get("feed_xy")
        metrics.strategy = cam_params.get("strategy")
        
        # Calculate efficiency score (0-100)
        # Formula: Balance time, energy, and quality (inverse of issues)
        if metrics.sim_time_s and metrics.sim_energy_j is not None:
            # Normalize: faster time = higher score, lower energy = higher score
            time_score = max(0, 100 - (metrics.sim_time_s / 10))  # Assume 10s = baseline
            energy_score = max(0, 100 - (metrics.sim_energy_j / 1000))  # Assume 1000J = baseline
            quality_score = max(0, 100 - (metrics.sim_issue_count or 0) * 10)  # -10 per issue
            
            metrics.efficiency_score = (time_score + energy_score + quality_score) / 3
        
        runs.append(metrics)
    
    # Sort runs by creation date for trend analysis
    runs_with_time = [r for r in runs if r.created_at]
    runs_with_time.sort(key=lambda r: r.created_at or "")
    
    # Calculate statistical summary
    times = [r.sim_time_s for r in runs if r.sim_time_s is not None]
    energies = [r.sim_energy_j for r in runs if r.sim_energy_j is not None]
    move_counts = [r.sim_move_count for r in runs if r.sim_move_count is not None]
    
    analysis = ComparisonAnalysis(
        runs=runs,
        avg_time_s=sum(times) / len(times) if times else None,
        min_time_s=min(times) if times else None,
        max_time_s=max(times) if times else None,
        avg_energy_j=sum(energies) / len(energies) if energies else None,
        avg_move_count=int(sum(move_counts) / len(move_counts)) if move_counts else None
    )
    
    # Trend analysis (if requested and enough data)
    if body.include_trends and len(runs_with_time) >= 3:
        # Simple trend: compare first 1/3 vs last 1/3
        third = len(runs_with_time) // 3
        early_runs = runs_with_time[:third]
        late_runs = runs_with_time[-third:]
        
        early_times = [r.sim_time_s for r in early_runs if r.sim_time_s]
        late_times = [r.sim_time_s for r in late_runs if r.sim_time_s]
        
        if early_times and late_times:
            early_avg = sum(early_times) / len(early_times)
            late_avg = sum(late_times) / len(late_times)
            
            if late_avg < early_avg * 0.95:  # 5% improvement
                analysis.time_trend = "improving"
            elif late_avg > early_avg * 1.05:  # 5% degradation
                analysis.time_trend = "degrading"
            else:
                analysis.time_trend = "stable"
        
        # Similar for energy
        early_energies = [r.sim_energy_j for r in early_runs if r.sim_energy_j is not None]
        late_energies = [r.sim_energy_j for r in late_runs if r.sim_energy_j is not None]
        
        if early_energies and late_energies:
            early_avg_e = sum(early_energies) / len(early_energies)
            late_avg_e = sum(late_energies) / len(late_energies)
            
            if late_avg_e < early_avg_e * 0.95:
                analysis.energy_trend = "improving"
            elif late_avg_e > early_avg_e * 1.05:
                analysis.energy_trend = "degrading"
            else:
                analysis.energy_trend = "stable"
    
    # Find best and worst runs by efficiency score
    runs_with_scores = [r for r in runs if r.efficiency_score is not None]
    if runs_with_scores:
        best_run = max(runs_with_scores, key=lambda r: r.efficiency_score or 0)
        worst_run = min(runs_with_scores, key=lambda r: r.efficiency_score or 0)
        
        analysis.best_run_id = best_run.preset_id
        analysis.worst_run_id = worst_run.preset_id
    
    # Generate recommendations (if requested)
    if body.include_recommendations:
        recommendations = []
        
        # Recommendation 1: Best configuration
        if analysis.best_run_id:
            best = next((r for r in runs if r.preset_id == analysis.best_run_id), None)
            if best:
                recommendations.append(
                    f"✅ Best performer: '{best.preset_name}' "
                    f"(Time: {best.sim_time_s:.1f}s, Efficiency: {best.efficiency_score:.0f}/100)"
                )
        
        # Recommendation 2: Time trend
        if analysis.time_trend == "degrading":
            recommendations.append(
                "⚠️ Performance degrading over time. Review recent parameter changes."
            )
        elif analysis.time_trend == "improving":
            recommendations.append(
                "✅ Performance improving. Continue current optimization direction."
            )
        
        # Recommendation 3: Strategy analysis
        strategy_times = {}
        for run in runs:
            if run.strategy and run.sim_time_s:
                if run.strategy not in strategy_times:
                    strategy_times[run.strategy] = []
                strategy_times[run.strategy].append(run.sim_time_s)
        
        if len(strategy_times) > 1:
            strategy_avgs = {
                strat: sum(times) / len(times)
                for strat, times in strategy_times.items()
            }
            best_strategy = min(strategy_avgs, key=strategy_avgs.get)
            recommendations.append(
                f"💡 '{best_strategy}' strategy shows best average time "
                f"({strategy_avgs[best_strategy]:.1f}s)"
            )
        
        # Recommendation 4: Feed rate analysis
        feeds = [(r.feed_xy, r.sim_time_s) for r in runs if r.feed_xy and r.sim_time_s]
        if len(feeds) >= 3:
            # Check correlation: higher feed = lower time?
            feeds_sorted = sorted(feeds, key=lambda x: x[0])
            if feeds_sorted[-1][1] < feeds_sorted[0][1]:  # Highest feed has lowest time
                recommendations.append(
                    f"💡 Higher feed rates correlated with better times. "
                    f"Consider increasing from {feeds_sorted[0][0]:.0f} to {feeds_sorted[-1][0]:.0f} mm/min"
                )
        
        # Recommendation 5: Issue count warning
        runs_with_issues = [r for r in runs if r.sim_issue_count and r.sim_issue_count > 0]
        if runs_with_issues:
            avg_issues = sum(r.sim_issue_count for r in runs_with_issues) / len(runs_with_issues)
            if avg_issues > 3:
                recommendations.append(
                    f"⚠️ High average issue count ({avg_issues:.1f}). Review toolpath quality."
                )
        
        analysis.recommendations = recommendations
    
    return analysis
