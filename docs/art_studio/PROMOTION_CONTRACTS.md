# Art Studio Promotion Contracts

> **Phase 33.0**: CAM Promotion Request Bridge

This document describes the promotion pipeline from Art Studio design-first workflow to CAM request.

---

## Overview

Art Studio does **not** have manufacturing authority. It can only:
1. Build a `PromotionIntentV1` (design + feasibility summary)
2. Request a `CamPromotionRequestV1` (downstream-safe handoff envelope)

The actual CAM execution (toolpath generation, G-code emission) is controlled by RMOS or CAM lane operators.

---

## Schemas

### PromotionIntentV1

**Purpose**: Summarizes design geometry + feasibility checks for CAM handoff consideration.

**Location**: `app/art_studio/schemas/promotion_intent.py`

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `intent_version` | str | Schema version (`"1.0"`) |
| `session_id` | str | Art Studio workflow session ID |
| `design_fingerprint` | str | SHA256 of normalized design JSON |
| `feasibility_fingerprint` | str | SHA256 of feasibility result JSON |
| `design_summary` | DesignSummaryV1 | Ring count, complexity, tool requirements |
| `feasibility_summary` | FeasibilitySummaryV1 | Passed status, risk level, checks |
| `export_ready` | bool | True if session in APPROVED or EXPORTED state |
| `created_at` | datetime | Timestamp of intent creation |

**What it is NOT**:
- Not an execution order
- Not a machine config
- Not a commitment to manufacture

---

### CamPromotionRequestV1

**Purpose**: Immutable record that Art Studio requested CAM consideration for a specific design+feasibility pair.

**Location**: `app/art_studio/schemas/cam_promotion_request.py`

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `promotion_request_version` | str | Schema version (`"1.0"`) |
| `promotion_request_id` | str | Unique UUID for this request |
| `created_at` | datetime | When request was created |
| `source` | str | Always `"art_studio_design_first"` |
| `session_id` | str | Originating Art Studio session |
| `design_fingerprint` | str | From PromotionIntentV1 |
| `feasibility_fingerprint` | str | From PromotionIntentV1 |
| `intent_snapshot` | PromotionIntentV1 | Full intent at promotion time |
| `cam_profile_id` | str? | Optional CAM profile hint |
| `status` | str | `"pending"` → downstream updates |

---

## API Endpoints

### Get Promotion Intent

```
GET /api/art/design-first-workflow/sessions/{session_id}/promotion-intent
```

Returns `PromotionIntentV1` if session is in APPROVED or EXPORTED state.

### Promote to CAM Request

```
POST /api/art/design-first-workflow/sessions/{session_id}/promote_to_cam
```

**Query Parameters**:
- `cam_profile_id` (optional): Hint for downstream CAM profile selection

**Response**:
```json
{
  "ok": true,
  "request": { /* CamPromotionRequestV1 */ }
}
```

**Blocked Response** (session not approved):
```json
{
  "ok": false,
  "blocked_reason": "Session is not in APPROVED or EXPORTED state",
  "request": null
}
```

**Idempotency**: Same `design_fingerprint:feasibility_fingerprint` pair returns existing request.

### Get Promotion Request by ID

```
GET /api/art/design-first-workflow/cam-promotion/requests/{request_id}
```

Returns `CamPromotionRequestV1` or 404.

---

## Idempotency

Promotion requests are keyed by fingerprint pair:
```
{design_fingerprint}:{feasibility_fingerprint}
```

If a request already exists for this pair:
- Return the existing request
- Do not create a duplicate
- Log for audit trail

This ensures:
1. Design changes create new requests
2. Re-clicking "Promote" is safe
3. Each unique design+feasibility combo has one request

---

## Architectural Boundary

```
┌─────────────────────────────────────────────────────────────┐
│                     Art Studio Domain                        │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Design-First    │───▶│ PromotionIntentV1               │ │
│  │ Workflow        │    │ (design summary, feasibility)   │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│                                     │                        │
│                                     ▼                        │
│                         ┌─────────────────────────────────┐ │
│                         │ CamPromotionRequestV1           │ │
│                         │ (immutable handoff envelope)    │ │
│                         └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                      │
                                      │ (Artifact handoff via JSON)
                                      │ (Not Python imports)
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     CAM / RMOS Domain                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ CAM Operator reads CamPromotionRequestV1                ││
│  │ → Validates fingerprints                                ││
│  │ → Creates execution artifacts                           ││
│  │ → Generates toolpaths and G-code                        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Key Principle**: Art Studio writes `CamPromotionRequestV1` artifacts but never:
- Imports from `app.cam.*`
- Generates toolpaths
- Creates G-code
- Has execution authority

---

## Storage

Promotion requests are stored in:
```
services/api/data/art_studio_cam_promotion_requests/
└── {promotion_request_id}.json
```

Idempotency index is stored in:
```
services/api/data/art_studio_cam_promotion_requests/
└── _idempotency_index.json
```

---

## Test Coverage

Contract tests in `test_art_studio_cam_promotion_contract.py`:

1. **test_promote_blocked_when_not_approved** - Returns ok=false for non-approved sessions
2. **test_promote_succeeds_when_approved** - Creates request for approved sessions
3. **test_promote_idempotent** - Same fingerprints return same request
4. **test_get_promotion_request** - Retrieves request by ID
5. **test_get_promotion_request_404** - Returns 404 for unknown ID

---

## See Also

- [FENCE_REGISTRY.json](../../FENCE_REGISTRY.json) - Art Studio scope fence
- [ENDPOINT_TRUTH_MAP.md](../../docs/ENDPOINT_TRUTH_MAP.md) - API surface
- [design_first_workflow_routes.py](../../services/api/app/art_studio/api/design_first_workflow_routes.py) - Router
