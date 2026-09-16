"""
r12_convert.py -- convert a DXF document to R12 without losing geometry silently.

Replaces the `add_foreign_entity` loop that the `/auto_fix` `convert_to_r12` fix used.
Built and verified in vectorizer-sandbox (`scripts/vectorize/r12_convert.py`,
`tests/skills/test_r12_convert.py`, PR #101) and transported here; this repository is
the authority for the endpoint.

## What went wrong without this

Measured on the live consolidator's own output -- 25 LWPOLYLINE contours on
BODY_OUTLINE, produced by `app.cam.layer_consolidator` from a raw 1,726-LINE
vectorizer dump:

    consolidator output   : R2000, {'LWPOLYLINE': 25}
    in memory after copy  : {'LWPOLYLINE': 25}   <- count looks right
    in the saved R12 file : {}                   <- EMPTY; what the caller received

`Layout.add_foreign_entity()` accepts an LWPOLYLINE into an R12 document, so any
in-memory count passes. The writer drops it on save, because R12 has no LWPOLYLINE.
Nothing raises and ezdxf's auditor reports the result clean. The same call drops
resources the target does not define: an entity keeps its layer NAME while the
output's LAYER table never defines that layer, and a TEXT's style falls back to
`Standard` -- same string, different font.

Consolidation emits exactly that shape: `app/cam/layer_consolidator.py` creates an
R2000 document because "LWPOLYLINE not supported in R12", one LWPOLYLINE per chain.

## What this does instead

1. **Converts explicitly.** LWPOLYLINE becomes an R12 POLYLINE, carrying vertex
   coordinates, bulges, widths, the closed flag and elevation.
2. **Carries resources first.** Layer and text-style table entries are created in
   the target, with their attributes, before any entity is copied.
3. **Verifies the SAVED file, semantically.** The output is written, reopened, and
   compared with the source's meaning. `LWPOLYLINE -> POLYLINE` is not a difference;
   a moved vertex, a lost bulge or a changed layer colour is. Entity counts are
   reported and are never the pass condition.
4. **Fails closed.** An entity R12 cannot hold raises `UnconvertibleEntity`; a caller
   must not present a partial file as a completed fix.

Losses the format itself forces -- R12's LAYER table has no lineweight -- are reported
under `format_limited_layer_attributes`, not hidden and not treated as defects.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import ezdxf

# Entity types DXF R12 can hold. Anything else must be converted or refused.
R12_NATIVE = frozenset({
    "LINE", "POINT", "CIRCLE", "ARC", "TEXT", "SHAPE", "INSERT", "ATTRIB",
    "ATTDEF", "POLYLINE", "VERTEX", "SEQEND", "SOLID", "TRACE", "3DFACE",
    "DIMENSION", "VIEWPORT", "BLOCK", "ENDBLK",
})

# Conversions this module performs, as {source type: target type}.
CONVERSIONS = {"LWPOLYLINE": "POLYLINE"}

LAYER_ATTRIBUTES = ("color", "true_color", "linetype", "lineweight", "plot", "flags")

# Layer properties a target version cannot store at all. R12's LAYER table carries
# name, flags, colour and linetype; lineweight, true colour and the plot flag arrived
# with R2000. Losing one of these is a property of the format, so it is REPORTED as a
# declared loss rather than treated as a defect -- and anything not on this list that
# changes is still a failure. Keyed by the written $ACADVER.
FORMAT_LIMITED_LAYER_ATTRIBUTES = {
    "AC1009": ("lineweight", "true_color", "plot"),
}
STYLE_ATTRIBUTES = ("font", "bigfont", "width", "oblique", "height", "flags",
                    "text_generation_flags", "last_height")


class ConversionError(RuntimeError):
    """Named failure. The caller must not present a partial output as a fix."""

    exit_code = 3


class UnconvertibleEntity(ConversionError):
    """R12 cannot hold this entity and this module will not approximate it."""

    exit_code = 7


class FidelityError(ConversionError):
    """The saved file does not contain what conversion predicted."""

    exit_code = 8


def _table_attributes(table, name: str, attributes) -> dict:
    if name not in table:
        return {}
    entry = table.get(name)
    return {a: getattr(entry.dxf, a) for a in attributes if entry.dxf.hasattr(a)}


def _carry(names, source_attrs, target_table, create) -> dict:
    """Create missing table entries in the target, carrying their attributes."""
    carried = {}
    for name in sorted(names):
        attributes = source_attrs(name)
        if name in target_table:
            carried[name] = {"status": "already_present"}
            continue
        entry = create(name, attributes)
        applied = {}
        for attr, value in attributes.items():
            try:
                setattr(entry.dxf, attr, value)
            except Exception:  # not supported at this DXF version; reported, not hidden
                continue
            applied[attr] = value
        carried[name] = {"status": "created", "attributes": applied}
    return carried


def _lwpolyline_to_polyline(entity, target_msp):
    """R12's POLYLINE, carrying points, bulges, widths, closure and elevation.

    `format="xyseb"` gives (x, y, start_width, end_width, bulge) per vertex, which is
    the whole of an LWPOLYLINE's per-vertex state.
    """
    points = list(entity.get_points(format="xyseb"))
    attribs = {"layer": entity.dxf.layer}
    for attr in ("linetype", "color", "true_color", "elevation", "extrusion", "thickness"):
        if entity.dxf.hasattr(attr):
            attribs[attr] = getattr(entity.dxf, attr)
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


def convert_document(doc, target_version: str = "R12"):
    """Return (converted document, report). Raises rather than losing an entity."""
    target = ezdxf.new(target_version)
    source_msp = doc.modelspace()
    target_msp = target.modelspace()

    used_layers = {e.dxf.layer for e in source_msp}
    used_styles = {e.dxf.style for e in source_msp if e.dxf.hasattr("style")}
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

    source_types, expected_types, converted = Counter(), Counter(), Counter()
    unconvertible = []
    for entity in source_msp:
        kind = entity.dxftype()
        source_types[kind] += 1
        if kind in CONVERSIONS:
            CONVERTERS[kind](entity, target_msp)
            converted[f"{kind}->{CONVERSIONS[kind]}"] += 1
            expected_types[CONVERSIONS[kind]] += 1
            continue
        if kind not in R12_NATIVE:
            unconvertible.append(kind)
            continue
        target_msp.add_foreign_entity(entity, copy=True)
        expected_types[kind] += 1

    if unconvertible:
        raise UnconvertibleEntity(
            f"{target_version} cannot hold these entity types and this converter will "
            f"not approximate them: {sorted(set(unconvertible))}\n"
            f"  affected entities: {len(unconvertible)}\n"
            "Converting them is a modelling decision with its own losses (a SPLINE "
            "becomes an approximation at some tolerance), not a format fix. Refused "
            "rather than dropped: the earlier behaviour wrote a valid-looking file "
            "with the geometry missing."
        )

    return target, {
        "target_version": target_version,
        "source_entity_types": dict(sorted(source_types.items())),
        "expected_entity_types": dict(sorted(expected_types.items())),
        "conversions": dict(sorted(converted.items())),
        "layers": layers,
        "styles": styles,
    }


# Coordinates are compared at a declared precision, not as raw floats: a value that
# survives a write/read round trip may differ in its last bits without meaning anything.
PRECISION = 6


def _r(value) -> float:
    return round(float(value), PRECISION)


def semantic_record(entity) -> tuple:
    """What an entity MEANS, independent of how the format stores it.

    LWPOLYLINE and POLYLINE both reduce to ("polyline", ...), so converting between
    the two is not a difference. An entity count would call it one; that is why the
    gate below is this and not a count.
    """
    kind = entity.dxftype()
    layer = entity.dxf.layer
    if kind in ("LWPOLYLINE", "POLYLINE"):
        if kind == "LWPOLYLINE":
            points = [tuple(_r(v) for v in p) for p in entity.get_points(format="xyseb")]
            closed = bool(entity.closed)
            elevation = _r(entity.dxf.elevation) if entity.dxf.hasattr("elevation") else 0.0
        else:
            points = [(_r(v.dxf.location.x), _r(v.dxf.location.y), _r(v.dxf.start_width),
                       _r(v.dxf.end_width), _r(v.dxf.bulge)) for v in entity.vertices]
            closed = bool(entity.is_closed)
            elevation = _r(entity.dxf.elevation.z) if entity.dxf.hasattr("elevation") else 0.0
        return ("polyline", layer, closed, elevation, tuple(points))
    if kind == "LINE":
        return ("line", layer, (_r(entity.dxf.start.x), _r(entity.dxf.start.y)),
                (_r(entity.dxf.end.x), _r(entity.dxf.end.y)))
    if kind == "CIRCLE":
        return ("circle", layer, (_r(entity.dxf.center.x), _r(entity.dxf.center.y)),
                _r(entity.dxf.radius))
    if kind == "ARC":
        return ("arc", layer, (_r(entity.dxf.center.x), _r(entity.dxf.center.y)),
                _r(entity.dxf.radius), _r(entity.dxf.start_angle), _r(entity.dxf.end_angle))
    if kind in ("TEXT", "ATTRIB"):
        return ("text", layer, entity.dxf.style, entity.dxf.text,
                (_r(entity.dxf.insert.x), _r(entity.dxf.insert.y)),
                _r(entity.dxf.height), _r(entity.dxf.rotation))
    if kind == "POINT":
        return ("point", layer, (_r(entity.dxf.location.x), _r(entity.dxf.location.y)))
    return (kind.lower(), layer)


def _semantics(msp) -> Counter:
    return Counter(semantic_record(e) for e in msp)


def verify_saved_file(path: Path, report: dict, source_doc=None) -> dict:
    """Reopen the written file and compare what it MEANS with the source.

    In-memory state is not evidence: the loss this module repairs happened at write
    time, with the in-memory document still looking correct.

    The gate is semantic, not a count. `LWPOLYLINE -> POLYLINE` legitimately changes
    representation, so entity counts and types are reported for information and are
    never the pass condition. What must survive is geometry (points, bulges, widths,
    closure, elevation), text and its style, layer assignment, and the resource
    definitions those references need.
    """
    saved = ezdxf.readfile(str(path))
    saved_msp = saved.modelspace()
    found_types = Counter(e.dxftype() for e in saved_msp)

    undefined_layers = sorted({e.dxf.layer for e in saved_msp}
                              - {layer.dxf.name for layer in saved.layers})
    undefined_styles = sorted({e.dxf.style for e in saved_msp if e.dxf.hasattr("style")}
                              - {style.dxf.name for style in saved.styles})

    missing_semantics, unexpected_semantics = [], []
    layer_attribute_drift, format_limited = {}, {}
    cannot_store = FORMAT_LIMITED_LAYER_ATTRIBUTES.get(saved.dxfversion, ())
    if source_doc is not None:
        source_semantics = _semantics(source_doc.modelspace())
        saved_semantics = _semantics(saved_msp)
        missing_semantics = sorted(str(k) for k in (source_semantics - saved_semantics))
        unexpected_semantics = sorted(str(k) for k in (saved_semantics - source_semantics))
        for name in {e.dxf.layer for e in saved_msp}:
            before = _table_attributes(source_doc.layers, name, LAYER_ATTRIBUTES)
            after = _table_attributes(saved.layers, name, LAYER_ATTRIBUTES)
            for attr, value in before.items():
                if after.get(attr) == value:
                    continue
                if attr in cannot_store:
                    format_limited.setdefault(name, {})[attr] = value
                else:
                    layer_attribute_drift.setdefault(name, {})[attr] = {
                        "source": value, "saved": after.get(attr)}

    verification = {
        "gate": "semantic comparison against the source document; entity counts are "
                "reported but are not the pass condition",
        "precision": PRECISION,
        "saved_version": saved.dxfversion,
        "saved_entity_types": dict(sorted(found_types.items())),
        "semantics_compared": source_doc is not None,
        "missing_from_saved_file": missing_semantics,
        "unexpected_in_saved_file": unexpected_semantics,
        "layer_attribute_drift": layer_attribute_drift,
        # Declared, expected losses: the target format has nowhere to put these.
        # Reported so a caller can say what the conversion cost.
        "format_limited_layer_attributes": format_limited,
        "entities_referencing_undefined_layers": undefined_layers,
        "entities_referencing_undefined_styles": undefined_styles,
    }
    if (missing_semantics or unexpected_semantics or undefined_layers
            or undefined_styles or layer_attribute_drift):
        raise FidelityError(
            "the saved file does not carry the source's meaning:\n"
            f"  missing: {missing_semantics or 'none'}\n"
            f"  unexpected: {unexpected_semantics or 'none'}\n"
            f"  layer attributes changed: {layer_attribute_drift or 'none'}\n"
            f"  undefined layers referenced: {undefined_layers or 'none'}\n"
            f"  undefined styles referenced: {undefined_styles or 'none'}"
        )
    return verification


def convert_file(source_path: Path, out_path: Path, target_version: str = "R12") -> dict:
    """Convert a DXF file, write it, and verify the written bytes. Fails closed."""
    source_path, out_path = Path(source_path), Path(out_path)
    if not source_path.is_file():
        raise ConversionError(f"input is not a file: {source_path}")
    doc = ezdxf.readfile(str(source_path))
    target, report = convert_document(doc, target_version)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    target.saveas(str(out_path))
    report["source_version"] = doc.dxfversion
    # The source document is passed in so the check is source-vs-saved meaning, not
    # saved-vs-its-own-prediction. A converter that mispredicts would otherwise agree
    # with itself.
    report["verification"] = verify_saved_file(out_path, report, source_doc=doc)
    return report
