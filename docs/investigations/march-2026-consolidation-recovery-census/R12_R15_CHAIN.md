# R12/R15 recovery chain — March BACKLOG to the "10/12 false migration claims" finding

Evidence only. Base: `origin/main` `d42712e0`. Nothing here grants production authority. "Migrated", "complete" or
"merged" in any record below means **a record said so**. Each claim is re-checked in `CLAIM_VERIFICATION.csv`.

## Negative search: there is no numbered R-12 or R-15 item

Locations searched for a numbered item "R-12" / "R-15" (or "R12"/"R15" used as an item ID):

| Source | Result |
|---|---|
| `SPRINTS.md`, current and full history (`git log --all -G "\bR-?15\b" -- SPRINTS.md`) | none. Its R-style IDs are R1 (IBG governance), R4a (Inv-037), and R-11 (DEP-SEC-001 matrix) |
| March planning documents (Downloads, 03-14…03-15: `calculator-unification-remediation*.md`, `migration-plan.md`, `tightened-migration-scope.md`, `engineering-session-summary.md`, `frontend-backend-mapping.md`, `guitar-assembly-tools-inventory.md`) | remediation tasks **R-1 … R-8 only** |
| Consolidation Lab `origin/main` (outside `reference/`) | order/ruling series **R0 … R8** only |
| `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md` | R-01 … R-11 (August dependency security; unrelated) |

All located uses of R12/R15 are **DXF format versions**:
- R12 = AC1009.
- R15 = the alias for R2000/AC1015: `services/api/app/util/dxf_compat.py:15`, `:27` (`'R2000': 'AC1015',  # AutoCAD 2000 (R15)`), and `:55` (`'R15': 'R2000'`).

The negative result is evidence. It does not block the census.

## The chain

Status markers: **D** = direct evidence (a hash or file:line at the base); **I** = inferred sequence; **U** = unresolved.

### 1. March BACKLOG and remediation tasks R-1…R-8
- **D:**
  - The archived March `BACKLOG.md` is `docs/archive/photo_vectorizer_patches/BACKLOG.md`, blob `50022d74`. It arrived in the `files - 2026-03-18T031920.383` bundle and was archived by `73a2703d` on 2026-03-21.
  - HEADSTOCK-001 is at `:169`, VECTORIZER-001 at `:187`, NECK-001 at `:129`, and CAM-SURVEY-001 at `:212`.
- **D:** The remediation tasks R-1…R-7 are in `Downloads/calculator-unification-remediation (1).md`, sha256 prefix `6f24f8f62f29`, at lines 120–271. The fuller list adds R-8, cited in `migration-plan.md` and `tightened-migration-scope.md`.
- **I:** These are calculator/UI tasks, not DXF tasks. The DXF thread starts with HEADSTOCK-001.

### 2. R12/R15 writer and export decisions
- **D:** CLAUDE.md records three dated decisions:
  - R12-only gate on 2026-04-02, after the Fusion 360 LWPOLYLINE freeze.
  - EXTMIN/EXTMAX sentinel removed on 2026-04-25 (`2aaff13f`).
  - R2000 lifted for the paid tier on 2026-04-28.
- **D:** `services/api/app/cam/dxf_writer.py:39` sets `DXF_VERSION_DEFAULT = "R12"` and `:52` declares "dual-format support (R12 free tier, R2000 paid tier)".
- **D:** `docs/architecture/DXF_COMPAT_EXEMPTIONS.md:3-17` (2026-05-11) makes `create_document(...)` the mandatory wrapper. Its own example uses `version="R2010"`, a version that neither the R12 nor the R2000 tier allows.
- **U:** The cited `dxf_writer.py` commit `4c4f1a52` (SPRINTS.md:384) does not resolve in this object store. It is a dead pre-rewrite citation.
- **U:** A repository record of the 2026-09-14 owner ruling ("R12 only; R2000 = bucket-1 paid-tier vectorizer output only") was not located by this pass. It is known from session records.

### 3. Sprint 1, Vectorizer Reconciliation (SPRINTS.md:298-341)
- **D:** The record claims raw-mode restoration to R12 (`04735bd4`, :305), and that "Benchmark output exceeded March 6 baseline" via `3db07c62` (:318-320).
- **U:** Neither `04735bd4` nor `3db07c62` resolves in this object store. Both are dead citations. "Exceeded" is the record's own claim, and no measurement artifact is cited.

### 4. Sprint 3, Remediation and Gap Closure (SPRINTS.md:377-471)
- **D:** The 12 migration tasks are checked `[x]` with "(2026-04-23)" at :388-389 and :424-434. The same file says "REOPENED (2026-04-26)" at :378 and "CORRECTED … 2/12 MIGRATED, 10 FALSE CLAIMS" at :454-471.
- **D:** `curve_export_router.py` appears both unchecked (:390) and checked (:429).
- Both conflicting dispositions are still in the file today. They are recorded here, not resolved.

### 5. The 10/12 false-migration finding
- **D:** The audit is `docs/audit/sprints_md_verification_2026-04-25.md`:
  - The table is at :13-34.
  - "No commits touched these files on 2026-04-23" (:32).
  - Its method was "commit existence, file presence, import grep, ezdxf.new call count" (:232).
  - The audit was committed in `414d41dc`, and the reopening in `8a86ae89`, both on 2026-04-26.
- **D (contradiction kept):** `docs/audit/sprints_audit_2026-04-23.md:88` had earlier said "10/12 correctly migrated". The 04-25 audit reversed it.
- **D (what happened next):**
  - `9b7630b9` (2026-05-11, "enforce dxf_compat usage") removed `ezdxf.new(` from 9 of the 10 files.
  - `smart_guitar_dxf.py` followed in `d5033799` on 2026-05-20.
- **D (current state, see CSV):** that later fix swapped `ezdxf.new("R2010")` for `create_document(version="R2010")` and **kept the version**.
  - Seven of the ten files still emit R2010.
  - Two emit R2000, or a mix of R2000 and R2010.
  - Only `contour_reconstruction.py` is R12 by default.
- So the *wrapper* migration is real. The *R12 writer* migration that was claimed never happened.
- Current classification: 3 VERIFIED, 7 PARTIAL_MIGRATION, 2 STRANDED_IMPLEMENTATION.

### 6. `headstock/dxf_export.py` moved to the writer
- **D:**
  - Born as HEADSTOCK-001 in `98c0b58d` on 2026-03-18.
  - Falsely claimed migrated on 04-23 (audit :21).
  - Wrapped on 05-11 (`9b7630b9`).
  - Emits **R2010** today (`dxf_export.py:278`, `:561`).
- **D:** The route is reachable at `/api/export/headstock-dxf` (+ `/preview`, `/cost`), registered at `cam_manifest.py:332-333`.
- **D:** The smoke test asserts only the HTTP status, the content type, and a non-zero length (`test_headstock_dxf_export_smoke.py:56-154`).

### 7. The stranded headstock views were its consumers
- **D:** The only client code that calls it is `packages/client/src/views/cam/headstock/WorkspaceView.vue:26,57` (`useExportDxf`).
  - `CamSpecPanel.vue:20` (both copies) mentions it in a comment only.
  - `WorkspaceView` is an unrouted view. PR #308's deletion of it was stranded and never reached main, and the open PR #438 preserves it into `archive/`.
- **I:** The endpoint is live, but no reachable UI uses it. That is a stranded consumer, not a broken producer.

### 8. VEC-ANCHOR-001 reproduced the March 6 baseline
- **D (session record):** The March 6 anchor `cuatro_puertoriqueño_simple.dxf` was reproduced with these settings:
  - 400 DPI, `_simple_extraction` with epsilon 0.001, R12 LINE output.
  - Result: 128,997 segments, sha `586a94f186bd7ad7` on both sides.
- **D:** The vectorizer-sandbox PR **#104** (`agent/vec-lightline-002-standalone`) is **MERGED**, head `9cb3fc63`. The session record had it open at `fd20499`.
- **I:** This anchors "March 6 baseline" as a reproducible artifact. It does **not** verify Sprint 1's "exceeded" claim, which rests on a dead citation.

## Pattern: marked complete, never reached the usable system
The same shape shows up in Sprint 3 (10 claims entered with no commits behind them), in headstock (#308 "MERGED" but stranded), and in the views being the only consumer of a live endpoint. This chain does **not** assume one technical cause. Every item is labelled CONSOLIDATION/MIGRATION ARTIFACT, and no collision record was found.

## Safety: reported, not fixed
`/api/headstock/transition/gcode` (`headstock_transition_export.py:299`, registered at `business_manifest.py:51-52`) emits G-code, but:
- it has **no readiness gate and no `@safety_critical`**;
- it has **no tests**;
- it **is** inventoried, at `services/api/governance/manufacturing_output_inventory.json:3456-3474`, as `CONFIRMED_EMITTER`, `authentication: none`, `containment: LIVE_UNGOVERNED`. *(Corrected 2026-10-14: an earlier draft said the route was absent and only `/dxf` at :3437 was listed. That was wrong.)* The inventory already knows the route is ungoverned. It does **not** record the motion finding below.

Default request, generated offline and measured with `scripts/investigations/neck_gcode_motion_metrics.py --plane-z 0.0`:
- 1,231 lines, sha256 prefix `3b5ddbaa53dfe40f`;
- 64 G0 moves, **21 ending below Z0, all with XY motion**.

The first is at line 15: `G00 X-26.262 Z-11.0199`, a diagonal rapid that ends 0.24 mm above that station's reported `surface_z=-11.2574`. Whether this is a rapid into stock depends on the Z datum and on the surface profile along the X travel, so the clearance question is **UNRESOLVED**. The route came from the `files - 2026-03-17T155948.549` claude.ai bundle (HEADSTOCK transition), and was registered by `c2c332b8` on 2026-03-18. It needs its own validation order.
