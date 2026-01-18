from __future__ import annotations


def test_toolpaths_lint_writes_artifact(monkeypatch):
    from app.saw_lab.toolpaths_lint_service import write_toolpaths_lint_report_artifact

    def _fake_validate(**kwargs):
        return {"ok": True, "errors": [], "warnings": [], "summary": {"units": "mm"}}

    def _fake_store_artifact(**kwargs):
        assert kwargs["kind"] == "saw_toolpaths_lint_report"
        assert kwargs["parent_id"] == "tp1"
        return "lint1"

    monkeypatch.setattr("app.saw_lab.toolpaths_lint_service.validate_toolpaths_artifact_static", _fake_validate)
    monkeypatch.setattr("app.rmos.runs_v2.store.store_artifact", _fake_store_artifact)

    out = write_toolpaths_lint_report_artifact(
        toolpaths_artifact_id="tp1",
        session_id="s1",
        batch_label="b1",
    )
    assert out["lint_artifact_id"] == "lint1"
    assert out["result"]["ok"] is True
