"""
Test: Run diff persists attachment when large

Verifies that /api/rmos/runs/diff stores large diffs as content-addressed
attachments and returns a downloadable URL.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import json


@pytest.fixture
def two_runs_with_large_diff(client: TestClient):
    """Create two runs with significant differences to produce large diff."""
    from app.rmos.runs_v2 import persist_run, RunArtifact, RunDecision, Hashes, utc_now, create_run_id
    
    run_id_a = create_run_id()
    run_id_b = create_run_id()
    
    # Create run A with substantial data
    run_a = RunArtifact(
        run_id=run_id_a,
        created_at_utc=utc_now(),
        event_type="TEST_DIFF_LARGE",
        status="OK",
        mode="test",
        tool_id="test_tool",
        hashes=Hashes(
            feasibility_sha256="a" * 64,
            toolpaths_sha256="b" * 64,
            gcode_sha256="c" * 64,
        ),
        decision=RunDecision(
            risk_level="LOW",
            score=0.95,
        ),
        feasibility={"key_" + str(i): f"value_{i}_" + "x" * 100 for i in range(50)},
        notes="Run A notes " + "x" * 500,
    )
    
    # Create run B with different data
    run_b = RunArtifact(
        run_id=run_id_b,
        created_at_utc=utc_now(),
        event_type="TEST_DIFF_LARGE",
        status="BLOCKED",
        mode="test",
        tool_id="test_tool_v2",
        hashes=Hashes(
            feasibility_sha256="d" * 64,
            toolpaths_sha256="e" * 64,
            gcode_sha256="f" * 64,
        ),
        decision=RunDecision(
            risk_level="HIGH",
            score=0.35,
            block_reason="Test block reason " + "y" * 500,
        ),
        feasibility={"key_" + str(i): f"different_value_{i}_" + "y" * 100 for i in range(50)},
        notes="Run B notes " + "y" * 500,
    )
    
    persist_run(run_a)
    persist_run(run_b)
    
    return run_id_a, run_id_b


@pytest.mark.rmos
class TestRunDiffAttachment:
    """Tests for diff attachment persistence and retrieval."""
    
    def test_small_diff_not_truncated(self, client: TestClient):
        """Small diffs should return inline without attachment."""
        from app.rmos.runs_v2 import persist_run, RunArtifact, RunDecision, Hashes, utc_now, create_run_id
        
        run_id_a = create_run_id()
        run_id_b = create_run_id()
        
        # Create minimal runs
        run_a = RunArtifact(
            run_id=run_id_a,
            created_at_utc=utc_now(),
            event_type="TEST_SMALL",
            status="OK",
            mode="test",
            tool_id="tool",
            hashes=Hashes(feasibility_sha256="a" * 64),
            decision=RunDecision(risk_level="LOW", score=0.9),
        )
        run_b = RunArtifact(
            run_id=run_id_b,
            created_at_utc=utc_now(),
            event_type="TEST_SMALL",
            status="OK",
            mode="test",
            tool_id="tool",
            hashes=Hashes(feasibility_sha256="a" * 64),
            decision=RunDecision(risk_level="LOW", score=0.9),
        )
        
        persist_run(run_a)
        persist_run(run_b)
        
        resp = client.get(f"/api/rmos/runs/diff?a={run_id_a}&b={run_id_b}")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["truncated"] is False
        assert "preview" in data
        assert "diff_attachment" not in data
    
    def test_large_diff_creates_attachment(self, client: TestClient, two_runs_with_large_diff):
        """Large diffs should be stored as attachments."""
        run_id_a, run_id_b = two_runs_with_large_diff
        
        # Request with small preview limit to force attachment
        resp = client.get(
            f"/api/rmos/runs/diff?a={run_id_a}&b={run_id_b}&preview_max_chars=1000"
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["truncated"] is True
        assert "diff_attachment" in data
        assert "sha256" in data["diff_attachment"]
        assert "download_url" in data["diff_attachment"]
        assert data["diff_attachment"]["download_url"].startswith("/api/rmos/runs/diff/download/")
    
    def test_force_attachment_always_stores(self, client: TestClient):
        """force_attachment=true should always store as attachment."""
        from app.rmos.runs_v2 import persist_run, RunArtifact, RunDecision, Hashes, utc_now, create_run_id
        
        run_id_a = create_run_id()
        run_id_b = create_run_id()
        
        # Create minimal runs
        run_a = RunArtifact(
            run_id=run_id_a,
            created_at_utc=utc_now(),
            event_type="TEST_FORCE",
            status="OK",
            mode="test",
            tool_id="tool",
            hashes=Hashes(feasibility_sha256="a" * 64),
            decision=RunDecision(risk_level="LOW", score=0.9),
        )
        run_b = RunArtifact(
            run_id=run_id_b,
            created_at_utc=utc_now(),
            event_type="TEST_FORCE",
            status="OK",
            mode="test",
            tool_id="tool",
            hashes=Hashes(feasibility_sha256="a" * 64),
            decision=RunDecision(risk_level="LOW", score=0.9),
        )
        
        persist_run(run_a)
        persist_run(run_b)
        
        resp = client.get(
            f"/api/rmos/runs/diff?a={run_id_a}&b={run_id_b}&force_attachment=true"
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["truncated"] is True
        assert "diff_attachment" in data
    
    def test_attachment_downloadable(self, client: TestClient, two_runs_with_large_diff):
        """Stored attachment should be downloadable via /diff/download/{sha256}."""
        run_id_a, run_id_b = two_runs_with_large_diff
        
        # First, create the attachment
        resp = client.get(
            f"/api/rmos/runs/diff?a={run_id_a}&b={run_id_b}&preview_max_chars=1000"
        )
        assert resp.status_code == 200
        
        data = resp.json()
        sha256 = data["diff_attachment"]["sha256"]
        
        # Now download it
        download_resp = client.get(f"/api/rmos/runs/diff/download/{sha256}")
        assert download_resp.status_code == 200
        assert download_resp.headers["content-type"].startswith("application/json")
        
        # Verify content is valid JSON diff
        content = download_resp.json()
        assert "a" in content
        assert "b" in content
        assert "diff_severity" in content
    
    def test_download_nonexistent_returns_404(self, client: TestClient):
        """Downloading non-existent attachment should return 404."""
        fake_sha = "0" * 64
        resp = client.get(f"/api/rmos/runs/diff/download/{fake_sha}")
        assert resp.status_code == 404
    
    def test_preview_contains_partial_diff(self, client: TestClient, two_runs_with_large_diff):
        """Preview should contain beginning of the diff."""
        run_id_a, run_id_b = two_runs_with_large_diff
        
        # Use minimum valid preview_max_chars (1000)
        resp = client.get(
            f"/api/rmos/runs/diff?a={run_id_a}&b={run_id_b}&preview_max_chars=1000"
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert len(data["preview"]) <= 1000
        assert data["full_bytes"] > 1000
        # Preview should be start of valid JSON
        assert data["preview"].startswith("{")
    
    def test_diff_response_contains_structured_fields(self, client: TestClient, two_runs_with_large_diff):
        """Response should contain all diff fields plus attachment info."""
        run_id_a, run_id_b = two_runs_with_large_diff
        
        resp = client.get(
            f"/api/rmos/runs/diff?a={run_id_a}&b={run_id_b}&preview_max_chars=1000"
        )
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Standard diff fields
        assert "a" in data
        assert "b" in data
        assert "diff_severity" in data
        assert "changed_paths" in data
        assert "diff" in data
        assert "summary" in data
        
        # Attachment fields
        assert "preview" in data
        assert "truncated" in data
        assert "full_bytes" in data
