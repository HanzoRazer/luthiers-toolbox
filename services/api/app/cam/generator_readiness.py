# services/api/app/cam/generator_readiness.py
"""Generator readiness -- the middle authority layer for manufacturing G-code.

Three separate questions govern manufacturing output. They are deliberately NOT
collapsed into one mechanism::

    SOURCE / ASSET AUTHORITY   may this source asset be manufactured from?
                               -> instrument_geometry.dxf_authority (PR #380),
                                  keyed on a DXF path. Unchanged by this module.
            |
    GENERATOR READINESS        is this generator qualified to emit manufacturing
                               G-code at all?   <-- THIS MODULE
            |
    OPERATION PREFLIGHT        is this particular emitted program physically
                               valid?  -> not built. An implementation precedent
                                  already exists, untouched and unwired, at
                                  ``app/cam/flying_v/depth_validator.py``.
            |
    G-CODE EMISSION

Why a separate layer at all: ``require_manufacturing_authority(path)`` resolves a
**DXF asset**. The Stratocaster, Flying V and neck routes present no DXF path, so
they are structurally outside it. That is a scope boundary, not an oversight, and
widening the asset gate to cover them would distort the substrate merged by #380.

**This registry contains no qualifying state.** There is deliberately no ``READY``
or ``QUALIFIED`` member: nothing here can authorize manufacturing. It can only
decline to authorize, or defer to the asset layer. Granting readiness is a
separate, evidence-backed decision that has not been made for any route.

Evidence: ``LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md``, audited read-only against
``origin/main`` ``c7523677``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple

__all__ = [
    "GeneratorReadiness",
    "GeneratorReadinessRecord",
    "GeneratorReadinessBlocked",
    "GENERATOR_READINESS",
    "resolve_generator_readiness",
    "require_generator_readiness",
]


class GeneratorReadiness(str, Enum):
    """Readiness states. None of these authorizes manufacturing."""

    #: Witnessed defects capable of damaging stock. Must not emit.
    BLOCKED = "BLOCKED"

    #: Repository evidence is insufficient to qualify this generator. This is
    #: explicitly NOT an authorization -- absence of a finding is not a pass.
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

    #: Emission for this route is governed upstream by the asset-authority layer
    #: (#380). This layer defers so that the asset gate produces its own,
    #: unchanged refusal.
    GOVERNED_BY_ASSET_AUTHORITY = "GOVERNED_BY_ASSET_AUTHORITY"

    #: No record exists for the route. Fail closed -- an omitted or renamed
    #: record must never read as authorization.
    UNKNOWN = "UNKNOWN"


#: States that stop emission at this layer. UNKNOWN is here so that deleting or
#: renaming a record fails closed rather than silently opening a route.
_STOPS_EMISSION = frozenset({GeneratorReadiness.BLOCKED, GeneratorReadiness.UNKNOWN})


@dataclass(frozen=True)
class GeneratorReadinessRecord:
    """A declared readiness state for one manufacturing route."""

    route: str
    readiness: GeneratorReadiness
    reason: str
    exit_condition: str
    evidence: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def permits_emission(self) -> bool:
        """True only when this layer does not itself stop emission.

        This is never an authorization: a route may pass this layer and still be
        refused downstream by asset authority.
        """
        return self.readiness not in _STOPS_EMISSION

    def as_detail(self) -> Dict[str, Any]:
        """Client-facing refusal body. Carries no filesystem paths."""
        return {
            "code": "GENERATOR_READINESS_BLOCKED",
            "route": self.route,
            "generator_readiness": self.readiness.value,
            "reason": self.reason,
            "evidence": list(self.evidence),
            "exit_condition": self.exit_condition,
        }


class GeneratorReadinessBlocked(Exception):
    """Raised when a generator is not permitted to emit manufacturing G-code."""

    def __init__(self, record: GeneratorReadinessRecord) -> None:
        self.record = record
        super().__init__(
            f"Generator readiness for route '{record.route}' is "
            f"{record.readiness.value}: {record.reason}"
        )

    def as_detail(self) -> Dict[str, Any]:
        return self.record.as_detail()


GENERATOR_READINESS: Mapping[str, GeneratorReadinessRecord] = {
    "stratocaster_body": GeneratorReadinessRecord(
        route="stratocaster_body",
        readiness=GeneratorReadiness.BLOCKED,
        reason=(
            "Five verified findings capable of destroying stock: outline and cavity "
            "placement are in different coordinate frames; the cached body outline is "
            "not the body; the advertised holding tabs are a comment with no tab "
            "geometry, so the part is severed on the final perimeter pass; rear-face "
            "operations are emitted inline into a top-face program behind a comment; "
            "the perimeter 'tool offset' is an X-only translation."
        ),
        exit_condition=(
            "Each finding repaired and proven by an end-to-end test asserting emitted "
            "manufacturing content, then a readiness decision recorded on evidence."
        ),
        evidence=(
            "LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md ST-1, ST-2, ST-3, ST-5, ST-6",
            "audited read-only against origin/main c7523677",
        ),
    ),
    "les_paul_body": GeneratorReadinessRecord(
        route="les_paul_body",
        readiness=GeneratorReadiness.GOVERNED_BY_ASSET_AUTHORITY,
        reason=(
            "Emission is already gated by the asset-authority layer (#380) on the "
            "source DXF. This layer defers so that refusal semantics established by "
            "#380 remain exactly as they are."
        ),
        exit_condition=(
            "Asset authority is adjudicated for the source DXF, after which generator "
            "readiness is decided separately on its own evidence."
        ),
        evidence=(
            "lespaul_body_generator calls require_manufacturing_authority before use",
            "LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md LP-1",
        ),
    ),
    "flying_v_body": GeneratorReadinessRecord(
        route="flying_v_body",
        readiness=GeneratorReadiness.REVIEW_REQUIRED,
        reason=(
            "Route is not covered by asset authority and has no evidence qualifying it "
            "for manufacturing. It emits cavities only and no body perimeter, so it "
            "cannot sever a part; its open exposure is cavity depth and placement. A "
            "depth validator for exactly that exposure exists and is not wired into "
            "the emission path. Recorded as unqualified, not as authorized."
        ),
        exit_condition=(
            "Depth and placement validated on the emission path, then a readiness "
            "decision recorded on evidence."
        ),
        evidence=(
            "LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md FV-1, FV-2, FV-4",
        ),
    ),
    "neck": GeneratorReadinessRecord(
        route="neck",
        readiness=GeneratorReadiness.REVIEW_REQUIRED,
        reason=(
            "Route is not covered by asset authority and has no evidence qualifying it "
            "for manufacturing. Distinct from the separately tracked neck path that "
            "carries a standing rapids-at-cutting-depth finding; that path is on "
            "another router and is not governed by this record. Recorded as "
            "unqualified, not as authorized."
        ),
        exit_condition=(
            "Surveyed for manufacturing-critical defects, then a readiness decision "
            "recorded on evidence."
        ),
        evidence=(
            "LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md NK-1, NK-2",
        ),
    ),
}


def resolve_generator_readiness(
    route_key: str,
    registry: Optional[Mapping[str, GeneratorReadinessRecord]] = None,
) -> GeneratorReadinessRecord:
    """Return the readiness record for ``route_key``.

    A missing record resolves to :attr:`GeneratorReadiness.UNKNOWN`, which stops
    emission. Omitting or renaming a record can therefore never open a route.
    """
    table = GENERATOR_READINESS if registry is None else registry
    record = table.get(route_key)
    if record is not None:
        return record
    return GeneratorReadinessRecord(
        route=route_key,
        readiness=GeneratorReadiness.UNKNOWN,
        reason=(
            "No generator readiness record exists for this route. Unknown readiness "
            "fails closed."
        ),
        exit_condition="Declare a readiness record for this route, backed by evidence.",
        evidence=(),
    )


def require_generator_readiness(
    route_key: str,
    registry: Optional[Mapping[str, GeneratorReadinessRecord]] = None,
) -> GeneratorReadinessRecord:
    """Raise :class:`GeneratorReadinessBlocked` unless emission may proceed.

    Returning does not mean the route is authorized to manufacture -- only that
    this layer does not stop it. Downstream layers may still refuse.
    """
    record = resolve_generator_readiness(route_key, registry)
    if not record.permits_emission:
        raise GeneratorReadinessBlocked(record)
    return record
