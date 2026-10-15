# Orchestrator diff: live vs archived (static)

Live is `services/api/app/cam/neck/orchestrator.py` (blob `db5904fe`, 279 lines). Archived is
`docs/archive/photo_vectorizer_patches/orchestrator.py` (blob `a574d921`, 385 lines). The diff is
146 insertions and 40 deletions.

| Aspect | Live | Archived | Forward-port assessment |
|---|---|---|---|
| **Operation sequencing** | OP10 truss rod → access pocket → OP40 rough → OP45 finish → OP50 fret slots | Same order and same flags; adds an unused `completed_ops` list | No change; nothing to port |
| **Tool-change emission** | None in the orchestrator. Each generator emits its own block through its injected PostProcessor (`fe1e2f51`, `1d7dbd9e`) | Adds `_tool_change_block()` before every op **and** keeps each generator's own block, so every change is emitted twice (replay: 4 → 8) | **Obsolete.** Duplication is a defect, not a fix |
| **Operator pause** | None: no `M0`/`M1` anywhere in the program | `M1  ( Optional stop - verify tool change )` via `ToolChangeMode.M1` | **The only behaviour absent from live.** Needs controller/owner adjudication (manual change on a non-ATC machine; `M1` is optional-stop and panel-skippable) |
| **Spindle commands** | `M5` before `T M6`; `S M3` after `G43` | Same, from the same PostProcessor | Already live |
| **Tool-length compensation** | `G43 Hn` after every `M6` | Same | Already live. G43-H support on the configured GRBL controller is unverified; see `GCODE-COMMENT-DIALECT-COMPATIBILITY-001` scope |
| **Dwell** | `G4 P2.0` after spindle start | Same; `dwell_after_spindle_ms` read from the machine | Already live |
| **Retract before tool change** | No retract inside the block. It relies on the previous op ending at safe Z (25) | Docstring claims a retract before `T M6`; the emitted block retracts **after** (`… G4`, then `G0 Z10`) | **The claim is false in its own output.** Nothing to port |
| **Safe-Z source** | Generators hard-code `self.safe_z_mm = 25.0`; the orchestrator ignores the machine | Overwrites each generator's `safe_z_mm` / `retract_z_mm` from `machine` after construction | Intent valid (invariant 7). The implementation is **partial**: generators build their PostProcessor in `__init__` at 25.0, so tool-change blocks still emit `G0 Z25.000` while moves use 10 |
| **Retract-Z source** | Generators hard-code 5.0 | `machine.retract_z_mm` (5.0 in the candidate contract; **absent** in the live contract) | Incompatible as written |
| **Footer** | `G0 Z50.000` hard-coded | `G0 Z{machine.safe_z_mm}` (10 under the candidate machine) | The intent is portable. The value change (50 → machine) needs a clearance decision |
| **Header** | Scale, frets, profile, material | Adds machine label, post dialect, safe/max Z | Cosmetic; portable |
| **Machine-profile selection** | None. The route resolves `machine` for gates/preflight but calls `NeckPipeline(cfg)` without it | `NeckPipeline(config, machine=BCAM_2030A)` default | Signature change; the route would also need to pass the machine |
| **Controller dialect** | PostProcessor default `controller="GRBL"` | `controller=machine.post_dialect.upper()` | Portable in principle; live `post_dialect` returns the enum value |
| **Error handling** | `ValueError` for an unknown op | Same | — |
| **Return value / artifact shape** | `NeckPipelineResult` (unchanged) | Identical dataclass | — |
| **`@safety_critical`** | On `generate()` and `generate_operation()` (`8e28ba4b`, 03-24) | **Absent**: the candidate predates the decorator | Wholesale replacement would **discard** it |
| **Dependencies that no longer exist** | — | `BCamMachineSpec.dwell_after_spindle_ms`, `.retract_z_mm`, and the candidate's flat `label` / `post_dialect` fields. Live has `spindle_ramp_time_ms` and computed properties | **Blocking** for an as-written replay (arm C) |

## Later live behaviour that wholesale replacement would discard

- The `@safety_critical` decorators (`8e28ba4b`).
- The live machine contract. The candidate `machines.py` replaces six presets with one and changes the
  BCAM 2030A envelope.
- Tool-change de-duplication. Live emits each change once.

## Selectively portable vs obsolete

| Archived change | Verdict |
|---|---|
| Propagate machine safe/retract Z into generators **and** into their PostProcessor | Valid intent (invariant 7). Port only after a clearance-authority decision, and the implementation must reach the PostProcessor too |
| Footer retract from the machine spec instead of 50 | Same: needs a clearance decision |
| `M1` operator pause on non-ATC machines | Needs controller and owner adjudication |
| Machine/dialect header annotation | Cosmetic; harmless |
| Orchestrator-level tool-change blocks | **Obsolete**: duplicates the generator blocks |
| Candidate `machines.py` contract | **Obsolete**: conflicts with the live contract |
| Lowering safe Z to 10 mm | **Not portable** without a machine-clearance ruling |
