# BR-001 — Repository Defect Register

> **Only currently verified defects.** No enhancements, no speculative concerns, no unavailable
> research. Every entry links to its [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md) record and
> carries current reproduction evidence (charter §4 · Disposition discipline).
>
> **Exception — the scan-intake section (BR-037+).** Entries below the *"Scan intake"* heading are
> **detector leads under adjudication**, not verified defects, and they are admitted here so the queue
> that adjudicates them is the same queue that ships fixes. They are labelled `CANDIDATE` or
> `STATIC-FACT CONFIRMED` and are **not** authorized for work. This exception was introduced by the
> 2026-07-26 scan intake and is stated explicitly because it otherwise contradicts the rule above —
> BR-038 is the standing example of why it matters: a lead admitted here read as a ready defect and
> would have caused a regression had anyone acted on it.

## What qualifies as a defect here

Implemented or promised behavior that is **incorrect, broken, unsafe, or inconsistent with its
governing contract** — and can be reproduced **now** (failing test / deterministic command / traceable
code-path inspection / contract mismatch / documented runtime observation / explicit evidence that a
promised implementation is absent).

- A missing capability that was never approved is **not** a defect → `ENHANCEMENT`.
- Authorized-but-incomplete work is **not** a defect → `UNFINISHED_SPRINT_WORK`.
- A historical defect that cannot be reproduced now → `STALE_OR_NOT_REPRODUCIBLE` (not listed here).

## Record schema

```text
Defect ID                  (= adjudication BR-NNN)
Title
Subsystem
Reproduction basis         (the current evidence — REQUIRED)
Observed vs expected
Governing contract         (what it violates, if any)
Severity / safety / data-integrity impact
Regression risk
Estimated fix size
Dependencies / blockers
Readiness
```

## Register

Verified against `origin/main` `d716d16` (2026-07-20). These entries (BR-001..BR-004) are grounded in
**code inspection and/or committed xfail tests** that assert the bug — the store-layer signatures and
their tests are the reproduction basis. The Wave 0 full-suite run was **subsequently performed** and
separately recorded ([WAVE_0_VERIFICATION.md](WAVE_0_VERIFICATION.md), 2026-07-20); it surfaced
additional items (BR-032/033/034) and did not invalidate these four. (BR-001..004 are xfail-marked, so
they do not appear among the Wave 0 failures.)

> ✅ **RESOLVED 2026-07-22 by BR-002B** (first executed code remediation): **BR-001, BR-002, BR-004**
> are fixed and no longer reproduce — the store layer now accepts `batch_label`/`tool_kind`, the xfail
> markers are removed, and the formerly-failing smoke tests pass. **BR-003** remains open. The
> per-defect entries below are retained as the historical reproduction record; each fixed entry carries
> a **Resolved** line. BR-035 (batch_tree exact-match) was fixed in the same tranche; a deeper
> batch_tree shape defect was found and filed as **BR-036** (out of BR-002B scope).

### BR-001 · `store_artifact()` rejects `batch_label`
- **Subsystem:** saw_lab
- **Reproduction basis:** `app/saw_lab/store.py:16` — `store_artifact(*, kind, payload, parent_id,
  session_id, index_meta, status)` has **no `batch_label` parameter**; committed xfail
  `tests/test_saw_lab_endpoint_smoke.py:30` reason = *"store_artifact() got unexpected keyword argument
  'batch_label'"*. Code inspection confirms the missing param on current `main`.
- **Observed vs expected:** endpoint call passing `batch_label=` raises `TypeError` (500) vs. should
  store/index the batch label (the value is used by `query_*_by_label` functions in the same module).
- **Severity:** high (endpoint 500) · **Regression risk:** low · **Fix size:** small (one function +
  caller). · **Readiness:** ready.
- ✅ **Resolved (BR-002B):** `app/saw_lab/store.py` `store_artifact` now accepts `batch_label`/`tool_kind`.
  The effective value is resolved once and mirrored into **both** `payload` (where the
  `query_*_by_label` readers look) and `index_meta`, so the two cannot disagree; an explicit
  caller-supplied `payload["batch_label"]` still takes precedence. Regression:
  `test_saw_lab_store_artifact_batch_label_roundtrip`,
  `test_saw_lab_batch_label_payload_and_meta_cannot_disagree`.
- ⚠️ **Evidence correction (2026-07-22, BR-002B review) — this entry overstates a live 500.**
  The reproduction basis is misattributed. The xfail that named this defect
  (`store_artifact() got unexpected keyword argument 'batch_label'`) was attached to
  `test_toolpaths_lint_endpoint_exists`, and that endpoint's service
  (`app/saw_lab/toolpaths_lint_service.py:49`) imports `store_artifact` from
  **`app.rmos.runs_v2.store`**, not from `app/saw_lab/store.py`. On `origin/main` the RMOS
  `store_artifact` (`store_api.py:134-144`) **already accepted** `batch_label` and `tool_kind`,
  so that endpoint could not have raised this `TypeError`; the marker was stale (and
  `strict=False`, so it XPASSed silently rather than failing).
  A repo-wide caller trace finds **no caller** passing `batch_label=`/`tool_kind=` to the
  saw_lab `store_artifact` — every such call site resolves to the RMOS store. The BR-002B
  change to `app/saw_lab/store.py` is therefore **forward-compatibility hardening, exercised
  only by its own tests**, not the repair of a reachable production 500. It is harmless and
  worth keeping; the *severity* claim ("high — endpoint 500") is what is unsupported.
  BR-002 and BR-004 are unaffected by this correction — those are the real, reachable
  `tool_kind` defects in the RMOS filter chain.

### BR-002 · `list_runs_filtered()` rejects `tool_kind`
- **Subsystem:** rmos/runs_v2 (+ saw_lab caller)
- **Reproduction basis (corrected 2026-07-21):** `app/saw_lab/executions_list_service.py:62` →
  `app.rmos.runs_v2.store.list_runs_filtered(tool_kind=…)`. The target `list_runs_filtered` and the
  **shared** filter it delegates to, `store_filter.matches_index_meta`, accept **no `tool_kind`**
  parameter. Committed xfail `tests/test_saw_lab_endpoint_smoke.py:24` reason = *"list_runs_filtered()
  got unexpected keyword argument 'tool_kind'"*.
- **Exact dispatch ([BR-002A_PROOF](BR-002A_PROOF.md) Q1):** `store.list_runs_filtered` is **re-exported
  from `store_api.py:200`** (via `store.py:396`) — so `store_api.py:200` **is** the raise-site (the
  original packet was right about the location; it was *under-scoped*, not wrong-file). The fix spans the
  3-layer chain: `store_api.py:200` → `store.py:294` class method → `store_filter.matches_index_meta`.
- **Observed vs expected:** saw_lab listing passing `tool_kind=` raises `TypeError` (HTTP 500) vs. should
  filter by tool kind.
- **Severity:** high · **Fix size:** small–moderate — 3 additive params + one filter match, **plus a
  `"saw"`/`"saw_lab"` value-normalization decision** (Q3/Q4); production blast radius **contained**
  (`matches_index_meta` has 2 production callers, both in scope; +33 `test_store_filter.py` assertions to
  run) · **Readiness:** **BR-002B-ready** (bounded, one design decision; owner authorization pending) —
  resolved via BR-002A
  (archaeology) → BR-002B (repair). Authoritative scoping record:
  [BR-002A_STORE_PATH_ARCHAEOLOGY.md](BR-002A_STORE_PATH_ARCHAEOLOGY.md).
- ✅ **Resolved (BR-002B):** `tool_kind` threaded through the full chain (`store_api` wrappers →
  `RunStoreV2.list_runs_filtered`/`count_runs_filtered` → `matches_index_meta`). The
  `"saw"`/`"saw_lab"` value decision was settled by the empirical gate (both are synonyms; missing is
  lenient) and encoded in the canonical `tool_kind_matches()` helper, which also reads the nested
  `meta.tool_kind` the store actually persists. List/count parity held. Regression:
  `test_tool_kind_filter.py` (16 tests).

### BR-003 · Simulation metrics router/schema mismatch
- **Subsystem:** simulation
- **Reproduction basis:** committed xfail `tests/test_simulation_endpoint_smoke.py:28` (applied to 8
  metrics tests) reason = *"router/schema mismatch in metrics endpoint"*.
- **Observed vs expected:** metrics endpoint responses do not match the declared schema. · **Severity:**
  medium · **Fix size:** small–medium (needs endpoint/schema inspection to bound exactly) · **Readiness:**
  ready.

### BR-004 · RMOS endpoint `store_artifact` bug
- **Subsystem:** rmos
- **Reproduction basis:** committed xfail `tests/test_rmos_endpoint_smoke.py:21`. **Possible shared root
  with BR-001** (`store_artifact` kwarg handling) — dedup to be confirmed when the fix is scoped.
- **Severity:** medium · **Readiness:** ready (verify duplicate relationship first).
- ✅ **Resolved (BR-002B):** confirmed the **same `store_artifact`/store-layer root as BR-001/BR-002** and
  fixed in the same tranche; xfail removed, `test_rmos_endpoint_smoke.py` passes.

> Not listed here (correctly excluded): BR-024 (R2000 `ezdxf.new` literal call refactored into
> `dxf_compat` — **`SUPERSEDED` into BR-018**, which owns the open R2000 policy question; not a
> currently-reproducible defect and not claimed "resolved"); disconnected UI surfaces BR-023/BR-030 (`ENHANCEMENT`, never
> approved); BR-019 auth/DB stubs (`OWNER_DECISION_REQUIRED` — scope question, not yet a contract-broken
> defect). Full reasoning in the [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md).

---

## Scan intake — 16-detector scan @ `ac3c96df` (2026-07-26)

Source: [`docs/audit/LUTHIERS_TOOLBOX_SCAN_ac3c96df.md`](../audit/LUTHIERS_TOOLBOX_SCAN_ac3c96df.md).
Entered as **CANDIDATES — NOT ADJUDICATED**. A detector produces leads; these have not been through
the adjudication ledger and none is authorized for fix.

**Confidence vocabulary (added 2026-07-26 after BR-037 was mislabelled).** A read and a run prove
different things, and this register must not blur them:

| Label | Means | What a code read can establish |
|---|---|---|
| `CANDIDATE` | a detector flagged it; nothing verified | — |
| `STATIC-FACT CONFIRMED` | the *code says so* — two writers exist, a default is unguarded | ✅ yes |
| `CONFIRMED` | the *symptom was reproduced* at runtime | ❌ never |

Reading a producer→consumer chain and inferring a symptom is a **hypothesis**, however convincing the
chain. BR-037 was filed as `CONFIRMED by producer->consumer read` and that was wrong; it became
genuinely confirmed only when the symptom was reproduced (1475 entities vs a 0 control). Do not
promote a hypothesis to `CONFIRMED` without a run.

### BR-037 · Text-detection failure silently vectorizes text into the DXF — ✅ RESOLVED ON `main`
- **Subsystem:** photo-vectorizer / DXF pipeline
- **Mechanism:** `detect_text_regions()`
  (`services/photo-vectorizer/edge_to_dxf.py:470-524`) returned `[]` from a bare
  `except Exception` at `:522`, collapsing three distinct states — OCR unavailable, no text found,
  and OCR crashed — into one falsy value. The consumer at `:1951` guards with `if text_regions:`, so
  the crash state skipped text masking entirely, leaving glyph edges in `combined_edges` for
  `findContours` to trace into the DXF as body geometry.
- **Observed vs expected:** OCR failure yielded a *successful* DXF containing text as body geometry,
  with no error and no `TEXT_MASK` log line. Expected: the output must not claim clean success.

#### Epistemic history — how this entry earned the word "confirmed"
This is recorded in full because the original wording overstated the evidence, and the register's
credibility depends on `CONFIRMED` meaning *reproduced*, not *reasoned*.

| Stage | Basis | Correct label at the time |
|---|---|---|
| 2026-07-26 (initial intake) | producer→consumer chain read statically | **HYPOTHESIS** — was wrongly filed as `CONFIRMED by producer->consumer read` |
| 2026-07-26 (challenged) | asked whether a bad DXF had actually been observed; it had not | hypothesis, explicitly unreproduced |
| 2026-07-26 (reproduction) | rendered text + body shape, forced the OCR reader to raise, converted, counted DXF entities inside the text bbox: **A (text present) = 1475 entities · B (no-text control) = 0**, while the result still reported `SUCCESS` | **CONFIRMED** |

> **Calibration note.** Reading a producer→consumer chain and inferring a symptom is a *hypothesis*.
> A register that prints `CONFIRMED` for a read teaches its readers to trust reads as proof — the
> same error that nearly shipped the wrong fix here. In this register, `CONFIRMED` means the symptom
> was reproduced. Anything else is `HYPOTHESIS` or `CANDIDATE`.

- **Resolution:** **merged to `main` 2026-07-27 as `97460755`** (PR #232,
  `fix/br-037-text-detection-silent-skip`). Verified present on `main` after merge, not just
  assumed from the merge event. During review this entry cited branch SHA `09818eee`, which went
  stale within the hour when a required CBSP21 manifest moved the head to `3e6a8a4e` — hence the
  merge commit is recorded here rather than any branch SHA.
  `[]` now means only "nothing to mask"; the crash path raises `TextDetectionError`; the caller still
  emits but marks the result `ConversionStatus.DEGRADED` with `text_detection_failed=True` and an
  explicit summary warning. 3 regression tests added (14 passed, 1 skipped).
- **Fix-shape history (also evidence-corrected):** the first implementation *refused* to emit on OCR
  failure. The **no-text control run rejected that** — it failed images with no text at all, trading
  silent corruption for silent false-refusal, because a failed OCR pass cannot know whether the image
  contained text. Emit-and-flag replaced it. *The control run, not the positive run, caught the bad fix.*
- **Known residual (accepted):** a no-text image that hits an OCR failure is still marked `DEGRADED`.
  Unavoidable — the information needed to rule it out is precisely what the failure destroyed. Honest
  uncertainty, but a real cost if OCR is flaky.
- **Severity:** high (silent wrong output) · **Fix size:** small
- **Status:** **RESOLVED — on `main`.** Merged 2026-07-27 with 44 checks passing, 1 skipped.
- **Blocker cleared en route:** #232 was held red by a `mypy` failure that was **pre-existing and
  unrelated** — `photo-vectorizer contains __init__.py but is not a valid Python package name`,
  introduced by `ffecf39f` and latent because that workflow is path-filtered, so #232 was simply
  the first PR since to touch that directory. Fixed separately in **PR #238** (`c07c917e`), which
  also revealed that gate had **never passed once** in its history and, in the course of making it
  pass, corrected two genuine unguarded `None` dereferences at `body_isolation_stage.py:387-388`.

### BR-038 · ~~Two store modules write the same `data/art_jobs.json`~~ — ❌ REFUTED (claimed shared-write defect is not present)
- **Subsystem:** art_studio / services
- **Reproduction basis (original claim):** `art_job_store.py:17` and `art_jobs_store.py:20` both
  declare `JOBS_PATH = Path("data/art_jobs.json")`.
- **Why it does not reproduce:** in the current code **neither module writes that file**. Both use it
  as a **read-only legacy migration source** (`read_text()` plus existence checks), migrating into
  **separate SQLite tables**, and the migration logic explicitly distinguishes the row shapes —
  `art_job_store.py:113` skips plural-shaped rows as *"owned by art_jobs_store"*. **A repo-wide search
  found no write site for `art_jobs.json`.** The current design routes through the SQLite-backed
  migration introduced in #189. `tests/test_art_job_stores_migration.py` exercises this split:
  **11 passed**.
- **Bearing on consolidation:** *this evidence does not justify consolidating these stores* — they
  currently have different schemas and distinct in-repo consumers. That is a statement about what this
  evidence supports, **not** a permanent architectural prohibition; a future design may justify
  consolidation on other grounds.
- **Why it was mis-filed:** the mis-file **appears** to have come from the D10 detector associating
  `JOBS_PATH` with modules containing write hints *elsewhere in the file*, without checking that
  symbol's own use. The entry then claimed *"verified by read"* when only the **declarations** had
  been read, not the write sites — the same overclaim this register's confidence vocabulary exists to
  prevent, committed under that vocabulary.
- **Severity:** n/a (no defect) · **Fix size:** n/a · **Readiness:** **CLOSED — REFUTED.** Do not open
  work from this entry.
- **Confidence:** **REFUTED 2026-07-27**, by source-level inspection of the write sites.
- **Applies to siblings:** BR-039 and BR-040 came from the same detector pass and still need the same
  **source-level verification — inspect the actual write/use sites, not the declarations.**

### BR-039 · Three preset-store modules with separate persistence paths
- **Subsystem:** services / util
- **Reproduction basis:** the current code shows three modules with separate preset-file paths:
  `services/art_presets_store.py:9` -> `data/art_presets.json`;
  `services/preset_store.py:14` -> `data/presets/presets.json`; `util/presets_store.py:23` ->
  `data/presets.json`.
- **Potential impact:** **unknown pending owner adjudication.** No drift, duplication, or inconsistent
  read/write has been demonstrated — only multiplicity. Severity is deliberately not asserted.
- **Readiness:** `OWNER_DECISION_REQUIRED` — whether a canonical store should be declared is a scope
  question, not a defect to fix unilaterally.
- **Confidence:** **STATIC-FACT CONFIRMED**, narrowly: three preset-store modules with distinct file
  paths exist. Whether this is a *defect* rather than intentional separation is **not** established.
  Per BR-038, the write behaviour was read from declarations and still needs source-level
  verification at the actual write sites.

### BR-040 · Potential silent domain-default fallback on key lookups (10 sites)
- **Subsystem:** instrument_geometry, calculators, analyzer, workflow
- **Reproduction basis:** 10 sites of `X.get(key, X[DEFAULT])`, incl.
  `body_contour_solver.py:250` (`FAMILY_DEFAULTS.get(family, FAMILY_DEFAULTS["dreadnought"])`),
  `neck_block_calc.py:202,246`, `viewer_pack_bridge.py:176,199,346,352,357,362`,
  `directional_workflow.py:187`.
- **Behaviour the pattern would produce (not observed at runtime):** *if* an unrecognized body family
  reaches these sites it would silently yield dreadnought geometry; *if* an unrecognized species
  reaches them it would silently yield default material properties. No such call has been witnessed.
- **Potential impact:** medium-high where the key space is open; none where upstream validation closes
  it · **Readiness:** needs triage — confirm per site whether the key is enum-validated upstream.
- **Confidence:** **STATIC-FACT CONFIRMED** for the 10 sites (the fallbacks are there in code);
  **CANDIDATE** as a defect — no site has been shown to receive an out-of-domain key at runtime.

### BR-041 · 447 production silent-swallow exception handlers (bulk lead, not a single defect)
- **Reproduction basis:** AST scan; 637 total, minus 106 `ImportError` optional-dep guards and 84
  archive/test = 447 production. The 146 `empty-return` + `log-then-empty-return` handlers share
  BR-037's shape and are the priority subset.
- **Severity:** unknown in bulk · **Readiness:** NOT ready as one item — must be split per subsystem.
- **Confidence:** CANDIDATE SET, explicitly not 447 bugs.

> **Refuted by the same scan — do not open work on these:** duplicate-filename drift
> (`store.py`x12 etc.) is a naming convention, not copy-paste — AST-hashing found exactly **one**
> cross-file clone group; and the router-count baseline is **not** stale (`ci/router_count_gate.py`
> reports 253/1228 = baseline exactly).

---

## Stranded-work intake — Tier D recovery (2026-07-28)

Source: `DEV_ORDER_CONV-002_TIER_D_STRANDED_BRANCH_DISPOSITION.md` (2026-07-27), a branch-audit
disposition order held in the Consolidation Lab as a historical source artifact. Only its TD-1 work
package is a demonstrable production defect and enters here; TD-2/TD-3/TD-4 are decision and archival
work and are handled Lab-side under Investigation 025.

### BR-042 · Ingest-audit browse lane is half-landed — router shipped but mounted nowhere
- **Subsystem:** rmos/acoustics (backend) + client tools view (frontend)
- **Confidence:** **CONFIRMED — re-witnessed against `origin/main` `9d22aa61` on 2026-07-28**, not
  inherited from the source document. Probes used `git ls-tree`/`git grep` on refs, never
  `git show <ref>:<path>`, which silently produces false-absent results under Git Bash on Windows.
- **Observed vs expected:** `main` ships a complete, working router that **no code mounts**, and a
  frontend view that is deliberately disabled *because* it is unmounted. The feature is unreachable
  in production while both halves of it exist in the repository.

| Fact | Evidence on `9d22aa61` |
|---|---|
| Router exists | `services/api/app/rmos/acoustics/router_ingest_audit.py`, 3 endpoints |
| Router is unmounted | **Zero mount sites.** All 5 references are docs/metrics; `metrics/wire_url_audit.json` tags it `UNMANIFESTED:` |
| UI honestly gated | `packages/client/src/views/tools/AcousticsIngestEvents.vue` lines 10, 345 — gating comments name the unmounted lane as the reason |
| Missing half is recoverable | `salvage/other-stash8-ingest-audit-binaries` @ `f102380d` (2026-05-14): carries the mount (`main.py:1186-1194`, `prefix="/api/rmos/acoustics"`) and a 717-line `IngestEventsView.vue` |
| **Contracts still align** | salvage view calls `/api/rmos/acoustics/ingest-events`, `…/counts`, `…/{eventId}` — router declares `/ingest-events`, `/ingest-events/counts`, `/ingest-events/{event_id}`. **All three match.** Prefix convention matches siblings `router_import.py` / `router_zip_export.py` ("prefix set once in main.py") |

- ⚠️ **CONFLICTS WITH A STANDING GOVERNANCE RULING — owner confirmation required before execution.**
  `docs/governance/audits/SYSTEM_CONFLATION_AUDIT_2026-06-21.md:123` rules this exact pair
  **"RETIRE / broken pair ✅"**, on the stated basis that *"FE fetches `/acoustics_ingest/` … paths
  diverge"*. **That basis could not be reproduced on current `main`:**
  `AcousticsIngestEvents.vue:209` is a Vue component import
  (`import EventDetailModal from "./acoustics_ingest/EventDetailModal.vue"`), not a fetch URL, and the
  gated view contains **no API calls or endpoint strings at all**. The divergence claim appears to be
  either a misread import path or a description of a pre-gating state. Executing BR-042 **reverses a
  RETIRE decision**; that is an owner call, not a maintainer call.
- **Scope when authorized** (bounded — do NOT merge the salvage branch wholesale):
  1. mount the existing router using the current registration convention;
  2. verify all three endpoints through the assembled app;
  3. reconcile the salvage view against the gated view — **retain one view and one route**;
  4. remove gating only after the live contract is proven;
  5. add focused backend + frontend coverage.
- **Severity:** medium (feature unreachable; no data loss, no wrong output) · **Fix size:** medium
- **Readiness:** **QUEUED / NOT STARTED — blocked on the owner ruling above.** Not authorized by this
  intake; this entry defines scope only.
- **Recovery record:** if `salvage/other-stash8-ingest-audit-binaries` is ever deleted, its content is
  recoverable at `f102380d` until garbage collection.

## Materials-index intake — static unit adjudication (2026-08-03)

Single item, surfaced while grounding an acoustics knowledge-pack SOP against runtime code. Unlike the
scan intake above, this entry is **not** a detector lead: it is reproduced by committed tests and is
authorized for bounded remediation.

### BR-043 · Tonewood radiation-ratio scale collapses acoustic recommendation scoring
- **Subsystem:** materials intelligence (backend schema + recommendation scorer)
- **Confidence:** **CONFIRMED — reproduced on `origin/main` `ada33581`** by
  `services/api/tests/materials/test_tonewood_acoustic_indices.py`
  (3 × `xfail(strict=True)` assertions of the intended scale; they fail against current code).
  Static contradiction confirmed first by direct read of the four sites below.
- **Observed vs expected:** `TonewoodEntry.radiation_ratio` returns `(c / rho) * 1e6`. Three
  independent places in this repository declare the *unscaled* `c / rho` value — including the
  property's own docstring. The `1e6` is spurious.

| Fact | Evidence on `ada33581` |
|---|---|
| Producer applies `*1e6` | `services/api/app/materials/schemas.py:148-156` — `return round((c / self.density_kg_m3) * 1e6, 2)` |
| Its own docstring contradicts it | same docstring: *"Reference: Schelleng (1963) — Adirondack spruce ~11.7, Sitka ~11.4"*. Shipped code returns ~1.17e7 for those species |
| Scorer targets are on the unscaled scale | `scorer.py:33-44` `_ROLE_TARGETS` — soundboard 11.5, bracing 12.0, back_sides 8.0, fretboard 4.0 |
| Consumer applies no inverse scaling | `scorer.py:61-73` `_score_acoustic` = `exp(-0.5*((rr - target)/3.0)**2)`, `sigma = 3.0`, compared directly |
| Router documents the unscaled form | `services/api/app/materials/router.py:88` — *"radiation_ratio (Schelleng c/ρ)"* |
| Value is user-visible unrepaired | `packages/client/src/instrument-workspace/acoustic/materials/InstrumentMaterialSelector.vue:97` renders `RR {{ entry.radiation_ratio.toFixed(1) }}`; `composables/useTonewoods.ts:66` passes the API value through with no rescale |
| Worked case from shipped reference data | American Basswood `rho = 415`, `E = 10.07 GPa` → `c = 4926 m/s`, `c/rho = 11.87`. Property returns `1.187e+07` |

- **Downstream effect:** with `rr ≈ 1.19e7` against a target of `11.5` and `sigma = 3.0`, the Gaussian
  exponent is astronomically negative. **`_score_acoustic` returns 0.0 for every acoustically-populated
  species in every role.** The acoustic term of `score_for_role` / `recommend_for_role` /
  `compare_species` is silently dead; only the structural and machinability terms differentiate.
  No consumer compensates, so the API also serves — and the UI displays — a value ~1e6 too large.
- **Governing contract:** the property's own docstring and the role-target profiles it is compared
  against. This is an internal-consistency defect, not a physics dispute.
- **Test gap:** `_score_acoustic` had **no direct test**. No test asserted `radiation_ratio`'s magnitude.
  The defect was reachable only by reading the producer and consumer side by side.
- **Severity:** high (silent wrong output in a user-facing advisory path; no data loss, no machine
  output affected) · **Regression risk:** low-medium — the repair *will* change recommendation ordering,
  which is the intended effect · **Fix size:** small (producer expression + docstring), with the
  substantive work in test coverage
- **Dependencies:** none. **Independent of PR #244** — the MB Sound corpus corroborates the target scale
  (vendor SRC medians 12.28–14.00, all on the unscaled `c/rho` scale) but is evidence only, and must not
  be imported or hard-coded by this repair.
- **Readiness:** **AUTHORIZED — bounded remediation in progress** under the BR-043 Dev Order.
- **Related but out of scope — recorded, not fixed here:**
  1. `TonewoodEntry.specific_moe` (`schemas.py:158-168`) applies `* 1e6` to a GPa-denominated ratio while
     its docstring claims *"Same as c²/10⁶"*; those differ by 1e3. Investigate-only under this order —
     see BR-043 Commit 4 disposition.
  2. The frontend `StiffnessIndexPanel` path is **independent of the API**, computing from hardcoded
     `tonewoodData.ts`. Its `calcRadiationRatio` (`useStiffnessIndex.ts:69-71`) applies `* 1000` and
     labels it `c/ρ ×10³` — self-consistent in display — but `rrColor` and `soundboardRating`
     (`useStiffnessIndex.ts:149-152`, `StiffnessIndexPanel.vue:312-317`) threshold at 12.0 / 10.5 / 9.0,
     the *unscaled* scale, so every wood renders "Excellent". Same defect family, different data path,
     **not** a compensating conversion for the backend. Needs its own entry.
