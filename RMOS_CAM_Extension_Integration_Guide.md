# RMOS/CAM Extension Integration Guide
## Prompt → SVG Variants → Run Attachments (Hybrid Storage)

**Date:** December 23, 2025  
**Project:** Luthier's ToolBox  
**Target:** RMOS v2 + Art Studio Integration

---

## Executive Summary

This document provides the **exact repository information** needed to integrate the RMOS/CAM extension for generating SVG variants from user prompts. The extension will:

- Generate **one or more SVG variants** from a user prompt
- Store SVGs as **runs_v2 attachments** (content-addressed, deduplicated)
- Maintain a lightweight **Art Studio asset index** referencing attachment SHAs
- Provide **stable regeneration** via `variant_seed`
- Include **provenance tracking** (revised_prompt, request_id, timings)

---

## 1. Canonical Attachment API (runs_v2)

### Location
`app/rmos/runs_v2/attachments.py`

### Storage Architecture
- **Content-addressed storage** using SHA256 hashes
- **Natural deduplication** - same content = same hash = single file
- **Sharded structure:** `{root}/{sha[0:2]}/{sha[2:4]}/{sha256}{ext}`
- **Default path:** `services/api/data/run_attachments`
- **Environment override:** `RMOS_RUN_ATTACHMENTS_DIR`

### Write Operations

```python
from app.rmos.runs_v2.attachments import (
    put_bytes_attachment,
    put_text_attachment,
    put_json_attachment,
)
from app.rmos.runs_v2.schemas import RunAttachment

# Store binary data (images, etc.)
attachment, storage_path = put_bytes_attachment(
    data: bytes,
    kind: str,              # e.g., "geometry_svg", "ai_provenance_json"
    mime: str,              # e.g., "image/svg+xml"
    filename: str,          # Display name
    ext: str = ""           # e.g., ".svg"
)
# Returns: Tuple[RunAttachment, str]
# - RunAttachment: metadata with sha256, kind, mime, filename, size_bytes
# - str: filesystem path where file was stored

# Store text content (SVG strings, etc.)
attachment, storage_path = put_text_attachment(
    text: str,
    kind: str,
    mime: str = "text/plain",
    filename: str = "attachment.txt",
    ext: str = ".txt"
)
# Returns: Tuple[RunAttachment, str]

# Store JSON objects (provenance, metadata, etc.)
attachment, storage_path, sha256 = put_json_attachment(
    obj: Any,
    kind: str,
    filename: str = "data.json",
    ext: str = ".json"
)
# Returns: Tuple[RunAttachment, str, str]
# Third return value is the computed sha256
```

### Read Operations

```python
from app.rmos.runs_v2.attachments import (
    get_attachment_path,
    verify_attachment,
)

# Get filesystem path by SHA256
path = get_attachment_path(sha256: str) -> Optional[str]
# Tries common extensions if exact match not found

# Verify attachment integrity
result = verify_attachment(sha256: str) -> Dict[str, Any]
# Recomputes hash and validates against expected
```

### RunAttachment Schema

```python
class RunAttachment(BaseModel):
    sha256: str              # Content hash (primary key)
    kind: str                # Attachment type
    mime: str                # MIME type
    filename: str            # Display filename
    size_bytes: int          # File size
    created_at_utc: str      # ISO timestamp
    request_id: Optional[str]  # Correlation ID for audit
    metadata: Dict[str, Any]   # Additional metadata
```

---

## 2. Run Provenance Fields

### Location
`app/rmos/runs_v2/schemas.py` → `RunArtifact` model

### Available Fields

```python
class RunArtifact(BaseModel):
    # Required fields
    run_id: str
    created_at_utc: datetime
    mode: str
    tool_id: str
    status: Literal["OK", "BLOCKED", "ERROR"]
    
    # Core payloads
    request_summary: Dict[str, Any]
    feasibility: Dict[str, Any]
    decision: RunDecision
    hashes: Hashes
    outputs: RunOutputs
    
    # Provenance (RECOMMENDED)
    request_id: Optional[str]
    # ↑ Request correlation ID from middleware
    # Extracted from: request.state.request_id or request.headers["x-request-id"]
    
    # Session linkage (OPTIONAL, marked [LEGACY])
    workflow_session_id: Optional[str]
    # ↑ Parent workflow session
    # Not required - can be None
    
    # Advisory/explanation hooks (append-only)
    advisory_inputs: List[AdvisoryInputRef]
    explanation_status: Literal["NONE", "PENDING", "READY", "ERROR"]
    explanation_summary: Optional[str]
    
    # Free-form metadata
    meta: Dict[str, Any]
    # ↑ Recommended for: versions, correlation IDs, custom provenance
```

### Standard Practice

1. **Always set `request_id`** from middleware:
   ```python
   request_id = request.state.request_id or request.headers.get("x-request-id")
   ```

2. **Use `meta` for additional provenance:**
   ```python
   meta = {
       "provider": "openai",
       "model": "dall-e-3",
       "variant_seed": seed,
       "revised_prompt": revised_prompt,
       "compute_ms": elapsed_ms,
   }
   ```

3. **Link to workflow sessions** (optional):
   ```python
   workflow_session_id = body.workflow_session_id  # if provided
   ```

---

## 3. Workflow Session Linkage

### Current Implementation

**Field:** `workflow_session_id` in `RunArtifact`  
**Type:** `Optional[str]`  
**Status:** Marked as `[LEGACY]` but still functional  
**Required:** No - can be None

### Schema Location
`app/workflow/sessions/schemas.py`

```python
class WorkflowSessionCreateRequest(BaseModel):
    user_id: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    workflow_type: Optional[str] = None
    current_step: Optional[str] = "draft"
    machine_id: Optional[str] = None
    material_id: Optional[str] = None
    tool_id: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None
    state_data_json: Optional[Dict[str, Any]] = None
```

### Usage Pattern

```python
# If linking to an existing session
if workflow_session_id:
    run_artifact.workflow_session_id = workflow_session_id
    
# Session can retrieve its runs via:
# GET /api/workflow-sessions/{session_id}/runs (planned)
```

---

## 4. Art Studio Router Mount Conventions

### Current Patterns in `main.py`

```python
# Wave 15 routers (define OWN prefix internally)
app.include_router(art_patterns_router, tags=["Art Studio", "Patterns"])
# ↑ Router has /api/art/patterns prefix defined internally

# Wave 20 routers (explicit prefix) ← RECOMMENDED
app.include_router(art_feasibility_router, prefix="/api/art", tags=["Art Studio", "Feasibility"])
app.include_router(art_snapshot_router, prefix="/api/art", tags=["Art Studio", "Snapshots v2"])

# Legacy pattern (avoid for new routers)
app.include_router(art_studio_rosette_router, prefix="/api", tags=["Rosette", "Art Studio"])
```

### Recommended Convention

**Use:** `prefix="/api/art"` (matches Wave 20 pattern)

```python
from .art_studio.api.prompt_to_svg_routes import router as prompt_to_svg_router

app.include_router(
    prompt_to_svg_router,
    prefix="/api/art",
    tags=["Art Studio", "AI Generation"]
)
```

### Resulting Endpoints

- `POST /api/art/prompt-to-svg`
- `POST /api/art/prompt-to-svg/attach-to-run` (optional convenience)
- `GET /api/art/assets/{asset_id}` (asset index lookup)

---

## 5. OpenAI Image Model Configuration

### Location
`app/ai/transport/image_client.py`

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (uses defaults if not set)
# No specific OPENAI_IMAGE_MODEL env var
```

### Default Configuration

```python
class ImageConfig:
    provider: ImageProvider = ImageProvider.OPENAI
    default_model: str = "dall-e-3"  # Set automatically for OPENAI provider
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
```

### Supported Parameters

```python
def generate(
    prompt: str,
    size: str = "1024x1024",    # Supported: 1024x1024, 1792x1024, 1024x1792
    quality: str = "standard",   # "standard" or "hd"
    model: Optional[str] = None, # Defaults to "dall-e-3"
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
) -> ImageResponse
```

### Usage Pattern

```python
from app.ai.transport import get_image_client, ImageProvider

# Get client (singleton pattern)
client = get_image_client(provider="openai")  # or "stub" for testing

# Generate image
response = client.generate(
    prompt="A intricate rosette pattern for guitar soundhole",
    model="dall-e-3",
    size="1024x1024",
    quality="standard"
)

# Extract results
image_bytes = response.image_bytes      # Raw PNG/JPEG bytes
revised_prompt = response.revised_prompt # Provider may rewrite prompt
seed = response.seed                     # For reproducibility
metadata = response.metadata            # Additional provider info
```

### ImageResponse Schema

```python
@dataclass
class ImageResponse:
    image_bytes: bytes
    model: str
    size: str
    revised_prompt: Optional[str] = None  # Important for provenance!
    seed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 6. Import Paths for Code Bundle

### Core Imports

```python
# Attachments (runs_v2)
from app.rmos.runs_v2.attachments import (
    put_text_attachment,
    put_json_attachment,
    put_bytes_attachment,
    get_attachment_path,
)
from app.rmos.runs_v2.schemas import RunAttachment, RunArtifact

# Store (for run linking and reading)
from app.rmos.runs_v2.store import get_run

# AI Transport
from app.ai.transport import (
    get_image_client,
    ImageProvider,
    ImageResponse,
    ImageClientError,
)

# Workflow sessions (optional linkage)
from app.workflow.sessions.schemas import WorkflowSessionResponse
```

### Safety & Observability Imports (TO VERIFY)

```python
# These paths need verification - may not exist yet
from app.ai.safety import assert_allowed, SafetyCategory
from app.ai.observability import get_request_id
```

**Action Required:** Verify these modules exist. If not, implement safety checks inline or skip for MVP.

---

## 7. Proposed File Structure

### New Files to Create

```
services/api/app/
├── art_studio/
│   ├── __init__.py
│   ├── ai/
│   │   ├── __init__.py
│   │   └── prompt_to_svg_service.py  # NEW: Core business logic
│   ├── assets/
│   │   ├── __init__.py
│   │   ├── schemas.py                 # NEW: ArtAsset, ArtAssetRef models
│   │   └── store.py                   # NEW: Asset index (lightweight)
│   └── api/
│       ├── __init__.py
│       └── prompt_to_svg_routes.py    # NEW: HTTP endpoints
```

### Files to Modify

```
services/api/app/
└── main.py  # ADD: Import and mount new router
```

---

## 8. Service Implementation Pattern

### prompt_to_svg_service.py

```python
"""
Art Studio AI - Prompt to SVG Service

Generates SVG variants from user prompts using AI image generation.
Stores results as runs_v2 attachments with Art Studio asset index.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any, Tuple
import time
import hashlib

from app.ai.transport import get_image_client, ImageProvider
from app.rmos.runs_v2.attachments import put_text_attachment, put_json_attachment
from app.rmos.runs_v2.schemas import RunAttachment


def generate_svg_variants(
    prompt: str,
    count: int = 1,
    variant_seed: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
    style_hints: Optional[Dict[str, Any]] = None,
    provider: str = "openai",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate SVG variants from prompt.
    
    Args:
        prompt: User creativity source
        count: Number of variants (>1 returns list)
        variant_seed: Stable regeneration seed
        constraints: CNC-friendly constraints
        style_hints: Rosette/inlay/ornament tags
        provider: "openai", "stub", etc.
        request_id: Correlation ID for audit
        
    Returns:
        Dict with:
        - variant_seed: str
        - variants: List[{svg, variant_sha256, attachment_sha256, warnings}]
        - revised_prompt: Optional[str]
        - compute_ms: float
    """
    t0 = time.perf_counter()
    
    # Implementation goes here
    # ...
    
    compute_ms = (time.perf_counter() - t0) * 1000
    
    return {
        "variant_seed": variant_seed,
        "variants": variants,
        "revised_prompt": revised_prompt,
        "compute_ms": compute_ms,
    }
```

---

## 9. Router Implementation Pattern

### prompt_to_svg_routes.py

```python
"""
Art Studio AI - Prompt to SVG Routes

HTTP endpoints for generating SVG variants from prompts.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

from app.art_studio.ai.prompt_to_svg_service import generate_svg_variants


router = APIRouter()


class PromptToSvgRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    count: int = Field(default=1, ge=1, le=4)
    variant_seed: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    style_hints: Optional[Dict[str, Any]] = None
    workflow_session_id: Optional[str] = None
    run_id: Optional[str] = None
    provider: Literal["openai", "stub"] = "openai"


class SvgVariant(BaseModel):
    svg: str
    variant_sha256: str
    attachment_sha256: str
    warnings: List[str] = Field(default_factory=list)


class PromptToSvgResponse(BaseModel):
    request_id: str
    variant_seed: str
    variants: List[SvgVariant]
    asset_ids: List[str]
    run_id: Optional[str] = None
    revised_prompt: Optional[str] = None
    compute_ms: float


@router.post("/prompt-to-svg", response_model=PromptToSvgResponse)
async def prompt_to_svg(
    body: PromptToSvgRequest,
    request: Request,
) -> PromptToSvgResponse:
    """Generate SVG variants from prompt."""
    request_id = request.state.request_id or request.headers.get("x-request-id")
    
    # Call service
    result = generate_svg_variants(
        prompt=body.prompt,
        count=body.count,
        variant_seed=body.variant_seed,
        constraints=body.constraints,
        style_hints=body.style_hints,
        provider=body.provider,
        request_id=request_id,
    )
    
    # Build response
    return PromptToSvgResponse(
        request_id=request_id,
        variant_seed=result["variant_seed"],
        variants=result["variants"],
        asset_ids=result.get("asset_ids", []),
        run_id=body.run_id,
        revised_prompt=result.get("revised_prompt"),
        compute_ms=result["compute_ms"],
    )
```

---

## 10. Router Mount in main.py

### Location to Add

Add in the **Wave 20 section** or create **Wave 21 section**:

```python
# =============================================================================
# WAVE 21: ART STUDIO AI GENERATION (1 router)
# =============================================================================
try:
    from .art_studio.api.prompt_to_svg_routes import router as prompt_to_svg_router
except ImportError as e:
    print(f"Warning: Art Studio AI Generation router not available: {e}")
    prompt_to_svg_router = None

# ... later in the app.include_router section ...

# Wave 21: Art Studio AI Generation (1)
if prompt_to_svg_router:
    app.include_router(
        prompt_to_svg_router,
        prefix="/api/art",
        tags=["Art Studio", "AI Generation"]
    )
```

---

## 11. Asset Index Schema (Lightweight)

### assets/schemas.py

```python
"""Art Studio Asset Index Schemas"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from datetime import datetime

class ArtAssetKind(str):
    SVG = "svg"
    GEOMETRY_SPEC = "geometry_spec"
    AI_PROVENANCE = "ai_provenance"

class ArtAssetRef(BaseModel):
    """Reference to a content-addressed attachment."""
    attachment_sha256: str
    kind: str
    filename: str
    size_bytes: int

class ArtAsset(BaseModel):
    """Lightweight asset index entry."""
    asset_id: str
    created_at_utc: datetime
    kind: str
    attachment_sha256: str  # Primary reference
    variant_seed: Optional[str] = None
    request_id: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
```

---

## 12. Testing Checklist

### Unit Tests
- [ ] `generate_svg_variants()` with stub provider
- [ ] Attachment storage and retrieval
- [ ] Asset index CRUD operations
- [ ] Variant seed reproducibility

### Integration Tests
- [ ] End-to-end POST `/api/art/prompt-to-svg`
- [ ] Verify attachment deduplication
- [ ] Verify provenance fields populated
- [ ] Verify revised_prompt captured

### Manual Testing
```bash
# Start server
cd services/api
uvicorn app.main:app --reload

# Test endpoint
curl http://localhost:8000/api/art/prompt-to-svg \
  -X POST \
  -H "Content-Type: application/json" \
  -H "x-request-id: test-req-001" \
  -d '{
    "prompt": "An intricate rosette pattern",
    "count": 2,
    "provider": "stub"
  }'
```

---

## 13. Known Issues & Decisions

### Safety Module
- **Status:** Import paths for `app.ai.safety` need verification
- **Decision:** Implement inline safety checks for MVP if module doesn't exist

### Observability Module
- **Status:** Import paths for `app.ai.observability` need verification  
- **Decision:** Use direct `request.state.request_id` access for MVP

### Workflow Session Linkage
- **Status:** Field marked as `[LEGACY]` but functional
- **Decision:** Support for MVP, plan migration path in future

### Asset Index Storage
- **Status:** No SQLite/DB implementation yet
- **Decision:** Use filesystem JSON store for MVP (matches runs_v2 pattern)

---

## 14. Next Steps

1. **Verify missing imports:**
   - Check if `app.ai.safety` exists
   - Check if `app.ai.observability` exists
   - Create stubs if needed

2. **Create directory structure:**
   ```bash
   mkdir -p services/api/app/art_studio/ai
   mkdir -p services/api/app/art_studio/assets
   mkdir -p services/api/app/art_studio/api
   ```

3. **Implement core files** in order:
   1. `art_studio/assets/schemas.py`
   2. `art_studio/assets/store.py`
   3. `art_studio/ai/prompt_to_svg_service.py`
   4. `art_studio/api/prompt_to_svg_routes.py`
   5. Modify `main.py` to mount router

4. **Test with stub provider** first

5. **Enable OpenAI provider** once stub tests pass

---

## 15. Key Architectural Principles

### Hybrid Storage
- **Binary content** → `runs_v2/attachments` (content-addressed, deduplicated)
- **Metadata index** → `art_studio/assets` (lightweight references)
- **Provenance** → `RunArtifact.meta` + `request_id`

### Separation of Concerns
- **Transport layer** (`ai.transport`) → HTTP/SDK clients only
- **Service layer** (`art_studio.ai`) → Business logic
- **Router layer** (`art_studio.api`) → HTTP surface
- **Storage layer** (`rmos.runs_v2`, `art_studio.assets`) → Persistence

### No Experimental Code
- All code goes in production paths
- No `_experimental/` directory usage
- No engine registry pattern

---

## Appendix A: Key File Locations

| Component | File Path |
|-----------|-----------|
| Attachments API | `app/rmos/runs_v2/attachments.py` |
| Run Schemas | `app/rmos/runs_v2/schemas.py` |
| Run Store | `app/rmos/runs_v2/store.py` |
| Image Client | `app/ai/transport/image_client.py` |
| Transport Exports | `app/ai/transport/__init__.py` |
| Workflow Sessions | `app/workflow/sessions/schemas.py` |
| Main App | `app/main.py` |

---

## Appendix B: Function Reference Quick Lookup

### Read a Run Artifact
```python
from app.rmos.runs_v2.store import get_run
run = get_run(run_id: str) -> Optional[RunArtifact]
```

### Store SVG as Attachment
```python
from app.rmos.runs_v2.attachments import put_text_attachment
attachment, path = put_text_attachment(
    text=svg_string,
    kind="geometry_svg",
    mime="image/svg+xml",
    filename="variant_1.svg",
    ext=".svg"
)
```

### Generate Image via AI
```python
from app.ai.transport import get_image_client
client = get_image_client(provider="openai")
response = client.generate(prompt="...", size="1024x1024")
image_bytes = response.image_bytes
```

---

## ADDENDUM: Critical Design Decisions (Required Before Implementation)

The following questions **must be answered explicitly** before code generation. These are not criticisms—they are architectural clarity checkpoints.

---

### Decision 1: Vectorization Pipeline Architecture

**Question:** Is SVG generation:
- **(A) Direct** - LLM produces SVG text (e.g., GPT-4 with SVG grammar prompt)
- **(B) Indirect** - Image (DALL-E) → Vectorization → SVG

**Current State:**
- OpenAI image client returns **raster bytes only** (PNG/JPEG via DALL-E)
- No vectorization module exists in codebase
- Guide examples assume SVG strings exist

**DECISION REQUIRED:**

```
[ ] Option A: Direct LLM → SVG
    Requires: LLM client with SVG-specific prompt engineering
    Pros: Native vector output, smaller files
    Cons: Less artistic variety, may hallucinate invalid SVG
    Location: Use existing app/ai/transport/llm_client.py
    
[ ] Option B: DALL-E → Vectorization → SVG
    Requires: New vectorization module (Potrace, Inkscape CLI, etc.)
    Pros: Rich artistic output, proven image quality
    Cons: Additional processing step, quality depends on vectorizer
    Location: Create app/art_studio/vectorize/
    
[ ] Option C: Hybrid (Both A and B, selectable via provider)
    Requires: Both implementations
    Pros: Flexibility, future-proof
    Cons: More code, more testing
```

**Recommendation:** If prompt is for **artistic creativity**, use **Option B** (DALL-E + vectorization).  
If prompt is for **geometric patterns**, use **Option A** (direct LLM).

**Implementation Impact:**
```python
# Option A (Direct LLM)
from app.ai.transport import get_llm_client
client = get_llm_client(provider="openai")
response = client.generate_json(prompt=svg_prompt, model="gpt-4")
svg_string = response.content  # Already SVG

# Option B (DALL-E + Vectorization)
from app.ai.transport import get_image_client
from app.art_studio.vectorize import raster_to_svg
client = get_image_client(provider="openai")
image_response = client.generate(prompt=prompt)
svg_string = raster_to_svg(image_response.image_bytes, method="potrace")
```

**Files to Create (if Option B):**
- `app/art_studio/vectorize/__init__.py`
- `app/art_studio/vectorize/potrace_adapter.py`
- `app/art_studio/vectorize/inkscape_adapter.py`

---

### Decision 2: Safety Enforcement Philosophy

**Question:** For user creativity prompts, is safety:
- **Hard-block** (raise HTTPException 400 on violation)
- **Soft-warn** (annotate provenance, allow generation)

**Current Philosophy:**
> "The user prompt is the source of creativity."

**DECISION REQUIRED:**

```
[✓] Soft Enforcement (RECOMMENDED)
    - Capture warnings in variants[].warnings
    - Store flags in RunArtifact.meta["safety_flags"]
    - Let user proceed with informed consent
    - Example: "Prompt contains 'guitar' → may include copyrighted designs"
    
[ ] Hard Enforcement
    - Block generation if safety flags triggered
    - Return 400 with explanation
    - Example: NSFW content, copyright violations
```

**Implementation Pattern (Soft Enforcement):**

```python
def generate_svg_variants(...) -> Dict[str, Any]:
    # Check safety (non-blocking)
    safety_flags = []
    try:
        # If app.ai.safety exists
        from app.ai.safety import check_prompt_safety
        safety_result = check_prompt_safety(prompt, category="IMAGE_GENERATION")
        safety_flags = safety_result.get("warnings", [])
    except ImportError:
        # Safety module doesn't exist yet - skip for MVP
        pass
    
    # Generate anyway, but annotate
    variants = []
    for i in range(count):
        variant = generate_single_variant(...)
        variant["warnings"].extend(safety_flags)
        variants.append(variant)
    
    # Store in provenance
    meta = {
        "safety_flags": safety_flags,
        "safety_enforcement": "SOFT_WARN",
    }
    
    return {"variants": variants, "meta": meta}
```

**Provenance Tracking:**
```python
RunArtifact.meta = {
    "safety_flags": ["prompt_contains_brand_names"],
    "safety_enforcement": "SOFT_WARN",
    "user_acknowledged": False,  # UI can flip to True
}
```

---

### Decision 3: Asset Index Store Scope & Lifetime

**Question:** Is the Art Asset Index:
- **Global** (all users, one namespace)
- **User-scoped** (per user_id)
- **Session-scoped** (per workflow_session_id)

**Question:** Is `asset_id`:
- **Random UUID** (e.g., `asset_abc123`)
- **Deterministic hash** (e.g., first 12 chars of attachment SHA)

**DECISION REQUIRED:**

```
Scope:
[✓] Global (RECOMMENDED for MVP)
    - Simple filesystem: data/art_assets/{asset_id}.json
    - No auth/isolation needed initially
    - Matches runs_v2 pattern
    
[ ] User-scoped
    - Filesystem: data/art_assets/{user_id}/{asset_id}.json
    - Requires auth/user extraction
    
[ ] Session-scoped
    - Tied to workflow_session_id lifecycle
    - Auto-cleanup when session deleted

ID Strategy:
[✓] Deterministic Hash (RECOMMENDED)
    - asset_id = f"asset_{attachment_sha256[:12]}"
    - Natural deduplication
    - Idempotent creation
    
[ ] Random UUID
    - asset_id = f"asset_{uuid4().hex[:12]}"
    - Unique per creation
    - Allows multiple assets for same attachment
```

**Implementation (Deterministic Hash):**

```python
def create_asset(attachment: RunAttachment, variant_seed: str, meta: Dict) -> str:
    # Deterministic ID from attachment SHA
    asset_id = f"asset_{attachment.sha256[:12]}"
    
    # Check if exists (idempotent)
    if asset_exists(asset_id):
        return asset_id
    
    # Create asset entry
    asset = ArtAsset(
        asset_id=asset_id,
        attachment_sha256=attachment.sha256,
        variant_seed=variant_seed,
        meta=meta,
    )
    
    store_asset(asset)
    return asset_id
```

**Cleanup Strategy:**
- **Deterministic hash:** Assets auto-deduplicate, no explicit cleanup needed
- **Random UUID:** Need TTL or session-based cleanup

---

### Decision 4: Run Attachment Linking Ownership

**Question:** If `run_id` is provided in the request, should the service:
- **Mutate the run** (append attachments to existing RunArtifact)
- **Return SHAs only** (caller is responsible for linking)

**DECISION REQUIRED:**

```
[✓] Return SHAs Only (RECOMMENDED)
    - Service returns: attachment_sha256, asset_id
    - Caller decides whether to create/update run
    - Clear ownership: Art Studio generates, RMOS persists
    - Example: POST /api/art/prompt-to-svg returns data, 
              then POST /api/rmos/runs with attachments
    
[ ] Mutate Existing Run
    - Service calls get_run(run_id)
    - Appends attachments to run.advisory_inputs
    - Calls store.put(run)
    - Tighter coupling between Art Studio and RMOS
```

**Implementation (Return SHAs Only):**

```python
@router.post("/prompt-to-svg")
async def prompt_to_svg(body: PromptToSvgRequest) -> PromptToSvgResponse:
    # Generate variants
    result = generate_svg_variants(...)
    
    # Return attachment SHAs - do NOT mutate run
    return PromptToSvgResponse(
        variants=result["variants"],  # Each has attachment_sha256
        asset_ids=result["asset_ids"],
        run_id=None,  # Run not created here
    )

# Separate endpoint for run persistence (optional convenience)
@router.post("/prompt-to-svg/attach-to-run")
async def attach_to_run(
    asset_ids: List[str],
    run_id: str,
) -> Dict[str, Any]:
    """Convenience endpoint to link existing assets to a run."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    
    # Append asset references
    for asset_id in asset_ids:
        asset = get_asset(asset_id)
        run.advisory_inputs.append(
            AdvisoryInputRef(
                advisory_id=asset.attachment_sha256,
                kind="geometry_svg",
            )
        )
    
    # Save (this mutates, but with explicit user intent)
    store.put(run)
    return {"status": "ok", "run_id": run_id}
```

**Ownership Boundary:**
- **Art Studio:** Generates SVGs, stores attachments, creates asset index
- **RMOS:** Persists runs, links attachments to run provenance
- **Caller (UI/orchestrator):** Decides when to create/link runs

---

### Decision 5: Variant Seed Determinism Guarantees

**Question:** What does "stable regeneration" via `variant_seed` guarantee?

**DECISION REQUIRED:**

```
variant_seed guarantees:
[✓] Same provider (e.g., "openai")
[✓] Same model (e.g., "dall-e-3")
[✓] Same prompt
[✓] Same constraints (if provided)
[✓] Same count

[✗] NO guarantee across:
    - Provider model upgrades (dall-e-3 → dall-e-4)
    - Provider API changes
    - Vectorization algorithm changes
    - Random provider behavior (DALL-E revised_prompt)
```

**Implementation (Explicit Contract):**

```python
def generate_svg_variants(
    prompt: str,
    variant_seed: Optional[str] = None,
    ...
) -> Dict[str, Any]:
    """
    Generate SVG variants with optional deterministic seeding.
    
    Variant Seed Guarantees:
    - If variant_seed provided, will attempt to reproduce results
    - Determinism depends on:
      ✓ Provider (must be same)
      ✓ Model version (must be same)
      ✓ Constraints (must be same)
      ✗ Provider may still introduce randomness (e.g., revised_prompt)
    
    Best-effort determinism, not cryptographic guarantee.
    """
    if variant_seed is None:
        # Generate new seed
        variant_seed = hashlib.sha256(
            f"{prompt}:{time.time()}".encode()
        ).hexdigest()[:16]
    
    # Use seed to derive per-variant seeds
    variant_seeds = [
        int(hashlib.sha256(f"{variant_seed}:{i}".encode()).hexdigest()[:8], 16)
        for i in range(count)
    ]
    
    # Pass seed to provider (best-effort)
    for i, seed in enumerate(variant_seeds):
        response = client.generate(prompt=prompt, seed=seed, ...)
        # Note: Provider may ignore seed or apply differently
```

**Documentation in Response:**

```python
class PromptToSvgResponse(BaseModel):
    variant_seed: str = Field(
        ...,
        description=(
            "Seed for variant generation. "
            "Reusing this seed with identical parameters should produce "
            "similar results, but absolute determinism is not guaranteed "
            "due to provider API behavior."
        )
    )
```

---

### Decision 6: Failure Modes & Partial Success Handling

**Question:** If generating multiple variants and one fails (timeout, vectorization crash), should the endpoint:
- **Fail entirely** (HTTP 500, rollback)
- **Return partial success** (HTTP 200, include failure metadata)

**DECISION REQUIRED:**

```
[✓] Partial Success (RECOMMENDED)
    - Return HTTP 200
    - Include successful variants
    - Include failed variants with error details
    - Matches governance philosophy: "capture what succeeded"
    
[ ] Fail Entirely
    - Return HTTP 500
    - No partial results
    - User must retry entire batch
```

**Implementation (Partial Success):**

```python
def generate_svg_variants(...) -> Dict[str, Any]:
    variants = []
    
    for i in range(count):
        try:
            # Generate single variant
            svg_string = generate_single_variant(...)
            
            # Store as attachment
            attachment, path = put_text_attachment(
                text=svg_string,
                kind="geometry_svg",
                mime="image/svg+xml",
                filename=f"variant_{i}.svg",
                ext=".svg",
            )
            
            variants.append({
                "svg": svg_string,
                "variant_sha256": hashlib.sha256(svg_string.encode()).hexdigest(),
                "attachment_sha256": attachment.sha256,
                "warnings": [],
                "status": "OK",
            })
            
        except Exception as e:
            # Capture failure, continue with others
            logger.error(f"Variant {i} failed: {e}")
            variants.append({
                "svg": None,
                "variant_sha256": None,
                "attachment_sha256": None,
                "warnings": [f"Generation failed: {str(e)}"],
                "status": "ERROR",
                "error_details": {
                    "type": type(e).__name__,
                    "message": str(e),
                },
            })
    
    # Return partial success
    success_count = sum(1 for v in variants if v["status"] == "OK")
    
    return {
        "variants": variants,
        "success_count": success_count,
        "failure_count": count - success_count,
    }
```

**Response Schema Update:**

```python
class SvgVariant(BaseModel):
    svg: Optional[str]  # None if failed
    variant_sha256: Optional[str]
    attachment_sha256: Optional[str]
    warnings: List[str]
    status: Literal["OK", "ERROR"]
    error_details: Optional[Dict[str, Any]] = None

class PromptToSvgResponse(BaseModel):
    # ... existing fields ...
    success_count: int
    failure_count: int
```

**Provenance Capture:**

```python
RunArtifact.meta = {
    "requested_variants": 4,
    "successful_variants": 3,
    "failed_variants": 1,
    "failure_reasons": ["Variant 2: Vectorization timeout"],
}
```

---

## Non-Goals (Explicitly Out of Scope)

This service **does NOT**:

- ❌ Decide artistic intent (prompt is user creativity source)
- ❌ Optimize CNC feasibility (that's RMOS Feasibility Scorer's job)
- ❌ Validate manufacturability (that's CAM layer's responsibility)
- ❌ Generate CAM toolpaths (use separate toolpath endpoints)
- ❌ Manage user authentication/authorization (assumes trusted caller)
- ❌ Provide real-time preview (variants generated synchronously)
- ❌ Perform style transfer or image editing (single-shot generation only)

**What it DOES do:**
- ✅ Generate SVG variants from text prompts
- ✅ Store results as content-addressed attachments
- ✅ Maintain lightweight asset index for discovery
- ✅ Capture provenance (request_id, seed, revised_prompt)
- ✅ Support stable regeneration via variant_seed
- ✅ Handle partial failures gracefully

---

## Implementation Readiness Checklist

Before writing code, verify these decisions are documented:

- [ ] **Decision 1:** Vectorization pipeline (A, B, or C) chosen
- [ ] **Decision 2:** Safety enforcement mode (hard/soft) chosen
- [ ] **Decision 3:** Asset index scope (global/user/session) chosen
- [ ] **Decision 3:** Asset ID strategy (UUID/hash) chosen
- [ ] **Decision 4:** Run linking ownership (mutate/return-only) chosen
- [ ] **Decision 5:** Variant seed guarantees documented
- [ ] **Decision 6:** Partial success handling confirmed
- [ ] **Non-goals** section reviewed and agreed

Once all checkboxes are marked, **hand this document to the developer** with zero ambiguity.

---

**End of Integration Guide**
