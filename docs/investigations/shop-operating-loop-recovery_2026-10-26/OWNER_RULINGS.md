# Owner rulings

**All seven ruled, 2026-10-26:**
- R3 and R4 in the first ruling message
- R1, R2, R5, R6 and R7 in the second

**Further decisions from the same messages:**
- The Les Paul DXF stays quarantined.
- The preset-ID CI defect is MAINT-DEFER-019, repaired separately in draft PR #463.
- PR #462 stays draft until dispositioned. The unrelated CI failure does not count against the audit.
- SHOP-OP-RECORD-001 may follow only after #462 records these rulings and is dispositioned.

## Resulting architecture (owner, 2026-10-26)

| Concern | Owner |
|---|---|
| Commercial job identity | CNC-Production-Shop |
| Official estimate and quote revision | CNC-Production-Shop |
| Design project and guided shop workflow | Luthier's Toolbox |
| Product configuration identity | Existing product definition + digest |
| Kit/BOM layer | Follows the CNC job/configuration contract |
| CAM package assembly and review | CAM Creation Studio |
| Manufacturing authority | Separate readiness/CAM verdict plus human authorization |
| Physical-engineering thresholds | Unapproved pending the first real soundboard evidence |
| Actual time and material | LTB operation records linked to CNC `job_id` |

---

## R1 — Job of record (RULED: option a)

**Question.** Which identifier is the job of record (LTB `project_id` or
CNC-PS `job_id`), and what stored field links the other system to it?

**Ruling.** CNC-Production-Shop `job_id` is the commercial and production job
of record. Its manifest must reference:
- the LTB `project_id`
- an immutable LTB design revision or snapshot ID
- the design-package SHA-256
- the generator identity and version, where applicable

The mutable `project_id` alone is insufficient, because LTB currently
overwrites the design. LTB remains the primary design and recovery
environment, but that does not make its project record the commercial job
authority.

**Recorded as:**
- SOL-A06 is RETAIN_CANONICAL (job of record).
- SOL-A01 stays ADAPT. It must supply an immutable design revision; that is S4.
- The JOB_IDENTITY_MAP link "LTB project ↔ CNC-PS job" stays UNKNOWN as *built*. The ruling defines it as *required*.
- None of the four manifest references exists yet.

## R2 — Official estimator (RULED: option a)

**Question.** Which estimator is official for a guitar job?

**Ruling.**
- CNC-Production-Shop is the official estimator. Its stored, versioned estimate feeds the bid and proposal.
- The LTB estimator remains a clearly labeled non-binding design preview.
- Shared calculations may later sit behind a common versioned contract, but a job still has only one official estimate revision.
- LTB previews must never silently replace or update the job's accepted estimate.

**Recorded as:**
- SOL-B04 is RETAIN_CANONICAL.
- SOL-B01 is ADAPT with authority NONE. The non-binding label is not present today.

## R3 — Kit and configuration base (RULED)

**Ruling.** S2 is ADAPT. The versioned `guitar_product_definition_v1`
snapshot and SHA-256 provide configuration identity. The missing work is the
commercial-kit layer: quantities, units, substitutions and BOM semantics. The
kit/BOM layer follows the CNC job/configuration contract (architecture table).

**Recorded as:**
- SOL-C07 is RETAIN_CANONICAL.
- SOL-C08 stays MISSING_BUILD.

## R4 — Self-set CAM approval (RULED)

**Ruling.**
- `manufacturing_state` is a project workflow assertion only, not manufacturing authority.
- Before `LesPaul_CAM_Closed.dxf` leaves quarantine, its surviving route must require an independently produced CAM/readiness disposition.
- Clearing the DXF must not make the boolean the effective release gate.
- The DXF stays quarantined.

**Recorded as:**
- SOL-E03 has authority NONE and is SUPERSEDED as a release input.
- The release precondition is a requirement, not implemented here.

## R5 — Shop-floor guide ownership (RULED: option c, split)

**Ruling.**
- CAM Creation Studio assembles and reviews the CAM package.
- LTB provides the beginner-guided shop-floor interface and records operations.
- Every LTB operation record references the CNC-Production-Shop `job_id`.
- Evidence, readiness, CAM disposition and human completion remain separately identifiable.
- Creation Studio does not become the general ERP or shop traveler.

**Recorded as:**
- SOL-E09 is REFERENCE_ONLY.
- SOL-E10 (traveler) and SOL-D09 (time entries) are MISSING_BUILD, owned by LTB, keyed to `job_id`.

## R6 — Validation policy values (RULED: remain unapproved)

**Ruling.** Do not approve 0.6 mm or 2.5 mm as production thresholds. The
beginner physical-engineering path stays disconnected until the first real
soundboard program produces a documented policy basis containing:
- plate identity and material state
- starting thickness measurements and uncertainty
- intended operation
- bounded proposed removal
- minimum acceptable remaining thickness and its source
- measurement method
- post-operation results
- named approver

PR #456 may preserve the inactive policy mechanism, but no policy becomes
`ACTIVE` from test values.

**Recorded as:**
- SOL-E01 stays RETAIN_CANONICAL and disconnected by ruling.
- MVS S6 stays BLOCKED on that evidence.

## R7 — Job-insights actual times (RULED: option a, with a hard qualification)

**Ruling.** Keep the screen, but correct it:
- If no measured time exists, display "No actual recorded".
- Move-count estimates are labeled `DERIVED_ESTIMATE`.
- Estimated values never populate `actual_time_s`.
- Derived values are excluded from estimate-versus-actual calculations.
- Only completed operation records with recorded provenance may supply actual time.

This is a correction, not a cosmetic relabeling.

**Recorded as:** SOL-D05 is ADAPT (correction required, not implemented here).
