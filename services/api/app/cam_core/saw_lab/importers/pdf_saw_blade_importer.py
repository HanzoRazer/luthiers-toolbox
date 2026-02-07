"""
CP-S63 — Universal Saw Blade PDF OCR Extractor

Automatically extracts saw blade specifications from vendor PDFs (Tenryu, Kanefusa,
SpeTool, etc.) into the Saw Lab registry. Eliminates manual data entry for 500+
blades across 9 vendor catalogs.

Key Features:
- Generic PDF table extraction via pdfplumber
- Vendor-agnostic header mapping
- Automatic unit parsing (mm, in, deg)
- Registry integration (upserts to CP-S50)
- CLI interface for batch imports

Usage:
```bash
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer \\
  data/vendor_pdfs/TENRYU_Catalogue.pdf --vendor Tenryu
```

Dependencies:
- pdfplumber>=0.11.0
- CP-S50 (Saw Blade Registry)
"""

from __future__ import annotations

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Install with: pip install pdfplumber>=0.11.0")
    sys.exit(1)


# ============================================================================
# DATA MODELS
# ============================================================================

class PdfBladeRow(BaseModel):
    """Raw extracted row from PDF table"""
    vendor: str
    source_pdf: str
    page_number: int
    cells: Dict[str, str]  # {header → cell_text}


class SawBladeSpec(BaseModel):
    """Normalized blade specification"""
    vendor: str
    model_code: Optional[str] = None
    
    # Geometry
    diameter_mm: Optional[float] = None
    bore_mm: Optional[float] = None
    teeth: Optional[int] = None
    kerf_mm: Optional[float] = None
    plate_thickness_mm: Optional[float] = None
    
    # Angles
    hook_angle_deg: Optional[float] = None
    top_bevel_angle_deg: Optional[float] = None
    clearance_angle_deg: Optional[float] = None
    tangential_clearance_deg: Optional[float] = None
    
    # Metadata
    material_family: Optional[str] = None
    application: Optional[str] = None
    
    # Preserve original data
    raw: Dict[str, Any] = {}


# ============================================================================
# HEADER MAPPING
# ============================================================================

def _header_map(headers: List[str]) -> Dict[int, str]:
    """
    Map vendor-specific headers to canonical field names.
    
    Common header synonyms:
    - D, dia, diameter → diameter_mm
    - B, kerf, width → kerf_mm
    - B1, plate, body → plate_thickness_mm
    - d2, bore, hole → bore_mm
    - Z, teeth → teeth
    - hook → hook_angle_deg
    - top bevel → top_bevel_angle_deg
    - clearance → clearance_angle_deg
    
    Args:
        headers: List of header strings from PDF table
    
    Returns:
        Dict mapping column index → canonical field name
    """
    mapped = {}
    
    for idx, header in enumerate(headers):
        if not header:
            continue
        
        # Normalize: lowercase, strip whitespace
        h = header.lower().strip()
        ch = re.sub(r'[^a-z0-9]', '', h)  # canonical (no punctuation/spaces)
        
        # Diameter
        if ch in {"d", "dia", "diameter", "od", "outsidediameter"}:
            mapped[idx] = "diameter_mm"
        
        # Kerf
        elif ch in {"b", "kerf", "width", "cut", "cutwidth"}:
            mapped[idx] = "kerf_mm"
        
        # Plate thickness
        elif ch in {"b1", "plate", "body", "platethickness", "bodythickness"}:
            mapped[idx] = "plate_thickness_mm"
        
        # Bore
        elif ch in {"d2", "bore", "hole", "arbor", "arborhole", "boresize"}:
            mapped[idx] = "bore_mm"
        
        # Teeth
        elif ch in {"z", "teeth", "numberofteeth", "teethcount", "t"}:
            mapped[idx] = "teeth"
        
        # Hook angle
        elif ch in {"hook", "hookangle", "rakeangle", "rake"}:
            mapped[idx] = "hook_angle_deg"
        
        # Top bevel
        elif ch in {"topbevel", "bevel", "bevelangle", "atb", "atbangle"}:
            mapped[idx] = "top_bevel_angle_deg"
        
        # Clearance
        elif ch in {"clearance", "clearanceangle", "relief", "reliefangle"}:
            mapped[idx] = "clearance_angle_deg"
        
        # Tangential clearance
        elif ch in {"tangentialclearance", "tangential", "sideclearance"}:
            mapped[idx] = "tangential_clearance_deg"
        
        # Material
        elif ch in {"material", "materialfamily", "mat", "for"}:
            mapped[idx] = "material_family"
        
        # Application
        elif ch in {"application", "app", "use", "usage", "type", "cuttype"}:
            mapped[idx] = "application"
        
        # Model code
        elif ch in {"model", "code", "item", "sku", "partno", "partnumber"}:
            mapped[idx] = "model_code"
    
    return mapped


# ============================================================================
# PARSING UTILITIES
# ============================================================================

def _parse_float(s: str) -> Optional[float]:
    """
    Extract float from string, stripping units.
    
    Examples:
    - "6.5mm" → 6.5
    - "1.25 in" → 1.25
    - "15°" → 15.0
    - "empty" → None
    
    Args:
        s: String with potential numeric value
    
    Returns:
        Float value or None if unparseable
    """
    if not s or s.strip().lower() in {"", "-", "—", "n/a", "na"}:
        return None
    
    # Strip units and non-numeric characters except decimal point and minus
    s = s.strip()
    match = re.search(r'[-+]?\d*\.?\d+', s)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _parse_int(s: str) -> Optional[int]:
    """
    Extract integer from string.
    
    Examples:
    - "48 teeth" → 48
    - "Z=60" → 60
    - "empty" → None
    
    Args:
        s: String with potential integer value
    
    Returns:
        Integer value or None if unparseable
    """
    if not s or s.strip().lower() in {"", "-", "—", "n/a", "na"}:
        return None
    
    match = re.search(r'\d+', s)
    if match:
        try:
            return int(match.group())
        except ValueError:
            return None
    return None


def _parse_string(s: str) -> Optional[str]:
    """
    Clean and normalize string value.
    
    Args:
        s: Raw string from PDF
    
    Returns:
        Cleaned string or None if empty
    """
    if not s:
        return None
    
    s = s.strip()
    if s.lower() in {"", "-", "—", "n/a", "na"}:
        return None
    
    return s


# ============================================================================
# NORMALIZATION
# ============================================================================

def normalize_pdf_row(row: PdfBladeRow, header_map: Dict[int, str]) -> SawBladeSpec:
    """
    Convert PdfBladeRow to normalized SawBladeSpec.
    
    Applies type conversions:
    - Float fields: diameter, kerf, bore, plate thickness, angles
    - Int fields: teeth
    - String fields: model code, material, application
    
    Args:
        row: Raw extracted row from PDF
        header_map: Mapping of column index → canonical field name
    
    Returns:
        Normalized SawBladeSpec
    """
    spec_data = {
        "vendor": row.vendor,
        "raw": {
            "source_pdf": row.source_pdf,
            "page_number": row.page_number,
            "cells": row.cells
        }
    }
    
    # Map cells to canonical fields
    cells_by_field = {}
    for header, value in row.cells.items():
        # Find column index from header
        headers_list = list(row.cells.keys())
        idx = headers_list.index(header)
        if idx in header_map:
            field = header_map[idx]
            cells_by_field[field] = value
    
    # Apply type conversions
    float_fields = [
        "diameter_mm", "kerf_mm", "bore_mm", "plate_thickness_mm",
        "hook_angle_deg", "top_bevel_angle_deg", "clearance_angle_deg",
        "tangential_clearance_deg"
    ]
    
    for field in float_fields:
        if field in cells_by_field:
            spec_data[field] = _parse_float(cells_by_field[field])
    
    if "teeth" in cells_by_field:
        spec_data["teeth"] = _parse_int(cells_by_field["teeth"])
    
    string_fields = ["model_code", "material_family", "application"]
    for field in string_fields:
        if field in cells_by_field:
            spec_data[field] = _parse_string(cells_by_field[field])
    
    return SawBladeSpec(**spec_data)


# ============================================================================
# PDF EXTRACTION
# ============================================================================

def extract_blade_rows_from_pdf(pdf_path: str, vendor: str) -> List[PdfBladeRow]:
    """
    Extract raw blade rows from PDF using pdfplumber.
    
    Treats first row as headers, subsequent rows as data.
    Handles multi-table pages.
    
    Args:
        pdf_path: Path to PDF file
        vendor: Vendor name (e.g., "Tenryu", "Kanefusa")
    
    Returns:
        List of PdfBladeRow objects
    """
    rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            
            for table in tables:
                if not table or len(table) < 2:
                    continue  # Need at least header + 1 data row
                
                headers = table[0]  # First row = headers
                
                # Process data rows
                for data_row in table[1:]:
                    if len(data_row) != len(headers):
                        continue  # Skip malformed rows
                    
                    cells = {
                        headers[i]: str(data_row[i]) if data_row[i] else ""
                        for i in range(len(headers))
                    }
                    
                    rows.append(PdfBladeRow(
                        vendor=vendor,
                        source_pdf=Path(pdf_path).name,
                        page_number=page_num,
                        cells=cells
                    ))
    
    return rows


# ============================================================================
# REGISTRY INTEGRATION
# ============================================================================

def upsert_into_registry(blades: List[SawBladeSpec], dry_run: bool = False) -> Dict[str, int]:
    """
    Upsert blades into CP-S50 Saw Blade Registry.
    
    Checks for duplicates by vendor + model_code. Updates existing
    records if found, inserts new records otherwise.
    
    Args:
        blades: List of normalized blade specs
        dry_run: If True, skip actual registry writes
    
    Returns:
        Stats dict: {"inserted": N, "updated": M, "skipped": K}
    """
    stats = {"inserted": 0, "updated": 0, "skipped": 0}
    
    if dry_run:
        stats["skipped"] = len(blades)
        return stats
    
    # ✅ INTEGRATED with CP-S50 saw_blade_registry.py
    from ..saw_blade_registry import get_registry
    
    registry = get_registry()
    result = registry.upsert_from_pdf_import(blades, update_existing=True)
    
    # Map registry stats to expected format
    stats["inserted"] = result["created"]
    stats["updated"] = result["updated"]
    stats["skipped"] = result["skipped"] + result["errors"]
    
    return stats


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extract saw blade specifications from vendor PDFs"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to PDF file (e.g., data/vendor_pdfs/TENRYU_Catalogue.pdf)"
    )
    parser.add_argument(
        "--vendor",
        required=True,
        help="Vendor name (e.g., Tenryu, Kanefusa, SpeTool)"
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Skip registry upsert, output JSON to stdout"
    )
    
    args = parser.parse_args()
    
    # Extract raw rows
    print(f"Extracting tables from {args.pdf_path}...", file=sys.stderr)
    rows = extract_blade_rows_from_pdf(args.pdf_path, args.vendor)
    print(f"Found {len(rows)} rows across all pages", file=sys.stderr)
    
    if not rows:
        print("No tables found in PDF. Check PDF structure.", file=sys.stderr)
        sys.exit(1)
    
    # Build header map from first row
    if rows:
        headers = list(rows[0].cells.keys())
        header_map = _header_map(headers)
        print(f"Header mapping: {header_map}", file=sys.stderr)
    else:
        header_map = {}
    
    # Normalize rows
    blades = []
    for row in rows:
        try:
            spec = normalize_pdf_row(row, header_map)
            blades.append(spec)
        except (ValueError, KeyError, TypeError) as e:  # WP-1: narrowed from except Exception
            print(f"Warning: Failed to normalize row on page {row.page_number}: {e}", file=sys.stderr)
            continue
    
    print(f"Normalized {len(blades)} blade specifications", file=sys.stderr)
    
    # Output or upsert
    if args.no_registry:
        # Output JSON to stdout
        print(json.dumps([b.dict() for b in blades], indent=2))
    else:
        # Upsert to registry
        stats = upsert_into_registry(blades)
        print(f"Registry stats: {stats}", file=sys.stderr)
        print(f"✓ Imported {stats['inserted']} blades", file=sys.stderr)


if __name__ == "__main__":
    main()
