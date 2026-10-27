# MVS gap matrix

Status vocabulary:
- **AVAILABLE:** a canonical artifact does the step today.
- **ADAPT:** useful capability exists and needs a bounded contract adapter.
- **BUILD:** nothing reusable exists.
- **BLOCKED:** cannot advance without an owner ruling or an unmerged dependency.

The artifact column names the canonical artifact for AVAILABLE steps, or the
best existing candidate otherwise.

| Step | Operating-loop step | Status | Artifact | Basis |
|---|---|---|---|---|
| S1 | Create a guitar job with a persistent identity | AVAILABLE | SOL-A06 | R1: CNC-PS `job_id` is the job of record. The merged job-quote CLI (PR #19) creates it with replay-safe ids and publishes without replacement. It is an operator CLI, not yet a guided surface. Its link to the LTB design is S4. |
| S2 | Select a reusable commercial kit or configuration | ADAPT | SOL-C07 | A CNC-PS job pins a reusable product *configuration* by content (manifest source: role, record_id, snapshot, sha256). R3 ruled: this is canonical configuration identity. The commercial-kit layer (quantities, units, substitutions, BOM semantics) is still missing (SOL-C08). |
| S3 | Preserve the quote or estimate revision | AVAILABLE | SOL-B04 | R2: CNC-PS is the official estimator. Its stored, versioned estimate feeds bid and proposal, and the job manifest pins the estimate input by sha256. The LTB estimator must be labeled a non-binding preview (SOL-B01, ADAPT); that is not a gap in this step. |
| S4 | Pin the design-package revision used by the job | BUILD | SOL-A01 | R1 requires the CNC-PS manifest to reference LTB `project_id`, an immutable design revision/snapshot id, the design-package sha256 and generator identity/version. None exist: LTB overwrites design state and has no revision id, and nothing invalidates on change. |
| S5 | Reserve the identified soundboard or material set | BUILD | SOL-A08 | No material, lot or reservation record. Evidence `subject_id` is a bare string. |
| S6 | Display evidence, validation and CAM readiness without authority leakage | BLOCKED | SOL-E01 | R6: the beginner path stays disconnected until the first real soundboard program documents a policy basis with a named approver. No policy becomes ACTIVE from test values. CAM readiness (SOL-E02) is live but unrendered. `manufacturing_state` is a workflow assertion only (R4). |
| S7 | Present the next approved shop operation in plain language | BUILD | SOL-E10 | R5: LTB hosts the guided interface, and Creation Studio is not the traveler. There is no persisted job/operation record to derive "next" from. `next_step_hint` (SOL-E05) is RMOS-only and unexposed. |
| S8 | Record actual labor and material consumption | BUILD | SOL-D09 | R5: LTB operation records keyed to CNC-PS `job_id`. Only the saw lab records actuals today (SOL-D02), with no job or op key. The op-keyed model (SOL-D03) is uncalled. |
| S9 | Compare actual cost and time with the estimate | BUILD | SOL-B05 | R2/R5/R7: compare the CNC-PS official estimate with LTB completed operation records on `job_id`. Derived values are excluded, and SOL-D05 must stop putting estimates in `actual_time_s`. No such comparison exists. |

## Smallest contiguous segment possible today

After the rulings, **S1 → S3 is a contiguous segment that exists today in
CNC-Production-Shop.** An operator CLI creates the job of record, pins the
product configuration (S2, configuration part) and estimate input by sha256,
and writes the official estimate, bid and proposal.

It is not beginner-guided. It stops at the repo boundary: no LTB design
revision is pinned (S4), and nothing downstream records operations. S2 is ADAPT
only because the commercial-kit layer is missing; configuration identity is
canonical.

In LTB the only reachable pieces are still the instrument project (a design
record, not the job) and a CAM-readiness refusal visible as an API 422 body.

AVAILABLE here means "a canonical artifact does the step today". It became
true for S1 and S3 through ownership rulings, not new code.

## Missing seam for the first-soundboard witness

There is **no durable record of a shop operation performed on a job**: which
operation, on which CNC-PS job and subject, started and completed by whom, with
what actual time and material, and corrected only by superseding.

Without that record:
- S7 cannot say what is next.
- S8 has nowhere to write.
- S9 has nothing to compare.

S6 would also have no place to attach the gate verdict it displays.
