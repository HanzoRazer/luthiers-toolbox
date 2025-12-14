"""
Smart Guitar DAW Bundle Router
Documentation and integration resources for Smart Guitar IoT/DAW system
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/cam/smart-guitar", tags=["smart-guitar"])


class SmartGuitarResource(BaseModel):
    """Smart Guitar resource item"""
    name: str
    type: str
    path: Optional[str] = None
    description: Optional[str] = None


class SmartGuitarIntegrationInfo(BaseModel):
    """Integration information"""
    ok: bool
    bundle_version: str
    build_date: str
    resources: List[SmartGuitarResource]
    status: str


@router.get("/info")
def get_smart_guitar_info() -> SmartGuitarIntegrationInfo:
    """
    Get Smart Guitar DAW Bundle integration information.
    
    Returns documentation, OEM letters, and integration plan.
    """
    bundle_dir = Path("Luthiers_ToolBox_Smart_Guitar_DAW_Bundle_v1.0/Build_10-14-2025")
    
    if not bundle_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="Smart Guitar DAW Bundle not found"
        )
    
    resources = []
    
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
    
    # Check for README
    readme = bundle_dir / "Read_Me_First.txt"
    if readme.exists():
        resources.append(SmartGuitarResource(
            name="Read Me First",
            type="instructions",
            path=str(readme),
            description="Getting started guide"
        ))
    
    return SmartGuitarIntegrationInfo(
        ok=True,
        bundle_version="1.0",
        build_date="2025-10-14",
        resources=resources,
        status="Documentation bundle - requires custom implementation"
    )


@router.get("/overview")
def get_smart_guitar_overview() -> Dict[str, Any]:
    """
    Get Smart Guitar system overview and architecture.
    
    Describes the IoT/DAW integration concept.
    """
    overview = {
        "concept": "Smart Guitar DAW Bundle",
        "description": (
            "Integration bundle documenting Smart Guitar IoT/DAW workflow. "
            "Combines lutherie CNC tools with digital audio workstation capabilities "
            "for embedded guitar electronics design and prototyping."
        ),
        "components": {
            "iot_platform": {
                "name": "Smart Guitar IoT Layer",
                "description": "Raspberry Pi 5 based embedded system for guitar electronics",
                "features": [
                    "Real-time audio processing",
                    "Sensor integration (piezo, capacitive touch)",
                    "Wireless connectivity (BLE, WiFi)",
                    "MIDI over USB/Bluetooth",
                    "Custom DSP algorithms"
                ]
            },
            "daw_integration": {
                "name": "DAW Integration Layer",
                "description": "Software bridges to professional audio production tools",
                "partners": [
                    {
                        "name": "Giglad",
                        "purpose": "Live performance and backing track generation",
                        "status": "OEM partnership documented"
                    },
                    {
                        "name": "PGMusic (Band-in-a-Box)",
                        "purpose": "Chord recognition and accompaniment generation",
                        "status": "OEM partnership documented"
                    }
                ]
            },
            "lutherie_bridge": {
                "name": "Lutherie CAD/CAM Bridge",
                "description": "Integration with Luthier's ToolBox CNC tools",
                "features": [
                    "Electronics cavity routing templates",
                    "PCB mounting bracket generation",
                    "Control panel cutout automation",
                    "Wiring harness design integration"
                ]
            }
        },
        "use_cases": [
            "IoT-enabled guitar prototyping",
            "Smart pickup routing and installation",
            "Digital effects integration",
            "MIDI guitar controller design",
            "Embedded DSP guitar pedal design"
        ],
        "status": {
            "phase": "Documentation and planning",
            "implementation": "Custom development required",
            "timeline": "TBD based on user requirements"
        },
        "documentation_available": True,
        "hardware_specs_available": False,
        "software_sdk_available": False
    }
    
    return {"ok": True, "overview": overview}


@router.get("/resources")
def list_smart_guitar_resources() -> Dict[str, Any]:
    """
    List all available Smart Guitar resources.
    
    Returns documentation files, OEM letters, and integration plans.
    """
    bundle_dir = Path("Luthiers_ToolBox_Smart_Guitar_DAW_Bundle_v1.0/Build_10-14-2025")
    
    if not bundle_dir.exists():
        return {
            "ok": True,
            "resources": [],
            "message": "Smart Guitar DAW Bundle directory not found"
        }
    
    resources = []
    for item in bundle_dir.iterdir():
        if item.is_file():
            resources.append({
                "name": item.name,
                "type": item.suffix[1:] if item.suffix else "file",
                "size_kb": round(item.stat().st_size / 1024, 2),
                "path": str(item)
            })
    
    return {
        "ok": True,
        "bundle_path": str(bundle_dir),
        "resources": resources,
        "count": len(resources)
    }


@router.get("/resources/{filename}")
def download_smart_guitar_resource(filename: str) -> FileResponse:
    """
    Download a specific Smart Guitar resource file.
    
    Available files: Integration_Plan_v1.0.txt, Read_Me_First.txt, etc.
    """
    bundle_dir = Path("Luthiers_ToolBox_Smart_Guitar_DAW_Bundle_v1.0/Build_10-14-2025")
    
    file_path = bundle_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Resource file not found: {filename}"
        )
    
    # Determine media type
    media_type_map = {
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".md": "text/markdown"
    }
    media_type = media_type_map.get(file_path.suffix, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )


@router.get("/integration-notes")
def get_integration_notes() -> Dict[str, Any]:
    """
    Get integration notes and requirements.
    
    Returns guidance for custom Smart Guitar implementation.
    """
    notes = {
        "overview": (
            "The Smart Guitar DAW Bundle is a documentation package that outlines "
            "the architecture and partnerships for integrating IoT guitar electronics "
            "with professional DAW software."
        ),
        "requirements": {
            "hardware": [
                "Raspberry Pi 5 (recommended) or similar SBC",
                "Audio interface HAT (HiFiBerry, Pisound, or AudioInjector)",
                "Piezo pickups or magnetic pickups with preamp",
                "Power supply (5V 3A minimum for Pi 5)",
                "Optional: Touch sensors, accelerometers, LED indicators"
            ],
            "software": [
                "Linux-based OS (Raspberry Pi OS recommended)",
                "JACK Audio Connection Kit",
                "Python 3.10+ for control scripts",
                "MIDI libraries (python-rtmidi or mido)",
                "Optional: Pure Data or SuperCollider for DSP"
            ],
            "lutherie_integration": [
                "Electronics cavity routing (use CAM adaptive pocketing)",
                "PCB mounting brackets (use 3D printing or CNC milling)",
                "Control panel cutouts (use DXF templates)",
                "Wiring harness integration (use Wiring Workbench module)"
            ]
        },
        "development_phases": [
            {
                "phase": 1,
                "name": "Hardware Prototyping",
                "tasks": [
                    "Select and test audio interface",
                    "Design electronics cavity (use Luthier's ToolBox CAM)",
                    "Route pickup mounting locations",
                    "Install and test basic audio capture"
                ]
            },
            {
                "phase": 2,
                "name": "Software Integration",
                "tasks": [
                    "Set up JACK audio routing",
                    "Implement MIDI output",
                    "Test DAW connectivity (Giglad, Band-in-a-Box)",
                    "Develop control interface"
                ]
            },
            {
                "phase": 3,
                "name": "Production Integration",
                "tasks": [
                    "Finalize electronics layout",
                    "Generate production CNC files",
                    "Create installation documentation",
                    "Test with multiple guitar models"
                ]
            }
        ],
        "oem_partnerships": {
            "giglad": {
                "purpose": "Live performance backing tracks",
                "integration": "MIDI input, chord recognition",
                "documentation": "Giglad_OEM_Letter.txt"
            },
            "pgmusic": {
                "purpose": "Band-in-a-Box integration",
                "integration": "Chord input, style selection",
                "documentation": "PGMusic_OEM_Letter.txt"
            }
        },
        "next_steps": [
            "Review Integration_Plan_v1.0.txt for architecture details",
            "Contact OEM partners (Giglad, PGMusic) if pursuing integration",
            "Use Luthier's ToolBox CAM tools for electronics cavity routing",
            "Prototype with Raspberry Pi and basic audio interface"
        ],
        "status": "Documentation bundle - custom implementation required"
    }
    
    return {"ok": True, "integration_notes": notes}


@router.get("/health")
def smart_guitar_health() -> Dict[str, Any]:
    """Health check for Smart Guitar module"""
    bundle_dir = Path("Luthiers_ToolBox_Smart_Guitar_DAW_Bundle_v1.0/Build_10-14-2025")
    bundle_exists = bundle_dir.exists()
    
    resources_count = 0
    if bundle_exists:
        resources_count = len([f for f in bundle_dir.iterdir() if f.is_file()])
    
    return {
        "ok": True,
        "module": "smart-guitar",
        "bundle_exists": bundle_exists,
        "bundle_version": "1.0",
        "build_date": "2025-10-14",
        "resources_count": resources_count,
        "status": "Documentation bundle available",
        "implementation_status": "Custom development required"
    }
