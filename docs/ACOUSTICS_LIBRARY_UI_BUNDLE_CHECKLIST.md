# Acoustics Library UI + Import Workflow — Bundle Checklist

> **Bundle Goal**: Connect ToolBox backend ingestion/indexing to operator-facing UI
> **Status**: Draft
> **Created**: 2026-01-17

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  tap_tone_pi (Analyzer)                                         │
│  └── exports viewer_pack_v1.zip                                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Upload
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  ToolBox Backend (ALREADY IMPLEMENTED)                          │
│  ├── POST /api/rmos/acoustics/import-zip                        │
│  ├── GET  /api/rmos/acoustics/index/attachment_meta             │
│  ├── GET  /api/rmos/acoustics/index/attachment_meta/facets      │
│  ├── GET  /api/rmos/acoustics/index/attachment_meta/recent      │
│  └── GET  /api/rmos/acoustics/attachments/{sha256}              │
└─────────────────────┬───────────────────────────────────────────┘
                      │ (THIS BUNDLE)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  ToolBox Client (TO IMPLEMENT)                                  │
│  ├── AudioAnalyzerLibrary.vue (new view)                        │
│  ├── rmosAcoustics.ts (API wrapper)                             │
│  └── Integration with existing AudioAnalyzerViewer.vue          │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Checklist

### Phase 1: API Wrapper Module

#### 1.1 Create API Client
```
NEW: packages/client/src/sdk/endpoints/rmosAcoustics.ts
```

```typescript
/**
 * RMOS Acoustics API Client
 *
 * Endpoints:
 * - importZip: Upload viewer_pack_v1 ZIP for ingestion
 * - getFacets: Get kind/mime facet counts
 * - getRecent: Get recently added attachments
 * - browseAttachmentMeta: Paginated browse with filters
 * - checkExists: Check if attachment exists by SHA256
 */

import { apiClient } from '../client';

// Types
export interface ImportZipResult {
  run_id: string;
  attachments_imported: number;
  bytes_total: number;
  warnings: string[];
}

export interface AttachmentMetaFacets {
  facets: {
    kind: Record<string, number>;
    mime: Record<string, number>;
  };
  total_attachments: number;
  index_version: string;
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
  ref_count: number;
  download_url?: string;
}

export interface BrowseParams {
  limit?: number;
  cursor?: string;
  kind?: string;
  mime_prefix?: string;
  include_urls?: boolean;
}

export interface BrowseResult {
  count: number;
  total_in_index: number;
  limit: number;
  next_cursor: string | null;
  entries: AttachmentMetaEntry[];
}

// API Functions
export async function importZip(file: File): Promise<ImportZipResult> {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/api/rmos/acoustics/import-zip', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

export async function getFacets(): Promise<AttachmentMetaFacets> {
  return apiClient.get('/api/rmos/acoustics/index/attachment_meta/facets');
}

export async function getRecent(limit = 20): Promise<BrowseResult> {
  return apiClient.get('/api/rmos/acoustics/index/attachment_meta/recent', {
    params: { limit }
  });
}

export async function browseAttachmentMeta(params: BrowseParams): Promise<BrowseResult> {
  return apiClient.get('/api/rmos/acoustics/index/attachment_meta', { params });
}

export async function checkExists(sha256: string): Promise<{
  sha256: string;
  in_index: boolean;
  in_store: boolean;
  size_bytes?: number;
}> {
  return apiClient.get(`/api/rmos/acoustics/index/attachment_meta/${sha256}/exists`);
}

export async function rebuildIndex(): Promise<{
  ok: boolean;
  runs_scanned: number;
  attachments_indexed: number;
  unique_sha256: number;
}> {
  return apiClient.post('/api/rmos/acoustics/index/rebuild_attachment_meta');
}

export function getDownloadUrl(sha256: string): string {
  return `/api/rmos/acoustics/attachments/${sha256}`;
}
```

#### 1.2 Export from SDK index
```
MODIFY: packages/client/src/sdk/endpoints/index.ts
```

Add export:
```typescript
export * as rmosAcoustics from './rmosAcoustics';
```

---

### Phase 2: Acoustics Library View

#### 2.1 Create Main Library View
```
NEW: packages/client/src/views/tools/AudioAnalyzerLibrary.vue
```

```vue
<template>
  <div class="acoustics-library">
    <h1>Acoustics Evidence Library</h1>

    <!-- Import Panel -->
    <section class="import-panel">
      <h2>Import Evidence Pack</h2>
      <input
        type="file"
        accept=".zip"
        @change="handleFileSelect"
        :disabled="importing"
      />
      <button @click="doImport" :disabled="!selectedFile || importing">
        {{ importing ? 'Importing...' : 'Import ZIP' }}
      </button>
      <div v-if="importResult" class="import-result">
        <p>Imported: {{ importResult.attachments_imported }} attachments</p>
        <p>Run ID: {{ importResult.run_id }}</p>
        <ul v-if="importResult.warnings.length">
          <li v-for="w in importResult.warnings" :key="w">{{ w }}</li>
        </ul>
      </div>
    </section>

    <!-- Facets Panel -->
    <section class="facets-panel">
      <h2>Filter by Kind</h2>
      <div v-if="facets" class="facet-chips">
        <button
          v-for="(count, kind) in facets.facets.kind"
          :key="kind"
          :class="{ active: filters.kind === kind }"
          @click="toggleKindFilter(kind)"
        >
          {{ kind }} ({{ count }})
        </button>
      </div>
      <p v-if="facets">Total: {{ facets.total_attachments }} attachments</p>
    </section>

    <!-- Browse Table -->
    <section class="browse-panel">
      <h2>Browse Attachments</h2>
      <table v-if="browseResult">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Kind</th>
            <th>Size</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in browseResult.entries" :key="entry.sha256">
            <td>{{ entry.filename }}</td>
            <td>{{ entry.kind }}</td>
            <td>{{ formatBytes(entry.size_bytes) }}</td>
            <td>{{ formatDate(entry.created_at_utc) }}</td>
            <td>
              <button @click="downloadAttachment(entry)">Download</button>
              <button
                v-if="isViewerPack(entry)"
                @click="openInViewer(entry)"
              >
                Open
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="pagination">
        <button
          @click="loadMore"
          :disabled="!browseResult?.next_cursor"
        >
          Load More
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import * as rmosAcoustics from '@/sdk/endpoints/rmosAcoustics';

const router = useRouter();

// State
const selectedFile = ref<File | null>(null);
const importing = ref(false);
const importResult = ref<rmosAcoustics.ImportZipResult | null>(null);
const facets = ref<rmosAcoustics.AttachmentMetaFacets | null>(null);
const browseResult = ref<rmosAcoustics.BrowseResult | null>(null);
const filters = ref({ kind: null as string | null, cursor: null as string | null });

// Load initial data
onMounted(async () => {
  await Promise.all([loadFacets(), loadBrowse()]);
});

// Watch filters
watch(() => filters.value.kind, () => {
  filters.value.cursor = null;
  loadBrowse();
});

async function loadFacets() {
  facets.value = await rmosAcoustics.getFacets();
}

async function loadBrowse() {
  browseResult.value = await rmosAcoustics.browseAttachmentMeta({
    limit: 20,
    cursor: filters.value.cursor || undefined,
    kind: filters.value.kind || undefined,
    include_urls: true,
  });
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] || null;
}

async function doImport() {
  if (!selectedFile.value) return;
  importing.value = true;
  try {
    importResult.value = await rmosAcoustics.importZip(selectedFile.value);
    await Promise.all([loadFacets(), loadBrowse()]);
  } finally {
    importing.value = false;
  }
}

function toggleKindFilter(kind: string) {
  filters.value.kind = filters.value.kind === kind ? null : kind;
}

async function loadMore() {
  if (browseResult.value?.next_cursor) {
    filters.value.cursor = browseResult.value.next_cursor;
    const more = await rmosAcoustics.browseAttachmentMeta({
      limit: 20,
      cursor: filters.value.cursor,
      kind: filters.value.kind || undefined,
      include_urls: true,
    });
    browseResult.value.entries.push(...more.entries);
    browseResult.value.next_cursor = more.next_cursor;
  }
}

function downloadAttachment(entry: rmosAcoustics.AttachmentMetaEntry) {
  const url = rmosAcoustics.getDownloadUrl(entry.sha256);
  window.open(url, '_blank');
}

function isViewerPack(entry: rmosAcoustics.AttachmentMetaEntry): boolean {
  return entry.kind === 'viewer_pack' || entry.filename.endsWith('.zip');
}

function openInViewer(entry: rmosAcoustics.AttachmentMetaEntry) {
  // Navigate to viewer with attachment reference
  router.push({
    name: 'AudioAnalyzerViewer',
    query: { sha256: entry.sha256 }
  });
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}
</script>

<style scoped>
.acoustics-library {
  padding: 1rem;
}
section {
  margin-bottom: 2rem;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.facet-chips button {
  margin: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}
.facet-chips button.active {
  background: #007bff;
  color: white;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
  text-align: left;
}
</style>
```

#### 2.2 Add Route
```
MODIFY: packages/client/src/router/index.ts
```

Add route:
```typescript
{
  path: '/tools/acoustics-library',
  name: 'AudioAnalyzerLibrary',
  component: () => import('@/views/tools/AudioAnalyzerLibrary.vue'),
  meta: { title: 'Acoustics Evidence Library' }
},
```

#### 2.3 Add Navigation Link
```
MODIFY: packages/client/src/components/navigation/ToolsMenu.vue (or equivalent)
```

Add link near Audio Analyzer Viewer:
```vue
<router-link to="/tools/acoustics-library">
  Acoustics Library
</router-link>
```

---

### Phase 3: Viewer Integration

#### 3.1 Modify Viewer to Accept SHA256 Query Param
```
MODIFY: packages/client/src/views/tools/AudioAnalyzerViewer.vue
```

Add to `<script setup>`:
```typescript
import { useRoute } from 'vue-router';
import * as rmosAcoustics from '@/sdk/endpoints/rmosAcoustics';

const route = useRoute();

onMounted(async () => {
  // Check for sha256 query param (from library)
  const sha256 = route.query.sha256 as string;
  if (sha256) {
    await loadFromServer(sha256);
  }
});

async function loadFromServer(sha256: string) {
  const url = rmosAcoustics.getDownloadUrl(sha256);
  const response = await fetch(url);
  const blob = await response.blob();
  const file = new File([blob], 'evidence.zip', { type: 'application/zip' });
  // Use existing ZIP loader logic
  await loadZipFile(file);
}
```

---

### Phase 4: Backend Verification (Already Implemented)

Verify these endpoints exist and work:

| Endpoint | File | Status |
|----------|------|--------|
| `POST /api/rmos/acoustics/import-zip` | `services/api/app/rmos/acoustics/router_import.py` | Verify |
| `GET /api/rmos/acoustics/index/attachment_meta` | `services/api/app/rmos/runs_v2/acoustics_router.py` | ✅ Tested |
| `GET /api/rmos/acoustics/index/attachment_meta/facets` | `services/api/app/rmos/acoustics/router_query.py` | ✅ Tested |
| `GET /api/rmos/acoustics/index/attachment_meta/recent` | Verify exists | Check |
| `GET /api/rmos/acoustics/attachments/{sha256}` | `services/api/app/rmos/acoustics/router_attachments.py` | ✅ Tested |
| `POST /api/rmos/acoustics/index/rebuild_attachment_meta` | `services/api/app/rmos/runs_v2/acoustics_router.py` | ✅ Tested |

---

### Phase 5: Tests

#### 5.1 API Wrapper Unit Tests
```
NEW: packages/client/src/sdk/endpoints/__tests__/rmosAcoustics.test.ts
```

#### 5.2 Component Tests
```
NEW: packages/client/src/views/tools/__tests__/AudioAnalyzerLibrary.test.ts
```

#### 5.3 E2E Test
```
NEW: packages/client/e2e/acoustics-library.spec.ts
```

Test flow:
1. Navigate to library
2. Upload test ZIP
3. Verify facets update
4. Filter by kind
5. Open attachment in viewer

---

## Implementation Order

```
Phase 1: API Wrapper (Day 1)
├── 1.1 Create rmosAcoustics.ts
└── 1.2 Export from index.ts

Phase 2: Library View (Day 2-3)
├── 2.1 Create AudioAnalyzerLibrary.vue
├── 2.2 Add route
└── 2.3 Add navigation link

Phase 3: Viewer Integration (Day 3)
└── 3.1 Add sha256 query param support

Phase 4: Backend Verification (Day 1, parallel)
└── Verify all endpoints exist and match expected signatures

Phase 5: Tests (Day 4)
├── 5.1 API wrapper tests
├── 5.2 Component tests
└── 5.3 E2E test
```

---

## File Summary

| Action | Path |
|--------|------|
| NEW | `packages/client/src/sdk/endpoints/rmosAcoustics.ts` |
| MODIFY | `packages/client/src/sdk/endpoints/index.ts` |
| NEW | `packages/client/src/views/tools/AudioAnalyzerLibrary.vue` |
| MODIFY | `packages/client/src/router/index.ts` |
| MODIFY | `packages/client/src/components/navigation/ToolsMenu.vue` |
| MODIFY | `packages/client/src/views/tools/AudioAnalyzerViewer.vue` |
| NEW | `packages/client/src/sdk/endpoints/__tests__/rmosAcoustics.test.ts` |
| NEW | `packages/client/src/views/tools/__tests__/AudioAnalyzerLibrary.test.ts` |
| NEW | `packages/client/e2e/acoustics-library.spec.ts` |

**Total: 4 new files, 4 modified files**

---

## Open Questions (Blocking)

Before implementation, confirm:

1. **Import endpoint path**: Is it `/api/rmos/acoustics/import-zip` or different?
2. **Recent endpoint**: Does `/attachment_meta/recent` exist or use different params?
3. **Auth requirements**: Does the client need to pass auth headers?
4. **Viewer pack detection**: Filter by `kind === 'viewer_pack'` or by filename?

---

## Acceptance Criteria

- [ ] Operator can upload a `viewer_pack_v1.zip` from tap_tone_pi
- [ ] Import shows success with run_id and attachment count
- [ ] Facets panel shows kind/mime counts
- [ ] Browse table shows paginated attachments
- [ ] Clicking "Open" on a viewer pack loads it in AudioAnalyzerViewer
- [ ] All existing viewer functionality preserved
- [ ] No console errors
- [ ] Works on Chrome/Firefox/Edge

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-17 | Claude Code | Initial draft from analysis |

