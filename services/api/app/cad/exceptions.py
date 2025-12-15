# services/api/app/cad/exceptions.py
"""
CAD/DXF Engine Exception Hierarchy.

These exceptions provide structured error handling for geometry validation,
DXF export operations, and optional offset computations.
"""

from __future__ import annotations

from typing import Optional, Any, Dict


class CadEngineError(Exception):
    """Base exception for all CAD engine errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "details": self.details,
        }


class DxfValidationError(CadEngineError):
    """
    Raised when geometry or configuration fails validation.
    
    Examples:
      - Coordinate exceeds bounds
      - Entity count exceeds limit
      - Invalid polyline (< 2 points)
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
    ) -> None:
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        if constraint:
            details["constraint"] = constraint
        super().__init__(message, details)
        self.field = field
        self.value = value
        self.constraint = constraint


class DxfExportError(CadEngineError):
    """
    Raised when DXF document creation or export fails.
    
    Examples:
      - ezdxf write failure
      - File I/O error
      - Invalid document state
    """
    
    def __init__(self, message: str, operation: Optional[str] = None) -> None:
        details = {"operation": operation} if operation else {}
        super().__init__(message, details)
        self.operation = operation


class OffsetEngineError(CadEngineError):
    """
    Raised when offset computation fails.
    
    Examples:
      - Shapely not installed
      - Invalid buffer geometry
      - Self-intersecting result
    """
    pass


class OffsetEngineNotAvailable(OffsetEngineError):
    """Raised if Shapely is not installed but offsets are requested."""
    
    def __init__(self) -> None:
        super().__init__(
            "Shapely is not installed. Install 'shapely' to enable offset operations.",
            details={"dependency": "shapely", "install_cmd": "pip install shapely"}
        )


class GeometryError(CadEngineError):
    """
    Raised for general geometry computation errors.
    
    Examples:
      - Self-intersecting polygon
      - Degenerate geometry
      - Computation overflow
    """
    
    def __init__(
        self, 
        message: str, 
        geometry_type: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> None:
        details = {}
        if geometry_type:
            details["geometry_type"] = geometry_type
        if operation:
            details["operation"] = operation
        super().__init__(message, details)
        self.geometry_type = geometry_type
        self.operation = operation
