"""
AI Integrator CLI Runner

The "engine room" that invokes ai-integrator as a subprocess.
This is the ONLY seam between RMOS and ai-integrator.

Usage:
    from app.rmos.ai_advisory import run_ai_integrator_job
    draft = run_ai_integrator_job(context_packet)
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from .config import AiIntegratorConfig, get_config
from .exceptions import (
    AiIntegratorRuntime,
    exception_for_exit_code,
)


def run_ai_integrator_job(
    packet: Dict[str, Any],
    *,
    config: AiIntegratorConfig | None = None,
) -> Dict[str, Any]:
    """
    Invoke ai-integrator CLI with an AIContextPacket.

    Args:
        packet: The AIContextPacket dict (must have schema_id: ai_context_packet_v1)
        config: Optional config override (defaults to env-based config)

    Returns:
        The AdvisoryDraft dict produced by ai-integrator

    Raises:
        AiIntegratorSchema: Exit code 1 - schema validation error
        AiIntegratorGovernance: Exit code 2 - governance violation
        AiIntegratorRuntime: Exit code 3 - runtime error (timeout, binary not found, etc.)
        AiIntegratorUnsupported: Exit code 4 - unsupported job/template
    """
    cfg = config or get_config()

    # Ensure workdir exists (lazy creation)
    cfg.workdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=str(cfg.workdir)) as td:
        td_path = Path(td)
        in_path = td_path / "context.json"
        out_path = td_path / "draft.json"

        # Write input packet
        in_path.write_text(
            json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # Build command
        cmd = [
            cfg.bin_path,
            "run-job",
            "--in", str(in_path),
            "--out", str(out_path),
        ]

        # Execute CLI
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=cfg.timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise AiIntegratorRuntime(
                f"ai-integrator timed out after {cfg.timeout_sec}s",
                exit_code=3,
            ) from e
        except FileNotFoundError as e:
            raise AiIntegratorRuntime(
                f"ai-integrator binary not found: {cfg.bin_path}",
                exit_code=3,
            ) from e
        except OSError as e:
            raise AiIntegratorRuntime(
                f"Failed to execute ai-integrator: {e}",
                exit_code=3,
            ) from e

        # Handle success
        if proc.returncode == 0:
            if not out_path.exists():
                raise AiIntegratorRuntime(
                    "ai-integrator returned success but did not write draft.json",
                    exit_code=3,
                )
            try:
                draft = json.loads(out_path.read_text(encoding="utf-8"))
                return draft
            except json.JSONDecodeError as e:
                raise AiIntegratorRuntime(
                    f"ai-integrator produced invalid JSON: {e}",
                    exit_code=3,
                ) from e

        # Handle error exit codes
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        error_detail = stderr or stdout or f"exit code {proc.returncode}"

        raise exception_for_exit_code(proc.returncode, error_detail)
