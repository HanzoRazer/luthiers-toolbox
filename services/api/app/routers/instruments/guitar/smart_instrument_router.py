"""
Smart Guitar Instrument Router (Non-CAM)
========================================

Instrument specifications and IoT integration info for Smart Guitar.
CAM operations moved to /api/cam/guitar/smart/*
Temperament data moved to /api/music/temperament/*

Endpoints:
  GET /spec - Smart Guitar base specifications
  GET /info - Integration overview
  GET /bundle - DAW bundle information

Wave 15: Option C API Restructuring
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Smart Guitar", "Instruments"])


class SmartGuitarSpec(BaseModel):
    """Smart Guitar specifications"""
    model: str = "smart"
    display_name: str = "Smart Guitar"
    category: str = "electric_guitar"
    scale_length_mm: float = 648.0  # 25.5" default
    fret_count: int = 22
    string_count: int = 6
    electronics: str = "IoT-enabled"
    connectivity: List[str] = [
        "Bluetooth LE",
        "USB-C",
        "MIDI over BLE",
    ]
    features: List[str] = [
        "Embedded Raspberry Pi 5",
        "Real-time pitch detection",
        "DAW integration",
        "Alternative temperament support",
        "LED fret markers",
        "Battery-powered operation",
    ]


class SmartGuitarResource(BaseModel):
    """Smart Guitar resource item"""
    name: str
    type: str
    path: Optional[str] = None
    description: Optional[str] = None


class SmartGuitarBundleInfo(BaseModel):
    """DAW bundle information"""
    ok: bool
    bundle_version: str
    build_date: str
    resources: List[SmartGuitarResource]
    status: str


@router.get("/spec")
def get_smart_guitar_spec() -> SmartGuitarSpec:
    """
    Get Smart Guitar base specifications.
    
    Returns standard dimensions and IoT features.
    """
    return SmartGuitarSpec()


@router.get("/info")
def get_smart_guitar_info() -> Dict[str, Any]:
    """
    Get Smart Guitar system overview and architecture.
    
    Describes the IoT/DAW integration concept.
    """
    return {
        "ok": True,
        "model_id": "smart",
        "display_name": "Smart Guitar",
        "category": "electric_guitar",
        "concept": "Smart Guitar DAW Bundle",
        "description": (
            "Integration bundle documenting Smart Guitar IoT/DAW workflow. "
            "Combines lutherie CNC tools with digital audio workstation capabilities "
            "for embedded guitar electronics design and prototyping."
        ),
        "architecture": {
            "hardware": {
                "processor": "Raspberry Pi 5",
                "connectivity": ["Bluetooth LE 5.0", "USB-C", "Wi-Fi 6"],
                "audio": "24-bit ADC with real-time DSP",
                "power": "Li-ion battery with USB-C charging"
            },
            "software": {
                "os": "Linux (headless)",
                "daw_integration": ["MIDI over BLE", "OSC", "USB Audio"],
                "temperament_engine": "/api/music/temperament/*"
            }
        },
        "status": "Development - requires custom implementation",
        "related_endpoints": {
            "spec": "/api/instruments/guitar/smart/spec",
            "bundle": "/api/instruments/guitar/smart/bundle",
            "temperament": "/api/music/temperament/health",
            "cam": "/api/cam/guitar/smart/health"
        }
    }


@router.get("/bundle")
def get_smart_guitar_bundle() -> SmartGuitarBundleInfo:
    """
    Get Smart Guitar DAW Bundle integration information.
    
    Returns documentation, OEM letters, and integration plan.
    """
    bundle_dir = Path("Luthiers_ToolBox_Smart_Guitar_DAW_Bundle_v1.0/Build_10-14-2025")
    
    resources = []
    
    if bundle_dir.exists():
        # Check for integration plan
        integration_plan = bundle_dir / "Integration_Plan_v1.0.txt"
        if integration_plan.exists():
            resources.append(SmartGuitarResource(
                name="Integration Plan v1.0",
                type="documentation",
                path=str(integration_plan),
                description="Integration workflow and architecture"
            ))
        
        # Check for PDF documentation
        pdf_doc = bundle_dir / "Smart_Guitar_DAW_Integration_Bundle_v1.0.pdf"
        if pdf_doc.exists():
            resources.append(SmartGuitarResource(
                name="Smart Guitar DAW Integration Bundle v1.0",
                type="pdf",
                path=str(pdf_doc),
                description="Complete bundle documentation"
            ))
        
        # Check for OEM letters
        giglad_letter = bundle_dir / "Giglad_OEM_Letter.txt"
        if giglad_letter.exists():
            resources.append(SmartGuitarResource(
                name="Giglad OEM Letter",
                type="oem_correspondence",
                path=str(giglad_letter),
                description="Giglad partnership documentation"
            ))
        
        pgmusic_letter = bundle_dir / "PGMusic_OEM_Letter.txt"
        if pgmusic_letter.exists():
            resources.append(SmartGuitarResource(
                name="PGMusic OEM Letter",
                type="oem_correspondence",
                path=str(pgmusic_letter),
                description="PGMusic integration documentation"
            ))
    
    return SmartGuitarBundleInfo(
        ok=True,
        bundle_version="1.0",
        build_date="2025-10-14",
        resources=resources,
        status="Documentation bundle - requires custom implementation"
    )
