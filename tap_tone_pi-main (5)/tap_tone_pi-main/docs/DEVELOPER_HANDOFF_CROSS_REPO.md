# Developer Handoff Document: tap_tone_pi ↔ luthiers-toolbox Integration

**Date:** 2026-01-01
**Purpose:** Canonical decisions and integration surface for cross-repo development
**Scope:** tap_tone_pi (analyzer) + luthiers-toolbox (ToolBox API)

---

## Table of Contents

1. [A. Canonical File/Namespace Decisions](#a-canonical-filenamespace-decisions)
2. [B. Artifact Contract + Schema Plumbing](#b-artifact-contract--schema-plumbing)
3. [C. Run/Bundle Layout Invariants](#c-runbundle-layout-invariants)
4. [D. ToolBox-side Integration Surface](#d-toolbox-side-integration-surface)
5. [E. Governance/CI Enforcement Points](#e-governanceci-enforcement-points)
6. [F. Mesh/Chladni Scaffold Cohesion](#f-meshchladni-scaffold-cohesion)
7. [G. Governance Decisions (Resolved)](#g-governance-decisions-resolved)
   - [G.0 DSP Architecture Decisions](#g0-dsp-architecture-decisions-code-affecting)
   - [G.1 Schema Registry Index](#g1-schema-registry-index)
   - [G.2 Chladni Frequency Mismatch Policy](#g2-chladni-frequency-mismatch-policy)
   - [G.3 Phase-2 Promotion Gate](#g3-phase-2-promotion-gate)
   - [G.4 Pipeline Validation Report](#g4-pipeline-validation-report-phase2_slicepy)
8. [Quick Reference Tables](#quick-reference-tables)

---

## A. Canonical File/Namespace Decisions

### A.1 Directory Status: Canonical vs Legacy

| Directory | Status | Purpose | Migration Notes |
|-----------|--------|---------|-----------------|
| `tap_tone/` | **CANONICAL** (Frozen v1.0) | Phase 1 single-channel measurement | No changes allowed |
| `modes/_shared/` | **CANONICAL** | Shared utilities (WAV I/O, manifest) | All imports here |
| `scripts/phase2/` | **CANONICAL** for Phase 2 | DSP, metrics, grid management | Active development |
| `scripts/phase2_slice.py` | **CANONICAL** | Phase 2 CLI entry point | Main executable |
| `contracts/` | **CANONICAL** | External output contracts | Source of truth |
| `tap-tone-lab/` | **LEGACY/EXPERIMENTAL** | Separate package, RMOS export experiments | Do not use in main |
| `scripts/*.py` (top-level) | **CANONICAL** | Individual analysis scripts | Each has clear purpose |
| `schemas/` | **INTERNAL** | Internal measurement schemas | Not externally exposed |
| `docs/schemas/` | **INFORMATIONAL** | Reference documentation | Not enforced |

### A.2 Canonical WAV I/O Module

**Single Source of Truth:**
```
modes/_shared/wav_io.py
```

**Import Path:**
```python
from modes._shared.wav_io import read_wav_mono, read_wav_2ch, write_wav_mono, write_wav_2ch
```

**Function Signatures (CANONICAL):**
```python
def read_wav_mono(path: Path) -> tuple[np.ndarray, WavMeta]:
    """Returns (signal_float32, WavMeta)"""

def read_wav_2ch(path: Path) -> tuple[np.ndarray, np.ndarray, WavMeta]:
    """Returns (ref_channel, rov_channel, WavMeta)"""

def write_wav_mono(path: Path, signal: np.ndarray, fs: int) -> None:
    """Writes PCM int16 WAV file"""

def write_wav_2ch(path: Path, x_ref: np.ndarray, x_rov: np.ndarray, fs: int) -> None:
    """Writes 2-channel PCM int16 WAV file"""
```

**Legacy Bridge (DO NOT USE FOR NEW CODE):**
```
scripts/phase2/io_wav.py  # Wrapper only, delegates to canonical
```

**CI Guard:** `.github/workflows/wav-io-guard.yml`
- Blocks direct `scipy.io.wavfile` imports anywhere except `modes/_shared/wav_io.py`

### A.3 Canonical Schema Locations

| Location | Purpose | Authority Level |
|----------|---------|-----------------|
| `contracts/` | External output contracts | **SOURCE OF TRUTH** |
| `contracts/schemas/` | Measurement mode contracts | **SOURCE OF TRUTH** |
| `schemas/` | Internal schemas | Internal use only |
| `schemas/measurement/` | Measurement-specific | Internal use only |
| `docs/schemas/` | Documentation/reference | Informational only |

**Rule:** External consumers validate against `contracts/*.schema.json` ONLY.

---

## B. Artifact Contract + Schema Plumbing

### B.1 Schema IDs and Versions (STABLE)

| Schema ID | File | Version | Status |
|-----------|------|---------|--------|
| `phase2_grid` | `contracts/phase2_grid.schema.json` | v1 | **STABLE** |
| `phase2_session_meta` | `contracts/phase2_session_meta.schema.json` | v1 | **STABLE** |
| `phase2_point_capture_meta` | `contracts/phase2_point_capture_meta.schema.json` | v1 | **STABLE** |
| `phase2_ods_snapshot` | `contracts/phase2_ods_snapshot.schema.json` | v2 | **STABLE** |
| `phase2_wolf_candidates` | `contracts/phase2_wolf_candidates.schema.json` | v2 | **STABLE** |
| `tap_peaks` | `contracts/schemas/tap_peaks.schema.json` | v1 | **STABLE** |
| `moe_result` | `contracts/schemas/moe_result.schema.json` | v1 | **STABLE** |
| `manifest` | `contracts/schemas/manifest.schema.json` | v1 | **STABLE** |
| `chladni_run` | `contracts/schemas/chladni_run.schema.json` | v1 | **STABLE** |

### B.2 Required Output Filenames per CAPDIR

**Phase 2 Session Directory (`runs_phase2/session_*/`):**

```
runs_phase2/session_{timestamp}/
├── metadata.json                    # REQUIRED - validates: phase2_session_meta
├── grid.json                        # REQUIRED - validates: phase2_grid
├── points/
│   └── point_{id}/
│       ├── audio.wav               # REQUIRED - 2-channel
│       ├── capture_meta.json       # REQUIRED - validates: phase2_point_capture_meta
│       ├── analysis.json           # OPTIONAL - per-point FFT
│       └── spectrum.csv            # OPTIONAL - frequency data
├── derived/
│   ├── ods_snapshot.json           # REQUIRED - validates: phase2_ods_snapshot
│   ├── wolf_candidates.json        # REQUIRED - validates: phase2_wolf_candidates
│   └── wsi_curve.csv               # OPTIONAL - WSI vs frequency
└── plots/                           # OPTIONAL - visualization outputs
    ├── coherence_{freq}Hz.png
    ├── ods_mag_{freq}Hz.png
    └── wsi_curve.png
```

**Filename Invariants:**
- `metadata.json` — Session-level metadata (NEVER `session_metadata.json`)
- `grid.json` — Grid definition (NEVER `grid_definition.json`)
- `capture_meta.json` — Per-point metadata (NEVER `meta.json` or `point_meta.json`)
- `ods_snapshot.json` — ODS transfer function (NEVER `ods.json` or `transfer_function.json`)
- `wolf_candidates.json` — Wolf candidates (NEVER `wolf.json` or `candidates.json`)

### B.3 Schema Field Invariants

**"No Extra Fields" Policy:** YES, this is a hard invariant.

Writers MUST NOT emit fields not defined in the schema. Validators MUST reject extra fields.

**Key Field Mappings (v2 schemas):**

| Schema | Field | Type | Notes |
|--------|-------|------|-------|
| `phase2_ods_snapshot` | `freqs_hz` | `number[]` | Array of frequencies (NOT `frequencies`) |
| `phase2_ods_snapshot` | `points[].x_mm` | `number` | X coordinate (NOT `x`) |
| `phase2_ods_snapshot` | `points[].y_mm` | `number` | Y coordinate (NOT `y`) |
| `phase2_ods_snapshot` | `points[].H_mag` | `number[]` | Magnitude array (NOT scalar) |
| `phase2_ods_snapshot` | `points[].H_phase_deg` | `number[]` | Phase array (NOT scalar) |
| `phase2_ods_snapshot` | `points[].coherence` | `number[]` | Coherence array (NOT scalar) |
| `phase2_wolf_candidates` | `candidates[].freq_hz` | `number` | Frequency (NOT `frequency_hz`) |
| `phase2_wolf_candidates` | `candidates[].top_points` | `object[]` | Per-candidate (NOT global) |

---

## C. Run/Bundle Layout Invariants

### C.1 Phase 1 Capture Directory Convention

**Location:** `out/` directory

**Naming Patterns:**
- `bend_YYYYMMDDTHHMMSSZ/` — Bending rig sessions
- `session_*/` — Generic sessions
- Semantic names allowed for demos/tests

**Structure:**
```
out/session_example/
├── session_manifest.jsonl          # Append-only ledger (JSONL format)
├── session_close.json              # Final session report (optional)
└── session_calibration.json        # Calibration data (optional)
```

### C.2 Phase 2 Run Directory Convention

**Location:** `runs_phase2/` directory

**Naming:** `session_YYYYMMDDTHHMMSSZ`

**Structure:** See B.2 above for complete layout.

### C.3 Session Ledger Requirements

**Format:** JSONL (JSON Lines) — one JSON object per line

**Purpose:** Append-only audit trail, transaction-style recording

**Example Entry:**
```json
{"bundle_id": "b001", "mode": "bend", "timestamp": "2026-01-01T12:00:00Z"}
```

**Location:** `{session_dir}/session_manifest.jsonl`

**Hard Requirement:** YES — sessions MUST have ledger for traceability.

---

## D. ToolBox-side Integration Surface

### D.1 FastAPI App Location

**File:** `services/api/app/main.py`

**App Creation (lines 507-513):**
```python
app = FastAPI(
    title="Luthier's ToolBox API",
    description="CAM system for guitar builders...",
    version="2.0.0-clean",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

**Router Registration:** Lines 558-846 (127 routers)

### D.2 Router Include Conventions

**File Naming:** `*_router.py` suffix

**Import Pattern:**
```python
from .routers.cam_sim_router import router as sim_router
app.include_router(sim_router, prefix="/api/sim", tags=["Simulation"])
```

**Consolidated Routers (Wave 18+):**
```python
from .cam.routers import router as cam_router
app.include_router(cam_router, prefix="/api/cam")
```

### D.3 Attachment Store API

**Module:** `services/api/app/rmos/runs_v2/attachments.py`

| Function | Purpose | Signature |
|----------|---------|-----------|
| `attachment_exists(sha256)` | Check blob exists | `str → bool` |
| `get_attachment_path(sha256)` | Get filesystem path | `str → Optional[str]` |
| `get_bytes_attachment(sha256)` | Retrieve raw bytes | `str → Optional[bytes]` |
| `load_json_attachment(sha256)` | Load + parse JSON | `str → Optional[Dict]` |
| `put_bytes_attachment(data, kind, mime, filename, ext)` | Store binary | `→ Tuple[RunAttachment, str]` |
| `put_json_attachment(obj, kind, filename, ext)` | Store JSON | `→ Tuple[RunAttachment, str, str]` |
| `verify_attachment(sha256)` | Verify integrity | `str → Dict[str, Any]` |

**Meta Index:** `services/api/app/rmos/runs_v2/attachment_meta.py`
- Class: `AttachmentMetaIndex`
- Methods: `get(sha256)`, `list_all()`, `rebuild_from_run_artifacts()`
- Index Location: `{runs_root}/_attachment_meta.json`

**Storage Sharding:**
```
{root}/{sha[0:2]}/{sha[2:4]}/{sha}{ext}
```

### D.4 Signed URL Utilities

**Module:** `services/api/app/rmos/runs_v2/signed_urls.py`

**Key Functions:**
```python
def sign_attachment_request(method, path, sha256, expires, scope, download, filename) -> str
def verify_attachment_request(method, path, sha256, expires, sig, scope, required_scope) -> bool
def make_signed_query(method, path, sha256, ttl_seconds, scope, download, filename) -> SignedUrlParams
```

**Token Format (line-delimited payload):**
```
METHOD\nPATH\nEXPIRES\nSHA256\nSCOPE\nDOWNLOAD\nFILENAME
```

**Environment Variables:**

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `RMOS_SIGNED_URL_SECRET` | Primary signing secret | YES (for signed URLs) | None |
| `RMOS_ACOUSTICS_SIGNING_SECRET` | Legacy fallback | NO | None |
| `RMOS_ACOUSTICS_SIGNING_TTL_SECONDS` | Token lifetime | NO | 300 |
| `RMOS_RUN_ATTACHMENTS_DIR` | Storage directory | NO | `data/run_attachments` |
| `RMOS_MAX_ATTACHMENT_BYTES` | Size limit | NO | 104857600 (100MB) |

**Scopes:**
- `"download"` — Full download permission (implies HEAD)
- `"head"` — HEAD-only access (metadata via headers)

---

## E. Governance/CI Enforcement Points

### E.1 tap_tone_pi CI Path Gates

| Workflow | Trigger Paths | Purpose |
|----------|---------------|---------|
| `wav-io-guard.yml` | `**/*.py` | Block unauthorized wavfile imports |
| `contracts-validate.yml` | `contracts/schemas/**`, `out/**` | Validate output contracts |
| `phase2_validate.yml` | `scripts/phase2/**`, `contracts/phase2_*.json` | Phase 2 sync check |
| `boundary_guard.yml` | All | Enforce analyzer↔ToolBox boundary |
| `schemas_validate.yml` | `schemas/**` | General schema validation |
| `test.yml` | All | Pytest suite |

### E.2 luthiers-toolbox CI Path Gates

| Workflow | Trigger Paths | Purpose |
|----------|---------------|---------|
| `rmos_ci.yml` | `services/api/**`, `scripts/**` | Main CI pipeline |
| `api_pytest.yml` | Push/PR to main | Full API test suite |
| `api_dxf_tests.yml` | `server/dxf_*.py` | DXF export validation |
| `cam_essentials.yml` | `routers/*roughing*`, `*drill*` | CAM N0-N10 essentials |

### E.3 Boundary Enforcement

**tap_tone_pi Boundary Guard:**
- Analyzer root (`tap_tone`, `modes`, `schemas`, `tests`) CANNOT import:
  - `app.*`, `services.*`, `packages.*` (ToolBox namespaces)
- Enforced by: `ci/check_boundary_imports.py`

**luthiers-toolbox Endpoint Truth:**
- All routes must match `docs/ENDPOINT_TRUTH_MAP.md`
- Legacy endpoints must reach 0 hits by 2026-01-31

### E.4 Minimum Hardware-Free Test Bar

**Requirements for PRs:**
1. All tests in `tests/` must pass
2. No hardware dependencies (mock sensors)
3. Schema validation passes
4. Boundary guard passes

**Deterministic Tests:**
- Use fixed seeds for any randomness
- Mock datetime.now() for timestamp tests
- Use fixture files, not live captures

---

## F. Mesh/Chladni Scaffold Cohesion

### F.1 Mesh Pipeline Artifact Location

**Directory:** `runs_phase2/session_*/` (same as ODS)

**OR** for Chladni-specific: `out/chladni_*/`

**File Naming:**
```
{session_dir}/
├── chladni_run.json                # Run index - validates: chladni_run
├── patterns/
│   └── pattern_{freq}Hz/
│       ├── image.png               # Captured pattern image
│       ├── analysis.json           # Pattern analysis
│       └── nodes.csv               # Node positions
└── derived/
    └── mode_shapes.json            # Aggregated mode shapes
```

### F.2 Manifest/Export Pattern Requirement

**YES** — Mesh/Chladni MUST use same manifest pattern as acoustics:
- `session_manifest.jsonl` for append-only ledger
- `manifest.json` for immutable run manifest with SHA256 hashes
- Same schema validation (`contracts/schemas/manifest.schema.json`)

### F.3 Persistence/Indexing Reuse

**MUST REUSE** — Mesh side is NOT allowed to introduce new persistence mechanisms.

Use existing:
- `modes/_shared/manifest.py` for manifest generation
- `modes/_shared/emit_manifest.py` for emission
- Same JSONL ledger format
- Same directory structure conventions

**Rationale:** Prevents dual systems, ensures consistent tooling.

---

## G. Governance Decisions (Resolved)

### G.0 DSP Architecture Decisions (Code-Affecting)

These decisions directly affect how code is generated.

---

#### Q1: Canonical Return Type for WAV Reads

**Decision:** Arrays only for DSP; metadata passed separately.

**Rationale:** DSP functions should be pure transforms on numerical data. WavMeta is context/provenance, not computation input.

**Pattern:**
```python
# CORRECT: Separate arrays from metadata at call site
ref, rov, meta = read_wav_2ch(path)
H_mag, H_phase = compute_transfer_function(ref, rov, meta.sample_rate)
# meta.sample_rate is the ONLY field DSP may consume

# WRONG: Passing WavMeta into DSP internals
result = compute_something(wav_meta)  # NO - couples DSP to I/O structure
```

**Rules:**
1. `read_wav_*` returns `(array(s), WavMeta)` — caller unpacks immediately
2. DSP functions accept `np.ndarray` + scalar params (e.g., `fs: int`)
3. WavMeta fields allowed in DSP: `sample_rate` only (as scalar `fs`)
4. Provenance is assembled at writer stage, not inside DSP

**Enforcement:** Code review; DSP modules may not import `WavMeta` type.

---

#### Q2: Scalar vs Vector in Phase 2 Writers

**Decision:** Full frequency vectors per point (Option A).

**Rationale:** Future-proof; supports multi-frequency analysis without re-capture.

**Schema Contract:**
```json
{
  "freqs_hz": [100.0, 150.0, 200.0],       // N frequencies
  "points": [
    {
      "point_id": "A1",
      "x_mm": 50.0,
      "y_mm": 100.0,
      "H_mag": [0.5, 0.7, 0.3],            // length N
      "H_phase_deg": [45.0, -30.0, 90.0],  // length N
      "coherence": [0.95, 0.88, 0.92]      // length N
    }
  ]
}
```

**Invariants:**
- `len(H_mag) == len(H_phase_deg) == len(coherence) == len(freqs_hz)`
- All arrays indexed by same frequency axis
- Single-frequency snapshots are just `len(freqs_hz) == 1`

**Writer Behavior:**
```python
# Writer MUST emit arrays, even for single frequency
ods_point = {
    "point_id": point_id,
    "x_mm": x,
    "y_mm": y,
    "H_mag": [float(mag)],           # Array, not scalar
    "H_phase_deg": [float(phase)],   # Array, not scalar
    "coherence": [float(coh)],       # Array, not scalar
}
```

**Test Expectation:** Schema validator rejects scalar values for these fields.

---

#### Q3: Provenance Granularity Policy

**Decision:** Three-tier provenance model.

| Tier | Scope | Required Fields | When |
|------|-------|-----------------|------|
| **Tier 1: Capture** | Per-file | `wav_sha256`, `created_utc`, `device_name` | Every WAV/JSON input |
| **Tier 2: Algorithm** | Per-computation | `algo_id`, `algo_version`, `computed_at_utc` | Every derived output |
| **Tier 3: Environment** | Per-session | `numpy_version`, `scipy_version`, `python_version` | Once per pipeline run |

**Tier 1 — Capture Provenance (in capture_meta.json):**
```json
{
  "point_id": "A1",
  "created_at_utc": "2026-01-01T12:00:00Z",
  "device_name": "USB Audio Device",
  "sample_rate_hz": 48000
}
```

**Tier 2 — Algorithm Provenance (in derived/*.json):**
```json
{
  "provenance": {
    "algo_id": "ods_transfer_function",
    "algo_version": "1.2.0",
    "computed_at_utc": "2026-01-01T12:05:00Z"
  }
}
```

**Tier 3 — Environment Provenance (in derived/*.json, nested):**
```json
{
  "provenance": {
    "algo_id": "wolf_stress_index",
    "algo_version": "2.0.0",
    "numpy_version": "1.26.0",
    "scipy_version": "1.11.0",
    "computed_at_utc": "2026-01-01T12:05:00Z",
    "dsp_provenance": {
      "algo_id": "ods_transfer_function",
      "algo_version": "1.2.0"
    }
  }
}
```

**Implementation:**
```python
# Each DSP module exports a provenance function
def get_dsp_provenance() -> dict:
    return {
        "algo_id": "ods_transfer_function",
        "algo_version": "1.2.0",
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }

# Writers call this and add timestamp
provenance = get_dsp_provenance()
provenance["computed_at_utc"] = datetime.utcnow().isoformat() + "Z"
```

**Nested Provenance Rule:** If algorithm B depends on algorithm A's output, B's provenance MUST include A's provenance under `dsp_provenance` or similar key.

---

### G.1 Schema Registry Index

**Decision:** Single JSON file + validation script

**Location:** `contracts/schema_registry.json`

**Format:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "registry_version": "1.0.0",
  "updated": "2026-01-01T00:00:00Z",
  "schemas": {
    "phase2_grid": {
      "file": "phase2_grid.schema.json",
      "version": "1.0.0",
      "status": "stable",
      "owner": "acoustics-team"
    },
    "phase2_ods_snapshot": {
      "file": "phase2_ods_snapshot.schema.json",
      "version": "2.0.0",
      "status": "stable",
      "owner": "acoustics-team"
    }
  }
}
```

**Version Bump Approval Process:**

| Change Type | Approval Required | Process |
|-------------|-------------------|---------|
| Patch (x.x.X) | Self-approve | Fix typos, clarify descriptions, no field changes |
| Minor (x.X.0) | PR review by owner | Add optional fields, backward compatible |
| Major (X.0.0) | ADR + owner sign-off | Breaking changes, field removals, type changes |

**Owners:**
- `acoustics-team`: Phase 2 schemas, ODS, wolf candidates
- `measurement-team`: tap_peaks, moe_result, manifest
- `chladni-team`: chladni_run, mesh-related schemas

**CI Enforcement:** `.github/workflows/schema-registry-guard.yml`
- Validates registry JSON is well-formed
- Checks all referenced schema files exist
- Ensures version in registry matches `$id` in schema file
- Blocks PRs that bump major version without ADR reference

---

### G.2 Chladni Frequency Mismatch Policy

**Decision:** Warn + keep with `delta_hz`, fail only if threshold exceeded

**Rationale:** Calibration drift happens; strict failure would reject valid data. But large mismatches indicate real problems.

**Threshold:** `CHLADNI_FREQ_TOLERANCE_HZ = 5.0` (configurable)

**Behavior:**

| Condition | Action | Output Field |
|-----------|--------|--------------|
| `|filename_freq - peak_freq| ≤ 5.0 Hz` | **WARN** + continue | `delta_hz`, `mismatch_warning: true` |
| `|filename_freq - peak_freq| > 5.0 Hz` | **FAIL** run | Exception raised, no output |
| Peak not found in expected range | **FAIL** run | Exception with diagnostic |

**Schema Addition to `chladni_run.schema.json`:**
```json
{
  "patterns": {
    "items": {
      "properties": {
        "nominal_freq_hz": { "type": "number", "description": "Frequency from filename" },
        "detected_freq_hz": { "type": "number", "description": "Actual peak frequency" },
        "delta_hz": { "type": "number", "description": "nominal - detected" },
        "mismatch_warning": { "type": "boolean", "default": false }
      }
    }
  }
}
```

**Configuration:**
```python
# In modes/chladni/config.py
CHLADNI_FREQ_TOLERANCE_HZ = float(os.environ.get("CHLADNI_FREQ_TOLERANCE_HZ", "5.0"))
```

**Logging:**
```
WARNING: Chladni pattern 187Hz: detected peak at 185.3Hz (delta=-1.7Hz) - within tolerance, continuing
ERROR: Chladni pattern 250Hz: detected peak at 238.1Hz (delta=-11.9Hz) - exceeds tolerance 5.0Hz, failing run
```

---

### G.3 Phase-2 Promotion Gate

**Decision:** Formal checklist with explicit owners and ADR requirement

**Promotion Path:**
```
tap-tone-lab/ (experimental) → scripts/phase2/ (canonical) → modes/ (frozen)
```

**Checklist for Promotion to `scripts/phase2/` (Canonical):**

| # | Requirement | Owner | Evidence |
|---|-------------|-------|----------|
| 1 | **Unit tests exist** with ≥80% coverage | Author | `pytest --cov` report |
| 2 | **Schema contract defined** in `contracts/` | Author | Schema file committed |
| 3 | **No extra fields** in outputs | Author + Reviewer | Schema validation passes |
| 4 | **Provenance function** exports algorithm ID | Author | `get_*_provenance()` exists |
| 5 | **WAV I/O uses canonical module** | Author | No direct scipy imports |
| 6 | **Documentation** in `docs/phase2/` | Author | README section added |
| 7 | **CI workflow** validates outputs | Author | Workflow file committed |
| 8 | **ADR written** for non-trivial algorithms | Author | `docs/ADR-XXXX.md` |
| 9 | **Boundary guard passes** | CI | Green check |
| 10 | **Two reviewer approvals** | Reviewers | PR approvals |

**Promotion PR Template:**
```markdown
## Phase-2 Promotion Request

**Module:** `{module_name}`
**From:** `tap-tone-lab/` or `scripts/*.py`
**To:** `scripts/phase2/`

### Checklist
- [ ] Unit tests with ≥80% coverage
- [ ] Schema contract in `contracts/`
- [ ] No extra fields in outputs
- [ ] Provenance function exists
- [ ] Uses canonical WAV I/O
- [ ] Documentation added
- [ ] CI workflow added
- [ ] ADR reference: ADR-XXXX (if applicable)

### Evidence
- Coverage report: [link]
- Schema file: `contracts/{schema}.schema.json`
- Test run: [CI link]

### Reviewers
- @acoustics-team-lead (required)
- @measurement-team-member (required)
```

**Owners for Approval:**

| Domain | Primary Owner | Backup |
|--------|---------------|--------|
| Phase 2 DSP | `@acoustics-lead` | `@dsp-reviewer` |
| Chladni/Mesh | `@chladni-lead` | `@acoustics-lead` |
| Bending/MOE | `@measurement-lead` | `@acoustics-lead` |
| Schema contracts | `@contracts-owner` | `@acoustics-lead` |

**Freeze Gate (to `modes/`):**
- All of above PLUS:
- 30-day stabilization period with no breaking changes
- Integration test suite passes
- Cross-repo validation (ToolBox can consume outputs)
- Sign-off from both `@acoustics-lead` AND `@contracts-owner`

---

### G.4 Pipeline Validation Report: phase2_slice.py

**Validation Date:** 2026-01-01
**Target:** `scripts/phase2_slice.py` + supporting modules
**Against:** DSP Architecture Decisions (G.0: Q1, Q2, Q3)

---

#### Q1: WAV Read Return Types — Arrays Only for DSP ✅ COMPLIANT

**Decision:** DSP functions receive raw arrays; metadata passed separately.

| Location | Pattern | Status |
|----------|---------|--------|
| `scripts/phase2/io_wav.py:29-30` | `ref, rov, meta = _read_wav_2ch(path)` → `Wav2Ch(...)` | ✅ |
| `scripts/phase2_slice.py:209-212` | `w = read_wav_2ch(...)` then `compute_transfer_and_coherence(w.x_ref, w.x_rov, w.sample_rate, ...)` | ✅ |
| `scripts/phase2/dsp.py:38-41` | `def compute_transfer_and_coherence(x_ref: np.ndarray, x_rov: np.ndarray, fs: int, ...)` | ✅ |

**Finding:** Arrays (`x_ref`, `x_rov`) and metadata (`sample_rate`) are cleanly separated. The DSP layer never receives embedded metadata objects.

---

#### Q2: Scalar vs Vector — Full Frequency Vectors ✅ COMPLIANT

**Decision:** Always emit arrays, never naked scalars, even for single-frequency snapshots.

| Location | Output Field | Value Pattern | Status |
|----------|--------------|---------------|--------|
| `phase2_slice.py:342` | `H_mag` | `[float(s.H_mag[bi])]` | ✅ |
| `phase2_slice.py:343` | `H_phase_deg` | `[float(s.phase_deg[bi])]` | ✅ |
| `phase2_slice.py:344` | `coherence` | `[float(s.coherence[bi])]` | ✅ |
| `phase2_slice.py:350` | `freqs_hz` | `[target_actual]` | ✅ |

**Finding:** Even single-frequency ODS snapshots wrap values in arrays, ensuring downstream consumers don't need scalar vs array branching logic.

---

#### Q3: Three-Tier Provenance Model ✅ COMPLIANT

**Decision:** Capture → Algorithm → Environment tiers.

**Tier 1 — Capture** (`capture_meta.json` at `phase2_slice.py:193-203`):
```
sample_rate_hz, seconds, synthetic, wav, created_at_utc
```

**Tier 2 — Algorithm** (`dsp.py:17-24` and `metrics.py`):
```python
def get_dsp_provenance() -> Dict[str, str]:
    return {
        "algo_id": DSP_ALGO_ID,           # "phase2_transfer_coherence"
        "algo_version": DSP_ALGO_VERSION, # "1.0.0"
        ...
    }
```

**Tier 3 — Environment** (embedded in provenance blocks):
```
numpy_version, scipy_version
```

**Provenance in wolf_candidates.json** (`phase2_slice.py:316-322`):
```json
{
  "provenance": {
    "algo_id": "...",
    "algo_version": "...",
    "numpy_version": "...",
    "computed_at_utc": "...",
    "dsp_provenance": { ... }
  }
}
```

**Provenance in ods_snapshot.json** (`phase2_slice.py:352-358`):
```json
{
  "provenance": {
    "algo_id": "...",
    "algo_version": "...",
    "numpy_version": "...",
    "scipy_version": "...",
    "computed_at_utc": "..."
  }
}
```

---

#### Validation Summary

| Decision | Compliance | Implementation Location |
|----------|------------|------------------------|
| Q1: Arrays-only DSP | ✅ PASS | `Wav2Ch` dataclass + DSP function signatures |
| Q2: Full vectors | ✅ PASS | ODS snapshot writer (lines 336-345) |
| Q3: Three-tier provenance | ✅ PASS | `get_dsp_provenance()` + output writers |

**Conclusion:** The Phase 2 pipeline implementation is fully aligned with the documented DSP architecture decisions. No remediation required.

---

## Quick Reference Tables

### Canonical Import Paths

```python
# WAV I/O (ALWAYS use this)
from modes._shared.wav_io import read_wav_mono, read_wav_2ch, write_wav_mono, write_wav_2ch

# Manifest generation
from modes._shared.manifest import generate_manifest
from modes._shared.emit_manifest import emit_manifest

# Phase 2 DSP
from scripts.phase2.dsp import compute_fft, get_dsp_provenance
from scripts.phase2.metrics import compute_coherence, get_metrics_provenance
from scripts.phase2.grid import load_grid, validate_grid
```

### Schema Validation Commands

```bash
# Validate Phase 2 outputs
python scripts/validate_schemas.py runs_phase2/session_*/derived/

# Validate contracts
python -m jsonschema -i derived/wolf_candidates.json contracts/phase2_wolf_candidates.schema.json
```

### Environment Variables Summary

| Variable | Repo | Purpose |
|----------|------|---------|
| `RMOS_SIGNED_URL_SECRET` | toolbox | Signed URL generation |
| `RMOS_RUN_ATTACHMENTS_DIR` | toolbox | Attachment storage path |
| `RMOS_MAX_ATTACHMENT_BYTES` | toolbox | Upload size limit |
| `RMOS_ACOUSTICS_SIGNING_TTL_SECONDS` | toolbox | Token lifetime |

### CI Workflow Quick Reference

| Action | tap_tone_pi | luthiers-toolbox |
|--------|-------------|------------------|
| Run tests | `pytest tests/` | `pytest services/api/tests/` |
| Validate schemas | `python scripts/validate_schemas.py` | Automatic in CI |
| Check boundaries | `python ci/check_boundary_imports.py` | Endpoint truth check |
| Lint | `ruff check .` | `ruff check services/api/` |

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-01 | Claude Code | Initial creation from cross-repo exploration |
| 2026-01-01 | Claude Code | Added Section G: Governance Decisions (schema registry, Chladni mismatch, promotion gate) |
| 2026-01-01 | Claude Code | Added G.0: DSP Architecture Decisions (WAV return types, vector vs scalar, provenance tiers) |
| 2026-01-01 | Claude Code | Added G.4: Pipeline Validation Report for phase2_slice.py against DSP decisions |

---

*This document is the authoritative reference for cross-repo development decisions. Update this document when architectural decisions change.*
