# Crosswalk — Holmberg Gore spreadsheets → Toolbox

**Canonical math hub:** [`docs/LUTHERIE_MATH.md`](../../../LUTHERIE_MATH.md) **Appendix B**  
**Rule:** Holmberg Sheets / `.xlsx` are a **Gore-school reference wiring diagram + test vectors**. Product math stays in LUTHERIE_MATH sections and named implementations. **Do not** port the spreadsheet runtime as a second engine.

| IDs | Topic | Canonical home (LUTHERIE_MATH → code) | Related packs |
|-----|-------|----------------------------------------|---------------|
| HM01–HM04 | Workbook identity / license | Docs attribution only | Gore lecture packs |
| HM05 | Wood Properties companion | Comparison UX; not FPL import | `wood_species.json` policy |
| HM06–HM07 | UX + presets | Example profiles only | Gore falcate / OM dialects |
| HM08–HM09 | Body area/volume | §4–§8, §11 → `soundhole_calc.py` / `acoustic_body_volume.py` | Mottola/Sevy external |
| HM10–HM16 | Panel thickness from tap + \(f\) | **§12, §13** → `plate_design/thickness_calculator.py`, `inverse_solver.py` — feed with **MB/TPC or shop tap**, not sheet presets | MB pack; Nicoletti TPC |
| HM17–HM18 | Fretboard + neck | §1 → `fret_math.py`; neck geometry stack | — |
| HM19–HM25 | Nut/saddle compensation | §3 → enhance `nut_compensation_physics.py` | Schaefer SC; Gore P25–P26 |
| HM26–HM33 | 4-DOF FRF/SPL | §7 culture; evolve `coupled_2osc.py` / lab FRF — **not** `freq_db` re-host | Gore Packs 1–5 |
| HM31 | Exceptional Y | Blocked on **G-R01/G-M09** | Pack 3/5 mobility |
| HM32 | Full monopole mobility | Research flag only | — |
| HM34–HM40 | Brace → \(K_t\)/\(K_b\) | §40 → `brace_prescription.py` (Holmberg sizing = experimental reference) | Jacob IB |
| HM41–HM42 | Ecosystem / CAD | Architecture only | Nicoletti tools |
| HM49 | Tab evaluation | Documents sheet spine for Appendix B.2 map | — |

**Primary index:** [`../PHYSICS_KNOWLEDGE_INDEX.md`](../PHYSICS_KNOWLEDGE_INDEX.md)  
**Universal wiring:** [`../../../LUTHERIE_MATH.md`](../../../LUTHERIE_MATH.md) Appendix B

## NO-CALC

- No spreadsheet runtime or cloned `freq_db` as product core  
- No cut lists from starter preset dims  
- No species-average thickness/brace tables as production defaults (HM14, HM37)  
- No predictive FRF claim from CAD-only inputs (HM27)  
- No mobility “exceptional” badges until unit profile locked (HM31 / G-R01)  
- No shipping Holmberg brace formulas as “Gore canonical” without **experimental** flag (HM34)  
- No nylon \(E\) hardcode as truth — require measure-rig (HM20)  
- Do not merge Schaefer shop carve ramps with Δn/Δs into one UI without clear modes
