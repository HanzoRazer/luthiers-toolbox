from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _risk_rank(r: str) -> int:
    r = (r or "").upper().strip()
    # lower is better (GREEN first)
    if r in ("GREEN", "OK", "PASS"):
        return 0
    if r in ("YELLOW", "WARN", "WARNING"):
        return 1
    if r in ("RED", "BLOCKED", "FAIL", "FAILED"):
        return 2
    return 9


def _extract_risk_and_score(feas: Any) -> Tuple[str, float]:
    """
    Accept either dict-like or pydantic-like feasibility.
    Score normalized to float (0..100 if provided, else 0..1 scaled).
    """
    if hasattr(feas, "model_dump"):
        feas = feas.model_dump()
    if hasattr(feas, "dict"):
        feas = feas.dict()
    if not isinstance(feas, dict):
        return "UNKNOWN", 0.0

    risk = str(feas.get("risk_bucket") or feas.get("risk") or "UNKNOWN")
    score = feas.get("score")
    try:
        score_f = float(score)
    except Exception:
        score_f = 0.0

    # If it's likely 0..1, scale to 0..100 for stable sorting/reporting
    if 0.0 <= score_f <= 1.0:
        score_f *= 100.0

    return risk, score_f


def _write_run_artifact_safely(*, kind: str, status: str, index_meta: Dict[str, Any], payload: Dict[str, Any]) -> str:
    """
    Use the canonical RunArtifact persistence layer from runs_v2.
    Returns artifact_id (run_id).
    """
    try:
        from app.rmos.runs_v2.store import persist_run, create_run_id
        from app.rmos.runs_v2.schemas import RunArtifact, Hashes, RunDecision
        from datetime import datetime, timezone
    except Exception as e:
        raise RuntimeError(
            "RunArtifact store not importable at app.rmos.runs_v2.store"
        ) from e

    # Build RunArtifact per governance contract
    run_id = create_run_id()
    
    # Extract required fields from index_meta
    tool_id = str(index_meta.get("tool_id") or "saw:unknown")
    mode = "saw_compare"
    
    # Extract risk level from payload if available
    risk_level = status
    if status == "OK" and isinstance(payload, dict):
        feas = payload.get("feasibility")
        if feas:
            extracted_risk, _ = _extract_risk_and_score(feas)
            risk_level = extracted_risk
    
    # Create minimal hashes (feasibility_sha256 will be computed from payload)
    # For now, use placeholder - ideally compute actual SHA256 of feasibility
    import hashlib
    import json
    feas_str = json.dumps(payload.get("feasibility", {}), sort_keys=True)
    feasibility_sha256 = hashlib.sha256(feas_str.encode()).hexdigest()
    
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc),
        event_type=kind,
        status=status,
        mode=mode,
        tool_id=tool_id,
        # Context fields
        workflow_session_id=index_meta.get("session_id"),
        material_id=index_meta.get("material_id"),
        machine_id=index_meta.get("machine_id"),
        # Required governance fields
        hashes=Hashes(feasibility_sha256=feasibility_sha256),
        decision=RunDecision(risk_level=risk_level),
        # Store batch_label and session_id at top level of meta for filtering
        meta={
            "batch_label": index_meta.get("batch_label"),
            "session_id": index_meta.get("session_id"),
            "payload": payload,
            "index_meta": index_meta
        }
    )
    
    persisted = persist_run(artifact)
    return persisted.run_id


def _compute_saw_feasibility(design: Dict[str, Any], context: Dict[str, Any]) -> Any:
    """
    Calls Saw Lab domain feasibility.
    This stays in services layer to avoid RMOS<->Saw domain entanglement.
    """
    from app.saw_lab import SawLabService, SawDesign, SawContext
    
    # Convert dict to Pydantic models
    # This is a best-effort conversion - adjust based on actual schema requirements
    try:
        saw_design = SawDesign(**design) if design else SawDesign()
        saw_context = SawContext(**context) if context else SawContext()
    except Exception:
        # Fallback: use dicts directly if Pydantic conversion fails
        saw_design = design
        saw_context = context
    
    svc = SawLabService()
    return svc.check_feasibility(saw_design, saw_context)


def compare_saw_candidates(
    *,
    candidates: List[Dict[str, Any]],
    batch_label: Optional[str],
    session_id: Optional[str],
) -> Dict[str, Any]:
    """
    For each candidate:
      - run saw feasibility
      - persist a RunArtifact (always; OK/BLOCKED/ERROR)
      - return artifact_id + sortable fields
    """
    results: List[Dict[str, Any]] = []
    child_refs: List[Dict[str, Any]] = []

    for c in candidates:
        candidate_id = str(c.get("candidate_id") or "")
        label = c.get("label")
        design = c.get("design") or {}
        context = c.get("context") or {}

        # best-effort index meta: helps /api/runs queries + UI panels
        index_meta = {
            "session_id": session_id,
            "batch_label": batch_label,
            "candidate_id": candidate_id,
            "tool_kind": "saw_lab",
            "tool_id": context.get("tool_id") or context.get("blade_id"),
            "material_id": context.get("material_id"),
            "machine_id": context.get("machine_id"),
        }

        try:
            feas = _compute_saw_feasibility(design, context)
            risk, score = _extract_risk_and_score(feas)
            status = "OK" if _risk_rank(risk) < 2 else "BLOCKED"

            artifact_id = _write_run_artifact_safely(
                kind="saw_compare_feasibility",
                status=status,
                index_meta=index_meta,
                payload={
                    "label": label,
                    "design": design,
                    "context": context,
                    "feasibility": feas.model_dump() if hasattr(feas, "model_dump") else (feas.dict() if hasattr(feas, "dict") else feas),
                },
            )

            results.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "artifact_id": artifact_id,
                    "risk_bucket": risk,
                    "score": float(score),
                }
            )

            child_refs.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "artifact_id": artifact_id,
                    "status": status,
                    "risk_bucket": risk,
                    "score": float(score),
                }
            )

        except Exception as e:
            # Always persist ERROR artifacts for forensics/diff
            artifact_id = _write_run_artifact_safely(
                kind="saw_compare_feasibility",
                status="ERROR",
                index_meta=index_meta,
                payload={
                    "label": label,
                    "design": design,
                    "context": context,
                    "error": {"type": type(e).__name__, "message": str(e)},
                },
            )

            results.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "artifact_id": artifact_id,
                    "risk_bucket": "ERROR",
                    "score": 0.0,
                }
            )

            child_refs.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "artifact_id": artifact_id,
                    "status": "ERROR",
                    "risk_bucket": "ERROR",
                    "score": 0.0,
                }
            )

    # sort: GREEN first, then higher score
    results.sort(key=lambda x: (_risk_rank(x["risk_bucket"]), -float(x["score"])))

    # --- Parent batch artifact (references all children) ---
    # This ensures a single artifact can represent the compare run,
    # and the UI/diff can treat it as a "batch container".
    batch_index_meta = {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": "saw_lab",
        "child_count": len(child_refs),
    }

    # Summaries for quick UI rendering
    counts = {"OK": 0, "BLOCKED": 0, "ERROR": 0}
    for r in child_refs:
        st = str(r.get("status") or "ERROR").upper()
        if st not in counts:
            st = "ERROR"
        counts[st] += 1

    parent_artifact_id = _write_run_artifact_safely(
        kind="saw_compare_batch",
        status="OK" if counts["ERROR"] == 0 else "ERROR",
        index_meta=batch_index_meta,
        payload={
            "batch_label": batch_label,
            "session_id": session_id,
            "summary": {
                "counts": counts,
                "sorted_by": "risk_rank ASC, score DESC",
            },
            "children": child_refs,
        },
    )

    return {
        "parent_artifact_id": parent_artifact_id,
        "items": results,
    }
