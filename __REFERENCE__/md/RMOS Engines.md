Got it. Your checklist is solid, and you’re right: the **design** is fine, but the **gaps** (error handling, observability, prod guards) are real. Below is a **one-pass implementation** of the engines layer that bakes in the 🔴 high-risk fixes you listed, while staying minimal and drop-in.

I’m going to give you the **full file contents** for the 5 engine files, so you can paste them in directly. This includes:

* structured error return (never throw raw exceptions to router)
* timing `compute_ms`
* engine_id validation (alnum + underscore)
* semver validation
* unknown engine_id warning before fallback
* registry non-empty assert
* **stub engine disabled in production by default** via `ALLOW_STUB_ENGINE=false`
* guarded import of `feasibility_fusion`

> Assumption: your router will call `engine.compute(spec=..., ctx=..., request_id=...)` and return the dict. If your router doesn’t have request_id, pass `None`—it works.

---

# 1) `services/api/app/rmos/engines/base.py`

```py
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Literal

RiskStatus = Literal["GREEN", "YELLOW", "RED", "ERROR"]

_ENGINE_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")
_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class EngineInfo:
    engine_id: str
    version: str
    description: str

    def validate(self) -> None:
        if not _ENGINE_ID_RE.match(self.engine_id):
            raise ValueError(f"Invalid engine_id '{self.engine_id}'. Use alphanumeric + underscore only.")
        if not _SEMVER_RE.match(self.version):
            raise ValueError(f"Invalid version '{self.version}'. Must be semver, e.g. 1.2.3")


class FeasibilityEngine(Protocol):
    info: EngineInfo

    def compute(
        self,
        *,
        spec: Optional[Dict[str, Any]],
        ctx: Any,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...


def validate_result_contract(result: Dict[str, Any]) -> None:
    # Required provenance
    if "engine_id" not in result or "engine_version" not in result:
        raise ValueError("Engine result missing engine_id/engine_version")

    # status
    status = result.get("status")
    if status not in ("GREEN", "YELLOW", "RED", "ERROR"):
        raise ValueError(f"Invalid status '{status}'. Must be GREEN/YELLOW/RED/ERROR")

    # reasons list
    reasons = result.get("reasons")
    if reasons is None or not isinstance(reasons, list):
        raise ValueError("reasons must be a list")

    # compute_ms (optional but recommended; enforce numeric if present)
    if "compute_ms" in result:
        if not isinstance(result["compute_ms"], (int, float)):
            raise ValueError("compute_ms must be numeric")
```

---

# 2) `services/api/app/rmos/engines/feasibility_baseline_v1.py`

```py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .base import EngineInfo, validate_result_contract


def _safe_import_fusion():
    try:
        from services.api.app.rmos.feasibility_fusion import evaluate_feasibility  # type: ignore
        return evaluate_feasibility, None
    except Exception as e:
        return None, e


_EVALUATE_FEASIBILITY, _IMPORT_ERR = _safe_import_fusion()


class BaselineFeasibilityEngineV1:
    info = EngineInfo(
        engine_id="baseline_v1",
        version="1.0.0",
        description="Deterministic baseline feasibility (wraps feasibility_fusion + scorer policies).",
    )

    def __init__(self):
        # Validate metadata early (fail fast on bad engine metadata)
        self.info.validate()

    def compute(
        self,
        *,
        spec: Optional[Dict[str, Any]],
        ctx: Any,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()

        # Guard: fusion import failed
        if _IMPORT_ERR is not None or _EVALUATE_FEASIBILITY is None:
            out = {
                "status": "ERROR",
                "reasons": [f"feasibility_fusion import failed: {_IMPORT_ERR}"],
                "engine_id": self.info.engine_id,
                "engine_version": self.info.version,
                "request_id": request_id,
                "compute_ms": (time.perf_counter() - t0) * 1000.0,
            }
            validate_result_contract(out)
            return out

        # Guard: null spec
        if spec is None:
            spec = {}

        try:
            # NOTE: keep wrapper thin. Fusion owns scoring logic.
            result = _EVALUATE_FEASIBILITY(spec=spec, ctx=ctx)  # type: ignore

            # Normalize to dict (some fusions return pydantic objects)
            if hasattr(result, "model_dump"):
                result = result.model_dump()
            elif not isinstance(result, dict):
                result = {"result": result}

            result.setdefault("status", "ERROR")
            result.setdefault("reasons", [])

        except Exception as e:
            result = {
                "status": "ERROR",
                "reasons": [f"engine exception: {type(e).__name__}: {e}"],
            }

        # Stamp provenance + observability
        result["engine_id"] = self.info.engine_id
        result["engine_version"] = self.info.version
        result["request_id"] = request_id
        result["compute_ms"] = (time.perf_counter() - t0) * 1000.0

        # Contract validation (fail-safe to ERROR)
        try:
            validate_result_contract(result)
        except Exception as e:
            result = {
                "status": "ERROR",
                "reasons": [f"result contract violation: {type(e).__name__}: {e}"],
                "engine_id": self.info.engine_id,
                "engine_version": self.info.version,
                "request_id": request_id,
                "compute_ms": (time.perf_counter() - t0) * 1000.0,
            }
            validate_result_contract(result)

        return result
```

---

# 3) `services/api/app/rmos/engines/feasibility_stub.py`

```py
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from .base import EngineInfo, validate_result_contract


class StubFeasibilityEngine:
    info = EngineInfo(
        engine_id="stub",
        version="0.0.0",
        description="Stub feasibility engine for tests/dev (disabled in production by default).",
    )

    def __init__(self):
        self.info.validate()

    def compute(
        self,
        *,
        spec: Optional[Dict[str, Any]],
        ctx: Any,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()

        allow = os.environ.get("ALLOW_STUB_ENGINE", "false").strip().lower()
        if allow not in ("1", "true", "yes", "on"):
            out = {
                "status": "ERROR",
                "reasons": ["stub engine disabled (set ALLOW_STUB_ENGINE=true to enable)"],
                "engine_id": self.info.engine_id,
                "engine_version": self.info.version,
                "request_id": request_id,
                "compute_ms": (time.perf_counter() - t0) * 1000.0,
            }
            validate_result_contract(out)
            return out

        spec = spec or {}
        forced = spec.get("force_status")
        status = forced if forced in ("GREEN", "YELLOW", "RED", "ERROR") else "GREEN"

        out = {
            "status": status,
            "reasons": [] if status == "GREEN" else ["stub-forced" if forced else "stub-non-green"],
            "engine_id": self.info.engine_id,
            "engine_version": self.info.version,
            "request_id": request_id,
            "compute_ms": (time.perf_counter() - t0) * 1000.0,
        }
        validate_result_contract(out)
        return out
```

---

# 4) `services/api/app/rmos/engines/registry.py`

```py
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .base import EngineInfo, FeasibilityEngine
from .feasibility_baseline_v1 import BaselineFeasibilityEngineV1
from .feasibility_stub import StubFeasibilityEngine

log = logging.getLogger("rmos.engines")

# Singleton instances (avoid recreation per request)
_FEASIBILITY_ENGINES: Dict[str, FeasibilityEngine] = {
    "baseline_v1": BaselineFeasibilityEngineV1(),
    "stub": StubFeasibilityEngine(),
}

_DEFAULT_ENGINE_ID = "baseline_v1"

# Prevent empty registry
assert _FEASIBILITY_ENGINES, "Feasibility engine registry must not be empty"
assert _DEFAULT_ENGINE_ID in _FEASIBILITY_ENGINES, "_DEFAULT_ENGINE_ID must exist in registry"


def get_feasibility_engine(engine_id: Optional[str] = None, *, request_id: Optional[str] = None) -> FeasibilityEngine:
    eid = (engine_id or _DEFAULT_ENGINE_ID).strip()
    eng = _FEASIBILITY_ENGINES.get(eid)
    if eng is None:
        log.warning("Unknown feasibility engine_id '%s' (request_id=%s). Falling back to '%s'.", eid, request_id, _DEFAULT_ENGINE_ID)
        eng = _FEASIBILITY_ENGINES[_DEFAULT_ENGINE_ID]
    return eng


def list_feasibility_engines() -> List[EngineInfo]:
    return [e.info for e in _FEASIBILITY_ENGINES.values()]
```

---

# 5) `services/api/app/rmos/engines/__init__.py`

```py
from .base import FeasibilityEngine, EngineInfo
from .registry import get_feasibility_engine, list_feasibility_engines
```

---

## Router wiring change (minimal)

In `services/api/app/rmos/feasibility_router.py`, wherever you compute feasibility, do:

```py
from services.api.app.rmos.engines.registry import get_feasibility_engine

engine = get_feasibility_engine(getattr(ctx, "feasibility_engine_id", None), request_id=req_id)
result = engine.compute(spec=spec_dict, ctx=ctx, request_id=req_id)
return result
```

And add an endpoint:

```py
from services.api.app.rmos.engines.registry import list_feasibility_engines

@router.get("/engines")
def engines():
    return {"engines": [e.__dict__ for e in list_feasibility_engines()]}
```

---

## Why this satisfies your checklist

* ✅ Implements protocol + info metadata
* ✅ Always stamps `engine_id` + `engine_version`
* ✅ Unknown engine logs warning then falls back
* ✅ compute wrapped in try/except
* ✅ fusion import failures handled at module load
* ✅ stub disabled by default with env var gate
* ✅ validates engine IDs + semver
* ✅ adds `compute_ms`
* ✅ prevents empty registry

---

### One detail I need from you (so it’s truly drop-in)

Your `evaluate_feasibility(...)` call: is it exactly `evaluate_feasibility(spec=spec, ctx=ctx)`?

If the fusion function uses different parameter names, paste its signature line and I’ll adjust the wrapper in **BaselineFeasibilityEngineV1** (one-line change).



Perfect — that’s exactly what we needed. Your fusion signature is:

````py
def evaluate_feasibility(design: Dict[str, Any], context: RmosContext) -> FeasibilityReport
``` :contentReference[oaicite:0]{index=0}

So we only need a **small, precise fix** in the Baseline engine wrapper: change `spec/ctx` → `design/context`, and normalize `FeasibilityReport` to a dict.

---

## Patch: fix BaselineFeasibilityEngineV1 to call fusion correctly

Update **only** `services/api/app/rmos/engines/feasibility_baseline_v1.py` as follows:

```diff
@@
 def _safe_import_fusion():
     try:
-        from services.api.app.rmos.feasibility_fusion import evaluate_feasibility  # type: ignore
+        from services.api.app.rmos.feasibility_fusion import evaluate_feasibility  # type: ignore
         return evaluate_feasibility, None
     except Exception as e:
         return None, e
@@
     def compute(
         self,
         *,
-        spec: Optional[Dict[str, Any]],
-        ctx: Any,
+        spec: Optional[Dict[str, Any]],
+        ctx: Any,
         request_id: Optional[str] = None,
     ) -> Dict[str, Any]:
@@
-        # Guard: null spec
-        if spec is None:
-            spec = {}
+        # Guard: null design
+        design = spec or {}
 
         try:
-            # NOTE: keep wrapper thin. Fusion owns scoring logic.
-            result = _EVALUATE_FEASIBILITY(spec=spec, ctx=ctx)  # type: ignore
+            # NOTE: keep wrapper thin. Fusion owns scoring logic.
+            # Fusion signature: evaluate_feasibility(design: Dict[str, Any], context: RmosContext) :contentReference[oaicite:1]{index=1}
+            result = _EVALUATE_FEASIBILITY(design=design, context=ctx)  # type: ignore
 
             # Normalize to dict (some fusions return pydantic objects)
             if hasattr(result, "model_dump"):
                 result = result.model_dump()
             elif not isinstance(result, dict):
                 result = {"result": result}
````

### Why this is correct

* Uses the exact signature you confirmed (`design`, `context`) 
* Keeps the engine wrapper thin (fusion remains the authoritative scorer)
* Still stamps `engine_id`, `engine_version`, `compute_ms`, `request_id`
* Still catches import failures and runtime exceptions cleanly

---

## Recommended small router naming alignment

Your router currently talks in “design” language; our engine Protocol uses `spec` as a generic dict. That’s fine, but in the router you can keep it semantically clear:

```py
design = req.design  # or however you build it
engine.compute(spec=design, ctx=ctx, request_id=req_id)
```

No need to rename protocol parameters yet.

---

If you want, paste the **current feasibility_router.py call site** where it invokes `evaluate_feasibility(...)`, and I’ll give you the exact 3-line edit to route through `get_feasibility_engine()` with request correlation ID.


Here’s the **exact 3-line replacement** you want at the call site where you currently do:

```py
report = evaluate_feasibility(design=design, context=context)
```

### ✅ Replace that single line with these 3 lines

```py
req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
engine = get_feasibility_engine(getattr(context, "feasibility_engine_id", None), request_id=req_id)
report = engine.compute(spec=design, ctx=context, request_id=req_id)
```

---

## One-time import you’ll need at top of `feasibility_router.py`

Add:

```py
from services.api.app.rmos.engines.registry import get_feasibility_engine
```

(Then you can delete the direct import of `evaluate_feasibility` from this router once all call sites are routed through the engine.)

---

## Notes on the “request correlation ID”

* This assumes your route function has access to `request: Request` (FastAPI) and you have some middleware that sets `request.state.request_id`.
* If you **don’t** have that middleware yet, the line still works (it’ll just try the header).

If you want the correlation ID to *always* exist, the next micro-step is a middleware that sets `request.state.request_id = uuid4()` when missing—but your requested change above is exactly the minimal safe wiring.
