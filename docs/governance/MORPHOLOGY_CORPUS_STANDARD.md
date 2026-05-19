# Morphology Corpus Standard

**Status:** ACTIVE GOVERNANCE  
**Effective:** 2026-05-11

---

## Purpose

Define standards for the corpus of instrument morphology data used by IBG and future morphology intelligence systems.

---

## Corpus Structure

```
morphology_corpus/
├── specs/                    # Instrument specifications
│   ├── dreadnought.json
│   ├── jumbo.json
│   ├── cuatro_venezolano.json
│   └── stratocaster.json
├── reference_outlines/       # Verified DXF outlines
│   └── {spec_name}_reference.dxf
├── validation_cases/         # Test cases with expected outputs
│   └── {spec_name}_validation.json
└── corrections/              # User correction history
    └── {session_id}_correction.json
```

---

## Specification Schema

```json
{
  "spec_name": "dreadnought",
  "family": "dreadnought",
  "body": {
    "length_mm": 520,
    "lower_bout_mm": 381,
    "upper_bout_mm": 241,
    "waist_mm": 254,
    "waist_y_norm": 0.45
  },
  "physical": {
    "back_radius_mm": 4572,
    "butt_depth_mm": 100,
    "shoulder_depth_mm": 95
  },
  "tolerances": {
    "dimension_pct": 10,
    "radius_pct": 15
  },
  "sources": {
    "primary": "Martin D-28 factory spec",
    "verified_date": "2026-04-16"
  }
}
```

---

## Data Quality Requirements

| Field | Requirement |
|-------|-------------|
| Dimensions | ±5% of published factory spec |
| Radii | ±10% of measured reference |
| Landmarks | Named per `LandmarkPoint` schema |
| Sources | Published reference required |

---

## Adding New Specifications

1. **Source requirement** — Published factory spec or measured reference instrument
2. **Verification** — `generate_from_defaults()` must produce ±10% of expected dimensions
3. **Test case** — Add to `test_body_solver_integration.py`
4. **Documentation** — Add to `INSTRUMENT_SPECS` dict with source citation

---

## Correction Handling

When user submits correction:

1. Store in `corrections/` with session ID
2. Do not auto-integrate into specs
3. Flag for manual review
4. Track correction frequency per spec

---

## Versioning

Corpus changes require:

1. Semantic version bump in `CORPUS_VERSION`
2. Migration script if schema changes
3. Regression test passage
4. Handoff documentation

---

*Morphology corpus standard. Data quality over quantity.*
