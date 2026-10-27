# SHOP-OP-RECORD-HARDEN-002

Narrow hardening of the shop-operation record merged in PR #464.
`SHOP-OP-RECORD-001` is not reopened. The file-per-event record stays the
canonical model. Schema id `ltb_shop_operation_record` and schema version `1.0`
stay. Stored files from that version stay readable.

## What changed

1. `new_operation_record_id` supplies a collision-safe default id
   (`sop_{milliseconds}_{uuid4 hex}`), the MAINT-DEFER-019 shape. A valid
   caller-supplied id is still accepted.
2. A new material line records `measurement_source`, `recorded_by`,
   `observed_at`, and `source_ref` when the measurement was imported.
   Sources are `MANUAL_MEASUREMENT`, `SCALE_READING`, `COUNTED`, and
   `IMPORTED_MEASUREMENT`. Estimate, derived, move-count, default, unknown,
   BOM, and planned sources are not members.
3. Historical material lines with only `material_ref`, `quantity`, and `unit`
   still round-trip. Their canonical JSON and digest are unchanged. A new file
   in that shape is refused.
4. Duration stays a positive decimal string in minutes. The string is the
   precision. It is not converted to seconds.
5. `docs/investigations/shop-op-record-001/AUTHORITY_BOUNDARY.md` states the
   non-authority boundary.
6. Structural tests reject imports of CAM generators, readiness mutators,
   G-code writers, routers, and estimate or BOM packages, and reject an
   estimate-derived actual on the measurement enums.

## Unit vocabulary

No authoritative vocabulary was adopted.

| Candidate | Why it was not adopted |
|---|---|
| CAM translator `supported_units` (`mm`, `inch`) | Toolpath units, and this package must not import `app.cam`. |
| BOM `Material.unit` | Free string with examples (`piece`, `bd_ft`, `oz`). Not a closed list. |
| Mesh `normalize_unit` | Stiffness and density units that convert to Pa and kg/m³. That is a conversion policy. |

The merged token rule remains: `^[a-z][a-z0-9_]*$`, stored as written, with no
conversion and no cross-unit aggregation.

## Deliberately unchanged

- One JSON file per status event, supersession, and `effective_for_job`
- `STARTED` / `COMPLETED` / `ABORTED`
- `UNVERIFIED_EXTERNAL_REFERENCE` only. No verified or revoked state
- Opaque evidence and readiness string references
- Human completion as `completed_by` and `completed_at`
- Single writer per directory
- No route and no UI
- No service error-code taxonomy

Verified job references wait for `SHOP-JOB-REFERENCE-RESOLVER-001` and a real
CNC-Production-Shop contract.

## Persistence limit

`os.link` publishes a temp file onto the record path, then the temp file is
removed. The sequence check is read-then-write. One writer per directory.
That is the durability this increment claims.

## Rerun

```bash
cd services/api
python -m pytest tests/shop_operations -q --no-cov
```

Local result on this increment: 26 passed.

Also run from `services/api`, all exiting 0: complexity (threshold 15, baseline), file size (500), bare except, fence checker v2, duplication (70 clone groups, threshold 100), manufacturing output inventory `--check` (239 candidates, no new route), execution-class compliance.
