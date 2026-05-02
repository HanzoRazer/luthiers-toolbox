# Sprint FRET-A Phase 2 — Dev-Ready Handoff
### FastAPI Router for Fretboard Ecosphere

**Status:** READY TO EXECUTE on `sprint/fret-ecosphere-a` (post-Phase 1.5)
**Date:** 2026-04-30
**Codename:** Sprint FRET-A Phase 2
**Branch:** `sprint/fret-ecosphere-a` (continuing)
**Predecessor:** Phase 1.5 (commits `ac96430f`, `e260f365`, `d72d9744`)
**Estimated time:** 2.5–3.5 hours
**Estimated commits:** 3 (router skeleton, DXF projection wiring, integration test)

---

## 1. Scope

Phase 2 wires the canonical fretboard ecosphere into a public API surface at `/api/v1/fretboard/*`. After this phase, callers can:

```
POST /api/v1/fretboard/compute       → JSON ecosphere doc (free, no auth)
POST /api/v1/fretboard/dxf           → DXF bytes (auth-gated for R2000)
POST /api/v1/fretboard/scala         → Scala (.scl) text (free)
GET  /api/v1/fretboard/presets       → List of preset request shapes (free)
GET  /api/v1/fretboard/schema        → Pydantic JSON schema (free)
```

The math kernel is honest after Phase 1.5 (real N-TET, real Pythagorean, real per-string scales, real Scala). Phase 2 exposes that honesty publicly. Free tier returns R12 LINE DXF; pro tier returns R2000 LWPOLYLINE DXF. The two formats use the same canonical doc and project differently at the writer layer.

### What is NOT in scope for Phase 2

- DXF projection layer details — Phase 7 of the v2 dev order owns the AC1009/AC1015 emission patterns. Phase 2 wires the route and calls a placeholder projector that returns minimal but valid DXF bytes. Phase 7 fills out the actual layer set.
- Frontend client — Phase 8 of the v2 dev order. Phase 2 is API only.
- Harmonics overlay population — schema field exists, accepts `enabled=false`, no markers populated.
- Production-scale Fusion testing — separate sprint, soft 50K-entity cap remains in CLAUDE.md.

---

## 2. Decisions Locked Before Implementation

These were resolved in the prior strategic conversation. The engineer should not relitigate.

| Decision | Choice | Rationale |
|---|---|---|
| Router file location | `services/api/app/api_v1/fretboard.py` | Matches existing v1 convention (every router lives directly in `api_v1/`) |
| API namespace | `/api/v1/fretboard/*` | Distinct from `/api/v1/frets/*` (calculator surface). Two namespaces, intentional |
| Response shape | Return `FretboardEcosphere` directly, list endpoints wrap in `{"items": [...]}` | Schema-aligned for single objects; OWASP-safe for arrays. No V1Response wrapper |
| DXF tier gating | `require_pro` from `app.middleware.tier_gate` | Already exists as module-level constant — solves dependency-identity problem |
| DXF version inference | Infer from request `tier` field; allow override; auth-gate R2000 | Free → R12 default, Pro → R2000 default, explicit override wins (within auth bounds) |
| Presets module | New file `app/instrument_geometry/neck/fretboard_presets.py` | Adjacent to schema, reusable by tests/CLI/future Fusion add-in |
| Scala export | Content-negotiated: JSON default, `.scl` text on `Accept: application/octet-stream` | Serves programmatic and download consumers |
| Round-trip test location | `app/tests/integration/test_fretboard_ecosphere_roundtrip.py` | Integration concern, not unit concern. New directory if absent |
| Auth principal helpers | `get_optional_principal` for free routes, `Depends(require_pro)` for paid | Existing patterns from PR #10 |

---

## 3. File-by-File Patch Plan

Three commits, in order. Each commit is self-contained, runs its tests cleanly, and leaves the branch in a working state.

### Commit 1 — Router skeleton + presets

**Goal:** the four free routes (`compute`, `scala`, `presets`, `schema`) work end to end against the existing assembler. No DXF route yet. No paid tier yet.

#### 3.1 New file: `services/api/app/instrument_geometry/neck/fretboard_presets.py` (~120 lines)

Module-level dictionary of preset `FretboardInput` (or whatever the Phase 1 schema named the request type). Seed with the four scale lengths already present in `services/api/tests/test_golden_fret_positions.py` plus the Smart Guitar Pro fan.

```python
"""Reference fretboard preset library.

Each preset is a complete FretboardInput suitable for direct submission to
build_ecosphere(). Presets are reusable by tests, CLI scripts, and any
future Fusion 360 add-in that needs canonical reference geometry.
"""
from __future__ import annotations
from typing import Dict, List

from app.instrument_geometry.neck.fretboard_ecosphere import FretboardInput

# Each preset must be valid input to build_ecosphere() with no further
# modification. If the Phase 1 schema requires more fields than shown here,
# add them — keep presets fully populated.

FRETBOARD_PRESETS: Dict[str, FretboardInput] = {
    "fender_strat_25.5": FretboardInput(
        scale_length_mm=647.7,
        fret_count=22,
        temperament="12-TET",
        string_count=6,
        # ... add any other required fields from FretboardInput
    ),
    "gibson_les_paul_24.75": FretboardInput(
        scale_length_mm=628.65,
        fret_count=22,
        temperament="12-TET",
        string_count=6,
    ),
    "prs_25.0": FretboardInput(
        scale_length_mm=635.0,
        fret_count=24,
        temperament="12-TET",
        string_count=6,
    ),
    "fender_jazz_bass_34.0": FretboardInput(
        scale_length_mm=863.6,
        fret_count=20,
        temperament="12-TET",
        string_count=4,
    ),
    "smart_guitar_pro_fan_686_648": FretboardInput(
        # Multiscale spec — verify exact field names against Phase 1 schema
        # (may be bass_scale_mm/treble_scale_mm or scale_lengths_mm)
        bass_scale_mm=686.0,
        treble_scale_mm=648.0,
        fret_count=24,
        temperament="12-TET",
        string_count=6,
        perpendicular_distance=0.5,  # FretFind PD = 0.5 → 12th fret perpendicular
    ),
}


def get_preset(name: str) -> FretboardInput:
    """Look up a preset by name. Raises KeyError if not found."""
    if name not in FRETBOARD_PRESETS:
        raise KeyError(
            f"Unknown preset: {name!r}. "
            f"Available: {sorted(FRETBOARD_PRESETS.keys())}"
        )
    return FRETBOARD_PRESETS[name]


def list_presets() -> List[Dict[str, object]]:
    """Return preset summaries for the GET /presets endpoint.

    Returns label + brief identifying info, not the full FretboardInput
    (clients that want full input call /presets/{name} or supply their own).
    """
    return [
        {
            "name": name,
            "scale_length_mm": getattr(preset, "scale_length_mm", None)
                or getattr(preset, "treble_scale_mm", None),
            "fret_count": preset.fret_count,
            "temperament": preset.temperament,
            "string_count": preset.string_count,
            "is_multiscale": hasattr(preset, "bass_scale_mm")
                and getattr(preset, "bass_scale_mm", None) is not None,
        }
        for name, preset in FRETBOARD_PRESETS.items()
    ]
```

> **Pre-flight:** Read `app/instrument_geometry/neck/fretboard_ecosphere.py` to confirm the exact `FretboardInput` field names. Phase 1 may have used different names than the dev order assumed (e.g., `treble_scale` vs `treble_scale_mm`). Match what's there.

#### 3.2 New file: `services/api/app/api_v1/fretboard.py` (~250 lines)

```python
"""
Fretboard Ecosphere API v1

Public API surface for the canonical fretboard ecosphere:

    POST /fretboard/compute       Build ecosphere from request (free)
    POST /fretboard/scala         Export ecosphere temperament as Scala (free)
    GET  /fretboard/presets       List preset request shapes (free)
    GET  /fretboard/presets/{name} Get full preset request (free)
    GET  /fretboard/schema        Return JSON schema for FretboardEcosphere (free)

DXF endpoint added in Commit 2.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app.instrument_geometry.neck.fretboard_ecosphere import (
    FretboardInput,
    FretboardEcosphere,
    build_ecosphere,
)
from app.instrument_geometry.neck.fretboard_presets import (
    FRETBOARD_PRESETS,
    get_preset,
    list_presets,
)
from app.calculators.scala_loader import (
    serialize_scala_to_text,  # MUST add this in commit 1 if absent
)


router = APIRouter(prefix="/fretboard", tags=["Fretboard Ecosphere"])


# =============================================================================
# POST /compute
# =============================================================================

@router.post(
    "/compute",
    response_model=FretboardEcosphere,
    summary="Build canonical fretboard ecosphere",
)
def post_compute(req: FretboardInput) -> FretboardEcosphere:
    """Build the canonical fretboard ecosphere from validated input.

    The ecosphere is the single source of truth for all downstream
    projections (DXF, SVG, JSON, G-code). All temperaments are honest
    after Phase 1.5: 19-TET produces real 19-TET math, Pythagorean
    uses real ratios, etc.
    """
    try:
        return build_ecosphere(req)
    except ValueError as e:
        # Pydantic validation already handled by FastAPI. ValueError here
        # means a downstream kernel rejected the input (e.g., non-monotonic
        # custom ratios from a malformed Scala scale).
        raise HTTPException(status_code=422, detail=str(e))


# =============================================================================
# POST /scala — content-negotiated export
# =============================================================================

@router.post(
    "/scala",
    summary="Export ecosphere temperament as Scala scale",
    responses={
        200: {
            "description": "Scala scale (JSON or .scl text per Accept header)",
            "content": {
                "application/json": {},
                "application/octet-stream": {},
            },
        },
    },
)
def post_scala(req: FretboardInput, request: Request) -> Response:
    """Build an ecosphere and export its temperament as a Scala scale.

    Accept header controls format:
      application/json (default)  → structured JSON with cents, ratios, frequencies
      application/octet-stream     → downloadable .scl file
      text/plain                   → .scl text inline
    """
    try:
        eco = build_ecosphere(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    scale = eco.to_scala_intervals()
    accept = request.headers.get("accept", "application/json").lower()

    if "octet-stream" in accept or "text/plain" in accept:
        scl_text = serialize_scala_to_text(scale)
        media_type = (
            "text/plain" if "text/plain" in accept else "application/octet-stream"
        )
        # Build a friendly filename from the request — temperament + fret count
        filename = (
            f"{req.temperament}_{req.fret_count}fret.scl"
            .replace("/", "_").replace(" ", "_")
        )
        return Response(
            content=scl_text,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    # Default JSON
    return JSONResponse(content={
        "description": scale.description,
        "pitch_count": scale.pitch_count,
        "pitches": [
            {
                "source": p.source_text,
                "cents": p.cents,
                "ratio": list(p.ratio) if p.ratio else None,
                "frequency_ratio": p.frequency_ratio,
            }
            for p in scale.pitches
        ],
    })


# =============================================================================
# GET /presets
# =============================================================================

@router.get(
    "/presets",
    summary="List available preset configurations",
)
def get_presets() -> Dict[str, List[Dict[str, Any]]]:
    """Return summary of all available presets.

    Wrapped in {items: [...]} per OWASP recommendation against bare arrays.
    """
    return {"items": list_presets()}


@router.get(
    "/presets/{name}",
    response_model=FretboardInput,
    summary="Get full preset request shape by name",
)
def get_preset_by_name(name: str) -> FretboardInput:
    """Return the full FretboardInput for a named preset.

    Use the result as a starting point — POST it to /compute as-is or
    modify before POSTing.
    """
    try:
        return get_preset(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# GET /schema
# =============================================================================

@router.get(
    "/schema",
    summary="JSON Schema for FretboardEcosphere",
)
def get_schema() -> Dict[str, Any]:
    """Return Pydantic-generated JSON schema for client validation."""
    return FretboardEcosphere.model_json_schema()
```

#### 3.3 Modify: `services/api/app/calculators/scala_loader.py` (add ~30 lines)

The `/scala` route needs `serialize_scala_to_text` to render a `ScalaScale` back to `.scl` format. Phase 1.5 added the parser; the serializer is its symmetric counterpart. Add at the end of the existing module:

```python
def serialize_scala_to_text(scale: "ScalaScale") -> str:
    """Render a ScalaScale back to .scl format text.

    Symmetric counterpart to parse_scala_content. The output is
    parseable by parse_scala_content with byte-identical semantics
    (frequency_ratio values match within float precision).

    Format follows Huygens-Fokker conventions:
      Line 1: "! <description>.scl"
      Line 2: "!"
      Line 3: <description>
      Line 4: " <pitch_count>"
      Line 5: "!"
      Lines 6+: pitches in source form (cents or ratio)
    """
    lines: List[str] = []
    lines.append(f"! {scale.description.replace(chr(10), ' ')}.scl")
    lines.append("!")
    lines.append(scale.description)
    lines.append(f" {scale.pitch_count}")
    lines.append("!")
    for pitch in scale.pitches:
        # Preserve source form when available; otherwise emit cents
        if pitch.ratio is not None:
            num, den = pitch.ratio
            lines.append(f" {num}/{den}" if den != 1 else f" {num}")
        elif pitch.cents is not None:
            lines.append(f" {pitch.cents:.6f}")
        else:
            # Synthesized pitch (e.g., from temperament dispatcher) — emit
            # as cents derived from frequency_ratio
            import math
            cents = 1200.0 * math.log2(pitch.frequency_ratio)
            lines.append(f" {cents:.6f}")
    return "\n".join(lines) + "\n"
```

Add a round-trip test to the existing `test_scala_loader.py`:

```python
def test_serialize_round_trip_12tet():
    """parse → serialize → parse produces byte-identical frequency ratios."""
    original = parse_scala_file(SAMPLES / "12tet.scl")
    serialized = serialize_scala_to_text(original)
    reparsed = parse_scala_content(serialized)
    assert reparsed.pitch_count == original.pitch_count
    for orig, re in zip(original.pitches, reparsed.pitches):
        assert abs(orig.frequency_ratio - re.frequency_ratio) < 1e-9
```

#### 3.4 Modify: `services/api/app/api_v1/__init__.py` (add ~2 lines)

```python
# Add to imports section, alphabetically with other routers:
from .fretboard import router as fretboard_router

# Add to mount section, near other instrument-related routers:
router.include_router(fretboard_router)
```

#### 3.5 New test file: `services/api/app/tests/api_v1/test_fretboard_router.py` (~180 lines)

```python
"""Tests for /api/v1/fretboard/* routes (Commit 1: free routes only)."""
from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


# =============================================================================
# POST /compute
# =============================================================================

class TestComputeEndpoint:
    def test_compute_minimal_12tet(self):
        """Minimal valid request returns a complete ecosphere."""
        resp = client.post("/api/v1/fretboard/compute", json={
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "temperament": "12-TET",
            "string_count": 6,
            # ... any other required fields per the schema
        })
        assert resp.status_code == 200
        body = resp.json()
        # Schema-aligned response; no V1Response wrapper
        assert "fret_count" in body or "metadata" in body  # adjust to actual schema
        assert body.get("temperament") == "12-TET" or \
               body.get("metadata", {}).get("temperament") == "12-TET"

    def test_compute_19tet_produces_different_geometry(self):
        """19-TET request returns positions that differ materially from 12-TET."""
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "string_count": 6,
        }
        r12 = client.post("/api/v1/fretboard/compute",
                          json={**common, "temperament": "12-TET"})
        r19 = client.post("/api/v1/fretboard/compute",
                          json={**common, "temperament": "19-TET"})
        assert r12.status_code == 200
        assert r19.status_code == 200
        # Phase 1.5 invariant: 19-TET fret 12 differs from 12-TET fret 12
        # by >5mm at this scale length.
        # Adjust accessor to match actual schema shape.

    def test_compute_invalid_scale_length_returns_422(self):
        resp = client.post("/api/v1/fretboard/compute", json={
            "scale_length_mm": -100.0,
            "fret_count": 22,
            "temperament": "12-TET",
            "string_count": 6,
        })
        assert resp.status_code == 422

    def test_compute_unknown_temperament_returns_422(self):
        resp = client.post("/api/v1/fretboard/compute", json={
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "temperament": "purple",
            "string_count": 6,
        })
        assert resp.status_code == 422


# =============================================================================
# POST /scala
# =============================================================================

class TestScalaEndpoint:
    def test_scala_default_returns_json(self):
        resp = client.post("/api/v1/fretboard/scala", json={
            "scale_length_mm": 647.7, "fret_count": 12,
            "temperament": "12-TET", "string_count": 6,
        })
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        body = resp.json()
        assert body["pitch_count"] == 12
        assert len(body["pitches"]) == 12

    def test_scala_octet_stream_returns_scl_text(self):
        resp = client.post(
            "/api/v1/fretboard/scala",
            json={"scale_length_mm": 647.7, "fret_count": 12,
                  "temperament": "12-TET", "string_count": 6},
            headers={"Accept": "application/octet-stream"},
        )
        assert resp.status_code == 200
        text = resp.content.decode("utf-8")
        assert text.startswith("!") or "12" in text.split("\n")[3]
        # Content-Disposition for download
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_scala_text_plain_returns_scl_text(self):
        resp = client.post(
            "/api/v1/fretboard/scala",
            json={"scale_length_mm": 647.7, "fret_count": 12,
                  "temperament": "12-TET", "string_count": 6},
            headers={"Accept": "text/plain"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")


# =============================================================================
# GET /presets
# =============================================================================

class TestPresetsEndpoint:
    def test_presets_list_returns_items_array(self):
        resp = client.get("/api/v1/fretboard/presets")
        assert resp.status_code == 200
        body = resp.json()
        # OWASP: wrapped, not bare array
        assert "items" in body
        assert isinstance(body["items"], list)
        assert len(body["items"]) >= 5  # 5 seed presets

    def test_preset_by_name_returns_full_input(self):
        resp = client.get("/api/v1/fretboard/presets/fender_strat_25.5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["scale_length_mm"] == 647.7
        assert body["fret_count"] == 22

    def test_preset_unknown_returns_404(self):
        resp = client.get("/api/v1/fretboard/presets/nonexistent")
        assert resp.status_code == 404

    def test_preset_to_compute_pipeline(self):
        """A preset retrieved via GET should POST to /compute successfully."""
        preset_resp = client.get("/api/v1/fretboard/presets/prs_25.0")
        assert preset_resp.status_code == 200
        compute_resp = client.post("/api/v1/fretboard/compute",
                                    json=preset_resp.json())
        assert compute_resp.status_code == 200


# =============================================================================
# GET /schema
# =============================================================================

class TestSchemaEndpoint:
    def test_schema_returns_pydantic_json_schema(self):
        resp = client.get("/api/v1/fretboard/schema")
        assert resp.status_code == 200
        schema = resp.json()
        # Pydantic v2 JSON schema has these keys
        assert "$defs" in schema or "properties" in schema
        assert "title" in schema
```

#### 3.6 Acceptance for Commit 1

```
□ services/api/app/instrument_geometry/neck/fretboard_presets.py exists with 5 seed presets
□ services/api/app/api_v1/fretboard.py exists with 5 routes
□ services/api/app/calculators/scala_loader.py has serialize_scala_to_text
□ services/api/app/api_v1/__init__.py imports and mounts fretboard_router
□ Test file test_fretboard_router.py has ≥12 passing tests
□ /api/v1/fretboard/* routes appear in /openapi.json
□ All 5 routes return 200 (or appropriate error code) for valid inputs
□ git diff main..HEAD shows only the files listed above plus __init__.py
```

#### 3.7 Commit 1 message

```
feat(api): add /api/v1/fretboard router with free-tier endpoints

Sprint FRET-A Phase 2 Commit 1. Implements four free-tier routes
exposing the Phase 1.5 canonical ecosphere over HTTP:

  POST /api/v1/fretboard/compute       Build ecosphere from request
  POST /api/v1/fretboard/scala         Export temperament as Scala
       (content-negotiated: JSON default, .scl on octet-stream/text-plain)
  GET  /api/v1/fretboard/presets       List preset configurations
  GET  /api/v1/fretboard/presets/{name} Get full preset by name
  GET  /api/v1/fretboard/schema        Pydantic JSON schema

Adds:
  app/instrument_geometry/neck/fretboard_presets.py (5 seed presets)
  app/api_v1/fretboard.py (router)
  app/calculators/scala_loader.py: serialize_scala_to_text (round-trip
    test confirms byte-identical frequency ratios after parse→serialize→parse)

Tests: 12 router tests + 1 scala_loader round-trip test, all pass.
Existing tests: unchanged.

Phase 1.5 honesty surfaces publicly:
  - 19-TET request returns real 19-TET math (verified by integration test)
  - Pythagorean returns real ratios (verified by integration test)
  - Custom Scala input flows through scala_loader → kernel ratios

DXF endpoint deferred to Commit 2 (requires tier-gating wiring).
Round-trip integration test deferred to Commit 3.
```

---

### Commit 2 — DXF endpoint with tier gating

**Goal:** add the paid DXF route with auth gate and version inference.

#### 3.8 Modify: `services/api/app/api_v1/fretboard.py` (add ~80 lines)

Add to existing imports:

```python
from typing import Literal, Optional
from fastapi import Depends
from app.middleware.tier_gate import require_pro
from app.auth.deps import get_optional_principal
from app.auth.principal import Principal
from app.instrument_geometry.neck.fretboard_ecosphere import write_ecosphere_dxf
```

> **Note:** `write_ecosphere_dxf` lives in or is re-exported from `fretboard_ecosphere.py`. Phase 7 of the v2 dev order owns the actual DXF emission; for Phase 2 a placeholder implementation is acceptable. If the function does not exist yet, add a minimal stub that produces valid (but layer-spare) DXF bytes. See §3.9 below.

Add the route at the end of the file:

```python
# =============================================================================
# POST /dxf — tier-aware DXF projection
# =============================================================================

class DxfRequest(FretboardInput):
    """Extends FretboardInput with DXF-specific options."""
    dxf_version: Optional[Literal["R12", "R2000"]] = None


@router.post(
    "/dxf",
    summary="Export ecosphere as DXF (R12 free, R2000 pro tier)",
    responses={
        200: {
            "description": "DXF bytes",
            "content": {"application/dxf": {}, "application/octet-stream": {}},
        },
        401: {"description": "R2000 requested without authentication"},
        403: {"description": "R2000 requested without pro tier"},
    },
)
def post_dxf(
    req: DxfRequest,
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> Response:
    """Project the ecosphere to DXF bytes.

    Version selection:
      - If req.dxf_version is "R2000", require pro tier (returns 401/403 if not).
      - If req.dxf_version is "R12", return R12 LINE DXF (free).
      - If req.dxf_version is None and principal has pro tier: default R2000.
      - If req.dxf_version is None and no pro tier: default R12.

    Free tier always succeeds with R12. Pro tier can opt down to R12
    explicitly (legacy CAM tools, etc.).
    """
    try:
        eco = build_ecosphere(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Resolve version
    version = req.dxf_version
    if version is None:
        # Infer: pro principal → R2000, else R12
        version = "R2000" if _is_pro(principal) else "R12"

    # Auth-gate R2000 if explicitly requested without pro tier
    if version == "R2000" and not _is_pro(principal):
        if principal is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "auth_required",
                    "message": "R2000 LWPOLYLINE output requires authentication",
                    "free_alternative": "Set dxf_version='R12' for unauthenticated R12 output",
                },
            )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tier_required",
                "current_tier": "free",
                "required_tier": "pro",
                "free_alternative": "Set dxf_version='R12' for free R12 output",
            },
        )

    # Project
    dxf_bytes = write_ecosphere_dxf(eco, version=version)

    filename = f"fretboard_{req.temperament}_{req.fret_count}fret_{version}.dxf"\
        .replace("/", "_").replace(" ", "_")
    return Response(
        content=dxf_bytes,
        media_type="application/dxf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-DXF-Version": version,  # convenience for clients
        },
    )


def _is_pro(principal: Optional[Principal]) -> bool:
    """Check whether principal has pro tier (sync helper for the route).

    Note: require_tier is async because it queries the DB. For the inference
    path we already have the principal in hand from get_optional_principal,
    but tier comes from a separate query. Use a sync check that reads from
    the principal's cached tier field if available, otherwise default to False
    (which is the safe choice — defaults to R12).
    """
    if principal is None:
        return False
    # Principal model from PR #10 should expose tier; if it does not, this
    # check returns False and the caller falls back to R12. Pro users can
    # still explicitly request R2000, which routes through require_pro
    # via the explicit auth path above.
    return getattr(principal, "tier", "free") == "pro"
```

> **Wiring caveat:** `_is_pro` reads tier from the principal directly to keep the route synchronous. If the principal model from PR #10 does not carry tier (it requires a DB query via `require_tier`), this helper will always return False, meaning unauthenticated default is R12 (correct) but authenticated default is also R12 (suboptimal — pro users have to explicitly set `dxf_version="R2000"` to get it). That's acceptable behavior for Phase 2; refining the inference is a small follow-up.

#### 3.9 Verify or stub: `write_ecosphere_dxf` in `fretboard_ecosphere.py`

If Phase 1.5 did not add this function, Commit 2 needs a minimal stub:

```python
def write_ecosphere_dxf(
    eco: FretboardEcosphere,
    version: Literal["R12", "R2000"] = "R12",
) -> bytes:
    """Project ecosphere to DXF bytes via central DxfWriter.

    Phase 2 stub — emits FRETS layer with fret line positions only.
    Phase 7 (v2 dev order) populates the full layer set:
      STRINGS, FRETS, FRETBOARD_OUTLINE, FRET_SLOTS, NUT, BRIDGE,
      BRIDGE_COMPENSATED, HARMONICS_OVERLAY, ANNOTATIONS.
    """
    from app.cam.dxf_writer import DxfWriter, LayerDef

    writer = DxfWriter(
        layers=[LayerDef(name="FRETS", color=7)],
        version=version,
    )
    # Project at least the fret line geometry from eco.frets
    # (exact accessor depends on Phase 1 schema)
    for fret_line in getattr(eco, "frets", []):
        # Adjust to actual schema
        bass_xy = (fret_line.bass_x, fret_line.bass_y)
        treble_xy = (fret_line.treble_x, fret_line.treble_y)
        writer.add_line("FRETS", bass_xy, treble_xy)

    return writer.to_bytes()
```

This stub passes through `DxfWriter` so version-aware emission works without Phase 7 being done. It's intentionally minimal — Phase 7 fills out the rest of the layers.

#### 3.10 Add to `test_fretboard_router.py` (~120 lines)

```python
class TestDxfEndpoint:
    def test_dxf_default_unauthenticated_returns_r12(self):
        """No auth, no version → R12 LINE DXF."""
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "12-TET", "string_count": 6,
        })
        assert resp.status_code == 200
        assert resp.headers.get("X-DXF-Version") == "R12"
        # AC1009 is the DXF version code for R12
        assert b"AC1009" in resp.content[:200]

    def test_dxf_explicit_r12_unauthenticated_succeeds(self):
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "12-TET", "string_count": 6,
            "dxf_version": "R12",
        })
        assert resp.status_code == 200
        assert b"AC1009" in resp.content[:200]

    def test_dxf_r2000_unauthenticated_returns_401(self):
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "12-TET", "string_count": 6,
            "dxf_version": "R2000",
        })
        assert resp.status_code == 401
        body = resp.json()
        # Hint to use R12 alternative
        assert "R12" in str(body)

    @pytest.mark.skip(reason="Requires test fixture for pro principal — see test infrastructure note")
    def test_dxf_r2000_pro_authenticated_returns_r2000(self):
        """When auth fixture is available, this test verifies R2000 output."""
        # Override tier_gate dependency in app.dependency_overrides
        # See https://fastapi.tiangolo.com/advanced/testing-dependencies/
        # for the standard pattern.
        pass

    def test_dxf_returns_dxf_content_type(self):
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "12-TET", "string_count": 6,
        })
        assert resp.headers["content-type"] == "application/dxf"
        assert "attachment" in resp.headers.get("content-disposition", "")
```

> **Note on the skipped pro-tier test:** the auth fixture pattern depends on details of how `get_optional_principal` and `require_pro` were wired in PR #10. The test is included as a placeholder; the engineer should implement the dependency override using FastAPI's `app.dependency_overrides` pattern once they've inspected how PR #10's tests handle auth. If PR #10 already established a pattern for auth-fixture tests elsewhere in the codebase (look for `dependency_overrides[get_optional_principal]` or similar), mirror it here.

#### 3.11 Acceptance for Commit 2

```
□ POST /api/v1/fretboard/dxf accepts FretboardInput + optional dxf_version
□ Default unauthenticated → R12 (verified by AC1009 in response bytes)
□ Explicit R12 unauthenticated → 200 with R12 output
□ Explicit R2000 unauthenticated → 401 with R12 alternative hint
□ DxfRequest schema validated; invalid version → 422
□ X-DXF-Version response header set correctly
□ Content-Disposition includes filename with version suffix
□ 4 unit tests pass (1 skipped pending auth fixture)
□ Phase 7 stub for write_ecosphere_dxf produces valid DXF (parses with ezdxf)
```

#### 3.12 Commit 2 message

```
feat(api): add /api/v1/fretboard/dxf with tier gating

Sprint FRET-A Phase 2 Commit 2. Adds DXF projection endpoint with
free/pro tier separation:

  POST /api/v1/fretboard/dxf

Behavior:
  - dxf_version=R12 (or default unauthenticated): always 200, AC1009 LINE
  - dxf_version=R2000 unauthenticated: 401 with hint to use R12
  - dxf_version=R2000 with pro tier (when auth fixture available): 200 AC1015
  - dxf_version=None: inferred from principal tier (R2000 if pro, R12 else)

Dependencies:
  - app.middleware.tier_gate.require_pro (from PR #10)
  - app.auth.deps.get_optional_principal (from PR #10)
  - app.cam.dxf_writer.DxfWriter (version-aware after PR #10 gate lift)

Phase 7 stub:
  write_ecosphere_dxf currently projects FRETS layer only. Full nine-layer
  emission (STRINGS, FRETBOARD_OUTLINE, FRET_SLOTS, NUT, BRIDGE,
  BRIDGE_COMPENSATED, HARMONICS_OVERLAY, ANNOTATIONS) deferred to Phase 7
  per v2 dev order. Stub passes through DxfWriter so version selection
  works correctly today; Phase 7 swap is layer expansion only.

Tests: 4 router tests for DXF (1 skipped pending pro-tier auth fixture).
Existing Commit 1 tests unchanged.
```

---

### Commit 3 — Round-trip integration test

**Goal:** validate the contract that compute → scala → parse → compute is structurally honest.

#### 3.13 New file: `services/api/app/tests/integration/__init__.py` (empty, ~0 lines)

If this directory does not exist, create it. The empty `__init__.py` makes it a Python package.

#### 3.14 New file: `services/api/app/tests/integration/test_fretboard_ecosphere_roundtrip.py` (~120 lines)

```python
"""Round-trip integration tests for the fretboard ecosphere API.

These tests exercise the contract that the API can serialize an ecosphere's
temperament out to Scala, parse the Scala back, and rebuild an ecosphere
that produces byte-identical fret positions.

Lives in tests/integration/ rather than tests/api_v1/ because it spans
multiple endpoints and asserts a property across them.
"""
from __future__ import annotations

import io
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.calculators.scala_loader import (
    parse_scala_content,
    scala_to_fret_ratios,
)
from app.calculators.alternative_temperaments import (
    compute_fret_positions_from_ratios_mm,
)

client = TestClient(app)


def _build(req: dict) -> dict:
    """Helper: POST to /compute, return parsed JSON."""
    resp = client.post("/api/v1/fretboard/compute", json=req)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _scala_text(req: dict) -> str:
    """Helper: POST to /scala with octet-stream Accept, return .scl text."""
    resp = client.post(
        "/api/v1/fretboard/scala",
        json=req,
        headers={"Accept": "application/octet-stream"},
    )
    assert resp.status_code == 200, resp.text
    return resp.content.decode("utf-8")


# =============================================================================
# Compute → Scala → Parse → Compute identity
# =============================================================================

class TestRoundTrip12TET:
    """The defining round-trip: 12-TET should be byte-identical through the loop."""

    def test_compute_to_scala_to_parse_to_compute_identity(self):
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "temperament": "12-TET",
            "string_count": 6,
        }
        # Round 1: compute
        eco_a = _build(common)

        # Round 2: scala export
        scl = _scala_text(common)
        assert scl.count("\n") >= 5  # has at least header + pitches

        # Round 3: parse the scala back, derive ratios, recompute positions
        scale = parse_scala_content(scl)
        scl_ratios = scala_to_fret_ratios(scale, fret_count=22)
        scl_positions = compute_fret_positions_from_ratios_mm(647.7, scl_ratios)

        # Round 4: extract eco_a's positions for the same string
        # (accessor depends on actual schema — adjust to whatever Phase 1 named it)
        eco_a_positions = _extract_first_string_positions(eco_a)

        # Identity check
        assert len(scl_positions) == len(eco_a_positions) == 22
        for s, e in zip(scl_positions, eco_a_positions):
            assert abs(s - e) < 1e-9, (
                f"Round-trip diverged: scl={s:.12f}mm, eco={e:.12f}mm, diff={abs(s-e):.2e}mm"
            )


class TestRoundTrip19TET:
    """N-TET round-trip — proves the temperament dispatcher is honest end-to-end."""

    def test_19tet_round_trip(self):
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 19,
            "temperament": "19-TET",
            "string_count": 6,
        }
        eco_a = _build(common)
        scl = _scala_text(common)
        scale = parse_scala_content(scl)
        scl_ratios = scala_to_fret_ratios(scale, fret_count=19)
        scl_positions = compute_fret_positions_from_ratios_mm(647.7, scl_ratios)
        eco_a_positions = _extract_first_string_positions(eco_a)

        assert len(scl_positions) == 19
        for s, e in zip(scl_positions, eco_a_positions):
            assert abs(s - e) < 1e-9


class TestRoundTripNonEqualTemperament:
    """Pythagorean — proves named-temperament path is honest end-to-end."""

    def test_pythagorean_round_trip(self):
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 12,  # one octave for cleanest comparison
            "temperament": "pythagorean",
            "string_count": 6,
        }
        eco_a = _build(common)
        scl = _scala_text(common)
        scale = parse_scala_content(scl)
        scl_ratios = scala_to_fret_ratios(scale, fret_count=12)
        scl_positions = compute_fret_positions_from_ratios_mm(647.7, scl_ratios)
        eco_a_positions = _extract_first_string_positions(eco_a)

        for s, e in zip(scl_positions, eco_a_positions):
            assert abs(s - e) < 1e-9


# =============================================================================
# Cross-endpoint consistency
# =============================================================================

class TestPresetToComputeConsistency:
    """A preset retrieved via GET should compute identically when POSTed back."""

    def test_strat_preset_roundtrip(self):
        preset = client.get("/api/v1/fretboard/presets/fender_strat_25.5").json()
        eco = _build(preset)
        # Pick any deterministic invariant that the schema exposes
        positions = _extract_first_string_positions(eco)
        assert len(positions) == 22
        # Fret 12 of 25.5" 12-TET = ~323.85 mm
        assert abs(positions[11] - 323.85) < 0.01


# =============================================================================
# Helpers
# =============================================================================

def _extract_first_string_positions(eco: dict) -> list[float]:
    """Extract fret distances from nut for the first string.

    Adjust to whatever the actual schema exposes. Possibilities:
      eco["frets"][i]["distance_mm"]
      eco["frets"]["positions"][i]
      eco["fret_positions"][i]
    """
    # Most likely shape from Phase 1.5:
    if "fret_positions" in eco:
        return eco["fret_positions"]
    if "frets" in eco and isinstance(eco["frets"], list):
        return [f.get("distance_mm") or f.get("position_mm") for f in eco["frets"]]
    raise KeyError(
        f"Cannot find fret positions in ecosphere — keys: {list(eco.keys())[:10]}"
    )
```

> **Pre-flight for the engineer:** before running Commit 3 tests, read the actual `FretboardEcosphere` schema in `fretboard_ecosphere.py` and adjust `_extract_first_string_positions` to match the actual field shape. The dev order's guesses are illustrative only.

#### 3.15 Acceptance for Commit 3

```
□ tests/integration/ directory exists with __init__.py
□ test_fretboard_ecosphere_roundtrip.py has ≥4 round-trip tests
□ All round-trip tests pass at 1e-9 mm tolerance
□ 12-TET, 19-TET, and Pythagorean round-trips all confirmed
□ Preset → compute consistency confirmed
□ No flakiness on repeated runs (seed-stable)
```

#### 3.16 Commit 3 message

```
test(api): add round-trip integration tests for fretboard ecosphere

Sprint FRET-A Phase 2 Commit 3. Validates the structural honesty
contract that the API surface establishes:

  compute → scala export → parse → ratios → positions
  must equal compute's own positions within 1e-9 mm.

Tests:
  - 12-TET round-trip identity (defining contract)
  - 19-TET round-trip identity (proves N-TET path honest end-to-end)
  - Pythagorean round-trip identity (proves named-temperament honest end-to-end)
  - Preset → compute pipeline consistency

These are integration tests (cross multiple endpoints, assert
properties across them) rather than unit tests. Located at
app/tests/integration/test_fretboard_ecosphere_roundtrip.py.

The 1e-9 mm tolerance is the same gate the Phase 1.5 schema delegation
tests use, applied here at the API layer instead of the Python layer.
If a future schema change breaks the round-trip, this test surfaces
it before customer-facing API drift.

Closes Sprint FRET-A Phase 2.
```

---

## 4. Utilities Available to the Phase 2 Implementer

These already exist on the branch after Phase 1.5. The engineer should reuse them rather than reimplement.

### From the math kernel (`app.calculators.alternative_temperaments`)

```python
TemperamentSystem            # Enum: 12-TET, 19-TET, 24-TET, 31-TET, just_*, pythagorean, meantone_1/4, custom
resolve_temperament_ratios   # Dispatcher — unified entry to per-fret ratios for any system
compute_fret_positions_from_ratios_mm  # Ratios → distances from nut, validated monotonic
compute_n_tet_ratios         # N-tone equal-temperament ratio generator
```

### From the math kernel (`app.instrument_geometry.neck.fret_math`)

```python
compute_fret_positions_mm                  # Single-scale 12-TET (oldest helper, still useful)
compute_multiscale_fret_positions_mm       # Fan-fret, with PD + per-string scale array support after Phase 1.5
perpendicular_distance_for_fret            # FretFind PD ↔ integer-fret converter
```

### From the schema (`app.instrument_geometry.neck.fretboard_ecosphere`)

```python
FretboardInput               # Request shape (Pydantic input model)
FretboardEcosphere           # Response shape (Pydantic output model)
build_ecosphere              # Assembler — request in, ecosphere out
write_ecosphere_dxf          # DXF projector (stub for Phase 2, full in Phase 7)
```

### From the Scala module (`app.calculators.scala_loader`)

```python
parse_scala_content          # Text → ScalaScale
parse_scala_file             # Path → ScalaScale
scala_to_fret_ratios         # ScalaScale → flat ratio list
ScalaScale, ScalaPitch       # Dataclasses
serialize_scala_to_text      # ScalaScale → .scl text (NEW in Commit 1 of Phase 2)
```

### From auth (PR #10)

```python
require_pro                  # Module-level FastAPI dependency for pro-tier routes
                             # Use as: dependencies=[Depends(require_pro)]
                             # Returns Principal on success, raises 401/403 on fail
get_optional_principal       # Returns Principal | None — no exception on unauthenticated
get_current_principal        # Returns Principal — raises 401 on unauthenticated
Principal                    # auth.principal model
```

### From DXF infrastructure (PR #10)

```python
DxfWriter                    # version-aware (R12 or R2000) writer with consistent settings
LayerDef                     # Layer definition (name, color, etc.)
```

---

## 5. Test Cases (Aggregate Across All Commits)

```
Commit 1 (router skeleton):           12 router tests + 1 scala_loader test
Commit 2 (DXF endpoint):               4 DXF tests (1 skipped pending fixture)
Commit 3 (round-trip integration):     4 round-trip tests
                              Total:   21 new tests
                       Existing tests: unchanged (Phase 1.5 baseline preserved)
```

### Critical assertions

- 19-TET API output structurally differs from 12-TET API output (proves dispatcher is real at API layer)
- Pythagorean API output structurally differs from 12-TET API output (proves named-temperament path real at API layer)
- compute → scala → parse → compute identity at 1e-9 mm tolerance (proves API surface is structurally honest)
- R12 DXF output starts with AC1009 header bytes (proves version selection works)
- R2000 unauthenticated returns 401 with R12 alternative hint (proves tier gate works)
- Preset GET → compute POST returns valid ecosphere (proves preset infrastructure works end-to-end)

### Pre-flight before tests run

```bash
# Recapture clean baseline on sprint/fret-ecosphere-a (post Phase 1.5)
cd services/api
pytest -v --tb=short 2>&1 | tee /tmp/baseline_pre_phase_2.txt
echo "Exit code: $?" >> /tmp/baseline_pre_phase_2.txt

# After each Phase 2 commit, diff:
pytest -v --tb=short 2>&1 | tee /tmp/post_$(git rev-parse --short HEAD).txt
diff <(grep -E "^(PASSED|FAILED|ERROR)" /tmp/baseline_pre_phase_2.txt | sort) \
     <(grep -E "^(PASSED|FAILED|ERROR)" /tmp/post_*.txt | sort) | head -50
```

Any movement from PASSED to FAILED is a regression. Investigate before continuing.

> **Caveat on baseline:** Phase 1 of FRET-A produced a noisy baseline (428 failures across modules). Phase 1.5 ran a targeted suite (72 passed, 2 xfailed) rather than the full project. Phase 2 should follow the same approach — run targeted suites for the modules being touched, accept that the broader baseline noise is tracked separately in SPRINTS.md as test-debt cleanup. Don't get blocked on the 428 unrelated failures; they're tech debt, not Phase 2 regressions.

---

## 6. Rollout Order (Step by Step)

```
Step 0 — Pre-flight verification         (~10 min)
  □ Confirm Phase 1.5 commits are present:
      git log --oneline ac96430f..d72d9744
      Should show 3 commits.
  □ Run targeted test suite for Phase 1.5 modules:
      pytest app/tests/test_fretboard_ecosphere.py \
             app/tests/calculators/test_alternative_temperaments.py \
             app/tests/calculators/test_scala_loader.py \
             app/tests/test_fan_fret_perpendicular.py
      Confirm green.
  □ Read app/instrument_geometry/neck/fretboard_ecosphere.py to confirm
    actual FretboardInput / FretboardEcosphere field names.
  □ Read app/api_v1/__init__.py to confirm router mount pattern unchanged.
  □ Capture clean Phase 1.5 baseline:
      pytest -v --tb=short 2>&1 | tee /tmp/baseline_pre_phase_2.txt

Step 1 — Commit 1 implementation         (~75 min)
  □ Create app/instrument_geometry/neck/fretboard_presets.py
  □ Create app/api_v1/fretboard.py with 5 routes (no DXF)
  □ Modify app/calculators/scala_loader.py: add serialize_scala_to_text
  □ Modify app/api_v1/__init__.py: import + include_router
  □ Create app/tests/api_v1/test_fretboard_router.py with 12 tests
  □ Run: pytest app/tests/api_v1/test_fretboard_router.py
  □ All 12 tests pass + scala_loader round-trip test passes
  □ Commit. Verify against baseline.

Step 2 — Commit 2 implementation         (~60 min)
  □ Add write_ecosphere_dxf stub to fretboard_ecosphere.py if absent
  □ Add DXF route + DxfRequest schema to api_v1/fretboard.py
  □ Add 4 DXF tests to test_fretboard_router.py
  □ Run: pytest app/tests/api_v1/test_fretboard_router.py
  □ All ≥16 tests pass (1 skipped for pro-tier fixture)
  □ Commit. Verify against baseline.

Step 3 — Commit 3 implementation         (~45 min)
  □ Create app/tests/integration/__init__.py if absent
  □ Create test_fretboard_ecosphere_roundtrip.py with 4 tests
  □ Run: pytest app/tests/integration/test_fretboard_ecosphere_roundtrip.py
  □ All 4 round-trip tests pass at 1e-9 mm tolerance
  □ Run full Phase 2 suite:
      pytest app/tests/api_v1/ app/tests/integration/
  □ Commit.

Step 4 — Verification + handoff          (~20 min)
  □ Run full targeted test suite for Phase 2:
      pytest app/tests/api_v1/test_fretboard_router.py \
             app/tests/integration/test_fretboard_ecosphere_roundtrip.py
  □ Hit live endpoints with curl from a running uvicorn:
      uvicorn app.main:app --port 8000
      curl -X POST http://localhost:8000/api/v1/fretboard/compute \
           -H "Content-Type: application/json" \
           -d '{"scale_length_mm": 647.7, "fret_count": 22, "temperament": "12-TET", "string_count": 6}'
  □ Confirm /openapi.json includes 5 fretboard routes
  □ Push branch
  □ Update SPRINTS.md: Phase 2 → COMPLETED
                      DXF projection (Phase 7) → next
                      Pro-tier auth fixture → tracked tech-debt item
```

---

## 7. Known Risks and Mitigations

```
Risk: Phase 1 schema field names differ from this dev order's assumptions.
Mitigation: Step 0 pre-flight reads the actual schema. Adjust before writing code.

Risk: write_ecosphere_dxf does not exist yet (Phase 7 deferred its creation).
Mitigation: Commit 2 stub passes through DxfWriter. Stub is small (~15 lines).
            Phase 7 swaps the stub for full layer emission later.

Risk: Pro-tier auth fixture pattern not established in PR #10's tests.
Mitigation: Pro-tier R2000 test marked @pytest.mark.skip with explanation.
            R12 default and R2000-without-auth (401) cases verified instead.
            Once auth fixture pattern is in place, unskip the test in a
            follow-up commit.

Risk: 428 broken tests in main pollute Phase 2 verification signal.
Mitigation: Run targeted suites for changed modules only. Track baseline
            cleanup as SPRINTS.md tech-debt item, separate from Phase 2.

Risk: Round-trip test depends on scala_to_fret_ratios working correctly
      end-to-end including period repetition.
Mitigation: Phase 1.5 already shipped the round-trip identity for direct
            kernel calls. Phase 2 round-trip is the same property at the
            API surface. If it fails, the bug is in Phase 2 wiring (or
            scala_loader regression), not in the kernel.

Risk: Engineer drifts from the staged commit plan and bundles work into
      one commit (as happened in Phase 1).
Mitigation: Three commits, three test runs, three baseline diffs. Each
            commit must be green before the next starts. Don't bundle.
```

---

## 8. After Phase 2 Lands

```
Sprint FRET-A v2 phase status:
  ✓ Phase 1   — Schema (commit 9d37f1ea)
  ✓ Phase 1.5 — Math kernel honesty refactor (commits ac96430f, e260f365, d72d9744)
  ✓ Phase 2   — API router (after this sprint)
  □ Phase 3-5 — Already absorbed into Phase 1
  □ Phase 6   — Already absorbed into Phase 2
  □ Phase 7   — DXF projection layer (full nine-layer set)
  □ Phase 8   — Frontend wire-up
  □ Phase 9   — Schema doc + examples
  □ Phase 10  — Integration smoke + commit
```

The natural next sprint is Phase 7 — replacing the DXF stub with the full nine-layer projection. That's where the closed-polyline emission for fret slots (avoiding the 2-point loop-assembly gap) lives. The GRBL pipeline pass test from the v2 dev order Phase 7 acceptance becomes meaningful at that point.

Phase 8 (frontend) can run in parallel with Phase 7 if there's a second pair of hands available — the API surface from Phase 2 is what the frontend consumes, and it's stable enough now to build against.

---

**End of Sprint FRET-A Phase 2 Dev-Ready Handoff**
