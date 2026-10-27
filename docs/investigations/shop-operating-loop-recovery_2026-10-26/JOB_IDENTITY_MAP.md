# Job identity map (track A)

**Finding:** no one identifier follows a guitar from quote to finished
operation. Two persistent identities exist:
- LTB `project_id`, a UUID in Postgres (SOL-A01)
- CNC-PS `job_id`, caller-supplied and stored in file records (SOL-A06)

Nothing stored links one to the other. Inside LTB, the only stored link from
a project to execution is `ProjectArtifactRef.run_id`, and it is one-way and
caller-asserted.

## Identifiers found

| Identifier | Owner row | Persistent? | Revisions |
|---|---|---|---|
| `project_id` | SOL-A01 | Yes. UUID, `projects` table. | **Overwritten.** PUT design-state replaces the JSONB blob. "Revision" is `updated_at`. |
| `run_id` (RMOS) | SOL-A03 | Yes. Date-partitioned JSON files. | Create-once (`store.py:205`). Mutable fields are rewritten in place (`store.py:225`). |
| `workflow_session_id` | SOL-E05 | Yes. `workflow_sessions` table. | `session_json` is overwritten. |
| saw `batch_execution_artifact_id` / `parent_id` chain | SOL-D02 | Execution and job-log are runs_v2 artifacts (append-only). Spec, plan and approve are **in memory**. | Append-only |
| `evidence_id` / `subject_id` | SOL-E01 | Injected JSON directory, not wired | Frozen records with a `supersedes_evidence_id` chain: the only real revision chain found |
| `job_id`, `estimate_id`, `bid_id`, `proposal_id` (CNC-PS) | SOL-A06 | Files written by the CLI, "publish without replacement" (`236527c`) | `revision` is a display string, not a chain |
| `package_reference` (CAM Assist) | SOL-A07 | Schema only | Optional, self-declared federation fields |
| api_v1 `job_id` | SOL-A04 | **No.** sha256(name+time), never stored. | — |

## Links

Status vocabulary:
- **PROVEN** means a stored field or a schema contract carries the link, cited as `stored:`.
- **UNKNOWN** means no evidence either way.
- **ABSENT** means a bounded search found no field.

No link is proven by name matching.

| From | To | Status | Evidence |
|---|---|---|---|
| LTB project | RMOS run | PROVEN | stored: `ProjectArtifactRef.run_id` at services/api/app/schemas/instrument_project.py:613, with `project_revision` at :654. The router itself calls the project side caller-asserted. |
| RMOS run | LTB project | ABSENT | `grep project_id\|job_id\|order_id services/api/app/rmos/runs_v2/*.py` = 0 |
| RMOS run | workflow session | PROVEN | stored: `RunArtifact.workflow_session_id` at services/api/app/rmos/runs_v2/schemas.py:370 |
| saw job-log | saw execution | PROVEN | stored: `parent_id=batch_execution_artifact_id` at services/api/app/saw_lab/batch_router.py:348 |
| saw execution | LTB project or job | ABSENT | No project or job field on any saw-lab request schema |
| evidence record | physical subject (e.g. `plate-007`) | PROVEN | stored: `subject_id` at services/api/app/physical_engineering/evidence_artifact_v1.py:69. This is a string, not a reference to any material record. |
| evidence `subject_id` | material / soundboard record | ABSENT | No material, lot or reservation record exists (SOL-A08) |
| CNC-PS job | estimate, bid, proposal | PROVEN | stored: required fields in CNC-Production-Shop schemas/workflows/job_quote_manifest_v1.schema.json:87 |
| CNC-PS job | product configuration (by content) | PROVEN | stored: manifest `sources[]` entries require role, record_id, snapshot_ref and sha256 at CNC-Production-Shop schemas/workflows/job_quote_manifest_v1.schema.json:28. Product role loaded at business/workflows/loading.py:385, `product_id` cross-checked at :404. |
| CNC-PS job | LTB project / design revision | ABSENT | Neither `job_quote_request_v1` nor `job_quote_manifest_v1` has a design, project or run field |
| LTB project | CNC-PS job | UNKNOWN | No field on either side as built, and no crosswalk invented. **R1 makes it required:** the CNC-PS manifest must reference LTB `project_id`, an immutable design revision/snapshot id, the design-package sha256 and generator identity/version (MVS S4, unbuilt). |
| LTB estimate (SOL-B01) | project or design revision | ABSENT | `EstimateResult` has no id, revision or design hash |
| CAM Assist package | CNC-PS job | UNKNOWN | Schema exists (SOL-A07); no consumer in LTB or CNC-PS |
| RMOS JobLog `op_id` | a shop operation definition | UNKNOWN | `op_id` is a free optional string (feedback/schemas.py:80). There is no operation catalog. |
| design-state change | invalidation of approvals or artifact refs | ABSENT | `invalidat` hits only a docstring (instrument_project.py:118). No code resets `manufacturing_state` or `manufacturing_artifacts`. |

## Answers to §6A

- **Persistent:** LTB `project_id` and RMOS `run_id`. CNC-PS ids persist only as files the CLI writes.
- **Immutable or overwritten:** project design state is overwritten. Runs are create-once with in-place mutable fields. Only physical-engineering evidence keeps a supersede chain.
- **Tied to one job:** quote ↔ design ↔ CAM ↔ execution cannot be tied by a stored field today. Inside LTB the only stored hop is project → run. Inside CNC-PS a job pins its commercial sources (product configuration, estimate input) by sha256 snapshot, which is the strongest revision pin found. It stops at the repo boundary.
- **Invalidation:** a changed design input invalidates nothing.
- **Cross-repo:** there are no explicit ID contracts in use. CAM Assist's handoff schema is the only candidate, and nothing consumes it.
