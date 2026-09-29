# Recommendation — one bounded next increment

## Recommended: Option A — contain the Saw Lab toolpaths cluster

Contain `POST /api/saw/batch/toolpaths/from-decision` and `POST /api/saw/compare/toolpaths` behind the existing RMOS manufacturing-output authority, mirroring the merged Rosette pattern exactly.

### Why this over the alternatives
- **Safety-positive and on the spine.** CF2 is the manufacturing-output safety program; these two rows are genuinely ungoverned G-code/toolpath emitters with **no governed sibling** (unlike the draft-lane rows). Containing them removes real ungoverned emission.
- **Proven, low-risk template.** The Rosette `/export-cnc` and `/design` increments established the exact pattern (authority-before-generation, single-artifact persistence, governed headers, `FAIL_CLOSED`, true-A classifier contract). Reuse `require_manufacturing_output_authority` / `persist_authorized_manufacturing_output` and the `rosette_output_authority` helper shape.
- **Bounded and coherent.** Two routes, **one shared service** (`generate_toolpaths_from_decision`) → one authority derivation. Fits one dev order; small file count; clear inventory movement 13 → 11.
- **Not a "next-in-inventory" pick.** Chosen on shared-handler coherence + no-governed-sibling risk, not order (frozen decision).
- **B waits** because it adds new production routes (larger, scope-gate sensitive) — completing stranded client work is valuable but riskier and not on the safety spine.
- **C waits** because retirement needs its own careful proof-per-target increment and (for CONS-04/CONS-11) owner rulings; it is cleanup, not safety.

### One bounded next increment (for a future dev order — NOT authorized here)
- **Target files (expected):** `services/api/app/services/saw_lab_toolpaths_from_decision_service.py` and/or its router(s); a pure complete-decision summary helper (new or extend `rosette_output_authority.py`); `services/api/tests/rmos/test_cf2_saw_toolpaths_containment.py` (new); update the Phase-A/B inventory count assertions (14→…) already at 13 → assert 11; regenerate `manufacturing_output_inventory.json`/`.md`; a new CBSP21 manifest. **Precondition requiring discovery:** confirm the exact router modules that expose the two routes and whether the "decision" payload can be represented truthfully by one authority request (the same feasibility-summary discipline used for Rosette).
- **Acceptance tests:** authority evaluated once before any generator; RED/UNKNOWN/ERROR → 409 with no toolpath output and one BLOCKED artifact; permitted → generation + single persisted artifact + governed headers + hash identity; inventory shows both saw rows `FAIL_CLOSED`, live-ungoverned 13→11, permitted 0, no unrelated row moved; existing saw baselines stay green.
- **Rollout order:** discover routes/payload → prove summary representability → pure helper + tests → authority before generation → single persistence + headers → regenerate inventory → gates → draft PR → clean-agent witness → stop for merge auth.
- **Rollback condition:** any saw baseline regresses, the decision payload cannot be represented truthfully by one authority request, a classifier change appears necessary, or a governed path already exists for these routes (it does not, per this audit).

### Reasons the other options should wait
- **B (design-first):** new backend surface + ornament-authority scope-gate exposure; higher risk; off the safety spine; better sequenced after the ungoverned-emitter backlog is smaller.
- **C (retirement):** low urgency; needs per-target import/route/build proof and owner rulings for the shared-module (CONS-04) and governed-dead (CONS-11) cases; a "no deletion" increment (this one) cannot pre-authorize it.

This keeps the project on consolidation with a single, bounded, safety-positive increment and no omnibus PR (CRO-016).
