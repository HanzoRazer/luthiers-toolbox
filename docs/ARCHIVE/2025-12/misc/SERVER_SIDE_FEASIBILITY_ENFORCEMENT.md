# Server-Side Feasibility Enforcement (No Client Trust)

## Overview

This bundle implements a **governance guarantee** for the bidirectional manufacturing system:

> **Toolpaths are only generated from feasibility computed by the server, in the same request context, using authoritative data.**

This is the correct production-grade posture for a safety-critical manufacturing system.

---

## Architectural Rule

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Client feasibility  =  ADVISORY ONLY (ignored)                │
│   Server feasibility  =  AUTHORITATIVE (enforced)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Even if the client sends a feasibility block:
- It is **ignored**
- It is **recomputed** server-side
- Discrepancies are **detectable and auditable**

---

## What This Changes

| Before | After |
|--------|-------|
| `/api/rmos/toolpaths` trusts client feasibility | Client feasibility is stripped and ignored |
| Safety depends on client honesty | Safety recomputed server-side every time |
| RED could be bypassed by lying client | RED/UNKNOWN → hard stop, non-bypassable |
| No audit trail of decisions | Authoritative feasibility returned in response |

---

## File Structure

```
services/api/app/rmos/
├── services/
│   └── feasibility_service.py     # NEW: Internal feasibility adapter
├── api/
│   ├── rmos_feasibility_router.py # MODIFIED: Expose internal function
│   └── rmos_toolpaths_router.py   # MODIFIED: Server-side enforcement
└── tests/
    └── test_toolpaths_server_side_feasibility.py  # NEW: Trust boundary test
```

---

## Implementation

### 1. Internal Feasibility Service

This adapter calls the same logic as `/api/rmos/feasibility` but for internal use.

**File:** `services/api/app/rmos/services/feasibility_service.py`

```python
from __future__ import annotations
from typing import Dict, Any

# Import your existing feasibility engine
# This MUST be the same code path used by /api/rmos/feasibility
from app.rmos.api.rmos_feasibility_router import compute_feasibility_internal


def recompute_feasibility_for_toolpaths(
    *,
    tool_id: str,
    req: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Server-side authoritative feasibility computation.
    
    - Ignores any client-provided feasibility
    - Uses the same engine as /api/rmos/feasibility
    - Returns the full feasibility payload
    """
    # Strip any client feasibility to avoid accidental trust
    clean_req = dict(req)
    clean_req.pop("feasibility", None)
    
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req=clean_req,
        context="toolpaths",  # Tag for logging
    )
    
    if not isinstance(feasibility, dict):
        raise RuntimeError("Feasibility engine returned invalid payload")
    
    return feasibility
```

**Key Invariant:**
> Toolpaths never call calculators directly — they call feasibility, which calls calculators.

---

### 2. Refactor Feasibility Router (Expose Internal Function)

Make the feasibility computation callable internally, not just via HTTP.

**File:** `services/api/app/rmos/api/rmos_feasibility_router.py`

```python
from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter

router = APIRouter()


def compute_feasibility_internal(
    *,
    tool_id: str,
    req: Dict[str, Any],
    context: str | None = None,
) -> Dict[str, Any]:
    """
    Internal feasibility computation.
    This is the SINGLE SOURCE OF TRUTH.
    """
    mode = _resolve_mode(tool_id)
    
    if mode == "saw":
        return _compute_saw_feasibility(req=req, context=context)
    
    # Add other modes as needed
    raise ValueError(f"Unsupported mode: {mode}")


@router.post("/api/rmos/feasibility")
def rmos_feasibility(req: Dict[str, Any]):
    """Public API endpoint - calls the same internal logic."""
    tool_id = str(req.get("tool_id") or "")
    return compute_feasibility_internal(tool_id=tool_id, req=req)


def _resolve_mode(tool_id: str) -> str:
    if tool_id.startswith("saw:"):
        return "saw"
    return "router"


def _compute_saw_feasibility(req: Dict[str, Any], context: str | None) -> Dict[str, Any]:
    """
    Saw-specific feasibility computation.
    Calls all 5 saw calculators and aggregates results.
    """
    # Your existing saw feasibility logic here
    pass
```

**Why This Matters:**
- One engine, two entrypoints (API + internal)
- No code duplication
- Guaranteed consistency

---

### 3. Update Toolpaths Router (Server-Side Enforcement)

**File:** `services/api/app/rmos/api/rmos_toolpaths_router.py`

```python
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.rmos.policies.safety_policy import SafetyPolicy
from app.rmos.policies.saw_safety_gate import compute_saw_safety_decision
from app.rmos.schemas.rmos_safety import RmosToolpathsBlocked, RmosSafetyDecision
from app.rmos.services.feasibility_service import recompute_feasibility_for_toolpaths

router = APIRouter()

SAFETY_POLICY = SafetyPolicy(block_on_red=True, treat_unknown_as_red=True)


@router.post("/api/rmos/toolpaths")
def rmos_toolpaths(req: Dict[str, Any]):
    tool_id = str(req.get("tool_id") or "")
    mode = _resolve_mode(tool_id)
    
    # ===============================
    # SERVER-SIDE FEASIBILITY (MANDATORY)
    # ===============================
    feasibility = recompute_feasibility_for_toolpaths(
        tool_id=tool_id,
        req=req,
    )
    
    # ===============================
    # SAFETY ENFORCEMENT
    # ===============================
    if mode == "saw":
        decision = compute_saw_safety_decision(feasibility)
        
        if SAFETY_POLICY.should_block(decision):
            blocked = RmosToolpathsBlocked(
                message="Toolpath generation blocked by server-side safety policy.",
                decision=RmosSafetyDecision(
                    risk_level=decision.risk_level.value,
                    score=decision.score,
                    block_reason=decision.block_reason,
                    warnings=decision.warnings or [],
                    details=decision.details or {},
                ),
                mode=mode,
                tool_id=tool_id,
            )
            raise HTTPException(
                status_code=409,
                detail={
                    **blocked.model_dump(),
                    "authoritative_feasibility": feasibility,  # For audit
                },
            )
    
    # ===============================
    # DISPATCH (SAFE TO PROCEED)
    # ===============================
    return _dispatch_toolpaths(
        mode=mode,
        req=req,
        feasibility=feasibility,  # Pass authoritative feasibility downstream
    )


def _resolve_mode(tool_id: str) -> str:
    if tool_id.startswith("saw:"):
        return "saw"
    return "router"


def _dispatch_toolpaths(
    *,
    mode: str,
    req: Dict[str, Any],
    feasibility: Dict[str, Any],
):
    """Dispatch to appropriate toolpath builder."""
    if mode == "saw":
        return build_saw_toolpaths(req=req, feasibility=feasibility)
    raise HTTPException(status_code=400, detail={"error": "UNKNOWN_MODE", "mode": mode})
```

---

### 4. Update Toolpath Builders (Require Feasibility)

Prevent "silent recomputation drift" by requiring feasibility explicitly.

```python
def build_saw_toolpaths(
    *,
    req: Dict[str, Any],
    feasibility: Dict[str, Any],
):
    """
    Build saw toolpaths with authoritative feasibility.
    """
    # This assertion prevents future regressions
    assert feasibility is not None, "Authoritative feasibility required"
    
    # Your existing toolpath building logic
    # ...
```

---

### 5. Test: Prove Client Feasibility Is Ignored

**File:** `services/api/tests/test_toolpaths_server_side_feasibility.py`

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_client_feasibility_is_ignored_and_red_blocks():
    """
    Even if client sends GREEN feasibility, server recomputes
    and blocks if the actual parameters trigger RED.
    """
    payload = {
        "tool_id": "saw:kerf_cut_v1",
        # Client lies - claims GREEN
        "feasibility": {
            "risk_level": "GREEN",
            "score": 95,
        },
        # But server inputs imply RED (unsafe rim speed)
        "blade": {
            "diameter_mm": 305,
            "rpm": 6500,  # Triggers rim-speed RED
        },
    }
    
    r = client.post("/api/rmos/toolpaths", json=payload)
    
    # Should be blocked despite client claiming GREEN
    assert r.status_code == 409
    
    detail = r.json()["detail"]
    assert detail["decision"]["risk_level"] == "RED"
    assert "authoritative_feasibility" in detail


def test_green_feasibility_allows_toolpath_generation():
    """Safe parameters should proceed."""
    payload = {
        "tool_id": "saw:veneer_160",
        "blade": {
            "diameter_mm": 160,
            "rpm": 3000,  # Safe rim speed
        },
        "material": "softwood",
    }
    
    r = client.post("/api/rmos/toolpaths", json=payload)
    
    assert r.status_code == 200
    assert "toolpath" in r.json() or "ok" in r.json()
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SERVER-SIDE ENFORCEMENT FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Client Request                                                            │
│   ┌─────────────────────────────────────┐                                  │
│   │ {                                   │                                  │
│   │   "tool_id": "saw:blade_v1",        │                                  │
│   │   "feasibility": {...} ← IGNORED    │                                  │
│   │   "blade": {...},                   │                                  │
│   │   "material": "maple"               │                                  │
│   │ }                                   │                                  │
│   └──────────────────┬──────────────────┘                                  │
│                      │                                                      │
│                      ▼                                                      │
│   ┌─────────────────────────────────────┐                                  │
│   │  Strip client feasibility           │                                  │
│   │  clean_req.pop("feasibility")       │                                  │
│   └──────────────────┬──────────────────┘                                  │
│                      │                                                      │
│                      ▼                                                      │
│   ┌─────────────────────────────────────┐                                  │
│   │  RECOMPUTE FEASIBILITY              │                                  │
│   │  (Same engine as /api/feasibility)  │                                  │
│   │                                     │                                  │
│   │  → rim_speed_calculator             │                                  │
│   │  → deflection_calculator            │                                  │
│   │  → heat_calculator                  │                                  │
│   │  → bite_load_calculator             │                                  │
│   │  → kickback_calculator              │                                  │
│   └──────────────────┬──────────────────┘                                  │
│                      │                                                      │
│                      ▼                                                      │
│   ┌─────────────────────────────────────┐                                  │
│   │  SAFETY DECISION                    │                                  │
│   │                                     │                                  │
│   │  risk_level = RED?                  │                                  │
│   │       │                             │                                  │
│   │       ├── YES → HTTP 409 (blocked)  │                                  │
│   │       │         + authoritative     │                                  │
│   │       │           feasibility       │                                  │
│   │       │                             │                                  │
│   │       └── NO  → Generate toolpaths  │                                  │
│   └─────────────────────────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Strategic Benefits

### Immediate

| Benefit | Description |
|---------|-------------|
| **Certifiable** | Safety decisions are server-controlled, auditable |
| **Non-bypassable** | Malicious clients cannot skip safety checks |
| **Consistent** | One feasibility engine, one source of truth |
| **Debuggable** | Authoritative feasibility included in error responses |

### Future SKU Support

| Tier | Behavior |
|------|----------|
| **Hobbyist** | Feasibility advisory only (warnings shown, not enforced) |
| **Pro** | YELLOW allowed with acknowledgment, RED blocked |
| **Enterprise** | RED never overridable, all decisions logged and signed |

---

## Next Recommended Step

**Persist Feasibility + Toolpath Hash as a Run Artifact**

This would:
- Tie geometry → safety → G-code in a single record
- Enable replay, audits, and rollback
- Create a complete manufacturing decision trail

---

## Summary

This implementation encodes a fundamental engineering principle:

> **The system that generates the action must also verify the safety.**

By recomputing feasibility server-side for every toolpath request, you guarantee that:
1. No toolpath is generated without a safety check
2. The safety check uses authoritative (not client-provided) data
3. Every blocked request includes the evidence for why it was blocked
4. Future audits can trace decisions to their source

This is the difference between a CAM system and a **manufacturing decision engine**.
