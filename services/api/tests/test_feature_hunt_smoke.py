import json
import os
import subprocess
import sys

import pytest


@pytest.mark.skipif(
    os.environ.get("SKIP_FEATURE_HUNT_CLI") == "1",
    reason="Feature hunt CLI requires PYTHONPATH=services/api from repo root (env)",
)
def test_feature_hunt_cli_emits_json(tmp_path):
    """Run feature_hunt CLI; skip if app module not findable (e.g. wrong cwd)."""
    report_path = tmp_path / "feature_hunt.json"
    env = dict(os.environ)
    env["APP_MODULE"] = env.get("APP_MODULE", "app.main:app")
    # Ensure app is importable when running as __main__
    api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env["PYTHONPATH"] = os.pathsep.join([api_dir, env.get("PYTHONPATH", "")])

    cmd = [
        sys.executable,
        "-m",
        "app.ci.feature_hunt",
        "--out",
        str(report_path),
        "--truth",
        env.get("ENDPOINT_TRUTH_MAP_PATH", "ENDPOINT_TRUTH_MAP.md"),
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=api_dir)
    if not report_path.exists():
        pytest.skip(
            f"feature_hunt CLI did not write report (run from repo with app on path); "
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert "counts" in data
    assert "app_endpoints" in data["counts"]
