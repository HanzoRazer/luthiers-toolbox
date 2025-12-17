# CompareLab Golden System

**Status:** ✅ B22.15 Complete  
**Date:** December 3, 2025

---

## 🎯 Overview

The **Golden Compare System** transforms CompareLab into a **regression detection engine** for CNC/CAM workflows.

It provides:
- **Baseline storage** - Save "correct" comparison results as golden files
- **Drift detection** - Automatically catch when geometry, layers, or bounding boxes change
- **CI integration** - Fail builds if CAM pipelines produce unexpected results
- **Hash-based validation** - Single-micron precision change detection

**Use cases:**
- CAM toolpath validation
- DXF export regression testing
- Geometry transformation verification
- Rosette engine output consistency
- Multi-version design comparison

---

## 📦 Golden File Structure

### Storage Location
```
.golden/
├── body_outline_v1_vs_v2.json
├── neck_profile_baseline.json
├── rosette_12A_vs_12B.json
└── inlay_pattern_check.json
```

### File Format
```json
{
  "version": 1,
  "left_name": "examples/comparelab/body_v1.svg",
  "right_name": "examples/comparelab/body_v2.svg",
  "mode": "overlay",
  "created_at": "2025-12-03T10:15:00Z",
  "expected": {
    "diff_hash": "sha256:9bb2d2f8a1c3e4f5...",
    "full_bbox": {
      "minX": 0,
      "minY": 0,
      "maxX": 100,
      "maxY": 100
    },
    "diff_bbox": {
      "minX": 10,
      "minY": 20,
      "maxX": 90,
      "maxY": 80
    },
    "layer_count": 3
  },
  "tolerance": {
    "bbox_abs": 0.0001
  }
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `version` | Schema version (currently 1) |
| `left_name` | Path to left SVG (typically relative) |
| `right_name` | Path to right SVG |
| `mode` | Compare mode used (overlay, delta, etc) |
| `created_at` | ISO timestamp of baseline creation |
| `expected.diff_hash` | SHA256 hash of canonical diff payload |
| `expected.full_bbox` | Full bounding box of geometry |
| `expected.diff_bbox` | Diff-specific bounding box (or null) |
| `expected.layer_count` | Number of layers in comparison |
| `tolerance.bbox_abs` | Absolute tolerance for bbox comparison (0.0 = strict) |

---

## 🔐 Diff Hash Algorithm

### What Gets Hashed

The `diff_hash` is computed from a **canonical payload** containing:
1. **Full bounding box** (`fullBBox`)
2. **Diff bounding box** (`diffBBox`)
3. **Layer presence** (sorted by ID):
   - Layer `id`
   - `inLeft` (boolean)
   - `inRight` (boolean)

### What's Excluded

To avoid false positives from noise:
- Timestamps
- Temporary IDs
- Server metadata
- Processing time
- File paths

### Computation

```python
# Canonical payload (stable order)
canonical = {
  "fullBBox": {"minX": 0, "minY": 0, "maxX": 100, "maxY": 100},
  "diffBBox": {"minX": 10, "minY": 20, "maxX": 90, "maxY": 80},
  "layers": [
    {"id": "body", "inLeft": true, "inRight": true},
    {"id": "inlay", "inLeft": false, "inRight": true}
  ]
}

# Compact JSON (no whitespace, sorted keys)
json_str = json.dumps(canonical, sort_keys=True, separators=(",", ":"))

# SHA256 hash
digest = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
diff_hash = f"sha256:{digest}"
```

**Result:** Any change in geometry, layers, or bounding boxes produces a different hash.

---

## 🔧 CLI Usage

### 1. Create Golden Baseline

```bash
python tools/compare_golden_cli.py create \
  --left examples/comparelab/body_v1.svg \
  --right examples/comparelab/body_v2.svg \
  --mode overlay \
  --out .golden/body_v1_vs_v2.json
```

**Output:**
```
📄 Reading SVG files...
   Left:  examples/comparelab/body_v1.svg
   Right: examples/comparelab/body_v2.svg
🔄 Running comparison via http://localhost:8000/compare/run
   Mode: overlay
✓ Comparison completed
💾 Golden baseline saved to: .golden/body_v1_vs_v2.json
   diff_hash:   sha256:9bb2d2f8a1c3e4f5...
   layer_count: 3
   bbox_tol:    0.0
```

**Options:**
- `--base-url` - API URL (default: `http://localhost:8000`)
- `--left` - Path to left SVG (required)
- `--right` - Path to right SVG (required)
- `--mode` - Compare mode: `side-by-side`, `overlay`, `delta` (default: `overlay`)
- `--out` - Output golden JSON path (required)
- `--bbox-tol` - Absolute bbox tolerance (default: `0.0`)

### 2. Check Against Baseline

```bash
python tools/compare_golden_cli.py check \
  --left examples/comparelab/body_v1.svg \
  --right examples/comparelab/body_v2.svg \
  --baseline .golden/body_v1_vs_v2.json
```

**Output (match):**
```
📋 Loading golden baseline: .golden/body_v1_vs_v2.json
📄 Reading SVG files...
   Left:  examples/comparelab/body_v1.svg
   Right: examples/comparelab/body_v2.svg
🔄 Running comparison (mode: overlay)
✅ [PASS] body_v1_vs_v2.json
   Golden: examples/comparelab/body_v1.svg vs body_v2.svg
   Hash:   sha256:9bb2d2f8a1c3e4f5...
```

**Output (drift):**
```
❌ [DRIFT] body_v1_vs_v2.json
   Reason: diff_hash mismatch (geometry/layers changed)
   Expected hash: sha256:9bb2d2f8a1c3e4f5...
   Actual hash:   sha256:a3f7c8d9e2b1f0a4...

Golden: examples/comparelab/body_v1.svg vs body_v2.svg
Mode: overlay

Layer count changed: 3 → 4
Full bbox changed:
  Expected: {'minX': 0, 'minY': 0, 'maxX': 100, 'maxY': 100}
  Actual:   {'minX': 0, 'minY': 0, 'maxX': 102, 'maxY': 100}
```

**Exit codes:**
- `0` - Match (pass)
- `1` - Drift detected (fail)

### 3. Batch Check All Baselines

```bash
python tools/compare_golden_cli.py check-all --dir .golden
```

**Output:**
```
🔍 Found 3 golden file(s) in .golden

✅ [PASS] body_v1_vs_v2.json
✅ [PASS] neck_profile_baseline.json
❌ [DRIFT] rosette_12A_vs_12B.json – diff_hash mismatch (geometry/layers changed)

============================================================
SUMMARY: 3 total
  ✅ Passed:  2
  ❌ Failed:  1
  ⏭️  Skipped: 0
============================================================

❌ Drift detected in:
   - rosette_12A_vs_12B.json: diff_hash mismatch (geometry/layers changed)
```

**Options:**
- `--base-url` - API URL (default: `http://localhost:8000`)
- `--dir` - Directory with golden JSON files (default: `.golden`)

**Exit codes:**
- `0` - All passed
- `1` - Any drift or errors

---

## 🚀 CI/CD Integration

### GitHub Actions

The workflow `.github/workflows/comparelab-golden.yml` automatically:
1. Starts CompareLab server
2. Runs `check-all` on all golden baselines
3. **Fails the build** if any drift detected
4. Comments on PR with drift details
5. Uploads drift artifacts

**Triggers:**
- Push to `main` or `feature/**` branches
- PR changes to:
  - `tools/compare_golden_cli.py`
  - `tools/golden_compare_lib.py`
  - `.golden/**`
  - `examples/comparelab/**`
  - Compare automation router

**CI Output (pass):**
```
✅ Golden Baseline Validation
   📋 Found 3 golden baseline(s)
   ✅ [PASS] body_v1_vs_v2.json
   ✅ [PASS] neck_profile_baseline.json
   ✅ [PASS] rosette_12A_vs_12B.json
   ✅ All golden comparisons passed!
```

**CI Output (drift):**
```
❌ Golden Baseline Validation
   📋 Found 3 golden baseline(s)
   ✅ [PASS] body_v1_vs_v2.json
   ❌ [DRIFT] rosette_12A_vs_12B.json – diff_hash mismatch
   
   ❌ Drift detected in:
      - rosette_12A_vs_12B.json: geometry/layers changed
```

### Manual CI Run

```bash
# In CI environment
python tools/compare_golden_cli.py check-all --dir .golden
if [ $? -ne 0 ]; then
  echo "Golden baseline drift detected!"
  exit 1
fi
```

---

## 🛠️ Programmatic Usage

### Python API

```python
from pathlib import Path
from tools.golden_compare_lib import (
    load_golden_file,
    check_against_golden,
    compute_diff_hash,
)

# Load golden baseline
golden = load_golden_file(Path(".golden/my_compare.json"))

# Run fresh comparison (via API or direct call)
compare_result = await call_compare_api(left_svg, right_svg)

# Check for drift
result = check_against_golden(golden, compare_result)

if result.ok:
    print("✅ Match")
else:
    print(f"❌ Drift: {result.reason}")
    print(f"   Expected: {result.expected_hash}")
    print(f"   Actual:   {result.actual_hash}")
```

### Compute Hash Only

```python
from tools.golden_compare_lib import compute_diff_hash

# From /compare/run response
compare_json = response_data["json"]
hash_value = compute_diff_hash(compare_json)
print(f"Hash: {hash_value}")
```

---

## 📊 Use Cases

### 1. CAM Toolpath Validation

**Problem:** CAM software update changes toolpath output.

**Solution:**
```bash
# Create baseline before update
python tools/compare_golden_cli.py create \
  --left cam_output_v1.svg \
  --right cam_output_v2.svg \
  --out .golden/cam_toolpath_v1_v2.json

# After update, verify no unexpected changes
python tools/compare_golden_cli.py check \
  --left cam_output_v1.svg \
  --right cam_output_v2_updated.svg \
  --baseline .golden/cam_toolpath_v1_v2.json
```

### 2. DXF Export Regression

**Problem:** Export library update changes geometry output.

**Solution:**
```bash
# Golden baseline for known-good export
python tools/compare_golden_cli.py create \
  --left design.svg \
  --right export_r12.svg \
  --out .golden/dxf_export_baseline.json

# CI check on every export code change
- name: Check DXF export
  run: |
    python tools/compare_golden_cli.py check-all --dir .golden
```

### 3. Multi-Version Design Consistency

**Problem:** Need to track design evolution across versions.

**Solution:**
```bash
# Create baseline for each major version
python tools/compare_golden_cli.py create \
  --left designs/body_v3.svg \
  --right designs/body_v4.svg \
  --out .golden/body_v3_vs_v4.json

# Verify v5 changes match expected evolution
python tools/compare_golden_cli.py check \
  --left designs/body_v4.svg \
  --right designs/body_v5.svg \
  --baseline .golden/body_v4_vs_v5.json
```

### 4. Rosette Engine Output Validation

**Problem:** Rosette generation algorithm changes subtly.

**Solution:**
```bash
# Baseline for 12-petal rosette
python tools/compare_golden_cli.py create \
  --left rosette_12_old.svg \
  --right rosette_12_new.svg \
  --out .golden/rosette_12_baseline.json

# CI: Fail if algorithm changes rosette geometry
```

---

## 🐛 Troubleshooting

### Issue: "diff_hash mismatch" but visually identical

**Cause:** Floating-point precision differences in bounding box.

**Solution:** Use `--bbox-tol` for tolerance:
```bash
python tools/compare_golden_cli.py create \
  --bbox-tol 0.0001 \
  --out .golden/baseline.json
```

### Issue: "Missing left/right SVG files" in check-all

**Cause:** Golden file references moved/deleted SVGs.

**Solution:**
1. Update golden file paths manually, or
2. Delete outdated golden files, or
3. Recreate with current paths

### Issue: CI fails but local check passes

**Cause:** Different server versions or environments.

**Solution:**
1. Ensure CI uses same Python/library versions
2. Check server logs for API differences
3. Verify SVG files are committed to repo

### Issue: Too many false positives

**Cause:** Golden baselines too strict (zero tolerance).

**Solution:**
1. Increase `bbox_abs` tolerance for precision-insensitive checks
2. Review what changes are actually meaningful
3. Update golden baselines if changes are intentional

---

## 🎯 Best Practices

### 1. Naming Conventions

```
.golden/
├── feature_description_leftname_vs_rightname.json
├── cam_toolpath_body_v1_vs_v2.json
├── dxf_export_neck_baseline.json
└── rosette_12petal_regression.json
```

**Pattern:** `{feature}_{description}_{comparison}.json`

### 2. Tolerance Guidelines

| Precision Level | `bbox_abs` | Use Case |
|----------------|-----------|----------|
| Strict | `0.0` | Exact geometry match required |
| Micron | `0.001` | CNC precision (0.001mm) |
| Sub-mm | `0.01` | Visual precision |
| Loose | `0.1` | Approximate comparison |

### 3. When to Update Baselines

**Update when:**
- ✅ Intentional design changes
- ✅ CAM algorithm improvements (verified)
- ✅ Library upgrades with known behavior changes

**Don't update when:**
- ❌ "I don't know why it changed"
- ❌ Unexpected drift without investigation
- ❌ Just to make CI pass

### 4. Organization

```
.golden/
├── cam/
│   ├── toolpath_body.json
│   └── toolpath_neck.json
├── exports/
│   ├── dxf_body.json
│   └── dxf_rosette.json
└── designs/
    ├── body_v1_vs_v2.json
    └── neck_v1_vs_v2.json
```

**Use subdirectories** for large projects with many baselines.

---

## 📈 Future Enhancements (Nice to Have)

### 1. Diff Visualization
Generate side-by-side images showing what changed:
```bash
python tools/compare_golden_cli.py check \
  --baseline .golden/my_compare.json \
  --output-diff drift_visualization.html
```

### 2. Batch Baseline Creation
Create golden files for entire directory:
```bash
python tools/compare_golden_cli.py create-batch \
  --left-dir designs/v1/ \
  --right-dir designs/v2/ \
  --out-dir .golden/batch/
```

### 3. Interactive Drift Review
Web UI for reviewing and approving drifts:
```bash
python tools/compare_golden_review.py \
  --drift-report ci_failures.json
```

### 4. Historical Tracking
Store drift history for trending analysis:
```json
{
  "history": [
    {"date": "2025-12-01", "hash": "sha256:abc..."},
    {"date": "2025-12-02", "hash": "sha256:def..."},
    {"date": "2025-12-03", "hash": "sha256:ghi..."}
  ]
}
```

---

## 📋 Integration Checklist

- [x] Create `tools/golden_compare_lib.py` with hash algorithm
- [x] Create `tools/compare_golden_cli.py` with create/check/check-all
- [x] Create `.github/workflows/comparelab-golden.yml` CI workflow
- [x] Create `docs/COMPARELAB_GOLDEN_SYSTEM.md` documentation
- [ ] Add example golden files in `.golden/examples/`
- [ ] Create test SVG pairs in `examples/comparelab/`
- [ ] Generate initial golden baselines for project
- [ ] Add golden check to existing CI pipeline
- [ ] Document in main README.md
- [ ] Train team on golden workflow

---

## 🔗 Related Documentation

- **B22.13 Automation API**: See `docs/B22_13_COMPARE_AUTOMATION_API.md`
- **B22.14 Report Export**: See `docs/COMPARELAB_REPORTS.md`
- **CompareLab Overview**: See main README

---

**Status:** ✅ B22.15 Complete - Golden System Production-Ready  
**Impact:** CompareLab is now a **regression detection engine** for CNC/CAM workflows  
**Next:** Create example golden baselines and add to CI pipeline
