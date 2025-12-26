import json
import os
import subprocess
import sys


def test_feature_hunt_cli_emits_json(tmp_path):
    report_path = tmp_path / "feature_hunt.json"
    env = dict(os.environ)
    env["APP_MODULE"] = env.get("APP_MODULE", "app.main:app")

    # If truth map missing in test env, we still want a JSON output.
    # The CLI will just compare against empty truth list.
    cmd = [
        sys.executable,
        "-m",
        "app.ci.feature_hunt",
        "--out",
        str(report_path),
        "--truth",
        env.get("ENDPOINT_TRUTH_MAP_PATH", "ENDPOINT_TRUTH_MAP.md"),
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert report_path.exists(), f"report not written; stdout={proc.stdout} stderr={proc.stderr}"

    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert "counts" in data
    assert "app_endpoints" in data["counts"]
