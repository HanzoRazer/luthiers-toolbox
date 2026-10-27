# Time capture (track D)

**Finding:** no labor timer exists. The `/rmos/time` view (SOL-D01) is a
routed mock: it has no backend, and its timer never advances. The only working
time capture is the saw-lab job-log (SOL-D02), which records machine-run
seconds per saw execution and is not tied to a job or an operation. The only
model that carries execution, operation and actual time together (SOL-D03) has
no caller.

| Row | Kind | Tied to job | Tied to operation | Survives restart | Auditable correction | Comparable with an estimate |
|---|---|---|---|---|---|---|
| SOL-D01 `TimeTrackingView` | UI mock | Free-text project | Free-text task | **No.** Vue ref only. | No | No |
| SOL-D02 saw job-log + execution lifecycle | Working API (no client caller) | No (saw execution artifact) | No `op_id` | **Yes** (runs_v2 files) | Append-only. A correction is a new artifact with no supersede link. | Seconds; no shared key |
| SOL-D03 RMOS JobLogService | Disconnected library | `execution_artifact_id` | **`op_id`** (optional string) | Would write artifacts | No | Seconds |
| SOL-D04 cam_core saw JobLog | Disconnected; client calls a dead route | `run_id` | `op_type` | JSON files | No | — |
| SOL-D07 archived `saw_joblog_models.py` | Pre-rewrite code | `run_id` | — | — | — | Has `actual_time_s` |
| SOL-D05 CAM job intelligence | Live read side | `run_id`/`job_id` | — | Reads a file nothing writes | — | **Fabricates actuals** |
| SOL-D06 cycle-time estimators | Estimate only | — | Per program | — | — | Estimate side |
| SOL-D08 CNC-PS Eco-Loom capture | Blank template | — | Per operation (planned) | — | — | Minutes (planned) |

## Durability and correction

- Start/stop events that survive a restart exist only in SOL-D02's execution
  lifecycle (start / confirm / complete / abort, with 409 on a repeat), as
  runs_v2 artifacts.
- No time record anywhere supports an auditable manual correction. Grep for
  `correct|supersede|amend` near time models found nothing. The pattern that
  does exist is physical-engineering evidence's `supersedes_evidence_id`
  (SOL-E01).

## Dead client calls (observed, not changed)

- `packages/client/src/components/saw_lab/SawBatchPanel.vue:365` posts to
  `/api/saw/joblog/run`, which has no backend route.
- `packages/client/src/api/sawLab.ts:195` calls `/api/joblog/saw_runs`. That
  router is recorded as removed at `system_manifest.py:49`.

Per the order, this audit retires and fixes nothing.
