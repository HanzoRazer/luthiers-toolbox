"""CLI exit-code and output tests (local-only claims; no network)."""

from __future__ import annotations

import json

from tools.grounding_agent import cli

LANE = {
    "project": "p",
    "active_repository": "HanzoRazer/luthiers-toolbox",
    "active_program": "prog",
    "active_order": "ord",
    "active_state": "IMPLEMENTATION",
    "cross_repo_policy": "EVIDENCE_ONLY",
}


def _write_request(tmp_path, claims):
    path = tmp_path / "request.json"
    path.write_text(json.dumps({"active_lane": LANE, "claims": claims}), encoding="utf-8")
    return str(path)


def test_cli_match_exit_0(tmp_path, capsys):
    present = tmp_path / "here.txt"
    present.write_text("x")
    req = _write_request(tmp_path, [
        {"claim_id": "C-1", "type": "local_path_exists", "path": str(present),
         "expected": True, "material": True},
    ])
    rc = cli.main(["--request", req])
    out = json.loads(capsys.readouterr().out)
    assert rc == cli.EXIT_MATCH
    assert out["status"] == "MATCH"
    assert out["decision"] == "PROCEED"


def test_cli_stale_exit_2(tmp_path, capsys):
    req = _write_request(tmp_path, [
        {"claim_id": "C-1", "type": "local_path_exists", "path": str(tmp_path / "nope.txt"),
         "expected": True, "material": True},
    ])
    rc = cli.main(["--request", req])
    out = json.loads(capsys.readouterr().out)
    assert rc == cli.EXIT_STALE
    assert out["status"] == "STALE"
    assert out["material_divergences"] == ["C-1"]


def test_cli_insufficient_exit_4(tmp_path, capsys):
    # active_lane claim missing target_repository -> INSUFFICIENT_EVIDENCE (material).
    req = _write_request(tmp_path, [
        {"claim_id": "C-1", "type": "active_lane", "action": "evidence", "material": True},
    ])
    rc = cli.main(["--request", req])
    out = json.loads(capsys.readouterr().out)
    assert rc == cli.EXIT_INSUFFICIENT
    assert out["status"] == "INSUFFICIENT_EVIDENCE"


def test_cli_malformed_request_exit_5(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    rc = cli.main(["--request", str(bad)])
    assert rc == cli.EXIT_TOOL_ERROR


def test_cli_missing_active_lane_exit_5(tmp_path):
    path = tmp_path / "r.json"
    path.write_text(json.dumps({"claims": [{"claim_id": "C", "type": "worktree_clean"}]}), encoding="utf-8")
    rc = cli.main(["--request", str(path)])
    assert rc == cli.EXIT_TOOL_ERROR


def test_cli_writes_output_file(tmp_path):
    present = tmp_path / "here.txt"
    present.write_text("x")
    req = _write_request(tmp_path, [
        {"claim_id": "C-1", "type": "local_path_exists", "path": str(present),
         "expected": True, "material": False},
    ])
    out_path = tmp_path / "report.json"
    rc = cli.main(["--request", req, "--output", str(out_path), "--pretty"])
    assert rc == cli.EXIT_MATCH
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "grounding_report_v0.1"
