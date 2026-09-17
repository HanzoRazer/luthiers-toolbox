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

# Types we copy AND fully compare. R12 can store SHAPE/INSERT/SOLID/TRACE/3DFACE/
# DIMENSION/VIEWPORT/ATTDEF/ATTRIB, but type+layer is not a meaning check, block
# records are not copied, and ATTDEF was not even in the TEXT comparator. Those
# are refused until a dedicated comparator and resource copy exist.
R12_VERIFIED = frozenset({"LINE", "POINT", "CIRCLE", "ARC", "TEXT", "POLYLINE"})

# Conversions this module performs, as {source type: target type}.
CONVERSIONS = {"LWPOLYLINE": "POLYLINE"}

# Group-70 bits that mean this POLYLINE is not a verified 2D contour.
_POLYLINE_UNVERIFIED_FLAGS = 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x40

_MODELSPACE_NAMES = frozenset({"MODEL", "*MODEL_SPACE"})

# Every DXF document defines these; they are references, not resources to carry.
BUILTIN_LINETYPES = frozenset({"BYLAYER", "BYBLOCK", "CONTINUOUS"})

LAYER_ATTRIBUTES = ("color", "true_color", "linetype", "lineweight", "plot", "flags")

# R12 LAYER stores name/flags/colour/linetype. lineweight, true_color and plot
# arrived with R2000 -- reported as format-limited, not defects. Keyed by $ACADVER.
FORMAT_LIMITED_LAYER_ATTRIBUTES = {
    "AC1009": ("lineweight", "true_color", "plot"),
}
STYLE_ATTRIBUTES = ("font", "bigfont", "width", "oblique", "height", "flags",
                    "text_generation_flags", "last_height")
# last_height is a cache of the last height used, not a definition. Do not treat
# it as fidelity.
STYLE_COMPARE_ATTRIBUTES = ("font", "bigfont", "width", "oblique", "height", "flags",
                            "text_generation_flags")


class ConversionError(RuntimeError):
    """Named failure. The caller must not present a partial output as a fix."""

    exit_code = 3


class UnconvertibleEntity(ConversionError):
    """R12 cannot hold this entity and this module will not approximate it."""

    exit_code = 7


class OutputPathError(ConversionError):
    """The destination is the source. Converting in place destroys the only copy."""


class FidelityError(ConversionError):
    """The saved file does not contain what conversion predicted."""

    exit_code = 8


def _table_attributes(table, name: str, attributes) -> dict:
    if name not in table:
        return {}
    entry = table.get(name)
    return {a: getattr(entry.dxf, a) for a in attributes if entry.dxf.hasattr(a)}


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


def _entity_style_name(entity):
    """Style an entity uses, including the default a TEXT does not declare.

    After a write/read round trip a TEXT reports its style through the DXF default
    rather than through `hasattr("style")`. Collecting names with `hasattr` alone
    therefore missed `Standard` entirely, so a source that customised its default
    style never had it carried -- the other half of G4, alongside reserved entries
    being skipped.
    """
    if entity.dxftype() == "TEXT":
        return entity.dxf.style
    if entity.dxf.hasattr("style"):
        return entity.dxf.style
    return None


def _style_names(msp) -> set:
    """Style names actually referenced, defaults included."""
    return {name for name in (_entity_style_name(e) for e in msp) if name}


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


def _occupied_non_model_layouts(doc) -> dict:
    """Layouts other than modelspace that actually contain entities."""
    occupied = {}
    for name in doc.layout_names():
        if str(name).upper() in _MODELSPACE_NAMES:
            continue
        count = sum(1 for _ in doc.layout(name))
        if count:
            occupied[name] = count
    return occupied


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
            target.linetypes.add(name, pattern=pattern or [0.0], description=description)
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


# Coordinates are compared at a declared precision, not as raw floats: a value that
# survives a write/read round trip may differ in its last bits without meaning anything.
PRECISION = 6


def _r(value) -> float:
    return round(float(value), PRECISION)


def _vec3(value) -> tuple:
    return (_r(value.x), _r(value.y), _r(value.z))


def _extrusion(entity) -> tuple:
    if entity.dxf.hasattr("extrusion"):
        return _vec3(entity.dxf.extrusion)
    return (0.0, 0.0, 1.0)


def _entity_cam_attrs(entity) -> tuple:
    color = entity.dxf.color if entity.dxf.hasattr("color") else 256
    linetype = (entity.dxf.linetype if entity.dxf.hasattr("linetype") else "BYLAYER").upper()
    thickness = _r(entity.dxf.thickness) if entity.dxf.hasattr("thickness") else 0.0
    return (color, linetype, thickness)


def _polyline_record(entity) -> tuple:
    layer = entity.dxf.layer
    if entity.dxftype() == "LWPOLYLINE":
        points = [tuple(_r(v) for v in p) for p in entity.get_points(format="xyseb")]
        closed = bool(entity.closed)
        elevation = _r(entity.dxf.elevation) if entity.dxf.hasattr("elevation") else 0.0
        # An LWPOLYLINE's vertices carry no z of their own: for a 2D polyline the z
        # lives in `elevation`, which is compared separately. Synthesising it into
        # vertex_z made this branch disagree with the POLYLINE branch by construction
        # -- a converted 2D POLYLINE stores z=0 per vertex -- so every elevated contour
        # failed verification even once it stopped crashing (G1).
        vertex_z = tuple(0.0 for _ in points)
        unverified_flags = 0
    else:
        points = [(_r(v.dxf.location.x), _r(v.dxf.location.y), _r(v.dxf.start_width),
                   _r(v.dxf.end_width), _r(v.dxf.bulge)) for v in entity.vertices]
        closed = bool(entity.is_closed)
        elevation = _r(entity.dxf.elevation.z) if entity.dxf.hasattr("elevation") else 0.0
        vertex_z = tuple(_r(v.dxf.location.z) for v in entity.vertices)
        flags = int(entity.dxf.flags) if entity.dxf.hasattr("flags") else 0
        unverified_flags = flags & _POLYLINE_UNVERIFIED_FLAGS
    return ("polyline", layer, closed, elevation, tuple(points), vertex_z, unverified_flags,
            _entity_cam_attrs(entity), _extrusion(entity))


def _line_record(entity) -> tuple:
    return ("line", entity.dxf.layer, _vec3(entity.dxf.start), _vec3(entity.dxf.end),
            _entity_cam_attrs(entity), _extrusion(entity))


def _circle_record(entity) -> tuple:
    return ("circle", entity.dxf.layer, _vec3(entity.dxf.center), _r(entity.dxf.radius),
            _entity_cam_attrs(entity), _extrusion(entity))


def _arc_record(entity) -> tuple:
    return ("arc", entity.dxf.layer, _vec3(entity.dxf.center), _r(entity.dxf.radius),
            _r(entity.dxf.start_angle), _r(entity.dxf.end_angle),
            _entity_cam_attrs(entity), _extrusion(entity))


def _text_record(entity) -> tuple:
    width = _r(entity.dxf.width) if entity.dxf.hasattr("width") else 1.0
    oblique = _r(entity.dxf.oblique) if entity.dxf.hasattr("oblique") else 0.0
    gen = int(entity.dxf.text_generation_flag) if entity.dxf.hasattr("text_generation_flag") else 0
    halign = int(entity.dxf.halign) if entity.dxf.hasattr("halign") else 0
    valign = int(entity.dxf.valign) if entity.dxf.hasattr("valign") else 0
    return ("text", entity.dxf.layer, entity.dxf.style, entity.dxf.text,
            _vec3(entity.dxf.insert), _r(entity.dxf.height), _r(entity.dxf.rotation),
            width, oblique, gen, halign, valign,
            _entity_cam_attrs(entity), _extrusion(entity))


def _point_record(entity) -> tuple:
    return ("point", entity.dxf.layer, _vec3(entity.dxf.location),
            _entity_cam_attrs(entity), _extrusion(entity))


_SEMANTIC_BUILDERS = {
    "LWPOLYLINE": _polyline_record,
    "POLYLINE": _polyline_record,
    "LINE": _line_record,
    "CIRCLE": _circle_record,
    "ARC": _arc_record,
    "TEXT": _text_record,
    "POINT": _point_record,
}


def semantic_record(entity) -> tuple:
    """What an entity MEANS, independent of how the format stores it.

    LWPOLYLINE and POLYLINE both reduce to ("polyline", ...), so converting between
    the two is not a difference. An entity count would call it one; that is why the
    gate below is this and not a count.

    Types without a builder raise: the generic (type, layer) fallback is how INSERT,
    ATTDEF, SOLID and DIMENSION could change geometry and still compare equal.
    """
    builder = _SEMANTIC_BUILDERS.get(entity.dxftype())
    if builder is None:
        raise FidelityError(
            f"no semantic comparator for {entity.dxftype()}; type+layer is not sufficient"
        )
    return builder(entity)


def _semantics(msp) -> Counter:
    return Counter(semantic_record(e) for e in msp)


def _undefined_references(saved_msp, saved) -> tuple:
    """Entities pointing at a layer, style or linetype the file never defines.

    Linetypes joined this check when the blanket refusal of custom linetypes was
    replaced by carrying the name (D5.2). The refusal used to guarantee no saved file
    could hold a dangling linetype reference; this is what guarantees it now.
    """
    layers = sorted({e.dxf.layer for e in saved_msp}
                    - {layer.dxf.name for layer in saved.layers})
    styles = sorted(_style_names(saved_msp)
                    - {style.dxf.name for style in saved.styles})
    referenced = {str(e.dxf.linetype).upper() for e in saved_msp
                  if e.dxf.hasattr("linetype")}
    for layer in saved.layers:
        if layer.dxf.hasattr("linetype"):
            referenced.add(str(layer.dxf.linetype).upper())
    linetypes = sorted((referenced - BUILTIN_LINETYPES)
                       - {lt.dxf.name.upper() for lt in saved.linetypes})
    return layers, styles, linetypes


def _compare_semantics(source_msp, saved_msp) -> tuple:
    """What the source means that the saved file does not, and the reverse."""
    source_semantics = _semantics(source_msp)
    saved_semantics = _semantics(saved_msp)
    missing = sorted(str(k) for k in (source_semantics - saved_semantics))
    unexpected = sorted(str(k) for k in (saved_semantics - source_semantics))
    return missing, unexpected


def _compare_layer_tables(source_doc, saved, saved_msp) -> tuple:
    """Split layer-table differences into defects and losses the format forces."""
    cannot_store = FORMAT_LIMITED_LAYER_ATTRIBUTES.get(saved.dxfversion, ())
    drift, format_limited = {}, {}
    for name in {e.dxf.layer for e in saved_msp}:
        before = _table_attributes(source_doc.layers, name, LAYER_ATTRIBUTES)
        after = _table_attributes(saved.layers, name, LAYER_ATTRIBUTES)
        for attr, value in before.items():
            if after.get(attr) == value:
                continue
            if attr in cannot_store:
                format_limited.setdefault(name, {})[attr] = value
            else:
                drift.setdefault(name, {})[attr] = {"source": value, "saved": after.get(attr)}
    return drift, format_limited


def _style_attr_equal(attr: str, before, after) -> bool:
    if attr in ("font", "bigfont"):
        return str(before or "").lower() == str(after or "").lower()
    if attr in ("width", "oblique", "height"):
        return _r(before) == _r(after if after is not None else 0)
    return before == after


def _compare_style_tables(source_doc, saved, source_msp, saved_msp) -> dict:
    """Style NAME equality is not preservation -- NOTES/arial vs NOTES/txt is a loss."""
    used = _style_names(source_msp)
    used |= _style_names(saved_msp)
    drift = {}
    for name in sorted(used):
        before = _table_attributes(source_doc.styles, name, STYLE_COMPARE_ATTRIBUTES)
        after = _table_attributes(saved.styles, name, STYLE_COMPARE_ATTRIBUTES)
        changed = {}
        for attr, value in before.items():
            saved_val = after.get(attr)
            if _style_attr_equal(attr, value, saved_val):
                continue
            changed[attr] = {"source": value, "saved": saved_val}
        if changed:
            drift[name] = changed
    return drift


_FIDELITY_KEYS = (
    "missing_from_saved_file", "unexpected_in_saved_file",
    "layer_attribute_drift", "style_attribute_drift",
    "entities_referencing_undefined_layers", "entities_referencing_undefined_styles",
    "entities_referencing_undefined_linetypes",
    "discarded_non_modelspace_layouts",
)


def _compare_source_to_saved(source_doc, saved, saved_msp) -> dict:
    discarded = dict(_occupied_non_model_layouts(source_doc))
    discarded.update({
        f"saved:{name}": n for name, n in _occupied_non_model_layouts(saved).items()
    })
    missing, unexpected = _compare_semantics(source_doc.modelspace(), saved_msp)
    layer_drift, format_limited = _compare_layer_tables(source_doc, saved, saved_msp)
    return {
        "missing_from_saved_file": missing,
        "unexpected_in_saved_file": unexpected,
        "layer_attribute_drift": layer_drift,
        "style_attribute_drift": _compare_style_tables(
            source_doc, saved, source_doc.modelspace(), saved_msp),
        "format_limited_layer_attributes": format_limited,
        "discarded_non_modelspace_layouts": discarded,
    }


def verify_saved_file(path: Path, report: dict, source_doc=None) -> dict:
    """Reopen the written file and compare what it MEANS with the source.

    In-memory state is not evidence: the loss this module repairs happened at write
    time. Counts are reported and are never the pass condition.
    """
    saved = ezdxf.readfile(str(path))
    saved_msp = saved.modelspace()
    undefined_layers, undefined_styles, undefined_linetypes = _undefined_references(
        saved_msp, saved)
    compared = {
        "missing_from_saved_file": [], "unexpected_in_saved_file": [],
        "layer_attribute_drift": {}, "style_attribute_drift": {},
        "format_limited_layer_attributes": {}, "discarded_non_modelspace_layouts": {},
    }
    if source_doc is not None:
        compared = _compare_source_to_saved(source_doc, saved, saved_msp)
    verification = {
        "gate": "semantic comparison against the source document; entity counts are "
                "reported but are not the pass condition",
        "precision": PRECISION,
        "saved_version": saved.dxfversion,
        "saved_entity_types": dict(sorted(Counter(e.dxftype() for e in saved_msp).items())),
        "semantics_compared": source_doc is not None,
        "entities_referencing_undefined_layers": undefined_layers,
        "entities_referencing_undefined_styles": undefined_styles,
        "entities_referencing_undefined_linetypes": undefined_linetypes,
        **compared,
    }
    if any(verification[key] for key in _FIDELITY_KEYS):
        raise FidelityError(
            f"""the saved file does not carry the source's meaning:
  missing: {verification['missing_from_saved_file'] or 'none'}
  unexpected: {verification['unexpected_in_saved_file'] or 'none'}
  layer attributes changed: {verification['layer_attribute_drift'] or 'none'}
  style attributes changed: {verification['style_attribute_drift'] or 'none'}
  undefined layers referenced: {verification['entities_referencing_undefined_layers'] or 'none'}
  undefined styles referenced: {verification['entities_referencing_undefined_styles'] or 'none'}
  undefined linetypes referenced: {verification['entities_referencing_undefined_linetypes'] or 'none'}
  non-modelspace layouts: {verification['discarded_non_modelspace_layouts'] or 'none'}"""
        )
    return verification


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
