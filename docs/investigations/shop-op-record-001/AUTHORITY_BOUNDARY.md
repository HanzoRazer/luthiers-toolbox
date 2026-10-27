# Shop-operation record — authority boundary

This document bounds `ShopOperationRecordV1` as merged in PR #464 and hardened by
`SHOP-OP-RECORD-HARDEN-002`. It does not replace the record or the first-slice
design in `README.md`.

## What the record is

One immutable JSON file is one factual event for one operation on one
CNC-Production-Shop job: `STARTED`, `COMPLETED`, or `ABORTED`. Current state for
a job is `effective_for_job`: the files that no later file supersedes.
Corrections are new files. The original file stays.

The record stores:

- the external `job_id`, always with verification `UNVERIFIED_EXTERNAL_REFERENCE`
- operation id and status
- a measured duration in decimal minutes, when one was measured
- material quantity, unit, and, on a new line, measurement provenance
- opaque evidence references and opaque readiness references, in separate fields
- who attested completion, and when, on a `COMPLETED` file

## What the record is not

The record does not grant authority and does not interpret anyone else's decision.

| Not stored and not inferred | Why |
|---|---|
| `CAM_APPROVED`, `MANUFACTURING_APPROVED`, `SAFE_TO_RUN`, or any release flag | Manufacturing authority is a separate readiness and CAM verdict plus a human authorization. This package does not import CAM generators, readiness mutators, or G-code writers. |
| A verified or revoked job reference | Luthier's Toolbox cannot check a CNC-Production-Shop `job_id`. `VERIFIED_EXTERNAL_REFERENCE` is deferred to `SHOP-JOB-REFERENCE-RESOLVER-001`. A caller cannot set it on this record. |
| Design revision or design digest | That is MVS step S4 (`SHOP-JOB-DESIGN-PIN-001`), not this record. `payload_digest` covers this file's own bytes. |
| An estimate, move-count, default, or BOM quantity used as an actual | Duration basis has one member, `MEASURED`. Material measurement source has only `MANUAL_MEASUREMENT`, `SCALE_READING`, `COUNTED`, and `IMPORTED_MEASUREMENT`. |
| Cost, labor rate, or estimate-versus-actual variance | Later. Multiple duration files are not summed here. Material lines in different units are not combined. |
| A route, screen, timer, or kit/BOM reservation | This package is a library. |

`COMPLETED` means a person attested that this shop operation was completed.
`completed_by` and `completed_at` are that attestation. They do not approve the
design, the CAM package, or the product. Attaching an evidence or readiness
reference does not change status and does not read the referenced decision.

## Job reference

`JobReference.system` is `CNC-Production-Shop`. `job_id` is an opaque non-empty
string. `verification` accepts only `UNVERIFIED_EXTERNAL_REFERENCE`. Creating a
record does not call CNC-Production-Shop and does not look the id up.
`EXTERNAL_JOB_UNVERIFIED` is not an error code of this library: the status on
the record is the fact, and a later consumer decides whether its own workflow
can proceed.

Reconciliation that would add verified or revoked history waits for a real
resolver contract. It must not be smuggled in by overwriting `job_id`.

## Material units

No authoritative unit vocabulary exists for this record.

- CAM translator units are millimeters and inches for toolpaths. This package does not import them.
- BOM `unit` is a free string (`piece`, `set`, `bd_ft`, and similar examples), not a closed list.
- Mesh material units are stiffness and density units with conversion to Pa and kg/m³. Adopting that conversion would invent a policy this record does not have.

The stored rule remains the one from the merged record: a unit is an explicit
lowercase identifier matching `^[a-z][a-z0-9_]*$`. The token is stored as
written. `g` and `kg` are not converted. `mm` and `cm2` are not converted.
Aggregation across units is out of scope.

## Material provenance

A new material line requires:

| Field | Rule |
|---|---|
| `measurement_source` | `MANUAL_MEASUREMENT`, `SCALE_READING`, `COUNTED`, or `IMPORTED_MEASUREMENT` |
| `recorded_by` | Who recorded the observation |
| `observed_at` | Timezone-aware timestamp |
| `source_ref` | Required for `IMPORTED_MEASUREMENT`. Optional for the other three sources. |

`make_operation_record` and a new `FileShopOperationRepository.save` refuse a
line that omits this. A file written before the rule, whose material object is
only `material_ref`, `quantity`, and `unit`, still loads. Its canonical bytes
and `payload_digest` stay the same. Saving that same payload again is
idempotent. A new file that copies the old shape is refused.

## Duration

`minutes` is a positive decimal string. Zero, negative, non-decimal, and a
basis other than `MEASURED` are refused. The string is not rewritten through a
binary float, so a value such as `18.60` stays `18.60`. The unit of the field
is minutes.

## Identifiers

A caller may still supply a `record_id` that passes the existing filename rule.
When `make_operation_record` is called without one, the id is
`sop_{unix milliseconds}_{uuid4 hex}`. Two calls in the same millisecond do not
share an id. This follows the MAINT-DEFER-019 repair: a clock prefix alone is
not an id.

## Persistence constraint

Publishing one new file uses `os.link` from a temporary file in the same
directory, then deletes the temporary file. That is the atomicity this store
implements. The sequence check reads the directory and then writes. It assumes
one writer per directory. Concurrent writers are not supported. Do not describe
this store as crash-safe beyond that link, and do not deploy it as a
multi-writer service without a later concurrency design.

## Package boundary

`app/shop_operations/` imports the standard library and itself. A structural
test fails if a module imports CAM, a readiness mutator, a G-code writer, a
router, a CNC-Production-Shop client, or an estimate/BOM package. The package
exports no route.
