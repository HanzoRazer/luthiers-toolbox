# Acoustics API Typed Contracts

> Extracted from live API: 2026-01-17
> Server: http://127.0.0.1:8000
> These are the **actual** response shapes for UI implementation.

---

## 1. Import ZIP

### Endpoint
```
POST /api/rmos/acoustics/import-zip
Content-Type: multipart/form-data
```

### Request
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | **Yes** | ZIP containing `manifest.json` + `attachments/...` |
| `session_id` | string \| null | No | Optional session grouping |
| `batch_label` | string \| null | No | Optional batch label |

### Response: `ImportResponse`
```typescript
interface ImportResponse {
  run_id: string;                    // Created run ID
  run_json_path: string;             // Server path to run JSON
  attachments_written: number;       // New blobs written
  attachments_deduped: number;       // Skipped (already existed)
  index_updated: boolean;            // Whether _attachment_meta.json updated
  mode?: string;                     // Default: "acoustics"
  event_type?: string | null;        // From manifest
  bundle_id?: string | null;         // From manifest
  bundle_sha256?: string | null;     // Hash of entire ZIP
}
```

### Example
```typescript
// Request
const formData = new FormData();
formData.append('file', zipFile);
formData.append('session_id', 'session_abc123');

// Response (200 OK)
{
  "run_id": "run_7a8b9c0d1e2f",
  "run_json_path": "data/runs_v2/2026-01-17/run_7a8b9c0d1e2f.json",
  "attachments_written": 5,
  "attachments_deduped": 2,
  "index_updated": true,
  "mode": "acoustics",
  "event_type": "tap_tone_session",
  "bundle_id": "viewer_pack_20260117",
  "bundle_sha256": "abc123..."
}
```

---

## 2. Browse Attachment Meta

### Endpoint
```
GET /api/rmos/acoustics/index/attachment_meta
```

### Query Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | 20 | Max entries to return |
| `cursor` | string | null | Opaque cursor for pagination |
| `kind` | string | null | Filter by attachment kind |
| `mime_prefix` | string | null | Filter by MIME prefix (e.g., `application/`) |
| `include_urls` | boolean | false | Include `attachment_url` in response |

### Response: `AttachmentMetaBrowseResponse`
```typescript
interface AttachmentMetaBrowseResponse {
  count: number;                     // Entries returned
  total_in_index: number;            // Total matching filter
  limit: number;                     // Requested limit
  kind_filter: string | null;        // Applied kind filter
  mime_prefix_filter: string | null; // Applied MIME filter
  next_cursor: string | null;        // Cursor for next page (null = no more)
  entries: AttachmentMetaEntry[];
}

interface AttachmentMetaEntry {
  sha256: string;                    // Content hash (primary key)
  kind: string;                      // e.g., "manifest", "gcode_output", "viewer_pack"
  mime: string;                      // e.g., "application/json", "text/plain"
  filename: string;                  // Original filename
  size_bytes: number;                // File size
  created_at_utc: string;            // ISO timestamp
  first_seen_run_id: string;         // First run that referenced this
  last_seen_run_id: string;          // Most recent run
  first_seen_at_utc: string;         // When first imported
  last_seen_at_utc: string;          // When last referenced
  ref_count: number;                 // How many runs reference this
  attachment_url?: string;           // Download URL (if include_urls=true)
}
```

### Example
```typescript
// Request
GET /api/rmos/acoustics/index/attachment_meta?limit=2&kind=manifest&include_urls=true

// Response (200 OK)
{
  "count": 2,
  "total_in_index": 30,
  "limit": 2,
  "kind_filter": "manifest",
  "mime_prefix_filter": null,
  "next_cursor": "e6ff9451b8e8d3fb204cd6edba59e6f5d1df9fb844a037121cd92c52b831a62b",
  "entries": [
    {
      "sha256": "fd5bbaa3a6c10f8366620820c29f05c6c833164dea158cc0adeccaf6fc4086ca",
      "kind": "manifest",
      "mime": "application/json",
      "filename": "manifest.json",
      "size_bytes": 642,
      "created_at_utc": "2026-01-15T21:54:20.262564+00:00",
      "first_seen_run_id": "run_4e30cb3ec69940058f6bec47a874c97c",
      "last_seen_run_id": "run_4e30cb3ec69940058f6bec47a874c97c",
      "first_seen_at_utc": "2026-01-15T21:54:20.266415Z",
      "last_seen_at_utc": "2026-01-15T21:54:20.266415Z",
      "ref_count": 1,
      "attachment_url": "/api/rmos/acoustics/attachments/fd5bbaa3a6c10f8366620820c29f05c6c833164dea158cc0adeccaf6fc4086ca"
    }
  ]
}
```

### Cursor Contract
- **Opaque**: Client should treat as pass-through string
- **Stable**: Same cursor returns same next page
- **Value**: Currently uses SHA256 of last entry (implementation detail)

---

## 3. Facets

### Endpoint
```
GET /api/rmos/acoustics/index/attachment_meta/facets
```

### Response: `AttachmentMetaFacetsResponse`
```typescript
interface AttachmentMetaFacetsResponse {
  facets: {
    kind: Record<string, number>;    // kind -> count
    mime: Record<string, number>;    // mime -> count
  };
  total_attachments: number;         // Total in index
  index_version: string;             // Schema version
}
```

### Example
```typescript
// Request
GET /api/rmos/acoustics/index/attachment_meta/facets

// Response (200 OK)
{
  "facets": {
    "kind": {
      "manifest": 42,
      "gcode_output": 38,
      "dxf_input": 30,
      "cam_plan": 25,
      "viewer_pack": 12
    },
    "mime": {
      "application/json": 67,
      "text/plain": 38,
      "application/dxf": 30,
      "application/zip": 12
    }
  },
  "total_attachments": 147,
  "index_version": "attachment_meta_v1"
}
```

### Notes
- Facets are computed from `_attachment_meta.json`
- Returns empty `{}` if index uses different storage location
- Use POST `/rebuild_attachment_meta` to rebuild if empty

---

## 4. Check Attachment Exists

### Endpoint
```
GET /api/rmos/acoustics/index/attachment_meta/{sha256}/exists
```

### Response: `AttachmentExistsResponse`
```typescript
interface AttachmentExistsResponse {
  sha256: string;                    // Requested hash
  in_index: boolean;                 // Exists in _attachment_meta.json
  in_store: boolean;                 // Blob exists on disk
  size_bytes?: number;               // From disk (if in_store)
  index_kind?: string;               // From index (if in_index)
  index_mime?: string;               // From index
  index_filename?: string;           // From index
  index_size_bytes?: number;         // From index
}
```

### Example
```typescript
// Request
GET /api/rmos/acoustics/index/attachment_meta/e9b55f5f.../exists

// Response (200 OK)
{
  "sha256": "e9b55f5f200b7e824269fa8541e4ab47dadc975edbb6a5a3c516296e10ee3242",
  "in_index": true,
  "in_store": true,
  "size_bytes": 17197,
  "index_kind": "dxf_input",
  "index_mime": "application/dxf",
  "index_filename": "mvp_rect_with_island.dxf",
  "index_size_bytes": 17197
}
```

---

## 5. Download Attachment

### Endpoint
```
GET /api/rmos/acoustics/attachments/{sha256}
```

### Response
- **Content-Type**: From stored MIME or `application/octet-stream`
- **Content-Disposition**: `attachment; filename="{original_filename}"`
- **Body**: Raw binary content

### Auth
- Currently: No auth required (direct download)
- Signed URLs: Available but not enforced

---

## 6. Rebuild Index

### Endpoint
```
POST /api/rmos/acoustics/index/rebuild_attachment_meta
```

### Response: `RebuildResponse`
```typescript
interface RebuildResponse {
  ok: boolean;
  runs_scanned: number;              // Total runs examined
  attachments_indexed: number;       // Total attachment refs found
  unique_sha256: number;             // Unique blobs indexed
}
```

### Example
```typescript
// Request
POST /api/rmos/acoustics/index/rebuild_attachment_meta

// Response (200 OK)
{
  "ok": true,
  "runs_scanned": 42,
  "attachments_indexed": 37,
  "unique_sha256": 30
}
```

---

## 7. Recent (Status: Needs Implementation)

### Endpoint
```
GET /api/rmos/acoustics/index/attachment_meta/recent
```

### Current Status
- Route exists but returns 404
- Likely needs `_attachment_recent.json` to be populated

### Expected Response (when working)
```typescript
interface RecentResponse {
  entries: AttachmentMetaEntry[];    // Sorted by created_at_utc DESC
  max_entries: number;               // Configured limit
  built_at_utc: string;              // When index was built
}
```

---

## Answers to Blocking Questions

### 1. Import Request Format
```
Form key: "file" (required)
Optional: "session_id", "batch_label"
Max size: Not specified in schema (check server config)
```

### 2. Viewer Pack Detection
```typescript
// Option A: By kind
entry.kind === 'viewer_pack'

// Option B: By filename
entry.filename.endsWith('.zip')

// Option C: By MIME
entry.mime === 'application/zip'

// Recommended: Use kind if available, fallback to filename
function isViewerPack(entry: AttachmentMetaEntry): boolean {
  return entry.kind === 'viewer_pack' ||
         (entry.mime === 'application/zip' && entry.filename.includes('viewer'));
}
```

### 3. Cursor Contract
```
Type: Opaque string (sha256 of last entry)
Client handling: Pass-through, do not parse
Stability: Stable within same index state
```

### 4. Auth
```
Current: No auth required
Import: No CSRF token required (multipart/form-data)
Downloads: Direct access via sha256
```

### 5. Open Flow
```typescript
// Preferred: Direct URL (no signing required currently)
const downloadUrl = `/api/rmos/acoustics/attachments/${sha256}`;

// If signed URLs required in future:
const signedUrl = await getSignedUrl(sha256, { scope: 'download', ttl: 300 });
```

### 6. Facet Scope
```
Scope: Global (all attachments in _attachment_meta.json)
Filter: Use kind/mime_prefix params on browse to narrow
```

---

## TypeScript Module (Copy-Paste Ready)

```typescript
// packages/client/src/sdk/endpoints/rmosAcoustics.ts

const BASE = '/api/rmos/acoustics';

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

export interface ImportResponse {
  run_id: string;
  run_json_path: string;
  attachments_written: number;
  attachments_deduped: number;
  index_updated: boolean;
  mode?: string;
  event_type?: string | null;
  bundle_id?: string | null;
  bundle_sha256?: string | null;
}

export interface AttachmentMetaEntry {
  sha256: string;
  kind: string;
  mime: string;
  filename: string;
  size_bytes: number;
  created_at_utc: string;
  first_seen_run_id: string;
  last_seen_run_id: string;
  first_seen_at_utc: string;
  last_seen_at_utc: string;
  ref_count: number;
  attachment_url?: string;
}

export interface BrowseResponse {
  count: number;
  total_in_index: number;
  limit: number;
  kind_filter: string | null;
  mime_prefix_filter: string | null;
  next_cursor: string | null;
  entries: AttachmentMetaEntry[];
}

export interface FacetsResponse {
  facets: {
    kind: Record<string, number>;
    mime: Record<string, number>;
  };
  total_attachments: number;
  index_version: string;
}

export interface ExistsResponse {
  sha256: string;
  in_index: boolean;
  in_store: boolean;
  size_bytes?: number;
  index_kind?: string;
  index_mime?: string;
  index_filename?: string;
  index_size_bytes?: number;
}

export interface RebuildResponse {
  ok: boolean;
  runs_scanned: number;
  attachments_indexed: number;
  unique_sha256: number;
}

export interface BrowseParams {
  limit?: number;
  cursor?: string;
  kind?: string;
  mime_prefix?: string;
  include_urls?: boolean;
}

// ─────────────────────────────────────────────────────────────
// API Functions
// ─────────────────────────────────────────────────────────────

export async function importZip(
  file: File,
  options?: { session_id?: string; batch_label?: string }
): Promise<ImportResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (options?.session_id) formData.append('session_id', options.session_id);
  if (options?.batch_label) formData.append('batch_label', options.batch_label);

  const resp = await fetch(`${BASE}/import-zip`, {
    method: 'POST',
    body: formData,
  });
  if (!resp.ok) throw new Error(`Import failed: ${resp.status}`);
  return resp.json();
}

export async function browse(params: BrowseParams = {}): Promise<BrowseResponse> {
  const url = new URL(`${BASE}/index/attachment_meta`, window.location.origin);
  if (params.limit) url.searchParams.set('limit', String(params.limit));
  if (params.cursor) url.searchParams.set('cursor', params.cursor);
  if (params.kind) url.searchParams.set('kind', params.kind);
  if (params.mime_prefix) url.searchParams.set('mime_prefix', params.mime_prefix);
  if (params.include_urls) url.searchParams.set('include_urls', 'true');

  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(`Browse failed: ${resp.status}`);
  return resp.json();
}

export async function getFacets(): Promise<FacetsResponse> {
  const resp = await fetch(`${BASE}/index/attachment_meta/facets`);
  if (!resp.ok) throw new Error(`Facets failed: ${resp.status}`);
  return resp.json();
}

export async function checkExists(sha256: string): Promise<ExistsResponse> {
  const resp = await fetch(`${BASE}/index/attachment_meta/${sha256}/exists`);
  if (!resp.ok) throw new Error(`Exists check failed: ${resp.status}`);
  return resp.json();
}

export async function rebuildIndex(): Promise<RebuildResponse> {
  const resp = await fetch(`${BASE}/index/rebuild_attachment_meta`, { method: 'POST' });
  if (!resp.ok) throw new Error(`Rebuild failed: ${resp.status}`);
  return resp.json();
}

export function getDownloadUrl(sha256: string): string {
  return `${BASE}/attachments/${sha256}`;
}

export function isViewerPack(entry: AttachmentMetaEntry): boolean {
  return entry.kind === 'viewer_pack' ||
    (entry.mime === 'application/zip' && entry.filename.includes('viewer'));
}
```

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-17 | Claude Code | Extracted from live API responses |

