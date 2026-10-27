# Options

Only the three paths named in the order are evaluated.

## 1. Reconnect and adapt existing internal capability

**What is reusable:**
- the SOL-E01 gate and evidence chain
- SOL-E02 readiness verdicts
- SOL-E07 "why blocked" display components
- the SOL-D02 append-only execution/job-log pattern
- the SOL-D03 op-keyed job-log schema

**What blocks it:**
- **No complete-but-disconnected capability exists for steps S7–S9.** Every RECONNECT-shaped asset is PARTIAL, so the ledger has zero RECONNECT dispositions.
- Routing SOL-E01 needs an approved policy (R6).
- The live shell (SOL-E04) leaks authority.

**Verdict:** necessary as the source of patterns and verdicts, but on its own
it cannot close the seam.

## 2. External ERP for commercial operations through explicit contracts

CNC-Production-Shop already is an internal commercial engine (SOL-A06/B04).
An external ERP (Factory.app was a comparison model only) could hold jobs,
quotes, kits and labor.

CNC-PS already shows the right pinning pattern for commercial sources: a job
manifest records each source by role, id, snapshot and sha256. Any bridge
should reuse that pattern rather than invent one.

**What blocks it:**
- No explicit contract exists today for an ERP job to pin an LTB design revision, material subject or operation (JOB_IDENTITY_MAP: ABSENT/UNKNOWN).
- Choosing an ERP is outside this order.
- Ruled since (R1, R2): CNC-PS owns the job and the official estimate. A bridge is therefore an internal LTB↔CNC-PS contract, not an ERP selection.
- An ERP would still need LTB to emit a durable per-operation record for actuals.

**Verdict:** not chosen. R1/R2 make CNC-Production-Shop the commercial engine, so an external ERP is outside scope. Any bridge is an internal LTB↔CNC-PS contract that reuses the sha256 source pattern, and it still needs the missing operation-record seam.

## 3. Build a narrow internal operating loop

Build only the missing seam inside LTB:
- an append-only shop-operation record keyed to the CNC-PS `job_id` (ruled R1/R5)
- operation key, subject and evidence ids
- start/complete/abort events
- actual minutes and material lines
- supersede-only corrections
- no approval fields

Reuse the SOL-D02 and SOL-E01 patterns rather than inventing new ones. Leave
the CNC-PS job and estimate (R1, R2), kits (R3) and the validation policy (R6)
untouched.

**Verdict:** recommended as the next increment. See RECOMMENDATION.md.
