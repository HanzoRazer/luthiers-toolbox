
● RMOS Acoustics H7.2.2.1 Implementation Report

  Developer Integration Guide

  Date: 2025-12-31
  Scope: Unified signing, attachment meta index, typed schemas, no-path disclosure
  Prefix: /api/rmos/acoustics

  ---
  1. Architecture Overview

  1.1 Module Layout

  services/api/app/rmos/
  ├── acoustics/                      # Wave 21: Import/Query/Export
  │   ├── router.py                   # Composite router (import + query + zip_export)
  │   ├── router_import.py            # POST /import-zip, POST /import-path
  │   ├── router_query.py             # GET /index, GET /runs/{run_id}
  │   ├── router_zip_export.py        # POST /runs/{run_id}/attachments/zip
  │   ├── persist_glue.py             # Import persistence + meta index hook
  │   ├── signed_urls.py              # LEGACY: ZIP export signing (deprecated)
  │   └── ...
  │
  └── runs_v2/                        # Wave 22: H7.2.2.1 Advisory Surface
      ├── acoustics_router.py         # Authoritative attachment router
      ├── acoustics_schemas.py        # NEW: Pydantic response models
      ├── signed_urls.py              # AUTHORITATIVE: Unified signing module
      ├── attachment_meta.py          # Global sha256→meta index
      ├── attachments.py              # Content-addressed blob storage
      └── store.py                    # RunStoreV2 abstraction

  1.2 Request Flow

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                              CLIENT REQUEST                                  │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  main.py                                                                     │
  │  ├── Wave 21: prefix="/api/rmos/acoustics" (import, query, zip_export)      │
  │  └── Wave 22: prefix="/api/rmos/acoustics" (H7.2.2.1 attachments/advisories)│
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                      ┌─────────────────┴─────────────────┐
                      ▼                                   ▼
          ┌───────────────────────┐           ┌───────────────────────┐
          │  acoustics/router.py  │           │ runs_v2/acoustics_    │
          │  (Wave 21)            │           │ router.py (Wave 22)   │
          │                       │           │                       │
          │  • /import-zip        │           │  • /attachments/{sha} │
          │  • /import-path       │           │  • /runs/{id}/attach  │
          │  • /index             │           │  • /advisories/{id}   │
          │  • /runs/{id}         │           │  • /index/rebuild_*   │
          │  • /runs/{id}/.../zip │           │  • /*/signed_url      │
          └───────────────────────┘           └───────────────────────┘
                      │                                   │
                      ▼                                   ▼
          ┌───────────────────────┐           ┌───────────────────────┐
          │  persist_glue.py      │           │  attachment_meta.py   │
          │  ─────────────────    │           │  signed_urls.py       │
          │  Calls meta index     │◀─────────▶│  attachments.py       │
          │  update on import     │           │  store.py             │
          └───────────────────────┘           └───────────────────────┘

  ---
  2. Signing Module

  2.1 Environment Variables

  | Variable                           | Purpose                    | Required              |
  |------------------------------------|----------------------------|-----------------------|
  | RMOS_SIGNED_URL_SECRET             | Primary signing secret     | Yes (for signed URLs) |
  | RMOS_ACOUSTICS_SIGNING_SECRET      | Legacy fallback            | No (deprecated)       |
  | RMOS_ACOUSTICS_SIGNING_TTL_SECONDS | Default TTL for ZIP export | No (default: 300)     |
  | RMOS_ACOUSTICS_SIGNING_BIND_IP     | IP binding for ZIP tokens  | No (default: "0")     |

  2.2 Hierarchical Scopes

  # runs_v2/signed_urls.py

  Scope = Literal["download", "head"]

  SCOPE_HIERARCHY = {
      "download": {"download", "head"},  # download token works for both
      "head": {"head"},                   # head token only works for head
  }

  Usage:
  from app.rmos.runs_v2.signed_urls import (
      make_signed_query,
      verify_attachment_request,
      Scope,
  )

  # Mint a download-scoped token (works for GET and HEAD)
  params = make_signed_query(
      method="GET",
      path="/api/rmos/acoustics/attachments/abc123...",
      sha256="abc123...",
      scope="download",  # or "head"
      ttl_seconds=300,
  )
  # Returns: SignedUrlParams(expires, sig, scope, download, filename)

  # Verify with scope hierarchy
  ok = verify_attachment_request(
      method="HEAD",
      path="/api/rmos/acoustics/attachments/abc123...",
      sha256="abc123...",
      expires=params.expires,
      sig=params.sig,
      scope="download",       # Token was signed with download scope
      required_scope="head",  # But we only need head access → PASSES
  )

  2.3 Canonical Signature Format

  METHOD\n
  PATH\n
  EXPIRES\n
  SHA256\n
  SCOPE\n
  DOWNLOAD(0/1)\n
  FILENAME

  Example payload:
  GET
  /api/rmos/acoustics/attachments/abcd1234...
  1735689600
  abcd1234...
  download
  1
  recording.wav

  2.4 Query String Format

  ?expires=1735689600&sig=BASE64URL&scope=download&download=true&filename=recording.wav

  ---
  3. Pydantic Response Schemas

  3.1 Import Location

  from app.rmos.runs_v2.acoustics_schemas import (
      AttachmentMetaPublic,
      RunAttachmentsListOut,
      AttachmentExistsOut,
      SignedUrlMintOut,
      RunAdvisoriesListOut,
      AdvisorySummary,
      IndexRebuildOut,
      AttachmentHeadOut,        # For documentation only (HEAD returns headers)
      AdvisoryResolveOut,
      AttachmentMetaIndexEntry,
  )

  3.2 Schema Reference

  AttachmentMetaPublic

  class AttachmentMetaPublic(BaseModel):
      sha256: str                           # Content hash (primary key)
      kind: Optional[str]                   # "manifest", "audio", "advisory", etc.
      mime: Optional[str]                   # MIME type
      filename: Optional[str]               # Display filename
      size_bytes: Optional[int]             # File size
      created_at_utc: Optional[str]         # ISO timestamp
      download_url: Optional[str]           # Relative URL (when include_urls=True)
      signed_url: Optional[str]             # Signed URL (when requested)
      data_b64: Optional[str]               # Base64 content (when include_bytes=True)
      omitted_reason: Optional[str]         # "too_large", "missing", "read_failed"

  RunAttachmentsListOut

  class RunAttachmentsListOut(BaseModel):
      run_id: str
      count: int
      include_bytes: bool
      max_inline_bytes: int
      attachments: List[AttachmentMetaPublic]

  AttachmentExistsOut

  class AttachmentExistsOut(BaseModel):
      sha256: str
      in_index: bool                        # Exists in _attachment_meta.json
      in_store: bool                        # Blob exists on disk
      size_bytes: Optional[int]             # From disk stat (if in_store)
      # Extended fields when in_index=True:
      index_kind: Optional[str]
      index_mime: Optional[str]
      index_filename: Optional[str]
      index_size_bytes: Optional[int]

  SignedUrlMintOut

  class SignedUrlMintOut(BaseModel):
      sha256: str
      method: str                           # "GET" or "HEAD"
      scope: Literal["download", "head"]
      expires: int                          # Unix timestamp
      signed_url: str                       # Relative signed URL

  IndexRebuildOut

  class IndexRebuildOut(BaseModel):
      ok: bool
      runs_scanned: int
      attachments_indexed: int
      unique_sha256: int

  ---
  4. Attachment Meta Index

  4.1 File Location

  {RMOS_RUNS_ROOT}/_attachment_meta.json

  Default: services/api/data/runs_v2/_attachment_meta.json

  4.2 Schema

  {
    "abcdef1234...": {
      "sha256": "abcdef1234...",
      "kind": "manifest",
      "mime": "application/json",
      "filename": "manifest.json",
      "size_bytes": 1234,
      "created_at_utc": "2025-12-31T12:00:00Z",
      "first_seen_run_id": "run-001",
      "last_seen_run_id": "run-005",
      "first_seen_at_utc": "2025-12-30T10:00:00Z",
      "last_seen_at_utc": "2025-12-31T12:00:00Z",
      "ref_count": 5
    }
  }

  4.3 API Usage

  from app.rmos.runs_v2.attachment_meta import AttachmentMetaIndex
  from pathlib import Path

  # Initialize
  idx = AttachmentMetaIndex(Path("/path/to/runs_v2"))

  # Lookup
  meta = idx.get("abcdef1234...")
  if meta:
      print(meta["kind"], meta["filename"])

  # Rebuild from all run artifacts
  stats = idx.rebuild_from_run_artifacts()
  # Returns: {"runs_scanned": 100, "attachments_indexed": 500, "unique_sha256": 450}

  # Incremental update (called automatically on import)
  from app.rmos.runs_v2.schemas import RunArtifact
  idx.update_from_artifact(artifact)

  4.4 Incremental Update Hook

  The import flow automatically updates the meta index:

  # persist_glue.py:224
  def persist_import_plan(...) -> PersistResult:
      ...
      # Update _index.json (best effort)
      index_updated = _update_index(...)

      # Update _attachment_meta.json (Decision B: incremental on every import)
      _update_attachment_meta_index(runs_root=runs_root, run_obj=run_obj)

      return PersistResult(...)

  ---
  5. Blob Resolution

  5.1 Storage Layout

  {RMOS_RUN_ATTACHMENTS_DIR}/
  ├── ab/
  │   └── cd/
  │       ├── abcd1234...5678.json
  │       ├── abcd1234...5678.wav
  │       └── abcd9999...0000.gcode
  └── ef/
      └── 01/
          └── ef01...

  5.2 Resolution Function

  from app.rmos.runs_v2.attachments import resolve_attachment_path

  # Tries extensions: "", ".json", ".gcode", ".txt", ".svg", ".dxf"
  path = resolve_attachment_path("abcd1234...")
  if path.exists():
      content = path.read_bytes()

  Decision B Implementation: The resolver globs for {sha}.* to find any extension, with optional fast-path when extension is known from meta index.

  5.3 No-Path-Disclosure Invariant

  CRITICAL: Never return path in API responses. Use these internal-only functions:

  # INTERNAL ONLY - do not expose
  from app.rmos.runs_v2.attachments import (
      resolve_attachment_path,  # Returns Path - internal only
      attachment_exists,        # Returns bool - safe
      attachment_stat,          # Returns {"sha256", "size_bytes"} - safe (no path)
  )

  ---
  6. Endpoint Reference

  6.1 Wave 22 Endpoints (H7.2.2.1)

  | Method | Path                                   | Response Model        | Description             |
  |--------|----------------------------------------|-----------------------|-------------------------|
  | GET    | /runs/{run_id}/advisories              | RunAdvisoriesListOut  | List advisory summaries |
  | GET    | /advisories/{advisory_id}              | Dict[str, Any]        | Resolve advisory lookup |
  | GET    | /attachments/{sha256}                  | FileResponse          | Stream attachment blob  |
  | HEAD   | /attachments/{sha256}                  | Headers only          | Metadata in headers     |
  | POST   | /attachments/{sha256}/signed_url       | SignedUrlMintOut      | Mint signed URL         |
  | GET    | /runs/{run_id}/attachments             | RunAttachmentsListOut | List with inline bytes  |
  | POST   | /index/rebuild_attachment_meta         | IndexRebuildOut       | Rebuild meta index      |
  | GET    | /index/attachment_meta/{sha256}/exists | AttachmentExistsOut   | Check existence         |

  6.2 Wave 21 Endpoints (Import/Query)

  | Method | Path                           | Description                  |
  |--------|--------------------------------|------------------------------|
  | POST   | /import-zip                    | Upload and import ZIP bundle |
  | POST   | /import-path                   | Import from server-side path |
  | GET    | /index                         | Query runs index             |
  | GET    | /runs/{run_id}                 | Get run artifact JSON        |
  | POST   | /runs/{run_id}/attachments/zip | Export attachments as ZIP    |

  ---
  7. Frontend Integration

  7.1 Minting a Signed URL

  // Step 1: Mint signed URL (requires auth)
  const response = await fetch(
    `/api/rmos/acoustics/attachments/${sha256}/signed_url`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ttl_seconds: 300,
        download: true,
        filename: 'recording.wav',
        method: 'GET',
        scope: 'download',
      }),
    }
  );

  const { signed_url, expires } = await response.json();

  // Step 2: Use signed URL (no auth required)
  window.open(signed_url, '_blank');
  // or
  const blob = await fetch(signed_url).then(r => r.blob());

  7.2 Listing Attachments with Inline Data

  const response = await fetch(
    `/api/rmos/acoustics/runs/${runId}/attachments?include_bytes=true&max_inline_bytes=500000`
  );

  const { attachments } = await response.json();

  for (const att of attachments) {
    if (att.data_b64) {
      // Inline base64 data available
      const bytes = atob(att.data_b64);
    } else if (att.omitted_reason) {
      // Too large or missing - use download_url
      console.log(`Omitted: ${att.omitted_reason}`);
    }
  }

  7.3 Checking Attachment Existence

  const response = await fetch(
    `/api/rmos/acoustics/index/attachment_meta/${sha256}/exists`
  );

  const { in_index, in_store, size_bytes } = await response.json();

  if (in_index && in_store) {
    console.log('Healthy: attachment indexed and blob exists');
  } else if (in_index && !in_store) {
    console.log('Orphaned: index entry but blob missing');
  } else if (!in_index && in_store) {
    console.log('Unindexed: blob exists but not in index');
  } else {
    console.log('Not found');
  }

  ---
  8. Testing

  8.1 Test File Location

  services/api/tests/rmos/test_acoustics_hardening.py

  8.2 Test Classes

  | Class                      | Tests | Coverage                                      |
  |----------------------------|-------|-----------------------------------------------|
  | TestNoPathDisclosure       | 4     | Schema field validation, serialization checks |
  | TestSignatureVerification  | 6     | Valid/expired/wrong sig, scope hierarchy      |
  | TestIndexRebuild           | 2     | Full rebuild, duplicate sha256 handling       |
  | TestBlobExistsTruthTable   | 4     | All (in_index, blob_exists) combinations      |
  | TestIncrementalIndexUpdate | 1     | Hook integration verification                 |

  8.3 Running Tests

  cd services/api
  pytest tests/rmos/test_acoustics_hardening.py -v

  8.4 Key Test Patterns

  # No-path-disclosure: Check for shard patterns
  PATH_PATTERNS = [
      re.compile(r"/[a-zA-Z0-9_/.-]+/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{64}"),
      re.compile(r"[A-Z]:\\[a-zA-Z0-9_\\.-]+\\[a-f0-9]{2}\\[a-f0-9]{2}\\[a-f0-9]{64}"),
  ]

  # Scope hierarchy test
  sig = sign_attachment_request(..., scope="download")
  result = verify_attachment_request(..., scope="download", required_scope="head")
  assert result is True  # download ⊇ head

  ---
  9. Migration Checklist

  9.1 Environment Setup

  # Required for signed URLs
  export RMOS_SIGNED_URL_SECRET="your-secret-key-here"

  # Optional: Legacy compatibility (deprecated)
  export RMOS_ACOUSTICS_SIGNING_SECRET="same-as-above-for-migration"

  9.2 Breaking Changes

  | Change                                     | Migration                                       |
  |--------------------------------------------|-------------------------------------------------|
  | Signature now includes scope               | Old tokens without scope will fail verification |
  | Response shapes are now typed              | Frontend should handle new fields gracefully    |
  | AttachmentExistsOut has new index_* fields | Frontend should check for presence              |

  9.3 Backwards Compatibility

  - Both RMOS_SIGNED_URL_SECRET and RMOS_ACOUSTICS_SIGNING_SECRET are checked
  - ZIP export signing (acoustics/signed_urls.py) continues to work
  - Endpoints return typed models but JSON shape is compatible

  ---
  10. Security Invariants

  10.1 No-Path-Disclosure

  NEVER include in API responses:
  - Absolute filesystem paths
  - Shard directory structure (/ab/cd/abcd...)
  - Environment variable values
  - Internal storage root paths

  10.2 Signature Binding

  Signatures are bound to:
  - HTTP method (GET, HEAD)
  - Full request path (including /api/rmos/acoustics prefix)
  - SHA256 of the attachment
  - Expiry timestamp
  - Scope (download, head)
  - Download flag and filename

  10.3 Scope Enforcement

  # Download scope: Can access both GET and HEAD
  # Head scope: Can only access HEAD

  # Verification checks:
  if required_scope not in SCOPE_HIERARCHY.get(token_scope, set()):
      return False  # Reject

  ---
  11. Doctrine Statement

  Signing is unified across runs_v2: all temporary URLs use a single HMAC scheme with expiry; scopes are hierarchical (download ⊇ head), and signatures are bound to route path + scope to prevent token replay across endpoints.

