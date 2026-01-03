# ROUTING_TRUTH_CONTRACT_v1

**Version:** 1.0  
**Status:** Canonical  
**Owner:** ToolBox Governance  
**Purpose:** Eliminate "where is this router mounted / what is live" ambiguity by providing a runtime source of truth.

---

## A. Why This Exists

The application mounts a dedicated routing truth router:

- Imported in `services/api/app/main.py` as:
  ```python
  from .meta.router_truth_routes import router as routing_truth_router
  ```
- Implementation: `services/api/app/meta/router_truth_routes.py`

This router answers:
- What endpoints are actually mounted *in the running app*
- Which paths are deprecated (and why)
- Runtime route table for diffing between environments

---

## B. Routing Truth Endpoint

### `GET /api/_meta/routing-truth`

**Returns:** JSON object describing all mounted routes in the running FastAPI app.

**Contract (actual implementation):**

```json
{
  "count": 347,
  "deprecated_count": 12,
  "routes": [
    {
      "path": "/api/rmos/runs",
      "methods": ["GET"],
      "name": "list_runs",
      "deprecated": false,
      "deprecated_reason": null
    },
    {
      "path": "/api/art-studio/rosette/preview",
      "methods": ["POST"],
      "name": "preview_rosette",
      "deprecated": true,
      "deprecated_reason": "legacy_art_studio_lane"
    }
  ]
}
```

**Field definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `count` | int | Total mounted routes |
| `deprecated_count` | int | Routes matching deprecated lanes |
| `routes` | array | Sorted by (path, methods) for stable diffing |
| `routes[].path` | string | Endpoint path |
| `routes[].methods` | string[] | HTTP methods (sorted) |
| `routes[].name` | string | FastAPI operation name |
| `routes[].deprecated` | bool | True if path matches deprecated lane |
| `routes[].deprecated_reason` | string? | Lane key if deprecated, else null |

**Interpretation rules:**

- Routes are sorted by `(path, methods)` for stable output across restarts
- Only `Route` instances are included (not `Mount` or WebSocket routes)
- `deprecated_reason` maps to lane keys used by `DeprecationHeadersMiddleware`

---

## C. Deprecation Detection Logic

The routing truth endpoint uses path-prefix matching to detect deprecated routes:

```python
def _is_deprecated_path(path: str) -> Optional[str]:
    if path.startswith("/api/art-studio"):
        return "legacy_art_studio_lane"
    if path.startswith("/rosette"):
        return "transitional_no_api_prefix_lane"
    return None
```

| Lane Key | Match Prefix | Notes |
|----------|--------------|-------|
| `legacy_art_studio_lane` | `/api/art-studio` | Migrate to `/api/art` |
| `transitional_no_api_prefix_lane` | `/rosette` | Missing `/api/` prefix |

---

## D. Deprecation Headers Middleware

### Integration

Imported in `services/api/app/main.py` as:
```python
from .middleware.deprecation import DeprecationHeadersMiddleware
app.add_middleware(DeprecationHeadersMiddleware)
```

Implementation: `services/api/app/middleware/deprecation.py`

### When Headers Are Set

Headers are added to responses when request path matches a deprecated lane prefix.

**This middleware does NOT block requests** — it's purely observational.

### Headers Contract

| Header | Example | Description |
|--------|---------|-------------|
| `Deprecation` | `true` | Endpoint is deprecated |
| `Sunset` | `2026-06-30` | Target removal date (from `DEPRECATION_SUNSET_DATE` env var) |
| `X-Deprecated-Lane` | `legacy_art_studio_lane` | Which lane triggered |
| `Link` | `</api/art>; rel="successor-version"` | Successor endpoint prefix (RFC-style) |

### Server Logging

Each deprecated endpoint hit emits a warning log:
```
DEPRECATED_ENDPOINT_HIT lane=legacy_art_studio_lane method=POST path=/api/art-studio/rosette/preview successor=/api/art
```

### Deprecated Lanes (Current)

| Lane Key | Match Prefix | Successor | Sunset Date |
|----------|--------------|-----------|-------------|
| `legacy_art_studio_lane` | `/api/art-studio/*` | `/api/art` | 2026-06-30 |
| `transitional_no_api_prefix_lane` | `/rosette/*` | `/api/art` | 2026-06-30 |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPRECATION_SUNSET_DATE` | `2026-06-30` | Date for `Sunset` header |

---

## E. Usage Examples

### Check Deprecated Route Count

```bash
curl -s http://localhost:8000/api/_meta/routing-truth | jq '.deprecated_count'
```

### List All Deprecated Paths

```bash
curl -s http://localhost:8000/api/_meta/routing-truth | \
  jq '.routes[] | select(.deprecated) | .path'
```

### Diff Routes Between Environments

```bash
# Capture prod
curl -s https://prod.example.com/api/_meta/routing-truth > prod_routes.json

# Capture local
curl -s http://localhost:8000/api/_meta/routing-truth > local_routes.json

# Diff
diff <(jq -S '.routes[].path' prod_routes.json) \
     <(jq -S '.routes[].path' local_routes.json)
```

### Check Deprecation Headers on a Request

```bash
curl -sI http://localhost:8000/api/art-studio/rosette/preview | grep -E '^(Deprecation|Sunset|Link|X-Deprecated)'
```

---

## F. Change Control

Any change to:
- Output shape of `/api/_meta/routing-truth`
- Deprecation lane definitions
- Header names/values

…requires:

1. Version bump on this contract doc
2. Update `router_truth_routes.py` and/or `deprecation.py`
3. Add/update tests covering the change
4. Update SCAFFOLDING_TRUTH_v1.md if lanes change

---

## G. Frontend Integration

### Fetch Wrapper Location

```
packages/client/src/sdk/core/apiFetch.ts
```

All SDK calls flow through `apiFetch()` which automatically calls `handleDeprecationHeaders()` on every response (line 65).

### Deprecation Handler Setup

```typescript
// In app initialization (e.g., main.ts or App.vue)
import { setDeprecationHandler } from '@/sdk/core/headers';

setDeprecationHandler((event) => {
  console.warn(
    `[DEPRECATED] ${event.method} ${event.url}`,
    event.sunset ? `Sunset: ${event.sunset}` : '',
    event.link ? `Replacement: ${event.link}` : ''
  );

  // Optional: Send to telemetry
  // analytics.track('deprecated_api_call', event);
});
```

### TypeScript Types

```typescript
// Already defined in packages/client/src/sdk/core/headers.ts
export type DeprecationEvent = {
  url: string;
  method: string;
  deprecation?: string | null;
  sunset?: string | null;
  link?: string | null;
  lane?: string | null;
};
```

### Files Reference

| File | Purpose |
|------|---------|
| `packages/client/src/sdk/core/apiFetch.ts` | Central fetch wrapper (line 65 handles deprecation) |
| `packages/client/src/sdk/core/headers.ts` | `handleDeprecationHeaders()` + `setDeprecationHandler()` |
| `packages/client/src/sdk/http.ts` | Lower-level `sdkRequest()` (alternative wrapper) |

---

## H. Machine-Readable Truth File

### Location

```
services/api/app/data/endpoint_truth.json
```

### Purpose

Provides a static, version-controlled source of truth for CI gates to detect:
- Missing endpoints (documented but not mounted)
- Undocumented endpoints (mounted but not in truth file)
- Deprecated endpoint usage in frontend code

### Schema

```typescript
interface EndpointTruthFile {
  $schema: string;           // JSON Schema reference
  _comment: string;          // Human description
  _version: string;          // Semver version
  _updated: string;          // ISO date of last update
  routes: EndpointTruthEntry[];
}

interface EndpointTruthEntry {
  path: string;              // Full path including /api prefix
  methods: string[];         // HTTP methods
  name: string;              // Canonical endpoint name
  lane: Lane;                // Classification for governance
  deprecated: boolean;       // Is this deprecated?
  deprecated_reason?: string;// Why deprecated (if applicable)
  successor?: string;        // Canonical replacement path
  sunset?: string;           // ISO date when removal planned
}

type Lane = 
  | "CORE"       // Health, meta endpoints
  | "META"       // Introspection, governance
  | "OPERATION"  // Governed machine-output endpoints
  | "RMOS"       // RMOS orchestration
  | "CAM"        // CAM toolpath generation
  | "TOOLING"    // Tool/material library
  | "ART"        // Art Studio (canonical)
  | "COMPARE"    // Compare workflows
  | "SIMULATION" // G-code simulation
  | "LEGACY"     // Deprecated endpoints
  | "UTILITY";   // Stateless utility endpoints
```

### CI Gate Script

```bash
#!/bin/bash
# .github/scripts/check_routing_truth_drift.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"
TRUTH_FILE="services/api/app/data/endpoint_truth.json"

# Extract expected paths from truth file
jq -r '.routes[].path' "$TRUTH_FILE" | sort > /tmp/expected.txt

# Extract runtime paths from running API
curl -s "$API_URL/api/_meta/routing-truth" | \
  jq -r '.routes[].path' | sort > /tmp/runtime.txt

# Check for missing (expected but not mounted)
MISSING=$(comm -23 /tmp/expected.txt /tmp/runtime.txt)
if [ -n "$MISSING" ]; then
  echo "❌ MISSING ENDPOINTS (documented but not mounted):"
  echo "$MISSING"
  EXIT_CODE=1
fi

# Check for undocumented (mounted but not in truth file)
UNDOCUMENTED=$(comm -13 /tmp/expected.txt /tmp/runtime.txt)
if [ -n "$UNDOCUMENTED" ]; then
  echo "⚠️  UNDOCUMENTED ENDPOINTS (mounted but not in truth file):"
  echo "$UNDOCUMENTED"
  # Warning only - don't fail CI for new endpoints
fi

exit ${EXIT_CODE:-0}
```

---

## I. Artifact Linkage Invariants (OPERATION Lane)

For OPERATION lane endpoints that produce run artifacts, the following linkage rules apply.

### Reference Implementation: Saw Lab Batch

**Artifact Chain:**
```
saw_batch_spec → saw_batch_plan → saw_batch_decision → saw_batch_execution
                                                           ↓
                                               saw_batch_job_log
                                               saw_batch_execution_metrics_rollup
```

### Required `index_meta` Keys by Kind

| Kind | Required Keys | Parent Link Field |
|------|---------------|-------------------|
| `saw_batch_spec` | `tool_kind`, `batch_label`, `session_id` | — (root) |
| `saw_batch_plan` | `tool_kind`, `batch_label`, `session_id` | `parent_batch_spec_artifact_id` |
| `saw_batch_decision` | `tool_kind`, `batch_label`, `session_id`, `approved_by` | `parent_batch_plan_artifact_id`, `parent_batch_spec_artifact_id` |
| `saw_batch_execution` | `tool_kind`, `batch_label`, `session_id` | `parent_batch_decision_artifact_id` |
| `saw_batch_job_log` | — | `parent_batch_execution_artifact_id`, `parent_batch_decision_artifact_id` |
| `saw_batch_execution_metrics_rollup` | — | `parent_batch_execution_artifact_id`, `parent_batch_decision_artifact_id` |

### Query Filter Support

The `store.py:query_run_artifacts()` function supports filtering by:
- `parent_batch_decision_artifact_id`
- `parent_batch_plan_artifact_id`
- `parent_batch_spec_artifact_id`

### Invariants

1. Every artifact except `spec` **MUST** have at least one `parent_*_artifact_id` in `index_meta`
2. `batch_label` and `session_id` **MUST** propagate to all descendants
3. Skip-level links (e.g., job_log → decision) are **ALLOWED** for UI navigation convenience
4. `tool_kind` **SHOULD** be set to enable cross-tool queries

---

## J. Related Documents

- [SCAFFOLDING_TRUTH_v1.md](./SCAFFOLDING_TRUTH_v1.md) — Repo topology and service structure
- [ENDPOINT_TRUTH_MAP.md](./ENDPOINT_TRUTH_MAP.md) — Complete API surface documentation
- [ROUTER_MAP.md](../ROUTER_MAP.md) — Router organization by wave
- [OPERATION_EXECUTION_GOVERNANCE_v1.md](./OPERATION_EXECUTION_GOVERNANCE_v1.md) — Lane classification rules
