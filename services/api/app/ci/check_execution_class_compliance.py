"""
CI Guard: Execution Class Compliance

Rules:
- All CAM endpoints MUST normalize CamIntentV1
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


def is_cam_router(file: Path) -> bool:
    """Check if file is a CAM router that produces machine output."""
    return "cam" in file.parts and file.suffix == ".py"


def has_intent_normalization(text: str) -> bool:
    """Check if module normalizes CamIntentV1."""
    return "normalize_cam_intent_v1" in text


def is_deterministic(file: Path) -> bool:
    """Check if module is in the deterministic allowlist (Execution Class B)."""
    return any(part in DETERMINISTIC_ALLOWLIST for part in file.parts)


def main() -> int:
    violations = []

    for py in ROOT.rglob("*.py"):
        if not is_cam_router(py):
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
