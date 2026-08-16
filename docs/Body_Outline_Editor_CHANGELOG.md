# Body Outline Editor — Changelog

**Artifact:** `hostinger/body-outline-editor.html`
**Sprint namespace:** `BOE` — *Body Outline Editor · Production* (`docs/governance/SPRINT_NAMESPACE_STANDARD.md`)
**Compiled:** 2026-08-16, reconstructed from git history against `main` @ `c8b0b549`. This file did not exist before.

> The editor carries no changelog of its own. Its only version marker is a single
> HTML comment on line 7:
>
> ```html
> <!-- v3.5.0 - Final Polish (Precision Tier Complete) -->
> ```
>
> Everything below is recovered from commit messages and verified against diffs
> and per-commit line counts. The **Precision Tier** is the release series
> v3.2.0–v3.5.0, named and closed by commit `8c3be18b`.

> ### ⚠️ This version line is not the platform version line
>
> The editor's `v3.x` numbering is **independent of** the repository's
> `CHANGELOG.md`, which tracks the platform as `toolbox-vX.Y.Z` (currently in the
> `toolbox-v0.x` range). `v3.5.0` is a *Body Outline Editor* version and has no
> relationship to any `toolbox-v*` release. Do not cross-reference the two.

---

## ⚠️ Current state: shipped file is ahead of its version stamp

The file still reads **v3.5.0**, but three commits have changed it since that
release — **+193 lines**, including a behavioural change to API configuration and
a template dimension correction.

| | Lines | |
|---|--:|---|
| v3.5.0 as released (`8c3be18b`) | 5,957 | version stamp set here |
| Current on `main` (`c8b0b549`) | 6,150 | stamp still says v3.5.0 |

Anything identifying the build from the line-7 comment will be wrong. See
[Unreleased](#unreleased--after-v350).

---

## Version summary

| Version | Date (2026) | Commit | Lines | Δ | Theme |
|---------|-------------|--------|------:|---:|-------|
| v3.1.0 | 04-21 23:06 | `a50a347c` | 4,247 | — | Empty mode, drag-to-refine *(pre-tier baseline)* |
| **v3.2.0** | 04-22 00:19 | `886184d8` | 4,469 | +222 | Precision Controls + Workflow |
| **v3.3.0** | 04-22 00:52 | `a0d5f216` | 5,071 | +602 | Image Tools & Templates |
| **v3.4.0** | 04-22 01:17 | `b79e29f5` | 5,875 | +804 | Measurement & Enhanced Export |
| **v3.5.0** | 04-22 01:23 | `8c3be18b` | 5,957 | +82 | Final Polish — *Precision Tier complete* |
| *(unversioned)* | 05-12 → 05-27 | 3 commits | 6,150 | +193 | IBG config, JSON import, jumbo fix |

The entire Precision Tier landed in **64 minutes** on 2026-04-22, growing the
editor by 1,710 lines (+40%).

---

## Namespace and boundary notes

The editor is legacy relative to the systems that have grown around it. Six
points where its namespace now overlaps something newer:

### 1. Two files claim to be v3.5.0 and are different builds — ⚠️ unresolved

**Both** `hostinger/body-outline-editor.html` and `tools/body-outline-editor.html`
carry the identical stamp on line 7:

```html
<!-- v3.5.0 - Final Polish (Precision Tier Complete) -->
```

They are not the same file:

| | Lines | Jumbo (L/LB/UB/W) | Content is |
|---|--:|---|---|
| `hostinger/body-outline-editor.html` | 6,150 | 530/432/**305**/**254** ✅ | current `main` |
| `tools/body-outline-editor.html` | 5,979 | 530/432/**304**/**280** ❌ | `hostinger` @ `70a0d3ee`, 2026-05-12 |

So the version stamp does not identify a build. It is stale on `hostinger/`
(193 lines behind, see the warning above) **and** duplicated onto a second,
different artifact — meaning "v3.5.0" currently names two distinct files whose
Jumbo dimensions disagree by 26 mm at the waist.

**The mirror is a clean lag, not a fork.** `tools/` is byte-identical to
`hostinger/` at commit `70a0d3ee` once CRLF/LF is normalised (`diff` → 0 lines);
the raw hash difference is line endings only. It carries no independent edits.
It is **171 lines behind**, missing exactly two commits: `c971d7a4` (JSON import) and
`f25bb949` (jumbo alignment). `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md`
marks it **Production**, risk **MEDIUM**, disposition *"Avoid collision"* — so
resyncing it is a governed change, not a copy. **Not addressed here.**

### 2. Jumbo is a six-path namespace; only four are guarded

`services/api/tests/test_jumbo_dimension_consistency.py` enforces agreement
across four paths (currently **4 passed, 1 skipped**):

| Path | Guarded | State |
|------|:---:|---|
| `body_contour_solver.py` → `FAMILY_DEFAULTS["jumbo"]` | ✅ | **canonical** — 530/432/305/254, `waist_y_norm` 0.44 |
| `app/instrument_geometry/guitars/jumbo_j200.py` | ✅ | aligned |
| `app/instrument_geometry/instrument_model_registry.json` | ✅ | aligned |
| `hostinger/body-outline-editor.html` | ✅ | aligned |
| `tools/body-outline-editor.html` | ❌ | **stale** — see above |
| `docs/Body_Outline_Editor_User_Manual.md` | ❌ | **corrected in this change** |
| `catalog.json` | — | known-unaligned; test explicitly skipped (DXF bbox, not body dims) |

### 3. Template names are lineage-tier, which governance has demoted

`docs/architecture/BOE_IBG_FAMILY_CONFLATION.md` (merged, PR #77) rules that
lineage descriptors — *dreadnought, jumbo, OM, parlor, archtop, slope-shouldered* —
are **Model metadata, not a taxonomy tier**, and that the target hierarchy is
`Type → Brand → Model`. The editor's 8-template grid is exactly the
"dreadnought/jumbo/OM grid" that document argues against.

Status there is **NAMED, re-architecture deferred post-MVP**. So the template
list below is *current behaviour*, not endorsed taxonomy. Do not treat it as the
canonical instrument model.

Related: the editor's generic **"Jumbo"** template now draws its dimensions from
`FAMILY_DEFAULTS["jumbo"]`, which is identical to the specific Gibson J-200
model (`jumbo_j200`, status `ASSETS_ONLY`) — an instance of the same conflation.

### 4. Web entry point now exists — `[INTERNAL_ACCESS_NOTE]` partly obsolete

PR **#268** (`c8b0b549`, 2026-08-15) added a Body Outline Editor card to the Free
Tools grid in `hostinger/production-shop-hub.html`, placed after Blueprint Reader
(scan/import → edit). Before that the editor had no web entry point at all.

The manual and Quick Start still use `[INTERNAL_ACCESS_NOTE]` placeholders where
the URL should be; the hub card is now the intended route in.

### 5. CBSP21 patch-id space

Existing BOE patch id: `boe-landing-page-entry` (PR #268). This change uses
`boe-changelog`. No collision.

### 6. `"Final Polish"` also exists in the estimator — harmless

A repo-wide search for the release name returns a second, unrelated hit:

```
services/api/app/business/estimator/work_breakdown.py:158
    WBSTaskTemplate("FIN_004", "Final Polish", 2.0, "finish", "finish"),
```

That is a lutherie **finishing** work-breakdown task, not a software release
name. Different domain, no shared identifier, nothing to reconcile — recorded
only so a future search for the release name is not misread. Outside those two,
`"Final Polish"` and `"Precision Tier"` appear nowhere else in the repository
(excluding build artifacts: `__pycache__`, `htmlcov/`).

---

## Unreleased — after v3.5.0

Three commits changed the editor without a version bump. None is documented in
the User Manual.

### `f25bb949` — 2026-05-27 · fix(ibg): align jumbo dimensions across four definition paths

**Changed — Jumbo template dimensions**, synced to canonical IBG `FAMILY_DEFAULTS["jumbo"]`:

| Field | Was | Now |
|-------|----:|----:|
| `upperBout` | 304 | **305** |
| `waist` | 280 | **254** |
| `waistYNorm` | 0.45 | **0.44** |

The manual was not updated at the time — a 26 mm waist discrepancy. **Corrected
in this change.** The other seven templates were re-verified and match.

### `c971d7a4` — 2026-05-13 · feat(mrp): MRP-2C/2D morphology spine verification complete

**Added** — JSON round-trip import (+178 lines): `importJSON()`, `loadBOEJson()`,
the `#btn-import-json` control, and a reworked `exportJSON()` to pair with it.

Previously the editor could export JSON but never reload an outline from it.
Not covered by Manual Chapter 8.

### `70a0d3ee` — 2026-05-12 · feat(ibg): IBG-2B production infrastructure enablement

**Changed** — the Body Solver API client is configurable instead of hardcoded.
Resolution order for both settings is
**constructor arg → URL param → `window.IBG_CONFIG` → default**:

| Setting | URL param | Config key | Default |
|---------|-----------|------------|---------|
| Base URL | `?ibg_api_url=` | `IBG_CONFIG.apiUrl` | `/api` |
| Mock mode | `?ibg_mock=false` | `IBG_CONFIG.useMock` | `true` (fail-safe) |

Mock mode still defaults **on**. Manual Chapter 9 documents mock mode but not
these overrides.

---

## v3.5.0 — Final Polish · 2026-04-22

`8c3be18b` · 5,957 lines (+92 / −10) · **Precision Tier (v3.2.0–v3.5.0) complete**

### Added
- `Ctrl+Shift+M` — clear all measurements
- Double-click a measurement list item to add an annotation
- Export settings persisted via `localStorage`

### Changed
- Improved tooltips on the measurement buttons (distance, angle, arc, clear)
- Version references updated throughout

**Companion docs** — `118e7850`, same day 02:07:

| Document | Change |
|----------|--------|
| `docs/Body_Outline_Editor_User_Manual.md` | Rewritten for v3.5.0 (+1,461 / −910) |
| `docs/Body_Outline_Editor_Quick_Start.md` | New — 105 lines |
| `docs/Smart_Guitar_Body_Outline_Workflow.md` | New — 178 lines; corrected dimensions (444.5 mm length, 368.3 mm width) |
| `docs/api/body_solver_openapi.yaml` | New — OpenAPI 3.0 spec, renamed from IBG API per ADR |

All four use `[INTERNAL_ACCESS_NOTE]` placeholders in place of URLs — never
filled in. See namespace note 4.

---

## v3.4.0 — Measurement & Enhanced Export · 2026-04-22

`b79e29f5` · 5,875 lines (+812 / −8) · largest release of the tier

### Added — Measurement tools
- Persistent distance measurement (click two points; annotation stays on canvas)
- 3-point angle measurement with arc visualisation
- Arc-length measurement along curves, by numerical integration
- Measurements panel with a visibility toggle
- Delete individual measurements, or clear all
- Unit conversion — mm / inches / points

### Added — Export
- DXF export options dialog
- Format selector: **R12 legacy** vs **R2004+ modern**
- Tessellation density control, 10–100 points per curve
- Layer naming: standard vs CAM-ready
- Optional inclusion of measurements as DXF `TEXT` entities
- Optional inclusion of voids
- SVG export with measurement annotations

> **Boundary note.** This R12/R2004+ selector is the editor's own client-side
> control. It predates and is separate from the repository's dual-format DXF
> policy in `CLAUDE.md` (R12 free tier / R2000 paid tier via `dxf_compat`), and
> does **not** route through `dxf_compat`. Two independent mechanisms.

---

## v3.3.0 — Image Tools & Templates · 2026-04-22

`a0d5f216` · 5,071 lines (+605 / −3)

### Added — Image layers
- Multiple layered reference images with z-order control
- Per-layer opacity, visibility and lock
- Layer management UI: add, delete, reorder up/down
- Layers panel in the right sidebar

### Added — Image transformations
- 90° rotation, left and right
- Free rotation slider, 0–360° continuous
- Non-uniform scaling by horizontal/vertical drag
- Uniform scaling with `Shift` held (aspect lock)

### Added — User templates
- Save an image plus its transforms as a user template (`localStorage`)
- Load user templates from a dropdown
- Templates panel in the right sidebar
- Storage-size warning above 4.5 MB

### Added — Workflow
- Hold `Shift` during a drag to temporarily disable snapping

---

## v3.2.0 — Precision Controls + Workflow · 2026-04-22

`886184d8` · 4,469 lines (+246 / −24) · *Phase 2.1* — opens the Precision Tier

### Added — Precision
- Sub-millimetre snap: 0.1 mm and 0.5 mm added to the snap dropdown
- Nudge amount selector: 0.1 / 0.5 / 1.0 mm
- 3-decimal coordinate display throughout the UI

### Added — Node editing
- Smooth with revert — stores pre-smooth state so it can be undone
- Reset handles to linear — strips all Bezier handles

### Added — Mode handling
- Exit-mode button, shown during calibrate and measure
- Mode indicator in the status bar: Ready / Calibrate / Measure / Empty
- `Esc` exits calibrate and measure modes
- Auto-reset to empty mode after calibration or measurement

### Added — Infrastructure
- Operation-logging foundation: `logOperation`, state snapshots

New functions: `smoothWithRevert`, `revertSmooth`, `resetHandlesToLinear`,
`updateActiveModeIndicator`, `exitCurrentMode`, `showToast`, `logOperation`.

---

## v3.1.0 — pre-tier baseline · 2026-04-21

`a50a347c` · 4,247 lines · the state the Precision Tier built on. Shipped inside
a mixed commit that also carried a vectorizer audit and IBG handoff material.

### Added
- **Empty mode** with click-to-place dots — the second option on the launch dialog
- Drag-to-refine interaction model
- Auto-save serialisation now includes `editorMode` and `emptyModeDots`
- First User Manual

### Fixed
- Zoom behaviour after the calibration modal

---

## Notes on this reconstruction

**Method.** Commit messages for `hostinger/body-outline-editor.html`, cross-checked
against `git show --stat` diffs and per-commit line counts. Template dimensions
were extracted from the current file and compared field-by-field with Manual
Chapter 7. Canonical jumbo values read from `FAMILY_DEFAULTS["jumbo"]`; the
consistency test was executed to confirm the four guarded paths agree.

**Confidence.** High for v3.2.0–v3.5.0 — those four commits carry detailed,
structured bodies. Lower for v3.1.0 and earlier, which are folded into
multi-purpose commits. **No git tags exist for any editor version**; nothing here
is derived from a release tag.

**Not covered.** Versions before v3.1.0.
`docs/handoffs/BODY_OUTLINE_EDITOR_V2_HANDOFF.md` records an earlier V2 era at
2,461 → 3,567 lines, but that period's version numbering was not recovered.

**Open items** — none of these is done here.

### Root cause — do this one first

**1. Extend `test_jumbo_dimension_consistency.py` to cover all six paths.**

The Jumbo drift did not survive because anyone missed it. It survived because
**the guard's coverage set was narrower than the namespace's member set.** Six
artifacts assert Jumbo dimensions; the test asserts four. The drift lived in the
two it does not look at — the User Manual and the `tools/` mirror — and was
invisible to CI for 81 days (`f25bb949`, 2026-05-27 → 2026-08-16).

Fixing the manual (done in this change) fixes *this* instance. It does not stop
the next one. The durable fix is closing the coverage gap, so a Jumbo dimension
cannot drift in any member without failing loudly:

| Path | Guarded today | After |
|------|:---:|:---:|
| `body_contour_solver.py` → `FAMILY_DEFAULTS["jumbo"]` (canonical) | ✅ | ✅ |
| `jumbo_j200.py` | ✅ | ✅ |
| `instrument_model_registry.json` | ✅ | ✅ |
| `hostinger/body-outline-editor.html` | ✅ | ✅ |
| `docs/Body_Outline_Editor_User_Manual.md` | ❌ | **add** |
| `tools/body-outline-editor.html` | ❌ | **add** |
| `catalog.json` | skipped | resolve or document why it is out of scope |

Note the manual states dimensions in prose (`Jumbo — 530/432/305/254`), so
covering it means parsing that line — the test already does regex extraction for
the HTML artifact, so the shape exists. The general principle: **a consistency
guard should enumerate its namespace, not a subset of it.** Any new artifact
that asserts Jumbo dimensions should be added to the test in the same change
that introduces it.

### Remaining

2. **Resync `tools/body-outline-editor.html`** — 171 lines behind, stale jumbo.
   Mechanically simple: it is a clean, unmodified snapshot of `hostinger/` at
   `70a0d3ee`, so the resync is a copy plus line-ending normalisation, with no
   edits to reconcile. **Governed, though** — Production, MEDIUM,
   *"Avoid collision"* — so it wants its own change and its own approval, and
   must not be bundled into a documentation change. Mechanical ≠ ungoverned.
3. Bump the line-7 version stamp, or roll the three unreleased commits into a
   v3.6.0. The stamp currently misidentifies the build **and is duplicated onto
   `tools/`**, so "v3.5.0" names two different files (namespace note 1). If the
   two artifacts are meant to stay separate, they need distinguishable stamps.
4. Document JSON import in Manual Chapter 8.
5. Document the `IBG_CONFIG` / URL-param overrides in Manual Chapter 9.
6. Replace the `[INTERNAL_ACCESS_NOTE]` placeholders — 7 across 3 documents —
   now that PR #268 has given the editor a hub entry point.

---

## Method note — don't trust a raw hash across a line-ending boundary

While preparing this document, `tools/body-outline-editor.html` was initially
reported as **diverged** from `hostinger/` on an MD5 comparison. That was wrong.
The two files' content is identical at `70a0d3ee`; the hash gap was **CRLF vs
LF** and nothing else:

```
md5 (raw)                     tools 370a413f29b7   ≠   hostinger@70a0d3ee 05b4d5029702
diff (line-endings normalised)                     → 0 lines
```

A raw hash comparison across a CRLF boundary reports divergence where there is
none, and it inflated the assessed difficulty of open item 2 from "copy" to
"reconcile a fork". When comparing text artifacts in this repository, normalise
line endings before concluding anything from a hash — or diff the content
directly.
