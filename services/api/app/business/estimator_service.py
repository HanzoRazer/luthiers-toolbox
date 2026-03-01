# services/api/app/business/estimator_service.py
"""Estimator Service - Core calculation logic."""
from __future__ import annotations
import math
from .schemas import (
    EstimateRequest, EstimateResult, WBSTask, MaterialEstimate,
    LearningCurveProjection, LearningCurvePoint, RiskFactor
)

WBS_BASELINES = {
    "acoustic_dreadnought": {"body_prep": 8.0, "top_bracing": 12.0, "back_bracing": 6.0,
        "sides_bending": 4.0, "body_assembly": 16.0, "binding": 8.0,
        "neck_carving": 12.0, "fretboard": 8.0, "neck_attach": 6.0,
        "finishing": 20.0, "setup": 4.0, "qc": 2.0},
    "acoustic_om": {"body_prep": 7.0, "top_bracing": 11.0, "back_bracing": 5.5,
        "sides_bending": 3.5, "body_assembly": 15.0, "binding": 7.5,
        "neck_carving": 11.0, "fretboard": 7.5, "neck_attach": 5.5,
        "finishing": 18.0, "setup": 4.0, "qc": 2.0},
    "electric_solid": {"body_shaping": 12.0, "body_routing": 6.0, "body_finishing": 16.0,
        "neck_carving": 10.0, "fretboard": 6.0, "neck_attach": 3.0,
        "electronics": 4.0, "hardware": 3.0, "setup": 3.0, "qc": 2.0},
    "bass_4": {"body_shaping": 14.0, "body_routing": 7.0, "body_finishing": 18.0,
        "neck_carving": 14.0, "fretboard": 8.0, "neck_attach": 4.0,
        "electronics": 4.0, "hardware": 3.0, "setup": 4.0, "qc": 2.0},
    "ukulele": {"body_prep": 3.0, "top_bracing": 4.0, "back_bracing": 2.0,
        "sides_bending": 1.5, "body_assembly": 6.0, "binding": 3.0,
        "neck_carving": 4.0, "fretboard": 3.0, "neck_attach": 2.0,
        "finishing": 8.0, "setup": 2.0, "qc": 1.0}
}

BODY_MULT = {"standard": 1.0, "cutaway_soft": 1.15, "cutaway_florentine": 1.25,
    "cutaway_venetian": 1.20, "double_cutaway": 1.30, "arm_bevel": 1.10,
    "tummy_cut": 1.08, "carved_top": 1.40}
BINDING_MULT = {"none": 1.0, "single": 1.15, "multiple": 1.35, "herringbone": 1.50}
NECK_MULT = {"standard": 1.0, "volute": 1.10, "scarf_joint": 1.15, "multi_scale": 1.40}
INLAY_MULT = {"none": 0.90, "dots": 1.0, "blocks": 1.20, "trapezoids": 1.25, "custom": 1.60}
FINISH_MULT = {"oil": 0.70, "wax": 0.65, "shellac_wipe": 0.85, "shellac_french_polish": 1.50,
    "nitro_solid": 1.20, "nitro_burst": 1.45, "nitro_vintage": 1.55, "poly_solid": 1.0, "poly_burst": 1.25}
ROSETTE_MULT = {"none": 1.0, "simple_rings": 1.05, "mosaic": 1.25, "custom_art": 1.50}
EXP_MULT = {"beginner": 1.50, "intermediate": 1.20, "experienced": 1.0, "master": 0.85}

MAT_COSTS = {
    "acoustic_dreadnought": [("Tonewoods", 350.0, 1.15), ("Hardware", 80.0, 1.05), ("Misc", 155.0, 1.08)],
    "acoustic_om": [("Tonewoods", 320.0, 1.15), ("Hardware", 80.0, 1.05), ("Misc", 143.0, 1.08)],
    "electric_solid": [("Body wood", 120.0, 1.10), ("Neck wood", 80.0, 1.10), ("Hardware", 150.0, 1.05), ("Electronics", 100.0, 1.02), ("Misc", 75.0, 1.10)],
    "bass_4": [("Body wood", 140.0, 1.10), ("Neck wood", 100.0, 1.10), ("Hardware", 180.0, 1.05), ("Electronics", 120.0, 1.02), ("Misc", 85.0, 1.10)],
    "ukulele": [("Tonewoods", 80.0, 1.15), ("Hardware", 30.0, 1.05), ("Misc", 67.0, 1.08)]
}


def compute_estimate(request: EstimateRequest) -> EstimateResult:
    inst_type = request.instrument_type.value
    baseline = WBS_BASELINES.get(inst_type, WBS_BASELINES["acoustic_dreadnought"])
    
    body_m = 1.0
    body_list = request.body_complexity if isinstance(request.body_complexity, list) else [request.body_complexity]
    for bc in body_list:
        body_m *= BODY_MULT.get(bc.value, 1.0)
    
    binding_m = BINDING_MULT.get(request.binding_body_complexity.value, 1.0)
    neck_m = NECK_MULT.get(request.neck_complexity.value, 1.0)
    inlay_m = INLAY_MULT.get(request.fretboard_inlay.value, 1.0)
    finish_m = FINISH_MULT.get(request.finish_type.value, 1.0)
    rosette_m = ROSETTE_MULT.get(request.rosette_complexity.value, 1.0)
    exp_m = EXP_MULT.get(request.builder_experience.value, 1.0)
    total_m = body_m * binding_m * neck_m * inlay_m * finish_m * rosette_m * exp_m
    
    wbs_tasks = []
    total_hrs = 0.0
    for tid, base_hrs in baseline.items():
        tm = exp_m
        if "body" in tid or "sides" in tid:
            tm *= body_m
        if "binding" in tid:
            tm *= binding_m
        if "neck" in tid:
            tm *= neck_m
        if "fretboard" in tid:
            tm *= inlay_m
        if "finish" in tid:
            tm *= finish_m
        adj = base_hrs * tm
        total_hrs += adj
        wbs_tasks.append(WBSTask(
            task_id=tid, task_name=tid.replace("_", " ").title(),
            base_hours=base_hrs, complexity_multiplier=tm, adjusted_hours=adj,
            labor_cost=adj * request.hourly_rate))
    
    mats = []
    mat_cost = 0.0
    for cat, base, waste in MAT_COSTS.get(inst_type, MAT_COSTS["acoustic_dreadnought"]):
        adj = base * waste
        mat_cost += adj
        mats.append(MaterialEstimate(category=cat, base_cost=base, waste_factor=waste, adjusted_cost=adj))
    
    learning = None
    avg_hrs = total_hrs
    first_hrs = sum(t.adjusted_hours for t in wbs_tasks[:1]) if wbs_tasks else total_hrs
    if request.batch_size > 1:
        rate = 0.85
        pts = []
        cum = 0.0
        for i in range(1, request.batch_size + 1):
            uh = total_hrs * (i ** (math.log(rate) / math.log(2)))
            cum += uh
            pts.append(LearningCurvePoint(unit_number=i, hours_per_unit=uh,
                cumulative_hours=cum, cumulative_cost=cum * request.hourly_rate))
        avg_hrs = cum / request.batch_size
        learning = LearningCurveProjection(
            first_unit_hours=total_hrs, learning_rate=rate, quantity=request.batch_size,
            points=pts, average_hours_per_unit=avg_hrs, total_hours=cum,
            efficiency_gain_pct=((total_hrs - avg_hrs) / total_hrs) * 100 if total_hrs > 0 else 0)
        total_hrs = cum
    
    labor = avg_hrs * request.hourly_rate
    mat = mat_cost if request.include_materials else 0.0
    total = labor + mat
    
    risks = []
    if total_m > 1.5:
        risks.append(RiskFactor(factor="High complexity", impact="medium",
            description="Multiple complexity features increase risk"))
    if request.builder_experience.value == "beginner":
        risks.append(RiskFactor(factor="Beginner builder", impact="high",
            description="First builds often require more time"))
    
    conf = "high" if exp_m <= 1.0 and total_m < 1.3 else ("medium" if total_m < 1.6 else "low")
    rf = 0.15 if conf == "high" else (0.25 if conf == "medium" else 0.35)
    
    return EstimateResult(
        instrument_type=inst_type, quantity=request.batch_size,
        first_unit_hours=first_hrs, average_hours_per_unit=avg_hrs, total_hours=total_hrs,
        labor_cost_per_unit=labor, material_cost_per_unit=mat, total_cost_per_unit=total,
        total_project_cost=total * request.batch_size, wbs_tasks=wbs_tasks,
        material_breakdown=mats, learning_curve=learning,
        complexity_factors_applied={"body": body_m, "binding": binding_m, "neck": neck_m,
            "inlay": inlay_m, "finish": finish_m, "rosette": rosette_m},
        total_complexity_multiplier=total_m, experience_level=request.builder_experience.value,
        experience_multiplier=exp_m, confidence_level=conf, risk_factors=risks,
        estimate_range_low=total * (1 - rf), estimate_range_high=total * (1 + rf), notes=[])

