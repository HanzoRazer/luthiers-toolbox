# Dependabot Alert Triage & Disposition Decision — 2026-08-09

**Subject:** 65 open Dependabot alerts on `HanzoRazer/luthiers-toolbox` default branch
**Substrate:** `origin/main` @ `0179a032`; alert data pulled live from
`GET /repos/HanzoRazer/luthiers-toolbox/dependabot/alerts?state=open`
**Posture:** READ-ONLY triage. No dependency bumped, no alert dismissed, no manifest edited.
**Purpose:** develop the disposition decision. **Owner ruling required** — options in §6.

---

## 1. The headline number is misleading in both directions

GitHub reports **65 open alerts — 1 critical, 28 high, 35 moderate, 1 low.** That framing overstates
urgency in one respect and understates a structural problem in another.

**Overstated:** 65 alerts are **17 packages**. Alert count inflates because one advisory is filed per
CVE per package, and `axios` alone carries 29. Two packages are 41 of the 65 (63%).

**Also overstated:** 9 of the 65 are in **dead archived code** that ships nowhere.

**Understated:** the reason these accumulated is that nothing in the repository's governance tracks
them. There is no `BR-*` entry, no `CI-RED-*` entry, and no `SPRINTS.md` line for dependency security.
This is an unowned surface, and that is the durable finding.

---

## 2. The most important fact: the machine-control path is clean

| Manifest | Open alerts |
|---|---|
| **`services/api/requirements.txt`** — production Python API | **0** |
| `packages/client/package-lock.json` — Vue client | 55 |
| `archive/…` + `docs/archive/…` — dead experimental code | 9 |
| `services/api/requirements-dev.txt` — Python dev deps | 1 |

**Every alert is in JavaScript tooling, the browser client, or dead code.** The Python service that
performs geometry, CAM, and G-code generation — the path whose output drives a physical machine — has
**zero** open alerts. Nothing here is a machine-safety issue.

---

## 3. Exposure tiers

Severity labels describe the advisory in the abstract. What matters is whether the vulnerable code
path is reachable *here*.

### Tier 0 — No exposure: dead archived manifests (9 alerts)

All 9 are `vite` in paths that are archived, not built, and not deployed:

- `archive/experimental/2026-03/Interactive_Headstock_Generator/…/package.json` (3)
- `archive/experimental/2026-03/Interactive_Neck and Cam _Modules/…/package.json` (3)
- `docs/archive/photo_vectorizer_patches/package.json` (3)

Includes 3 rated `high`. **Real exposure: none.** These inflate the count and dilute attention.

### Tier 1 — Ships to the browser (client runtime)

| Package | Alerts | Direct? | Note |
|---|---|---|---|
| `axios` | 29 | direct, `dependencies` | **20 import sites in `packages/client/src`; zero in `scripts/` or `services/`** |
| `postcss` | 3 | declared in `devDependencies`; Dependabot classifies the lockfile instance `runtime` | discrepancy worth one check — see §7 |
| `ws` | 2 | transitive | memory-exhaustion DoS |
| `form-data` | 1 | transitive | CRLF injection |
| `follow-redirects` | 1 | transitive | medium |

**The axios cluster needs splitting, and this is the key judgment in the triage.** axios is used
**browser-side only**. A large share of its 29 advisories are **Node-adapter-specific** — the
`Proxy-Authorization` leak pair (#4, #5), the `NO_PROXY` incomplete fix (#44), and related proxy /
redirect handling. Those code paths **do not execute in a browser bundle**, so their practical
exposure here is nil.

But the remainder **do** apply to browser usage: prototype-pollution via response handling (#10, #42,
#47), header injection (#46), ReDoS via cookies (#2), and resource-throttling (#1). Those are real,
and they sit on the surface that talks to your API.

Since a single bump fixes all 29 regardless, this distinction does **not** change the action — it
changes the **urgency**, and it means the count should not be read as "29 live browser vulnerabilities."

### Tier 2 — Dev/build toolchain only (attacker must already reach your dev machine or CI)

`vite` (12, incl. the client's own 3 highs), `vitest` (1 **critical**), `rollup`, `esbuild`, `lodash`,
`minimatch` (2), `brace-expansion` (2), `js-yaml` (2), `js-cookie`, `flatted`, `picomatch` (2),
`pytest` (1, Python dev).

**The critical is not critical in this repository.** GHSA-5xrq-8626-4rwp (`vitest` < 3.2.6) requires
that **the Vitest UI server be listening**. The client's scripts are:

```
test:            vitest run
test:watch:      vitest
test:request-id: vitest run …
test:composables:vitest run …
```

**No `--ui` flag appears in any script or workflow.** The precondition is never met in normal use.
It remains worth patching — a developer can start the UI ad hoc — but it is **not an emergency**, and
treating it as one would misallocate the effort.

The `vite` `server.fs.deny` bypasses (#57/#59/#61/#65) are **dev-server** issues, and specifically
Windows-path issues — relevant to this workstation, but only while a dev server is running.

---

## 4. Effort collapse — what it actually takes

| Action | Alerts cleared | Current → required | Risk |
|---|---|---|---|
| Bump **axios** | **29** | `^1.13.2` → `1.18.0` | **Low** — minor bump inside 1.x |
| Delete/ignore **archive manifests** | **9** | n/a | **None** — dead code |
| Bump **postcss** | 3 | `^8.5.8` → `8.5.18` | **Very low** — patch bump |
| Bump **pytest** (dev) | 1 | → `9.0.3` | Low |
| Bump **vite** | 12 | `^5.0.0` → `6.4.3` | **Major version bump (5 → 6)** |
| Bump **vitest** | 1 (the critical) | `^2.1.0` → `3.2.6` | **Major version bump (2 → 3)** |
| Transitive-only resolution | ~10 | via `npm audit fix` / overrides | Low–medium |

**42 of 65 alerts (65%) clear through three low-risk actions** — one minor bump, one patch bump, and
deleting dead manifests. The remaining ~23 concentrate in two major-version migrations plus transitive
resolution.

---

## 5. The blocker nobody has named: there is no working client build gate

This is the finding that should shape the decision, and it connects directly to the maintenance audit.

**BR-021** (`BACKLOG_ADJUDICATION_LEDGER.md`, `MAINTAINABILITY_DEBT`, Wave 3 Rank 1) records — and
`MAINTENANCE_BACKLOG_AUDIT_002` re-witnessed on `origin/main` — that:

- `.github/workflows/client_lint_build.yml:42` — `continue-on-error: true  # TODO: Fix 400+ pre-existing type errors then remove this`
- `.github/workflows/vue_decomposition_gate.yml:31` — `continue-on-error: true`

**The client's build and lint gates are non-blocking.** A `vite` 5 → 6 major bump performed against
that configuration would produce **no automated signal if it broke the build** — CI would stay green
by construction. And the tool that would otherwise catch it, `vitest`, is itself one of the two
migrations, so the runner verifying the bump would be changing in the same window.

**Consequence for sequencing:** the two majors (`vite`, `vitest`) are not merely "bigger bumps." They
are bumps into a subsystem with the verification gate switched off. Either BR-021 is addressed first,
or those bumps require an explicit manual build-and-smoke witness in place of CI.

The cheap tier (axios, postcss, archive, pytest) does **not** carry this constraint.

---

## 6. Options for owner ruling

### Option A — Split the work by risk *(recommended)*

Three independent tranches, each separately authorizable:

1. **Tranche 1 — cheap and safe (42 alerts, ~65%).** Bump `axios` → 1.18.0 and `postcss` → 8.5.18;
   delete or `.github/dependabot.yml`-ignore the three dead archive manifests; bump dev `pytest`. No
   major versions, no gate dependency. Verifiable by the existing client test suite.
2. **Tranche 2 — transitive sweep (~10).** `npm audit fix` plus targeted `overrides` for the
   dev-only transitives that do not resolve cleanly.
3. **Tranche 3 — the two majors (13), gated.** `vite` 5 → 6 and `vitest` 2 → 3, **sequenced after
   BR-021 or behind an explicit manual build witness.** Bump `vitest` first so the verifying runner is
   settled before the build tool moves.

**Why recommended:** it matches the repository's own remediation discipline — bounded tranches, each
with acceptance evidence — and it stops the two genuinely risky bumps from holding 42 easy fixes
hostage.

### Option B — Bump everything in one pass

Fastest to zero alerts. **Rejected on the §5 evidence:** a `vite` major into a non-blocking build gate,
bundled with 16 other packages, gives no way to attribute a regression. If the client breaks, you would
be bisecting 17 packages with CI reporting green.

### Option C — Triage-and-accept: fix Tier 1, formally accept Tier 2

Bump only what reaches the browser (`axios`, `postcss`, `ws`, `form-data`, `follow-redirects`); record
a dated risk acceptance for the dev-toolchain alerts. **Defensible for a solo-operator repo** — the
Tier 2 threat model requires an attacker who already has your dev machine or CI inputs. Lowest effort,
but it leaves the critical unpatched and needs a documented acceptance with a review date, or it decays
into the same unowned drift that produced this backlog.

### Option D — Do nothing

Recorded for completeness. **Not recommended:** the count grows, and the signal-to-noise gets worse
until the alert list is ignored wholesale — which is effectively the current state.

---

## 7. Governance gap — the durable finding

Whatever is ruled on the bumps, **dependency security is currently owned by nothing in this
repository.** No `BR-*` item, no `CI-RED-*` entry, no `SPRINTS.md` line, no `DEFERRED MAINTENANCE`
record. `SPRINTS.md` describes itself as *"the parking lot — the live index where open work registers
at session end"*; 65 alerts standing on the default branch have never registered there.

That is why the count reached 65 — not because any individual alert was hard, but because the surface
had no owner and no review cadence.

**Recommended regardless of which option is chosen:**

1. Register dependency security in `SPRINTS.md` — a `MAINT-DEFER-*` entry if deferred, or a
   `CI-RED-*` entry if it is to be gated in CI.
2. Add `.github/dependabot.yml` with `ignore`/`open-pull-requests-limit` and **path exclusions for
   `archive/**` and `docs/archive/**`**, so dead code stops generating alerts permanently.
3. Set a review cadence, mirroring `SPRINTS_MAINTENANCE.md`'s existing recurring-audit trigger model.

---

## 8. Open questions this triage could not settle

1. **`postcss` scope discrepancy.** `package.json` declares it in `devDependencies`, but Dependabot
   classifies the lockfile instance as `runtime`/`direct`. If it genuinely ships in the browser bundle,
   its 3 alerts belong in Tier 1; if it is build-time only, Tier 2. **One lockfile check settles it.**
   The recommended bump is trivial either way, so this does not block Tranche 1.
2. **Whether the archive manifests should be deleted or ignored.** Deletion removes dead code
   (aligned with Sprint M6's disposition categories); ignoring is reversible. This is a scope call.
3. **The `vite` 5 → 6 migration surface was not assessed.** Breaking changes between those majors were
   not enumerated. Tranche 3 needs that assessment before it is authorized.
4. **Exploitability was not tested for any alert.** This triage reasons from advisory preconditions
   and code-path reachability (e.g. the Vitest UI server is never started, axios never runs in Node).
   Under the defect register's own vocabulary these are **`STATIC-FACT CONFIRMED`**, not `CONFIRMED` —
   no symptom was reproduced.

---

## 9. Provenance

| Field | Value |
|---|---|
| Alert source | `GET /repos/HanzoRazer/luthiers-toolbox/dependabot/alerts?state=open&per_page=100`, 2026-08-09 |
| Alert count at pull | 65 open (1 critical · 28 high · 35 medium · 1 low) |
| Code substrate | `origin/main` @ `0179a032` |
| Dependencies changed | **none** |
| Alerts dismissed | **none** |
| Related | `docs/audit/MAINTENANCE_BACKLOG_AUDIT_002_2026-08-09.md` — BR-021 (§5 blocker), F-11 (unowned-surface pattern) |
