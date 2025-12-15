# services/api/app/cam/dxf_upload_guard.py
"""
DXF Upload Guard

Reusable validation for DXF file uploads.
Provides file size checking and entity count validation.

Usage in routers:
    from app.cam.dxf_upload_guard import validate_dxf_upload, read_dxf_with_validation
    
    @router.post("/upload")
    async def upload_dxf(file: UploadFile = File(...)):
        dxf_bytes = await read_dxf_with_validation(file)
        # ... process dxf_bytes ...
"""

from __future__ import annotations

from typing import Tuple, Optional
import tempfile
import os
import logging

from fastapi import UploadFile, HTTPException

from app.cam.dxf_limits import (
    MAX_DXF_FILE_SIZE_BYTES,
    MAX_DXF_FILE_SIZE_MB,
    MAX_DXF_ENTITIES,
)

logger = logging.getLogger(__name__)


class DXFValidationError(Exception):
    """Raised when DXF validation fails."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.status_code = status_code
        super().__init__(message)


def validate_dxf_filename(filename: Optional[str]) -> None:
    """
    Validate that the filename indicates a DXF file.
    
    Args:
        filename: The uploaded filename
    
    Raises:
        DXFValidationError: If filename is missing or not .dxf
    """
    if not filename:
        raise DXFValidationError("No filename provided")
    
    if not filename.lower().endswith(".dxf"):
        raise DXFValidationError(
            f"Only .dxf files are supported (got: {filename})"
        )


def validate_file_size(file: UploadFile) -> int:
    """
    Check file size before reading into memory.
    
    Args:
        file: The uploaded file
    
    Returns:
        File size in bytes
    
    Raises:
        DXFValidationError: If file exceeds size limit
    """
    # Seek to end to get size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_DXF_FILE_SIZE_BYTES:
        logger.warning(
            "DXF_UPLOAD_REJECTED",
            extra={
                "reason": "file_too_large",
                "size_mb": file_size / 1024 / 1024,
                "limit_mb": MAX_DXF_FILE_SIZE_MB,
                "filename": file.filename,
            }
        )
        raise DXFValidationError(
            f"DXF file exceeds {MAX_DXF_FILE_SIZE_MB:.0f}MB limit "
            f"({file_size / 1024 / 1024:.1f}MB uploaded)",
            status_code=413  # Payload Too Large
        )
    
    return file_size


async def read_dxf_with_validation(
    file: UploadFile,
    require_extension: bool = True,
) -> bytes:
    """
    Read DXF file with size validation.
    
    This is the main entry point for safely reading DXF uploads.
    It checks the filename extension and file size before reading.
    
    Args:
        file: The uploaded file
        require_extension: Whether to require .dxf extension
    
    Returns:
        DXF file bytes
    
    Raises:
        HTTPException: On validation failure
    """
    try:
        # Validate filename
        if require_extension:
            validate_dxf_filename(file.filename)
        
        # Validate size
        validate_file_size(file)
        
        # Read file
        dxf_bytes = await file.read()
        
        if not dxf_bytes:
            raise DXFValidationError("Empty DXF file")
        
        return dxf_bytes
        
    except DXFValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


def validate_entity_count(entity_count: int) -> None:
    """
    Validate that entity count is within limits.
    
    Call this after parsing the DXF to prevent processing
    excessively complex files.
    
    Args:
        entity_count: Number of entities in the DXF
    
    Raises:
        DXFValidationError: If count exceeds limit
    """
    if entity_count > MAX_DXF_ENTITIES:
        logger.warning(
            "DXF_ENTITY_COUNT_EXCEEDED",
            extra={
                "reason": "too_many_entities",
                "entity_count": entity_count,
                "limit": MAX_DXF_ENTITIES,
            }
        )
        raise DXFValidationError(
            f"DXF contains {entity_count:,} entities (limit: {MAX_DXF_ENTITIES:,}). "
            "Simplify the geometry or split into multiple files."
        )


async def validate_dxf_upload(
    file: UploadFile,
) -> Tuple[bytes, int]:
    """
    Full validation of DXF upload.
    
    Args:
        file: The uploaded file
    
    Returns:
        Tuple of (dxf_bytes, file_size)
    
    Raises:
        HTTPException: On any validation failure
    """
    try:
        validate_dxf_filename(file.filename)
        file_size = validate_file_size(file)
        dxf_bytes = await file.read()
        
        if not dxf_bytes:
            raise DXFValidationError("Empty DXF file")
        
        return dxf_bytes, file_size
        
    except DXFValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
