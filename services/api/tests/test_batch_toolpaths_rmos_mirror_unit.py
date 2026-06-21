from __future__ import annotations


class BatchToolpathsMirrorStubs:
    def __init__(self):
        self.saw_artifacts = {
            "spec-saw": {
                "payload": {
                    "batch_label": "batch-a",
                    "session_id": "session-a",
                    "tool_id": "saw:thin_140",
                    "items": [{"part_id": "part-1"}],
                }
            },
            "plan-saw": {
                "payload": {
                    "batch_spec_artifact_id": "spec-saw",
                    "batch_label": "batch-a",
                    "session_id": "session-a",
                    "setups": [{"setup_key": "setup_1", "tool_id": "saw:thin_140"}],
                }
            },
            "decision-saw": {
                "payload": {
                    "batch_plan_artifact_id": "plan-saw",
                    "batch_spec_artifact_id": "spec-saw",
                    "batch_label": "batch-a",
                    "session_id": "session-a",
                    "selected_setup_key": "setup_1",
                    "selected_op_ids": ["op_1"],
                }
            },
        }
        self.stored = []
        self.generated_ids = iter(
            ["spec-rmos", "plan-rmos", "decision-rmos", "exec-rmos"]
        )

    def get_artifact(self, artifact_id: str):
        return self.saw_artifacts.get(artifact_id)

    def store_artifact(self, **kwargs):
        artifact_id = next(self.generated_ids)
        self.stored.append({"id": artifact_id, **kwargs})
        return artifact_id


def _assert_toolpaths_response(response):
    assert response.batch_execution_artifact_id == "exec-rmos"
    assert response.batch_decision_artifact_id == "decision-rmos"
    assert response.batch_plan_artifact_id == "plan-rmos"
    assert response.batch_spec_artifact_id == "spec-rmos"
    assert response.batch_label == "batch-a"
    assert response.session_id == "session-a"
    assert response.results[0].toolpaths_artifact_id == "decision-rmos"


def _assert_store_call_shape(stored):
    assert [entry["kind"] for entry in stored] == [
        "saw_batch_spec",
        "saw_batch_plan",
        "saw_batch_decision",
        "saw_batch_execution",
    ]
    assert [entry["parent_id"] for entry in stored] == [
        None,
        "spec-rmos",
        "plan-rmos",
        "decision-rmos",
    ]
    assert [entry["session_id"] for entry in stored] == ["session-a"] * 4
    assert [entry["batch_label"] for entry in stored] == ["batch-a"] * 4
    assert [entry["tool_kind"] for entry in stored] == ["saw"] * 4


def _assert_mirrored_payloads(stored):
    spec_payload = stored[0]["payload"]
    plan_payload = stored[1]["payload"]
    decision_payload = stored[2]["payload"]
    execution_payload = stored[3]["payload"]

    assert spec_payload["source_saw_artifact_id"] == "spec-saw"
    assert plan_payload["batch_spec_artifact_id"] == "spec-rmos"
    assert plan_payload["source_saw_artifact_id"] == "plan-saw"
    assert plan_payload["source_saw_batch_spec_artifact_id"] == "spec-saw"
    assert decision_payload["batch_plan_artifact_id"] == "plan-rmos"
    assert decision_payload["batch_spec_artifact_id"] == "spec-rmos"
    assert decision_payload["source_saw_artifact_id"] == "decision-saw"
    assert decision_payload["source_saw_batch_plan_artifact_id"] == "plan-saw"
    assert decision_payload["source_saw_batch_spec_artifact_id"] == "spec-saw"
    assert execution_payload["batch_decision_artifact_id"] == "decision-rmos"
    assert execution_payload["batch_plan_artifact_id"] == "plan-rmos"
    assert execution_payload["batch_spec_artifact_id"] == "spec-rmos"


def test_batch_toolpaths_mirrors_saw_chain_into_rmos(monkeypatch):
    from app.rmos.runs_v2 import store as runs_store
    from app.saw_lab import batch_router
    from app.saw_lab import batch_router_helpers
    from app.saw_lab.batch_router import BatchToolpathsRequest

    stubs = BatchToolpathsMirrorStubs()
    # _load_saw_batch_chain now lives in batch_router_helpers, so patch get_artifact
    # there (where the mirror path resolves it), not in batch_router.
    monkeypatch.setattr(batch_router_helpers, "get_artifact", stubs.get_artifact)
    monkeypatch.setattr(runs_store, "store_artifact", stubs.store_artifact)

    response = batch_router.create_batch_toolpaths(
        BatchToolpathsRequest(batch_decision_artifact_id="decision-saw")
    )

    _assert_toolpaths_response(response)
    _assert_store_call_shape(stubs.stored)
    _assert_mirrored_payloads(stubs.stored)
