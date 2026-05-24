"""
Runtime Spine Versioning.

Sprint: MRP-5T
Status: FROZEN

Version constants for the runtime spine.
These versions track structural compatibility, not marketing releases.
"""

# Runtime spine version - tracks the overall spine structure
# Increment MAJOR for breaking changes to governed contracts
# Increment MINOR for backward-compatible additions
# Increment PATCH for fixes that don't affect contracts
RUNTIME_SPINE_VERSION = "0.1.0"

# Replay bundle schema version - tracks bundle serialization format
# Increment when bundle structure changes in ways that affect replay
REPLAY_BUNDLE_SCHEMA_VERSION = "1"

# Manifest schema version - tracks manifest serialization format
MANIFEST_SCHEMA_VERSION = "1"

# Contract freeze date - when governed contracts were frozen
CONTRACT_FREEZE_DATE = "2026-05-21"

# Sprint that established the contract freeze
CONTRACT_FREEZE_SPRINT = "MRP-5T"


def parse_version(version_str: str) -> tuple:
    """Parse version string into tuple."""
    parts = version_str.split(".")
    return tuple(int(p) for p in parts)


def is_compatible(current: str, required: str) -> bool:
    """
    Check if current version is compatible with required version.

    Compatibility rules:
    - Same MAJOR version required
    - Current MINOR >= required MINOR
    """
    current_parts = parse_version(current)
    required_parts = parse_version(required)

    if len(current_parts) < 2 or len(required_parts) < 2:
        return current == required

    # MAJOR must match
    if current_parts[0] != required_parts[0]:
        return False

    # Current MINOR must be >= required MINOR
    return current_parts[1] >= required_parts[1]


def get_version_info() -> dict:
    """Get all version information."""
    return {
        "runtime_spine_version": RUNTIME_SPINE_VERSION,
        "replay_bundle_schema_version": REPLAY_BUNDLE_SCHEMA_VERSION,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "contract_freeze_date": CONTRACT_FREEZE_DATE,
        "contract_freeze_sprint": CONTRACT_FREEZE_SPRINT,
    }
