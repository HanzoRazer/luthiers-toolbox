# Luthier’s ToolBox – Route Reduction Phase 2 Handoff

## Context & Objective

- **Goal:** Reduce FastAPI route count from 727 to <300 (WP-2, API Surface Reduction).
- **Current State:** Route count at 530 after systematic disabling of unused/duplicate routers and legacy lanes.
- **Scope:** Focused on backend (FastAPI, Python 3.11+), with frontend usage checks (Vue 3, Pinia, TypeScript) to ensure no breakage.

## Approach & Methodology

1. **Cluster Analysis:** Identified large route clusters (CAM aggregator, RMOS, Art Studio, Compare, Saw Lab, Workflow Sessions, Runs v2).
2. **Frontend Usage Audit:** Used `grep_search` to confirm which API prefixes are actively consumed by the frontend (see [copilot-instructions.md](../../.github/copilot-instructions.md)).
3. **Disabling Pattern:** For unused routers, set `router = None` and wrap registration in `if router:` check in [main.py](services/api/app/main.py) and aggregator modules (see lines referencing `WP-2` comments).
4. **Duplicate/Legacy Cleanup:** Removed or disabled legacy routers, duplicate subrouters, and double-prefix bugs (see [cam/routers/aggregator.py](services/api/app/cam/routers/aggregator.py)).
5. **Batch Commits:** Changes committed in phases (2A–2E), with route count and distribution tracked after each batch.

## Key Findings

- **High-Impact Clusters:**
  - CAM aggregator ([cam/routers/aggregator.py](services/api/app/cam/routers/aggregator.py))
  - RMOS ([main.py](services/api/app/main.py), search for `rmos_` and `runs_`)
  - Art Studio ([main.py](services/api/app/main.py), search for `art_`)
  - Compare ([main.py](services/api/app/main.py), search for `compare_`)
  - Saw Lab Batch ([main.py](services/api/app/main.py), search for `saw_`)
  - Workflow Sessions ([main.py](services/api/app/main.py), search for `workflow_sessions_router`)
  - Runs v2 ([main.py](services/api/app/main.py), search for `runs_`)
- **Reductions Achieved:**
  - Disabled `instrument_geometry_router`, `pipeline_presets_router`, `rmos_patterns_router`, `rmos_saw_ops_router`, and several CAM subrouters (monitoring, utility, export) (see [main.py](services/api/app/main.py) and [cam/routers/aggregator.py](services/api/app/cam/routers/aggregator.py)).
- **Legacy/Unused:** Many legacy routers and subrouters had no frontend usage and were safely disabled.
- **Remaining Opportunities:** Further reduction possible in large clusters by deeper frontend usage analysis and consolidation.

## Pending Actions

- **Further Cluster Reduction:** Continue systematic disabling in large clusters, especially within RMOS, Art Studio, and CAM aggregator.
- **Exception Audit:** 278 `except Exception` statements remain (WP-1), to be addressed after route reduction (see [copilot-instructions.md](../../.github/copilot-instructions.md), [FENCE_REGISTRY.json](FENCE_REGISTRY.json)).
- **Analytics Endpoint Bug:** High-priority, tracked in [TODO_HIGH_PRIORITY.md](TODO_HIGH_PRIORITY.md), to be fixed post-reduction.

## Risks & Safeguards

- **Frontend Breakage:** All router removals cross-checked with frontend usage to avoid breaking active features (see grep_search results in session logs).
- **Golden Path Integrity:** Golden snapshot tests (DXF → GRBL) remain locked; no changes to manufacturing intent without explicit review (see [tests/README.md](services/api/tests/README.md)).
- **Governance Compliance:** All changes respect architectural fences and operation lane governance (see [FENCE_REGISTRY.json](FENCE_REGISTRY.json), [ROUTER_MAP.md](ROUTER_MAP.md)).

## Recommendations for Chief Engineer

- **Review Disabled Routers:** Confirm that all disabled routers are truly unused and not required for future features (see [main.py](services/api/app/main.py), search for `router = None`).
- **Prioritize Next Clusters:** Advise on which large clusters to target next for maximum reduction impact.
- **Consult on Consolidation:** Recommend consolidation strategies for overlapping endpoints within aggregators (see [cam/routers/aggregator.py](services/api/app/cam/routers/aggregator.py)).
- **Approve Exception Audit Plan:** Validate plan for exception hardening post-route reduction.

## Reference Materials

- [ROUTER_MAP.md](ROUTER_MAP.md): Full router breakdown and consolidation status.
- [FENCE_REGISTRY.json](FENCE_REGISTRY.json): Architectural boundary enforcement.
- [copilot-instructions.md](../../.github/copilot-instructions.md): AI agent and codebase operation patterns.
- [TODO_HIGH_PRIORITY.md](TODO_HIGH_PRIORITY.md): High-priority bug tracking.
- [main.py](services/api/app/main.py): Central router registration and current state.
- [cam/routers/aggregator.py](services/api/app/cam/routers/aggregator.py): CAM router aggregator and subrouter disables.
- [tests/README.md](services/api/tests/README.md): Golden snapshot policy and test guarantees.

---

Ready for Chief Engineer review and consultation. Please advise on next reduction priorities and any concerns before proceeding.
