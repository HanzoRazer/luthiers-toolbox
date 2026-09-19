# The working recipe — how to get a usable DXF out of a plan

**Written:** 2026-09-19
**Status:** method record. Describes what demonstrably works today; authorizes nothing.
**Companion order:** `DEV_ORDER_RESTORED_BASELINE_FALLBACK.md`

---

## 0. Read this first

There are at least three documents in this repository describing a "secret sauce" for the
vectorizer, and they disagree with each other. Two of them describe behaviour the code no
longer has. This document exists because the recipe is actually short, and every number in it
was measured on 2026-09-19 against plans in `My Drive/Guitar Plans`.

**The whole recipe is two rules:**

> **1. Extract permissively. Do not filter before you have a candidate field.**
> **2. Remove junk afterwards, never before.**

Everything else is parameters. The reason this needs writing down is that the production
default violates rule 1, has done since 2026-04-12, and the resulting output is between 27×
and 127× thinner than the same code produces with one flag changed.

---

## 1. The one flag that matters

`extract_blueprint_to_dxf(..., isolate_body=True|False)`.

| | `isolate_body=True` (REFINED, the live default) | `isolate_body=False` (RESTORED_BASELINE) |
|---|---|---|
| Contour retrieval | `cv2.RETR_TREE` | `cv2.RETR_LIST` |
| Hierarchy parent/child | yes | no |
| Border removal | yes, **before** grouping | no |
| Grouping + scoring | winning group only is exported | all contours exported |

Measured, same input, nothing else changed:

| Plan | REFINED | RESTORED_BASELINE | Ratio |
|---|---:|---:|---:|
| Cuatro Puertorriqueño | 3,437 | 437,469 | **127×** |
| 12-String Dreadnought #2 | 12,785 | 1,071,127 | **83.8×** |
| Gibson SG Custom | 16,762 | 462,053 | **27.6×** |
| Melody Maker (April benchmark) | 24,097 | 343,399 | 14.3× |

**Counts are not the point. What survives is.** On the cuatro, REFINED returns a page border
and one stray fragment — not the instrument. RESTORED_BASELINE returns the slotted peghead with
its inlay, the fretboard and frets, the scalloped waist, soundhole and rosette, the bridge, the
tail motif, the side elevation with neck profile, the fret-interval table and the title block.

On the 12-String, REFINED returns **an empty rectangle**.

**Why:** `RECOVERY_BASELINE.md` (2026-04-13) established the mechanism and it has not changed —

> *"If you destroy the candidate field early, no amount of scoring can recover the object."*

The scorer is fine. On the Melody Maker the identical scorer produces 0.086/REJECT against
0.690/REVIEW depending only on what it is given to score.

---

## 2. Step by step

### Step 1 — check the input is even loadable

`cv2.imread` returns `None` on a non-ASCII path on Windows and the pipeline reports
*"Could not load blueprint image for processing"*, which reads as a corrupt file. It is not.

```
cv2.imread  cuatro puertoriqueño.png  -> None
cv2.imread  byte-identical ASCII copy -> (6450, 3600, 3)
PIL.open    cuatro puertoriqueño.png  -> (3600, 6450) RGB    <- the file is fine
```

Until that is fixed (**D-15**), rename accented files before processing. This is not exotic —
it hits Spanish, French, Portuguese and Scandinavian instrument names.

### Step 2 — know what the size caps will do to you

```
max_raster_dim_px = 4000      max_megapixels = 12
max_pdf_dpi       = 200       max_upload_bytes = 20 MB
```

A 10785 × 7208 scan becomes 4000 × 2673 before extraction. That is production behaviour and
measurements taken at full resolution do not describe it. **Always measure through
`extract_blueprint_to_dxf`, never the `edge_to_dxf` CLI at native resolution.**

Note also that the CLI takes images, not PDFs — the lane renders the PDF first. Handing it a
PDF raises `ValueError: Failed to load image`, which is correct behaviour, not a defect.

### Step 3 — extract permissively

```python
extract_blueprint_to_dxf(
    source_path=str(src), output_path=str(dst),
    target_height_mm=<real height of the drawn content>,
    warnings=[], isolate_body=False,          # <- the whole recipe
)
```

Expect a large file. That is correct and documented:

> *"The 14x Entity Increase is NOT a Bug... This is exactly what the old system did. That's why
> it worked as a starter. DO NOT try to 'fix' or reduce this yet."*

### Step 4 — remove the sheet border, AFTER extraction

The plan's printed frame is ink, so it gets traced. It is removable with a purely geometric
rule and no guessing: **both endpoints within ~6 mm of the same bounding-box edge, and running
parallel to that edge.**

| Plan | Border segments | Share | Interior lost |
|---|---:|---:|---|
| Gibson SG Custom | 6,508 of 462,053 | 1.41% | none |
| Cuatro | 9,718 of 437,469 | 2.22% | none |

**Never do this before extraction.** The pipeline already has `_remove_page_borders_early()`,
and that function *is* the regression — it runs before grouping, so on a fragmented body it
removes the body along with the frame. That is the mechanism behind the page-border-only result.

### Step 5 — set the viewport, or the file opens blank

**D-12.** On ezdxf 1.4.2, `saveas()` overwrites `$EXTMIN`/`$EXTMAX` with the inverted `1e+20`
sentinel — *including in memory*. `set_document_bounds()` therefore cannot work, and **42 of 42**
March corpus files carry the sentinel with 0 carrying geometry extents. Every writer in the repo
is affected, not just `dxf_compat`.

```python
from ezdxf import zoom
zoom.extents(doc.modelspace())   # sets the active VPORT; this DOES survive the save
doc.saveas(path)
```

**Cost warning:** on a 1M-entity file the ezdxf round-trip to do this takes minutes — it is a
full parse and rewrite to set two header values. Batch it, or patch the header by streaming.

---

## 3. Parameters that actually matter

| Parameter | Value | Why |
|---|---|---|
| `isolate_body` | **`False`** | The entire difference between a usable starter and a page border |
| `target_height_mm` | real height of the drawn content | Scales the output; wrong here means wrong millimetres everywhere |
| border margin | 6 mm | Wide enough for a hand-drawn frame, narrow enough to miss interior geometry |
| parallel tolerance | 1 mm | Separates a frame run from a drawing line that happens to pass near the edge |
| `--gap-close` | **does nothing in `--raw`** | **D-14**: `raw_output` returns at `vectorizer_phase3.py:3378`, before `body_gap_close` is read at `:3430`; `_raw_extract` hardcodes `threshold=120`. Do not tune what is not wired |

---

## 4. Which extractor for which input

| Input | Use | Not |
|---|---|---|
| Blueprint / plan sheet | `vectorizer_phase3` (classified layers) or the permissive `edge_to_dxf` path | The REFINED default |
| Photograph of an instrument | `photo_vectorizer_v2` | Blueprint modes |
| Archival edge trace for manual tracing | `edge_to_dxf` as designed | Anything expecting a clean single contour |

`edge_to_dxf`'s own docstring is explicit — *"Creating reference DXFs from photos for manual
tracing"*, example input `Benedetto Front.jpg`, expected output *"10-50MB with 50,000-300,000+
LINE entities"*. **That docstring describes the pre-`f49ead1d` tool.** The code kept the
docstring and lost the behaviour, which is why the live default produces 12–17k entities while
claiming a design range of 50k–300k. Do not read its documentation as a description of what it
currently does.

The orchestrator states the domain boundary itself, at `blueprint_orchestrator.py:587`:

> `# Pixel edge extraction via multi-scale Canny - works for photos, not blueprints`

---

## 5. What this recipe does NOT give you

Stated plainly so nobody reads more into the output than is there.

- **Absolute scale is not established.** `mm_per_px × scale_factor` comes from a page-size
  assumption nothing records. Aspect ratio is trustworthy — a uniform scalar cannot distort it —
  absolute millimetres are not.
- **No classification.** The permissive path emits one `EDGES` layer. Layer separation requires
  `vectorizer_phase3`, and even there the layer *names* are unreliable (`F_HOLE` has been
  observed on a headstock, `BRACING` on a side elevation). Separation is real; the taxonomy is
  not.
- **Not CAM-ready.** Output is an edge field, not closed contours. Closing a body outline is a
  separate operation — see `vectorizer-sandbox/reports/extraction/carlos_jumbo_001/METHOD.md`
  for a worked case, including the traps (a connected-component search returns an unordered set;
  a mirror must be symmetry-tested before it is trusted).
- **Text is included.** Annotations, dimensions and title blocks are ink and will be traced.

---

## 6. Provenance of every number here

| Claim | How it was obtained |
|---|---|
| Ratios (127×, 83.8×, 27.6×) | `extract_blueprint_to_dxf` run twice per plan, 2026-09-19, `isolate_body` the only variable |
| Border shares (1.41%, 2.22%) | Geometric rule applied post-extraction, entity counts before and after |
| D-12, 42 of 42 | Header scan of the March corpus plus an ezdxf 1.4.2 probe |
| D-14 identical geometry | Two runs with and without the flag: 93,379,060 bytes and 853,947 segments both |
| D-15 | `cv2.imread` vs `PIL.open` on the same path, and on a byte-identical ASCII copy |
| Regression window | `git log --follow` on `edge_to_dxf.py`, bounded by `86c49526` and `f49ead1d` |
| Mechanism and the April benchmark | `docs/archive/2026/status/RECOVERY_BASELINE.md`, 2026-04-13 |

---

**Standing.** Method record, not an authorization. It describes how to obtain usable output from
the code as it exists today; it does not approve any change to the production default.
