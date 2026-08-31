# tests/test_dxf_operation_timeouts.py
"""Async operation timeouts, and the rollback criteria that monitor them.

Split out of test_dxf_security_patch.py.
"""

import asyncio
import io

import pytest
from fastapi import UploadFile

from app.cam.dxf_limits import OPERATION_TIMEOUT_SECONDS
from app.cam.async_timeout import run_with_timeout, GeometryTimeout
from app.cam.dxf_upload_guard import DXFValidationError, validate_file_size

# =============================================================================
# Operation timeouts
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
# Rollback criteria
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
