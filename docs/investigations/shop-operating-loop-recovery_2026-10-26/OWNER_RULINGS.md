# Owner rulings

Status as of 2026-10-26: **2 ruled (R3, R4), 5 open (R1, R2, R5, R6, R7).**

Further decisions from the same owner message:
- The Les Paul DXF stays quarantined.
- The preset-ID CI defect is separated: MAINT-DEFER-019, repaired in draft PR #463.
- SHOP-OP-RECORD-001 does not start until every ruling below is closed and this package is final.
- PR #462 stays draft. The unrelated CI failure does not count against the audit.

Dependency order for the open rulings:
- **R1** (job anchor) and **R5** (traveler host) decide where and on what key SHOP-OP-RECORD-001 is built.
- **R2** decides S3/S9.
- **R6** decides S6.
- **R7** is independent.

---

## R1 — Job of record (OPEN)

**Question.** Which identifier is the job of record, and what *stored* field
links the other system to it?

- LTB `project_id`: a persistent UUID in the `projects` table, but a design project. Design state is overwritten on save.
- CNC-PS `job_id`: caller-supplied, commercial, written into a job-quote manifest whose sources are pinned by sha256.

**Evidence.**
- Neither the CNC-PS `job_quote_request_v1` / `job_quote_manifest_v1` schemas nor any LTB record carries the other's id (JOB_IDENTITY_MAP.md, link row "LTB project ↔ CNC-PS job": UNKNOWN).
- No crosswalk was invented.

**Options.**
- **(a)** CNC-PS `job_id` is the job of record. The job manifest gains the LTB `project_id` plus a design-state digest as a pinned source, reusing its existing role/record_id/snapshot/sha256 pattern.
- **(b)** LTB `project_id` is the job of record. CNC-PS quote requests reference it.
- **(c)** A new neutral job id that both reference.

**Evidence leans to (a).** CNC-PS is the only system that already pins sources
by content, and the frozen decision names it the likely commercial-job owner.
Under (a), SHOP-OP-RECORD-001 would key on LTB `project_id` and carry the
CNC-PS `job_id` as an external reference.

**Unblocks:** S1, S4, and the key of SHOP-OP-RECORD-001.

## R2 — Canonical estimator (OPEN)

**Question.** Which estimator is canonical for a guitar job?

- **LTB `business/estimator` (SOL-B01):** WBS, complexity, learning curve. Recalculated per call, never stored. Live UI at `/business/estimator`.
- **CNC-PS `business/estimates` (SOL-B04):** stored, schema'd records that feed the bid and proposal, pinned per job.

**Options.**
- **(a)** CNC-PS is canonical. The LTB estimator becomes a design-time preview labelled non-binding.
- **(b)** LTB is canonical, and CNC-PS consumes its output through a contract.
- **(c)** Both are kept with distinct, written roles.

**Evidence leans to (a).** Only CNC-PS keeps a revision a job can pin.

**Unblocks:** S3, and the estimate side of S9.

## R3 — Kit and configuration base (RULED 2026-10-26)

**Question as asked:** should a kit be built on LTB BOM templates or on the
CNC-PS product definition (`GuitarProductDefinitionV1`, already pinned per job
by sha256)?

**Ruling:** S2 is ADAPT, not BUILD. The versioned
`guitar_product_definition_v1` snapshot and SHA-256 already provide
configuration identity. The missing work is the commercial-kit layer:
quantities, units, substitutions and BOM semantics.

**Recorded as:**
- SOL-C07 is RETAIN_CANONICAL (configuration identity).
- SOL-C08 stays MISSING_BUILD (the kit layer).
- SOL-C01 stays ADAPT.

**Not decided by the ruling:** which repo hosts the kit layer. It follows R1/R2.

## R4 — Self-set CAM approval (RULED 2026-10-26)

**Question as asked:** should `manufacturing_state` stop being client-writable
through PUT design-state, given that it is a G-code precondition?

**Ruling:**
- The flag is a project workflow assertion only, not manufacturing authority.
- Before `LesPaul_CAM_Closed.dxf` can leave quarantine, the surviving route must require an independently produced CAM/readiness disposition.
- Clearing the DXF must not make this boolean the effective release gate.
- The Les Paul DXF stays quarantined: its block is protecting the system from a latent authority bypass.

**Recorded as:**
- SOL-E03 has authority NONE and is SUPERSEDED as a release input by an independent readiness disposition (SOL-E02 lineage).
- The release precondition is a ruled requirement, **not implemented** in this evidence-only order.
- Any order that proposes clearing the DXF must first satisfy it.

## R5 — Guided traveler ownership vs CAM Creation Studio (OPEN)

**Question.** Does CAM Creation Studio's ratified role include a shop-floor job
traveler (next operation, why blocked, completion, actuals)? The roles in
question are "guided authoring and progressive disclosure" and "artifact
assembly and job composition" (product boundary §4 items 4–5, ratified
2026-08-05). Or are those roles limited to CAM-program authoring, packaging and
machining education?

**Evidence.**
- The CCS boundary assigns operator-facing job composition to CCS.
- The LTB MVS lineage (001–004) assumes an LTB-hosted guided shop-floor surface.
- No code in either repo implements a traveler (SOL-E10 MISSING).

**Options.**
- **(a)** CCS is CAM authoring and packaging only. The shop-floor traveler and its operation record belong to LTB.
- **(b)** The traveler belongs to CCS, and LTB supplies evidence and readiness verdicts only.
- **(c)** Split: CCS composes the CAM package; LTB records operations against the job.

**Unblocks:** the host of S7 and the home of SHOP-OP-RECORD-001.

## R6 — Validation policy values (OPEN; PR #456)

**Question.** Approve, with a named source, values for the two fields that
`docs/investigations/ltb-mvs-validation-policy-004/POLICY_FIELD_AUTHORITY.md`
(on PR #456 head `7a42854e`, not yet on main) leaves without an approver or source: `max_test_removal_mm` and
`min_test_remaining_thickness_mm`. Alternatively, rule that the beginner
proposal gate stays unrouted until they exist.

**Evidence.**
- PR #456 ships the record, repository and selector.
- The selector fails closed with no approved record.
- The fixture numbers 0.6 and 2.5 are test-only.

This audit proposes **no** values: inventing an engineering threshold is a stop
condition.

**Unblocks:** S6. The beginner gate's route and UI depend on it.

## R7 — Fabricated "actuals" in CAM job intelligence (OPEN)

**Question.** Retire, relabel or fix SOL-D05?

- `/api/cam/job_log/insights/*` (live, rendered by `CamJobInsightsPanel.vue:130`) reports `actual_time_s`.
- When no actual exists it substitutes `move_count × 0.1` or the estimate itself (`job_intelligence_router.py:107-110`).
- Its writer, `append_job_log_entry`, has no production caller, so every displayed "actual" is derived.

**Options.**
- **(a)** Relabel: return a null actual with a `derived` flag, and show "no actual recorded".
- **(b)** Retire the panel and route until real actuals exist (SHOP-OP-RECORD-001).
- **(c)** Leave it, but bar it by rule from any variance report.

**Unblocks:** the truthfulness of S9.
