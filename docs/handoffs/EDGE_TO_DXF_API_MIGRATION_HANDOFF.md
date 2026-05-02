# Edge-to-DXF API Migration — Executive Handoff

**Date:** 2026-04-28  
**Scope:** photo-vectorizer edge_to_dxf.py integration with FastAPI backend  
**Status:** COMPLETE — production-ready with entity caps and batch modes  
**Sprint context:** Sprint 4 (Photo Vectorizer Production Readiness)

---

## Summary

The `edge_to_dxf.py` high-fidelity converter has been fully integrated into the API layer. This tool converts image/PDF edges directly to DXF LINE entities, preserving every detected edge pixel as vector geometry. Two recent commits completed this work:

| Commit | Date | Change |
|--------|------|--------|
| `d383f6c5` | 2026-04-27 | Path resolution fix, complete API integration |
| `3f315dfe` | 2026-04-28 | Entity caps (5M per-image, 12M aggregate) and batch modes |

---

## Architecture Position

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Vectorizer Ecosystem                         │
├─────────────────────┬─────────────────────┬─────────────────────────┤
│ Blueprint Import    │ Photo Vectorizer    │ Edge-to-DXF             │
│ (vectorizer_phase3) │ (photo_vectorizer_v2)│ (edge_to_dxf)          │
├─────────────────────┼─────────────────────┼─────────────────────────┤
│ ML classification   │ 12-stage pipeline   │ High-fidelity archival  │
│ OCR integration     │ Grid zone system    │ Multi-scale edge fusion │
│ PDF parsing         │ Body isolation      │ Every pixel preserved   │
├─────────────────────┼─────────────────────┼─────────────────────────┤
│ OUTPUT: Classified  │ OUTPUT: Body +      │ OUTPUT: 50K-7.5M LINE   │
│ layers (BODY,       │ cavities (SVG/DXF)  │ entities per image      │
│ CAVITY, DETAIL)     │                     │                         │
├─────────────────────┼─────────────────────┼─────────────────────────┤
│ 4K-40K entities     │ 120-500 entities    │ 500K-7.5M entities      │
└─────────────────────┴─────────────────────┴─────────────────────────┘
```

**Key distinction:** Edge-to-DXF is for archival and manual CAD tracing. It preserves maximum detail at the cost of file size (10-1100 MB). The other vectorizers produce semantically structured output with far fewer entities.

---

## Files Delivered

### Core Implementation
| File | Location | Purpose |
|------|----------|---------|
| `edge_to_dxf.py` | `services/photo-vectorizer/` | CLI tool + library (~500 lines) |
| `edge_to_dxf_router.py` | `services/api/app/routers/blueprint/` | FastAPI endpoints (368 lines) |

### Documentation
| File | Location | Purpose |
|------|----------|---------|
| `edge_to_dxf_test_procedures.md` | `docs/testing/` | Test protocols, benchmark data |
| `blueprint_import_sandbox_phase2_2026-04-27.md` | `docs/audit/` | Cross-reference analysis |
| `DEVELOPER_HANDOFF.md` | `services/photo-vectorizer/` | Photo vectorizer architecture |

---

## API Endpoints

### Status Check
```
GET /api/blueprint/edge-to-dxf/status
```
Returns module availability and PDF support status.

### Standard Conversion
```
POST /api/blueprint/edge-to-dxf/convert
```
Single-pass Canny edge detection with configurable thresholds.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `file` | (required) | Image or PDF upload |
| `target_height_mm` | 500.0 | Output scale target |
| `canny_low` | 50 | Edge detection low threshold |
| `canny_high` | 150 | Edge detection high threshold |
| `adjacency` | 3.0 | Pixel connection distance |
| `return_file` | false | Return DXF directly vs JSON metadata |

### Enhanced Conversion (Highest Quality)
```
POST /api/blueprint/edge-to-dxf/enhanced
```
Multi-scale edge fusion (3 Canny threshold levels). This is the method that produced the reference `cuatro_puertoriqueno_simple.dxf` (15.5MB, 129K entities).

---

## CLI Usage (Direct)

```bash
cd services/photo-vectorizer

# Basic conversion
python edge_to_dxf.py "blueprint.png" -o output.dxf --height 500

# Enhanced multi-scale fusion
python edge_to_dxf.py "blueprint.png" --enhanced -o output.dxf

# Batch: combine multiple images
python edge_to_dxf.py page1.png page2.png --batch -o combined.dxf

# Batch: process directory to separate files
python edge_to_dxf.py "Guitar Plans/" --separate-batch --output-dir outputs/

# With entity cap override
python edge_to_dxf.py "high_detail.jpg" --max-entities 8000000
```

---

## Entity Cap System (New in 3f315dfe)

Prevents memory exhaustion and unmanageable output files.

| Cap | Default | Scope |
|-----|---------|-------|
| Per-image | 5,000,000 | Single image conversion |
| Aggregate | 12,000,000 | Combined batch DXF |

When a cap is exceeded:
1. Conversion aborts gracefully (no partial corrupt DXF)
2. API returns `status: "CAP_EXCEEDED"` with diagnostics
3. Recommendation provided: higher thresholds or image downsampling

**Cap exceeded response:**
```json
{
  "success": false,
  "status": "CAP_EXCEEDED",
  "cap_value": 5000000,
  "entities_at_failure": 5000001,
  "cap_message": "Try higher edge thresholds (canny_low=80, canny_high=200)..."
}
```

---

## Batch Modes (New in 3f315dfe)

### Combined Batch (`--batch`)
Multiple images merged into single DXF with each on its own layer.

```bash
python edge_to_dxf.py *.png --batch -o combined.dxf --spacing 50 --layout grid
```

Layouts: `vertical` (stack) or `grid` with configurable columns.

### Separate Batch (`--separate-batch`)
Each input processed to its own DXF with JSON report.

```bash
python edge_to_dxf.py "Plans/" --separate-batch --output-dir out/ --recursive
```

Produces `batch_report.json` with per-file success/failure status and entity counts.

---

## Benchmark Data (2026-04-27 Test Run)

### Blueprint Scans (Clean Input)
| File | Entities | Size | Time |
|------|----------|------|------|
| Bailey Page 1 | 955,692 | 139 MB | ~3 min |
| Bailey Page 2 | 544,796 | 79 MB | ~2 min |

### Photos (High Texture)
| File | Entities | Size | Status |
|------|----------|------|--------|
| 12 String Dread 2 | 3,123,516 | 456 MB | SUCCESS |
| Benedetto Front | 7,569,875 | 1,106 MB | SUCCESS (high thresholds) |
| Benedetto Back | 2,669,225 | 389 MB | SUCCESS |

**Threshold guidance:**
- Clean blueprints: 50/150 (default)
- High-detail photos: 80/200
- Photos with wood grain: 100/250

---

## Output Characteristics

- **Format:** DXF R12 (AC1009) for maximum CAD compatibility
- **Entities:** Individual LINE segments (not LWPOLYLINE)
- **Layer:** `CONTOURS` (single layer per image; multi-layer in batch)
- **Scale:** Calculated from `--height` parameter
- **Coordinates:** mm, Y-up orientation

**File size formula:**
```
Approximate size = LINE_entities × 145 bytes
```

---

## Integration Points

### Upstream (Input Sources)
- User uploads via Blueprint Lab UI
- PDF rasterization at 300 DPI (PyMuPDF)
- Existing image files from vectorizer test corpus

### Downstream (Consumers)
- Manual CAD tracing in Fusion 360 / AutoCAD
- InstrumentBodyGenerator (IBG) for constraint extraction
- Body Outline Editor for cleanup and editing

### Cross-Service Dependencies
```
edge_to_dxf_router.py
  ↓ imports
services/photo-vectorizer/edge_to_dxf.py
  ↓ uses
cv2 (OpenCV), ezdxf, numpy
```

No database. No state. Pure stateless conversion service.

---

## Known Limitations

1. **Memory:** Images with 4M+ edge pixels and 60K+ contours can trigger MemoryError before cap is hit. Mitigate with image downsampling.

2. **Wood grain texture:** Photos with prominent wood grain (archtops, Benedetto) generate millions of texture edges. Requires high thresholds (100/250+).

3. **Unicode filenames:** Now handled via fallback loader (fixed in d383f6c5), but Windows paths with special characters may still have edge cases.

4. **No semantic classification:** Unlike photo_vectorizer_v2 and vectorizer_phase3, edge_to_dxf produces raw edges without body/cavity/detail classification. It's a preservation tool, not a feature extraction tool.

---

## Relationship to Other Vectorizer Work

### Active Systems

| System | Status | Primary Use |
|--------|--------|-------------|
| Blueprint vectorizer (phase3) | LIVE | Classified PDF extraction |
| Photo vectorizer (blueprint path) | LIVE | Scanned blueprint PNG/JPEG |
| Edge-to-DXF | LIVE | High-fidelity archival |

### Suspended Systems

| System | Status | Reason |
|--------|--------|--------|
| Photo vectorizer (photo path) | SUSPENDED | Poor results on L-1 historical images |
| Photo vectorizer (AI path) | SUSPENDED | Poor results on AI renders |

---

## Sprint Context

From `SPRINTS.md`:

**Sprint 4 — Photo Vectorizer Production Readiness**
- Status: IN PROGRESS — PARTIALLY SUSPENDED
- Edge-to-DXF integration: COMPLETE
- Remaining work: body isolation filter, scale discrepancy (photo/AI paths only)

**Sprint 3 — Remediation and Gap Closure**
- Edge-to-DXF now follows DXF R12 standard via dxf_compat pattern
- No direct ezdxf.new() calls in production path

---

## Testing

### API Test
```bash
curl http://127.0.0.1:8000/api/blueprint/edge-to-dxf/status

curl -X POST http://127.0.0.1:8000/api/blueprint/edge-to-dxf/convert \
  -F "file=@blueprint.png" \
  -F "target_height_mm=500" \
  -F "return_file=true" \
  -o output.dxf
```

### CLI Test
```bash
cd services/photo-vectorizer
python edge_to_dxf.py "test_image.png" -o test_output.dxf --debug
```

### Full Test Suite
See `docs/testing/edge_to_dxf_test_procedures.md` for comprehensive test protocols.

---

## Next Steps (Recommended)

1. **Production deployment:** Edge-to-DXF router is registered in `services/api/app/routers/blueprint/__init__.py` — verify Railway deployment includes photo-vectorizer service path.

2. **UI integration:** Add "High-Fidelity Export" button to Blueprint Lab that calls `/edge-to-dxf/enhanced`.

3. **Batch processing UI:** For multi-page plans (e.g., Fender headstock pages), expose batch mode through frontend.

4. **Cap tuning:** Monitor production usage. Default 5M cap may need adjustment based on real-world failure rates.

---

## Author

This handoff compiled from:
- Recent commits `d383f6c5`, `3f315dfe`
- Test procedures documentation (2026-04-27)
- Blueprint Import Sandbox Audit Phase 2 (2026-04-27)
- SPRINTS.md registry (2026-04-26)
- DEVELOPER_HANDOFF.md in photo-vectorizer

**Generated:** 2026-04-28
