# Gaps Not Recorded — Holmberg Gore modeling spreadsheets

**Status vocabulary:** `Open` (unresolved) · `Confirmed` (issue verified, still unresolved) · `Closed` (resolved) · `Informational` (won't-fix / trust note).  
**Canonical mobility blocker:** [`../CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`](../CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md) (**G-R01** / **G-M09**) — G-HM04 inherits it.

| ID | Gap | Severity | Status | Why it matters |
|----|-----|----------|--------|----------------|
| **G-HM01** | Public Google Sheet URLs + starter workbooks | Medium | **Closed** | Five Get-started guitars + Wood Properties inventoried; hashes in WORKBOOK_INVENTORY |
| **G-HM02** | Wood Properties schema not ingested | Medium | **Closed** | WORKBOOK_INVENTORY §4 (306 spp, role sheets, 27 named ranges) |
| **G-HM03** | No independent build verification of starter dims | High | **Open** | Author warning (HM02) |
| **G-HM04** | Mobility unit profile vs book Y&gt;14 / in-sheet s/kg·e-3 | Critical | **Open** | Badge/UI blocked — see **G-R01** canonical file |
| **G-HM05** | Exact Equ. implementations not re-derived from book | Medium | **Open** | Port fidelity |
| **G-HM06** | Brace shear/rotation incomplete; bridge-rotation calc failed | Medium | **Open** | Brace module experimental |
| **G-HM07** | Nylon measure-rig datasets empty (`#DIV/0!` on measure path) | Medium | **Confirmed** | Issue verified in tab audit; compensation path still unresolved |
| **G-HM08** | Taylor GA study citation [3] full ref | Low | **Open** | Factory variance claim |
| **G-HM09** | Onshape / Mottola-Sevy links not archived | Low | **Open** | Area workflow |
| **G-HM10** | Medium SS CF `summary` back mass = 150 g vs noCF ~230 g | Medium | **Confirmed** | Suspicious override / stale cell — do not treat as golden |
| **G-HM11** | Medium SS CF `int_error_total` = 6.84¢ &gt; author steel &lt;6¢ band | Medium | **Confirmed** | Do not ship those Δn/Δs as golden |
| **G-HM12** | `const` column A mislabels E_nylon / E_PVDF as “Density” | Low | **Informational** | Cosmetic; symbols correct — trust/UX issue |
| **G-HM13** | Wood Properties `Chassis` unfinished (author ToDo → Chassis 2) | Low | **Open** | Use Chassis 2 |
| **G-HM14** | `deflection` tab only on Medium SS falcate noCF; not in docs spine | Low | **Informational** | Undocumented extra |

## Closure log

| Gap ID | Status | Date | Evidence |
|--------|--------|------|----------|
| G-HM01 | Closed | 2026-08-04 | Full five-guitar set + Wood Properties |
| G-HM02 | Closed | 2026-08-04 | WORKBOOK_INVENTORY.md §4 |
| G-HM07 | Confirmed (not closed) | 2026-08-04 | Tab audit: `#DIV/0!` on all measure-rig paths |
| G-HM10–G-HM11 | Confirmed (not closed) | 2026-08-04 | Inventory + tab audit |
| G-HM03–G-HM06, G-HM08–G-HM09, G-HM12–G-HM14 | Open / Informational | — | — |

## Explicit non-gaps

- Module list and sheet spine match real workbooks (HM43)  
- Author experimental flags recorded (HM21, HM34)  
- Fit≠predict warning recorded (HM27)  
- In-sheet mobility unit string `s/kg e-3` recorded (HM44)
