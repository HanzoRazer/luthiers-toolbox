# SHOP-OPERATING-LOOP-RECOVERY-001 — existing capability and MVS gap audit

| | |
|---|---|
| **Type** | Evidence-only recovery and reconciliation |
| **Date** | 2026-10-26 |
| **Baseline** | luthiers-toolbox `origin/main` `02032884` (secondary SHAs in BASELINE.md) |
| **Implementation authority** | None. No production source, route, schema, threshold, policy or deployment file changes. |
| **Status** | Draft PR, **internally final: all seven owner rulings recorded (2026-10-26, OWNER_RULINGS.md); 0 rows await a ruling.** Awaiting owner disposition. The CI red is MAINT-DEFER-019, unrelated (#463). |

## Conclusion

**No segment runs end to end.** After the owner rulings, two steps are
AVAILABLE in CNC-Production-Shop through an operator CLI, not a guided surface.
They became AVAILABLE because the rulings named canonical owners, not because
of new code.

- 2 steps are AVAILABLE:
  - **S1 job of record:** CNC-PS `job_id` (R1)
  - **S3 official estimate revision:** CNC-PS (R2)
- 1 step is ADAPT: **S2.** The product definition plus digest is canonical configuration identity; the commercial-kit layer is missing (R3).
- 5 steps are BUILD: S4, S5, S7, S8, S9.
- 1 step is BLOCKED: **S6.** By ruling, it waits on the first real soundboard policy evidence (R6).

**Ownership, as ruled:**
- CNC-PS owns the job and the estimate.
- LTB owns the design project, the guided shop workflow and the operation records keyed to `job_id`.
- Creation Studio owns CAM package assembly and review.
- Manufacturing authority stays a separate readiness/CAM verdict plus human authorization (OWNER_RULINGS.md).

The missing seam for a first-soundboard witness is a durable,
append-only record of a shop operation performed on a job. Steps S7 (next
operation), S8 (actuals) and S9 (compare) all need it, and no scoped repo has
one. The single recommended increment is **SHOP-OP-RECORD-001**: that record,
as an LTB library with no route, no UI and no authority (RECOMMENDATION.md).

## Headline counts (40 ledger rows; 52 raw candidates screened per SOURCE_SCOPE.md)

| | |
|---|---|
| By track | A job identity 8 · B estimate/actual 5 · C kits 8 · D time 9 · E guided 10 |
| By repo | luthiers-toolbox 34 (85%) · CNC-Production-Shop 4 · CAM-Assist-Blueprint 1 · CAM-Creation-Studio 1 |
| By reachability | LIVE_ROUTED 17 · LIVE_LIBRARY 4 · BUILT_DISCONNECTED 8 · ARCHIVED_RECOVERABLE 1 · CONCEPT_ONLY 5 · MISSING 5 |
| By disposition | RETAIN_CANONICAL 9 · ADAPT 8 · REFERENCE_ONLY 17 · MISSING_BUILD 5 · SUPERSEDED 1 · OWNER_RULING_REQUIRED 0 · RECONNECT 0 |

**RECONNECT is 0:** no complete capability is waiting to be switched back on.
Every useful disconnected asset is PARTIAL.

## Recovered, proposed, and production-qualified

| Class | What |
|---|---|
| **Production-qualified** (live, canonical, fail-closed) | CAM generator readiness (SOL-E02). RMOS run identity (SOL-A03). Species catalog (SOL-C06). Cycle-time *estimators* (SOL-D06). Gate display components (SOL-E07). |
| **Recovered capability** (exists, not production-qualified for this loop) | LTB projects (SOL-A01/A02). Saw-lab append-only actuals (SOL-D02). Op-keyed JobLogService (SOL-D03, uncalled). Beginner proposal gate + evidence chain (SOL-E01, unrouted by design). CNC-PS job→estimate→bid→proposal CLI and its digest-pinned product configuration (SOL-A06/B04/C07). BOM templates (SOL-C01). |
| **Proposed only** (concept, mock, or missing) | Time tracking (SOL-D01 mock). Inventory and orders (SOL-C04 mock). Quotes/invoices/CRM plan (SOL-A05). Beginner-safe mode (SOL-E08). Archtop kits (SOL-C05). Versioned kit, reservation, labor entries, variance, traveler (5 MISSING rows). |

## Answers to §13

1. **What exists per capability:** JOB_IDENTITY_MAP, ESTIMATE_ACTUAL_MAP, KIT_LINEAGE, TIME_CAPTURE_MAP and GUIDED_WORKFLOW_MAP.
2. **Reachable today:** the 21 LIVE_* rows. Each cites its registration or caller as file:line.
3. **Disconnected or archived:** 8 BUILT_DISCONNECTED rows, plus 1 ARCHIVED_RECOVERABLE from pre-rewrite tag `v2.4.0-alpha.1`.
4. **Discussed, never built:** the 5 CONCEPT_ONLY rows and 2 routed mocks.
5. **Overlaps and conflicts:** see AUTHORITY_BOUNDARY.md. All are now ruled:
   - two job identities (R1: CNC-PS)
   - two estimators (R2: CNC-PS official, LTB preview)
   - two configuration bases (R3: product definition)
   - a self-asserted `manufacturing_state` (R4: workflow assertion only; the DXF stays quarantined)
   - the CCS claim (R5: split)
   - the beginner policy values (R6: unapproved)
   - fabricated actuals (R7: correct the screen)
6. **Truly missing:** MVS_GAP_MATRIX.md.
7. **Next increment:** SHOP-OP-RECORD-001.
8. **Why it advances a beginner-guided app:** every guided surface found kept completion in memory or in a bare list. A beginner flow can say "next" and "done" only from a durable operation record.

## Continuation pass

SPOT_CHECK.md records the second pass:
- 26/26 agent-sourced citations hold.
- **One correction:** SOL-C07 now covers CNC-PS product records. A job pins them by sha256, so S2 moved from BUILD to ADAPT.
- R4 is shown to be **latent**: no project G-code route reaches emission today, because the only readiness-passing route's DXF is quarantine-BLOCKED.
- The PR's red CI is attributed to an existing timestamp-collision flake in `sqlite_art_presets_store.py:134`.

## Rerun

```bash
python -I scripts/investigations/shop_operating_loop_ledger.py \
  --package docs/investigations/shop-operating-loop-recovery_2026-10-26 --verify-digests
pytest services/api/tests/test_shop_operating_loop_recovery_evidence.py -q --no-cov
```

`--write-json` regenerates `CAPABILITY_LEDGER.json` from the CSV.
`--verify-digests` recomputes every luthiers-toolbox digest that is present in
the local object store. Secondary-repo digests were computed at the SHAs in
BASELINE.md and need those clones to recheck.

## Validator proxies (stated, so they are not mistaken for proofs)

- **"Authority inferred from a name"** is enforced as: a CONCEPT_ONLY or MISSING
  row must hold authority NONE. Something that does not run decides nothing
  today. Authority on live rows was assigned from cited behavior, which the
  validator cannot judge.
- **"Production path changed in this PR"** is enforced against the declared
  `evidence.json.changed_paths`. A reviewer should still compare it with the
  real PR diff.
