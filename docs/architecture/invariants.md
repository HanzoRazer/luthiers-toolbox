# Architecture Invariants (v1)

These invariants are **human policy**, with **machine heuristics** that flag likely violations.
The scan harness is **read-only** and **non-blocking**; humans decide what to fix and when.

## INV-001: GCODE_TRACEABLE

**Rule:** All machine-executable output (G-code / DXF) must be traceable to a persisted artifact (hashes + provenance).

**Heuristic violation:** A file contains **machine output signals** *and* **direct response signals** but **no persistence signals**.

Examples of signals:
- Machine output: `gcode`, `.nc`, `dxf`, `ezdxf`
- Direct response: `Response(`, `PlainTextResponse`
- Persistence: `store_artifact`, `persist_run`, `write_run_artifact`

## INV-002: AI_NO_AUTHORITY

**Rule:** Code under `_experimental/` must not create authority (IDs, artifacts, safety decisions).

**Heuristic violation:** A file under `_experimental/` contains any of:
- ID creation: `uuid.uuid4`, `create_run_id`
- Persistence: `store_artifact`, `persist_run`, `write_run_artifact`
- Safety gate: `compute_feasibility`, `should_block`, `risk_bucket`

## INV-003: ADVISORY_ATTACHED

**Rule:** Advisory artifacts must attach to a parent run (e.g., `parent_id` / `run_id` linkage).

**Heuristic violation:** File appears advisory-related (mentions `advisory`) but lacks any clear run linkage markers
(`parent_id`, `run_id`, `attach_advisory`).

---

## Notes

- v1 favors **finding things** over being perfectly precise.
- False positives are acceptable; every finding should be verified with a local diff/read.
- Future versions can move from substring heuristics to AST/import analysis when needed.
