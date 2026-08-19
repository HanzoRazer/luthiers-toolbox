"""
ToolBox-local material evidence contracts (MESH-MAT-001).

Artifact-based ingestion only — no tap_tone / Analyzer runtime imports.
Epistemic vocabulary follows ADR-0012 via ``EpistemicStatus``.

UNKNOWN is represented as *absence* of an evidence value, not as a
primary epistemic authority state on a populated field.
ASSUMED model inputs are tracked separately as ``ModelAssumption``
(see ``orthotropic.py``), not as EpistemicStatus members.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence

from app.governance.confidence_envelope import EpistemicStatus

# ADR-0012 primary categories allowed on populated EvidenceValue fields.
ALLOWED_EVIDENCE_EPISTEMIC: frozenset[str] = frozenset(
    {
        EpistemicStatus.OBSERVED.value,
        EpistemicStatus.DERIVED.value,
        EpistemicStatus.ESTIMATED.value,
        EpistemicStatus.PREDICTED.value,
        EpistemicStatus.HEURISTIC.value,
        EpistemicStatus.OPERATOR_ANNOTATED.value,
        EpistemicStatus.EXTERNALLY_SOURCED.value,
    }
)

# Canonical SI units after normalization.
_UNIT_ALIASES: Dict[str, str] = {
    "pa": "Pa",
    "pascal": "Pa",
    "gpa": "GPa",
    "mpa": "MPa",
    "kg/m3": "kg/m3",
    "kg/m^3": "kg/m3",
    "kg_m3": "kg/m3",
    "hz": "Hz",
    "mm": "mm",
    "m": "m",
}


class MaterialEvidenceError(ValueError):
    """Raised when material evidence fails validation."""


@dataclass(frozen=True)
class UncertaintyDescriptor:
    """Optional uncertainty attached to an evidence value."""

    std_dev: Optional[float] = None
    relative: Optional[float] = None  # fraction (0.05 = 5%)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass(frozen=True)
class MeasurementReference:
    """Pointer to an upstream artifact that supplied evidence."""

    source_artifact_id: Optional[str] = None
    source_hash: Optional[str] = None
    method: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass(frozen=True)
class EvidenceValue:
    """
    A single typed evidence field with ADR-0012 epistemic status.

    ``epistemic_status`` must be one of ALLOWED_EVIDENCE_EPISTEMIC.
    OBSERVED / DERIVED values that claim measurement authority require
    provenance references (source_artifact_id or source_hash).
    """

    property: str
    value: float
    unit: str
    epistemic_status: str
    uncertainty: Optional[UncertaintyDescriptor] = None
    source_artifact_id: Optional[str] = None
    source_hash: Optional[str] = None
    method: Optional[str] = None

    def __post_init__(self) -> None:
        status = str(self.epistemic_status).strip().lower()
        object.__setattr__(self, "epistemic_status", status)
        if status not in ALLOWED_EVIDENCE_EPISTEMIC:
            raise MaterialEvidenceError(
                f"Unsupported epistemic_status {self.epistemic_status!r} "
                f"for property {self.property!r}; allowed={sorted(ALLOWED_EVIDENCE_EPISTEMIC)}"
            )
        if status in {
            EpistemicStatus.OBSERVED.value,
            EpistemicStatus.DERIVED.value,
        } and not (self.source_artifact_id or self.source_hash):
            raise MaterialEvidenceError(
                f"Property {self.property!r} with epistemic_status={status!r} "
                "requires source_artifact_id or source_hash (no silent provenance)"
            )
        if self.value != self.value:  # NaN
            raise MaterialEvidenceError(f"Property {self.property!r} value is NaN")

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "property": self.property,
            "value": self.value,
            "unit": self.unit,
            "epistemic_status": self.epistemic_status,
        }
        if self.uncertainty is not None:
            out["uncertainty"] = self.uncertainty.to_dict()
        if self.source_artifact_id is not None:
            out["source_artifact_id"] = self.source_artifact_id
        if self.source_hash is not None:
            out["source_hash"] = self.source_hash
        if self.method is not None:
            out["method"] = self.method
        return out


@dataclass(frozen=True)
class ModalEvidence:
    """Measured modal peak supplied with the evidence bundle."""

    frequency_hz: float
    mode_indices: Optional[tuple[int, int]] = None
    q_factor: Optional[float] = None
    epistemic_status: str = EpistemicStatus.OBSERVED.value
    label: Optional[str] = None

    def __post_init__(self) -> None:
        status = str(self.epistemic_status).strip().lower()
        object.__setattr__(self, "epistemic_status", status)
        if status not in ALLOWED_EVIDENCE_EPISTEMIC:
            raise MaterialEvidenceError(
                f"Unsupported modal epistemic_status {self.epistemic_status!r}"
            )
        if self.frequency_hz <= 0:
            raise MaterialEvidenceError("modal frequency_hz must be positive")

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "frequency_hz": self.frequency_hz,
            "epistemic_status": self.epistemic_status,
        }
        if self.mode_indices is not None:
            out["mode_indices"] = list(self.mode_indices)
        if self.q_factor is not None:
            out["q_factor"] = self.q_factor
        if self.label is not None:
            out["label"] = self.label
        return out


@dataclass(frozen=True)
class MaterialEvidenceBundle:
    """
    ToolBox-local material evidence envelope.

    Designed so a future DO-103 Stage 3 / Tap Tone adapter can map into
    this structure without changing the internal representation.
    """

    specimen_id: str
    values: tuple[EvidenceValue, ...]
    modal_evidence: tuple[ModalEvidence, ...] = ()
    environment: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    schema_id: str = "material_evidence"
    schema_version: str = "1.0"
    research_only: bool = True

    def get(self, property_name: str) -> Optional[EvidenceValue]:
        for item in self.values:
            if item.property == property_name:
                return item
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "research_only": self.research_only,
            "specimen_id": self.specimen_id,
            "values": [v.to_dict() for v in self.values],
            "modal_evidence": [m.to_dict() for m in self.modal_evidence],
            "environment": dict(self.environment),
            "provenance": dict(self.provenance),
        }


def normalize_unit(unit: str) -> str:
    key = unit.strip().lower().replace(" ", "")
    if key not in _UNIT_ALIASES:
        raise MaterialEvidenceError(f"Unsupported unit {unit!r}")
    return _UNIT_ALIASES[key]


def canonicalize_stiffness_pa(value: float, unit: str) -> float:
    """Normalize stiffness to Pa."""
    u = normalize_unit(unit)
    if u == "Pa":
        return float(value)
    if u == "MPa":
        return float(value) * 1.0e6
    if u == "GPa":
        return float(value) * 1.0e9
    raise MaterialEvidenceError(f"Unit {unit!r} is not a stiffness unit")


def canonicalize_density_kg_m3(value: float, unit: str) -> float:
    u = normalize_unit(unit)
    if u != "kg/m3":
        raise MaterialEvidenceError(f"Unit {unit!r} is not a density unit")
    return float(value)


def _parse_uncertainty(raw: Any) -> Optional[UncertaintyDescriptor]:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise MaterialEvidenceError("uncertainty must be an object")
    return UncertaintyDescriptor(
        std_dev=_optional_float(raw.get("std_dev")),
        relative=_optional_float(raw.get("relative")),
        notes=raw.get("notes"),
    )


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _parse_evidence_value(raw: Mapping[str, Any]) -> EvidenceValue:
    if "property" not in raw or "value" not in raw or "unit" not in raw:
        raise MaterialEvidenceError("Evidence value requires property, value, unit")
    if "epistemic_status" not in raw:
        raise MaterialEvidenceError(
            f"Evidence value {raw.get('property')!r} missing epistemic_status"
        )
    prop = str(raw["property"])
    unit = normalize_unit(str(raw["unit"]))
    value = float(raw["value"])

    # Canonicalize known material properties to SI.
    if prop in {"E_L", "E_C", "E_L_Pa", "E_C_Pa", "G_LC", "G_LC_Pa"}:
        if prop in {"E_L", "E_C", "G_LC"}:
            # Keep property names stable; store SI Pa.
            value = canonicalize_stiffness_pa(value, unit)
            unit = "Pa"
            if prop == "E_L":
                prop = "E_L_Pa"
            elif prop == "E_C":
                prop = "E_C_Pa"
            elif prop == "G_LC":
                prop = "G_LC_Pa"
        else:
            value = canonicalize_stiffness_pa(value, unit)
            unit = "Pa"
    elif prop in {"density", "density_kg_m3", "rho"}:
        value = canonicalize_density_kg_m3(value, unit)
        unit = "kg/m3"
        prop = "density_kg_m3"

    return EvidenceValue(
        property=prop,
        value=value,
        unit=unit,
        epistemic_status=str(raw["epistemic_status"]),
        uncertainty=_parse_uncertainty(raw.get("uncertainty")),
        source_artifact_id=raw.get("source_artifact_id"),
        source_hash=raw.get("source_hash"),
        method=raw.get("method"),
    )


def _parse_modal(raw: Mapping[str, Any]) -> ModalEvidence:
    indices = raw.get("mode_indices")
    mode_indices: Optional[tuple[int, int]] = None
    if indices is not None:
        if not isinstance(indices, Sequence) or len(indices) != 2:
            raise MaterialEvidenceError("mode_indices must be [m, n]")
        mode_indices = (int(indices[0]), int(indices[1]))
    return ModalEvidence(
        frequency_hz=float(raw["frequency_hz"]),
        mode_indices=mode_indices,
        q_factor=_optional_float(raw.get("q_factor")),
        epistemic_status=str(raw.get("epistemic_status", EpistemicStatus.OBSERVED.value)),
        label=raw.get("label"),
    )


def _require_specimen_id(payload: Mapping[str, Any]) -> str:
    specimen_id = payload.get("specimen_id")
    if not specimen_id or not isinstance(specimen_id, str):
        raise MaterialEvidenceError("specimen_id is required")
    return specimen_id


def _is_json_array(value: Any) -> bool:
    """JSON arrays only. ``str``/``bytes`` are Sequences but are not arrays."""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _parse_values(raw_values: Any) -> tuple[EvidenceValue, ...]:
    if not _is_json_array(raw_values) or not raw_values:
        raise MaterialEvidenceError("values must be a non-empty list")
    values = tuple(_parse_evidence_value(v) for v in raw_values)
    _reject_duplicate_properties(values)
    return values


def _reject_duplicate_properties(values: Sequence[EvidenceValue]) -> None:
    """
    One evidence entry per property.

    ``MaterialEvidenceBundle.get()`` returns the first match, so a duplicate is
    silently order-dependent — the later value would be ignored without a word.
    Canonicalization makes this easy to hit by accident: ``E_L`` (GPa) and
    ``E_L_Pa`` (Pa) both normalize to ``E_L_Pa``, so a bundle carrying both
    would quietly keep whichever came first in the payload.
    """
    seen: Dict[str, int] = {}
    for item in values:
        if item.property in seen:
            raise MaterialEvidenceError(
                f"Duplicate evidence for property {item.property!r}; "
                "one value per property (note that E_L/E_C/G_LC/density "
                "canonicalize onto their _Pa / _kg_m3 names)"
            )
        seen[item.property] = 1


def _parse_modes(raw_modes: Any) -> tuple[ModalEvidence, ...]:
    if raw_modes is None:
        return ()
    if not _is_json_array(raw_modes):
        raise MaterialEvidenceError("modal_evidence must be a list")
    return tuple(_parse_modal(m) for m in raw_modes)


def _parse_context(payload: Mapping[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    environment = payload.get("environment") or {}
    provenance = payload.get("provenance") or {}
    if not isinstance(environment, Mapping) or not isinstance(provenance, Mapping):
        raise MaterialEvidenceError("environment and provenance must be objects")

    # Hard rule: no caller-supplied HARDWARE=true authority flag.
    if provenance.get("HARDWARE") is True or provenance.get("hardware") is True:
        raise MaterialEvidenceError(
            "Caller-supplied HARDWARE=true is forbidden; "
            "hardware provenance belongs to DO-103 Stage 3 adapters"
        )
    return dict(environment), dict(provenance)


def _require_research_only(payload: Mapping[str, Any]) -> bool:
    """
    ``research_only`` is constitutional for this surface, not a caller preference.

    Absent means True. Present means it must *be* True — accepting False would
    let a payload mint a non-research bundle from a package whose entire premise
    is that it carries no CAM or manufacturing authority.
    """
    if "research_only" not in payload:
        return True
    if payload["research_only"] is not True:
        raise MaterialEvidenceError(
            "research_only must be true or omitted; MESH-MAT-001 evidence carries "
            "no CAM authority and cannot be downgraded out of research posture"
        )
    return True


def import_material_evidence(payload: Mapping[str, Any]) -> MaterialEvidenceBundle:
    """
    Validate and import a ToolBox-local material evidence envelope.

    Accepts fixture / adapter dicts. Does not import Analyzer runtime.
    """
    if not isinstance(payload, Mapping):
        raise MaterialEvidenceError("payload must be a mapping")

    environment, provenance = _parse_context(payload)
    return MaterialEvidenceBundle(
        specimen_id=_require_specimen_id(payload),
        values=_parse_values(payload.get("values")),
        modal_evidence=_parse_modes(payload.get("modal_evidence")),
        environment=environment,
        provenance=provenance,
        research_only=_require_research_only(payload),
    )
