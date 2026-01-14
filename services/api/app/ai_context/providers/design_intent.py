"""
AI Context Adapter - Design Intent Provider

Provides read-only design intent context from patterns/designs.
Excludes manufacturing details.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..schemas import (
    AdapterWarning,
    ContextAttachment,
    ContextRequest,
    ContextSource,
    RedactionPolicy,
    SourceKind,
    WarningCode,
)


class DesignIntentProvider:
    """
    Provides design_intent context from patterns/designs.
    
    Includes:
    - Pattern parameters (rosette, design specs)
    - Design goals and constraints
    - Visual metadata
    
    Excludes:
    - Manufacturing parameters
    - Toolpath generation settings
    - Machine-specific data
    """
    
    @property
    def source_kind(self) -> SourceKind:
        return SourceKind.DESIGN_INTENT
    
    def provide(
        self,
        req: ContextRequest,
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[ContextAttachment], List[AdapterWarning]]:
        """Provide design intent context."""
        sources: List[ContextSource] = []
        attachments: List[ContextAttachment] = []
        warnings: List[AdapterWarning] = []
        
        pattern_id = req.scope.pattern_id
        if not pattern_id:
            warnings.append(AdapterWarning(
                code=WarningCode.SCOPE_NOT_FOUND,
                message="No pattern_id in scope, skipping design_intent provider",
            ))
            return sources, attachments, warnings
        
        # Attempt to fetch pattern data
        pattern_data = self._fetch_pattern(pattern_id)
        if pattern_data is None:
            warnings.append(AdapterWarning(
                code=WarningCode.SCOPE_NOT_FOUND,
                message=f"Pattern '{pattern_id}' not found",
            ))
            return sources, attachments, warnings
        
        # Build sanitized design intent
        intent = self._build_intent(pattern_data)
        
        sources.append(ContextSource(
            source_id=f"design_intent_{pattern_id}",
            kind=SourceKind.DESIGN_INTENT,
            content_type="application/json",
            payload=intent,
        ))
        
        return sources, attachments, warnings
    
    def _fetch_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch pattern data.
        
        This is a stub that should be wired to actual pattern stores.
        """
        try:
            # Try art studio rosette patterns first
            from app.art_studio.rosette_patterns import get_pattern
            
            pattern = get_pattern(pattern_id)
            if pattern:
                return pattern if isinstance(pattern, dict) else pattern.dict()
        except (ImportError, AttributeError):
            pass
        
        try:
            # Try RMOS patterns
            from app.rmos.patterns.store import get_pattern as get_rmos_pattern
            
            pattern = get_rmos_pattern(pattern_id)
            if pattern:
                return pattern if isinstance(pattern, dict) else pattern.dict()
        except (ImportError, AttributeError):
            pass
        
        return None
    
    def _build_intent(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a sanitized design intent from pattern data.
        
        Only includes design-level fields, no manufacturing parameters.
        """
        intent: Dict[str, Any] = {
            "pattern_id": pattern_data.get("pattern_id") or pattern_data.get("id"),
            "name": pattern_data.get("name"),
            "kind": pattern_data.get("kind") or pattern_data.get("type"),
        }
        
        # Include created/updated timestamps
        if "created_at" in pattern_data:
            intent["created_at"] = pattern_data["created_at"]
        if "updated_at" in pattern_data:
            intent["updated_at"] = pattern_data["updated_at"]
        
        # Include description/notes
        if "description" in pattern_data:
            intent["description"] = pattern_data["description"]
        if "notes" in pattern_data:
            intent["notes"] = pattern_data["notes"]
        
        # Include visual parameters (safe design-level data)
        visual_params = self._extract_visual_params(pattern_data)
        if visual_params:
            intent["visual_parameters"] = visual_params
        
        # Include design constraints
        if "constraints" in pattern_data:
            intent["constraints"] = pattern_data["constraints"]
        
        # Include symmetry info
        if "symmetry" in pattern_data:
            intent["symmetry"] = pattern_data["symmetry"]
        if "fold_count" in pattern_data:
            intent["fold_count"] = pattern_data["fold_count"]
        
        # Include dimensions (design-level, not manufacturing)
        dims = self._extract_dimensions(pattern_data)
        if dims:
            intent["dimensions"] = dims
        
        return intent
    
    def _extract_visual_params(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract safe visual parameters."""
        visual: Dict[str, Any] = {}
        
        # Rosette-specific visual params
        for key in ["petal_count", "ring_count", "layers", "motif", "style"]:
            if key in pattern_data:
                visual[key] = pattern_data[key]
        
        # Color/appearance
        for key in ["fill_color", "stroke_color", "background"]:
            if key in pattern_data:
                visual[key] = pattern_data[key]
        
        # Geometric properties
        for key in ["rotation", "scale", "offset"]:
            if key in pattern_data:
                visual[key] = pattern_data[key]
        
        return visual
    
    def _extract_dimensions(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract safe dimension info."""
        dims: Dict[str, Any] = {}
        
        for key in [
            "outer_radius_mm", "inner_radius_mm",
            "width_mm", "height_mm",
            "diameter_mm", "depth_mm",
        ]:
            if key in pattern_data:
                dims[key] = pattern_data[key]
        
        return dims


# Singleton instance
design_intent_provider = DesignIntentProvider()
