"""
G-Code Explainer 2.0 (Wave 11)

Reads a G-code file line-by-line and annotates:
- motion type (rapid, cut)
- Z height analysis (safe or dangerous)
- feed rate changes
- potential collisions
- missing retracts
- unsafe RPM/feed combos for material

Stub-level for Wave 11, expandable in Wave 12.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .models import GCodeExplanation, GCodeExplainerResult


class GCodeExplainer:
    """
    Explains G-code line-by-line with risk annotations.
    """

    # G-code command patterns
    GCODE_PATTERNS = {
        "G0": ("Rapid move (non-cutting)", None),
        "G00": ("Rapid move (non-cutting)", None),
        "G1": ("Linear cutting move", None),
        "G01": ("Linear cutting move", None),
        "G2": ("Clockwise arc", None),
        "G02": ("Clockwise arc", None),
        "G3": ("Counter-clockwise arc", None),
        "G03": ("Counter-clockwise arc", None),
        "G17": ("XY plane selection", None),
        "G18": ("XZ plane selection", None),
        "G19": ("YZ plane selection", None),
        "G20": ("Units: Inches", None),
        "G21": ("Units: Millimeters", None),
        "G28": ("Return to home position", None),
        "G40": ("Cutter compensation OFF", None),
        "G41": ("Cutter compensation LEFT", None),
        "G42": ("Cutter compensation RIGHT", None),
        "G43": ("Tool length compensation ON", None),
        "G49": ("Tool length compensation OFF", None),
        "G54": ("Work coordinate system 1", None),
        "G55": ("Work coordinate system 2", None),
        "G80": ("Cancel canned cycle", None),
        "G81": ("Drilling cycle", None),
        "G83": ("Peck drilling cycle", None),
        "G90": ("Absolute positioning mode", None),
        "G91": ("Incremental positioning mode", None),
        "M0": ("Program stop (wait for operator)", None),
        "M1": ("Optional program stop", None),
        "M2": ("Program end", None),
        "M3": ("Spindle ON (clockwise)", None),
        "M03": ("Spindle ON (clockwise)", None),
        "M4": ("Spindle ON (counter-clockwise)", None),
        "M04": ("Spindle ON (counter-clockwise)", None),
        "M5": ("Spindle OFF", None),
        "M05": ("Spindle OFF", None),
        "M6": ("Tool change", None),
        "M06": ("Tool change", None),
        "M8": ("Coolant ON", None),
        "M08": ("Coolant ON", None),
        "M9": ("Coolant OFF", None),
        "M09": ("Coolant OFF", None),
        "M30": ("Program end and reset", None),
    }

    def __init__(self, safe_z: float = 5.0):
        """
        Initialize explainer.
        
        Args:
            safe_z: Z height considered safe (mm above work)
        """
        self.safe_z = safe_z

    def explain_gcode(self, gcode_text: str) -> GCodeExplainerResult:
        """
        Explain G-code line by line.
        
        Args:
            gcode_text: Raw G-code text
        
        Returns:
            GCodeExplainerResult with explanations and overall risk
        """
        explanations: List[GCodeExplanation] = []
        overall_risk = "low"
        high_risk_count = 0
        medium_risk_count = 0

        current_z: Optional[float] = None
        current_feed: Optional[float] = None
        spindle_on = False

        for i, raw in enumerate(gcode_text.splitlines(), start=1):
            raw_stripped = raw.strip()
            
            # Skip empty lines and comments
            if not raw_stripped or raw_stripped.startswith("(") or raw_stripped.startswith(";"):
                explanation = "Comment or empty line"
                risk = None
            else:
                explanation, risk = self._explain_line(
                    raw_stripped,
                    current_z,
                    current_feed,
                    spindle_on,
                )
                
                # Track state changes
                z_match = re.search(r'Z([-+]?\d*\.?\d+)', raw_stripped, re.IGNORECASE)
                if z_match:
                    current_z = float(z_match.group(1))
                
                f_match = re.search(r'F([-+]?\d*\.?\d+)', raw_stripped, re.IGNORECASE)
                if f_match:
                    current_feed = float(f_match.group(1))
                
                if re.search(r'M0?3\b', raw_stripped, re.IGNORECASE):
                    spindle_on = True
                if re.search(r'M0?5\b', raw_stripped, re.IGNORECASE):
                    spindle_on = False

                # Count risks
                if risk == "high":
                    high_risk_count += 1
                elif risk == "medium":
                    medium_risk_count += 1

            explanations.append(
                GCodeExplanation(
                    line_number=i,
                    raw=raw,
                    explanation=explanation,
                    risk=risk,
                )
            )

        # Determine overall risk
        if high_risk_count > 0:
            overall_risk = "high"
        elif medium_risk_count > 2:
            overall_risk = "medium"

        return GCodeExplainerResult(
            explanations=explanations,
            overall_risk=overall_risk,
        )

    def _explain_line(
        self,
        line: str,
        current_z: Optional[float],
        current_feed: Optional[float],
        spindle_on: bool,
    ) -> Tuple[str, Optional[str]]:
        """
        Explain a single G-code line.
        
        Returns:
            Tuple of (explanation, risk_level)
        """
        line_upper = line.upper()
        explanation_parts = []
        risk = None

        # Check for known commands
        for code, (desc, _) in self.GCODE_PATTERNS.items():
            if re.search(rf'\b{code}\b', line_upper):
                explanation_parts.append(desc)

        # Extract coordinate values
        coords = []
        for axis in ['X', 'Y', 'Z']:
            match = re.search(rf'{axis}([-+]?\d*\.?\d+)', line_upper)
            if match:
                val = float(match.group(1))
                coords.append(f"{axis}={val}")
                
                # Z-height risk analysis
                if axis == 'Z':
                    if val < -10:
                        risk = "high"
                        explanation_parts.append(f"DEEP CUT at Z={val}mm")
                    elif val < 0 and not spindle_on:
                        risk = "medium"
                        explanation_parts.append("Moving below Z=0 with spindle OFF")

        # Feed rate
        f_match = re.search(r'F([-+]?\d*\.?\d+)', line_upper)
        if f_match:
            feed = float(f_match.group(1))
            coords.append(f"F={feed}")
            if feed < 100:
                risk = risk or "medium"
                explanation_parts.append("Very slow feed rate")
            elif feed > 5000:
                risk = risk or "medium"
                explanation_parts.append("Very high feed rate")

        # Spindle speed
        s_match = re.search(r'S(\d+)', line_upper)
        if s_match:
            rpm = int(s_match.group(1))
            coords.append(f"S={rpm}")
            if rpm > 30000:
                risk = risk or "medium"
                explanation_parts.append("Very high RPM")

        # Tool number
        t_match = re.search(r'T(\d+)', line_upper)
        if t_match:
            tool = int(t_match.group(1))
            explanation_parts.append(f"Tool {tool}")

        # Build final explanation
        if coords:
            explanation_parts.append(f"[{', '.join(coords)}]")

        if not explanation_parts:
            explanation_parts.append("Unknown or custom command")

        return " — ".join(explanation_parts), risk


def explain_gcode(gcode_text: str, safe_z: float = 5.0) -> GCodeExplainerResult:
    """
    Convenience function to explain G-code.
    
    Args:
        gcode_text: Raw G-code text
        safe_z: Z height considered safe
    
    Returns:
        GCodeExplainerResult
    """
    explainer = GCodeExplainer(safe_z=safe_z)
    return explainer.explain_gcode(gcode_text)
