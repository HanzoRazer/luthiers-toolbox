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

## 1a. Measured at scale — all 24 Fender headstock pages

Four one-off plans are an anecdote. This is one document family, **24 pages**, all 2200 × 1700 px
so **no downscale fires** and resolution cannot confound the comparison. `isolate_body` is the
only variable.

| | Pages 01–12 | Pages 13–24 |
|---|---|---|
| Ratio min / median / max | 20.7× / 75.8× / 83.6× | 25.7× / 99.5× / 144.3× |
| Border share of baseline | 14.08% / 15.58% / 15.98% | 9.34% / 12.21% / 17.81% |

**The finding is not the ratio. It is this:**

> **13 of 24 plans return byte-identical REFINED output.**

Pages **01, 02, 03, 04, 07, 08, 09, 10, 11, 12, 13, 15, 19** all produce geometry hash
`f13dab6370b2ba8b` — 7,004 entities, 329.7 × 247.4 mm, identical in every one. Pages 17 and 18
share a second identical result. **24 sheets produce only 11 distinct geometries.**

Note that entity count alone would have understated this: pages 16, 17, 18 and 22 also return
7,004 entities but *different* geometry. The duplication is only visible by hashing the
coordinates, which is why this was checked that way rather than by counting.

Rendered, that shared output is **an empty rectangle**: the page frame and nothing else. The
baseline path on the same page (13) returns two Telecaster headstocks with tuner holes, the
dimensions *1.590 nut width* and *0.122 as drawn*, a 7.53° angle callout, and the label
*"Bonnie Raitt"* — 468,929 entities.

This is `BORDER_FALLBACK` at scale. The default is not producing a poor result on these pages; it
is producing **the same result regardless of what is drawn on them**, because the candidate field
is destroyed before scoring and only the frame survives. A system in that state cannot be
distinguished from one that ignores its input.

**Border-strip timing, measured across both batches.** Pages 01–12 used the `ezdxf` round-trip,
pages 13–24 the streaming implementation, on comparable files:

| | per page | 24-page total |
|---|---:|---:|
| `ezdxf` parse-and-rewrite | 1,177–1,434 s | ~4.5 h |
| `strip_border_streaming.py` | 144–295 s | ~40 min |

Roughly **6–8× faster**, same rule, same result. This is the difference between a bench tool and
a pipeline stage.

Per-page detail, pages 13–24:

```
page       refined   baseline   ratio      final  border%     extent mm
Page_13      7,004    468,929   67.0x    386,489   17.58%   317.9 x 235.5
Page_14     18,035    463,231   25.7x    381,761   17.59%   317.9 x 235.5
Page_15      7,004    480,839   68.7x    398,823   17.06%   317.9 x 235.5
Page_16      7,004    801,529  114.4x    715,239   10.77%   317.9 x 235.5
Page_17      7,004    708,712  101.2x    623,741   11.99%   317.9 x 235.5
Page_18      7,004    696,819   99.5x    611,730   12.21%   317.9 x 235.5
Page_19      7,004    462,225   66.0x    379,881   17.81%   317.9 x 235.5
Page_20      5,148    742,669  144.3x    657,299   11.50%   317.9 x 236.4
Page_21     12,952    651,639   50.3x    579,544   11.06%   317.9 x 239.6
Page_22      7,004    636,308   90.8x    550,112   13.55%   317.9 x 235.5
Page_23      6,108    766,846  125.5x    679,174   11.43%   318.0 x 235.5
Page_24      8,438    941,571  111.6x    853,667    9.34%   317.9 x 235.5
```

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

### Step 1a — copy your input somewhere else first

**`extract_blueprint_to_dxf` overwrites its own input file when it downscales.**
`blueprint_extract.py:247`:

```python
if (final_w, final_h) != (original_w, original_h):
    cv2.imwrite(source_path, image)     # rewrites the SOURCE
```

In production the source is a temp render of an upload, so this is invisible — which is why it
has survived. Call it directly on a plan over the size cap and **that plan is replaced by a
4000 px version, in place, with no warning.** The docstring says *"Run edge-to-DXF conversion on
an image file"* and promises nothing about mutating it.

Verified the hard way on 2026-09-19: three source plans were silently downscaled in place
(7200 × 9600 → 3000 × 4000, and two 10 000 px scans → 4000 px). Recovered byte-for-byte from
other copies. **Always process a copy.** Filed as **D-16**.

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

### Step 3a — how to get restored output WITHOUT writing Python

`restored_baseline` is reachable over HTTP today. It is not new code and nothing needs building
— it only has to be asked for by name, because the production page never sends a `mode` field
(`hostinger/blueprint-reader.html:1078-1083` appends `file`, `target_height_mm`,
`min_contour_length_mm`, `close_gaps_mm` and `debug`, and nothing else), so
`blueprint_async_router.py:147` falls to its `refined` default on every upload ever made.

Route verified 2026-09-19: manifest prefix `/api` + router prefix `/blueprint` + `/vectorize/async`.

```bash
curl -X POST "http://localhost:8000/api/blueprint/vectorize/async" \
  -F "file=@plan.pdf" \
  -F "mode=restored_baseline" \
  -F "target_height_mm=500"
# -> {"job_id": "..."}   then poll /api/blueprint/vectorize/status/{job_id}
```

A PDF is fine here — the orchestrator renders it before extraction. That is the one place the
PDF path is handled for you.

### Step 3b — ingesting a PDF yourself

The `edge_to_dxf` CLI and `extract_blueprint_to_dxf` both take **images**, not PDFs; handing
either a PDF raises `ValueError: Failed to load image`, which is correct behaviour rather than a
defect. The render step lives one level up, in `blueprint_extract.render_pdf_page()`, capped at
`LIMITS.max_pdf_dpi` (200).

To do it by hand:

```python
import pymupdf
page = pymupdf.open("plan.pdf")[0]
page.get_pixmap(dpi=200).save("plan.png")          # 200 = the production cap
# then Step 1a (copy), Step 3 (isolate_body=False), Step 4 (strip), Step 5 (viewport)
```

Read the page size from the PDF rather than assuming one — `page.rect.width / 72 * 25.4` gives
millimetres. A Letter-size sheet carrying a scaled drawing will not yield real instrument
dimensions no matter what is done downstream, and that mistake has already been made in this
investigation.

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
