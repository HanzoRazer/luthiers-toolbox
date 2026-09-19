"""
LTB-R12-002 D4 — generate a consolidator fixture, deterministically.

The landed smoke test builds a consolidator-**shaped** document by hand. That tests the
converter against someone's model of what `LayerConsolidator` emits. This runs the real
chain instead:

    synthetic raw LINE dump  ->  LayerConsolidator  ->  R2000 with LWPOLYLINE

Every coordinate here is fixed, so the output is reproducible; the generator is
committed rather than an opaque binary, so a reader can see what the fixture is and
regenerate it after any consolidator change.

**This fixture cannot reach G1.** `LayerConsolidator` calls `add_lwpolyline(chain,
close=..., dxfattribs={"layer": ...})` and never sets `elevation`, so its output is
always flat. G1 needs a source that sets elevation, which is why the two tests are
independent and neither substitutes for the other.
"""
from __future__ import annotations

from pathlib import Path

import ezdxf

from app.cam.layer_consolidator import consolidate_preserving_layers

# A closed rectangular contour plus an interior detail, expressed the way the
# vectorizer emits geometry: many short LINE segments on a named layer.
BODY_OUTLINE = [(0.0, 0.0), (100.0, 0.0), (100.0, 60.0), (0.0, 60.0), (0.0, 0.0)]
CAVITY = [(30.0, 20.0), (70.0, 20.0), (70.0, 40.0), (30.0, 40.0), (30.0, 20.0)]
SEGMENTS_PER_EDGE = 8


def _segment(start, end, count):
    """Split one edge into `count` collinear LINE endpoints, as a raw dump would."""
    (x0, y0), (x1, y1) = start, end
    for index in range(count):
        a = index / count
        b = (index + 1) / count
        yield ((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a),
               (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b))


def write_raw_dump(path: Path) -> Path:
    """The vectorizer's shape: R12, LINE entities only, named layers."""
    doc = ezdxf.new("R12")
    doc.layers.add("BODY_OUTLINE")
    doc.layers.add("CAVITY")
    msp = doc.modelspace()
    for layer, ring in (("BODY_OUTLINE", BODY_OUTLINE), ("CAVITY", CAVITY)):
        for start, end in zip(ring, ring[1:]):
            for a, b in _segment(start, end, SEGMENTS_PER_EDGE):
                msp.add_line(a, b, dxfattribs={"layer": layer})
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(path))
    return path


def generate_consolidator_fixture(out_dir: Path) -> dict:
    """Run the real chain. Returns the paths and the consolidator's own counts."""
    out_dir = Path(out_dir)
    raw = write_raw_dump(out_dir / "raw_lines.dxf")
    consolidated = out_dir / "consolidated.dxf"
    result = consolidate_preserving_layers(str(raw), str(consolidated), dedupe_body=False)
    return {
        "raw": raw,
        "consolidated": Path(result.output_path),
        "input_lines": result.input_lines,
        "output_polylines": result.output_polylines,
        "layer_stats": result.layer_stats,
    }


if __name__ == "__main__":  # regeneration by hand, into a directory you name
    import sys

    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    record = generate_consolidator_fixture(target)
    print(f"raw            : {record['raw']}")
    print(f"consolidated   : {record['consolidated']}")
    print(f"lines in       : {record['input_lines']}")
    print(f"polylines out  : {record['output_polylines']}")
    print(f"layer stats    : {record['layer_stats']}")
