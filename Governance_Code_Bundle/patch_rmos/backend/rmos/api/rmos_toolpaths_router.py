from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, Optional

from app.rmos.runs import RunStore
from app.rmos.runs.schemas import RunArtifact, RunDecision, Hashes, RunOutputs
from app.rmos.runs.hashing import sha256_json, sha256_text, sha256_toolpaths_payload, summarize_request


router = APIRouter()
RUN_STORE = RunStore()

# Safety policy (hardcoded production invariants)
BLOCK_ON_RED = True
TREAT_UNKNOWN_AS_RED = True


@router.post("/api/rmos/toolpaths")
def rmos_toolpaths(req: Dict[str, Any]) -> Dict[str, Any]:
    tool_id = str(req.get("tool_id") or "")
    mode = resolve_mode(tool_id)

    # 1) Recompute feasibility server-side (mandatory)
    feasibility = compute_feasibility_server_side(tool_id=tool_id, req=req)

    # 2) Derive decision (mode-specific; saw enforced)
    decision_obj = compute_safety_decision(mode=mode, feasibility=feasibility)

    # 3) Always compute feasibility hash
    feas_hash = sha256_json(feasibility)

    # 4) Block if policy says so (BLOCKED artifact)
    if should_block(mode=mode, decision=decision_obj):
        run_id = RUN_STORE.new_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status="BLOCKED",
            request_summary=summarize_request(req),
            feasibility=feasibility,
            decision=decision_obj,
            hashes=Hashes(feasibility_sha256=feas_hash),
            outputs=RunOutputs(),
            meta={"policy": {"block_on_red": BLOCK_ON_RED, "treat_unknown_as_red": TREAT_UNKNOWN_AS_RED}},
        )
        path = RUN_STORE.write_artifact(artifact)

        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "Toolpath generation blocked by server-side safety policy.",
                "run_id": run_id,
                "run_artifact_path": str(path),
                "decision": artifact.decision.model_dump(),
                # Optional: include feasibility for debug; remove if too large
                "authoritative_feasibility": feasibility,
            },
        )

    # 5) Generate toolpaths (OK artifact) or persist ERROR artifact
    try:
        toolpaths_payload = dispatch_toolpaths(mode=mode, req=req, feasibility=feasibility)

        toolpaths_hash = sha256_toolpaths_payload(toolpaths_payload)

        outputs = RunOutputs()
        gcode_hash: Optional[str] = None
        opplan_hash: Optional[str] = None

        gcode = toolpaths_payload.get("gcode_text") or toolpaths_payload.get("gcode")
        if isinstance(gcode, str):
            gcode_hash = sha256_text(gcode)
            outputs.gcode_text = gcode if len(gcode) <= 200_000 else None

        opplan = toolpaths_payload.get("opplan_json") or toolpaths_payload.get("opplan")
        if isinstance(opplan, dict):
            opplan_hash = sha256_json(opplan)
            outputs.opplan_json = opplan

        run_id = RUN_STORE.new_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status="OK",
            request_summary=summarize_request(req),
            feasibility=feasibility,
            decision=decision_obj,
            hashes=Hashes(
                feasibility_sha256=feas_hash,
                toolpaths_sha256=toolpaths_hash,
                gcode_sha256=gcode_hash,
                opplan_sha256=opplan_hash,
            ),
            outputs=outputs,
            meta={"dispatch": {"mode": mode}},
        )
        path = RUN_STORE.write_artifact(artifact)

        # Return payload + audit linkage
        toolpaths_payload["_run_id"] = run_id
        toolpaths_payload["_run_artifact_path"] = str(path)
        toolpaths_payload["_hashes"] = artifact.hashes.model_dump()
        return toolpaths_payload

    except HTTPException:
        raise
    except Exception as e:
        run_id = RUN_STORE.new_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status="ERROR",
            request_summary=summarize_request(req),
            feasibility=feasibility,
            decision=decision_obj,
            hashes=Hashes(feasibility_sha256=feas_hash),
            outputs=RunOutputs(),
            meta={"exception": {"type": type(e).__name__, "message": str(e)}},
        )
        path = RUN_STORE.write_artifact(artifact)
        raise HTTPException(
            status_code=500,
            detail={"error": "TOOLPATHS_ERROR", "run_id": run_id, "run_artifact_path": str(path)},
        )


# -----------------------------
# Mode + policy helpers
# -----------------------------

def resolve_mode(tool_id: str) -> str:
    if tool_id.startswith("saw:"):
        return "saw"
    return "unknown"


def should_block(*, mode: str, decision: RunDecision) -> bool:
    if mode != "saw":
        return False
    rl = (decision.risk_level or "UNKNOWN").upper()
    if rl == "RED" and BLOCK_ON_RED:
        return True
    if rl == "UNKNOWN" and TREAT_UNKNOWN_AS_RED:
        return True
    return False


def compute_safety_decision(*, mode: str, feasibility: Dict[str, Any]) -> RunDecision:
    """
    Normalizes safety decision from feasibility payload into RunDecision.
    For saw mode, expects feasibility to contain or imply safety fields.
    """
    safety = find_safety_object(feasibility)

    if not safety:
        return RunDecision(
            risk_level="UNKNOWN",
            block_reason="Missing safety decision in feasibility payload",
            warnings=["No safety decision returned; treating as unsafe for production toolpaths."],
            details={"payload_keys": sorted(list(feasibility.keys()))},
        )

    risk_level = str(safety.get("risk_level") or safety.get("risk") or "UNKNOWN").upper()
    score = safety.get("score")
    warnings = safety.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = [str(warnings)]
    block_reason = safety.get("block_reason") or safety.get("reason")

    details = safety.get("details") or {}
    if not isinstance(details, dict):
        details = {"details": details}

    return RunDecision(
        risk_level=risk_level,
        score=score if isinstance(score, (int, float)) else None,
        block_reason=str(block_reason) if block_reason else None,
        warnings=[str(w) for w in warnings],
        details=details,
    )


def find_safety_object(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # direct
    if isinstance(payload.get("risk_level"), str) or isinstance(payload.get("risk"), str):
        return payload

    # nested common shapes
    for path in (
        ("safety",),
        ("feasibility", "safety"),
        ("result", "safety"),
        ("saw", "safety"),
    ):
        cur: Any = payload
        ok = True
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                ok = False
                break
            cur = cur[k]
        if ok and isinstance(cur, dict):
            return cur

    return None


# -----------------------------
# Replace these with real engines
# -----------------------------

def compute_feasibility_server_side(*, tool_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
    """
    TODO: Replace with your canonical feasibility dispatcher:
      compute_feasibility_internal(tool_id=tool_id, req=clean_req, context="toolpaths")

    For now: returns an UNKNOWN decision unless req contains a safety block.
    """
    clean_req = dict(req)
    clean_req.pop("feasibility", None)

    # If caller provided a precomputed safety blob for testing, allow it to flow through feasibility shape.
    safety = clean_req.get("safety")
    if isinstance(safety, dict):
        return {"safety": safety}

    # Default: no safety computed => UNKNOWN => blocked (saw mode)
    return {"safety": {"risk_level": "UNKNOWN", "block_reason": "Feasibility engine not wired yet"}}


def dispatch_toolpaths(*, mode: str, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    TODO: Replace with actual per-mode toolpath builders.
    Must accept authoritative feasibility.
    """
    if mode == "saw":
        # Placeholder gcode skeleton
        gcode = "G90\nG21\n; SAW TOOLPATH PLACEHOLDER\nM2\n"
        return {"mode": "saw", "gcode_text": gcode, "opplan_json": {"kind": "saw_opplan", "version": 1}}
    raise HTTPException(status_code=400, detail={"error": "UNKNOWN_MODE", "mode": mode})
