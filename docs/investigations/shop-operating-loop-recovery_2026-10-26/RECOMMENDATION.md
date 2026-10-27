# Recommendation

RECOMMENDED_INCREMENT: SHOP-OP-RECORD-001 — an LTB-local, append-only `ShopOperationRecordV1` library with tests: no route, no UI, no authority

## Scope of the increment

**Location:** `services/api/app/physical_engineering/` or a sibling package.
This is a placement question for the owner. Either way it stays inside LTB,
because shop-execution evidence on LTB-designed instruments already lives here
(the SOL-D02 saw lab).

**Record fields:**
- the existing `project_id`
- a caller-named operation key
- `subject_id`
- cited `evidence_id`s
- the observed SHA-256 of the canonical design state at start, for drift *detection* only
- the event (`started` / `completed` / `aborted`)
- operator
- UTC timestamps
- actual minutes
- material lines with explicit quantity and unit

**Behaviors:**
- Persists to an injected directory, as `stored_evidence_repository` does, so it survives a restart.
- Refuses a second `completed` or `aborted` (the SOL-D02 409 pattern).
- A correction is a new record carrying `supersedes_record_id` and a reason. Nothing is edited in place.
- Carries no approval field, never writes `manufacturing_state`, and is never read by a CAM gate (AUTHORITY_BOUNDARY.md).

**Explicitly not in it:**
- an invented operation catalog
- commercial job ids or any LTB↔CNC-PS crosswalk
- cost rates
- thresholds
- routes, client changes, migrations

## Why this one

- It is the missing seam named in MVS_GAP_MATRIX.md. S7, S8 and S9 all need a
  durable per-operation record, and none exists in any scoped repo.
- It is unblocked:
  - it needs no owner ruling (R1–R5)
  - it needs no approved validation policy (R6)
  - it needs no new authority
- It advances the **beginner-guided** app rather than another isolated feature.
  Every guided surface found (Hub, GuidedWorkflow, wizards) failed the same
  way: completion lived in memory or in a bare string list. A guided flow can
  only tell a beginner "next" and "done" from a durable record. This record
  would also be the first thing the soundboard witness writes.

## Deferred, and why

| Deferred | Reason |
|---|---|
| Route and UI for the beginner gate (SOL-E01) | Needs an owner-approved policy (PR #456 has none, R6). Slice 002 found no MVS client host. |
| Hub CNC Prep rewiring (SOL-E04) and the `manufacturing_state` self-assertion (R4) | Authority changes. The order forbids combining them with an increment. R4 deserves its own owner-scoped order. |
| Commercial job crosswalk / ERP bridge | Needs R1 and R2; would otherwise invent a crosswalk |
| Versioned kits | Needs R3, and a job record to pin into first |
| Time-entry UI (`/rmos/time`) | Needs the record this increment creates |
| Variance reporting | Needs both estimate and actual on one key. SOL-D05's fabricated actuals must be excluded (R7). |

## Open owner rulings

| ID | Question |
|---|---|
| R1 | Is LTB `project_id` the job anchor, or does CNC-PS `job_id` own job identity, and through what contract? |
| R2 | Which estimator is canonical for guitar jobs: LTB `business/estimator` or CNC-PS `business/estimates`? |
| R3 | Should a kit be built on LTB BOM templates or on CNC-PS `InstrumentProductV2`? |
| R4 | Should `manufacturing_state` stop being client-writable through PUT design-state? |
| R5 | Does CAM Creation Studio's "job composition" role overlap an LTB shop-floor traveler? |
| R6 | Approve or source the PR #456 policy values |
| R7 | Retire or relabel CAM job-intelligence derived "actuals" |
