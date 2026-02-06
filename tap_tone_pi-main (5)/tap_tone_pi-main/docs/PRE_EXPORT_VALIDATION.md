# Pre-Export Validation — viewer_pack_v1

> **Status:** Normative. Exporters MUST pass validation before ZIP creation.
> **Module:** `tap_tone/validate/viewer_pack_v1.py`

This document defines the validation rules enforced before creating a viewer pack ZIP.

---

## Validation Flow

```
Staged Pack Directory
        ↓
    Validator
        ↓
  validation_report.json
        ↓
    [PASS] → Create ZIP
    [FAIL] → Abort with errors
```

---

## Rule Table

| Rule ID | Severity | Description | File/Column |
|---------|----------|-------------|-------------|
| **M-001** | ERROR | Manifest exists at root | `viewer_pack.json` |
| **M-002** | ERROR | Schema identity correct | `schema_id`, `schema_version` |
| **M-003** | ERROR | Points list non-empty | `manifest.points[]` |
| **S-001** | ERROR | Spectrum file exists for each point | `spectra/points/{PID}/spectrum.csv` |
| **S-002** | ERROR | Required columns present | `freq_hz`, `H_mag` |
| **S-003** | ERROR | Frequency monotonically increasing | `freq_hz` column |
| **S-004** | ERROR | No duplicate frequencies | `freq_hz` column |
| **S-005** | ERROR | Magnitudes finite | `H_mag` column |
| **S-006** | ERROR | Shared frequency grid | All `spectrum.csv` files |
| **P-001** | ERROR | Analysis file exists for each point | `spectra/points/{PID}/analysis.json` |
| **P-002** | ERROR | Peaks JSON parseable | `analysis.json` structure |
| **P-003** | ERROR | Peak frequencies in grid | `peaks[].freq_hz` matches bins |
| **W-001** | ERROR | WSI has required columns | `wolf/wsi_curve.csv` |
| **W-002** | ERROR | WSI admissible values valid | `admissible` = `"true"` or `"false"` |
| **W-003** | ERROR | WSI frequencies match grid | `wolf/wsi_curve.csv` `freq_hz` |
| **A-001** | WARN | Audio file exists for each point | `audio/points/{PID}.wav` |
| **O-001** | WARN | Optional JSON files parseable | `coherence/`, `meta/`, `provenance.json` |

---

## Rule Details

### M-001: Manifest Existence
```
CHECK: viewer_pack.json exists at pack root
FAIL:  "Manifest viewer_pack.json not found at pack root"
```

### M-002: Schema Identity
```
CHECK: manifest.schema_id == "viewer_pack_v1"
       AND manifest.schema_version == "v1"
FAIL:  "Schema identity mismatch: expected viewer_pack_v1/v1, got {id}/{version}"
```

### M-003: Points List
```
CHECK: manifest.points is non-empty list of strings
FAIL:  "Points list empty or missing"
```

### S-001: Spectrum Existence
```
FOR each PID in manifest.points:
  CHECK: spectra/points/{PID}/spectrum.csv exists
  FAIL:  "Spectrum missing for point {PID}"
```

### S-002: Required Columns
```
CHECK: CSV has columns "freq_hz" and "H_mag"
FAIL:  "Spectrum {PID} missing required column: {column}"
```

### S-003: Frequency Monotonicity
```
CHECK: freq_hz[i] < freq_hz[i+1] for all i
FAIL:  "Spectrum {PID}: freq_hz not strictly increasing at row {row}"
```

### S-004: No Duplicate Frequencies
```
CHECK: len(set(freq_hz)) == len(freq_hz)
FAIL:  "Spectrum {PID}: duplicate freq_hz value {value}"
```

### S-005: Finite Magnitudes
```
CHECK: all H_mag values are finite (not NaN, not Inf)
FAIL:  "Spectrum {PID}: non-finite H_mag at row {row}"
```

### S-006: Shared Frequency Grid
```
CHECK: All spectrum.csv files have identical freq_hz arrays
FAIL:  "Frequency grid mismatch: {PID1} has {n1} bins, {PID2} has {n2} bins"
       OR "Frequency mismatch at bin {i}: {PID1}={f1}, {PID2}={f2}"
```

### P-001: Analysis Existence
```
FOR each PID in manifest.points:
  CHECK: spectra/points/{PID}/analysis.json exists
  FAIL:  "Analysis missing for point {PID}"
```

### P-002: Peaks Structure
```
CHECK: analysis.json parses as {"peaks": [{"freq_hz": number, ...}, ...]}
FAIL:  "Analysis {PID}: invalid JSON or missing peaks array"
```

### P-003: Peaks Grid Alignment
```
FOR each peak in analysis.peaks:
  CHECK: peak.freq_hz exists in shared frequency grid (exact or within tolerance)
  FAIL:  "Peak {PID}@{freq_hz}Hz not in frequency grid (nearest: {nearest}Hz)"
```

### W-001: WSI Columns
```
IF wolf/wsi_curve.csv exists:
  CHECK: has columns: freq_hz, wsi, loc, grad, phase_disorder, coh_mean, admissible
  FAIL:  "WSI curve missing required column: {column}"
```

### W-002: Admissible Values
```
CHECK: admissible column contains only "true" or "false" (lowercase strings)
FAIL:  "WSI curve: invalid admissible value '{value}' at row {row}"
```

### W-003: WSI Frequency Alignment
```
CHECK: WSI freq_hz array == shared spectrum frequency grid
FAIL:  "WSI frequency grid mismatch: {n_wsi} bins vs {n_spectrum} spectrum bins"
```

### A-001: Audio Existence
```
FOR each PID in manifest.points:
  CHECK: audio/points/{PID}.wav exists
  WARN:  "Audio missing for point {PID}"
```

### O-001: Optional Files
```
FOR each optional JSON file (coherence_summary.json, session_meta.json, provenance.json):
  IF file exists:
    CHECK: parses as valid JSON
    WARN:  "Optional file {path} is not valid JSON"
```

---

## Validation Report Format

```json
{
  "schema_id": "validation_report_v1",
  "validated_at_utc": "2026-01-17T12:00:00Z",
  "pack_path": "path/to/staged_pack",
  "passed": false,
  "errors": [
    {"rule": "S-001", "message": "Spectrum missing for point A3", "path": "spectra/points/A3/spectrum.csv"}
  ],
  "warnings": [
    {"rule": "A-001", "message": "Audio missing for point B2", "path": "audio/points/B2.wav"}
  ],
  "stats": {
    "points_checked": 35,
    "spectra_valid": 34,
    "peaks_aligned": 34,
    "audio_present": 33
  }
}
```

---

## CLI Usage

```bash
# Validate a staged pack directory
python -m tap_tone.validate.viewer_pack_v1 path/to/staged_pack

# Export with validation (default: validation required)
python scripts/phase2/export_viewer_pack_v1.py --session runs_phase2/session_001 --out pack.zip

# Export with validation report output
python scripts/phase2/export_viewer_pack_v1.py --session runs_phase2/session_001 --out pack.zip --report validation_report.json

# Skip validation (NOT RECOMMENDED)
python scripts/phase2/export_viewer_pack_v1.py --session runs_phase2/session_001 --out pack.zip --no-validate
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation passed (no errors) |
| 2 | Validation failed (errors found) |
| 3 | Validator internal failure |

---

## Configuration

### Peak Alignment Tolerance

By default, peaks must match frequency bins exactly. To allow tolerance:

```python
# In validator call
validate_pack(path, peak_tolerance_hz=0.5)
```

This is recorded in the validation report for auditability.

### Audio Omission Policy

Audio files are WARN-level by default. To make them ERROR:

```python
validate_pack(path, audio_required=True)
```

---

## References

- [FAILURE_MODES_VIEWER.md](FAILURE_MODES_VIEWER.md) — Symptom→rule mapping
- [EVIDENCE_PACK_CONTRACT_v1.md](contracts/EVIDENCE_PACK_CONTRACT_v1.md) — Full column specs
- [viewer_pack_v1.schema.json](../contracts/viewer_pack_v1.schema.json) — JSON Schema
