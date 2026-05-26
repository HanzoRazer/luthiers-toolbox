"""
CI Guard: CAM Intent Surface Compliance

Ensures the H7.1/H7.2 CamIntentV1 HTTP surface cannot be removed silently:
- Required intent router modules exist on disk
- Each router calls normalize_cam_intent_v1
- Both routers are registered in router_registry manifests

Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md (Appendix D)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # services/api/app

REQUIRED_INTENT_ROUTER_FILES = (
    "routers/cam_roughing_intent_router.py",
    "routers/rmos_cam_intent_router.py",
)

REQUIRED_MANIFEST_MODULES = {
    "app.routers.cam_roughing_intent_router",
    "app.routers.rmos_cam_intent_router",
}

MANIFEST_PATHS = (
    ROOT / "router_registry" / "manifests" / "cam_manifest.py",
    ROOT / "router_registry" / "manifests" / "rmos_manifest.py",
)


def has_intent_normalization(text: str) -> bool:
    return "normalize_cam_intent_v1" in text


def check_required_routers() -> list[str]:
    violations: list[str] = []
    for rel in REQUIRED_INTENT_ROUTER_FILES:
        path = ROOT / rel
        if not path.is_file():
            violations.append(f"Missing required CAM intent router: app/{rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not has_intent_normalization(text):
            violations.append(f"app/{rel} must call normalize_cam_intent_v1")
    return violations


def check_manifest_registration() -> list[str]:
    violations: list[str] = []
    found: set[str] = set()
    for manifest in MANIFEST_PATHS:
        if not manifest.is_file():
            violations.append(f"Missing router manifest: {manifest}")
            continue
        text = manifest.read_text(encoding="utf-8", errors="ignore")
        for module in REQUIRED_MANIFEST_MODULES:
            if f'module="{module}"' in text or f"module='{module}'" in text:
                found.add(module)
    missing = REQUIRED_MANIFEST_MODULES - found
    for module in sorted(missing):
        violations.append(f"CAM intent router not registered in manifest: {module}")
    return violations


def main() -> int:
    violations = check_required_routers() + check_manifest_registration()
    if violations:
        print("\nFAIL: CAM Intent surface compliance violation\n")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nRestore routers via git checkout and register in "
            "cam_manifest.py / rmos_manifest.py.\n"
        )
        return 1

    print("OK: CAM intent surface compliance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
