# IBG / AGE Precursor Chronology

**Sprint:** IBG/AGE Precursor Forensic Sprint (read-only archaeology)  
**Repository:** `HanzoRazer/luthiers-toolbox`  
**Secondary evidence:** `HanzoRazer/vectorizer-sandbox` — **UNAVAILABLE** this run (`gh repo view` → repository not found for this token; `docs/audit-sources/vectorizer-sandbox` is a local-only junction, not present). Sandbox-dependent arrows are `UNKNOWN`.

**Does not authorize implementation.** Later governance documents are claims, not April facts.

---

## Phase 0 — Immutable starting state

| Field | Value |
| ----- | ----- |
| Forensic worktree | `/tmp/ibg-forensics` |
| Branch | `cursor/ibg-age-precursor-forensics-5bd1` |
| Base | `origin/main` |
| HEAD | `2646992fc294a904438042d529b939ec6db80662` |
| HEAD date | 2026-08-28 00:15:52 -0500 |
| HEAD subject | Merge pull request #331 from HanzoRazer/cursor/rmos-drilling-contract-001-de8d |
| Clean tree (forensic worktree) | YES (no production edits) |
| Left untouched | `cursor/rmos-deferred-queue-5bd1` in `/workspace` with uncommitted `SPRINTS.md` |

Naming used in this file:

- **IBG** = Instrument Body Generator (April implementation).
- **"Image Body Generator"** only when quoting later documents.
- **AGE** = Agentic Guidance Engine (April CLAUDE.md expansion), unless a cited document uses a different expansion.

Event types: `CODE EVENT` · `DOCUMENT EVENT` · `GOVERNANCE EVENT` · `RENAME` · `MOVE` · `DELETE` · `PRODUCTION PROMOTION`

Classifications: `CODE_PROVEN` · `HISTORY_PROVEN` · `DOC_PROVEN` · `SUPPORTED_INFERENCE` · `TEMPORAL_ADJACENCY_ONLY` · `CONFLICTED` · `UNKNOWN`

---

## Chronological evidence table

| Date (author tz) | Commit | Artifact | Event | Classification | Significance |
| ---- | ------ | -------- | ----- | -------------- | ------------ |
| 2026-03-04 | `1ce27294` | `services/blueprint-import/vectorizer_phase3.py` | CODE EVENT: `FeedbackSystem` and `TrainingDataCollector` classes added | CODE_PROVEN | Precursor *code* later cited as Loop 3 scaffolding. Not named AGE. Default `enable_feedback=False` already present by 2026-04-02 (`6075db47` grep). |
| 2026-03-15 | `c958ccfa` | `geometry_coach.py` (photo-vectorizer) | CODE EVENT: GeometryCoach V1 extracted | CODE_PROVEN | Intra-run coaching/retry exists *before* April 2 three-loop document. No Claude/Anthropic calls in `geometry_coach*.py` (search this tree). |
| 2026-03-15 | `50123379` | `geometry_coach_v2.py` | CODE EVENT: GeometryCoachV2 retry profiles + monotonic improvement gate | CODE_PROVEN | Behavioral cousin of Loop 1 heuristics (retry strategies inside one extraction). Not `ValidatedExtractor` / not AGE. |
| 2026-04-01 | `b02091cd` / `3676d75d` | photo-vectorizer light-line + pipeline integration | CODE EVENT: blueprint/silhouette extractors integrated | CODE_PROVEN | Vectorizer extraction capability immediately before April 2 architecture note. |
| 2026-04-02 23:55 | `6075db47` | `CLAUDE.md` | DOCUMENT EVENT: “approved vectorizer feedback loop architecture”; defines Loop 1/2/3 and AGE (`VectorizerAGE`); commit message says loops “never implemented” and AGE “dropped from scope” | DOC_PROVEN | **Contemporaneous April definition of the three loops and AGE.** Places AGE “as the decision layer above Loop 1.” Sketch classes `ValidatedExtractor`, `AdaptiveExtractor`, `VectorizerAGE` appear only in markdown. |
| 2026-04-03 00:11 | `bf5b2d48` | `vectorizer_phase3.py` | CODE EVENT: `validate_scale_before_export()` | CODE_PROVEN | Commit message: implements scale gate “as specified in CLAUDE.md”. This is the only April fragment that contemporaneously claims to implement a piece of that document. It is not Loop 1’s `ValidatedExtractor`. |
| 2026-04-03 | `b0c4ace6` | `CLAUDE.md` | DOCUMENT EVENT: Vectorizer Sprint B segmentation plan added | DOC_PROVEN | Separate vectorizer sprint name (“Sprint B”), not IBG Sprint 1/2. |
| 2026-04-04 09:59 | `77560aec` | `SPRINTS.md` | DOCUMENT EVENT: sprint registry created | DOC_PROVEN | **Shop Sprint 1 = Vectorizer Reconciliation. Shop Sprint 2 = Repo Split and Standalone Products. Shop Sprint 3 = Remediation.** This sequence is not IBG. |
| 2026-04-05 22:38 | `4f3ee9e2` | `tools/body-outline-editor.html` | CODE EVENT: Body Outline Editor created | CODE_PROVEN | **BOE exists 12 days before IBG code.** First HTML has no IBG / `/api/body` references. |
| 2026-04-06 | `68120ea1` / `727c05e2` | `SPRINTS.md` | DOCUMENT EVENT: “Sprint 2 audit” / “Sprint 2 Step 1 complete — publish workflow” | DOC_PROVEN | Shop Sprint 2 (repo-split/publish), not IBG. |
| 2026-04-15 (docstring) | *(no commit this date)* | `arc_reconstructor.py` (first git add `471bc902` on 2026-04-17) | DOCUMENT EVENT inside later CODE EVENT: file header `Date: 2026-04-15` | SUPPORTED_INFERENCE | Author-date in source claims the gap-bridger was written two days before the first IBG commit. Not independently HISTORY_PROVEN until `471bc902`. |
| 2026-04-16 13:53 | `96410500` | vectorizer phase 6b | CODE EVENT: vectorizer `fit_circle_3pts` | CODE_PROVEN | Same *function name* as later IBG math; **different collinearity formula** (not a copy). |
| 2026-04-16 (docstring) | *(planning doc committed 2026-04-19 `95385be9`)* | `docs/planning/instrument_body_generator.md` | DOCUMENT EVENT: “InstrumentBodyGenerator — Dev Order”; **Sprint: Sprint 9**; Steps 1–6; “Zero imports from services/” | DOC_PROVEN (as of 04-19 commit) | Identifies IBG as **shop Sprint 9**, not Sprint 1. Requires `SESSION_AUDITS.md` — **that file is NOT_FOUND in git**. |
| 2026-04-16 (docstring) | `ca2b2347` / `33aaf3d3` (committed 04-17) | IBG / `body_contour_solver.py` headers | DOCUMENT EVENT: `Sprint: 9 — InstrumentBodyGenerator`; `Date: 2026-04-16` | DOC_PROVEN | File headers agree with the Dev Order’s Sprint 9 label and predate the commit timestamps by one calendar day. |
| 2026-04-17 01:59 | `d6bcd03f` | `services/api/app/cam/layer_consolidator.py` | CODE EVENT: layer-aware DXF consolidator | CODE_PROVEN | Same-day CAM consolidator; later wired as IBG DXF “step zero”. Not named IBG. |
| 2026-04-17 21:14 | `ca2b2347` | `sandbox/arc_reconstructor/instrument_body_generator.py` **created** | CODE EVENT: first git appearance of IBG; docstring “Instrument Body Generator — Complete Body from Partial Vectorizer Output” | CODE_PROVEN / HISTORY_PROVEN | **IBG birth in git.** Directory did not exist at `ca2b2347^`. File imports `body_contour_solver` and `constraint_extractor` **which are not in this commit** — incomplete tree. Also imports production `LayerConsolidator`, violating Dev Order “zero imports from services/”. |
| 2026-04-17 22:45 | `33aaf3d3` | `body_contour_solver.py`, `reference_outline_bridge.py` | CODE EVENT: commit subject `feat(ibg): Sprint 3 production-readiness fixes` | CODE_PROVEN / CONFLICTED | **First IBG commit labeled “Sprint 3”.** Adds solver that still `import`s untracked `arc_reconstructor`. “Systems engineering review” cited here; the review markdown is dated 2026-04-19 and committed 2026-04-21. |
| 2026-04-17 23:24 | `471bc902` | `services/api/app/instrument_geometry/body/ibg/*` | PRODUCTION PROMOTION: `feat(ibg): Sprint 4 — move IBG to production` (3722 lines); first git add of `arc_reconstructor.py` (1611 lines) and `constraint_extractor.py` | CODE_PROVEN / HISTORY_PROVEN | Production copy of IBG. Sandbox still retained until May 20. |
| 2026-04-18 13:16 | `3ed636a9` | `body_contour_solver.py` | CODE EVENT: `feat(ibg): Sprint 5 — replace hardcoded sagitta with circle fitting` | CODE_PROVEN | Uses `fit_arc_segment` from IBG `arc_reconstructor.py`. |
| 2026-04-18 14:14 | `6816cd7f` | `constraint_extractor.py` | CODE EVENT: reject centerline noise in waist landmarks | CODE_PROVEN | Landmark/waist refinement; not a new product. |
| 2026-04-18 15:30 | `c9ebf8a8` | `body_solver_router.py` | CODE EVENT + DOCUMENT EVENT: `feat(ibg): Week 1 API endpoints — body solver router`; module docstring “Body Outline Editor ↔ IBG”; FastAPI tags `["Body Solver"]`; imports `InstrumentBodyGenerator` | CODE_PROVEN / HISTORY_PROVEN | **Body Solver HTTP surface is born wrapping IBG.** Not a later rename of an existing IBG router. BOE named as client. Numbering switches from “Sprint N” to “Week 1”. |
| 2026-04-18 16:10 | `40d5e3f9` | `body_solver_router.py` + `light_line_body_extractor.py` | CODE EVENT: Week 2 `run_in_executor` + DXF base64; **same commit also edits photo-vectorizer light-line extractor** | CODE_PROVEN / TEMPORAL_ADJACENCY_ONLY (vectorizer file) | IBG API change is proven. The light-line hunk is a mixed commit; no IBG import of that module. |
| 2026-04-19 05:17 | `3e75a7cb` | instrument geometry / curvature / vectorizer modules | CODE EVENT | HISTORY_PROVEN | Broader geometry drop; not AGE. |
| 2026-04-19 05:23 | `95385be9` | `docs/planning/instrument_body_generator.md` added; `SPRINTS.md` rewritten (later truncation) | DOCUMENT EVENT / MOVE | HISTORY_PROVEN | First git add of the 2026-04-16 IBG Dev Order markdown. |
| 2026-04-19 10:06 | `2b94549c` | `docs/handoffs/FEEDBACK_LOOP_SYSTEM_HANDOFF.md` | DOCUMENT EVENT: “Loop 1 is fully implemented and working in the photo pipeline” | DOC_PROVEN | **April 19 reinterpretation.** Labels GeometryCoach / scale gate / FeedbackSystem as the three loops. Conflicts with `6075db47` (“never implemented”) and with absence of `ValidatedExtractor`/`AdaptiveExtractor`/`VectorizerAGE` in Python. |
| 2026-04-19 (doc date) / 2026-04-21 commit `a50a347c` | `docs/handoffs/IBG_SYSTEMS_ENGINEERING_REVIEW.md` | DOCUMENT EVENT: “Sprint: 9 — InstrumentBodyGenerator”; IBG = geometry completor for 82–88% vectorizer DXF; frontend = BOE hitting `/api/body/solve-from-dxf` | DOC_PROVEN | Written *after* Sprint 3–5 and Week 1–2 commits. Cannot be the review that `33aaf3d3` already “fixed,” unless an uncommitted session review preceded the markdown (`SUPPORTED_INFERENCE`). |
| 2026-04-22 | `118e7850` | `docs/api/body_solver_openapi.yaml` | DOCUMENT EVENT: OpenAPI `title: Body Solver API`; commit body: “renamed from IBG API per ADR”; yaml says IBG “is a separate geometry correction library used internally… no direct API endpoint” | DOC_PROVEN / CONFLICTED | **No predecessor OpenAPI titled IBG API found** (`git log -S 'title: Instrument Body'` on yaml: empty). **No ADR file found** under `docs/adr/` for this rename. Router was already tagged Body Solver on 04-18. |
| 2026-04-29 | `3f508163` | `SPRINTS.md` | DOCUMENT EVENT: recover truncated registry including `### Sprint 9 — InstrumentBodyGenerator` | HISTORY_PROVEN | Shop-level Sprint 9 entry survives; still no IBG Sprint 1/2 sections. |
| 2026-05-11 10:50 | `ccb30161` | `docs/handoffs/VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md` | DOCUMENT EVENT / RENAME: first git hit for string **“Image Body Generator”** | DOC_PROVEN | 24 days after Instrument Body Generator code. Asks whether Loop 2 moved into “Image Body Generator” — answers no. |
| 2026-05-11 11:54 | `b5c51220` | `IBG_FUNCTIONAL_CAPABILITY_ASSESSMENT_2026-05-11.md` | GOVERNANCE EVENT / RENAME: title `# Image Body Generator (IBG)`; “Sprint Origin: Sprint 9”; “Despite the name suggesting image processing, it is actually a parametric geometry solver” | DOC_PROVEN | Explicitly replaces the expansion while describing the April solver. |
| 2026-05-11 12:36 | `c9da01bd` | `docs/governance/IBG_ROLE_DEFINITION.md`, `THREE_LOOP_ARCHITECTURE_REFRAMED.md` | GOVERNANCE EVENT | DOC_PROVEN | IBG = “Image Body Generator”; three-loop reframed as MRP governance (later demoted 2026-05-30). |
| 2026-05-12 | `70a0d3ee` | BOE / IBG-2B | CODE EVENT: BOE begins calling `/api/body` | HISTORY_PROVEN | Integration boundary, not identity. |
| 2026-05-20 21:18 | `261436ae` | `sandbox/arc_reconstructor/*.py` deleted | DELETE / MOVE: “Deleted (migrated to vectorizer-sandbox)” | HISTORY_PROVEN | Sandbox copies removed from this repo. Destination **not verifiable here** (sandbox UNAVAILABLE). Production IBG package remains. |
| 2026-05-20 | `docs/handoffs/SANDBOX_FOLDER_REMEDIATION_HANDOFF.md` | DOCUMENT EVENT: incubation “circa March-April 2026” | DOC_PROVEN | **Later widening of IBG start into March** with no IBG code commit before 2026-04-17 in this repo. |
| 2026-05-30 | `8fad48d9` | CLAUDE.md + conflation handoffs | GOVERNANCE EVENT: three-loop/AGE “approved design” retracted; experimental/sandboxed | DOC_PROVEN | Later column: what governance said the April text *meant*. Does not rewrite `6075db47` contents. |
| 2026-08-16 | `90c918f8` | `docs/Body_Outline_Editor_CHANGELOG.md` | DOCUMENT EVENT: repeats “OpenAPI 3.0 spec, renamed from IBG API per ADR” | DOC_PROVEN | Reconstructive changelog, not new primary evidence. |

---

## Three statements (not reconciled)

### WHAT THE CODE DID (April)

- Vectorizer extracted images/blueprints to DXF (`vectorizer_phase3.py`, photo-vectorizer). Scale gate added 2026-04-03. GeometryCoach retry existed since March. `FeedbackSystem` existed since March, off by default.
- No Python class `VectorizerAGE`, `ValidatedExtractor`, or `AdaptiveExtractor` was ever added in this repository (`git log -S 'class VectorizerAGE' -- '*.py'` empty).
- IBG first appears 2026-04-17 as `InstrumentBodyGenerator` completing **files** described as partial vectorizer DXF. It does not import vectorizer modules.
- Body Solver router (2026-04-18) wraps IBG for HTTP. BOE is a separate HTML editor (2026-04-05) later pointed at that API.

### WHAT CONTEMPORARY DOCUMENTS SAID (April 2–22)

- `6075db47`: three loops + AGE are the approved vectorizer architecture, not yet built; AGE belongs above Loop 1; pattern claimed from `tap_tone_pi/.../analyzer_guidance_engine.py`.
- IBG Dev Order / file headers: this work is **Sprint 9 — InstrumentBodyGenerator**, sandbox-only, no `services/` imports.
- `2b94549c` (Apr 19): Loop 1 “fully implemented” in photo pipeline — already a same-week split from the Apr 2 “never implemented” claim.
- OpenAPI commit message claims an ADR rename from “IBG API”; yaml and router already say Body Solver; ADR file not in repo.

### WHAT LATER GOVERNANCE SAID (May–August)

- IBG expanded as **Image Body Generator** (2026-05-11) while describing the same parametric solver.
- Three-loop called approved, then (2026-05-30) experimental/never approved/never implemented/sandboxed.
- IBG incubation back-dated to “circa March-April” (May 20 handoff).
- BOE/IBG family-conflation docs treat IBG as Image Body Generator alongside BOE.

These three columns disagree. This chronology does not pick a winner.

---

## H0 / H1 — AGE ↔ IBG (special test)

**H0:** No demonstrated historical identity or direct lineage exists between AGE and Instrument Body Generator.  
**H1:** Repository evidence demonstrates a specific AGE ↔ IBG implementation or architectural relationship.

| Test | Result |
| ---- | ------ |
| Shared Python types/imports | NONE — IBG never references AGE/`VectorizerAGE`; AGE sketch never references IBG |
| Shared commits | NONE — AGE doc `6075db47` (Apr 2); IBG code `ca2b2347` (Apr 17) |
| Contemporaneous doc linking them | NONE_FOUND in April sources |
| Later docs mentioning both | May governance places Loop 2 *away* from IBG (`ccb30161`: “No relocation to Image Body Generator”) |

**Burden on H1 is not met. H0 stands.** Classification: `NONE_FOUND` for identity/lineage. Shared vectorizer *context* is `TEMPORAL_ADJACENCY_ONLY`.

---

## Wrong-reason audit

| CLAIM | BEST SUPPORT | BEST COUNTEREVIDENCE | RULING | CONFIDENCE |
| ----- | ------------ | -------------------- | ------ | ---------- |
| AGE became IBG | None in this repo | Different dates, files, languages (markdown sketch vs parametric solver); no rename commit | **False** | High |
| IBG became BOE | Body Solver docstring “BOE ↔ IBG”; later BOE calls `/api/body` | BOE HTML exists 2026-04-05 *before* IBG; they remain separate artifacts | **False as identity**; **true as later integration** | High |
| IBG descended from Photo Vectorizer | IBG consumes “partial vectorizer DXF”; mixed commit `40d5e3f9` | No import/copy of photo-vectorizer; `fit_circle_3pts` not the same implementation | **Not descent.** Data-consumer relationship only | High |
| Sprints 1 and 2 existed (as IBG commits) | IBG commit series starts at “Sprint 3”; Dev Order has Steps 1–6; docstring dates Apr 15–16 | No `feat(ibg): Sprint 1/2` commits; `SESSION_AUDITS.md` missing; shop Sprint 1/2 are vectorizer/repo-split | **Not recovered as git sprints.** See `IBG_SPRINT_1_2_RULING.md` | Medium |
| Three-loop architecture governed IBG | May IBG_ROLE denies Loop 2 inside IBG | April IBG Dev Order / code never mention Loop 1/2/3 or AGE | **False for April implementation** | High |
| Agentic intelligence belonged above Loop 1 | `6075db47` CLAUDE.md explicit “decision layer above Loop 1”; priority list item 4 | Same commit: AGE not built; 2026-05-30 retracts approval | **Documented April intent only; not implemented; later disputed** | High for the April sentence; High that it is not runtime fact |
| Agentic intelligence belonged above Loop 2 | None contemporaneous | April text places AGE above Loop 1, Loop 2 is a cache, Loop 3 is retraining | **Not an April claim** | High |
| “Image Body Generator” was the original IBG expansion | May 11 titles | `ca2b2347` docstring **Instrument** Body Generator; first “Image Body” string `ccb30161` 2026-05-11 | **False** | High |
| Later governance accurately describes the April implementation | Overlap: IBG completes partial DXF with Sevy/Mottola math | Image vs Instrument; March incubation claim; three-loop “approved” then “never approved”; Loop 1 “fully implemented” vs named classes absent | **CONFLICTED** — do not treat as equivalent | High |

---

## Terminal recommendation

```text
FORENSIC RECORD SUFFICIENT
    Architectural review may begin.
```

Review may begin **only** on proven constraints (AGE ≠ IBG; three-loop did not govern IBG; original expansion is Instrument Body Generator; Body Solver is an HTTP wrapper, not a silent absorption of IBG into BOE).

Scoped insufficiency (do not fill these arrows):

- AGE *implementation* inside `vectorizer-sandbox` (`agentic_supervisor.py` is a later claim): `UNKNOWN`
- Exact identity of IBG-internal Sprints 1 and 2: `INCONCLUSIVE` / `PARTIALLY_RECOVERED`
- ADR named in “renamed from IBG API per ADR”: `NOT_FOUND`

This forensic sprint does not issue an implementation Dev Order.
