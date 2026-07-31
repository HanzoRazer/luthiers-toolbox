# Crosswalk — Shop Talk #20 → Luthier’s Toolbox & Tap Tone Pi

This map answers three questions for each teaching cluster:

1. **Already represented?** (docs/code today)  
2. **Missing?**  
3. **Destination type** — documentation, guided lab, design rule, measurement procedure, empirical model, or knowledge-base entry — with explicit “do **not** turn into another calculator” flags.

Point IDs refer to `ANNOTATED_LECTURE_NOTES.md` §12.

---

## Legend — destination types

| Type | Meaning |
|------|---------|
| **DOC** | Builder/engineer documentation |
| **LAB** | Guided laboratory workflow (stepwise measurement/voicing) |
| **RULE** | Design rule / decision gate in product logic or UX |
| **MEAS** | Measurement procedure / stage metadata contract |
| **EMP** | Empirical model or corpus table (calibrated from shop data) |
| **KB** | Knowledge-base entry (explanations, caveats, philosophy) |
| **NO-CALC** | Must remain knowledge/guidance — not a new closed-form calculator |

---

## A. Coverage matrix

| IDs | Topic | Status in Toolbox today | Gap severity | Primary destinations |
|-----|-------|-------------------------|--------------|----------------------|
| P01 | Uncoupled top (plug hole) | Partial — voicing stages exist; plug-hole SOP not first-class | Medium | **MEAS**, **LAB** |
| P02 | Mode-selective voicing | Thin — advisor/WSI exist; no guided “move mode A not B” | High | **LAB**, **KB**, **EMP** |
| P03–P05 | Scale-tone avoidance + 100/180/226 triad | Partial — WSI ingest; targets scattered (voicing 180/200, advisor 95/180/280/380, plate calib air/monopole bands). **No named mid-scale Gore triad** | High | **RULE**, **EMP**, **DOC** |
| P06–P08 | Bridge mass+stiffness / putty fallacy / Δf | Partial — geometry + mass-frequency tracker; no teaching model or putty warning UX | Medium | **KB**, **MEAS**, **EMP**, **NO-CALC** for putty simulator |
| P09–P11 | Monopole mobility | **Missing as mobility/admittance** — “monopole-like frequency” only | Critical | **EMP**, **MEAS**, **LAB**, **DOC** |
| P12–P13 | Free-top useless as finished proxy; design→closed-box | Partial — γ / stages encode physics; UX/docs understate the prohibition | High | **KB**, **RULE**, **LAB** |
| P14–P16 | Live vs non-live; lattice vanilla | Partial — 2-osc/3-osc models; little builder methodology | High | **KB**, **RULE**, **LAB**, **EMP** |
| P17–P18 | X scooped mids vs falcate | Partial — X/fan/ladder geometry; **falcate absent** | High | **DOC**, **KB**; falcate geometry later (separate build) |
| P19–P21 | Chladni symmetry / FRF identity / SRC vocab | Partial — γ from Chladni; SRC as Schelleng radiation_ratio in materials | Medium | **KB**, **DOC**, **LAB** |
| P22–P23 | Cross-dipole/tripole targeting policy | Missing as explicit policy | Medium | **RULE**, **KB** |
| P24 | Neck barely shifts body modes | Missing caveat near neck/body coupling | Low | **KB** |
| P25–P26 | Nut compensation global effect | Strong math/docs/calcs; “global tension” story can be clearer in UI copy | Low | **DOC**/UI copy |
| P27–P28 | Torrefaction; playing-in | Materials/process notes thin; archive types exist for drift | Low–Med | **KB**, **EMP** (time series) |
| P29–P31 | Double-top / archtop transfer / tilt neck | Sparse | Low | **KB** |
| P32 | Upper-back stiffening | Thin | Low | **KB** |
| P33–P34 | VA FRF SOP; DIY Chladni rig | Soundhole Audacity SOP exists; no general FRF lab pack | High | **LAB**, **MEAS** |
| P35–P36 | Historical ear method; acoustic spec philosophy | Philosophy scattered in LUTHERIE_MATH / handoffs | Medium | **KB**, **DOC** |
| P37–P38 | Spectrum interpretation; Mac tooling | Partial client spectrum UI | Medium | **KB**, **LAB** |

---

## B. Already represented (keep; link from lecture notes)

| Capability | Paths (representative) | Lecture link |
|------------|------------------------|--------------|
| Helmholtz / A0 design | `docs/LUTHERIE_MATH.md`, `docs/calculators/acoustics/soundhole_calculator_user_guide.md`, `soundhole_*` calculators | P04 air target neighborhood |
| Plate / coupled oscillators / γ / Chladni→box | `services/api/app/calculators/plate_design/*` | P01, P12, P19–P20 |
| Voicing stages & style targets | `voicing_history_calc.py`, `voicing_router.py` | P12–P13; **reconcile** with P04 triad |
| Wolf metrics ingest / advisor | `analyzer/design_advisor.py`, viewer-pack / RMOS acoustics | P03 — extend with scale-tone map |
| Nut & saddle compensation | `nut_compensation_*`, `saddle_compensation_*`, bridge theory docs | P25–P26 |
| Bracing geometry (X/fan/ladder/back) | `bracing_calc.py`, `instrument_geometry/bracing/*`, Art Studio | P17 — not falcate |
| Materials radiation ratio (Schelleng) | `materials/schemas.py` `radiation_ratio` | P21 — keep vocab distinct from modal SRC confusion |
| TapTone bundle ingest | `rmos/acoustics/*`, client acoustics utils | P33 modern path |
| Analyzer boundary | `docs/ANALYZER_BOUNDARY_SPEC.md` | Measurement vs interpretation law |

---

## C. Missing — recommended work packets (knowledge-first)

### C1. Monopole mobility packet (Critical) — P09–P11
- **DOC:** Define mobility vs monopole *frequency* in `docs/calculators/acoustics/`.
- **MEAS:** Tap Tone Pi stage fields: `mobility_driving_point`, bridge on/off, force/response units.
- **EMP:** Target bands by body style (corpus), not a fake closed-form “mobility calculator” from wood species alone.
- **LAB:** Guided: measure → compare → brace-height reduction decision (H1).
- **NO-CALC:** Do not ship `mobility = 1/sqrt(k*m)` as a design oracle without measured \(k,m\).

### C2. Mid-scale target & wolf-avoidance packet (High) — P03–P05, P35
- **RULE:** “Main resonances prefer midpoints between scale tones.”
- **EMP:** Named profile `gore_mid_scale_triad_v1`: 100 / 180 / 226 with body-style variants and explicit taste disclaimer.
- **LAB:** Overlay peaks on scale-tone grid; show nearest-note distance.
- **DOC:** Distinguish this triad from existing Martin-reference mode lists in `design_advisor.py`.

### C3. Free-top prohibition & stage gates (High) — P12–P13
- **RULE:** UI warning when user sets “target note” on `braced_free_plate` as if finished.
- **KB:** Dedicated page (this pack’s §2.6 / §3.2).
- **LAB:** Design → close → trim sequence (notes §10).

### C4. Live-back methodology (High) — P14–P16, P32
- **KB + RULE:** Tone/peak-density vs volume trade.
- **EMP:** Peak-count / peak-density metric 300–1000 Hz from FRF archives.
- **LAB:** Decide live vs rigid; optional upper-back stiffen check.
- Wire narrative to existing 2-osc vs 3-osc code — do not duplicate physics engines.

### C5. FRF lab pack (High) — P33–P34, P01, P20
- **LAB:** Software-agnostic SOP (10 averages, 0–1 kHz focus, grass rejection) with Visual Analyzer appendix + Tap Tone Pi primary path.
- **MEAS:** Align stage taxonomy: `uncoupled_top`, `closed_box_no_bridge`, `closed_box_bridge`, `strung`.

### C6. Falcate / spectral dialect packet (High for completeness; larger build) — P17–P18
- Near term: **KB/DOC** only (X scooped vs symmetric mids) — no fake falcate calculator.
- Later: geometry + Art Studio pattern (separate sprint; Feature Parity rules apply).

### C7. Bridge install expectation model (Medium) — P06–P08
- **EMP:** Δf distributions pre/post bridge from corpus (seeded by ~10–12 Hz demo observation).
- **KB:** Putty/tape fallacy.
- **NO-CALC:** No “poster putty preview” feature.

### C8. Spectrum character heuristics (Medium) — P16, P37
- **KB/EMP:** Lattice vanilla; live-back peak enrichment; interpret “too much low-mode only.”
- Fits empirical knowledge layer / advisor copy — not a new endpoint.

---

## D. What should stay in the empirical knowledge layer (not new calculators)

These are high-value as **guided knowledge + corpus**, low-value as yet another formula endpoint:

1. Live vs non-live taste trade (P14–P15)  
2. X vs falcate midrange dialect (P17–P18)  
3. Free-top tuning prohibition narrative (P12)  
4. Priority stack: modes → mobility → intonation over secondary geometry (P10)  
5. Torrefaction glue/process caveat (P27)  
6. Playing-in timelines (P28)  
7. Historical Fleta pedagogy (P35)  
8. “Ideal is to your own taste” disclaimer on 100/180/226 (P04)  
9. Cross-dipole “usually leave alone” policy (P22)  
10. Putty ≠ bridge (P08)

---

## E. Tap Tone Pi vs Toolbox ownership

| Concern | Owner | Notes |
|---------|-------|-------|
| Spectrum capture, averaging, calibration, wolf metrics raw | **tap_tone_pi** | Boundary unchanged |
| Stage metadata (bridge on/off, hole plugged, mobility) | **tap_tone_pi** contract → Toolbox consumer | Extend viewer-pack / bundle manifest carefully |
| Scale-tone collision interpretation, voicing advice, brace edit suggestions | **Toolbox analyzer / guided workflows** | Advisory; fail soft |
| Design targets library (triad profiles) | **Toolbox** `plate_design` / `voicing_history` | Single consolidation home |
| Chladni hardware DIY | Docs only | Optional lab appendix |

---

## F. Proposed doc/code placement (when implementing)

| Artifact | Path |
|----------|------|
| This knowledge pack | `docs/calculators/acoustics/gore_shop_talk_20/` *(done)* |
| Lab SOPs (future) | `docs/calculators/acoustics/labs/` |
| Theory deep links | Extend `docs/LUTHERIE_MATH.md` with pointers — avoid duplicating full notes |
| Target profile constants | `plate_design/calibration.py` + `voicing_history_calc.py` (reconcile) |
| Guided UI | `packages/client/src/components/guided/workflows/` |
| Measurement archive semantics | client `utils/acoustics/` + governance C1 inventories |

---

## G. Implementation priority (technical, not calendar)

1. **Publish knowledge pack** (this PR) — unlocks shared vocabulary.  
2. **C2 scale-tone + triad profile** — small code surface, high methodology leverage.  
3. **C3 free-top stage warnings** — UX/docs.  
4. **C5 FRF lab SOP** — docs first; Tap Tone stage tags next.  
5. **C1 mobility** — requires measurement contract work; do not fake in Toolbox alone.  
6. **C4 live-back methodology** — narrative on existing oscillators + EMP peak-density.  
7. **C6 falcate** — geometry sprint only after KB acceptance.  

---

## H. Quick verdict

Shop Talk #20’s durable value for the Acoustics environment is **methodology and priority**: mid-scale modal placement, closed-box voicing, mobility as a first-class goal, live-back trade-offs, and aggressive skepticism toward free-top pitch tuning and secondary metrics.

The Toolbox already has substantial **physics and ingest**. It lacks a **curriculum-shaped empirical layer** that turns those capabilities into Gore-consistent guided practice. This pack is that layer’s first source document.
