# Recommendation

**Disposition (owner ruling 2026-10-14):** `SUPERSEDED` for the rapid-at-depth defect;
`INCOMPATIBLE_WITH_CURRENT_RUNTIME` as written; `DO_NOT_FORWARD_PORT` without a separate
machine-clearance decision. The file is preserved as evidence and closed as a production repair
candidate.

### 1. Does the archived orchestrator address the same failure class as the rapid-at-depth defect?

**No.**

- The defect was in `profile_carving.py`'s station loop: lateral stepovers emitted as `G0` while the
  cutter was plunged.
- The candidate does not touch that loop.
- On the pre-fix tree it still emits 702 rapids below Z0 (arm E = arm A).

### 2. Does it measurably reduce or eliminate unsafe rapid moves?

**No.** The count is 702 with it and 702 without it on the pre-fix tree, and 0 with it and 0 without it
on the fixed tree.

### 3. Does it introduce different safety or compatibility risks?

**Yes.**

- It duplicates every tool change (4 → 8).
- It lowers safe Z from 25 to 10 mm.
- It mixes 10 mm and 25 mm clearances in one program.
- It removes `@safety_critical` if swapped in wholesale.
- It cannot be constructed against the live machine contract (`AttributeError`).
- Its docstring claims a retract-before-change that its output does not perform.

### 4. Which exact behaviours deserve selective forward-porting?

**None now.** Two intents are worth preserving as inputs to a later decision, but not as code:

- machine-sourced clearance reaching both the generators and their PostProcessor;
- an operator pause (`M1` or `M0`) at manual tool changes on a non-ATC machine.

### 5. Which behaviours require controller or machine-owner adjudication?

- **The clearance authority.** Which of 25 (machine and generators), 5 (`PreflightConfig`), 50 (footer)
  or 10 (candidate) governs.
- **The tool-change pause on the BCAM 2030A.** `M0` or `M1`, and whether the PostProcessor should emit it.
- **Controller syntax.** Whether `T n M6`, `G43 Hn` and nested parenthetical comments are valid on the
  configured controller. Proposed: **`GCODE-COMMENT-DIALECT-COMPATIBILITY-001`**.

### 6. Is the current production repair order still necessary?

**The rapid-at-depth repair is done.** #398 is merged, and this replay independently confirms 0 rapids
at or below Z0 on the fixture. The route stays fail-closed under `neck_pipeline_full`. Readiness has
**not** been granted, and #398 records a remaining plunge-feed defect.

What is still open is not this defect:

- the plunge-feed defect (#399);
- the clearance-authority question (invariant 8);
- the tool-change position for the first change (invariant 4).

### 7. What should the next bounded implementation order contain?

There is **no orchestrator port.** If the owner wants to proceed, three separate orders:

1. **`NECK-CLEARANCE-AUTHORITY-001`** (decision first, then code):
   - rank the clearance sources;
   - pass the resolved machine into `NeckPipeline`;
   - make generators and PostProcessor read one value;
   - add a test that a program contains exactly one safe-Z height and no footer literal.
2. **`NECK-TOOLCHANGE-PAUSE-001`:** after the owner rules on `M0`/`M1`, configure the existing
   PostProcessor `ToolChangeMode` for the BCAM preset. No orchestrator-level blocks.
3. **`GCODE-COMMENT-DIALECT-COMPATIBILITY-001`:** test the exact emitted syntax (nested comments,
   `T M6`, `G43 H`) against the configured controller/post contract. No syntax rewrite until that
   contract exists.
