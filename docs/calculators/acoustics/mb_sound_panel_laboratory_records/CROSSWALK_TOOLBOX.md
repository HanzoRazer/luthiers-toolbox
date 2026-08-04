# Crosswalk — MB Sound panel lab records → Toolbox

**Canonical math hub:** [`docs/LUTHERIE_MATH.md`](../../../LUTHERIE_MATH.md) **Appendix B**  
**Rule:** MB/TPC rows are **measured inputs** to existing §12 / §13 / `plate_design/*` solvers. **Do not** recreate a TPC or Holmberg equation engine.

| Points | Toolbox surface | Notes / NO-CALC |
|--------|-----------------|-----------------|
| MB01, MB02, MB16 | Lab evidence UI | “Screenshot-derived” badge; no fake FFT download |
| MB03, MB04 | Plate metrology SOP | Dialect for capture; math still LUTHERIE_MATH |
| MB05, MB18, **MB29** | Plate intake → §12/§13 | Map L/W/t/ρ/\(E\)/\(f\) per Appendix B.1 → `plate_modal_frequency` / `solve_for_thickness` |
| MB06–MB09 | Specimen library | Cohort browse; not species defaults |
| MB10, MB11 | Data hygiene | Prefer complete 49-row aged book |
| MB12, MB14, MB25 | Import pipeline | Blank+flag; dual-store; honor Capture Audit |
| MB13 | Climate metadata | Leave null |
| MB15 | Stats service | Recompute aggregates |
| MB17 | Glossary | NO-CALC until C/W meaning confirmed |
| MB19, G-MB08 | Radiation fields | FoM display; §41 not yet built |
| MB20 | Pack linking | Kit study-set ≠ panel books |
| MB21 | `wood_species.json` | **NO-CALC** — not FPL/CIRAD replacement |
| MB22, MB23, G-MB07 | Marketing claims | **NO-CALC** treatment/aging effect sizes |
| MB26 | Holmberg pack | Reference wiring only — see LUTHERIE_MATH Appendix B.2 |
| MB28 | Tab evaluation | Schema checklist for intake |

## Standing NO-CALC (repeat)

- No parallel “MB calculator” or Holmberg Sheets runtime in product  
- No exceptional-mobility badges from Q / \(E\)  
- No cut lists from batch averages  
- No silent reconciliation of Summary vs Detailed mismatches
