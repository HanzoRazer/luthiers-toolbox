# DEV ORDER — Revert ungated R2000 (bucket ②) to R12 default

**Created:** 2026-06-04
**Status:** READY — execute as the first task of a fresh session on a confirmed shell.
**Self-contained:** this doc carries the spec, the sites, the traps, *and* the ordered execution runbook
(see "Execution sequence" below) — it is the complete handoff; no companion doc required.
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

2. **`services/api/app/cam/dxf_consolidator.py:247` — ESCALATE, do NOT revert as written.**
   > **SPEC CORRECTION (2026-06-07, applied during execution).** This item was originally written as
   > a mechanical revert (`version="R2000"` → `version="R12"`) with `:281` as the only conditional
   > stop-and-ask. Code reading during execution showed that assumption is **inverted**: `_write_output`
   > calls `add_lwpolyline()` **unconditionally** (`:306`), and ezdxf cannot place LWPOLYLINE in an R12
   > document — so a literal R12 revert here **breaks the consolidator at runtime** and re-creates the
   > R12+LWPOLYLINE malformed-entity class that CLAUDE.md's R12 gate exists to prevent. The consolidator
   > *is itself* the "consumer that depends on R2000/LWPOLYLINE output" that Verification §2 says is a
   > STOP-AND-ASK. Making it R12-safe requires adding version-adaptive LINE-fallback logic — that is
   > **new work, not a revert**, and the order forbids improvising a fix under execution.
   >
   > **Disposition:** `:247` and the coupled lifecycle assertion `:281` (`dxf_version="R2000"`, which
   > merely declares what `:247` builds) are **both escalated, not executed.** They become their own
   > scoped dev order: *"make `dxf_consolidator` R12-safe via LINE fallback, OR formally sanction its
   > R2000 dependency as legitimate (bucket ①)."* Two real options, codeowner's call — not absorbed
   > into the revert session.
   >
   > Net effect: the executable scope of THIS order is **Scope #1 only** (`dxf_exporter.py`), which
   > *is* a clean version-adaptive default flip.

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

## Execution sequence — the runbook (ordered; each arrow is a gate)

**Single-stream session:** this executes the bucket-② revert and *nothing else*. Bundling the queued
vitest closeouts, 8H recovery, or Surface D would be scope drift — each is its own session.

**Step 0 — shell gate (decides whether the session runs at all).** `echo ok` then a native-exit probe
(`git --version; "exit=$LASTEXITCODE"` → must print `exit=0`). If the exit code doesn't return clean,
**abort before touching source** — no degrading to "edit and assume." (Detail: Pre-flight §1.)

**Entry checklist (before editing):** read this dev order (spec + runbook); confirm the working repo is
on `main`, current, clean tree; branch off `origin/main`, explicit-path staging only.

Then, in order — each step gated:
1. **Re-ground** — run the bucket-② grep (Pre-flight §3); catch any drifted or additional ungated site.
2. **Edit the two sites** — `dxf_exporter.py:46`, `dxf_consolidator.py:247` (Scope §1–2).
3. **`:281` → STOP-AND-ASK if ambiguous.** If `:281`'s gating status is not unambiguous from reading,
   escalate; do not make the gated-vs-ungated call under execution. (Scope §2.)
4. **Flip the manufactured-evidence test** — `test_dxf_exporter_versions.py:85-86` to expect R12/AC1009;
   a conscious overrule, documented in the PR (top warning + Verification §1).
5. **Downstream-consumer audit → STOP-AND-ASK if a consumer depends on R2000** — first caller to check
   `relief_export_router.py:195` (Verification §2).
6. **Verify** — targeted tests collect + pass.
7. **Hold at push** for the codeowner (Verification §3).

**The only two escalation points are steps 3 and 5** — both are *interpretation, not verification*, so
they escalate rather than improvise. Everything else the session completes autonomously up to the push hold.

**Definition of done:** branch pushed-ready (held), PR drafted, two sites reverted, the pinning test
flipped, downstream audit clean-or-escalated, `:281` resolved-or-escalated. **Not done** = any
stop-and-ask still open, or tests not run.

---

## Re-ground findings (2026-06-07) — sites caught that were NOT in the original inventory

The Pre-flight §3 re-ground (run in `luthiers-toolbox`) surfaced three ungated-R2000 sites in
neither Scope nor Excluded. Per discipline they are **reported, not folded into this session** — each
needs its own disposition (likely future dev orders), and two carry the same LWPOLYLINE-dependency
wall as `:247`:

1. **`cam/layer_consolidator.py:183, :247` — twin of the consolidator the cross-repo inventory missed.**
   Same unconditional-LWPOLYLINE pattern (`create_document(version="R2000")` when source is R12, for
   LWPOLYLINE output). Hits the identical can't-cleanly-revert wall as `dxf_consolidator.py:247`.
   Belongs with the consolidator's future "R12-safe-or-sanction" dev order, not this revert.
2. **`routers/blueprint_cam/contour_reconstruction.py:375, :461` — needs an explicit in/out call.**
   LWPOLYLINE contour output, R2000 functionally required. Lives in `routers/blueprint_cam/`, which is
   **adjacent to but NOT** the Excluded Surface-D path (`services/blueprint-import/`). Whether it falls
   under the blueprint-path exclusion is a scope determination for the codeowner.
3. **`cam/translator_capability_registry.py:240, :280` — probably bucket ① by association, unconfirmed.**
   Adjacent to the Excluded `translators/base/registry.py` paid-tier registration. Likely sanctioned
   tier-gated R2000; confirm before any action.

A note on tooling: the first re-ground pass returned only 4 of 18 matches (a truncated ripgrep result;
the file was never gitignored — `git check-ignore` exits 1). A single rg pass on this repo is not a
trustworthy re-ground; reconcile against named sites and re-run to a stable count.

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
