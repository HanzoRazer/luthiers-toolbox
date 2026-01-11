from __future__ import annotations


def test_rollup_execution_metrics_from_job_logs_sums_fields():
    from app.saw_lab.execution_metrics_rollup_service import (
        rollup_execution_metrics_from_job_logs,
    )

    logs = [
        {
            "id": "jl1",
            "kind": "saw_batch_job_log",
            "payload": {
                "statistics": {
                    "total_length_mm": 10.0,
                    "cut_count": 1,
                    "move_count": 4,
                    "duration_sec": 2.0,
                },
                "notes": "burn",
            },
        },
        {
            "id": "jl2",
            "kind": "saw_batch_job_log",
            "payload": {
                "statistics": {
                    "total_length_mm": 3.25,
                    "cut_count": 2,
                    "move_count": 5,
                    "duration_sec": 1.0,
                },
                "notes": "tearout chatter",
            },
        },
    ]

    out = rollup_execution_metrics_from_job_logs(logs)
    totals = out["totals"]
    assert totals["job_log_count"] == 2
    assert totals["total_length_mm"] == 13.25
    assert totals["total_cut_count"] == 3
    assert totals["total_move_count"] == 9
    assert totals["duration_sec_total"] == 3.0
    assert totals["duration_sec_avg"] == 1.5
    assert out["signal_mentions"]["burn"] == 1
    assert out["signal_mentions"]["tearout"] == 1
    assert out["signal_mentions"]["chatter"] == 1


def test_write_execution_metrics_rollup_artifact_filters_by_execution(monkeypatch):
    # Patch BEFORE importing the function that uses these dependencies
    # The function does lazy imports inside, so we patch at the module level
    import app.rmos.runs_v2.store as store_module

    # two job logs, only one matches execution id
    jl_ok = {
        "id": "jl_ok",
        "kind": "saw_batch_job_log",
        "payload": {
            "batch_execution_artifact_id": "exec1",
            "statistics": {"total_length_mm": 10.0},
        },
    }
    jl_no = {
        "id": "jl_no",
        "kind": "saw_batch_job_log",
        "payload": {
            "batch_execution_artifact_id": "exec2",
            "statistics": {"total_length_mm": 99.0},
        },
    }

    def _fake_list_runs_filtered(**kwargs):
        return {"items": [jl_ok, jl_no]}

    created = {}

    def _fake_store_artifact(
        kind: str,
        payload: dict,
        parent_id=None,
        session_id=None,
        batch_label=None,
        tool_kind=None,
        **kwargs,
    ):
        created["kind"] = kind
        created["payload"] = payload
        created["parent_id"] = parent_id
        return "mx1"

    monkeypatch.setattr(store_module, "list_runs_filtered", _fake_list_runs_filtered)
    monkeypatch.setattr(store_module, "store_artifact", _fake_store_artifact)

    # Now import the function AFTER patching
    from app.saw_lab.execution_metrics_rollup_service import (
        write_execution_metrics_rollup_artifact,
    )

    mid = write_execution_metrics_rollup_artifact(
        batch_execution_artifact_id="exec1",
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
    )
    assert mid == "mx1"
    assert created["kind"] == "saw_batch_execution_metrics"
    assert created["parent_id"] == "exec1"
    assert created["payload"]["job_log_artifact_ids"] == ["jl_ok"]
    assert created["payload"]["kpis"]["totals"]["total_length_mm"] == 10.0
