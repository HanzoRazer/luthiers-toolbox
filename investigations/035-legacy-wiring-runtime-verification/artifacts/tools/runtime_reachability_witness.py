#!/usr/bin/env python3
"""Investigation 035 Utility B — runtime reachability witness.

Supports the five manually chosen specimens plus instrument controls.
Does not assign D-status.

Spy discipline (from Vectorizer witness hazard):
  Patch the bound namespace the caller actually dereferences, not merely the
  defining module. Each specimen records spy location. Instrument controls
  IW-01/IW-02 prove the difference.

Containment:
  - filesystem writes go to artifacts/scratch (or LTB_035_SCRATCH)
  - outbound network is blocked except loopback
"""
from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from unittest.mock import patch

INVESTIGATION_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCRATCH = INVESTIGATION_ROOT / "artifacts" / "scratch"
PRODUCTION_SHA = os.environ.get(
    "LTB_PROD_SHA", "cab91edacaedc66a0492c35275ce2c255935bf8e"
)


@dataclass
class SpySpec:
    """Patch target: module_qualname.attr, counted under label."""

    module: str
    attr: str
    label: str


@dataclass
class WitnessResult:
    specimen: str
    production_sha: str
    entrypoint: str
    expected_implementation: str
    alternates: list[str]
    spy_location: dict[str, str]
    request: dict[str, Any]
    http_result: dict[str, Any]
    actual_calls: dict[str, int]
    terminal_effect: str
    consumer: str
    test_path_comparison_placeholder: str
    limitations: list[str]
    spy_control_fired: Optional[bool]
    exception: Optional[str] = None
    voided: bool = False
    void_reason: Optional[str] = None


class CallCounter:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.events: list[dict[str, Any]] = []

    def wrap(self, label: str, original: Callable) -> Callable:
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            self.counts[label] = self.counts.get(label, 0) + 1
            self.events.append({"label": label, "argc": len(args), "kwargs": list(kwargs)})
            return original(*args, **kwargs)

        _wrapped.__name__ = getattr(original, "__name__", label)
        _wrapped.__qualname__ = getattr(original, "__qualname__", label)
        return _wrapped


def _block_network() -> Any:
    """Replace socket.create_connection so non-loopback connects fail."""
    real_create = socket.create_connection

    def guarded(address, timeout=None, source_address=None, *, all_errors=False):
        host = address[0] if isinstance(address, tuple) else address
        if host in {"127.0.0.1", "::1", "localhost"}:
            return real_create(address, timeout, source_address)
        raise RuntimeError(
            f"035 witness blocked external network connect to {address!r}"
        )

    return patch("socket.create_connection", guarded)


@contextmanager
def scratch_space(scratch: Optional[Path] = None):
    root = Path(scratch or os.environ.get("LTB_035_SCRATCH", DEFAULT_SCRATCH))
    root.mkdir(parents=True, exist_ok=True)
    td = tempfile.mkdtemp(prefix="witness-", dir=str(root))
    yield Path(td)


def install_spies(specs: list[SpySpec], counter: CallCounter) -> list[Any]:
    patches = []
    for spec in specs:
        target = f"{spec.module}.{spec.attr}"
        import importlib

        mod = importlib.import_module(spec.module)
        original = getattr(mod, spec.attr)
        p = patch(target, counter.wrap(spec.label, original))
        p.start()
        patches.append(p)
        counter.counts.setdefault(spec.label, 0)
    return patches


def stop_spies(patches: list[Any]) -> None:
    for p in reversed(patches):
        try:
            p.stop()
        except Exception:  # noqa: BLE001
            pass


def _jsonable_body(response) -> Any:
    ctype = (response.headers.get("content-type") or "").lower()
    text = response.text
    snippet = text[:800]
    body: dict[str, Any] = {
        "status_code": response.status_code,
        "content_type": ctype,
        "text_snippet": snippet,
        "headers": {
            k: v
            for k, v in response.headers.items()
            if k.lower().startswith("x-cam") or k.lower() in {"content-type", "content-disposition"}
        },
    }
    if "application/json" in ctype:
        try:
            body["json"] = response.json()
        except Exception:
            body["json_error"] = True
    return body


def run_http_specimen(
    *,
    specimen: str,
    entrypoint: str,
    method: str,
    path: str,
    expected_implementation: str,
    alternates: list[str],
    spies: list[SpySpec],
    json_body: Optional[dict] = None,
    files: Optional[dict] = None,
    data: Optional[dict] = None,
    consumer: str,
    limitations: list[str],
    spy_control: Optional[Callable] = None,
) -> WitnessResult:
    """Drive current production TestClient and count bound-name spies."""
    from fastapi.testclient import TestClient

    limitations = list(limitations)
    counter = CallCounter()
    patches: list[Any] = []
    http_result: dict[str, Any] = {}
    exception = None
    spy_control_fired = None
    terminal = "unrecorded"

    with _block_network(), scratch_space() as tmp:
        os.environ.setdefault("LTB_035_WITNESS_TMP", str(tmp))
        try:
            from app.main import app

            patches = install_spies(spies, counter)
            if spy_control is not None:
                spy_control_fired = bool(spy_control(app, counter))
            with TestClient(app, raise_server_exceptions=False) as client:
                fn = getattr(client, method.lower())
                kwargs: dict[str, Any] = {}
                if json_body is not None:
                    kwargs["json"] = json_body
                if files is not None:
                    kwargs["files"] = files
                if data is not None:
                    kwargs["data"] = data
                response = fn(path, **kwargs)
                http_result = _jsonable_body(response)
                terminal = f"HTTP {response.status_code}"
        except Exception as exc:  # noqa: BLE001
            exception = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            terminal = f"EXCEPTION {type(exc).__name__}"
            limitations.append("request aborted by exception; see exception field")
        finally:
            stop_spies(patches)

    spy_loc = {s.label: f"{s.module}.{s.attr}" for s in spies}
    fired = [k for k, n in counter.counts.items() if n]
    actual = (
        ",".join(fired)
        if fired
        else "NO_SPIED_IMPLEMENTATION_CALLED"
    )

    return WitnessResult(
        specimen=specimen,
        production_sha=PRODUCTION_SHA,
        entrypoint=entrypoint,
        expected_implementation=expected_implementation,
        alternates=alternates,
        spy_location=spy_loc,
        request={
            "method": method,
            "path": path,
            "json_body": json_body,
            "files": list(files) if files else None,
        },
        http_result=http_result,
        actual_calls=dict(counter.counts),
        terminal_effect=f"{terminal}; spies={actual}",
        consumer=consumer,
        test_path_comparison_placeholder="see artifacts/TEST_RUNTIME_COMPARISON.md",
        limitations=limitations,
        spy_control_fired=spy_control_fired,
        exception=exception,
    )


def result_to_dict(r: WitnessResult) -> dict[str, Any]:
    return {
        "SPECIMEN": r.specimen,
        "PRODUCTION_SHA": r.production_sha,
        "ENTRYPOINT": r.entrypoint,
        "EXPECTED_IMPLEMENTATION": r.expected_implementation,
        "ALTERNATES": r.alternates,
        "SPY_LOCATION": r.spy_location,
        "REQUEST_OR_INVOCATION": r.request,
        "HTTP_CLI_RESULT": r.http_result,
        "ACTUAL_CALLS": r.actual_calls,
        "TERMINAL_EFFECT": r.terminal_effect,
        "CONSUMER": r.consumer,
        "TEST_PATH_COMPARISON": r.test_path_comparison_placeholder,
        "LIMITATIONS": r.limitations,
        "SPY_CONTROL_FIRED": r.spy_control_fired,
        "EXCEPTION": r.exception,
        "VOIDED": r.voided,
        "VOID_REASON": r.void_reason,
        "COLLECTED_AT_UTC": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "D_STATUS_ASSIGNED_BY_THIS_TOOL": False,
    }


# ---------------------------------------------------------------------------
# Manually frozen specimens (see artifacts/CANDIDATE_SELECTION.md)
# ---------------------------------------------------------------------------

SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0], [0.0, 0.0]]
GCODE_TINY = "G21\nG90\nG0 X0 Y0 Z5\nG1 X10 Y0 F300\nG1 X10 Y10\nM30\n"


def specimen_cam_sim_fe() -> WitnessResult:
    """S1 — FE SimLab path POST /api/cam/simulate_gcode."""
    return run_http_specimen(
        specimen="S1_CAM_SIM_FE_PATH",
        entrypoint="POST /api/cam/simulate_gcode  (SimLab.vue / useGcodeSimulation.ts)",
        method="POST",
        path="/api/cam/simulate_gcode",
        expected_implementation="app.routers.simulation_consolidated_router.simulate_gcode_json",
        alternates=[
            "app.cam.routers.simulation.simulation_consolidated_router.simulate_gcode",
            "app.routers.gcode_consolidated_router.simulate_gcode",
            "app.routers.simulation_consolidated_router.simulate_gcode_legacy",
        ],
        spies=[
            SpySpec(
                "app.routers.simulation_consolidated_router",
                "simulate_gcode_json",
                "expected_sim_json",
            ),
            SpySpec(
                "app.routers.simulation_consolidated_router",
                "simulate_gcode_legacy",
                "alternate_sim_legacy_under_sim_prefix",
            ),
            SpySpec(
                "app.routers.gcode_consolidated_router",
                "simulate_gcode",
                "alternate_gcode_consolidated_simulate",
            ),
        ],
        json_body={"gcode": GCODE_TINY},
        consumer="packages/client SimLab.vue, SimLabWorker.vue, GeometryOverlay.vue, bridge_lab/useGcodeSimulation.ts",
        limitations=[
            "Disabled package app.cam.routers.simulation is not imported by aggregator (simulation_router=None); cannot spy a never-imported handler without importing it (which would not be the production path).",
            "Spy targets are the live simulation_consolidated_router functions as bound on that module; FastAPI stores the function object at include_router time, so these patches match the production dereference if the route is hit.",
        ],
    )


def specimen_soundhole_post() -> WitnessResult:
    """S2 — POST /api/instrument/soundhole dual mount."""
    return run_http_specimen(
        specimen="S2_SOUNDHOLE_POST_DUAL_MOUNT",
        entrypoint="POST /api/instrument/soundhole",
        method="POST",
        path="/api/instrument/soundhole",
        expected_implementation="app.routers.instrument_geometry.soundhole_router.calculate_soundhole → soundhole_facade.compute_soundhole_spec",
        alternates=[
            "app.routers.instrument_router.get_soundhole_spec",
            "app.routers.instrument.soundhole_router.calculate_soundhole",
        ],
        spies=[
            SpySpec(
                "app.routers.instrument_geometry.soundhole_router",
                "calculate_soundhole",
                "expected_geometry_router",
            ),
            SpySpec(
                "app.routers.instrument_router",
                "get_soundhole_spec",
                "alternate_legacy_instrument_router",
            ),
            SpySpec(
                "app.calculators.soundhole_facade",
                "compute_soundhole_spec",
                "shared_facade_compute",
            ),
        ],
        json_body={
            "body_style": "dreadnought",
            "body_length_mm": 500.0,
            "soundhole_type": "spiral",
        },
        consumer="instrument geometry UI / spiral type dropdown via /api/instrument/soundhole",
        limitations=[
            "Both live POST handlers ultimately call soundhole_facade.compute_soundhole_spec; a facade spy firing does not by itself identify which HTTP handler won.",
            "instrument.soundhole_router (thin calc-only) is not expected to be mounted on this path; absence of that spy is not a defect by itself.",
        ],
    )


def specimen_polygon_offset_nc() -> WitnessResult:
    """S3 — POST /api/cam/polygon_offset.nc dual mount (OffsetLab FE schema)."""
    return run_http_specimen(
        specimen="S3_POLYGON_OFFSET_NC_DUAL_MOUNT",
        entrypoint="POST /api/cam/polygon_offset.nc  (OffsetLabView.vue default stepover=0.4)",
        method="POST",
        path="/api/cam/polygon_offset.nc",
        expected_implementation="app.routers.polygon_offset_router.polygon_offset_nc (governed; stepover fraction)",
        alternates=[
            "app.cam.routers.utility.polygon_router.polygon_offset (N17; stepover mm)",
        ],
        spies=[
            SpySpec(
                "app.routers.polygon_offset_router",
                "polygon_offset_nc",
                "expected_governed_nc",
            ),
            SpySpec(
                "app.cam.routers.utility.polygon_router",
                "polygon_offset",
                "alternate_utility_n17",
            ),
        ],
        json_body={
            "polygon": SQUARE,
            "tool_dia": 6.0,
            "stepover": 0.4,
            "link_mode": "arc",
            "units": "mm",
        },
        consumer="packages/client/src/views/OffsetLabView.vue getGcode(); n17_n18.ts also posts polygon_offset.nc",
        limitations=[
            "OffsetLab preview uses /polygon_offset.preview (governed-only in live_routes); NC uses /polygon_offset.nc (colliding).",
            "Utility handler schema uses absolute mm stepover; OffsetLab default 0.4 is the governed fraction convention.",
        ],
    )


def specimen_dxf_polyline_legacy() -> WitnessResult:
    """S4 — CurveMath FE POST /exports/polyline_dxf vs governed translate."""
    return run_http_specimen(
        specimen="S4_DXF_CURVEMATH_LEGACY_EXPORT",
        entrypoint="POST /exports/polyline_dxf  (packages/client/src/utils/curvemath_dxf.ts)",
        method="POST",
        path="/exports/polyline_dxf",
        expected_implementation="app.routers.export.dxf_translate_router.translate_to_dxf (governed dxf_compat R12/R2000)",
        alternates=[
            "app.routers.legacy_dxf_exports_router.export_polyline_dxf",
            "app.exports.dxf_helpers.try_build_with_ezdxf",
            "app.exports.dxf_helpers.build_ascii_r12",
        ],
        spies=[
            SpySpec(
                "app.routers.legacy_dxf_exports_router",
                "export_polyline_dxf",
                "actual_legacy_handler",
            ),
            SpySpec(
                "app.exports.dxf_helpers",
                "try_build_with_ezdxf",
                "legacy_ezdxf_helper",
            ),
            SpySpec(
                "app.exports.dxf_helpers",
                "build_ascii_r12",
                "legacy_ascii_r12_fallback",
            ),
            SpySpec(
                "app.routers.export.dxf_translate_router",
                "translate_to_dxf",
                "expected_governed_translate",
            ),
        ],
        json_body={"polyline": {"points": [[0, 0], [100, 0], [100, 50], [0, 50]]}},
        consumer="packages/client/src/utils/curvemath_dxf.ts",
        limitations=[
            "Governed translator expects Export Object JSON, not a raw polyline; FE CurveMath never posts /api/export/translate/dxf in this specimen.",
            "ASCII R12 fallback in the legacy handler is only a defect if ezdxf helper does not fire and ASCII is not the intended path for this consumer.",
        ],
    )


def specimen_fret_slots_preview() -> WitnessResult:
    """S5 — POST /api/cam/fret_slots/preview vs ecosphere DXF stack."""
    return run_http_specimen(
        specimen="S5_FRET_SLOTS_CAM_PREVIEW",
        entrypoint="POST /api/cam/fret_slots/preview  (fretSlotsCamStore.ts / instrumentGeometryStore.ts)",
        method="POST",
        path="/api/cam/fret_slots/preview",
        expected_implementation="app.cam.routers.fret_slots_router.preview_fret_slots → generate_fret_slot_toolpaths",
        alternates=[
            "app.calculators.fret_slots_fan_cam.generate_fan_fret_cam",
            "POST /api/v1/fretboard/dxf (ecosphere; not invoked by this request)",
        ],
        spies=[
            SpySpec(
                "app.cam.routers.fret_slots_router",
                "preview_fret_slots",
                "expected_preview_handler",
            ),
            SpySpec(
                "app.calculators.fret_slots_cam",
                "generate_fret_slot_toolpaths",
                "expected_standard_generator",
            ),
            SpySpec(
                "app.calculators.fret_slots_fan_cam",
                "generate_fan_fret_cam",
                "alternate_fan_generator",
            ),
        ],
        json_body={"model_id": "dreadnought", "fret_count": 20, "mode": "standard"},
        consumer="packages/client/src/stores/fretSlotsCamStore.ts; FretSlottingView.vue documents preview-only vs /api/v1/fretboard/dxf",
        limitations=[
            "This specimen does not POST /api/v1/fretboard/dxf; ecosphere is an alternate product path, not a runtime alternate for this URL.",
            "model_id may be missing from the registry; handler has an explicit default-scale fallback — that fallback is not automatically D3.",
        ],
    )


def specimen_vectorizer_control() -> WitnessResult:
    """IW-03 — current Toolbox Vectorizer healthy control (inexpensive POST)."""
    import io

    # 1x1 PNG
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return run_http_specimen(
        specimen="IW03_VECTORIZER_CONTROL",
        entrypoint="POST /api/blueprint/vectorize",
        method="POST",
        path="/api/blueprint/vectorize",
        expected_implementation="app.routers.blueprint.vectorize_router.vectorize_blueprint → BlueprintOrchestrator.process_file",
        alternates=[
            "photo vectorizer POST /api/vectorizer/extract (not invoked)",
        ],
        spies=[
            SpySpec(
                "app.routers.blueprint.vectorize_router",
                "vectorize_blueprint",
                "expected_vectorize_route",
            ),
        ],
        files={"file": ("tiny.png", io.BytesIO(png), "image/png")},
        consumer="control only — not a selected 035 specimen",
        limitations=[
            "Tiny synthetic PNG is not a real blueprint; the control asks whether the production route reaches vectorize_blueprint, not whether extraction quality is good.",
            "BlueprintOrchestrator.process_file is an instance method on a singleton; patching the bound method on the class is a different namespace. Route-function spy is the dereference FastAPI holds.",
        ],
    )


SPECIMEN_RUNNERS = {
    "s1": specimen_cam_sim_fe,
    "s2": specimen_soundhole_post,
    "s3": specimen_polygon_offset_nc,
    "s4": specimen_dxf_polyline_legacy,
    "s5": specimen_fret_slots_preview,
    "iw03": specimen_vectorizer_control,
}


def main(argv: list[str]) -> int:
    names = argv[1:] or list(SPECIMEN_RUNNERS)
    out_dir = INVESTIGATION_ROOT / "artifacts" / "census"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for name in names:
        key = name.lower()
        if key not in SPECIMEN_RUNNERS:
            print(f"unknown specimen {name}", file=sys.stderr)
            return 2
        print(f"--- running {key} ---", flush=True)
        result = SPECIMEN_RUNNERS[key]()
        d = result_to_dict(result)
        results.append(d)
        path = out_dir / f"WITNESS_{key.upper()}.json"
        path.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: d[k] for k in ("SPECIMEN", "HTTP_CLI_RESULT", "ACTUAL_CALLS", "TERMINAL_EFFECT")}, indent=2))
    bundle = out_dir / "WITNESS_BUNDLE.json"
    existing = []
    if bundle.exists() and argv[1:]:
        try:
            existing = json.loads(bundle.read_text(encoding="utf-8")).get("results", [])
        except Exception:
            existing = []
        labels = {r["SPECIMEN"] for r in results}
        existing = [r for r in existing if r.get("SPECIMEN") not in labels]
    bundle.write_text(
        json.dumps({"results": existing + results, "d_status_by_tool": False}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
