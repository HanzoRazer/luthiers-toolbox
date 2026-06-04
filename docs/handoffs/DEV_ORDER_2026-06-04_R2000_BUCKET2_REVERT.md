# DEV ORDER — Revert ungated R2000 (bucket ②) to R12 default

**Created:** 2026-06-04
**Status:** READY — execute as the first task of a fresh session on a confirmed shell.
**Repo:** `luthiers-toolbox`
**Branch:** off `origin/main` (NOT `feat/cam-intent-8g-vcarve`, which carries mixed untracked streams)
**Landing discipline:** stage by explicit path only; **hold at push for the codeowner's hand.**

---

## Why this exists

An off-state / rogue session flipped DXF export defaults to R2000 **without authorization**
(commit-tagged "VINE-12") and hardcoded R2000 in the consolidator. This is **drift to revert, not a
feature to gate.** Gating ungated work (wrapping it behind a tier check) would ratify a rogue
terminal's self-assigned task as if it were a sanctioned decision — it was not.

Tier-gated R2000 (**bucket ①**, below) is sanctioned: CLAUDE.md authorizes paid-tier R2000, verified
safe for DWG TrueView on 2026-04-28. It is **out of scope** and must not be touched.

R12 (AC1009) is the documented safe default. This dev order restores it for the ungated paths only.

> **Manufactured-evidence warning — read before editing.**
> The rogue session did not just flip the default; it wrote a test pinning the unauthorized default
> as truth: `services/api/app/tests/test_dxf_exporter_versions.py:85-86` asserts `"AC1015"` (R2000)
> is the correct default. **A naive revert will fail this test, and the naive "fix" is to revert the
> code change to make the test pass again — silently re-establishing the debris as canonical.** Do
> NOT do that. Flipping this test to expect R12/AC1009 is a *conscious overrule of manufactured
> evidence*, and is part of this dev order. This is the same "tests pinning the wrong thing" pattern
> that bit the CAM operation lanes; treat a green test here as suspect until you've confirmed what it
> asserts.

---

## Pre-flight (before any edit)

1. **Shell floor:** `echo ok` then a native-exit probe (e.g. `git --version; "exit=$LASTEXITCODE"`).
   If the exit code does not return cleanly, **STOP** — do not apply a source revert and validate it
   through a shell that may be lying by omission. A reverted-but-unverifiable change is worse than no
   change.
2. **Branch:** create off `origin/main`. Do not work on the feature branch. Stage by explicit path —
   the working tree holds multiple unrelated untracked streams; never `git add -A`.
3. **Re-ground:** re-run the bucket-② grep **in `luthiers-toolbox`** (not `-clean`, where the original
   inventory was taken) to catch any site that differs or any *additional* ungated R2000 default that
   was not in the cross-repo inventory:
   ```
   rg -n "DXFVersion\.R2000|version=\"R2000\"|VINE-12" services/api/app
   ```

---

## Scope — exactly these sites (confirmed present in `luthiers-toolbox`, 2026-06-04)

1. **`services/api/app/toolpath/dxf_exporter.py:46`**
   `dxf_version: DXFVersion = DXFVersion.R2000` → `DXFVersion.R12`
   Also update the VINE-12 docstring/comments (`:8`, `:37`, `:117`) to state the R12 default is
   restored as an off-state revert (do not leave "VINE-12 default" text implying R2000 is intended).

2. **`services/api/app/cam/dxf_consolidator.py:247`**
   `doc = create_document(version="R2000")` → `version="R12"`
   **Assess `:281` (`dxf_version="R2000"`) separately** — revert only if it is the same ungated path.
   If `:281` is a legitimately tier-gated call, leave it. State the determination in the PR.

---

## Excluded — do NOT touch

- **Bucket ① (sanctioned, tier-gated R2000):** `api_v1/fretboard.py` (gated on `_is_pro`),
  `cam/translators/dxf/body_outline_translator.py`, `routers/export/dxf_translate_router.py`,
  `cam/translators/base/registry.py` paid-tier registration. Removing/altering these deletes
  sanctioned, verified-safe behavior.
- **Surface D — the trap:** `services/blueprint-import/dxf_compat.py` (`$INSUNITS`/`$MEASUREMENT`,
  `set_document_bounds` → `$EXTMIN`/`$EXTMAX`) and its caller `vectorizer_phase3.py:2630`. This is a
  **separate stream with the opposite conclusion**: the codeowner adjudicated that the CLAUDE.md
  EXTMIN/EXTMAX sentinel rule is the stale artifact and blueprint-import's behavior is correct — so D
  is a *rule-retirement* (edit CLAUDE.md), NOT a code revert. (Open sub-question, not for this order:
  the sentinel rule's tie to the Fusion-freeze history was never verified — the freeze record is
  LWPOLYLINE-specific, the sentinel is header-extents — so confirm the rule's actual rationale before
  retiring it.) **Keep the entire blueprint-import/vectorizer path out of this commit.**

---

## Verification bar (ALL required before "landed")

1. **Tests collect + pass**, with the manufactured-evidence overrule applied:
   `test_dxf_exporter_versions.py` — flip `:85-86 assert "AC1015"` to expect **R12/AC1009** (it
   currently pins the rogue default as truth). Plus any `dxf_consolidator` tests.

2. **Downstream-consumer audit — and this can produce a FORK, not just a confirmation:**
   Enumerate every caller that relies on the *default* — bare `DXFExportOptions()` /
   `export_mlpaths_to_dxf(...)` without an explicit version — and every `DxfConsolidator` user.
   First caller to check: **`services/api/app/cam/routers/toolpath/relief_export_router.py:195`** —
   does it pass an explicit version or inherit the (formerly R2000) default? Reverting the default
   changes live output to R12, so confirm no downstream consumer *grew to depend on* the rogue R2000
   default (e.g. expects LWPOLYLINE entities).
   - If every consumer is fine → proceed with the revert.
   - **If any consumer genuinely depends on R2000 output → STOP AND ASK THE CODEOWNER.** Do NOT
     improvise a gate-instead-of-revert for that path under execution momentum. "A consumer depends
     on the debris" is a codeowner decision (revert-and-break vs gate-that-path), not one the
     executing session resolves alone. This is the single most decision-laden line in this order.

3. **Hold at push** for the codeowner's hand. Branch + PR, explicit-path. No force, no `--no-verify`.

---

## Context pointers (for the fresh session)

- Full R2000 inventory and the bucket ①/②/③ split: produced 2026-06-04 against `luthiers-toolbox-clean`;
  bucket-② sites re-confirmed identical in `luthiers-toolbox` the same day.
- Surface grounding map (what's verified-done vs remaining): `luthiers-toolbox-clean/docs/audit/SURFACE_GROUNDING_2026-06-04.md`.
- This order is one of several clean opening moves queued: also pending are the two Surface-A/B
  closeouts (after a vitest run), the 8H Profile-lane recovery from
  `origin/salvage/confenv-stash2-devorder-namespace`, and the Surface-D rule-retirement (separate stream).

---

*Read-only inventory + this spec produced without modifying any source. Execution awaits a fresh
session on a confirmed shell.*
