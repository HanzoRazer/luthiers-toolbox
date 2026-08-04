# Lutherie Math — Unfinished §§ / Implementations  
## Annotated Developer Handoff (Executive Summary)

**Date:** 2026-08-04  
**Status:** DEV-READY orientation — knowledge layer closed on PR #243; math taxonomy evolution continues here  
**Location:** `docs/handoffs/` (active index: [`CURRENT_ACTIVE.md`](./CURRENT_ACTIVE.md))  
**Canonical hub:** [`docs/LUTHERIE_MATH.md`](../LUTHERIE_MATH.md)  
**Related:** Appendix B (measurement → solvers); acoustics packs under `docs/calculators/acoustics/` (inputs/dialect only)  
**Audience:** Engineers extending calculators / lab UI — not a lecture harvest checklist  
**On `main`:** yes (merge commit `5a885f31` / PR #243). If missing locally: `git checkout main && git pull origin main`.

---

## How to read this document

| Marker | Meaning |
|--------|---------|
| **DECISION** | Locked architecture — do not fork |
| **ANNOTATION** | Why it matters / trap for implementers |
| **GAP** | Work still owed |
| **STALE-DOC** | Math file text lags code (fix docs, don’t rebuild) |
| **BUILT** | Treat as canonical — call it, don’t recreate |

---

## Executive summary

**PR #243 finished the knowledge-pack cohort.** The next evolution of this instrument-building taxonomy is **inside `LUTHERIE_MATH.md`**, not more parallel spreadsheet engines.

| Layer | State |
|-------|--------|
| Acoustics knowledge packs (Gore / Nicoletti / Holmberg / MB / shop) | **Cohort floor held** — searchable, lane-filed, CBSP21 covered |
| Canonical equations + product path | **`LUTHERIE_MATH.md` → named `services/api/app/calculators/*`** |
| MB / TPC panel data + Holmberg Sheets | **Inputs / reference maps only** (Appendix B) |
| Unfinished math | **This handoff** — missing §§ text, missing modules, product coupling |

**DECISION — No independent product runtimes.** Do not ship Holmberg Sheets / `freq_db` or a vendor TPC UI as a **parallel calculator stack**. Reference models may later be re-expressed for parity **only** through `LUTHERIE_MATH.md` ownership + named modules. Missing capability → add/extend a § there, then implement beside the named module.

**ANNOTATION:** Book scans (Gore / Nicoletti) were scoped for the LLM layer. For engineering, extract equations **into** `LUTHERIE_MATH.md` §§. Lab values from instruments built this way calibrate and validate — they do not replace unfinished §§.

---

## 1. What is already finished (do not rebuild)

Call these; wire measured inputs into them.

| § | Topic | Implementation |
|---|--------|----------------|
| §1 | Fret positions | `instrument_geometry/neck/fret_math.py` |
| §3 | Saddle slant | **BUILT** in `acoustic_bridge_calc.py → compute_saddle_slant_angle()` — see STALE-DOC below |
| §4–§11 | Helmholtz / ports / volume proxy / inverse hole / ring / placement | `soundhole_calc.py` (+ `acoustic_body_volume.py`) |
| §12–§13 | Orthotropic plate \(f\) + inverse thickness | `plate_design/thickness_calculator.py`, `inverse_solver.py` |
| §19–adjacent | String tension / saddle force | tension / `saddle_force_calc` routers |
| §21 | Kerfing | **BUILT** `kerfing_calc.py` — see STALE-DOC |
| §23–§24 | Side port / two-cavity | `soundhole_calc.py` |
| §43–§44 | Dome radius / radius pairs | `tools/backRadiusCalculator.js` (+ §43–44 text) |
| Related | Brace prescription (not full \(D(x,y)\)) | `plate_design/brace_prescription.py` |
| Related | 2-oscillator couple | `plate_design/coupled_2osc.py` (not Holmberg 4-DOF parity) |

**DOC SYNC (§3 / §21):** Implementation lines updated to `acoustic_bridge_calc.py` and built `kerfing_calc.py` (2026-08-04 review remediation). Do not create a second slant API.

---

## 2. Unfinished inventory (priority stacks)

Three stacks. Do not flatten into one mega-sprint.

### Stack A — Geometry ↔ acoustics product loop (highest product leverage)

Closes Appendix A: outline editor as cabinet, acoustic stack as port calculator.

| ID | Status | Planned / owed | Blocks |
|----|--------|----------------|--------|
| **§37** | **GAP** — reserved, no full § | Outline (polygon/Bézier) → enclosed air \(V\) | Cabinet UX; can’t use drawn outline for \(f_H\) |
| **§38** | **GAP** — reserved, no full § | Body-style → depth law \(z(x,y)\) / section stack | §37 needs a depth model |
| **App. A coupling** | **GAP** | Outline → \(V\) → §11 `solve_for_diameter_mm` → canvas hole | Today \(V\) still from dimensional presets (§8) |
| **§16** | Formula present; **module missing** | `calculators/body_geometry_calc.py` (sagitta / C-bout) | Parametric waist/bout geometry helpers |

> **ANNOTATION:** §8 / `volume_from_dimensions` remain the **proxy** until §37–§38 ship. Do not invent outline→V outside this file.

### Stack B — Design-problem synthesis (§39–§42)

Forward analysis (§1–§25) is largely written; Part II turns that into *design* (mode shape → radiation → brace changes).

| § | Topic | Planned implementation | Depends on |
|---|--------|------------------------|------------|
| **§39** | Modal area \(A_n\) | `tap_tone_pi/analysis/modal_area.py` (external / research) | Chladni / mode-shape capture |
| **§40** | Brace field \(D(x,y)\) | `plate_design/stiffness_field.py` | §12 plate \(D\); not the same as `brace_prescription.py` |
| **§41** | Radiation power \(P_\mathrm{rad}\) | `plate_design/radiation_power.py` | §39 \(A_n\), \(\sigma_n(ka)\) |
| **§42** | Brace optimization loop | `plate_design/brace_optimizer.py` | **§39–§41** |

> **ANNOTATION:** `brace_prescription.py` is a **style→spec** helper. It is **not** §40. Shipping prescription UI does not close \(D(x,y)\) or \(P_\mathrm{rad}\).

### Stack C — Named modules still missing (shop geometry)

| § | Topic | Planned implementation | Notes |
|---|--------|------------------------|-------|
| **§25** | Neck angle | `calculators/neck_angle_calc.py` | GEOMETRY-001; formula in math file |
| **§14–§15** | Archtop arch stiffness / \(\Delta V\) | No dedicated module named | Text complete; fold into archtop path / §43–§44 — don’t fork flat-top plate API |
| **§17–§18** | Nut slot / setup cascade | No dedicated module named | Construction backlog; may live near setup/neck tools |
| **§20** | Acoustic impedance | Formula in math file | Thin surface; confirm before new file |
| **§22** | FB extension mass loading | Formula in math file | Geometry + mass; soundhole conflict narrative |

### Stack D — Documented FoM / parity gaps (not full §§ yet)

| Gap | Blocks | Disposition |
|-----|--------|-------------|
| **Q / damping §** | Damping as first-class solver | Appendix B: FoM only today — add numbered § before badges |
| **Mobility unit profile** (G-R01 / G-M09) | “Exceptional Y” UI | Carrico / SI lock — **outside** unfinished §§ list but blocks badges. **Dev order:** [`G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md`](./G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md) (separate PRs A–D) |
| **4-DOF closed-box FRF** | Holmberg `model` parity | Evolve `coupled_2osc` + lab FRF against §7 — **not** Sheets re-host |
| **TPC \(E_C\)** | Full orthotropic §12 from MB cards | Intake flag or second measure — Appendix B.3 |
| **§44 wood tiers** | Qualitative cheap/mid/premium | Bind to measured \(E_L\)/ρ/damping when data exists |

---

## 3. Recommended work order (technical, not calendar)

```text
0. Doc hygiene: fix STALE-DOC §3 and §21 Implementation lines
1. Stack A: write §37 + §38 → body_geometry / outline→V → App. A wire to §11
2. Stack C (parallel-safe): neck_angle_calc (§25); body_geometry_calc sagitta (§16)
3. Stack B: §39 hardware/research → stiffness_field (§40) → radiation_power (§41) → optimizer (§42)
4. Q/damping § + mobility unit profile before any “exceptional” badges
   (mobility: execute [`G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md`](./G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md) PRs A–D)
5. 4-DOF product FRF only after §7 contract clear — never clone Holmberg freq_db
```

**DECISION — Measurement path stays Appendix B:**

```text
MB/TPC or shop tap row
  → LUTHERIE_MATH §12 / §13 (plate) · §4–§11 (air when V known)
  → plate_design/* · soundhole_calc.py
```

---

## 4. Annotated gap cards (implementer detail)

### GAP-A1 — §37 Outline → \(V\)

**Owed:** Derivation + algorithm for closed outline × depth law → Helmholtz \(V\) (or defined effective \(V\)).  
**Not owed:** Replacing §11 inverse solver (already built).  
**ANNOTATION:** This is the missing hinge for “speaker cabinet designer” product promise.

### GAP-A2 — §38 Depth profile

**Owed:** Map body style → \(z(x,y)\) or section stack (endblock depths, taper, arch).  
**ANNOTATION:** Without §38, §37 collapses to a constant-depth lie.

### GAP-A3 — §16 `body_geometry_calc.py`

**Owed:** Sagitta / C-bout radius helpers as named in §16.  
**VERIFY:** Unit tests on waist/bout arc radius from \(w_1, w_2,\) setback.

### GAP-B1 — §39 \(A_n\)

**Owed:** Modal area from mode-shape measurement; external tap_tone path noted in math file.  
**ANNOTATION:** Frequency-only plate labs cannot close radiation-first brace design.

### GAP-B2 — §40 `stiffness_field.py`

**Owed:** \(D_\mathrm{total}(x,y) = D_\mathrm{plate} + \sum D_\mathrm{brace},k\).  
**ANNOTATION:** Distinct from Holmberg experimental \(K_t\)/\(K_b\) sheet and from `prescribe_bracing()`.

### GAP-B3 — §41 / §42

**Owed:** \(P_\mathrm{rad}\) from \(A_n, v_n, \sigma_n\); then closed-loop brace changes.  
**Depends:** Do not start §42 optimizer without §39–§41.

### GAP-C1 — §25 `neck_angle_calc.py`

**Owed:** Module matching §25 geometric derivation (GEOMETRY-001).  
**ANNOTATION:** Setup/neck UX likely consumer; keep formula ownership in math file.

### GAP-D1 — Q / damping §

**Owed:** Numbered section + Implementation path before productizing sustain/Q targets.  
**ANNOTATION:** MB Q columns are FoMs, not SI mobility.

---

## 5. Explicit non-goals

| Non-goal | Why |
|----------|-----|
| Ship Holmberg Sheets / `freq_db` as an independent product runtime | Forbidden (Appendix B); parity only via LUTHERIE_MATH §§ |
| New “TPC calculator” bypassing `LUTHERIE_MATH` | Same |
| Import MB averages into `wood_species.json` as FPL | Wood data policy |
| Merge Gore / Nicoletti / Somogyi dialects into one UI without modes | Cohort governance |
| Ship mobility “exceptional” badges | G-R01 / G-M09 open |
| Treat PR #243 lecture packs as unfinished math | Packs are satellite; §§ are the taxonomy |

---

## 6. Pointers

| Resource | Path |
|----------|------|
| Math hub | [`docs/LUTHERIE_MATH.md`](../LUTHERIE_MATH.md) |
| Measurement → solvers | Same file, **Appendix B** |
| Knowledge cohort orientation | [`docs/calculators/acoustics/KNOWLEDGE_PACK_DEVELOPER_ORIENTATION.md`](../calculators/acoustics/KNOWLEDGE_PACK_DEVELOPER_ORIENTATION.md) |
| Physics lane index | [`docs/calculators/acoustics/PHYSICS_KNOWLEDGE_INDEX.md`](../calculators/acoustics/PHYSICS_KNOWLEDGE_INDEX.md) |
| MB panel labs | [`docs/calculators/acoustics/mb_sound_panel_laboratory_records/`](../calculators/acoustics/mb_sound_panel_laboratory_records/) |
| Holmberg sheets | [`docs/calculators/acoustics/holmberg_gore_modeling_spreadsheets/`](../calculators/acoustics/holmberg_gore_modeling_spreadsheets/) |
| Coverage gate | `python3 scripts/knowledge_packs/check_cohort_coverage.py` |
| G-R01 Carrico close (separate PRs) | [`G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md`](./G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md) |

---

## 7. One-page scoreboard

| Stack | Items | Code state |
|-------|-------|------------|
| **A — Cabinet loop** | §37, §38, App. A wire, §16 module | Missing |
| **B — Radiation design** | §39–§42 modules | Missing (prescription ≠ §40) |
| **C — Shop geometry** | §25 module; §14–15/17–18/20/22 as modules TBD | §25 missing; others formula-only |
| **D — FoM / parity** | Q §, mobility units, 4-DOF product, \(E_C\) intake | Open / blocked |
| **Hygiene** | §3, §21 Implementation lines | STALE-DOC |

**Bottom line for the next owner:** Extend **`LUTHERIE_MATH.md`**, then implement the named gaps — starting with **Stack A** if the product promise is outline↔port, or **Stack B** if the promise is radiation-first bracing. Do not open a third math stack.
