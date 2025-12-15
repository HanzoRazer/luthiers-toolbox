# scripts/rmos_ci_test.py
import json
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict

import requests


BASE_URL = os.environ.get("RMOS_BASE_URL", "http://127.0.0.1:8000/rmos")
APP_MODULE = os.environ.get("APP_MODULE", "app.main:app")


def log(msg: str) -> None:
    print(f"[RMOS-CI] {msg}", flush=True)


def start_server() -> subprocess.Popen:
    """
    Start uvicorn with the configured app module.
    Returns the Popen handle.
    """
    log(f"Starting uvicorn {APP_MODULE} on 127.0.0.1:8000...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", APP_MODULE, "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc


def wait_for_server(timeout: float = 20.0) -> None:
    """
    Poll the base URL until the server responds or timeout is reached.
    """
    deadline = time.time() + timeout
    url = BASE_URL.rstrip("/") + "/joblog"
    while time.time() < deadline:
        try:
            log(f"Checking server at {url} ...")
            resp = requests.get(url, timeout=2.0)
            if resp.status_code in (200, 404):  # joblog may be empty / not mounted yet
                log("Server is up.")
                return
        except Exception:
            pass
        time.sleep(1.0)
    raise RuntimeError("Server did not become ready in time")


def request(
    method: str,
    path: str,
    json_body: Dict[str, Any] | None = None,
) -> Any:
    url = BASE_URL.rstrip("/") + path
    log(f"{method} {url}")
    try:
        resp = requests.request(method, url, json=json_body, timeout=10.0)
    except Exception as exc:
        raise RuntimeError(f"Request failed: {method} {url}: {exc}") from exc

    if resp.status_code >= 400:
        raise RuntimeError(f"Request error {resp.status_code}: {method} {url}: {resp.text}")

    if resp.content:
        try:
            return resp.json()
        except Exception:
            return resp.text
    return None


def main() -> int:
    proc: subprocess.Popen | None = None
    try:
        proc = start_server()
        time.sleep(2.0)
        wait_for_server()

        # 1) Create a smoke-test rosette pattern
        ts = int(time.time())
        pattern_id = f"ci_rosette_{ts}"
        pattern_payload = {
            "id": pattern_id,
            "name": f"CI Rosette {ts}",
            "center_x_mm": 0,
            "center_y_mm": 0,
            "ring_bands": [
                {
                    "id": "ring0",
                    "index": 0,
                    "radius_mm": 45,
                    "width_mm": 2,
                    "color_hint": "bw_outer",
                    "strip_family_id": "bw_checker_main",
                    "slice_angle_deg": 0,
                    "tile_length_override_mm": None,
                },
                {
                    "id": "ring1",
                    "index": 1,
                    "radius_mm": 48,
                    "width_mm": 2,
                    "color_hint": "bw_inner",
                    "strip_family_id": "bw_checker_main",
                    "slice_angle_deg": 0,
                    "tile_length_override_mm": None,
                },
            ],
            "default_slice_thickness_mm": 1.0,
            "default_passes": 1,
            "default_workholding": "vacuum",
            "default_tool_id": "saw_default",
        }

        log("Creating CI rosette pattern...")
        created_pattern = request("POST", "/rosette/patterns", pattern_payload)
        log(f"Pattern created: id={created_pattern['id']}")

        # 2) Manufacturing plan (also writes rosette_plan JobLog)
        plan_req = {
            "pattern_id": pattern_id,
            "guitars": 4,
            "tile_length_mm": 8.0,
            "scrap_factor": 0.12,
            "record_joblog": True,
        }
        log("Requesting manufacturing plan...")
        plan = request("POST", "/rosette/manufacturing-plan", plan_req)
        log(
            f"Plan ok: pattern={plan['pattern']['name']}, "
            f"guitars={plan['guitars']}, "
            f"families={len(plan['strip_plans'])}"
        )

        # 3) Single-slice circle preview
        circle_op = {
            "id": f"ci_slice_circle_{ts}",
            "op_type": "saw_slice",
            "tool_id": "saw_default",
            "geometry_source": "circle_param",
            "circle": {"center_x_mm": 0, "center_y_mm": 0, "radius_mm": 50},
            "line": None,
            "dxf_path": None,
            "slice_thickness_mm": 1.0,
            "passes": 1,
            "material": "hardwood",
            "workholding": "vacuum",
            "risk_options": {
                "allow_aggressive": False,
                "machine_gantry_span_mm": 1200.0,
            },
        }
        log("Requesting single-slice circle preview...")
        circle_res = request("POST", "/saw-ops/slice/preview", circle_op)
        log(f"Circle slice risk: {circle_res['risk']['risk_grade']}")

        # 4) Batch preview (circle_param)
        batch_id = f"ci_batch_{ts}"
        batch_op = {
            "id": batch_id,
            "op_type": "saw_slice_batch",
            "tool_id": "saw_default",
            "geometry_source": "circle_param",
            "base_circle": {
                "center_x_mm": 0,
                "center_y_mm": 0,
                "radius_mm": 45,
            },
            "num_rings": 2,
            "radial_step_mm": 3,
            "radial_sign": 1,
            "slice_thickness_mm": 1.0,
            "passes": 1,
            "material": "hardwood",
            "workholding": "vacuum",
        }
        log("Requesting batch preview...")
        batch_res = request("POST", "/saw-ops/batch/preview", batch_op)
        log(
            f"Batch preview ok: slices={batch_res['num_slices']}, "
            f"overall={batch_res['overall_risk_grade']}"
        )

        # 5) JobLog sanity
        log("Fetching JobLog entries...")
        joblog = request("GET", "/joblog") or []
        if isinstance(joblog, list):
            log(f"JobLog entries: {len(joblog)} (CI expects >= 1 after plan)")
            if not joblog:
                raise RuntimeError("JobLog is empty after CI plan run")
        else:
            raise RuntimeError("JobLog response is not a list")

        log("RMOS CI smoke test completed SUCCESSFULLY.")
        return 0

    except Exception as exc:
        log(f"ERROR: {exc}")
        return 1
    finally:
        if proc is not None:
            log("Shutting down uvicorn...")
            try:
                proc.send_signal(signal.SIGINT)
            except Exception:
                pass
            try:
                proc.wait(timeout=5.0)
            except Exception:
                proc.kill()
                proc.wait()


if __name__ == "__main__":
    sys.exit(main())
