# Blueprint Vectorizer Provenance — Forensic Audit

**Date:** 2026-09-17
**Subject repos:** `luthiers-toolbox` @ `origin/main 22e67686` (all refs) · `vectorizer-sandbox` @ `origin/master e32e9da` (all branches + tags)
**Method:** read-only. Nothing executed — no vectorizer, no server, not even `--help`. Git, code reading, file stat, GitHub read API.
**Repos modified:** none. **Authorizes:** nothing.
**Rendered copy:** https://claude.ai/artifact/YYdrqgBtFDDCAK924CQvCK

**Evidence tags used throughout:**

| Tag | Meaning |
|---|---|
| VERIFIED | read in code, git, or on disk during this audit |
| DOC-CLAIM | only a document asserts it |
| REFUTED | the record contradicts it |
| UNRESOLVED | no evidence either way |

---

## 1. Verdict

The canonical blueprint vectorizer — the code the public Hostinger tool actually reaches — is a two-lane
system, and **neither lane descends from the 2026-03-06 SIMPLE work**. The March 6 lineage is real but sits
behind modes the public page has never sent. The claim binding Edge-to-DXF to the March 6 artifact was
written on 1 April as an untested sentence in a docstring; every later "confirmation" rests on it.

| ID | Finding | Status |
|---|---|---|
| F-01 | The Blueprint Reader's blueprint lane runs `EdgeToDXF.convert()` + REFINED cleanup; its photo lane runs `PhotoVectorizerV2`. The page sends no `mode`, so the server default decides. | VERIFIED |
| F-02 | `vectorizer_phase3` — holding both March 6 SIMPLE and its April successor `_raw_extract` — is reachable only via `mode=v2_raw` or `cam_ready_r2000`. The page has never sent either. | VERIFIED |
| F-03 | `edge_to_dxf.py` was born 2026-04-01, 26 days after the event, as a *photo* archival exporter. It cannot have produced the March 6 artifact. | REFUTES A DOC |
| F-04 | `photo_vectorizer_v2.py` was born 2026-03-09, three days after the event, for hobbyists working from a concept photo. Nothing links it to the artifact. | REFUTES A DOC |
| F-05 | The anchor artifact is genuine and dates to the evening of 6 March. No committed code in either repo, at any date, can write a file with its structure. | VERIFIED |
| F-06 | SIMPLE as committed on 6 March wrote an **empty** DXF: it labels every contour UNKNOWN and the export excluded UNKNOWN. | VERIFIED |
| F-07 | ~~No document, run log or report in either repo records a re-run within 5% of the anchor's 128,997 entities. The "recovery" recovered a mode, not the output.~~ | **OVERTURNED same day — see §12** |
| F-08 | Five governance documents describe the runtime backwards, naming `vectorizer_phase3` authoritative and Edge-to-DXF legacy. | VERIFIED |
| F-09 | The whole Edge-to-DXF attribution traces to one unevidenced docstring sentence in `dd6cb7e7` (1 Apr 21:52), still on main. | VERIFIED |
| F-10 | The public photo lane cannot succeed: the page tests for DXF fields the server never returns. | VERIFIED IN CODE |
| F-11 | The live blueprint lane calls neither `validate_scale_before_export` nor `dxf_compat`, both required by CLAUDE.md. | VERIFIED |
| F-12 | Several commit hashes cited by the recovery documents no longer exist; history was rewritten after those documents were written. | VERIFIED |

---

## 2. The platform as it exists

Public entry point: `hostinger/production-shop-hub.html` (Free Tools landing page). Its Blueprint Reader card
(`:386-388`) links to `hostinger/blueprint-reader.html`, which calls the Railway API at
`https://luthiers-toolbox-production.up.railway.app`. Hostinger is updated by hand via File Manager/FTP; no
workflow in `.github/workflows` references it. **Git shows intent, not what is on the server.**

Lane selection is by file extension plus a user-toggleable badge persisted in `localStorage`
(`:849-858`, `:914-923`). PDFs and unknown types → blueprint lane; `jpg/png/webp` → photo lane.

### 2.1 Blueprint lane (the canonical path) — VERIFIED

```
blueprint-reader.html:1078-1089  POST /api/blueprint/vectorize/async
      multipart: file, target_height_mm=500, min_contour_length_mm=50, close_gaps_mm=1.0, debug=false
      NO mode field; then polls /vectorize/status/{job_id}, 5 s x 120 (:1109-1115)
 -> blueprint_async_router.py:147   mode: str = Form("refined")  -> CleanupMode.REFINED (:175-178)
 -> :186 asyncio.create_task -> to_thread(BlueprintOrchestrator.process_file)
 -> blueprint_orchestrator.py:304   PDF -> extract_pdf_page, asks 300 DPI, capped at BLUEPRINT_MAX_PDF_DPI=200
 -> :688-704                        REFINED -> else-branch -> extract_blueprint_to_dxf(isolate_body=True)
 -> blueprint_extract.py:199-264    downscale if >4000 px / >12 MP; _ensure_edge_to_dxf_importable (:183-194)
                                    inserts services/photo-vectorizer at sys.path[0]
 -> edge_to_dxf.py:1575             EdgeToDXF.convert()
 -> blueprint_orchestrator.py:815   clean_blueprint_dxf(REFINED) -> blueprint_clean.py:538
 -> unified_dxf_cleaner.py:199-241  write_selected_chains -> final DXF, base64 in artifacts.dxf (:1415)
```

| Stage | Parameters actually in effect | Evidence |
|---|---|---|
| Edge detection | grayscale → Gaussian blur 3 → `Canny(50,150)`; morphological close **off** (`morph_close_kernel=0`) | `edge_to_dxf.py:1627-1637, 1581` |
| Contours | `isolate_body=True` → `RETR_TREE` + `CHAIN_APPROX_NONE`, early page-border removal, grouping area ratio 0.005–0.95 | `:1664-1689` |
| Simplification | **none** — no `approxPolyDP`; every pixel step becomes one LINE | `:1786` |
| Scale | `mm_per_px = 500 / image height px`; whole sheet forced to 500 mm tall; no instrument spec consulted | `:1649` |
| Intermediate DXF | R12, LINE only, layer `EDGES`, direct `ezdxf.new` | `:1553-1554, 1786, 1814` |
| Cleanup | 1.0 mm joins; score area ratio 0.005–0.99; drop chains <50 mm, all open chains, scores <0.20; 5-tier fallback | `blueprint_clean.py:489, 563-567, 641-678, 698-748` |
| Final DXF | `create_document(version="R12")`, LINE only, layers `contour_0 … contour_N` | `unified_dxf_cleaner.py:222-226` |

### 2.2 Photo lane — VERIFIED

```
blueprint-reader.html:1210-1229  POST /api/vectorizer/extract
      JSON: image_b64 (resized <=1600 px, JPEG q0.7), source_type='photo', export_svg, export_dxf
 -> photo_vectorizer_router.py:79-108, 307   sys.path insert -> services/photo-vectorizer
 -> photo_orchestrator.py:226-239            PhotoVectorizerV2().extract(...)
 -> photo_vectorizer_v2.py:3820, 3897+       12-stage pipeline:
      background removal AUTO -> Canny (auto sigma 0.33) OR Sobel>50 OR Laplacian>40 -> GatedAdaptiveCloser
      -> ContourAssembler RETR_TREE / CHAIN_APPROX_NONE -> approxPolyDP 0.3 mm
      -> R12 LINE, feature-named layers (BODY_OUTLINE...), EXTMIN/EXTMAX from geometry
```

### 2.3 Filter step — unreachable

`/api/blueprint/clean` exists and is mounted, but `showFilterNote` (`:946`) has had no caller since
`d5f9e6bf` (12 Apr) removed it, and the async result carries no `dxf_path`. If called, its SVG preview would
always be empty: the preview reads only LWPOLYLINE while the cleaner writes LINE (`clean_router.py:193`).

### 2.4 Mounting

`main.py:257-261` loops `load_all_routers()` into `include_router`: `app.routers.blueprint` at `/api`
(package adds `/blueprint`, includes `clean_router` at `/clean`), `blueprint_async_router` at `/api` with its
own `/blueprint` prefix, `photo_vectorizer_router` at `/api/vectorizer`. No duplicate or shadowing
registration serves these paths. Railway builds `docker/api/Dockerfile`, which copies both
`services/blueprint-import` and `services/photo-vectorizer` onto `PYTHONPATH` (`:66-67, 83`) — this is what
makes the `sys.path` inserts work in production. VERIFIED

### 2.5 How the public page's wiring changed — VERIFIED

| Date | Commit | Blueprint lane called | Note |
|---|---|---|---|
| 04-05 | `d722f432` | — | First standalone `blueprint-reader/index.html`, no API calls |
| 04-07 | `445e0aae` | — | Moves to `tools/blueprint-reader.html`; photo lane already on `/api/vectorizer/extract` |
| 04-07 | `1fcb04b8` → `71aad998` | `/api/blueprint/edge-to-dxf/convert` | Blueprint/photo routing added; missing `/api` prefix fixed 44 min later |
| 04-07 | `dcb7d217` | same | `/api/blueprint/clean` + static download added |
| 04-08 | `7affc790` | same | Moves to tracked `hostinger/`; commit says deploy "via Hostinger File Manager or FTP" |
| 04-12 | `d5f9e6bf` | **`/api/blueprint/vectorize/async`** | Endpoint switched, filter call dropped, timeout 180 s → 90 s, inside a commit titled "render best-effort artifacts even when ok=false". **Last change to the page** |
| 04-13 | `e2b4ad66` | (server) default `refined` | Direct commit to main, no PR. Body: "without changing default behavior" |

For ~15 h (12 Apr → 13 Apr) the page called an async endpoint that had no `mode` parameter at all.
`git log -S` confirms the page has never contained the string `v2_raw`.

---

## 3. Component dossiers

### 3.1 Edge-to-DXF — `services/photo-vectorizer/edge_to_dxf.py`

**Origin.** `55c30622`, 2026-04-01 01:08:52 −05:00, "feat(photo-vectorizer): add edge_to_dxf high-fidelity
exporter", 414 lines. No predecessor under any name in either repo (`git log --all -S'EdgeToDXF'` and
`-S'convert_enhanced'` both start here); nothing renamed into it; the March photo-vectorizer patches archive
has no trace. VERIFIED

**Stated intent.** Birth commit + docstring: "Converts image edges directly to DXF LINE entities for maximum
detail: 50,000-300,000+ LINE entities per image… Use cases: high-fidelity archival of guitar body outlines;
reference DXFs from photos for manual tracing; when contour-based extraction loses detail." Docstring dated
2026-04-01, example file *Benedetto Front.jpg*, expected output 10–50 MB. **A photo archival / hand-tracing
tool — not blueprints, not CAM.** VERIFIED

**At birth** neither `convert()` nor `convert_enhanced()` traced contours: both `np.lexsort`-ed edge pixels
row-major and drew LINEs between neighbours within 3.0 px. R12, layer `EDGES`, direct `ezdxf.new`. VERIFIED

**Evolution — VERIFIED from diffs**

| Date | Commit | Behavioural change |
|---|---|---|
| 04-01 | `55c30622` | Birth (above) |
| 04-01 | `3fc41c79` | Default DXF version R12 → R2010 |
| 04-02 | `8d7bbeea` | Silently reverted to R12 inside "Minor fixes across photo-vectorizer modules" |
| 04-09 | `3ce820c1` | **First real contour tracing:** `findContours(RETR_LIST, CHAIN_APPROX_NONE)` replaces the pixel sort in both functions |
| 04-09 | `38e609bd` | Per-stage timings |
| 04-12 | `9cc92ba9` | `isolate_body` → `RETR_TREE` + hierarchy filter, debug overlay. Documents cite this as `f49ead1d`, a hash that no longer exists |
| 04-13 | `ea83589f` | Early page-border removal + group scoring, +669 lines. **The logic the live lane runs today** |
| 04-13 | `014e720f` | Adds `extract_entities_simple` (adaptive 21/10, `CHAIN_APPROX_SIMPLE`, eps 0.001), docstring "Based on March 6, 2026 SIMPLE extraction mode". Only March 6 code ever copied here; used only by `layered_dual_pass` |
| 04-20 | `e9cdf13c` | `convert_enhanced` gains 7×7 `MORPH_CLOSE`, "the proven March 6 value". Cited in docs as `3db07c62`, which does not exist |
| 04-26 | `20f78236` | EasyOCR text masking, default on in `convert_enhanced` |
| 04-27 | `7656d5c9` | 5M entity cap, `ConversionStatus`, batch + PDF-page modes, +998 lines |
| 05-12 | `778394c7` | First caller passes `layer_name='CONTOURS'`; the module never defaults to it |
| 05-20 → 07-27 | `#28`, `aab69089`, `#232` | Grouping telemetry, CI fix, BR-037 (OCR crash → `DEGRADED`) |

**Public surface today** (2,914 lines): `EdgeToDXF(canny_low=50, canny_high=150, adjacency_threshold=3.0,
dxf_version="R12", layer_name="EDGES")` `:1548`; `convert()` `:1575`; `convert_enhanced(gap_close_size=7,
mask_text=True)` `:1926`; `convert_batch` `:2145`; `convert_separate_batch` `:2414`; CLI `:2776`.

**Callers on main.** The public blueprint lane via `blueprint_extract.py:251-264`; `photo_v2` →
`EdgeToDXF(layer_name='CONTOURS').convert_enhanced(mask_text=False)` (`orchestrator:608`); `photo_refined` →
`.convert(morph_close_kernel=0, max_entities=0)` (`:660`); `layered_dual_pass` → `extract_entities_simple`
(`:344, :360`); its own router `/api/blueprint/edge-to-dxf/{status,convert,enhanced}`; tests
`test_text_masking.py`, `test_vectorizer_grouping_telemetry.py`.

### 3.2 Photo Vectorizer V2 — `services/photo-vectorizer/photo_vectorizer_v2.py`

`0bb31bf8`, 2026-03-09 02:45:02 — "standalone photo-to-SVG/DXF extractor … for beginners/hobbyists who have a
concept photo", tested on *Smart Guitar_1.png*. **Three days after the anchor.** No reference anywhere in it
to SIMPLE, the cuatro, March 6 or phase3. At birth: `RETR_EXTERNAL` / `CHAIN_APPROX_SIMPLE`, per-feature
layers, R12 POLYLINE. Today a 12-stage pipeline serving the public photo lane. VERIFIED

### 3.3 Phase 3 — `services/blueprint-import/vectorizer_phase3.py`

The file that actually carries the March 6 lineage, and it is not on the public path.

| Function | Born | Algorithm | Reached by |
|---|---|---|---|
| `_simple_extraction` | `5b5a3a38` 03-06 17:01 | adaptive threshold (21,10) → `RETR_LIST`/`CHAIN_APPROX_SIMPLE` → min area 50 px → `approxPolyDP` eps 0.001×perimeter; everything classified UNKNOWN | SIMPLE mode; still present unchanged at `:3799` |
| `_raw_extract` | `33226f9b` 04-03 17:15 | `extract_dark_lines(threshold=120)` with an unconditional 2×2 close → `RETR_TREE`/`CHAIN_APPROX_NONE` → no area filter, no simplification → pixel coords, Y = H−py → `add_polyline(layer='CONTOURS', closed=True, version='R12')` | `v2_raw`, `cam_ready_r2000` |

**`_raw_extract` is not a descendant of SIMPLE.** Every parameter differs (fixed vs adaptive threshold, TREE
vs LIST, NONE vs SIMPLE, no area filter vs 50 px, no epsilon vs 0.001, pixels vs mm), and `_simple_extraction`
survives untouched beside it. Its commit claims to restore "March 2026 fidelity" and cites **no source** — no
file, session, parameters or predecessor. VERIFIED

### 3.4 Cleanup layer

`blueprint_orchestrator.py` + `blueprint_clean.py` born together in `c1987620`, 2026-04-10.
`CleanupMode.V2_RAW` and `PHOTO_V2` added 2026-05-12 in `778394c7` (same commit as the archaeology handoff).
The cleaner produces the `contour_N` layers and is the only part of the live lane writing through
`dxf_compat`. VERIFIED

### 3.5 vectorizer-sandbox

Created 2026-04-01 02:53 UTC — **25 days after the event** — five commits on 31 March, then nothing until
20 May. Its governance: "*Not* the Blueprint Reader MVP, *not* commercially ACTIVE"; not "a drop-in
replacement for `services/blueprint-import/` in production"; graduation requires "**new** code in
`luthiers-toolbox/services/` — not restore of relocated files". It never tracked `edge_to_dxf.py` as source;
`docs/audit-sources/` holds a gitignored mirror, now two changes stale. VERIFIED

The relocation pair is **LTB #27 + sandbox #2** (both 20 May). LTB #27's body is the one May document that
describes the live path correctly: "What does NOT change: Blueprint Reader MVP
(`/api/blueprint/vectorize/async`, `CleanupMode.REFINED`), `edge_to_dxf`, `vectorizer_phase3`."

---

## 4. The 6 March event

### 4.1 Timeline (−06:00) — VERIFIED

| Time | Event |
|---|---|
| 01:45 | `994c3453` pixel calibration + grid-zone classifier; 33-blueprint results; no SIMPLE content |
| 09:04 / 09:15 | `b41b3abd` PDF resize fix, then `977e81a1` appends "Session Log: March 6, 2026" to `VECTORIZER_UPGRADE_PLAN.md`. The log covers only the resize (14044×9934 → 4756×3364) and records "Phase 2: Vectorization ⚠️ 0% accuracy". It cites `bc1f8c2a`, which does not exist (real commit `b41b3abd`). **No SIMPLE, cuatro or DXF content** |
| 16:52 | `9d75d692` gitignores `Cuatro/simple_extract/`, `Cuatro/test_raw/`, `Cuatro/regenerated_v3/`, `Cuatro/*.zip`. **Folders named "simple" and "raw" already existed, outside git, nine minutes before SIMPLE was committed** |
| 17:01 | `5b5a3a38` adds SIMPLE. Body: "Tested on Cuatro blueprints: 500-600 contours vs ~60 with SMART mode" — contour count, not entity count |
| 18:25 | `4b443693` adds the Smart/Simple UI toggle. Its form field routes to Phase 2 `analyze_and_vectorize`, which has no "simple" branch and falls through to `_extract_full_image` (threshold 200, `RETR_EXTERNAL`, min area 500, layer GEOMETRY, no Y flip). **The toggle never reached `_simple_extraction`** |
| 18:25 → 23:55 | No further vectorizer commits; 22:50–23:55 are CAM/RMOS |
| ~22:44 | Anchor header `$TDCREATE` Julian 2461106.6977 ≈ 2026-03-07 04:44 → 6 Mar 22:44 local if the header is UTC (UNRESOLVED) |
| 23:08:07 → :13 | The ten `_simple.dxf` files are created on `G:\My Drive\El Cuatro`, ~one per second |
| 23:08:48.905 | All ten share one last-modified time, to the millisecond |
| 04-01 13:20 | Copied into `luthiers-toolbox/Guitar Plans/El Cuatro/` (creation 13:20:32–:37), keeping the 6 March mtime |
| 04-16 | An inventory document lists the same ten files in three further folders: `simple_extract/`, `Cuatro_DXF_Simple_Package/`, and beside `regenerated_v3/*_phase3.dxf` and `test_raw/` |

### 4.2 The anchor vs the candidate code paths

Anchor `cuatro_puertoriqueño_simple.dxf`, all 11 recorded fields match: **AC1009 (R12); 128,997 LINE; single
layer CONTOURS; bbox [50.4, −1684.0, 935.4, −20.3]; line lengths min 0.1 / median 0.3 / max 818.0 mm;
16,264,730 bytes**; SHA-256 `41e62ec0…`.

| Signature element | SIMPLE @ 5b5a3a38 | UI "simple" @ 4b443693 | `_raw_extract` @ 33226f9b | edge_to_dxf |
|---|---|---|---|---|
| R12, LINE entities | consistent | consistent | consistent | did not exist on 6 Mar; at birth layer EDGES, positive Y, lines a few px long |
| Single layer CONTOURS | **no** — UNKNOWN | **no** — GEOMETRY | consistent | — |
| All-negative Y | **no** — Y=(H−py)·mm_per_px | **no** — positive | **no** — Y=H−py ≥ 0 | — |
| Longest line 818 mm | possible | possible | **no** — NONE chains step ≤ √2 px | — |
| Non-empty / ~129k | **empty** (UNKNOWN excluded; capped at 10 if allowed) | non-empty | 1,150,754 (8.9×) | — |

**Inference — now VERIFIED (§12).** The anchor's profile — long simplified segments, CONTOURS layer,
negative Y — fits SIMPLE-style extraction written by a *different, untracked writer* using `y = −py × scale`
and no second simplification. Built and run the same day: it emits the file. Every element that excluded
SIMPLE (layer UNKNOWN, positive Y, empty output) belonged to `export_to_dxf`, never to the extractor.

### 4.3 Producer search — five bounded negatives

Covered: git history of both repos (all refs); `scripts/` in both archives; the plans tree in both locations;
all 140 scripts on `G:\My Drive` (none containing `import cv2`, `findContours`, `RETR_*`, `CHAIN_APPROX_*`,
`adaptiveThreshold`, `vectorizer_phase3`, or "cuatro"); every Markdown/text file across Downloads, Documents,
Desktop, `C:\tmp`, `G:\My Drive`. The folder holding the anchor contains only `.dxf` and `.pdf`. VERIFIED

### 4.4 Reproduction attempts — none succeeded

| When | What ran | Entities | vs 128,997 |
|---|---|---|---|
| 04-03 | `_raw_extract` on the cuatro PDF (commit body) | 1,150,754 | 8.9× |
| 04-16→21 | ENHANCED + gap-close 7 (V3.6 audit) | 204,125 | 1.6×; 21.8 MB vs 16.3 MB |
| 05-12 | MRP-1C sweep 72–300 DPI | 9,455 – 1,473,689 | 0.07× – 11× |
| 05-17 | `v2_raw` (secret-sauce doc) | 1,150,754 / 477,429 | 8.9× / 3.7× |
| 09-16 | REFINED, the live default (sandbox #98) | 2,022,289 | 15.7×; 308 MB |
| 09-16 | Ruler re-measuring the ten existing files | 10/10 exact | measurement, not reproduction |
| **09-17** | **`light_line.py`, 400 DPI, 0.1 mm/px literal** | **128,997** | **exact — see §12** |

Up to 09-16 a numeric sweep of both repos for 128,997 ±5% found nothing beyond the recorded metrics,
and the May documents' own status line read "Entity count matched | DEFERRED — behavior preservation >
parameter matching." **That is no longer the state: see §12.**

---

## 5. How the claims were made

### 5.1 Attribution chain

| Date | Source | Claim | Basis given |
|---|---|---|---|
| 04-01 21:52 | `dd6cb7e7` → `edge_to_dxf_router.py:7, :273` | "This is the technology that produced the excellent cuatro_puertoriqueno_simple.dxf (15.5MB, 129,000 LINE entities)" | **None.** Written 20 h after the module was created, 8 h after the files were copied into the tree. Still on main |
| 04-16→21 | V3.6 audit | Secret sauce = morphological gap closing borrowed from the photo-vectorizer; "the March 6 breakthrough refers to the 12-stage pipeline in `photo_vectorizer_v2.py`"; 7 px is "the March 6 proven value" | Cites three hashes that do not resolve |
| 04-20 | `e9cdf13c` | "reproduces March 6 16MB output" | `test_gap_close_fix.py` — compares **file size only**, passes above ratio 0.8 |
| 04-21 | Supersession dev order (never in git) | Sauce = `gap_close_size=7` in `vectorizer_phase2.py`, "ported to edge_to_dxf.py" | Narrative |
| 05-12 | MRP-1C `:59-67` | "System 3: Edge-to-DXF … **CONFIRMED March 6 Source** … This IS the system that produced the anchor artifact", with `convert_enhanced`, `CHAIN_APPROX_NONE`, layer CONTOURS | Cites two documents that repeat the docstring claim. Every element post-dates 6 March |
| 05-12 | Same document `:169, :297, :308-317` | `_raw_extract` is "CONFIRMED_V2_SOURCE"; edge_to_dxf `convert_enhanced` is "REJECTED_REGRESSION" | Visual inspection. **The `:59` claim was never retracted** |
| 05-17 | Secret-sauce routing doc | Records the parameters; lists the March 6 reference method as "**Unknown**" | Quietly drops the confirmation |
| 06-21 | System conflation audit | edge_to_dxf LEGACY, "not in auto pipeline; no tests"; phase3 AUTHORITATIVE | Contradicted by code: default extractor, two test modules |
| 07-20 | Sandbox tag `vectorizer-architecture-cv-001` | "March 6 breakthrough = the 12-stage pipeline in photo_vectorizer_v2.py … *Not* a Simple Method" | Tag points at a commit not on master; PV2 born 9 March |
| 09-06 | Sandbox PR #92 (VEC-LIGHTLINE-001) | Ties March 6 to `_simple_extraction`; standalone script NOT_FOUND; current code does not reproduce the counts | Git evidence — closest to the record |

### 5.2 Three different "secret sauces"

1. **April:** `cv2.MORPH_CLOSE` kernel 7, borrowed from the photo-vectorizer (V3.6 audit, `e9cdf13c`).
2. **April, off-git:** same kernel, sourced instead from `vectorizer_phase2.py` (supersession dev order).
3. **May:** threshold 120, `RETR_TREE`, `CHAIN_APPROX_NONE`, layer CONTOURS, R12 — plus
   `morph_close_kernel = 0`, closing switched *off*, "preserves text strokes" (routing doc).

(1) and (2) are REFUTED as March 6 values: on 6 March Phase 2's `gap_close_size` defaulted to 0 everywhere
including the UI, and neither SIMPLE path closes gaps at all. (3) describes real current behaviour, but the
closing figure belongs to `photo_refined`/edge_to_dxf, not `_raw_extract`; and its `RETR_TREE` is the same
flag the regression chain blames for fragmentation. Both can hold — different pipelines — but no document
says so.

### 5.3 Rewritten history

Cited hashes that no longer resolve: `f49ead1d`, `3db07c62`, `bc1f8c2a`, `86c49526`, `94d90243`, `9417fd9b`,
`f573c4f6`. Several have twins with identical author timestamp and subject (`9cc92ba9`, `e9cdf13c`), so the
content survives under new hashes — history was rewritten after those documents were written. "189 layers vs
1", the headline of Regression 3, is **not in the diff it is attributed to** (`e3fb4792`); it first appears in
the May documents. VERIFIED

---

## 6. Contradiction register

Two audits ran in parallel on 2026-09-17: the *finding aid* (luthiers-toolbox session) and *VEC-ANCHOR-001*
(vectorizer-sandbox session).

| # | Claim | Source | Adjudication |
|---|---|---|---|
| C-01 | "SIMPLE is the `--raw` path of vectorizer_phase3" | Finding aid | REFUTED — two functions a month apart, sharing no parameters |
| C-02 | Edge-to-DXF `convert_enhanced` produced the March 6 output | Finding aid; MRP-1C `:59-67` | REFUTED — module born 04-01; `CHAIN_APPROX_NONE` added 04-09; never defaults to CONTOURS |
| C-03 | Ten files "written in the same second" prove a batch script ran | Finding aid | PARTLY — creation times 23:08:07→:13, one per second; consistent with generation, not proof |
| C-04 | The identical-millisecond mtime means a bulk copy, weakening the March 6 date | VEC-ANCHOR-001 | REFUTED — Drive creation times date the files to 6 March; the April stamps belong to the *Guitar Plans* copy |
| C-05 | The behaviour was recovered and put back | Finding aid | ~~REFUTED~~ → **the output has now been reproduced; see §12.** The finding aid's *mechanism* stays refuted (it credited edge_to_dxf), but its claim that the behaviour was recoverable holds |
| C-06 | `977e81a1` is the same-day narrative record of the breakthrough | Finding aid | REFUTED — written 09:15, about PDF resizing, records 0% accuracy |
| C-07 | `4b443693` is "the UI exposure of the mode" | Finding aid | REFUTED — routes to Phase 2 full-image extraction |
| C-08 | "No API endpoint exposed SIMPLE" (Regression 1) | MRP-1C | HALF — a toggle existed; it reached different code |
| C-09 | 7 px close is "the proven March 6 value" | V3.6 audit, `e9cdf13c`, SPRINTS | REFUTED — Phase 2 defaulted to 0 on 6 March; SIMPLE never closes gaps |
| C-10 | "March 6 breakthrough = photo_vectorizer_v2's 12-stage pipeline" | V3.6 audit; sandbox CV-001 tag | REFUTED — PV2 born 9 March |
| C-11 | `_raw_extract` is the confirmed V2 source of the anchor | MRP-1C `:308`; June audit | REFUTED AS TO THE ANCHOR — positive Y, pixel-step lines, counts 3.7–8.9× high. A real recovery mode, not this file's source |
| C-12 | The producer script was never findable | VEC-ANCHOR-001 | UPHELD — five searches, five negatives |
| C-13 | The anchor's location was lost | VEC-ANCHOR-001 §0 premise | SELF-REFUTED — the path was recorded in the metrics file all along |

### 6.2 Governance documents vs code

| Document | Says | Code on main |
|---|---|---|
| `VECTORIZER_CANONICAL_PATHS.md` `:28,:51,:57,:90,:104,:119-127,:136-138` | Reader sends v2_raw/refined/baseline; async route in `vectorize_router.py`; `_raw_extract` writes via `dxf_compat`; phase3 is "primary blueprint extraction"; edge_to_dxf only as `convert_enhanced`; `source_type=auto`; `PhotoOrchestrator.process()`; dual-pass uses `extract_dual_pass()` | Only refined reachable; route is `blueprint_async_router.py:139`; extractor is `EdgeToDXF.convert` on raw `ezdxf.new`; `source_type` defaults to `photo`; method is `process_image()`; dual-pass built inline |
| `VECTORIZER_API_ROUTING_AND_SECRET_SAUCE.md` `:179,:258,:273-275` | `/api/photo-vectorizer/extract`; prefer v2_raw for PDFs; refined yields "classified layers" | Route is `/api/vectorizer/extract`; PDFs run refined; layers are `contour_N`, unclassified |
| `BLUEPRINT_READER_PROTECTION_RULES.md` `:22-23,:97-98` | Locked components include `dxf_compat` and `validate_scale_before_export`; `?mode=v2_raw` is a query parameter | Scale gate never called on this lane; extractor bypasses `dxf_compat`; `mode` is a form field, so a query value is silently ignored |
| `SYSTEM_CONFLATION_AUDIT_2026-06-21.md` `:37,:51,:100-102,:153` | edge_to_dxf LEGACY, "endpoint exists; not in auto pipeline; no tests"; phase3 AUTHORITATIVE for blueprints | edge_to_dxf is the default extractor with two test modules; phase3 runs only in opt-in modes |
| `MRP_1C…HANDOFF.md` `:59-67` vs `:169,:308` | Two different "CONFIRMED" sources in one document | Neither existed on 6 March |
| `BLUEPRINT_READER_MVP_BASELINE_2026-05-11.md` `:137-139` | Production frontend is the `HanzoRazer/blueprint-reader` repo; `hostinger/` is a "development copy" | That repo has one commit from 2025-12-03; the hub links to the tracked `hostinger/` page |

---

## 7. Defects and rule violations

| ID | Issue | Impact | Evidence |
|---|---|---|---|
| D-01 | Photo lane can never report success: page requires `dxf_base64`/`dxf_content`/`dxf_path`; server returns `artifacts.dxf.base64` and hardcodes `dxf_path: ""` | Every photo upload throws "missing DXF" in the browser | `blueprint-reader.html:1278`; `photo_vectorizer_router.py:258` (shim `4570a876`, 05-28) |
| D-02 | Filter step is dead code; its SVG preview would be empty anyway (reads LWPOLYLINE, cleaner writes LINE) | A documented capability is unreachable | `:946` uncalled since `d5f9e6bf`; `clean_router.py:193` |
| D-03 | `validate_scale_before_export` not called anywhere on the live lane | CLAUDE.md: "DO NOT ship a DXF export without running scale validation first" | grep across orchestrator, extract, clean, async router, edge_to_dxf, cleaner |
| ~~D-04~~ | ~~Edge-to-DXF writes DXFs with `ezdxf.new` directly at five sites~~ | ~~CLAUDE.md: "direct `ezdxf.new()` calls forbidden"~~ | ~~`edge_to_dxf.py:814, 1786, 2044, 2206, 2704`~~ |
| **D-04** *(corrected 09-18)* | **The R&D exemption is broader than its register and its review trigger has fired unactioned.** `DXF_COMPAT_EXEMPTIONS.md:68` authorizes **one** file — `ai_render_extractor.py` — under `EXCLUDED_R_AND_D_SANDBOX`. `check_dxf_compat.py:42-44` excludes the **whole directory**, silently covering **9 files / 15 calls**. The register's Review Trigger for that class is **"Promotion to Blueprint Reader"**, and `edge_to_dxf.py` *was* promoted — it is the live default lane (§2.5, §3.1). Its note reads "Photo Vectorizer is experimental and should not contaminate Blueprint Reader"; it is now the Blueprint Reader | The gate cannot fail on production code. `light_line_body_extractor.py` sits in the same blind spot — its writer was flipped R2010→R12 in a sweep and raised on every call for five months with no gate able to see it (§15) | `scripts/check_dxf_compat.py:42-44, 80-86`; `docs/architecture/DXF_COMPAT_EXEMPTIONS.md:64-70`. Gate run 09-18 prints all nine as `[INFO] … allowed per EXCLUDED_R_AND_D_SANDBOX`, exit 0 |
| D-05 | 5M-entity overflow returns `CAP_EXCEEDED` with no output path; caller reports success regardless | Silent empty result on large inputs | `edge_to_dxf.py:1852-1874`; `blueprint_extract.py:282` |
| D-06 | `convert_batch` writes `IMAGE_nn_*` layers | Breaks the `ContourCategory.value.upper()` convention | `edge_to_dxf.py:2145+` |
| D-07 | An unevidenced provenance claim is live in production source | Root of the conflation chain; still reads as authoritative | `edge_to_dxf_router.py:7, :273` |
| D-08 | Sandbox PRs #97/#98 state "DRAFT … No merge requested" yet were merged same-day with no review | Process record contradicts itself | GitHub, 09-16 |
| **D-09** | **`_remove_page_borders_early` assigns into the tuple `cv2.findContours` returns** — `TypeError: 'tuple' object does not support item assignment`. Fires only when a page border is detected | **The Fender Strat '62 plan cannot be processed at all.** Fails closed (`ok=False`, `stage=edge_extraction`, REJECT, no artifacts), so it announces rather than corrupts | `edge_to_dxf.py:395`, reached from `:1632`. Reproduced on cv2 **5.0.0 and 4.13.0**; pin is `opencv-python-headless>=4.8.0`, no upper bound (`services/api/requirements.txt:36`) |
| ~~**D-13** *(new 09-18)*~~ | ~~**Phase 3 certifies the sheet border as the body, on a second unrelated plan.** Same inverted-certification class as **D-10**, now shown to be general rather than sample-specific~~ | ~~filed as a new September finding~~ | ~~Run 09-18~~ |
| **D-13** *(corrected 09-19)* | **NOT a new defect — this is the `BORDER_FALLBACK` regression of `f49ead1d` (2026-04-12 15:42, "feat: hierarchy-based isolation"), unfixed and reproducing on a new plan.** On `Gibson-L0-IN.pdf` the classified run returns `BODY_OUTLINE` = **6 segments spanning 634.7 × 493.4 mm** — a rectangle — and reports `Body: 635x493mm`, `Scale validation PASSED (generic plausibility)`. `docs/archive/2026/status/RECOVERY_BASELINE.md` (2026-04-13) describes the mechanism exactly: *"hierarchy-based filtering removes all non-border contours, leaving only the page border as a candidate"* | The observation stands — the generic 200–700 mm window admits a sheet border, and the plan states its own lower bout (13¾ in = 349.25 mm) so the reported figure is out by 82%. What was wrong was the **attribution**: filed on 09-18 as a September discovery when it is a five-month-old diagnosed regression whose fix was specified on 2026-04-13, marked CRITICAL, and never shipped (`Ship as fallback \| PENDING`). Re-measured 09-19 with `isolate_body` as the only variable: SG Custom 16,762 → 462,053 entities (27.6×), 12-String 12,785 → 1,071,127 (83.8×), and the 12-String refined output is a page border and nothing else | Run 09-18, `--dpi 400 -t acoustic`; evidence `vectorizer-sandbox/reports/extraction/gibson_l00_002/`. Regression bounded by `86c49526` (2026-04-11 01:41, last good) and `f49ead1d`. Order: `docs/handoffs/DEV_ORDER_RESTORED_BASELINE_FALLBACK.md` |
| **D-14** *(new 09-18)* | **`--gap-close` is silently ignored in `--raw` mode, which also hardcodes its threshold.** `raw_output` returns at `vectorizer_phase3.py:3378`, **before** `body_gap_close` is read at `:3430`; `_raw_extract` calls `extract_dark_lines(image, threshold=120)` at `:2864` with no `gap_close` argument | The CLI advertises a flag that does nothing, and raw mode cannot be tuned for any document. `morph_close_kernel` is the documented routing control for text-dense sheets, so the one lever the routing guidance depends on is unreachable in the mode the owner ruled canonical (`--raw`, not `--simple`) | Two runs with and without the flag produced **identical geometry** — 93,379,060 bytes and 853,947 segments both, differing only in header timestamps |
| **D-16** *(new 09-19)* | **`extract_blueprint_to_dxf` silently overwrites its own input file.** `services/api/app/services/blueprint_extract.py:246-247` — when the raster exceeds the size caps it downscales and then writes the reduced image back over `source_path`: `if (final_w, final_h) != (original_w, original_h): cv2.imwrite(source_path, image)`. The docstring reads *"Run edge-to-DXF conversion on an image file"* and declares no mutation of the input | **Destroys the caller's original.** Invisible in production, because the orchestrator passes a temp render of an upload — which is why it has survived. Any other caller loses data: a 7200×9600 plan becomes 3000×4000 in place, with no warning and no backup. It also makes the operation non-idempotent, since a second run downscales the already-downscaled file | Reproduced 2026-09-19 against three plans in `My Drive/Guitar Plans`: `Gibson-SG-Custom.png` 7200×9600 → 3000×4000, `12 StringDreadnaught_2.jpg` 10764×7165 → 4000×2662, `12 String Dreadnaught_1.jpg` 10785×7208 → 4000×2673. All three recovered byte-for-byte (369,315 / 3,597,097 / 3,880,562 bytes) from `Downloads/luthiers-toolbox/Guitar Plans/`. Found only because the function was read while answering an unrelated question |
| **D-15** *(new 09-19)* | **`cv2.imread` fails on a non-ASCII path, and the product blames the user's file.** On Windows it returns `None` for `cuatro puertoriqueño.png`; the lane reports *"Could not load blueprint image for processing"*, which reads as corruption | **Any plan named in Spanish, French, Portuguese or a Scandinavian language cannot be processed**, and the error misattributes the fault to the customer's file. The cuatro puertorriqueño is the plan this entire audit rests on | `cv2.imread` non-ASCII → `None`; byte-identical ASCII copy → `(6450, 3600, 3)`; `PIL.open` on the same non-ASCII path → `(3600, 6450) RGB`, so the file is sound. Same bytes, 1,406,060 both. cv2 5.0.0. Renamed copy then processed in 1.2 s. Fix is `cv2.imdecode` on bytes rather than `imread` on a path |
| **D-12** *(new 09-18)* | **`set_document_bounds()` is a no-op on the installed ezdxf, and the audit that cleared it checked the call site rather than the output.** `services/blueprint-import/dxf_compat.py:185-200` assigns `$EXTMIN`/`$EXTMAX`; on **ezdxf 1.4.2** `saveas()` overwrites both with the inverted `1e+20` sentinel — *including in memory*, so the assignment cannot be observed after the save either. It is live-called at `vectorizer_phase3.py:2630` | Every Phase 3 DXF ships the blank-canvas extents CLAUDE.md forbids. **42 of 42** March corpus files carry the sentinel; **0** carry geometry extents. CLAUDE.md:212 cites this function as the correct mechanism, and `SURFACE_GROUNDING_2026-06-04.md:140-141` marks it "live-called (VERIFIED)" — a call-site check read as an output guarantee. `zoom.extents()` (VPORT) does survive the save and is the working alternative | Probe on ezdxf 1.4.2: fresh doc → assign → `saveas` → read back = sentinel. Corpus scan 09-18, 42/42 |
| **D-10** *(re-attributed 09-19)* | **On the cuatro, the default lane returns the neck and certifies it** `accept` at 0.745 confidence, while returning a substantially correct body outline on the Melody Maker and flagging it `review` at 0.475 | The confidence signal is inverted on this sample; a wrong result is presented as accepted. **Probable shared root cause with D-13: `f49ead1d`.** `RECOVERY_BASELINE.md` benchmarks the *same Melody Maker plan* at REFINED score **0.086 / REJECT** against RESTORED_BASELINE **0.690 / REVIEW** on an unchanged scorer, and concludes *"scoring works; the candidate field was the problem."* A scorer fed a corrupted candidate set produces exactly this inversion. **Not yet proven for the cuatro** — that requires running it through both paths, which has not been done | Live `process_file` runs, 09-17. Owner identified the contour in DWG TrueView. Re-attribution basis: `docs/archive/2026/status/RECOVERY_BASELINE.md` (2026-04-13) |

---

## 8. Documents outside git

All Markdown/text across Downloads, Documents, Desktop, `C:\tmp`, `G:\My Drive` scanned for March 6 terms:
550 files dated March–June matched, reducing to 32 distinct contents. Most are copies of repo documents inside
downloaded ZIPs and dated backups. Those that add something:

| File | In git? | What it adds |
|---|---|---|
| `docs/archive/2026/status/dxf_files_march20_april1_2026.md` (16 Apr) | Yes — added `9fc3fe4c`, archived `6fb853dd` | Cited by neither earlier audit. Lists the ten files in **three further folders** — `simple_extract/`, `Cuatro_DXF_Simple_Package/`, and beside `regenerated_v3/` and `test_raw/` — exactly the names gitignored at 16:52 on 6 March. Also lists `test_simple_mode_primitives.dxf` |
| `Downloads\Edge-to-DXF Router.txt` (12 Apr) | Never | Verbatim copy of the docstring that started the attribution (§5.1) |
| `Downloads\SUPERSESSION_AND_ORPHAN_AUDIT_DevOrder_v3.md` (21 Apr) | Never | The third, off-git definition of the "secret sauce" |
| `…\verify_vectorizer_audit_results.txt` (20 May) | Never | Ground-truth re-run log from the governance audit; records `_simple_extraction` and the UNKNOWN-export defect |
| `…\Phase 3.6 Vectorizer Robustness Enhancements.txt` (9 Mar) | Never | 2,117-line chat transcript implementing Phase 3.6 into `vectorizer_phase3.py`, calling `_simple_extraction`. The only off-git text within three days of the event touching SIMPLE |
| `ltb-express\…\GRID_VECTORIZER_TRAINING_ANALYSIS.md` (6 Mar) | Never | Dated the day itself, but about the STEM colour grid as training data |

**No document anywhere records the run that made the anchor, its command, or its parameters.**

---

## 9. Method, coverage, limits

**Method.** Four parallel read-only traces — live call chain, Edge-to-DXF lineage, March 6 lineage, GitHub and
deploy record — each reporting claim-by-claim with evidence, followed by direct re-checks of every claim the
verdict rests on: the default mode, the Edge-to-DXF call site, both birth dates, the SIMPLE export exclusion,
the anchor file timestamps, and the origin of the attribution sentence. Contradictions between the two morning
audits were adjudicated against primary evidence, not by preferring either report.

**Coverage.** LTB `origin/main` @ `22e67686` and all refs; sandbox `origin/master` @ `e32e9da`, all branches
and tags; 381 LTB PRs and 102 sandbox PRs; file-level inspection of the anchor set in two locations; a
disk-wide document sweep across five roots.

**Limits.**

- **Nothing was executed.** Runtime claims are read from code, not observed.
- **Deployed artifacts were not inspected.** The Railway build and the file actually on Hostinger are outside
  git's knowledge; deployment is manual.
- **Google Drive timestamps may come from cloud metadata** rather than the local filesystem.
- **Cloud-only Google Docs were not searched**, nor chat histories off this machine.
- A search for surviving copies of `simple_extract/` and `Cuatro_DXF_Simple_Package/` was still running when
  this was written.
- Rewritten history means some cited commits can only be matched to twins by timestamp and subject.

---

## 10. Decisions for the owner

1. **Which is authoritative: the documents or the runtime?** The public tool ships REFINED / Edge-to-DXF.
   Five governance documents say the canonical path is `_raw_extract`. Either the documents are corrected to
   describe what ships, or the default changes to match the documents. A product ruling; the audit cannot
   make it.
2. **The unevidenced claim in production source** (`edge_to_dxf_router.py:7, :273`) is the root of the
   conflation and is still live. Correcting it is a one-line change, but it invalidates the "corroboration"
   three later documents rest on.
3. **The photo-lane defect (D-01).** If the deployed page matches the tracked one, every photo upload fails.
   Does this get its own fix order?
4. **The measurement nobody has taken.** Run `_simple_extraction` with UNKNOWN permitted, and `_raw_extract`,
   on the cuatro PDF; compare entity count, layer and Y sign against the anchor. No code change, but it
   executes the vectorizer — needs owner go.
5. **Owner memory is the best remaining lead.** The producer wrote a single CONTOURS layer with negative Y
   into `Cuatro/simple_extract/` between roughly 22:45 and 23:08 on 6 March. A filename, notebook, or script
   pasted from a chat that evening would close this; no further repository search will.

---

## 11. Reference index

| Identifier | Date | What it is |
|---|---|---|
| `994c3453` | 03-06 01:45 | Pixel calibration + grid-zone classifier |
| `977e81a1` | 03-06 09:15 | "March 6 session log" — PDF resize only |
| `9d75d692` | 03-06 16:52 | Gitignores `Cuatro/simple_extract/`, `test_raw/`, `regenerated_v3/` |
| `5b5a3a38` | 03-06 17:01 | SIMPLE extraction mode — the anchor commit |
| `4b443693` | 03-06 18:25 | Smart/Simple UI toggle (routes to Phase 2) |
| `0bb31bf8` | 03-09 02:45 | Photo Vectorizer V2 born |
| `55c30622` | 04-01 01:08 | `edge_to_dxf.py` born |
| `dd6cb7e7` | 04-01 21:52 | Router docstring makes the March 6 attribution |
| `33226f9b` | 04-03 17:15 | `_raw_extract` / `--raw` born |
| `3ce820c1` | 04-09 12:52 | edge_to_dxf gains real contour tracing |
| `c1987620` | 04-10 | Orchestrator + cleanup layer born |
| `e16bc0fd` | 04-11 | Async job pipeline created |
| `d5f9e6bf` | 04-12 | Public page switched to the async endpoint |
| `e2b4ad66` | 04-13 03:28 | Default `mode="refined"` — unchanged since |
| `ea83589f` | 04-13 | Border removal + grouping — the live extraction logic |
| `014e720f` | 04-13 | `extract_entities_simple`, "based on March 6" |
| `778394c7` | 05-12 | MRP-1C archaeology handoff; V2_RAW + PHOTO_V2 wired |
| `86b07b07` | 05-17 | Routing and secret-sauce document |
| LTB #27 + sandbox #2 | 05-20 | The semantic-lineage relocation pair |
| `ef954747` | 05-20 | Five governance documents, ARCHAEOLOGY_COMPLETE |
| LTB #28 | 05-21 | Makes SIMPLE export-safe, fail-closed |
| `22e67686` | 09-17 | The `origin/main` this report audits |

---

## 12. Addendum, same day — the anchor was reproduced

Written after §1–§11 were published. **F-07 is overturned and C-05 changes.** The producer search
result (§4.3) stands, but it no longer blocks anything.

`scripts/light_line.py` in vectorizer-sandbox (PR #104, branch `agent/vec-lightline-002-standalone`)
lifts `_simple_extraction` verbatim and supplies the writer that function never had. Four runs, each
with pass criteria registered before execution, including the one that missed:

| Run | Settings | Entities | Verdict |
|---|---|---:|---|
| A | 300 DPI, three plans | 160,252 / 109,429 / 112,203 | structural PASS 3/3; cuatro bbox differs from the anchor by a **uniform 1.5747×** |
| B | render 472, scale 300 | 157,413 | frame confirmed to 0.10%; **count refuted, +22%**. No retry |
| C | render 400, scale 254 | **128,997** | reproduced |
| D | render 400, **literal 0.1 mm/px** | **128,997** | reproduced; file size closes to **+72 bytes** |

### Against the eleven recorded fields

Ten of eleven exact. The exception is `file_size_bytes` at +72 bytes (+0.0004%) — and its own rounded
twin `file_size_mb` matches at 15.51.

```
MATCH  dxf_version AC1009          MATCH  line_length_min_mm     0.1
MATCH  total_entities 128,997      MATCH  line_length_median_mm  0.3
MATCH  entity_types {LINE:128997}  MATCH  line_length_max_mm     818.0
MATCH  layers {CONTOURS:128997}    MATCH  coord_bbox  [50.4, -1684.0, 935.4, -20.3]
MATCH  file_size_mb 15.51          DIFFER file_size_bytes  16,264,802 vs 16,264,730
```

**The two fields that excluded every committed candidate both match exactly:** all-negative Y
(`[-1684.0, -20.3]`, identical), and the 818.0 mm maximum line.

Segment-level, at the catalog's 3 dp: both files digest to `sha256 586a94f186bd7ad7`; 128,997
identical segments; **zero** on either side alone. The owner opened both in DWG TrueView 2026 and
confirmed they match. The residual 72 bytes are two timestamps, one handle number, and one LAYER
table record the anchor does not carry — the producer named `CONTOURS` on the entities and left the
table undefined. ENTITIES sections are identical in length, 2,321,951 lines each.

### The recipe

```
render   the PDF at 400 DPI                (Phase3Vectorizer.__init__ default)
extract  grayscale; invert if mean < 127
         adaptiveThreshold(ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY_INV, 21, 10)
         findContours(RETR_LIST, CHAIN_APPROX_SIMPLE)
         drop contourArea < 50 px
         approxPolyDP(epsilon = 0.001 × arcLength), drop < 3 vertices
write    x = px × 0.1 mm     y = −py × 0.1 mm     (0.1 literal, not 25.4/254)
         R12 / AC1009, LINE, chains closed, layer CONTOURS
```

### What follows

1. **§4.2's inference is verified**, by construction rather than by argument.
2. **The producer search stops mattering.** You do not need the 2026-03-06 script once the recipe
   rebuilds its output. §4.3's five negatives remain true and are no longer load-bearing.
3. **The REFINED ruling does not reverse, but its terms change** — and the comparison has now been
   run, against six metrics registered beforehand (`RUNS.md`, "Lane comparison"). `_raw_extract`
   still cites no source and still emits 8.9×; that reasoning is untouched.
   **Correction to an earlier figure in this report:** the 2,022,289-entity / 308 MB result does
   *not* describe the live lane. Driven through the real production path, REFINED caps the render at
   200 DPI, downscales 4800×8600 → 2232×4000, and returns **3,453 segments forming one contour**.
   That contour is **40.6 × 145.9 mm, aspect 3.59** — **the neck**, identified by the owner in DWG
   TrueView, not the body outline of an instrument whose body is ~260 × 375 mm at aspect 1.44. It
   came back `ok=True`, `contour_confidence 0.745`, `recommendation ACCEPT`, no warning.
   Extended to all three plans: **cuatro → the neck, certified `accept`; Gibson Melody Maker →
   a substantially correct body-and-neck outline, flagged `review` at 0.475; Fender Strat '62 →
   crash, REJECT, no artifacts (D-09).** Zero correct, certified body outlines in three attempts.
   Measured side by side: SIMPLE covers **73.8%** of the page ink at 100 DPI against REFINED's
   **0.45%**; IoU 0.556 vs 0.0041, with the ranking stable at 400, 200 and 100 DPI. Both lanes are
   R12, audit-clean, and have **zero open endpoints**. Redundancy at ε=0.1 mm: SIMPLE 34.15%,
   REFINED 89.05%.
   **Text resolves sharper than "traded against":** both lanes emit **zero** TEXT entities. No lane
   has ever delivered text; the text problem is untouched by this recovery.
4. **The anchor is still mis-scaled.** 885 × 1664 mm for a ~260 × 375 mm instrument. Reproducing it
   reproduces the defect that became `validate_scale_before_export`. Fidelity, not manufacturing
   geometry.

Evidence: `vectorizer-sandbox/reports/lightline/vec_lightline_002/` — `METHOD.md` (every step,
including the misses), `RUNS.md` (registered criteria and verdicts), `verify_anchor_match.py`, raw
ruler inventories per run. CI on PR #104: pass.

---

## 13. Owner ruling, 2026-09-18 — REFINED is a regression

**Ruling:** *"the refined method is a regression."* — owner, 2026-09-18, after reviewing the lane
comparison and opening both outputs in DWG TrueView.

Recorded as a ruling, not as a measurement. What the audit measured, and what it did not:

**Measured, and consistent with the ruling**

| Evidence | §
|---|---|
| Three production plans through the live default: **neck only, certified `accept` 0.745** · body+neck, flagged `review` 0.475 · **crash, REJECT**. Zero correct certified outlines | §12, D-09, D-10 |
| Page-ink coverage **0.45%** against SIMPLE's **73.8%**; IoU 0.0041 vs 0.556 at 100 DPI, ranking stable at 400/200/100 | §12 |
| **89.05%** of its vertices are removable at ε = 0.1 mm | §12 |
| It discards detail before extraction: render capped 300 → 200 DPI, raster downscaled 4800×8600 → 2232×4000 | §12 |
| Its extractor was written on 2026-04-01 for **photo archival and manual tracing**, and became the blueprint default twelve days later in `e2b4ad66`, a direct commit to main with no PR whose message says "without changing default behavior" | §3.1, §2.6 |
| Five governance documents already name `vectorizer_phase3` authoritative and Edge-to-DXF legacy — the documents and this ruling agree **against the runtime** | §6.2 |

**What "regression" is measured against.** The capability that existed on 2026-03-06: a method that
traces the whole sheet, reproduced segment-for-segment on 2026-09-17 (§12). The default moved from
that to a single-contour selector. The May archaeology described a four-link regression chain but
attributed the links to the wrong components; this ruling names the surviving one.

**What the ruling does NOT do, and each needs its own order:**

1. It does **not** change the live default. `mode="refined"` is still what `blueprint_async_router.py:147`
   serves and what the Hostinger page gets.
2. It does **not** promote SIMPLE. `light_line.py` is sandbox research; `GOVERNANCE.md` requires
   graduation as **new code in `luthiers-toolbox/services/`**, and `FEATURE_PARITY_MIGRATION_POLICY.md`
   forbids superseding a canonical implementation before parity is verified.
3. It does **not** by itself authorize touching the Blueprint Reader, which
   `BLUEPRINT_READER_PROTECTION_RULES.md` holds under protection.
4. It leaves three defects open and unfixed: **D-09** (crash on the Strat), **D-10** (wrong contour
   certified), and **D-11** below.

## 14. D-11 — enhanced mode's text masking is not installed in production

`convert_enhanced`'s purpose is gap bridging (7×7 close, `e9cdf13c`). That bridging welds text glyph
strokes into blobs, which is why OCR text masking was added, default on (`20f78236`). **EasyOCR
appears in none of the six requirements files and is never installed by `docker/api/Dockerfile`**,
while `edge_to_dxf.py` references it five times.

When the library is absent, `_get_easyocr_reader()` returns `None`, `detect_text_regions` returns
`[]` (`:511-512`), the caller reads that as "no text present", and the result is marked **SUCCESS**.
BR-037 hardened the *crashed-OCR* path to `DEGRADED` but not the *absent-library* path. So in
production `mask_text=True` is honoured by doing nothing, and text is bridged into the geometry and
shipped as clean output. Separately, `blueprint_orchestrator.py:613` calls
`convert_enhanced(mask_text=False)` for `photo_v2` while the routing doc advertises that mode as
"Text: No (masked)".

---

## 15. The light-line extractor, 2026-09-18 — reproduced exactly; its dimensions were typed

### 15.1 Correction first

Earlier the same day this audit stated that `carlos_jumbo_cutaway.dxf` was **the unscaled April 1
output** and that its **476.2 × 521.2 mm** was a measured ground truth to pin against. **Both are
wrong.** The inference rested on the numbers not being round. They are not measurements at all.

`save_contour_to_dxf` (`b02091cd:services/photo-vectorizer/light_line_body_extractor.py:407-463`):

```python
pts_mm = body.to_mm_coordinates()          # = pixel indices * mm_per_px, no y flip
if scale_to_dimensions:                    # only when --target-width AND --target-height given
    pts[:,0] = (pts[:,0] - mean_x) * scale_x
    pts[:,1] = (pts[:,1] - mean_y) * scale_y
```

Pixel indices are non-negative and there is no y-negation, so an **unscaled** file cannot contain a
negative coordinate; subtracting the mean puts the centroid at exactly the origin. Every
light-line-era output fails that test:

| Written | Centroid (mm) | Bbox (mm) | File |
|---|---|---|---|
| 04-01 10:04 | (−0.000, 0.000) | 477.0 × 522.0 | `carlos_jumbo_body_light_line.dxf` |
| 04-01 10:14 | (0.000, 0.000) | 476.2 × 521.2 | `carlos_jumbo_cutaway.dxf` |
| 04-01 10:15 | (−0.000, 0.000) | 476.1 × 521.2 | `carlos_jumbo_cutaway_clean.dxf` |
| 04-01 13:24 | (0.000, 0.000) | 476.2 × 513.1 | `carlos jumbo with cutaway_silhouette.dxf` |
| 04-01 13:24 | (−0.000, 0.000) | 477.0 × 563.4 | `JUMBO-CARLOS-3-3_blueprint.dxf` |

All five were rescaled to operator-typed targets. **No light-line output carries a measured
dimension.** Two files with untransformed coordinates — `body_validated.dxf` 09:35 and
`body_complete.dxf` 09:58 — predate the commit at 10:03 and were written by something else.

Two shape metrics were tried as substitutes and both **failed their own controls**: `matchShapes`/Hu
scored a synthetic rectangle (0.73) *better* than the known-same-body light-line output (1.65);
filled-mask IoU put a rectangle at 0.627 against a best candidate of 0.738 with same-body siblings
spread 0.69–0.95. Neither separates signal from noise on these silhouettes, so neither can support a
verdict in either direction. 511 contours were scored and nothing was established by them.

### 15.2 The April 1 run, recovered and reproduced

The parameters were recovered not from a log — none exists — but from the debug stages the run wrote
beside its input, `Guitar Plans/Jumbo Carlos/debug/`, timestamped 2026-04-01 10:04:

| Parameter | Value | How fixed |
|---|---|---|
| Source | `JUMBO-CARLOS-3-3.pdf`, **A0 portrait 841.0 × 1188.9 mm** | page size of the PDF beside the debug folder |
| Render | **200 DPI** → 6623 × 9362 px | `07_result.png` is exactly 6623 × 9362 |
| Crop | **`crop_left = 0.350`** — `create_acoustic_body_config()` unmodified | `01_cropped.png` is 4305 px = 6623 × 0.650 |
| Scale | mm_per_px **0.12699** | 841.0 / 6623 |

Re-running `b02091cd` unmodified at those settings reproduces `carlos_jumbo_body_light_line.dxf`
**vertex for vertex — 114 of 114 unique points, rotation 0, same direction, worst vertex offset
0.000000** after normalising out the operator's per-axis rescale.

### 15.3 What that shows

**The extractor measured 421.3 × 497.3 mm. The operator typed 477 × 522 over it** — x ×1.1323,
y ×1.0496, **distorting the aspect by 7.9%**. A 17″ jumbo lower bout is 431.8 mm: the extraction was
within 2.4% of it, and the typed override (18.8″) is not a jumbo dimension. The artifact recorded as
the good one is the correct silhouette wearing wrong numbers, and the wrongness was entered by hand.

**Light-line has no scale capability by construction.** `mm_per_px` is derived from a page size given
on the command line, and `--target-width/--target-height` overwrite the result outright. It has never
measured an instrument in any version. What it does well — finding the closed body silhouette in a
light-line drawing — works, and is reproduced above. Scale recovery from a dimension line or scale bar
on the plan does not exist and never has. That, not a lost flag, is the open requirement.

### 15.4 The outage, and why nothing caught it

Born `b02091cd` **2026-04-01 10:03** (its own docstring: *"Developed for Carlos Jumbo blueprint
extraction, April 2026"* — the March framing was never the code's claim). Writer broken at `8d7bbeea`
**2026-04-02 20:38**, when a sweep changed `ezdxf.new('R2010')` to `'R12'` and `add_lwpolyline` began
raising on every call. Working window: **34.6 hours**.

Nothing was lost — `git show b02091cd:…` retrieves the working form. No downloaded repo copy has it:
161 were examined, and `luthiers-toolbox-main (31).zip` was pulled at **20:45, seven minutes after the
break**; the copy before it (03-25) predates the file entirely.

It went unnoticed for five months because the file sits inside the directory-wide blind spot in
**D-04**. Other instruments were run against it — `double_neck`, `dreadnought`, `melody_maker`
(`services/api/test_temp/sandbox_diagnostic/*_debug/`, surviving only in
`luthiers-toolbox.backup-20260502`, deleted from the live checkout). Only `dreadnought` reached
`07_result.png`; the writer was already broken, so **none left a DXF**.

Repaired writer, routed through `dxf_compat` so the entity type tracks the version: branch
`fix/lightline-dxf-writer` @ `e72d0156`, pushed, no PR.

---

## 16. Correction, 2026-09-19 — the default lane's failures trace to one April commit

Several defects in this record were filed as September discoveries. At least one, and probably
two, are a single regression from **2026-04-12** that was diagnosed the next day and never fixed.

**The window.** `86c49526` (2026-04-11 01:41) was the last good state. **`f49ead1d`
(2026-04-12 15:42, "feat: hierarchy-based isolation")** replaced `RETR_LIST` with `RETR_TREE`
and added `_remove_page_borders_early()`, `_isolate_with_grouping()` and cleanup-stage border
removal. `docs/archive/2026/status/RECOVERY_BASELINE.md`, dated **2026-04-13**, names the cause:

> *"The regression was caused by early filtering / structure enforcement, NOT by lack of
> detection capability."*
> *"If you destroy the candidate field early, no amount of scoring can recover the object."*

**The fix was specified and never shipped.** That document's Step 2 gives the code; its own
status table still reads `Ship as fallback | PENDING | —`. It was archived on 2026-05-02 with
the work outstanding. Verified 2026-09-19: **no automatic fallback exists in
`services/api/app`** — `restored_baseline` must be requested by name, and
`blueprint_async_router.py:147` still defaults to `refined`.

**Still live, and wider than when measured.** Re-run 2026-09-19 with `isolate_body` as the only
variable:

| Plan | REFINED | RESTORED_BASELINE | Ratio |
|---|---:|---:|---:|
| Gibson-SG-Custom | 16,762 | 462,053 | 27.6× |
| 12 StringDreadnaught_2 | 12,785 | 1,071,127 | 83.8× |
| Melody Maker (April) | 24,097 | 343,399 | 14.3× |

Counts are not the point; what survives is. The **12-String refined output is a page border and
nothing else** — zero usable content — while its baseline counterpart carries both peghead
designs, the fret-spacing table, neck sections, dovetail options, bridge detail and title block.

**What this corrects in this record:**

- **D-13** — re-attributed. Not a new defect; it is `BORDER_FALLBACK` from `f49ead1d`. The
  original row is struck through rather than deleted.
- **D-10** — probable shared root cause, **not proven**. The same document benchmarks the same
  Melody Maker plan at 0.086/REJECT against 0.690/REVIEW on an unchanged scorer. Confirming it
  for the cuatro means running that plan through both paths, which has not been done.
- **A framing error of this audit's author.** Edge-to-DXF was judged here against blueprint
  output without recording that its documented behaviour — *"captures every edge pixel",
  "50,000–300,000+ LINE entities"* — describes the **pre-`f49ead1d`** tool. The docstring was
  kept; the behaviour was not. Measurements taken against the post-regression artifact and read
  as the tool's design are unsafe.

Order: `docs/handoffs/DEV_ORDER_RESTORED_BASELINE_FALLBACK.md`.

### 16a. The regression, measured at scale (added 2026-09-19)

The re-measurement above used four one-off plans. A 15-page sample from one document family —
Fender headstock sheets, all 2200 × 1700 px so **no downscale fires** and resolution cannot
confound the comparison, `isolate_body` the only variable — gives a much stronger result.

Ratios: pages 01–12 min 20.7× / median 75.8× / max 83.6×; pages 13–24 min 25.7× / median 99.5× /
max 144.3×. But the ratio is not the finding:

> **13 of 24 plans return byte-identical REFINED output.** Pages 01, 02, 03, 04, 07, 08, 09, 10,
> 11, 12, 13, 15 and 19 all produce geometry hash `f13dab6370b2ba8b` — 7,004 entities,
> 329.7 × 247.4 mm, identical in every one. Pages 17 and 18 share a second. **24 sheets produce
> only 11 distinct geometries.**

Entity count alone would have understated this: pages 16, 17, 18 and 22 also return 7,004
entities but *different* geometry. The duplication is visible only by hashing coordinates.

Rendered, that shared output is **an empty rectangle** — the page frame. The permissive path on
the same page returns two Telecaster headstocks with tuner holes, the callouts *1.590 nut width*
and *0.122 as drawn*, a 7.53° angle and the label *"Bonnie Raitt"*: 468,929 entities.

This is `BORDER_FALLBACK` at scale, and it sharpens what the defect is. The default is not
producing a poor result on these pages; it is producing **the same result regardless of what is
drawn on them**. A system in that state cannot be distinguished from one that ignores its input.

### 16b. Two defects found while measuring

**D-15** and **D-16** above were both found in the course of this work rather than by looking for
them: D-15 because the cuatro would not load under its own name, and D-16 because the function
was read while answering an unrelated question about PDF ingestion. D-16 had already silently
downscaled three source plans in place before it was noticed; they were recovered byte-for-byte.

Both share the shape of every defect in this record: **harmless on the single path anyone
exercises, destructive on every other, and absent from the contract.** D-16 is invisible in
production because the orchestrator passes a temp file. D-12 was cleared by an audit that checked
the call site instead of the output. D-14 advertises a flag that does nothing. The common failure
is not the code; it is that nothing checks what the code actually produced.

---

**Standing.** This is an audit record, not an authorization. No repository was modified, no pull request
opened, and no merge, ruling or remediation is implied. Claims resting on inference rather than evidence are
marked UNRESOLVED and stay that way until someone measures them.
