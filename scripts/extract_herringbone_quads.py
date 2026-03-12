"""Extract embedded herringbone quads from JSX mothership to Python module."""
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSX_PATH = ROOT / "docs" / "rosette-prototypes" / "jsx" / "rosette-grid-designer-v4-mothership.jsx"
OUT_PATH = ROOT / "services" / "api" / "app" / "cam" / "rosette" / "prototypes" / "herringbone_embedded_quads.py"

with open(JSX_PATH, "r") as f:
    for line in f:
        if line.strip().startswith("const DXF"):
            match = re.search(r"const DXF\s*=\s*(\{.*?\});", line)
            if match:
                data = json.loads(match.group(1))
                dark = data["d"]
                light = data["l"]
                print(f"Dark quads: {len(dark)}")
                print(f"Light quads: {len(light)}")
                print(f"Total: {len(dark) + len(light)}")
                break

lines = []
lines.append('"""')
lines.append("Embedded herringbone DXF tile quads.")
lines.append("")
lines.append("Extracted from: rosette-grid-designer-v4-mothership.jsx")
lines.append("Source: parquet_herringbone_rosette.dxf")
lines.append("")
lines.append("596 dark + 602 light tiles, each quad as 4 corner points in mm.")
lines.append("Raw format: [x0, y0, x1, y1, x2, y2, x3, y3] per quad.")
lines.append("")
lines.append("Ring dimensions (mm):")
lines.append("    Soundhole:     r = 40.8")
lines.append("    Inner Border:  r = 40.8 - 41.8")
lines.append("    Pattern Zone:  r = 41.8 - 47.8  (tile zone)")
lines.append("    Ebony Ring:    r = 47.8 - 49.3")
lines.append("    Green Ring:    r = 49.3 - 50.8")
lines.append('"""')
lines.append("")
lines.append("")
lines.append("# 596 dark parity quads [x0, y0, x1, y1, x2, y2, x3, y3] in mm")
lines.append("DARK_QUADS_RAW: list[list[float]] = [")
for q in dark:
    lines.append(f"    {q},")
lines.append("]")
lines.append("")
lines.append("")
lines.append("# 602 light parity quads [x0, y0, x1, y1, x2, y2, x3, y3] in mm")
lines.append("LIGHT_QUADS_RAW: list[list[float]] = [")
for q in light:
    lines.append(f"    {q},")
lines.append("]")
lines.append("")
lines.append("")
lines.append("def get_embedded_quads() -> list[tuple[int, list[tuple[float, float]]]]:")
lines.append('    """')
lines.append("    Return embedded quads as (parity, [(x,y) x 4]) pairs.")
lines.append("")
lines.append("    parity 0 = dark, 1 = light.")
lines.append("    Each quad is 4 corner points in mm coordinates.")
lines.append('    """')
lines.append("    quads: list[tuple[int, list[tuple[float, float]]]] = []")
lines.append("    for raw in DARK_QUADS_RAW:")
lines.append("        pts = [(raw[i], raw[i + 1]) for i in range(0, 8, 2)]")
lines.append("        quads.append((0, pts))")
lines.append("    for raw in LIGHT_QUADS_RAW:")
lines.append("        pts = [(raw[i], raw[i + 1]) for i in range(0, 8, 2)]")
lines.append("        quads.append((1, pts))")
lines.append("    return quads")
lines.append("")

OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"Written to {OUT_PATH}")
print(f"  {len(lines)} lines")
