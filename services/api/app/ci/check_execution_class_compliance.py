"""
CI Guard: CAM Intent Surface + Operation-Lane Compliance

Enforces TWO invariants (synthesized DO-CAM-RESCUE-02 — neither subsumes the other):

(A) Surface anti-deletion (H7.1/H7.2 CamIntentV1 HTTP surface cannot be removed
    silently — the guard that exists because of the 545fccad silent deletion):
    - Required intent router modules exist on disk
    - Each calls normalize_cam_intent_v1
    - Both are registered in router_registry manifests

(B) Operation-lane coverage (the 8G/8H pattern — self-extending to future lanes):
    - Every */routers/*/intent_router.py MUST call normalize_cam_intent_v1
    - Execution Class B (deterministic) modules are allowed to skip (allowlist)

Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md (Appendix D)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # services/api/app

# --- (A) Surface anti-deletion invariant ---------------------------------------

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

# --- (B) Operation-lane coverage invariant -------------------------------------

# Explicitly allowed deterministic modules (Execution Class B) — ported from 8H.
# Carried verbatim so a deterministic intent_router is not falsely flagged.
DETERMINISTIC_ALLOWLIST = {
    "saw_lab",
    "saw",
    "cnc_saw",
}


def has_intent_normalization(text: str) -> bool:
    return "normalize_cam_intent_v1" in text


def is_operation_lane_router(file: Path) -> bool:
    """
    OPERATION-lane router that must normalize CamIntentV1 — the canonical
    pattern established by 8G (V-Carve) and extended by 8H+ migrations.
    Self-extending: any future */routers/*/intent_router.py is covered with
    no allowlist maintenance.
    """
    return file.name == "intent_router.py" and "routers" in file.parts


def is_deterministic(file: Path) -> bool:
    """Module is in the deterministic allowlist (Execution Class B)."""
    return any(part in DETERMINISTIC_ALLOWLIST for part in file.parts)


def check_required_routers() -> list[str]:
    """(A) H7 surface routers must exist on disk and normalize CamIntentV1."""
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
    """(A) H7 surface routers must be registered in router_registry manifests."""
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


def check_operation_lane_routers() -> list[str]:
    """
    (B) Every */routers/*/intent_router.py must call normalize_cam_intent_v1,
    unless it is an allowlisted deterministic (Execution Class B) module.
    """
    violations: list[str] = []
    for py in ROOT.rglob("intent_router.py"):
        if not is_operation_lane_router(py):
            continue
        if is_deterministic(py):
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        if not has_intent_normalization(text):
            rel = py.relative_to(ROOT).as_posix()
            violations.append(
                f"app/{rel} (operation-lane) must call normalize_cam_intent_v1"
            )
    return violations


def main() -> int:
    violations = (
        check_required_routers()
        + check_manifest_registration()
        + check_operation_lane_routers()
    )
    if violations:
        print("\nFAIL: CAM Intent surface + operation-lane compliance violation\n")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nFix: (A) restore/register the H7 surface routers in "
            "cam_manifest.py / rmos_manifest.py; (B) ensure every "
            "*/routers/*/intent_router.py calls normalize_cam_intent_v1 "
            "(or is an allowlisted Class-B module).\n"
        )
        return 1

    print("OK: CAM intent surface + operation-lane compliance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
