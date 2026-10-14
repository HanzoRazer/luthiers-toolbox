# CAM-ORCHESTRATOR-RECOVERY-EVIDENCE-001

**Status:** evidence only. No production behaviour changed. Nothing here is manufacturing-approved.
**Base:** `origin/main` @ `d42712e0e358b2344ddc046e83f169233581dce5` (2026-10-13)
**Branch:** `docs/cam-orchestrator-recovery-evidence`

## Purpose

An archived March 18, 2026 neck-CAM `orchestrator.py` describes itself as a "SAFETY FIX". This
investigation asks one question: is it a valid predecessor, or a partial solution, to the
`/api/cam-workspace/neck/generate-full` rapid-at-cutting-depth defect?

## Final disposition (owner ruling, 2026-10-14)

| Question | Disposition |
|---|---|
| Rapid-at-depth defect | **`SUPERSEDED`**. `main` was already corrected by #398 (LTB-REMEDIATE-P1). The archived file never touched the defect. |
| The archived file as written | **`INCOMPATIBLE_WITH_CURRENT_RUNTIME`**. It fails at construction against the live machine contract. |
| Forward-port | **`DO_NOT_FORWARD_PORT`** without a separate machine-clearance decision. |

The file is preserved as evidence. It is closed as a production repair candidate.

## Investigated artifacts

| Artifact | Identity |
|---|---|
| External bundle | `Downloads\Storage\files - 2026-03-18T031920.383.zip`, sha256 `ee3f5fdb…80aa` |
| Archived orchestrator (repo) | `docs/archive/photo_vectorizer_patches/orchestrator.py`, blob `a574d921` |
| Archived orchestrator (bundle) | blob `2f10f102`. Differs from the repo copy only in two docstring words. |
| Archived machines (repo / bundle) | blob `0946b833` / `53c5580f` |
| Live orchestrator | `services/api/app/cam/neck/orchestrator.py`, blob `db5904fe` |
| Live machines | `services/api/app/cam/machines.py`, blob `0ded9112` |

Full hashes are in [`PROVENANCE.md`](PROVENANCE.md) and [`EVIDENCE.json`](EVIDENCE.json).

## Principal findings

1. **The historical defect count is 702, not 780.**
   - The pre-#398 tree emits 702 rapids below Z0, all of them XY moves. That reproduces exactly the
     figure #398 recorded.
   - "780" could not be tied to any fixture or definition, so it is superseded.
2. **The archived orchestrator does not address the defect.**
   - Run on the pre-#398 tree it still emits **702**.
   - The defect lived in `profile_carving.py`'s station loop, which the orchestrator does not touch.
3. **It cannot run on the current runtime.**
   - `AttributeError: 'BCamMachineSpec' object has no attribute 'dwell_after_spindle_ms'` at
     `orchestrator.py:113`.
   - It also reads `machine.retract_z_mm`, which the live contract does not have.
4. **Run as shipped with its own `machines.py`:**
   - it duplicates every tool change (4 → 8);
   - it lowers safe Z from 25 mm to 10 mm;
   - it mixes 10 mm and 25 mm clearance heights in one program.
5. **Its "SAFETY FIX" docstring does not describe what it emits.**
   - It claims `M5 → retract to safe_z → T_ M6`.
   - The emitted block is `M5`, `T M6`, `G43`, `S M3`, `M1`, `G4`, then `G0 Z`. The retract comes after
     the tool change, exactly as live.
   - The only behaviour live lacks is the `M1` operator pause.
6. **The spindle-off / G43 / spindle-on sequence was already live.**
   - It arrived through generator-level PostProcessor wiring (`fe1e2f51`, `1d7dbd9e`, 2026-03-17).
   - Every arm stops the spindle before each tool change and applies G43 after it.

**🔴 Safety candidate found during the census, NOT fixed here:**

- `/api/headstock/transition/gcode` is live. It is registered at `business_manifest.py:50-56` and
  handled at `routers/neck/headstock_transition_export.py:299`.
- It has no readiness gate, no `@safety_critical`, and no tests.
- The governance inventory already records it (`manufacturing_output_inventory.json:3456-3474`:
  `CONFIRMED_EMITTER`, `authentication: none`, `containment: LIVE_UNGOVERNED`). The motion defect
  below is **not** recorded there.
- On the default request it emits 21 rapids that end below Z0 while moving in X, one per station. The
  first is `G00 X-26.262 Z-11.0199` (program SHA-256 `3b5ddbaa…1956`).
- Whether those paths cross stock depends on an undeclared Z datum, so this is unresolved.
- It needs its own validation order: proposed **`HEADSTOCK-TRANSITION-GCODE-SAFETY-001`**. See the
  census `RECOVERY_RECOMMENDATIONS.md`.

**Separate follow-up, not fixed here:** every arm, live included, emits header comments with nested
parentheses, e.g. `( Scale length: 647.70mm (25.500in) )`. Strict RS274 ends a comment at the first `)`.
Candidate order: **`GCODE-COMMENT-DIALECT-COMPATIBILITY-001`**.

## Limitations

- **Offline generation only.** No controller, simulator or machine interpreted any program. "Spindle
  state" and "Z at tool change" are parser-resolved modal state, not observed machine behaviour.
- **One fixture:** `_build_pipeline_config(NeckConfigIn())`. This is the default neck config, the same
  one the #398 motion test uses.
- **Z0 is the workpiece top.** It is not a machine-authorised safe plane, because the repository carries
  25, 5 and 50 mm clearances that no document ranks.
- **Replay arms C, D and E swap files inside a throw-away extracted tree.** This was done to observe the
  candidate's behaviour, not to repair it. Arm C was not patched to run.

## Files

| File | Content |
|---|---|
| [`PROVENANCE.md`](PROVENANCE.md) | Bundle, archive and live identities, commits, ancestry |
| [`ORCHESTRATOR_DIFF.md`](ORCHESTRATOR_DIFF.md) | Function-level static comparison |
| [`SAFETY_REPLAY.md`](SAFETY_REPLAY.md) | Five-arm offline replay with metrics and hashes |
| [`SAFETY_INVARIANTS.md`](SAFETY_INVARIANTS.md) | Eight candidate invariants: source, live, archived, status |
| [`CONSOLIDATION_CONTEXT.md`](CONSOLIDATION_CONTEXT.md) | Bounded March 15–21 provenance context |
| [`RECOMMENDATION.md`](RECOMMENDATION.md) | Answers to the seven order questions |
| [`EVIDENCE.json`](EVIDENCE.json) | Machine-readable record |
| `replay/` | Harness, preserved programs (`*.gcode.evidence`), per-arm records and `metrics.json` |

The parser is `scripts/investigations/neck_gcode_motion_metrics.py`. Its tests are
`services/api/tests/investigations/test_cam_orchestrator_recovery_evidence.py`.

The broader March census lives in
[`../march-2026-consolidation-recovery-census/`](../march-2026-consolidation-recovery-census/).
