# MRP-3B: DXF Translator API Endpoint Integration

**Date:** 2026-05-13  
**Sprint:** MRP-3B  
**Status:** COMPLETE

---

## Executive Summary

MRP-3B exposes the governed DXF translator (MRP-3A) through the platform API. Export Objects can now be converted into DXF files through a controlled, validated endpoint.

**Endpoint Status: OPERATIONAL**

---

## Endpoints Implemented

### POST /api/export/translate/dxf

Translate Export Object to DXF file.

**Request:**
```json
{
  "schema_version": "1.0.0",
  "export_id": "EXP-BODY-20260513-dread001",
  "export_type": "geometry",
  "metadata": { ... },
  "geometry": { ... },
  "validation": {
    "gate_status": "green",
    ...
  },
  "intent": { ... },
  "extensions": { ... }
}
```

**Query Parameters:**
- `version=r12` (default): R12 format, LINE entities, free tier
- `version=r2000`: R2000 format, LWPOLYLINE entities, paid tier

**Response (200):**
- Content-Type: `application/dxf`
- Content-Disposition: `attachment; filename="EXP-BODY-20260513-dread001_r12.dxf"`
- Body: DXF file bytes

**Response Headers:**
```
X-Export-ID: EXP-BODY-20260513-dread001
X-Translator-ID: body_outline_dxf_r12
X-Translator-Version: 1.0.0
X-Governance-Gate: green
X-Provenance-Hash: abc123def456
X-IBG-Session-ID: ibg-dread-001
X-Instrument-Spec: dreadnought
```

### POST /api/export/translate/dxf/metadata

Get translation metadata without DXF bytes (dry run).

**Response (200):**
```json
{
  "export_id": "EXP-BODY-20260513-dread001",
  "translator_id": "body_outline_dxf_r12",
  "translator_version": "1.0.0",
  "gate_status": "green",
  "output_format": "dxf_r12",
  "output_size_bytes": 6284,
  "entities_translated": 1,
  "provenance_hash": "abc123def456",
  "ibg_session_id": "ibg-dread-001",
  "instrument_spec": "dreadnought"
}
```

---

## Gate Enforcement

| Gate Status | HTTP Response | Behavior |
|-------------|---------------|----------|
| GREEN | 200 | Translation proceeds |
| YELLOW | 200 + warning header | Translation proceeds, X-Governance-Warnings header added |
| RED | 422 | Translation blocked |

**Red Gate Error Response:**
```json
{
  "ok": false,
  "error": "EXPORT_OBJECT_NOT_TRANSLATABLE",
  "gate": "red",
  "reasons": ["Outer contour not closed", ...]
}
```

---

## Version Selection

| Parameter | Translator ID | Output Format |
|-----------|---------------|---------------|
| `version=r12` (default) | body_outline_dxf_r12 | DXF R12, LINE entities |
| `version=r2000` | body_outline_dxf_r2000 | DXF R2000, LWPOLYLINE entities |

Unknown versions return 400 Bad Request.

---

## Rate Limiting

| User Type | Rate Limit |
|-----------|------------|
| Unauthenticated | 10/hour |
| Authenticated | 100/hour |

Rate limits are enforced via `app.middleware.rate_limit`.

---

## Verification Results

```
r12_translation:      VERIFIED
r2000_translation:    VERIFIED
red_gate_rejection:   VERIFIED
yellow_gate_warning:  VERIFIED
provenance_headers:   VERIFIED
filename_disposition: VERIFIED
metadata_endpoint:    VERIFIED
default_version_r12:  VERIFIED
no_geometry_mutation: VERIFIED
```

All 9 endpoint tests pass via `standalone_endpoint_verify.py`.

---

## Files Created

| File | Purpose |
|------|---------|
| `app/routers/export/dxf_translate_router.py` | API endpoint implementation |
| `tests/export/__init__.py` | Test package init |
| `tests/export/test_dxf_translate_endpoint.py` | pytest tests (skipped due to numpy) |
| `tests/mrp_spine_verification/standalone_endpoint_verify.py` | Standalone verification |

---

## Files Modified

| File | Change |
|------|--------|
| `app/router_registry/manifests/cam_manifest.py` | Added RouterSpec for dxf_translate_router |

---

## Router Registry Entry

```python
RouterSpec(
    module="app.routers.export.dxf_translate_router",
    prefix="/api/export/translate",
    tags=["Export", "Translate", "DXF", "MRP"],
    category="cam",
)
```

Classification:
- `machine_output`: false
- `translator_execution`: true
- `requires_export_object`: true
- `red_gate_blocks`: true

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Client Request                                               │
│   POST /api/export/translate/dxf?version=r12                │
│   Body: BodyExportObject JSON                               │
├─────────────────────────────────────────────────────────────┤
│ API Endpoint (dxf_translate_router.py)                      │
│   1. Validate version parameter                             │
│   2. Check gate status (red → 422)                          │
│   3. Select translator from registry                        │
│   4. Execute governed translation                           │
│   5. Return DXF bytes with metadata headers                 │
├─────────────────────────────────────────────────────────────┤
│ Governed Translator (MRP-3A)                                │
│   - BodyOutlineDxfTranslator                                │
│   - Wraps dxf_writer.py                                     │
│   - Embeds provenance                                       │
├─────────────────────────────────────────────────────────────┤
│ Response                                                     │
│   Content-Type: application/dxf                             │
│   Body: DXF file bytes                                      │
│   Headers: provenance metadata                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Governance Invariants Verified

| Invariant | Status |
|-----------|--------|
| Uses governed translator registry | VERIFIED |
| Red gate blocks translation | VERIFIED |
| R12 and R2000 versions work | VERIFIED |
| No geometry mutation | VERIFIED |
| No ad hoc DXF bypass | VERIFIED |
| No machine-output fields | VERIFIED |
| Provenance preserved | VERIFIED |

---

## Known Limitations

1. **pytest skipped**: Python 3.14/numpy module reload conflict requires standalone verification
2. **No STEP export**: Out of scope for MRP-3B
3. **No G-code**: machine_output_supported remains false
4. **Single Export Object per request**: Batch translation not implemented

---

## Follow-Up Documentation (Not Yet Created)

The following governance documents are referenced in the DEV ORDER but do not yet exist:

- `docs/governance/TRANSLATOR_LAYER_RULES.md`
- `docs/governance/DXF_TRANSLATOR_SERIALIZATION_POLICY.md`

**Note:** Implementation remains valid because:
- Endpoint uses governed translator registry
- Red gate blocks translation
- R12/R2000 work correctly
- No geometry mutation occurs
- No ad hoc DXF bypass exists

The missing docs should be created as follow-up work to formalize the rules that are currently enforced in code.

---

## Next Steps (MRP-3C+)

1. **Batch Translation**: Multiple Export Objects → single DXF
2. **STEP Translator**: Alternative output format
3. **Streaming Response**: Large file support
4. **Governance Docs**: Create TRANSLATOR_LAYER_RULES.md and DXF_TRANSLATOR_SERIALIZATION_POLICY.md
5. **Deprecation Path**: Migrate existing DXF generators to translator consumption

---

## Usage Example

```bash
# Translate Export Object to R12 DXF
curl -X POST "https://api.theproductionshop.com/api/export/translate/dxf?version=r12" \
  -H "Content-Type: application/json" \
  -d @export_object.json \
  -o body_outline.dxf

# Get metadata only (dry run)
curl -X POST "https://api.theproductionshop.com/api/export/translate/dxf/metadata" \
  -H "Content-Type: application/json" \
  -d @export_object.json
```

---

## References

- `docs/handoffs/MRP_3A_DXF_TRANSLATOR_ARCHITECTURE_HANDOFF.md`
- `docs/handoffs/MRP_2B_EXPORT_OBJECT_ENDPOINT_HANDOFF.md`
- `docs/handoffs/MRP_2D_MORPHOLOGY_SPINE_VERIFICATION_REPORT.md`
- `docs/architecture/BOE_EXPORT_OBJECT_BRIDGE_MODEL.md`

---

*MRP-3B complete. The DXF translator is now accessible via API. Export Objects have a governed path to DXF output.*
