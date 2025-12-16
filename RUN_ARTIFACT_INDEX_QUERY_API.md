# Run Artifact Index + Query API

## Overview

This bundle adds API endpoints to query and retrieve Run Artifacts created by the toolpath generation system.

**Endpoints:**
- `GET /api/rmos/runs` — List artifacts with filters + pagination
- `GET /api/rmos/runs/{run_id}` — Fetch one artifact
- `GET /api/rmos/runs/{run_id}/download` — Download artifact JSON file

---

## Prerequisites

This bundle requires the prior **Run Artifact Persistence** bundle:
- `app.rmos.runs.store.RunStore`
- `app.rmos.runs.schemas.RunArtifact`
- Artifacts written to `RMOS_RUNS_DIR` or default `services/api/data/runs/rmos/<YYYY-MM-DD>/<run_id>.json`

---

## File Structure

```
services/api/app/rmos/
├── runs/
│   ├── index.py        # NEW: Scan + filter + pagination
│   └── store.py        # UPDATED: Add read methods
└── api/
    └── rmos_runs_router.py  # NEW: Query endpoints

services/api/tests/
└── test_rmos_runs_query_api.py  # NEW
```

---

## Implementation

### 1. Store Updates: Read Artifacts by run_id

**File:** `services/api/app/rmos/runs/store.py` (append these methods)

```python
from __future__ import annotations
from pathlib import Path
from typing import Optional
import json

from .schemas import RunArtifact


class RunStore:
    # ... existing __init__, new_run_id, write_artifact ...
    
    def find_artifact_path(self, run_id: str) -> Optional[Path]:
        """
        Find an artifact by run_id by scanning day directories.
        Returns the path if found, None otherwise.
        """
        # Security: reject path traversal attempts
        if not run_id or any(c in run_id for c in ("/", "\\", "..")):
            return None
        
        if not self.runs_dir.exists():
            return None
        
        # Day folders are YYYY-MM-DD, scan newest first
        for day_dir in sorted(
            [p for p in self.runs_dir.iterdir() if p.is_dir()],
            reverse=True
        ):
            candidate = day_dir / f"{run_id}.json"
            if candidate.exists():
                return candidate
        
        return None
    
    def read_artifact(self, run_id: str) -> Optional[RunArtifact]:
        """Load and parse a RunArtifact by run_id."""
        path = self.find_artifact_path(run_id)
        if not path:
            return None
        
        obj = json.loads(path.read_text(encoding="utf-8"))
        return RunArtifact.model_validate(obj)
```

---

### 2. Indexer: Scan + Filter + Pagination

**File:** `services/api/app/rmos/runs/index.py`

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class RunIndexItem:
    """Lightweight index entry for listing runs."""
    run_id: str
    created_at_utc: str
    status: str
    mode: str
    tool_id: str
    risk_level: str
    score: Optional[float]
    feasibility_sha256: str
    toolpaths_sha256: Optional[str]
    artifact_path: str


def _parse_artifact_quick(path: Path) -> Optional[RunIndexItem]:
    """
    Quick parse of only fields needed for index listing.
    Avoids full model validation for speed.
    Returns None on corrupt JSON.
    """
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        decision = obj.get("decision") or {}
        hashes = obj.get("hashes") or {}
        
        return RunIndexItem(
            run_id=str(obj.get("run_id") or ""),
            created_at_utc=str(obj.get("created_at_utc") or ""),
            status=str(obj.get("status") or ""),
            mode=str(obj.get("mode") or ""),
            tool_id=str(obj.get("tool_id") or ""),
            risk_level=str(decision.get("risk_level") or "UNKNOWN"),
            score=decision.get("score") if isinstance(decision.get("score"), (int, float)) else None,
            feasibility_sha256=str(hashes.get("feasibility_sha256") or ""),
            toolpaths_sha256=str(hashes.get("toolpaths_sha256")) if hashes.get("toolpaths_sha256") else None,
            artifact_path=str(path),
        )
    except Exception:
        return None


def list_run_artifacts(
    runs_root: Path,
    *,
    status: Optional[str] = None,           # OK | BLOCKED | ERROR
    mode: Optional[str] = None,             # saw | router | ...
    tool_id_prefix: Optional[str] = None,   # "saw:"
    risk_level: Optional[str] = None,       # GREEN | YELLOW | RED | UNKNOWN
    date_from: Optional[str] = None,        # YYYY-MM-DD
    date_to: Optional[str] = None,          # YYYY-MM-DD
    limit: int = 50,
    cursor: Optional[str] = None,           # Opaque: "<day>|<filename>"
) -> Tuple[List[RunIndexItem], Optional[str]]:
    """
    List run artifacts with filters and cursor-based pagination.
    
    Returns: (items, next_cursor)
    Cursor format: "<YYYY-MM-DD>|<filename.json>"
    Scans newest day directories first.
    """
    limit = max(1, min(int(limit), 200))
    
    # Get day directories
    day_dirs = [p for p in runs_root.iterdir()] if runs_root.exists() else []
    day_dirs = [p for p in day_dirs if p.is_dir()]
    day_dirs = sorted(day_dirs, key=lambda p: p.name, reverse=True)
    
    # Apply date filters
    if date_from:
        day_dirs = [d for d in day_dirs if d.name >= date_from]
    if date_to:
        day_dirs = [d for d in day_dirs if d.name <= date_to]
    
    # Parse cursor
    start_day = None
    start_file = None
    if cursor and "|" in cursor:
        start_day, start_file = cursor.split("|", 1)
    
    items: List[RunIndexItem] = []
    next_cursor: Optional[str] = None
    started = cursor is None
    
    for day in day_dirs:
        files = sorted(
            [f for f in day.iterdir() if f.is_file() and f.suffix == ".json"],
            reverse=True
        )
        
        for f in files:
            if not started:
                # Skip until we reach the cursor point
                if day.name == start_day and f.name == start_file:
                    started = True
                continue
            
            it = _parse_artifact_quick(f)
            if not it or not it.run_id:
                continue
            
            # Apply filters
            if status and it.status != status:
                continue
            if mode and it.mode != mode:
                continue
            if tool_id_prefix and not it.tool_id.startswith(tool_id_prefix):
                continue
            if risk_level and it.risk_level != risk_level:
                continue
            
            items.append(it)
            
            if len(items) >= limit:
                # Next cursor is current position (resume AFTER this file)
                next_cursor = f"{day.name}|{f.name}"
                return items, next_cursor
    
    return items, None
```

---

### 3. Query API Router

**File:** `services/api/app/rmos/api/rmos_runs_router.py`

```python
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Any, Dict, Optional

from app.rmos.runs.store import RunStore
from app.rmos.runs.index import list_run_artifacts

router = APIRouter()

RUN_STORE = RunStore()


@router.get("/api/rmos/runs")
def rmos_runs_index(
    status: Optional[str] = None,
    mode: Optional[str] = None,
    tool_id_prefix: Optional[str] = None,
    risk_level: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List run artifacts with optional filters and pagination.
    
    Query Parameters:
        status: Filter by OK | BLOCKED | ERROR
        mode: Filter by mode (e.g., "saw")
        tool_id_prefix: Filter by tool_id prefix (e.g., "saw:")
        risk_level: Filter by GREEN | YELLOW | RED | UNKNOWN
        date_from: Filter runs on or after YYYY-MM-DD
        date_to: Filter runs on or before YYYY-MM-DD
        limit: Max results (1-200, default 50)
        cursor: Pagination cursor from previous response
    """
    items, next_cursor = list_run_artifacts(
        RUN_STORE.runs_dir,
        status=status,
        mode=mode,
        tool_id_prefix=tool_id_prefix,
        risk_level=risk_level,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )
    
    return {
        "items": [i.__dict__ for i in items],
        "next_cursor": next_cursor,
        "runs_dir": str(RUN_STORE.runs_dir),
    }


@router.get("/api/rmos/runs/{run_id}")
def rmos_run_get(run_id: str) -> Dict[str, Any]:
    """Fetch a single run artifact by run_id."""
    art = RUN_STORE.read_artifact(run_id)
    if art is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "RUN_NOT_FOUND", "run_id": run_id}
        )
    return art.model_dump()


@router.get("/api/rmos/runs/{run_id}/download")
def rmos_run_download(run_id: str):
    """Download a run artifact as a JSON file."""
    path = RUN_STORE.find_artifact_path(run_id)
    if path is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "RUN_NOT_FOUND", "run_id": run_id}
        )
    
    return FileResponse(
        str(path),
        media_type="application/json",
        filename=f"{run_id}.json",
    )
```

---

### 4. Router Registration

**File:** `services/api/app/main.py` (add to router includes)

```python
from app.rmos.api.rmos_runs_router import router as rmos_runs_router

app.include_router(rmos_runs_router)
```

---

### 5. Tests

**File:** `services/api/tests/test_rmos_runs_query_api.py`

```python
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_runs_index_returns_items(tmp_path: Path, monkeypatch):
    """Index endpoint should return list of artifacts."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    
    # Trigger a toolpaths call that creates a run artifact
    r = client.post("/api/rmos/toolpaths", json={"tool_id": "saw:kerf_cut_v1"})
    assert r.status_code in (200, 409, 500)
    
    idx = client.get("/api/rmos/runs?limit=10")
    assert idx.status_code == 200
    
    data = idx.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    assert "run_id" in data["items"][0]


def test_run_get_404_for_missing():
    """Should return 404 for non-existent run_id."""
    r = client.get("/api/rmos/runs/not_a_real_run_id")
    assert r.status_code == 404


def test_run_get_returns_artifact(tmp_path: Path, monkeypatch):
    """Should return full artifact for valid run_id."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    
    r = client.post("/api/rmos/toolpaths", json={"tool_id": "saw:kerf_cut_v1"})
    assert r.status_code in (200, 409, 500)
    
    idx = client.get("/api/rmos/runs?limit=1")
    run_id = idx.json()["items"][0]["run_id"]
    
    got = client.get(f"/api/rmos/runs/{run_id}")
    assert got.status_code == 200
    
    art = got.json()
    assert art["run_id"] == run_id


def test_run_download_streams_json(tmp_path: Path, monkeypatch):
    """Download endpoint should stream artifact as JSON file."""
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
    
    r = client.post("/api/rmos/toolpaths", json={"tool_id": "saw:kerf_cut_v1"})
    assert r.status_code in (200, 409, 500)
    
    idx = client.get("/api/rmos/runs?limit=1")
    run_id = idx.json()["items"][0]["run_id"]
    
    dl = client.get(f"/api/rmos/runs/{run_id}/download")
    assert dl.status_code == 200
    assert dl.headers.get("content-type", "").startswith("application/json")
    assert '"run_id"' in dl.text
```

---

## API Usage Examples

### List Recent Runs

```bash
# Get 10 most recent runs
curl "http://localhost:8000/api/rmos/runs?limit=10"

# Filter by status
curl "http://localhost:8000/api/rmos/runs?status=BLOCKED"

# Filter by risk level
curl "http://localhost:8000/api/rmos/runs?risk_level=RED"

# Filter by date range
curl "http://localhost:8000/api/rmos/runs?date_from=2025-12-01&date_to=2025-12-15"

# Combine filters
curl "http://localhost:8000/api/rmos/runs?status=BLOCKED&risk_level=RED&mode=saw"
```

### Pagination

```bash
# First page
curl "http://localhost:8000/api/rmos/runs?limit=20"
# Response includes: {"items": [...], "next_cursor": "2025-12-15|abc123.json"}

# Next page
curl "http://localhost:8000/api/rmos/runs?limit=20&cursor=2025-12-15|abc123.json"
```

### Fetch Single Artifact

```bash
curl "http://localhost:8000/api/rmos/runs/abc123def456"
```

### Download Artifact File

```bash
curl -o artifact.json "http://localhost:8000/api/rmos/runs/abc123def456/download"
```

---

## Filter Reference

| Parameter | Values | Description |
|-----------|--------|-------------|
| `status` | `OK`, `BLOCKED`, `ERROR` | Filter by run outcome |
| `mode` | `saw`, `router`, etc. | Filter by processing mode |
| `tool_id_prefix` | `"saw:"`, etc. | Filter by tool_id prefix |
| `risk_level` | `GREEN`, `YELLOW`, `RED`, `UNKNOWN` | Filter by safety decision |
| `date_from` | `YYYY-MM-DD` | Runs on or after this date |
| `date_to` | `YYYY-MM-DD` | Runs on or before this date |
| `limit` | `1-200` | Max results per page (default 50) |
| `cursor` | opaque string | Resume pagination |

---

## Design Notes

- **Filesystem-simple** — Date folders + JSON files, no database required
- **Clone-safe** — Works in monorepo and standalone clones
- **Cursor pagination** — Stable for real use
- **Security** — Rejects path traversal in run_id

---

## Next Recommended Step

**Run Artifact UI Panel**

A frontend component to:
- Show recent runs
- Filter by RED blocks
- Download artifacts
- Diff two artifacts by hashes
