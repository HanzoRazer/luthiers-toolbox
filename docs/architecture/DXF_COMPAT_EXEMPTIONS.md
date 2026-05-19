# DXF Compatibility Exemptions

**Date:** 2026-05-11  
**Status:** Active Governance

---

## Rule

All DXF document creation in production code must use:

```python
from app.util.dxf_compat import create_document
doc = create_document(version="R2010")
```

Direct `ezdxf.new()` calls are forbidden outside documented exemptions.

---

## Enforcement

- **Script:** `scripts/check_dxf_compat.py`
- **Pre-commit hook:** `dxf-compat-check` (enabled after remediation)
- **CI gate:** Added to DXF validation workflow

---

## Exemption Classifications

| Classification | Description | Review Trigger |
|----------------|-------------|----------------|
| CANONICAL_WRAPPER_ALLOWED | The dxf_compat wrapper itself | Never |
| EXCLUDED_EXTERNAL_ECOSYSTEM | Separate ecosystem, not Production Shop | Repo separation |
| EXCLUDED_R_AND_D_SANDBOX | Experimental code, not production path | Promotion to production |
| TEST_FIXTURE_ALLOWED | Test files creating DXF fixtures | Phase 2 migration |

---

## Documented Exemptions

### CANONICAL_WRAPPER_ALLOWED

| File | Reason | Owner | Expiration |
|------|--------|-------|------------|
| `services/api/app/util/dxf_compat.py` | Canonical DXF wrapper implementation | Production Shop | Never |
| `services/blueprint-import/dxf_compat.py` | Blueprint Reader DXF wrapper | Production Shop | Never |
| `services/api/app/cam/dxf_writer.py` | Central DXF writer (docstring reference only) | Production Shop | Never |

---

### EXCLUDED_EXTERNAL_ECOSYSTEM

| File | Reason | Owner | Review Trigger |
|------|--------|-------|----------------|
| `services/api/app/instrument_geometry/body/smart_guitar_dxf.py` | Smart Guitar ecosystem, pending repo separation | Smart Guitar Team | Repo separation complete |
| `services/api/app/routers/instruments/guitar/smart_guitar_dxf_router.py` | Smart Guitar ecosystem | Smart Guitar Team | Repo separation complete |
| `services/api/scripts/generate_smart_guitar_v3_dxf.py` | Smart Guitar build script | Smart Guitar Team | Repo separation complete |

**Note:** Smart Guitar is its own ecosystem and should not drive or contaminate Production Shop governance decisions. These files are excluded pending Smart Guitar repo separation or separate governance establishment.

---

### EXCLUDED_R_AND_D_SANDBOX

| File | Reason | Owner | Review Trigger |
|------|--------|-------|----------------|
| `services/photo-vectorizer/ai_render_extractor.py` | Experimental R&D, not production path | R&D | Promotion to Blueprint Reader |

**Note:** Photo Vectorizer is experimental and should not contaminate Blueprint Reader. Its original goal is commercially premature; useful primitives may be promoted later, but it is not part of the hardened Blueprint Reader path.

---

### TEST_FIXTURE_ALLOWED

Test files are allowed to use `ezdxf.new()` for fixture creation:

| Pattern | Count | Phase 2 Action |
|---------|-------|----------------|
| `services/api/tests/test_*.py` | 7 files | Migrate to test helper using dxf_compat |
| `services/api/tests/e2e_*.py` | 1 file | Migrate to test helper using dxf_compat |

**TODO (Phase 2):** Migrate test DXF creation to a test helper using dxf_compat where practical. New tests should prefer dxf_compat unless specifically testing raw ezdxf behavior.

---

## Adding New Exemptions

To add a new exemption:

1. **Document the exemption** in this file with:
   - File path
   - Classification
   - Reason (why it cannot use dxf_compat)
   - Owner
   - Expiration or review trigger

2. **Add to enforcement script** in `scripts/check_dxf_compat.py`:
   ```python
   EXCLUDED_EXTERNAL_ECOSYSTEM = {
       # ... existing ...
       'path/to/new/file.py',
   }
   ```

3. **Get review** from Production Shop architecture owner

---

## History

| Date | Change |
|------|--------|
| 2026-05-11 | Initial exemptions document created |
| 2026-05-11 | DXF compliance remediation sprint completed |
| 2026-05-11 | Smart Guitar and Photo Vectorizer excluded |

---

*Governance document for Production Shop DXF compliance*
