# VEC-ROOT-001 — reproduction record

Supports `docs/audit/VEC-ROOT-001_eligibility_body_definition.md`. Eleven instrumented scripts,
run 2026-09-19. Every one is a **runtime wrap**: it imports `edge_to_dxf` and replaces functions on
the module object at call time. **No script edits any repo file**, and the refined-extraction freeze
is not touched.

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
media.** The scripts read from the owner's corpus by absolute path; the hashes pin which file.

| script variable | file | bytes | SHA-256 |
|---|---|---|---|
| `SRC` (cuatro, 9 scripts) | `cuatro_ascii.png` | 1,406,120 | `2d7f85f5040d3d21f5fe9918e7e8d40205406240534fa858af34ce91e0fcd0f9` |
| `SRC` (L-00) | `Gibson-L0-IN.png` | 1,651,220 | `2a3fea551282feef07a4ed58d1c1d7880518c690a0a6d6e9ab3148112f80fda7` |
| archtop CONTROL | `…Florentine Cutaway_02_foreground.jpg` | 204,115 | `ee2db7346c9fb29b27b48a1eade4e7d473b194b198e552705d51c6f25a383f86` |
| archtop compare | `…Florentine Cutaway_00_original.jpg` | 417,041 | `997634c9fc4eb3a39b417ce193850fe36d979decfd26c0b81750e6c7272a98ad` |

To re-run, point each `SRC` / `GP` at your own copy. The scripts are otherwise self-contained.

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

§12 of the audit previously listed six of these. The three archtop scripts carry §11 and §11a —
the positive control — and `cuatro_render_groups.py` and `longest_rejects.py` produce two of the
six renders §12 names. All eleven are here.

---

## 4. Renders — not in this repository

Each render draws the result **on top of the source plan**, so it reproduces the plan in full and
falls under the same ruling as §2. They are retained in the owner's private corpus. Hashes pin
which image each `[RENDER]` tag in the audit rests on.

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

## 5. What this record does and does not buy

**Does:** the code path is pinned to a blob, the offset to `main` is stated, every number in the
audit has a named producer, and every image a hash. A reader with the corpus can re-run and compare.

**Does not:** a reader **without** the corpus cannot reproduce the measurements from this
repository alone. That is a custody consequence, not an oversight, and it is why the hashes are
here instead of the files.

## 6. D-16 guard

Observed on every run: the source was copied to a scratch directory and hashed before and after.
Both `OK` — no run modified an original.
