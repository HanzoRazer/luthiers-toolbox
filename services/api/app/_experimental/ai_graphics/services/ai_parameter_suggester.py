"""
AI Graphics Parameter Suggester

Main entrypoint for AI rosette suggestions with RMOS feedback loop.

Flow:
1. Generate raw RosetteParamSpec candidates via LLM
2. Score each with RMOS feasibility (including ring diagnostics)
3. Run optional refinement rounds (mutate weak designs based on ring feedback)
4. Filter/mark RED designs as non-recommended
5. Sort by ai_score and return batch
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from ..schemas.ai_schemas import (
    AiRosettePromptInput,
    AiRosetteSuggestion,
    AiRosetteSuggestionBatch,
    AiFeasibilitySnapshot,
    AiRingSummary,
    RosetteParamSpec,
    RiskBucket,
    score_suggestion_from_feasibility,
    mutate_design_from_feasibility,
)
from ..sessions import (
    fingerprint_spec,
    get_or_create_session,
    mark_explored,
    is_explored,
    add_suggestion_to_history,
)
from .llm_client import generate_rosette_param_candidates


# ---------------------------------------------------------------------------
# RMOS Integration Helpers
# ---------------------------------------------------------------------------

def _build_mock_feasibility_snapshot(spec: RosetteParamSpec) -> AiFeasibilitySnapshot:
    """
    Build a mock feasibility snapshot for testing.
    
    In production, this calls RMOS compute_feasibility().
    """
    # Mock scoring based on ring widths
    ring_summaries: List[AiRingSummary] = []
    worst_index = None
    worst_risk = None
    
    for rp in spec.ring_params:
        width = rp.width_mm
        
        # Simple heuristic: narrow rings are risky
        if width < 2.0:
            risk = RiskBucket.RED
        elif width < 3.0:
            risk = RiskBucket.YELLOW
        else:
            risk = RiskBucket.GREEN
        
        ring_summaries.append(
            AiRingSummary(
                ring_index=rp.ring_index,
                width_mm=width,
                risk_bucket=risk,
                utilization_score=min(100.0, width * 15),
            )
        )
        
        # Track worst
        risk_order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
        if worst_risk is None or risk_order.get(risk.value, 0) > risk_order.get(worst_risk.value, 0):
            worst_index = rp.ring_index
            worst_risk = risk
    
    # Overall score based on ring risks
    red_count = sum(1 for r in ring_summaries if r.risk_bucket == RiskBucket.RED)
    yellow_count = sum(1 for r in ring_summaries if r.risk_bucket == RiskBucket.YELLOW)
    
    overall = 100.0 - (red_count * 30) - (yellow_count * 10)
    overall = max(0.0, min(100.0, overall))
    
    # Overall risk bucket
    if red_count > 0:
        overall_risk = RiskBucket.RED
    elif yellow_count > 0:
        overall_risk = RiskBucket.YELLOW
    else:
        overall_risk = RiskBucket.GREEN
    
    return AiFeasibilitySnapshot(
        overall_score=overall,
        risk_bucket=overall_risk,
        estimated_cut_time_min=len(spec.ring_params) * 2.5,  # Mock
        material_efficiency=0.75,  # Mock
        worst_ring_index=worst_index,
        worst_ring_risk=worst_risk,
        rings=ring_summaries,
    )


def _evaluate_designs(
    specs: List[RosetteParamSpec],
    tool_diameter_mm: float = 3.175,
) -> List[AiRosetteSuggestion]:
    """
    Evaluate a list of specs and convert to suggestions with feasibility.
    """
    suggestions: List[AiRosetteSuggestion] = []
    
    for spec in specs:
        # Get feasibility snapshot (mock for now, replace with RMOS call)
        snap = _build_mock_feasibility_snapshot(spec)
        ai_score = score_suggestion_from_feasibility(snap)
        
        # Policy: recommended if no RED worst ring and overall not RED
        recommended = True
        if snap.risk_bucket == RiskBucket.RED:
            recommended = False
        if snap.worst_ring_risk == RiskBucket.RED:
            recommended = False
        
        suggestions.append(
            AiRosetteSuggestion(
                suggestion_id=str(uuid.uuid4()),
                params=spec,
                summary="AI-generated rosette design",
                notes=spec.notes,
                feasibility=snap,
                ai_score=ai_score,
                recommended=recommended,
            )
        )
    
    return suggestions


# ---------------------------------------------------------------------------
# Main Entrypoint
# ---------------------------------------------------------------------------

def suggest_rosette_parameters(
    req: AiRosettePromptInput,
) -> AiRosetteSuggestionBatch:
    """
    Main entrypoint for AI rosette suggestions.
    
    Flow:
    1. Use LLM to generate raw RosetteParamSpec candidates
    2. For each candidate:
        - Build feasibility snapshot (via RMOS)
        - Compute ai_score with ring penalties
    3. Run optional refinement rounds:
        - Select weak-but-promising designs
        - Mutate based on ring diagnostics
        - Re-evaluate and add to pool
    4. Filter duplicates via session fingerprinting
    5. Sort by ai_score (descending)
    """
    # Session handling
    session_id = req.session_id or str(uuid.uuid4())
    session = get_or_create_session(session_id)
    
    # Seed seen fingerprints from session history
    seen = set(session.explored_fingerprints)
    
    # 1) Base generation via LLM
    raw_candidates = generate_rosette_param_candidates(
        prompt=req.prompt,
        count=req.count,
    )
    
    # Filter already-explored designs
    filtered_candidates = []
    for spec in raw_candidates:
        fp = fingerprint_spec(spec)
        if fp not in seen:
            seen.add(fp)
            filtered_candidates.append(spec)
    
    # Evaluate base generation
    suggestions = _evaluate_designs(filtered_candidates)
    
    # 2) Refinement rounds (RMOS feedback loop)
    rounds = max(0, min(req.refine_rounds, 3))
    target_min_score = req.target_min_score
    
    for _round in range(rounds):
        # Select candidates to refine:
        # - Below target_min_score (if set)
        # - Or having YELLOW worst ring
        # - But not completely RED-overall (hopeless)
        to_refine = []
        
        for s in suggestions:
            snap = s.feasibility
            if snap is None:
                continue
            if snap.risk_bucket == RiskBucket.RED:
                continue  # Too risky, skip
            
            below_target = (
                target_min_score is not None
                and snap.overall_score < target_min_score
            )
            has_yellow_ring = (
                snap.worst_ring_risk is not None
                and snap.worst_ring_risk == RiskBucket.YELLOW
            )
            
            if below_target or has_yellow_ring:
                to_refine.append((s.params, snap))
        
        if not to_refine:
            break  # Nothing to refine
        
        # Mutate and re-evaluate
        refined_specs = []
        for spec, snap in to_refine:
            mutated = mutate_design_from_feasibility(spec, snap)
            fp = fingerprint_spec(mutated)
            if fp not in seen:
                seen.add(fp)
                refined_specs.append(mutated)
        
        if not refined_specs:
            break
        
        refined_suggestions = _evaluate_designs(refined_specs)
        suggestions.extend(refined_suggestions)
    
    # 3) Mark all explored fingerprints in session
    all_fingerprints = [fingerprint_spec(s.params) for s in suggestions]
    mark_explored(session_id, all_fingerprints)
    
    # Add to session history
    for s in suggestions:
        snap = s.feasibility
        add_suggestion_to_history(
            session_id=session_id,
            suggestion_id=s.suggestion_id,
            overall_score=snap.overall_score if snap else 0.0,
            risk_bucket=snap.risk_bucket if snap else None,
            worst_ring_risk=snap.worst_ring_risk if snap else None,
        )
    
    # 4) Sort by ai_score (best first)
    suggestions.sort(key=lambda s: s.ai_score, reverse=True)
    
    return AiRosetteSuggestionBatch(suggestions=suggestions)
