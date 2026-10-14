# Safety replay: offline, five arms

**Nothing here was run on a machine, controller or simulator.** Programs were generated in Python and
read by an offline parser. A generated program in this directory is **not manufacturing-approved**.

## Method

- **Fixture:** `_build_pipeline_config(NeckConfigIn())` with OP10, OP40, OP45 and OP50 all enabled.
  This is the default neck request, and the same fixture the #398 motion test
  (`tests/test_p1_neck_pipeline_motion.py::_full_program`) uses. No parameter was set, tuned or invented.
- **Generator:** [`replay/generate_arm.py`](replay/generate_arm.py).
  - It runs with `python -I`, and the extracted tree's `services/api` is the only import root.
  - Each tree is `git archive <sha> services/api/app`, extracted **outside** the repository.
  - Only the generated `( Generated: … UTC )` comment is normalised before hashing; it is the only
    non-deterministic line.
- **Parser:** [`scripts/investigations/neck_gcode_motion_metrics.py`](../../../scripts/investigations/neck_gcode_motion_metrics.py).
  - Motion mode, X/Y/Z, spindle state, tool and G43 are carried modally.
  - Comments are stripped by depth, and nesting is reported.
  - Malformed input is refused with a non-zero exit.
  - `--plane-z 0.0` (workpiece top) was passed explicitly; the parser has no default.

| Arm | Tree | Swapped files |
|---|---|---|
| A `A_pre_p1` | `9c5f46a9` (first parent of #398) | none |
| B `B_live` | `d42712e0` (base) | none |
| C `C_archived_on_live` | `d42712e0` | `cam/neck/orchestrator.py` ← archived |
| D `D_bundle_as_shipped` | `d42712e0` | orchestrator **and** `cam/machines.py` ← archived pair |
| E `E_bundle_on_pre_p1` | `9c5f46a9` | orchestrator **and** `cam/machines.py` ← archived pair |

Arm D runs the bundle as the unit it shipped as. It is **not** the current runtime; arm C is. D and E
exist to observe the candidate's own behaviour. Neither patches the candidate.

## Arm C: not runnable on current dependencies (stopped, as ordered)

```
AttributeError: 'BCamMachineSpec' object has no attribute 'dwell_after_spindle_ms'
  raised at orchestrator.py:113   dwell_after_spindle_ms=machine.dwell_after_spindle_ms,
```

`machine.retract_z_mm` (lines 125–129) would fail next. Nothing was changed to make it run. Record:
`replay/results/C_archived_on_live.json`.

## Metrics

Plane = Z 0.000 (workpiece top).

| Metric | A pre-P1 | B live | D bundle | E bundle on pre-P1 |
|---|---|---|---|---|
| Total lines | 1935 | 1935 | 1974 | 1974 |
| Executable blocks | 1779 | 1779 | 1807 | 1807 |
| `G0` moves (axis-bearing) | 927 | 207 | 211 | 931 |
| **`G0` below Z0** | **702** | **0** | **0** | **702** |
| `G0` at or below Z0 | 711 | 0 | 0 | 711 |
| **XY rapids below Z0** | **702** | **0** | **0** | **702** |
| XY rapids at or below Z0 | 711 | 0 | 0 | 711 |
| `G0` Z-only moves | 139 | 139 | 143 | 143 |
| Z-only heights used (mm × count) | 25×58, 5×80, 50×1 | 25×58, 5×80, 50×1 | 10×59, 25×4, 5×80 | 10×59, 25×4, 5×80 |
| Tool changes (`M6`) | 4 | 4 | **8** | **8** |
| Tool changes with spindle on | 0 | 0 | 0 | 0 |
| Tool changes at unknown or ≤ Z0 | 1 | 1 | 1 | 1 |
| Tool changes without `G43` before next motion | 0 | 0 | 0 | 0 |
| Nested-comment lines | 3 | 3 | 3 | 3 |
| Program SHA-256 | `e305d5f7…806e` | `5f78b3c2…4b46` | `600c8d55…bdd6` | `8c90da30…96ff` |

**How to read some rows:**

- **Safe and retract heights.** Arms A and B use safe 25.0 and retract 5.0 in all three generators,
  plus footer `G0 Z50.000`. Arms D and E use safe 10.0 and retract 5.0, but the generator tool-change
  blocks still emit `G0 Z25.000` (the 25×4 row), and the footer uses machine safe Z 10.
- **Remaining `25.0` literals.** There is one each in `truss_rod_channel.py`, `profile_carving.py` and
  `fret_slots.py` in every arm. The archived orchestrator's one is in a comment.
- **The one "unknown" tool change in every arm** is the first: `T2 M6` comes before any Z word in the
  program, so its Z is unknown to an offline reader. Every other change happens at Z = 25 (A/B) or Z = 10
  (D/E).
- **First violation lines:** A 157, 159, 161…; E 178, 180, 182…. These are profile-station lateral
  stepovers.

## Inter-operation transitions

State immediately before each operation header:

| Arm | OP10 | OP40 | OP45 | OP50 |
|---|---|---|---|---|
| A / B | L30, Z unknown, spindle off | L142, Z 25, spindle on | L942, Z 25, spindle on | L1744, Z 25, spindle on |
| D / E | L42, Z 10, spindle on | L163, Z 10, spindle on | L972, Z 10, spindle on | L1783, Z 10, spindle on |

In every arm each operation ends with a Z-only rapid to safe height before the next tool-change block.
In D and E the extra orchestrator block sits **before** the operation header, then the generator's own
block repeats the change after it.

## Tool-change block, verbatim

Live (B), OP10:

```
( Tool Change: T2 - 1/8" Flat End - Truss Rod )
M5
T2 M6
G43 H2
S20000 M3
G4 P2.0
G0 Z25.000
```

Archived (D) emits this block first, then the live block above:

```
( Tool Change: T2 - 1/8" Flat End - Truss Rod )
M5
T2 M6
G43 H2
S20000 M3
M1  ( Optional stop - verify tool change )
G4 P2.0
G0 Z10.000
```

## What the replay establishes

1. **702 is the reproducible historical count.** It equals #398's own figure.
   - A further 9 XY rapids ran at exactly Z = 0.000 (711 at or below).
   - "780" is not reproduced by any definition measured here (below, at-or-below, XY-only, all `G0`).
2. **#398 eliminated every rapid below and at Z0** on this fixture.
3. **The archived orchestrator does not affect the rapid class.** E = A = 702.
4. **The archived orchestrator duplicates tool changes and mixes clearance heights.**
5. **Spindle-off and G43 sequencing are the same with or without the candidate.**

## Reproduce

```
git archive <sha> services/api/app | tar -x -C <tmp>/<arm>     # outside the repo
python -I docs/investigations/cam-orchestrator-recovery_2026-10-14/replay/generate_arm.py \
    --tree <tmp>/<arm>/services/api --arm <arm> --out-dir <out>
python -I scripts/investigations/neck_gcode_motion_metrics.py --plane-z 0.0 --out metrics.json \
    A_pre_p1=A_pre_p1.gcode.evidence B_live=B_live.gcode.evidence \
    D_bundle_as_shipped=D_bundle_as_shipped.gcode.evidence E_bundle_on_pre_p1=E_bundle_on_pre_p1.gcode.evidence
```

Re-running the parser on the committed programs reproduces `replay/results/metrics.json` byte for byte
(SHA-256 `2ba26f1f…7b3d`).

Programs carry a `.gcode.evidence` extension on purpose. `*.txt` is ignored repository-wide, and no
machine tooling recognises `.gcode.evidence`. A local `.gitattributes` (`-text`) keeps their bytes, and
so their hashes, identical on every platform.
