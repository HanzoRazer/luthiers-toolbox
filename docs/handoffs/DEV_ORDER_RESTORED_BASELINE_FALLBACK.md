# DEV ORDER — ship the `restored_baseline` fallback

**Raised:** 2026-09-19
**Status:** ORDER — not implemented, not authorized to merge without owner GO
**Supersedes nothing. Completes:** `docs/archive/2026/status/RECOVERY_BASELINE.md` (2026-04-13),
Step 2, whose own status table still reads `Ship as fallback | PENDING | —`

---

## 1. Why this exists

The blueprint lane's default extraction mode has been in a known, diagnosed, benchmarked
regression since **2026-04-12**. The fix was specified the following day and never shipped. The
document that specified it was archived on 2026-05-02 with the work outstanding.

This order asks for that one change and nothing else.

## 2. The regression, established

| | |
|---|---|
| Last good state | `86c49526`, 2026-04-11 01:41 |
| Regression introduced | **`f49ead1d`, 2026-04-12 15:42** — "feat: hierarchy-based isolation" |
| What it added | `RETR_TREE` in place of `RETR_LIST`, `_remove_page_borders_early()`, `_isolate_with_grouping()`, cleanup-stage border removal |
| Diagnosed | 2026-04-13, `RECOVERY_BASELINE.md` |
| Fix specified | Same document, Step 2, marked CRITICAL |
| Shipped | **No** |

Root cause, in that document's own words:

> *"The regression was caused by early filtering / structure enforcement, NOT by lack of
> detection capability."*
> *"If you destroy the candidate field early, no amount of scoring can recover the object."*

## 3. It is still live, and worse than when it was measured

Re-run 2026-09-19 against two production plans. The only difference between the two columns is
the `isolate_body` flag:

| Plan | REFINED (default) | RESTORED_BASELINE | Ratio |
|---|---:|---:|---:|
| `Gibson-SG-Custom.png` | 16,762 | 462,053 | **27.6×** |
| `12 StringDreadnaught_2.jpg` | 12,785 | 1,071,127 | **83.8×** |
| Melody Maker (April benchmark) | 24,097 | 343,399 | 14.3× |

Entity counts are not the point; **what survives is.** Rendered:

- **SG Custom, REFINED** — a deformed body silhouette, one cutaway horn mangled, stray
  tick-marks along the neck. No pickups, bridge, controls, headstock, side elevation, section
  or specification block.
- **SG Custom, RESTORED_BASELINE** — the complete sheet, including all of the above.
- **12-String, REFINED** — **an empty rectangle.** The 12,785 entities are the page border
  traced at pixel resolution. Zero usable content.
- **12-String, RESTORED_BASELINE** — the complete sheet: both peghead designs, fret-spacing
  table, neck sections, dovetail options, bridge detail, Section I-I, title block.

Evidence: `CMP_Gibson-SG-Custom.png`, `CMP_12_StringDreadnaught_2.png`, and the four
`CMP_*_{refined,baseline}.dxf` files.

The 12-String case is `BORDER_FALLBACK` exactly as described in April:

> *"hierarchy-based filtering removes all non-border contours, leaving only the page border as
> a candidate."*

## 4. What is being asked for

Implement the automatic fallback specified in `RECOVERY_BASELINE.md` Step 2. Nothing more.

**Location:** `services/api/app/services/blueprint_orchestrator.py`, in `process_file`, at the
single return site `:1009` (`return BlueprintResult(...)`). The recommendation is computed at
`:994-998`; `is_ok` is `rec.action == RecommendationAction.ACCEPT`.

**Shape** (as written in the April document, adapted to the current return path):

```python
result_refined = <existing path>

if mode == CleanupMode.REFINED and _is_unacceptable(result_refined):
    result_baseline = <same path, mode=CleanupMode.RESTORED_BASELINE>
    result_baseline.metrics["behavior_source"] = "restored_baseline"
    return result_baseline

result_refined.metrics["behavior_source"] = "refined"
return result_refined
```

**`_is_unacceptable` — the April definition, unchanged:**

- `rec.action == RecommendationAction.REJECT`
- OR a page-border warning is present
- OR `selection.selection_score < 0.15`
- OR `dxf.entity_count < 5000`

**Telemetry (Step 3):** emit `behavior_source` in the response so fallback frequency and the
files that still break refined can be tracked. Note `behavior_source` is already used at `:458`
for `dual_pass_phase4`; keep the key and add these two values.

## 5. Constraints — carried verbatim from the April document

> ```
> # DO NOT MODIFY restored_baseline WITHOUT EXPLICIT APPROVAL
> # - No refactoring   - No cleanup   - No optimization   - No "quick improvements"
> ```

Specifically, **do not**:

| Action | Why not |
|---|---|
| Reduce the baseline entity count | Reintroduces the filtering that caused the regression |
| "Optimize" `restored_baseline` | Any change risks breaking the ground-truth path |
| Re-tune scoring | Scoring works; the candidate field was the problem (0.086 → 0.690 on identical scorer) |
| Change the REFINED path | Out of scope. This order adds a fallback, it does not alter refined |

## 6. Acceptance criteria

1. `12 StringDreadnaught_2.jpg` through the **default** endpoint no longer returns a page-border-only result.
2. `Gibson-SG-Custom.png` through the default endpoint returns the plan detail, not the bare silhouette.
3. A plan that already succeeds under refined is **unchanged** — fallback must not fire on it.
4. `behavior_source` is present in every response and reports which path produced the artifact.
5. No change to `restored_baseline`'s own behaviour; existing `restored_baseline` output is byte-comparable before and after.

## 7. Known cost, stated up front

The baseline path is heavy and this will be felt: **58.7 MB / 462k entities** for the SG and
**155.6 MB / 1.07M entities** for the 12-String, against 2 MB for refined. Load time in a viewer
was ~37 s and ~905 MB RAM for the SG.

The April document addressed this directly and the answer is recorded:

> *"The 14x Entity Increase is NOT a Bug... This is exactly what the old system did. That's why
> it worked as a starter. DO NOT try to 'fix' or reduce this yet."*

Controlled reduction is explicitly post-stabilisation work: *"Remove obvious junk AFTER
extraction, not before."* If size is unacceptable for the web tier, that is a separate order
about output reduction, and it must not be solved by leaving the regression in place.

## 7a. Follow-on step — border removal, AFTER extraction

The permissive path returns the sheet's printed border along with everything else, because edge
tracing has no concept of "frame" versus "instrument". That is cosmetic and cheap to fix, and
fixing it is the whole difference between this order and the regression it addresses.

**The pipeline already has a border remover, and it is the regression.**
`_remove_page_borders_early()` runs *before* grouping — the name says it — so when the body
contour is fragmented it removes the body along with the frame. That is the mechanism behind
the page-border-only result.

`RECOVERY_BASELINE.md`'s post-stabilisation plan states the correct order:

> *"Controlled reduction — Remove obvious junk AFTER extraction, not before."*

**Measured 2026-09-19** on the SG Custom baseline, with a purely geometric rule — both endpoints
within 6 mm of the same bounding-box edge, and running parallel to it:

| | |
|---|---|
| Border segments | **6,508 of 462,053 (1.41%)** |
| Extent before | 336.3 × 536.5 mm |
| Extent after | 321.9 × 524.7 mm |
| Interior geometry lost | none — plan view, side elevation, Section A-A, headstock, split-diamond inlay and the full specification block all intact |

Artifact: `CMP_Gibson-SG-Custom_baseline_noborder.dxf` (60.7 MB, 455,545 entities), rendered
as `CMP_Gibson-SG-Custom_noborder.png`.

**Sequencing.** This is a follow-on, not a precondition. Ship the fallback first; add border
removal as a post-extraction stage once the fallback is stable. Do **not** fold it into the
extraction path — that is precisely the mistake `f49ead1d` made.

**Known cost, and it is solved.** The obvious `ezdxf` implementation costs a full document
round-trip to delete ~2% of entities: **122 s** on 462k entities, and still running past **1,300 s**
on a 1M-entity file. Unusable as a pipeline stage.

`strip_border_streaming.py` (beside this order) does the same job on the DXF text. An R12 `LINE`
is a fixed group-code block, so the file is scanned for its `10/20/11/21` pairs without building
a document — one pass for the bounding box, one to copy through minus the border blocks.
Everything else, including non-`LINE` entities, passes through untouched.

Measured on the same 81.5 MB / 567,692-entity file: **15.1 s**, roughly **8× faster**, identical
rule and identical result.

**One caveat, found by rendering what it removed rather than trusting the percentage.** Border
share is not constant by document family:

| Sheet | Border share | Why |
|---|---:|---|
| Gibson SG Custom | 1.41% | plain frame |
| Cuatro | 2.22% | plain frame |
| Fender headstock page | **14.52%** | frame **plus a dense perimeter ruler scale** |

The Fender removal is correct — it is frame furniture — but at that margin the rule also clipped
two edge-adjacent dimension annotations ("least nut width", "7.06"). **Verify by rendering the
removed set, not by reading the percentage.** `--margin` should be tuned per sheet family, and a
frame-detection pass would be better than a fixed margin if this becomes a product stage.

## 8. Out of scope

- **D-12** — `set_document_bounds()` is a no-op on ezdxf 1.4.2, so every DXF ships `1e+20`
  extents and opens on a blank canvas. Affects both paths. Separate fix (`zoom.extents`).
- **D-15** — `cv2.imread` fails on non-ASCII paths, so a plan named `cuatro puertoriqueño.png`
  cannot be processed and the product blames the user's file. Separate fix (`cv2.imdecode`).
- Routing blueprints away from a photo-oriented extractor altogether. A larger question; this
  order restores the behaviour that was praised, it does not re-architect the lane.

## 9. Record correction this order implies

**D-13** in `docs/audit/VECTORIZER_PROVENANCE_FORENSIC_2026-09-17.md` — "Phase 3 certifies the
sheet border as the body" — was filed on 2026-09-18 as a new finding. It is not. It is this
April regression reproducing on a different plan. **D-10** (cuatro neck certified `accept` at
0.745) is likely the same root cause. Both should be re-pointed at `f49ead1d` rather than
carried as independent defects.

---

**Standing.** This is an order, not an authorization to merge. No code has been changed. The
measurements above are reproducible from the scripts and artifacts named in §3.
