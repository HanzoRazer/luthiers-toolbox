#!/usr/bin/env python3
"""End-to-End Integration Test: Workflow → Feasibility → Approval → Toolpaths → Artifacts"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def test_db():
    """Create a temporary SQLite database for testing."""
    import tempfile
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create temp database
    fd, db_path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    
    # Import all models to register with Base
    from app.db.base import Base
    from app.workflow.db.models import WorkflowSessionRow
    from app.rmos.runs_v2.db.models import RunArtifactRow, AdvisoryAttachmentRow
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    
    yield Session
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Provide a transactional database session."""
    session = test_db()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# =============================================================================
# Helper Functions
# =============================================================================

def sha256_hash(data: Any) -> str:
    """Create SHA256 hash of JSON-serialized data."""
    if isinstance(data, str):
        content = data
    else:
        content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()


def create_test_design() -> Dict[str, Any]:
    """Create a test rosette design specification."""
    return {
        "outer_diameter_mm": 100.0,
        "inner_diameter_mm": 85.0,
        "ring_count": 3,
        "ring_params": [
            {"ring_index": 0, "width_mm": 2.5, "tile_length_mm": 4.0},
            {"ring_index": 1, "width_mm": 3.0, "tile_length_mm": 5.0},
            {"ring_index": 2, "width_mm": 2.0, "tile_length_mm": 3.5},
        ],
        "depth_mm": 2.5,
    }


def create_test_context() -> Dict[str, Any]:
    """Create a test manufacturing context."""
    return {
        "tool_id": "router:6mm-downcut",
        "material_id": "spruce:european-aa",
        "machine_id": "cnc:x-carve-1000",
        "rpm": 12000,
        "feed_rate_mm_min": 1500,
    }


# =============================================================================
# Test: Complete Workflow Flow
# =============================================================================

class TestEndToEndWorkflowIntegration:
    """End-to-end test of workflow → artifact chain."""
    
    def test_complete_workflow_chain(self, db_session):
        """Test the complete chain:"""
        from app.workflow.state_machine import (
            WorkflowSession,
            WorkflowMode,
            WorkflowState,
            FeasibilityResult,
            ToolpathPlanRef,
            RunArtifactRef,
            RiskBucket,
            ActorRole,
            RunStatus,
            set_design,
            set_context,
            request_feasibility,
            store_feasibility,
            approve,
            request_toolpaths,
            store_toolpaths,
        )
        from app.workflow.db.store import DbWorkflowSessionStore
        from app.rmos.runs_v2.db.store import DbRunArtifactStore
        from app.rmos.runs_v2.schemas import (
            RunArtifact,
            Hashes,
            RunDecision,
            RunOutputs,
        )
        
        workflow_store = DbWorkflowSessionStore()
        run_store = DbRunArtifactStore()
        
        # ---------------------------------------------------------------------
        # Step 1: Create workflow session
        # ---------------------------------------------------------------------
        print("\n📋 Step 1: Creating workflow session...")
        
        session = WorkflowSession(
            mode=WorkflowMode.DESIGN_FIRST,
            state=WorkflowState.DRAFT,
            index_meta={
                "project": "test-rosette",
                "created_by": "integration-test",
            },
        )
        
        assert session.state == WorkflowState.DRAFT
        assert session.mode == WorkflowMode.DESIGN_FIRST
        print(f"   ✅ Session created: {session.session_id[:8]}...")
        
        # ---------------------------------------------------------------------
        # Step 2: Set design and context
        # ---------------------------------------------------------------------
        print("\n🎨 Step 2: Setting design and context...")
        
        design = create_test_design()
        context = create_test_context()
        
        session = set_design(session, design, actor=ActorRole.USER)
        assert session.design == design
        
        session = set_context(session, context, actor=ActorRole.USER)
        assert session.state == WorkflowState.CONTEXT_READY
        assert session.context == context
        
        # Update index_meta with context fields
        session.index_meta.update({
            "tool_id": context["tool_id"],
            "material_id": context["material_id"],
            "machine_id": context["machine_id"],
        })
        
        print(f"   ✅ Design: {design['ring_count']} rings, {design['outer_diameter_mm']}mm")
        print(f"   ✅ Context: {context['tool_id']}")
        
        # Persist session
        workflow_store.put(db_session, session)
        db_session.flush()
        
        # ---------------------------------------------------------------------
        # Step 3: Request and store feasibility
        # ---------------------------------------------------------------------
        print("\n🔍 Step 3: Evaluating feasibility...")
        
        session = request_feasibility(session, actor=ActorRole.USER)
        assert session.state == WorkflowState.FEASIBILITY_REQUESTED
        
        # Simulate server-side feasibility computation
        feasibility_data = {
            "score": 85.5,
            "risk_bucket": "GREEN",
            "warnings": ["Channel depth may need stepdown passes"],
            "calculator_results": {
                "chipload": {"score": 90, "chipload_mm": 0.08},
                "heat": {"score": 85, "surface_temp_c": 45},
                "geometry": {"score": 82, "complexity": "medium"},
            },
        }
        
        feasibility_hash = sha256_hash(feasibility_data)
        
        feasibility_result = FeasibilityResult(
            score=feasibility_data["score"],
            risk_bucket=RiskBucket.GREEN,
            warnings=feasibility_data["warnings"],
            meta={
                "feasibility_hash": feasibility_hash,
                "design_hash": sha256_hash(design),
                "context_hash": sha256_hash(context),
                "source": "server_recompute",  # Required for toolpath gate
                "policy_version": "v2.1",
                "calculator_versions": {
                    "chipload": "1.2.0",
                    "heat": "1.1.0",
                    "geometry": "1.0.0",
                },
            },
        )
        
        session = store_feasibility(session, feasibility_result, actor=ActorRole.SYSTEM)
        assert session.state == WorkflowState.FEASIBILITY_READY
        assert session.feasibility.score == 85.5
        assert session.feasibility.risk_bucket == RiskBucket.GREEN
        
        # Create and store run artifact for feasibility
        run_id_feasibility = str(uuid4())
        feasibility_artifact = RunArtifact(
            run_id=run_id_feasibility,
            mode="router",
            tool_id=context["tool_id"],
            status="OK",
            request_summary={"design": design, "context": context},
            feasibility=feasibility_data,
            decision=RunDecision(
                risk_level="GREEN",
                score=feasibility_data["score"],
                warnings=feasibility_data["warnings"],
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_hash,
            ),
            workflow_session_id=session.session_id,
            material_id=context["material_id"],
            machine_id=context["machine_id"],
            meta={"phase": "feasibility"},
        )
        
        run_store.put(db_session, feasibility_artifact)
        
        # Link artifact to session
        session.last_feasibility_artifact = RunArtifactRef(
            artifact_id=run_id_feasibility,
            kind="feasibility",
            status=RunStatus.OK,
        )
        
        print(f"   ✅ Feasibility score: {feasibility_result.score}")
        print(f"   ✅ Risk bucket: {feasibility_result.risk_bucket.value}")
        print(f"   ✅ Artifact stored: {run_id_feasibility[:8]}...")
        
        # Update session in store
        workflow_store.put(db_session, session)
        
        # ---------------------------------------------------------------------
        # Step 4: Approve design
        # ---------------------------------------------------------------------
        print("\n✅ Step 4: Approving design...")
        
        session = approve(session, actor=ActorRole.OPERATOR, note="Looks good for production")
        assert session.state == WorkflowState.APPROVED
        assert session.approval.approved is True
        
        print(f"   ✅ Approved by: {session.approval.approved_by.value}")
        
        workflow_store.put(db_session, session)
        
        # ---------------------------------------------------------------------
        # Step 5: Request and store toolpaths
        # ---------------------------------------------------------------------
        print("\n🛠️ Step 5: Generating toolpaths...")
        
        session = request_toolpaths(session, actor=ActorRole.USER)
        assert session.state == WorkflowState.TOOLPATHS_REQUESTED
        
        # Simulate toolpath generation
        toolpath_data = {
            "plan_id": str(uuid4()),
            "segments": 847,
            "total_length_mm": 12450.5,
            "estimated_time_min": 8.5,
            "gcode_lines": 2340,
        }
        
        toolpath_hash = sha256_hash(toolpath_data)
        gcode_content = "; G-code for rosette\nG21 ; mm mode\nG90 ; absolute\n..."
        gcode_hash = sha256_hash(gcode_content)
        
        toolpath_ref = ToolpathPlanRef(
            plan_id=toolpath_data["plan_id"],
            meta={
                "toolpath_hash": toolpath_hash,
                "segments": toolpath_data["segments"],
                "total_length_mm": toolpath_data["total_length_mm"],
                "estimated_time_min": toolpath_data["estimated_time_min"],
            },
        )
        
        session = store_toolpaths(session, toolpath_ref, actor=ActorRole.SYSTEM)
        assert session.state == WorkflowState.TOOLPATHS_READY
        
        # Create and store run artifact for toolpaths
        run_id_toolpaths = str(uuid4())
        toolpaths_artifact = RunArtifact(
            run_id=run_id_toolpaths,
            mode="router",
            tool_id=context["tool_id"],
            status="OK",
            request_summary={"design": design, "context": context},
            feasibility=feasibility_data,
            decision=RunDecision(
                risk_level="GREEN",
                score=feasibility_data["score"],
                warnings=feasibility_data["warnings"],
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_hash,
                toolpaths_sha256=toolpath_hash,
                gcode_sha256=gcode_hash,
            ),
            outputs=RunOutputs(
                gcode_text=gcode_content[:200],  # Truncated for test
                opplan_json=toolpath_data,
            ),
            workflow_session_id=session.session_id,
            material_id=context["material_id"],
            machine_id=context["machine_id"],
            event_type="toolpaths",
            meta={"phase": "toolpaths"},
        )
        
        run_store.put(db_session, toolpaths_artifact)
        
        # Link artifact to session
        session.last_toolpaths_artifact = RunArtifactRef(
            artifact_id=run_id_toolpaths,
            kind="toolpaths",
            status=RunStatus.OK,
        )
        
        print(f"   ✅ Toolpath segments: {toolpath_data['segments']}")
        print(f"   ✅ Estimated time: {toolpath_data['estimated_time_min']} min")
        print(f"   ✅ Artifact stored: {run_id_toolpaths[:8]}...")
        
        workflow_store.put(db_session, session)
        
        # Flush to ensure data is written
        db_session.flush()
        
        # ---------------------------------------------------------------------
        # Step 6: Verify artifact chain
        # ---------------------------------------------------------------------
        print("\n🔗 Step 6: Verifying artifact chain...")
        
        # Reload session from store
        reloaded_session = workflow_store.get(db_session, session.session_id)
        assert reloaded_session is not None
        assert reloaded_session.state == WorkflowState.TOOLPATHS_READY
        assert reloaded_session.last_feasibility_artifact is not None
        assert reloaded_session.last_toolpaths_artifact is not None
        
        print(f"   ✅ Session state: {reloaded_session.state.value}")
        
        # Reload feasibility artifact
        feasibility_reloaded = run_store.get(db_session, run_id_feasibility)
        assert feasibility_reloaded is not None
        assert feasibility_reloaded.status == "OK"
        assert feasibility_reloaded.decision.risk_level == "GREEN"
        assert feasibility_reloaded.hashes.feasibility_sha256 == feasibility_hash
        
        print(f"   ✅ Feasibility artifact verified")
        
        # Reload toolpaths artifact
        toolpaths_reloaded = run_store.get(db_session, run_id_toolpaths)
        assert toolpaths_reloaded is not None
        assert toolpaths_reloaded.status == "OK"
        assert toolpaths_reloaded.hashes.toolpaths_sha256 == toolpath_hash
        assert toolpaths_reloaded.hashes.gcode_sha256 == gcode_hash
        
        print(f"   ✅ Toolpaths artifact verified")
        
        # List artifacts for session
        session_artifacts, total = run_store.list(
            db_session,
            workflow_session_id=session.session_id,
        )
        assert total == 2
        assert len(session_artifacts) == 2
        
        print(f"   ✅ Session has {total} artifacts")
        
        # Verify events logged
        assert len(reloaded_session.events) >= 5  # design, context, feasibility, approve, toolpaths
        print(f"   ✅ {len(reloaded_session.events)} workflow events recorded")
        
        print("\n" + "="*60)
        print("🎉 END-TO-END TEST PASSED!")
        print("="*60)
        
        # Return artifacts for further testing
        return {
            "session": reloaded_session,
            "feasibility_artifact": feasibility_reloaded,
            "toolpaths_artifact": toolpaths_reloaded,
        }
    
    def test_run_artifact_queries(self, db_session):
        """Test various run artifact query patterns."""
        from app.rmos.runs_v2.db.store import DbRunArtifactStore
        from app.rmos.runs_v2.schemas import RunArtifact, Hashes, RunDecision
        
        run_store = DbRunArtifactStore()
        
        print("\n📊 Testing run artifact queries...")
        
        session_id = f"query-test-{uuid4().hex[:8]}"
        
        # Create multiple artifacts with varying attributes
        artifacts_data = [
            {"status": "OK", "risk": "GREEN", "score": 95, "mode": "router"},
            {"status": "OK", "risk": "GREEN", "score": 88, "mode": "router"},
            {"status": "OK", "risk": "YELLOW", "score": 72, "mode": "saw"},
            {"status": "BLOCKED", "risk": "RED", "score": 35, "mode": "router"},
            {"status": "ERROR", "risk": "UNKNOWN", "score": None, "mode": "saw"},
        ]
        
        for i, data in enumerate(artifacts_data):
            artifact = RunArtifact(
                run_id=str(uuid4()),
                mode=data["mode"],
                tool_id=f"tool-{data['mode']}",
                status=data["status"],
                request_summary={"test": i},
                feasibility={"score": data["score"]},
                decision=RunDecision(
                    risk_level=data["risk"],
                    score=data["score"],
                ),
                hashes=Hashes(feasibility_sha256="b" * 64),
                workflow_session_id=session_id,
            )
            run_store.put(db_session, artifact)
        
        db_session.flush()
        print(f"   ✅ Created {len(artifacts_data)} test artifacts")
        
        # Query by status
        ok_artifacts, ok_count = run_store.list(db_session, status="OK")
        assert ok_count >= 3
        print(f"   ✅ Status=OK: {ok_count} artifacts")
        
        # Query by mode
        router_artifacts, router_count = run_store.list(db_session, mode="router")
        assert router_count >= 3
        print(f"   ✅ Mode=router: {router_count} artifacts")
        
        # Query by risk level
        green_artifacts, green_count = run_store.list(db_session, risk_level="GREEN")
        assert green_count >= 2
        print(f"   ✅ Risk=GREEN: {green_count} artifacts")
        
        # Query by score range
        high_score, high_count = run_store.list(db_session, min_score=80)
        print(f"   ✅ Score>=80: {high_count} artifacts")
        
        # Query by session
        session_artifacts, session_count = run_store.list(
            db_session, workflow_session_id=session_id
        )
        assert session_count == len(artifacts_data)
        print(f"   ✅ Session artifacts: {session_count}")
        
        # Count by status
        status_counts = run_store.count_by_status(db_session)
        print(f"   ✅ Status distribution: {status_counts}")
        
        # Count by risk
        risk_counts = run_store.count_by_risk(db_session)
        print(f"   ✅ Risk distribution: {risk_counts}")
        
        print("\n   🎉 Run artifact query test passed!")


# =============================================================================
# Standalone Execution
# =============================================================================

def run_standalone():
    """Run tests without pytest for quick validation."""
    import tempfile
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    print("="*60)
    print("🧪 Running End-to-End Integration Tests (Standalone)")
    print("="*60)
    
    # Create temp database
    fd, db_path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    
    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        
        # Import all models
        from app.db.base import Base
        from app.workflow.db.models import WorkflowSessionRow
        from app.rmos.runs_v2.db.models import RunArtifactRow, AdvisoryAttachmentRow
        
        # Create tables
        Base.metadata.create_all(engine)
        print("\n✅ Database tables created")
        
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        
        # Run tests
        test = TestEndToEndWorkflowIntegration()
        
        with Session() as db:
            test.test_complete_workflow_chain(db)
            db.commit()
        
        with Session() as db:
            test.test_advisory_attachment(db)
            db.commit()
        
        with Session() as db:
            test.test_ai_session_persistence(db)
            db.commit()
        
        with Session() as db:
            test.test_run_artifact_queries(db)
            db.commit()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    run_standalone()
