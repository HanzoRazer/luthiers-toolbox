# Morphology Harvest — Semantic Evidence Coordination Layer

**Sprint:** IBG Semantic Morphology Harvest Pass 1A  
**Status:** Production  
**Governance:** [MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md](../../../../../../../docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md)

---

## Purpose

The Morphology Harvest module is a **thin coordination layer** that:

- Inventories the instrument corpus
- Preserves semantic morphology evidence
- Normalizes terminology per governance audit
- Coordinates existing extraction authorities
- Generates human-reviewable morphology records

---

## What This Module Is NOT

This module does NOT:

- Extract dimensions (delegates to Phase 4)
- Detect scale (delegates to calibration)
- Classify morphology directly (delegates to body_grid)
- Own ontology authority
- Implement adaptive/LLM behavior
- Duplicate any existing extraction logic

---

## Architecture

```
morphology_harvest/
├── __init__.py           # Public API
├── schema.py             # HarvestRecord, terminology normalization
├── evidence_categories.py # BodyData, NeckPocketData, etc.
├── pdf_inventory.py      # Corpus scanner, manifest generation
├── adapters.py           # Stubbed Phase 4/calibration adapters
├── harvest_coordinator.py # Thin orchestration layer
├── overlay_wrapper.py    # Human review overlay generation
├── review_manifest.py    # Record tracking and index
├── outputs/              # Generated outputs (gitignored)
└── README.md
```

---

## Usage

### Scan Corpus

```python
from app.instrument_geometry.body.ibg.morphology_harvest import (
    PDFInventoryScanner,
    scan_corpus,
)

# Quick scan
corpus = scan_corpus("Guitar Plans/", max_files=50)
print(f"Found {corpus.total_pdfs} PDFs")
print(f"With dimensions: {corpus.with_dimensions}")
print(f"Suggested representatives: {corpus.suggested_representatives}")

# Save manifest
corpus.save("outputs/manifest.json")
```

### Harvest from PDF

```python
from app.instrument_geometry.body.ibg.morphology_harvest import (
    HarvestCoordinator,
)

coordinator = HarvestCoordinator()

# Check available systems
print(coordinator.check_systems())
# {
#   "phase4": {"available": false, "reason": "not_wired_in_1A"},
#   "calibration": {"available": false, "reason": "not_wired_in_1A"},
#   "body_grid": {"available": true}
# }

# Harvest
result = coordinator.harvest_from_pdf("plans/dreadnought.pdf")

if result.success:
    record = result.record
    print(f"Body length: {record.body_data.body_length_mm}")
    print(f"Morphology: {record.body_data.morphology_class}")
```

### Manage Records

```python
from app.instrument_geometry.body.ibg.morphology_harvest import (
    ManifestManager,
)

manager = ManifestManager("outputs/")

# Save record with overlay
manager.save_record(record, generate_overlay=True)

# Get statistics
stats = manager.get_statistics()
print(f"Total records: {stats['total_records']}")
print(f"Pending review: {stats['pending_review']}")

# Export report
manager.export_report("outputs/report.md")
```

### CLI Tools

```bash
# Scan corpus
python -m app.instrument_geometry.body.ibg.morphology_harvest.pdf_inventory \
    --corpus-root "Guitar Plans/" \
    --output manifest.json

# Harvest from PDF
python -m app.instrument_geometry.body.ibg.morphology_harvest.harvest_coordinator \
    plans/dreadnought.pdf \
    --output record.json

# Check systems
python -m app.instrument_geometry.body.ibg.morphology_harvest.harvest_coordinator \
    --check-systems
```

---

## Governance Compliance

### Authority Reuse

| Authority | Owner | Harvest Role |
|-----------|-------|--------------|
| Body zones | `body_grid.ZoneId` | Consumer |
| Morphology classes | `BodyMorphologyClass` | Consumer |
| Dimension association | Phase 4 | Caller (stubbed in 1A) |
| Scale/calibration | Calibration pipeline | Caller (stubbed in 1A) |
| Centerline semantics | Body Grid | Consumer |
| BodyEvidence schema | IBG | Producer (via conversion) |

### Terminology Normalization

```python
TERM_NORMALIZATIONS = {
    "lower_bout_mm": "lower_bout_width_mm",
    "upper_bout_mm": "upper_bout_width_mm",
    "waist_mm": "waist_width_mm",
    "body_width_mm": "lower_bout_width_mm",
}
```

### Forbidden Actions

- Creating new body zone names
- Creating parallel morphology enums
- Duplicating dimension parsing from Phase 4
- Creating competing coordinate systems
- Implementing autonomous reconstruction
- Implementing adaptive/LLM behavior

---

## Evidence Categories

| Category | Description |
|----------|-------------|
| `BodyData` | Body dimensions and morphology |
| `NeckPocketData` | Neck pocket dimensions |
| `NeckSystemData` | Scale length, nut width, profile |
| `FretboardData` | Radius, fret count, material |
| `HeadstockData` | Style, angle, dimensions |
| `HardwareCavityData` | Pickups, cavities, bridge |
| `AlignmentData` | Centerline, symmetry |
| `ConstructionNotes` | Free-form text observations |

Each category supports:

- `observed` — Was this data observed?
- `confidence` — 0.0-1.0 confidence score
- `source_type` — Where did this come from?
- `source_authority` — Which system owns this?
- `requires_review` — Needs human verification?

---

## Output Structure

```
outputs/
├── manifest.json         # Corpus index
├── records/
│   ├── harvest_abc123.json
│   └── harvest_def456.json
└── overlays/
    ├── harvest_abc123.png
    └── harvest_def456.png
```

Generated outputs are gitignored. Only schemas, sample fixtures, and documentation are committed.

---

## Storage Authority Warning

**IMPORTANT:** `morphology_harvest/outputs/` is **NOT canonical storage**.

It is a **temporary/generated staging area** for 1A harvest outputs only.

Harvested records represent reusable instrument-building knowledge that may support:

- IBG reconstruction
- Body Grid morphology
- Neck/fretboard/headstock systems
- Cavity and hardware layout
- CAD generation
- Validation pipelines
- Future adaptive sandboxes
- Downstream instrument-building workflows

### Canonical Storage Candidates

The repository has existing data authorities that may be the correct promotion target:

| Authority | Path | Purpose |
|-----------|------|---------|
| data_registry | `app/data_registry/` | Three-tier hybrid registry (system/curated/user) |
| body_templates | `data_registry/system/instruments/body_templates.json` | Standard body templates |
| instrument_specs | `app/instrument_geometry/instrument_specs.py` | Canonical body dimensions |

### Promotion Rules

```
HarvestRecord is a preservation/coordination artifact.
Canonical promotion target must be resolved before harvested
records are used as shared instrument-building data.
```

Until governance explicitly assigns canonical storage authority:

1. `morphology_harvest/outputs/` remains **non-canonical staging**
2. Harvested records should **not** be treated as authoritative instrument data
3. Promotion to `data_registry` or `instrument_specs` requires governance approval

See: `docs/governance/MORPHOLOGY_HARVEST_STORAGE_AUTHORITY.md` (pending)

---

## Integration Path

### BodyEvidence Conversion

```python
# HarvestRecord -> BodyEvidence (approved integration path)
body_evidence = record.to_body_evidence()

# Then use with Body Grid
from ..body_grid.morphology_descriptor import MorphologyAnalyzer
analyzer = MorphologyAnalyzer()
descriptor = analyzer.analyze(body_evidence)
```

### Future 1B Integration

Phase 4 and calibration adapters are stubbed in 1A. Actual wiring deferred to 1B:

```python
# 1A status
phase4.check_availability()
# AdapterResult(available=False, reason="not_wired_in_1A")

# Future 1B: actual wiring
# from services.blueprint_import.phase4.pipeline import BlueprintPipeline
```

---

## References

- [Governance Audit](../../../../../../../docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md)
- [Dev Order 0B](../../../../../../../docs/dev-orders/IBG_SEMANTIC_MORPHOLOGY_HARVEST_PASS_0B.md)
- [Body Grid](../body_grid/README.md)
- [IBG/BOE Boundary](../../../../../../../docs/architecture/IBG_BOE_BOUNDARY_MODEL.md)
