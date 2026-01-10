# Viewer Pack v1 Validation Gate

## Overview

This gate ensures cross-repo compatibility between:
- **tap_tone_pi** (producer): Exports `viewer_pack_v1` bundles from Phase 2 sessions
- **ToolBox** (consumer): Ingests and renders `viewer_pack_v1` bundles

**Contract**: "If a pack exports, it validates; if it validates, ToolBox can render it."

---

## Gate Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        tap_tone_pi (Producer)                       │
├─────────────────────────────────────────────────────────────────────┤
│  contracts/viewer_pack_v1.schema.json    ← SOURCE OF TRUTH         │
│  scripts/phase2/export_viewer_pack_v1.py ← Exporter CLI             │
│  scripts/phase2/validate_viewer_pack_v1.py ← Validator CLI          │
│  tests/test_viewer_pack_v1_gate.py       ← Producer gate test       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Schema vendored to ToolBox
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          ToolBox (Consumer)                         │
├─────────────────────────────────────────────────────────────────────┤
│  contracts/viewer_pack_v1.schema.json    ← VENDORED COPY            │
│  scripts/validate/validate_viewer_pack_v1.py ← Vendored validator   │
│  scripts/validate/check_viewer_pack_schema_parity.py ← Parity check │
│  packages/client/src/evidence/validate.ts ← TS validation + integrity│
│  services/api/tests/test_viewer_pack_v1_ingestion_gate.py ← Consumer gate │
│  services/api/tests/fixtures/viewer_packs/session_minimal.zip ← Fixture │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What the Gate Validates

### Must Check (Normative)

1. **Manifest schema shape**
   - Required keys: `schema_version`, `schema_id`, `created_at_utc`, `source_capdir`, `detected_phase`, `measurement_only`, `interpretation`, `points`, `contents`, `files`, `bundle_sha256`
   - Const fields: `schema_version == "v1"`, `schema_id == "viewer_pack_v1"`
   - `additionalProperties: false` (no unexpected keys)

2. **File inventory integrity**
   - Every `files[].relpath` exists in pack
   - Every `files[].bytes` matches actual file size
   - Every `files[].sha256` matches actual file hash

3. **Bundle integrity**
   - `bundle_sha256` matches SHA256 of canonical manifest JSON (before adding `bundle_sha256`)

4. **Minimal semantic sanity**
   - `points[]` is non-empty
   - `contents` booleans match file presence

### Must NOT Check (Stability)

- Audio WAV format correctness
- PNG image decodability
- CSV semantic correctness
- DSP math correctness
- "Analysis is internally valid"

---

## CI Configuration

### tap_tone_pi CI

Add to `.github/workflows/tests.yml`:

```yaml
viewer-pack-gate:
  name: Viewer Pack v1 Gate
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: pip install pytest

    - name: Run viewer pack gate
      run: pytest tests/test_viewer_pack_v1_gate.py -v
```

### ToolBox CI

Add to `.github/workflows/api-tests.yml`:

```yaml
viewer-pack-ingestion-gate:
  name: Viewer Pack v1 Ingestion Gate
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd services/api
        pip install pytest

    - name: Run schema parity check
      run: python scripts/validate/check_viewer_pack_schema_parity.py --mode check

    - name: Run ingestion gate
      run: |
        cd services/api
        pytest tests/test_viewer_pack_v1_ingestion_gate.py -v
```

---

## Exit Codes

### validate_viewer_pack_v1.py

| Code | Meaning |
|------|---------|
| 0 | PASS - All validations succeeded |
| 2 | FAIL - Validation mismatch (schema, hash, file) |
| 3 | ERROR - Runtime error (IO, parse, missing file) |

### check_viewer_pack_schema_parity.py

| Code | Meaning |
|------|---------|
| 0 | PARITY OK |
| 1 | PARITY MISMATCH |
| 2 | ERROR |

---

## Updating the Schema

When the schema changes in tap_tone_pi:

1. **Update tap_tone_pi schema**
   ```bash
   # In tap_tone_pi
   vim contracts/viewer_pack_v1.schema.json
   pytest tests/test_viewer_pack_v1_gate.py -v
   ```

2. **Update ToolBox vendored copy**
   ```bash
   # Copy schema (remove _vendored_* metadata if present, then re-add)
   cp /path/to/tap_tone_pi/contracts/viewer_pack_v1.schema.json \
      contracts/viewer_pack_v1.schema.json

   # Get new hash
   python scripts/validate/check_viewer_pack_schema_parity.py --mode print

   # Update PINNED_SCHEMA_HASH in check_viewer_pack_schema_parity.py

   # Regenerate fixture if needed
   python scripts/validate/generate_minimal_viewer_pack_fixture.py \
      --output services/api/tests/fixtures/viewer_packs/session_minimal.zip
   ```

3. **Verify both gates pass**
   ```bash
   # ToolBox
   python scripts/validate/check_viewer_pack_schema_parity.py --mode check
   cd services/api && pytest tests/test_viewer_pack_v1_ingestion_gate.py -v
   ```

---

## Kind Vocabulary

The schema defines a strict enum for `files[].kind`:

| Kind | Description |
|------|-------------|
| `audio_raw` | Raw audio WAV file |
| `spectrum_csv` | Frequency spectrum CSV |
| `analysis_peaks` | Peak analysis JSON |
| `coherence` | Coherence data |
| `transfer_function` | Transfer function JSON |
| `wolf_candidates` | Wolf tone candidates JSON |
| `wsi_curve` | WSI curve data |
| `provenance` | Provenance/metadata JSON |
| `plot_png` | Plot image PNG |
| `session_meta` | Session metadata JSON |
| `manifest` | Manifest file itself |
| `unknown` | Fallback for unrecognized |

**Policy**: Soft (unknown kinds allowed, ToolBox falls back to `UnknownRenderer`)

---

## Fixture Management

### Generating Fixtures

```bash
# From ToolBox repo
python scripts/validate/generate_minimal_viewer_pack_fixture.py \
    --output services/api/tests/fixtures/viewer_packs/session_minimal.zip
```

### Validating Fixtures

```bash
python scripts/validate/validate_viewer_pack_v1.py \
    --pack services/api/tests/fixtures/viewer_packs/session_minimal.zip
```

---

## Troubleshooting

### "Schema hash mismatch"

The vendored schema differs from the pinned hash.

1. Check if schema was updated in tap_tone_pi
2. If intentional: update `PINNED_SCHEMA_HASH` in `check_viewer_pack_schema_parity.py`
3. If accidental: restore schema from tap_tone_pi

### "bundle_sha256 mismatch"

The manifest's `bundle_sha256` doesn't match computed hash.

1. Ensure exporter uses: `json.dumps(manifest, indent=2, sort_keys=True)`
2. Ensure hash is computed BEFORE adding `bundle_sha256` to manifest

### "missing file in pack"

A file listed in manifest doesn't exist in the pack.

1. Check if file was accidentally excluded during export
2. Verify file paths use forward slashes (not backslashes)

---

## File Locations Summary

### tap_tone_pi
| File | Purpose |
|------|---------|
| `contracts/viewer_pack_v1.schema.json` | Canonical schema (source of truth) |
| `scripts/phase2/validate_viewer_pack_v1.py` | Validator CLI |
| `scripts/phase2/export_viewer_pack_v1.py` | Exporter CLI |
| `tests/test_viewer_pack_v1_gate.py` | Producer gate test |
| `fixtures/sessions/` | Fixture sessions for CI |

### ToolBox
| File | Purpose |
|------|---------|
| `contracts/viewer_pack_v1.schema.json` | Vendored schema |
| `scripts/validate/validate_viewer_pack_v1.py` | Vendored validator |
| `scripts/validate/check_viewer_pack_schema_parity.py` | Parity checker |
| `scripts/validate/generate_minimal_viewer_pack_fixture.py` | Fixture generator |
| `packages/client/src/evidence/validate.ts` | TS validation + integrity |
| `services/api/tests/test_viewer_pack_v1_ingestion_gate.py` | Consumer gate test |
| `services/api/tests/fixtures/viewer_packs/session_minimal.zip` | Fixture zip |
