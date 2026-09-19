"""
r12_verify.py -- the saved-file gate for r12_convert.

Split out of r12_convert.py (LTB-R12-002) to keep both modules under the 500-line
file-size ratchet. Behaviour is unchanged: this is the verification half -- reopen
the written file and compare what it MEANS with the source -- plus the table and
style helpers both halves share. r12_convert re-exports every public name here, so
`from app.cam.r12_convert import verify_saved_file` and friends keep working.

Dependency direction is one-way: r12_convert imports this module, never the reverse.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import ezdxf


class ConversionError(RuntimeError):
    """Named failure. The caller must not present a partial output as a fix."""

    exit_code = 3


class FidelityError(ConversionError):
    """The saved file does not contain what conversion predicted."""

    exit_code = 8


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
# last_height is a cache of the last height used, not a definition. Do not treat
# it as fidelity.
STYLE_COMPARE_ATTRIBUTES = ("font", "bigfont", "width", "oblique", "height", "flags",
                            "text_generation_flags")


def _table_attributes(table, name: str, attributes) -> dict:
    if name not in table:
        return {}
    entry = table.get(name)
    return {a: getattr(entry.dxf, a) for a in attributes if entry.dxf.hasattr(a)}


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
