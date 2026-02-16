# scripts/rmos_ci_test.py
import json
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict

import requests


BASE_URL = os.environ.get("RMOS_BASE_URL", "http://127.0.0.1:8000")
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
    Poll the health endpoint until the server responds or timeout is reached.
    """
    deadline = time.time() + timeout
    url = BASE_URL.rstrip("/") + "/api/health"
    while time.time() < deadline:
        try:
            log(f"Checking server at {url} ...")
            resp = requests.get(url, timeout=2.0)
            if resp.status_code in (200, 404):  # health endpoint may not exist yet
                log("Server is up.")
                return
        except requests.RequestException:
            pass  # Expected during server startup - retry
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

        # 1) RMOS Saw slice preview (simple geometry estimation)
        slice_req = {
            "geometry": {
                "type": "circle",
                "radius_mm": 50.0,
            },
            "tool_id": "saw_default",
            "cut_depth_mm": 3.0,
            "feed_rate_mm_min": 800.0,
        }
        log("Testing RMOS saw slice preview...")
        slice_res = request("POST", "/api/rmos/saw-ops/slice/preview", slice_req)
        log(f"Slice preview ok: path_length={slice_res['statistics']['path_length_mm']:.1f}mm")

        # 2) RMOS Pipeline handoff (queues a job)
        handoff_req = {
            "pattern_id": "ci_test_pattern",
            "tool_id": "saw_default",
            "material_id": "hardwood",
            "operation_type": "channel",
            "parameters": {},
        }
        log("Testing RMOS pipeline handoff...")
        handoff_res = request("POST", "/api/rmos/saw-ops/pipeline/handoff", handoff_req)
        log(f"Handoff ok: job_id={handoff_res['job_id']}, status={handoff_res['status']}")

        # 3) Health check endpoint
        log("Testing health endpoint...")
        health_res = request("GET", "/api/health")
        log(f"Health ok: status={health_res.get('status', 'unknown')}")

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
            except OSError:
                pass  # Process may have already exited
            try:
                proc.wait(timeout=5.0)
            except Exception:
                proc.kill()
                proc.wait()


if __name__ == "__main__":
    sys.exit(main())
