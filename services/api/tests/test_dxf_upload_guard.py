# tests/test_dxf_upload_guard.py
"""DXF upload guard - file size and entity count limits.

Split out of test_dxf_security_patch.py, which had grown to cover six unrelated
concerns in one 500-line module and was sitting on the file-size debt ceiling.
Covers the December 2025 security patch's memory-exhaustion guards.
"""

import io

import pytest
from fastapi import UploadFile, HTTPException

from app.cam.dxf_limits import MAX_DXF_ENTITIES
from app.cam.dxf_upload_guard import (
    validate_file_size,
    validate_entity_count,
    read_dxf_with_validation,
    DXFValidationError,
)

# =============================================================================
# File size limits
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
# Entity count limits
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
# Integration
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
    
