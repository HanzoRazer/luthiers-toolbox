# Gaps Not Recorded — Holmberg Gore modeling spreadsheets

**Status:** Documentation + V4 workbook inventory complete; equation cell-audit still open.

| ID | Gap | Severity | Status | Why it matters |
|----|-----|----------|--------|----------------|
| **G-HM01** | Public Google Sheet URLs + starter workbooks | Medium | **Closed** — all five docs Get-started guitars + Wood Properties inventoried (incl. Classical nylon falcate noCF V4). Hashes in WORKBOOK_INVENTORY. | Reproducible clone |
| **G-HM02** | Wood Properties schema not ingested | Medium | **Closed** — see WORKBOOK_INVENTORY §4 (306 spp, role sheets, 27 named ranges) | Species ranking companion |
| **G-HM03** | No independent build verification of starter dims | High | Open | Author warning (HM02) |
| **G-HM04** | Mobility unit profile vs book Y&gt;14 / in-sheet s/kg·e-3 | Critical | Open — tied to G-R01/G-M09 | Badge/UI blocked |
| **G-HM05** | Exact Equ. implementations not re-derived from book | Medium | Open | Port fidelity |
| **G-HM06** | Brace shear/rotation incomplete; bridge-rotation calc failed | Medium | Open | Brace module experimental |
| **G-HM07** | Nylon measure-rig datasets empty in published sheets | Medium | Open | Compensation path |
| **G-HM08** | Taylor GA study citation [3] full ref | Low | Open | Factory variance claim |
| **G-HM09** | Onshape / Mottola-Sevy links not archived | Low | Open | Area workflow |
| **G-HM10** | Medium SS CF `summary` back mass = 150 g vs noCF ~230 g | Medium | Open | Possible manual override / stale cell |
| **G-HM11** | Medium SS CF `int_error_total` = 6.84¢ &gt; author steel &lt;6¢ band | Medium | Open | Do not ship those Δn/Δs as golden |
| **G-HM12** | `const` column A mislabels E_nylon / E_PVDF as “Density” | Low | Open | Cosmetic; symbols correct |
| **G-HM13** | Wood Properties `Chassis` unfinished (author ToDo → Chassis 2) | Low | Open | Use Chassis 2 |
| **G-HM14** | `deflection` tab only on Medium SS falcate noCF; not in docs spine | Low | Open | Undocumented extra |

## Closure log

| Gap ID | Closed? | Date | Evidence |
|--------|---------|------|----------|
| G-HM02 | Yes | 2026-08-04 | WORKBOOK_INVENTORY.md §4 |
| G-HM01 | Yes | 2026-08-04 | Full five-guitar set + Wood Properties |
| G-HM07 | Confirmed | 2026-08-04 | Tab audit: `#DIV/0!` on all measure-rig paths |
| G-HM03–G-HM06, G-HM08–G-HM09 | No | — | — |
| G-HM10–G-HM14 | No | — | Inventory + tab audit |

## Explicit non-gaps

- Module list and sheet spine match real workbooks (HM43)  
- Author experimental flags recorded (HM21, HM34)  
- Fit≠predict warning recorded (HM27)  
- In-sheet mobility unit string `s/kg e-3` recorded (HM44)
