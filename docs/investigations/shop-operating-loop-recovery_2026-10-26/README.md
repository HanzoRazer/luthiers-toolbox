# SHOP-OPERATING-LOOP-RECOVERY-001 — existing capability and MVS gap audit

| | |
|---|---|
| **Type** | Evidence-only recovery and reconciliation |
| **Date** | 2026-10-26 |
| **Baseline** | luthiers-toolbox `origin/main` `02032884` (secondary SHAs in BASELINE.md) |
| **Implementation authority** | None. No production source, route, schema, threshold, policy or deployment file changes. |
| **Status** | Draft PR for owner review. **Two of seven owner rulings made (R3, R4, 2026-10-26); five open** (OWNER_RULINGS.md). The CI red is MAINT-DEFER-019, unrelated (#463). |

## Conclusion

**No step of the nine-step operating loop is AVAILABLE today, and no segment
runs end to end.**

- 3 steps are ADAPT:
  - **S1 job identity:** LTB `project_id`
  - **S2 configuration:** the CNC-PS product definition, which a job pins by sha256
  - **S3 estimate revision:** CNC-PS quote records
- 5 steps are BUILD.
- 1 step is BLOCKED: **S6** needs an owner-approved validation policy (PR #456 has the mechanism, not the values).

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
| By disposition | RETAIN_CANONICAL 8 · ADAPT 6 · REFERENCE_ONLY 17 · OWNER_RULING_REQUIRED 3 · MISSING_BUILD 5 · SUPERSEDED 1 · RECONNECT 0 |

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
5. **Overlaps and conflicts:** see AUTHORITY_BOUNDARY.md.
   - Two job identities (R1).
   - Two estimators (R2).
   - Two kit/configuration bases (R3).
   - A self-asserted `manufacturing_state` that feeds a G-code precondition (R4).
   - The CCS guided/job-composition claim (R5).
   - Fabricated "actuals" (R7).
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
