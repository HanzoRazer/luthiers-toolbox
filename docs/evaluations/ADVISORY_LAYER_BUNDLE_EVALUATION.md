# Advisory_Layer_Bundle Evaluation

**Evaluated:** December 2024
**Location:** `Advisory_Layer_Bundle/` (repo root - needs relocation)
**Status:** AI-generated, fills infrastructure gap

---

## 1. Current State Analysis

### Existing Infrastructure (ai_graphics)

| File | Location | Lines | Status |
|------|----------|-------|--------|
| `image_providers.py` | `services/api/app/_experimental/ai_graphics/` | 794 | ✅ EXISTS |
| `prompt_engine.py` | `services/api/app/_experimental/ai_graphics/` | 698 | ✅ EXISTS |
| `vision_routes.py` | `services/api/app/_experimental/ai_graphics/api/` | 802 | ✅ EXISTS |

### Missing Infrastructure (Advisory Layer)

| File | Provided By Bundle | Lines | Status |
|------|-------------------|-------|--------|
| `advisory_store.py` | ✅ Yes | 194 | ❌ MISSING from codebase |
| `advisory_schemas.py` | ✅ Yes | 156 | ❌ MISSING from codebase |
| `advisory_routes.py` | ✅ Yes | 333 | ❌ MISSING from codebase |

---

## 2. Bundle Contents

```
Advisory_Layer_Bundle/           (683 total lines)
├── advisory_store.py           (194 lines) - Asset storage
├── api/
│   └── advisory_routes.py      (333 lines) - API endpoints
└── schemas/
    └── advisory_schemas.py     (156 lines) - Pydantic models
```

---

## 3. Architecture & Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXISTING (ai_graphics)                       │
├─────────────────────────────────────────────────────────────────┤
│  vision_routes.py                                                │
│       │                                                          │
│       ▼                                                          │
│  GuitarVisionEngine (image_providers.py)                        │
│       │                                                          │
│       ▼                                                          │
│  prompt_engine.py → image_transport.py → OpenAI/SDXL            │
│                                                                  │
│  PROBLEM: No governance layer. Images go directly to workflow.  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     WITH ADVISORY LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  advisory_routes.py                                              │
│       │                                                          │
│       ├─→ GuitarVisionEngine (existing)                         │
│       │                                                          │
│       ▼                                                          │
│  AdvisoryAssetStore                                              │
│       │                                                          │
│       ├─→ Save as AdvisoryAsset (NOT approved)                  │
│       │                                                          │
│       ▼                                                          │
│  HUMAN REVIEW REQUIRED                                           │
│       │                                                          │
│       ├─→ POST /assets/{id}/review (approve/reject)             │
│       │                                                          │
│       ▼                                                          │
│  Only approved assets can be used in workflow                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Features

### 4.1 AdvisoryAsset Schema

```python
class AdvisoryAsset(BaseModel):
    asset_id: str                    # adv_{uuid}
    asset_type: AdvisoryAssetType    # IMAGE, SUGGESTION, ANALYSIS, PATTERN
    source: str                      # ai_graphics, ai_analysis, ai_suggestion
    provider: str                    # dalle3, sdxl, stub

    # Content
    prompt: str
    content_hash: str
    content_uri: Optional[str]

    # GOVERNANCE
    reviewed: bool = False
    approved_for_workflow: bool = False
    reviewed_by: Optional[str]
    reviewed_at_utc: Optional[datetime]
    review_note: Optional[str]
```

### 4.2 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/advisory/generate/image` | POST | Generate image → AdvisoryAsset (NOT approved) |
| `/api/advisory/assets` | GET | List assets with filters |
| `/api/advisory/assets/{id}` | GET | Get asset metadata |
| `/api/advisory/assets/{id}/content` | GET | Get binary content |
| `/api/advisory/assets/{id}/review` | POST | Human review (approve/reject) |
| `/api/advisory/pending` | GET | List assets pending review |
| `/api/advisory/stats` | GET | System statistics |

### 4.3 Storage Structure

```
data/advisory_assets/           (ADVISORY_ASSETS_ROOT env var)
├── 2025/
│   └── 12/
│       └── 19/
│           ├── adv_abc123.json          # Asset metadata
│           └── adv_abc123_content.png   # Binary content
```

---

## 5. Governance Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| AI cannot create RunArtifacts | AdvisoryAsset is separate type | ✅ |
| Human review required | `reviewed=False` by default | ✅ |
| Approval before workflow | `approved_for_workflow=False` by default | ✅ |
| Audit trail | `reviewed_by`, `reviewed_at_utc`, `review_note` | ✅ |
| Content integrity | `content_hash` (SHA256) | ✅ |
| Cost tracking | `cost_usd` field | ✅ |

---

## 6. Integration Requirements

### 6.1 Import Dependencies

`advisory_routes.py` imports:
```python
from ..image_providers import (
    GuitarVisionEngine,
    ImageSize,
    ImageQuality,
    ImageProvider,
)
```

**Required location:** Bundle must be placed where it can import from `image_providers.py`.

### 6.2 Recommended Location

```
services/api/app/_experimental/ai_graphics/
├── image_providers.py          # EXISTING
├── prompt_engine.py            # EXISTING
├── api/
│   ├── vision_routes.py        # EXISTING
│   └── advisory_routes.py      # ← MOVE HERE
├── schemas/
│   └── advisory_schemas.py     # ← MOVE HERE
└── advisory_store.py           # ← MOVE HERE
```

### 6.3 Alternative: Sibling Directory

```
services/api/app/_experimental/
├── ai_graphics/                 # EXISTING
│   ├── image_providers.py
│   └── ...
└── advisory/                    # NEW
    ├── __init__.py
    ├── advisory_store.py
    ├── schemas/
    │   └── advisory_schemas.py
    └── api/
        └── advisory_routes.py
```

---

## 7. Edge Cases

### 7.1 Content Hash Verification

```python
computed_hash = compute_content_hash(content)
if asset.content_hash and asset.content_hash != computed_hash:
    raise ValueError(f"Content hash mismatch...")
```

**Behavior:** Fails if hash doesn't match.

### 7.2 Missing Content

```python
if content is None:
    raise HTTPException(
        status_code=404,
        detail={"error": "CONTENT_NOT_FOUND", "asset_id": asset_id}
    )
```

### 7.3 Generation Failure

```python
if not result.success or not result.images:
    raise HTTPException(
        status_code=500,
        detail={"error": "GENERATION_FAILED", "message": result.error}
    )
```

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Import path issues | High | Must relocate to correct directory |
| Missing `image_providers.py` exports | Medium | Verify `GuitarVisionEngine`, `ImageSize`, etc. are exported |
| Date partition scan slowness | Low | Only an issue at 10,000+ assets |
| Cost accumulation | Medium | `cost_usd` tracked, add monitoring |

---

## 9. Action Items for Integration

1. **Relocate bundle** to `services/api/app/_experimental/ai_graphics/`

2. **Fix imports** in `advisory_routes.py`:
   ```python
   # Change from:
   from ..image_providers import ...
   # To:
   from .image_providers import ...  # (if same directory)
   ```

3. **Add to router** in `main.py`:
   ```python
   from services.api.app._experimental.ai_graphics.api.advisory_routes import router as advisory_router
   app.include_router(advisory_router)
   ```

4. **Set environment variable**:
   ```
   ADVISORY_ASSETS_ROOT=data/advisory_assets
   ```

5. **Test generation endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/advisory/generate/image \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Test rosette", "size": "1024x1024"}'
   ```

---

## 10. Re-Review Checklist

### Schema
- [ ] `AdvisoryAsset` has `reviewed=False` default
- [ ] `AdvisoryAsset` has `approved_for_workflow=False` default
- [ ] `content_hash` is SHA256

### Store
- [ ] Date partitions: `YYYY/MM/DD/`
- [ ] Metadata and content stored separately
- [ ] `get_advisory_store()` singleton works

### Routes
- [ ] `/generate/image` returns unapproved asset
- [ ] `/assets/{id}/review` requires human action
- [ ] `/pending` lists unreviewed assets

### Integration
- [ ] Imports resolve correctly
- [ ] `GuitarVisionEngine` accessible
- [ ] Router registered in `main.py`

---

## 11. Verdict

**Purpose:** Fills the missing governance layer between AI image generation and workflow use.

**Quality:** Well-structured, follows existing patterns.

**Action:** Relocate from repo root to `services/api/app/_experimental/ai_graphics/` and fix imports.

**Recommendation:** INTEGRATE after relocation and import fixes.
