# Gaps Not Recorded — Shop Talk #51 (Luther Academy Apps)

| ID | Gap | Severity |
|----|-----|----------|
| G-A01 | Stable URLs / version pins for all five Mallaloy tools on Luther Academy | High (bitrot) |
| G-A02 | Canonical Gore spreadsheet edition that apps claim to match | High |
| G-A03 | Book example list used for A12 “exhaustive” verification | Medium |
| G-A04 | Exact plate-thickness formula / coefficients (spoken only as “formula”) | High — use book, not invent |
| G-A05 | Spoken “533 Newton meters” vs N/m (or other) for \(k_\mathrm{eff}\) | **Blocker** for mobility→4DOF import |
| G-A06 | Carrico weight: 1.00 vs historical 1.02 kg — which jig/build ships which | Medium (ties Pack 3) |
| G-A07 | Deflection δ under 1 kg still conflicting Pack 3 (~27 mm) vs Pack 5 (~0.15 mm) — **not restated this stream** | **Blocker** (G-R01 / G-M09) |
| G-A08 | Altitude / air-property model tables inside app “environment” | High (G-R11) |
| G-A09 | Autofill / 4DOF snap / multi-target solver bug list + fix status | Medium (product) |
| G-A10 | Flexural rigidity calculator: brace library, CF laminate assumptions, compare metric | High — demo named only |
| G-A11 | Resonance reader → flexural rigidity forward path (mentioned as future) | Low |
| G-A12 | Pre-war Martin / vintage corpus measurements | Leave empty until measured |
| G-A13 | Full Luther Academy domain path for Resources modal tools | Medium |
| G-A14 | Tone-generator hardware assumptions (Spark USB / Bluetooth) as requirement vs optional | Low |
| G-A15 | Whether Toolbox should embed, deep-link, or stay independent of Academy apps | Product decision — not technical |

## Closure log

| Gap ID | Closed? | Date | Evidence |
|--------|---------|------|----------|
| *(none yet)* | — | — | — |

## Policy

- Do **not** invent jig geometry, δ thresholds, or plate-thickness coefficients from this livestream alone.  
- Do **not** treat on-camera beta failures as absence of the feature in the design.  
- Cross-close G-A07 with Pack 5 **G-R01** and Pack 3 **G-M09** when Carrico/Gore calibration exists.
