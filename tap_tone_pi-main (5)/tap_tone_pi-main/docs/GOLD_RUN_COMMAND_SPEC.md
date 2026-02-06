# `tap_tone gold-run` — One-Command Gold Standard Run

## Purpose

Run a complete "Gold Standard Example Run" with **minimal operator decisions**:

1. Detect/configure device
2. Capture **N** impulse measurements (default **3**)
3. Label points deterministically (`A1..A3`)
4. Export viewer pack ZIP
5. Validate (`validation_report.json passed=true`)
6. Optionally ingest into ToolBox (luthiers-toolbox) evidence library

This command is **instrument UX**: it reduces first-run friction and produces a canonical, repeatable dataset.

---

## Command Synopsis

```bash
tap_tone gold-run \
  --specimen-id gold_plate_A1 \
  --device "<device name or index>" \
  --out-dir ./exports \
  [--points 3] \
  [--session-id <id>] \
  [--batch-label <label>] \
  [--tap-timeout-s 8] \
  [--min-peak-hz 50] \
  [--max-peak-hz 3000] \
  [--audio-required {true|false}] \
  [--export-zip {true|false}] \
  [--ingest-url http://localhost:8000] \
  [--ingest] \
  [--dry-run] \
  [--json]
```

---

## Outputs (Deterministic)

### Staged session directory

Created under a predictable location (configurable), e.g.:

```
runs/gold/<YYYY-MM-DD>/<specimen-id>/<session_key>/
```

Contains:

* captured audio + intermediate artifacts (whatever your existing capture pipeline produces)
* `viewer_pack.json` and `validation_report.json` during export

### Exported viewer pack ZIP

```
<out-dir>/gold_standard_viewer_pack_v1_<specimen-id>_<YYYY-MM-DD>_<HHMMSS>.zip
```

### Console summary

At end, prints:

* session dir
* zip path
* validation status
* (if ingest) ToolBox run_id + browse URL hint

---

## Operator Workflow (What the user does)

The operator does only:

* set up specimen + mic
* run command
* tap when prompted (or when auto-trigger is enabled later)

---

## Capture Semantics

### Point labeling

Default: `A1..A{N}` (N=`--points`, default 3)

Each point is one clean capture. If capture fails, retry rules apply.

### Tap timeout

If no adequate impulse is detected within `--tap-timeout-s`:

* prompt user to retry that point
* after `--max-retries` (default 3) → abort run

### Quality gate per point (minimal)

A point is accepted if:

* signal peak exceeds a threshold above noise floor (simple SNR heuristic)
* no clipping detected (if available)
* spectrum produced successfully

This is intentionally basic—Gold Run is about repeatability, not perfect acoustics.

---

## Export + Validation Semantics

After last point:

1. Calls existing `export_viewer_pack_v1.export_viewer_pack(session_dir, out_dir, as_zip=True)`
2. Export must create:

   * `viewer_pack.json` at pack root
   * `validation_report.json` at pack root
3. Validation must pass:

   * if `passed=false` → command exits non-zero and prints excerpt + report path

Exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `2` | Validation failed |
| `3` | Capture failed / retries exceeded |
| `4` | Device configuration error |
| `5` | Unexpected exception |

---

## ToolBox Ingest (Optional)

### Trigger

If `--ingest` is passed, after successful export:

```
POST {--ingest-url}/api/rmos/acoustics/import-zip
Form fields:
- file=@<zip>
- session_id=<--session-id> (optional)
- batch_label=<--batch-label> (optional)
```

Success prints:

* `run_id`
* counts
* any index updates

Failure prints:

* status code (400/422)
* error payload excerpt

This step is optional and can be disabled by default.

---

## Arguments (Detailed)

### Required

| Argument | Description |
|----------|-------------|
| `--specimen-id` | Human identifier used in metadata and file naming |
| `--device` | Audio device selector (index, exact name, or substring match) |
| `--out-dir` | Directory for exported ZIP |

### Common optional

| Argument | Default | Description |
|----------|---------|-------------|
| `--points` | 3 | Number of captures |
| `--tap-timeout-s` | 8 | Seconds to wait for impulse |
| `--audio-required` | false | Mirrors validator semantics |
| `--export-zip` | true | If false: only stages pack, still validates |

### ToolBox ingest optional

| Argument | Default | Description |
|----------|---------|-------------|
| `--ingest` | false | Enable ToolBox ingest |
| `--ingest-url` | `http://localhost:8000` | ToolBox API base URL |
| `--session-id` | (none) | Passed through to ingest |
| `--batch-label` | (none) | Passed through to ingest |

### Diagnostics

| Argument | Description |
|----------|-------------|
| `--dry-run` | Prints planned paths and device selection, does not capture |
| `--json` | Prints machine-readable summary JSON at end |

---

## Machine-Readable Summary (`--json`)

Example:

```json
{
  "schema_id": "tap_tone_gold_run_out_v1",
  "specimen_id": "gold_plate_A1",
  "points": ["A1", "A2", "A3"],
  "session_dir": "runs/gold/2026-01-21/gold_plate_A1/session_153012",
  "zip_path": "exports/gold_standard_viewer_pack_v1_gold_plate_A1_2026-01-21_153012.zip",
  "validation": {
    "passed": true,
    "errors": 0,
    "warnings": 1,
    "report_path": "…/validation_report.json"
  },
  "ingest": {
    "attempted": true,
    "ok": true,
    "run_id": "run_...",
    "http_status": 200
  }
}
```

---

## Minimal Implementation Plan (Files)

### New CLI entrypoint

* `tap_tone/cli/gold_run.py`
  * `main(argv=None) -> int`

### Wire into CLI dispatcher

Wherever you register commands:

* add `gold-run` command

### Core logic components (reuse existing)

| Component | Source |
|-----------|--------|
| Device selection | Existing audio device enumeration module |
| Capture loop | Call existing "capture one point" function N times |
| Session directory | Reuse existing session/run builder |
| Export | Call existing `export_viewer_pack_v1.export_viewer_pack(...)` |
| Validation | Already runs inside export; handle exit codes + messaging |
| Ingest | Small HTTP POST helper using `requests` (or stdlib) |

### Tests (smoke)

* `tests/test_gold_run_dry_run.py`: verifies path planning + device selection logic on `--dry-run`
* (Optional) integration tests behind a flag requiring audio hardware

---

## Definition of Done

- [ ] `tap_tone gold-run --dry-run ...` works everywhere
- [ ] `tap_tone gold-run ...` produces a valid viewer pack ZIP
- [ ] Validation report is embedded and passes
- [ ] Optional ingest works against local ToolBox (`/api/rmos/acoustics/import-zip`)
- [ ] Command prints a clear success summary and returns `0`

---

## Future Extensions

**Auto-trigger**: Start capture, listen for impulse over threshold, record automatically. Not required for initial ship — the above spec delivers value immediately without new DSP.

---

## Related Documents

* [GOLD_STANDARD_EXAMPLE_RUN.md](../GOLD_STANDARD_EXAMPLE_RUN.md) — Manual gold run procedure
* [FIRST_MEASUREMENT_CHECKLIST.md](../FIRST_MEASUREMENT_CHECKLIST.md) — Step-by-step operator checklist
* [QUICKSTART.md](../QUICKSTART.md) — 5-minute first measurement

---

### Version

Gold Run Command Spec v1.0
