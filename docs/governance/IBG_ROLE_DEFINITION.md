# Image Body Generator (IBG) — Role Definition

**Status:** ACTIVE GOVERNANCE  
**Effective:** 2026-05-11

---

## Canonical Role

IBG is a **parametric geometry completor**, not an image processor.

```
Input: Partial DXF outline (82-88% complete)
Process: Landmark extraction → Constraint solving → Outline generation
Output: Solved body model (100% complete)
```

---

## What IBG Does

| Function | Method | Status |
|----------|--------|--------|
| Complete partial DXF from vectorizer | `complete_from_dxf()` | PRODUCTION |
| Complete from user landmarks | `complete_from_landmarks()` | PRODUCTION |
| Generate from family defaults | `generate_from_defaults()` | PRODUCTION |
| Export solved model to DXF | `save_dxf()` | PRODUCTION |
| Calculate side heights | `solve_side_height()` | PRODUCTION |

---

## What IBG Does NOT Do

| Capability | Status | Reason |
|------------|--------|--------|
| Image processing | NEVER | Works on DXF geometry only |
| Strategy caching (Loop 2) | NEVER | Not a learning system |
| ML classification | NEVER | Uses deterministic lutherie math |
| Photo input | NEVER | Requires vectorizer preprocessing |

---

## Math Authority

IBG math is LOCKED. Source references:

- **Jon Sevy** — "Calculating Arc Parameters," American Lutherie #58
- **R. Mottola** — "Calculating Side Contours," American Lutherie #78

Verification: ±0.01 inch tolerance against published spreadsheet values.

---

## Position in Pipeline

```
Blueprint Reader (upstream)
  → Partial DXF
  → IBG (this system)
  → Solved Body Model
  → CAM pipeline (downstream)
```

IBG is a **one-way consumer** of vectorizer output. No feedback loop exists upstream.

---

## Protected Interfaces

| Interface | Protection |
|-----------|------------|
| `SolvedBodyModel` schema | LOCKED |
| `BodyContourSolver` math | LOCKED |
| API response contract | LOCKED |
| DXF layer naming | LOCKED |

---

## Governance Authority

Changes to IBG core math require:
1. Published lutherie reference
2. Verification against known instruments
3. Regression test passage
4. Explicit approval

---

*IBG role definition. No learning systems. No image processing.*
