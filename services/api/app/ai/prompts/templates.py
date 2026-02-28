"""
AI Prompt Templates - Centralized Prompt Engineering

Provides reusable prompt templates for different AI applications.
Vocabulary merging, parameter injection, and format standardization.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from string import Template


@dataclass
class PromptTemplate:
    """
    A reusable prompt template with variable substitution.

    Example:
        template = PromptTemplate(
            name="rosette",
            system_prompt="You are a rosette design assistant...",
            user_template="Design a rosette with $style style and $rings rings."
        )
        prompt = template.render(style="herringbone", rings=5)
    """
    name: str
    system_prompt: str
    user_template: str
    default_vars: Dict[str, Any] = field(default_factory=dict)

    def render(self, **kwargs) -> str:
        """Render the user template with provided variables."""
        merged = {**self.default_vars, **kwargs}
        return Template(self.user_template).safe_substitute(merged)

    def render_full(self, **kwargs) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) tuple."""
        return (self.system_prompt, self.render(**kwargs))


# ---------------------------------------------------------------------------
# Rosette Design Prompts
# ---------------------------------------------------------------------------

ROSETTE_SYSTEM_PROMPT = """You are an expert luthier specializing in acoustic guitar rosette design.
You understand traditional patterns (herringbone, rope, checkerboard) and modern interpretations.
You generate precise specifications that can be manufactured with CNC or hand tools.

When generating rosette parameters, always output valid JSON with these fields:
- outer_diameter_mm: float (typically 100-120mm)
- inner_diameter_mm: float (typically 20-30mm for soundhole)
- ring_count: int (number of concentric rings)
- rings: array of ring specifications
- pattern_type: string (herringbone, rope, checkerboard, mosaic, custom)
- notes: string (any special instructions)

Each ring in the rings array should have:
- width_mm: float
- pattern: string
- material_primary: string (wood species or color)
- material_secondary: string (optional)
"""

ROSETTE_USER_TEMPLATE = """Design a rosette pattern with the following characteristics:
- Style: $style
- Number of rings: $ring_count
- Outer diameter: $outer_diameter_mm mm
- Inner diameter: $inner_diameter_mm mm
$additional_instructions

Output only valid JSON matching the specification format."""


class RosettePromptBuilder:
    """Builder for rosette design prompts."""

    def __init__(self):
        self.style = "traditional"
        self.ring_count = 3
        self.outer_diameter_mm = 110.0
        self.inner_diameter_mm = 25.0
        self.additional_instructions = ""

    def with_style(self, style: str) -> "RosettePromptBuilder":
        self.style = style
        return self

    def with_rings(self, count: int) -> "RosettePromptBuilder":
        self.ring_count = count
        return self

    def with_diameters(self, outer: float, inner: float) -> "RosettePromptBuilder":
        self.outer_diameter_mm = outer
        self.inner_diameter_mm = inner
        return self

    def with_instructions(self, instructions: str) -> "RosettePromptBuilder":
        self.additional_instructions = instructions
        return self

    def build(self) -> tuple[str, str]:
        """Build (system_prompt, user_prompt) tuple."""
        user_prompt = Template(ROSETTE_USER_TEMPLATE).safe_substitute(
            style=self.style,
            ring_count=self.ring_count,
            outer_diameter_mm=self.outer_diameter_mm,
            inner_diameter_mm=self.inner_diameter_mm,
            additional_instructions=self.additional_instructions,
        )
        return (ROSETTE_SYSTEM_PROMPT, user_prompt)


def build_rosette_prompt(
    style: str = "traditional",
    ring_count: int = 3,
    outer_diameter_mm: float = 110.0,
    inner_diameter_mm: float = 25.0,
    additional_instructions: str = "",
) -> tuple[str, str]:
    """Convenience function to build rosette prompt."""
    return (
        RosettePromptBuilder()
        .with_style(style)
        .with_rings(ring_count)
        .with_diameters(outer_diameter_mm, inner_diameter_mm)
        .with_instructions(additional_instructions)
        .build()
    )


# ---------------------------------------------------------------------------
# CAM Advisor Prompts
# ---------------------------------------------------------------------------

CAM_ADVISOR_SYSTEM_PROMPT = """You are an expert CNC machinist specializing in woodworking operations for guitar building.
You understand feeds, speeds, chipload, heat management, and tool selection for various wood species.

When advising on CAM operations, consider:
- Tool type and diameter
- Wood species and grain orientation
- Feed rate (mm/min)
- Spindle speed (RPM)
- Depth of cut and stepover
- Chip evacuation and heat buildup

Provide specific, actionable recommendations with numerical values.
Flag any safety concerns or potential issues."""

CAM_ADVISOR_USER_TEMPLATE = """Analyze this CNC operation for guitar building:

Tool: $tool_description
Material: $material
Operation: $operation_type
Current Parameters:
- Feed rate: $feed_mm_min mm/min
- Spindle speed: $rpm RPM
- Depth of cut: $depth_mm mm
$additional_context

Provide recommendations for optimal parameters and any warnings."""


class CAMAdvisorPromptBuilder:
    """Builder for CAM advisor prompts."""

    def __init__(self):
        self.tool_description = "1/4\" upcut spiral end mill"
        self.material = "mahogany"
        self.operation_type = "pocket"
        self.feed_mm_min = 1000
        self.rpm = 18000
        self.depth_mm = 3.0
        self.additional_context = ""

    def with_tool(self, description: str) -> "CAMAdvisorPromptBuilder":
        self.tool_description = description
        return self

    def with_material(self, material: str) -> "CAMAdvisorPromptBuilder":
        self.material = material
        return self

    def with_operation(self, op_type: str) -> "CAMAdvisorPromptBuilder":
        self.operation_type = op_type
        return self

    def with_parameters(
        self,
        feed_mm_min: float,
        rpm: int,
        depth_mm: float
    ) -> "CAMAdvisorPromptBuilder":
        self.feed_mm_min = feed_mm_min
        self.rpm = rpm
        self.depth_mm = depth_mm
        return self

    def with_context(self, context: str) -> "CAMAdvisorPromptBuilder":
        self.additional_context = context
        return self

    def build(self) -> tuple[str, str]:
        """Build (system_prompt, user_prompt) tuple."""
        user_prompt = Template(CAM_ADVISOR_USER_TEMPLATE).safe_substitute(
            tool_description=self.tool_description,
            material=self.material,
            operation_type=self.operation_type,
            feed_mm_min=self.feed_mm_min,
            rpm=self.rpm,
            depth_mm=self.depth_mm,
            additional_context=self.additional_context,
        )
        return (CAM_ADVISOR_SYSTEM_PROMPT, user_prompt)


def build_cam_advisor_prompt(
    tool_description: str,
    material: str,
    operation_type: str,
    feed_mm_min: float,
    rpm: int,
    depth_mm: float,
    additional_context: str = "",
) -> tuple[str, str]:
    """Convenience function to build CAM advisor prompt."""
    return (
        CAMAdvisorPromptBuilder()
        .with_tool(tool_description)
        .with_material(material)
        .with_operation(operation_type)
        .with_parameters(feed_mm_min, rpm, depth_mm)
        .with_context(additional_context)
        .build()
    )
