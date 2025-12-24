# RMOS Art Studio Binding Bundle — Integration Location

**Document Version:** 1.0
**Date:** 2025-12-23
**Status:** Implemented

---

## Overview

### What It Does

**Art Studio → RMOS Authority Binding** — Binds Art Studio candidate attachments (SVG/spec JSON) into a RunArtifact with:

- ALLOW/BLOCK decision
- GREEN/YELLOW/RED risk level
- SVG safety gate (blocks `<script>`, `<foreignObject>`, `<image>`, `<path>`, `<text>`)
- Feasibility SHA256 hash
- Advisory blob browser with mime sniffing, filename inference, and download/preview

---

## Inputs

| Component | Inputs |
|-----------|--------|
| `bind_art_studio_candidate` | `run_id`, `attachment_ids[]` (sha256 CAS keys), `operator_notes`, `strict` flag |
| `advisory_blob_service` | `run_id`, `sha256` (advisory blob key) |
| `AdvisoryBlobBrowser.vue` | `runId` prop, optional `apiBase` prop |

---

## Outputs

| Component | Outputs |
|-----------|---------|
| `bind_art_studio_candidate` | `BindArtStudioCandidateResponse` (artifact_id, decision, risk_level, score, feasibility_sha256) |
| `list_advisory_blobs` | `AdvisoryBlobListResponse` (run_id, count, items[]) |
| `preview_svg` | SVG bytes as `image/svg+xml` (or 415 if blocked by safety gate) |
| `download_all_zip` | ZIP file containing all linked advisory blobs |

---

## Connection Point

**RMOS Runs v2 Subsystem** — `app/rmos/runs_v2/`

---

## Pattern

- [x] **Schema → Store → Router** (like rmos/runs/)
- [x] **Service called by router** (like services/)

```
Schema:    advisory_blob_schemas.py
Service:   bind_art_studio_service.py, advisory_blob_service.py
Router:    api_runs.py (endpoints added)
Store:     Uses existing runs_v2/store.py and attachments.py
```

---

## Dependencies

### Backend — bind_art_studio_service.py

```python
from app.rmos.runs_v2.attachments import (
    get_bytes_attachment,
    get_attachment_path,
    load_json_attachment,
    verify_attachment,
)
from app.rmos.runs_v2.schemas import RunAttachment
from app.rmos.runs_v2.hashing import sha256_of_text
```

### Backend — advisory_blob_service.py

```python
from app.rmos.runs_v2.store import get_run
from app.rmos.runs_v2.attachments import get_attachment_path, get_bytes_attachment
```

### Frontend — AdvisoryBlobBrowser.vue

```typescript
import { computed, onMounted, ref, watch } from "vue"
```

---

## Who Calls It

- [x] **HTTP endpoint (user/frontend)**
- [ ] Another Python module
- [ ] Background job

---

## Directory Structure

```
services/api/app/rmos/runs_v2/
├── advisory_blob_schemas.py      ← NEW
├── advisory_blob_service.py      ← NEW
├── bind_art_studio_service.py    ← NEW
├── attachments.py                ← MODIFIED (added get_bytes_attachment)
├── api_runs.py                   ← MODIFIED (added 6 endpoints)
└── ...

packages/client/src/components/rmos/
├── AdvisoryBlobBrowser.vue       ← NEW
└── ...
```

---

## Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `runs_v2/attachments.py` | MODIFIED | Added `get_bytes_attachment()` |
| `runs_v2/bind_art_studio_service.py` | NEW | SVG safety logic, risk scoring |
| `runs_v2/advisory_blob_schemas.py` | NEW | Pydantic schemas for advisory blob API |
| `runs_v2/advisory_blob_service.py` | NEW | Mime sniffing, SVG preview, zip download |
| `runs_v2/api_runs.py` | MODIFIED | Updated binding endpoint, added 5 advisory endpoints |
| `components/rmos/AdvisoryBlobBrowser.vue` | NEW | Vue component for blob browser UI |

---

## Import/Wiring

### Backend (Already Wired in api_runs.py)

```python
# In api_runs.py - bind service import (line 757)
from .bind_art_studio_service import bind_art_studio_candidate, ENGINE_VERSION

# In api_runs.py - advisory blob imports (lines 844-851)
from .advisory_blob_schemas import AdvisoryBlobListResponse, SvgPreviewStatusResponse
from .advisory_blob_service import (
    list_advisory_blobs,
    download_advisory_blob,
    preview_svg,
    check_svg_preview_status,
    download_all_zip,
)
```

### Frontend (NEEDS PATCH)

```vue
<!-- In RunDetailPage.vue or equivalent -->
<script setup lang="ts">
import AdvisoryBlobBrowser from "@/components/rmos/AdvisoryBlobBrowser.vue";
// Assume runId is available from route or parent
</script>

<template>
  <!-- Add to run detail view -->
  <AdvisoryBlobBrowser
    v-if="selectedRunId"
    :runId="selectedRunId"
    apiBase="/api/rmos"
  />
</template>
```

---

## API Endpoints Added

| Method | Path | Handler |
|--------|------|---------|
| POST | `/{run_id}/artifacts/bind-art-studio-candidate` | `bind_art_studio_candidate_route` |
| GET | `/{run_id}/advisory/blobs` | `list_run_advisory_blobs` |
| GET | `/{run_id}/advisory/blobs/{sha256}/download` | `download_run_advisory_blob` |
| GET | `/{run_id}/advisory/blobs/{sha256}/preview/svg` | `preview_run_advisory_svg` |
| GET | `/{run_id}/advisory/blobs/{sha256}/preview/status` | `check_run_advisory_svg_status` |
| GET | `/{run_id}/advisory/blobs/download-all.zip` | `download_all_run_advisory_blobs_zip` |

---

## SVG Safety Rules

The bind service evaluates SVG content for risk:

| Element | Decision | Risk Level | Score | Reason |
|---------|----------|------------|-------|--------|
| `<script>` | BLOCK | RED | 0.0 | Security risk |
| `<foreignObject>` | BLOCK | RED | 0.0 | Security risk |
| `<image>` | BLOCK | RED | 0.10 | External content risk |
| `<text>` | ALLOW | YELLOW | 0.75 | Manufacturing risk (fonts need outlining) |
| `<path>`, `<circle>`, etc. | ALLOW | GREEN | 1.0 | Expected geometry elements |

### Complexity Scoring

| Element Count | Decision | Risk Level | Score |
|---------------|----------|------------|-------|
| ≤80 | ALLOW | GREEN | 0.90 |
| ≤200 | ALLOW | YELLOW | 0.70 |
| >200 | BLOCK | RED | 0.45 |

---

## Patch Checklist

| Item | Status | Action |
|------|--------|--------|
| Backend services | Complete | No patch needed |
| API endpoints | Complete | No patch needed |
| Vue component | Complete | Wired into RunArtifactDetail.vue |
| API base path | Complete | Verified: `/api` (router mounted at `/api` with prefix `/runs`) |

---

## Related Documents

- `docs/Bundle_31.0.27_Executive_Summary.md` — Art Studio Run Orchestration
- `tests/verification/VERIFICATION_INSTRUCTIONS.md` — Verification procedures

---

*End of Document*
