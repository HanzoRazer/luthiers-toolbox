# MB Sound Extraction Playbook

Goal: turn ~60+ video (or web) listings into rows in  
`services/api/app/data_registry/system/materials/panel_acoustic/mb_sound_panels.json`  
without hand-screenshotting every sample as the primary workflow.

## Preferred order (least pain first)

| Priority | Method | When |
|----------|--------|------|
| 1 | **Catalog / data-sheet capture** (HTML, PDF, or vendor export) | You have listing pages or downloads with the same numbers as the video overlays |
| 2 | **ffmpeg keyframes → OCR → JSONL** | Data only appears as on-screen graphics in video |
| 3 | **Manual key-in from paused video** | OCR fails on a field; fill only those cells |

Manual “60 screenshots into a folder then type everything” is a last resort for a few hard frames, not the plan for the whole set.

**Numbering gap:** MB Sound **data cards** carry `000001`-style IDs; analysis **spectrum plots** often do not. Always capture the Parameters sidebar (`Sample name`) or use fingerprint/timeline rules in [`LINKAGE.md`](./LINKAGE.md).

## Directory layout

```text
docs/reference/mb-sound/
  EXTRACTION_PLAYBOOK.md          ← this file
  FIELD_GLOSSARY_ES_EN.md         ← Spanish UI → schema
  schema/panel.example.json       ← one filled example (synthetic placeholders)
  staging/
    videos/                       ← private local copies (gitignored)
    frames/<sample_id>/           ← ffmpeg output (gitignored by default)
    ocr/<sample_id>.txt           ← OCR dumps
    rows.jsonl                    ← one JSON object per panel (committed when clean)
```

Bulk media stays out of git. Commit `rows.jsonl` + merged `mb_sound_panels.json` when reviewed.

## Video → frames (batch)

From repo root, with videos named or listed by sample id:

```bash
# One video → scene-change frames (good for static data sheets in the cut)
python scripts/mb_sound_extract_frames.py \
  --video /path/to/sample.mp4 \
  --sample-id mb_sound_adirondack_001 \
  --mode scene

# Or fixed interval (e.g. every 2 s) if scene detect misses overlays
python scripts/mb_sound_extract_frames.py \
  --video /path/to/sample.mp4 \
  --sample-id mb_sound_adirondack_001 \
  --mode interval --interval-sec 2
```

Frames land in `docs/reference/mb-sound/staging/frames/<sample_id>/`.

## Frames → text

If `tesseract` is installed (Spanish + English packs recommended):

```bash
python scripts/mb_sound_ocr_frames.py \
  --sample-id mb_sound_adirondack_001 \
  --lang spa+eng
```

Otherwise: open the 2–5 frames that show the data card, type into `staging/rows.jsonl` using the schema below.

## Merge into corpus

```bash
python scripts/mb_sound_merge_rows.py \
  --rows docs/reference/mb-sound/staging/rows.jsonl \
  --out services/api/app/data_registry/system/materials/panel_acoustic/mb_sound_panels.json
```

Validate required numeric fields and species mapping:

```bash
python scripts/mb_sound_validate_corpus.py
```

## Target fields (minimum for plate-math proofs)

Reuse **TonewoodEntry** names for overlapping quantities ([`NAMESPACE.md`](./NAMESPACE.md)):

| Schema field | Why |
|--------------|-----|
| `density_kg_m3` | ρ |
| `modulus_of_elasticity_gpa`, `E_C_gpa` | E∥ / E⊥ (same names as registry) |
| `panel.thickness_mm`, `panel.mass_g`, optional L×W | Panel geometry + density check |
| `panel.modes[].frequency_hz` + labels | Free-plate / vendor FR peaks |
| `species_id`, `record_kind: "measured_panel"` | Join + discrimination |
| `provenance.*` | Traceability |

Optional: `panel.src_vendor`, `panel.q`, `panel.cutting_year`, `panel.moisture_content_pct`, `panel.role`.  
Do **not** invent `E_parallel_*` / `E_perpendicular_*`.

## Validation uses (after ≥ a few real rows)

1. Compare vendor `E∥`, `E⊥`, `ρ` to `MaterialPreset` ranges in `plate_design/calibration.py`.  
2. Recompute \(c=\sqrt{E/\rho}\), \(R_\mathrm{anis}=E_L/E_C\), SRC-style \(\sqrt{E/\rho^3}\) and compare to any vendor index.  
3. If modes + geometry exist: run forward frequency / inverse thickness and record residual — **do not** “fix” vendor numbers when residuals are large; file a gap.

## Spanish / translation caution

Many cards will be Spanish. Map labels via [`FIELD_GLOSSARY_ES_EN.md`](./FIELD_GLOSSARY_ES_EN.md). If a translation of a **lecture** mentions MB Sound but does not show numbers, that goes in a knowledge pack — not this corpus.

## Legal / ethics

- Extract **numeric metadata** for research/validation inside this project.  
- Do not commit copyrighted full videos or wholesale audio libraries.  
- Record `source_url` / local path hash so a human can re-open the listing.
