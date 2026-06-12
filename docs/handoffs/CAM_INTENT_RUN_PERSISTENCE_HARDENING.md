# CAM Intent — Run-Artifact Persistence Hardening

**Status:** RECONSTRUCTED DRAFT — pending ratification. **Not approved. Not executed.**
**Type:** Spec / dev-order draft (read-only document; contains no code changes)
**Date drafted:** 2026-06-03
**Drafted by:** Claude, from code grounding (not retrieved from an authoritative source — see §0)
**Execution target (when ratified):** `luthiers-toolbox-clean` @ `main` (post PR #88, Dev Order 8G merged)

---

## §0 — Provenance of this document (read this first)

This spec was **reconstructed in-session**, not retrieved from an authoritative dev order.
There is no durable artifact on disk that defines this work. Searches confirmed:

- `git grep -ril "persist_cam_intent_run"` in the clean clone → **no matches** (net-new symbol).
- Working-dir glob for `*CAM-RESCUE*`, `*03.1*`, `*persist_cam_intent*` → **empty**.
- `docs/dev_orders/` → **does not exist** in this repo (the real convention is `docs/handoffs/CAM_8X_*.md`).

**OPEN QUESTION — label provenance (operator to resolve):**
Did the work labelled "03.1 / CAM-RESCUE" ever have an authoritative spec, or did that
label originate in conversation and get carried forward across recaps? On contact with the
code, this task is **CAM-intent provenance hardening** in the 8-series lineage — it is *not*
file-recovery from `recovery_triage.docx` (that doc is a separate 88-file recovery analysis).
If, on a fresh read, you conclude "03.1" was only ever a narration-generated name, that is
**permission to discard the label entirely** and let this be what the disk says it is.

The filename deliberately carries **no number and no "rescue"** to avoid enshrining an
unverified label. Note also: the 8G handoff already earmarks **8H for the Profile endpoint**
migration, so this work is *not* "8H." No 8-series number is assigned here on purpose.

Everything in §2 below is **evidence with line citations** so that, reading fresh, you are
evaluating the actual code — not re-litigating this document's interpretation of it.

---

## §1 — Summary

The V-Carve intent endpoint (`POST /api/cam/vcarve/intent-gcode`) persists an RMOS
`RunArtifact` at three points, each constructed inline by hand. The three blocks are
near-duplicates and, on inspection, persist **inconsistent provenance hashes** across the
three outcomes. This spec proposes a single helper, `persist_cam_intent_run(...)`, to
(1) collapse the duplication and (2) — *if the operator rules the asymmetry a defect* —
persist provenance consistently across all three outcomes.

**File under inspection:** `services/api/app/cam/routers/vcarve/intent_router.py`

---

## §2 — Evidence (findings, not recommendations)

### 2.1 — The three persistence call sites (confirmed by read, not inferred)

All three call the trivial `persist_run(artifact)` (`rmos/runs_v2/store_api.py:30`, a thin
`store.put`), each after building a `RunArtifact` inline:

| Outcome | Call site | Artifact built at | `status` |
|---|---|---|---|
| BLOCKED (safety policy) | `intent_router.py:199` | `:184–198` | `"BLOCKED"` |
| ERROR (toolpath gen failed) | `intent_router.py:236` | `:224–235` | `"ERROR"` |
| OK (success) | `intent_router.py:264` | `:250–263` | `"OK"` |

### 2.2 — The provenance-hash asymmetry (the finding that matters)

`request_hash` is computed once at **`intent_router.py:113`**
(`request_hash = sha256_of_obj(intent.model_dump())`) and returned to the caller in the
response dict at **`:272`** (`"request_sha256": request_hash`).

But the **persisted** artifacts store hashes inconsistently, and **none** store the request hash:

| Outcome | `Hashes(...)` constructed at | Hashes persisted |
|---|---|---|
| BLOCKED | `intent_router.py:196` | `feasibility_sha256` **only** |
| ERROR | `intent_router.py:233` | `feasibility_sha256` **only** |
| OK | `intent_router.py:259–262` | `feasibility_sha256` + `gcode_sha256` |
| (all) | — | `request_sha256` → **never persisted on any path** |

**Net asymmetry:**
- A **BLOCKED** run — the record of *why the machine was told not to cut* — persists the
  least provenance (feasibility hash only).
- `request_sha256` is returned to the API caller but is **not durable** anywhere; it cannot
  be recovered later via `get_run`.

> ⚠️ **Schema caveat (unverified — a required pre-execution check):** the response builds
> `request_sha256` into a plain `dict` at `:271–275`, *not* via the `Hashes` object. Whether
> `Hashes` (`rmos/runs_v2`) even has a `request_sha256` field has **not been confirmed**.
> Option (b) below may therefore require a `Hashes` schema field addition — verify before
> scoping.

### 2.3 — Disposition fork (decide HERE, next to the evidence)

The operator holds knowledge the code does not. Choose one:

- **(a) Intended — blocked/errored runs store less by design.**
  → Helper is **dedup-only**; it reproduces current behavior exactly, asymmetry preserved.
  Test asserts *no change* to persisted hashes. Clean refactor.

- **(b) Defect — provenance should be complete on every path.**
  → Helper persists `request_sha256` + `feasibility_sha256` (+ `gcode_sha256` where a gcode
  exists) on **all three** outcomes. This is a **behavior change** to persisted data and may
  require a `Hashes` schema field (see 2.2 caveat). Test asserts a full-hash round-trip via
  `get_run` on a **BLOCKED** run.

This is the single largest driver of the spec body and the test. **Unresolved by design.**

---

## §3 — Proposed change (shape only; not final until forks resolved)

### 3.1 — Helper

```python
def persist_cam_intent_run(
    *,
    run_id: str,
    tool_id: str,
    mode: str,                 # e.g. "vcarve_intent"
    event_type: str,           # e.g. "vcarve_intent_gcode_blocked" | "_execution"
    status: str,               # "BLOCKED" | "ERROR" | "OK"
    created_at_utc: str,
    feasibility: dict | None = None,
    decision: RunDecision | None = None,
    request_sha256: str | None = None,    # (b): persisted; (a): ignored
    feasibility_sha256: str | None = None,
    gcode_sha256: str | None = None,
    notes: str | None = None,
    errors: list[str] | None = None,
) -> RunArtifact:
    """Build a CAM-intent RunArtifact with consistent provenance and persist it."""
    ...
```

The three inline blocks at `:184–198`, `:224–235`, `:250–263` each collapse to one call.

### 3.2 — Home of the helper — **OPEN (operator/scope decision)**

- **Narrow:** beside the V-Carve router (fixes only these three). Smallest blast radius.
- **Shared (lean):** beside `persist_run` in `rmos/runs_v2/store_api.py`, exported via
  `rmos/runs_v2/__init__.py`, so the forthcoming intent migrations (8H Profile, 8I Drilling,
  8J Pocketing) call the *same* contract. 8G's stated purpose was "establish the pattern,"
  which argues for the shared home — but this is a scope call, not a code-derivable fact.

---

## §4 — Consolidated open decisions (all operator-held)

1. **Label provenance** (§0): is "03.1/rescue" a real prior spec or an in-session label? If
   the latter → discard the label; this is "CAM-intent provenance hardening," full stop.
2. **Behavior fork** (§2.3): (a) dedup-only / asymmetry intended, or (b) fix the gap.
3. **Helper home** (§3.2): narrow (near vcarve) vs shared (`store_api.py`).
4. **Naming/lineage:** keep this descriptive filename, or attach to a real, sourced 8-series
   number (NOT 8H — taken by Profile).

None of these are resolved in this draft. Resolving them is the act of ratification.

---

## §5 — Test plan (written; **not run**)

- **Refactor invariance (both forks):** existing 33 V-Carve intent tests
  (`tests/cam/test_vcarve_design_schema.py`, `tests/cam/test_vcarve_intent_migration.py`)
  remain green — the helper must not change endpoint responses.
- **Fork (a):** assert persisted `Hashes` on BLOCKED/ERROR/OK are *unchanged* from today.
- **Fork (b):** new test — POST an intent that trips `SafetyPolicy.should_block`, capture
  `run_id`, then `get_run(run_id)` and assert the persisted artifact carries
  `request_sha256` + `feasibility_sha256` (round-trip, not just response-shape).
- **Schema pre-check (b):** confirm/extend `Hashes` to hold `request_sha256` (per §2.2 caveat).

---

## §6 — Branch & execution discipline (**not executed**)

When ratified and the operator is fresh:

- New dedicated branch off `main` in `luthiers-toolbox-clean` (e.g.
  `feat/cam-intent-run-persistence`). **One stream = one branch = one PR.**
- **Stage by explicit path only — never `git add -A`** in this repo.
- Agent runs the mechanical refactor in its verified tool shell with **per-step read-back**
  (re-read the edited file + run the relevant test/gate after *each* step), and **holds at
  push**. The operator performs the push by hand (the tag-push split).
- Verification gates before push: targeted `pytest tests/cam/test_vcarve_intent_migration.py`
  (+ the new round-trip test for fork b), plus the repo's manifest/governance ratchet if the
  helper's export touches a manifested surface.

---

## §7 — What this document does NOT do

- No branch created. No source file edited. No test run. No code executed.
- No open decision in §4 silently resolved.
- The provenance gap (§2.2) is **documented, not fixed.** It will still be there tomorrow,
  and is best fixed by a fresh operator reading **this file** — not a recap.

*End of reconstructed draft. Stop point.*
