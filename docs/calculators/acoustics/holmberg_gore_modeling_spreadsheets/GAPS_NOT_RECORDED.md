# Gaps Not Recorded — Holmberg Gore modeling spreadsheets

**Status:** Documentation + V4 workbook inventory complete; equation cell-audit still open.

| ID | Gap | Severity | Status | Why it matters |
|----|-----|----------|--------|----------------|
| **G-HM01** | Public Google Sheet URLs + starter workbooks | Medium | **Closed** for user-supplied page set — Classical nylon CF V4, Medium SS falcate ±CF V4, OM SS X noCF **V3**, Wood Properties V1 (hashes in WORKBOOK_INVENTORY). Optional residual: docs-table classical falcate Yellow Poplar noCF if a separate file exists. | Reproducible clone |
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

## Closure log

| Gap ID | Closed? | Date | Evidence |
|--------|---------|------|----------|
| G-HM02 | Yes | 2026-08-04 | WORKBOOK_INVENTORY.md §4 |
| G-HM01 | Partial | 2026-08-04 | Three guitar V4 + hashes; OM X still missing |
| G-HM03–G-HM09 | No | — | — |
| G-HM10–G-HM11 | No | — | Found in V4 inventory |

## Explicit non-gaps

- Module list and sheet spine match real workbooks (HM43)  
- Author experimental flags recorded (HM21, HM34)  
- Fit≠predict warning recorded (HM27)  
- In-sheet mobility unit string `s/kg e-3` recorded (HM44)
