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

It follows that this layer is **fail-closed**: every state stops manufacturing
G-code except ``GOVERNED_BY_ASSET_AUTHORITY``, and that one is a *delegation*
rather than an authorization -- it says "this layer does not decide; the asset
layer does", and the asset layer then renders its own verdict. Only an explicitly
established manufacturing authority may permit emission, and no such authority is
expressed here.

Evidence: ``LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md``, audited read-only against
``origin/main`` ``c7523677``.

OPEN CONTAINMENT FINDINGS (recorded here, not closed by this module)
-------------------------------------------------------------------

**CF-1 -- the neck surface is three code paths, not one.**
Confirmed 2026-09-21 by reading the endpoints' sources, and extended 2026-09-22
when LTB-REMEDIATE-P1 gave the third path its own identity:

===========================================  ==========================  ======
route                                        emits via                   gated
===========================================  ==========================  ======
``/api/cam/guitar/{model_id}/neck/gcode``    35 inline                   yes
                                             ``gcode_lines.append``
                                             calls in the router;
                                             **no generator class**
``/api/neck/gcode/generate``                 ``NeckGCodeGenerator``      no
``/api/neck/gcode/download``                 delegates to ``/generate``  no
``/api/cam-workspace/neck/generate-full``    ``NeckPipeline``            yes
                                             (orchestrator), via
                                             ``neck_pipeline_full``
===========================================  ==========================  ======

They are **not the same governed generator identity**, which is the opposite of
what the route names suggest. The ``"neck"`` record below governs a handler that
constructs no generator, while the real ``NeckGCodeGenerator`` is reachable only
through the two ungated endpoints -- and those answer unauthenticated. Gating
them under the ``"neck"`` key would therefore be wrong: it would attach a record
written about inline router code to a different implementation with different
exposure. They need their own classification, or retirement, decided on their own
evidence. Deliberately out of scope for CAM-CONTAIN-001; they are the subject of
LTB-REMEDIATE-P2 and remain ungated here.

The third path, ``/api/cam-workspace/neck/generate-full``, was contained by
LTB-REMEDIATE-P1 under its own key ``neck_pipeline_full`` for the same reason:
it reaches ``NeckPipeline``, a third implementation, and reusing ``"neck"`` would
have repeated the identity error rather than fixed it.

**CF-3 -- every routine refusal is logged as a CRITICAL failure with a
traceback.** Observed 2026-09-22 during LTB-REMEDIATE-P1, pre-existing and
uniform: all eight gated handlers carry ``@safety_critical``, which catches
every exception including the ``HTTPException(422)`` this layer raises, logs it
at CRITICAL with ``exc_info=True``, and re-raises. Containment therefore works
correctly but turns an expected, designed refusal into a critical-severity log
line with a stack trace. Nothing here is broken; the cost is signal quality --
a real safety-critical failure now shares a severity and a shape with a routine
"this generator is not qualified" answer. Fixing it means teaching
``safety_critical`` to pass through an intended refusal, which touches all
eight routes at once and belongs in its own increment, not in a containment PR.

**CF-2 -- enforcement is per handler, across independently registered route
families.** Containment closed the seven G-code routes under ``/api/cam/guitar/``
one handler at a time, and each round of review found another that had been
missed, because nothing structurally requires a G-code-producing endpoint to
consult an authority layer. The application exposes roughly sixty such endpoints
outside this prefix (probe, retract, drilling, vcarve, binding, toolpath, saw,
vision, geometry...). The next increment should inventory every G-code-producing
endpoint application-wide and reconcile each to a governed generator, rather than
extending this registry prefix by prefix.
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
    #: explicitly NOT an authorization -- absence of a finding is not a pass, so
    #: it stops emission exactly as BLOCKED does. The two differ in meaning, not
    #: in effect: BLOCKED records witnessed defects, REVIEW_REQUIRED records
    #: absent evidence.
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

    #: Emission for this route is governed upstream by the asset-authority layer
    #: (#380). This layer defers so that the asset gate produces its own,
    #: unchanged refusal.
    GOVERNED_BY_ASSET_AUTHORITY = "GOVERNED_BY_ASSET_AUTHORITY"

    #: No record exists for the route. Fail closed -- an omitted or renamed
    #: record must never read as authorization.
    UNKNOWN = "UNKNOWN"


#: States that stop emission at this layer -- which is every state except the
#: delegation. A state that permits emission is operationally a "yes", whatever
#: the enum calls it, so REVIEW_REQUIRED stops emission too: it cannot mean both
#: "evidence is insufficient" and "carry on emitting manufacturing G-code".
#: UNKNOWN is here so that deleting or renaming a record fails closed rather than
#: silently opening a route.
_STOPS_EMISSION = frozenset({
    GeneratorReadiness.BLOCKED,
    GeneratorReadiness.REVIEW_REQUIRED,
    GeneratorReadiness.UNKNOWN,
})


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
            "the emission path. Recorded as unqualified, and therefore refused."
        ),
        exit_condition=(
            "Depth and placement validated on the emission path, then a readiness "
            "decision recorded on evidence."
        ),
        evidence=(
            "LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md FV-1, FV-2, FV-4",
        ),
    ),
    "acoustic_body": GeneratorReadinessRecord(
        route="acoustic_body",
        readiness=GeneratorReadiness.BLOCKED,
        reason=(
            "The emitted holding-tab geometry does not follow the requested tab "
            "count, on a full-depth perimeter pass -- the operation that decides "
            "whether the part stays in the blank. Measured on DREADNOUGHT at "
            "tool 6.0mm, depth 12.0mm, stepdown 3.0mm: tab_count 2/4/6 emit 7/13/19 "
            "lifts to the tab plane, but tab_count 8, 12, 16 and 24 all collapse to "
            "4 lifts in a 95-line program, while the program header still advertises "
            "the number requested -- e.g. '( Tabs: 16 x 15.0mm wide x 3.0mm tall )' "
            "over 4 actual lifts. The route's own default is tab_count=8, so the "
            "default request is already in the collapsed regime. Distinct from the "
            "Stratocaster finding ST-3: here the tab lifts are real geometry, they "
            "just do not correspond to the parameter. Recorded as unqualified, and "
            "therefore refused."
        ),
        exit_condition=(
            "Emitted tab geometry proven to track tab_count across the parameter "
            "range by a test asserting lift events in the emitted program, then a "
            "readiness decision recorded on evidence."
        ),
        evidence=(
            "CAM-CONTAIN-001 acoustic survey 2026-09-21, reproduced against "
            "AcousticBodyGenerator.generate_perimeter_gcode",
        ),
    ),
    "acoustic_soundhole": GeneratorReadinessRecord(
        route="acoustic_soundhole",
        readiness=GeneratorReadiness.REVIEW_REQUIRED,
        reason=(
            "Route is not covered by asset authority and has no evidence qualifying "
            "it for manufacturing. It emits no perimeter and no holding tabs, so it "
            "cannot sever the body; its open exposure is soundhole diameter and "
            "depth placement, which has not been surveyed. It shares a generator "
            "with the body perimeter route, which is BLOCKED. Recorded as "
            "unqualified, and therefore refused."
        ),
        exit_condition=(
            "Surveyed for manufacturing-critical defects, then a readiness decision "
            "recorded on evidence."
        ),
        evidence=(
            "CAM-CONTAIN-001 acoustic survey 2026-09-21: no tab logic in "
            "generate_soundhole_gcode; not previously surveyed",
        ),
    ),
    "acoustic_binding": GeneratorReadinessRecord(
        route="acoustic_binding",
        readiness=GeneratorReadiness.REVIEW_REQUIRED,
        reason=(
            "Route is not covered by asset authority and has no evidence qualifying "
            "it for manufacturing. It emits a channel rather than a perimeter and "
            "carries no holding tabs, so it cannot sever the body; its open exposure "
            "is channel depth and offset against a binding stock dimension, which "
            "has not been surveyed. It shares a generator with the body perimeter "
            "route, which is BLOCKED. Recorded as unqualified, and therefore refused."
        ),
        exit_condition=(
            "Surveyed for manufacturing-critical defects, then a readiness decision "
            "recorded on evidence."
        ),
        evidence=(
            "CAM-CONTAIN-001 acoustic survey 2026-09-21: no tab logic in "
            "generate_binding_channel_gcode; not previously surveyed",
        ),
    ),
    "neck_pipeline_full": GeneratorReadinessRecord(
        route="neck_pipeline_full",
        readiness=GeneratorReadiness.BLOCKED,
        reason=(
            "Witnessed defect capable of damaging stock, reproduced against this "
            "exact implementation. POST /api/cam-workspace/neck/generate-full "
            "answers an uncredentialed default request with a 28,260-byte .nc "
            "attachment containing 1,779 G/M records, of which 702 are G0 rapids "
            "below the workpiece top surface, reaching Z=-25.000mm. The mechanism "
            "is in app/cam/neck/profile_carving.py: the station loop alternates "
            "'G1 Z<depth>' with 'G0 X<next>', so every lateral stepover is taken "
            "at rapid feed while the cutter is engaged in the material. All 702 "
            "inherit their Z modally; none carries an explicit Z word, so a "
            "substring search for a rapid and a negative Z on one line finds "
            "zero. Distinct identity: this route reaches "
            "app.cam.neck.orchestrator.NeckPipeline, which is neither the inline "
            "router code governed by the 'neck' record nor the NeckGCodeGenerator "
            "behind /api/neck/gcode/*."
        ),
        exit_condition=(
            "Two separate conditions, both required. (1) The lateral stepover in "
            "profile_carving.py roughing and finishing emits a feed move, proven "
            "by a semantic modal-state regression fixture that asserts zero G0 "
            "rapids below the workpiece top and that is itself proven able to "
            "fail on a deliberately unsafe fixture. (2) A readiness decision "
            "recorded on evidence through the governing qualification process. "
            "Removing the unsafe rapid does NOT by itself qualify this generator."
        ),
        evidence=(
            "LTB-AUDIT-001 finding P-1 (HIGH, confirmed)",
            "LTB-REMEDIATE-P1 reproduction at main 5e683d8e: 702/927 rapids "
            "below Z=0, min Z -25.000mm, 0 with an explicit Z word on the line",
            "services/api/app/cam/neck/profile_carving.py:301 (roughing), :360 "
            "(finishing) -- the two lateral-rapid emitters",
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
            "unqualified, and therefore refused."
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
