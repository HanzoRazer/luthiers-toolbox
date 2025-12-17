You’re exactly right: that `__init__.py` is exporting symbols from three modules that don’t exist yet, so **imports like `from app.rmos.runs import RunStore` will fail until you create them**. The `__init__.py` contract is clear about what must exist and what it must export .

Below is a **one-pass, drop-in implementation** for:

* `services/api/app/rmos/runs/schemas.py`
* `services/api/app/rmos/runs/hashing.py`
* `services/api/app/rmos/runs/store.py`

These match the exports exactly: `RunArtifact`, `RunDecision`, `Hashes`, `RunOutputs`, `sha256_text`, `sha256_json`, `sha256_toolpaths_payload`, `summarize_request`, `RunStore` .

---

## 1) `services/api/app/rmos/runs/schemas.py`

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Hashes(BaseModel):
    feasibility_sha256: str
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    opplan_sha256: Optional[str] = None


class RunOutputs(BaseModel):
    # Inline outputs (small) or references (paths)
    gcode_text: Optional[str] = None
    opplan_json: Optional[Dict[str, Any]] = None

    gcode_path: Optional[str] = None
    opplan_path: Optional[str] = None
    preview_svg_path: Optional[str] = None


class RunDecision(BaseModel):
    risk_level: str = "UNKNOWN"
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class RunArtifact(BaseModel):
    run_id: str
    created_at_utc: datetime = Field(default_factory=utc_now)

    mode: str
    tool_id: str

    status: Literal["OK", "BLOCKED", "ERROR"]

    request_summary: Dict[str, Any] = Field(default_factory=dict)

    # Authoritative feasibility (server-computed)
    feasibility: Dict[str, Any]

    # Decision derived from feasibility
    decision: RunDecision

    # Stable hashes
    hashes: Hashes

    # Outputs (optional; empty for BLOCKED/ERROR)
    outputs: RunOutputs = Field(default_factory=RunOutputs)

    # Misc metadata (versions, host, policy, etc.)
    meta: Dict[str, Any] = Field(default_factory=dict)
```

---

## 2) `services/api/app/rmos/runs/hashing.py`

```python
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def sha256_text(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def sha256_json(obj: Any) -> str:
    """
    Stable hash for JSON-like objects:
    - sort keys
    - compact separators
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_text(s)


def sha256_toolpaths_payload(toolpaths_payload: Dict[str, Any]) -> str:
    """
    Stable hash of the toolpaths response payload.
    For audit accuracy, hash it as-is (caller can strip huge blobs first if desired).
    """
    return sha256_json(toolpaths_payload)


def summarize_request(req: Dict[str, Any], *, max_keys: int = 80) -> Dict[str, Any]:
    """
    Minimized request snapshot for artifacts:
    - drops client-provided 'feasibility' to avoid trust confusion
    - summarizes huge dict/list values by length
    """
    summary: Dict[str, Any] = {}
    for k in sorted(req.keys()):
        if k == "feasibility":
            continue
        v = req.get(k)

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

## 3) `services/api/app/rmos/runs/store.py`

```python
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .schemas import RunArtifact


def default_runs_dir() -> Path:
    """
    Default: services/api/data/runs/rmos
    Override with env var: RMOS_RUNS_DIR
    """
    env = os.environ.get("RMOS_RUNS_DIR")
    if env:
        return Path(env).expanduser().resolve()

    # .../services/api/app/rmos/runs/store.py -> .../services/api
    here = Path(__file__).resolve()
    api_root = here.parents[4]
    return (api_root / "data" / "runs" / "rmos").resolve()


class RunStore:
    def __init__(self, runs_dir: Optional[Path] = None):
        self.runs_dir = (runs_dir or default_runs_dir())
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def new_run_id(self) -> str:
        return uuid4().hex

    def write_artifact(self, artifact: RunArtifact) -> Path:
        """
        Writes:
          <runs_dir>/<YYYY-MM-DD>/<run_id>.json
        """
        day = artifact.created_at_utc.date().isoformat()
        out_dir = self.runs_dir / day
        out_dir.mkdir(parents=True, exist_ok=True)

        path = out_dir / f"{artifact.run_id}.json"
        path.write_text(
            json.dumps(artifact.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def find_artifact_path(self, run_id: str) -> Optional[Path]:
        """
        Locate an artifact by run_id by scanning day directories (newest first).
        Good enough for file-store scale; can be indexed later if needed.
        """
        if not run_id or any(c in run_id for c in ("/", "\\", "..")):
            return None
        if not self.runs_dir.exists():
            return None

        for day_dir in sorted([p for p in self.runs_dir.iterdir() if p.is_dir()], reverse=True):
            candidate = day_dir / f"{run_id}.json"
            if candidate.exists():
                return candidate
        return None

    def read_artifact(self, run_id: str) -> Optional[RunArtifact]:
        path = self.find_artifact_path(run_id)
        if not path:
            return None
        obj = json.loads(path.read_text(encoding="utf-8"))
        return RunArtifact.model_validate(obj)
```

---

## Quick verification steps

1. Create the files above.
2. Run a quick import check from `services/api` (same venv you use for uvicorn):

```python
from app.rmos.runs import RunStore, RunArtifact, sha256_json
print("ok", RunStore, RunArtifact, sha256_json)
```

If that prints “ok …”, your `__init__.py` exports are now satisfied exactly as written .

---

## One important note

Once these exist, **do not create alternate RunArtifact definitions elsewhere**. Everything should import from `app.rmos.runs` (or its submodules) so the whole repo stays consistent with the export contract .

If you paste your current `rmos_toolpaths_router.py` (just the part where it writes the artifact), I’ll align it to use this exact module surface in one clean patch.
