# VEC-ROOT-001 — reproduction record

Supports `docs/audit/VEC-ROOT-001_eligibility_body_definition.md`. Eleven instrumented scripts,
first run 2026-09-19, **re-run from a clean invocation 2026-09-20 against `main` and against the
pinned revision — every figure in the audit reproduced** (§6).

Every script is a **runtime wrap**: it imports `edge_to_dxf` and replaces functions on the module
object at call time. **No script edits any repo file**, no script writes anywhere inside the
checkout, and the refined-extraction freeze is not touched.

All eleven share one environment contract, in `_repro.py`: the repository is discovered, the
imported revision is verified against the pinned blob, inputs are addressed by logical name and
checked by SHA-256, and every output goes to a temporary directory outside the repository. Nothing
is hard-coded to one machine — see §3.

---

## 1. The revision the measurements were taken at

Measured against the working tree of `smart-guitar-cavity-geometry-1` at commit
**`ffd155e436be89c15cdb0b83a96dc7d2cbefa251`**.

The subject file was **clean** at that commit — `git status` reported no modification to
`services/photo-vectorizer/edge_to_dxf.py`, and its content hashes to blob
**`f3e7d802fefa`**. That is the durable pin: the blob id resolves whatever happens to the branch.

### 1a. That commit is behind `main`, and the line numbers move

`main` carries **`97460755`** (BR-037, PR #232), which the measured branch does not. BR-037 edits
`edge_to_dxf.py` — 74 lines added across eight hunks — so **every line number in the audit and in
these script headers is offset on `main`.**

The eligibility block itself is **byte-identical** on both revisions (same five-branch ladder, same
`min_area_ratio=0.005` / `max_area_ratio=0.95`). Only its position moved.

| symbol | measured (`ffd155e4`) | `main` (`c847c043`) |
|---|---|---|
| `area = float(cv2.contourArea(contour))` | 930 | 956 |
| the eligibility ladder | **941–950** | **967–976** |
| `elif area_ratio < min_area_ratio` (`too_small`) | 943 | 969 |
| `nodes = _build_hierarchy_nodes(` | 1233 | 1259 |
| `def convert(` | 1535 | 1575 |
| `cv2.findContours(... RETR_TREE ...)` | 1624 | 1664 |
| `_remove_page_borders_early(` | 1632 | 1672 |
| `_isolate_with_grouping(` | 1645 | 1685 |
| `else:` → the `RETR_LIST` branch | 1731 | 1771 |
| `def convert_enhanced(` | 1886 | 1926 |
| `if mask_text:` | 1950 | 1991 |
| `converter.convert_enhanced(` (CLI) | 2827 | 2896 |

**What BR-037 changed, and what it did not.** It adds a `DEGRADED` status when OCR fails inside
`convert_enhanced`, so a failed text-mask can no longer be mistaken for a clean conversion. It does
**not** change reachability: on `main`, `convert()` (1575–1925) still contains no call to
`detect_text_regions` and never sets `mask_text`; `convert_enhanced` (1926) still has exactly one
caller, the CLI at 2896. **§3a of the audit holds on `main` as written, at the remapped lines.**

---

## 2. Inputs — not in this repository

Third-party plan material. Owner ruling R1 / SC-A02 (2026-09-10, CUSTODY-REMED-001): the private
reference corpus is legitimate development input; **the public repository must not hold source
media.**

Inputs are addressed by **logical name**, resolved against `--corpus-root`. The hash is not
decoration: `corpus()` verifies it before the run and exits `ENVIRONMENT_MISMATCH` on a mismatch,
so a measurement taken against a different file is caught rather than argued about afterwards.

| logical name | file, relative to `--corpus-root` | bytes | SHA-256 |
|---|---|---|---|
| `cuatro` (8 scripts) | `cuatro_ascii.png` | 1,652,751 | `2d7f85f5040d3d21f5fe9918e7e8d40205406240534fa858af34ce91e0fcd0f9` |
| `l00` | `Gibson-L0-IN.png` | 1,651,220 | `2a3fea551282feef07a4ed58d1c1d7880518c690a0a6d6e9ab3148112f80fda7` |
| `archtop_foreground` | `…Florentine Cutaway_02_foreground.jpg` | 204,115 | `ee2db7346c9fb29b27b48a1eade4e7d473b194b198e552705d51c6f25a383f86` |
| `archtop_original` | `…Florentine Cutaway_00_original.jpg` | 417,041 | `997634c9fc4eb3a39b417ce193850fe36d979decfd26c0b81750e6c7272a98ad` |

Put those four files in one directory and point `--corpus-root` at it; the names above are what
each script looks for. A missing file exits `NOT_RUN_SOURCE_ABSENT` (2) naming what it wanted and
where it looked — a reproduction record that silently skips its own run is one that cannot fail.

---

## 3. Scripts, and the claims each one carries

| script | produces | audit claim it supports |
|---|---|---|
| `cuatro_stage_census.py` | `CUATRO_stage_census.png` | §2 — 7,368 → 7,332 nodes → 3 eligible; 7,328 `too_small` |
| `where_is_the_perimeter.py` | `CUATRO_lower_bout_by_reason.png` | §2 — lower bout 1,437 contours, 0 eligible |
| `whole_sheet_by_reason.py` | `CUATRO_whole_sheet_by_reason.png` | §2 — whole sheet, coloured by reject reason |
| `cuatro_render_groups.py` | `CUATRO_scored_groups.png` | §2, §4 — the winner is the fret table, s=0.7323 |
| `longest_rejects.py` | `CUATRO_the_rejected_body.png` | §2 — the perimeter is traced, then discarded |
| `hull_vs_area.py` | *(stdout)* | §5 — convex hull is the right diagnostic, wrong fix |
| `arclen_discriminates.py` | `CUATRO_top50_by_arclength.png` | §5 — arc length ranks a ruled fret table #5 |
| `l00_prediction.py` | `L00_too_small_pile.png` | §2, §3 — L-00 0 eligible; refused `child_contour` |
| `archtop_control.py` | *(stdout)* | §11 — 488 contours, 1 eligible, s=0.8464 / 0.9894 |
| `archtop_render.py` | `ARCHTOP_eligible.png` | §11 — the eligible contour **is** the guitar |
| `archtop_neck_check.py` | `ARCHTOP_neck_check.png` | §11a — one path weaving between neck edge and inlays |
| `_repro.py` | *(none)* | the shared environment contract — repo discovery, revision check, corpus resolution, output placement (§5) |

§12 of the audit previously listed six of these. The three archtop scripts carry §11 and §11a —
the positive control — and `cuatro_render_groups.py` and `longest_rejects.py` produce two of the
six renders §12 names. All eleven are here.

---

## 4. Renders — not in this repository

Each render draws the result **on top of the source plan**, so it reproduces the plan in full and
falls under the same ruling as §2. They are retained in the owner's private corpus. Hashes pin
which image each `[RENDER]` tag in the audit rests on.

**These hashes are a bit-exact reproduction target, not a record of what once existed.** On
2026-09-20 the six cuatro and L-00 renders were regenerated from a different working directory,
against `main`'s blob rather than the pinned branch, through the rewritten harness — and came back
**byte-identical to every value below**. That is also the evidence that moving the scripts onto
`_repro.py` changed no behaviour.

| render | bytes | SHA-256 |
|---|---|---|
| `CUATRO_stage_census.png` | 469,361 | `72620a6c504de4672a79b9e8c0acf6bc54b43e63458e4ff992ec986b72efe7da` |
| `CUATRO_scored_groups.png` | 480,117 | `9693ddafe135b7fb03f9c2dab204be792936cc3e94abd4c060aacf996492242c` |
| `CUATRO_lower_bout_by_reason.png` | 443,784 | `65aef5fdcd8548f07a50c5f82e8939ea8332ba398a05611f2a20207e0e71b250` |
| `CUATRO_whole_sheet_by_reason.png` | 662,743 | `326c0ba7ada22661cb93b521b0ecf8be01eacba68da583876c6ec212d7c9cdf1` |
| `CUATRO_the_rejected_body.png` | 448,791 | `380133c2152bd7b6a0e85c9badbd360912ba610d93c6d22b00552ce88ca942d4` |
| `CUATRO_top50_by_arclength.png` | 596,984 | `a756b35283dd2daaa4715cf7bd67ae45811dd4de2ffff0db31723af19043e2b4` |
| `L00_too_small_pile.png` | 919,226 | `7e5c911bcde75161b9e09b1963870a476d066abb73cb1a689a6c947fe71148ee` |
| `ARCHTOP_eligible.png` | 2,069,762 | `ef3799fdffdec3f3201da6e6b7c4ea46efd2d7dc14ab79d7b50a14887881ea93` |
| `ARCHTOP_neck_check.png` | 1,342,724 | `96370aa5344d4b7f4b7ab65ebd413ca1f5e79b882f6f504df41177ec6656a895` |

---

## 5. Running them

From a fresh clone, with `opencv-python` and `numpy` installed and the corpus on disk:

```bash
python docs/audit/vec-root-001-repro/cuatro_stage_census.py     --corpus-root /path/to/plans     --out-dir /tmp/vec-root-001
```

Every script takes the same five options, handled once in `_repro.py`:

| option | environment variable | default |
|---|---|---|
| `--repo-root` | `LTB_REPO_ROOT` | discovered by walking up to the enclosing `.git` |
| `--corpus-root` | `LTB_CORPUS_ROOT` | none — absent inputs exit `NOT_RUN_SOURCE_ABSENT` |
| `--out-dir` | `LTB_OUT_DIR` | a temp directory; **refused if inside the repository** |
| `--work-dir` | — | a temp directory; **refused if inside the repository** |
| `--allow-revision-drift` | — | off — an unrecognised `edge_to_dxf.py` refuses to run |

**The revision is checked before anything else happens.** Each run opens with one of:

```
[revision] ... is the PINNED blob f3e7d802fefa (ffd155e4) -- the audit's line numbers apply as written.
[revision] ... is MAIN blob c847c04365d3 (after BR-037, 97460755).
           The eligibility block is byte-identical but sits 26 lines later: 967-976, not 941-950.
```

Anything else refuses with `ENVIRONMENT_MISMATCH` (3) rather than producing numbers that look like
the audit's and are not. Pinning a revision and then importing whatever is on disk pins nothing.

### 5a. What is written where

Working copies and renders go to a temporary directory. `--out-dir` and `--work-dir` are both
rejected if they resolve inside the checkout. After the fifteen runs recorded in §6, `git status`
in the repository was clean.

The one thing Python writes inside the checkout is `docs/audit/vec-root-001-repro/__pycache__/`
for the `_repro` import. It is covered by `.gitignore:20`. Set `PYTHONDONTWRITEBYTECODE=1` to
suppress it entirely.

---

## 6. Re-run 2026-09-20 — the audit reproduces, including on `main`

All eleven scripts were re-run from a clean invocation after the rewrite. **Every figure the audit
states was reproduced**, against `main`'s blob and, for the archtop, against the pinned blob too.
The original measurements were only ever taken on the stale branch; this is the first evidence they
hold on the branch the document merges into.

| claim | audit | re-run |
|---|---|---|
| cuatro contours → nodes → eligible | 7,368 → 7,332 → 3 | 7,368 → 7,332 → 3 |
| cuatro `too_small` refusals | 7,328 | 7,328 |
| cuatro winner | fret table, s=0.7323, 2.92% | s=0.7323, 2.92% |
| cuatro lower bout | 1,437 contours, 0 eligible | 1,437, 0 |
| longest refused arcs | 8,290 px and 7,421 px | 8,290 and 7,421 |
| fret table by arc length | rank 5, 6,606 px | rank 5, 6,606 px |
| L-00 | 3,053 contours, 0 eligible, run fails | 3,053, 0, `No valid contours found` |
| L-00 largest contour | 1815×1365, 0.276, `child_contour` | 1815×1365, 0.276110, `child_contour` |
| L-00 page border | 0.962, `too_large` | 0.962446, `too_large` |
| archtop CONTROL | 488 contours, 1 eligible @ 0.0145, parent `None`, s=0.8464 | 488, 1 @ 0.014521, `None`, 0.8464 |
| archtop original | 634 contours, `too_small`=632, `child`=1, s=0.9894 | 634, 632, 1, 0.9894 |
| archtop neck corridor | 13,322 points, arc 14,626, 39.2%, 3,864 v 1,352, 569/569 | identical |

The guards were exercised too: absent corpus → exit 2; wrong input hash → exit 3; unrecognised
`edge_to_dxf.py` → exit 3; `--out-dir` inside the repository → exit 3.

## 7. D-16 guard

Observed on every run: the source was copied to a scratch directory and hashed before and after.
Both `OK` — no run modified an original. Re-confirmed on the 2026-09-20 archtop and L-00 runs
(`source untouched: OK`).
