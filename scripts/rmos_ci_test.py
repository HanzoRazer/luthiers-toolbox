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

        # 1) Health check endpoint (basic connectivity)
        log("Testing health endpoint...")
        health_res = request("GET", "/health")
        log(f"Health ok: status={health_res.get('status', 'unknown')}")

        # 2) RMOS v1 Feasibility Check
        check_req = {
            "tool_diameter_mm": 6.0,
            "depth_of_cut_mm": 3.0,
            "stepover_percent": 40.0,
            "feed_xy_mm_min": 1000.0,
            "feed_z_mm_min": 200.0,
            "spindle_rpm": 18000,
            "material": "hardwood",
            "operation": "profile",
        }
        log("Testing RMOS v1 feasibility check...")
        check_res = request("POST", "/api/v1/rmos/check", check_req)
        decision = check_res.get("data", {}).get("decision", "unknown")
        log(f"Feasibility check ok: decision={decision}")

        # 3) RMOS v1 Create Run
        run_req = {
            "session_id": "ci_test_session",
            "operation": "profile",
            "parameters": {
                "tool_diameter_mm": 6.0,
                "depth_of_cut_mm": 3.0,
                "stepover_percent": 40.0,
                "feed_xy": 1000.0,
                "feed_z": 200.0,
                "spindle_rpm": 18000,
                "material": "hardwood",
            },
        }
        log("Testing RMOS v1 create run...")
        run_res = request("POST", "/api/v1/rmos/runs", run_req)
        run_id = run_res.get("data", {}).get("run_id", "unknown")
        export_allowed = run_res.get("data", {}).get("export_allowed", False)
        log(f"Create run ok: run_id={run_id}, export_allowed={export_allowed}")

        # 4) RMOS v1 List Rules
        log("Testing RMOS v1 list rules...")
        rules_res = request("GET", "/api/v1/rmos/rules")
        rule_count = len(rules_res.get("data", {}).get("rules", []))
        log(f"List rules ok: {rule_count} rules defined")

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
