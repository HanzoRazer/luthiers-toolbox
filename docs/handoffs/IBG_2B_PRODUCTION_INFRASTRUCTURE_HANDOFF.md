# IBG-2B: Production Infrastructure Handoff

**Date:** 2026-05-12  
**Sprint:** IBG-2B  
**Status:** COMPLETE

---

## Summary

IBG-2B enables the Body Outline Editor to call real IBG backend endpoints in production. This sprint implements:

- Redis-backed session persistence
- Authentication via existing Supabase/JWT system
- Rate limiting via existing slowapi infrastructure
- Configurable CORS (no wildcard in production)
- BOE production mode configuration

No IBG math, geometry behavior, or BOE editing behavior was changed.

---

## Files Changed

### New Files

| File | Purpose |
|------|---------|
| `app/instrument_geometry/body/ibg/session_store.py` | Redis/in-memory session storage |
| `tests/test_ibg_2b_infrastructure.py` | Infrastructure tests (18 tests) |

### Modified Files

| File | Change |
|------|--------|
| `app/routers/body_solver_router.py` | Wired session store, auth, rate limiting |
| `app/instrument_geometry/body/ibg/__init__.py` | Export session store classes |
| `app/main.py` | CORS configuration from env var |
| `hostinger/body-outline-editor.html` | Production API configuration |
| `tools/body-outline-editor.html` | Synced with hostinger/ |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IBG_SESSION_STORE` | `memory` | Session backend: `memory` or `redis` |
| `REDIS_URL` | (none) | Redis connection URL (required if `redis`) |
| `IBG_SESSION_TTL_SECONDS` | `86400` | Session TTL (24 hours) |
| `IBG_RATE_LIMIT_FREE` | `10/hour` | Rate limit for free tier |
| `IBG_RATE_LIMIT_PAID` | `100/hour` | Rate limit for paid tier |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |

### Production Configuration Example

```bash
# .env (production)
IBG_SESSION_STORE=redis
REDIS_URL=redis://localhost:6379/0
IBG_SESSION_TTL_SECONDS=86400
IBG_RATE_LIMIT_FREE=10/hour
IBG_RATE_LIMIT_PAID=100/hour
CORS_ORIGINS=https://theproductionshop.app,https://api.theproductionshop.app
AUTH_MODE=supabase
```

---

## Endpoints Affected

| Endpoint | Auth | Rate Limit |
|----------|------|------------|
| `POST /api/body/solve-from-dxf` | Optional | 10/hour |
| `POST /api/body/solve-from-landmarks` | Required | 100/hour |
| `GET /api/body/session/{id}` | Optional | 10/hour |
| `PUT /api/body/session/{id}/landmarks` | Required | 100/hour |

---

## Session Persistence Behavior

### In-Memory (Default)

- Sessions stored in process memory
- Lost on restart
- Not suitable for multi-worker deployment
- Use for development/testing

### Redis (Production)

- Sessions stored in Redis with TTL
- Survives restarts
- Supports multi-worker deployment
- Auto-fallback to memory if Redis unavailable

### Session Data Structure

```json
{
  "instrument_spec": "dreadnought",
  "landmarks": [
    {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0, ...}
  ],
  "model": {
    "body_length_mm": 520.0,
    "lower_bout_width_mm": 381.0,
    "outline_points": [[x, y], ...],
    "side_heights_mm": [...],
    "radii_by_zone": {...},
    "confidence": 0.87
  }
}
```

---

## Auth Behavior

Uses the existing auth system (`app/auth/deps.py`).

| Tier | Dependency | Behavior |
|------|------------|----------|
| Free | `get_optional_principal()` | No auth required, rate limited |
| Paid | `get_current_principal()` | Auth required, higher rate limit |

### Auth Modes (from existing system)

| Mode | Environment |
|------|-------------|
| `supabase` | Production (JWT from Supabase) |
| `header` | Development (x-user-role, x-user-id headers) |

---

## Rate Limit Behavior

Uses existing slowapi infrastructure (`app/middleware/rate_limit.py`).

- Redis-backed when `RATE_LIMIT_STORAGE=redis://...`
- In-memory otherwise
- Returns 429 with `Retry-After` header when exceeded

---

## CORS Configuration

| Setting | Development | Production |
|---------|-------------|------------|
| `CORS_ORIGINS` | (unset) | Explicit list |
| `allow_origins` | `["*"]` | From env var |
| `allow_credentials` | `False` | `True` |

---

## BOE Configuration

The Body Outline Editor now supports production mode via configuration.

### Configuration Methods (priority order)

1. **Constructor args**: `new InstrumentBodyAPI('/api', false)`
2. **URL params**: `?ibg_api_url=/api&ibg_mock=false`
3. **Window config**: `window.IBG_CONFIG = {apiUrl: '/api', useMock: false}`
4. **Default**: Mock mode enabled for safety

### Production Setup

```html
<script>
  window.IBG_CONFIG = {
    apiUrl: 'https://api.theproductionshop.app',
    useMock: false
  };
</script>
```

Or via URL: `body-outline-editor.html?ibg_mock=false`

Mock mode remains available for offline demo/testing.

---

## Test Results

```
18 passed in 26.58s
Coverage: 21.99% (meets 20% threshold)
```

| Test Category | Tests | Status |
|---------------|-------|--------|
| In-memory session store | 6 | PASS |
| Redis session store (mocked) | 4 | PASS |
| Session store factory | 2 | PASS |
| CORS configuration | 4 | PASS |
| API integration | 1 | PASS |
| Rate limit configuration | 1 | PASS |

---

## Known Limitations

1. **Redis package optional** — Falls back to memory if `redis` not installed
2. **Rate limit storage shared** — IBG uses the same Redis as global rate limiter
3. **Auth stub in tests** — Tests use header-based auth, not Supabase JWT
4. **Router loading in tests** — Some test configurations don't load body_solver_router

---

## Deployment Checklist

### Backend

- [ ] Set `IBG_SESSION_STORE=redis`
- [ ] Configure `REDIS_URL`
- [ ] Set `CORS_ORIGINS` (no wildcard)
- [ ] Verify `AUTH_MODE=supabase`
- [ ] Test session persistence across restarts
- [ ] Verify rate limiting works

### Frontend (BOE)

- [ ] Set `window.IBG_CONFIG.useMock = false`
- [ ] Set `window.IBG_CONFIG.apiUrl` to production API
- [ ] Test solve workflow end-to-end
- [ ] Verify auth error handling (401)
- [ ] Verify rate limit error handling (429)

---

## Next Steps

With IBG-2B complete, the integration path is:

```
Blueprint Reader → IBG (solver) → BOE (human authority) → Export
```

Recommended follow-on work:

1. **IBG-2C: UX Improvements** — Landmark visualization in BOE
2. **IBG-3A: Additional Specs** — Add OM, parlour, classical specs
3. **Redis session cleanup** — Add monitoring/metrics for session usage

---

## References

- `docs/handoffs/IBG_2A_BOE_INTEGRATION_BOUNDARY_AUDIT.md`
- `docs/architecture/IBG_BOE_BOUNDARY_MODEL.md`
- `docs/handoffs/IBG_BACKEND_COORDINATION.md`
- `app/auth/deps.py` — Auth system documentation
- `app/middleware/rate_limit.py` — Rate limit system documentation

---

*IBG-2B complete. Production infrastructure enabled. No geometry changes.*
