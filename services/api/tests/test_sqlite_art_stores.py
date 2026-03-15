# tests/test_sqlite_art_stores.py
"""
Tests for Art Studio SQLite Stores

Tests for:
- SQLiteArtJobsStore
- SQLiteArtPresetsStore
"""

import pytest
from pathlib import Path
import tempfile
import os


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_rmos.db"
        # Reset any existing DB instance
        from app.core.rmos_db import reset_rmos_db
        reset_rmos_db()
        yield db_path


@pytest.fixture
def art_jobs_store(temp_db):
    """Create an art jobs store with temp database."""
    from app.core.rmos_db import RMOSDatabase
    from app.stores.sqlite_art_jobs_store import SQLiteArtJobsStore

    db = RMOSDatabase(temp_db)
    return SQLiteArtJobsStore(db)


@pytest.fixture
def art_presets_store(temp_db):
    """Create an art presets store with temp database."""
    from app.core.rmos_db import RMOSDatabase
    from app.stores.sqlite_art_presets_store import SQLiteArtPresetsStore

    db = RMOSDatabase(temp_db)
    return SQLiteArtPresetsStore(db)


# =============================================================================
# ART JOBS STORE TESTS
# =============================================================================


class TestSQLiteArtJobsStore:
    """Tests for SQLiteArtJobsStore."""

    @pytest.mark.unit
    def test_create_art_job(self, art_jobs_store):
        """Test creating an art job."""
        job = art_jobs_store.create_art_job(
            job_id="test-job-001",
            job_type="rosette_cam",
            post_preset="grbl_mm",
            rings=3,
            z_passes=5,
            length_mm=1234.56,
            gcode_lines=500,
            meta={"comment": "Test job"},
        )

        assert job["id"] == "test-job-001"
        assert job["job_type"] == "rosette_cam"
        assert job["post_preset"] == "grbl_mm"
        assert job["rings"] == 3
        assert job["z_passes"] == 5
        assert job["length_mm"] == 1234.56
        assert job["gcode_lines"] == 500
        assert job["meta"]["comment"] == "Test job"
        assert job["created_at"] is not None

    @pytest.mark.unit
    def test_get_by_id(self, art_jobs_store):
        """Test retrieving a job by ID."""
        art_jobs_store.create_art_job(
            job_id="test-job-002",
            job_type="rosette_cam",
        )

        retrieved = art_jobs_store.get_by_id("test-job-002")
        assert retrieved is not None
        assert retrieved["id"] == "test-job-002"
        assert retrieved["job_type"] == "rosette_cam"

    @pytest.mark.unit
    def test_get_nonexistent_returns_none(self, art_jobs_store):
        """Test getting a nonexistent job returns None."""
        result = art_jobs_store.get_by_id("nonexistent-job")
        assert result is None

    @pytest.mark.unit
    def test_get_by_job_type(self, art_jobs_store):
        """Test filtering jobs by type."""
        art_jobs_store.create_art_job(job_id="job-1", job_type="rosette_cam")
        art_jobs_store.create_art_job(job_id="job-2", job_type="rosette_cam")
        art_jobs_store.create_art_job(job_id="job-3", job_type="adaptive_cam")

        rosette_jobs = art_jobs_store.get_by_job_type("rosette_cam")
        assert len(rosette_jobs) == 2

        adaptive_jobs = art_jobs_store.get_by_job_type("adaptive_cam")
        assert len(adaptive_jobs) == 1

    @pytest.mark.unit
    def test_get_recent(self, art_jobs_store):
        """Test getting recent jobs."""
        for i in range(15):
            art_jobs_store.create_art_job(job_id=f"job-{i}", job_type="test")

        recent = art_jobs_store.get_recent(limit=5)
        assert len(recent) == 5

    @pytest.mark.unit
    def test_delete_job(self, art_jobs_store):
        """Test deleting a job."""
        art_jobs_store.create_art_job(job_id="delete-me", job_type="test")

        assert art_jobs_store.get_by_id("delete-me") is not None

        deleted = art_jobs_store.delete("delete-me")
        assert deleted is True

        assert art_jobs_store.get_by_id("delete-me") is None

    @pytest.mark.unit
    def test_meta_json_serialization(self, art_jobs_store):
        """Test that meta field is properly serialized/deserialized."""
        complex_meta = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 3.14,
        }

        art_jobs_store.create_art_job(
            job_id="meta-test",
            job_type="test",
            meta=complex_meta,
        )

        retrieved = art_jobs_store.get_by_id("meta-test")
        assert retrieved["meta"] == complex_meta


# =============================================================================
# ART PRESETS STORE TESTS
# =============================================================================


class TestSQLiteArtPresetsStore:
    """Tests for SQLiteArtPresetsStore."""

    @pytest.mark.unit
    def test_create_preset(self, art_presets_store):
        """Test creating a preset."""
        preset = art_presets_store.create_preset(
            lane="rosette",
            name="Fast Roughing",
            params={
                "feedrate": 1000,
                "stepover": 0.5,
                "doc": 2.0,
            },
        )

        assert preset["lane"] == "rosette"
        assert preset["name"] == "Fast Roughing"
        assert preset["params"]["feedrate"] == 1000
        assert preset["created_at"] is not None
        assert "rosette_preset_" in preset["id"]

    @pytest.mark.unit
    def test_get_preset(self, art_presets_store):
        """Test retrieving a preset by ID."""
        created = art_presets_store.create_preset(
            lane="adaptive",
            name="Test Preset",
            params={"key": "value"},
        )

        retrieved = art_presets_store.get_preset(created["id"])
        assert retrieved is not None
        assert retrieved["name"] == "Test Preset"

    @pytest.mark.unit
    def test_list_by_lane(self, art_presets_store):
        """Test listing presets by lane."""
        art_presets_store.create_preset("rosette", "Preset 1", {})
        art_presets_store.create_preset("rosette", "Preset 2", {})
        art_presets_store.create_preset("adaptive", "Preset 3", {})
        art_presets_store.create_preset("all", "Universal", {})

        rosette_presets = art_presets_store.list_by_lane("rosette")
        # Should include rosette + "all" lane presets
        assert len(rosette_presets) == 3

        adaptive_presets = art_presets_store.list_by_lane("adaptive")
        # Should include adaptive + "all" lane presets
        assert len(adaptive_presets) == 2

    @pytest.mark.unit
    def test_list_all_presets(self, art_presets_store):
        """Test listing all presets without lane filter."""
        art_presets_store.create_preset("rosette", "P1", {})
        art_presets_store.create_preset("adaptive", "P2", {})
        art_presets_store.create_preset("relief", "P3", {})

        all_presets = art_presets_store.list_by_lane(None)
        assert len(all_presets) == 3

    @pytest.mark.unit
    def test_delete_preset(self, art_presets_store):
        """Test deleting a preset."""
        created = art_presets_store.create_preset("test", "Delete Me", {})

        assert art_presets_store.get_preset(created["id"]) is not None

        deleted = art_presets_store.delete_preset(created["id"])
        assert deleted is True

        assert art_presets_store.get_preset(created["id"]) is None

    @pytest.mark.unit
    def test_search_by_name(self, art_presets_store):
        """Test searching presets by name pattern."""
        art_presets_store.create_preset("rosette", "Fast Roughing", {})
        art_presets_store.create_preset("rosette", "Slow Finishing", {})
        art_presets_store.create_preset("adaptive", "Fast Adaptive", {})

        fast_presets = art_presets_store.search_by_name("%Fast%")
        assert len(fast_presets) == 2

    @pytest.mark.unit
    def test_params_json_serialization(self, art_presets_store):
        """Test that params field is properly serialized/deserialized."""
        complex_params = {
            "nested": {"toolpath": {"type": "contour"}},
            "values": [1.5, 2.5, 3.5],
            "enabled": True,
        }

        created = art_presets_store.create_preset(
            lane="test",
            name="Complex Params",
            params=complex_params,
        )

        retrieved = art_presets_store.get_preset(created["id"])
        assert retrieved["params"] == complex_params


# =============================================================================
# STORE REGISTRY INTEGRATION TESTS
# =============================================================================


class TestStoreRegistryIntegration:
    """Test that new stores are properly registered."""

    @pytest.mark.unit
    def test_art_jobs_store_registered(self):
        """Test art jobs store is accessible via registry."""
        from app.core.store_registry import StoreKeys

        assert hasattr(StoreKeys, "ART_JOBS")
        assert StoreKeys.ART_JOBS == "sqlite_art_jobs"

    @pytest.mark.unit
    def test_art_presets_store_registered(self):
        """Test art presets store is accessible via registry."""
        from app.core.store_registry import StoreKeys

        assert hasattr(StoreKeys, "ART_PRESETS")
        assert StoreKeys.ART_PRESETS == "sqlite_art_presets"

    @pytest.mark.unit
    def test_get_art_jobs_store_dependency(self):
        """Test FastAPI dependency function exists."""
        from app.core.store_registry import get_art_jobs_store

        assert callable(get_art_jobs_store)

    @pytest.mark.unit
    def test_get_art_presets_store_dependency(self):
        """Test FastAPI dependency function exists."""
        from app.core.store_registry import get_art_presets_store

        assert callable(get_art_presets_store)
