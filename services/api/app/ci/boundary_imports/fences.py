"""Fence check functions for boundary import checker."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from .config import (
    AI_SANDBOX_FORBIDDEN_IMPORTS,
    AI_SANDBOX_PATHS,
    ARTIFACT_AUTHORITY_ALLOWED_FILES,
    CAM_ALLOWED_RMOS_IMPORTS,
    CAM_FORBIDDEN_RMOS_IMPORTS,
    EXTERNAL_FORBIDDEN_PREFIXES,
    RMOS_CAM_EXCEPTION_FILES,
    RMOS_FORBIDDEN_CAM_IMPORTS,
    RUNARTIFACT_SYMBOL,
    SAW_LAB_ALLOWED_IMPORTS,
    SAW_LAB_PATHS,
)
from .models import ImportRef, SymbolRef
from .parser import (
    file_matches_path,
    is_cam_file,
    is_rmos_file,
    module_matches_prefix,
    normalize_file_key,
)


def check_external_boundary(
    file_path: Path,
    imports: List[Tuple[int, str]],
) -> List[ImportRef]:
    """Fence 1: Block imports from tap_tone.* and modes.*"""
    violations = []
    for lineno, module in imports:
        for prefix in EXTERNAL_FORBIDDEN_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                violations.append(ImportRef(
                    file=file_path,
                    line=lineno,
                    module=module,
                    fence="external_boundary",
                    reason="Analyzer internals (tap_tone.*, modes.*) are forbidden in ToolBox.",
                ))
                break
    return violations


def check_rmos_cam_boundary(
    file_path: Path,
    imports: List[Tuple[int, str]],
    root: Path,
) -> List[ImportRef]:
    """Fence 2: Bidirectional RMOS <-> CAM isolation."""
    violations = []
    file_key = normalize_file_key(file_path, root)

    # Check exception files
    if file_key in RMOS_CAM_EXCEPTION_FILES:
        return []

    is_cam = is_cam_file(file_path)
    is_rmos = is_rmos_file(file_path)

    for lineno, module in imports:
        # CAM must not import RMOS workflow/runs/feasibility
        if is_cam:
            # Check if it's an allowed exception (CamIntentV1)
            if module_matches_prefix(module, CAM_ALLOWED_RMOS_IMPORTS):
                continue
            if module_matches_prefix(module, CAM_FORBIDDEN_RMOS_IMPORTS):
                violations.append(ImportRef(
                    file=file_path,
                    line=lineno,
                    module=module,
                    fence="rmos_cam_boundary",
                    reason="CAM must not import RMOS workflow/runs/feasibility. Only CamIntent envelope allowed.",
                ))

        # RMOS must not import CAM toolpath/post
        if is_rmos:
            if module_matches_prefix(module, RMOS_FORBIDDEN_CAM_IMPORTS):
                violations.append(ImportRef(
                    file=file_path,
                    line=lineno,
                    module=module,
                    fence="rmos_cam_boundary",
                    reason="RMOS must not import CAM toolpath/post generation. Use CamIntent envelope.",
                ))

    return violations


def check_ai_sandbox_boundary(
    file_path: Path,
    imports: List[Tuple[int, str]],
) -> List[ImportRef]:
    """Fence 4: AI sandbox must not access execution authority."""
    violations = []

    if not file_matches_path(file_path, AI_SANDBOX_PATHS):
        return []

    for lineno, module in imports:
        if module_matches_prefix(module, AI_SANDBOX_FORBIDDEN_IMPORTS):
            violations.append(ImportRef(
                file=file_path,
                line=lineno,
                module=module,
                fence="ai_sandbox_boundary",
                reason="AI sandbox cannot access workflow, runs store, or toolpath generation.",
            ))

    return violations


def check_saw_lab_encapsulation(
    file_path: Path,
    imports: List[Tuple[int, str]],
) -> List[ImportRef]:
    """Fence 5: Saw Lab must stay self-contained."""
    violations = []

    if not file_matches_path(file_path, SAW_LAB_PATHS):
        return []

    for lineno, module in imports:
        # Skip non-app imports
        if not module.startswith("app."):
            continue

        # Check if it's an allowed import
        if module_matches_prefix(module, SAW_LAB_ALLOWED_IMPORTS):
            continue

        violations.append(ImportRef(
            file=file_path,
            line=lineno,
            module=module,
            fence="saw_lab_encapsulation",
            reason="Saw Lab imports must stay within saw_lab, runs_v2, CamIntent envelope, and shared infra.",
        ))

    return violations


def check_artifact_authority(
    file_path: Path,
    symbol_refs: List[Tuple[int, str]],
    root: Path,
) -> List[SymbolRef]:
    """Fence 7: RunArtifact usage restricted to authorized files."""
    violations = []
    file_key = normalize_file_key(file_path, root)

    # Authorized files can use RunArtifact freely
    if file_key in ARTIFACT_AUTHORITY_ALLOWED_FILES:
        return []

    for lineno, symbol in symbol_refs:
        if RUNARTIFACT_SYMBOL in symbol:
            if "()" in symbol:
                reason = "Direct RunArtifact() construction is restricted to runs_v2 store/schemas."
            else:
                reason = "Importing RunArtifact is restricted (use dicts or TYPE_CHECKING only)."

            violations.append(SymbolRef(
                file=file_path,
                line=lineno,
                symbol=symbol,
                fence="artifact_authority",
                reason=reason,
            ))

    return violations
