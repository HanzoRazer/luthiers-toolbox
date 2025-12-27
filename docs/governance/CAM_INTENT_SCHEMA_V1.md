# CAM Intent Schema v1.0 (Frozen)

**Status:** Canonical / Frozen
**Applies to:** RMOS CAM entrypoints (HTTP, SDK, CLI, internal callers)
**Source of truth:** `services/api/app/rmos/cam/schemas_intent.py` (`CamIntentV1`)

## Purpose

`CamIntentV1` is the **request envelope** for CAM operations. It is **not**:
- a toolpath format
- a RunArtifact
- an output/report schema

It exists to normalize and stabilize:
1) validation
2) engine routing (mode selection)
3) feasibility + planning inputs
4) persistence mapping into runs_v2 + attachment store

## Invariants

1. **Schema changes are intentional and gated**
   - Any change to `CamIntentV1` must update the pinned schema hash and this doc.
2. **User payload is the source of creativity**
   - RMOS may normalize/validate, but does not invent design goals.
3. **Mode-specific details live in `design`**
   - The envelope stays stable; domain detail is isolated.

## Fields

### Top-level

| Field | Type | Required | Notes |
|------|------|----------|------|
| `schema_version` | `str` | yes (default) | Always `"cam_intent_v1"` in v1. |
| `intent_id` | `str \| null` | no | Caller-provided correlation/idempotency key. |
| `mode` | enum | yes | v1: `router_3axis`, `saw`. |
| `units` | enum | no | v1: `mm` (default), `inch`. |
| `tool_id` | `str \| null` | no | Optional catalog reference. |
| `material_id` | `str \| null` | no | Optional catalog reference. |
| `machine_id` | `str \| null` | no | Optional catalog reference. |
| `design` | `object` | **yes** | Mode-specific design descriptor. |
| `context` | `object` | no | Operational context (limits, feeds/speeds caps). |
| `options` | `object` | no | Execution options (preview/quality flags, tolerances). |
| `requested_by` | `str \| null` | no | Optional user/session label (not auth). |
| `created_at_utc` | `datetime \| null` | no | Optional caller timestamp; server may set if absent. |

### Mode expectations (non-exhaustive)

#### `router_3axis`
`design` should include geometry + operation hints, e.g.:
```json
{
  "operation": "pocket",
  "geometry": {"type": "polyline", "points": [[0,0],[10,0],[10,10],[0,10],[0,0]]},
  "depth_mm": 2.0
}
```

#### `saw`
`design` typically includes kerf/stock/cut descriptors, e.g.:
```json
{
  "kerf_width_mm": 2.0,
  "stock_thickness_mm": 10.0,
  "cuts": [{"type":"rip","length_mm":300,"depth_mm":10}]
}
```

## Contract Freeze Guard

CI enforces a pinned schema hash:
- Script: `python -m app.ci.check_cam_intent_schema_hash`
- Pin constant: `CAM_INTENT_SCHEMA_HASH_V1` in `schemas_intent.py`

### Initial pinning workflow (one-time)
From `services/api/`:
```bash
python -m app.ci.check_cam_intent_schema_hash --print
```
Copy the output into:
`services/api/app/rmos/cam/schemas_intent.py` -> `CAM_INTENT_SCHEMA_HASH_V1`

## Versioning policy

- **Breaking envelope change** -> new schema version (v2) with parallel support window
- **Non-breaking doc-only changes** -> update this doc only

---

*Last updated: 2025-12-26*
