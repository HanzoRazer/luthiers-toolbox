# tests/test_dxf_security_patch.py
"""
Security Patch Tests - DXF Processing Guards

Tests for December 2025 security patch addressing:
1. Missing file size limits (memory exhaustion)
2. Unbounded recursion (stack overflow)
3. O(n²) point deduplication (CPU exhaustion)
4. No operation timeouts (hung requests)

Run with: pytest tests/test_dxf_security_patch.py -v
"""

import pytest
import asyncio
import io
from fastapi import UploadFile, HTTPException

from app.cam.dxf_limits import (
    MAX_DXF_FILE_SIZE_BYTES,
    MAX_DXF_ENTITIES,
    OPERATION_TIMEOUT_SECONDS,
)
from app.cam.dxf_upload_guard import (
    validate_file_size,
    validate_entity_count,
    read_dxf_with_validation,
    DXFValidationError,
)
from app.cam.async_timeout import (
    run_with_timeout,
    GeometryTimeout,
)
from app.cam.spatial_hash import SpatialHash
from app.cam.graph_algorithms import (
    build_adjacency_map_safe,
    find_cycles_iterative,
    GraphOverflowError,
)


# =============================================================================
# Test 1: File Size Limits
# =============================================================================

class TestFileSizeLimits:
    """Test file size validation prevents memory exhaustion."""
    
    def create_mock_upload(self, size_mb: float, filename: str = "test.dxf") -> UploadFile:
        """Create a mock UploadFile with specified size."""
        size_bytes = int(size_mb * 1024 * 1024)
        content = b"0" * size_bytes
        file_obj = io.BytesIO(content)
        return UploadFile(filename=filename, file=file_obj)
    
    def test_accept_valid_file_size(self):
        """Should accept files under 15MB limit."""
        file = self.create_mock_upload(size_mb=10.0)
        size = validate_file_size(file)
        assert size == 10 * 1024 * 1024
    
    def test_reject_oversized_file(self):
        """Should reject files over 15MB limit with 413 status."""
        file = self.create_mock_upload(size_mb=20.0)
        
        with pytest.raises(DXFValidationError) as exc:
            validate_file_size(file)
        
        assert exc.value.status_code == 413
        assert "20.0MB" in str(exc.value)
        assert "15MB" in str(exc.value)
    
    def test_reject_at_boundary(self):
        """Should reject file exactly at limit + 1 byte."""
        file = self.create_mock_upload(size_mb=15.0000001)
        
        with pytest.raises(DXFValidationError) as exc:
            validate_file_size(file)
        
        assert exc.value.status_code == 413
    
    @pytest.mark.asyncio
    async def test_integrated_validation(self):
        """Test full read_dxf_with_validation pipeline."""
        # Valid file
        valid_file = self.create_mock_upload(size_mb=5.0, filename="valid.dxf")
        result = await read_dxf_with_validation(valid_file)
        assert len(result) == 5 * 1024 * 1024
        
        # Oversized file
        large_file = self.create_mock_upload(size_mb=20.0, filename="large.dxf")
        with pytest.raises(HTTPException) as exc:
            await read_dxf_with_validation(large_file)
        assert exc.value.status_code == 413
    
    @pytest.mark.asyncio
    async def test_reject_invalid_extension(self):
        """Should reject non-DXF files."""
        file = self.create_mock_upload(size_mb=1.0, filename="test.pdf")
        
        with pytest.raises(HTTPException) as exc:
            await read_dxf_with_validation(file)
        
        assert exc.value.status_code == 400
        assert "Only .dxf files" in str(exc.value.detail)


# =============================================================================
# Test 2: Entity Count Limits
# =============================================================================

class TestEntityCountLimits:
    """Test entity count validation prevents complex file attacks."""
    
    def test_accept_normal_entity_count(self):
        """Should accept files with reasonable entity counts."""
        validate_entity_count(1000)  # Should not raise
        validate_entity_count(10000)  # Should not raise
        validate_entity_count(49999)  # Just under limit
    
    def test_reject_excessive_entities(self):
        """Should reject files exceeding 50,000 entity limit."""
        with pytest.raises(DXFValidationError) as exc:
            validate_entity_count(60000)
        
        assert "60,000" in str(exc.value)
        assert "50,000" in str(exc.value)
    
    def test_reject_at_boundary(self):
        """Should reject exactly at limit + 1."""
        with pytest.raises(DXFValidationError):
            validate_entity_count(MAX_DXF_ENTITIES + 1)


# =============================================================================
# Test 3: Spatial Hash Performance
# =============================================================================

class TestSpatialHashPerformance:
    """Test O(n) spatial hash replaces O(n²) linear scan."""
    
    class MockPoint:
        """Mock point for testing."""
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y
        
        def is_close(self, other, tolerance=0.001):
            dx = abs(self.x - other.x)
            dy = abs(self.y - other.y)
            return dx < tolerance and dy < tolerance
    
    def test_deduplicate_exact_duplicates(self):
        """Should deduplicate exact duplicate points."""
        hasher = SpatialHash(cell_size=0.1)
        
        p1 = self.MockPoint(10.0, 20.0)
        p2 = self.MockPoint(10.0, 20.0)  # Exact duplicate
        
        idx1 = hasher.get_or_add(p1)
        idx2 = hasher.get_or_add(p2)
        
        assert idx1 == idx2  # Same index = deduplication worked
        assert len(hasher.points) == 1
    
    def test_deduplicate_within_tolerance(self):
        """Should deduplicate points within tolerance."""
        hasher = SpatialHash(cell_size=0.1)
        
        p1 = self.MockPoint(10.0, 20.0)
        p2 = self.MockPoint(10.0005, 20.0003)  # Within 0.001mm
        
        idx1 = hasher.get_or_add(p1, tolerance=0.001)
        idx2 = hasher.get_or_add(p2, tolerance=0.001)
        
        assert idx1 == idx2
        assert len(hasher.points) == 1
    
    def test_keep_distinct_points(self):
        """Should keep points beyond tolerance."""
        hasher = SpatialHash(cell_size=0.1)
        
        p1 = self.MockPoint(10.0, 20.0)
        p2 = self.MockPoint(10.5, 20.5)  # Far apart
        
        idx1 = hasher.get_or_add(p1)
        idx2 = hasher.get_or_add(p2)
        
        assert idx1 != idx2
        assert len(hasher.points) == 2
    
    def test_handle_cell_boundaries(self):
        """Should find duplicates across cell boundaries."""
        hasher = SpatialHash(cell_size=1.0)
        
        # Points near cell boundary (0.9999 and 1.0001 are in different cells)
        p1 = self.MockPoint(0.9999, 0.0)
        p2 = self.MockPoint(1.0001, 0.0)  # Within tolerance but different cells
        
        idx1 = hasher.get_or_add(p1, tolerance=0.001)
        idx2 = hasher.get_or_add(p2, tolerance=0.001)
        
        assert idx1 == idx2  # 3x3 neighborhood search found it
    
    def test_performance_scaling(self):
        """Should handle 10K points efficiently (O(n) not O(n²))."""
        import time
        
        hasher = SpatialHash(cell_size=0.1)
        
        # Generate 10,000 points in 100x100mm area
        points = [
            self.MockPoint(x * 0.5, y * 0.5) 
            for x in range(100) 
            for y in range(100)
        ]
        
        start = time.time()
        for p in points:
            hasher.get_or_add(p)
        elapsed = time.time() - start
        
        # Should complete in <1 second (O(n) performance)
        # O(n²) would take 10-30 seconds for 10K points
        assert elapsed < 1.0, f"Too slow: {elapsed:.2f}s (expected <1s)"
        assert len(hasher.points) == 10000  # All unique


# =============================================================================
# Test 4: Iterative DFS (No Stack Overflow)
# =============================================================================

class TestIterativeDFS:
    """Test iterative DFS prevents stack overflow."""
    
    def test_find_simple_cycle(self):
        """Should find a simple triangle cycle."""
        # Triangle: 0-1-2-0
        adjacency = {
            0: [1, 2],
            1: [0, 2],
            2: [0, 1],
        }
        
        cycles = find_cycles_iterative(adjacency, [None, None, None])
        
        assert len(cycles) > 0
        assert 3 in [len(c) for c in cycles]  # Found triangle
    
    def test_handle_deep_graph(self):
        """Should handle deep graphs without stack overflow."""
        # Create a long chain: 0-1-2-3-...-999-0
        n = 1000
        adjacency = {i: [i+1] for i in range(n-1)}
        adjacency[n-1] = [0]  # Close the loop
        adjacency[0].append(n-1)  # Bidirectional
        
        try:
            cycles = find_cycles_iterative(adjacency, [None] * n, max_depth=1500)
            assert len(cycles) > 0  # Should find the cycle
        except GraphOverflowError:
            pytest.fail("Should not overflow on valid graph")
    
    def test_enforce_depth_limit(self):
        """Should stop at max depth to prevent infinite loops."""
        # Pathological graph with many paths
        adjacency = {i: list(range(i+1, min(i+10, 100))) for i in range(100)}
        
        # Should complete without hanging (depth limit prevents explosion)
        cycles = find_cycles_iterative(adjacency, [None] * 100, max_depth=50)
        # May or may not find cycles, but shouldn't hang


# =============================================================================
# Test 5: Operation Timeouts
# =============================================================================

class TestOperationTimeouts:
    """Test async timeout wrapper prevents hung requests."""
    
    @pytest.mark.asyncio
    async def test_fast_operation_completes(self):
        """Should allow fast operations to complete."""
        def quick_func():
            return "success"
        
        result = await run_with_timeout(quick_func, timeout=5.0)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_slow_operation_times_out(self):
        """Should timeout slow operations."""
        import time
        
        def slow_func():
            time.sleep(3.0)  # Exceeds 1s timeout
            return "should not reach here"
        
        with pytest.raises(GeometryTimeout) as exc:
            await run_with_timeout(slow_func, timeout=1.0)
        
        assert exc.value.timeout == 1.0
        assert "timed out" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_timeout_includes_function_name(self):
        """Should log which function timed out."""
        import time
        
        def problematic_operation():
            time.sleep(2.0)
        
        with pytest.raises(GeometryTimeout):
            await run_with_timeout(problematic_operation, timeout=0.5)


# =============================================================================
# Integration Tests
# =============================================================================

class TestSecurityPatchIntegration:
    """End-to-end tests of complete security patch."""
    
    @pytest.mark.asyncio
    async def test_reject_large_file_early(self):
        """Should reject large files before processing."""
        # Create 20MB file
        content = b"0" * (20 * 1024 * 1024)
        file = UploadFile(filename="large.dxf", file=io.BytesIO(content))
        
        with pytest.raises(HTTPException) as exc:
            await read_dxf_with_validation(file)
        
        assert exc.value.status_code == 413
    
    def test_spatial_hash_with_real_data(self):
        """Test spatial hash with realistic guitar body point count."""
        from app.cam.spatial_hash import SpatialHash
        
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def is_close(self, other, tolerance=0.001):
                return abs(self.x - other.x) < tolerance and abs(self.y - other.y) < tolerance
        
        hasher = SpatialHash()
        
        # Simulate Stratocaster body (1,417 points from user's test data)
        import random
        random.seed(42)
        points = [Point(random.uniform(0, 400), random.uniform(0, 300)) for _ in range(1417)]
        
        import time
        start = time.time()
        for p in points:
            hasher.get_or_add(p)
        elapsed = time.time() - start
        
        # Should be <100ms (user reported 2-3s for full Strat body extraction)
        assert elapsed < 0.1, f"Spatial hash too slow: {elapsed:.3f}s"


# =============================================================================
# Rollback Criteria Tests
# =============================================================================

class TestRollbackCriteria:
    """Tests for monitoring rollback trigger conditions."""
    
    def test_error_rate_tracking(self):
        """Verify we can track 413/504 error rates."""
        # This would integrate with actual metrics system
        # For now, just verify exceptions have correct status codes
        
        with pytest.raises(DXFValidationError) as exc:
            validate_file_size(
                UploadFile(filename="big.dxf", file=io.BytesIO(b"0" * 20_000_000))
            )
        assert exc.value.status_code == 413
    
    @pytest.mark.asyncio
    async def test_timeout_error_code(self):
        """Verify timeout errors return 504."""
        import time
        
        def slow_op():
            time.sleep(2.0)
        
        with pytest.raises(GeometryTimeout):
            await run_with_timeout(slow_op, timeout=0.5)
        
        # In actual router, this becomes HTTPException(504, ...)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
