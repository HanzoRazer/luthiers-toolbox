# Recommendation

RECOMMENDED_INCREMENT: SHOP-OP-RECORD-001 — an LTB append-only shop-operation record keyed to the CNC-Production-Shop job_id: library with tests, no route, no UI, no CAM authority

**Sequencing (owner ruling 2026-10-26):** start only after #462 records the
seven rulings (done: OWNER_RULINGS.md) **and is dispositioned**. The record is
derived from the settled ownership and identity map below. It is not designed
alongside open audit conclusions.

## Scope of the first slice (owner ruling 2026-10-26)

**Governing key:** CNC-Production-Shop `job_id` (R1, R5). LTB holds it as an
external reference. No runtime contract between the repos exists today
(JOB_IDENTITY_MAP.md), so the order must state how a `job_id` is accepted and
later reconciled. This audit does not invent that contract.

**Record contents, as ruled:**
- **Operation identity:** which operation on which job. An operation catalog is not invented here.
- **Status:** `started` / `completed` / `aborted`.
- **Measured duration:** with its measurement provenance. Per R7, only completed records with recorded provenance may supply actual time, and a derived or estimated value is never an actual.
- **Material usage:** explicit quantity and unit.
- **Evidence references and readiness references:** kept as separate fields (R5).
- **Human completion:** who completed the operation, and when.

These four kinds of fact must stay separately identifiable (R5):
1. evidence
2. readiness
3. CAM disposition
4. human completion

**Behaviors carried over from existing patterns:**
- **Survives a restart:** persists to an injected directory, as `stored_evidence_repository` (SOL-E01) does.
- **Refuses a repeat:** a second `completed` or `aborted` is refused (the SOL-D02 409 pattern).
- **Corrections append:** a correction is a new record with `supersedes_record_id` and a reason. Nothing is edited in place (the SOL-E01 supersede chain).

**Authority:** none. The record:
- carries no approval field
- never writes `manufacturing_state`
- is never read by a CAM gate (R4, AUTHORITY_BOUNDARY.md)

Human completion records that a person finished an operation. It does not
authorize manufacturing.

**Explicitly not in it:**
- an operation catalog
- cost rates
- thresholds (R6)
- the CNC-PS manifest's LTB design references (S4; a separate order)
- routes, client changes, migrations

## Why this one

- **It is the missing seam** named in MVS_GAP_MATRIX.md. S7, S8 and S9 all need a durable per-operation record, and none exists in any scoped repo.
- **Every dependency is ruled:**
  - key: R1/R5
  - host: R5
  - authority boundary: R4
  - actual-time provenance: R7
- **It needs nothing that is still missing:** no approved policy (R6), and no new authority.
- **It advances the beginner-guided app** rather than another isolated feature. Every guided surface found (Hub, GuidedWorkflow, wizards) kept completion in memory or in a bare string list. A guided flow can only tell a beginner "next" and "done" from a durable record. This record would also be the first thing the soundboard witness writes.

## Ruled follow-on work (each its own order; not recommended next)

| Work | Owner | Basis |
|---|---|---|
| LTB immutable design revision/snapshot id, and the CNC-PS manifest references to it (`project_id`, revision, design-package sha256, generator identity/version) | LTB + CNC-PS | R1; MVS S4 |
| Label the LTB estimator a non-binding preview; guarantee it never writes an accepted estimate | LTB | R2 |
| Correct job-insights actuals (`DERIVED_ESTIMATE`, "No actual recorded", exclusion from variance) | LTB | R7 |
| Independent CAM/readiness disposition on the Les Paul route before the DXF leaves quarantine | LTB | R4 |
| Commercial-kit layer (quantities, units, substitutions, BOM semantics) | Follows the CNC job/configuration contract | R3 |
| Beginner gate route and UI | LTB, after first real soundboard policy evidence | R6 |
| Time-entry UI, guided traveler screens, variance report | LTB, after SHOP-OP-RECORD-001 | R5, R7 |

## Owner rulings

All seven were ruled 2026-10-26. Full text: OWNER_RULINGS.md.

| ID | Ruling |
|---|---|
| R1 | CNC-PS `job_id` is the job of record. Its manifest must reference LTB `project_id`, an immutable design revision, the design-package sha256, and generator identity/version. |
| R2 | CNC-PS is the official estimator. The LTB estimator is a labeled non-binding preview. |
| R3 | The product definition plus digest is configuration identity. The kit layer is unbuilt. |
| R4 | `manufacturing_state` is a workflow assertion only. The LP DXF stays quarantined until an independent readiness disposition is required. |
| R5 | Split. CCS assembles and reviews CAM packages. LTB hosts the guided interface and operation records keyed to `job_id`. |
| R6 | No production thresholds. The beginner path stays disconnected pending the first real soundboard policy basis. |
| R7 | Correct the screen. Estimates never populate `actual_time_s`, and derived values are excluded from variance. |
