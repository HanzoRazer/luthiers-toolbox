"""
AI Safety Policy - Allow/Deny Rules

Defines what categories of AI generation are allowed,
blocked terms, and safety classification logic.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional, Set, Tuple
from dataclasses import dataclass


class SafetyCategory(str, Enum):
    """Categories of AI-generated content."""
    ROSETTE_DESIGN = "rosette_design"
    GUITAR_PATTERN = "guitar_pattern"
    WOODWORKING = "woodworking"
    CAM_ADVISOR = "cam_advisor"
    GENERAL_IMAGE = "general_image"
    CODE_GENERATION = "code_generation"
    UNKNOWN = "unknown"


class SafetyLevel(str, Enum):
    """Safety classification levels."""
    GREEN = "green"   # Safe, proceed
    YELLOW = "yellow" # Caution, may need review
    RED = "red"       # Blocked, do not proceed


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    level: SafetyLevel
    category: SafetyCategory
    blocked_terms_found: List[str]
    warnings: List[str]
    is_allowed: bool

    @property
    def is_blocked(self) -> bool:
        return self.level == SafetyLevel.RED


# ---------------------------------------------------------------------------
# Blocked Terms
# ---------------------------------------------------------------------------

# Terms that should never appear in lutherie/woodworking AI prompts
BLOCKED_TERMS: Set[str] = {
    # Violence
    "weapon", "weapons", "gun", "knife", "bomb", "explosive",
    # Inappropriate content
    "nude", "nsfw", "explicit", "sexual",
    # Harmful
    "harm", "hurt", "kill", "destroy", "attack",
    # Off-topic indicators
    "cryptocurrency", "nft", "blockchain",
}

# Terms that trigger warnings but don't block
WARNING_TERMS: Set[str] = {
    "sharp", "blade", "cut", "carve",  # Valid in woodworking context
    "fire", "burn",  # Valid for finishing/aging
}


# ---------------------------------------------------------------------------
# Category Detection
# ---------------------------------------------------------------------------

def detect_category(prompt: str) -> SafetyCategory:
    """
    Detect the likely category of an AI prompt.

    Args:
        prompt: The user's prompt text

    Returns:
        SafetyCategory enum value
    """
    prompt_lower = prompt.lower()

    # Rosette/inlay patterns
    rosette_keywords = ["rosette", "inlay", "soundhole", "ring", "pattern", "mosaic"]
    if any(kw in prompt_lower for kw in rosette_keywords):
        return SafetyCategory.ROSETTE_DESIGN

    # Guitar/instrument patterns
    guitar_keywords = ["guitar", "fret", "neck", "body", "headstock", "pickguard"]
    if any(kw in prompt_lower for kw in guitar_keywords):
        return SafetyCategory.GUITAR_PATTERN

    # Woodworking general
    wood_keywords = ["wood", "carving", "routing", "cnc", "toolpath", "grain"]
    if any(kw in prompt_lower for kw in wood_keywords):
        return SafetyCategory.WOODWORKING

    # CAM/machining advice
    cam_keywords = ["feed", "speed", "rpm", "chipload", "depth", "stepover"]
    if any(kw in prompt_lower for kw in cam_keywords):
        return SafetyCategory.CAM_ADVISOR

    return SafetyCategory.UNKNOWN


# ---------------------------------------------------------------------------
# Allowed Categories
# ---------------------------------------------------------------------------

# Categories that are always allowed
ALWAYS_ALLOWED: Set[SafetyCategory] = {
    SafetyCategory.ROSETTE_DESIGN,
    SafetyCategory.GUITAR_PATTERN,
    SafetyCategory.WOODWORKING,
    SafetyCategory.CAM_ADVISOR,
}

# Categories that require review
REQUIRES_REVIEW: Set[SafetyCategory] = {
    SafetyCategory.GENERAL_IMAGE,
    SafetyCategory.CODE_GENERATION,
    SafetyCategory.UNKNOWN,
}


def is_category_allowed(category: SafetyCategory) -> bool:
    """Check if a category is allowed without review."""
    return category in ALWAYS_ALLOWED


# ---------------------------------------------------------------------------
# Safety Check
# ---------------------------------------------------------------------------

def check_prompt_safety(
    prompt: str,
    category: Optional[SafetyCategory] = None,
) -> SafetyCheckResult:
    """
    Check if a prompt is safe for AI generation.

    Args:
        prompt: The user's prompt text
        category: Optional category override (auto-detected if not provided)

    Returns:
        SafetyCheckResult with level, category, and details
    """
    if category is None:
        category = detect_category(prompt)

    prompt_lower = prompt.lower()

    # Check for blocked terms
    blocked_found = []
    for term in BLOCKED_TERMS:
        if re.search(rf'\b{re.escape(term)}\b', prompt_lower):
            blocked_found.append(term)

    # Check for warning terms
    warnings = []
    for term in WARNING_TERMS:
        if re.search(rf'\b{re.escape(term)}\b', prompt_lower):
            # Only warn if not in woodworking context
            if category not in (SafetyCategory.WOODWORKING, SafetyCategory.CAM_ADVISOR):
                warnings.append(f"Term '{term}' may need review in this context")

    # Determine safety level
    if blocked_found:
        level = SafetyLevel.RED
        is_allowed = False
    elif category in REQUIRES_REVIEW or warnings:
        level = SafetyLevel.YELLOW
        is_allowed = True  # Allowed but flagged
    else:
        level = SafetyLevel.GREEN
        is_allowed = True

    return SafetyCheckResult(
        level=level,
        category=category,
        blocked_terms_found=blocked_found,
        warnings=warnings,
        is_allowed=is_allowed,
    )
