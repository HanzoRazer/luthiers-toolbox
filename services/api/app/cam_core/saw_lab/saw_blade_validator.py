"""
Saw Blade Validator - Safety checks for saw operations.

Validates blade specifications against operation parameters to prevent:
- Blade binding (radius too tight for blade diameter)
- Excessive depth of cut (kerf overload)
- RPM out of safe range (blade manufacturer limits)
- Feed rate too high (chipload safety)
- Kerf vs plate thickness ratio issues

Returns: OK, WARN, or ERROR with human-readable messages.

Integrates with:
- saw_blade_registry.py (CP-S50) for blade specs
- SawSlicePanel.vue for straight cut validation
- SawContourPanel.vue for curved path validation
- SawBatchPanel.vue for multi-operation validation
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel

from .saw_blade_registry import SawBladeSpec, get_registry


# ============================================================================
# Validation Result Types
# ============================================================================

class ValidationLevel(str, Enum):
    """Validation result severity."""
    OK = "OK"           # Safe to proceed
    WARN = "WARN"       # Risky but may be acceptable
    ERROR = "ERROR"     # Unsafe, must not proceed


class ValidationResult(BaseModel):
    """Validation check result."""
    level: ValidationLevel
    message: str
    details: Optional[Dict[str, Any]] = None


class OperationValidation(BaseModel):
    """Complete operation validation result."""
    overall: ValidationLevel
    checks: List[ValidationResult]
    blade: Optional[SawBladeSpec] = None
    safe_to_proceed: bool


# ============================================================================
# Safety Constants
# ============================================================================

class SafetyLimits:
    """Safety thresholds for saw operations."""
    
    # Contour radius limits
    MIN_RADIUS_SAFETY_FACTOR = 1.0  # min_radius = blade_diameter / 2 * factor
    
    # Depth of cut limits (multiplier of kerf)
    DOC_MIN_KERF_MULTIPLE = 1.0     # Minimum DOC = 1× kerf
    DOC_MAX_KERF_MULTIPLE = 10.0    # Maximum DOC = 10× kerf (conservative)
    DOC_WARN_KERF_MULTIPLE = 7.0    # Warning threshold
    
    # RPM limits (typical saw blade ranges)
    RPM_MIN_UNIVERSAL = 2000        # Minimum for most blades
    RPM_MAX_UNIVERSAL = 6000        # Maximum for most blades
    RPM_WARN_HIGH = 5000            # High RPM warning
    
    # Feed rate limits (inches per minute)
    FEED_MIN_IPM = 10.0             # Minimum to avoid burning
    FEED_MAX_IPM = 300.0            # Maximum for safety
    FEED_WARN_HIGH_IPM = 200.0      # High feed warning
    
    # Chipload limits (inches per tooth)
    CHIPLOAD_MIN = 0.001            # Minimum to avoid rubbing
    CHIPLOAD_MAX = 0.020            # Maximum for hardwood
    CHIPLOAD_WARN_HIGH = 0.015      # High chipload warning
    
    # Kerf vs plate thickness
    KERF_PLATE_RATIO_MIN = 1.1      # Kerf should be > plate × 1.1
    KERF_PLATE_RATIO_MAX = 2.0      # Kerf should be < plate × 2.0
    KERF_PLATE_RATIO_WARN = 1.5     # Warning if > plate × 1.5


# ============================================================================
# Validator
# ============================================================================

class SawBladeValidator:
    """Validates saw operations against blade specifications."""
    
    def __init__(self):
        """Initialize validator with registry access."""
        self.registry = get_registry()
        self.limits = SafetyLimits()
    
    # ------------------------------------------------------------------------
    # Main Validation Entry Point
    # ------------------------------------------------------------------------
    
    def validate_operation(
        self,
        blade_id: str,
        operation_type: str,
        doc_mm: Optional[float] = None,
        rpm: Optional[float] = None,
        feed_ipm: Optional[float] = None,
        contour_radius_mm: Optional[float] = None,
        material_family: Optional[str] = None
    ) -> OperationValidation:
        """
        Validate complete operation against blade specs.
        
        Args:
            blade_id: Blade registry ID
            operation_type: "slice", "batch", "contour"
            doc_mm: Depth of cut in mm (optional)
            rpm: Spindle RPM (optional)
            feed_ipm: Feed rate in inches per minute (optional)
            contour_radius_mm: Minimum radius for contours (optional)
            material_family: Material being cut (optional)
            
        Returns:
            OperationValidation with overall status and individual checks
        """
        checks = []
        
        # Get blade from registry
        blade = self.registry.read(blade_id)
        if blade is None:
            return OperationValidation(
                overall=ValidationLevel.ERROR,
                checks=[ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Blade not found in registry: {blade_id}"
                )],
                blade=None,
                safe_to_proceed=False
            )
        
        # Run applicable checks
        if contour_radius_mm is not None:
            checks.append(self._check_contour_radius(blade, contour_radius_mm))
        
        if doc_mm is not None:
            checks.append(self._check_depth_of_cut(blade, doc_mm))
        
        if rpm is not None:
            checks.append(self._check_rpm(blade, rpm))
        
        if feed_ipm is not None and rpm is not None:
            checks.append(self._check_feed_rate(blade, feed_ipm, rpm))
        
        # Blade design check (kerf vs plate ratio)
        checks.append(self._check_blade_design(blade))
        
        # Material compatibility check
        if material_family:
            checks.append(self._check_material_compatibility(blade, material_family))
        
        # Determine overall level
        has_error = any(c.level == ValidationLevel.ERROR for c in checks)
        has_warn = any(c.level == ValidationLevel.WARN for c in checks)
        
        if has_error:
            overall = ValidationLevel.ERROR
        elif has_warn:
            overall = ValidationLevel.WARN
        else:
            overall = ValidationLevel.OK
        
        return OperationValidation(
            overall=overall,
            checks=checks,
            blade=blade,
            safe_to_proceed=(overall != ValidationLevel.ERROR)
        )
    
    # ------------------------------------------------------------------------
    # Individual Validation Checks
    # ------------------------------------------------------------------------
    
    def _check_contour_radius(
        self,
        blade: SawBladeSpec,
        radius_mm: float
    ) -> ValidationResult:
        """
        Check if contour radius is safe for blade diameter.
        
        Rule: min_radius >= blade_diameter / 2
        """
        min_safe_radius = (blade.diameter_mm / 2.0) * self.limits.MIN_RADIUS_SAFETY_FACTOR
        
        if radius_mm < min_safe_radius:
            return ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Contour radius {radius_mm:.1f}mm is too tight for {blade.diameter_mm:.0f}mm blade",
                details={
                    "radius_mm": radius_mm,
                    "min_safe_radius_mm": min_safe_radius,
                    "blade_diameter_mm": blade.diameter_mm,
                    "reason": "Blade will bind in tight curves"
                }
            )
        
        # Warn if close to minimum
        if radius_mm < min_safe_radius * 1.2:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Contour radius {radius_mm:.1f}mm is close to minimum for {blade.diameter_mm:.0f}mm blade",
                details={
                    "radius_mm": radius_mm,
                    "min_safe_radius_mm": min_safe_radius,
                    "recommended_radius_mm": min_safe_radius * 1.5
                }
            )
        
        return ValidationResult(
            level=ValidationLevel.OK,
            message=f"Contour radius {radius_mm:.1f}mm is safe for {blade.diameter_mm:.0f}mm blade"
        )
    
    def _check_depth_of_cut(
        self,
        blade: SawBladeSpec,
        doc_mm: float
    ) -> ValidationResult:
        """
        Check if depth of cut is within safe range.
        
        Rule: kerf × 1 <= DOC <= kerf × 10 (conservative)
        """
        min_doc = blade.kerf_mm * self.limits.DOC_MIN_KERF_MULTIPLE
        max_doc = blade.kerf_mm * self.limits.DOC_MAX_KERF_MULTIPLE
        warn_doc = blade.kerf_mm * self.limits.DOC_WARN_KERF_MULTIPLE
        
        if doc_mm < min_doc:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"DOC {doc_mm:.1f}mm is very shallow (< {min_doc:.1f}mm)",
                details={
                    "doc_mm": doc_mm,
                    "min_doc_mm": min_doc,
                    "kerf_mm": blade.kerf_mm,
                    "reason": "May cause excessive rubbing and heat"
                }
            )
        
        if doc_mm > max_doc:
            return ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"DOC {doc_mm:.1f}mm exceeds safe limit ({max_doc:.1f}mm)",
                details={
                    "doc_mm": doc_mm,
                    "max_doc_mm": max_doc,
                    "kerf_mm": blade.kerf_mm,
                    "reason": "Excessive load on blade, risk of kickback"
                }
            )
        
        if doc_mm > warn_doc:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"DOC {doc_mm:.1f}mm is high (> {warn_doc:.1f}mm recommended)",
                details={
                    "doc_mm": doc_mm,
                    "warn_doc_mm": warn_doc,
                    "max_doc_mm": max_doc,
                    "recommendation": "Consider multiple passes"
                }
            )
        
        return ValidationResult(
            level=ValidationLevel.OK,
            message=f"DOC {doc_mm:.1f}mm is within safe range"
        )
    
    def _check_rpm(
        self,
        blade: SawBladeSpec,
        rpm: float
    ) -> ValidationResult:
        """
        Check if RPM is within safe range.
        
        Uses universal limits + blade-specific recommendations if available.
        """
        # TODO: Add blade-specific RPM limits to SawBladeSpec model
        # For now, use universal limits
        
        if rpm < self.limits.RPM_MIN_UNIVERSAL:
            return ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"RPM {rpm:.0f} is too low (min {self.limits.RPM_MIN_UNIVERSAL})",
                details={
                    "rpm": rpm,
                    "min_rpm": self.limits.RPM_MIN_UNIVERSAL,
                    "reason": "Insufficient cutting speed, risk of burning"
                }
            )
        
        if rpm > self.limits.RPM_MAX_UNIVERSAL:
            return ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"RPM {rpm:.0f} exceeds safe limit (max {self.limits.RPM_MAX_UNIVERSAL})",
                details={
                    "rpm": rpm,
                    "max_rpm": self.limits.RPM_MAX_UNIVERSAL,
                    "reason": "Excessive blade speed, risk of failure"
                }
            )
        
        if rpm > self.limits.RPM_WARN_HIGH:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"RPM {rpm:.0f} is high (> {self.limits.RPM_WARN_HIGH} recommended)",
                details={
                    "rpm": rpm,
                    "warn_rpm": self.limits.RPM_WARN_HIGH,
                    "recommendation": "Verify blade is rated for high RPM"
                }
            )
        
        return ValidationResult(
            level=ValidationLevel.OK,
            message=f"RPM {rpm:.0f} is within safe range"
        )
    
    def _check_feed_rate(
        self,
        blade: SawBladeSpec,
        feed_ipm: float,
        rpm: float
    ) -> ValidationResult:
        """
        Check if feed rate and resulting chipload are safe.
        
        Chipload = feed_ipm / (rpm × teeth)
        """
        # Calculate chipload (inches per tooth)
        chipload = feed_ipm / (rpm * blade.teeth)
        
        # Check absolute feed rate limits
        if feed_ipm < self.limits.FEED_MIN_IPM:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Feed rate {feed_ipm:.1f} IPM is very slow",
                details={
                    "feed_ipm": feed_ipm,
                    "min_feed_ipm": self.limits.FEED_MIN_IPM,
                    "reason": "May cause burning"
                }
            )
        
        if feed_ipm > self.limits.FEED_MAX_IPM:
            return ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Feed rate {feed_ipm:.1f} IPM exceeds safe limit",
                details={
                    "feed_ipm": feed_ipm,
                    "max_feed_ipm": self.limits.FEED_MAX_IPM,
                    "reason": "Risk of kickback"
                }
            )
        
        # Check chipload
        if chipload < self.limits.CHIPLOAD_MIN:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Chipload {chipload:.4f}\" is too low",
                details={
                    "chipload": chipload,
                    "min_chipload": self.limits.CHIPLOAD_MIN,
                    "feed_ipm": feed_ipm,
                    "rpm": rpm,
                    "teeth": blade.teeth,
                    "reason": "Rubbing instead of cutting, will burn wood"
                }
            )
        
        if chipload > self.limits.CHIPLOAD_MAX:
            return ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Chipload {chipload:.4f}\" exceeds safe limit",
                details={
                    "chipload": chipload,
                    "max_chipload": self.limits.CHIPLOAD_MAX,
                    "feed_ipm": feed_ipm,
                    "rpm": rpm,
                    "teeth": blade.teeth,
                    "reason": "Excessive load per tooth, risk of tooth breakage"
                }
            )
        
        if chipload > self.limits.CHIPLOAD_WARN_HIGH:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Chipload {chipload:.4f}\" is high",
                details={
                    "chipload": chipload,
                    "warn_chipload": self.limits.CHIPLOAD_WARN_HIGH,
                    "max_chipload": self.limits.CHIPLOAD_MAX,
                    "recommendation": "Reduce feed rate or increase RPM"
                }
            )
        
        if feed_ipm > self.limits.FEED_WARN_HIGH_IPM:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Feed rate {feed_ipm:.1f} IPM is high (chipload {chipload:.4f}\")",
                details={
                    "feed_ipm": feed_ipm,
                    "chipload": chipload,
                    "recommendation": "Ensure machine can handle this feed rate"
                }
            )
        
        return ValidationResult(
            level=ValidationLevel.OK,
            message=f"Feed rate {feed_ipm:.1f} IPM is safe (chipload {chipload:.4f}\")"
        )
    
    def _check_blade_design(
        self,
        blade: SawBladeSpec
    ) -> ValidationResult:
        """
        Check blade design parameters (kerf vs plate thickness).
        
        Rule: 1.1 < kerf/plate < 2.0
        """
        ratio = blade.kerf_mm / blade.plate_thickness_mm
        
        if ratio < self.limits.KERF_PLATE_RATIO_MIN:
            return ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Kerf/plate ratio {ratio:.2f} is too low",
                details={
                    "ratio": ratio,
                    "min_ratio": self.limits.KERF_PLATE_RATIO_MIN,
                    "kerf_mm": blade.kerf_mm,
                    "plate_mm": blade.plate_thickness_mm,
                    "reason": "Blade may bind in kerf"
                }
            )
        
        if ratio > self.limits.KERF_PLATE_RATIO_MAX:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Kerf/plate ratio {ratio:.2f} is unusually high",
                details={
                    "ratio": ratio,
                    "max_ratio": self.limits.KERF_PLATE_RATIO_MAX,
                    "kerf_mm": blade.kerf_mm,
                    "plate_mm": blade.plate_thickness_mm,
                    "reason": "Excessive kerf width, wasteful"
                }
            )
        
        if ratio > self.limits.KERF_PLATE_RATIO_WARN:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Kerf/plate ratio {ratio:.2f} is high",
                details={
                    "ratio": ratio,
                    "kerf_mm": blade.kerf_mm,
                    "plate_mm": blade.plate_thickness_mm
                }
            )
        
        return ValidationResult(
            level=ValidationLevel.OK,
            message=f"Blade design is good (kerf/plate ratio {ratio:.2f})"
        )
    
    def _check_material_compatibility(
        self,
        blade: SawBladeSpec,
        material_family: str
    ) -> ValidationResult:
        """
        Check if blade is compatible with material.
        
        Uses blade.material_family and blade.application fields.
        """
        # If blade has no material specification, pass
        if not blade.material_family:
            return ValidationResult(
                level=ValidationLevel.OK,
                message="Blade has no material restriction"
            )
        
        # Normalize for comparison
        blade_material = blade.material_family.lower()
        cut_material = material_family.lower()
        
        # Check for mismatch
        if blade_material not in cut_material and cut_material not in blade_material:
            return ValidationResult(
                level=ValidationLevel.WARN,
                message=f"Blade is for {blade.material_family}, cutting {material_family}",
                details={
                    "blade_material": blade.material_family,
                    "cut_material": material_family,
                    "recommendation": "Use blade designed for this material"
                }
            )
        
        return ValidationResult(
            level=ValidationLevel.OK,
            message=f"Blade is compatible with {material_family}"
        )


# ============================================================================
# Singleton Instance
# ============================================================================

_validator_instance = None

def get_validator() -> SawBladeValidator:
    """Get singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = SawBladeValidator()
    return _validator_instance
