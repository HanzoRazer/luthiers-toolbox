# MRP-3A: DXF Translator Architecture & Governance Integration

**Date:** 2026-05-13  
**Sprint:** MRP-3A  
**Status:** COMPLETE

---

## Executive Summary

MRP-3A establishes the governed translator layer downstream of Export Objects. DXF translators now consume Export Objects (not raw geometry) and produce governed DXF output with embedded provenance.

**Translator Layer Status: OPERATIONAL**

---

## Architecture Achievement

```
┌─────────────────────────────────────────────────────────────┐
│ MRP Morphology Spine (MRP-2D verified)                      │
│   IBG → BOE → Export Object                                 │
├─────────────────────────────────────────────────────────────┤
│ MRP-3A Translator Layer (NEW)                               │
│   Export Object → DXF Translator → DXF File                 │
│                                                             │
│   Key innovations:                                          │
│   - Translators CONSUME semantics (Export Objects)          │
│   - Translators DO NOT CREATE semantics                     │
│   - Gate enforcement: red gate blocks translation           │
│   - Provenance embedding: IBG context in DXF output         │
│   - Dual-format: R12 (free tier), R2000 (paid tier)         │
└─────────────────────────────────────────────────────────────┘
```

---

## New Execution Tier: governed_execution

MRP-3A introduces a new execution state in the capability registry:

| State | execution_supported | artifact_generation_supported | Use Case |
|-------|---------------------|-------------------------------|----------|
| validation_only | false | false | 7B declarative-only translators |
| execution_disabled | false | false | Disabled/placeholder translators |
| **governed_execution** | **true** | **true** | MRP-3A translators for Export Objects |

---

## Files Created

| File | Purpose |
|------|---------|
| `app/cam/translators/__init__.py` | Package init with exports |
| `app/cam/translators/base.py` | ExportTranslator Protocol, BaseTranslator class |
| `app/cam/translators/dxf/__init__.py` | DXF translator package |
| `app/cam/translators/dxf/body_outline_translator.py` | BodyOutlineDxfTranslator implementation |
| `tests/cam/test_body_outline_translator.py` | pytest tests (skipped due to numpy) |
| `tests/mrp_spine_verification/standalone_translator_verify.py` | Standalone verification |

---

## Files Modified

| File | Change |
|------|--------|
| `app/cam/translator_capability_registry.py` | Added governed_execution state, registered body_outline_dxf_r12/r2000 |

---

## Translator Protocol

```python
@runtime_checkable
class ExportTranslator(Protocol):
    @property
    def translator_id(self) -> str: ...
    
    @property
    def translator_version(self) -> str: ...
    
    @property
    def output_format(self) -> str: ...
    
    def can_translate(
        self,
        export_object: Union[BodyExportObject, ExportObject],
    ) -> bool: ...
    
    def translate(
        self,
        export_object: Union[BodyExportObject, ExportObject],
        options: Optional[Dict[str, Any]] = None,
    ) -> TranslatorResult: ...
```

---

## Registered Translators

| ID | Output | State | Maturity |
|----|--------|-------|----------|
| body_outline_dxf_r12 | DXF R12 | governed_execution | governed |
| body_outline_dxf_r2000 | DXF R2000 | governed_execution | governed |

---

## Translation Flow

```
1. Export Object arrives (gate must be green or yellow)
2. Translator checks gate status
   - Red gate → TranslatorError(GATE_RED), no output
   - Green/yellow → proceed
3. Translator extracts geometry entities
4. DXF writer generates format-appropriate output
   - R12: LINE entities for maximum CAM compatibility
   - R2000: LWPOLYLINE entities for modern CAM
5. Provenance embedded as text entities in PROVENANCE layer
6. TranslatorResult returned with bytes + statistics
```

---

## Verification Results

```
r12_translation:      VERIFIED
r2000_translation:    VERIFIED
red_gate_rejection:   VERIFIED
dxf_file_output:      VERIFIED
capability_registry:  VERIFIED
```

---

## Provenance Embedding

Each DXF output includes provenance text on the PROVENANCE layer:

```
Export ID: EXP-BODY-20260513-dread001
Translator: body_outline_dxf_r12 v1.0.0
Translated: 2026-05-13
IBG Session: ibg-dread-001
Instrument: dreadnought
```

---

## Governance Invariants

| Invariant | Enforced |
|-----------|----------|
| governed_execution requires execution_supported=true | ENFORCED (model_validator) |
| validation_only forbids execution_supported=true | ENFORCED |
| machine_output_supported always false | ENFORCED |
| Red gate blocks translation | ENFORCED |
| Translator wraps existing dxf_writer (no direct ezdxf) | ENFORCED |

---

## Usage Example

```python
from app.cam.translators.dxf import create_r12_translator
from app.export.body_export_bridge import create_body_export_object

# Create export object from BOE-approved geometry
export_obj = create_body_export_object(approved_geometry)

# Translate to DXF
translator = create_r12_translator()
result = translator.translate(export_obj)

if result.success:
    # Write DXF file
    with open("body_outline.dxf", "wb") as f:
        f.write(result.output_bytes)
    
    # Access provenance
    print(f"IBG Session: {result.provenance.ibg_session_id}")
else:
    # Handle errors
    for error in result.errors:
        print(f"{error.code}: {error.message}")
```

---

## Relationship to Existing Infrastructure

| Component | Relationship |
|-----------|--------------|
| dxf_writer.py | Wrapped by translator (PROTECTED, not modified) |
| dxf_compat.py | Used by dxf_writer (PROTECTED, not modified) |
| translator_capability_registry.py | Extended with new state and registrations |
| body_export_bridge.py | Provides input schema (BodyExportObject) |

---

## Next Steps (MRP-3B+)

1. **API Endpoint**: `POST /api/translate/body-outline` that accepts BodyExportObject
2. **Batch Translation**: Multiple export objects to single DXF
3. **STEP Translator**: Future alternative output format
4. **Deprecation Path**: Migrate existing DXF generators to translator consumption

---

## References

- `docs/handoffs/MRP_2D_MORPHOLOGY_SPINE_VERIFICATION_REPORT.md`
- `docs/architecture/BOE_EXPORT_OBJECT_BRIDGE_MODEL.md`
- `CLAUDE.md` — DXF output standard (dual-format via dxf_compat)

---

*MRP-3A complete. The translator era has begun. Export Objects now have a governed downstream path to DXF output.*
