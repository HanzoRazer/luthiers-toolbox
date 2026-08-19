"""
Orthotropic material state derived from MaterialEvidenceBundle.

Constructs ``OrthotropicPlate`` inputs explicitly. Never uses
``OrthotropicPlate.from_wood()`` as the default research path — that
method silently estimates G_LC and Poisson reciprocity.

Missing E_C remains absent (incomplete state). Prediction must fail
closed until E_C is OBSERVED/ESTIMATED/etc. via evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.calculators.plate_design.rayleigh_ritz import OrthotropicPlate

from .evidence import MaterialEvidenceBundle, MaterialEvidenceError

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


def _override_assumptions(
    g_lc_pa: Optional[float], nu_lc: Optional[float], nu_cl: Optional[float]
) -> List[ModelAssumption]:
    """
    Record caller-supplied overrides as assumptions.

    An override bypasses both evidence and the literature defaults. If it did
    not appear in ``assumptions`` it would be indistinguishable from measured
    evidence in the serialized state — the exact silent-authority failure this
    package exists to prevent.
    """
    out: List[ModelAssumption] = []
    for name, override, unit in (
        ("G_LC_Pa", g_lc_pa, "Pa"),
        ("nu_LC", nu_lc, "1"),
        ("nu_CL", nu_cl, "1"),
    ):
        if override is not None:
            out.append(
                ModelAssumption(
                    name=name,
                    value=float(override),
                    unit=unit,
                    rationale="Caller-supplied override (not evidence, not a default)",
                )
            )
    return out


def _from_evidence_or_default(
    bundle: MaterialEvidenceBundle,
    property_name: str,
    default_value: float,
    unit: str,
    rationale: str,
    assumptions: List[ModelAssumption],
) -> float:
    """Prefer evidence; fall back to the literature default, recorded as an assumption."""
    found = bundle.get(property_name)
    if found is not None:
        return float(found.value)
    assumptions.append(
        ModelAssumption(
            name=property_name, value=default_value, unit=unit, rationale=rationale
        )
    )
    return default_value


@dataclass(frozen=True)
class OrthotropicMaterialState:
    """
    Research orthotropic material state.

    ``e_crossgrain_pa`` may be None when evidence does not provide E_C.

    ``nu_cl`` is likewise Optional: Poisson reciprocity is nu_LC x E_C / E_L, so
    without E_C the value is *unknown*, not zero. Serializing a placeholder 0.0
    would publish "we know nu_CL and it is zero", which is a different and
    false claim. Absence is the honest encoding, matching how the evidence
    layer represents UNKNOWN.
    """

    specimen_id: str
    density_kg_m3: float
    e_longitudinal_pa: float
    e_crossgrain_pa: Optional[float]
    g_lc_pa: float
    nu_lc: float
    nu_cl: Optional[float]
    density_origin: str
    e_longitudinal_origin: str
    e_crossgrain_origin: Optional[str]
    assumptions: Tuple[ModelAssumption, ...] = ()
    research_only: bool = True

    @property
    def is_complete_for_prediction(self) -> bool:
        return self.e_crossgrain_pa is not None and self.e_crossgrain_pa > 0

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
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
            "assumptions": [a.to_dict() for a in self.assumptions],
            "complete_for_prediction": self.is_complete_for_prediction,
        }
        # Omitted rather than zero-filled when reciprocity is unavailable.
        if self.nu_cl is not None:
            out["nu_CL"] = self.nu_cl
        return out

    def to_orthotropic_plate(self, geometry: PlateGeometry) -> OrthotropicPlate:
        """Build OrthotropicPlate with explicit fields only (no from_wood)."""
        if not self.is_complete_for_prediction:
            raise IncompleteMaterialStateError(
                "Cannot build OrthotropicPlate without E_C; "
                "cross-grain stiffness is unavailable (absence ≠ assumed)"
            )
        if self.nu_cl is None:
            raise IncompleteMaterialStateError(
                "Cannot build OrthotropicPlate without nu_CL; Poisson reciprocity "
                "is undefined while E_C is absent"
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

        assumptions.extend(_override_assumptions(g_lc_pa, nu_lc, nu_cl))

        e_c_value: Optional[float] = e_c.value if e_c is not None else None
        e_c_origin: Optional[str] = e_c.epistemic_status if e_c is not None else None

        if g_lc_pa is None:
            g_lc_pa = _from_evidence_or_default(
                bundle,
                "G_LC_Pa",
                DEFAULT_G_OVER_EL * e_l.value,
                "Pa",
                f"DEFAULT_G_OVER_EL={DEFAULT_G_OVER_EL} × E_L (not evidence)",
                assumptions,
            )

        if nu_lc is None:
            nu_lc = _from_evidence_or_default(
                bundle,
                "nu_LC",
                DEFAULT_NU_LC,
                "1",
                f"DEFAULT_NU_LC={DEFAULT_NU_LC} (not evidence)",
                assumptions,
            )

        if nu_cl is None:
            nu_cl_ev = bundle.get("nu_CL")
            if nu_cl_ev is not None:
                nu_cl = nu_cl_ev.value
            elif e_c_value is None:
                # Reciprocity needs E_C. Leave nu_CL ABSENT rather than 0.0 —
                # a placeholder number would be serialized as a known value.
                nu_cl = None
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
            nu_cl=None if nu_cl is None else float(nu_cl),
            density_origin=density.epistemic_status,
            e_longitudinal_origin=e_l.epistemic_status,
            e_crossgrain_origin=e_c_origin,
            assumptions=tuple(assumptions),
            research_only=True,
        )
