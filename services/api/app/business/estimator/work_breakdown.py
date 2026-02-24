"""
Work Breakdown Structure Templates — Task decomposition by instrument type.

Each task has:
- task_id: Unique identifier
- task_name: Human-readable name
- base_hours: Time for experienced builder, standard complexity
- complexity_group: Which complexity factors apply (body, neck, finish, etc.)
- phase: Build phase for grouping

Hours are calibrated for:
- Experienced builder (not beginner, not master)
- Standard complexity (no cutaways, simple binding, etc.)
- One-off build (not batch optimized)
"""
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from .schemas import InstrumentType


@dataclass
class WBSTaskTemplate:
    """Template for a WBS task."""
    task_id: str
    task_name: str
    base_hours: float
    complexity_group: Optional[str]  # body, neck, finish, binding, rosette, electronics
    phase: str  # design, prep, body, neck, assembly, finish, final


# =============================================================================
# ACOUSTIC DREADNOUGHT WBS (Baseline: 120-150 hours)
# =============================================================================

WBS_ACOUSTIC_DREADNOUGHT: List[WBSTaskTemplate] = [
    # Design Phase (8-12 hours)
    WBSTaskTemplate("DES_001", "Design & Planning", 4.0, None, "design"),
    WBSTaskTemplate("DES_002", "Wood Selection & Matching", 3.0, None, "design"),
    WBSTaskTemplate("DES_003", "Template Prep & Layout", 2.0, None, "design"),

    # Material Prep Phase (12-15 hours)
    WBSTaskTemplate("PREP_001", "Top Joining & Thicknessing", 3.0, "body", "prep"),
    WBSTaskTemplate("PREP_002", "Back Joining & Thicknessing", 3.0, "body", "prep"),
    WBSTaskTemplate("PREP_003", "Side Thicknessing", 1.5, "body", "prep"),
    WBSTaskTemplate("PREP_004", "Neck Blank Prep", 2.0, "neck", "prep"),
    WBSTaskTemplate("PREP_005", "Fretboard Prep", 1.5, "neck", "prep"),
    WBSTaskTemplate("PREP_006", "Brace Stock Prep", 1.5, None, "prep"),

    # Body Phase (35-45 hours)
    WBSTaskTemplate("BODY_001", "Rosette Installation", 2.5, "rosette", "body"),
    WBSTaskTemplate("BODY_002", "Soundhole Cutting", 0.5, None, "body"),
    WBSTaskTemplate("BODY_003", "Top Bracing Layout", 1.5, None, "body"),
    WBSTaskTemplate("BODY_004", "Top Brace Shaping", 4.0, None, "body"),
    WBSTaskTemplate("BODY_005", "Top Brace Gluing", 2.0, None, "body"),
    WBSTaskTemplate("BODY_006", "Back Bracing", 3.0, None, "body"),
    WBSTaskTemplate("BODY_007", "Side Bending", 2.5, "body", "body"),
    WBSTaskTemplate("BODY_008", "Mold Assembly", 1.0, None, "body"),
    WBSTaskTemplate("BODY_009", "Kerfing Installation", 2.0, None, "body"),
    WBSTaskTemplate("BODY_010", "Top Gluing", 1.5, None, "body"),
    WBSTaskTemplate("BODY_011", "Back Gluing", 1.5, None, "body"),
    WBSTaskTemplate("BODY_012", "Body Trimming & Shaping", 2.0, "body", "body"),
    WBSTaskTemplate("BODY_013", "Binding Channel Routing", 2.5, "binding", "body"),
    WBSTaskTemplate("BODY_014", "Binding Installation", 4.0, "binding", "body"),
    WBSTaskTemplate("BODY_015", "Binding Scraping & Cleanup", 2.0, "binding", "body"),

    # Neck Phase (18-25 hours)
    WBSTaskTemplate("NECK_001", "Neck Shaping (Rough)", 3.0, "neck", "neck"),
    WBSTaskTemplate("NECK_002", "Neck Shaping (Final)", 3.0, "neck", "neck"),
    WBSTaskTemplate("NECK_003", "Headstock Shaping", 2.0, "neck", "neck"),
    WBSTaskTemplate("NECK_004", "Truss Rod Channel", 1.0, None, "neck"),
    WBSTaskTemplate("NECK_005", "Truss Rod Installation", 0.5, None, "neck"),
    WBSTaskTemplate("NECK_006", "Fretboard Radiusing", 1.5, "neck", "neck"),
    WBSTaskTemplate("NECK_007", "Fret Slot Cutting", 1.0, None, "neck"),
    WBSTaskTemplate("NECK_008", "Inlay Routing", 2.0, "inlay", "neck"),
    WBSTaskTemplate("NECK_009", "Inlay Installation", 2.0, "inlay", "neck"),
    WBSTaskTemplate("NECK_010", "Fretboard Gluing", 1.0, None, "neck"),
    WBSTaskTemplate("NECK_011", "Fret Installation", 2.5, None, "neck"),
    WBSTaskTemplate("NECK_012", "Fret Leveling & Crowning", 2.0, None, "neck"),
    WBSTaskTemplate("NECK_013", "Fret End Dressing", 1.0, None, "neck"),

    # Assembly Phase (8-12 hours)
    WBSTaskTemplate("ASSY_001", "Neck Pocket/Dovetail Fitting", 3.0, None, "assembly"),
    WBSTaskTemplate("ASSY_002", "Neck Setting & Gluing", 2.0, None, "assembly"),
    WBSTaskTemplate("ASSY_003", "Bridge Location & Prep", 1.5, None, "assembly"),
    WBSTaskTemplate("ASSY_004", "Nut Blank Fitting", 1.0, None, "assembly"),

    # Finish Phase (25-40 hours)
    WBSTaskTemplate("FIN_001", "Sanding (150-220)", 3.0, None, "finish"),
    WBSTaskTemplate("FIN_002", "Sanding (320-400)", 2.0, None, "finish"),
    WBSTaskTemplate("FIN_003", "Grain Filling (if needed)", 2.0, "finish", "finish"),
    WBSTaskTemplate("FIN_004", "Sealer Application", 2.0, "finish", "finish"),
    WBSTaskTemplate("FIN_005", "Color Coats (if burst)", 3.0, "finish", "finish"),
    WBSTaskTemplate("FIN_006", "Clear Coats", 4.0, "finish", "finish"),
    WBSTaskTemplate("FIN_007", "Finish Curing (wait time)", 0.0, None, "finish"),  # Calendar time, not labor
    WBSTaskTemplate("FIN_008", "Wet Sanding", 3.0, "finish", "finish"),
    WBSTaskTemplate("FIN_009", "Buffing & Polishing", 2.5, "finish", "finish"),

    # Final Phase (8-12 hours)
    WBSTaskTemplate("FINAL_001", "Bridge Gluing", 1.5, None, "final"),
    WBSTaskTemplate("FINAL_002", "Nut Shaping & Slotting", 1.5, None, "final"),
    WBSTaskTemplate("FINAL_003", "Saddle Fitting", 1.0, None, "final"),
    WBSTaskTemplate("FINAL_004", "Tuner Installation", 0.5, None, "final"),
    WBSTaskTemplate("FINAL_005", "String Installation", 0.5, None, "final"),
    WBSTaskTemplate("FINAL_006", "Setup & Intonation", 2.0, None, "final"),
    WBSTaskTemplate("FINAL_007", "Final Inspection & QA", 1.5, None, "final"),
    WBSTaskTemplate("FINAL_008", "Documentation & Photos", 1.0, None, "final"),
]


# =============================================================================
# CLASSICAL GUITAR WBS (Similar to dreadnought, different bracing)
# =============================================================================

WBS_CLASSICAL: List[WBSTaskTemplate] = [
    # Design Phase
    WBSTaskTemplate("DES_001", "Design & Planning", 4.0, None, "design"),
    WBSTaskTemplate("DES_002", "Wood Selection & Matching", 3.0, None, "design"),
    WBSTaskTemplate("DES_003", "Template Prep & Layout", 2.0, None, "design"),

    # Material Prep Phase
    WBSTaskTemplate("PREP_001", "Top Joining & Thicknessing", 3.0, "body", "prep"),
    WBSTaskTemplate("PREP_002", "Back Joining & Thicknessing", 3.0, "body", "prep"),
    WBSTaskTemplate("PREP_003", "Side Thicknessing", 1.5, "body", "prep"),
    WBSTaskTemplate("PREP_004", "Neck Blank Prep (Spanish heel)", 3.0, "neck", "prep"),
    WBSTaskTemplate("PREP_005", "Fretboard Prep", 1.5, "neck", "prep"),
    WBSTaskTemplate("PREP_006", "Brace Stock Prep", 1.5, None, "prep"),

    # Body Phase (Fan bracing is more complex)
    WBSTaskTemplate("BODY_001", "Rosette Installation", 3.0, "rosette", "body"),
    WBSTaskTemplate("BODY_002", "Soundhole Cutting", 0.5, None, "body"),
    WBSTaskTemplate("BODY_003", "Fan Brace Layout", 2.0, None, "body"),
    WBSTaskTemplate("BODY_004", "Fan Brace Shaping", 5.0, None, "body"),
    WBSTaskTemplate("BODY_005", "Fan Brace Gluing", 2.5, None, "body"),
    WBSTaskTemplate("BODY_006", "Harmonic Bars", 1.5, None, "body"),
    WBSTaskTemplate("BODY_007", "Back Bracing", 2.5, None, "body"),
    WBSTaskTemplate("BODY_008", "Side Bending", 2.5, "body", "body"),
    WBSTaskTemplate("BODY_009", "Spanish Heel Integration", 3.0, "neck", "body"),
    WBSTaskTemplate("BODY_010", "Kerfing/Tentellones", 2.0, None, "body"),
    WBSTaskTemplate("BODY_011", "Top Gluing", 1.5, None, "body"),
    WBSTaskTemplate("BODY_012", "Back Gluing", 1.5, None, "body"),
    WBSTaskTemplate("BODY_013", "Body Trimming", 2.0, "body", "body"),
    WBSTaskTemplate("BODY_014", "Binding Installation", 3.5, "binding", "body"),

    # Neck Phase
    WBSTaskTemplate("NECK_001", "Neck Shaping", 4.0, "neck", "neck"),
    WBSTaskTemplate("NECK_002", "Headstock Shaping (Slotted)", 2.5, "neck", "neck"),
    WBSTaskTemplate("NECK_003", "Fretboard Prep (Flat)", 1.0, "neck", "neck"),
    WBSTaskTemplate("NECK_004", "Fret Slot Cutting", 1.0, None, "neck"),
    WBSTaskTemplate("NECK_005", "Fretboard Gluing", 1.0, None, "neck"),
    WBSTaskTemplate("NECK_006", "Fret Installation", 2.0, None, "neck"),
    WBSTaskTemplate("NECK_007", "Fret Dressing", 2.0, None, "neck"),

    # Finish Phase (Often French polish)
    WBSTaskTemplate("FIN_001", "Sanding Prep", 4.0, None, "finish"),
    WBSTaskTemplate("FIN_002", "Pore Filling", 2.0, "finish", "finish"),
    WBSTaskTemplate("FIN_003", "French Polish/Lacquer", 8.0, "finish", "finish"),
    WBSTaskTemplate("FIN_004", "Final Polish", 2.0, "finish", "finish"),

    # Final Phase
    WBSTaskTemplate("FINAL_001", "Bridge Gluing", 1.5, None, "final"),
    WBSTaskTemplate("FINAL_002", "Nut Shaping", 1.5, None, "final"),
    WBSTaskTemplate("FINAL_003", "Saddle Fitting", 1.0, None, "final"),
    WBSTaskTemplate("FINAL_004", "Tuner Installation", 0.5, None, "final"),
    WBSTaskTemplate("FINAL_005", "Setup", 2.0, None, "final"),
    WBSTaskTemplate("FINAL_006", "Final QA", 1.5, None, "final"),
]


# =============================================================================
# ELECTRIC SOLID BODY WBS (Baseline: 60-80 hours)
# =============================================================================

WBS_ELECTRIC_SOLID: List[WBSTaskTemplate] = [
    # Design Phase
    WBSTaskTemplate("DES_001", "Design & Planning", 3.0, None, "design"),
    WBSTaskTemplate("DES_002", "Wood Selection", 2.0, None, "design"),
    WBSTaskTemplate("DES_003", "Template Prep", 2.0, None, "design"),

    # Body Phase
    WBSTaskTemplate("BODY_001", "Body Blank Glue-up", 1.5, None, "body"),
    WBSTaskTemplate("BODY_002", "Body Outline Routing", 1.5, "body", "body"),
    WBSTaskTemplate("BODY_003", "Body Shaping/Carving", 3.0, "body", "body"),
    WBSTaskTemplate("BODY_004", "Pickup Routing", 2.0, "electronics", "body"),
    WBSTaskTemplate("BODY_005", "Control Cavity Routing", 1.5, "electronics", "body"),
    WBSTaskTemplate("BODY_006", "Neck Pocket Routing", 1.5, None, "body"),
    WBSTaskTemplate("BODY_007", "Bridge/Trem Routing", 2.0, None, "body"),
    WBSTaskTemplate("BODY_008", "Wire Channels", 1.0, "electronics", "body"),
    WBSTaskTemplate("BODY_009", "Body Sanding", 2.0, None, "body"),

    # Neck Phase
    WBSTaskTemplate("NECK_001", "Neck Blank Prep", 1.5, "neck", "neck"),
    WBSTaskTemplate("NECK_002", "Neck Profile Shaping", 3.0, "neck", "neck"),
    WBSTaskTemplate("NECK_003", "Headstock Shaping", 1.5, "neck", "neck"),
    WBSTaskTemplate("NECK_004", "Truss Rod Install", 1.0, None, "neck"),
    WBSTaskTemplate("NECK_005", "Fretboard Prep", 1.5, "neck", "neck"),
    WBSTaskTemplate("NECK_006", "Inlay Work", 2.0, "inlay", "neck"),
    WBSTaskTemplate("NECK_007", "Fret Installation", 2.0, None, "neck"),
    WBSTaskTemplate("NECK_008", "Fret Leveling", 1.5, None, "neck"),

    # Finish Phase
    WBSTaskTemplate("FIN_001", "Sanding Prep", 2.0, None, "finish"),
    WBSTaskTemplate("FIN_002", "Grain Filling", 1.5, "finish", "finish"),
    WBSTaskTemplate("FIN_003", "Sealer", 1.0, "finish", "finish"),
    WBSTaskTemplate("FIN_004", "Color/Clear Coats", 4.0, "finish", "finish"),
    WBSTaskTemplate("FIN_005", "Wet Sand & Buff", 3.0, "finish", "finish"),

    # Assembly Phase
    WBSTaskTemplate("ASSY_001", "Neck Attachment", 1.0, None, "assembly"),
    WBSTaskTemplate("ASSY_002", "Hardware Install", 1.5, None, "assembly"),
    WBSTaskTemplate("ASSY_003", "Electronics Install", 2.0, "electronics", "assembly"),
    WBSTaskTemplate("ASSY_004", "Wiring", 1.5, "electronics", "assembly"),
    WBSTaskTemplate("ASSY_005", "Nut & Setup", 2.0, None, "assembly"),
    WBSTaskTemplate("ASSY_006", "Final QA", 1.0, None, "assembly"),
]


# =============================================================================
# WBS REGISTRY
# =============================================================================

WBS_TEMPLATES: Dict[InstrumentType, List[WBSTaskTemplate]] = {
    InstrumentType.ACOUSTIC_DREADNOUGHT: WBS_ACOUSTIC_DREADNOUGHT,
    InstrumentType.ACOUSTIC_OM: WBS_ACOUSTIC_DREADNOUGHT,  # Same as dread, slightly smaller
    InstrumentType.ACOUSTIC_PARLOR: WBS_ACOUSTIC_DREADNOUGHT,  # Same structure
    InstrumentType.CLASSICAL: WBS_CLASSICAL,
    InstrumentType.ELECTRIC_SOLID: WBS_ELECTRIC_SOLID,
    InstrumentType.ELECTRIC_HOLLOW: WBS_ACOUSTIC_DREADNOUGHT,  # Hybrid
    InstrumentType.ELECTRIC_SEMI: WBS_ELECTRIC_SOLID,  # Modified solid
    InstrumentType.BASS_4: WBS_ELECTRIC_SOLID,  # Similar to electric
    InstrumentType.BASS_5: WBS_ELECTRIC_SOLID,
}


def get_wbs_template(instrument_type: InstrumentType) -> List[WBSTaskTemplate]:
    """Get WBS template for instrument type."""
    return WBS_TEMPLATES.get(instrument_type, WBS_ACOUSTIC_DREADNOUGHT)


def get_wbs_total_hours(instrument_type: InstrumentType) -> float:
    """Get total base hours for instrument type."""
    template = get_wbs_template(instrument_type)
    return sum(t.base_hours for t in template)


def get_wbs_by_phase(instrument_type: InstrumentType) -> Dict[str, List[WBSTaskTemplate]]:
    """Get WBS grouped by phase."""
    template = get_wbs_template(instrument_type)
    phases: Dict[str, List[WBSTaskTemplate]] = {}

    for task in template:
        if task.phase not in phases:
            phases[task.phase] = []
        phases[task.phase].append(task)

    return phases
