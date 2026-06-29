#!/usr/bin/env python3
"""Unit tests for wait_for_api_ready (CI-RED-020-A).

Stdlib-only: no FastAPI/uvicorn/requests. Probing is exercised against a real
stdlib http.server (success/fallback) and via monkeypatched probe/process_alive
(timeout/dead-pid/log-tail) for determinism.

Run:
    python scripts/ci/test_wait_for_api_ready.py
    python -m pytest scripts/ci/test_wait_for_api_ready.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wait_for_api_ready as mod  # noqa: E402


class _Handler(BaseHTTPRequestHandler):
    # Map path -> status code, and (optionally) path -> JSON body, per server.
    def do_GET(self):  # noqa: N802
        code = self.server.path_status.get(self.path, 404)  # type: ignore[attr-defined]
        body = self.server.path_body.get(self.path, '{"status":"ok"}')  # type: ignore[attr-defined]
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *args):  # silence
        pass


class _Server:
    """Context-managed throwaway HTTP server on an ephemeral port."""

    def __init__(self, path_status, path_body=None):
        self.httpd = HTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.path_status = path_status  # type: ignore[attr-defined]
        self.httpd.path_body = path_body or {}  # type: ignore[attr-defined]
        self.port = self.httpd.server_address[1]

    def __enter__(self):
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.port}"


class WaitForReadyTests(unittest.TestCase):
    def test_success_first_path(self):
        with _Server({"/api/health": 200, "/health": 200}) as srv:
            path = mod.wait_for_ready(
                srv.base_url, ["/api/health", "/health"],
                timeout_seconds=5, interval_seconds=0.05,
            )
            self.assertEqual(path, "/api/health")

    def test_fallback_to_second_path_when_first_404(self):
        with _Server({"/api/health": 404, "/health": 200}) as srv:
            path = mod.wait_for_ready(
                srv.base_url, ["/api/health", "/health"],
                timeout_seconds=5, interval_seconds=0.05,
            )
            self.assertEqual(path, "/health", "should fall back past the 404 path")

    def test_connection_failure_recorded_as_transport_error(self):
        # Nothing listening on this port -> every probe hits the transport-failure
        # branch (status None, error repr captured), NOT an HTTP status code.
        # This is the genuine connection-refused path; a shared base+path cannot
        # express a per-path transport failure, so it is exercised standalone.
        with self.assertRaises(mod.ReadinessError) as ctx:
            mod.wait_for_ready(
                "http://127.0.0.1:9", ["/health"],
                timeout_seconds=0.3, interval_seconds=0.05,
            )
        status, err = ctx.exception.last["/health"]
        self.assertIsNone(status, "transport failure must not surface as an HTTP code")
        self.assertIsNotNone(err, "the connection error repr should be captured")

    def test_timeout_when_no_path_ready(self):
        ticks = iter([0.0, 0.1, 0.2, 99.0])  # last tick blows past the deadline

        def fake_clock():
            return next(ticks)

        with _Server({"/api/health": 503, "/health": 500}) as srv:
            with self.assertRaises(mod.ReadinessError) as ctx:
                mod.wait_for_ready(
                    srv.base_url, ["/api/health", "/health"],
                    timeout_seconds=1, interval_seconds=0.01,
                    clock=fake_clock, sleep=lambda s: None,
                )
            self.assertIn("timed out", ctx.exception.reason)
            # Last results recorded per path (503 / 500), not a bare refusal.
            self.assertEqual(ctx.exception.last["/api/health"][0], 503)

    def test_dead_pid_fails_fast(self):
        # PID file present; process_alive forced False -> immediate failure,
        # well before the (large) timeout would expire.
        original = mod.process_alive
        mod.process_alive = lambda pid: False
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix="_pid") as pf:
                pf.write("424242")
                pid_path = pf.name
            with self.assertRaises(mod.ReadinessError) as ctx:
                mod.wait_for_ready(
                    "http://127.0.0.1:9",  # nothing listening
                    ["/health"],
                    timeout_seconds=999, interval_seconds=0.01,
                    pid_file=pid_path,
                )
            self.assertIn("exited before readiness", ctx.exception.reason)
        finally:
            mod.process_alive = original
            os.unlink(pid_path)

    def test_failure_output_includes_paths_and_log_tail(self):
        last = {"/api/health": (503, None), "/health": (None, "ConnectionRefused")}
        err = mod.ReadinessError("timed out after 1s waiting for readiness", last)
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".log") as lf:
            lf.write("line1\nTRACEBACK boom\nImportError: no module xyz\n")
            log_path = lf.name
        try:
            out = mod._format_failure("http://127.0.0.1:8000", err, log_path)
        finally:
            os.unlink(log_path)
        self.assertIn("/api/health -> HTTP 503", out)
        self.assertIn("/health -> error ConnectionRefused", out)
        self.assertIn("ImportError: no module xyz", out)  # log tail surfaced
        self.assertIn("timed out", out)

    def test_no_third_party_imports(self):
        # The module must rely only on the stdlib.
        import inspect
        src = inspect.getsource(mod)
        for banned in ("import requests", "import httpx", "import fastapi", "import uvicorn"):
            self.assertNotIn(banned, src)

    def test_main_success_exit_zero(self):
        with _Server({"/health": 200}) as srv:
            rc = mod.main(["--base-url", srv.base_url, "--paths", "/health",
                           "--timeout-seconds", "5", "--interval-seconds", "0.05"])
            self.assertEqual(rc, 0)

    def test_main_timeout_exit_one(self):
        with _Server({"/health": 500}) as srv:
            rc = mod.main(["--base-url", srv.base_url, "--paths", "/health",
                           "--timeout-seconds", "0.2", "--interval-seconds", "0.05"])
            self.assertEqual(rc, 1)


class RequirementTests(unittest.TestCase):
    """--require body assertion (issue #165: 200 is not enough on degraded boot)."""

    def test_parse_requirement_variants(self):
        self.assertIsNone(mod.parse_requirement(None))
        self.assertIsNone(mod.parse_requirement(""))
        self.assertEqual(mod.parse_requirement("routers.loaded>0"), ("routers.loaded", ">", 0))
        self.assertEqual(mod.parse_requirement("routers.failed==0"), ("routers.failed", "==", 0))
        self.assertEqual(mod.parse_requirement("status=='healthy'"), ("status", "==", "healthy"))
        self.assertEqual(mod.parse_requirement("x>=1.5"), ("x", ">=", 1.5))
        with self.assertRaises(ValueError):
            mod.parse_requirement("routers.loaded")  # no operator
        with self.assertRaises(ValueError):
            mod.parse_requirement(">0")  # no key

    def test_compare_numeric_and_string(self):
        self.assertTrue(mod._compare(5, ">", 0))
        self.assertFalse(mod._compare(0, ">", 0))
        self.assertTrue(mod._compare(0, "==", 0))
        self.assertTrue(mod._compare("0", "==", 0))         # numeric-coerced equality
        self.assertTrue(mod._compare("healthy", "==", "healthy"))
        self.assertTrue(mod._compare("degraded", "!=", "healthy"))
        self.assertFalse(mod._compare("healthy", ">", 0))    # non-numeric ordering -> False

    def test_check_requirement_cases(self):
        ok, _ = mod.check_requirement('{"routers":{"loaded":50}}', ("routers.loaded", ">", 0))
        self.assertTrue(ok)
        ok, detail = mod.check_requirement('{"routers":{"loaded":0}}', ("routers.loaded", ">", 0))
        self.assertFalse(ok); self.assertIn("got 0", detail)
        ok, detail = mod.check_requirement('{"routers":{}}', ("routers.loaded", ">", 0))
        self.assertFalse(ok); self.assertIn("missing", detail)
        ok, detail = mod.check_requirement("not json", ("routers.loaded", ">", 0))
        self.assertFalse(ok); self.assertIn("not JSON", detail)
        # No requirement -> always ok.
        self.assertEqual(mod.check_requirement('{"x":1}', None), (True, ""))

    def test_require_gates_degraded_boot(self):
        # 200 but routers.loaded==0 (degraded boot) must NOT be treated as ready.
        with _Server({"/api/health": 200},
                     {"/api/health": '{"status":"degraded","routers":{"loaded":0,"failed":7}}'}) as srv:
            with self.assertRaises(mod.ReadinessError) as ctx:
                mod.wait_for_ready(
                    srv.base_url, ["/api/health"],
                    timeout_seconds=0.3, interval_seconds=0.05,
                    requirement=("routers.loaded", ">", 0),
                )
            status, note = ctx.exception.last["/api/health"]
            self.assertEqual(status, 200)            # got a 200...
            self.assertIn("routers.loaded>0", note)  # ...but the body gate failed

    def test_require_passes_on_healthy_boot(self):
        with _Server({"/api/health": 200},
                     {"/api/health": '{"status":"healthy","routers":{"loaded":120,"failed":0}}'}) as srv:
            path = mod.wait_for_ready(
                srv.base_url, ["/api/health"],
                timeout_seconds=5, interval_seconds=0.05,
                requirement=("routers.loaded", ">", 0),
            )
            self.assertEqual(path, "/api/health")

    def test_degraded_failure_output_names_the_gate(self):
        last = {"/api/health": (200, "require routers.loaded>0: got 0")}
        err = mod.ReadinessError("timed out after 1s waiting for readiness", last)
        out = mod._format_failure("http://127.0.0.1:8000", err, None)
        self.assertIn("HTTP 200 — require routers.loaded>0: got 0", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
