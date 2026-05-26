# CAM Dev Order 7V — Fixture & Topology Intelligence Governance

**Status**: COMPLETE  
**Date**: 2026-05-21  
**Preceding**: CAM Dev Orders 7S, 7T, 7U  

## Overview

7V provides fixture-aware topology cognition without geometry mutation. It creates, stores, and packages fixture topology constraints and topology continuity evaluations for human review, while strictly enforcing non-execution invariants.

### Core Principle

Fixture packages are review artifacts. They are not machine jobs or execution plans. 7V records and packages fixture/topology cognition. It does not perform authoritative geometry analysis, repair topology, mutate geometry, or generate machine behavior.

## 7V Invariants (Model-Enforced)

All 7V artifacts enforce these invariants via Pydantic `model_validator`:

| Artifact | Invariant Field | Value | Enforcement |
|----------|-----------------|-------|-------------|
| FixtureTopologyConstraint | `may_modify_geometry` | False | ValueError on True |
| FixtureTopologyConstraint | `execution_authorized` | False | ValueError on True |
| FixtureTopologyConstraint | `machine_output_allowed` | False | ValueError on True |
| TopologyContinuityEvaluation | `auto_correction_attempted` | False | ValueError on True |
| TopologyContinuityEvaluation | `geometry_mutation_attempted` | False | ValueError on True |
| TopologyContinuityEvaluation | `execution_authorized` | False | ValueError on True |
| TopologyContinuityEvaluation | `machine_output_allowed` | False | ValueError on True |
| FixtureStrategyCompatibilityEvaluation | `fixture_execution_present` | False | ValueError on True |
| FixtureStrategyCompatibilityEvaluation | `execution_authorized` | False | ValueError on True |
| FixtureStrategyCompatibilityEvaluation | `machine_output_allowed` | False | ValueError on True |
| ReviewSafeFixturePackage | `executable_payload_present` | False | ValueError on True |
| ReviewSafeFixturePackage | `execution_authorized` | False | ValueError on True |
| ReviewSafeFixturePackage | `machine_output_allowed` | False | ValueError on True |

## Artifact Taxonomy

### FixtureTopologyConstraint

Fixture-aware topology constraints that affect manufacturing interpretation based on fixture configuration.

**Constraint Categories**:
- `clamp_zone` — Areas occupied by clamps
- `keepout_zone` — Areas that must remain clear
- `vacuum_hold` — Vacuum table holding zones
- `bridge_support` — Bridge/tab support locations
- `registration_constraint` — Registration/alignment constraints
- `edge_clearance` — Edge clearance requirements
- `tool_access_constraint` — Tool access limitations
- `fragility_constraint` — Material fragility zones

**Severity Levels**: `low`, `medium`, `high`, `critical`

### TopologyContinuityEvaluation

One evaluation per geometry authority reference. Metadata-based evaluation, not real geometry analysis.

**Risk Categories**:
- `thin_bridge` — Structurally weak bridges
- `unsupported_span` — Long unsupported sections
- `fragmented_region` — Disconnected topology regions
- `clamp_interference` — Clamp/workpiece conflicts
- `edge_instability` — Unstable edges
- `registration_instability` — Registration instability
- `fixture_conflict` — Fixture configuration conflicts
- `continuity_break` — Topology continuity breaks

**Validation Gates**: `green`, `yellow`, `red`

### FixtureStrategyCompatibilityEvaluation

Evaluates strategy ↔ fixture compatibility with operation family hints.

**Operation Family Hints**:
- `rosette` — Recommends vacuum hold, avoids clamp zones
- `binding_channel` — Recommends clamps, edge clearance
- `neck_profile` — Recommends clamps, registration
- `fret_slotting` — Recommends vacuum, avoids clamps
- `body_outline` — Recommends vacuum, bridge support

### ReviewSafeFixturePackage

Human-review bundle collecting ID-only references to:
- Fixture constraints
- Topology evaluations
- Compatibility evaluations
- Geometry authority refs

**Review Statuses**:
- `draft` — Initial creation
- `pending_review` — Awaiting review
- `under_review` — Being reviewed
- `approved_for_export_review` — Ready for export review
- `approved` — Fully approved
- `rejected` — Rejected
- `deferred` — Deferred for later

## Module Structure

```
app/cam/
├── fixture_topology_constraints.py      # FixtureTopologyConstraint model
├── topology_continuity_evaluation.py    # TopologyContinuityEvaluation model
├── fixture_strategy_compatibility.py    # FixtureStrategyCompatibilityEvaluation
├── review_safe_fixture_package.py       # ReviewSafeFixturePackage model
└── fixture_topology_registry.py         # Indexes, CI summary

app/routers/cam/
└── fixture_topology_router.py           # HTTP endpoints
```

## API Endpoints

### Fixture Constraints
- `POST /api/cam/fixture-topology/constraints` — Create constraint
- `POST /api/cam/fixture-topology/constraints/from-fixture` — Create from golden fixture
- `GET /api/cam/fixture-topology/constraints` — List constraints
- `GET /api/cam/fixture-topology/constraints/{id}` — Get constraint

### Topology Evaluations
- `POST /api/cam/fixture-topology/evaluate` — Evaluate topology continuity
- `GET /api/cam/fixture-topology/evaluations` — List evaluations
- `GET /api/cam/fixture-topology/evaluations/{id}` — Get evaluation
- `GET /api/cam/fixture-topology/evaluations/by-geometry/{ref_id}` — By geometry ref

### Fixture/Strategy Compatibility
- `POST /api/cam/fixture-topology/strategy-compatibility` — Evaluate compatibility
- `GET /api/cam/fixture-topology/strategy-compatibility` — List compatibilities
- `GET /api/cam/fixture-topology/strategy-compatibility/{id}` — Get compatibility
- `GET /api/cam/fixture-topology/strategy-compatibility/by-strategy/{id}` — By strategy

### Review Packages
- `POST /api/cam/fixture-topology/review-package` — Create package
- `GET /api/cam/fixture-topology/review-package` — List packages
- `GET /api/cam/fixture-topology/review-package/{id}` — Get package
- `GET /api/cam/fixture-topology/review-package/by-workspace/{id}` — By workspace
- `POST /api/cam/fixture-topology/review-package/{id}/review-status` — Update status
- `POST /api/cam/fixture-topology/review-package/{id}/validate` — Validate package

### CI Summary
- `GET /api/cam/fixture-topology/ci` — Get CI health summary

## Integration Points

### 7S Integration (LuthierOperationWorkspace)
```python
class LuthierOperationWorkspaceV1(BaseModel):
    fixture_package_refs: List[str] = Field(default_factory=list)
```

### 7S Integration (LuthierManufacturingStrategy)
```python
class LuthierManufacturingStrategy(BaseModel):
    fixture_constraint_refs: List[str] = Field(default_factory=list)
    topology_evaluation_refs: List[str] = Field(default_factory=list)
```

### 7U Integration (StrategyExportCompatibilityEvaluation)
```python
class StrategyExportCompatibilityEvaluation(BaseModel):
    fixture_compatibility_refs: List[str] = Field(default_factory=list)
```

## Golden Fixture Adapter

Adapts 7S golden fixtures to 7V fixture constraints:

```python
def create_constraint_from_golden_fixture(
    fixture_id: str,
    clearance_zone_id: Optional[str] = None,
    geometry_authority_ref_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
) -> Optional[List[FixtureTopologyConstraint]]:
```

Maps fixture zone types to constraint categories:
- `clamp` → `clamp_zone`
- `screw` → `keepout_zone`
- `vacuum_port` → `vacuum_hold`
- `registration` → `registration_constraint`
- `custom` → `keepout_zone`

## CI Summary

The CI endpoint returns governance health metrics:

```json
{
  "total_constraints": 5,
  "total_topology_evaluations": 3,
  "total_compatibility_evaluations": 2,
  "total_packages": 1,
  "topology_green_count": 2,
  "topology_yellow_count": 1,
  "topology_red_count": 0,
  "compatibility_green_count": 1,
  "compatibility_yellow_count": 1,
  "compatibility_red_count": 0,
  "packages_with_risks": 0,
  "packages_with_conflicts": 0,
  "packages_without_review": 1,
  "constraints_by_category": {
    "clamp_zone": 2,
    "keepout_zone": 1,
    "vacuum_hold": 1,
    "bridge_support": 1
  },
  "status": "warn"
}
```

**Status Logic**:
- `pass` — No red gates, no yellow gates, all packages reviewed
- `warn` — Yellow gates present OR packages without review
- `fail` — Any red gate present

## Test Coverage

108 tests in `tests/cam/test_fixture_topology_governance.py`:

- **TestFixtureTopologyConstraint** (13 tests) — Model creation, invariants, validation
- **TestGoldenFixtureAdapter** (2 tests) — Golden fixture adaptation
- **TestTopologyContinuityEvaluation** (11 tests) — Model, invariants, evaluation
- **TestTopologyRiskDeclaration** (3 tests) — Risk declaration model
- **TestRiskDetectionFunctions** (6 tests) — Detection functions
- **TestFixtureStrategyCompatibility** (10 tests) — Model, invariants, evaluation
- **TestReviewSafeFixturePackage** (18 tests) — Model, invariants, operations
- **TestFixtureTopologyRegistry** (18 tests) — Registry operations
- **TestCISummary** (9 tests) — CI summary generation
- **TestLuthierWorkspaceIntegration** (2 tests) — 7S workspace integration
- **TestLuthierStrategyIntegration** (3 tests) — 7S strategy integration
- **TestStrategyExportCompatibilityIntegration** (2 tests) — 7U integration
- **TestInvariantEnforcement** (7 tests) — Invariant enforcement

## Guardrails

7V records and packages fixture/topology cognition. It does NOT:
- Perform authoritative geometry analysis
- Repair topology defects
- Mutate geometry
- Generate machine behavior
- Authorize execution
- Allow machine output

These guardrails are enforced via model validators that raise `ValueError` if violated.

## Usage Example

```python
from app.cam.fixture_topology_constraints import create_fixture_constraint
from app.cam.topology_continuity_evaluation import evaluate_topology_continuity
from app.cam.fixture_strategy_compatibility import evaluate_fixture_strategy_compatibility
from app.cam.review_safe_fixture_package import create_review_safe_fixture_package
from app.cam.fixture_topology_registry import (
    register_fixture_constraint,
    register_topology_evaluation,
    register_fixture_strategy_compatibility,
    register_review_safe_fixture_package,
)

# Create constraint
constraint = create_fixture_constraint(
    constraint_category="clamp_zone",
    description="Upper bout clamp zone",
    affected_regions=["upper_bout"],
    severity="high",
)
registered_constraint = register_fixture_constraint(constraint)

# Evaluate topology
evaluation = evaluate_topology_continuity(
    geometry_authority_ref_id="geo-auth-123",
    declared_thin_bridges=True,
)
registered_evaluation = register_topology_evaluation(evaluation)

# Evaluate compatibility
compatibility = evaluate_fixture_strategy_compatibility(
    strategy_id="strategy-456",
    fixture_constraints=[constraint],
)
registered_compatibility = register_fixture_strategy_compatibility(compatibility)

# Create review package
package = create_review_safe_fixture_package(
    workspace_id="ws-789",
    strategy_id="strategy-456",
    fixture_constraint_ids=[registered_constraint.constraint_id],
    topology_evaluation_ids=[registered_evaluation.evaluation_id],
    compatibility_evaluation_ids=[registered_compatibility.evaluation_id],
    title="Upper bout fixture review",
)
registered_package = register_review_safe_fixture_package(package)
```

## Completion Criteria

✅ Fixture constraint taxonomy exists  
✅ Topology continuity evaluations work  
✅ Fixture compatibility evaluation works  
✅ Review-safe fixture packages exist  
✅ Topology mutation attempts are blocked  
✅ Authority boundaries preserved  
✅ No execution authority introduced  
✅ All 108 tests pass  

## Related Documents

- `CAM_7S_GOVERNED_MANUFACTURING_COGNITION_HANDOFF.md` — 7S workspaces/strategies
- `CAM_7T_GEOMETRY_AUTHORITY_REFERENCES_HANDOFF.md` — 7T authority contracts
- `CAM_7U_STRATEGY_EXPORT_INTEROPERABILITY_HANDOFF.md` — 7U export contracts
- `docs/architecture/CAM_GOVERNED_EXPORT_ARCHITECTURE.md` — CAM governance architecture
