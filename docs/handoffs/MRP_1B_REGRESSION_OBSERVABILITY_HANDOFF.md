# MRP-1B: Regression & Behavioral Observability Infrastructure Handoff

**Date:** 2026-05-11  
**Status:** COMPLETE  
**Sprint:** MRP-1B  
**Domain:** Morphology Reconstruction Platform

---

## Summary

MRP-1B creates the observability framework for comparing protected Blueprint Reader outputs against baselines. The infrastructure is ready; reference artifacts remain declared but unpopulated.

---

## Deliverables

| Deliverable | Status | Location |
|-------------|--------|----------|
| Regression signature schema | COMPLETE | `app/regression/signature_schema.py` |
| Blueprint Reader output signature | COMPLETE | `app/regression/blueprint_signature.py` |
| Basic DXF summary comparator | COMPLETE | `app/regression/dxf_comparator.py` |
| Invariant definitions | COMPLETE | `app/regression/invariants.py` |
| Baseline comparison harness | COMPLETE | `app/regression/comparison_harness.py` |
| Local pytest coverage | COMPLETE | `tests/regression/` (40 tests) |
| Handoff document | COMPLETE | This file |

---

## Infrastructure Components

### 1. Regression Signature Schema

Base schema for capturing output characteristics:

```python
@dataclass
class RegressionSignature:
    artifact_id: str
    system_id: str
    dimensions: Dict[str, float]  # Dimensional measurements
    counts: Dict[str, int]        # Entity/element counts
    flags: Dict[str, bool]        # Boolean characteristics
```

### 2. Blueprint Reader Output Signature

Specialized signature for Blueprint Reader:

```python
@dataclass
class BlueprintOutputSignature(RegressionSignature):
    body_width_mm: float
    body_height_mm: float
    dxf_entity_count: int
    dxf_closed_contours: int
    selection_score: float
    recommendation_action: str
    # ... (12 additional fields)
```

### 3. DXF Summary Comparator

Basic dimensional comparison of DXF outputs:

```python
@dataclass
class DXFSummary:
    width: float
    height: float
    entity_counts: Dict[str, int]
    layers: List[str]
    has_closed_paths: bool
```

Comparison detects:
- Dimensional drift (width, height)
- Entity count changes
- Layer additions/removals
- Structural changes (closed vs open paths)

### 4. Invariants (9 defined for Blueprint Reader)

| ID | Description | Severity |
|----|-------------|----------|
| BR_INV_001 | Body dimensions must be positive | CRITICAL |
| BR_INV_002 | Body dimensions must be plausible (100-700mm) | WARNING |
| BR_INV_003 | Body aspect ratio must be plausible (0.8-2.5) | WARNING |
| BR_INV_004 | DXF output must not be empty | CRITICAL |
| BR_INV_005 | DXF entity count must be reasonable (10-100000) | WARNING |
| BR_INV_006 | DXF should have closed contours | WARNING |
| BR_INV_007 | Selection index must be valid | CRITICAL |
| BR_INV_008 | Confidence values must be bounded [0, 1] | CRITICAL |
| BR_INV_009 | Accepted results must have artifacts | CRITICAL |

### 5. Baseline Comparison Harness

```python
# Save a baseline
save_baseline(signature, baseline_dir=Path("tests/regression_corpus/baselines"))

# Load a baseline
baseline = load_baseline("artifact_id", "BLUEPRINT_READER_MVP", BlueprintOutputSignature)

# Compare current output to baseline
result = compare_to_baseline(current_signature)
```

Result includes:
- Comparison result (MATCH, DRIFT, REGRESSION, BASELINE_MISSING)
- Dimensional deltas and drift percentages
- Invariant check results
- Blocking issues and warnings

---

## Test Coverage

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_signature_schema.py` | 10 | Base schema serialization |
| `test_blueprint_signature.py` | 9 | Blueprint-specific signature |
| `test_invariants.py` | 12 | Invariant check logic |
| `test_comparison_harness.py` | 9 | Baseline save/load/compare |
| **Total** | **40** | All passing |

---

## File Structure

```
services/api/app/regression/
├── __init__.py               # Package exports
├── signature_schema.py       # Base signature schema
├── blueprint_signature.py    # Blueprint Reader signature
├── dxf_comparator.py         # DXF summary comparison
├── invariants.py             # Invariant definitions
└── comparison_harness.py     # Baseline utilities

services/api/tests/regression/
├── __init__.py
├── test_signature_schema.py
├── test_blueprint_signature.py
├── test_invariants.py
└── test_comparison_harness.py

tests/regression_corpus/
├── manifest.json             # Updated to v1.1.0
└── baselines/
    └── blueprint_reader_mvp/ # Baseline storage (empty)
```

---

## Usage Example

```python
from app.regression import (
    extract_blueprint_signature,
    compare_to_baseline,
    save_baseline,
)

# After Blueprint Reader run
result_dict = orchestrator.process_file(...).to_response_dict()

# Extract signature
signature = extract_blueprint_signature(
    result_dict,
    artifact_id="dreadnought_test_001",
    input_bytes=pdf_bytes,
)

# Compare to baseline (if exists)
comparison = compare_to_baseline(signature)

if comparison.has_critical_failures:
    raise RegressionError(comparison.blocking_issues)

if comparison.drift_detected:
    log.warning(f"Drift detected: {comparison.warnings}")

# Save as new baseline (manual operation)
# save_baseline(signature, overwrite=True)
```

---

## What Was NOT Implemented

| Capability | Status | Reason |
|------------|--------|--------|
| Reference artifact population | NOT DONE | Per scope |
| GitHub Actions integration | NOT DONE | Per scope |
| Visual diffing | NOT DONE | Per scope |
| Full semantic DXF differ | NOT DONE | Per scope |
| IBG/CAM observability | NOT DONE | Blueprint Reader first |

---

## Manifest Update

`tests/regression_corpus/manifest.json` updated to v1.1.0:

```json
{
  "manifest_version": "1.1.0",
  "status": "INFRASTRUCTURE_READY",
  "infrastructure": {
    "signature_schema": "services/api/app/regression/signature_schema.py",
    "baselines_dir": "tests/regression_corpus/baselines/"
  },
  "invariant_definitions": {
    "BLUEPRINT_READER_MVP": 9
  }
}
```

---

## Definition of Done

MRP-1B is complete:

- [x] Regression signature schema created
- [x] Blueprint Reader output signature model created
- [x] Basic DXF summary comparator created
- [x] 9 invariants defined for Blueprint Reader
- [x] Baseline comparison harness created
- [x] 40 pytest tests passing
- [x] Manifest updated to INFRASTRUCTURE_READY
- [x] Handoff document created

---

## Next Recommended Phase

### MRP-1C: Reference Artifact Population

Populate the declared reference artifacts:
- MELODY_MAKER_PDF
- DREADNOUGHT_REFERENCE
- CUATRO_REFERENCE
- LES_PAUL_REFERENCE

### MRP-2A: CI Integration

Wire observability to GitHub Actions:
- Run invariant checks on PR
- Compare against baselines
- Block on regressions

---

*MRP-1B complete. Observability infrastructure ready for baseline population.*
