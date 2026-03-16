# ADR-004: Promote _experimental/cnc_production to Production Module

## Status
Pending — do not delete or refactor until this ADR is resolved

## Date
2026-03-16

## Finding
_experimental/cnc_production/ is NOT dead code. It is actively imported by three production consumers:

| Consumer | Imports |
|----------|---------|
| cam_core/saw_lab/learning.py | live_learn_ingestor, risk_buckets, joblog/storage |
| routers/learned_overrides_router.py | LaneKey, LaneOverrides, LearnedOverridesStore |
| core/store_registry.py:184 | LearnedOverridesStore factory |

The "experimental" label is a facade. This code is wired into production routing and the SAW Lab learning pipeline.

## Three deflection implementations exist (not unified)
| Module | Purpose | LOC |
|--------|---------|-----|
| _experimental/cnc_production/feeds_speeds/core/deflection_model.py | Router bits | 14 |
| saw_lab/calculators/saw_deflection.py | Saw blades Euler-Bernoulli | 176 |
| calculators/saw/deflection_adapter.py | Saw blades simplified | 139 |

These serve different physical domains and should NOT be merged without domain expert review.

## Decision
Promote _experimental/cnc_production/ to app/cnc_production/ as a first-class production module.

## Migration steps (do not execute until Generator Remediation GEN-1 through GEN-5 is complete)
1. Move _experimental/cnc_production/ → cnc_production/ at app root
2. Update imports in:
   - cam_core/saw_lab/learning.py
   - routers/learned_overrides_router.py
   - core/store_registry.py
3. Register router in router_registry/manifest.py
4. Update .cursorrules — remove from experimental do-not-touch list
5. Add to REMEDIATION_STATUS as resolved item

## Why not now
The learned_overrides_router.py is in the NEEDS_REVIEW category from the router safety audit. The promotion should happen as a single coordinated move after the router consolidation sprint is complete, not piecemeal.

## References
- ROUTER_SAFETY_AUDIT.md
- UNFINISHED_REMEDIATION_EFFORTS.md #25 (_experimental/ modules)
- World-class features: species-aware learned feeds/speeds
