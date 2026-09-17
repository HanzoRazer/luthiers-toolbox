"""Fail-closed R12 conversion: style definitions, blocks, paper space, unverified types.

These tests reopen or inspect converter exceptions. A successful conversion_report
is not evidence -- that is how the empty-file defect reached production.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from app.cam.r12_convert import (
    FidelityError,
    UnconvertibleEntity,
    convert_document,
    convert_file,
    verify_saved_file,
)


def _save(doc, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(path))
    return path


def _r2000_with_notes_text():
    doc = ezdxf.new("R2000")
    doc.styles.add("NOTES", font="arial.ttf")
    doc.modelspace().add_text("cut depth 6mm", dxfattribs={
        "style": "NOTES", "insert": (5.0, 5.0), "height": 2.5,
    })
    return doc


def test_text_style_font_survives_roundtrip(tmp_path):
    """The original loss: style NAME survived, font did not."""
    source = _save(_r2000_with_notes_text(), tmp_path / "src.dxf")
    out = tmp_path / "out.dxf"
    report = convert_file(source, out)
    saved = ezdxf.readfile(str(out))
    assert saved.dxfversion == "AC1009"
    assert saved.styles.get("NOTES").dxf.font.lower() == "arial.ttf"
    assert report["verification"]["style_attribute_drift"] == {}


def test_same_style_name_wrong_font_fails_verification(tmp_path):
    """Verifier must not treat NOTES/arial and NOTES/txt as the same resource."""
    source = _r2000_with_notes_text()
    lookalike = ezdxf.new("R12")
    lookalike.styles.add("NOTES", font="txt.shx")
    lookalike.modelspace().add_text("cut depth 6mm", dxfattribs={
        "style": "NOTES", "insert": (5.0, 5.0), "height": 2.5,
    })
    saved_path = _save(lookalike, tmp_path / "wrong_font.dxf")

    with pytest.raises(FidelityError) as exc:
        verify_saved_file(saved_path, {}, source_doc=source)
    message = str(exc.value)
    assert "NOTES" in message
    assert "style attributes changed" in message


def test_insert_with_block_definition_is_refused():
    """INSERT is R12-native, but block records are not copied. Refuse, don't 200."""
    doc = ezdxf.new("R2000")
    block = doc.blocks.new("BODY_BLOCK")
    block.add_line((0, 0), (10, 0))
    doc.modelspace().add_blockref("BODY_BLOCK", insert=(0, 0))

    with pytest.raises(UnconvertibleEntity) as exc:
        convert_document(doc, "R12")
    assert "INSERT" in str(exc.value)


def test_paperspace_geometry_is_refused():
    """Modelspace-only conversion must not report success after dropping layouts."""
    doc = ezdxf.new("R2000")
    doc.modelspace().add_line((0, 0), (10, 0))
    doc.paperspace().add_line((0, 0), (5, 5))

    with pytest.raises(UnconvertibleEntity) as exc:
        convert_document(doc, "R12")
    message = str(exc.value).lower()
    assert "paper" in message or "modelspace-only" in message


def test_3d_polyline_is_refused():
    doc = ezdxf.new("R2000")
    doc.modelspace().add_polyline3d([(0, 0, 0), (1, 1, 1), (2, 0, 0)])

    with pytest.raises(UnconvertibleEntity) as exc:
        convert_document(doc, "R12")
    assert "3D POLYLINE" in str(exc.value)


@pytest.mark.parametrize("factory", [
    lambda msp: msp.add_solid([(0, 0), (1, 0), (1, 1), (0, 1)]),
    lambda msp: msp.add_3dface([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
    lambda msp: msp.add_attdef(tag="PART", text="SN", insert=(0, 0), height=2.5),
])
def test_unverified_native_types_are_refused(factory):
    """R12 can store these; we do not, because there is no semantic comparator."""
    doc = ezdxf.new("R2000")
    factory(doc.modelspace())
    with pytest.raises(UnconvertibleEntity):
        convert_document(doc, "R12")


def test_attdef_is_named_in_the_refusal():
    """ATTDEF was declared native but compared as (type, layer) only."""
    doc = ezdxf.new("R2000")
    doc.modelspace().add_attdef(tag="PART", text="SN", insert=(0, 0), height=2.5)
    with pytest.raises(UnconvertibleEntity) as exc:
        convert_document(doc, "R12")
    assert "ATTDEF" in str(exc.value)


def test_custom_linetype_is_carried_not_refused():
    """Supersedes `test_custom_linetype_is_refused` (LTB-R12-002 D5.2).

    The original concern stands and is unchanged: *"linetype names without copied
    table definitions would pass a type+layer check."* What changed is the answer to
    it. Refusing the whole file was too blunt -- R12 cannot store a modern dash
    pattern, but it stores the NAME, and a reference that resolves keeps the drawing
    readable. Refusing over a dash pattern reports a format limit as a defect.

    The concern is now enforced where it belongs, on the SAVED file: an entity
    pointing at a linetype the file never defines fails verification. See
    `test_d5_the_verifier_took_over_the_refusals_job` in
    tests/test_r12_convert_divergences.py.
    """
    doc = ezdxf.new("R2000")
    if "DASHED" not in doc.linetypes:
        doc.linetypes.add("DASHED", pattern=[0.5, 0.25, -0.25])
    doc.modelspace().add_line((0, 0), (10, 0), dxfattribs={"linetype": "DASHED"})

    target, report = convert_document(doc, "R12")

    assert "DASHED" in target.linetypes
    assert report["linetypes"]["DASHED"]["status"] in {"created", "updated"}


def test_verified_line_circle_arc_point_roundtrip(tmp_path):
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    msp.add_line((0, 0, 1), (10, 0, 1))
    msp.add_circle((5, 5, 0), 2.5)
    msp.add_arc((0, 0), 4.0, 0.0, 90.0)
    msp.add_point((3, 4, 5))
    report = convert_file(_save(doc, tmp_path / "src.dxf"), tmp_path / "out.dxf")
    saved = ezdxf.readfile(str(tmp_path / "out.dxf"))
    kinds = {e.dxftype() for e in saved.modelspace()}
    assert kinds == {"LINE", "CIRCLE", "ARC", "POINT"}
    assert report["verification"]["missing_from_saved_file"] == []


def test_2d_polyline_vertex_z_is_part_of_the_record(tmp_path):
    """A 2D POLYLINE whose vertex Z changes must not compare equal."""
    source = ezdxf.new("R2000")
    source.modelspace().add_polyline2d([(0, 0), (10, 0), (10, 5)], close=True)
    lookalike = ezdxf.new("R12")
    mutated = lookalike.modelspace().add_polyline2d([(0, 0), (10, 0), (10, 5)], close=True)
    for vertex in mutated.vertices:
        vertex.dxf.location = (vertex.dxf.location.x, vertex.dxf.location.y, 7.0)
    saved_path = _save(lookalike, tmp_path / "z_mutated.dxf")

    with pytest.raises(FidelityError) as exc:
        verify_saved_file(saved_path, {}, source_doc=source)
    assert "missing" in str(exc.value).lower() or "polyline" in str(exc.value).lower()
