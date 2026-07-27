# Luthier's Toolbox — 16-Detector Scan @ `ac3c96df`

**Scanned commit:** `ac3c96dfd5f751fc870b5ea218fefc6b1cabe775` (`origin/main` tip, fetched
2026-07-26; unchanged since #231 merged 2026-07-23).
**Method:** read-only. Clean detached worktree, tracked files only (`git ls-files`), so no
`node_modules`, `.venv`, `dist`, `htmlcov`, `__pycache__`, or build output is counted.
**Status:** every entry below is a **lead**, not a verdict.

**Confidence vocabulary** (shared with
[`REPOSITORY_DEFECT_REGISTER.md`](../remediation/REPOSITORY_DEFECT_REGISTER.md) — the two documents
must not drift):

| Label | Means | Can a code read establish it? |
|---|---|---|
| `CANDIDATE` | a detector flagged it; nothing verified | — |
| `STATIC-FACT CONFIRMED` | the *code says so* — two writers exist, a default is unguarded | ✅ yes |
| `CONFIRMED` | the *symptom was reproduced* at runtime | ❌ never |

Reading a producer→consumer chain and inferring a symptom is a **hypothesis**, however convincing the
chain. F-1 below was originally labelled `CONFIRMED` on a read alone; that was an overclaim, and it is
annotated in place rather than quietly rewritten.

> **Grounding note.** The prior pass ran against a July-15 *file snapshot*. This ran against current
> `main`. Where the two disagree, **these numbers are the real ones** — but several disagreements are
> *method* differences, not drift, and are labelled as such rather than reported as change.

---

## 1. Delta table — snapshot vs current

| # | Detector | Snapshot (Jul-15) | Current @ `ac3c96df` | Read |
|---|---|---|---|---|
| — | Python files | 2,514 | **2,633** | grew |
| — | Vue files | 771 | **812** | grew |
| 1 | bare `except:` | 14 | **2** | **improved** |
| 1 | `except Exception` | 107 | **594** | method differs (snapshot likely counted `except Exception:` only, not `as e`) |
| 1 | **silent-swallow handlers** | 199 | **637 total / 447 production** | method differs — see §2 |
| 2 | domain-default lookups | 38 | **10** (strict `X.get(k, X[DEFAULT])`) | narrower, higher-confidence set |
| 3 | hard caps returning empty | — | **0 confirmed** (62 cap constants, none return-empty-on-breach) | clean |
| 4 | duplication shortlist | store×12, registry×7, geometry×6, schemas×19 | **identical** (12/7/6/19) | **unchanged** |
| 4 | near-identical clones (AST) | — | **1 clone group** | **hypothesis refuted** — see §3 |
| 6 | context-pinned hashes | 0 | **0 confirmed** | **snapshot confirmed** |
| 7 | relocation-fragile imports | — | **239** production `from ...` | new measure |
| 8 | routers | 278 | **253 files / 1,228 routes** (gate's own counter) | **improved** |
| 9 | stale baselines | — | **no drift** — gate reports 253/1228 = baseline exactly | **clean** |
| 10 | multi-writer storage | 3 | **11 candidates, 1 confirmed collision** | see §2 |
| 12 | TODO/FIXME/HACK | 66 | **72 total / 37 production** | flat |
| 11 | order-dependent resolution | — | **BLOCKED — needs runtime** | §5 |
| 13 | untested files | — | **BLOCKED — needs coverage report** | §5 |

**Headline:** the repo got *bigger* but the two things that were measured as broken — bare excepts
(14→2) and router sprawl (278→253) — **went down**. Real fixes landed. The duplication shortlist did
not move at all.

---

## 2. Ranked findings — by (severity × confidence × cheapness to confirm)

### 🔴 F-1 · CONFIRMED (reproduced) · `detect_text_regions()` returns `[]` on any failure → text is silently vectorized into the DXF
`services/photo-vectorizer/edge_to_dxf.py:522` (function `detect_text_regions`, 470–524)
consumed at `edge_to_dxf.py:1951`.

```python
except Exception as e:
    logger.warning(f"Text detection failed: {e}")
    return []                       # :522
...
text_regions = detect_text_regions(img, ...)
if text_regions:                    # :1951 — empty list is falsy
    ... apply_text_mask_to_edges(...)
```

If OCR raises for **any** reason, the function returns `[]`, the `if text_regions:` guard skips text
masking entirely, and the pipeline proceeds into the 7×7 morphological close — which the code's own
comment says text masking exists to prevent: *"This prevents the 7×7 kernel from bridging text glyph
strokes."* The DXF is produced **successfully**, silently containing text strokes as body geometry.
The `TEXT_MASK | Removed …` log line never prints, so nothing distinguishes *"no text in this image"*
from *"text detection crashed."* Textbook failure-mimics-success.
**Confidence: CONFIRMED — reproduced.** *(This label was initially `CONFIRMED by producer→consumer
read`, which was an overclaim: a chain read is a hypothesis, not a confirmation. It was later
reproduced — an image with text plus a body shape, OCR forced to raise, produced **1475 DXF entities
inside the text bounding box against 0 in a no-text control**, while the result still reported
`SUCCESS`. That run is what earned the word.)* **Fix size:** small. **Fixed and merged to `main` 2026-07-27 (`97460755`, PR #232).**

### 🟠 F-2 · STATIC-FACT CONFIRMED · Two store modules write the same JSON file
`services/api/app/services/art_job_store.py:17` and
`services/api/app/services/art_jobs_store.py:20` — **singular/plural twins** — both declare
`JOBS_PATH = Path("data/art_jobs.json")` and both write it. Two writers, one file, no coordination.
This is exactly the art-jobs shared-JSON class.
**Confidence: STATIC-FACT CONFIRMED** — that both writers exist and both write is established by
read. The *runtime* consequence (interleaved writes losing data) is **not reproduced**, so this is
not `CONFIRMED` in the sense F-1 now is.

### 🟠 F-3 · CANDIDATE · Three parallel preset stores, three different files
`art_presets_store.py:9` → `data/art_presets.json` · `preset_store.py:14` →
`data/presets/presets.json` · `util/presets_store.py:23` → `data/presets.json`. Not a write
collision (paths differ) but an **authority** problem: three modules named `*preset*store` each own a
different presets file, with no declared canonical. **Needs:** owner ruling on which is canonical.

### 🟠 F-4 · CANDIDATE · Silent domain-default fallback (the `FAMILY_DEFAULTS` class) — 10 sites
An unknown domain key silently becomes a default instead of erroring:

| Site | Fallback |
|---|---|
| `instrument_geometry/body/ibg/body_contour_solver.py:250` | `FAMILY_DEFAULTS.get(family, FAMILY_DEFAULTS["dreadnought"])` |
| `calculators/neck_block_calc.py:202` | `_BODY_STYLE_DEFAULTS.get(style, _BODY_STYLE_DEFAULTS["dreadnought"])` |
| `calculators/neck_block_calc.py:246` | `DEFAULTS.get(key, DEFAULTS["dreadnought"])` |
| `analyzer/viewer_pack_bridge.py` ×6 (176, 199, 346, 352, 357, 362) | `_SPECIES_DEFAULTS.get(species, _SPECIES_DEFAULTS[_DEFAULT_SPECIES])` |
| `workflow/directional_workflow.py:187` | `_MODE_DEFAULTS.get(mode, _MODE_DEFAULTS[design_first])` |

An unrecognized body family silently produces **dreadnought geometry**; an unrecognized species
silently produces **default material properties**. **Confirm by:** checking whether each key space is
closed (enum-validated upstream). Where it is, these are harmless; where it isn't, each is a live
wrong-output path.

### 🟡 F-5 · CANDIDATE · 447 production silent-swallow handlers
Segmented from 637 total: **106** are `ImportError` optional-dependency guards (usually legitimate),
**84** are archive/test, leaving **447** production. By kind: `pass` 115 · `empty-return` 85 ·
`log-only` 81 · `continue` 75 · `log-then-empty-return` 61 · `log-then-pass` 30.
The `empty-return` + `log-then-empty-return` subset (**146**) is the F-1 shape and is where to look
next. Hotspots: `photo_vectorizer_v2.py` (11), `vectorizer_phase3.py` (10),
`rmos/runs_v2/store.py` (8), `art_studio/services/rosette_snapshot_store.py` (7).

### 🟡 F-6 · CANDIDATE · 239 production `from ...` deep-relative imports
Depth ≥3 relative imports assume a package root; concentrated in
`services/api/app/art_studio/api/*_routes.py`. Refactor-fragile, not currently broken.

---

## 3. Two hypotheses this scan **refuted**

Reporting these matters as much as the findings — they redirect effort away from non-problems.

- **Duplicate-filename drift is not real.** AST-hashing every function in the shortlist
  (`store.py`×12, `registry.py`×7, `geometry.py`×6, `schemas.py`×19) — name/docstring/literal
  normalized — found **exactly one** structurally-identical group spanning >1 file: `require()` in
  `rmos/runs_v2/db/store.py:120` and `workflow/db/store.py:75`. The duplicate filenames are a
  **naming convention, not copy-paste drift.** Consolidating them on duplication grounds would be
  wasted work.
- **Baselines are not stale.** My filename-based count (359 routers / 1,473 routes) looked like large
  drift against the 253/1,228 baseline — but running the gate's *own* counter returns **253/1,228,
  exactly baseline**. The discrepancy was my counting scope, not repo drift. `ci/router_count_gate.py`
  reports `OK: Router counts within baseline`.

Also confirmed clean: **context-pinned hashes = 0** (1,293 `sha256`/`hexdigest` sites, but zero hash a
text-mode file read, so no line-ending/OS fragility) and **hard-caps-returning-empty = 0** (62 cap
constants, none return `[]`/`0` on breach).

---

## 4. The one-hour subset — confirmed and cheap

1. ~~**F-1** — make `detect_text_regions` distinguish "no text" from "detection failed".~~
   ✅ **DONE — PR #232.** Reproduced first (1475 entities vs a 0 control), then fixed. The shipped fix
   is *emit-and-flag*, not the "raise" suggested here: raising was implemented and then **rejected by
   the no-text control run**, which showed it also refuses images containing no text at all — a failed
   OCR pass cannot know whether the image had any. The result is now marked
   `ConversionStatus.DEGRADED` instead. Estimate was ~20 min; actual was considerably longer, because
   the first two candidate fixes were wrong and only running them showed it.
2. **F-2** — collapse `art_job_store` / `art_jobs_store` to one writer, or make one delegate. ~30 min;
   the risk is which is canonical, so confirm consumers first.

Both are small, both are confirmed, and F-1 is a live wrong-output bug in the DXF pipeline.

---

## 5. Blocked — needs runtime, not reported as a number

Deliberately **not** estimated rather than guessed:

- **D11 order-dependent resolution.** Requires shuffling router mount/import order and asserting
  behavior is unchanged. Run:
  `python -m pytest services/api/tests -p no:randomly` vs. with shuffling enabled, and diff the
  resolved route table. If behavior changes, load order is the de-facto authority.
- **D13 files with no covering test.** Requires a full coverage report. The full suite is 331 test
  files and does **not** complete in this environment (killed twice mid-run in the CV/DXF tests).
  Run in CI: `pytest --cov=services/api/app --cov-report=json`, then diff covered files against
  `git ls-files 'services/api/app/**.py'`.
- **D5 name≠behavior** was bounded to a ~25-function sample by agreement; no mismatch rose above
  candidate confidence, so nothing is claimed here rather than padding the report.

---

## 6. Detector reliability notes

Two bugs in *my own* detectors were found and fixed mid-scan; both would have understated results:

1. Splitting `git ls-files` on whitespace broke paths containing spaces → **102 files went unscanned**.
   Fixed with `-z` / NUL-splitting; the real parse-failure count is **10**, all
   `docs/archive/recovered/__RECOVERED__/` files that are genuinely unparseable.
2. The AST walker caught only `SyntaxError`; a null-byte file raised `ValueError` and killed the run.

The `except Exception` and silent-swallow counts differ from the snapshot largely by **definition**,
not by drift — this scan counts `continue`, `log-only`, and tuple-typed handlers that a
`grep "except Exception:"` pass would miss. Compare the *segmented production* number (447), not the
raw total, against any future run.
