
Your remediation framing is sound: controlled stabilization, not cleanup or semantic expansion. Below is an evaluation plus a surgical implementation spec you can run as three small PRs.

Evaluation of your plan
Your lane	Verdict	Why
P0 SIMPLE/UNKNOWN
Correct and urgent
Verified: _simple_extraction() → all UNKNOWN; export_to_dxf() excludes UNKNOWN by default → zero entities. That is evidence poisoning, not a cosmetic bug.
P1 grouping telemetry
Correct; partially already built
GroupSelectionResult.fallback_used exists; EdgeToDXFResult.grouping and blueprint_orchestrator debug payload already carry it. Gap is visibility (top-level API, counters, alerts), not missing logic.
P1 feedback classify/gate
Correct sequencing
Wire-or-delete is right after classification. Reviving learning now would violate your own “instrumentation-before-modification” rule.
Delayed items
Correct
Classifier rewrites, federation, ontology, etc. need trustworthy degradation signals first.
Sequence 1→6
Correct
Matches observability → determinism → containment.
One scope correction (important):

API extraction_mode=simple on /vectorize-geometry routes to Phase 2 (phase2_router.py), not ExtractionMode.SIMPLE in Phase 3.
Phase 3 SIMPLE is latent today (no production caller found in services/api), but planned in handoffs (CleanupMode.VECTORIZER_V2_SIMPLE → Phase 3 SIMPLE).
P0 is still justified: fix the landmine before anyone routes cuatro/OM specs through Phase 3 SIMPLE; add a regression test so it cannot regress.

Enhanced surgical implementation spec
PR-1 — P0: SIMPLE export integrity (single file + test)
Goal: SIMPLE mode must never emit an empty DXF when contours were extracted.

Touch only:

services/blueprint-import/vectorizer_phase3.py (extract() export call ~3568–3578, optionally export_to_dxf() ~2463–2468)
New: services/api/tests/test_vectorizer_simple_export.py (or under blueprint-import/tests/ if that’s the convention)
Do not touch: v2_raw, photo_v2, photo_refined, orchestrator mode routing, classifiers.

Option A (recommended — minimal semantics change):

At export in extract(), when mode == ExtractionMode.SIMPLE:

excluded = [
    ContourCategory.TEXT,
    ContourCategory.PAGE_BORDER,
    # UNKNOWN intentionally omitted for SIMPLE
    ContourCategory.SMALL_FEATURE,  # optional: keep excluding noise
]
body_w, body_h = export_to_dxf(..., excluded_categories=excluded)
Map UNKNOWN → layer UNCLASSIFIED (add to layer_colors in export_to_dxf if missing).

Option B (fail-closed guard — add alongside A):

After export, if SIMPLE and exported_count == 0 (return it from export_to_dxf or count entities in file):

Append warning: simple_export_empty: N contours extracted, 0 exported
Set validation_passed = False on ExtractionResult
Do not return success-with-empty-DXF to downstream IBG/topology
Acceptance criteria:

Unit test: synthetic image / fixture → _simple_extraction path → DXF has ≥1 LINE entity on UNCLASSIFIED or body layer.
SMART default path unchanged: UNKNOWN still excluded when not SIMPLE.
v2_raw smoke unchanged (grep CI job or one existing blueprint test).
Out of scope for PR-1: Promoting largest UNKNOWN to BODY_OUTLINE (that’s semantic interpretation — Lane 4+).

PR-2 — P1: Grouping fallback telemetry (instrumentation only)
Goal: Every grouping fallback is measurable and visible without changing isolation authority.

Touch only:

services/photo-vectorizer/edge_to_dxf.py (existing GroupSelectionResult paths ~1270–1308)
services/api/app/services/blueprint_extract.py (surface grouping on user-visible metadata)
services/api/app/services/blueprint_orchestrator.py (promote from debug-only if needed)
Optional: services/api/app/services/photo_orchestrator.py if photo path bypasses blueprint_extract
Do not change: _isolate_body_contours() algorithm, grouping scores, CANONICAL_RECOVERY modes.

Implement:

Structured log (required) — one line per conversion:

GROUPING_FALLBACK | reason=exception|selection_failed | group_count=… | source=…

Use logger.warning with a stable key for log aggregation.

In-process counter (required) — module-level or small TelemetryCounters dataclass:

grouping_fallback_total
grouping_fallback_by_reason: dict[str, int]
Increment in all branches where fallback_used=True (not only exception path).

API contract (required) — top-level fields on vectorize response (not buried in debug-only):

"topology_provenance": {
  "grouping_fallback_used": false,
  "grouping_fallback_reason": null,
  "grouping_algorithm": "primary|legacy_isolation"
}
Mirror what blueprint_orchestrator already builds (~1091–1099) into the standard response envelope.

Optional admin endpoint — GET /api/internal/vectorizer-metrics returning counters (behind env flag). Defer if you want zero new routes.

Acceptance criteria:

Forced test double: mock _isolate_with_grouping to raise → response has grouping_fallback_used: true.
Happy path → false, counters unchanged for fallback.
No diff in DXF bytes for golden photo_v2 fixture (telemetry-only PR).
Note: Audit said “warning only”; code uses logger.exception — treat telemetry PR as surfacing, not “add logging.”

PR-3 — P1: Feedback lifecycle classification (gate, not revive)
Goal: Truthful lifecycle labels; no implied learning loop.

Touch only:

New: docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md (single source of truth)
services/blueprint-import/vectorizer_phase3.py (docstrings + optional runtime flags)
services/api/app/routers/blueprint/ — only if exposing submit_correction as explicit 501
Lifecycle enum (document + code comments):

State	Meaning
ACTIVE
Called on production path with defined contract
PARTIAL
Instantiated or called under narrow conditions
SANDBOX
Dev/test only
DISABLED
Explicitly off in production
DEAD
No instantiation, no API
FUTURE
Designed, not scheduled this quarter
Classifications (recommended):

Component	State	Notes
export_to_dxf (SMART)
ACTIVE
Default production
ExtractionMode.SIMPLE
FUTURE → ACTIVE after PR-1
Was broken
FeedbackSystem.record_classification
PARTIAL
Only if enable_feedback + SMART + ml_clf
FeedbackSystem.submit_correction
DEAD
Zero call sites
TrainingDataCollector
DEAD
Never instantiated
calibration_integration
PARTIAL
calibration_router only, not main vectorize
GroupSelectionResult telemetry
ACTIVE after PR-2
v2_raw / photo_refined
ACTIVE (recovery)
Do not refactor
Code gates (minimal):

enable_feedback: bool = False default on Phase3Vectorizer factory used by orchestrator (verify current default).
If any route exposes correction: return 501 with body "feedback_correction_disabled: lifecycle DEAD until Loop 3 ratified".
Add module header in vectorizer_phase3.py pointing to lifecycle doc.
Do not: Instantiate TrainingDataCollector, add retrain jobs, or connect to IBG morphology.

Acceptance criteria:

Lifecycle doc merged and referenced from VECTORIZER_TECHNICAL_DEBT_INVENTORY.md.
Grep CI check (optional script): submit_correction( only in definition + docs, not routers.
Recommended sequence (refined)
PR-1 SIMPLE export fix + test
PR-2 Grouping telemetry
PR-3 Lifecycle registry + gates
Lane 4: morphology interpretation trace
Lane 5: topology integrity
Lane 6: primitive extraction
Later: confidence calibration
Step	When	Size
PR-1
Now
~30–80 LOC + test
PR-2
Immediately after
~40–100 LOC, no algorithm change
PR-3
Same sprint, parallel
Docs + 5–15 LOC gates
Lane 4–6
Next sprint
Separate specs per subsystem
Archive ~5.8k LOC
After PR-1–3 green
Separate janitorial PR; grep-gated
Still avoid in this sprint: cognitive archive mixed with P0 (confuses blast radius), classifier changes, IBG provenance Phase 2, touching CANONICAL_RECOVERY.

Constitutional alignment (why this is “surgical”)
P0 restores evidence integrity at the export boundary (deterministic output).
P1 telemetry adds observability without authority (no semantic rewrite).
P1 lifecycle prevents false affordances (half-dead code reading as “learning ready”).
That matches: observability → determinism → containment before confidence or federation.

Definition of done (sprint)
Verification script passes; new test for SIMPLE export.
Dashboard or log query can answer: “How often did grouping fallback fire this week?”
Lifecycle doc lists every vectorizer-adjacent component with a single state.
No change to v2_raw / photo_refined golden outputs.
No new ML training or feedback API surface.
I can implement PR-1 (SIMPLE/UNKNOWN fix + test) in the repo next if you want that as the first surgical commit (still no git commit unless you ask).




Verification was re-run against the repo (grep/read) and the verification script was updated to match your doc corrections. Full output is in:

scripts/governance/verify_vectorizer_audit_results.txt

Run locally in Cursor:

cd C:\Users\thepr\Downloads\luthiers-toolbox
.\scripts\governance\verify_vectorizer_audit.ps1
Results vs corrected docs
Check	Status	Notes
Cognitive LOC + zero imports
PASS
Unchanged
SIMPLE / UNKNOWN empty DXF
PASS (still P0)
Not fixed by doc edits — PR-1 still required
calibration_integration
PASS (PARTIAL)
Matches your correction: calibration_router, constants, phase2_router; not on main vectorize orchestrator
Grouping fallback
PASS
PR-2 telemetry still right
TrainingDataCollector
PASS (DEAD)
Still CRITICAL for authority
Feedback split
PASS
record_classification PARTIAL (1 call @ :3673); submit_correction DEAD (0 call sites)
Dead files / ezdxf bypass
PASS
Unchanged
No FAILs on the claims you corrected. The script now treats calibration and feedback as PASS (PARTIAL) instead of failing on “never called.”

Effect on the remediation plan
Unchanged (still do first):

PR-1 — SIMPLE/UNKNOWN export fix
PR-2 — Grouping fallback telemetry
PR-3 — Lifecycle classify/gate (not revive learning)
Adjusted priorities:

Item	Before	After doc fix
calibration_integration
P0 / CRITICAL
P2 / MEDIUM — document scope or wire main vectorize later
FeedbackSystem whole
P0 “wire feedback”
PR-3 only: gate submit_correction (DEAD); leave record_classification as PARTIAL
True P0 count
4
3 — SIMPLE export, submit_correction, TrainingDataCollector
PR-3 lifecycle table should say:

calibration_integration → PARTIAL (calibration API only)
record_classification → PARTIAL
submit_correction → DEAD
TrainingDataCollector → DEAD
One doc housekeeping item
VECTORIZER_TECHNICAL_DEBT_INVENTORY.md top tables match your commit, but lower sections are stale:

“Semantic Interpretation Impact” still has calibration_integration.py orphaned | CRITICAL (~107)
“Authority Risk” still has FeedbackSystem never triggered | CRITICAL (~116)
Priority matrix still says “P0 CRITICAL | 4 | wire feedback systems” (~167)
Conclusion still says “Wiring FeedbackSystem would enable learning” (~182)
Worth a small follow-up commit so the inventory file doesn’t contradict the correction block.

VECTORIZER_DUPLICATION_MATRIX.md line ~102 still says calibration integration is “orphaned” — consider “partial; not on main vectorize.”

Bottom line
Your corrections align with verification. The surgical sprint is narrower and clearer: three CRITICAL code items, not four. PR-1 remains the only topology/evidence fix; calibration consolidation moves out of this sprint.

I can patch the stale sections in VECTORIZER_TECHNICAL_DEBT_INVENTORY.md and the duplication matrix in a single doc-only commit if you want that next.