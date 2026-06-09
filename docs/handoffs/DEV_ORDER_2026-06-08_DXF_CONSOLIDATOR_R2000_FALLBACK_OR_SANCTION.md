# DEV ORDER (DRAFT) — dxf_consolidator R2000: make R12-safe via fallback, OR sanction as bucket ①

**Created:** 2026-06-08
**Status:** DRAFT — carries the spec, the sites, and the **decision fork**; the fork itself
(Option A vs B) is an **unmade architectural call for the codeowner.** Do NOT execute until the fork
is resolved; resolving it rewrites the Scope section below.
**Repo:** `luthiers-toolbox`
**Branch (when executed):** off `origin/main`. Stage by explicit path; hold at push.
**Origin:** spun out of `DEV_ORDER_2026-06-04_R2000_BUCKET2_REVERT.md` Scope #2, which was reclassified
from "revert to R12" to **ESCALATE** during execution (PR #91, merged 2026-06-08): a literal R12 revert
breaks the consolidator because it writes LWPOLYLINE unconditionally and R12 cannot hold LWPOLYLINE.

---

## Why this exists

The bucket-② revert (PR #91) cleanly reverted the one *ungated default* (`dxf_exporter.py:46`,
R2000→R12) — safe because that exporter is version-adaptive and already emits R12-style entities by
default. It then **escalated** the consolidator, because `dxf_consolidator._write_output` calls
`add_lwpolyline()` **unconditionally** (`:306`); ezdxf cannot place LWPOLYLINE in an R12 document, so
the "revert to R12" instruction was not executable — it would break the consolidator at runtime and
re-create the malformed R12+LWPOLYLINE class the R12 gate exists to prevent.

So the consolidator's R2000 is **not the same kind of thing** as the exporter's was. The exporter's was
a rogue *default* on a tier-facing path. The consolidator's is a *functional requirement* of an
internal pipeline stage whose entire job is producing LWPOLYLINE. This dev order decides what to do
about that — and the right answer depends on **who consumes the output**, which is an evidence question,
not a preference.

---

## The sites (confirmed present on main @ `de1d150c`, 2026-06-08)

| Site | What it does | Exposure |
|---|---|---|
| `cam/dxf_consolidator.py:247` (`create_document(version="R2000")`), `:281` (lifecycle assertion `dxf_version="R2000"`), writes LWPOLYLINE at `:306` | Converts raw vectorizer LINE dumps → clean LWPOLYLINE per layer. `DxfConsolidator` class (`:85`), convenience instantiation `:319`. | Vectorizer → **IBG** (InstrumentBodyGenerator, Sprint 9). Internal pipeline. `COMPAT_ONLY`, `pipeline_stage`, `provenance_status=NO`. |
| `cam/layer_consolidator.py:183` (R2000 created **conditionally**, `if is_r12:`, for LWPOLYLINE output), `:247` (lifecycle assertion) | Twin consolidator — LINE→LWPOLYLINE per layer; only creates a new R2000 doc when the *source* is R12. | Imported only by `instrument_geometry/body/ibg/instrument_body_generator.py:50`. IBG-internal. |
| `routers/blueprint_cam/contour_reconstruction.py:375, :461` (`create_document(version="R2000")`); saves `governed_doc_saveas(..., dxf_version="AC1015")` | Reconstructs LWPOLYLINE contours / bracing from blueprint DXF. | **Router-exposed** (`routers/blueprint_cam/`). The one site where free-tier reachability must be checked directly. |

**Note on relationship to the excluded Surface-D path:** these live in `services/api/app/cam/` and
`routers/blueprint_cam/`, NOT the bucket-② Excluded `services/blueprint-import/` path. They are
adjacent to the blueprint/vectorizer pipeline but are not the Surface-D `dxf_compat`/`set_document_bounds`
stream. Treat them as their own surface.

---

## STEP 1 — the audit that decides the fork (do this FIRST; it picks A or B)

**The fork is resolved by one evidence question: is any of the three sites reachable from a free-tier
user-facing DXF export?**

- Enumerate the call chains from each site upward to an HTTP route. `contour_reconstruction.py` is
  router-exposed — trace its router(s) and any tier gate. `DxfConsolidator`/`LayerConsolidator` are
  IBG-internal — confirm they terminate in IBG body-generation artifacts, not a tier-facing download.
- For each reachable route, determine the tier context (free vs `_is_pro`/paid gate), the way
  bucket-① sites (`api_v1/fretboard.py` gated on `_is_pro`) are gated.

**Decision rule:**
- **If NO site is free-tier-reachable** (all are internal pipeline / paid-gated) → **Option B (sanction).**
  R2000 here is legitimate by construction; the work is to *document* it, not change it.
- **If ANY site is free-tier-reachable** → **Option A (make R12-safe)** for that site at minimum, because
  a free-tier consumer must get R12-legal output.

State the audit result and the chosen option in the PR. This is the single decision-laden step; it
escalates to the codeowner if reachability is ambiguous.

---

## The fork — two real options (codeowner's call, informed by STEP 1)

### Option A — make the consolidators version-adaptive (R12-safe)

Add the same kind of version awareness `dxf_exporter` has, so an R12 target emits **R12-legal entities**
instead of LWPOLYLINE.

- **Tension to resolve, not ignore:** the consolidator's *purpose* is LINE→LWPOLYLINE. R12-legal output
  means either (a) **old-style `POLYLINE`/VERTEX** (R12-legal, preserves the closed-chain semantics, but
  heavyweight), or (b) **LINE chains** (matches this repo's stated R12 convention — CLAUDE.md: "Free tier
  output: R12, LINE entities only" — but that partially *un-does* the consolidation the stage exists to
  perform). Pick (a) or (b) explicitly; (a) preserves contour semantics, (b) matches house R12 style.
- Cost: real new logic in three places (plus the lifecycle assertions at `:281`/`:247` must then declare
  the *actual* emitted version, not a hardcoded `"R2000"`).
- When this is right: a free-tier path genuinely consumes consolidator output.

### Option B — formally sanction the R2000 dependency as bucket ①

Recognize these as legitimately-R2000 internal/paid stages and **document** them as bucket-① sanctioned,
the way paid-tier R2000 is already sanctioned in CLAUDE.md (verified safe for DWG TrueView 2026-04-28).

- Work: add these sites to the bucket-① sanctioned inventory; correct the misleading comments (e.g.
  `dxf_consolidator.py:246` "Use R2000 for LWPOLYLINE support" is fine, but ensure nothing reads as
  rogue/ungated); confirm via STEP 1 they're not on a free-tier path; leave the code as-is.
- Cost: near-zero code; the value is removing the "is this rogue R2000?" ambiguity permanently.
- When this is right: STEP 1 shows no free-tier reachability — the likely outcome given all three are
  vectorizer/IBG pipeline stages producing LWPOLYLINE by design.

**Drafter's read (NOT the decision):** the evidence so far leans **B** — all three are LWPOLYLINE-by-design
pipeline stages, `COMPAT_ONLY`, and the two consolidators are IBG-internal. But `contour_reconstruction`
is router-exposed, so B is only safe if STEP 1 confirms that router is not a free-tier export. If it is,
that one site needs A while the other two take B. A split outcome (B for the two IBG-internal, A for the
router site) is legitimate and likely.

---

## Twin & scope-call sites (handle within this order, per STEP 1 result)

- `layer_consolidator.py:183/247` — the twin the cross-repo inventory missed; same disposition as
  `dxf_consolidator` (it's IBG-internal, so almost certainly B).
- `contour_reconstruction.py:375/461` — the explicit in/out scope call; its router exposure is exactly
  what STEP 1 resolves.

---

## Verification bar (when executed)

1. **STEP 1 audit documented** — reachability + tier context for all three sites, decision rule applied.
2. **If Option A:** consolidator tests collect + pass with R12 target producing R12-legal entities
   (no LWPOLYLINE in an R12 doc); lifecycle assertions declare the actual emitted version. Add a test
   that an R12 request does NOT emit LWPOLYLINE.
3. **If Option B:** sites added to the bucket-① sanctioned inventory; a test or assertion that pins the
   R2000 dependency as *intentional* (so a future "revert" session doesn't re-escalate it); comments
   corrected to read sanctioned, not rogue.
4. **Hold at push** for the codeowner. Branch + PR, explicit-path. No force, no `--no-verify`.

---

## Context pointers

- Parent order (Scope #2 escalation, now ESCALATE on main): `docs/handoffs/DEV_ORDER_2026-06-04_R2000_BUCKET2_REVERT.md`.
- Bucket split (①/②/③) + full R2000 inventory: produced 2026-06-04 against `luthiers-toolbox-clean`;
  bucket-② re-confirmed in `luthiers-toolbox` 2026-06-06/07.
- Squash-merge verify gotcha (applies to any execution here): verify content on main via the squash
  commit / PR state, NOT `--is-ancestor` on the original branch SHA.

---

*DRAFT. The fork (A vs B, possibly split) is unresolved and is the codeowner's architectural call,
to be made with STEP 1's evidence. No source modified. No branch cut. Not committed.*
