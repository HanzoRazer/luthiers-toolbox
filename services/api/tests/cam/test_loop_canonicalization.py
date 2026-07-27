"""CONV-001 — canonical CAM ``Loop`` consolidation guards.

Source: LAB-013 WP-GEOM-3. Three functionally identical ``Loop(BaseModel)``
definitions (``app/schemas/adaptive_schemas.py``,
``app/routers/blueprint_cam_bridge_schemas.py``,
``app/cam/contour_reconstructor.py``) were consolidated onto
``app/schemas/cam_geometry.py``.

This module proves the consolidation is real (single class identity, no
surviving duplicate definitions) and behavior-invariant (constructor,
validation, coercion, serialization, and downstream CAM geometry parity
against replicas of the pre-change definitions).
"""

import ast
import io
from pathlib import Path
from typing import List, Tuple

import ezdxf
import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.cam_geometry import Loop as CanonicalLoop


# =============================================================================
# PRE-CHANGE REPLICAS
#
# Verbatim copies of the two distinct definitions that existed before
# CONV-001. They are the behavioral reference the canonical class must match.
# Do not "clean these up" — their point is to be historically exact.
# =============================================================================

class _LegacyPlainLoop(BaseModel):
    """Replica of the pre-CONV-001 adaptive_schemas / bridge_schemas Loop."""

    pts: List[Tuple[float, float]]


class _LegacyReconstructorLoop(BaseModel):
    """Replica of the pre-CONV-001 contour_reconstructor Loop.

    Carried ``arbitrary_types_allowed = True``, which CONV-001 dropped as
    configuration residue. The parity tests below are the proof that dropping
    it changed no observable behavior.
    """

    pts: List[Tuple[float, float]]

    class Config:
        arbitrary_types_allowed = True


LEGACY_MODELS = [_LegacyPlainLoop, _LegacyReconstructorLoop]


# =============================================================================
# GEOMETRY PARITY FIXTURES
# =============================================================================

RECTANGLE = [(0.0, 0.0), (100.0, 0.0), (100.0, 60.0), (0.0, 60.0)]
NON_AXIS_ALIGNED = [(3.5, 1.25), (91.75, 12.5), (64.0, 88.125), (-12.25, 47.5)]
PRECISION_EDGE = [
    (0.0005, -0.0005),
    (1e-9, 1234567.891011),
    (-1234567.891011, 1e-9),
    (0.1 + 0.2, 0.30000000000000004),
]

GEOMETRY_FIXTURES = [
    pytest.param(RECTANGLE, id="axis-aligned-rectangle"),
    pytest.param(NON_AXIS_ALIGNED, id="non-axis-aligned-polygon"),
    pytest.param(PRECISION_EDGE, id="precision-edge-case"),
]


# =============================================================================
# TC-01 / TC-02 / TC-03 — OWNERSHIP AND IDENTITY
# =============================================================================

AUTHORIZED_SCOPE = ("app/cam", "app/schemas", "app/routers")
CANONICAL_OWNER = "app/schemas/cam_geometry.py"


def _api_root() -> Path:
    # tests/cam/<this file> -> tests/cam -> tests -> services/api
    return Path(__file__).resolve().parents[2]


def _loop_class_definitions() -> List[str]:
    """Return posix-relative paths of executable ``class Loop`` definitions.

    AST-based, so it counts only real class definitions — imports,
    re-exports, annotations, and string mentions are invisible to it, as are
    the deliberately-excluded ``LoopGeometry`` / ``LoopIn`` models (name match
    is exact).
    """
    api_root = _api_root()
    found: List[str] = []

    for scope in AUTHORIZED_SCOPE:
        scope_dir = api_root / scope
        if not scope_dir.is_dir():
            continue
        for path in sorted(scope_dir.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:  # pragma: no cover - would fail collection anyway
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "Loop":
                    found.append(path.relative_to(api_root).as_posix())

    return found


class TestOwnership:
    """The consolidation is structural, not cosmetic."""

    def test_exactly_one_loop_definition_in_authorized_scope(self):
        """TC-01 — one canonical definition, owned by cam_geometry."""
        definitions = _loop_class_definitions()
        assert definitions == [CANONICAL_OWNER], (
            "Exactly one class definition named Loop may exist in "
            f"{AUTHORIZED_SCOPE}, and it must be {CANONICAL_OWNER}. "
            f"Found: {definitions}"
        )

    def test_historical_import_paths_resolve_to_canonical_class(self):
        """TC-02 — every historical access path is the same class object."""
        from app.cam.contour_reconstructor import Loop as ReconstructorLoop
        from app.routers.blueprint_cam_bridge_schemas import Loop as BlueprintLoop
        from app.schemas.adaptive_schemas import Loop as AdaptiveLoop

        assert AdaptiveLoop is CanonicalLoop
        assert BlueprintLoop is CanonicalLoop
        assert ReconstructorLoop is CanonicalLoop

    def test_downstream_consumer_imports_resolve_to_canonical_class(self):
        """Consumers that import Loop transitively also share the identity."""
        from app.cam.project_adapter import Loop as ProjectAdapterLoop
        from app.routers.adaptive.dxf_router import Loop as DxfRouterLoop
        from app.routers.blueprint_cam.extraction import Loop as ExtractionLoop

        assert ProjectAdapterLoop is CanonicalLoop
        assert DxfRouterLoop is CanonicalLoop
        assert ExtractionLoop is CanonicalLoop

    def test_no_import_cycle(self):
        """TC-03 — all affected modules import cleanly together."""
        import importlib

        for module in (
            "app.schemas.cam_geometry",
            "app.schemas.adaptive_schemas",
            "app.routers.blueprint_cam_bridge_schemas",
            "app.cam.contour_reconstructor",
            "app.cam.project_adapter",
            "app.routers.blueprint_cam.extraction",
            "app.routers.adaptive.dxf_router",
        ):
            assert importlib.import_module(module) is not None

    def test_compatibility_reexport_stays_in_dunder_all(self):
        """``adaptive_schemas`` publishes Loop in ``__all__``; keep it that way.

        ``blueprint_cam_bridge_schemas`` never declared ``__all__`` and this
        change does not add one — a restrictive ``__all__`` there would hide
        its other public schemas from ``import *``.
        """
        import app.routers.blueprint_cam_bridge_schemas as bridge_schemas
        import app.schemas.adaptive_schemas as adaptive_schemas

        assert "Loop" in adaptive_schemas.__all__
        assert not hasattr(bridge_schemas, "__all__")
        assert bridge_schemas.Loop is CanonicalLoop


# =============================================================================
# TC-04 .. TC-07 — CONSTRUCTOR AND VALIDATION PARITY
# =============================================================================

class TestConstructorParity:
    """Accepted and rejected inputs are unchanged from both legacy models."""

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_keyword_construction_parity(self, pts):
        """TC-05 — keyword construction succeeds identically."""
        canonical = CanonicalLoop(pts=pts)
        for legacy in LEGACY_MODELS:
            assert canonical.pts == legacy(pts=pts).pts

    def test_positional_construction_rejected_by_both(self):
        """TC-04 — pydantic models never accepted positional args; still don't."""
        with pytest.raises(TypeError):
            CanonicalLoop(RECTANGLE)
        for legacy in LEGACY_MODELS:
            with pytest.raises(TypeError):
                legacy(RECTANGLE)

    def test_no_defaults_pts_is_required(self):
        """TC-06 — ``pts`` had no default before and has none now."""
        assert CanonicalLoop.model_fields["pts"].is_required()
        for legacy in LEGACY_MODELS:
            assert legacy.model_fields["pts"].is_required()
        with pytest.raises(ValidationError):
            CanonicalLoop()

    def test_integer_coordinates_coerced_to_float(self):
        """Integer input coerces identically (proves config was inert)."""
        raw = [(0, 0), (10, 0), (10, 5)]
        canonical = CanonicalLoop(pts=raw)
        assert canonical.pts == [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0)]
        assert all(isinstance(c, float) for pt in canonical.pts for c in pt)
        for legacy in LEGACY_MODELS:
            assert legacy(pts=raw).pts == canonical.pts

    def test_list_points_coerced_to_tuples(self):
        """List-of-list input coerces to tuples identically."""
        raw = [[0, 0], [10, 0], [10, 5]]
        canonical = CanonicalLoop(pts=raw)
        assert canonical.pts == [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0)]
        assert all(isinstance(pt, tuple) for pt in canonical.pts)
        for legacy in LEGACY_MODELS:
            assert legacy(pts=raw).pts == canonical.pts

    @pytest.mark.parametrize(
        "bad_pts,label",
        [
            ([(0.0, 0.0, 0.0)], "three-element-point"),
            ([(0.0,)], "one-element-point"),
            ([("a", "b")], "nonnumeric-point"),
            ([(0.0, None)], "none-coordinate"),
            ("not-a-sequence-of-points", "scalar-string"),
            ([0.0, 1.0], "flat-scalar-list"),
            (None, "none-pts"),
        ],
    )
    def test_invalid_input_parity(self, bad_pts, label):
        """TC-07 — rejected inputs stay rejected, with the same error codes."""
        with pytest.raises(ValidationError) as canonical_exc:
            CanonicalLoop(pts=bad_pts)
        canonical_codes = sorted(e["type"] for e in canonical_exc.value.errors())

        for legacy in LEGACY_MODELS:
            with pytest.raises(ValidationError) as legacy_exc:
                legacy(pts=bad_pts)
            assert sorted(e["type"] for e in legacy_exc.value.errors()) == canonical_codes, (
                f"error classification drifted for {label} vs {legacy.__name__}"
            )

    def test_empty_loop_accepted_by_both(self):
        """An empty point list was permitted before; it still is."""
        assert CanonicalLoop(pts=[]).pts == []
        for legacy in LEGACY_MODELS:
            assert legacy(pts=[]).pts == []

    def test_mutability_parity(self):
        """Models were never frozen; assignment behavior is unchanged."""
        assert CanonicalLoop.model_config.get("frozen") in (None, False)
        canonical = CanonicalLoop(pts=RECTANGLE)
        canonical.pts = list(NON_AXIS_ALIGNED)
        assert canonical.pts == NON_AXIS_ALIGNED

    def test_equality_parity(self):
        """Pydantic value-equality within a class is unchanged."""
        assert CanonicalLoop(pts=RECTANGLE) == CanonicalLoop(pts=RECTANGLE)
        assert CanonicalLoop(pts=RECTANGLE) != CanonicalLoop(pts=NON_AXIS_ALIGNED)


# =============================================================================
# TC-08 .. TC-10 — DATA AND SERIALIZATION PARITY
# =============================================================================

class TestSerializationParity:
    """Wire contract is byte-identical to the pre-change definitions."""

    def test_field_parity(self):
        """TC-08 — same field set, same annotation."""
        assert list(CanonicalLoop.model_fields) == ["pts"]
        for legacy in LEGACY_MODELS:
            assert list(legacy.model_fields) == list(CanonicalLoop.model_fields)
            assert (
                legacy.model_fields["pts"].annotation
                == CanonicalLoop.model_fields["pts"].annotation
            )

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_python_dump_parity(self, pts):
        """TC-09 — model_dump output identical."""
        canonical = CanonicalLoop(pts=pts).model_dump()
        for legacy in LEGACY_MODELS:
            assert legacy(pts=pts).model_dump() == canonical

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_json_dump_parity(self, pts):
        """TC-09 — JSON serialization identical, including field name."""
        canonical = CanonicalLoop(pts=pts).model_dump_json()
        assert '"pts"' in canonical
        for legacy in LEGACY_MODELS:
            assert legacy(pts=pts).model_dump_json() == canonical

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_round_trip_parity(self, pts):
        """TC-10 — dump → validate → dump loses nothing."""
        first = CanonicalLoop(pts=pts).model_dump_json()
        second = CanonicalLoop.model_validate_json(first).model_dump_json()
        assert first == second

        for legacy in LEGACY_MODELS:
            legacy_json = legacy(pts=pts).model_dump_json()
            crossed = CanonicalLoop.model_validate_json(legacy_json)
            assert crossed.model_dump_json() == legacy_json

    def test_json_schema_parity(self):
        """OpenAPI-visible schema is unchanged apart from the class title."""

        def normalize(schema):
            schema = dict(schema)
            schema.pop("title", None)
            schema.pop("description", None)
            return schema

        canonical = normalize(CanonicalLoop.model_json_schema())
        for legacy in LEGACY_MODELS:
            assert normalize(legacy.model_json_schema()) == canonical


# =============================================================================
# TC-11 .. TC-15 — GEOMETRY AND DOWNSTREAM CAM PARITY
# =============================================================================

def _dxf_with_closed_lwpolyline(pts, layer: str) -> bytes:
    doc = ezdxf.new("R2000")
    doc.layers.add(layer)
    msp = doc.modelspace()
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


def _dxf_with_line_loop(pts, layer: str) -> bytes:
    doc = ezdxf.new("R2000")
    doc.layers.add(layer)
    msp = doc.modelspace()
    closed = list(pts) + [pts[0]]
    for start, end in zip(closed, closed[1:]):
        msp.add_line(start, end, dxfattribs={"layer": layer})
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


class TestGeometryParity:
    """Vertex order, closure, orientation, and bounds survive the move."""

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_vertex_order_parity(self, pts):
        """TC-11 — ordering is preserved exactly, not normalized."""
        assert CanonicalLoop(pts=pts).pts == [tuple(map(float, p)) for p in pts]

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_closure_parity(self, pts):
        """TC-12 — the model neither adds nor removes a closing vertex."""
        loop = CanonicalLoop(pts=pts)
        assert len(loop.pts) == len(pts)
        assert loop.pts[0] != loop.pts[-1]

        explicitly_closed = list(pts) + [pts[0]]
        closed_loop = CanonicalLoop(pts=explicitly_closed)
        assert len(closed_loop.pts) == len(pts) + 1
        assert closed_loop.pts[0] == closed_loop.pts[-1]

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_orientation_parity(self, pts):
        """TC-13 — signed area (winding) is unchanged, both directions."""

        def signed_area(points):
            total = 0.0
            for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
                total += x1 * y2 - x2 * y1
            return total / 2.0

        ccw = CanonicalLoop(pts=pts)
        cw = CanonicalLoop(pts=list(reversed(pts)))
        assert signed_area(ccw.pts) == pytest.approx(-signed_area(cw.pts))
        for legacy in LEGACY_MODELS:
            assert signed_area(legacy(pts=pts).pts) == signed_area(ccw.pts)

    @pytest.mark.parametrize("pts", GEOMETRY_FIXTURES)
    def test_bounds_parity(self, pts):
        """TC-14 — bounding envelope identical to the legacy models."""

        def bounds(points):
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            return (min(xs), min(ys), max(xs), max(ys))

        canonical = bounds(CanonicalLoop(pts=pts).pts)
        for legacy in LEGACY_MODELS:
            assert bounds(legacy(pts=pts).pts) == canonical

    def test_blueprint_cam_extraction_returns_canonical_loops(self):
        """TC-15 — blueprint→CAM entry point produces canonical geometry."""
        from app.routers.blueprint_cam.extraction import extract_loops_from_dxf

        dxf_bytes = _dxf_with_closed_lwpolyline(RECTANGLE, "GEOMETRY")
        loops, warnings = extract_loops_from_dxf(dxf_bytes, layer_name="GEOMETRY")

        assert loops, f"expected one extracted loop, warnings={warnings}"
        assert all(isinstance(loop, CanonicalLoop) for loop in loops)
        assert loops[0].pts == RECTANGLE

    def test_contour_reconstructor_returns_canonical_loops(self):
        """TC-15 — contour reconstruction entry point produces canonical geometry."""
        from app.cam.contour_reconstructor import reconstruct_contours_from_dxf

        dxf_bytes = _dxf_with_line_loop(RECTANGLE, "Contours")
        result = reconstruct_contours_from_dxf(dxf_bytes, layer_name="Contours")

        assert result.loops, f"expected one reconstructed loop, warnings={result.warnings}"
        assert all(isinstance(loop, CanonicalLoop) for loop in result.loops)
        assert set(result.loops[0].pts) == set(RECTANGLE)

    def test_reconstruction_result_accepts_canonical_loops(self):
        """The reconstructor's own container still validates canonical loops."""
        from app.cam.contour_reconstructor import ReconstructionResult

        result = ReconstructionResult(loops=[CanonicalLoop(pts=RECTANGLE)])
        assert result.loops[0].pts == RECTANGLE
        assert result.outer_loop_idx == 0

    def test_adaptive_plan_accepts_canonical_loops(self):
        """TC-15 — adaptive planning request still validates canonical loops."""
        from app.schemas.adaptive_schemas import PlanIn

        plan = PlanIn(loops=[CanonicalLoop(pts=RECTANGLE)], tool_d=6.0)
        assert plan.loops[0].pts == RECTANGLE
        assert isinstance(plan.loops[0], CanonicalLoop)

    def test_blueprint_bridge_response_accepts_canonical_loops(self):
        """The bridge response model's List[Loop] field is the canonical type."""
        from app.routers.blueprint_cam_bridge_schemas import (
            BlueprintToAdaptiveResponse,
        )

        response = BlueprintToAdaptiveResponse(
            loops_extracted=1,
            loops=[CanonicalLoop(pts=RECTANGLE)],
            moves=[],
            stats={},
        )
        assert isinstance(response.loops[0], CanonicalLoop)
        assert response.model_dump()["loops"][0]["pts"] == RECTANGLE
