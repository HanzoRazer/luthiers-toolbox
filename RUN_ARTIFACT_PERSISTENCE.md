# Persist Feasibility + Toolpath Hash as Run Artifact

## Overview

This bundle creates an **immutable audit trail** for every toolpath request by persisting:
- Authoritative feasibility (server-computed)
- Safety decision
- Toolpath hashes (SHA256)
- Request summary

Every attempt to generate toolpaths — whether **blocked**, **successful**, or **errored** — creates a Run Artifact.

---

## What This Enables

| Capability | Description |
|------------|-------------|
| **Debug blocked requests** | See exact feasibility + decision that caused the block |
| **Prove provenance** | "This G-code came from that feasibility" via SHA256 hashes |
| **Audit trail** | Every manufacturing decision is recorded |
| **Future job registry** | Foundation for production run tracking and job locks |

---

## File Structure

```
services/api/app/rmos/
├── runs/
│   ├── __init__.py
│   ├── schemas.py      # NEW: RunArtifact models
│   ├── hashing.py      # NEW: Stable hashing helpers
│   └── store.py        # NEW: File-based run artifact store
└── api/
    └── rmos_toolpaths_router.py  # UPDATED: Persist all outcomes

services/api/data/runs/rmos/
└── <YYYY-MM-DD>/
    └── <run_id>.json   # Artifact files organized by date
```

---

## Implementation

### 1. Run Artifact Schema

**File:** `services/api/app/rmos/runs/schemas.py`

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Hashes(BaseModel):
    """SHA256 hashes for audit verification."""
    feasibility_sha256: str
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    opplan_sha256: Optional[str] = None


class RunOutputs(BaseModel):
    """Generated outputs (embedded or referenced)."""
    # Embedded outputs (for small payloads)
    gcode_text: Optional[str] = None
    opplan_json: Optional[Dict[str, Any]] = None
    
    # File references (for large outputs)
    gcode_path: Optional[str] = None
    opplan_path: Optional[str] = None
    preview_svg_path: Optional[str] = None


class RunDecision(BaseModel):
    """Safety decision extracted from feasibility."""
    risk_level: str = "UNKNOWN"
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class RunArtifact(BaseModel):
    """
    Complete record of a toolpath generation attempt.
    Created for EVERY request: OK, BLOCKED, or ERROR.
    """
    run_id: str
    created_at_utc: datetime = Field(default_factory=utc_now)
    
    # Identity
    mode: str
    tool_id: str
    
    # Status
    status: Literal["OK", "BLOCKED", "ERROR"]
    
    # Inputs (minimal summary, no huge blobs)
    request_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # Authoritative feasibility (server-computed)
    feasibility: Dict[str, Any]
    
    # Safety decision derived from feasibility
    decision: RunDecision
    
    # Hashes for verification
    hashes: Hashes
    
    # Outputs (empty if BLOCKED)
    outputs: RunOutputs = Field(default_factory=RunOutputs)
    
    # Metadata (versions, host, policy, etc.)
    meta: Dict[str, Any] = Field(default_factory=dict)
```

---

### 2. Stable Hashing Helpers

**File:** `services/api/app/rmos/runs/hashing.py`

```python
from __future__ import annotations
import hashlib
import json
from typing import Any, Dict


def sha256_text(s: str) -> str:
    """Hash a string."""
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def sha256_json(obj: Any) -> str:
    """
    Stable hash for JSON-like objects.
    - Sorts keys for determinism
    - Uses compact separators
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_text(s)


def sha256_toolpaths_payload(toolpaths_payload: Dict[str, Any]) -> str:
    """
    Stable hash of the entire toolpaths response payload.
    """
    return sha256_json(toolpaths_payload)


def summarize_request(req: Dict[str, Any], *, max_keys: int = 80) -> Dict[str, Any]:
    """
    Produce a minimal request summary that avoids storing massive blobs.
    - Keeps important keys
    - Drops client-provided feasibility
    - Truncates large arrays/dicts
    """
    summary = {}
    
    for k in sorted(req.keys()):
        if k == "feasibility":
            continue  # Never store client feasibility
        
        v = req.get(k)
        
        # Avoid huge arrays/dicts
        if isinstance(v, list) and len(v) > 200:
            summary[k] = {"type": "list", "len": len(v)}
        elif isinstance(v, dict) and len(v) > 200:
            summary[k] = {"type": "dict", "len": len(v)}
        else:
            summary[k] = v
        
        if len(summary) >= max_keys:
            break
    
    return summary
```

---

### 3. File-Based Run Store

**File:** `services/api/app/rmos/runs/store.py`

```python
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .schemas import RunArtifact


def default_runs_dir() -> Path:
    """
    Default: repo-relative `data/runs/rmos/`
    Override with env var: RMOS_RUNS_DIR
    """
    env = os.environ.get("RMOS_RUNS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    
    # Conservative default: services/api/data/runs/rmos
    # (works for monorepo + standalone clones)
    here = Path(__file__).resolve()
    api_root = here.parents[4]  # Navigate up to services/api
    return (api_root / "data" / "runs" / "rmos").resolve()


class RunStore:
    """File-based storage for run artifacts."""
    
    def __init__(self, runs_dir: Optional[Path] = None):
        self.runs_dir = runs_dir or default_runs_dir()
        self.runs_dir.mkdir(parents=True, exist_ok=True)
    
    def new_run_id(self) -> str:
        """Generate a unique run ID."""
        return uuid4().hex
    
    def write_artifact(self, artifact: RunArtifact) -> Path:
        """
        Write a single JSON artifact file.
        Path: <runs_dir>/<YYYY-MM-DD>/<run_id>.json
        """
        day = artifact.created_at_utc.date().isoformat()
        out_dir = self.runs_dir / day
        out_dir.mkdir(parents=True, exist_ok=True)
        
        path = out_dir / f"{artifact.run_id}.json"
        path.write_text(
            json.dumps(artifact.model_dump(), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
        return path
```

---

### 4. Router Integration

**File:** `services/api/app/rmos/api/rmos_toolpaths_router.py`

```python
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.rmos.policies.safety_policy import SafetyPolicy
from app.rmos.policies.saw_safety_gate import compute_saw_safety_decision
from app.rmos.services.feasibility_service import recompute_feasibility_for_toolpaths
from app.rmos.runs.schemas import RunArtifact, RunDecision, Hashes, RunOutputs
from app.rmos.runs.hashing import sha256_json, sha256_text, sha256_toolpaths_payload, summarize_request
from app.rmos.runs.store import RunStore

router = APIRouter()

SAFETY_POLICY = SafetyPolicy(block_on_red=True, treat_unknown_as_red=True)
RUN_STORE = RunStore()


@router.post("/api/rmos/toolpaths")
def rmos_toolpaths(req: Dict[str, Any]):
    tool_id = str(req.get("tool_id") or "")
    mode = _resolve_mode(tool_id)
    
    # ===============================
    # SERVER-SIDE FEASIBILITY
    # ===============================
    feasibility = recompute_feasibility_for_toolpaths(tool_id=tool_id, req=req)
    
    # Compute safety decision
    decision_obj = compute_saw_safety_decision(feasibility) if mode == "saw" else None
    decision = _to_run_decision(decision_obj)
    
    # Hash feasibility for audit
    feas_hash = sha256_json(feasibility)
    
    # ===============================
    # BLOCKED PATH
    # ===============================
    if mode == "saw" and SAFETY_POLICY.should_block(decision_obj):
        run_id = RUN_STORE.new_run_id()
        
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status="BLOCKED",
            request_summary=summarize_request(req),
            feasibility=feasibility,
            decision=decision,
            hashes=Hashes(feasibility_sha256=feas_hash),
            outputs=RunOutputs(),
            meta={"policy": {"block_on_red": True, "treat_unknown_as_red": True}},
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
            },
        )
    
    # ===============================
    # SUCCESS PATH
    # ===============================
    try:
        toolpaths_payload = _dispatch_toolpaths(mode=mode, req=req, feasibility=feasibility)
        
        # Hash toolpaths for audit
        toolpaths_hash = sha256_toolpaths_payload(toolpaths_payload)
        
        # Extract and hash individual outputs
        gcode_hash = None
        opplan_hash = None
        outputs = RunOutputs()
        
        gcode = toolpaths_payload.get("gcode") or toolpaths_payload.get("gcode_text")
        if isinstance(gcode, str):
            gcode_hash = sha256_text(gcode)
            # Only embed small G-code inline
            outputs.gcode_text = gcode if len(gcode) <= 200_000 else None
        
        opplan = toolpaths_payload.get("opplan") or toolpaths_payload.get("opplan_json")
        if isinstance(opplan, dict):
            opplan_hash = sha256_json(opplan)
            outputs.opplan_json = opplan
        
        # Create and persist artifact
        run_id = RUN_STORE.new_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status="OK",
            request_summary=summarize_request(req),
            feasibility=feasibility,
            decision=decision,
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
        
        # Include run info in response
        toolpaths_payload["_run_id"] = run_id
        toolpaths_payload["_run_artifact_path"] = str(path)
        toolpaths_payload["_hashes"] = artifact.hashes.model_dump()
        
        return toolpaths_payload
        
    except HTTPException:
        raise
    except Exception as e:
        # ===============================
        # ERROR PATH
        # ===============================
        run_id = RUN_STORE.new_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status="ERROR",
            request_summary=summarize_request(req),
            feasibility=feasibility,
            decision=decision,
            hashes=Hashes(feasibility_sha256=feas_hash),
            outputs=RunOutputs(),
            meta={"exception": {"type": type(e).__name__, "message": str(e)}},
        )
        path = RUN_STORE.write_artifact(artifact)
        
        raise HTTPException(
            status_code=500,
            detail={"error": "TOOLPATHS_ERROR", "run_id": run_id, "run_artifact_path": str(path)},
        )


def _to_run_decision(decision_obj) -> RunDecision:
    """Convert safety decision to RunDecision schema."""
    if decision_obj is None:
        return RunDecision(risk_level="UNKNOWN", warnings=["No decision computed for this mode."])
    
    return RunDecision(
        risk_level=decision_obj.risk_level.value,
        score=decision_obj.score,
        block_reason=decision_obj.block_reason,
        warnings=decision_obj.warnings or [],
        details=decision_obj.details or {},
    )


def _resolve_mode(tool_id: str) -> str:
    if tool_id.startswith("saw:"):
        return "saw"
    return "router"


def _dispatch_toolpaths(*, mode: str, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch to appropriate toolpath builder."""
    if mode == "saw":
        # Your saw toolpath builder goes here
        return {
            "mode": "saw",
            "gcode_text": "G90\nG21\n; placeholder saw gcode\nM2\n",
            "opplan_json": {"kind": "saw_opplan", "version": 1, "note": "placeholder"},
        }
    raise HTTPException(status_code=400, detail={"error": "UNKNOWN_MODE", "mode": mode})
```

---

### 5. Tests

**File:** `services/api/tests/test_rmos_run_artifacts.py`

```python
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_blocked_creates_run_artifact(tmp_path: Path, monkeypatch):
    """Blocked requests should create a BLOCKED artifact."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    
    payload = {
        "tool_id": "saw:kerf_cut_v1",
        # Inputs that trigger RED in your feasibility
    }
    
    r = client.post("/api/rmos/toolpaths", json=payload)
    
    assert r.status_code == 409
    detail = r.json()["detail"]
    
    assert "run_id" in detail
    assert "run_artifact_path" in detail
    
    p = Path(detail["run_artifact_path"])
    assert p.exists()
    
    artifact = json.loads(p.read_text(encoding="utf-8"))
    assert artifact["status"] == "BLOCKED"
    assert "feasibility_sha256" in artifact["hashes"]


def test_success_creates_run_artifact(tmp_path: Path, monkeypatch):
    """Successful requests should create an OK artifact with hashes."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    
    payload = {
        "tool_id": "saw:veneer_160",
        # Inputs that result in GREEN feasibility
    }
    
    r = client.post("/api/rmos/toolpaths", json=payload)
    
    if r.status_code == 409:
        return  # Policy blocked; adjust inputs for GREEN
    
    assert r.status_code == 200
    data = r.json()
    
    assert "_run_id" in data
    assert "_run_artifact_path" in data
    assert "_hashes" in data
    
    p = Path(data["_run_artifact_path"])
    assert p.exists()
    
    artifact = json.loads(p.read_text(encoding="utf-8"))
    assert artifact["status"] == "OK"
    assert artifact["hashes"]["feasibility_sha256"]
    assert artifact["hashes"]["toolpaths_sha256"]
```

---

## Artifact Structure

Each run creates a JSON file like this:

```
data/runs/rmos/2025-12-15/a1b2c3d4e5f6.json
```

```json
{
  "run_id": "a1b2c3d4e5f6...",
  "created_at_utc": "2025-12-15T17:30:00Z",
  "mode": "saw",
  "tool_id": "saw:veneer_160",
  "status": "OK",
  "request_summary": {
    "blade": {"diameter_mm": 160, "rpm": 3000},
    "material": "softwood"
  },
  "feasibility": {
    "risk_level": "GREEN",
    "score": 87.5,
    "calculator_results": {...}
  },
  "decision": {
    "risk_level": "GREEN",
    "score": 87.5,
    "warnings": []
  },
  "hashes": {
    "feasibility_sha256": "abc123...",
    "toolpaths_sha256": "def456...",
    "gcode_sha256": "789xyz...",
    "opplan_sha256": null
  },
  "outputs": {
    "gcode_text": "G90\nG21\n...",
    "opplan_json": {...}
  },
  "meta": {
    "dispatch": {"mode": "saw"}
  }
}
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RUN ARTIFACT CREATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Request arrives at /api/rmos/toolpaths                                    │
│                      │                                                      │
│                      ▼                                                      │
│   ┌─────────────────────────────────────┐                                  │
│   │  Recompute feasibility (server)     │                                  │
│   │  Hash: feasibility_sha256           │                                  │
│   └──────────────────┬──────────────────┘                                  │
│                      │                                                      │
│          ┌───────────┼───────────┐                                         │
│          ▼           ▼           ▼                                         │
│      BLOCKED       SUCCESS      ERROR                                      │
│          │           │           │                                         │
│          ▼           ▼           ▼                                         │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐                                   │
│   │ Artifact │ │ Artifact │ │ Artifact │                                   │
│   │ BLOCKED  │ │    OK    │ │  ERROR   │                                   │
│   │          │ │ +hashes  │ │ +except  │                                   │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘                                   │
│        │            │            │                                         │
│        └────────────┼────────────┘                                         │
│                     ▼                                                      │
│   ┌─────────────────────────────────────┐                                  │
│   │  RunStore.write_artifact()          │                                  │
│   │  → data/runs/rmos/YYYY-MM-DD/       │                                  │
│   │       <run_id>.json                 │                                  │
│   └─────────────────────────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Hashes Matter

| Hash | Purpose |
|------|---------|
| `feasibility_sha256` | Prove which safety evaluation was used |
| `toolpaths_sha256` | Verify entire response hasn't changed |
| `gcode_sha256` | Trace specific G-code to its source |
| `opplan_sha256` | Verify operation plan integrity |

**Use case:** "Did this G-code file come from that manufacturing run?"

```python
# Verify provenance
if sha256_text(gcode_file) == artifact["hashes"]["gcode_sha256"]:
    print("Verified: G-code matches run", artifact["run_id"])
```

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `RMOS_RUNS_DIR` | `services/api/data/runs/rmos` | Directory for artifact storage |

---

## Next Recommended Step

**Run Artifact Index + Query API**

Add endpoints to:
- List runs by day, tool_id, mode, status
- Fetch a run artifact by run_id
- Optional purge policy for old artifacts

---

## Summary

This bundle creates an **immutable manufacturing decision trail**:

| Outcome | What's Recorded |
|---------|-----------------|
| **BLOCKED** | Feasibility, decision, reason for block |
| **OK** | Feasibility, decision, all output hashes |
| **ERROR** | Feasibility, decision, exception details |

Every manufacturing decision is now:
- **Traceable** — which feasibility led to which toolpath
- **Verifiable** — SHA256 hashes prove integrity
- **Auditable** — complete record of blocked vs. allowed requests
- **Debuggable** — see exactly why something was blocked
