"""
DXF-TOPO-CRLF-001: TopologyValidator must not depend on DXF line endings.

TopologyValidator used to parse the decoded text through io.StringIO without
newline translation. ezdxf then read a CRLF file as an empty R12 document, so
the self-intersection check examined zero entities and reported nothing, and
the export gate (enforce_dxf_validation) let a self-intersecting CRLF outline
through while blocking the identical LF file. 73 of the 95 catalog DXFs are
stored CRLF.

Contract under test: identical geometry gives the identical entity population
and the identical topology verdict for LF, CRLF and CR line endings.
"""
import io

import ezdxf
import pytest
from fastapi import HTTPException

from app.cam.dxf_advanced_validation import (
    TopologyValidator,
    create_test_figure8_dxf,
    create_test_valid_dxf,
)
from app.cam.dxf_validation_gate import enforce_dxf_validation

pytestmark = pytest.mark.allow_missing_request_id

LINE_ENDINGS = {"LF": b"\n", "CRLF": b"\r\n", "CR": b"\r"}


def _with_line_ending(dxf_bytes: bytes, eol: bytes) -> bytes:
    lf = dxf_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return lf.replace(b"\n", eol)


def _lwpolyline_handles(dxf_bytes: bytes) -> list:
    """Reference population, parsed from an LF copy that ezdxf reads correctly."""
    text = _with_line_ending(dxf_bytes, b"\n").decode("cp1252")
    doc = ezdxf.read(io.StringIO(text))
    return sorted(e.dxf.handle for e in doc.modelspace() if e.dxftype() == "LWPOLYLINE")


def _topology(dxf_bytes: bytes):
    validator = TopologyValidator(dxf_bytes, "witness.dxf")
    handles = sorted(e.dxf.handle for e in validator.msp if e.dxftype() == "LWPOLYLINE")
    report = validator.check_self_intersections()
    issues = sorted((i.severity.value, i.message, i.entity_handle) for i in report.issues)
    return handles, report.entities_checked, report.self_intersections, issues


@pytest.fixture(params=["figure8", "valid"])
def witness(request) -> bytes:
    return create_test_figure8_dxf() if request.param == "figure8" else create_test_valid_dxf()


@pytest.mark.parametrize("eol_name", list(LINE_ENDINGS))
def test_validator_sees_every_lwpolyline_for_each_line_ending(witness, eol_name):
    dxf_bytes = _with_line_ending(witness, LINE_ENDINGS[eol_name])
    handles, checked, _, _ = _topology(dxf_bytes)
    expected = _lwpolyline_handles(witness)
    assert expected, "witness must contain LWPOLYLINE entities"
    assert handles == expected
    assert checked == len(expected)


def test_topology_result_identical_across_line_endings(witness):
    results = {name: _topology(_with_line_ending(witness, eol)) for name, eol in LINE_ENDINGS.items()}
    assert results["CRLF"] == results["LF"]
    assert results["CR"] == results["LF"]


@pytest.mark.parametrize("eol_name", list(LINE_ENDINGS))
def test_crlf_figure8_is_still_self_intersecting(eol_name):
    dxf_bytes = _with_line_ending(create_test_figure8_dxf(), LINE_ENDINGS[eol_name])
    _, checked, self_intersections, _ = _topology(dxf_bytes)
    assert checked >= 1
    assert self_intersections >= 1


@pytest.mark.parametrize("eol_name", list(LINE_ENDINGS))
def test_export_gate_blocks_figure8_for_each_line_ending(eol_name):
    dxf_bytes = _with_line_ending(create_test_figure8_dxf(), LINE_ENDINGS[eol_name])
    with pytest.raises(HTTPException) as excinfo:
        enforce_dxf_validation(dxf_bytes, f"figure8_{eol_name}.dxf")
    assert excinfo.value.status_code == 422


@pytest.mark.parametrize("eol_name", list(LINE_ENDINGS))
def test_export_gate_checks_valid_outline_for_each_line_ending(eol_name):
    dxf_bytes = _with_line_ending(create_test_valid_dxf(), LINE_ENDINGS[eol_name])
    _, topology = enforce_dxf_validation(dxf_bytes, f"valid_{eol_name}.dxf")
    assert topology is not None
    assert topology.entities_checked == len(_lwpolyline_handles(dxf_bytes))
    assert topology.entities_checked >= 1
