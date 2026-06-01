# CI-RED-015-D — Open Decisions + Resolutions

**Date:** 2026-05-30
**Status:** **CLOSED (2026-05-30)** — MVP-path verified collision-free via live `app.routes` dump. `dump_and_assert_routes.py` RAN, exit 0, `mvp_problems: []`; `audit_wire_urls.py` regex fix RAN. Live dump committed as `metrics/live_routes.json`. Shadow verdict = **Y (deferrable)**, 11 non-MVP collisions confirmed off-path. Structural debt deferred to CI-RED-016.
**Branch note:** Closure committed on `fix/ci-red-015-d-closure` (off `origin/main 88d24f4`). Shell recovered 2026-05-30; gate ran, exit 0.

---

## 0. Working-copy vs. snapshot discrepancy — RESOLVED (no conflict)

The reconciliation doc reported "Doc 3's closure edits are absent"; the engineer reported "they're applied." **Both are correct.** The reconciliation audited a flat zip export (no `.git`, no working-tree state); the edits live as **uncommitted working-tree changes** in `C:\Users\thepr\Downloads\luthiers-toolbox` on `docs/boe-ibg-family-conflation`. Verified present here:
- `services/api/scripts/audit_wire_urls.py` — rewritten `load_manifest_entries` (split-on-`RouterSpec(`) + `LIMITATIONS` docstring.
- `SPRINTS.md` — 015-D = "MVP-path audited (2026-05-30)".
- `docs/handoffs/CI_RED_015D_WIRE_URL_COLLISION_HANDOFF.md` — 2026-05-30 second-defect note.

**Standing correction:** treat the edits as **real and uncommitted**, not missing. This does NOT close the verification gap — the live `app.routes` dump is still not in-tree, so the MVP-clean conclusion remains *asserted, not verified*.

---

## 1. Commit the closure edits — YES, with a guardrail
Commit the three edits. The `audit_wire_urls.py` regex fix **RAN** (2026-05-30) and `metrics/wire_url_audit.json` is reconciled. The live dump (`dump_and_assert_routes.py`, exit 0) is the authoritative closure artifact.

**Branch sub-decision:** the closure is **CI-hygiene**, not docs. Put SPRINTS status + audit script + handoff note on a **small branch off current `main`** (e.g. `fix/ci-red-015-d-closure`). Reconcile local `main` (`a9150f5`) → origin (`88d24f4`) **before** branching so the closure lands on top of current origin. Confirm whether `docs/boe-ibg-family-conflation` is residual (BOE/IBG doc reportedly merged via #77).

## 2. Authoritative live dump — (a) now + (b) durably; NOT (c)
- **(a)** Run an in-process dump (cold `import app.main` is pure introspection, ~40s, no port bind), commit `services/api/metrics/live_routes.json`, assert each MVP-path URL appears exactly once.
- **(b)** Commit a reusable `dump_and_assert_routes.py` (Appendix A) so the authoritative artifact is reproducible and never lives only in someone's `C:\tmp`. This is the seed of the `DRIFT-AUDIT` pattern: dump loaded reality, assert against intent.
- **NOT (c):** do not import the old out-of-tree `C:\tmp\015d_route_dump.json` as canonical — that's the exact anti-pattern that caused this. Fine only as a one-time sanity cross-check ("does my fresh dump also show ~11?").

## 3. Shadow collision scope — file as a CONTINUATION of the March overlap record, NOT folded into 015-D, NOT net-new
015-D is the MVP-path collision check; the shadow is **off the MVP path**. Folding it in re-violates one-cause-class and entangles 015-D's clean verdict. **Post-review correction (see § R3):** the shadow is *not* a fresh discovery — `docs/INSTRUMENT_ROUTER_MIGRATION_MAP.md` (2026-03-29, marked COMPLETE) already records these four endpoints as "Parallel Implementations — RETAINED … pending schema reconciliation." So the substantive ticket is **"complete the schema reconciliation the March migration map deferred, now that 015-D has identified the live winner (legacy)."** `DRIFT-AUDIT-001` is the *pattern wrapper* (intended architecture ≠ loaded behavior), referencing this as its first worked example — but the work has an existing home and must be filed as continuation, not surprise.

## 4. Shadow action — diff-then-fix (diff DONE below); fix ownership inversion, but reconcile schemas FIRST
The end-to-end diff AND the consumer sweep are complete — see **§ Diff verdict** and **§ Post-review corrections**. Outcome: handlers **diverge**, but **no frontend/production caller** hits the divergent endpoints → **bucket Y (dead overlap, deferrable)**, not an active production bug. **Post-review correction (§R1):** the divergent endpoints *are* consumed by **two test suites** (one asserting the legacy contract, one the canonical), so "no caller" is wrong as stated — the accurate claim is "no *production* caller." Ownership inversion should still be corrected, but **schema reconciliation must precede flipping the winner**: the legacy `action_at_nut_mm` contract is the one currently served, so reordering is a breaking change for anything that adopted live behavior (Appendix B, Option 3 caution).

## 5. Re-run static audit — run once, then deprecate
After a shell exists: `cd services/api && python scripts/audit_wire_urls.py` to overwrite the stale `wire_url_audit.json` (currently shows inflated "68"). Then add a one-line "superseded by `metrics/live_routes.json`" note. Run-once-then-demote; do not make the static audit composition-aware.

## 6. Structural finding (143 unmanifested, 49%) — keep deferred; add a bleed-stop
Do NOT reopen the 143 triage (it's a re-architecture sprint, correctly deferred to retirement / CI-RED-016). DO add a cheap **manifest-discipline check** (Appendix C): fail when a new `@router` file lands without a manifest entry or documented exemption. Stops the percentage climbing while the repo winds down; same shape as wiring `check_execution_class_compliance.py` after the CAM-intent deletion.

---

## Diff verdict — `instrument_router` (legacy) vs `instrument_geometry` (canonical)

Both manifested under `/api/instrument`; legacy registers first (`business_manifest.py:39` < `:128`) → **legacy wins on every shared (method, path)**.

| Wire URL | Legacy handler | Canonical handler | Equivalent? | Consumed (client)? | Bucket |
|---|---|---|---|---|---|
| `POST /soundhole` | `get_soundhole_spec` | `calculate_soundhole` | **Yes** — identical logic, same `compute_soundhole_spec`, same models | Yes (Standard Aperture) | Y (safe) |
| `GET /soundhole/types` | `get_soundhole_types` | `get_soundhole_types` | **Yes** — identical | — | Y (safe) |
| `POST /soundhole/check-position` | returns `position_ratio` | returns `diameter_mm` | **No** — response schema differs | **test-only** (geometry smoke, lenient assert masks it) | Y (dead in prod) |
| `POST /nut-compensation` | req `{action_at_nut_mm, fret_height_mm,…}` → `{setback_mm, intonation_error_cents}` | req `{nut_width_mm, break_angle_deg,…}` → `{compensation_mm, effective_scale_length_mm, open_string_pitch_error_cents}` | **No** — different inputs, outputs, AND math | **test-only** (both suites; geometry test 422s deceptively) | Y (dead in prod) |
| `POST /nut-compensation/compare` | `NutCompareResponse` | `NutComparisonResponse` (different shape) | **No** | **test-only** (both suites) | Y (dead in prod) |
| `POST /soundhole/spiral/*`, `/soundhole/options`, `/soundhole/body-styles` | — (legacy lacks) | canonical-only | n/a | Yes (Carlos Spiral Jumbo) | safe (canonical-only) |

**Net → Y (deferrable), with recommended cleanup.** Real divergence exists; **no frontend/production caller** hits the divergent endpoints; the consumed paths (`POST /soundhole` equivalent; spiral endpoints canonical-only) are safe → **dead overlap (Y)**, not an active production bug. The ownership inversion is still worth a low-risk cleanup (Appendix B) — but **reconcile schemas before flipping the winner** (the legacy contract is the one live). **Caveat:** scoped Y — swept `packages/client/src` + `services/api` only; did not sweep other services or external repos.

> **Correction to the original sweep claim:** my first pass said "no caller *anywhere* — only refs are in `wire_url_audit.json`." That was a **`head_limit` truncation artifact** (the giant audit JSON + CAM nut-slot tests filled the result window before the real callers appeared). Re-verified below in § Post-review corrections: there **are** callers — two test suites — and one of them passes *deceptively* against the legacy-winning mount.

---

## Post-review corrections (2026-05-30, repo-verified)

Independent re-verification confirmed three corrections to the consumer sweep. The **Y verdict survives all three**; the *reasoning* is what needed fixing.

### R1 — "No caller" is false: two test suites hit the divergent endpoints, and the geometry suite passes deceptively
- `tests/test_instrument_router_smoke.py` posts the **legacy** contract (`action_at_nut_mm`) → hits the legacy (winning) handler → passes legitimately.
- `tests/test_instrument_geometry_router_smoke.py` builds its client from **`app.main:app`** (line 11–13 → the live, legacy-winning mount) and posts the **canonical** contract:
  - `test_nut_compensation_traditional` (:456) sends `{nut_width_mm, break_angle_deg, …}`. The legacy handler requires `action_at_nut_mm`/`fret_height_mm` → **422**. The assert is lenient `in (200, 422)`, so the test **passes on the 422**, and the `if 200: assert "compensation_mm"` block **never runs.** It is green for the wrong reason and never exercises the canonical handler it names.
  - `test_soundhole_check_position_valid` (:211) — requests are actually identical, so it hits legacy, gets 200 with `position_ratio` (not canonical `diameter_mm`), and `assert "gate" in data` (present in both) masks the response-shape divergence.
- **Consequence:** a geometry smoke test that believes it tests the canonical handler is silently testing the legacy one — same camouflage shape as skipped-test / swallowed-warning findings. This is its own small cleanup (see § Test cleanup), tracked under the DRIFT-AUDIT ticket.

### R2 — A third `/nut-compensation` exists, but is dead (unmounted)
`app/routers/instrument/fretwork_router.py:383` defines `POST /nut-compensation` (canonical-style `nut_width_mm`/`break_angle_deg`). But `app.routers.instrument` is **not manifested** (manifest grep: no matches) → never mounts → does not collide at runtime. The two-way *live* framing is correct. Latent trap: if anyone ever manifests the `instrument/` package, a third handler joins the race. One-line note in the ticket so it isn't rediscovered as a surprise.

### R3 — Not a new discovery: a deliberately retained known condition since March
`docs/INSTRUMENT_ROUTER_MIGRATION_MAP.md:20-31` (2026-03-29, **COMPLETE**) lists these exact four endpoints under **"Parallel Implementations (4 endpoints) — RETAINED … pending schema reconciliation,"** with the contract pairs spelled out (`action_at_nut_mm` vs `nut_width_mm`, `NutCompareResponse` vs `NutComparisonResponse`, `position_ratio` vs missing). `docs/INSTRUMENT_ROUTER_OVERLAP.md` documents the same overlap. The **new** fact 015-D adds is the *runtime winner* (legacy) the migration map left unspecified. → File as continuation of that record (see §3), not net-new.

### Test cleanup (small, separate from the inversion fix)
`test_instrument_geometry_router_smoke.py`'s nut-compensation / check-position cases should either (a) be marked `xfail`/`skip` with a reason pointing at the retained-parallel record until reconciliation lands, or (b) be tightened so a 422-from-the-wrong-handler stops counting as a pass. Do **not** silently leave them green.

---

## Lineage + plumbing — refs-verified (2026-05-30); gates the post-shell push

**Export-lineage question = RESOLVED → commit AND push.** `.git/refs/remotes/origin/docs/boe-ibg-family-conflation` = `ca197291` = local HEAD → the branch is **already pushed and in sync**; local and origin hold identical committed state, so a clean export cannot be distinguished by source (local archive vs origin clone). The uncommitted 015-D work is on **neither**. Resolution: **commit AND push** — correct in both export worlds; removes any "stranded on the wrong remote" risk without having to know how the zips are produced.

**Divergent main (load-bearing for the branch base).** Local `refs/heads/main` = `5052f72` ≠ `refs/remotes/origin/main` = `88d24f4`. Cut `fix/ci-red-015-d-closure` off **origin/main `88d24f4`** after a fetch — NOT off stale local `main`, or the closure inherits the divergence.

**Plumbing risk flag — `.git/config` is ~164 KB.** `origin` is configured (`github.com/HanzoRazer/luthiers-toolbox.git`) but the config is ~3 orders of magnitude oversized, bloated with hundreds of `remote = origin` branch entries — evidence that something is **mechanically rewriting git plumbing**, the same layer as the dead-shell / two-backends trouble. A bloated config can yield wrong refspecs / fan-out pushes / fetch storms — and the queue's one committed action is a **push**. Verify config sanity BEFORE that push, not after.

---

## DEV ORDER — `DO-015D-CLOSE-01` (executable close; reviewed 2026-05-30)

**Objective:** 015-D *audited* → *closed*: satisfy the live-dump closure criterion (`SPRINTS.md:1093`), reconcile the static audit, commit + push.
**Hard precondition:** working shell, confirmed by a returned exit status on `echo ok`. If commands return no exit status → do not start (agent/IDE restart, not a server restart).
**Terminal state of THIS order:** branch pushed + PR opened + CI triggered. **"Merged" is a follow-on human gate (CI green + review), outside this order's commands.**

### GATE 0 — verify tree + plumbing (don't trust the pre-restart inventory)
```
cd C:\Users\thepr\Downloads\luthiers-toolbox
git rev-parse --abbrev-ref HEAD            # expect docs/boe-ibg-family-conflation
git status --short                          # expect uncommitted: audit_wire_urls.py (M), SPRINTS.md (M),
                                            #   CI_RED_015D_WIRE_URL_COLLISION_HANDOFF.md (M),
                                            #   dump_and_assert_routes.py (??), check_manifest_discipline.py (??),
                                            #   docs/handoffs/CI_RED_015D_OPEN_DECISIONS.md (??)
git stash list                              # expect empty
git config --get-all remote.origin.fetch    # PRIMARY: expect exactly ONE normal refspec.
                                            #   >1 = the 164 KB-config bloat fingerprint → STOP (fetch-storm risk in Step 1)
git config --get-all remote.origin.push     # secondary: expect empty. NOTE: Step 4's `push -u <branch>` is an explicit
                                            #   refspec and BYPASSES this setting — the fetch refspec is the gating one here.
```
**STOP** if fetch returns >1 refspec, or `status` ≠ the expected set.

### STEP 1 — branch off origin/main; know the conflict surface BEFORE stashing
Local main (`5052f72`) ≠ origin/main (`88d24f4`); the edits were made against `ca197291`, which diverges from origin/main, so the pop can conflict. Check first so the resolution is calm, not 2 a.m. panic:
```
git fetch origin
git diff --stat origin/main -- SPRINTS.md services/api/scripts/audit_wire_urls.py docs/handoffs/CI_RED_015D_WIRE_URL_COLLISION_HANDOFF.md
#   empty  → pop will be trivial.
#   non-empty → a conflict is coming; resolve it TOWARD the 015-D content deliberately.
git stash -u
git checkout -b fix/ci-red-015-d-closure origin/main
git stash pop                               # on conflict: keep the 015-D edits (audited status; split-on-`RouterSpec(` regex)
```

### STEP 2 — run the closure GATE (per `SPRINTS.md:1093`), then confirm the artifact is trackable
```
cd services/api
python scripts/dump_and_assert_routes.py    # PASS = exit 0 + "OK: all MVP-path URLs resolve to exactly one handler"
git check-ignore metrics/live_routes.json   # if this PRINTS the path → metrics/ is gitignored → use `git add -f` in Step 4
```
- **Exit 0:** proceed.
- **Exit 1 (MVP URL missing/duplicated):** this FALSIFIES the "no MVP blocker" verdict → 015-D stays **OPEN**. **Persist the evidence before triage so it can't evaporate if the shell dies again:** `git checkout -b scratch/015d-failing-dump && git add -f metrics/live_routes.json && git commit -m "evidence(015-d): failing live dump — MVP URL not unique"`. Then triage. Do **not** close.

### STEP 3 — make "regex fix ran" actually TRUE (don't claim a run that didn't happen)
`dump_and_assert_routes.py` does **not** exercise `audit_wire_urls.py` — different scripts. To legitimately commit "regex fix run + count reconciled," run it:
```
python scripts/audit_wire_urls.py           # overwrites stale metrics/wire_url_audit.json with the prefix-corrected count
```
If you choose NOT to run it, the Step 4 commit message must say **"regex fix applied, unrun"** — never assert a run that didn't happen.

### STEP 4 — flip status, stage EXPLICITLY (never `git add -A`), commit, push
- `SPRINTS.md` 015-D → **CLOSED (2026-05-30), MVP-path verified collision-free, live dump `metrics/live_routes.json`**; record X/Y/Z = no-X.
- This doc's Status → 015-D closed; drop "unrun" on the two scripts (they ran in Steps 2–3).
```
cd C:\Users\thepr\Downloads\luthiers-toolbox
# Explicit add ONLY. Do NOT `git add -A`: check_manifest_discipline.py and any DRIFT-AUDIT work
# MUST stay UNTRACKED here (separate branches, one-cause-class).
git add services/api/scripts/audit_wire_urls.py services/api/scripts/dump_and_assert_routes.py SPRINTS.md docs/handoffs/CI_RED_015D_WIRE_URL_COLLISION_HANDOFF.md docs/handoffs/CI_RED_015D_OPEN_DECISIONS.md
git add metrics/live_routes.json metrics/wire_url_audit.json     # prepend `-f` if Step 2's check-ignore flagged metrics/
git status --short                          # CONFIRM check_manifest_discipline.py is STILL "??" (untracked)
git commit -m "fix(ci-red-015-d): close — MVP-path wire URLs verified unique via live app.routes dump

- dump_and_assert_routes.py: RAN, exit 0, all MVP-path URLs unique; live_routes.json committed (authoritative)
- audit_wire_urls.py: manifest-prefix regex fix RAN; wire_url_audit.json reconciled + superseded by live dump
- SPRINTS 015-D -> CLOSED; structural debt (143 unmanifested, non-MVP overlaps) deferred to CI-RED-016"
git push -u origin fix/ci-red-015-d-closure
```

### DEFINITION OF DONE — two finish lines, stated explicitly
- **This order completes at:** dump exit 0 + `live_routes.json` committed (and verified *not* gitignored) + `audit_wire_urls.py` run + SPRINTS 015-D = CLOSED + branch **pushed** + PR opened + CI triggered.
- **Follow-on human gate (NOT this order):** CI green — the regex fix + scripts run in CI for the *first time* there, a different env than the local Step 2/3 runs — plus review → **merge**. Reaching push with all commands green IS this order's success; do **not** force-merge to check the box.

### GUARDRAILS / ROLLBACK
STOP on: Gate 0 fetch-refspec >1; Step 2 exit 1 (persist evidence, halt); stash-pop resolved toward anything but the 015-D content. Rollback: branch is isolated off origin/main → `git checkout docs/boe-ibg-family-conflation && git branch -D fix/ci-red-015-d-closure`; main/origin untouched until merge.

---

## Remaining follow-ons (separate branches; AFTER 015-D closes)
**A.** **[READY — diff + sweep DONE]** File the shadow as a **continuation of the March `INSTRUMENT_ROUTER_MIGRATION_MAP.md` reconciliation** (draft entry: Appendix D), with `DRIFT-AUDIT-001` as the pattern wrapper. Sequence: reconcile schemas → pick canonical contract → THEN correct ownership inversion (Appendix B). Note the dead third definition (R2) and the deceptive geometry test (Test cleanup) in the ticket.
**B.** **[READY — authored, own branch]** Commit the manifest-discipline bleed-stop check `services/api/scripts/check_manifest_discipline.py` (currently uncommitted/untracked; **must not** ride the 015-D commit — see DEV ORDER Step 4). Leave the 143 triage deferred.

> The live-dump asserter `services/api/scripts/dump_and_assert_routes.py` is **not** a follow-on — it is the close tool, run as the gate in DEV ORDER Step 2 and committed with the 015-D closure.

*Nothing in this doc is committed; all edits are uncommitted working-tree changes (durable on disk, but not version-controlled) pending a working shell + the correct branch. The doc itself is the recovery runbook — if the shell stays dead across sessions, committing this doc is the single highest-value action, because it is the only place this plan survives a session boundary.*

---

## Appendix A — proposed `services/api/scripts/dump_and_assert_routes.py` (unrun)

```python
"""Dump composed FastAPI routes and assert MVP-path URLs are unique.
Run: cd services/api && python scripts/dump_and_assert_routes.py
Authoritative source of truth for CI-RED-015-D (supersedes the static audit_wire_urls.py)."""
import json, sys
from collections import Counter
from pathlib import Path
from app.main import app

MVP_EXACT = ["/api/rmos/wrap/mvp/dxf-to-grbl", "/api/v1/fretboard/dxf"]
MVP_PREFIXES = ["/api/rmos/runs", "/api/export/"]

routes = [{"path": getattr(r, "path", None),
           "methods": sorted(m for m in (getattr(r, "methods", None) or []) if m not in ("HEAD", "OPTIONS")),
           "name": getattr(r, "name", None)} for r in app.routes]

(Path(__file__).resolve().parent.parent / "metrics" / "live_routes.json").write_text(
    json.dumps(routes, indent=2), encoding="utf-8")

keys = [f"{m} {rt['path']}" for rt in routes for m in rt["methods"]]
collisions = {k: c for k, c in Counter(keys).items() if c > 1}
mvp_problems = [(p, sum(1 for rt in routes if rt["path"] == p)) for p in MVP_EXACT
                if sum(1 for rt in routes if rt["path"] == p) != 1]

print(json.dumps({"total_routes": len(routes),
                  "collision_count": len(collisions),
                  "collisions": collisions,
                  "mvp_problems": mvp_problems}, indent=2))
sys.exit(1 if mvp_problems else 0)
```

## Appendix B — ownership-inversion fix options (pick after consumer sweep + contract decision)

- **Option 1 (surgical):** delete the duplicated `@router` routes (`/soundhole*`, `/nut-compensation*`) from `app/routers/instrument_router.py`, leaving canonical `instrument_geometry` the sole owner. Lowest blast radius if legacy has unique routes worth keeping.
- **Option 2 (registration):** if `instrument_geometry` covers everything `instrument_router` serves, remove the legacy `RouterSpec` (`business_manifest.py:38-43`) entirely.
- **Option 3 (reorder):** move the `instrument_geometry` `RouterSpec` above the legacy one so canonical wins. **Caution:** flips the nut-compensation/check-position contracts to canonical — only safe after confirming no caller depends on the legacy contract.
- Required first: backend/test/CLI/SDK consumer sweep for `/api/instrument/nut-compensation*` and `/soundhole/check-position`; then decide which contract is canonical (stated intent: `instrument_geometry`).

## Appendix C — manifest-discipline bleed-stop (proposed CI check)
Scan `app/**/*.py` for files containing `@router.<verb>(`; flag any whose module is neither referenced by a `RouterSpec(module=...)` in `router_registry/manifests/` nor composed via a known aggregator (`cam/routers/aggregator.py`, `api_v1`) nor on an explicit allowlist. Fail CI on a NET-NEW unmanifested router file. Does not touch the existing 143; only stops new bleed. **Materialized (unrun):** `services/api/scripts/check_manifest_discipline.py` — ratchet against a committed baseline (`scripts/manifest_discipline_baseline.txt`); first run bootstraps the baseline and passes.

## Appendix D — `DRIFT-AUDIT-001` SPRINTS entry (draft, ready to paste; filed as continuation)

```markdown
### DRIFT-AUDIT-001 — Loaded behavior ≠ intended architecture (pattern wrapper)

**Status:** OPEN (deferred — non-MVP, no production caller). Surfaced by CI-RED-015-D live route audit, 2026-05-30.

**Pattern:** Where the *loaded* FastAPI app diverges from the *intended* router ownership/contract. Audit method: dump composed `app.routes`, assert against intent (`scripts/dump_and_assert_routes.py`).

**First worked example — instrument_geometry shadow (CONTINUATION of `INSTRUMENT_ROUTER_MIGRATION_MAP.md` 2026-03-29):**
- The March migration map marked four endpoints "Parallel Implementations — RETAINED, pending schema reconciliation": `POST /api/instrument/nut-compensation`, `/nut-compensation/compare`, `/soundhole`, `/soundhole/check-position`.
- **New runtime fact (015-D):** the **legacy** `instrument_router` wins the live mount (manifested first, `business_manifest.py:39 < :128`), so the **legacy `action_at_nut_mm` contract is the one served**; the canonical `instrument_geometry` handlers are shadowed/dead.
- **Bucket Y** (no production caller). Test-only callers: `test_instrument_router_smoke.py` (legacy contract, legit) and `test_instrument_geometry_router_smoke.py` (canonical contract — **passes deceptively**: 422 from the legacy handler satisfies a lenient `in (200,422)` assert; canonical success path never runs).
- **Latent (R2):** a third `/nut-compensation` in `app/routers/instrument/fretwork_router.py:383` is currently dead (package unmanifested); would join the race if `instrument/` is ever manifested.

**Work, in order (do NOT reorder blindly):**
1. Reconcile the two retained schemas → choose the canonical contract (stated intent: `instrument_geometry`).
2. Fix the geometry smoke test so it stops passing against the wrong handler (xfail w/ reason, or tighten asserts).
3. Correct the ownership inversion (Appendix B) — **after** (1), because flipping the winner is a breaking contract change for the currently-served legacy contract.
4. Close out the `INSTRUMENT_ROUTER_MIGRATION_MAP.md` "RETAINED" row.

**Scope guard:** off the MVP-cut path; does not block CI-RED-015-D closure. Scoped-Y caveat: only `services/api` + `packages/client/src` swept.
```
