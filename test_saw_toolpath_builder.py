Here is the tiny pytest bundle you requested.
You can drop this directly into:

services/api/tests/test_saw_toolpath_builder.py


It is intentionally minimal but fully executable once your skeleton files exist.
It verifies:

RMOS + Saw Lab + Toolpath Builder all connect end-to-end.

You get a valid RmosToolpathPlan.

At least one operation is produced.

Runtime estimates are > 0.

No crashes anywhere in the pipeline.

✅ test_saw_toolpath_builder.py
"""
Tiny test to validate that the Saw Toolpath Builder 2.0 skeleton is wired
end-to-end and produces a valid RmosToolpathPlan.

This test does NOT check physics correctness, geometry, or optimization.
It simply ensures the entire chain runs without error:

    RosetteParamSpec + RmosContext
        → SawCutContext
        → Saw Path Planner
        → RmosToolpathPlan

Drop this file into:
    services/api/tests/test_saw_toolpath_builder.py
"""

from rmos.api_contracts import RmosContext
from art_studio.schemas.rosette_params import RosetteParamSpec
from toolpath.saw_engine import plan_saw_toolpaths_for_design


def test_saw_toolpath_builder_end_to_end():
    """
    A minimal “smoke test” for plan_saw_toolpaths_for_design().
    Ensures the system produces a valid toolpath plan with at least one operation.
    """

    # ----------------------------
    # 1. Create dummy design spec
    # ----------------------------
    # These values do not matter for the skeleton — they only need to pass Pydantic validation.
    design = RosetteParamSpec(
        outer_diameter_mm=100.0,
        ring_count=3,
        seed=42,
        # Add any other fields required by your actual schema.
    )

    # ----------------------------
    # 2. Create minimal RMOS context
    # ----------------------------
    context = RmosContext(
        tool_id="saw:test_blade",       # MUST start with "saw:" for Saw Toolpath Builder
        material_id="mahogany",
        search_budget={"max_candidates": 1},
        caller="pytest",
        version="test",
    )

    # ----------------------------
    # 3. Call the Saw Toolpath Builder
    # ----------------------------
    plan = plan_saw_toolpaths_for_design(design, context)

    # ----------------------------
    # 4. Assertions
    # ----------------------------
    # It must produce a valid RmosToolpathPlan object
    assert plan is not None

    # It must contain at least one conceptual saw operation
    assert hasattr(plan, "operations")
    assert len(plan.operations) > 0, "Saw toolpath plan produced zero operations."

    # Each operation should have IDs, descriptions, metadata
    for op in plan.operations:
        assert op.op_id is not None
        assert isinstance(op.description, str)
        assert op.metadata is not None

        # Skeleton uses empty ml_paths — OK for now.
        assert hasattr(op, "ml_paths")

        # Runtime estimate must be > 0
        assert op.estimated_runtime_min > 0

    # The plan should have a total runtime field
    assert plan.total_estimated_runtime_min > 0

    # And some metadata from the SawCutPlan
    assert "saw_plan_is_feasible" in plan.metadata

    print("\nSaw Toolpath Builder skeleton end-to-end test passed.")

📌 Notes for You (Developer Guidance)
This test verifies:

Your imports work.

plan_saw_toolpaths_for_design() doesn’t crash.

SawCutContext builds correctly.

Saw Path Planner returns a valid plan.

Toolpath Builder mapping works.

RMOS models accept the plan.

This test does NOT attempt to:

Validate physics correctness

Validate geometry correctness

Validate toolpath realism

Test shapely or M/L engines

Test kickback/bite/heat/etc.

Those come later with deeper integration tests.


