# Holmberg Gore sheets — calculation spine (physics workbook)

**Source pack:** this folder · **Lane:** physics  
**Author:** Gregory Holmberg implementing Gore/Gilet  
**Role:** Describes the **Holmberg workbook process spine** — not the project’s sole approved build workflow and not product acceptance criteria. Canonical math ownership: [`docs/LUTHERIE_MATH.md`](../../../LUTHERIE_MATH.md) Appendix B.  
**Rule:** Measure *your* wood. Presets are examples. Brace sheet experimental. Target-accuracy norms in the sheets (e.g. ~1 Hz) are **workbook culture**, not Toolbox ship gates.

---

## Spine

```text
0  Copy a starter workbook (steel falcate / OM X / classical falcate …)
1  body — outline area + cavity volume accounting
2  top_panel / back_panel — measure billet → thickness for chosen f
3  body (return) — blocks/linings/active areas
4  fretboard + neck — geometry templates
5  intonation + first…sixth — μ,k → Δn,Δs (solver)
6  model — fit 4-DOF to known guitar (or iterate cautiously)
7  Set air/top/back targets (between notes)
8  Adjust D, Kt, Kb, ms_added → hit targets
9  top_braces / back_braces — size to Kt/Kb + stress gate
10 Build → measure → refit model → revise next guitar
```

---

## Stage 0 — Choose preset

| Step | Action |
|------|--------|
| 0.1 | Pick closest dialect (Gore falcate, OM X, classical falcate ±CF) |
| 0.2 | File→Make a copy (or download .xlsx/.ods) |
| 0.3 | Read HM02: do not cut from defaults |

**Gate:** Workbook owned; metric units accepted.

---

## Stages 1–3 — Body & panels

| Step | Action |
|------|--------|
| 1.1 | Enter body L, lower bout, top area (HM08–HM09) |
| 2.1 | Square/flat panel; measure L W t mass + 3 tap frequencies (HM10) |
| 2.2 | Set vibrational stiffness \(f\) for your finish targets (HM11) |
| 2.3 | Take red `t_tp` / `t_bp`; check mass (HM14–HM16) |
| 3.1 | Enter blocks, linings, active/inactive areas → cavity V |

**Gate:** Thicknesses + cavity volume locked from *measured* panels.

---

## Stage 4 — Neck geometry

| Step | Action |
|------|--------|
| 4.1 | Scale, frets, nut, radii → fretboard sheet (HM17) |
| 4.2 | Neck depths / tumblehome → templates (HM18) |

**Gate:** Fret positions + neck sections available for CAD/carve.

---

## Stage 5 — Intonation

| Step | Action |
|------|--------|
| 5.1 | Common params: action, relief, string set, neck E if using parabola (HM21–HM22) |
| 5.2 | Per string: get μ, k — prefer measure-rig (HM19–HM20) |
| 5.3 | Choose action column (measure &gt; models) |
| 5.4 | Minimize `error_cents` via Δn, Δs (HM23–HM24) |
| 5.5 | Summarize all six on `intonation` sheet |

**Gate:** Nut/saddle compensations documented; cents band accepted.

---

## Stages 6–8 — Frequency model

| Step | Action |
|------|--------|
| 6.1 | Load areas/masses (factors or CAD); acknowledge HM27 |
| 7.1 | Choose air/top/back Target IDs between notes (HM28) |
| 8.1 | Iterate D, Kt, Kb, ms_added (HM29–HM30) |
| 8.2 | Prefer equal peaks / deep valleys; watch mobility (HM31 — no UI badge yet) |
| 8.3 | Record soundhole Ø + Kt + Kb (HM33) |

**Gate:** Targets within ~1 Hz total abs error if possible; ft &lt; fb.

---

## Stage 9 — Braces

| Step | Action |
|------|--------|
| 9.1 | Measure brace stock E (HM37) |
| 9.2 | Size major/minor at 50 mm station for Kt + stress (HM34–HM36) |
| 9.3 | Repeat for back → Kb (HM40) |
| 9.4 | Enter real bridge/brace masses back into model if needed |

**Gate:** Stress under chosen safety factor; Kt/Kb differences minimized.

---

## Stage 10 — Build loop

| Step | Action |
|------|--------|
| 10.1 | Build; measure finished FRF / mobility |
| 10.2 | Refit model factors |
| 10.3 | Decide next-guitar deltas (depth, hole, braces) per Gore sensitivity notes |

**Gate:** Next instrument starts from fitted, not virgin, model.
