# services/api/app/generators/cam_utils.py
"""
CAM Utilities for Generator Factory Methods (GEN-3)

Shared helpers for creating generator instances from InstrumentProjectData.

See docs/GENERATOR_REMEDIATION_PLAN.md — GEN-3 section.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas.instrument_project import InstrumentProjectData


def _require_cam_ready(project: "InstrumentProjectData") -> None:
    """
    Validate that a project is ready for CAM operations.

    Raises ValueError if project is missing manufacturing_state or is still DRAFT.
    Generators should call this at the start of from_project() to enforce
    the design-complete gate.

    Args:
        project: InstrumentProjectData instance to validate

    Raises:
        ValueError: If project is not CAM-ready
    """
    if not project.manufacturing_state:
        raise ValueError(
            "No manufacturing state. "
            "Set manufacturing_state before generating CAM output."
        )

    status_value = project.manufacturing_state.status.value
    if status_value == "draft":
        raise ValueError(
            "Project is DRAFT. Advance to DESIGN_COMPLETE first. "
            "Use PUT /api/projects/{id}/design-state to update manufacturing_state.status."
        )


def _require_spec(project: "InstrumentProjectData") -> None:
    """
    Validate that a project has an InstrumentSpec.

    Raises ValueError if project.spec is None.

    Args:
        project: InstrumentProjectData instance to validate

    Raises:
        ValueError: If project has no spec
    """
    if project.spec is None:
        raise ValueError(
            "No instrument spec. "
            "Set spec (scale_length_mm, fret_count, etc.) before generating CAM output."
        )


def _require_body_config(project: "InstrumentProjectData") -> None:
    """
    Validate that a project has a BodyConfig.

    Raises ValueError if project.body_config is None.

    Args:
        project: InstrumentProjectData instance to validate

    Raises:
        ValueError: If project has no body_config
    """
    if project.body_config is None:
        raise ValueError(
            "No body config. "
            "Set body_config (pickup_config, tremolo_style, etc.) before generating CAM output."
        )
