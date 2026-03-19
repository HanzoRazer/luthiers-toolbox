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
## CONSTRUCTION-003 — Fret leveling geometry

**Status:** Not implemented  
**Priority:** Medium  
**Effort:** ~3 hours

**What exists:** nothing directly applicable  
**What it needs:** given a measured fret height map (dict of fret number → height_mm from a straightedge or digital gauge), compute:

1. Best-fit plane through all fret tops (least squares)
2. Cut depth at each fret = current height − plane height at that position
3. Flag any fret where cut depth > (current height − minimum playable height)
4. Output: which frets to level, which to replace, total material removed estimate

**Minimum playable fret height:** typically 0.5mm (depends on fret wire spec)  
**File to create:** `calculators/fret_leveling.py`

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

## CONSTRUCTION-006 — Humidity and wood movement

**Status:** Not implemented — zero coverage  
**Priority:** Low-Medium (Houston has real humidity risk)  
**Effort:** ~3 hours

**The physics:**
```
ΔW = W₀ × (MC₂ - MC₁) × S_r
where:
  ΔW = dimensional change (mm)
  W₀ = initial dimension (mm)
  MC  = moisture content (%)
  S_r = shrinkage coefficient (species-dependent, radial vs tangential)
```

**Equilibrium moisture content from RH:**  
EMC% ≈ (RH / (100 - RH)) × K (Henderson equation with species factor K)

**What to build:**
- Wood movement table per species (radial/tangential shrinkage coefficients)
- EMC calculator from temperature + RH
- Crack risk assessment: seasonal RH swing → dimensional change → stress vs wood MOR

**Houston-specific note:** RH swings 30–90% seasonally. A 400mm-wide top at 30% RH
vs 80% RH moves 3-6mm depending on species. That's crack territory for improperly sealed instruments.

**File to create:** `calculators/wood_movement.py`

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

## GEOMETRY-004 — Bridge design geometry

**Status:** Saddle position and compensation exist; bridge shape absent  
**Priority:** Medium  
**Effort:** ~half day

**What exists:**
- `instrument_geometry/bridge/geometry.py`:
  - `compute_bridge_location_mm()` — bridge centerline from nut
  - `compute_saddle_positions_mm(scale_length_mm, compensations_mm)` — per-string positions
  - `compute_compensation_estimate(gauge_mm, is_wound, action_mm)` — rough compensation
  - `compute_bridge_height_profile(width_mm, string_count, radius_mm, base_height_mm)` — saddle crown

**What's missing:**

*1. Saddle slant angle (the J-45 / Taylor question):*
```
# compute_saddle_positions_mm() already returns per-string positions
# The slant angle is just:
Δcomp = comp_low_E_mm - comp_high_e_mm    # ~2mm typical
string_spread_mm = distance between outer string contact points
slant_angle_deg = degrees(arctan(Δcomp / string_spread_mm))
# Typical result: 2.0–4.0°, Gibson J-45 = ~4°
```
This should be added directly to `compute_saddle_positions_mm()` as an output field —
the data is already there.

*2. Bridge footprint geometry:*
- Bridge pin hole positions (offset from saddle, typically 9–11mm)
- Bridge plate dimensions (internal reinforcement under bridge)
- Belly profile (the raised section forward of the saddle on acoustic bridges)
- Tie block dimensions (classical/nylon string)

*3. Saddle slot dimensions:*
- Slot width from saddle blank width (typically 2.4–3.2mm)
- Slot depth = saddle blank height − saddle projection (must seat ≥3mm)
- Slot angle = saddle slant angle (must match cut to slant)

**Add to existing file:** `instrument_geometry/bridge/geometry.py`
```python
def compute_saddle_slant_angle(
    compensations_mm: Dict[str, float],
    string_positions_mm: Dict[str, float],
) -> float   # degrees

def compute_bridge_pin_positions(
    saddle_positions_mm: Dict[str, float],
    pin_to_saddle_mm: float = 10.0,
) -> Dict[str, float]

def compute_bridge_plate_dimensions(
    bridge_width_mm: float,
    string_tension_total_N: float,   # from calculators/string_tension.py
    top_thickness_mm: float,
) -> BridgePlateSpec
```

---

## GEOMETRY-005 — Neck block and tail block sizing

**Status:** Not implemented — no standalone calculator  
**Priority:** Medium  
**Effort:** ~2 hours

**What exists:**
- `instrument_geometry/specs/martin_d28_1937.py` — side depth profile includes kerfing offset
- Neck pocket routing exists in body generators (body-specific CAM, not a calculator)

**What's missing:** structural sizing from first principles.

**Neck block:**
```
# Minimum glue surface area for neck joint strength:
# String tension pulls neck forward with ~45–80 kg total force
# Wood shear strength (mahogany): ~8 MPa
# Safety factor 4:

min_glue_area_mm2 = (total_string_tension_N × safety_factor) / shear_strength_MPa
# Typical: (600N × 4) / 8 = 300 mm²
# Typical neck block face: 90mm × 60mm = 5400 mm² — well above minimum
# But dovetail vs bolt-on vs tenon each have different effective shear areas

# Block height = side depth at neck end (from SIDE_PROFILE data)
# Block width = typically upper bout width × 0.45
# Block thickness = typically 60–75mm along body centerline
```

**Tail block:**
```
# Tail block is compressive — end pin pulls strap load (strap + guitar weight)
# Typically 90mm wide × 50mm tall × side_depth deep
# No structural calculation needed — geometry is by convention
```

**Connect to:**
- `instrument_geometry/specs/martin_d28_1937.py` — side depth profile
- `calculators/string_tension.py` — neck block sizing input

**File to create:** `calculators/neck_block_calc.py`
```python
def compute_neck_block_dimensions(
    upper_bout_width_mm: float,
    side_depth_at_neck_mm: float,
    joint_type: Literal["dovetail", "bolt_on", "tenon"],
    total_string_tension_N: float,
) -> NeckBlockSpec
```

---

## GEOMETRY-006 — Fret wire selection

**Status:** Not implemented — no fret wire data or calculator  
**Priority:** Medium  
**Effort:** ~2 hours

**What exists:**
- `instrument_geometry/neck/radius_profiles.py` — `compute_fret_crown_height_mm()` takes `fret_height_mm` as input but has no table of actual fret wire dimensions
- `calculators/nut_slot_calc.py` (CONSTRUCTION-001) will need fret crown height — depends on this

**What's missing:** a fret wire specification table and selection calculator.

**Standard fret wire profiles (industry data):**
```python
FRET_WIRE_PROFILES = {
    "vintage_narrow":   FretWireSpec(crown_width_mm=2.0,  crown_height_mm=1.0,  tang_width_mm=0.5),
    "medium":           FretWireSpec(crown_width_mm=2.4,  crown_height_mm=1.2,  tang_width_mm=0.5),
    "medium_jumbo":     FretWireSpec(crown_width_mm=2.7,  crown_height_mm=1.3,  tang_width_mm=0.6),
    "jumbo":            FretWireSpec(crown_width_mm=2.9,  crown_height_mm=1.5,  tang_width_mm=0.6),
    "tall_narrow":      FretWireSpec(crown_width_mm=2.0,  crown_height_mm=1.5,  tang_width_mm=0.5),  # "mandolin style"
    "stainless_6105":   FretWireSpec(crown_width_mm=2.3,  crown_height_mm=1.4,  tang_width_mm=0.5),  # common SS
    "gold_evo":         FretWireSpec(crown_width_mm=2.4,  crown_height_mm=1.3,  tang_width_mm=0.5),
}
```

**Selection logic:**
```
# Playability: wider crown = easier bending, less precise intonation feel
# Durability: taller crown = more leveling material before replacement
# Fretboard radius: tighter radius boards suit taller frets (less rocking)
# Slot width must match tang width ±0.02mm for press fit without splitting

slot_width_tolerance_mm = fret_wire.tang_width_mm + 0.01   # light press fit
# If slot_width < tang_width - 0.05: tang barbs won't compress → fret pops
# If slot_width > tang_width + 0.05: fret seats loose, buzzes
```

**Connect to:**
- `instrument_geometry/neck/radius_profiles.py` — `compute_fret_crown_height_mm()` should accept a `FretWireSpec` instead of raw `fret_height_mm`
- `calculators/nut_slot_calc.py` (CONSTRUCTION-001) — slot depth depends on fret crown height
- `cam/neck/config.py` — `FretSlotConfig.slot_width_mm` should derive from tang width

**File to create:** `calculators/fret_wire_calc.py`
```python
@dataclass
class FretWireSpec:
    crown_width_mm: float
    crown_height_mm: float
    tang_width_mm: float
    tang_depth_mm: float
    material: Literal["nickel_silver", "stainless", "gold_evo", "brass"]
    wear_factor: float    # relative wear rate, nickel_silver = 1.0

def select_fret_wire(
    fretboard_radius_mm: float,
    playing_style: Literal["fingerstyle", "flatpicking", "shredding"],
    preference: Literal["vintage", "modern", "durability"],
) -> List[FretWireSpec]   # ranked recommendations
```

---

## GEOMETRY-007 — Nut compensation: zero-fret vs traditional

**Status:** Traditional nut compensation exists as parameter; zero-fret not modeled  
**Priority:** Medium  
**Effort:** ~2 hours

**What exists:**
- `instrument_geometry/neck/fret_math.py` line 109: `nut_comp_mm: float = 0.0` parameter in `compute_compensated_scale_length_mm()`
- `tests/instrument_geometry/test_instrument_geometry.py` line 133: `test_nut_compensation_subtracts` — test confirms nut comp subtracts from scale length

**What's missing:** the calculation of *what* nut compensation should be, and the zero-fret alternative.

**Traditional nut compensation:**
```
# The nut acts as the zero fret. Fretting at fret 1 stretches the string
# slightly (increasing tension, sharpening pitch).
# Nut compensation moves the nut contact point slightly TOWARD the saddle:

nut_comp_mm = (string_diameter_mm / 2) × nut_break_angle_factor
# Typically 0.3–0.8mm depending on string gauge and break angle
# Heavier strings and steeper break angles need more compensation

# Fine compensation per string (for compensated nut):
nut_comp_per_string = f(gauge, is_wound, action_at_nut, break_angle)
```

**Zero-fret system:**
```
# A zero fret replaces the nut as the string contact point.
# The nut becomes a string guide only (no intonation responsibility).
#
# Advantages:
#   - Open strings have same tone as fretted strings (same contact material)
#   - Eliminates nut slot depth precision requirement
#   - Compensation handled entirely at saddle
#
# Zero-fret placement:
zero_fret_position_mm = 0.0   # AT the nut position
# Nut (now guide-only) sits 1–2mm behind zero fret
nut_to_zero_fret_mm = 1.5     # just enough to guide strings, not intonate them

# Scale length reference changes:
# Traditional: measured from nut face to saddle
# Zero-fret: measured from zero-fret crown center to saddle
# This shifts ALL fret positions by ~0.5mm (half the fret crown width)
```

**Add to existing file:** `instrument_geometry/neck/fret_math.py`
```python
def compute_nut_compensation_per_string(
    gauges_mm: List[float],
    is_wound: List[bool],
    action_at_nut_mm: float,
    break_angle_deg: float,
) -> List[float]   # compensation_mm per string

def compute_zero_fret_positions(
    scale_length_mm: float,
    fret_count: int,
    zero_fret_crown_width_mm: float = 1.0,
) -> ZeroFretSpec   # all fret positions adjusted for zero-fret reference
```

---

## GEOMETRY-008 — Tuning machine post height and string tree geometry

**Status:** Fields exist in headstock break angle calculator; no selection or sizing calculator  
**Priority:** Low-Medium  
**Effort:** ~2 hours

**What exists:**
- `calculators/headstock_break_angle.py`:
  - Line 92: `tuner_post_height_mm` — field present, default value used
  - Line 99: `string_tree_depression_mm` — field present
  - Line 104: `nut_to_string_tree_mm` — field present
  - Line 136: `needs_string_tree: bool` — computed output
  - Line 201: logic: if flat headstock and no string tree depression → angle = 0°

**What's missing:** the selection calculator that tells you WHICH tuner to use and whether a string tree is needed.

**Post height → break angle relationship:**
```
# For angled headstock (Gibson style):
break_angle = arctan(
    (nut_to_tuner_mm × sin(headstock_angle) - tuner_post_height_mm)
    / (nut_to_tuner_mm × cos(headstock_angle))
)
# Minimum recommended break angle: 7–10° for tone and tuning stability
# Too steep (>20°): string breaks at nut, excessive friction

# For flat headstock (Fender style):
# Break angle comes entirely from string tree or angled nut
# G and B strings on Strat-style heads need string trees because they run
# nearly parallel to headstock → near-zero break angle without tree
```

**String tree selection:**
```
# Need string tree if:
# break_angle_without_tree < 7°  AND  string is G or B (most common case)

# String tree types:
# "butterfly": depresses ~3mm, suits vintage Fender
# "roller": depresses ~3mm, reduces friction
# "disc": depresses ~2mm, modern
# "none": only valid if break angle ≥ 7° without it
```

**Post wrap count:**
```
# Strings should wrap 2–3 times around post for tuning stability
# More wraps = more slippage risk; fewer = string can pop off
# Post height determines how many wraps fit:
string_wraps = floor(post_height_mm / (string_diameter_mm + 0.5mm clearance))
```

**Add to existing file:** `calculators/headstock_break_angle.py`
```python
def compute_required_post_height(
    headstock_angle_deg: float,
    nut_to_post_mm: float,
    target_break_angle_deg: float = 9.0,
) -> float   # minimum post height in mm

def check_string_tree_needed(
    string_positions: List[str],   # ["E","A","D","G","B","e"]
    break_angles: List[float],
    min_break_angle_deg: float = 7.0,
) -> List[StringTreeSpec]
```

---

