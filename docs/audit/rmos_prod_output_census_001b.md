# RMOS-CONVERGE-001B — Production Output Census

**Status:** PHASE 0 + PHASE 1 COMPLETE — **CHECKPOINT REACHED, AWAITING OWNER RULING**
**Date:** 2026-08-23
**Base SHA:** `96a0c5bfa2007d6555a9d8c73318a8387bcfc278`
**Provenance:** cut from `main` after PR #312 (RMOS-CONVERGE-001A) merged 2026-08-23T22:48:03Z and PR #313 merged 19:39:31Z.

Entry gate verified against `origin/main` before branching:

```text
PR #312                        MERGED
feasibility_authority.py       PRESENT
compute_cam_stub_feasibility   ABSENT
001A owner ruling              PRESENT
```

**Remediation applied in this tranche: the retract capability only.** Every other bypass below is
classified and reported, not patched — per the owner's checkpoint ruling: *the census may discover
and fully classify additional production-output bypasses; it may not take a newly discovered
capability offline without an explicit owner acceptance of that availability change.*

---

## 1. Method

The candidate set was taken from the **live mounted route table** (`app.routes` on the imported
FastAPI app), not from grep. Grep over source finds text; the mounted table finds what is actually
reachable, which is what "live" means. Each endpoint's own source was then read for artifact
evidence (G-code literals, DXF writers, file responses) and authority evidence (feasibility calls,
`RunDecision` construction, persistence).

```text
TOTAL MOUNTED ROUTES                                    1062
keyword candidates                                       293
routes whose source shows machine-artifact emission       62
  ├─ of those, making NO feasibility/policy call          60
  └─ of those, self-minting a literal GREEN RunDecision     5   (LOWER BOUND)
```

**The GREEN figure is a lower bound, not a repository total.** The detector reads each route's own
source for a literal `RunDecision(risk_level="GREEN")`. It cannot see authority minted one level
down: `store_api.persist_run_artifact()` hardcodes `risk_level="GREEN"` for every caller, inside the
fence-*authorized* module, so a route that reaches it self-authorizes without ever naming
`RunDecision`. Five call sites exist today. That is a **different search dimension** — helper-level
rather than route-level — and it is queued (§8), not folded into this census. What the mounted-route
census measured, it measured correctly; it simply did not measure this.

## 2. Inclusion rule

Applied per the handoff: classification follows the route's **declared purpose**, not hypothetical
downstream use. A drawing DXF does not become manufacturing output because an operator could later
import it into CAM.

**IN** — G-code/NC, manufacturing/toolpath DXF, operator/machine execution packs.
**OUT** — UI preview geometry, visualization move lists, drawing/documentation DXF, design-only
export, blueprint vectorization and DXF repair intermediates.

Every exclusion carries one line of evidence. Nothing left the census silently.

---

## 3. Phase 0 — triage summary

| Group | Count | Disposition |
|---|---|---|
| G-code / NC emitters | 25 | **IN** |
| ZIP bundles containing G-code | 3 | **IN** |
| Operator pack | 1 | **IN** (already gated) |
| Drawing / design / vectorization DXF | 31 | **OUT** — declared purpose |
| Simulation input analyser | 1 | **OUT** — consumes G-code, emits analysis |
| Content-addressed attachment fetch | 1 | **OUT** — serves an already-governed stored blob |

**OUT set, with evidence** (declared purpose taken from each endpoint's own docstring):

* `blueprint/*`, `blueprint_cam/*` (11) — *"Convert image/PDF edges to DXF"*, *"Correct DXF
  geometry to match spec"*, *"Densify coarse polylines"*, *"Normalize DXF to R2000"*. Vectorization
  and DXF repair intermediates; they do not declare a machining operation.
* `art-studio/bracing|inlay/export-dxf` (2) — *"Export bracing layout"*, *"Export inlay pattern"*. Design.
* neck / headstock / soundhole / smart-guitar / fretboard / bridge DXF (8) — *"Generate and export
  neck geometry"*, *"Project the ecosphere to DXF bytes"*, etc. Drawing/geometry export.
* `geometry/convert`, `export/translate/dxf`, `legacy_dxf_exports/*` (5) — format conversion.
* `geometry/export` (1) — *"Export geometry to DXF or SVG"*. Drawing.
* `cam/sim/gcode` (1) — *"Simulate G-code from JSON body"*. Consumes G-code; emits analysis.
* `rmos/runs/attachments/{sha256}` (1) — serves a stored, already-governed attachment by hash.

---

## 4. Phase 1 — deep trace of the IN set

| Capability | Routes | Feasibility authority | Decision source | Gate before generation | Verdict |
|---|---|---|---|---|---|
| **Retract** | 4 | canonical (001B) | server | **yes** | **CONVERGED — BLOCKED-BY-DESIGN** |
| Drilling pattern | `cam/drilling/pattern/gcode` | canonical | server | yes | GOVERNED (blocked, no evaluator) |
| Pocketing intent | `cam/pocketing/intent-gcode` | direct evaluator | server | yes | GOVERNED_CANONICAL |
| Operator pack | `rmos/runs_v2/{id}/operator-pack` | export gate on stored risk | server | yes | GOVERNED_CANONICAL |
| **Adaptive G-code** | `cam/pocket/adaptive/gcode` | **none** | **self-minted GREEN** | **no** | **BYPASS — SELF-AUTHORIZING** |
| **Adaptive batch** | `cam/pocket/adaptive/batch_export` | **none** | none | **no** | **BYPASS** |
| **Geometry G-code** | `geometry/export_gcode`, `..._governed` | **none** | **self-minted GREEN** (`_governed`) | **no** | **BYPASS — SELF-AUTHORIZING** |
| **Geometry bundles** | `geometry/export_bundle`, `..._multi` | **none** | none | **no** | **BYPASS** (ZIP contains G-code) |
| **Polygon offset** | `cam/polygon_offset.nc`, `..._governed.nc` | **none** | **self-minted GREEN** (`_governed`) | **no** | **BYPASS — SELF-AUTHORIZING** |
| **Drilling modal** | `cam/drilling/gcode` | **none** | none | **no** | **BYPASS** |
| **Profiling** | `cam/profiling/gcode` | **none** | none | **no** | **BYPASS** |
| **V-carve production** | `cam/vcarve/production/gcode` | **none** | none | **no** | **BYPASS** |
| **Binding** | `cam/binding/channel|purfling/gcode` | **none** | none | **no** | **BYPASS** |
| **Guitar body/neck** | `cam/guitar/flying_v/body/gcode`, `cam/guitar/{id}/neck/gcode`, `neck/gcode/download` | **none** | none | **no** | **BYPASS** |
| **Probe** | `v1/machines/probe/corner|surface` | **none** | none | **no** | **BYPASS** |
| **Post/wrap** | `cam/post/post_v155`, `rmos/wrap/mvp/dxf-to-grbl`, `v1/dxf/cam/gcode` | **none** | none | **no** | **BYPASS** |
| **Vision** | `vision/photo-to-gcode` | **none** | none | **no** | **BYPASS** |

**Two of twenty-nine in-scope routes were governed before this tranche.** The `_governed` suffix
turns out to be a naming family, not an authority family: **four routes wear it while minting their
own GREEN.**

---

## 5. Retract — remediated (owner-ruled)

### Owner ruling — Retract capability

> All four live retract G-code routes are subject to the same RMOS production authority. Until a
> substantive retract feasibility evaluator exists, all four are blocked by design. An ungoverned
> convenience endpoint is not an accepted alternate production path.

### Two defects inside one capability failure

| Routes | Defect |
|---|---|
| `/gcode_governed`, `/gcode/download_governed` | **manufactured authority** — built the G-code, *then* minted `RunDecision(risk_level="GREEN")` and persisted a governed-looking run around output no evaluator had assessed |
| `/gcode`, `/gcode/download` | **bypassed RMOS entirely** — emitted the same G-code, including a `.nc` download with `Content-Disposition: attachment`, with no run, no decision, no hash |

Both built output *before* any authority existed. The `X-ToolBox-Lane: draft` marker on the plain
pair is precisely the "ungoverned convenience endpoint" the ruling rejects.

### Pre-fix witness

```text
POST /api/cam/retract/gcode_governed  -> 200, G-code body,
                                         RunDecision(risk_level="GREEN"), persisted OK run
POST /api/cam/retract/gcode           -> 200, G-code body, no RMOS involvement at all
POST /api/cam/retract/gcode/download  -> 200, retract_direct.nc attachment, no RMOS involvement
```

### Post-fix witness

```text
all four routes -> 409 SAFETY_BLOCKED
                   decision.risk_level = UNKNOWN
                   code = FEASIBILITY_ENGINE_UNAVAILABLE
                   no G21/G90/G0/G1/G2/M30 in any response body
                   no Content-Disposition attachment
                   no X-GCode-SHA256 header
                   X-ToolBox-Lane: governed   (including the former draft URLs)
                   X-Run-ID: <blocked run>
                   BLOCKED RunArtifact persisted, gcode_sha256 = None, attachments = []
```

### Contract change — former draft paths are now governed

This is an explicit compatibility break, not an implementation detail.

| Path | Before 001B | After 001B (now) | After a retract evaluator lands |
|---|---|---|---|
| `POST /api/cam/retract/gcode` | `200` text/plain G-code, `X-ToolBox-Lane: draft`, no run/hash | `409 SAFETY_BLOCKED`, `X-ToolBox-Lane: governed`, `X-Run-ID`, no G-code | still **governed** (will not revert to `draft`) |
| `POST /api/cam/retract/gcode/download` | `200` `.nc` attachment, `X-ToolBox-Lane: draft`, no run/hash | same 409 + governed headers as above | still **governed** |
| `POST /api/cam/retract/gcode_governed` | `200` G-code + self-minted GREEN run | same 409 + governed headers | governed, evaluator-backed |
| `POST /api/cam/retract/gcode/download_governed` | `200` `.nc` + self-minted GREEN run | same 409 + governed headers | governed, evaluator-backed |

The `_governed` suffix is a retained alias of the plain path. Consumers that branched on `X-ToolBox-Lane: draft`, treated `200` as “G-code bytes”, or downloaded the body as `.nc` without checking status must update. In-tree consumer: `packages/client/src/components/toolbox/cam-essentials/useRetractOperation.ts`.

### Truthful operation identity

`tool_id` moved from `"retract_gcode"` (which matched no prefix and resolved to `unknown`) to
`"retract:<strategy>"`, and `resolve_mode` gained a `retract:` prefix. The capability now blocks as
a **known operation with no authorized evaluator**, not as an unknown tool. This adds no engine:
`resolve_feasibility_engine("retract")` is `None`. No retract evaluator was invented.

### Structural, not statement-order

Generation was extracted into pure builders (`_build_simple_retract_gcode`,
`_build_download_retract_gcode`) that contain no authority code and are reached only after
`_authorize_retract` returns. Per D5, **no production seam was added for testing**; the
non-generation witness is observable (no G-code in body, no hash, no attachment).

21 witnesses pass: `services/api/tests/rmos/test_rmos_output_route_convergence.py`.

---

## 6. CHECKPOINT — capability-level ruling requested

The following live capabilities emit machine-consumable output with no authority. **None is
covered by an existing owner ruling**, so none has been touched.

| # | Capability | Routes | Artifact | If converged today |
|---|---|---|---|---|
| 1 | Adaptive G-code + batch | 2 | G-code | **goes dark** — adaptive *plan* is governed, adaptive *gcode* is not. Split authority inside one capability. |
| 2 | Geometry export G-code + bundles | 4 | G-code, ZIP | **goes dark** |
| 3 | Polygon offset `.nc` | 2 | NC | **goes dark** |
| 4 | Drilling modal | 1 | G-code | **goes dark** — note the drilling *intent* lane is governed by its own evaluator; this is a second, ungoverned drilling route |
| 5 | Profiling | 1 | G-code | **goes dark** — same split as drilling |
| 6 | V-carve production | 1 | G-code | **goes dark** — vcarve intent/direct already blocked by 001A; this is a third vcarve route that still emits |
| 7 | Binding channel / purfling | 2 | G-code | **goes dark** |
| 8 | Guitar body / neck | 3 | G-code | **goes dark** |
| 9 | Probe corner / surface | 2 | G-code | **goes dark** — probing may warrant a different safety model than cutting |
| 10 | Post-processor / wrap | 3 | G-code | **goes dark** — these post-process *existing* toolpaths; authority may belong upstream |
| 11 | Vision photo-to-gcode | 1 | G-code | **goes dark** |

**Three observations the ruling should probably weigh.**

*Split authority inside single capabilities.* Drilling, profiling and V-carve each have a governed
lane **and** an ungoverned lane. A caller blocked on the governed one can reach the ungoverned one —
the same structural hole the retract ruling just closed. These are the strongest candidates for the
next cutover group.

*Post-processors and probing may not belong in the same bucket.* Items 9 and 10 emit G-code but do
not plan a cut: probing measures, and post-processors re-render a toolpath decided upstream.
Blocking them may be the wrong shape of fix even though they currently carry no authority.

*Item 1 is a 001A completeness gap.* 001A governed `adaptive/plan` and promoted adaptive to a real
evaluator. `adaptive/gcode` was not in its scope and still self-mints GREEN — so an evaluated plan
can be re-emitted as G-code through an unevaluated route.

---

### Artifact-authority fence

The first push of this tranche turned `Fence Checks (Blocking)` and both `api-verify` runs red on a
single root cause: `artifact_authority` violations in `retract_gcode_router.py`. The scan reported
three NEW and three RESOLVED — the same three violations, at new line numbers. The baseline key is
`fence|file|line|symbol|reason`, so refactoring inside an already-baselined file reads as newly
introduced debt.

Resolved rather than re-baselined. The router now persists through `validate_and_persist()`, which
`FENCE_REGISTRY.json` names as the sanctioned alternative to direct `RunArtifact()` construction,
and imports no `RunArtifact` / `RunDecision` / `Hashes` at all. Three baseline entries deleted.

`validate_and_persist()` had no `event_type` passthrough, which is *why* callers reached around the
fence: the sanctioned helper could not carry the audit label. Added as an optional kwarg; every
existing call site is unchanged.

Two follow-ups are out of scope here and are recorded, not fixed:

1. **The baseline key embeds the line number.** Threading the new kwarg through
   `store_completeness.py` shifted two of its own baselined lines and produced two more phantom NEW
   violations — the identical failure mode, in a second file, within one change. The entries were
   re-keyed (98 in / 98 out). A file+symbol+count key would end this class.
2. **The fence contradicts itself.** `FENCE_REGISTRY.json` prescribes `validate_and_persist()` but
   authorizes only `store.py` and `schemas.py` — not `store_completeness.py`, the module that
   implements it. That module was extracted *out of* `store.py` by WP-3 and baselined as a violation
   instead of inheriting its authorization. Separately, `app/ci/boundary_imports/config.py`
   allowlists two CAM routers that `FENCE_REGISTRY.json` does not list: the executable allowlist and
   the declared one have drifted.

---

## 7. Deferrals preserved

| Item | Status |
|---|---|
| **F9** — override persistence defect | deferred to 001C; not required by any 001B witness |
| **F10** — adaptive `run_id` stripped by `PlanOut` | deferred to 001D; server-side run remains trustworthy, only client visibility is lost |
| **F7** — orphaned `get_run_with_attachments` | deferred to 001C (D6); no 001B in-scope route depends on it — the operator pack and the global attachment fetch both use live paths |
| adaptive `feed_z = feed_xy` derived input | follow-up authority item, untouched |
| String-course / formula recovery (#313) | untouched; zero files in this diff |

## 8. Queued findings — discovered here, deliberately not fixed here

Convergence work surfaces adjacent debt. Recording it is in scope; chasing it is not. None of the
below is a defect in the retract cutover, and none is a reason to widen this tranche.

| Finding | Disposition |
|---|---|
| `store_api.persist_run_artifact()` hardcodes `risk_level="GREEN"` for all callers (`decision_intelligence_service` ×2, `decision_intel_apply_service`, `translator_governance_review_ledger`, `translator_governance_review_matrix`) | **Queue HIGH** — authority defect; needs its own caller trace, not a repo-wide GREEN re-sweep |
| `FENCE_REGISTRY.json` prescribes `validate_and_persist()` but authorizes only `store.py` / `schemas.py`, not `store_completeness.py` — the module that implements it, extracted out of `store.py` by WP-3 and baselined as a violation instead of inheriting authorization | **Queue — governance reconciliation** |
| `app/ci/boundary_imports/config.py` allowlists two CAM routers that `FENCE_REGISTRY.json` does not list; enforced and declared allowlists have drifted | **Queue — same governance reconciliation** |
| Five CAM composables (`useContourOperation`, `useDrillingOperation`, `usePatternOperation`, `useRoughingOperation`, `useProbeOperation` SVG path) do `await response.text()` → `downloadFile(...)` with no status check, so a governed 409 is saved as a `.nc` file | **Queue as a convergence dependency** for those capabilities — see the cutover invariant below |
| `Governance Baseline Diff Report` (`baseline-diff`) computes its report correctly but **403s posting it** — the workflow declares no `permissions:` block, so the default token cannot `issues.createComment`. Its comment step is gated on the `governance` label, so the step had never executed until this PR; it broke on first use. Not a required check | **RESOLVED in this PR** — root cause was the repository default `default_workflow_permissions=read` against a workflow declaring no `permissions:` block. Fixed at the cause with a minimal `contents: read` + `pull-requests: write` grant, not by suppressing the step: the report was always computed correctly and only the POST failed. Same class as the fence resolution — making this PR pass its own governance controls. |
| Retract carries two disjoint strategy vocabularies: `/gcode` takes `direct\|ramped\|helical`, `/gcode/download` takes `RetractStrategyIn.strategy` (`minimal\|safe\|incremental`, default `safe`). Both feed `tool_id=f"retract:{strategy}"`, so one capability emits six peer identities, none validated | **Queue before retract evaluator work** — needs a ruling on one canonical vocabulary or an explicit translation. An evaluator must not be built against six ambiguous peer identities. Pinned meanwhile by `test_retract_strategy_vocabularies_are_split_and_unreconciled` so the split cannot change silently or persist silently into evaluator work — the guard records the state, it does not endorse it. |

### Cutover invariant added by these findings

The client discovery changes the readiness test for the remaining capabilities:

> **A server route is not ready for authority cutover merely because its backend gate is correct.
> Its production consumer must also fail closed on the governed rejection.**

Closing `adaptive/gcode`, the drilling sibling, profiling and V-carve is therefore gated on each
one's client either already rejecting non-2xx machine artifacts or receiving the same narrow
compatibility treatment retract gets. This is not a retreat from convergence — it is what stops
convergence from producing `.nc` files that contain JSON error messages.

---

## 9. Definition-of-done status

Met: complete mounted-route census · every live output route classified · retract blocked before
generation · retract emits no machine output · client authority cannot rescue it · missing evaluator
fail-closed · evaluator ERROR fail-closed · blocked attempts auditable · F9/F10/F7 bounded ·
string-course untouched.

**Not yet met, by design:** `LIVE_UNGOVERNED_OUTPUT = 0`. Twenty-two routes across eleven
capabilities remain ungoverned and are reported above rather than patched, because converging them
takes availability offline and no owner ruling covers them. That is the checkpoint this tranche was
built to reach.
