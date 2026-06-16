# Session handoff — 2026-06-16 — CI-RED-015 characterization pass (next: finish body-solver)

**main HEAD at handoff:** `97c4a1e8` (#134). **Open PRs:** none (all merged/closed). Working tree clean.
**Re-entry rule:** the board moves — re-verify `main` HEAD + open PRs + the live Core CI count before acting.

---

## What this session was doing

Grounding the **CI-RED-015** failure surface **one cluster at a time**, three-way per cluster
(**stale-test** / **real-regression** / **another-mask**), per
`docs/sprints/SPRINT_SCOPE_CI-RED-015_characterization.md`. The ledger is `SPRINTS.md`
(source of truth). Every fix is witnessed **on the heavy Core CI suite**, count taken from the
**authoritative pytest summary** (never subtracted).

### Critical workflow-topology fact (cost time twice — do not re-conflate)
- **Core CI (Consolidated)** = the heavy ~7,300-test suite. **This is where CI-RED-015's failures live** (the 43).
- **"API Tests" / api-smoke** = a 293-test *subset* (a different workflow). NOT the CI-RED-015 surface.
- To witness a CI-RED-015 fix, read the **Core CI** run's pytest summary, not api-smoke.

---

## CI-RED-015 status — 43 failed (witnessed)

**Authoritative:** Core CI run `27630309072` @ `c41fc656` = **`43 failed, 7217 passed`** (was 56).
Count is **witnessed, not subtracted** (subtracting 11 → "45" would have been wrong; #132 cleared 13).

### Clusters CLOSED
- **015-E-1** `board_feet` → STALE-TEST → CLOSED (#125).
- **015-E-2** `fretboard ecosphere` → TEST-ON-WRONG-PATH (misplaced GRBL-pipeline test; production cuts fret slots via the dedicated `fret_slots_router`/`fret_slots_cam`) → CLOSED (#129, test removed; coverage intact via `test_generate_cam_output_from_ecosphere`).
- **015-G** RMOS-persistence (11) → **REAL-REGRESSION** → CLOSED (#132). Root: `export_lifecycle_orchestrator.py:610` set `audit_snapshot.rmos_summary` but `LifecycleAuditSnapshot` (`cam_lifecycle_audit_ledger.py`) never declared the field → `ValueError`, crashing the governed export lifecycle (production-reachable: `export_lifecycle_router.py:68`). Fix = declare the field. **Set-diff verified** #132 cleared 13 (11 RMOS + `test_lifecycle_policy_engine::test_rmos_persistence_respects_policy` + `test_drilling_export_lifecycle::test_drilling_rmos_persistence_works`), **0 regressions**.

### Cluster GROUNDED but OPEN — needs a USER decision
- **015-H** geometry-authority (10) → **NEVER-WIRED ROUTER** (3rd distinct shape; not regression, not stale-test).
  `geometry_authority_router.py` (added `d5033799`, `prefix=/api/cam/geometry-authority`, full routes) is **never registered in any manifest** → all routes 404; tests correctly expect 200.
  **Governance checked:** router is safe-by-design (CAM Dev Order **7T**: no execution, no machine output); **C2-A Geometry Authority is RATIFIED**; never deliberately de-mounted. → **leans FORGOTTEN WIRING; likely fix = add one `RouterSpec`** to the cam manifest (low-risk given 7T).
  **CAVEAT (why it's a USER call, not auto):** geometry-authority is in *active* arbitration with a flagged *authority-chain violation* (`RUNTIME_BOUNDARY_INVENTORY.md`: chain terminates at TopologyBuilder without Translation→Authorization Gate) + one packet marks it *"unresolved."* **Do NOT mount without governance-owner confirmation.** Sub-case: `test_validate_reference` → `KeyError`, separate (so mounting clears ~9 of 10).

### Clusters REMAINING — uncharacterized (the next passes)
From run `27630309072`:
- **body-solver/IBG (11)** — `tests/test_body_solver_integration.py`. **IN PROGRESS — STOPPED MID-GROUNDING.** It is a **MIXED cluster** (multiple roots, unlike RMOS's single root). Confirmed so far: at least **401 Unauthorized** (`test_solve_from_landmarks_returns_valid_model` expects 200 → gets 401 — auth required where test assumes none) and a **confidence-threshold** failure (`test_solve_dreadnought_returns_valid_dimensions`: `assert 0.455 > 0.5` — solver confidence below the test's threshold). **NEXT ACTION: get the full per-test error breakdown and classify each sub-cause three-way** (401 = real auth-gating vs test-needs-auth; confidence = stale threshold vs real solver regression).
- **lifecycle-policy (3)** — was 4; #132 cleared 1 (the rmos one). The other 3 are a separate sub-cause (the 3 may relate to the orchestrator/policy engine — re-read errors).
- **body-geometry-repair (4)**, **morphology-spine (3)**, + **singletons (~12)**: saddle_compensation, rmos_runs_e2e, outline_reconstructor, morphology_harvest, ibg_* (3-4), body_export_bridge, artifact_constitutional, operation_capability.
- **Possible shared-root cluster to watch:** `test_drilling_intent_migration` + `test_pocketing_intent_migration` (and a route-enumeration test) fail on `AttributeError: '_IncludedRouter' object has no attribute 'path'` — a route-enumeration bug hitting an `_IncludedRouter` mount object. Likely ONE root across several tests — ground it as a cluster.

---

## Standing governance / enforcement (not CI-RED-015)

- **CI-RED-021 (merged #131) — THE headline standing item.** `main` has **ZERO branch protection** (classic 404, active rules `[]`, ruleset disabled). So **every gate is advisory** — Core CI (red, 43 real failures), the repaired fence (CI-RED-004), contract checks; and `.github/CODEOWNERS` (`@toolbox-governance` over the CI/fence code) is **inert**. This is the structural root of #114. **FIX = enable branch protection (required status checks + code-owner review) — USER ACTION, a terminal cannot do it.** Closes **004 + 021 together** and makes every honest gate this session built actually *guard* main. *This is the single highest-leverage item and it is yours.*
- **CI-RED-004** (fence): code green; pending the 021 required-status enforcement (same USER action).
- **CI-RED-019** (routing-truth masked by setuptools editable-build): OPEN. Cause known = `services/api/pyproject.toml` flat-layout (`Multiple top-level packages: app/data/metrics/test_support`); fix = add `[tool.setuptools.packages.find]`. Fixing UNMASKS routing-truth (Phase-2b), does not close.
- **CI-RED-020** (api-smoke server-unreachable, `curl 127.0.0.1:8000` refused; app loads then HTTP never ready): OPEN, cause TBD; distinct from 019 (app DOES start).

## Backlog (CAM Enhancements section, merged #134)
- Generic `dxf-to-grbl` thin-feature handling (optional, R2000/pro-tier; delegate to existing slot generator, do NOT add a `compute_plan` strategy — feature-parity).
- Type the `rmos_summary` contract (optional, quality — denormalizes already-typed `report.rmos`).
- **Determinism TEST (MEDIUM):** `deterministic_hash` is a **provenance parent-hash** (`translation_artifact_provenance.py:305` → `parent_audit_hashes`); folding the non-deterministic `run_id` in would break the provenance chain. #132 added only an advisory comment — a test guards-by-enforcement.

## Resolved earlier this session (context)
- **Railway deploy** (#121/#122/#123): API container crash was unpinned `fastapi` 0.137.0 + `goals_router` empty-prefix (fixed #121); `fastapi` pinned (#122); the redundant/mis-targeted `railway-deploy.yml` CLI workflow **removed** (#123) — deploys owned by the **Railway GitHub App on project reliable-elegance** (`644a5eb9`). `RAILWAY_TOKEN` is project-scoped to the OLD project (exquisite-balance) — do NOT re-point a CLI deploy without an account/reliable-elegance token. (See memory `project_railway_deploy_ownership`.)

## MVP tag
Still in **decision phase** — no consolidated tag-readiness/release-notes doc on `main` (the decision handoff `SESSION_HANDOFF_2026-06-12_MVP_TAG_DECISION_NEXT.md` is on an unmerged branch). **When cut, name CI-RED-021 (gates unenforced) as a known-limitation** in the release notes, alongside BCAM-cut and api-verify.

---

## Disciplines that held all session (carry them)
1. **Witness on the enforcing surface, authoritative count.** Heavy Core CI suite, pytest summary — never subtract, never api-smoke.
2. **Cited risks dissolve on grounding; the real find is usually uncited.** 4 PR-reviews in a row: the reviewer's risks grounded out as non-issues; the substantive issue was uncited (and once, in our *own* ledger wording — the "intent/op singleton" mislabel caught by set-diff).
3. **Ground the seam/target before building** — caught a would-be duplicate (typed slot strategy already exists), caught the never-wired router.
4. **Verify before a status flip** — caught a false-close on 015-E (the fretboard half was failing while board_feet was fixed).
5. **Honest ≠ green ≠ enforced.** The gates now tell the truth (this session's work); they are not yet *guards* (CI-RED-021, the USER action).

## Immediate next action on re-entry
1. Re-verify `main` HEAD + open PRs + the live Core CI count.
2. **Finish grounding body-solver/IBG (11)** — full per-test error breakdown, classify each sub-cause three-way (it's a MIXED cluster: 401-auth + confidence-threshold + possibly more). One fix-PR per cause-class.
3. Get the **geometry-authority (015-H) governance decision** (mount via `RouterSpec` vs hold).
4. Continue remaining clusters; consider grounding the `_IncludedRouter` `AttributeError` shared-root (drilling/pocketing intent_migration) as its own cluster.
