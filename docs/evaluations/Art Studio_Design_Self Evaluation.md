According to a document from December 20, 2025, your sandbox (and the broader repo architecture it plugs into) has undergone a major maturity shift from “MVP that works” to “production architecture with enforceable rules”—centered on the Fortran Rule (“all math operations must be in their own subroutine”) and a canonical service-layer map that keeps routing/HTTP thin and computation testable.
Below is an evaluation of the Art Studio sandbox as a system, aligned to that new philosophy.
________________________________________
Executive summary
Delegated task (what this sandbox is responsible for)
Art Studio (Design-First mode) is the “creative input + preview” lane. It should:
•	Accept/edit a RosetteParamSpec
•	Call feasibility/preview services (deterministic, governed)
•	Show the operator “safe/unsafe + why”
•	Persist user artifacts (patterns, snapshots, etc.)
•	Never bury math in routers or duplicate canonical algorithms
This aligns directly with the repo’s governing principle: routers are HTTP only; computation lives in modules.
Why this is now “production-ready architecture”
The repo’s architectural transformation explicitly targets:
•	No scattered endpoints
•	No duplicated implementations
•	No hardcoded constants
•	CI/governance tests to prevent drift/regression
That’s exactly the foundation you want before scaling Art Studio feature bundles (Pattern Library, Generators, Preview, Snapshots, Macros, Replay, etc.).
________________________________________
Repo schema placement
Your current “canonical map” says where things belong. This is the most important alignment constraint.
Canonical placement:
•	Pure Geometry Math → geometry/
•	Instrument Math → instrument_geometry/
•	CAM Algorithms → cam/
•	Domain Calculators → calculators/
•	Domain Modules → rmos/, saw_lab/
•	Orchestration / Stores / Bridges → services/
What this means for Art Studio:
•	Art Studio routers live in your API router area (or art_studio/api/ if you’re keeping Art Studio as a domain module).
•	Any “preview scoring / feasibility scoring” belongs in a domain module service (Art Studio or RMOS), not inside the router.
•	Any real geometry math should be pulled from canonical geometry modules (not re-implemented in Art Studio routes), consistent with the transformation examples.
________________________________________
Architecture and flow
1) Design-First workflow (system flow)
1.	User edits RosetteParamSpec in Art Studio UI
2.	UI calls preview endpoints (SVG render) + feasibility endpoints (deterministic scoring)
3.	UI displays:
o	Score/risk bucket
o	Warnings
o	(later) ring-level diagnostics
4.	Only when feasibility is acceptable does the user proceed to exports/toolpaths
This matches the repo’s “director/oracle” concept: deterministic evaluation sits in the governed domain modules; routers simply expose it.
2) Router behavior (must be thin)
Your governance posture is explicit:
•	“Routers must delegate calculations to math modules, not compute inline.”
•	The governance tests literally scan router files for inline-math patterns (sin/cos/tan, hardcoded pi, circle formulas, etc.).
So every Art Studio endpoint should follow:
•	Validate request → call service → return response
•	No inline trig/geometry formulas
•	No “quick helper math” inside routers unless explicitly grandfathered (and then temporary)
________________________________________
Example of code produced (and how it should look in this architecture)
Your repo’s transformation report shows the ideal pattern: a router that used to compute inline math becomes a router that imports and delegates to a canonical module.
Pattern to copy for Art Studio feasibility + preview:
•	art_studio/api/*.py: request/response + call domain service
•	art_studio/services/*.py: orchestration logic (assemble inputs, call calculators/RMOS, aggregate results)
•	calculators/service.py: canonical orchestrations for chipload/heat/deflection/rim-speed/BOM
•	canonical geometry helpers pulled from geometry/arc_utils.py rather than duplicated circle code, etc.
That is the “drop-in style” you’ve been aiming for.
________________________________________
Edge cases to handle (Design-First mode)
These are the failure modes you’ll hit in real use:
Input integrity / validation
•	Ring widths sum > rosette band width (or becomes physically impossible)
•	Negative widths, zero diameters, inner >= outer, etc.
•	Too many rings (UI spam / compute load)
•	Missing optional fields (tile length, pattern metadata)
Calculator contract mismatches
•	Missing tool/material defaults (context not set)
•	Units mismatched (mm/in) — silently corrupts feasibility if not guarded
Performance
•	Batch feasibility with many candidates can become heavy; needs:
o	request caps
o	debouncing on the frontend
o	caching by fingerprint (you already planned this in later bundles)
Determinism / reproducibility
•	Feasibility must remain deterministic given the same inputs (otherwise logs/replay become meaningless)
________________________________________
Observability and testing (what “good” looks like)
Observability
The repo’s shift is explicitly toward governance + auditability (“CI-enforced contracts”).
For Art Studio + feasibility:
•	Log each call with:
o	mode (Design-First)
o	spec fingerprint
o	context (tool/material/presets)
o	result score/risk/warnings
•	Keep payload sizes reasonable (store fingerprints + references, not giant blobs everywhere)
Testing layers
You now have governance tests that prevent structural backsliding:
•	No scattered endpoints
•	No /api/api/ double prefixes
•	API stability snapshots
•	Fortran Rule router scanning (no inline math / no hardcoded pi)
For Art Studio-specific correctness, add:
•	Unit tests for feasibility aggregator service
•	API tests for /api/art/rosette/feasibility/batch
•	Property-style tests for spec validation (inner/outer/ring widths)
________________________________________
Operational risks
Biggest risks (in priority order)
1.	Architectural drift: someone adds “just a tiny bit of math” in a router
o	Mitigation: Fortran Rule scanning + code review rules.
2.	Duplicate implementations: someone re-implements circle generation or arc tessellation in Art Studio
o	Mitigation: canonical geometry/arc_utils.py usage; governance culture.
3.	Nondeterministic feasibility: mixing “AI-ish heuristics” into feasibility paths
o	Mitigation: keep feasibility deterministic; AI is sandboxed elsewhere (your shift).
4.	Silent unit errors: mm/in mismatch contaminates scoring
o	Mitigation: strict schema + explicit units + tests
5.	Performance regressions as you add what-if optimization and replay
o	Mitigation: caching by fingerprint; bounded batch sizes; profiling on batch endpoints
________________________________________
How it fails gracefully
When the system breaks, it should break predictably:
•	Invalid RosetteParamSpec → 422 with clear validation error (field-level)
•	Missing presets/context → “cannot evaluate feasibility (missing tool/material)” warning result (YELLOW) rather than a crash, if you choose “soft fail”
•	Calculator exception → return RED with a warning “Feasibility evaluation failed: ” + log stack trace server-side
•	Preview SVG fails → return placeholder SVG + warning in response; UI shows “Preview unavailable”
•	Batch overload → 413/422/429 style response with message “Too many candidates; reduce batch size”
This supports your operator-centric workflow: no mystery failures, no silent corruption.
________________________________________
Re-review checklist (use this after changes)
A) Architecture invariants (must remain true)
•	Routers contain no inline math (no trig formulas, no hardcoded pi, no geometry loops)
•	Art Studio routers delegate to art_studio/services/* or rmos/*
•	Geometry computations come from canonical modules (geometry/, instrument_geometry/, cam/) not re-implemented
•	Calculators remain the orchestrators of math modules (no duplicate formulas)
(These are directly aligned to the Fortran Rule and canonical layering.)
B) Governance / CI safety
•	pytest tests/test_route_governance.py -v passes (no new violations)
•	No new routers added without being included in the canonical domain + prefix pattern
•	No “temporary exceptions” added unless accompanied by TODO and planned cleanup
C) API behavior
•	/api/art/rosette/feasibility/batch rejects invalid specs cleanly
•	Batch results preserve request order and are stable/deterministic
•	Response schema contains enough data for UI gating (risk bucket + warnings)
D) Data / logging
•	Each feasibility call logs: mode, fingerprint, context, result
•	Logs avoid storing massive payloads unless explicitly required
•	CSV export produces consistent headers and escapes strings safely
E) UX / operator safety
•	RED results block “apply” actions by default
•	“Jump to design” always re-runs feasibility (or warns if stale)
•	Undo/redo is bounded (no infinite growth)
________________________________________
Recommendation for the next developmental step
Given the architecture shift, the best “next delivery” is the one that locks correctness and determinism before adding more operator power:
1.	Finalize Ring-level diagnostics backend (31.0.8) with a strict schema, and add tests that ensure:
•	ring_diagnostics lengths match ring count
•	worst-ring identification is stable
2.	Then ship the UI diagnostics panel (31.0.7) + safety gates, because it becomes the foundation for:
•	fix-it macros
•	macro replay
•	what-if optimization
•	culprit pinpointing
That sequence keeps you aligned with the repo’s production posture: build deterministic, testable primitives first; then build operator tooling on top.
