# IBG Backend Coordination Package

**Date:** 2026-04-20  
**Status:** Ready for Backend Implementation  
**Blocks:** Body Outline Editor v3.0.0 Phase 2 (Real API)

---

## Executive Summary

The Body Outline Editor v3.0.0 frontend is complete and deployed with mock mode enabled. Phase 2 deployment requires backend infrastructure that is currently stubbed or missing. This document provides actionable specs for the backend team.

---

## Backend Ticket (Copy to Jira/GitHub Issues)

### Title: IBG Backend Infrastructure — Redis + Auth + Solve Endpoint

### Priority: P0 (Blocks Frontend v3.0.0 Production Deployment)

### Description
The Body Outline Editor v3.0.0 frontend is complete and ready. However, it requires backend infrastructure that is currently stubbed or missing. This ticket implements the missing components.

### Acceptance Criteria

#### 1. Redis Session Storage (Replace In-Memory Dict)
- [ ] Redis instance configured in production/staging
- [ ] Session TTL set to 24 hours
- [ ] Session data includes: `session_id`, `landmarks`, `solved_model`, `confidence`, `created_at`
- [ ] Multiple workers can share session state (no data loss on restart)

#### 2. Real Authentication (Replace Stub Decorator)
- [ ] Remove `@requires_paid_tier` passthrough stub
- [ ] Implement Bearer token validation from `Authorization` header
- [ ] Free tier: requests without token → rate limited (10/hour by IP)
- [ ] Paid tier: valid token → higher rate limit (100/hour)
- [ ] Token validation endpoint or shared secret (JWT recommended)

#### 3. Solve Endpoint: POST /api/body/solve-from-landmarks
- [ ] Accepts JSON body (see API contract below)
- [ ] Calls `InstrumentBodyGenerator.complete_from_landmarks()`
- [ ] Returns response matching API contract
- [ ] Creates Redis session and returns `session_id`
- [ ] Handles missing landmarks gracefully (returns confidence < 0.5)

#### 4. Session Endpoints
- [ ] `GET /api/body/session/{session_id}` — retrieve solved model
- [ ] `PUT /api/body/session/{session_id}/landmarks` — override and re-solve
- [ ] Both require valid auth token (user must own session)

#### 5. CORS Configuration
- [ ] Allow requests from `https://theproductionshop.app`
- [ ] Allow `Authorization` header
- [ ] Allow `Content-Type: application/json`

#### 6. Error Responses
- [ ] 401: Missing/invalid token → `{ "detail": "Authentication required" }`
- [ ] 429: Rate limit exceeded → `{ "detail": "Rate limit exceeded. Try again in X seconds" }`
- [ ] 500: Server error → `{ "detail": "Internal server error" }` (log full error internally)

### Testing Requirements
- [ ] All endpoints pass curl tests (see test commands below)
- [ ] Staging deployment passes frontend integration tests
- [ ] Rate limiting works (10/hour for free, 100/hour for paid)

### Definition of Done
- [ ] Code merged to main
- [ ] Deployed to staging
- [ ] Frontend team confirms `/api/body/solve-from-landmarks` returns expected schema
- [ ] Frontend team confirms session resume works across page reloads
- [ ] Documentation updated (API.md)

### Estimated Effort
- Backend: 3-5 days
- Testing: 1 day
- Total: 4-6 days

---

## API Contract

### Base URL

```
https://theproductionshop.app/api/body
```

### Endpoint 1: Solve from Landmarks

**Request:**

```http
POST /solve-from-landmarks
Content-Type: application/json
Authorization: Bearer <token>  (optional for free tier)

{
  "instrument_spec": "dreadnought",
  "landmarks": [
    {
      "label": "lower_bout_max",
      "x_mm": 190.5,
      "y_mm": 80.0,
      "source": "user_input",
      "confidence": 1.0
    },
    {
      "label": "butt_center",
      "x_mm": 0,
      "y_mm": 0,
      "source": "user_input",
      "confidence": 1.0
    },
    {
      "label": "neck_center",
      "x_mm": 0,
      "y_mm": 520.0,
      "source": "user_input",
      "confidence": 1.0
    }
  ],
  "options": {
    "return_side_heights": true,
    "return_zone_radii": true
  }
}
```

**Response (200 OK):**

```json
{
  "session_id": "abc123-def456-7890",
  "status": "completed",
  "confidence": 0.87,
  "dimensions": {
    "body_length_mm": 521.3,
    "lower_bout_mm": 382.1,
    "upper_bout_mm": 293.5,
    "waist_mm": 240.8,
    "waist_y_norm": 0.442
  },
  "outline_points": [
    [0, 0],
    [190.5, 80.0],
    [120.5, 228.0],
    [0, 520.0],
    [-120.5, 228.0],
    [-190.5, 80.0]
  ],
  "side_heights": [94.2, 95.1, 96.3, 97.2, 96.8, 95.5],
  "radii_by_zone": {
    "lower_bout": 265.3,
    "waist": 85.2,
    "upper_bout": 175.6
  },
  "missing_landmarks": [],
  "back_radius_source": "spec"
}
```

**Error Responses:**

```json
// 401 Unauthorized
{ "detail": "Authentication required. Please login for paid tier access." }

// 429 Rate Limit Exceeded
{ "detail": "Rate limit exceeded. Try again in 360 seconds." }

// 400 Bad Request
{ "detail": "Missing required landmark: lower_bout_max" }

// 500 Internal Server Error
{ "detail": "Internal server error. Our team has been notified." }
```

### Endpoint 2: Get Session

**Request:**

```http
GET /session/{session_id}
Authorization: Bearer <token>
```

**Response:** Same as solve response (200 OK)

### Endpoint 3: Update Session Landmarks

**Request:**

```http
PUT /session/{session_id}/landmarks
Content-Type: application/json
Authorization: Bearer <token>

{
  "landmarks": [
    {
      "label": "waist_min",
      "x_mm": 118.0,
      "y_mm": 225.0,
      "source": "user_override",
      "confidence": 1.0
    }
  ]
}
```

**Response:** New solved model (same structure as solve response)

---

## Test curl Commands

### Test 1: Free Tier (No Auth)

```bash
curl -X POST https://staging.theproductionshop.app/api/body/solve-from-landmarks \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_spec": "dreadnought",
    "landmarks": [
      {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0, "source": "user_input", "confidence": 1.0},
      {"label": "butt_center", "x_mm": 0, "y_mm": 0, "source": "user_input", "confidence": 1.0},
      {"label": "neck_center", "x_mm": 0, "y_mm": 520.0, "source": "user_input", "confidence": 1.0}
    ]
  }'
```

### Test 2: Paid Tier (With Auth)

```bash
curl -X POST https://staging.theproductionshop.app/api/body/solve-from-landmarks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-paid-token-123" \
  -d '{
    "instrument_spec": "dreadnought",
    "landmarks": [
      {"label": "lower_bout_max", "x_mm": 190.5, "y_mm": 80.0, "source": "user_input", "confidence": 1.0},
      {"label": "waist_min", "x_mm": 120.5, "y_mm": 228.0, "source": "user_input", "confidence": 1.0},
      {"label": "upper_bout_max", "x_mm": 146.0, "y_mm": 390.0, "source": "user_input", "confidence": 1.0},
      {"label": "butt_center", "x_mm": 0, "y_mm": 0, "source": "user_input", "confidence": 1.0},
      {"label": "neck_center", "x_mm": 0, "y_mm": 520.0, "source": "user_input", "confidence": 1.0}
    ]
  }'
```

### Test 3: Get Session

```bash
# Replace {session_id} with actual from test 2 response
curl -X GET https://staging.theproductionshop.app/api/body/session/abc123-def456 \
  -H "Authorization: Bearer test-paid-token-123"
```

### Test 4: Rate Limit Test (Free Tier)

```bash
# Run 11 times in quick succession
for i in {1..11}; do
  curl -X POST https://staging.theproductionshop.app/api/body/solve-from-landmarks \
    -H "Content-Type: application/json" \
    -d '{"instrument_spec":"dreadnought","landmarks":[]}'
  echo "Request $i"
done
# Expect request 11 to return 429
```

---

## Staging Test Plan

### Pre-requisites
- Staging environment deployed
- Redis instance running
- Test API keys generated

### Test Suite

| Test ID | Description | Expected Result | Status |
|---------|-------------|-----------------|--------|
| T01 | Free tier solve (no auth) | 200 OK, confidence >= 0.7 | |
| T02 | Paid tier solve (valid token) | 200 OK, session_id returned | |
| T03 | Missing required landmarks | 200 OK but confidence < 0.5 | |
| T04 | Invalid auth token | 401 Unauthorized | |
| T05 | Rate limit exceeded | 429 after 10 requests | |
| T06 | Get session by ID | 200 OK, matches solve response | |
| T07 | Get non-existent session | 404 Not Found | |
| T08 | Update session landmarks | 200 OK, outline updates | |
| T09 | Update session with invalid token | 401 Unauthorized | |
| T10 | CORS preflight | 200 OK with CORS headers | |

---

## Frontend-Backend Integration Checklist

### Backend Team (Complete First)
- [ ] Redis session storage implemented
- [ ] Bearer token validation implemented
- [ ] Rate limiting configured (10/hr free, 100/hr paid)
- [ ] All 3 endpoints deployed to staging
- [ ] CORS headers configured
- [ ] Staging URL confirmed

### Frontend Team (After Backend Ready)
- [ ] Change `useMock = false` in body-outline-editor.html
- [ ] Test against staging API
- [ ] Verify session resume works
- [ ] Verify auth flow (Login/Logout)
- [ ] Deploy to production

### Joint Sign-off
- [ ] All staging tests pass
- [ ] Frontend team confirms mock -> real transition works
- [ ] Production deployment scheduled

---

## Timeline Estimate

| Task | Owner | Days |
|------|-------|------|
| Redis implementation | Backend | 1 |
| Auth implementation | Backend | 2 |
| Endpoint development | Backend | 1 |
| Rate limiting | Backend | 0.5 |
| Staging deployment | Backend | 0.5 |
| Testing & validation | Both | 1 |
| Production deployment | Both | 0.5 |
| **Total** | | **6.5 days** |

---

## Contact

**Frontend:** Body Outline Editor v3.0.0 is ready with `useMock = true`  
**File:** `hostinger/body-outline-editor.html`  
**Phase 2 Trigger:** Set `useMock = false` at line 671 when backend is ready

---

*Generated: 2026-04-20*
