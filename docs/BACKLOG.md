# Production Shop — Implementation Backlog

Items here are fully analyzed and scoped. Each one has a source, a
specific file path, and enough context to implement without re-researching.
Nothing here was invented in a planning meeting — every item came from
reading actual code.

---


## TEST-001 — Fix 33 pre-existing test failures

**Status:** Known, not investigated
**Priority:** Medium
**Effort:** Unknown until investigated

33 tests consistently fail in pytest runs.
They are pre-existing and unrelated to recent work.

**First step:** Run pytest with -v and capture
the failing test names:
```bash
pytest services/api/tests/ -v 2>&1 | grep "FAILED" | head -40
```

**Then:** Triage into:
- Genuinely broken (fix)
- Skipped intentionally (add skip marker)
- Environment-dependent (document)

Do not fix them now — just document in BACKLOG.

---


## WOOD-001 — Merge material registries

**Status:** Structural cleanup, not urgent  
**Priority:** Low

Two separate material tables exist:
- `materials/registry/tonewoods.py` — machining properties (feeds/speeds context)
- `calculators/plate_design/calibration.py` (after PORT-001) — acoustic properties

Neither knows about the other. Long term they should be one record per species.
Short term they can coexist — do not block PORT-001 on this.

---

## Notes on how this backlog works

Each item here was identified by reading code, not by speculation.
Every "file to create" path is deliberate — it fits the existing module structure.
Every "what exists" section cites real function names from the actual codebase.

When an item is implemented: delete it from here and add it to `CHANGELOG.md`.
When a new gap is found during implementation: add it here before closing the session.
Do not let findings live only in conversation history.

---

## CONSTRUCTION-005 — Glue joint geometry calculator

**Status:** Not implemented  
**Priority:** Medium  
**Effort:** ~half day

**What exists:** `generators/stratocaster_body_generator.py` has neck pocket routing, but it's body-specific CAM, not a geometry calculator

**What's missing:**

*Dovetail (set neck):*
- Joint angle (typically 10-15°), cheek width, tenon depth, mortise depth
- Heel carve profile — how much material removed from heel for neck reset access
- Glue surface area calculation

*Bolt-on:*
- Screw placement pattern (4-bolt vs 3-bolt), ferrule sizing, neck plate geometry
- Torque spec by screw diameter and wood density

*Set neck (Les Paul style):*
- Tenon dimensions relative to body thickness and neck pocket depth
- Pocket angle for correct neck pitch

**File to create:** `calculators/neck_joint_calc.py`

---




