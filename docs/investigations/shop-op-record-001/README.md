# SHOP-OP-RECORD-001 — shop-operation record (first slice)

| | |
|---|---|
| **Authority for this work** | Owner GO, 2026-10-26, after PR #462 merged. The increment was recommended by SHOP-OPERATING-LOOP-RECOVERY-001 (`docs/investigations/shop-operating-loop-recovery_2026-10-26/RECOMMENDATION.md`) and bounded by its OWNER_RULINGS.md. |
| **Baseline** | `origin/main` `93f9fa9a` (merge of #462) |
| **Code** | `services/api/app/shop_operations/`, a new self-contained domain package |
| **Tests** | `services/api/tests/shop_operations/` |
| **Status** | Draft PR. Library only. |

## What it is

`ShopOperationRecordV1` is one event in the life of one operation on one job:
STARTED, COMPLETED or ABORTED. `FileShopOperationRepository` stores those
events durably and append-only.

They are the factual substrate that time entry, guided screens and
estimate-versus-actual reporting will later read. None of those layers is
built here.

## The owner's boundaries, and where each is enforced

| Boundary (owner GO) | Enforcement |
|---|---|
| Key records to the CNC-Production-Shop `job_id` | `JobReference.system` must equal `CNC-Production-Shop`. Every record carries one. Queries are per `job_id`. |
| Do not pretend LTB can verify that external id; say so explicitly | `JobReferenceVerification` has one member, `UNVERIFIED_EXTERNAL_REFERENCE`. Any other value is refused: "no job resolver exists". |
| Do not invent a cross-repository lookup | The package imports nothing outside `app.shop_operations` and makes no network or file access outside its injected directory. |
| No design fingerprints (that is S4) | No design, digest-of-design or fingerprint field. A test fails on field names containing `design_`, `fingerprint`, `sha256`. The record's own `payload_digest` is integrity of the record bytes, not a design pin. |
| Record only operation identity/status, measured duration and provenance, material quantity/unit, separate evidence/readiness references, human completion | These are the only fact fields. Beyond them the record carries only bookkeeping: who recorded the event and when, and the correction link. |
| Derived duration must never become an actual | `DurationBasis` has one member, `MEASURED`. `DERIVED_ESTIMATE` and any other basis is refused: "never an actual". An unmeasured operation has *no* duration, never a guess. |
| Evidence and readiness references stay separate | Two fields. A reference appearing in both is refused. |
| Add no CAM or manufacturing authority | No approval, release, CAM or manufacturing field (tested by name). It never writes `manufacturing_state`, and nothing reads the record as a gate. Human completion records that a person finished; it authorizes nothing. |
| Stop at a draft PR | Yes |

## Record rules

**Status:**
- **STARTED** has no duration and no material usage yet.
- **COMPLETED** requires `human_completion` (who and when). No other status may carry it.
- **ABORTED** may carry a duration and material used, for example scrap.

**Value formats:**
- **Duration:** positive decimal minutes as a string, plus method, measured-by and source id.
- **Material:** `material_ref`, a positive decimal quantity string, and a lowercase unit identifier.
- **Times:** must be timezone-aware.

**Integrity:** a SHA-256 over the canonical payload. A changed field fails on read (`DIGEST_MISMATCH`).

## Repository rules (per `job_id` + `operation_id`, superseded records excluded)

- **Order:**
  - STARTED comes first, and only once.
  - At most one terminal event (COMPLETED or ABORTED) follows, no earlier than the start. A second one is refused.
  - A retry after ABORTED is a new `operation_id`.
- **Corrections append.** A correction is a new record naming `supersedes_record_id` with a `correction_reason`. The original is kept unchanged. Only a not-yet-superseded record of the same job, operation and status can be corrected. `effective_for_job` hides superseded records; `list_for_job` keeps the full history.
- **Durability:**
  - one JSON file per record
  - published atomically with `os.link`
  - re-read by a new object or a new process
  - the same bytes saved twice are idempotent; different bytes under an existing id are refused
- **Exclusive directory:** any foreign JSON file is treated as corruption.
- **Concurrency:** the sequence check reads, then writes. It assumes **one writer per directory**. Concurrent writers are not supported in this slice.

## Placement

`app/shop_operations/` is a new Layer-4 domain module. It does not import
`physical_engineering`, because `ARCHITECTURE_INVARIANTS.md` Rule 4 forbids
domain-to-domain imports. It repeats that package's small canonical-JSON and
atomic-publish pattern instead. The duplication gate reports 0 clone groups.

## Deliberately not built

| Not built | Why / owner |
|---|---|
| A route, client screen, migration or database table | First slice is a library (owner GO) |
| A resolver or contract to verify a `job_id` | None exists. Represented as `UNVERIFIED_EXTERNAL_REFERENCE` until one does. |
| An operation catalog | Operation ids are caller-named; nothing is invented |
| Design revision pins | MVS S4 (R1) |
| Cost, labor rates, estimate comparison | Later layers (R2, R7) |
| Thresholds or validation policy | R6: unapproved pending the first real soundboard |
| Correction of the CAM job-insights "actuals" | Its own order (R7) |

## Rerun

```bash
cd services/api
python -m pytest tests/shop_operations -q --no-cov
```

## Addendum — SHOP-OP-RECORD-HARDEN-002 (2026-10-27)

PR #464 remains the first slice described above. This addendum does not replace it.

`SHOP-OP-RECORD-HARDEN-002` keeps `schema_id` `ltb_shop_operation_record` and the file-per-event store. Schema 1.0 files stay readable and are not rewritten. New writes use schema 1.1, which adds material measurement provenance. A 1.0 material line is reported as `LEGACY_PROVENANCE_UNAVAILABLE`. No recorder, source, or observation time is invented for it.

The versioning decision, unit audit, id factory, and limits are in `HARDEN_002.md`. The authority boundary is in `AUTHORITY_BOUNDARY.md`.
