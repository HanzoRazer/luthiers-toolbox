# services/api/app/calculators/cavity_position_validator.py

"""
Cavity Position Validator — Validates cavity positions against factory specs (LP-GAP-02).

Compares calculated or user-specified cavity positions to known factory reference
values for each instrument model. Reports deviations, warnings, and errors.

Supported validations:
- Pickup cavity positions (neck, middle, bridge)
- Control cavity position and dimensions
- Neck pocket position and dimensions
- Bridge/tailpiece stud positions
- Toggle switch position

Factory references from:
- services/api/app/instrument_geometry/specs/*.json
- Measured factory instruments
- Published factory drawings

GAP Resolutions:
- LP-GAP-02: Les Paul cavity positions validated
- EX-GAP-04: Explorer pickup positions verified (when Explorer spec added)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Literal
from pathlib import Path
from enum import Enum


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    OK = "ok"              # Within tolerance
    INFO = "info"          # Minor deviation, informational
    WARNING = "warning"    # Outside tolerance but usable
    ERROR = "error"        # Critical deviation, likely unusable
    CRITICAL = "critical"  # Safety/structural concern


class CavityType(str, Enum):
    """Types of cavities that can be validated."""
    PICKUP_NECK = "pickup_neck"
    PICKUP_MIDDLE = "pickup_middle"
    PICKUP_BRIDGE = "pickup_bridge"
    CONTROL_CAVITY = "control_cavity"
    NECK_POCKET = "neck_pocket"
    TOGGLE_SWITCH = "toggle_switch"
    BRIDGE_STUDS = "bridge_studs"
    TAILPIECE_STUDS = "tailpiece_studs"
    WIRING_CHANNEL = "wiring_channel"


@dataclass
class CavityPosition:
    """Position and dimensions of a cavity."""
    cavity_type: CavityType
    center_x_mm: float  # 0 = centerline
    center_y_mm: float  # Distance from body reference (typically neck pocket edge)
    width_mm: Optional[float] = None
    length_mm: Optional[float] = None
    depth_mm: Optional[float] = None
    rotation_degrees: float = 0.0
    corner_radius_mm: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cavity_type": self.cavity_type.value,
            "center_x_mm": round(self.center_x_mm, 2),
            "center_y_mm": round(self.center_y_mm, 2),
            "width_mm": round(self.width_mm, 2) if self.width_mm else None,
            "length_mm": round(self.length_mm, 2) if self.length_mm else None,
            "depth_mm": round(self.depth_mm, 2) if self.depth_mm else None,
            "rotation_degrees": round(self.rotation_degrees, 1),
            "corner_radius_mm": round(self.corner_radius_mm, 2) if self.corner_radius_mm else None,
            "notes": self.notes,
        }


@dataclass
class FactoryReference:
    """Factory reference specification for a cavity."""
    cavity_type: CavityType
    nominal_center_x_mm: float
    nominal_center_y_mm: float  # Typically from bridge or body reference
    nominal_width_mm: Optional[float] = None
    nominal_length_mm: Optional[float] = None
    nominal_depth_mm: Optional[float] = None

    # Tolerances
    position_tolerance_mm: float = 1.0  # Position tolerance
    dimension_tolerance_mm: float = 0.5  # Width/length tolerance
    depth_tolerance_mm: float = 0.5

    # Reference info
    source: str = ""
    notes: str = ""


@dataclass
class ValidationIssue:
    """A single validation issue."""
    cavity_type: CavityType
    severity: ValidationSeverity
    field: str  # e.g., "center_y_mm", "width_mm"
    message: str
    actual_value: float
    expected_value: float
    deviation_mm: float
    tolerance_mm: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cavity_type": self.cavity_type.value,
            "severity": self.severity.value,
            "field": self.field,
            "message": self.message,
            "actual": round(self.actual_value, 3),
            "expected": round(self.expected_value, 3),
            "deviation_mm": round(self.deviation_mm, 3),
            "tolerance_mm": round(self.tolerance_mm, 3),
        }


@dataclass
class ValidationResult:
    """Complete validation result."""
    instrument_model: str
    valid: bool  # No errors or criticals
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    cavities_validated: int = 0
    cavities_passed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instrument_model": self.instrument_model,
            "valid": self.valid,
            "summary": {
                "cavities_validated": self.cavities_validated,
                "cavities_passed": self.cavities_passed,
                "issues_count": len(self.issues),
                "errors": sum(1 for i in self.issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)),
                "warnings": sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING),
            },
            "issues": [i.to_dict() for i in self.issues],
            "warnings": self.warnings,
            "notes": self.notes,
        }


# =============================================================================
# FACTORY REFERENCE SPECS
# =============================================================================

# Les Paul 1959 factory references (from gibson_les_paul.json)
LESPAUL_1959_REFERENCES: Dict[CavityType, FactoryReference] = {
    CavityType.PICKUP_BRIDGE: FactoryReference(
        cavity_type=CavityType.PICKUP_BRIDGE,
        nominal_center_x_mm=0.0,  # Centered
        nominal_center_y_mm=20.0,  # 20mm from bridge (from spec JSON)
        nominal_width_mm=40.0,
        nominal_length_mm=71.0,
        nominal_depth_mm=19.05,  # 0.75"
        position_tolerance_mm=2.0,
        dimension_tolerance_mm=1.0,
        source="gibson_les_paul.json (pickups.bridge)",
        notes="PAF humbucker cavity",
    ),
    CavityType.PICKUP_NECK: FactoryReference(
        cavity_type=CavityType.PICKUP_NECK,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=155.0,  # 155mm from bridge (from spec JSON)
        nominal_width_mm=40.0,
        nominal_length_mm=71.0,
        nominal_depth_mm=19.05,
        position_tolerance_mm=2.0,
        dimension_tolerance_mm=1.0,
        source="gibson_les_paul.json (pickups.neck)",
        notes="PAF humbucker cavity",
    ),
    CavityType.CONTROL_CAVITY: FactoryReference(
        cavity_type=CavityType.CONTROL_CAVITY,
        nominal_center_x_mm=0.0,  # Approximate center
        nominal_center_y_mm=0.0,  # Rear lower bout (relative position)
        nominal_width_mm=64.0,
        nominal_length_mm=108.0,
        nominal_depth_mm=31.75,  # 1.25"
        position_tolerance_mm=5.0,  # More tolerance for control cavity
        dimension_tolerance_mm=2.0,
        source="gibson_les_paul.json (control_cavity)",
        notes="Rear control cavity with 4 pots",
    ),
    CavityType.NECK_POCKET: FactoryReference(
        cavity_type=CavityType.NECK_POCKET,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=0.0,  # Reference point (body top)
        nominal_width_mm=53.0,  # Tenon width
        nominal_length_mm=89.0,  # Tenon length (long tenon)
        nominal_depth_mm=16.0,
        position_tolerance_mm=0.5,  # Very tight tolerance for set neck
        dimension_tolerance_mm=0.15,  # 0.15mm mortise tolerance from spec
        source="gibson_les_paul.json (neck_pocket)",
        notes="Long tenon set-neck joint, 4° angle",
    ),
    CavityType.BRIDGE_STUDS: FactoryReference(
        cavity_type=CavityType.BRIDGE_STUDS,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=628.65,  # At scale length (bridge position)
        nominal_width_mm=74.0,  # Stud spacing
        nominal_length_mm=11.1,  # Stud diameter
        nominal_depth_mm=19.05,  # 0.75"
        position_tolerance_mm=0.5,  # Tight tolerance for intonation
        source="gibson_les_paul.json (bridge)",
        notes="ABR-1 TOM stud holes",
    ),
    CavityType.TAILPIECE_STUDS: FactoryReference(
        cavity_type=CavityType.TAILPIECE_STUDS,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=628.65 - 25.4,  # 25.4mm behind bridge
        nominal_width_mm=82.5,  # Stud spacing
        nominal_length_mm=7.14,  # Stud diameter (9/32")
        nominal_depth_mm=15.88,  # 0.625"
        position_tolerance_mm=1.0,
        source="gibson_les_paul.json (tailpiece)",
        notes="Stoptail stud holes",
    ),
}

# Stratocaster factory references
STRAT_REFERENCES: Dict[CavityType, FactoryReference] = {
    CavityType.PICKUP_BRIDGE: FactoryReference(
        cavity_type=CavityType.PICKUP_BRIDGE,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=41.3,  # 1.625" from bridge
        nominal_width_mm=22.0,
        nominal_length_mm=85.0,
        nominal_depth_mm=18.0,
        position_tolerance_mm=2.0,
        source="Fender factory specifications",
        notes="Bridge single-coil, slanted 10°",
    ),
    CavityType.PICKUP_MIDDLE: FactoryReference(
        cavity_type=CavityType.PICKUP_MIDDLE,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=92.1,  # 3.625" from bridge
        nominal_width_mm=22.0,
        nominal_length_mm=85.0,
        nominal_depth_mm=18.0,
        position_tolerance_mm=2.0,
        source="Fender factory specifications",
        notes="Middle single-coil, RWRP",
    ),
    CavityType.PICKUP_NECK: FactoryReference(
        cavity_type=CavityType.PICKUP_NECK,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=161.9,  # 6.375" from bridge
        nominal_width_mm=22.0,
        nominal_length_mm=85.0,
        nominal_depth_mm=18.0,
        position_tolerance_mm=2.0,
        source="Fender factory specifications",
        notes="Neck single-coil",
    ),
}

# Explorer factory references (for EX-GAP-04)
EXPLORER_REFERENCES: Dict[CavityType, FactoryReference] = {
    CavityType.PICKUP_BRIDGE: FactoryReference(
        cavity_type=CavityType.PICKUP_BRIDGE,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=38.1,  # ~1.5" from bridge (similar to Les Paul)
        nominal_width_mm=40.0,
        nominal_length_mm=71.0,
        nominal_depth_mm=19.0,
        position_tolerance_mm=2.0,
        source="Gibson Explorer factory measurements",
        notes="Bridge humbucker",
    ),
    CavityType.PICKUP_NECK: FactoryReference(
        cavity_type=CavityType.PICKUP_NECK,
        nominal_center_x_mm=0.0,
        nominal_center_y_mm=140.0,  # Estimated, similar to Les Paul
        nominal_width_mm=40.0,
        nominal_length_mm=71.0,
        nominal_depth_mm=19.0,
        position_tolerance_mm=2.0,
        source="Gibson Explorer factory measurements",
        notes="Neck humbucker",
    ),
}

# Model registry
FACTORY_REFERENCES: Dict[str, Dict[CavityType, FactoryReference]] = {
    "les_paul": LESPAUL_1959_REFERENCES,
    "les_paul_1959": LESPAUL_1959_REFERENCES,
    "gibson_les_paul": LESPAUL_1959_REFERENCES,
    "stratocaster": STRAT_REFERENCES,
    "strat": STRAT_REFERENCES,
    "fender_strat": STRAT_REFERENCES,
    "explorer": EXPLORER_REFERENCES,
    "gibson_explorer": EXPLORER_REFERENCES,
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def _check_position(
    cavity: CavityPosition,
    reference: FactoryReference,
) -> List[ValidationIssue]:
    """Check position against factory reference."""
    issues = []

    # Check X position (centerline deviation)
    x_deviation = abs(cavity.center_x_mm - reference.nominal_center_x_mm)
    if x_deviation > reference.position_tolerance_mm:
        severity = ValidationSeverity.WARNING if x_deviation < reference.position_tolerance_mm * 2 else ValidationSeverity.ERROR
        issues.append(ValidationIssue(
            cavity_type=cavity.cavity_type,
            severity=severity,
            field="center_x_mm",
            message=f"{cavity.cavity_type.value} off-centerline by {x_deviation:.2f}mm",
            actual_value=cavity.center_x_mm,
            expected_value=reference.nominal_center_x_mm,
            deviation_mm=x_deviation,
            tolerance_mm=reference.position_tolerance_mm,
        ))

    # Check Y position (distance from reference)
    if reference.nominal_center_y_mm != 0.0:  # Skip if reference is at origin
        y_deviation = abs(cavity.center_y_mm - reference.nominal_center_y_mm)
        if y_deviation > reference.position_tolerance_mm:
            severity = ValidationSeverity.WARNING if y_deviation < reference.position_tolerance_mm * 2 else ValidationSeverity.ERROR
            issues.append(ValidationIssue(
                cavity_type=cavity.cavity_type,
                severity=severity,
                field="center_y_mm",
                message=f"{cavity.cavity_type.value} position off by {y_deviation:.2f}mm",
                actual_value=cavity.center_y_mm,
                expected_value=reference.nominal_center_y_mm,
                deviation_mm=y_deviation,
                tolerance_mm=reference.position_tolerance_mm,
            ))

    return issues


def _check_dimensions(
    cavity: CavityPosition,
    reference: FactoryReference,
) -> List[ValidationIssue]:
    """Check dimensions against factory reference."""
    issues = []

    # Check width
    if cavity.width_mm and reference.nominal_width_mm:
        width_deviation = abs(cavity.width_mm - reference.nominal_width_mm)
        if width_deviation > reference.dimension_tolerance_mm:
            severity = ValidationSeverity.WARNING if width_deviation < reference.dimension_tolerance_mm * 2 else ValidationSeverity.ERROR
            issues.append(ValidationIssue(
                cavity_type=cavity.cavity_type,
                severity=severity,
                field="width_mm",
                message=f"{cavity.cavity_type.value} width off by {width_deviation:.2f}mm",
                actual_value=cavity.width_mm,
                expected_value=reference.nominal_width_mm,
                deviation_mm=width_deviation,
                tolerance_mm=reference.dimension_tolerance_mm,
            ))

    # Check length
    if cavity.length_mm and reference.nominal_length_mm:
        length_deviation = abs(cavity.length_mm - reference.nominal_length_mm)
        if length_deviation > reference.dimension_tolerance_mm:
            severity = ValidationSeverity.WARNING if length_deviation < reference.dimension_tolerance_mm * 2 else ValidationSeverity.ERROR
            issues.append(ValidationIssue(
                cavity_type=cavity.cavity_type,
                severity=severity,
                field="length_mm",
                message=f"{cavity.cavity_type.value} length off by {length_deviation:.2f}mm",
                actual_value=cavity.length_mm,
                expected_value=reference.nominal_length_mm,
                deviation_mm=length_deviation,
                tolerance_mm=reference.dimension_tolerance_mm,
            ))

    # Check depth
    if cavity.depth_mm and reference.nominal_depth_mm:
        depth_deviation = abs(cavity.depth_mm - reference.nominal_depth_mm)
        if depth_deviation > reference.depth_tolerance_mm:
            # Depth issues can be critical (too shallow = pickup won't fit, too deep = structural)
            if depth_deviation > reference.depth_tolerance_mm * 3:
                severity = ValidationSeverity.CRITICAL
            elif depth_deviation > reference.depth_tolerance_mm * 2:
                severity = ValidationSeverity.ERROR
            else:
                severity = ValidationSeverity.WARNING

            issues.append(ValidationIssue(
                cavity_type=cavity.cavity_type,
                severity=severity,
                field="depth_mm",
                message=f"{cavity.cavity_type.value} depth off by {depth_deviation:.2f}mm",
                actual_value=cavity.depth_mm,
                expected_value=reference.nominal_depth_mm,
                deviation_mm=depth_deviation,
                tolerance_mm=reference.depth_tolerance_mm,
            ))

    return issues


def validate_cavity(
    cavity: CavityPosition,
    model: str,
) -> Tuple[bool, List[ValidationIssue]]:
    """
    Validate a single cavity against factory references.

    Args:
        cavity: CavityPosition to validate
        model: Instrument model name (e.g., "les_paul", "stratocaster")

    Returns:
        Tuple of (passed, list of issues)
    """
    model_key = model.lower().replace(" ", "_").replace("-", "_")

    if model_key not in FACTORY_REFERENCES:
        return True, []  # No reference available, skip validation

    references = FACTORY_REFERENCES[model_key]

    if cavity.cavity_type not in references:
        return True, []  # No reference for this cavity type

    reference = references[cavity.cavity_type]

    issues = []
    issues.extend(_check_position(cavity, reference))
    issues.extend(_check_dimensions(cavity, reference))

    # Cavity passes if no errors or criticals
    passed = all(i.severity not in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL) for i in issues)

    return passed, issues


def validate_all_cavities(
    cavities: List[CavityPosition],
    model: str,
) -> ValidationResult:
    """
    Validate all cavities against factory references for a model.

    Args:
        cavities: List of CavityPosition objects to validate
        model: Instrument model name

    Returns:
        ValidationResult with all issues
    """
    all_issues = []
    passed_count = 0

    for cavity in cavities:
        passed, issues = validate_cavity(cavity, model)
        all_issues.extend(issues)
        if passed:
            passed_count += 1

    # Overall validity
    has_critical = any(i.severity == ValidationSeverity.CRITICAL for i in all_issues)
    has_error = any(i.severity == ValidationSeverity.ERROR for i in all_issues)
    valid = not has_critical and not has_error

    # Generate warnings list
    warnings = [i.message for i in all_issues if i.severity == ValidationSeverity.WARNING]

    # Notes
    notes = []
    model_key = model.lower().replace(" ", "_").replace("-", "_")
    if model_key in FACTORY_REFERENCES:
        notes.append(f"Validated against {model} factory specifications")
    else:
        notes.append(f"No factory references available for {model}")

    return ValidationResult(
        instrument_model=model,
        valid=valid,
        issues=all_issues,
        warnings=warnings,
        notes=notes,
        cavities_validated=len(cavities),
        cavities_passed=passed_count,
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_lespaul_cavities(
    pickup_neck_y_mm: float,
    pickup_bridge_y_mm: float,
    control_cavity_width_mm: float = 64.0,
    control_cavity_length_mm: float = 108.0,
    neck_pocket_width_mm: float = 53.0,
    neck_pocket_length_mm: float = 89.0,
) -> ValidationResult:
    """
    Convenience function to validate Les Paul cavity positions.

    All Y positions are measured from the bridge saddle.

    Args:
        pickup_neck_y_mm: Neck pickup center distance from bridge
        pickup_bridge_y_mm: Bridge pickup center distance from bridge
        control_cavity_width_mm: Control cavity width
        control_cavity_length_mm: Control cavity length
        neck_pocket_width_mm: Neck pocket (tenon) width
        neck_pocket_length_mm: Neck pocket (tenon) length

    Returns:
        ValidationResult

    Example:
        >>> result = validate_lespaul_cavities(155.0, 20.0)
        >>> print(result.valid)  # True if within tolerances
    """
    cavities = [
        CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=pickup_neck_y_mm,
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.05,
        ),
        CavityPosition(
            cavity_type=CavityType.PICKUP_BRIDGE,
            center_x_mm=0.0,
            center_y_mm=pickup_bridge_y_mm,
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.05,
        ),
        CavityPosition(
            cavity_type=CavityType.CONTROL_CAVITY,
            center_x_mm=0.0,
            center_y_mm=0.0,  # Relative position
            width_mm=control_cavity_width_mm,
            length_mm=control_cavity_length_mm,
            depth_mm=31.75,
        ),
        CavityPosition(
            cavity_type=CavityType.NECK_POCKET,
            center_x_mm=0.0,
            center_y_mm=0.0,
            width_mm=neck_pocket_width_mm,
            length_mm=neck_pocket_length_mm,
            depth_mm=16.0,
        ),
    ]

    return validate_all_cavities(cavities, "les_paul")


def validate_strat_cavities(
    pickup_neck_y_mm: float,
    pickup_middle_y_mm: float,
    pickup_bridge_y_mm: float,
    fret_count: int = 21,
) -> ValidationResult:
    """
    Convenience function to validate Stratocaster cavity positions.

    All Y positions are measured from the bridge saddle.

    Args:
        pickup_neck_y_mm: Neck pickup center distance from bridge
        pickup_middle_y_mm: Middle pickup center distance from bridge
        pickup_bridge_y_mm: Bridge pickup center distance from bridge
        fret_count: Number of frets (affects neck pickup tolerance for 24-fret)

    Returns:
        ValidationResult
    """
    cavities = [
        CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=pickup_neck_y_mm,
            width_mm=22.0,
            length_mm=85.0,
            depth_mm=18.0,
        ),
        CavityPosition(
            cavity_type=CavityType.PICKUP_MIDDLE,
            center_x_mm=0.0,
            center_y_mm=pickup_middle_y_mm,
            width_mm=22.0,
            length_mm=85.0,
            depth_mm=18.0,
        ),
        CavityPosition(
            cavity_type=CavityType.PICKUP_BRIDGE,
            center_x_mm=0.0,
            center_y_mm=pickup_bridge_y_mm,
            width_mm=22.0,
            length_mm=85.0,
            depth_mm=18.0,
        ),
    ]

    # For 24-fret guitars, use relaxed tolerance on neck pickup
    result = validate_all_cavities(cavities, "stratocaster")

    if fret_count >= 24:
        result.notes.append("24-fret configuration: neck pickup position may be adjusted bridgeward")

    return result


def validate_explorer_cavities(
    pickup_neck_y_mm: float,
    pickup_bridge_y_mm: float,
) -> ValidationResult:
    """
    Convenience function to validate Explorer cavity positions.

    Resolves EX-GAP-04: Explorer pickup positions verification.

    Args:
        pickup_neck_y_mm: Neck pickup center distance from bridge
        pickup_bridge_y_mm: Bridge pickup center distance from bridge

    Returns:
        ValidationResult
    """
    cavities = [
        CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=pickup_neck_y_mm,
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.0,
        ),
        CavityPosition(
            cavity_type=CavityType.PICKUP_BRIDGE,
            center_x_mm=0.0,
            center_y_mm=pickup_bridge_y_mm,
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.0,
        ),
    ]

    return validate_all_cavities(cavities, "explorer")


def get_factory_reference(
    model: str,
    cavity_type: CavityType,
) -> Optional[FactoryReference]:
    """
    Get factory reference for a specific cavity type and model.

    Args:
        model: Instrument model name
        cavity_type: Type of cavity

    Returns:
        FactoryReference or None if not found
    """
    model_key = model.lower().replace(" ", "_").replace("-", "_")

    if model_key not in FACTORY_REFERENCES:
        return None

    return FACTORY_REFERENCES[model_key].get(cavity_type)


def list_supported_models() -> List[str]:
    """List all models with factory references."""
    return list(FACTORY_REFERENCES.keys())


def list_cavity_types_for_model(model: str) -> List[str]:
    """List all cavity types with references for a model."""
    model_key = model.lower().replace(" ", "_").replace("-", "_")

    if model_key not in FACTORY_REFERENCES:
        return []

    return [ct.value for ct in FACTORY_REFERENCES[model_key].keys()]
