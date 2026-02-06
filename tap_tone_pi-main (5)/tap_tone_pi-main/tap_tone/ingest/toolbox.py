# tap_tone/ingest/toolbox.py
"""ToolBox ZIP ingest — POST viewer_pack to RMOS acoustics import endpoint.

Usage:
    from tap_tone.ingest import ingest_zip

    result = ingest_zip(
        zip_path="/path/to/viewer_pack.zip",
        ingest_url="http://localhost:8000",
    )
    if result.ok:
        print(f"Ingested: {result.run_id}")
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import json


@dataclass
class IngestResult:
    """Result from ToolBox ingest attempt."""

    ok: bool
    http_status: Optional[int]
    run_id: Optional[str]
    error: Optional[str]
    payload: Optional[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Return dict for JSON serialization."""
        return {
            "attempted": True,
            "ok": self.ok,
            "http_status": self.http_status,
            "run_id": self.run_id,
            "error": self.error,
        }


# Endpoint path (matches shipped ToolBox API)
INGEST_ENDPOINT = "/api/rmos/acoustics/import-zip"


def ingest_zip(
    zip_path: Path | str,
    *,
    ingest_url: str = "http://localhost:8000",
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    timeout_s: float = 30.0,
) -> IngestResult:
    """
    POST a viewer_pack ZIP to ToolBox for import.

    Args:
        zip_path: Path to the viewer_pack_v1.zip file
        ingest_url: Base URL of ToolBox (default: http://localhost:8000)
        session_id: Optional session ID for grouping
        batch_label: Optional batch label for grouping
        timeout_s: Request timeout in seconds

    Returns:
        IngestResult with status, run_id (on success), or error details

    Notes:
        - Never raises exceptions — all errors are captured in IngestResult
        - ZIP file is never deleted, even on failure
        - Uses requests library (lazy import)
    """
    zip_path = Path(zip_path)

    if not zip_path.exists():
        return IngestResult(
            ok=False,
            http_status=None,
            run_id=None,
            error=f"ZIP file not found: {zip_path}",
            payload=None,
        )

    # Lazy import requests
    try:
        import requests
    except ImportError:
        return IngestResult(
            ok=False,
            http_status=None,
            run_id=None,
            error="requests library not installed (pip install requests)",
            payload=None,
        )

    url = f"{ingest_url.rstrip('/')}{INGEST_ENDPOINT}"

    # Build multipart form data
    try:
        with open(zip_path, "rb") as f:
            files = {"file": (zip_path.name, f, "application/zip")}
            data: dict[str, str] = {}
            if session_id:
                data["session_id"] = session_id
            if batch_label:
                data["batch_label"] = batch_label

            try:
                resp = requests.post(url, files=files, data=data, timeout=timeout_s)
            except requests.exceptions.ConnectionError:
                return IngestResult(
                    ok=False,
                    http_status=None,
                    run_id=None,
                    error=f"Connection failed: {ingest_url} (is ToolBox running?)",
                    payload=None,
                )
            except requests.exceptions.Timeout:
                return IngestResult(
                    ok=False,
                    http_status=None,
                    run_id=None,
                    error=f"Request timed out after {timeout_s}s",
                    payload=None,
                )
            except requests.exceptions.RequestException as e:
                return IngestResult(
                    ok=False,
                    http_status=None,
                    run_id=None,
                    error=f"Request error: {e}",
                    payload=None,
                )

    except OSError as e:
        return IngestResult(
            ok=False,
            http_status=None,
            run_id=None,
            error=f"Cannot read ZIP: {e}",
            payload=None,
        )

    # Parse response
    try:
        payload = resp.json()
    except (json.JSONDecodeError, ValueError):
        payload = {"raw": resp.text[:500]}

    if resp.status_code in (200, 201):
        # Success
        run_id = payload.get("run_id") or payload.get("id")
        return IngestResult(
            ok=True,
            http_status=resp.status_code,
            run_id=run_id,
            error=None,
            payload=payload,
        )

    # Error response
    error_msg = payload.get("detail") or payload.get("error") or payload.get("message")
    if not error_msg and isinstance(payload.get("raw"), str):
        error_msg = payload["raw"]
    if not error_msg:
        error_msg = f"HTTP {resp.status_code}"

    return IngestResult(
        ok=False,
        http_status=resp.status_code,
        run_id=None,
        error=error_msg,
        payload=payload,
    )
