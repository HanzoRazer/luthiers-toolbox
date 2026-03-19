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

## CONSTRUCTION-007 — Finish schedule calculator

**Status:** Not implemented — zero coverage  
**Priority:** Low  
**Effort:** ~1 day

No nitro schedule, no poly schedule, no grain fill calculator, no French polish guidance.
This is the longest phase of many builds and is completely dark in the codebase.

**Minimum viable implementation:**

```python
class FinishType(Enum):
    NITROCELLULOSE = "nitro"
    POLYURETHANE = "poly"
    OIL = "oil"
    FRENCH_POLISH = "french_polish"

class FinishSchedule:
    coats: List[CoatSpec]        # sequence of coat steps
    total_dry_time_hours: float
    sanding_schedule: List[SandingStep]
    grain_fill_coats: int        # from pore size estimate
```

**Grain fill model:** coats needed ≈ pore_depth_mm / coat_fill_mm_per_layer  
Pore size by species: rosewood ~0.3mm, mahogany ~0.2mm, maple ~0.05mm (barely needs filling)

**File to create:** `calculators/finish_schedule.py`

---

## CONSTRUCTION-008 — Electronics physical layout

**Status:** Not implemented  
**Priority:** Low  
**Effort:** ~3 hours

**What exists:**
- `calculators/wiring/impedance_math.py` — tone rolloff, pickup loading
- `calculators/wiring/treble_bleed.py`
- `instrument_geometry/pickup/cavity_placement.py` — pickup cavity routing

**What's missing:** physical layout — how the components are arranged in space:
- Pot spacing (minimum 19mm center-to-center to clear knobs)
- Jack placement relative to strap button and output path
- Control cavity routing paths for wire runs between pickups and controls
- Shielding area calculation (conductive paint coverage)
- Switch placement geometry

**File to create:** `calculators/electronics_layout.py`

---

## CONSTRUCTION-009 — Acoustic voicing history / longitudinal brace model

**Status:** Not implemented — structural gap between tap-tone-pi and toolbox  
**Priority:** High (this is the core lutherie intelligence loop)  
**Effort:** ~1 day design + implementation

**What exists in tap-tone-pi:**
- `analyzer/analysis/plate_tuning.py` — `TuningPoint` (mass + frequency per measurement)
  Linear regression on mass vs frequency — outputs objective math only
- Tap tone measurement acquisition (WAV → FFT → peaks)

**What's missing:** the longitudinal model — tap before/after brace thinning, record the shift, predict what further thinning will do.

**The physics:**  
For a plate: `f ∝ √(EI/ρ)` where I = bh³/12 (moment of inertia from brace cross-section)  
Thinning a brace by Δh → ΔI/I = 3Δh/h (cube law) → Δf/f ≈ 1.5 × Δh/h

**What to build:**
```python
class VoicingSession:
    plate: str                         # "top" | "back"
    measurements: List[TuningPoint]    # each is (mass_g, freq_hz, notes)
    brace_changes: List[BraceChange]   # what was removed between measurements

def predict_next_tap(
    session: VoicingSession,
    proposed_removal_mm3: float        # volume to remove from which brace
) -> FrequencyPrediction:
    """Given current regression slope and proposed material removal,
    predict new fundamental and whether it will cross target."""
```

**Connect to:** PORT-001 (plate design) — target frequency from `analyze_plate()` drives the voicing goal

**File to create:** `calculators/acoustic_voicing.py`  
**Also needed:** API endpoint + simple Vue panel showing the regression line with prediction

---

## CONSTRUCTION-010 — Build sequence composition (structural gap)

**Status:** Architecture gap — no individual file to create  
**Priority:** High — this is what makes all the above useful  
**Effort:** ~1 week (after individual calculators exist)

**The problem:**  
Every calculator in this codebase is a standalone tool. A builder doing a complete spec transfers numbers between them by hand:
- Headstock break angle result → nut slot angle (not connected)
- Saddle height → neck angle → body depth at neck block → top curvature from X-brace dish (not connected)
- String tension → brace sizing → plate thickness target (not connected)
- Tap tone reading → voicing decision → brace thinning → next tap prediction (not connected)

**The CAM workspace is starting to close this on the machining side** — `NeckPipelineConfig` flows through all four operations as shared state. The same pattern needs to exist for acoustic/setup calculations.

**What this looks like:**
```python
class BuildSpec:
    """Shared state that flows through the entire build sequence."""
    body: BodyCalibration          # from PORT-001 calibration.py
    top_plate: PlateThicknessResult
    back_plate: PlateThicknessResult
    neck: NeckPipelineConfig
    strings: StringSet
    setup: SetupSpec

class BuildSequence:
    """Ordered operations that populate and validate BuildSpec fields."""
    stages: List[BuildStage]       # each stage reads from + writes to BuildSpec
    
    def run_through(self, spec: BuildSpec) -> BuildReport:
        """Execute all stages, propagating outputs as inputs to the next."""
```

**Prerequisite:** CONSTRUCTION-001 through 009 don't all need to be done first — but the shared `BuildSpec` state object should be defined early so individual calculators can be connected to it incrementally.

---



