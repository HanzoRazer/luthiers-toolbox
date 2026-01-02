# compare_automation_helpers.py
# B22.13: Helper functions for compare automation API

from typing import Optional


async def resolve_svg(source: dict) -> str:
    """
    Resolve SVG text from the given SvgSource.
    
    Args:
        source: Dict with 'kind' and 'value' keys
            - kind='svg': value is raw SVG text
            - kind='id': value is asset ID to lookup
    
    Returns:
        SVG text as string
    
    Raises:
        ValueError: If source kind is unsupported or ID not found
    """
    kind = source.get("kind")
    value = source.get("value", "")
    
    if kind == "svg":
        return value
    
    if kind == "id":
        svg = await load_svg_by_id(value)
        if not svg:
            raise ValueError(f"Unknown SVG id: {value}")
        return svg
    
    raise ValueError(f"Unsupported SVG kind: {kind}")


async def load_svg_by_id(svg_id: str) -> Optional[str]:
    """
    Load SVG content by asset ID.
    
    Supports multiple storage backends:
    1. File system (data/svg_assets/)
    2. Baseline storage (data/baselines/)
    
    Args:
        svg_id: Asset identifier
    
    Returns:
        SVG text if found, None otherwise
    """
    from pathlib import Path
    import json
    
    # Define storage directories
    base_path = Path(__file__).resolve().parent.parent / "data"
    svg_assets_dir = base_path / "svg_assets"
    baselines_dir = base_path / "baselines"
    
    # Try direct SVG file
    svg_file = svg_assets_dir / f"{svg_id}.svg"
    if svg_file.exists():
        return svg_file.read_text(encoding="utf-8")
    
    # Try JSON-wrapped SVG asset
    json_file = svg_assets_dir / f"{svg_id}.json"
    if json_file.exists():
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("svg") or data.get("content") or data.get("svg_content")
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Try baseline storage (baselines may contain SVG in geometry)
    baseline_file = baselines_dir / f"{svg_id}.json"
    if baseline_file.exists():
        try:
            with baseline_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Check for SVG in geometry or direct svg field
            geometry = data.get("geometry", {})
            return geometry.get("svg") or data.get("svg")
        except (json.JSONDecodeError, KeyError):
            pass
    
    return None


async def compute_diff_for_automation(
    left_svg: str,
    right_svg: str,
    mode: str,
    include_layers: bool = True,
) -> dict:
    """
    Core comparison engine wrapper for automation API.
    
    This delegates to the same logic used by interactive CompareLab,
    ensuring consistency between UI and headless modes.
    
    Args:
        left_svg: Left SVG content
        right_svg: Right SVG content
        mode: Comparison mode (side-by-side, overlay, delta)
        include_layers: Whether to analyze layer differences
    
    Returns:
        Dict shaped for CompareAutomationJsonResult:
        {
            'fullBBox': {...},
            'diffBBox': {...},
            'layers': [...],
            'stats': {...}  # comparison statistics
        }
    """
    from ..services.geometry_diff import annotate_geometries_with_colors
    
    # Parse SVG content to geometry format using built-in parser
    left_geometry = _parse_svg_to_geometry(left_svg)
    right_geometry = _parse_svg_to_geometry(right_svg)
    
    # Compute diff using the core geometry diff service
    stats, left_annotated, right_annotated = annotate_geometries_with_colors(
        left_geometry, right_geometry
    )
    
    # Extract bounding boxes from the annotated geometries
    full_bbox = _compute_combined_bbox(left_annotated, right_annotated)
    diff_bbox = _compute_diff_bbox(left_annotated, right_annotated)
    
    result = {
        "fullBBox": full_bbox,
        "diffBBox": diff_bbox,
        "stats": {
            "leftPathCount": stats.baseline_path_count,
            "rightPathCount": stats.current_path_count,
            "addedPaths": stats.added_paths,
            "removedPaths": stats.removed_paths,
            "unchangedPaths": stats.unchanged_paths,
        },
        "mode": mode,
    }
    
    if include_layers:
        result["layers"] = _extract_layer_info(left_annotated, right_annotated)
    
    return result


def _parse_svg_to_geometry(svg_text: str) -> dict:
    """
    Parse SVG text to a geometry dict format compatible with geometry_diff.
    
    Extracts path data from SVG path elements and converts to geometry format.
    
    Args:
        svg_text: Raw SVG content string
        
    Returns:
        Dict with 'paths' key containing list of path dicts
    """
    import re
    import xml.etree.ElementTree as ET
    
    paths = []
    
    try:
        # Parse SVG XML
        root = ET.fromstring(svg_text)
        
        # Define SVG namespace
        ns = {"svg": "http://www.w3.org/2000/svg"}
        
        # Extract all path elements (with and without namespace)
        path_elements = root.findall(".//path", ns) or root.findall(".//path") or []
        path_elements.extend(root.iter("{http://www.w3.org/2000/svg}path"))
        path_elements.extend(root.iter("path"))
        
        # Also check for polylines, lines, etc.
        for tag in ["polyline", "line", "polygon", "circle", "ellipse", "rect"]:
            path_elements.extend(root.iter("{http://www.w3.org/2000/svg}" + tag))
            path_elements.extend(root.iter(tag))
        
        seen_ids = set()
        for elem in path_elements:
            d = elem.get("d", "") or ""
            elem_id = elem.get("id", f"path_{len(paths)}")
            
            # Skip duplicates (due to namespace iteration)
            if elem_id in seen_ids:
                continue
            seen_ids.add(elem_id)
            
            # Extract basic path info
            path_entry = {
                "id": elem_id,
                "d": d,
                "points": _extract_points_from_path(d) if d else [],
                "meta": {
                    "stroke": elem.get("stroke", ""),
                    "fill": elem.get("fill", ""),
                },
            }
            paths.append(path_entry)
            
    except ET.ParseError:
        # If XML parsing fails, try regex extraction
        path_pattern = r'd="([^"]*)"'
        matches = re.findall(path_pattern, svg_text)
        for i, d in enumerate(matches):
            paths.append({
                "id": f"path_{i}",
                "d": d,
                "points": _extract_points_from_path(d),
                "meta": {},
            })
    
    return {"paths": paths}


def _extract_points_from_path(d: str) -> list:
    """
    Extract coordinate points from an SVG path 'd' attribute.
    
    This is a simplified parser that handles common path commands.
    """
    import re
    
    points = []
    
    # Extract numeric coordinates (pairs of numbers)
    # This handles M, L, C, etc. commands
    num_pattern = r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
    numbers = re.findall(num_pattern, d)
    
    # Pair up numbers as x,y coordinates
    for i in range(0, len(numbers) - 1, 2):
        try:
            x = float(numbers[i])
            y = float(numbers[i + 1])
            points.append([x, y])
        except (ValueError, IndexError):
            pass
    
    return points


def _compute_combined_bbox(left: dict, right: dict) -> dict:
    """Compute combined bounding box for both geometries."""
    # Extract paths from both geometries
    left_paths = left.get("paths", []) or left.get("loops", [])
    right_paths = right.get("paths", []) or right.get("loops", [])
    
    all_points = []
    for paths in [left_paths, right_paths]:
        for path in paths:
            if isinstance(path, dict):
                points = path.get("points", [])
                all_points.extend(points)
    
    if not all_points:
        return {"minX": 0, "minY": 0, "maxX": 0, "maxY": 0}
    
    xs = [p[0] if isinstance(p, (list, tuple)) else p.get("x", 0) for p in all_points]
    ys = [p[1] if isinstance(p, (list, tuple)) else p.get("y", 0) for p in all_points]
    
    return {
        "minX": min(xs) if xs else 0,
        "minY": min(ys) if ys else 0,
        "maxX": max(xs) if xs else 0,
        "maxY": max(ys) if ys else 0,
    }


def _compute_diff_bbox(left: dict, right: dict) -> dict:
    """Compute bounding box of just the changed regions."""
    # Only include paths marked as added (green) or removed (red)
    left_paths = left.get("paths", []) or left.get("loops", [])
    right_paths = right.get("paths", []) or right.get("loops", [])
    
    diff_points = []
    for paths in [left_paths, right_paths]:
        for path in paths:
            if isinstance(path, dict):
                color = path.get("meta", {}).get("color")
                if color in ("red", "green"):  # Changed paths only
                    points = path.get("points", [])
                    diff_points.extend(points)
    
    if not diff_points:
        return {"minX": 0, "minY": 0, "maxX": 0, "maxY": 0}
    
    xs = [p[0] if isinstance(p, (list, tuple)) else p.get("x", 0) for p in diff_points]
    ys = [p[1] if isinstance(p, (list, tuple)) else p.get("y", 0) for p in diff_points]
    
    return {
        "minX": min(xs) if xs else 0,
        "minY": min(ys) if ys else 0,
        "maxX": max(xs) if xs else 0,
        "maxY": max(ys) if ys else 0,
    }


def _extract_layer_info(left: dict, right: dict) -> list:
    """Extract layer information from annotated geometries."""
    layers = []
    
    # Check for layer metadata in the geometries
    left_layers = left.get("layers", {})
    right_layers = right.get("layers", {})
    
    all_layer_names = set(left_layers.keys()) | set(right_layers.keys())
    
    for name in sorted(all_layer_names):
        left_count = len(left_layers.get(name, {}).get("paths", []))
        right_count = len(right_layers.get(name, {}).get("paths", []))
        
        layers.append({
            "name": name,
            "leftPathCount": left_count,
            "rightPathCount": right_count,
            "hasChanges": left_count != right_count,
        })
    
    return layers
