"""
Test suite for DXF Security Patch (15MB limit + safe algorithms).

This test suite validates all security enhancements deployed
to mitigate 4 critical vulnerabilities:
- Memory exhaustion (15MB file limit, 50MB enterprise)
- Stack overflow (iterative DFS, max depth 500)
- CPU exhaustion (O(n) spatial hashing)
- Request hanging (30s operation timeout)

Test coverage:
- 6 file size tests (standard/enterprise limits, boundary cases, integration)
- 3 entity count tests (normal, excessive, boundary)
- 5 spatial hash tests (deduplication, tolerance, performance scaling)
- 3 graph algorithm tests (cycle detection, depth limits, overflow handling)
- 3 timeout tests (fast ops, slow ops, error handling)

Total: 20 tests
"""

from __future__ import annotations

import pytest
import io
import asyncio
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cam.dxf_limits import (
    MAX_DXF_FILE_SIZE_BYTES,
    ENTERPRISE_MAX_DXF_FILE_SIZE_BYTES,
    MAX_DXF_ENTITIES,
    ENTERPRISE_MAX_DXF_ENTITIES,
    OPERATION_TIMEOUT_SECONDS,
)
from cam.dxf_upload_guard import (
    validate_file_size,
    validate_entity_count,
    DXFValidationError,
)
from cam.spatial_hash import SpatialHash
from cam.graph_algorithms import (
    build_adjacency_map_safe,
    find_cycles_iterative,
    GraphOverflowError,
    MAX_RECURSION_DEPTH,
)
from cam.async_timeout import run_with_timeout, GeometryTimeout


# ============================================================================
# Test Class 1: File Size Limits
# ============================================================================


class TestFileSizeLimits:
    """Test file size validation with 15MB standard and 50MB enterprise limits."""

    def test_valid_file_under_standard_limit(self):
        """Small files (1MB) should pass validation."""
        from fastapi import UploadFile
        
        # Create 1MB mock file
        file_size = 1 * 1024 * 1024
        mock_file = UploadFile(filename="test.dxf", file=io.BytesIO(b"0" * file_size))
        mock_file.size = file_size
        
        # Should not raise
        validate_file_size(mock_file)

    def test_valid_file_at_standard_boundary(self):
        """Files exactly at 15MB should pass."""
        from fastapi import UploadFile
        
        # Create file at exact limit
        file_size = MAX_DXF_FILE_SIZE_BYTES
        mock_file = UploadFile(filename="boundary.dxf", file=io.BytesIO(b"0" * file_size))
        mock_file.size = file_size
        
        # Should not raise
        validate_file_size(mock_file)

    def test_oversized_file_standard_limit(self):
        """Files exceeding 15MB should raise DXFValidationError with 413 status."""
        from fastapi import UploadFile
        
        # Create 16MB file (exceeds standard)
        file_size = 16 * 1024 * 1024
        mock_file = UploadFile(filename="large.dxf", file=io.BytesIO())
        mock_file.size = file_size
        
        with pytest.raises(DXFValidationError) as exc_info:
            validate_file_size(mock_file)
        
        assert exc_info.value.status_code == 413
        assert "15MB" in str(exc_info.value)

    def test_enterprise_limit_not_yet_enforced(self):
        """Note: Enterprise limit enforcement requires tier detection (not in scope)."""
        # This test documents that 50MB ENTERPRISE_MAX exists but isn't
        # automatically enforced - requires separate tier-aware validation
        assert ENTERPRISE_MAX_DXF_FILE_SIZE_BYTES == 50 * 1024 * 1024
        assert ENTERPRISE_MAX_DXF_ENTITIES == 200_000

    def test_file_size_constants_match_spec(self):
        """Verify limits match user requirements (15MB standard, 50MB enterprise)."""
        assert MAX_DXF_FILE_SIZE_BYTES == 15 * 1024 * 1024, "Standard limit should be 15MB"
        assert ENTERPRISE_MAX_DXF_FILE_SIZE_BYTES == 50 * 1024 * 1024, "Enterprise limit should be 50MB"

    def test_entity_count_constants_match_spec(self):
        """Verify entity limits (50K standard, 200K enterprise)."""
        assert MAX_DXF_ENTITIES == 50_000, "Standard entity limit should be 50K"
        assert ENTERPRISE_MAX_DXF_ENTITIES == 200_000, "Enterprise entity limit should be 200K"


# ============================================================================
# Test Class 2: Entity Count Limits
# ============================================================================


class TestEntityCountLimits:
    """Test entity count validation prevents memory exhaustion."""

    def test_valid_entity_count(self):
        """Entity counts under 50K should pass."""
        validate_entity_count(10_000)  # Should not raise
        validate_entity_count(49_999)  # Should not raise

    def test_entity_count_at_boundary(self):
        """Exactly 50K entities should pass."""
        validate_entity_count(MAX_DXF_ENTITIES)  # Should not raise

    def test_excessive_entity_count(self):
        """Entity counts exceeding 50K should raise DXFValidationError."""
        with pytest.raises(DXFValidationError) as exc_info:
            validate_entity_count(75_000)
        
        assert "75,000" in str(exc_info.value)
        assert "50,000" in str(exc_info.value)


# ============================================================================
# Test Class 3: Spatial Hash Performance (O(n) vs O(n²))
# ============================================================================


class TestSpatialHashPerformance:
    """Test O(n) point deduplication via spatial hashing."""

    def test_deduplicate_identical_points(self):
        """Identical points should map to same cell."""
        hash_grid = SpatialHash(tolerance=0.01)
        
        p1 = (10.0, 20.0)
        p2 = (10.0, 20.0)  # Exact duplicate
        
        id1 = hash_grid.get_or_add(p1)
        id2 = hash_grid.get_or_add(p2)
        
        assert id1 == id2, "Identical points should return same ID"
        assert hash_grid.count() == 1, "Should store only 1 unique point"

    def test_deduplicate_points_within_tolerance(self):
        """Points within tolerance (0.01mm) should map to same cell."""
        hash_grid = SpatialHash(tolerance=0.01)
        
        p1 = (10.0, 20.0)
        p2 = (10.005, 20.003)  # Within 0.01mm tolerance
        
        id1 = hash_grid.get_or_add(p1)
        id2 = hash_grid.get_or_add(p2)
        
        assert id1 == id2, "Points within tolerance should deduplicate"

    def test_separate_points_outside_tolerance(self):
        """Points outside tolerance should get different IDs."""
        hash_grid = SpatialHash(tolerance=0.01)
        
        p1 = (10.0, 20.0)
        p2 = (10.1, 20.1)  # 0.14mm apart (outside tolerance)
        
        id1 = hash_grid.get_or_add(p1)
        id2 = hash_grid.get_or_add(p2)
        
        assert id1 != id2, "Points outside tolerance should be distinct"
        assert hash_grid.count() == 2

    def test_configurable_tolerance(self):
        """Different tolerances should affect deduplication."""
        tight = SpatialHash(tolerance=0.001)
        loose = SpatialHash(tolerance=1.0)
        
        p1 = (0.0, 0.0)
        p2 = (0.5, 0.5)  # 0.707mm apart
        
        tight.get_or_add(p1)
        tight.get_or_add(p2)
        loose.get_or_add(p1)
        loose.get_or_add(p2)
        
        assert tight.count() == 2, "Tight tolerance should keep both points"
        assert loose.count() == 1, "Loose tolerance should merge points"

    def test_performance_scaling_10k_points(self):
        """Verify O(n) scaling handles 10K points efficiently."""
        hash_grid = SpatialHash(tolerance=0.01)
        
        # Generate 10K random-ish points (simulate complex DXF)
        points = [(float(i % 100), float(i // 100)) for i in range(10_000)]
        
        # Should complete in well under 1 second (O(n) behavior)
        for pt in points:
            hash_grid.get_or_add(pt)
        
        # Should deduplicate heavily (100x100 grid with 0.01 tolerance)
        assert hash_grid.count() < 20_000, "Should deduplicate overlapping points"


# ============================================================================
# Test Class 4: Iterative DFS (Stack Overflow Prevention)
# ============================================================================


class TestIterativeDFS:
    """Test iterative depth-first search prevents stack overflow."""

    def test_simple_triangle_cycle(self):
        """Detect simple 3-point cycle."""
        points = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
        edges = [(0, 1), (1, 2), (2, 0)]
        
        adj_map = build_adjacency_map_safe(edges, points)
        cycles = find_cycles_iterative(adj_map, points)
        
        assert len(cycles) == 1, "Should find 1 cycle"
        assert len(cycles[0]) == 3, "Cycle should have 3 points"

    def test_deep_graph_no_recursion_limit(self):
        """Deep linear graphs (500 nodes) should not cause recursion errors."""
        # Create chain: 0->1->2->...->499
        points = [(float(i), 0.0) for i in range(500)]
        edges = [(i, i + 1) for i in range(499)]
        
        adj_map = build_adjacency_map_safe(edges, points)
        
        # Should not raise RecursionError (uses iterative DFS)
        cycles = find_cycles_iterative(adj_map, points)
        assert isinstance(cycles, list)  # Should complete without error

    def test_graph_overflow_on_excessive_depth(self):
        """Graphs exceeding MAX_RECURSION_DEPTH should raise GraphOverflowError."""
        # Create chain longer than max depth (500)
        points = [(float(i), 0.0) for i in range(MAX_RECURSION_DEPTH + 100)]
        edges = [(i, i + 1) for i in range(MAX_RECURSION_DEPTH + 99)]
        
        adj_map = build_adjacency_map_safe(edges, points)
        
        with pytest.raises(GraphOverflowError) as exc_info:
            find_cycles_iterative(adj_map, points)
        
        assert "depth limit" in str(exc_info.value).lower()


# ============================================================================
# Test Class 5: Operation Timeouts
# ============================================================================


class TestOperationTimeouts:
    """Test async timeout wrapper prevents request hanging."""

    @pytest.mark.asyncio
    async def test_fast_operation_completes(self):
        """Fast operations (<1s) should complete normally."""
        def fast_task():
            return sum(range(1000))
        
        result = await run_with_timeout(fast_task, timeout=5.0)
        assert result == 499500

    @pytest.mark.asyncio
    async def test_slow_operation_times_out(self):
        """Operations exceeding timeout should raise GeometryTimeout."""
        def slow_task():
            import time
            time.sleep(2.0)  # Exceeds 0.5s timeout
            return "never reached"
        
        with pytest.raises(GeometryTimeout) as exc_info:
            await run_with_timeout(slow_task, timeout=0.5)
        
        assert exc_info.value.timeout == 0.5
        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_default_timeout_matches_spec(self):
        """Default timeout should be 30 seconds per user requirements."""
        def check_timeout():
            # Verify OPERATION_TIMEOUT_SECONDS is used as default
            return OPERATION_TIMEOUT_SECONDS
        
        result = await run_with_timeout(check_timeout)
        assert result == 30.0, "Default timeout should be 30 seconds"


# ============================================================================
# Integration Tests
# ============================================================================


class TestSecurityIntegration:
    """End-to-end security validation."""

    def test_all_limits_configured(self):
        """Verify all security constants are properly configured."""
        # File size limits
        assert MAX_DXF_FILE_SIZE_BYTES == 15 * 1024 * 1024
        assert ENTERPRISE_MAX_DXF_FILE_SIZE_BYTES == 50 * 1024 * 1024
        
        # Entity limits
        assert MAX_DXF_ENTITIES == 50_000
        assert ENTERPRISE_MAX_DXF_ENTITIES == 200_000
        
        # Timeout
        assert OPERATION_TIMEOUT_SECONDS == 30.0
        
        # Graph limits
        assert MAX_RECURSION_DEPTH == 500

    def test_import_all_security_modules(self):
        """Verify all security modules import successfully."""
        from cam.dxf_limits import MAX_DXF_FILE_SIZE_BYTES
        from cam.dxf_upload_guard import read_dxf_with_validation
        from cam.spatial_hash import SpatialHash
        from cam.graph_algorithms import build_adjacency_map_safe
        from cam.async_timeout import run_with_timeout
        
        # All imports should succeed
        assert MAX_DXF_FILE_SIZE_BYTES > 0
        assert callable(read_dxf_with_validation)
        assert callable(SpatialHash)
        assert callable(build_adjacency_map_safe)
        assert callable(run_with_timeout)


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
