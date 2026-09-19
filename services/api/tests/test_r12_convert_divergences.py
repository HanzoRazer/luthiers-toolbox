"""
LTB-R12-002 D5 — the two divergences from the sandbox repair source.

**These land RED.** Both are reproduced against this branch before either is fixed,
the same discipline the four gap reproductions follow.

  D5.1  `convert_file(p, p)` converts a file onto itself, destroying the source
  D5.2  a custom linetype is REFUSED (422) where the sandbox carries the name

D5.1 is not a transport. The sandbox's `r12_convert` has no same-path guard either;
the guard lives in its `merge.py`, and this order brings the idea across, not the code.

D5.2 is a **contract change**, which is why it travels with its own gate. Today the
refusal is the only thing guaranteeing that no entity in a saved file points at a
linetype the file never defines. Carrying the name instead removes that guarantee, so
the verifier has to take it over -- `test_d5_the_verifier_took_over_the_refusals_job`
is the test that says so. Without it this change trades a loud 422 for a silent
dangling reference.
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from app.cam.r12_convert import (  # noqa: E402
    BUILTIN_LINETYPES,
    FidelityError,
    OutputPathError,
    convert_document,
    convert_file,
    verify_saved_file,
)

ENDPOINT = "/api/dxf/preflight/auto_fix"


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


def _custom_linetype_doc():
    """An R2000 source using a linetype R12 cannot store the full pattern of."""
    doc = ezdxf.new("R2000")
    doc.linetypes.add(
        "CUTLINE", pattern=[1.0, 0.6, -0.2, 0.0, -0.2], description="Cut - dash dot")
    doc.layers.add("CUT")
    doc.modelspace().add_line(
        (0, 0), (100, 0), dxfattribs={"layer": "CUT", "linetype": "CUTLINE"})
    return doc


def _r2000_source(path: Path) -> Path:
    doc = ezdxf.new("R2000")
    doc.layers.add("BODY")
    doc.modelspace().add_lwpolyline(
        [(0, 0), (100, 0), (100, 60)], close=True, dxfattribs={"layer": "BODY"})
    doc.saveas(str(path))
    return path


# ------------------------------------------------------------------- D5.1


def test_d5_convert_file_refuses_to_write_over_its_own_source(tmp_path):
    """CONFIRMED: `convert_file(p, p)` replaces an R2000 source with its R12 reduction.

    Measured before the fix: a 16,982-byte AC1015 source came back as a 6,298-byte
    AC1009 file at the same path. The caller keeps no copy of what was converted, so
    the conversion cannot be checked, repeated or undone.

    Publishing atomically (G3) does not help here -- it makes the replacement cleaner,
    not less destructive. The only safe answer is to refuse.
    """
    source = _r2000_source(tmp_path / "inplace.dxf")
    before = source.read_bytes()

    with pytest.raises(OutputPathError):
        convert_file(source, source)

    assert source.read_bytes() == before, "the source was converted onto itself"
    assert ezdxf.readfile(str(source)).dxfversion == "AC1015"
    assert not list(tmp_path.glob("*.tmp"))


def test_d5_the_same_file_named_two_ways_is_still_the_same_file(tmp_path):
    """A guard comparing strings would pass this and still destroy the file."""
    source = _r2000_source(tmp_path / "inplace.dxf")
    before = source.read_bytes()

    disguised = tmp_path / "sub" / ".." / "inplace.dxf"
    with pytest.raises(OutputPathError):
        convert_file(source, disguised)

    assert source.read_bytes() == before


def test_d5_a_genuinely_different_destination_still_converts(tmp_path):
    """The refusal must not cost the ordinary case."""
    source = _r2000_source(tmp_path / "source.dxf")
    destination = tmp_path / "converted.dxf"

    convert_file(source, destination)

    assert ezdxf.readfile(str(destination)).dxfversion == "AC1009"
    assert ezdxf.readfile(str(source)).dxfversion == "AC1015", "source left alone"


# ------------------------------------------------------------------- D5.2


def test_d5_custom_linetype_is_carried_rather_than_refused():
    """CONFIRMED: this raised `UnconvertibleEntity: custom linetype CUTLINE`.

    R12 cannot hold a modern linetype's full definition, but it can hold the NAME, and
    a named reference that resolves is what keeps the drawing readable. Refusing a
    whole file over a dash pattern is D3's category -- a format limit reported as a
    converter defect.
    """
    doc = _custom_linetype_doc()

    target, report = convert_document(doc, "R12")

    assert "CUTLINE" in target.linetypes, "the linetype name was not carried"
    assert report["linetypes"]["CUTLINE"]["status"] in {"created", "updated"}
    line = [e for e in target.modelspace() if e.dxftype() == "LINE"][0]
    assert line.dxf.linetype == "CUTLINE"


def test_d5_builtin_linetypes_are_not_carried_as_custom():
    """CONTINUOUS/BYLAYER/BYBLOCK are every document's; carrying them is noise."""
    doc = ezdxf.new("R2000")
    doc.layers.add("PLAIN")
    doc.modelspace().add_line(
        (0, 0), (10, 10), dxfattribs={"layer": "PLAIN", "linetype": "CONTINUOUS"})

    _, report = convert_document(doc, "R12")

    assert report["linetypes"] == {}
    assert BUILTIN_LINETYPES == frozenset({"BYLAYER", "BYBLOCK", "CONTINUOUS"})


def test_d5_a_layers_own_linetype_is_carried_too(tmp_path):
    """A linetype can be referenced by the LAYER table, not just by an entity."""
    doc = ezdxf.new("R2000")
    doc.linetypes.add("HIDDEN2", pattern=[1.0, 0.5, -0.5], description="Hidden")
    # Keyword-only. `add("GUIDE", dxfattribs={"linetype": ...})` is accepted and
    # SILENTLY IGNORED -- the layer keeps Continuous and the test passes vacuously.
    doc.layers.add("GUIDE", linetype="HIDDEN2")
    assert doc.layers.get("GUIDE").dxf.linetype == "HIDDEN2", "fixture built wrong"
    doc.modelspace().add_line((0, 0), (10, 0), dxfattribs={"layer": "GUIDE"})

    target, report = convert_document(doc, "R12")

    assert "HIDDEN2" in report["linetypes"], report["linetypes"]
    assert "HIDDEN2" in target.linetypes


def test_d5_the_carried_linetype_survives_to_the_saved_file(tmp_path):
    """In-memory is not evidence: the whole module exists because writing loses things."""
    source = tmp_path / "custom.dxf"
    _custom_linetype_doc().saveas(str(source))
    destination = tmp_path / "out.dxf"

    convert_file(source, destination)

    saved = ezdxf.readfile(str(destination))
    assert "CUTLINE" in saved.linetypes
    assert [e for e in saved.modelspace()][0].dxf.linetype == "CUTLINE"


def test_d5_the_carried_linetype_keeps_its_dash_pattern(tmp_path):
    """The NAME surviving is not the pattern surviving.

    `simplified_line_pattern()` returns plain `[dash, gap, ...]` lengths, but
    `linetypes.add` expects `[total, dash, -gap, ...]`. Passing one as the other saved
    CUTLINE (a 1.0 cycle: 0.6 dash, 0.2 gap, dot, 0.2 gap) as a 0.6 cycle holding
    0.2 / 0.0 / 0.2 -- while the report still said the pattern was carried. Compared
    on the reopened file, because that is where the loss would be.
    """
    source_doc = _custom_linetype_doc()
    source = tmp_path / "custom.dxf"
    source_doc.saveas(str(source))
    destination = tmp_path / "out.dxf"

    convert_file(source, destination)

    expected = source_doc.linetypes.get("CUTLINE").simplified_line_pattern()
    saved = ezdxf.readfile(str(destination)).linetypes.get("CUTLINE")
    assert saved.simplified_line_pattern() == pytest.approx(expected)
    total_length = [tag.value for tag in saved.pattern_tags.tags if tag.code == 40]
    assert total_length == [pytest.approx(1.0)]


def test_d5_the_verifier_took_over_the_refusals_job(tmp_path):
    """The gate this contract change depends on.

    Refusing custom linetypes guaranteed no saved file could reference one it did not
    define. Carrying the name removes that guarantee, so verification must fail on a
    dangling reference -- otherwise the change swaps a loud 422 for a silent one.

    The saved file here is built by hand precisely because the converter should never
    produce it; the test asserts the NET catches it, not that the converter aims well.

    **Verified non-vacuous.** An earlier version of this test passed `source_doc` and
    matched on "linetype". It passed even with the linetype check removed: the failure
    came from ordinary semantic drift, and the word "linetype" appears in the error
    TEMPLATE whichever key trips. So no `source_doc` is passed here -- with semantic
    comparison switched off, an undefined reference is the ONLY thing that can raise --
    and the assertion names the offending linetype rather than the word.
    """
    def _saved_file(path, define_linetype):
        doc = ezdxf.new("R12")
        doc.layers.add("CUT")
        doc.linetypes.add("CUTLINE", pattern=[1.0, 0.6, -0.2, 0.0, -0.2])
        doc.modelspace().add_line(
            (0, 0), (100, 0), dxfattribs={"layer": "CUT", "linetype": "CUTLINE"})
        if not define_linetype:
            # Exactly what a silently failed carry leaves: the reference without the
            # definition. ezdxf writes the reference because it existed at build time.
            doc.linetypes.remove("CUTLINE")
        doc.saveas(str(path))
        return path

    intact = _saved_file(tmp_path / "intact.dxf", define_linetype=True)
    assert verify_saved_file(intact, {})["entities_referencing_undefined_linetypes"] == []

    dangling = _saved_file(tmp_path / "dangling.dxf", define_linetype=False)
    with pytest.raises(FidelityError, match="CUTLINE"):
        verify_saved_file(dangling, {})


def test_d5_the_endpoint_now_accepts_what_it_used_to_refuse(client):
    """The contract change, stated at the boundary a caller sees: 422 -> 200."""
    buffer = io.StringIO()
    _custom_linetype_doc().write(buffer)
    payload = base64.b64encode(buffer.getvalue().encode("cp1252")).decode("utf-8")

    response = client.post(ENDPOINT, json={
        "dxf_base64": payload, "filename": "custom_linetype.dxf",
        "fixes": ["convert_to_r12"],
    })

    assert response.status_code == 200, response.text[:300]
    report = response.json()["conversion_report"]
    assert report["linetypes"]["CUTLINE"]["status"] in {"created", "updated"}
