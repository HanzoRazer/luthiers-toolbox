# Smart Guitar v1.1 — Full CNC Build Handoff

> **Model:** `smart_guitar` | **Registry Status:** `STUB` → `COMPLETE` | **Session Date:** 2026-03-08

---

## Executive Summary

The Smart Guitar is the **first IoT-enabled instrument** in the The Production Shop codebase. This session created the authoritative v1.1 spec JSON with all 12 cavity definitions, updated the registry from `STUB` to `COMPLETE`, designed the full dual-board separated electronics architecture (Arduino Uno + Raspberry Pi 5), and generated **11,967 lines of G-code** across two phases covering the entire body build process.

**What works:** Body outline DXF (21-point R12 polygon), authoritative spec with all 12 cavities mapped to STEM grid 24×32 normalized coordinates, 2-phase G-code generation (front face routing + rear face electronics cavities), 3-tool library, build summary manifest, complete IoT cavity system (Pi 5 cavity, Arduino pocket, antenna recess, USB-C edge slot, 4 wiring channels).

**What breaks:** DXF outline is 44.4mm narrower and 19.1mm shorter than spec dimensions — build script scales to compensate, distorting the shape. Pickle positions use `y_from_bridge` while all other cavities use `y_from_top` — forced derivation at build time. Wiring channels have logical routes but zero coordinate pairs — build script infers endpoints from cavity centers. Output jack bore angle is undefined — G-code drills vertically with operator note.

**Critical annotation:** The DXF-to-spec dimension mismatch (SG-GAP-01) means the perimeter contour toolpath is scaled, not geometrically accurate. The DXF must be regenerated to match v1.1 body dimensions before any cutting operation. SG-GAP-01 and SG-GAP-02 are production blockers.

---

## Part 1 · Base Instrument

| Field | Value |
|-------|-------|
| Model ID | `smart_guitar` |
| Display Name | Smart Guitar |
| Spec Version | v1.1 |
| Category | `electric_guitar` |
| Scale Length | 628.65mm (24.75" — Gibson standard) |
| Frets | 24 |
| Strings | 6 |
| Body Style | Les Paul-Explorer hybrid angular |
| Body Dimensions | 444.5mm L × 368.3mm W × 44.45mm (1.75") thick |
| Body Material — Prototype | Khaya (African Mahogany), ~0.50 g/cm³ |
| Body Material — Production | Khaya, maple, ash |
| Neck Design | Headless — no headstock, locking nut clamp |
| Neck Joint | Bolt-on (4 bolt, neck pocket 76.2×55.9×15.9mm) |
| Overall Length | 812.8mm (headless saves ~180mm vs headed) |
| Pickups | HH — dual humbuckers, 92×40mm routes |
| Bridge | Headless fixed with fine tuners (95×42mm, 4 mount screws) |
| Controls | Volume, tone, rotary switch — top-mount plate (100×50mm) |
| Weight Estimate | 7.5 lbs (3.4 kg) |
| IoT Platform | Raspberry Pi 5 (compute/DSP) + Arduino Uno R4 (I/O coprocessor) — separated |
| Wireless | WiFi 6 + BLE 5.0 via dual-band PCB antenna under 2mm wood window |
| Charging | USB-C PD 20W edge-mount slot |
| Registry Status | `COMPLETE` (was `STUB`) |
| Neck Blank Length | 444.5mm minimum (368.3mm above body + 76.2mm pocket tenon) |
| Spec File | `instrument_geometry/body/specs/smart_guitar_v1.json` |

### IoT Architecture

| Board | Location | Power | Function |
|-------|----------|-------|----------|
| Arduino Uno R4 | `arduino_preamp_pocket` — near neck pickup, rear access | 9V PP3 battery (independent) | I/O coprocessor only — footswitches, pots, LEDs, BMS telemetry, relay bypass. No audio. |
| Raspberry Pi 5 (4GB) | `rear_electronics_cavity` — lower body, rear access | Li-ion 18650 + USB-C PD 20W | DSP, AI coaching, WiFi/BLE, NVMe SSD storage |

**Signal chain — canonical v2.0 (2026-03-23):**

| Path | Chain | Latency |
|------|-------|---------|
| A — Dry analog | P90 pickup → buffered splitter (1MΩ) → 1/4" TS output jack | 0ms |
| B — Digital processed | P90 pickup → buffered splitter → Hi-Z USB interface (Scarlett Solo) → Pi 5 USB → JACK (64-frame) → HiFiBerry DAC+ADC HAT (I2S GPIO) → headphone out + WiFi (PipeWire network sink) | ~3.1ms |
| Control | Arduino Uno R4 → USB serial → Pi 5 | n/a |

**WiFi audio:** PipeWire network sink via Pi 5 built-in WiFi — no additional hardware required.

**Deprecated:** Arduino ADC audio path (10-bit, 44.1kHz) — replaced by Hi-Z USB interface. Arduino is I/O coprocessor only.

_Reconciled across luthiers-toolbox and sg-spec repos. Commits: 7364621a (luthiers-toolbox), 898d0dd (sg-spec)._

---

## Part 2 · Subsystem Status Matrix

| Subsystem | Status | Can Produce G-code? | Notes |
|-----------|--------|---------------------|-------|
| Spec JSON v1.1 | ✅ CREATED | N/A | `smart_guitar_v1.json` — 12 cavities, headless, Gibson scale, Khaya |
| Registry Entry | ✅ UPDATED | N/A | `STUB` → `COMPLETE`, IoT fields, all cam_features |
| Body Outline DXF | ⚠️ EXISTS (STALE) | Phase 1 perimeter (scaled) | 21-point polygon, dimensions don't match v1.1 spec |
| DXF Generator Script | ✅ EXISTS | Can regenerate | `scripts/generate_smart_guitar_dxf.py` — stale scale comment |
| Phase 1 G-code (Front Face) | ✅ GENERATED | Yes (5,350 lines) | OP10–OP50, cavity positions from spec |
| Phase 2 G-code (Rear Face) | ✅ GENERATED | Yes (6,617 lines) | OP60–OP71, electronics cavities + wiring |
| Build Summary | ✅ GENERATED | N/A | `SmartGuitar_v1_BuildSummary.json` |
| Full-Build Generator Script | ✅ CREATED | Yes | `scripts/generate_smart_guitar_full_build.py` |
| Neck CNC Pipeline | ❌ MISSING | No | Headless neck requires locking nut slot, no fret pipeline |
| Fret Slot CAM | ⚠️ EXISTS (disconnected) | Separate API call | `fret_slots_cam.py` (934 lines), not wired to build |
| Vectorizer | ⚠️ PARTIAL | No | GridZoneClassifier wired (uncommitted), Smart Guitar not trained |
| sg-spec Contract | ✅ EXISTS | N/A | `sg-spec/` repo: Pydantic schemas, cavity map JSON |

---

## Part 3 · CNC Program Summary

### Machine & Post Processor

| Parameter | Value |
|-----------|-------|
| Machine Target | GRBL_3018_Default |
| Units | Millimeters (G21) throughout — both phases |
| Post Processor | Generic GRBL (G90 G17 G54) |
| Workholding | Double-sided tape + 4 registration pins + 6 holding tabs (12mm wide × 3mm tall) |
| Stock | Khaya (African Mahogany) 444.5 × 368.3 × 44.45mm |

### Tool Library

| Tool | Diameter | Type | RPM | Feed | Plunge | DOC | Used In |
|------|----------|------|-----|------|--------|-----|---------|
| T1 | 10mm | 2-flute flat end mill | 18,000 | 5,000 mm/min | 800 mm/min | 5.0mm | OP20–OP22, OP60–OP61 (rough pockets) |
| T2 | 6mm | 2-flute flat end mill | 18,000 | 3,500 mm/min | 600 mm/min | 1.5mm | OP25–OP26, OP30, OP50, OP62–OP63 (finish, perimeter, recess) |
| T3 | 3mm | Flat/drill | 20,000 | 1,500 mm/min | 400 mm/min | 1.0mm | OP10, OP40–OP42, OP70–OP71 (channels, drilling, slots) |

### G-code Files

| File | Phase | Operations | Lines | Size | Tool Changes |
|------|-------|------------|-------|------|--------------|
| `SmartGuitar_v1_Phase1_FrontFace.nc` | 1 | OP10–OP50: fixtures, pockets, drilling, perimeter | 5,350 | 120 KB | 4 (T3→T1→T2→T3→T2) |
| `SmartGuitar_v1_Phase2_RearFace.nc` | 2 | OP60–OP71: rear cavities, channels, slots | 6,617 | 143 KB | 4 (T1→T2→T1→T2→T3) |
| `SmartGuitar_v1_BuildSummary.json` | — | Manifest + metadata | — | 3.2 KB | — |

### Operation Sequence

**Phase 1 — Front Face** (body face-up, Z=0 at top surface)

| Op | Description | Tool | Depth | Strategy |
|----|-------------|------|-------|----------|
| OP10 | Fixture / registration holes (4×) | T3 | 10mm | G83 peck drill in waste corners |
| OP20 | Neck pocket rough | T1 | 15.9mm | Helical entry + spiral-outward |
| OP21 | Neck pickup cavity rough | T1 | 19mm | Helical entry + spiral-outward |
| OP22 | Bridge pickup cavity rough | T1 | 19mm | Helical entry + spiral-outward |
| OP25 | Neck pocket finish | T2 | 15.9mm | Fine stepover finish pass |
| OP26a/b | Pickup cavities finish (2×) | T2 | 19mm | Fine stepover finish pass |
| OP30 | Control plate surface recess | T2 | 3mm | Shallow pocket for top-mount plate |
| OP40 | Headless bridge mount holes (4×) | T3 | 15mm | G83 peck drill, 80×35mm pattern |
| OP41 | Pot shaft holes (3× 9.5mm through) | T3 | 44.45mm | Helical bore (9.5mm bore via 3mm tool) |
| OP42 | Output jack bore (12.7mm) | T3 | 25mm | Helical bore (NOTE: vertical, not angled) |
| OP50 | Body perimeter contour | T2 | 44.45mm (through) | Profile with 6 tabs, 3mm tab height |

**Phase 2 — Rear Face** (flip body, Z=0 at rear surface, use registration pins)

| Op | Description | Tool | Depth | Strategy |
|----|-------------|------|-------|----------|
| OP60 | Rear electronics cavity (Pi 5) — rough + finish | T1→T2 | 22mm | Helical + spiral, 95×65mm |
| OP61 | Arduino preamp pocket — rough + finish | T1→T2 | 20mm | Helical + spiral, 80×60mm |
| OP62 | Antenna recess (2mm shelf) | T2 | 24mm total (22+2) | Extension of electronics floor |
| OP63a/b | Rear cover plate recesses (2×) | T2 | 2mm | Shallow lip around each cavity |
| OP70 | Wiring channels (4 routes) | T3 | 15mm | Linear plunge + traverse |
| OP71 | USB-C edge slot | T3 | 6.5mm | Linear traverse from edge |

### Workpiece Orientation & Setup

1. **Phase 1:** Khaya slab face-up, origin at lower-left of stock. Z=0 at top surface. Route all visible-side features: neck pocket, pickup cavities, bridge holes, pot holes, output jack, control plate recess, full body perimeter with tabs.
2. **Phase 2:** Flip body to rear face using registration pins from OP10 for alignment. Re-zero Z to rear surface. Route all electronics cavities, wiring channels, cover plate recesses, and USB-C slot.

### Cavity Map (STEM Grid Coordinates)

| Cavity | Grid Zone | Grid (x, y) Norm | Body Center mm | Dimensions mm | Depth mm | Face |
|--------|-----------|-------------------|----------------|---------------|----------|------|
| neck_pocket | HEADSTOCK | 0.50, 0.10 | x=0, y=53.3 | 76.2 × 55.9 | 15.9 | Front |
| neck_pickup_route | NECK_ZONE | 0.50, 0.38 | x=0, y=167.6* | 92 × 40 | 19 | Front |
| bridge_pickup_route | BRIDGE_SADDLE | 0.50, 0.67 | x=0, y=294.6* | 92 × 40 | 19 | Front |
| bridge_route | BRIDGE_SADDLE | 0.50, 0.72 | x=0, y=320 | 95 × 42 | 12 | Front |
| control_plate_surface | BODY_CANVAS | 0.65, 0.78 | x=55.2**, y=346.7** | 100 × 50 | 3 | Front |
| output_jack | LOWER_BOUT | 0.80, 0.88 | x=110.4, y=391.2 | ⌀12.7 bore | 25 | Front |
| rear_electronics_cavity | BODY_CANVAS | 0.60, 0.62 | x=36.8, y=275.7 | 95 × 65 | 22 | Rear |
| arduino_preamp_pocket | NECK_ZONE | 0.60, 0.30 | x=36.8, y=133.5 | 80 × 60 | 20 | Rear |
| antenna_recess | BODY_CANVAS | 0.56, 0.46 | x=22.2, y=202.6 | 50 × 30 | 2 | Rear |
| rear_wiring_channel | (multi-zone) | — | — | 10 wide | 15 | Rear |
| usb_c_port | BODY_CANVAS | 0.99, 0.54 | x=216, y=239.4 | 12 × 6.5 slot | 7 | Edge |

\* Derived: `y_from_top = bridge_y(320) - y_from_bridge` — see SG-GAP-04
\** Derived from grid_position: `x = (0.65-0.5) × 368.3`, `y = 0.78 × 444.5` — see SG-GAP-05

---

## Part 4 · Asset Inventory

### Created This Session

| Asset | Path | Type |
|-------|------|------|
| Spec JSON v1.1 | `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json` | Authoritative spec |
| Phase 1 G-code | `exports/smart_guitar_v1/SmartGuitar_v1_Phase1_FrontFace.nc` | 5,350 lines |
| Phase 2 G-code | `exports/smart_guitar_v1/SmartGuitar_v1_Phase2_RearFace.nc` | 6,617 lines |
| Build Summary | `exports/smart_guitar_v1/SmartGuitar_v1_BuildSummary.json` | Manifest |
| Generator Script | `scripts/generate_smart_guitar_full_build.py` | Reproducible build |

### Modified This Session

| Asset | Path | Change |
|-------|------|--------|
| Registry | `services/api/app/instrument_geometry/instrument_model_registry.json` | `STUB` → `COMPLETE`, IoT fields, headless, cam_features |
| sg-spec cavity map | `sg-spec/smart_guitar_cavity_map.json` | Cavity definitions synced |

### Pre-Existing (Unchanged)

| Asset | Path | Notes |
|-------|------|-------|
| Body DXF | `instrument_geometry/body/dxf/electric/Smart-Guitar-v1_preliminary.dxf` | 21-point outline, dimensions stale (SG-GAP-01) |
| DXF Generator | `scripts/generate_smart_guitar_dxf.py` | Stale 25.5" scale comment (SG-GAP-11) |
| Fret Calculator | `calculators/fret_slots_cam.py` | 934 lines, not wired to build |
| Vectorizer | `services/blueprint-import/vectorizer_phase3.py` | GridZoneClassifier wired (uncommitted) |

---

## Part 5 · Gap Registry

| ID | Gap | Severity | Category | Shared With |
|----|-----|----------|----------|-------------|
| SG-GAP-01 | **DXF body outline doesn't match spec dimensions.** DXF measures 323.9×425.4mm vs spec 368.3×444.5mm — 44.4mm narrow (12.1%) and 19.1mm short (4.3%). Build script scales X and Y independently, distorting the Explorer-Klein shape. The DXF was generated from the pre-v1.1 21-point polygon and never updated for the v1.1 body dimensions. | **CRITICAL** | DXF / Asset | FV-GAP-01 (Flying V DXF missing) |
| SG-GAP-02 | **DXF X-axis is asymmetric — centerline offset.** DXF X range: -139.7mm to +184.15mm. Body centerline (x=0) is 22.2mm off-center within the bounding box. Treble horn extends 44.45mm further than bass side. Build script assumes center = midpoint of bounding box, so all cavity placements relative to `x_center=0` are shifted from the acoustic centerline. | **CRITICAL** | DXF / Geometry | LP-GAP-02 (heuristic cavity positions) |
| SG-GAP-03 | **Output jack bore angle undefined.** Spec says "angled bore through lower bout edge" but no `angle_degrees` field exists. Build script drills vertically with an operator note. Actual installation requires a 15-30° angled bore from the body edge inward. | **HIGH** | Spec / Missing Field | — |
| SG-GAP-04 | **Pickup positions use `y_from_bridge`, not `y_from_top`.** Both pickup cavities position relative to bridge saddle (neck: 152.4mm, bridge: 25.4mm) while all 9 other cavities use `y_from_top`. Build script derives: `y_from_top = 320 - y_from_bridge`. If bridge position changes, pickup positions silently break. | **HIGH** | Spec / Consistency | — |
| SG-GAP-05 | **Control plate has NO `body_position_mm`.** Sole cavity positioned only via `grid_position` (normalized 0–1). Every other cavity has absolute `body_position_mm` with `x_center` and `y_from_top`. Build script converts: `x = (0.65 - 0.5) × 368.3 = 55.2mm`, `y = 0.78 × 444.5 = 346.7mm`. | **HIGH** | Spec / Consistency | — |
| SG-GAP-06 | **Wiring channels have no coordinate pairs.** `rear_wiring_channel.paths` contains 4 route objects with `from`/`to` labels and `length_mm` but zero XYZ coordinates. Build script infers endpoints from connected cavity centers. Actual channels need specific entry/exit points to avoid intersecting other features or structural wood. | **HIGH** | Spec / Missing Data | — |
| SG-GAP-07 | **Neck pocket bolt pattern undefined.** Type is `bolt_on` but no bolt hole positions, diameters, count, or spacing defined. Standard bolt-on uses 4 screws in a rectangular or trapezoidal pattern. Build script generates the pocket but skips bolt pilot holes entirely. | **HIGH** | Spec / Missing Field | — |
| SG-GAP-08 | **Cover plate screw positions undefined.** Both rear cavities specify cover plates (electronics: 4× M3, Arduino: 2× M3) but no screw position coordinates. Build script generates cover recesses but skips M3 pilot holes. | **MEDIUM** | Spec / Missing Field | — |
| SG-GAP-09 | **USB-C slot requires edge routing (3+1 axis).** Spec defines an edge-routed slot perpendicular to body surface. A standard 3-axis CNC cannot reach this orientation. Build script approximates by milling from the rear face vertically. Production requires either a 4th-axis rotary, manual router jig, or redesign as a rear-access slot. | **MEDIUM** | CAM / Axis Limitation | — |
| SG-GAP-10 | **Antenna recess depth geometry ambiguous.** Spec says 2mm pocket depth with "2mm wood cover remaining." But the recess is described as "a stepped shelf inside the rear electronics cavity." From rear surface: 22mm (elec cavity) + 2mm (recess) = 24mm deep. Remaining front wood: 44.45 - 24 = 20.45mm — far more than "2mm cover." For the 2mm wood window to work, total depth from rear must be 42.45mm (44.45 - 2). Spec intent vs. math needs clarification. | **MEDIUM** | Spec / Ambiguity | — |
| SG-GAP-11 | **DXF generator has stale scale length comment.** `generate_smart_guitar_dxf.py` references "Scale: 25.5"" (Fender) from before the Gibson 24.75" correction. Cosmetic but misleading. | **LOW** | Script / Comment | — |
| SG-GAP-12 | **No `corner_radius` on any pocket.** No cavity in the spec declares minimum internal corner radius. T1 (10mm) leaves 5mm fillets, T2 (6mm) leaves 3mm fillets. Hardware fitment (Pi 5 board = sharp corners, Arduino = sharp corners) requires either spec-declared radii or corner-relief cuts. | **LOW** | Spec / Missing Field | FV-GAP-07 (no corner dogbone relief) |
| SG-GAP-13 | **No G-code simulation/backplot validation.** 11,967 lines across 2 phases unverified for collisions, over-depth plunges, or tab miscalculation. | **MEDIUM** | Verification | LP-GAP-08 (452K unverified lines) |
| SG-GAP-14 | **No G43 tool length compensation emitted.** All tool changes require manual Z-touch-off. | **LOW** | Post / G-code | LP-GAP-06, FV-GAP-07 |

---

## Part 6 · Cross-References to Prior Builds

| Shared Gap Pattern | This Build | Les Paul | Flying V | OM-28 | Benedetto |
|-------------------|------------|----------|----------|-------|-----------|
| DXF dimensions stale/missing | SG-GAP-01 | LP-GAP-01 | FV-GAP-01 | — | — |
| Cavity positions heuristic/derived | SG-GAP-02, SG-GAP-04, SG-GAP-05 | LP-GAP-02 | FV-GAP-10 | — | — |
| No cutter compensation (G41/G42/G43) | SG-GAP-14 | LP-GAP-06 | FV-GAP-07 | OM-PURF-07 | — |
| No simulation validation | SG-GAP-13 | LP-GAP-08 | — | — | — |
| Corner radius / dogbone relief | SG-GAP-12 | — | FV-GAP-07 | — | — |

### New gaps unique to this build

- **SG-GAP-03:** First design with an angled bore (output jack) — all prior guitars use top-mount or rear-mount jacks.
- **SG-GAP-06:** First design with a multi-route wiring channel system — prior builds had 1–3 simple channels.
- **SG-GAP-07:** First bolt-on neck design to reach G-code phase — all prior builds were set-neck.
- **SG-GAP-09:** First design requiring 4th-axis capability (edge-mount USB-C slot).
- **SG-GAP-10:** First design with RF-transparent wood window — depth geometry uniquely constrained by antenna physics.
- **SG-GAP-12:** First design where internal electronics have sharp-cornered PCBs that must fit inside CNC-milled pockets with tool-radius fillets.

### Evolution note

The Smart Guitar is the first instrument to produce **IoT electronics integration** — cavity design driven by PCB dimensions, battery compartments, antenna physics, and cable routing rather than traditional guitar pickup/control geometry. This exposes a new category of gaps (SG-GAP-09, SG-GAP-10, SG-GAP-12) that no prior acoustic or electric guitar build encountered.

---

## Part 7 · Remediation Roadmap

### Phase A — Pre-Cut Validation (before any machining)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Regenerate DXF from `generate_smart_guitar_dxf.py` with corrected v1.1 body dimensions (368.3×444.5mm) | SG-GAP-01 | 1 hour |
| Fix DXF centerline: ensure body acoustic center = x=0 in DXF coordinate frame | SG-GAP-02 | 30 min |
| Run both `.nc` files through CAMotics or NCViewer, verify cavity positions | SG-GAP-13 | 30 min |
| Print 1:1 template from Phase 1, overlay Arduino Uno + Pi 5 boards, verify fit with corner fillets | SG-GAP-12 | 30 min |
| Add `G43 H{n}` after each tool change in generator | SG-GAP-14 | 15 min |
| Fix stale "25.5 inch" scale comment in DXF generator | SG-GAP-11 | 5 min |

### Phase B — Spec Completeness (resolves derived/missing positions)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Add `y_from_top` to both pickup cavity `body_position_mm` (neck: 167.6, bridge: 294.6) | SG-GAP-04 | 15 min |
| Add `body_position_mm` to `control_plate_surface` with absolute mm coordinates | SG-GAP-05 | 15 min |
| Add XYZ start/end coordinates to each wiring channel path | SG-GAP-06 | 1 hour |
| Add `bolt_pattern` to neck pocket: 4 holes, M5 diameter, rectangular spacing | SG-GAP-07 | 30 min |
| Add `screw_positions` to both rear cover plates with M3 hole coordinates | SG-GAP-08 | 30 min |
| Add `angle_degrees` field to output jack (target: 20° from vertical) | SG-GAP-03 | 15 min |
| Add `corner_radius_mm` to all rectangular pockets | SG-GAP-12 | 30 min |
| Clarify antenna recess: define absolute depth from rear surface (42.45mm for 2mm window) | SG-GAP-10 | 15 min |

### Phase C — CAM Capability Upgrade

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Add angled bore G-code support (rotated work plane or 4th-axis G68) for output jack | SG-GAP-03 | 3 hours |
| Add edge-routing support (4th-axis or fixture jig) for USB-C slot | SG-GAP-09 | 3 hours |
| Wire `fret_slots_cam.py` into build as Phase 3 (24 frets, Gibson scale) | LP-GAP-04 (shared) | 2 hours |
| Build headless neck CNC pipeline (locking nut slot, no headstock) | New | 8+ hours |
| Re-generate G-code after all Phase A+B fixes, validate with simulation | SG-GAP-13 | 1 hour |

---

## Part 8 · Design Decisions & Rationale

### Why Separated Boards?

**Stacked layout (rejected):** Arduino + Pi 5 stacked = 42mm — exceeds the 40mm usable cavity depth (44.45mm stock minus 4mm structural floor). No clearance for cables.

**Side-by-side layout (rejected):** Both boards in one cavity requires minimum 140×70mm. Largest reasonable cavity in the Explorer-Klein body is 130×75mm — the asymmetric shape constrains available wood.

**Separated layout (accepted):** Arduino near neck pickup (short analog signal path, active preamp style) with independent 9V PP3 battery. Pi 5 in lower body rear cavity with Li-ion 18650 power. Connected by USB serial through wiring channel. Each board has its own cover plate.

### Why Headless?

- Saves ~180mm overall length (812.8mm vs ~990mm)
- Eliminates headstock wood, tuner holes, nut slot — simplifies CNC
- Headless bridge with fine tuners keeps tuning precision
- Better balance — no headstock dive on the lightweight Explorer-Klein shape
- Fewer CNC operations (no headstock profile, no tuner bore pattern)

### Why Gibson Scale (24.75") with 24 Frets?

- Gibson scale + 24 frets places the last fret at the neck-body joint — clean bolt-on geometry
- Shorter scale = slightly lower string tension = easier bending for the IoT teaching use case
- 24 frets provide full 2-octave range needed for the AI coaching system

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total gaps | 14 |
| Critical | 2 |
| High | 5 |
| Medium | 4 |
| Low | 3 |
| Shared with prior builds | 5 (of 14) |
| New/unique to Smart Guitar | 9 |
| G-code files generated | 2 |
| Total G-code lines | 11,967 |
| Tool changes across all programs | 8 |
| Distinct bits required | 3 (T1–T3) |
| CNC operations | 17 (OP10–OP71) |
| IoT cavities defined | 5 (Pi 5, Arduino, antenna, USB-C, wiring) |
| Wiring routes | 4 |
| Registry status change | `STUB` → `COMPLETE` |
| Files created this session | 5 |
| Files modified this session | 2 |
| Build phases | 2 (Front Face → Rear Face) |
| First IoT instrument build | ✅ Yes |
| First headless design | ✅ Yes |
| First bolt-on neck at G-code phase | ✅ Yes |
