"""
Art Studio Output Validators

Validates generated outputs against CNC manufacturing constraints.
Each validator checks format-specific requirements for manufacturability.
"""
from __future__ import annotations

import re
import io
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """Validation result severity."""
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of output validation."""
    valid: bool
    level: ValidationLevel
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_manufacturable(self) -> bool:
        """True if output can be manufactured (no errors)."""
        return self.level != ValidationLevel.ERROR

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "level": self.level.value,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


def validate_output(prompt_id: str, content: bytes | str) -> ValidationResult:
    """
    Validate output based on prompt category.

    Args:
        prompt_id: The prompt that generated this output
        content: The generated content (bytes or string)

    Returns:
        ValidationResult with pass/fail and details
    """
    from . import get_prompt

    prompt = get_prompt(prompt_id)
    category = prompt.get("category", "")
    output_format = prompt.get("outputs", {}).get("format", "svg")

    if output_format == "svg":
        content_str = content.decode() if isinstance(content, bytes) else content
        return validate_svg(content_str, prompt.get("validation", {}))
    elif output_format == "png":
        content_bytes = content if isinstance(content, bytes) else content.encode()
        return validate_heightmap(content_bytes, prompt.get("validation", {}))
    elif output_format == "stl":
        content_bytes = content if isinstance(content, bytes) else content.encode()
        return validate_stl(content_bytes, prompt.get("validation", {}))
    else:
        return ValidationResult(
            valid=True,
            level=ValidationLevel.WARNING,
            warnings=[f"No validator for format: {output_format}"],
        )


def validate_svg(
    svg_content: str,
    validation_rules: Optional[Dict] = None,
) -> ValidationResult:
    """
    Validate SVG for CNC manufacturability.

    Checks:
        - Valid XML structure
        - Required elements present (paths)
        - No forbidden elements (gradients)
        - Closed paths
        - File size limits

    Args:
        svg_content: SVG content as string
        validation_rules: Optional validation rules from prompt

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    metadata = {}
    rules = validation_rules or {}

    # Parse SVG
    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError as e:
        return ValidationResult(
            valid=False,
            level=ValidationLevel.ERROR,
            errors=[f"Invalid SVG XML: {e}"],
        )

    # Get SVG namespace
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Check required elements
    required = rules.get("required_elements", ["path"])
    for elem_name in required:
        found = root.findall(f".//{elem_name}", ns) or root.findall(f".//{{{ns['svg']}}}{elem_name}")
        if not found:
            # Try without namespace
            found = root.findall(f".//{elem_name}")
        if not found:
            errors.append(f"Missing required element: {elem_name}")
        else:
            metadata[f"{elem_name}_count"] = len(found)

    # Check forbidden elements
    forbidden = rules.get("forbidden_elements", [])
    for elem_name in forbidden:
        found = root.findall(f".//{elem_name}", ns) or root.findall(f".//{elem_name}")
        if found:
            errors.append(f"Forbidden element found: {elem_name} (not CNC-compatible)")

    # Check for gradients (common problem)
    for grad_type in ["linearGradient", "radialGradient"]:
        if grad_type not in forbidden:
            found = root.findall(f".//{grad_type}") or root.findall(f".//{{{ns['svg']}}}{grad_type}")
            if found:
                warnings.append(f"Found {grad_type} - may not be CNC-compatible")

    # Check file size
    max_size_kb = rules.get("max_file_size_kb", 500)
    actual_size_kb = len(svg_content.encode()) / 1024
    metadata["file_size_kb"] = round(actual_size_kb, 2)
    if actual_size_kb > max_size_kb:
        warnings.append(f"File size {actual_size_kb:.1f}KB exceeds recommended {max_size_kb}KB")

    # Check for open paths (basic heuristic)
    paths = root.findall(".//path", ns) or root.findall(".//{http://www.w3.org/2000/svg}path") or root.findall(".//path")
    open_path_count = 0
    for path in paths:
        d = path.get("d", "")
        # Check if path ends with Z (close) command
        if d and not re.search(r'[zZ]\s*$', d.strip()):
            open_path_count += 1

    if open_path_count > 0:
        metadata["open_paths"] = open_path_count
        if rules.get("closed_paths", False):
            errors.append(f"Found {open_path_count} open path(s) - CNC requires closed paths")
        else:
            warnings.append(f"Found {open_path_count} open path(s) - may cause toolpath issues")

    # Determine result level
    if errors:
        level = ValidationLevel.ERROR
        valid = False
    elif warnings:
        level = ValidationLevel.WARNING
        valid = True
    else:
        level = ValidationLevel.PASS
        valid = True

    return ValidationResult(
        valid=valid,
        level=level,
        errors=errors,
        warnings=warnings,
        metadata=metadata,
    )


def validate_heightmap(
    image_bytes: bytes,
    validation_rules: Optional[Dict] = None,
) -> ValidationResult:
    """
    Validate heightmap image for relief conversion.

    Checks:
        - Valid image format
        - Grayscale mode
        - Minimum resolution
        - Bit depth

    Args:
        image_bytes: PNG image bytes
        validation_rules: Optional validation rules from prompt

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    metadata = {}
    rules = validation_rules or {}

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
    except ImportError:
        return ValidationResult(
            valid=True,
            level=ValidationLevel.WARNING,
            warnings=["PIL not available - skipping heightmap validation"],
        )
    except (OSError, ValueError) as e:  # WP-1: narrowed from except Exception
        return ValidationResult(
            valid=False,
            level=ValidationLevel.ERROR,
            errors=[f"Invalid image: {e}"],
        )

    # Check dimensions
    width, height = img.size
    metadata["width"] = width
    metadata["height"] = height

    min_width = rules.get("min_width", 1024)
    min_height = rules.get("min_height", 1024)

    if width < min_width:
        warnings.append(f"Width {width}px below recommended {min_width}px")
    if height < min_height:
        warnings.append(f"Height {height}px below recommended {min_height}px")

    # Check color mode
    metadata["mode"] = img.mode
    if rules.get("grayscale_only", True):
        if img.mode not in ("L", "LA", "I", "F"):
            if img.mode in ("RGB", "RGBA"):
                # Check if actually grayscale
                r, g, b = img.split()[:3]
                if r.tobytes() == g.tobytes() == b.tobytes():
                    warnings.append("Image is RGB but appears grayscale - consider converting")
                else:
                    errors.append(f"Image mode is {img.mode}, expected grayscale (L)")
            else:
                errors.append(f"Image mode is {img.mode}, expected grayscale (L)")

    # Check bit depth (8-bit preferred for heightmaps)
    if img.mode == "I":
        metadata["bit_depth"] = 32
        warnings.append("32-bit image - consider converting to 8-bit for compatibility")
    elif img.mode == "F":
        metadata["bit_depth"] = "float"
        warnings.append("Float image - consider converting to 8-bit for compatibility")
    else:
        metadata["bit_depth"] = 8

    # Determine result level
    if errors:
        level = ValidationLevel.ERROR
        valid = False
    elif warnings:
        level = ValidationLevel.WARNING
        valid = True
    else:
        level = ValidationLevel.PASS
        valid = True

    return ValidationResult(
        valid=valid,
        level=level,
        errors=errors,
        warnings=warnings,
        metadata=metadata,
    )


def validate_stl(
    stl_bytes: bytes,
    validation_rules: Optional[Dict] = None,
) -> ValidationResult:
    """
    Validate STL mesh for CNC machining.

    Checks:
        - Valid STL format (ASCII or binary)
        - Triangle count within limits
        - Basic watertight heuristics

    Args:
        stl_bytes: STL file bytes
        validation_rules: Optional validation rules from prompt

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    metadata = {}
    rules = validation_rules or {}

    # Detect format (ASCII vs binary)
    is_ascii = stl_bytes[:5].lower() == b"solid"

    if is_ascii:
        metadata["format"] = "ascii"
        content = stl_bytes.decode("utf-8", errors="replace")

        # Count triangles
        triangle_count = content.lower().count("facet normal")
        metadata["triangles"] = triangle_count

        # Check for endsolid
        if "endsolid" not in content.lower():
            errors.append("ASCII STL missing 'endsolid' - file may be truncated")

    else:
        metadata["format"] = "binary"

        # Binary STL: 80 byte header + 4 byte triangle count + triangles
        if len(stl_bytes) < 84:
            errors.append("Binary STL too short - invalid file")
        else:
            import struct
            triangle_count = struct.unpack("<I", stl_bytes[80:84])[0]
            metadata["triangles"] = triangle_count

            # Each triangle is 50 bytes (12 floats + 2 byte attribute)
            expected_size = 84 + (triangle_count * 50)
            if len(stl_bytes) < expected_size:
                errors.append(f"Binary STL truncated: expected {expected_size} bytes, got {len(stl_bytes)}")

    # Check triangle count limits
    max_triangles = rules.get("max_triangles", 500000)
    if metadata.get("triangles", 0) > max_triangles:
        warnings.append(f"Triangle count {metadata['triangles']} exceeds {max_triangles} - may cause CAM slowdown")

    if metadata.get("triangles", 0) == 0:
        errors.append("STL has no triangles - empty mesh")

    # File size check
    metadata["file_size_mb"] = round(len(stl_bytes) / (1024 * 1024), 2)

    # Determine result level
    if errors:
        level = ValidationLevel.ERROR
        valid = False
    elif warnings:
        level = ValidationLevel.WARNING
        valid = True
    else:
        level = ValidationLevel.PASS
        valid = True

    return ValidationResult(
        valid=valid,
        level=level,
        errors=errors,
        warnings=warnings,
        metadata=metadata,
    )


def validate_geometry_constraints(
    svg_content: str,
    min_feature_size: float = 0.0625,
    tool_diameter: float = 0.125,
    units: str = "in",
) -> ValidationResult:
    """
    Advanced geometry validation for CNC constraints.

    Checks for features too small to machine with specified tool.
    This is a more expensive check - use for final validation.

    Args:
        svg_content: SVG content
        min_feature_size: Minimum feature size in units
        tool_diameter: Tool diameter in units
        units: Measurement units

    Returns:
        ValidationResult with geometry analysis
    """
    warnings = []
    metadata = {
        "min_feature_size": min_feature_size,
        "tool_diameter": tool_diameter,
        "units": units,
    }

    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError:
        return ValidationResult(
            valid=False,
            level=ValidationLevel.ERROR,
            errors=["Invalid SVG"],
        )

    # Get viewBox for scale reference
    viewbox = root.get("viewBox", "")
    if viewbox:
        parts = viewbox.split()
        if len(parts) == 4:
            metadata["viewbox_width"] = float(parts[2])
            metadata["viewbox_height"] = float(parts[3])

    # Count path elements for complexity estimate
    paths = root.findall(".//{http://www.w3.org/2000/svg}path") or root.findall(".//path")
    metadata["path_count"] = len(paths)

    if len(paths) > 1000:
        warnings.append(f"High path count ({len(paths)}) may cause CAM performance issues")

    # Tool radius constraint note
    min_corner = tool_diameter / 2
    metadata["min_internal_corner_radius"] = min_corner
    warnings.append(f"Internal corners must have radius >= {min_corner} {units} for {tool_diameter} {units} tool")

    return ValidationResult(
        valid=True,
        level=ValidationLevel.WARNING if warnings else ValidationLevel.PASS,
        warnings=warnings,
        metadata=metadata,
    )
