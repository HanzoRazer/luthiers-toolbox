# Estimate versus actual (track B)

**Finding:** there are two estimate engines with incompatible contracts, one
in LTB and one in CNC-PS, and no actual-cost record anywhere. The only
recorded actuals are saw-lab seconds and part counts, and they share no key
with any estimate. No feedback loop updates a cost or time estimate.

## Estimate side

| Row | What | Stored or recalculated | Revision-pinned | Keys |
|---|---|---|---|---|
| SOL-B01 | LTB parametric engineering estimator (WBS, complexity, learning curve, yield) + `/estimate/quote` | Recalculated every call. Presets and history are in browser localStorage only. | No | None. WBS `task_id` (e.g. `DES_001`) in hours. |
| SOL-B04 | CNC-PS guitar estimate → bid → proposal | Written as JSON records by the job-quote CLI (SOL-A06) | Schema'd `quote_revision_v1`; job request carries a display `revision` | `estimate_id`, `bid_id`, `proposal_id`, `job_id` |
| SOL-D06 | LTB G-code cycle-time estimator / what-if | Recalculated | No | Seconds per program |
| SOL-C01 | LTB BOM/COGS templates | In-memory class dicts | No | `material_id`, `InstrumentType` |

## Actual side

| Row | What | Persisted | Keys |
|---|---|---|---|
| SOL-D02 | Saw-lab job-log: `cut_time_s`, `setup_time_s`, `total_time_s`, `parts_ok`, `parts_scrap`, operator | Append-only runs_v2 artifacts | `batch_execution_artifact_id`. No job, project or op id. |
| SOL-D03 | RMOS JobLogService (setup/cut/total seconds + `op_id`) | Would write artifacts. **No caller.** | `execution_artifact_id`, `op_id` |
| SOL-B03 | Cost attribution facts | Append-only JSONL. **No caller.** | `manufacturing_batch_id`, `instrument_id`. Telemetry units, not money. |
| SOL-D05 | CAM job-intelligence "actual" | Reads `data/cam_job_log.jsonl`, which **nothing writes** | When actual is missing it is set to `move_count*0.1` or to the estimate itself |

## Feedback

- The only feedback loop is saw-lab learning, folded into SOL-D02. It adjusts feed, RPM and depth-of-cut multipliers for future plans. It updates no cost or time estimate.
- `estimatorStore.linkedRunId` (SOL-B02) declares the intended estimate→actual link. Nothing imports the store.

## Answers to §6B

- **Stored or recalculated:** LTB estimates are recalculated. CNC-PS estimates are stored as files.
- **Revision-pinned:** LTB estimates are not. CNC-PS records carry ids and a display revision, but nothing ties them to a design revision.
- **Actuals on the same job and operation:** no. No actual shares a key with an estimate (SOL-B05 MISSING).
- **Feedback into future estimates:** none for cost or time.
- **Commercial or engineering authority:** cost is commercial only. No gate consumes it; LTB labels the business router `LANE: UTILITY`.
- **Truthfulness risk:** SOL-D05 shows derived numbers labelled "actual". Ruled (R7): estimates never populate `actual_time_s`, and derived values are excluded from estimate-versus-actual.

## Ownership conflict

SOL-B01 and SOL-B04 both estimate guitar builds, with different inputs, keys
and persistence.

**Ruled (R2, 2026-10-26):**
- CNC-PS (SOL-B04) is the official estimator, with one official estimate revision per job.
- The LTB estimator (SOL-B01) is a clearly labeled non-binding design preview that must never silently replace or update a job's accepted estimate.
- Actuals for S9 come from LTB completed operation records keyed to the CNC-PS `job_id` (R5).
