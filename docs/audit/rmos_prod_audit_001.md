# RMOS-PROD-AUDIT-001 — Canonical Manufacturing Round Trip (Pass 1)

**Status:** PASS 1 COMPLETE (static map) — 2026-08-22. Read-only evidence artifact.
**Not a schedule. No remediation authorized. No item selected. No Dev Order.**

**Addendum (2026-08-27).** Route-level classifications in this document remain
historical evidence. Where they conflict with the capability-level census in
[`rmos_manufacturing_authority_map_001.md`](rmos_manufacturing_authority_map_001.md)
and `services/api/app/rmos/manufacturing_authority_registry.json`, the newer
registry is the capability identity — **once Stage 2 dispositions are populated**.
Stage 2 of that census now populates capability dispositions. It still
authorizes **no remediation**. Route-level rows below remain historical.
This addendum does not rewrite the findings below.

**Charter.** Prove whether the Resource Management Operating System still performs its intended
role as the **bidirectional manufacturing spine** on current `main` — carry a manufacturing
decision forward (intake → feasibility → decision → persistence → export → hash) and expose it
back upstream (retrieval → integrity → provenance) without breaking identity, safety status, or
audit history. This pass is a **static map only**; dynamic execution is explicitly out of scope
(see "Not this pass").

**Controls (same as the formula census).** Read-only; single artifact (`docs/audit/rmos_prod_audit_001.md`);
no code, no `SPRINTS.md`, no commit, no Dev Order, no remediation. Server spine first; client
RMOS surface is a follow-up note (invariant 7).

**Static verdict vocabulary:** `STATICALLY CONFIRMED` · `STATICALLY REFUTED` · `WITNESS REQUIRED`
· `INSUFFICIENT EVIDENCE`.
**Authority source (per stage):** `code` · `contract/schema` · `ADR` · `runtime config (env)` ·
`documentation`.

**Not this pass:** start server · execute GREEN/YELLOW/RED scenarios · attempt RED override ·
corrupt artifacts · mutate DB/files · run live production workflow.

**Taxonomy (RMOS 12-family, as given):** `FUNCTIONING_AS_DESIGNED` · `FUNCTIONING_WITH_DOC_DRIFT`
· `LIVE_WORKFLOW_GAP` · `SAFETY_CONTRACT_DRIFT` · `BIDIRECTIONAL_BREAK` · `AUDIT_CHAIN_BREAK` ·
`PERSISTENCE_SPLIT` · `CANONICAL_PLUS_SHIM` · `LEGACY_RMOS_GENERATION` · `ORPHANED_CAPABILITY` ·
`INCOMPLETE_MIGRATION` · `INSUFFICIENT_EVIDENCE`. (No new class proposed this pass.)

---

## Canonical path — identified

The two "intent" routers are **not** the canonical round trip — they are normalization/delegation
shims (`CANONICAL_PLUS_SHIM`): `routers/rmos_cam_intent_router.py` (`POST /api/rmos/cam/intent/normalize`,
normalize-only) and `routers/cam_roughing_intent_router.py` (`POST /api/cam/roughing/gcode_intent`,
delegates to the roughing round trip, surfaces no `run_id`).

**The canonical production round trip** is the consolidated CAM toolpath routers + the adaptive
package, all sharing one pattern:

```
server feasibility (compute_feasibility_internal)
  → SafetyPolicy.extract_safety_decision → should_block
    → persist_run(RunArtifact)  [BLOCKED on block, else OK]
      → G-code build → sha256_of_text(body)
        → persist_run(OK artifact, gcode_sha256)
          → export headers X-Run-ID / X-GCode-SHA256 / X-ToolBox-Lane: governed
```

Representative canonical callers (all live): `cam/routers/toolpath/roughing_router.py` (`roughing_gcode`),
`vcarve_router`, `helical_router`, `biarc_router`, `relief_export_router`, `drilling/drill_pattern_router`,
`rosette/rosette_toolpath_router`; and `routers/adaptive/plan_router.py` (`plan`) + `routers/adaptive/gcode_router.py` (`gcode`).
Shared server engine: `rmos/api/rmos_feasibility_router.py::compute_feasibility_internal` (`@safety_critical`).
Single run store: `rmos/runs_v2/store.py::RunStoreV2` (via `persist_run`). All registered live through
`router_registry/manifest.py`.

**Engine coverage split (decisive for the safety verdict):** `compute_feasibility_internal`
dispatches `saw`→ real `SawEngine`, `rosette`→ real manufacturability scorer, but **all CAM modes**
(`vcarve/roughing/drilling/biarc/relief/adaptive/helical`) → `compute_cam_stub_feasibility`, which
**returns GREEN by default** ("Phase 2 infrastructure… Future: wire to real engines").

---

## Stage matrix

Fields: Implementation · Authority source · Contract/schema · Direct caller/consumer · Persistence/identity
· Safety authority · Liveness · Static verdict · Witness required? · Drift/classification.

| Stage | Implementation | Authority src | Contract/schema | Caller/consumer | Persistence/identity | Safety authority | Live | Static verdict | Witness? | Drift / class |
|-------|---------------|---------------|-----------------|-----------------|----------------------|------------------|------|----------------|----------|---------------|
| **Intake** | Canonical toolpath/adaptive routers; intent routers are shims | code | `RoughReq`/`PlanIn` etc. (geometry/params only; **no** GREEN/RED/decision field) | frontend SDK → router | — | request carries params, not a decision | ✅ | `STATICALLY CONFIRMED` | no | intent routers = `CANONICAL_PLUS_SHIM` |
| **Feasibility** | `compute_feasibility_internal` (`@safety_critical`) → saw/rosette real engines; **CAM → GREEN-default stub** | code | `{"safety":{risk_level,score,block_reason,warnings}}` | canonical routers (in-process) + `POST /api/rmos/feasibility` | — | **server-computed for saw/rosette; stubbed GREEN for CAM** | ✅ | `STATICALLY CONFIRMED` (server path) **+ two gaps below** | partial | **F1, F2** |
| **Run identity** | `create_run_id()` = `run_{uuid4().hex}` | code | governance contract | all writers | one minted durable ID | n/a | ✅ | `STATICALLY CONFIRMED` | no | `FUNCTIONING_AS_DESIGNED` |
| **Decision** | `SafetyPolicy.should_block` / `extract_safety_decision` | code + runtime config (env) | `RiskLevel` enum; `RMOS_BLOCK_ON_RED`/`TREAT_UNKNOWN_AS_RED` (default true) | canonical routers | risk_level in `RunDecision` | **fail-closed: RED & UNKNOWN block by default; invalid→UNKNOWN→block** | ✅ | `STATICALLY CONFIRMED` (gate logic sound) | no | `FUNCTIONING_AS_DESIGNED` (input poisonable — F1/F2) |
| **Persistence** | `persist_run`→`RunStoreV2.put`; **3 writers** | code | `RunArtifact`/`RunDecision`/`Hashes` (`runs_v2/schemas.py`) | canonical (direct); `create_run_from_feasibility` (art_studio); workflow bridge | **one store, RunStoreV2** | canonical preserves RED; secondary writers weaker | ✅ | `STATICALLY CONFIRMED` (one store) | no | **F5** — write-path fan-in, not a store split |
| **Override** | `runs_v2/override_service.apply_override` | code + runtime config (env) | `OverrideRequest/Record` (`schemas_override.py`) | `router_override` (`POST /{run_id}/override`) | content-addressed audit attachment; `decision.risk_level` **never mutated** | **fail-closed: RED needs `RMOS_ALLOW_RED_OVERRIDE=1` + `acknowledge_risk` + scope match** | ✅ | `STATICALLY CONFIRMED` | confirm-only | **F4** (doc conflict) |
| **Export** | `runs_v2/exports.export_operator_pack` | code + runtime config (env) | operator-pack ZIP (canonical names) | `GET /{run_id}/operator-pack` | pack assembled from same run's content-addressed attachments | **fail-closed: RED→403 unless override+env; YELLOW→403 unless override; GREEN passes** | ✅ | `STATICALLY CONFIRMED` (sound *given* truthful stored risk) | no | linkage OK; depends on F1/F2 input |
| **Hash/integrity** | `hashing.sha256_of_obj` (canonical `sort_keys`); `attachments.verify_attachment` | code | SHA256 content-addressing (shard `s[0:2]/s[2:4]`) | run creation; `/attachments/verify` | filename = hash | recompute+compare → `hash_mismatch` on drift | ✅ | `STATICALLY CONFIRMED` (mechanism) | round-trip + negative | `FUNCTIONING_AS_DESIGNED` |
| **Retrieval** | `api_runs.read_run`; `api_runs_attachments` | code | `RunArtifact` JSON incl. hashes/decision/feasibility/attachments | `GET /api/rmos/runs/{id}`, `/{id}/attachments/verify` | by run_id | integrity via `/verify` | ✅ | `STATICALLY CONFIRMED` (backend live) | UI-coherence | `FUNCTIONING_AS_DESIGNED` |
| **Upstream return** | backward path present; **`get_run_with_attachments` orphaned** | code | — | live: `/verify` + `read_run`; orphaned: service fn (no HTTP caller) | by run_id | integrity status exposed | ✅/⚠️ | `STATICALLY CONFIRMED` (path exists) | prod-UI witness | **F7** `ORPHANED_CAPABILITY` |

---

## Findings

**F1 — Client-supplied `safety` is echoed through the `@safety_critical` canonical entry. `SAFETY_CONTRACT_DRIFT` (authority bypass). STATICALLY CONFIRMED (path); end-to-end effect WITNESS REQUIRED.**
`compute_feasibility_internal` declares "NEVER trusts client-provided feasibility" and strips
`clean_req.pop("feasibility", None)` — but **only `feasibility`, not `safety`**. The per-engine
functions each contain a test hook: `if isinstance(req.get("safety"), dict): return {…"safety": safety…}`
(saw L138-145, rosette, stub). `SafetyPolicy.extract_safety_decision` then reads risk from nested
`safety` (L143). So a request body carrying `{"safety":{"risk_level":"GREEN"}}` survives the strip,
is echoed by the engine, and is read as the authoritative decision. The strip-list (`feasibility`)
does not match the echo key (`safety`); the "test hook" has no env/test guard. *Authority source:
code contradicts its own stated contract.* Witness (Pass 2): submit a saw/rosette request whose real
engine would return RED, with client `safety:GREEN`, and observe whether the run persists GREEN and
exports.

**F2 — CAM toolpath modes use GREEN-default stub feasibility. `INCOMPLETE_MIGRATION` / `LIVE_WORKFLOW_GAP`. STATICALLY CONFIRMED.**
`compute_cam_stub_feasibility` returns GREEN by default for `vcarve/roughing/drilling/biarc/relief/adaptive/helical`
— the exact modes the canonical toolpath routers serve. Real engines exist only for `saw` and
`rosette`. So for the CAM manufacturing round trip, the safety computation is presently a
pass-through; the gate downstream is sound but receives GREEN. *Authority source: code + code
comment ("Future: wire to real feasibility engines").*

**F3 — Feasibility fails OPEN to YELLOW on engine error. `SAFETY_CONTRACT_DRIFT` (deliberate). STATICALLY CONFIRMED.**
`compute_saw_feasibility` (and peers) catch engine exceptions and return `risk_level="YELLOW"`,
`block_reason=None` — comment: "Governance: fail-open to YELLOW so manufacturing is not blocked."
YELLOW is overridable without the RED env flag. Contrast with the RED default (fail-closed) and the
gate's `TREAT_UNKNOWN_AS_RED` (an engine *error* could instead map to UNKNOWN→block; here it is
downgraded to YELLOW). *Authority source: code.*

**F4 — RED-override doc conflict; code is fail-closed + gated + audited. `SAFETY_CONTRACT_DRIFT` (documentation). STATICALLY CONFIRMED (code).**
`override_service.apply_override` requires status `BLOCKED`, and for RED scope requires **both**
`RMOS_ALLOW_RED_OVERRIDE=1` **and** `acknowledge_risk=true`, scope-matched, single-use, with a
content-addressed audit attachment — and **never mutates `decision.risk_level`** (history stays
authoritative). This matches `docs/cam/safety-rmos.md`; the operator-concepts guide's "RED cannot be
overridden" is documentation drift (reconcilable as "not overridable from the operator seat without
an admin env flag"). *Authority source: `code` + `runtime config (env)` vs. `documentation`.*

**F5 — Three run-writers with inconsistent risk derivation; one store. `PERSISTENCE_SPLIT`-adjacent (write-path fan-in). STATICALLY CONFIRMED.**
All writers land in one `RunStoreV2` (not a store split), but risk derivation differs:
(1) canonical routers → `SafetyPolicy` decision, persist BLOCKED preserving RED;
(2) `services/rmos_run_service.create_run_from_feasibility` (art_studio path) → auto-maps RED→BLOCKED;
(3) generic helpers in `store_api.py` — `persist_run_artifact` **hard-codes GREEN/OK**, and
`store_artifact._status_risk` maps **`BLOCKED→YELLOW`** (risk-level loss / inversion). The canonical
manufacturing path is sound; the secondary helpers carry weaker/again-GREEN semantics and should not
be used for gated decisions. *Authority source: code.* (Workflow bridge instantiates its own
`RunStoreV2()` rather than the singleton — same class/on-disk store; noted, not a split.)

**F6 — Retract "governed" lane persists GREEN runs with no feasibility. `LIVE_WORKFLOW_GAP`. STATICALLY CONFIRMED.**
`routers/retract/retract_gcode_router.py` `/gcode_governed` + `/gcode/download_governed` create RMOS
runs hard-coding `RunDecision(risk_level="GREEN")` and never call the feasibility engine. A live
run-creating, G-code-emitting path that bypasses the safety computation entirely. *Authority source: code.*

**F7 — `get_run_with_attachments` is orphaned. `ORPHANED_CAPABILITY`. STATICALLY CONFIRMED.**
The service function `services/rmos_run_service.get_run_with_attachments` (with `verify_integrity` →
`integrity_verified`) — the architecture's cited backward-integrity ingredient — has **no HTTP caller**.
The live backward-integrity path is `api_runs_attachments` `GET /{run_id}/attachments/verify`. Capability
exists twice: one wired, one orphaned.

**F8 — Core spine functions as designed (positives). `FUNCTIONING_AS_DESIGNED`. STATICALLY CONFIRMED.**
One durable minted run identity (`run_{uuid4().hex}`); canonical deterministic hashing (`sort_keys`);
content-addressed attachment verification with mismatch detection; the `SafetyPolicy` gate is
fail-closed by default (RED/UNKNOWN block); the export gate is fail-closed (RED/YELLOW → 403 without
override); the override path preserves original risk_level and writes an audit attachment; backward
retrieval endpoints are live. The *framework* is intact — the gaps are in feasibility **input**
(F1/F2/F3), secondary write-paths (F5/F6), and one orphaned backward fn (F7).

**F9 — RMOS identity lineage drift. `LEGACY_RMOS_GENERATION` (lineage/doc). Treat as doc drift until runtime proves otherwise.**
Three documented names (Run Manufacturing Operations System / Run Management & Operations System /
Resource Management Operating System). No runtime divergence observed; classify as documentation
lineage drift, not a code split.

---

## Invariant scorecard

| # | Invariant | Static verdict | Class |
|---|-----------|----------------|-------|
| 1 | One canonical run identity | `STATICALLY CONFIRMED` (one store, minted id) — 3 writers, canonical preserves risk | `FUNCTIONING_AS_DESIGNED` / F5 |
| 2 | Server-computed safety authority | **MIXED** — gate sound & server-computed for saw/rosette; **F1 client-echo path + F2 CAM stub GREEN** undercut it on the CAM path | `SAFETY_CONTRACT_DRIFT` + `INCOMPLETE_MIGRATION` |
| 3 | Fail-closed safety behavior | `STATICALLY CONFIRMED` fail-closed for RED/override/export; **F3 fail-open-to-YELLOW on engine error** is the exception | `FUNCTIONING_AS_DESIGNED` + F3 drift |
| 4 | Content integrity survives round trip | `STATICALLY CONFIRMED` (mechanism); round-trip + negative = `WITNESS REQUIRED` | `FUNCTIONING_AS_DESIGNED` |
| 5 | Decision → export linkage | `STATICALLY CONFIRMED` (run_id-bound, gated) — sound given truthful stored risk (F1/F2) | `FUNCTIONING_AS_DESIGNED` |
| 6 | Bidirectional retrieval works | `STATICALLY CONFIRMED` (backend live); prod-UI coherence + orphaned fn = follow-up | `FUNCTIONING_AS_DESIGNED` / F7 |
| 7 | RMOS remains internal | `INSUFFICIENT EVIDENCE` this pass (server-first scope) — client RMOS API/types present, classify next | follow-up |

**Bidirectional verdict (the charter question):** the spine **statically supports** the full loop —
forward (intake→feasibility→decision→persist→export→hash) and backward (retrieve→verify→provenance),
with identity, audit history, and risk_level preserved by the canonical path. The **integrity of that
loop is undercut on the CAM path** by feasibility-input weakness (F1 client-echo, F2 stub-GREEN), not
by a broken persistence/export/retrieval chain. No `BIDIRECTIONAL_BREAK` or `AUDIT_CHAIN_BREAK`
observed statically.

---

## Narrow dynamic-witness list for Pass 2 (evidence-driven, not blind TC-01…12)

Only these are actually needed to close what static analysis could not settle:

- **W1 (F1, highest priority).** Saw/rosette request whose real engine returns RED, submitted with
  client `{"safety":{"risk_level":"GREEN"}}` → does the run persist GREEN and export? (Confirms/refutes
  the client-echo bypass end-to-end.)
- **W2 (F2).** Any CAM-mode request → confirm persisted decision is stub-GREEN regardless of design
  (documents the pass-through).
- **W3 (F3).** Force a feasibility engine error → confirm the run proceeds as YELLOW, not blocked.
- **W4 (invariant 4).** Create run with attachments → `/attachments/verify` `ok:true`; corrupt a
  disposable blob → `ok:false, hash_mismatch` (positive + negative integrity witness).
- **W5 (invariant 3 / F4).** Real RED run → operator-pack export = 403; override without env = 403;
  override with `RMOS_ALLOW_RED_OVERRIDE=1` + `acknowledge_risk` → OK + audit attachment; confirm
  `decision.risk_level` still RED after override.
- **W6 (F6).** Retract `/gcode_governed` → confirm it persists a GREEN run with no feasibility record.
- **W7 (invariant 6/7).** Confirm the production-facing caller retrieves via `GET /api/rmos/runs/{id}`
  + `/attachments/verify` (and whether the client consumes RMOS internally vs. leaks it — invariant 7).

This replaces the blind twelve-scenario matrix with seven targeted witnesses tied to specific
static findings.

---

## Pass 1 status

Static map complete. **Stop here** per charter. No code, no execution, nothing mutated; single new
artifact created. Pass 2 (the seven witnesses above) requires separate owner authorization and will
involve live execution (server + `runs_v2` DB), run per the standing environment convention.

**Authorization state:** NO REMEDIATION AUTHORIZED · NO ITEM SELECTED · NO DEV ORDER DRAFTED.

---

# Addendum — RMOS-CONVERGE-001A implementation & witnesses (2026-08-23)

*Appended, not edited. The Pass-1 static findings above stand as written; this section records
what happened when they were taken to runtime.*

**Increment:** RMOS-CONVERGE-001A — canonical feasibility authority cutover
**Base:** `origin/main` `6dbb2791`
**Disposition summary:** F1 closed · F2 closed · F3 closed · F4 documentation reconciled ·
F5/F6/F7 deferred unchanged · **three new findings (F8, F9, F10) discovered at runtime**

---

## D8 — runtime witness before declaration of closure

Both witnesses were taken on this tree by driving `compute_feasibility_internal` directly, with
the pre-fix router restored from `origin/main` for the first.

### F1 pre-fix witness — CONFIRMED (client `safety` carries authority)

```text
=== PRE-FIX F1: client-supplied safety GREEN ===
saw:default        risk=GREEN  block=False  meta={'note': 'echoed safety from request (test hook)'}
rosette:default    risk=GREEN  block=False  meta={'note': 'echoed safety from request (test hook)'}
roughing:default   risk=GREEN  block=False  meta={'note': 'echoed safety from request (test hook)'}
vcarve:default     risk=GREEN  block=False  meta={'note': 'echoed safety from request (test hook)'}
adaptive:plan      risk=GREEN  block=False  meta={'note': 'echoed safety from request (test hook)'}
```

The static path Pass 1 traced is real end to end: `{"safety": {"risk_level": "GREEN"}}` survives
the `feasibility`-only strip, is echoed by the per-engine test hook, and is read by
`SafetyPolicy.extract_safety_decision` as the authoritative decision.

### F1 post-fix witness — CLOSED

```text
=== POST-FIX F1: client authority keys ===
client safety          -> risk=RED  block=True  meta=None
client feasibility     -> risk=RED  block=True  meta=None
client decision        -> risk=RED  block=True  meta=None
client risk_level      -> risk=RED  block=True  meta=None
client export_allowed  -> risk=RED  block=True  meta=None
```

Every authority-shaped key is stripped at one boundary, and no echo path survives (`meta` is gone
because the hooks are gone). Note that the pre-fix `saw:default` row read YELLOW and the post-fix
row reads RED — see F8.

### F2 disposition — CLOSED, with one mode promoted and six failed closed

`compute_cam_stub_feasibility` is deleted. Engines resolve from an explicit table with no default.

| tool_id | mode | pre-fix | post-fix |
| --- | --- | --- | --- |
| `saw:*` | saw | YELLOW (fail-open, see F8) | **real verdict** (RED on the probe design) |
| `rosette:*` | rosette | YELLOW (fail-open, see F8) | **real verdict** (YELLOW, real calculator output) |
| `adaptive:plan` | adaptive | GREEN (stub) | **real rule engine** — GREEN when sane, RED on F002/F004 |
| `roughing:*` | roughing | GREEN (stub) | UNKNOWN · `FEASIBILITY_ENGINE_UNAVAILABLE` · **blocked** |
| `vcarve:*` | vcarve | GREEN (stub) | UNKNOWN · `FEASIBILITY_ENGINE_UNAVAILABLE` · **blocked** |
| `helical:gcode` | helical | GREEN (stub) | UNKNOWN · `FEASIBILITY_ENGINE_UNAVAILABLE` · **blocked** |
| `biarc_gcode` | unknown | UNKNOWN · blocked | UNKNOWN · blocked *(unchanged)* |
| `relief_dxf` | unknown | UNKNOWN · blocked | UNKNOWN · blocked *(unchanged)* |
| `drill_pattern_gcode` | unknown | UNKNOWN · blocked | UNKNOWN · blocked *(unchanged)* |

**`adaptive` was promoted because its input contract genuinely matches**, field for field:
`PlanIn` carries `tool_d`, `stepover`, `stepdown`, `z_rough`, `feed_xy`, `safe_z`, `strategy`,
`climb`, `smoothing`, `margin`, `units`, `loops` — exactly what
`app/rmos/feasibility/schemas.py::FeasibilityInput` requires. That is dispatch to an existing
evaluator, not new physics. Two fields have no source in the plan request (`layer_name`, which no
rule reads, and `feed_z`, so rule F011 is inert); both are declared in the result's
`details.derived_inputs` rather than passed off as measured.

**The other six were not promoted** because no existing evaluator's input contract matches:

- the `app/rmos/feasibility` rule engine needs `tool_d` + `z_rough` + `safe_z` + `strategy`;
  `RoughReq` has no tool diameter, `BiarcReq` / `HelicalReq` / `ReliefDXFExportRequest` have neither;
- `app/cam/drilling/feasibility.py` needs `hole_diameter_mm`; `DrillParams` has no tool diameter;
- `app/cam/pocketing/feasibility.py` and `app/cam/profiling/feasibility.py` need
  `plunge_rate_mm_min` + `retract_z_mm` + geometry these requests do not carry.

Supplying those would be inventing inputs to make a lane green, which D4 forbids. They fail closed.

### Engine-error disposition (F3) — CLOSED

Evaluation failure now returns `ERROR` + `FEASIBILITY_ENGINE_ERROR`, which
`SafetyPolicy.should_block` treats as blocking under `RMOS_TREAT_UNKNOWN_AS_RED` (default true).
The former `risk_level="YELLOW", block_reason=None, score=50.0` fail-open — comment
*"Governance: fail-open to YELLOW so manufacturing is not blocked"* — is gone.

### F4 — documentation reconciled

`docs/RMOS_CONCEPTS_GUIDE.md` said *"RED operations cannot be overridden."* Corrected to the
behaviour the code implements: RED is blocked by default; it proceeds only through the explicitly
enabled (`RMOS_ALLOW_RED_OVERRIDE=1`), acknowledged, audited administrative override; and the
original RED decision is never rewritten. No code change.

---

## New findings discovered at runtime

### F8 — the saw/rosette "real engines" never ran. `SAFETY_CONTRACT_DRIFT` (dead adapter). RUNTIME-CONFIRMED. **CLOSED HERE.**

Pass 1 recorded saw and rosette as *server-computed by real engines*. At runtime, on `origin/main`,
**every** call raised and was swallowed by the F3 fail-open, so both lanes answered a constant
`YELLOW` / `score=50.0` regardless of input:

```text
pydantic_core.ValidationError: 4 validation errors for RosetteParamSpec
  ring_count / pattern_type / depth_mm / petal_count
    Extra inputs are not permitted [type=extra_forbidden]
```

The router built its design spec from `art_studio.schemas.RosetteParamSpec`, which is
`extra="forbid"` and models a rosette as `outer_diameter_mm` + `inner_diameter_mm` + `ring_params`.
`feasibility_scorer` reads `design.ring_count` — a field that schema does not have. The
`except ImportError: from ..api_contracts import RosetteParamSpec` fallback was dead, because
`api_contracts` prefers the same `art_studio` schema. So the two findings compounded: a broken
adapter (F8) hidden by a fail-open (F3), presenting as a plausible YELLOW.

Closed by binding the adapter to the contract the scorer actually consumes (`ScorerDesignSpec` in
`rmos_feasibility_router.py`). Post-fix the lanes produce differentiated verdicts with real
calculator output — saw RED on heat/deflection, rosette YELLOW on chipload/rim-speed.

*This is the material difference from Pass 1 that §8 asks to be reported: the safety verdict for
saw/rosette in the Pass-1 table was an artifact of a swallowed exception, not an evaluation.*

### F9 — `override_service.apply_override` raises before it writes. `LIVE_WORKFLOW_GAP`. RUNTIME-CONFIRMED. **DEFERRED to 001C.**

```text
TypeError: put_json_attachment() got an unexpected keyword argument 'data'
```

`override_service.py:246` calls `put_json_attachment(data=..., kind=..., filename=..., run_id=...)`
and unpacks two values. `attachments.py:124` defines `put_json_attachment(obj, kind, filename, ext)`
returning a three-tuple. Every override application therefore fails before writing the audit
attachment. The *policy* half is sound and is witnessed (TC-16 / TC-16b / TC-17 below): the flag and
acknowledgement gates refuse correctly, because validation runs before the broken call.

Also noted: `apply_override` never calls `exports._register_override`, so even once the call is
repaired the export gate's `_has_override` index would not see it. Both belong to the run-writer /
persistence authority tranche (001C), not to feasibility authority. Not repaired here.

### F10 — the client cannot see the run its plan produced. `LIVE_WORKFLOW_GAP`. RUNTIME-CONFIRMED. **DEFERRED to 001D.**

`adaptive/plan_router.py` sets `response["_run_id"]` and `response["_hashes"]`, but the endpoint
declares `response_model=PlanOut`, which has no such fields — FastAPI strips them. The governed run
is reachable only through the store. Natural subject of the bidirectional client/workflow witness
tranche (001D).

### Supplementary observation — the router calculators are parameter-insensitive

`app/calculators/service.py::check_chipload_feasibility` and peers use hard-coded
`spindle_rpm=18000` / `feed_rate_mm_min=1200` on the Express edition and read almost nothing from
`RmosContext`. Separately, `api_contracts.RmosContext` declares only `material_id` / `tool_id` /
`machine_profile_id` / `use_shapely_geometry`, so the `rpm`, `feed_rate_mm_min`,
`spindle_power_watts` and `tool_diameter_mm` the router passes are silently dropped by Pydantic.
The saw/rosette verdict is therefore a function of design geometry and tool lane, not of the
requested cutting parameters. Substantive, but narrower than it appears. Recorded for a later
tranche; not in scope here.

### Supplementary observation — an uncollected safety-critical test suite

`app/tests/rmos/test_safety_policy.py` is a 237-line `SafetyPolicy` suite that `pytest.ini`
(`testpaths = tests`) never collects. The gate's own unit coverage has not been running. The
witnesses this increment depends on were written to `tests/rmos/` so they actually execute; moving
or re-pointing the orphaned suite is a test-tree change left out of this PR.

---

## Remaining deferred findings

| Finding | Status after 001A | Owner tranche |
| --- | --- | --- |
| F5 — three run-writers, inconsistent risk derivation | unchanged; no canonical CAM caller uses the weak helpers | 001C |
| F6 — retract `/gcode_governed` persists GREEN with no feasibility | unchanged | 001B |
| F7 — `get_run_with_attachments` orphaned | unchanged | 001B |
| F9 — override application raises | new; policy gates sound, write path broken | 001C |
| F10 — `_run_id` stripped by `PlanOut` | new | 001D |
| calculator parameter-insensitivity | new observation | later |
| uncollected `app/tests/rmos/` suite | new observation | later |

---

## Blast radius — RULED: blocked by design (see "Owner ruling" below)

Four production CAM lanes change from authorized to blocked, because no evaluator exists for them
and D3 forbids translating that into GREEN:

```text
POST .../roughing/gcode        GREEN -> 409 SAFETY_BLOCKED
POST .../vcarve/gcode          GREEN -> 409 SAFETY_BLOCKED
POST .../vcarve/intent-gcode   GREEN -> 409 SAFETY_BLOCKED
POST .../helical/gcode         GREEN -> 409 SAFETY_BLOCKED
```

`biarc`, `relief` and `drill_pattern` already returned 409 on `origin/main` — their `tool_id`
values (`biarc_gcode`, `relief_dxf`, `drill_pattern_gcode`) do not match `resolve_mode`'s
prefixes, so they resolved to `unknown` and were already failing closed. That is evidence the
posture is already tolerated across part of the CAM surface.

Per §8 this is the "fail-closed behaviour would break an owner-required workflow" stop condition,
and per §8 it is **not** permission to fall back to GREEN. The repair is complete and correct on
the branch; whether these four lanes may be blocked in production is an authority decision, and
the merge is the decision point. No new fail-open escape hatch was invented for it: an operator who
needs an unevaluated lane to run can already say so explicitly with the pre-existing
`RMOS_TREAT_UNKNOWN_AS_RED=false`.

---

## Test witnesses

| ID | Witness | Result |
| --- | --- | --- |
| TC-01 | legitimate GREEN request computed GREEN (adaptive, rule engine) | pass |
| TC-02 | legitimate RED request blocks (F002) | pass |
| TC-03/04/05 | client `safety` / `feasibility` / `decision` / `risk_level` / `export_allowed` GREEN on a RED request | pass — ignored |
| TC-06 | unknown authority-shaped keys cannot create GREEN | pass |
| TC-07 | supported mode uses its real evaluator, no stub | pass |
| TC-08 | 11 tool_id/mode pairs with no evaluator → UNKNOWN + blocked | pass |
| TC-09 | evaluator raises → ERROR + blocked, never YELLOW | pass |
| TC-10..13 | SafetyPolicy GREEN allow; RED, UNKNOWN, malformed block | pass |
| TC-14 | persisted run risk == server decision; client GREEN never reaches it | pass |
| TC-15 | export from RED unoverridden run → 403 | pass |
| TC-16 | RED override with flag disabled, or without acknowledgement → refused | pass |
| TC-17 | RED override enabled + acknowledged → permitted by policy; original RED preserved | pass (policy + invariant halves; end-to-end blocked by F9) |
| TC-18/19 | run ↔ feasibility/G-code hashes linked and retrievable | pass |
| TC-20 | saw/rosette real feasibility | pass — and now actually evaluates (F8) |
| TC-21 | drilling / profiling operation-specific evaluators | pass |
| TC-22 | source scan: no request-driven `safety` echo / test hook | pass |
| TC-23 | source scan: no production `mode → GREEN-default stub` | pass |
| TC-24 | targeted RMOS suite | 278 passed, 1 skipped |
| TC-25 | existing CAM tests | 2538 passed, 3 skipped; 4 pre-existing failures reproduce on `origin/main`, 9 were the ruled blocking — see the TC-25 triage section |
| TC-26 | governance / boundary checks | see PR body |
| TC-27 | CBSP21 | see PR body |

---

# Owner ruling — 2026-08-23

The stop condition raised above was put to the owner and ruled on. Recorded here verbatim in
substance, because it changes the disposition of four production lanes.

> Keep pushing through the bottleneck rather than retreat to the old GREEN-default behavior.
> The four lanes that now return `409 SAFETY_BLOCKED` should remain blocked until they have a
> substantive evaluator. A manufacturing lane with no valid feasibility authority is not
> production-ready merely because it previously returned GREEN. Do not use
> `RMOS_TREAT_UNKNOWN_AS_RED=false` as the normal operational workaround; that would reintroduce
> the authority problem this tranche exists to remove.
>
> Availability may not outrank manufacturing authority.

## Ruled disposition

```text
RMOS-CONVERGE-001A

F1 client-authored safety       CLOSED
F2 GREEN-default CAM stub       CLOSED
F3 evaluator-error fail-open    CLOSED
F8 saw/rosette broken adapter   CLOSED

roughing / vcarve / helical lanes
→ BLOCKED BY DESIGN until evaluator authority exists

F9 override attachment write path
→ CONFIRMED DEFECT / DEFER TO 001C

F10 adaptive run-id propagation
→ CONFIRMED DEFECT / DEFER TO 001D
```

The **Blast radius** section above therefore stands as a statement of intended behaviour, not as
an open question. `RMOS_TREAT_UNKNOWN_AS_RED=false` is explicitly **not** the sanctioned way to
reopen these lanes; the sanctioned way is to give a lane a real evaluator and register it in
`_PRODUCTION_FEASIBILITY_ENGINES`. That ruling is also recorded in the router's module docstring
so it is not lost to whoever next meets a 409 there.

The saw/rosette repair (F8) is ruled in-scope for 001A rather than deferrable: without it the
claim that the feasibility authority boundary works could not be made, because the two lanes said
to have real engines were in fact throwing inside the adapter and presenting the swallowed failure
as a plausible YELLOW.

---

# Definition of Done — what is and is not satisfied

**This increment does not claim the RMOS production workflow is complete.** It establishes
trustworthy feasibility authority. The following DoD items are satisfied in full:

| # | Item | Status |
| --- | --- | --- |
| 1 | Production clients cannot inject authoritative GREEN state | met |
| 2 | One explicit server-authority boundary at `compute_feasibility_internal` | met |
| 3 | No production CAM mode gets GREEN because its evaluator is unimplemented | met |
| 4 | Evaluator failure does not silently preserve authorization | met |
| 5 | `SafetyPolicy` continues to fail closed | met |
| 6 | Supported operation-specific engines continue to work | met — and saw/rosette now actually run (F8) |
| 7 | `RunArtifact` records the server-derived decision | met (TC-14) |
| 8 | RED cannot export without the explicit audited override | met (TC-15) |
| 12 | Stub/dispatcher source test proves no GREEN-default fallback | met (TC-23) |
| 13 | Targeted RMOS + CAM regression tests pass | RMOS met; CAM see PR |
| 15 | CBSP21 | met — 100% patch coverage |
| 16 | No unrelated RMOS namespace migration included | met |

**Two are satisfied only in part. They are recorded as truthful limitations, not waived:**

- **DoD 9 / TC-17 — "override does not rewrite original RED history."** The *policy* half and the
  *immutability* half are witnessed: the flag and acknowledgement gates refuse correctly, the
  override record carries `original_risk_level="RED"`, the stored run is untouched, and
  `apply_override`'s update set structurally never contains `decision`. **The complete override
  round trip is not witnessed**, because F9 makes `apply_override` raise before it writes the
  attachment. This is not evidence that the round trip works; it is evidence that it cannot
  currently be exercised. It becomes evidence for 001C.

- **DoD 10 / TC-20 — "supported operation-specific feasibility engines continue to work."** TC-20
  proves the repaired saw and rosette lanes execute, reach their calculators, and differentiate
  outcomes between lanes. It does **not** prove that the requested cutting parameters influence the
  verdict — they do not, because `app/calculators/service.py` uses hard-coded rpm/feed and
  `api_contracts.RmosContext` silently drops the `rpm`, `feed_rate_mm_min`, `spindle_power_watts`
  and `tool_diameter_mm` the router passes. A repaired engine that ignores its inputs is a smaller
  claim than a working one. It becomes evidence for a later tranche.

**DoD 11** ("characterization test born from F1 fails before the fix and passes after it") is met
in substance rather than in form: the F1 pre-fix behaviour was reproduced at runtime against the
`origin/main` router and is recorded verbatim above, rather than committed as a test that fails on
the pre-fix tree. The post-fix witnesses are committed (TC-03/04/05).

**DoD 14** (governance/boundary gates) — see the timeout evidence below.

---

# Why each blocked lane is blocked

The merge gate asks for confirmation that the four lanes are blocked because **no evaluator
exists**, not because the new dispatcher fails to reach one that does. Both halves are evidenced:

*The dispatcher does reach evaluators that exist.* TC-07 asserts
`resolve_feasibility_engine("adaptive"/"saw"/"rosette")` returns the three real engine functions,
and TC-01/TC-02/TC-20 show all three producing real verdicts through
`compute_feasibility_internal`. The dispatcher is not the failure.

*No evaluator's input contract matches the blocked lanes.* Per lane, the nearest candidate and the
specific field it requires that the request model cannot supply:

| blocked lane | tool_id → mode | request model | what the rule engine needs and cannot get |
| --- | --- | --- | --- |
| `roughing/gcode` | `roughing:default` → roughing | `RoughReq` — has `stepdown`, `stepover`, `safe_z`, `feed` | no **tool diameter** (`tool_d`, rule F001) and no `z_rough` (F004) |
| `vcarve/gcode` | `vcarve:default` → vcarve | `VCarveGCodeRequest` — has `depth_mm`, `safe_z_mm`, `feed_rate_mm_min`, `plunge_rate_mm_min`, `bit_angle_deg` | no `tool_d`, `stepover`, `stepdown`, `strategy` — and a V-bit has an *angle*, not a straight diameter, so the engine's `tool_d`-based rules (F001, F025, chatter/deflection) do not model this cutter at all |
| `vcarve/intent-gcode` | `vcarve:intent` → vcarve | normalized intent — `target_depth_mm`, `bit_angle_deg`, `feed_rate_mm_min` | as above |
| `helical/gcode` | `helical:gcode` → helical | `HelicalReq` — has `tool_diameter_mm`, `z_target_mm`, `feed_xy_mm_min`, `pitch_mm_per_rev` | no `stepover`, `stepdown`, `strategy`, `climb`, `smoothing`, `margin`; a helical ramp is a pitch-per-revolution entry, which the engine's pass-schedule rules do not describe |
| *(already blocked on main)* `biarc_gcode` | → unknown | `BiarcReq` — `path`, `z`, `feed`, `safe_z` | no `tool_d`, `stepover`, `stepdown` |
| *(already blocked on main)* `relief_dxf` | → unknown | `ReliefDXFExportRequest` — an SVG plus export options | carries no CAM parameters at all |
| *(already blocked on main)* `drill_pattern_gcode` | → unknown | `DrillParams` — `z`, `feed`, `peck_q`, `safe_z`, `rpm` | `app/cam/drilling/feasibility.py` requires `hole_diameter_mm`, which the pattern request never carries |

`app/cam/pocketing/feasibility.py` and `app/cam/profiling/feasibility.py` were also considered and
rejected for all seven: both require `plunge_rate_mm_min`, `retract_z_mm` and explicit contour/
boundary geometry that none of these requests carry. Note that the drilling, pocketing and
profiling **intent** lanes already call those evaluators directly and never route through this
dispatcher — they are unaffected, and TC-21 witnesses that.

Supplying any of the missing fields would mean inventing an input in order to make a lane green,
which is what D4 forbids and what the ruling above declines.

This table is the scope statement for the follow-on feasibility-engine recovery program, and it
splits the work into two visibly different sizes:

- **`roughing` is close to plumbing.** The request already carries `stepdown`, `stepover`, `safe_z`
  and `feed`; it needs a tool diameter and a signed cutting depth, and the existing rule engine
  then applies as-is.
- **`vcarve`, `helical`, `biarc`, `relief` and `drill_pattern` need real evaluators.** The rule
  engine models a flat-end-mill pass schedule. A V-bit, a helical ramp, a bi-arc contour follow and
  a hole pattern are different operations, and adding fields to their requests would not make the
  existing rules mean anything about them. Writing those evaluators is the substance of the
  recovery program.

In both cases the last step is the same: register the mode in `_PRODUCTION_FEASIBILITY_ENGINES`.
That registration is a claim that a real engine evaluates the mode, and the module comment says so.

---

# Governance check evidence (DoD 14)

`python scripts/governance/check_all.py --tier ci` on this branch reported **2 blocking failures**.
Both are runner timeouts, not semantic failures — note the durations, which sit within a
millisecond of the runner's 120 000 ms limit:

```text
[FAIL] DXF compatibility enforcement                        (120165ms) [blocking]
[FAIL] Semantic sandbox import gate (Tier A cognition/grid)  (120197ms) [blocking]
```

Run standalone on the same tree, both pass:

```text
py -3.11 scripts/check_dxf_compat.py                              -> exit 0
py -3.11 scripts/governance/check_semantic_sandbox_imports.py     -> exit 0
   check_semantic_sandbox_imports: PASS (no forbidden imports under services/)
```

Neither check has any relationship to the files this branch touches — no DXF generator and nothing
under the Tier A semantic sandbox is modified. **No code was changed to appease these**; per the
ruling they are to be confirmed in CI, where the runner is not competing with a local test run.

Of the five warnings, the RMOS-adjacent one is also environmental:
`scripts/governance/validate_run_artifact_contract.py` requires a live API server and fails with
`URLError: [WinError 10061]`. It names none of this branch's files.

---

# TC-25 — CAM regression triage

First run of the CAM regression set (`tests/cam` plus the toolpath/adaptive/rosette/drilling files):

```text
13 failed, 2538 passed, 3 skipped in 4145.55s
```

Every failure was triaged against the merge gate's question — *does this contradict the cutover?*
None does. They fall into two groups.

## Group 1 — pre-existing, unrelated (4)

| test | failure |
| --- | --- |
| `test_relief_vcarve_endpoint_smoke.py::test_relief_preview_endpoint_exists` | `404 - router not wired` |
| `test_relief_vcarve_endpoint_smoke.py::test_vcarve_preview_endpoint_exists` | `404 - router not wired` |
| `cam/test_translator_execution_quarantine.py::test_get_latest_quarantine` | `'quarantine-7a4ea40daedf' == 'quarantine-bc60128bda9b'` |
| `cam/test_translator_governance_review_ledger.py::test_get_latest_for_translator` | `'ledger-94f9ed824c19' == 'ledger-1c3eb7fcb28f'` |

Verified pre-existing by restoring the `origin/main` router into this tree and re-running the four
in isolation — all four fail identically, with the same messages:

```text
git checkout origin/main -- services/api/app/rmos/api/rmos_feasibility_router.py
py -3.11 -m pytest <the four> -q  ->  4 failed
    Relief preview endpoint returned 404 - router not wired. Got: 404
    VCarve preview endpoint returned 404 - router not wired. Got: 404
    assert 'quarantine-e9e8eae97935' == 'quarantine-b6e72900233d'
    assert 'ledger-c6294d9ebfd0'     == 'ledger-f2cb2ea6001b'
```

The two 404s are unmounted preview routers — this branch mounts and unmounts nothing. The two id
mismatches are `get_latest` returning a different record than the test expects, and the ids differ
on every run, so they are order/isolation-dependent. Neither touches feasibility. **Not fixed
here** — outside this tranche, and fixing them would mean editing files the manifest does not
declare.

## Group 2 — the ruled blocking, reconciled (9)

All nine assert that the roughing or vcarve **intent** lanes produce G-code. They now receive
`409`, which is the ruled behaviour, not a defect. The intent routers normalize first and delegate
second, so the strict-mode contract is untouched — `test_strict_on_rejects_with_issues`,
`test_strict_query_param_variations` and `test_strict_reject_increments_counter` still pass at 422,
never reaching feasibility. What broke is precisely the half that says *the request survives and
manufactures*.

Reconciled without weakening anything:

- **Eight are `xfail(strict=True)`**, with the reason and the restore condition in the marker.
  Their assertions are preserved **verbatim** as the contract to restore. Rewriting them to expect
  `409` was rejected: such a test keeps passing after the lane reopens and would then assert the
  wrong thing, whereas a strict xfail fails loudly at exactly the moment a roughing or vcarve
  evaluator lands. The marker is the tripwire for the recovery program.
- **One** (`test_roughing_intent_increments_metrics`) has its incidental status assertion widened
  to `(200, 409, 422)`. Its subject is the intent counter, which increments before delegation and
  is unaffected; the counter equality assertion is unchanged.
- **Two new classes positively witness the ruled behaviour** rather than leaving only an absence:
  `TestRoughingIntentBlockedLane` and `TestVCarveIntentBlockedLane` assert the `409` carries
  `SAFETY_BLOCKED` and `FEASIBILITY_ENGINE_UNAVAILABLE`, that normalization/strict rejection still
  precedes the safety gate, and — for vcarve — that a `BLOCKED` run artifact is still persisted, so
  the blocking is **governed rather than silent**.

```text
tests/test_cam_roughing_intent_strict.py + test_roughing_gcode_intent_metrics.py
    ->  7 passed, 4 xfailed
tests/cam/test_vcarve_intent_migration.py
    -> 18 passed, 4 xfailed
```

## TC-25 verdict

No failure contradicts the cutover. Four are pre-existing and reproduce on `origin/main`; nine were
the intended blocking and are now either witnessed positively or held as strict-xfail contracts
awaiting an evaluator.
