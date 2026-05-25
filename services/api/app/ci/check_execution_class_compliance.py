"""
CI Guard: Execution Class Compliance

Rules:
- OPERATION-lane CamIntentV1 endpoints MUST call normalize_cam_intent_v1
- Only checks intent_router.py files (canonical OPERATION-lane pattern)
- Execution Class B (deterministic) endpoints are allowed
  to execute in a single pass without feasibility/advisory logic

Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md (Appendix D)
"""

from pathlib import Path
import sys

ROOT = Path(__file__).parents[3]

# Explicitly allowed deterministic modules (Execution Class B)
DETERMINISTIC_ALLOWLIST = {
    "saw_lab",
    "saw",
    "cnc_saw",
}


def is_operation_lane_router(file: Path) -> bool:
    """
    Check if file is an OPERATION-lane router that must normalize CamIntentV1.

    Only checks intent_router.py files - the canonical OPERATION-lane pattern
    established by 8G (V-Carve) and extended by 8H+ migrations.

    Legacy routers with LANE: OPERATION markers predate CamIntentV1 and will
    be migrated incrementally. This guard enforces compliance for new
    intent-first endpoints only.
    """
    # Check for intent_router.py pattern (canonical OPERATION-lane pattern from 8G)
    return file.name == "intent_router.py" and "routers" in file.parts


def has_intent_normalization(text: str) -> bool:
    """Check if module normalizes CamIntentV1."""
    return "normalize_cam_intent_v1" in text


def is_deterministic(file: Path) -> bool:
    """Check if module is in the deterministic allowlist (Execution Class B)."""
    return any(part in DETERMINISTIC_ALLOWLIST for part in file.parts)


def main() -> int:
    violations = []

    for py in ROOT.rglob("*.py"):
        if not is_operation_lane_router(py):
            continue

        text = py.read_text(encoding="utf-8", errors="ignore")

        # Has normalization - compliant
        if has_intent_normalization(text):
            continue

        # Is deterministic (Class B) - allowed to skip
        if is_deterministic(py):
            continue

        violations.append(str(py.relative_to(ROOT)))

    if violations:
        print("\n❌ Execution Governance Violation\n")
        print("The following CAM modules do not normalize CamIntentV1:\n")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nSee OPERATION_EXECUTION_GOVERNANCE_v1.md → Appendix D: Execution Classes\n"
        )
        return 1

    print("✅ Execution class compliance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
