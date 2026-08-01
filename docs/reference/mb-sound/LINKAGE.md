# MB Sound video linkage — numbered cards vs unnumbered spectra

## The problem

In MB Sound batch videos (e.g. Adirondack complete-batch analysis), **two on-screen surfaces** appear:

| Surface | Numbered? | Typical content |
|---------|-----------|-----------------|
| **MB Sound data card** | Yes — e.g. `000001` under “TORREFIED ADIRONDACK” | Density, Stiffness, Resonance Frequency, Sustain (Q), Radiation coefficient |
| **Nicoletti / analysis software UI** | Sometimes — `Sample name` e.g. `ADT-C-01` in Parameters; **spectrum / impulse plots themselves are not stamped with an ID** | Geometry, mass, density, Young modulus, Q, radiation, signal stats, plots |

If you only screenshot a spectrum pane, you can lose which of the 22 tops it belongs to.

## Dual vendor IDs (store both)

For each panel row, keep:

| Field | Example | Role |
|-------|---------|------|
| `source.catalog_id` | `000001` / `000012` | MB Sound card number (zero-padded) |
| `source.analysis_sample_name` | `ADT-C-01` / `ADT-W-02` | Software “Sample name” (prefix may be `ADT-C-` or `ADT-W-`) |
| `specimen_id` | `mb-adt-000012` | Stable repo key from catalog id |

Do **not** assume catalog `000012` ≡ `ADT-C-12`. Observed W-series pairs: **000011 ↔ ADT-W-01**, **000012 ↔ ADT-W-02**, **000013 ↔ ADT-W-03**, **000014 ↔ ADT-W-04**, **000015 ↔ ADT-W-05**, **000016 ↔ ADT-W-06**, **000017 ↔ ADT-W-07**, **000018 ↔ ADT-W-08**, **000019 ↔ ADT-W-09**, **000020 ↔ ADT-W-10**, **000021 ↔ ADT-W-11**, **000022 ↔ ADT-W-12** (fingerprint: ρ/E/f/Q/radiation). Always confirm with evidence.

## How to attach unnumbered spectral frames

Use this order (stop at first success):

1. **Sidebar Sample name visible** in the same frame → join on `analysis_sample_name`.  
2. **Numeric fingerprint** against already-linked rows (tolerance):  
   - `density_kg_m3` ±0.05  
   - resonance Hz ±0.05  
   - `modulus_of_elasticity_gpa` ±0.05  
   - optional: `mass_g` ±0.5  
3. **Timeline adjacency** — spectrum segment immediately after a numbered data card in the same video; record `provenance.video_t_start_sec` / `video_t_end_sec` and `batch_sequence` (1…22).  
4. If none work → leave `spectrum_linkage: "unresolved"`; do **not** invent an ID.

## What not to do

- Do not invent a third ID namespace for “spectrum clip 7”.  
- Do not rename vendor `Stiffness (Gpa)` to a new schema key — map to `modulus_of_elasticity_gpa`.  
- Do not map vendor `Radiation coefficient` onto computed TonewoodEntry `radiation_ratio` without `indices_source: "vendor_stated"`; prefer `panel.src_vendor`.  
- Do not assume the single resonance peak is a specific Chladni (m,n) mode unless the video states it.

## Batch video reference (Adirondack)

- Title: *Adirondack - MB Sound - Sample and analysis of the complete batch*  
- Channel: Maderas Barber Official  
- URL: https://www.youtube.com/watch?v=Ovhx0BxcbtQ  
- Stated batch size: **22** Adirondack pieces  
- Software attribution (vendor): Giuliano Nicoletti (measurement software); blog collaboration on maderasbarber.com
