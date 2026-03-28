"""Unified Body Generator Dispatcher

Routes body generation requests to the appropriate instrument-specific generator.

Usage:
    from app.generators.body_generator import BodyGenerator

    # From project data (recommended)
    gen = BodyGenerator.from_project(project_data)
    gen.generate("output.nc")

    # Direct instantiation by model
    gen = BodyGenerator.for_model("stratocaster", spec=strat_spec)
    gen.generate("output.nc")

Supported models:
    - stratocaster: StratocasterBodyGenerator (parametric G-code)
    - lespaul: LesPaulBodyGenerator (DXF-based G-code)
    - acoustic/*: AcousticBodyGenerator (outline + G-code)

For outline-only generation (no G-code), use:
    - electric_body_generator.generate_body_outline()
    - acoustic_body_generator.generate_acoustic_outline()
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from pathlib import Path

if TYPE_CHECKING:
    from ..schemas.instrument_project import InstrumentProjectData


# Supported model identifiers
ELECTRIC_MODELS = frozenset({
    "stratocaster", "strat",
    "lespaul", "les_paul", "les-paul",
    "telecaster", "tele",
    "sg",
    "explorer",
    "flying_v", "flyingv",
    "jazzmaster",
    "jaguar",
    "mustang",
    "offset",
})

ACOUSTIC_MODELS = frozenset({
    "dreadnought",
    "om", "orchestra_model",
    "concert",
    "auditorium",
    "jumbo",
    "parlor", "parlour",
    "classical",
    "00", "oo",
    "000", "ooo",
})


class BodyGenerator:
    """Unified dispatcher for instrument body G-code generation.

    This class routes to the appropriate underlying generator based on
    instrument type and model. It provides a consistent interface for
    project-driven CAM generation.
    """

    def __init__(
        self,
        delegate: Any,
        model_id: str,
    ):
        """Internal constructor - use factory methods instead.

        Args:
            delegate: The underlying generator instance
            model_id: Normalized model identifier
        """
        self._delegate = delegate
        self._model_id = model_id

    @classmethod
    def from_project(
        cls,
        project: "InstrumentProjectData",
        machine: str = "txrx_router",
    ) -> "BodyGenerator":
        """Create a BodyGenerator from InstrumentProjectData.

        Routes to the appropriate generator based on project.spec.model_id.

        Args:
            project: InstrumentProjectData with spec and manufacturing_state
            machine: Machine profile name (default: txrx_router)

        Returns:
            BodyGenerator wrapping the appropriate delegate

        Raises:
            ValueError: If project model is not supported or not CAM-ready
        """
        model_id = _extract_model_id(project)
        normalized = _normalize_model_id(model_id)

        if normalized in {"stratocaster", "strat"}:
            from .stratocaster_body_generator import StratocasterBodyGenerator
            delegate = StratocasterBodyGenerator.from_project(project, machine=machine)
            return cls(delegate, "stratocaster")

        elif normalized in {"lespaul", "les_paul", "les-paul"}:
            from .lespaul_body_generator import LesPaulBodyGenerator
            delegate = LesPaulBodyGenerator.from_project(project, machine=machine)
            return cls(delegate, "lespaul")

        elif normalized in ACOUSTIC_MODELS:
            from .acoustic_body_generator import AcousticBodyGenerator
            delegate = AcousticBodyGenerator.from_project(project, machine=machine)
            return cls(delegate, normalized)

        else:
            # Fallback: try Les Paul generator for unknown electric models
            # (it uses DXF templates which may exist for the model)
            from .lespaul_body_generator import LesPaulBodyGenerator
            try:
                delegate = LesPaulBodyGenerator.from_project(project, machine=machine)
                return cls(delegate, normalized)
            except ValueError as e:
                raise ValueError(
                    f"No body generator available for model '{model_id}'. "
                    f"Supported electric: {sorted(ELECTRIC_MODELS)}. "
                    f"Supported acoustic: {sorted(ACOUSTIC_MODELS)}."
                ) from e

    @classmethod
    def for_model(
        cls,
        model_id: str,
        *,
        dxf_path: Optional[str] = None,
        spec: Optional[Any] = None,
        machine: str = "txrx_router",
    ) -> "BodyGenerator":
        """Create a BodyGenerator for a specific model.

        Args:
            model_id: Model identifier (e.g., "stratocaster", "lespaul", "dreadnought")
            dxf_path: Path to DXF file (required for DXF-based generators)
            spec: Model-specific spec object (e.g., StratBodySpec)
            machine: Machine profile name

        Returns:
            BodyGenerator wrapping the appropriate delegate
        """
        normalized = _normalize_model_id(model_id)

        if normalized in {"stratocaster", "strat"}:
            from .stratocaster_body_generator import StratocasterBodyGenerator
            if spec is None:
                from .stratocaster_body_generator import StratBodySpec
                spec = StratBodySpec()
            delegate = StratocasterBodyGenerator(spec, machine=machine)
            return cls(delegate, "stratocaster")

        elif normalized in {"lespaul", "les_paul", "les-paul"}:
            from .lespaul_body_generator import LesPaulBodyGenerator
            if dxf_path is None:
                # Use canonical template
                dxf_path = str(
                    Path(__file__).parent.parent
                    / "instrument_geometry"
                    / "body"
                    / "dxf"
                    / "electric"
                    / "LesPaul_CAM_Closed.dxf"
                )
            delegate = LesPaulBodyGenerator(dxf_path, machine=machine)
            return cls(delegate, "lespaul")

        elif normalized in ACOUSTIC_MODELS:
            from .acoustic_body_generator import AcousticBodyGenerator
            delegate = AcousticBodyGenerator(style=normalized, machine=machine)
            return cls(delegate, normalized)

        else:
            raise ValueError(
                f"Unknown model '{model_id}'. "
                f"Supported electric: {sorted(ELECTRIC_MODELS)}. "
                f"Supported acoustic: {sorted(ACOUSTIC_MODELS)}."
            )

    def generate(
        self,
        output_path: str,
        **kwargs,
    ) -> str:
        """Generate G-code and save to file.

        Args:
            output_path: Path for output .nc file
            **kwargs: Passed to underlying generator

        Returns:
            Path to generated file
        """
        return self._delegate.generate(output_path, **kwargs)

    def get_summary(self) -> Dict[str, Any]:
        """Get generation summary from delegate."""
        if hasattr(self._delegate, "get_summary"):
            return self._delegate.get_summary()
        return {"model_id": self._model_id}

    @property
    def model_id(self) -> str:
        """Normalized model identifier."""
        return self._model_id

    @property
    def delegate(self) -> Any:
        """Underlying generator instance."""
        return self._delegate


def _extract_model_id(project: "InstrumentProjectData") -> str:
    """Extract model_id from project data."""
    if hasattr(project, "spec") and project.spec:
        if hasattr(project.spec, "model_id"):
            return str(project.spec.model_id)
        if hasattr(project.spec, "model"):
            return str(project.spec.model)
    raise ValueError("Project has no spec.model_id")


def _normalize_model_id(model_id: str) -> str:
    """Normalize model_id to canonical form."""
    return model_id.lower().replace("-", "_").replace(" ", "_")


# Convenience re-exports for direct usage
__all__ = [
    "BodyGenerator",
    "ELECTRIC_MODELS",
    "ACOUSTIC_MODELS",
]
