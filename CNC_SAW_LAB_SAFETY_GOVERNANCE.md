# CNC Saw Lab Safety Governance Policy

## Overview

This bundle adds a **Safety Governance Policy** that enforces a **hard stop on RED risk** inside `/api/rmos/toolpaths` for Saw Lab mode (when `tool_id` starts with `saw:`).

### Design Principle

- **Feasibility** → computes safety + risk score
- **Toolpaths** → refuses to generate if risk is RED

This makes unsafe execution **impossible by default**, not just "discouraged."

---

## File Structure

```
services/api/app/
├── rmos/
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── safety_policy.py      # Risk model + enforcement
│   │   └── saw_safety_gate.py    # Extract risk from feasibility
│   ├── schemas/
│   │   └── rmos_safety.py        # Pydantic response models
│   └── api/
│       └── rmos_toolpaths_router.py  # UPDATED with hard stop
└── tests/
    └── test_rmos_toolpaths_safety_gate.py
```

---

## Implementation Files

### 1. Safety Policy (`rmos/policies/safety_policy.py`)

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class RiskLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SafetyDecision:
    risk_level: RiskLevel
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: Optional[list[str]] = None
    details: Optional[Dict[str, Any]] = None

    @property
    def is_blocking(self) -> bool:
        return self.risk_level == RiskLevel.RED


@dataclass(frozen=True)
class SafetyPolicy:
    """
    Central governance policy.
    - RED is non-overridable in toolpath generation (hard stop)
    - UNKNOWN is treated as RED for Saw mode unless explicitly configured
    """
    block_on_red: bool = True
    treat_unknown_as_red: bool = True

    def should_block(self, decision: SafetyDecision) -> bool:
        if decision.risk_level == RiskLevel.RED and self.block_on_red:
            return True
        if decision.risk_level == RiskLevel.UNKNOWN and self.treat_unknown_as_red:
            return True
        return False
```

---

### 2. Response Schema (`rmos/schemas/rmos_safety.py`)

```python
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RmosSafetyDecision(BaseModel):
    risk_level: str
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = []
    details: Dict[str, Any] = {}


class RmosToolpathsBlocked(BaseModel):
    error: str = "SAFETY_BLOCKED"
    message: str
    decision: RmosSafetyDecision
    mode: str
    tool_id: str
```

---

### 3. Saw Safety Gate (`rmos/policies/saw_safety_gate.py`)

```python
from __future__ import annotations
from typing import Any, Dict, Optional
from .safety_policy import RiskLevel, SafetyDecision


def compute_saw_safety_decision(feasibility_payload: Dict[str, Any]) -> SafetyDecision:
    """
    Normalize Saw feasibility response into a SafetyDecision.
    
    Accepts any of these shapes:
    A) {"risk_level":"RED","score":92,"warnings":[...],"block_reason":"kickback risk"}
    B) {"safety":{"risk_level":"YELLOW","score":55,"warnings":[...]}}
    C) {"feasibility":{"safety":{...}}}
    
    If missing, returns UNKNOWN.
    """
    safety = _find_safety_object(feasibility_payload)
    
    if not safety:
        return SafetyDecision(
            risk_level=RiskLevel.UNKNOWN,
            score=None,
            block_reason="Missing safety decision in feasibility payload",
            warnings=["No safety decision returned; treating as unsafe for production toolpaths."],
            details={"payload_keys": sorted(list(feasibility_payload.keys()))},
        )

    # Extract risk level
    rl_raw = str(safety.get("risk_level") or safety.get("risk") or safety.get("level") or "UNKNOWN").upper()
    try:
        rl = RiskLevel(rl_raw)
    except Exception:
        rl = RiskLevel.UNKNOWN

    # Extract other fields
    score = safety.get("score", None)
    warnings = safety.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = [str(warnings)]
    
    block_reason = safety.get("block_reason") or safety.get("reason")
    details = safety.get("details") or {}

    # Default reason for RED
    if rl == RiskLevel.RED and not block_reason:
        block_reason = "Safety gate returned RED risk level"

    return SafetyDecision(
        risk_level=rl,
        score=score if isinstance(score, (int, float)) else None,
        block_reason=str(block_reason) if block_reason else None,
        warnings=[str(w) for w in warnings],
        details=details if isinstance(details, dict) else {"details": details},
    )


def _find_safety_object(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Search common payload shapes for safety object."""
    # Direct shape
    if isinstance(payload.get("risk_level"), str) or isinstance(payload.get("risk"), str):
        return payload
    
    # Nested shapes
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
```

---

### 4. Toolpaths Router Update (`rmos/api/rmos_toolpaths_router.py`)

```python
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict

from app.rmos.policies.safety_policy import SafetyPolicy
from app.rmos.policies.saw_safety_gate import compute_saw_safety_decision
from app.rmos.schemas.rmos_safety import RmosToolpathsBlocked, RmosSafetyDecision

router = APIRouter()

SAFETY_POLICY = SafetyPolicy(block_on_red=True, treat_unknown_as_red=True)


@router.post("/api/rmos/toolpaths")
def rmos_toolpaths(req: Dict[str, Any]):
    """
    Generate toolpaths with safety enforcement.
    
    If Saw mode (tool_id starts with 'saw:'), enforce safety decision from feasibility.
    """
    tool_id = str(req.get("tool_id") or "")
    mode = _resolve_mode(tool_id)

    # --- HARD STOP FOR SAW ON RED/UNKNOWN ---
    if mode == "saw":
        feasibility = req.get("feasibility") or {}
        if not isinstance(feasibility, dict):
            feasibility = {}
        
        decision = compute_saw_safety_decision(feasibility)
        
        if SAFETY_POLICY.should_block(decision):
            blocked = RmosToolpathsBlocked(
                message="Toolpath generation blocked by safety policy (RED/UNKNOWN).",
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
            # 409 Conflict = "request valid, but policy blocks execution"
            raise HTTPException(status_code=409, detail=blocked.model_dump())

    # --- NORMAL DISPATCH ---
    return _dispatch_toolpaths(mode=mode, req=req)


def _resolve_mode(tool_id: str) -> str:
    if tool_id.startswith("saw:"):
        return "saw"
    return "unknown"


def _dispatch_toolpaths(*, mode: str, req: Dict[str, Any]):
    """Existing implementation goes here."""
    if mode == "saw":
        return {"ok": True, "mode": "saw", "note": "toolpath generation placeholder"}
    raise HTTPException(status_code=400, detail={"error": "UNKNOWN_MODE", "mode": mode})
```

---

### 5. Tests (`tests/test_rmos_toolpaths_safety_gate.py`)

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_saw_toolpaths_blocked_on_red():
    """RED risk level should block toolpath generation."""
    payload = {
        "tool_id": "saw:kerf_cut_v1",
        "feasibility": {
            "risk_level": "RED",
            "score": 95,
            "block_reason": "kickback risk high",
            "warnings": ["kickback probability elevated"],
        },
    }
    r = client.post("/api/rmos/toolpaths", json=payload)
    
    assert r.status_code == 409
    detail = r.json().get("detail", {})
    assert detail.get("error") == "SAFETY_BLOCKED"
    assert detail["decision"]["risk_level"] in ("RED", "UNKNOWN")


def test_saw_toolpaths_blocked_on_unknown_when_missing_safety():
    """Missing feasibility should be treated as UNKNOWN (blocked)."""
    payload = {"tool_id": "saw:kerf_cut_v1"}  # no feasibility
    r = client.post("/api/rmos/toolpaths", json=payload)
    
    assert r.status_code == 409
    detail = r.json().get("detail", {})
    assert detail.get("decision", {}).get("risk_level") == "UNKNOWN"
```

---

## Client Workflow

### Correct Usage:

```
1. POST /api/rmos/feasibility (Saw mode)
   ↓
   Response: {risk_level: "GREEN", score: 75, ...}
   ↓
2. POST /api/rmos/toolpaths (with feasibility attached)
   ↓
   Response: {toolpaths: [...]}
```

### If Feasibility Skipped:

```
1. POST /api/rmos/toolpaths (no feasibility)
   ↓
   Response: 409 SAFETY_BLOCKED (UNKNOWN → treated as RED)
```

---

## Risk Level Behavior

| Risk Level | Toolpath Generation |
|------------|---------------------|
| GREEN | ✅ Allowed |
| YELLOW | ✅ Allowed |
| RED | ❌ Blocked (HTTP 409) |
| UNKNOWN | ❌ Blocked (HTTP 409) |

---

## Future Upgrade Options

1. **Server-side feasibility recompute** — toolpaths calls feasibility internally (no client trust)
2. **Override policy** — allow YELLOW with signed operator acknowledgment
3. **Risk artifact logging** — save feasibility + decision + toolpath hash for audit

---

## Integration Notes

- Adjust file paths to match your router structure
- The safety gate accepts multiple payload shapes (flexible parsing)
- HTTP 409 (Conflict) communicates "request valid, but policy blocks execution"
