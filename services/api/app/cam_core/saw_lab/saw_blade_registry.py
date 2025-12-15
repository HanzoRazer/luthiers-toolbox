"""
Saw Blade Registry - Centralized storage and management of saw blade specifications.

Integrates with:
- pdf_saw_blade_importer.py (CP-S63) for bulk import
- saw_blade_validator.py for safety checks
- Saw operation panels for blade selection

Storage: JSON file at app/data/cam_core/saw_blades.json
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Models
# ============================================================================

class SawBladeSpec(BaseModel):
    """Normalized saw blade specification."""
    
    # Identity
    id: str = Field(..., description="Unique blade ID (auto-generated)")
    vendor: str = Field(..., description="Manufacturer (Tenryu, Kanefusa, etc.)")
    model_code: str = Field(..., description="Manufacturer model/part number")
    
    # Dimensions (mm)
    diameter_mm: float = Field(..., description="Blade outer diameter")
    kerf_mm: float = Field(..., description="Cutting width")
    plate_thickness_mm: float = Field(..., description="Blade body thickness")
    bore_mm: float = Field(..., description="Arbor hole diameter")
    
    # Tooth geometry
    teeth: int = Field(..., description="Number of teeth")
    hook_angle_deg: Optional[float] = Field(None, description="Tooth hook angle")
    top_bevel_angle_deg: Optional[float] = Field(None, description="Top bevel angle")
    clearance_angle_deg: Optional[float] = Field(None, description="Clearance angle")
    
    # Design features
    expansion_slots: Optional[int] = Field(None, description="Number of expansion slots")
    cooling_slots: Optional[int] = Field(None, description="Number of cooling slots")
    
    # Application
    application: Optional[str] = Field(None, description="Rip, crosscut, combo, specialty")
    material_family: Optional[str] = Field(None, description="Hardwood, softwood, plywood, etc.")
    
    # Metadata
    source: Optional[str] = Field(None, description="PDF filename or manual entry")
    source_page: Optional[int] = Field(None, description="PDF page number")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Raw data preservation
    raw: Optional[Dict[str, Any]] = Field(None, description="Raw PDF cells or original data")


class SawBladeSearchFilter(BaseModel):
    """Search filters for blade registry."""
    vendor: Optional[str] = None
    diameter_min_mm: Optional[float] = None
    diameter_max_mm: Optional[float] = None
    kerf_min_mm: Optional[float] = None
    kerf_max_mm: Optional[float] = None
    teeth_min: Optional[int] = None
    teeth_max: Optional[int] = None
    application: Optional[str] = None
    material_family: Optional[str] = None


# ============================================================================
# Registry Storage
# ============================================================================

class SawBladeRegistry:
    """Centralized saw blade specification storage."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize registry.
        
        Args:
            storage_path: Path to JSON storage file (default: app/data/cam_core/saw_blades.json)
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "data" / "cam_core" / "saw_blades.json"
        
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage if not exists
        if not self.storage_path.exists():
            self._save_blades([])
    
    def _load_blades(self) -> List[Dict[str, Any]]:
        """Load blades from JSON storage."""
        if not self.storage_path.exists():
            return []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('blades', [])
        except Exception as e:
            print(f"Error loading blades: {e}")
            return []
    
    def _save_blades(self, blades: List[Dict[str, Any]]) -> None:
        """Save blades to JSON storage."""
        data = {
            'blades': blades,
            'last_updated': datetime.utcnow().isoformat(),
            'count': len(blades)
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_id(self, vendor: str, model_code: str) -> str:
        """Generate unique blade ID."""
        base = f"{vendor}_{model_code}".replace(' ', '_').replace('/', '_').lower()
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"{base}_{timestamp}"
    
    # ------------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------------
    
    def create(self, blade: SawBladeSpec) -> SawBladeSpec:
        """
        Add new blade to registry.
        
        Args:
            blade: Blade specification
            
        Returns:
            Created blade with generated ID
            
        Raises:
            ValueError: If blade with same vendor+model already exists
        """
        blades = self._load_blades()
        
        # Check for duplicates
        for existing in blades:
            if (existing.get('vendor') == blade.vendor and 
                existing.get('model_code') == blade.model_code):
                raise ValueError(f"Blade already exists: {blade.vendor} {blade.model_code}")
        
        # Generate ID if not provided
        if not blade.id or blade.id == "":
            blade.id = self._generate_id(blade.vendor, blade.model_code)
        
        blade.created_at = datetime.utcnow().isoformat()
        blade.updated_at = blade.created_at
        
        blades.append(blade.dict())
        self._save_blades(blades)
        
        return blade
    
    def read(self, blade_id: str) -> Optional[SawBladeSpec]:
        """
        Get blade by ID.
        
        Args:
            blade_id: Unique blade ID
            
        Returns:
            Blade specification or None if not found
        """
        blades = self._load_blades()
        
        for blade_data in blades:
            if blade_data.get('id') == blade_id:
                return SawBladeSpec(**blade_data)
        
        return None
    
    def update(self, blade_id: str, updates: Dict[str, Any]) -> Optional[SawBladeSpec]:
        """
        Update blade specification.
        
        Args:
            blade_id: Unique blade ID
            updates: Fields to update
            
        Returns:
            Updated blade or None if not found
        """
        blades = self._load_blades()
        
        for i, blade_data in enumerate(blades):
            if blade_data.get('id') == blade_id:
                # Apply updates
                blade_data.update(updates)
                blade_data['updated_at'] = datetime.utcnow().isoformat()
                
                blades[i] = blade_data
                self._save_blades(blades)
                
                return SawBladeSpec(**blade_data)
        
        return None
    
    def delete(self, blade_id: str) -> bool:
        """
        Delete blade from registry.
        
        Args:
            blade_id: Unique blade ID
            
        Returns:
            True if deleted, False if not found
        """
        blades = self._load_blades()
        
        for i, blade_data in enumerate(blades):
            if blade_data.get('id') == blade_id:
                blades.pop(i)
                self._save_blades(blades)
                return True
        
        return False
    
    def list_all(self) -> List[SawBladeSpec]:
        """
        Get all blades in registry.
        
        Returns:
            List of blade specifications
        """
        blades = self._load_blades()
        return [SawBladeSpec(**b) for b in blades]
    
    def search(self, filters: SawBladeSearchFilter) -> List[SawBladeSpec]:
        """
        Search blades by filters.
        
        Args:
            filters: Search criteria
            
        Returns:
            List of matching blades
        """
        blades = self._load_blades()
        results = []
        
        for blade_data in blades:
            blade = SawBladeSpec(**blade_data)
            
            # Apply filters
            if filters.vendor and blade.vendor.lower() != filters.vendor.lower():
                continue
            
            if filters.diameter_min_mm and blade.diameter_mm < filters.diameter_min_mm:
                continue
            
            if filters.diameter_max_mm and blade.diameter_mm > filters.diameter_max_mm:
                continue
            
            if filters.kerf_min_mm and blade.kerf_mm < filters.kerf_min_mm:
                continue
            
            if filters.kerf_max_mm and blade.kerf_mm > filters.kerf_max_mm:
                continue
            
            if filters.teeth_min and blade.teeth < filters.teeth_min:
                continue
            
            if filters.teeth_max and blade.teeth > filters.teeth_max:
                continue
            
            if filters.application and blade.application != filters.application:
                continue
            
            if filters.material_family and blade.material_family != filters.material_family:
                continue
            
            results.append(blade)
        
        return results
    
    # ------------------------------------------------------------------------
    # Bulk Import Integration (CP-S63)
    # ------------------------------------------------------------------------
    
    def upsert_from_pdf_import(self, blades: List[SawBladeSpec], update_existing: bool = False) -> Dict[str, int]:
        """
        Bulk import blades from PDF importer (CP-S63 integration).
        
        Args:
            blades: List of blade specifications from PDF
            update_existing: If True, update existing blades; if False, skip duplicates
            
        Returns:
            Dictionary with counts: {'created': N, 'updated': M, 'skipped': K, 'errors': L}
        """
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        existing_blades = self._load_blades()
        
        for blade in blades:
            try:
                # Check if blade exists (by vendor + model_code)
                existing_index = None
                for i, existing in enumerate(existing_blades):
                    if (existing.get('vendor') == blade.vendor and 
                        existing.get('model_code') == blade.model_code):
                        existing_index = i
                        break
                
                if existing_index is not None:
                    if update_existing:
                        # Update existing blade
                        blade.id = existing_blades[existing_index]['id']
                        blade.created_at = existing_blades[existing_index]['created_at']
                        blade.updated_at = datetime.utcnow().isoformat()
                        existing_blades[existing_index] = blade.dict()
                        stats['updated'] += 1
                    else:
                        # Skip duplicate
                        stats['skipped'] += 1
                else:
                    # Create new blade
                    blade.id = self._generate_id(blade.vendor, blade.model_code)
                    blade.created_at = datetime.utcnow().isoformat()
                    blade.updated_at = blade.created_at
                    existing_blades.append(blade.dict())
                    stats['created'] += 1
                    
            except Exception as e:
                print(f"Error importing blade {blade.vendor} {blade.model_code}: {e}")
                stats['errors'] += 1
        
        self._save_blades(existing_blades)
        return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Statistics dictionary
        """
        blades = self._load_blades()
        
        vendors = set()
        diameters = []
        applications = set()
        material_families = set()
        
        for blade_data in blades:
            blade = SawBladeSpec(**blade_data)
            vendors.add(blade.vendor)
            diameters.append(blade.diameter_mm)
            if blade.application:
                applications.add(blade.application)
            if blade.material_family:
                material_families.add(blade.material_family)
        
        return {
            'total_blades': len(blades),
            'vendors': sorted(list(vendors)),
            'vendor_count': len(vendors),
            'diameter_range_mm': {
                'min': min(diameters) if diameters else 0,
                'max': max(diameters) if diameters else 0
            },
            'applications': sorted(list(applications)),
            'material_families': sorted(list(material_families))
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_registry_instance = None

def get_registry() -> SawBladeRegistry:
    """Get singleton registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SawBladeRegistry()
    return _registry_instance
