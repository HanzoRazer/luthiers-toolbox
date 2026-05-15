# MRP Dev Order 5E — Acoustic Body Semantic Research Handoff

**Date:** 2026-05-14  
**Dev Order:** MRP-5E  
**Status:** COMPLETE

---

## Summary

MRP-5E established the semantic vocabulary and architectural concepts for future acoustic CAD translation:

1. **Acoustic Body Semantic Model** — Comprehensive inventory of acoustic body concepts
2. **Topology Continuity Model** — G0/G1/G2 continuity requirements for body junctions
3. **Thickness Hierarchy Model** — Four-level progression from uniform to continuous thickness
4. **Semantic Rules** — Authority boundaries between BOE, IBG, cad_semantics, and translator
5. **Readiness Matrix** — Instrument family classification by CAD translation readiness

**Sprint Type:** Research + Semantic Architecture (no runtime code changes)

---

## Deliverables

### 1. Acoustic Body Semantic Model

**Location:** `docs/architecture/ACOUSTIC_BODY_SEMANTIC_MODEL.md`

**Content:**
- Current state analysis (flat-body semantics, IBG morphology data)
- Acoustic semantic inventory with readiness classifications
- Side/rim semantic model with `AcousticSideSemantics` proposal
- Top/back semantic model with `AcousticPlateSemantics` proposal
- Proposed `AcousticCadSemantics` extension

**Semantic Classifications:**

| Classification | Count | Examples |
|----------------|-------|----------|
| SCHEMA_READY | 7 | side_depth_profile, butt_depth_mm, back_radius_mm |
| DERIVABLE | 4 | Side taper profile, chamber volume estimate |
| REQUIRES_USER_INPUT | 4 | Top arch height, side thickness |
| RESEARCH_ONLY | 4 | Longitudinal arch curve, tap-tuned thickness maps |
| OUT_OF_SCOPE | 4 | Sound post position, f-hole carving |

### 2. Topology Continuity Model

**Location:** `docs/architecture/ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md`

**Content:**
- Continuity classifications (G0, G1, G2)
- Junction types (side-to-top, side-to-back, side seam)
- Shell continuity requirements
- Surface type transitions
- Topology validation rules

**Key Decisions:**
- G0 (positional) sufficient for visualization/prototyping
- G1 (tangent) required for acoustic body shells
- G2 (curvature) reserved for archtop carving (RESEARCH_ONLY)

### 3. Thickness Hierarchy Model

**Location:** `docs/governance/THICKNESS_HIERARCHY_MODEL.md`

**Content:**
- Level 1: Uniform thickness (IMPLEMENTED)
- Level 2: Component thickness (SCHEMA_READY)
- Level 3: Zonal thickness (DERIVABLE)
- Level 4: Continuous thickness field (RESEARCH_ONLY)

**Translator Support Matrix:**

| Translator | L1 | L2 | L3 | L4 |
|------------|----|----|----|----|
| body_outline_step_ap203 | YES | FUTURE | FUTURE | NO |
| acoustic_body_step (proposed) | NO | YES | FUTURE | NO |

### 4. Acoustic CAD Semantic Rules

**Location:** `docs/governance/ACOUSTIC_CAD_SEMANTIC_RULES.md`

**Content:**
- Authority hierarchy (BOE → IBG → cad_semantics → Translator)
- Core semantic rules (5 rules)
- Semantic field authority matrix
- Validation rules (pre/post translation)
- Error classifications

**Core Rules:**
1. Geometry Non-Mutation — Translator may NOT alter BOE coordinates
2. Semantic Extension Only — cad_semantics extends, never overrides
3. Advisory Consumption — IBG data consumed but not required
4. Continuity Construction — Translator may construct for continuity
5. Classification Fidelity — Respect cad_intent classification

### 5. Acoustic CAD Readiness Matrix

**Location:** `docs/governance/ACOUSTIC_CAD_READINESS_MATRIX.md`

**Content:**
- Readiness classifications (5 levels)
- Instrument family matrix (guitar, archtop, electric, mandolin, ukulele)
- Capability requirements by family
- Blocker analysis
- Sprint alignment

**Instrument Readiness Summary:**

| Family | SCHEMA_READY | RESEARCH_REQUIRED | OUT_OF_SCOPE |
|--------|--------------|-------------------|--------------|
| Acoustic guitar | 7 types | — | — |
| Archtop | — | 3 types | — |
| Electric (chamber) | 1 type | 1 type | — |
| Mandolin | 1 type | 2 types | — |
| Ukulele | 4 types | — | — |
| Violin | — | — | All |

---

## IBG Data Investigation

### Existing IBG Morphology Data

**Source:** `app/ibg/ibg_morphology_extension.py`

| Field | Type | Purpose |
|-------|------|---------|
| `side_heights_mm` | `List[float]` | Side depth at profile points |
| `radii_by_zone` | `Dict[str, float]` | Zone-based radii for brace fitting |
| `dimensions` | `Dict[str, float]` | lower_bout, upper_bout, waist, body_length |

**Source:** `app/ibg/instrument_specs.py` (INSTRUMENT_SPECS)

| Field | Type | Example (Dreadnought) |
|-------|------|----------------------|
| `back_radius_mm` | `float` | 7620mm (25ft standard) |
| `butt_depth_mm` | `float` | 121mm |
| `shoulder_depth_mm` | `float` | 105mm |
| `top_thickness_mm` | `float` | 2.8mm |
| `back_thickness_mm` | `float` | 2.5mm |

### IBG Authority Boundaries

```
IBG = Advisory morphology authority (may provide hints)
BOE = Geometry approval authority (owns outline)
cad_semantics = CAD construction hints (for translator use)
CAD Translator = Topology construction (from approved data only)
```

**Key Rule:** cad_semantics may EXTEND context from IBG. It may NOT OVERRIDE geometry approved by BOE.

---

## Files Created

| File | Type | Purpose |
|------|------|---------|
| `docs/architecture/ACOUSTIC_BODY_SEMANTIC_MODEL.md` | Architecture | Semantic vocabulary |
| `docs/architecture/ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md` | Architecture | Topology continuity |
| `docs/governance/THICKNESS_HIERARCHY_MODEL.md` | Governance | Thickness levels |
| `docs/governance/ACOUSTIC_CAD_SEMANTIC_RULES.md` | Governance | Authority rules |
| `docs/governance/ACOUSTIC_CAD_READINESS_MATRIX.md` | Governance | Instrument readiness |
| `docs/handoffs/MRP_5E_ACOUSTIC_BODY_SEMANTIC_RESEARCH.md` | Handoff | This document |

---

## What Was NOT Built (By Design)

This sprint explicitly excludes:

- **Runtime code changes** — No Python implementation
- **Schema modifications** — No Pydantic model changes
- **Translator updates** — No STEP generator modifications
- **Test additions** — No new pytest files

MRP-5E is research and semantic architecture only.

---

## Key Concepts Established

### Acoustic cad_semantics Extension (Proposed)

```python
class AcousticCadSemantics(BaseModel):
    cad_intent: Literal["flat_body", "acoustic_body", "archtop_body"]
    acoustic_type: Optional[Literal["flat_top", "arched_top", "hollow_electric"]]
    side_profile_type: Optional[Literal["constant", "tapered"]]
    butt_depth_mm: Optional[float]
    shoulder_depth_mm: Optional[float]
    top_surface_type: Optional[Literal["flat", "radiused", "arched"]]
    back_surface_type: Optional[Literal["flat", "radiused"]]
    back_radius_mm: Optional[float]
    top_thickness_mm: Optional[float]
    back_thickness_mm: Optional[float]
```

**Status:** PROPOSED (not implemented)

### Thickness Hierarchy

| Level | Name | Status |
|-------|------|--------|
| 1 | Uniform | IMPLEMENTED |
| 2 | Component | SCHEMA_READY |
| 3 | Zonal | DERIVABLE |
| 4 | Continuous | RESEARCH_ONLY |

### Continuity Requirements

| Junction | Required Level |
|----------|----------------|
| Side-to-top | G1 (tangent) |
| Side-to-back | G1 (tangent) |
| Side seam | G0 (positional) |

---

## Next Steps (Not in MRP-5E Scope)

| Sprint | Focus | Deliverables |
|--------|-------|--------------|
| MRP-5F | External CAD validation | FreeCAD import tests |
| MRP-5G | Side/rim topology prototype | Tapered rim generator |
| MRP-5H | CAD kernel evaluation | CadQuery/OCC assessment |
| MRP-5I | Acoustic STEP prototype | Acoustic body translator |
| MRP-5J | Carved-top research | Archtop topology model |

---

## Definition of Done

✅ IBG morphology data documented  
✅ INSTRUMENT_SPECS reviewed and catalogued  
✅ Acoustic semantic vocabulary defined  
✅ Semantic inventory classified (SCHEMA_READY, DERIVABLE, etc.)  
✅ Side/rim semantic model documented  
✅ Top/back semantic model documented  
✅ Thickness hierarchy documented (Levels 1-4)  
✅ Topology continuity model documented  
✅ Authority boundaries documented  
✅ Instrument readiness matrix created  
✅ Handoff document exists

---

## Related Documents

- `MRP_5D_CAD_REGRESSION_GOVERNANCE_HANDOFF.md` — Previous sprint
- `ACOUSTIC_BODY_SEMANTIC_MODEL.md` — Semantic vocabulary
- `ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md` — Topology requirements
- `THICKNESS_HIERARCHY_MODEL.md` — Thickness progression
- `ACOUSTIC_CAD_SEMANTIC_RULES.md` — Authority rules
- `ACOUSTIC_CAD_READINESS_MATRIX.md` — Instrument readiness
- `CAD_TRANSLATOR_PROMOTION_THRESHOLDS.md` — Promotion criteria
