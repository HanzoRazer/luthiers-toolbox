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

## H. Related Documents

- [SCAFFOLDING_TRUTH_v1.md](./SCAFFOLDING_TRUTH_v1.md) — Repo topology and service structure
- [ENDPOINT_TRUTH_MAP.md](./ENDPOINT_TRUTH_MAP.md) — Complete API surface documentation
- [ROUTER_MAP.md](../ROUTER_MAP.md) — Router organization by wave
