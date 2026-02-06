"""
Tap Tone Analyzer Capability Declaration

Declares what the tap_tone_pi desktop analyzer can do.
This is the "thin waist" contract between repos.

The actual analyzer lives in tap_tone_pi repo.
This declaration enables agent discovery and orchestration.
"""

from ..contracts import (
    ToolCapabilityV1,
    CapabilityAction,
    SafeDefaults,
)


# -----------------------------------------------------------------------------
# Tap Tone Analyzer Capability
# -----------------------------------------------------------------------------

TAP_TONE_ANALYZER = ToolCapabilityV1(
    # Identity
    tool_id="tap_tone_analyzer",
    version="1.0.0",
    display_name="Tap Tone Analyzer",
    description=(
        "Analyzes acoustic tap tone recordings to identify resonant modes, "
        "wolf tones, and tonal characteristics of instrument bodies. "
        "Produces structured analysis artifacts including mode identification, "
        "ODS snapshots, and wolf candidate detection."
    ),

    # Capabilities
    actions=[
        CapabilityAction.ANALYZE_AUDIO,
        CapabilityAction.ANALYZE_SPECTRUM,
        CapabilityAction.GENERATE_REPORT,
        CapabilityAction.VALIDATE_SCHEMA,
    ],

    # Input/Output schemas
    input_schemas=[
        "tap_tone_bundle_v1",       # TapToneBundleManifestV1
        "audio_wav",                # Raw WAV files
        "session_meta_v1",          # Session metadata
        "capture_meta_v1",          # Capture metadata
    ],
    output_schemas=[
        "wolf_candidates_v1",       # Wolf tone candidates
        "mode_analysis_v1",         # Mode identification
        "ods_snapshot_v1",          # Operating deflection shapes
        "chladni_run_v1",           # Chladni pattern analysis
        "moe_result_v1",            # Mixture of experts result
        "viewer_pack_v1",           # Exportable viewer pack
    ],

    # Safety defaults
    safe_defaults=SafeDefaults(
        redaction_layer=2,          # Analysis results can be Layer 2
        pii_scrub_enabled=True,     # No PII in acoustic data
        dry_run=False,              # Analysis is read-only, no dry_run needed
        require_confirmation=False, # Analysis is non-destructive
        timeout_seconds=120,        # Acoustic analysis can take time
        max_output_size_bytes=50_000_000,  # 50MB for viewer packs
    ),

    # Metadata
    tags=[
        "acoustic",
        "analysis",
        "tap_tone",
        "modal_analysis",
        "wolf_tone",
        "instrument",
        "guitar",
        "violin",
    ],

    # Cross-repo coordination
    source_repo="tap_tone_pi",
    requires_repos=[],  # Self-contained
)


# -----------------------------------------------------------------------------
# Sub-Capabilities (Phase 2 pipeline stages)
# -----------------------------------------------------------------------------

TAP_TONE_WOLF_DETECTOR = ToolCapabilityV1(
    tool_id="tap_tone_wolf_detector",
    version="1.0.0",
    display_name="Wolf Tone Detector",
    description=(
        "Detects potential wolf tone frequencies in tap tone recordings. "
        "Identifies problematic resonances that may cause tonal issues."
    ),
    actions=[
        CapabilityAction.ANALYZE_SPECTRUM,
    ],
    input_schemas=["phase2_grid_v1"],
    output_schemas=["wolf_candidates_v1"],
    safe_defaults=SafeDefaults(
        redaction_layer=2,
        timeout_seconds=60,
    ),
    tags=["wolf_tone", "spectrum", "analysis"],
    source_repo="tap_tone_pi",
)


TAP_TONE_ODS_ANALYZER = ToolCapabilityV1(
    tool_id="tap_tone_ods_analyzer",
    version="1.0.0",
    display_name="ODS Analyzer",
    description=(
        "Generates Operating Deflection Shape (ODS) snapshots from tap tone data. "
        "Visualizes how the instrument body moves at specific frequencies."
    ),
    actions=[
        CapabilityAction.ANALYZE_AUDIO,
        CapabilityAction.GENERATE_PREVIEW,
    ],
    input_schemas=["phase2_grid_v1"],
    output_schemas=["ods_snapshot_v1"],
    safe_defaults=SafeDefaults(
        redaction_layer=2,
        timeout_seconds=90,
    ),
    tags=["ods", "deflection", "visualization"],
    source_repo="tap_tone_pi",
)


TAP_TONE_CHLADNI_ANALYZER = ToolCapabilityV1(
    tool_id="tap_tone_chladni_analyzer",
    version="1.0.0",
    display_name="Chladni Pattern Analyzer",
    description=(
        "Analyzes Chladni patterns from tap tone grid data. "
        "Identifies nodal lines and resonant mode shapes."
    ),
    actions=[
        CapabilityAction.ANALYZE_AUDIO,
        CapabilityAction.GENERATE_PREVIEW,
    ],
    input_schemas=["phase2_grid_v1"],
    output_schemas=["chladni_run_v1"],
    safe_defaults=SafeDefaults(
        redaction_layer=2,
        timeout_seconds=120,
    ),
    tags=["chladni", "modal", "visualization"],
    source_repo="tap_tone_pi",
)


# -----------------------------------------------------------------------------
# Capability Registry
# -----------------------------------------------------------------------------

TAP_TONE_CAPABILITIES = [
    TAP_TONE_ANALYZER,
    TAP_TONE_WOLF_DETECTOR,
    TAP_TONE_ODS_ANALYZER,
    TAP_TONE_CHLADNI_ANALYZER,
]


def get_tap_tone_capabilities() -> list[ToolCapabilityV1]:
    """Return all tap_tone_pi capabilities for agent discovery."""
    return TAP_TONE_CAPABILITIES.copy()


def get_capability_by_id(tool_id: str) -> ToolCapabilityV1 | None:
    """Look up a specific capability by ID."""
    for cap in TAP_TONE_CAPABILITIES:
        if cap.tool_id == tool_id:
            return cap
    return None
