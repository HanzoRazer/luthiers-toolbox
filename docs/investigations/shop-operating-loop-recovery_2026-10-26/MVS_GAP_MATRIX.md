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
| S1 | Create a guitar job with a persistent identity | ADAPT | SOL-A01 | LTB `project_id` is persistent and live, but it is a design project, not a commercial job. CNC-PS `job_id` (SOL-A06) is commercial and file-based. No link exists between them (R1). |
| S2 | Select a reusable commercial kit or configuration | ADAPT | SOL-C07 | A CNC-PS job pins a reusable product *configuration* by content (manifest source: role, record_id, snapshot, sha256). R3 ruled: this is canonical configuration identity. The commercial-kit layer (quantities, units, substitutions, BOM semantics) is still missing (SOL-C08). |
| S3 | Preserve the quote or estimate revision | ADAPT | SOL-B04 | CNC-PS writes revision-schema'd estimate/bid/proposal records. LTB estimates are not stored. Canonical estimator unresolved (R2). |
| S4 | Pin the design-package revision used by the job | BUILD | SOL-A02 | Project design state is overwritten. `ProjectArtifactRef` pins run hashes, not a design revision. Nothing invalidates on change. |
| S5 | Reserve the identified soundboard or material set | BUILD | SOL-A08 | No material, lot or reservation record. Evidence `subject_id` is a bare string. |
| S6 | Display evidence, validation and CAM readiness without authority leakage | BLOCKED | SOL-E01 | Validation needs an owner-approved policy (PR #456 open, no approved values, R6). CAM readiness (SOL-E02) is live but unrendered. `manufacturing_state` is ruled a workflow assertion only (R4). |
| S7 | Present the next approved shop operation in plain language | BUILD | SOL-E10 | No persisted job/operation record to derive "next" from. `next_step_hint` (SOL-E05) is RMOS-only and unexposed. |
| S8 | Record actual labor and material consumption | BUILD | SOL-D09 | Only the saw lab records actuals (SOL-D02), with no job or op key. The op-keyed model (SOL-D03) is uncalled. |
| S9 | Compare actual cost and time with the estimate | BUILD | SOL-B05 | No shared key between any estimate and any actual. SOL-D05 fabricates actuals. |

## Smallest contiguous segment possible today

There is **no end-to-end segment**. The only steps a beginner can reach in
sequence today are:
- S1 in its LTB form: create an instrument project in the Hub.
- A CAM-readiness refusal at S6, visible only as an API 422 body.

Neither step records anything a later step can consume.

## Missing seam for the first-soundboard witness

There is **no durable record of a shop operation performed on a job**: which
operation, on which project and subject, started and completed by whom, with
what actual time and material, and corrected only by superseding.

Without that record:
- S7 cannot say what is next.
- S8 has nowhere to write.
- S9 has nothing to compare.

S6 would also have no place to attach the gate verdict it displays.
