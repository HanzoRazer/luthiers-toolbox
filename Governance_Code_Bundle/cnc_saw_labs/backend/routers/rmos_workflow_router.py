from app.rmos.engine import load_rmos_engine
from app.rmos.hashing import stable_hash
2) Replace the two stubs with real engine calls
Replace _compute_feasibility_server() and _generate_toolpaths_server() with:
def _compute_feasibility_server(design: Dict[str, Any], ctx: RmosContextIn, *, source: str) -> FeasibilityResult:
    engine = load_rmos_engine()

    context_dict = ctx.model_dump()
    design_hash = stable_hash(design)
    context_hash = stable_hash(context_dict)

    raw = engine.compute_feasibility_for_design(design, context_dict)

    # Normalize fields
    score = float(raw.get("score", 0.0))
    risk_bucket = RiskBucket(str(raw.get("risk_bucket", "UNKNOWN")).upper())
    warnings = list(raw.get("warnings", [])) if raw.get("warnings") else []

    # Versions (repo-wide requirements)
    policy_version = engine.get_policy_version()
    calculator_versions = engine.get_calculator_versions()

    # Hash feasibility payload deterministically (for diff/audit)
    feasibility_core = {
        "score": score,
        "risk_bucket": risk_bucket.value,
        "warnings": warnings,
        "details": raw.get("details"),
        "policy_version": policy_version,
        "calculator_versions": calculator_versions,
        "design_hash": design_hash,
        "context_hash": context_hash,
        "tool_id": ctx.tool_id,
        "material_id": ctx.material_id,
        "machine_id": ctx.machine_id,
        "source": source,
    }
    feasibility_hash = stable_hash(feasibility_core)

    return FeasibilityResult(
        score=score,
        risk_bucket=risk_bucket,
        warnings=warnings,
        meta={
            "source": source,  # MUST be server_recompute for toolpaths in prod
            "tool_id": ctx.tool_id,
            "material_id": ctx.material_id,
            "machine_id": ctx.machine_id,
            "policy_version": policy_version,
            "calculator_versions": calculator_versions,
            "design_hash": design_hash,
            "context_hash": context_hash,
            "feasibility_hash": feasibility_hash,
        },
    )


def _generate_toolpaths_server(design: Dict[str, Any], ctx: RmosContextIn) -> ToolpathPlanRef:
    engine = load_rmos_engine()

    context_dict = ctx.model_dump()
    design_hash = stable_hash(design)
    context_hash = stable_hash(context_dict)

    raw = engine.generate_toolpaths_for_design(design, context_dict)

    plan_id = str(raw.get("plan_id", "plan_TODO"))
    policy_version = engine.get_policy_version()
    calculator_versions = engine.get_calculator_versions()

    toolpath_core = {
        "plan_id": plan_id,
        "raw": raw,
        "policy_version": policy_version,
        "calculator_versions": calculator_versions,
        "design_hash": design_hash,
        "context_hash": context_hash,
        "tool_id": ctx.tool_id,
        "material_id": ctx.material_id,
        "machine_id": ctx.machine_id,
    }
    toolpath_hash = stable_hash(toolpath_core)

    return ToolpathPlanRef(
        plan_id=plan_id,
        meta={
            "toolpath_hash": toolpath_hash,
            "policy_version": policy_version,
            "calculator_versions": calculator_versions,
            "design_hash": design_hash,
            "context_hash": context_hash,
            "plan_summary": raw.get("summary") or raw.get("plan_summary") or {},
            "tool_id": ctx.tool_id,
            "material_id": ctx.material_id,
            "machine_id": ctx.machine_id,
        },