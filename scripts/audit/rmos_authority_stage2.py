"""RMOS-AUTHORITY-MAP-001 Stage 2 overlay.

Classification conclusions applied onto the Stage-1 inventory skeleton.
This module does not walk production routers at import time and does not
grant execution authority. The census script imports it only for
``--emit-stage2`` (stdout) and for validation helpers.

Owner ruling 2026-08-27: Stage 1 taxonomy accepted with the surface_kind
boundary. Proceed to Stage 2 deep classification. Do not merge remediation.
"""
from __future__ import annotations

from typing import Any, Dict, List

SURFACE_KIND_VOCABULARY = [
    "manufacturing_capability",
    "artifact_transformation",
    "artifact_retrieval",
    "advisory",
]

GENERATION_ORDERING_VOCABULARY = [
    "AUTHORITY_BEFORE_GENERATION",
    "GENERATION_WITHOUT_AUTHORITY",
    "AUTHORITY_AFTER_GENERATION",
    "MIXED",
    "NOT_APPLICABLE",
    "UNKNOWN",
]

INPUT_CONTRACT_VOCABULARY = [
    "TRUTHFUL",
    "MISMATCH",
    "MIXED",
    "NOT_APPLICABLE",
    "UNKNOWN",
]

UNGATED_EXPOSURE_VOCABULARY = ["YES", "NO", "RETRIEVAL_ONLY", "UNKNOWN"]


def _ev(cls: str, ref: str, note: str) -> Dict[str, str]:
    return {"class": cls, "ref": ref, "note": note}


def _overlay(
    *,
    surface_kind: str,
    intent_contract: str,
    authority_status: str,
    evaluator: str | None,
    policy_boundary: str | None,
    generation_ordering: str,
    input_contract_status: str,
    ungated_output_exposure: str,
    generators: List[str],
    persistence_status: str,
    persistence_mechanism: str | None,
    client_consumers: List[str],
    reachability: str,
    runtime_evidence: str,
    authority_disposition: str,
    evidence: List[Dict[str, str]],
    evidence_class: str,
    confidence: str,
) -> Dict[str, Any]:
    return {
        "surface_kind": surface_kind,
        "intent_contract": intent_contract,
        "authority": {
            "status": authority_status,
            "evaluator": evaluator,
            "policy_boundary": policy_boundary,
        },
        "generation_ordering": generation_ordering,
        "input_contract_status": input_contract_status,
        "ungated_output_exposure": ungated_output_exposure,
        "generators": generators,
        "persistence": {
            "status": persistence_status,
            "mechanism": persistence_mechanism,
        },
        "client_consumers": client_consumers,
        "reachability": reachability,
        "runtime_evidence": runtime_evidence,
        "authority_disposition": authority_disposition,
        "evidence": evidence,
        "evidence_class": evidence_class,
        "confidence": confidence,
    }


# Capability-id → Stage 2 fields. Routes stay inventory-owned.
STAGE2_BY_ID: Dict[str, Dict[str, Any]] = {
    "retract": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "All four mounted retract G-code routes share one authority path "
            "(_authorize_retract → compute_feasibility_internal → SafetyPolicy) "
            "before any builder. resolve_feasibility_engine('retract') is None, "
            "so the result is UNKNOWN and SafetyPolicy blocks. No G-code is "
            "emitted. Strategy vocabularies are split (query vs download body) "
            "but both feed tool_id='retract:{strategy}'."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="SafetyPolicy.should_block via _authorize_retract",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="TRUTHFUL",
        ungated_output_exposure="NO",
        generators=[
            "app.routers.retract.retract_gcode_router.generate_simple_retract_gcode",
            "app.routers.retract.retract_gcode_router.download_retract_gcode",
        ],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="validate_and_persist (BLOCKED; no gcode_sha256)",
        client_consumers=[
            "packages/client/src/components/toolbox/cam-essentials/useRetractOperation.ts",
        ],
        reachability="RUNTIME_BLOCKED_BY_POLICY",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="BLOCKED_BY_DESIGN",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/retract/retract_gcode_router.py:_authorize_retract",
                "Authority precedes builders. Engine table has no retract evaluator.",
            ),
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/rmos/api/rmos_feasibility_router.py:_PRODUCTION_FEASIBILITY_ENGINES",
                "Registered engines are saw, rosette, adaptive only.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/retract/gcode and /gcode/download",
                "409 SAFETY_BLOCKED; body contains no G21/M30; no X-GCode-SHA256.",
            ),
            _ev(
                "CLIENT_CALL_SITE",
                "packages/client/src/components/toolbox/cam-essentials/useRetractOperation.ts",
                "In-repo consumer of /api/cam/retract/gcode. Reachability evidence, not authority.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "adaptive": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Machine-output routes are /gcode and /batch_export. /plan is not a "
            "machine-output candidate. gcode calls _enforce_safety_policy "
            "(compute_adaptive_feasibility + SafetyPolicy) before plan() and "
            "before post-processor assembly. Persistence records the evaluator "
            "decision (feasibility_sha256 of the result, not a request hash)."
        ),
        authority_status="NAMED",
        evaluator="app.rmos.api.rmos_feasibility_router.compute_adaptive_feasibility",
        policy_boundary="SafetyPolicy.should_block via _enforce_safety_policy",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="TRUTHFUL",
        ungated_output_exposure="NO",
        generators=["app.routers.adaptive.gcode_router.gcode"],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="validate_and_persist with evaluator feasibility + gcode_sha256",
        client_consumers=[
            "packages/client/src/api/adaptive.ts",
            "packages/client/src/components/adaptive/composables/useToolpathExport.ts",
        ],
        reachability="RUNTIME_REACHABLE",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="GOVERNED",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/adaptive/gcode_router.py:gcode",
                "Gate then plan() then assembly then validate_and_persist.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/pocket/adaptive/gcode",
                "Sane plan → 200 G-code + X-Run-ID. F004 z_rough=1.5 → 409, no G-code.",
            ),
            _ev(
                "CLIENT_CALL_SITE",
                "packages/client/src/components/adaptive/composables/useToolpathExport.ts",
                "Client calls /gcode and /batch_export.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "drilling": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "RMOS-DRILLING-CONTRACT-001: canonical DrillingOperationSpec exists; "
            "intent maps completely; modal/pattern remain incomplete without "
            "optional diameter+datum+RPM. Three routes, three HTTP contracts. "
            "Modal POST /gcode (DrillReq) still emits G81/G83 with no feasibility "
            "call and no RMOS gate. Hole.z is a coordinate, not depth; tool is "
            "not diameter. Do not invent abs(z) or tool-as-diameter. Pattern "
            "/pattern/gcode still calls compute_feasibility_internal("
            "tool_id='drill_pattern_gcode') which resolves to mode 'unknown'. "
            "Intent /intent-gcode uses compute_drilling_feasibility via the "
            "canonical adapter (intent-lane, not the RMOS engine table). "
            "input_contract_status remains MISMATCH until a separately "
            "authorized converge order. Not GOVERNED."
        ),
        authority_status="MISMATCH",
        evaluator="app.cam.drilling.feasibility.compute_drilling_feasibility (intent route only; not in _PRODUCTION_FEASIBILITY_ENGINES)",
        policy_boundary="none on modal; SafetyPolicy on pattern (always UNKNOWN); intent-local feasible flag",
        generation_ordering="MIXED",
        input_contract_status="MISMATCH",
        ungated_output_exposure="YES",
        generators=[
            "app.cam.routers.drilling.drill_modal_router.drill_gcode",
            "app.cam.routers.drilling.drill_pattern_router.drill_pattern_gcode",
            "app.cam.routers.drilling.intent_router.generate_drilling_intent_gcode",
        ],
        persistence_status="NONE",
        persistence_mechanism="modal: none; pattern: persist_run BLOCKED; intent: validate_and_persist",
        client_consumers=[],
        reachability="RUNTIME_REACHABLE",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="AUTHORITY_CONTRACT_MISMATCH",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/drilling/drill_modal_router.py:drill_gcode",
                "No RMOS import. DrillReq vs compute_drilling_feasibility kwargs do not match.",
            ),
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/drilling/feasibility.py:compute_drilling_feasibility",
                "Named kwargs only. hole_diameter_mm required. Canonical "
                "adapter (operation_contract) exists; DrillReq still lacks "
                "required diameter/datum/RPM unless optional fields are "
                "supplied. No fabricated mapping from Hole.z or tool.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/drilling/gcode",
                "200 text/plain G81/G83. Ungated machine output on the modal route.",
            ),
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/drilling/drill_pattern_router.py",
                "tool_id='drill_pattern_gcode' → resolve_mode 'unknown'; engine None.",
            ),
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/drilling/operation_contract.py",
                "RMOS-DRILLING-CONTRACT-001: manufacturing spec + evaluator "
                "adapter. Modal remains ungated. Disposition still "
                "AUTHORITY_CONTRACT_MISMATCH.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "profiling": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "RMOS-PROFILING-CONVERGE-001. Production POST /gcode evaluates "
            "compute_profile_feasibility (via compute_profiling_feasibility) "
            "then SafetyPolicy before ProfileToolpath.generate(). Finishing "
            "defaults are ProfileConfig runtime values the generator actually "
            "uses. Intent /intent-gcode already used the same canonical scorer. "
            "Preview /preview is unchanged and is not a machine-output path. "
            "GOVERNED != FUNCTIONAL != AVAILABLE. Frozen before-state from "
            "PR #328 was LIVE_UNGOVERNED_OUTPUT / RUNTIME_REACHABLE."
        ),
        authority_status="NAMED",
        evaluator=(
            "app.cam.profiling.feasibility.compute_profile_feasibility "
            "via app.rmos.api.rmos_feasibility_router.compute_profiling_feasibility"
        ),
        policy_boundary="SafetyPolicy.should_block via _authorize_profiling",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="TRUTHFUL",
        ungated_output_exposure="NO",
        generators=[
            "app.cam.routers.profiling.profile_router.generate_profile_gcode",
            "app.cam.routers.profiling.intent_router.generate_profile_intent_gcode",
        ],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="validate_and_persist with evaluator feasibility + gcode_sha256",
        client_consumers=[],
        reachability="RUNTIME_REACHABLE",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="GOVERNED",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/profiling/profile_router.py:generate_profile_gcode",
                "_authorize_profiling (compute_feasibility_internal + SafetyPolicy) "
                "returns only when allowed; ProfileToolpath.generate() follows.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/profiling/gcode",
                "Valid contour → 200 G-code + X-Run-ID + X-Risk-Level GREEN. "
                "tab_height_mm >= cut_depth_mm → 409 SAFETY_BLOCKED, no G-code. "
                "Empty body remains 422 (PR #324 binding preserved).",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "vcarve": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Production POST /api/cam/vcarve/production/gcode is @safety_critical "
            "with no RMOS call and emits G-code after #324 restored body binding. "
            "Toolpath /api/cam/toolpath/vcarve/gcode and intent /intent-gcode "
            "call compute_feasibility_internal; mode vcarve has no engine so "
            "they 409. The live production path is the post-merge exposure. "
            "RMOS-VCARVE-CONVERGE-001 HOLD (2026-08-27): no substantive V-carve "
            "evaluator exists. AUTHORITY CONTRACT = NOT SATISFIABLE. Adjacent "
            "profiling/drilling/pocketing/FeasibilityInput(tool_d) evaluators "
            "are not V-carve-capable (D1). Production behavior unchanged; "
            "disposition remains POST_MERGE_AUTHORITY_EXPOSURE."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="none on production; SafetyPolicy on toolpath/intent (UNKNOWN → block)",
        generation_ordering="MIXED",
        input_contract_status="MIXED",
        ungated_output_exposure="YES",
        generators=[
            "app.cam.routers.vcarve.production_router.generate_production_vcarve_gcode",
            "app.cam.routers.toolpath.vcarve_router.generate_vcarve_gcode",
            "app.cam.routers.vcarve.intent_router.generate_vcarve_intent_gcode",
        ],
        persistence_status="NONE",
        persistence_mechanism="production: none; toolpath/intent: persist_run / validate_and_persist on BLOCKED",
        client_consumers=[],
        reachability="RUNTIME_REACHABLE",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="POST_MERGE_AUTHORITY_EXPOSURE",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/vcarve/production_router.py:generate_production_vcarve_gcode",
                "VCarveToolpath.generate() with no RMOS gate.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/vcarve/production/gcode",
                "200 text/plain G-code after #324. No X-Run-ID required.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/vcarve/intent-gcode",
                "409 SAFETY_BLOCKED — engine unavailable, fail-closed. Not the exposure path.",
            ),
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/rmos/api/rmos_feasibility_router.py:_PRODUCTION_FEASIBILITY_ENGINES",
                "RMOS-VCARVE-CONVERGE-001 HOLD: no vcarve engine. "
                "AUTHORITY CONTRACT = NOT SATISFIABLE. Do not gate production "
                "to 409 UNKNOWN without an owner availability ruling (D3).",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "roughing": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Both /toolpath/roughing/gcode and /roughing/gcode_intent call "
            "compute_feasibility_internal(tool_id='roughing:default' or body). "
            "Mode roughing has no engine → unavailable_feasibility UNKNOWN → "
            "SafetyPolicy 409 before G-code. Persistence of BLOCKED is not GREEN "
            "and is not GOVERNED manufacturing authority."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="SafetyPolicy.should_block (UNKNOWN from missing engine)",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="TRUTHFUL",
        ungated_output_exposure="NO",
        generators=[
            "app.cam.routers.toolpath.roughing_router.roughing_gcode",
            "app.routers.cam_roughing_intent_router",
        ],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="persist_run BLOCKED (roughing_gcode_blocked)",
        client_consumers=[
            "packages/client/src/components/toolbox/cam-essentials/useRoughingOperation.ts",
            "packages/client/src/sdk/endpoints/cam/roughing.ts",
        ],
        reachability="RUNTIME_BLOCKED_BY_POLICY",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="BLOCKED_BY_DESIGN",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/toolpath/roughing_router.py:roughing_gcode",
                "compute_feasibility_internal then should_block then generate. Engine None for roughing.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/toolpath/roughing/gcode",
                "Valid RoughReq → 409 SAFETY_BLOCKED; no G-code body.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "helical": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/cam/toolpath/helical_entry calls "
            "compute_feasibility_internal(tool_id='helical:gcode'). Mode helical "
            "has no engine → UNKNOWN → 409 before helical_gcode()."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="SafetyPolicy.should_block (UNKNOWN from missing engine)",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="TRUTHFUL",
        ungated_output_exposure="NO",
        generators=["app.cam.routers.toolpath.helical_router.helical_entry"],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="persist_run BLOCKED (helical_gcode_blocked)",
        client_consumers=["packages/client/src/api/v161.ts"],
        reachability="RUNTIME_BLOCKED_BY_POLICY",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="BLOCKED_BY_DESIGN",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/toolpath/helical_router.py:helical_entry",
                "tool_id helical:gcode; resolve_feasibility_engine('helical') is None.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/toolpath/helical_entry",
                "Valid HelicalReq → 409 SAFETY_BLOCKED; no G-code.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "rosette": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "plan-toolpath and post-gcode share one upstream authority: "
            "compute_feasibility_internal with tool_id rosette:* dispatches to "
            "compute_rosette_feasibility (manufacturability scorer via "
            "ScorerDesignSpec). Historical fail-open (wrong schema / CAM stub "
            "GREEN) is retired. post-gcode is serialization of the same family, "
            "not a second manufacturing authority. Router maps inner/outer "
            "radius to scorer diameters; that mapping is in the handler, not invented here. "
            "GOVERNED here means the named evaluator is consulted before generation. "
            "It does not mean generation is functional or the path is available. "
            "Witnessed generation failure: 400 TOOLPATH_PLAN_ERROR "
            "(RosetteGeometry.__init__ unexpected keyword center_x). Not remediated."
        ),
        authority_status="NAMED",
        evaluator="app.rmos.api.rmos_feasibility_router.compute_rosette_feasibility",
        policy_boundary="SafetyPolicy.should_block",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="TRUTHFUL",
        ungated_output_exposure="NO",
        generators=[
            "app.cam.routers.rosette.rosette_toolpath_router.plan_rosette_cam_toolpath",
            "app.cam.routers.rosette.rosette_toolpath_router.postprocess_toolpath_grbl",
        ],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="persist_run OK or BLOCKED with evaluator feasibility",
        client_consumers=[],
        reachability="RUNTIME_BROKEN",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="GOVERNED",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/rmos/api/rmos_feasibility_router.py:compute_rosette_feasibility",
                "Real scorer. Evaluation failure → error_feasibility (blocking ERROR), not fail-open GREEN.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/rosette/plan-toolpath",
                "Evaluator is consulted (not 409 UNKNOWN). After a non-blocking decision, generation currently returns 400 TOOLPATH_PLAN_ERROR (RosetteGeometry constructor kwargs). No G-code leaked. Recorded as reachability RUNTIME_BROKEN so GOVERNED is not read as functional/available. Not remediated here.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "probing": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Work-offset / setup G38 programs. Draft /api/probe/*/gcode has no "
            "RMOS evaluator. download_governed persists a hardcoded GREEN "
            "decision (create_governed_probe_response) without "
            "compute_feasibility_internal. /api/v1/machines/probe/{corner,surface} "
            "is a parallel ungated contract, not an alias. GREEN persistence on "
            "the governed lane is not GOVERNED manufacturing authority."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="none on draft/v1; hardcoded GREEN persist on governed downloads",
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="MIXED",
        ungated_output_exposure="YES",
        generators=[
            "app.routers.probe",
            "app.api_v1.machines",
        ],
        persistence_status="FALSE_PROVENANCE",
        persistence_mechanism="draft: none; governed download: persist_run RunDecision(risk_level=GREEN) without evaluator",
        client_consumers=[
            "packages/client/src/components/toolbox/cam-essentials/useProbeOperation.ts",
        ],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/probe",
                "Draft JSON gcode has no feasibility call. Governed downloads mint GREEN.",
            ),
            _ev(
                "CLIENT_CALL_SITE",
                "packages/client/src/components/toolbox/cam-essentials/useProbeOperation.ts",
                "Client path /api/cam/probe/* does not match live /api/probe/*. Consumer evidence only.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime POST of probe G38 programs",
                "Withheld: machine-setup probing programs are not a side-effect-free compute POST for this audit.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "binding": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Owner ruling: binding stays separate from guitar body. Includes "
            "/api/cam/binding/{channel,purfling}/gcode (caller-supplied outline, "
            "BindingChannel/PurflingLedge) and acoustic "
            "/api/cam/guitar/acoustic/{style}/binding/gcode (style-parametric). "
            "Distinct geometry/tooling from body cuts. Neither route family "
            "calls RMOS. Input contracts differ; manufacturing intent is binding."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="@safety_critical logging only",
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="MIXED",
        ungated_output_exposure="YES",
        generators=[
            "app.cam.routers.binding.binding_router",
            "app.routers.cam.guitar.acoustic_cam_router.generate_binding_channel_gcode",
        ],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[],
        reachability="RUNTIME_REACHABLE",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/binding/binding_router.py",
                "No RMOS. Channel and purfling emit G-code from body_outline.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/binding/channel/gcode",
                "200 G21 from JSON body_outline rectangle.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "inlay": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/art-studio/inlay/export-gcode builds pocket G-code from "
            "inlay shapes. No RMOS evaluator. Client currently uses export-dxf, "
            "not this path."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="UNKNOWN",
        ungated_output_exposure="YES",
        generators=["app.art_studio.inlay_router"],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/art_studio/inlay_router.py",
                "export-gcode has no compute_feasibility_internal.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime POST /api/art-studio/inlay/export-gcode",
                "Withheld: request contract needs inlay document state; do not fabricate inputs.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "radius-dish": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/acoustics/radius-dish/generate-gcode is a parametric "
            "spherical raster generator. No RMOS. Client downloads static public "
            ".nc files instead of this API."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="UNKNOWN",
        ungated_output_exposure="YES",
        generators=["app.routers.radius_dish_router"],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/radius_dish_router.py",
                "generate-gcode has no RMOS gate.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime POST generate-gcode",
                "Withheld rather than guess a full parametric payload.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "feeds-speeds": _overlay(
        surface_kind="advisory",
        intent_contract=(
            "POST /api/cam/opt/feeds-speeds returns JSON machining parameters "
            "(feed_xy, rpm, stepdown, …), not a machine file. Keep on the "
            "authority map because the numbers can influence execution. "
            "Not classified as machine-output authority unless a later stage "
            "shows the JSON is consumed as authoritative machine parameters."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="@safety_critical logging only",
        generation_ordering="NOT_APPLICABLE",
        input_contract_status="NOT_APPLICABLE",
        ungated_output_exposure="NO",
        generators=["app.cam.routers.utility.optimization_router.calculate_feeds_speeds"],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[],
        reachability="RUNTIME_REACHABLE",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="ADVISORY_ONLY",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/utility/optimization_router.py:calculate_feeds_speeds",
                "calculate_feed_plan → FeedsSpeedsResponse. No G-code.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/opt/feeds-speeds",
                "200 JSON with feed_xy/rpm; body is not G-code.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "biarc-contour": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/cam/toolpath/biarc/gcode calls "
            "compute_feasibility_internal(tool_id='biarc_gcode'). That tool_id "
            "does not use the biarc: prefix, so resolve_mode returns 'unknown' "
            "and there is no engine either way. Result UNKNOWN → 409 before "
            "linear G1 generation. Name is historical (no bi-arc fit)."
        ),
        authority_status="MISMATCH",
        evaluator=None,
        policy_boundary="SafetyPolicy.should_block (UNKNOWN)",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="MISMATCH",
        ungated_output_exposure="NO",
        generators=["app.cam.routers.toolpath.biarc_router.biarc_gcode"],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="persist_run BLOCKED",
        client_consumers=[
            "packages/client/src/components/toolbox/cam-essentials/useContourOperation.ts",
        ],
        reachability="RUNTIME_BLOCKED_BY_POLICY",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="BLOCKED_BY_DESIGN",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/toolpath/biarc_router.py:biarc_gcode",
                "tool_id='biarc_gcode' → mode unknown; engine None.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/toolpath/biarc/gcode",
                "Valid BiarcReq → 409 SAFETY_BLOCKED; no G-code.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "pocketing": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/cam/pocketing/intent-gcode uses compute_pocket_feasibility "
            "(intent-lane, shapely) before adaptive L1 G-code, then "
            "validate_and_persist. Not in _PRODUCTION_FEASIBILITY_ENGINES. "
            "Named local evaluator + gate-before-generate."
        ),
        authority_status="NAMED",
        evaluator="compute_pocket_feasibility (intent-lane; not RMOS engine table)",
        policy_boundary="block on not feasibility.feasible; validate_and_persist",
        generation_ordering="AUTHORITY_BEFORE_GENERATION",
        input_contract_status="TRUTHFUL",
        ungated_output_exposure="NO",
        generators=["app.cam.routers.pocketing.intent_router"],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="validate_and_persist",
        client_consumers=[
            "packages/client/src/api/pocketing.ts",
        ],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="GOVERNED",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/cam/routers/pocketing/intent_router.py",
                "compute_pocket_feasibility before generate; persist records the decision.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime POST intent-gcode",
                "Withheld: CamIntentV1 payload not reproduced here; static trace names evaluator and ordering.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "polygon-offset": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Draft /polygon_offset.nc emits NC with no RMOS. "
            "Governed /polygon_offset_governed.nc generates first, then persists "
            "RunDecision(risk_level='GREEN') hashing the request, not a "
            "feasibility result. GREEN persistence is not GOVERNED."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="NOT_APPLICABLE",
        ungated_output_exposure="YES",
        generators=["app.routers.polygon_offset_router"],
        persistence_status="FALSE_PROVENANCE",
        persistence_mechanism="governed lane: persist_run RunDecision(GREEN) + request_hash as feasibility_sha256",
        client_consumers=[
            "packages/client/src/views/PolygonOffsetLab.vue",
        ],
        reachability="RUNTIME_REACHABLE",
        runtime_evidence="POST_COMPUTE_WITNESS",
        authority_disposition="GOVERNED_PROVENANCE_DEFECT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/polygon_offset_router.py:polygon_offset_nc_governed",
                "Generate program, then mint GREEN. No compute_feasibility_internal.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "POST /api/cam/polygon_offset_governed.nc",
                "200 NC body; X-ToolBox-Lane governed does not imply an evaluator.",
            ),
        ],
        evidence_class="RUNTIME_REQUEST_WITNESS",
        confidence="HIGH",
    ),
    "neck-gcode": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Parametric NeckGCodeGenerator OP10–40 via /api/neck/gcode/generate "
            "and /download. Distinct from project-driven guitar neck stub and "
            "from headstock-transition surfacing (owner: split only for a "
            "distinct operation/authority contract). No RMOS."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="UNKNOWN",
        ungated_output_exposure="YES",
        generators=["app.routers.neck.gcode_router"],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/neck/gcode_router.py",
                "generate/download have no RMOS feasibility call.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime POST /api/neck/gcode/generate",
                "Withheld: full neck program payload not fabricated.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "operator-pack": _overlay(
        surface_kind="artifact_retrieval",
        intent_contract=(
            "GET /api/rmos/runs_v2/{run_id}/operator-pack zips existing run "
            "attachments. It does not regenerate G-code. Not a manufacturing "
            "capability. Stored YELLOW/RED require override before export. "
            "Can re-export G-code persisted under a defective GREEN (wrap)."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="exports.py stored-risk gate (YELLOW/RED override)",
        generation_ordering="NOT_APPLICABLE",
        input_contract_status="NOT_APPLICABLE",
        ungated_output_exposure="RETRIEVAL_ONLY",
        generators=[],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="reads RunStoreV2 attachments; does not create manufacturing identity",
        client_consumers=[
            "packages/client/src/sdk/rmos/runs.ts",
            "packages/client/src/composables/useDxfToGcode.ts",
        ],
        reachability="MOUNTED",
        runtime_evidence="GET_WITNESS",
        authority_disposition="INSUFFICIENT_EVIDENCE",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/rmos/runs_v2/exports.py",
                "ZIP of existing blobs. No manufacturing evaluator. Not GOVERNED.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "GET /api/rmos/runs_v2/missing/operator-pack",
                "Mounted retrieval: missing run_id is not 200 G-code. No run planted to export a pack.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="HIGH",
    ),
    "cam-guitar": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "Electric project-driven body/neck G-code and acoustic "
            "body/soundhole G-code. Acoustic binding moved to capability "
            "binding per owner ruling. Auth/project gates may apply; no RMOS "
            "evaluator on the generators."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="@safety_critical logging; some routes require auth + manufacturing_state",
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="MIXED",
        ungated_output_exposure="YES",
        generators=[
            "app.routers.cam.guitar.body_gcode_router",
            "app.routers.cam.guitar.acoustic_cam_router",
        ],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/cam/guitar",
                "No compute_feasibility_internal on body/neck/soundhole G-code.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime POST guitar gcode",
                "Withheld: project auth and durable project state. Record MOUNTED, not RUNTIME_REACHABLE.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "geometry": _overlay(
        surface_kind="artifact_transformation",
        intent_contract=(
            "export_gcode / export_gcode_governed wrap caller-supplied G-code "
            "with a post-processor. Bundles zip DXF/SVG/NC. Not a new "
            "manufacturing authority: transformation of an already-produced "
            "artifact. Draft lane has no evaluator. Governed lane persists; "
            "simulation gate is not a manufacturing evaluator."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="governed: _check_simulation_gate (not RMOS engine table)",
        generation_ordering="NOT_APPLICABLE",
        input_contract_status="NOT_APPLICABLE",
        ungated_output_exposure="YES",
        generators=[
            "app.geometry.export_router",
            "app.geometry.bundle_router",
        ],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="governed export_gcode: persist_run; draft: none",
        client_consumers=[
            "packages/client/src/components/GeometryOverlay.vue",
        ],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/geometry/export_router.py",
                "Wraps supplied gcode. Draft ungated. Not a manufacturing capability.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "saw-batch": _overlay(
        surface_kind="artifact_retrieval",
        intent_contract=(
            "Three GETs serialize stored saw-batch toolpath/execution moves to "
            "machine-consumable G-code (or redirect to an attachment). Included "
            "because the artifact is job instructions, not status metadata. "
            "HTTP GET is irrelevant. Export has no feasibility gate; module is "
            "marked QUARANTINE. Not a manufacturing generator."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="NOT_APPLICABLE",
        input_contract_status="NOT_APPLICABLE",
        ungated_output_exposure="RETRIEVAL_ONLY",
        generators=["app.saw_lab.batch_gcode_router", "app.saw_lab.toolpaths_router"],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="reads stored saw_batch artifacts; no new manufacturing decision",
        client_consumers=[],
        reachability="MOUNTED",
        runtime_evidence="GET_WITNESS",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/saw_lab/batch_gcode_router.py",
                "export_op_toolpaths_gcode / export_execution_gcode: stored moves → G-code. QUARANTINE header.",
            ),
            _ev(
                "RUNTIME_REQUEST_WITNESS",
                "GET missing artifact gcode",
                "404 without a planted batch artifact. Emission not runtime-witnessed; static trace is the classifier.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "cam-post": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/cam/post/post_v155 is contour → v15.5 post G-code. "
            "Kept separate from wrap and v1-dxf: it does not share an upstream "
            "authorized artifact; the post is the manufacturing authority. "
            "Not a mere serializer of someone else's decision. No RMOS."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="UNKNOWN",
        ungated_output_exposure="YES",
        generators=["app.routers.cam_post_v155_router"],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=["packages/client/src/api/postv155.ts"],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/cam_post_v155_router.py",
                "Independent contour-to-G-code authority. Client still names /api/cam_gcode/post_v155.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime POST post_v155",
                "Withheld: full contour/post payload not fabricated for this audit.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "rmos-wrap": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/rmos/wrap/mvp/dxf-to-grbl parses DXF, calls adaptive "
            "plan(), emits GRBL, persists attachments with a hardcoded "
            "risk_level GREEN. Independent of cam-post and v1-dxf. GREEN "
            "persistence is not GOVERNED (MAR-009)."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary="hardcoded GREEN in mvp_router (not SafetyPolicy)",
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="NOT_APPLICABLE",
        ungated_output_exposure="YES",
        generators=["app.rmos.mvp_router.dxf_to_grbl"],
        persistence_status="FALSE_PROVENANCE",
        persistence_mechanism="CAS attachments + risk_level GREEN literal",
        client_consumers=[
            "packages/client/src/composables/useDxfToGcode.ts",
            "packages/client/src/views/QuickCutView.vue",
        ],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="GOVERNED_PROVENANCE_DEFECT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/rmos/mvp_router.py:dxf_to_grbl",
                "Literal risk_level GREEN. Calls plan() but records GREEN rather than the evaluator decision.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime multipart DXF POST",
                "Withheld: file-upload pipeline not exercised; static GREEN mint is sufficient for MAR-009/010.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="HIGH",
    ),
    "v1-dxf": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/v1/dxf/cam/gcode returns placeholder G-code "
            "('; TODO: Full toolpath generation requires CAM engine'). "
            "Kept separate from wrap/post. Explicitly a non-production stub."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="NOT_APPLICABLE",
        ungated_output_exposure="NO",
        generators=["app.api_v1.dxf_workflow"],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[
            "packages/client/src/views/DxfToGcodeWizard.vue",
        ],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="EXPLICITLY_NON_PRODUCTION",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/api_v1/dxf_workflow.py",
                "Placeholder toolpath comment in the G-code wrapper.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="HIGH",
    ),
    "vision": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/vision/photo-to-gcode segments a photo, plans via "
            "adaptive plan(), emits G-code. No RMOS feasibility gate on the "
            "vision entry. Independent of wrap even though both can call plan()."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="UNKNOWN",
        ungated_output_exposure="YES",
        generators=["app.vision.segmentation_router"],
        persistence_status="RUN_ARTIFACT",
        persistence_mechanism="CAS attachments kind=advisory",
        client_consumers=[],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/vision/segmentation_router.py",
                "Photo pipeline emits G-code without compute_feasibility_internal.",
            ),
            _ev(
                "INSUFFICIENT_EVIDENCE",
                "runtime photo POST",
                "Withheld: may invoke external/AI services. NOT_OBTAINED_SAFELY.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
    "headstock-transition": _overlay(
        surface_kind="manufacturing_capability",
        intent_contract=(
            "POST /api/headstock/transition/gcode is ball-nose 3-axis finish of "
            "the headstock/neck blend. Distinct operation from full-neck OP10–40 "
            "and from guitar project neck stub. No RMOS."
        ),
        authority_status="NONE",
        evaluator=None,
        policy_boundary=None,
        generation_ordering="GENERATION_WITHOUT_AUTHORITY",
        input_contract_status="UNKNOWN",
        ungated_output_exposure="YES",
        generators=["app.routers.neck.headstock_transition_export"],
        persistence_status="NONE",
        persistence_mechanism=None,
        client_consumers=[],
        reachability="MOUNTED",
        runtime_evidence="NOT_OBTAINED_SAFELY",
        authority_disposition="LIVE_UNGOVERNED_OUTPUT",
        evidence=[
            _ev(
                "STATIC_CODE_TRACE",
                "services/api/app/routers/neck/headstock_transition_export.py",
                "No RMOS gate. Client can also build G-code locally.",
            ),
        ],
        evidence_class="STATIC_CODE_TRACE",
        confidence="MEDIUM",
    ),
}


def infer_surface_kind(capability_id: str) -> str:
    overlay = STAGE2_BY_ID.get(capability_id)
    if overlay:
        return overlay["surface_kind"]
    if capability_id == "feeds-speeds":
        return "advisory"
    if capability_id in {"operator-pack", "saw-batch"}:
        return "artifact_retrieval"
    if capability_id == "geometry":
        return "artifact_transformation"
    return "manufacturing_capability"


def apply_stage2(skeleton: Dict[str, Any]) -> Dict[str, Any]:
    """Return a Stage-2 registry. Does not write files. Preserves inventory routes."""
    out = dict(skeleton)
    out["stage"] = "stage_2_authority"
    out["surface_kind_vocabulary"] = list(SURFACE_KIND_VOCABULARY)
    caps = []
    missing = []
    for cap in skeleton.get("capabilities") or []:
        cid = cap["capability_id"]
        extra = STAGE2_BY_ID.get(cid)
        merged = dict(cap)
        if extra is None:
            missing.append(cid)
            merged.setdefault("surface_kind", infer_surface_kind(cid))
            merged.setdefault("generation_ordering", "UNKNOWN")
            merged.setdefault("input_contract_status", "UNKNOWN")
            merged.setdefault("ungated_output_exposure", "UNKNOWN")
            caps.append(merged)
            continue
        routes = cap.get("routes") or []
        grouping = cap.get("grouping_rule")
        artifacts = cap.get("artifact_types")
        mounted_ev = {
            "class": "MOUNTED_ROUTE_TABLE",
            "ref": "app.main:app",
            "note": "Stage 2: inventory routes unchanged; authority fields from static trace + safe witnesses.",
        }
        merged.update(extra)
        merged["routes"] = routes
        merged["grouping_rule"] = grouping
        merged["artifact_types"] = artifacts
        merged["operation_family"] = cap.get("operation_family", cid)
        evidence = [mounted_ev, *list(extra.get("evidence") or [])]
        merged["evidence"] = evidence
        caps.append(merged)
    out["capabilities"] = caps
    if missing:
        out.setdefault("unexplained_emitters", [])
        # Taxonomy gap, not an emitter: recorded so validate can fail loudly.
        out["_stage2_unclassified_capabilities"] = missing
    return out
