# Candidate safety invariants

These are **recovered candidate invariants**, not adopted production policy. Each status means:

- **proven:** measured on the replay fixture;
- **inferred:** follows from code reading, not measured;
- **unresolved:** needs a decision or a controller this investigation does not have.

"Live" is arm B (`d42712e0`). "Archived" is the candidate, as written (arm C) or as shipped (arm D).

### 1. Cutting motion ends before inter-operation travel

- **Source:** archived docstring (sequence); #398 motion test (`test_modal_state_at_every_station_transition`).
- **Live:** each op closes with a Z-only rapid to 25 mm; there are 0 rapids at or below Z0.
- **Archived:** same structure, closing at 10 mm.
- **Status:** **proven** for both arms on this fixture.

### 2. Retract to a machine-authorised safe plane before XY rapid movement

- **Source:** archived docstring; #398 test.
- **Live:** 0 XY rapids at or below Z0. The plane used is the generator's 25.0, which is **not read from
  the machine**.
- **Archived:** 0 below Z0 (arm D). The plane is machine-derived 10.0, but the PostProcessor blocks still
  emit 25.0.
- **Status:** **proven** against Z0. **Unresolved** against a *machine-authorised* plane: the repository
  carries 25 (machine / generators), 5 (`PreflightConfig`) and 50 (footer), and no document ranks them.

### 3. The spindle is stopped before a tool change

- **Source:** archived docstring; `post_processor.tool_change()`.
- **Live:** `M5` before every `M6`; spindle off at 4 of 4 changes.
- **Archived:** off at 8 of 8 changes.
- **Status:** **proven** for both.

### 4. Tool change occurs only after safe retraction

- **Source:** archived docstring ("M5 → retract to safe_z → T M6").
- **Live:** no retract inside the block. Changes 2–4 happen at Z 25 because the previous op ended there.
  Change 1 happens before any Z word, so the position is unknown to an offline reader.
- **Archived:** identical ordering. Its own block retracts **after** `M6`, so the docstring's claim is
  false in its output.
- **Status:** **unresolved**. Inferred safe for changes 2–4 in both arms. Change 1 depends on machine
  state at program start.

### 5. Tool-length compensation is applied in the correct controller sequence

- **Source:** PostProcessor (`emit_tool_length_comp=True`).
- **Live:** `G43 Hn` after every `M6`, before the next motion.
- **Archived:** same.
- **Status:** **proven** present. **Unresolved** whether `G43 H` is valid on the configured BCAM 2030A
  controller (`ControllerType.GRBL` in the live contract). Belongs to `GCODE-COMMENT-DIALECT-COMPATIBILITY-001`.

### 6. The spindle restarts only after the tool change and compensation steps

- **Source:** PostProcessor.
- **Live:** `S M3` follows `G43`.
- **Archived:** same, then `M1`.
- **Status:** **proven** for both.

### 7. Generator-local fallback clearance does not override an available machine profile

- **Source:** archived (`# Push machine safe_z into each generator (overrides their hardcoded 25.0mm)`).
- **Live:** **not satisfied by construction.** The route resolves a machine but calls
  `NeckPipeline(cfg)` without it, and the generators hard-code 25.0 / 5.0. The values coincide with the
  BCAM 2030A preset (safe Z 25) only by default.
- **Archived:** partially satisfied. Generator attributes are overwritten, but the PostProcessor
  built in `__init__` keeps 25.0, so one program carries two clearances.
- **Status:** **inferred** (code reading) and **proven** in effect (arm D shows the 10/25 mix).

### 8. Unknown or missing clearance authority must not be replaced by a plausible default

- **Source:** order frozen decision 6; #398 test (`WORKPIECE_TOP_MM` rationale).
- **Live:** defaults are used: 25.0 / 5.0 in generators, 50.0 in the footer, 5.0 in `PreflightConfig`.
- **Archived:** substitutes a different default (candidate `machines.py` safe 10.0).
- **Status:** **unresolved**. It needs a clearance-authority decision from the owner. Neither arm
  satisfies it.
