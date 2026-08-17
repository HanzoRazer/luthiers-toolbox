# Body Outline Editor — Build Resumption Dev Handoff

**Date:** 2026-08-16
**Namespace:** `BOE` — *Body Outline Editor · Production* (`docs/governance/SPRINT_NAMESPACE_STANDARD.md`)
**Baseline:** `main` @ `114cef1a`
**Artifact:** `hostinger/body-outline-editor.html` — v3.5.0, 6,150 lines
**Status of this doc:** every figure below was verified against `main` on the date above, not carried from prior notes. Where a repository record disagrees, that is called out.

---

## 0. Read this first — two things are not what the records say

**A. A merged PR's work is missing from `main`.** PR #270 (jumbo consistency coverage) was stacked on `docs/boe-changelog`. Its base merged to `main` at 19:10Z; #270 then merged **into that already-merged base** at 20:57Z. Its merge commit `b510ae54` is **not an ancestor of `main`**. The work is intact on the branch and recoverable — see §2 (P0).

**B. `SPRINTS.md:2323` is stale.** It lists *"Body Outline Editor (BOE) — backend endpoint claim (Sprint 3) marked MISSING"*. The endpoint exists and is mounted. See §4.

---

## 1. Artifact inventory (verified on `main` @ `114cef1a`)

| Artifact | State | Notes |
|---|---|---|
| `hostinger/body-outline-editor.html` | 6,150 lines | **Canonical.** Deployed to `theproductionshop.app/body-outline-editor.html`; linked from the hub's Free Tools grid since PR #268 |
| `tools/body-outline-editor.html` | 5,979 lines | **Stale mirror** — byte-identical to `hostinger/` @ `70a0d3ee` (2026-05-12) once CRLF is normalised. 171 lines behind |
| `docs/Body_Outline_Editor_User_Manual.md` | v3.5.0 | Ch. 7 Jumbo row corrected in #269 |
| `docs/Body_Outline_Editor_Quick_Start.md` | 105 lines | |
| `docs/Body_Outline_Editor_CHANGELOG.md` | current | Reconstructed history v3.1.0→v3.5.0; merged #269 |
| `docs/api/body_solver_openapi.yaml` | OpenAPI 3.0 | Body Solver contract |
| `services/api/app/routers/body_solver_router.py` | **live** | Mounted — see §4 |

### The version stamp does not identify a build

Both HTML files carry the identical comment on line 7:

```html
<!-- v3.5.0 - Final Polish (Precision Tier Complete) -->
```

They are 171 lines apart and their Jumbo dimensions disagree by 26 mm at the waist. Separately, `hostinger/` is **193 lines ahead** of the v3.5.0 release commit — three commits landed after the stamp without a bump (`70a0d3ee` IBG config, `c971d7a4` JSON import, `f25bb949` jumbo alignment). Do not use the stamp to identify what you are running.

---

## 2. Work queue, prioritised

### P0 — Recover PR #270 (lost coverage work)

The jumbo consistency guard on `main` is the **original 4-path version, 120 lines**. The 7-path version with the namespace-completeness guard never landed.

```
main                                  120 lines, 4 guarded paths
origin/test/jumbo-consistency-coverage  @ 7c62ad2f — full version intact
```

Recover by cherry-picking `7c62ad2f` onto `main` and opening a fresh PR to `main` (**not** to a stacked base). Expect it to apply cleanly — the detector-adjacent files it touches are unchanged on `main`.

> **Process lesson worth encoding:** the stacked PR merged into a base that had already merged. Retarget stacked PRs to `main` the moment their base merges, and verify with
> `git merge-base --is-ancestor <mergeCommit> origin/main` before calling a stacked PR done.

### P1 — Family dimension drift is not limited to jumbo

The Jumbo drift that motivated #269/#270 is **an instance, not the problem.** Comparing canonical `FAMILY_DEFAULTS` (`body_contour_solver.py`) against the editor's `INSTRUMENT_TEMPLATES`:

| Family | Canonical L/LB/UB/W | Editor template | Status |
|---|---|---|---|
| **jumbo** | 530 / 432 / 305 / 254 | 530 / 432 / 305 / 254 | ✅ **ALIGNED** |
| **dreadnought** | 520 / 381 / 292 / 241 | 508 / 394 / 286 / 254 | ❌ all four differ, up to ±13 mm |
| **stratocaster** | 406 / 332 / 311 / 250 | 400 / 318 / 166 / 220 | ❌ upper bout off by **145 mm** |

**Jumbo is aligned precisely because someone wrote a test for it.** The two other families present in both sources are both wrong, and nothing guards them.

Two different problems are hiding here:

- **dreadnought** looks like ordinary drift — small deltas, same measurement intent. Likely alignable to canonical.
- **stratocaster's** 311 → 166 upper bout is too large to be drift. That is almost certainly a **definitional** difference (upper bout on an offset solid body is not the same measurement as on a flat-top). **Investigate the definition before aligning anything** — forcing 166 → 311 would encode a wrong number with high confidence.

Deliverable: generalise the guard from `test_jumbo_dimension_consistency.py` to every family present in both sources, after resolving the stratocaster definition.

### P2 — Version identity

1. Bump the line-7 stamp, or roll the three unreleased commits into **v3.6.0**.
2. Give the two artifacts **distinguishable** stamps if they are meant to stay separate — today "v3.5.0" names two different builds.

### P3 — `tools/` mirror resync — **GOVERNED**

`docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` marks `tools/body-outline-editor.html` **Production / MEDIUM / "Avoid collision"**.

Mechanically it is trivial — a clean unmodified snapshot, so the resync is a copy plus line-ending normalisation with nothing to reconcile. **Mechanical is not the same as ungoverned.** It needs its own change and its own approval; do not fold it into a feature or docs PR.

### P4 — Documentation gaps

| Gap | Location |
|---|---|
| JSON **import** undocumented (added `c971d7a4`; editor could previously export but never reload) | Manual Ch. 8 |
| `IBG_CONFIG` / URL-param overrides undocumented | Manual Ch. 9 |
| `[INTERNAL_ACCESS_NOTE]` placeholders — **7 remaining** | Manual ×2, Quick Start ×4, `body_solver_openapi.yaml` ×1 |

The placeholders are now trivially closable: PR #268 gave the editor a hub entry point, so there is a real URL to name.

---

## 3. Architecture orientation

Single self-contained HTML file. One external dependency — **paper.js 0.12.18 from cdnjs** — so it needs network access but no build step, no bundler, and no dev server.

**Entry point.** A full-screen `#mode-dialog-overlay` on load: *Default Mode* (8-node dreadnought starter) or *Empty Mode* (place every node manually).

**Key structures**

| Symbol | Line | Role |
|---|---|---|
| `INSTRUMENT_TEMPLATES` | — | The 8 built-in body templates and their dimensions |
| `class InstrumentBodyAPI` | 918 | Body Solver client — config resolution, solve, session I/O |
| `_mockSolve` path | ~1036 | Fallback outline generator used when mock mode is on |

**Client persistence** (`localStorage`)

| Key | Contents |
|---|---|
| `body_outline_autosave` | Full session incl. `editorMode` and `emptyModeDots` |
| `ibg_api_key` | Body Solver credential |
| `ibg_last_session` | Last solver session id |

**Panels:** `#image-panel`, `#layers-panel`, `#templates-panel`, `#measurements-panel`.
**Modals:** `#modal-calibrate`, `#modal-coord`, `#modal-void`, `#modal-export`, `#modal-confirm`.

> ⚠️ The mock outline generator hardcodes its own dimensions (`dreadnought ? 381 : 250`, `bodyLength = dreadnought ? 520 : 350`). These match `instrument_body_generator.py`'s `expected_dimensions`, **not** the editor's own template table — a third dimension source inside one file. Fold it into whatever P1 produces.

---

## 4. Backend integration — it exists

`services/api/app/routers/body_solver_router.py`, mounted through the router registry at
`app/router_registry/manifests/cam_manifest.py:364` (`tags=["Body Solver", "IBG"]`).

| Endpoint | Tier |
|---|---|
| `POST /api/body/solve-from-dxf` | free |
| `POST /api/body/solve-from-landmarks` | paid |
| `GET /api/body/session/{session_id}` | — |
| `PUT /api/body/session/{session_id}/landmarks` | paid |

**The editor defaults to mock mode**, resolved as
**constructor arg → URL param → `window.IBG_CONFIG` → default**:

| Setting | URL param | Config key | Default |
|---|---|---|---|
| Base URL | `?ibg_api_url=` | `IBG_CONFIG.apiUrl` | `/api` |
| Mock mode | `?ibg_mock=false` | `IBG_CONFIG.useMock` | `true` (fail-safe) |

So the *first* live-backend task is not building the endpoint — it is deciding how the deployed editor is pointed at a real API and how the key is provisioned, given `ibg_api_key` currently lives in `localStorage`.

---

## 5. Governance constraints

| Constraint | Effect on this work |
|---|---|
| `BOE` is a **Production** sprint namespace | Changes carry production expectations |
| `tools/` mirror: Production / MEDIUM / *"Avoid collision"* | Resync needs its own approved change (P3) |
| `BOE_IBG_FAMILY_CONFLATION.md` (merged #77) | Lineage descriptors — *dreadnought, jumbo, OM, parlor* — are **Model metadata, not a taxonomy tier**. Target is `Type → Brand → Model`; re-architecture **deferred post-MVP**. The 8-template grid is current behaviour, **not** endorsed taxonomy — do not build new structure on it |
| CBSP21 | Every PR needs its own manifest at `.cbsp21/patches/<patch-id>.json`, including docs-only |
| DXF policy in `CLAUDE.md` | The editor's R12/R2004+ export selector is **client-side and separate** from the `dxf_compat` free/paid tier policy. Two independent mechanisms — do not conflate |

---

## 6. Build & verify loop

```bash
# Run it — no build step. Open directly:
#   file:///C:/Users/thepr/Downloads/luthiers-toolbox/hostinger/body-outline-editor.html
# or via the hub card added in #268.

# Point at a live backend instead of mock:
#   body-outline-editor.html?ibg_mock=false&ibg_api_url=https://<host>/api

# Dimension consistency (currently jumbo-only, 4 paths — see P0):
cd services/api && py -3.11 -m pytest tests/test_jumbo_dimension_consistency.py -q --no-cov

# Body solver router:
cd services/api && py -3.11 -m pytest tests/ -q --no-cov -k body_solver

# CBSP21 gates before opening any PR:
py -3.11 scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
py -3.11 scripts/ci/check_cbsp21_gate.py --changed-files <changed file set>
```

**In-browser console helpers** (documented in Manual Appendix B): `testAll()`, `testBackendAPI()`, `testTemplate(id)`, `testLandmarks()`, `testWeightedMirror()`, `testSelfIntersection()`.

---

## 7. Recommended sequence

1. **P0** — recover #270 onto `main`. Cheap, and it restores the guard everything else leans on.
2. **P1a** — resolve the **stratocaster upper-bout definition**. Blocks any alignment work; a decision, not a code change.
3. **P1b** — align dreadnought, fold in the mock generator's hardcoded dimensions, generalise the guard to all families.
4. **P2** — version stamp / v3.6.0, with distinguishable identities for the two artifacts.
5. **P3** — `tools/` resync as its own governed change.
6. **P4** — documentation gaps; the `[INTERNAL_ACCESS_NOTE]` placeholders are now trivially closable.

---

## 8. Decisions needed from the owner

1. **Stratocaster upper bout — 311 or 166?** Which is the correct measurement definition for an offset solid body? Everything in P1 waits on this.
2. **Is `tools/` still a supported artifact,** or should it be retired rather than resynced? It has been stale since May and nothing observed in this session reads it.
3. **v3.6.0 scope** — a version bump alone, or bundle P1/P4 into a release?
4. **Live-backend posture** — should the deployed editor stay mock-default, and how is `ibg_api_key` provisioned if not?

---

## 9. Provenance

Verified during preparation of this document, against `main` @ `114cef1a`:

- Line counts and version stamps read from both HTML artifacts.
- `#270` non-ancestry confirmed via `git merge-base --is-ancestor b510ae54 origin/main` → false; `main`'s guard confirmed at 120 lines with zero coverage markers.
- Family dimensions compared numerically (not as strings) between `FAMILY_DEFAULTS`, `INSTRUMENT_SPECS.expected_dimensions`, and the editor's `INSTRUMENT_TEMPLATES`.
- Router mounting traced to `cam_manifest.py:364`; endpoint list read from the router source.
- `tools/` staleness confirmed as a clean snapshot — `diff` against `hostinger/` @ `70a0d3ee` is 0 lines after CRLF normalisation.
- Placeholder counts read per file.

Related: [Body_Outline_Editor_CHANGELOG.md](../Body_Outline_Editor_CHANGELOG.md) ·
[Body_Outline_Editor_User_Manual.md](../Body_Outline_Editor_User_Manual.md) ·
[BOE_IBG_FAMILY_CONFLATION.md](../architecture/BOE_IBG_FAMILY_CONFLATION.md)
