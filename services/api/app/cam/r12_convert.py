"""
r12_convert.py -- convert a DXF document to R12 without losing geometry silently.

Replaces the `add_foreign_entity` loop that `/auto_fix` `convert_to_r12` used.
`add_foreign_entity` accepts an LWPOLYLINE into an R12 document so in-memory
counts look right, then the writer drops it: consolidator output (R2000, 25
LWPOLYLINE) came back EMPTY while the endpoint reported the fix applied. Layer
definitions and text styles failed the same way -- an entity kept the NAME while
the table defined only `0`/`Standard` (same string, different font).

This module converts LWPOLYLINE to POLYLINE explicitly, carries layer and style
tables first, reopens the SAVED file and compares meaning (including style
definitions, not just names), and fails closed on unverified natives, INSERT/
blocks, 3D/mesh polylines, and paper-space geometry. Format-forced layer losses
(R12 has no lineweight) are reported, not hidden.

Transported from vectorizer-sandbox PR #101; this repository owns the endpoint.
The sandbox's TEST suite was never transported -- LTB's tests are its own, written
for PR #381. See docs/handoffs/LTB_R12_002_DIVERGENCE_RECORD.md for the measured
behavioural delta and the one divergence still open.

The saved-file gate (semantic records, table comparison, `verify_saved_file`) lives
in r12_verify.py; its public names are re-exported here.

`ezdxf` validated at **1.4.2** (local, Python 3.13) and **1.4.3** (sandbox). Recorded,
deliberately NOT pinned: `requirements.txt` declares `ezdxf>=1.1.0` in two services and
pinning one splits them. A recorded version still makes a version change diagnosable.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf.lldxf.const import DXFAttributeError, DXFValueError

# Documents go through dxf_compat -- scripts/check_dxf_compat.py flags ezdxf.new
# even in comments. The sandbox copy of this module has no app package to import.
from app.util.dxf_compat import create_document

from app.cam.r12_verify import (  # noqa: F401 -- re-exported, see __all__
    BUILTIN_LINETYPES,
    FORMAT_LIMITED_LAYER_ATTRIBUTES,
    LAYER_ATTRIBUTES,
    PRECISION,
    STYLE_COMPARE_ATTRIBUTES,
    _POLYLINE_UNVERIFIED_FLAGS,
    ConversionError,
    FidelityError,
    _occupied_non_model_layouts,
    _style_names,
    _table_attributes,
    semantic_record,
    verify_saved_file,
)

__all__ = [
    "BUILTIN_LINETYPES", "CONVERSIONS", "CONVERTERS", "ConversionError",
    "FORMAT_LIMITED_LAYER_ATTRIBUTES", "FidelityError", "LAYER_ATTRIBUTES",
    "OutputPathError", "PRECISION", "R12_VERIFIED", "STYLE_ATTRIBUTES",
    "STYLE_COMPARE_ATTRIBUTES", "UnconvertibleEntity", "convert_document",
    "convert_file", "publish_converted_document", "same_path", "semantic_record",
    "verify_saved_file",
]

# Types we copy AND fully compare. R12 can store SHAPE/INSERT/SOLID/TRACE/3DFACE/
# DIMENSION/VIEWPORT/ATTDEF/ATTRIB, but type+layer is not a meaning check, block
# records are not copied, and ATTDEF was not even in the TEXT comparator. Those
# are refused until a dedicated comparator and resource copy exist.
R12_VERIFIED = frozenset({"LINE", "POINT", "CIRCLE", "ARC", "TEXT", "POLYLINE"})

# Conversions this module performs, as {source type: target type}.
CONVERSIONS = {"LWPOLYLINE": "POLYLINE"}

# Style attributes carried into the target (last_height included; it is not compared).
STYLE_ATTRIBUTES = ("font", "bigfont", "width", "oblique", "height", "flags",
                    "text_generation_flags", "last_height")


class UnconvertibleEntity(ConversionError):
    """R12 cannot hold this entity and this module will not approximate it."""

    exit_code = 7


class OutputPathError(ConversionError):
    """The destination is the source. Converting in place destroys the only copy."""


# Errors a table entry can legitimately raise when a value is not storable at the
# target version. Anything else is a bug here and propagates rather than being
# recorded as a routine failure.
_TABLE_SET_ERRORS = (AttributeError, TypeError, ValueError, DXFAttributeError, DXFValueError)


def _apply_table_attributes(entry, attributes) -> tuple:
    """Set attributes on a table entry. Record failures; unexpected errors propagate."""
    applied, failed = {}, {}
    for attr, value in attributes.items():
        try:
            setattr(entry.dxf, attr, value)
        except _TABLE_SET_ERRORS as exc:
            failed[attr] = {"source": value, "error": f"{type(exc).__name__}: {exc}"}
            continue
        applied[attr] = value
    return applied, failed


def _carry(names, source_attrs, target_table, create) -> dict:
    """Create or update table entries, including reserved names already in the target.

    Every document defines layer `0` and style `Standard`, so skipping a name the
    target already has meant a source that customised either one silently converted
    with the target's defaults (G2). Updating is what "preserve the table" has to mean;
    the distinction between `created` and `updated` stays in the report.
    """
    carried = {}
    for name in sorted(names):
        attributes = source_attrs(name)
        if name in target_table:
            entry = target_table.get(name)
            status = "updated"
        else:
            entry = create(name, attributes)
            status = "created"
        applied, failed = _apply_table_attributes(entry, attributes)
        record = {"status": status, "attributes": applied}
        if failed:
            record["failed_attributes"] = failed
        carried[name] = record
    return carried


def _as_elevation_vec(value) -> tuple:
    """POLYLINE.elevation is a point; LWPOLYLINE.elevation is a float z.

    Passing the float straight through to add_polyline2d raises TypeError -- the Vec3
    constructor calls len() on it -- which aborted conversion of any elevated contour
    and reached the caller as an unhandled 500 (G1). ezdxf hands this attribute back as
    a Vec3, a float, or a sequence depending on the entity class and DXF version, so
    the variance is flattened here, once, rather than per call site.
    """
    if hasattr(value, "z"):
        return (0.0, 0.0, float(value.z))
    if isinstance(value, (int, float)):
        return (0.0, 0.0, float(value))
    coords = list(value)
    if len(coords) == 1:
        return (0.0, 0.0, float(coords[0]))
    while len(coords) < 3:
        coords.append(0.0)
    return (float(coords[0]), float(coords[1]), float(coords[2]))


def _lwpolyline_to_polyline(entity, target_msp):
    """R12 POLYLINE with points, bulges, widths, closure and elevation (`xyseb`)."""
    points = list(entity.get_points(format="xyseb"))
    attribs = {"layer": entity.dxf.layer}
    for attr in ("linetype", "color", "true_color", "extrusion", "thickness"):
        if entity.dxf.hasattr(attr):
            attribs[attr] = getattr(entity.dxf, attr)
    if entity.dxf.hasattr("elevation"):
        attribs["elevation"] = _as_elevation_vec(entity.dxf.elevation)
    polyline = target_msp.add_polyline2d(points, format="xyseb", dxfattribs=attribs)
    if entity.closed:
        polyline.close(True)
    return polyline


# Dispatch for CONVERSIONS, defined once the converters exist. Keeping the two
# tables adjacent is how a future entity type gets added without a silent gap:
# a key in CONVERSIONS without a converter here raises KeyError rather than
# reporting a conversion that never happened.
CONVERTERS = {"LWPOLYLINE": _lwpolyline_to_polyline}
assert set(CONVERTERS) == set(CONVERSIONS), "every declared conversion needs a converter"


def _unverified_polyline_reason(entity) -> str | None:
    """Return a reason if this POLYLINE is not a verified 2D contour."""
    if entity.dxftype() != "POLYLINE":
        return None
    if getattr(entity, "is_3d_polyline", False):
        return "3D POLYLINE"
    if getattr(entity, "is_polygon_mesh", False):
        return "polygon-mesh POLYLINE"
    if getattr(entity, "is_polyface_mesh", False):
        return "polyface-mesh POLYLINE"
    flags = int(entity.dxf.flags) if entity.dxf.hasattr("flags") else 0
    if flags & 0x02:
        return "curve-fit POLYLINE"
    if flags & 0x04:
        return "spline-fit POLYLINE"
    if flags & _POLYLINE_UNVERIFIED_FLAGS:
        return "non-2D POLYLINE"
    return None


def _used_linetypes(doc, source_msp, used_layers) -> set[str]:
    """Custom linetype names referenced by an entity or by a layer definition."""
    names = {str(e.dxf.linetype).upper() for e in source_msp
             if e.dxf.hasattr("linetype")}
    for layer_name in used_layers:
        attrs = _table_attributes(doc.layers, layer_name, LAYER_ATTRIBUTES)
        if "linetype" in attrs:
            names.add(str(attrs["linetype"]).upper())
    return (names - BUILTIN_LINETYPES) - {""}


def _ltype_add_pattern(simplified) -> list:
    """`simplified_line_pattern()` output in the form `linetypes.add` expects.

    The two use different encodings: the simplified pattern is plain lengths
    `[dash, gap, dash, ...]`; `add` takes `[total_length, dash, -gap, ...]`. Passing
    one as the other read the first dash as the total -- a 7-on/3-off pattern saved
    as a 7-unit cycle holding a single 3-unit dash.
    """
    if not simplified:
        return [0.0]
    elements = [v if i % 2 == 0 else -v for i, v in enumerate(simplified)]
    return [float(sum(simplified)), *elements]


def _carry_linetypes(doc, target, names) -> dict:
    """Ensure referenced custom linetype names exist in the target.

    R12 rarely holds a modern linetype's full definition, but it holds the NAME, and
    a reference that resolves is what keeps the drawing readable. The pattern is
    carried when ezdxf can simplify it and reported when it cannot; losing the dash
    pattern is a format limit, not a converter defect.

    This replaces a blanket refusal. Because it does, `_undefined_references` now
    checks linetypes as well -- a carry that fails silently would otherwise produce
    exactly the dangling reference the refusal used to prevent.
    """
    carried = {}
    for name in sorted(names):
        if name not in doc.linetypes:
            carried[name] = {"status": "missing_in_source"}
            continue
        source_lt = doc.linetypes.get(name)
        description = ""
        if source_lt.dxf.hasattr("description"):
            description = source_lt.dxf.description or ""
        try:
            pattern = tuple(source_lt.simplified_line_pattern())
        except (TypeError, ValueError, AttributeError):
            pattern = ()
        if name in target.linetypes:
            carried[name] = {"status": "updated", "pattern": list(pattern)}
            continue
        try:
            target.linetypes.add(name, pattern=_ltype_add_pattern(pattern),
                                 description=description)
            carried[name] = {"status": "created", "pattern": list(pattern)}
        except _TABLE_SET_ERRORS as exc:
            carried[name] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    return carried


def _copy_modelspace_entities(source_msp, target_msp):
    """Copy verified modelspace entities. Collect unverified types rather than dropping them."""
    source_types, expected_types, converted = Counter(), Counter(), Counter()
    unconvertible = []
    for entity in source_msp:
        kind = entity.dxftype()
        source_types[kind] += 1
        reason = _unverified_polyline_reason(entity)
        if reason:
            unconvertible.append(reason)
            continue
        if kind in CONVERSIONS:
            CONVERTERS[kind](entity, target_msp)
            converted[f"{kind}->{CONVERSIONS[kind]}"] += 1
            expected_types[CONVERSIONS[kind]] += 1
            continue
        if kind not in R12_VERIFIED:
            unconvertible.append(kind)
            continue
        target_msp.add_foreign_entity(entity, copy=True)
        expected_types[kind] += 1
    return source_types, expected_types, converted, unconvertible


def convert_document(doc, target_version: str = "R12"):
    """Return (converted document, report). Raises rather than losing an entity."""
    occupied = _occupied_non_model_layouts(doc)
    if occupied:
        raise UnconvertibleEntity(
            f"{target_version} conversion is modelspace-only; refusing rather than "
            f"discarding paper-space geometry: {occupied}"
        )

    target = create_document(version=target_version)
    source_msp = doc.modelspace()
    target_msp = target.modelspace()

    used_layers = {e.dxf.layer for e in source_msp}
    used_styles = _style_names(source_msp)
    layers = _carry(
        used_layers,
        lambda n: _table_attributes(doc.layers, n, LAYER_ATTRIBUTES),
        target.layers,
        lambda name, attrs: target.layers.add(name),
    )
    styles = _carry(
        used_styles,
        lambda n: _table_attributes(doc.styles, n, STYLE_ATTRIBUTES),
        target.styles,
        lambda name, attrs: target.styles.add(name, font=attrs.get("font", "txt")),
    )

    linetypes = _carry_linetypes(
        doc, target, _used_linetypes(doc, source_msp, used_layers))

    source_types, expected_types, converted, unconvertible = _copy_modelspace_entities(
        source_msp, target_msp)

    if unconvertible:
        raise UnconvertibleEntity(
            f"{target_version} conversion refused rather than dropping unverified "
            f"or unsupported content: {sorted(set(unconvertible))}\n"
            f"  affected entities: {len(unconvertible)}\n"
            "Converting them is a modelling decision with its own losses (a SPLINE "
            "becomes an approximation at some tolerance), not a format fix. Refused "
            "rather than dropped: the earlier behaviour wrote a valid-looking file "
            "with the geometry missing."
        )

    return target, {
        "target_version": target_version,
        "conversion_boundary": "modelspace-only; unverified R12 types are refused",
        "source_entity_types": dict(sorted(source_types.items())),
        "expected_entity_types": dict(sorted(expected_types.items())),
        "conversions": dict(sorted(converted.items())),
        "layers": layers,
        "styles": styles,
        "linetypes": linetypes,
    }


def publish_converted_document(target, report, out_path, source_doc, encoding=None) -> dict:
    """Write a converted document, verify the bytes, then publish. Fails closed.

    The destination is replaced only after verification succeeds (G3): the previous
    order wrote `out_path` and verified afterwards, so a failed verification left the
    caller's existing file already overwritten by output just judged unfit. The
    temporary file is removed on either outcome -- publishing renames it away, and a
    failure unlinks it -- so no `.tmp` is left behind.

    Takes a document rather than a path because the endpoint applies its other fixes
    (close_open_polylines, units) to the document in memory. Re-reading the source
    from disk here would silently discard them.

    `encoding` is forwarded to ezdxf's `saveas`. Measured on this base: for a target
    built by `create_document("R12")` the document's own `output_encoding` is already
    cp1252 (from $DWGCODEPAGE: ANSI_1252), so passing "cp1252" changes no byte other
    than the writer's timestamp. It is kept explicit because the endpoint's contract
    said cp1252, not because it alters the output.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = out_path.with_suffix(out_path.suffix + ".tmp")
    try:
        if encoding is None:
            target.saveas(str(temporary_path))
        else:
            target.saveas(str(temporary_path), encoding=encoding)
        report["source_version"] = source_doc.dxfversion
        # The source document is passed in so the check is source-vs-saved meaning, not
        # saved-vs-its-own-prediction. A converter that mispredicts would otherwise
        # agree with itself.
        report["verification"] = verify_saved_file(
            temporary_path, report, source_doc=source_doc
        )
        temporary_path.replace(out_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return report


def same_path(a: Path, b: Path) -> bool:
    """Do two paths name the same file? Resolves links, relative forms and case."""
    try:
        if a.exists() and b.exists():
            return a.samefile(b)
    except OSError:
        pass
    return a.resolve(strict=False) == b.resolve(strict=False)


def convert_file(source_path: Path, out_path: Path, target_version: str = "R12",
                 encoding: str | None = None) -> dict:
    """Convert a DXF file, write it, and verify the written bytes. Fails closed."""
    source_path, out_path = Path(source_path), Path(out_path)
    if not source_path.is_file():
        raise ConversionError(f"input is not a file: {source_path}")
    if same_path(source_path, out_path):
        raise OutputPathError(
            f"output path is the input: {out_path}\n"
            "Converting a file onto itself destroys the only copy of the source: an "
            "R2000 original is replaced by its R12 reduction, so the conversion can "
            "no longer be checked, repeated or undone. Write a new file."
        )
    doc = ezdxf.readfile(str(source_path))
    target, report = convert_document(doc, target_version)
    return publish_converted_document(target, report, out_path, doc, encoding=encoding)
