"""
Orthotropic material state derived from MaterialEvidenceBundle.

Constructs ``OrthotropicPlate`` inputs explicitly. Never uses
``OrthotropicPlate.from_wood()`` as the default research path — that
method silently estimates G_LC and Poisson reciprocity.

Missing E_C remains absent (incomplete state). Prediction must fail
closed until E_C is OBSERVED/ESTIMATED/etc. via evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.calculators.plate_design.rayleigh_ritz import OrthotropicPlate
from app.governance.confidence_envelope import EpistemicStatus

from .evidence import EvidenceValue, MaterialEvidenceBundle, MaterialEvidenceError

# Softwood literature defaults — ALWAYS serialized as ModelAssumption.
DEFAULT_G_OVER_EL = 0.06
DEFAULT_NU_LC = 0.3


class IncompleteMaterialStateError(MaterialEvidenceError):
    """Required orthotropic inputs are unavailable."""


@dataclass(frozen=True)
class ModelAssumption:
    """Explicit model-input assumption (not an EpistemicStatus)."""

    name: str
    value: float
    unit: str
    rationale: str
    assumption: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlateGeometry:
    """Bounded rectangular plate specimen geometry (SI meters)."""

    thickness_m: float
    length_m: float  # along grain (a)
    width_m: float  # across grain (b)

    def __post_init__(self) -> None:
        if min(self.thickness_m, self.length_m, self.width_m) <= 0:
            raise MaterialEvidenceError("PlateGeometry dimensions must be positive")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thickness_m": self.thickness_m,
            "length_m": self.length_m,
            "width_m": self.width_m,
        }


@dataclass(frozen=True)
class OrthotropicMaterialState:
    """
    Research orthotropic material state.

    ``e_crossgrain_pa`` may be None when evidence does not provide E_C.
    """

    specimen_id: str
    density_kg_m3: float
    e_longitudinal_pa: float
    e_crossgrain_pa: Optional[float]
    g_lc_pa: float
    nu_lc: float
    nu_cl: float
    density_origin: str
    e_longitudinal_origin: str
    e_crossgrain_origin: Optional[str]
    assumptions: Tuple[ModelAssumption, ...] = ()
    research_only: bool = True

    @property
    def is_complete_for_prediction(self) -> bool:
        return self.e_crossgrain_pa is not None and self.e_crossgrain_pa > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specimen_id": self.specimen_id,
            "research_only": self.research_only,
            "density_kg_m3": self.density_kg_m3,
            "density_origin": self.density_origin,
            "E_L_Pa": self.e_longitudinal_pa,
            "E_L_origin": self.e_longitudinal_origin,
            "E_C_Pa": self.e_crossgrain_pa,
            "E_C_origin": self.e_crossgrain_origin,
            "G_LC_Pa": self.g_lc_pa,
            "nu_LC": self.nu_lc,
            "nu_CL": self.nu_cl,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "complete_for_prediction": self.is_complete_for_prediction,
        }

    def to_orthotropic_plate(self, geometry: PlateGeometry) -> OrthotropicPlate:
        """Build OrthotropicPlate with explicit fields only (no from_wood)."""
        if not self.is_complete_for_prediction:
            raise IncompleteMaterialStateError(
                "Cannot build OrthotropicPlate without E_C; "
                "cross-grain stiffness is unavailable (absence ≠ assumed)"
            )
        assert self.e_crossgrain_pa is not None
        return OrthotropicPlate(
            E_L=self.e_longitudinal_pa,
            E_C=self.e_crossgrain_pa,
            G_LC=self.g_lc_pa,
            nu_LC=self.nu_lc,
            nu_CL=self.nu_cl,
            rho=self.density_kg_m3,
            h=geometry.thickness_m,
            a=geometry.length_m,
            b=geometry.width_m,
        )

    @classmethod
    def from_evidence(
        cls,
        bundle: MaterialEvidenceBundle,
        *,
        g_lc_pa: Optional[float] = None,
        nu_lc: Optional[float] = None,
        nu_cl: Optional[float] = None,
    ) -> "OrthotropicMaterialState":
        density = bundle.get("density_kg_m3")
        e_l = bundle.get("E_L_Pa")
        e_c = bundle.get("E_C_Pa")

        if density is None:
            raise IncompleteMaterialStateError("density_kg_m3 evidence is required")
        if e_l is None:
            raise IncompleteMaterialStateError("E_L_Pa evidence is required")

        assumptions: List[ModelAssumption] = []

        e_c_value: Optional[float] = e_c.value if e_c is not None else None
        e_c_origin: Optional[str] = e_c.epistemic_status if e_c is not None else None

        if g_lc_pa is None:
            g_ev = bundle.get("G_LC_Pa")
            if g_ev is not None:
                g_lc_pa = g_ev.value
            else:
                g_lc_pa = DEFAULT_G_OVER_EL * e_l.value
                assumptions.append(
                    ModelAssumption(
                        name="G_LC_Pa",
                        value=g_lc_pa,
                        unit="Pa",
                        rationale=f"DEFAULT_G_OVER_EL={DEFAULT_G_OVER_EL} × E_L (not evidence)",
                    )
                )

        if nu_lc is None:
            nu_ev = bundle.get("nu_LC")
            if nu_ev is not None:
                nu_lc = nu_ev.value
            else:
                nu_lc = DEFAULT_NU_LC
                assumptions.append(
                    ModelAssumption(
                        name="nu_LC",
                        value=nu_lc,
                        unit="1",
                        rationale=f"DEFAULT_NU_LC={DEFAULT_NU_LC} (not evidence)",
                    )
                )

        if nu_cl is None:
            nu_cl_ev = bundle.get("nu_CL")
            if nu_cl_ev is not None:
                nu_cl = nu_cl_ev.value
            elif e_c_value is None:
                # Reciprocity needs E_C; leave placeholder 0 and note incompleteness.
                nu_cl = 0.0
                assumptions.append(
                    ModelAssumption(
                        name="nu_CL",
                        value=0.0,
                        unit="1",
                        rationale="Unavailable until E_C is present (reciprocity deferred)",
                    )
                )
            else:
                nu_cl = nu_lc * e_c_value / e_l.value
                assumptions.append(
                    ModelAssumption(
                        name="nu_CL",
                        value=nu_cl,
                        unit="1",
                        rationale="Reciprocity nu_CL = nu_LC × E_C / E_L (not measured)",
                    )
                )

        return cls(
            specimen_id=bundle.specimen_id,
            density_kg_m3=density.value,
            e_longitudinal_pa=e_l.value,
            e_crossgrain_pa=e_c_value,
            g_lc_pa=float(g_lc_pa),
            nu_lc=float(nu_lc),
            nu_cl=float(nu_cl),
            density_origin=density.epistemic_status,
            e_longitudinal_origin=e_l.epistemic_status,
            e_crossgrain_origin=e_c_origin,
            assumptions=tuple(assumptions),
            research_only=True,
        )
