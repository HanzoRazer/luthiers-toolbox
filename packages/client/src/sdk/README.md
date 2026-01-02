# Luthier's Tool Box SDK

**H8.2.1: Frontend SDK skeleton + request wrapper**

## Purpose

Single choke point for all frontend → backend API calls with:
- Request-id correlation (matches backend `RequestIdMiddleware`)
- Progressive strictness enforcement (`off` → `warn` → `error`)
- Observable transport events for telemetry
- Framework-agnostic design

## Usage

```typescript
import { sdkRequest } from '@/sdk'

// Basic request
const response = await sdkRequest('/api/cam/fret_slots/preview', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ scale_length: 650 })
})

// With options
const response = await sdkRequest('/api/rmos/runs', {
  method: 'GET'
}, {
  strictRequestId: 'error', // Enforce header validation
  onEvent: (evt) => console.log('SDK Event:', evt)
})
```

## Architecture

```
packages/client/src/sdk/
├── http.ts        # Core transport (sdkRequest, request-id logic)
├── index.ts       # Public exports
└── README.md      # This file
```

### Future modules (H8.2.2+)
```
├── cam.ts         # CAM endpoint wrappers
├── rmos.ts        # RMOS endpoint wrappers
├── art.ts         # Art Studio endpoint wrappers
└── instruments.ts # Instrument geometry wrappers
```

## Request-ID Contract

**Backend** (`RequestIdMiddleware` in `main.py`):
- Accepts client `X-Request-Id` or generates one
- Echoes back in response header

**Frontend** (this SDK):
- Generates `sdk_req_<12-char-hex>` if not provided
- Validates presence of echo header (default: warn mode)
- Enables end-to-end request correlation

## Migration Path

Replace raw `fetch()` calls with `sdkRequest()`:

**Before:**
```typescript
const resp = await fetch('/api/rmos/rosette/generate-slices', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
```

**After:**
```typescript
const resp = await sdkRequest('/api/rmos/rosette/generate-slices', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
```

**Priority migration targets** (20+ raw `fetch()` calls found):
1. `stores/useRosetteDesignerStore.ts` (4 calls)
2. `stores/instrumentGeometryStore.ts` (3 calls)
3. `stores/useStripFamilyStore.ts` (3 calls)
4. `features/ai_images/api.ts` (2 calls)
5. `composables/useCompareState.ts`
6. `cnc_production/CompareRunsPanel.vue`

## Observability

Enable transport events for debugging/telemetry:

```typescript
const response = await sdkRequest('/api/cam/toolpath', {
  method: 'POST',
  body: JSON.stringify(params)
}, {
  onEvent: (evt) => {
    if (evt.kind === 'response' && !evt.hasRequestIdHeader) {
      // Log missing request-id for investigation
      telemetry.trackWarning('missing_request_id', { url: evt.url })
    }
  }
})
```

## Strictness Levels

| Mode | Behavior |
|------|----------|
| `"off"` | No validation (legacy compatibility) |
| `"warn"` | Console warning if header missing (default) |
| `"error"` | Throw error if header missing (enforce contract) |

**Recommended progression:**
1. Start with `"warn"` (current default)
2. Monitor console warnings in production
3. Fix backend issues if found
4. Ratchet to `"error"` after validation period
5. Add CI gate to prevent regressions

## Backend Integration

This SDK matches the backend `RequestIdMiddleware` contract exactly:

**Backend** (`services/api/app/main.py`, lines 34-72):
```python
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id")
        if not req_id:
            req_id = f"req_{uuid.uuid4().hex[:12]}"
        
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["x-request-id"] = req_id  # Echo back
        return response
```

**Frontend** (this SDK):
- Sends `X-Request-Id` header on every request
- Validates echo in response
- Correlates logs/errors with backend request-id

## Related

- Backend: `services/api/app/main.py` - RequestIdMiddleware
- CI: `.github/workflows/ai_platform_enforcement.yml` - Guards SDK contract
- Docs: `docs/handoffs/DEVELOPER_HANDOFF_DEC19_2025.md` - Request correlation architecture
