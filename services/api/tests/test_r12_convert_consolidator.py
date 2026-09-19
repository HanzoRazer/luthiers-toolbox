"""
LTB-R12-002 D4 — convert real `LayerConsolidator` output, not a hand-built imitation.

The landed smoke test constructs a consolidator-**shaped** document itself. This runs
the producer: synthetic raw LINE dump -> `LayerConsolidator` -> R2000 with LWPOLYLINE,
then converts that to R12 and checks what survived.

These tests pass against `22e6768`. They are **missing coverage, not a defect
reproduction** — the four reproductions live in `test_r12_convert_gaps.py`. This file
exists because the gap the review named was that nothing exercised the real producer.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

sys.path.insert(0, str(Path(__file__).parent / "fixtures" / "r12_convert"))

from app.cam.r12_convert import convert_document, semantic_record  # noqa: E402
from generate import generate_consolidator_fixture  # noqa: E402


@pytest.fixture
def consolidated(tmp_path):
    """Real consolidator output, regenerated per test rather than committed."""
    record = generate_consolidator_fixture(tmp_path)
    return record, ezdxf.readfile(str(record["consolidated"]))


def test_the_producer_emits_what_the_converter_will_be_asked_to_convert(consolidated):
    """R2000 with LWPOLYLINE — the shape that used to come back empty."""
    record, doc = consolidated
    assert record["input_lines"] == 64
    assert record["output_polylines"] == 2

    assert doc.dxfversion == "AC1015", "consolidation emits R2000 for LWPOLYLINE support"
    kinds = {e.dxftype() for e in doc.modelspace()}
    assert kinds == {"LWPOLYLINE"}, kinds
    assert {e.dxf.layer for e in doc.modelspace()} == {"BODY_OUTLINE", "CAVITY"}


def test_real_consolidator_output_converts_with_its_meaning_intact(consolidated):
    """Every semantic record survives, and both layers are defined in the output."""
    _, doc = consolidated
    source_records = sorted(str(semantic_record(e)) for e in doc.modelspace())

    target, report = convert_document(doc, "R12")

    assert report["conversions"] == {"LWPOLYLINE->POLYLINE": 2}
    converted_records = sorted(str(semantic_record(e)) for e in target.modelspace())
    assert converted_records == source_records, (
        "LWPOLYLINE and POLYLINE reduce to the same semantic record; a difference "
        "here is lost geometry, not a change of representation"
    )
    for layer in ("BODY_OUTLINE", "CAVITY"):
        assert layer in target.layers, f"{layer} must be defined, not merely referenced"


def test_this_fixture_cannot_reach_g1_and_says_so(consolidated):
    """Asserted, not assumed: the producer never sets elevation.

    `LayerConsolidator` calls `add_lwpolyline(chain, close=..., dxfattribs={"layer":
    ...})`. So this fixture cannot exercise G1, and G1's reproduction cannot be folded
    into it — the two are independent and both are needed.
    """
    _, doc = consolidated
    elevations = {round(float(e.dxf.elevation), 6) for e in doc.modelspace()
                  if e.dxftype() == "LWPOLYLINE"}
    assert elevations == {0.0}, (
        f"the consolidator now sets elevation ({elevations}); if that is deliberate, "
        "this fixture reaches G1 and the G1 reproduction should be reconsidered"
    )


def test_the_fixture_is_reproducible_in_content(tmp_path):
    """Regeneration yields the same drawing.

    Not byte-identical: an R2000 save stamps `$FINGERPRINTGUID`, `$VERSIONGUID` and two
    ezdxf write timestamps, all of which vary per run. Those are the writer's, not the
    fixture's, so equality is asserted on meaning.
    """
    first = generate_consolidator_fixture(tmp_path / "a")
    second = generate_consolidator_fixture(tmp_path / "b")

    def records(path):
        return sorted(str(semantic_record(e))
                      for e in ezdxf.readfile(str(path)).modelspace())

    assert records(first["consolidated"]) == records(second["consolidated"])
    assert first["layer_stats"] == second["layer_stats"]
