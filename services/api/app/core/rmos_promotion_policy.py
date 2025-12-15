"""
RMOS Promotion Policy Engine (MM-5)

Ultra-fragility guard that blocks unsafe lane promotions based on:
- Material fragility scores (from MM-2)
- Job history cleanliness (risk grades)
- Configurable thresholds per lane

Prevents promoting brittle material combinations (shell, metal, charred wood)
to production lanes until they pass sufficient validation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

from app.api.deps.rmos_stores import get_joblog_store
from app.schemas.rmos_analytics import Lane, RiskGrade


POLICY_PATH = Path(os.getcwd()) / "data" / "rmos" / "promotion_policy.json"


@dataclass
class PromotionPolicyConfig:
    """Promotion policy configuration with lane-specific thresholds."""
    fragility_to_safe_max: float = 0.60
    min_clean_runs_for_safe: int = 5
    min_clean_runs_for_tuned_v1: int = 3
    min_clean_runs_for_tuned_v2: int = 4

    grade_ok_for_clean: Tuple[RiskGrade, ...] = ("GREEN",)
    allow_yellow_if_fragility_low: bool = True
    yellow_fragility_max: float = 0.30

    block_ultra_fragile_anywhere: bool = True
    ultra_fragile_threshold: float = 0.90

    lookback_jobs_per_preset: int = 200


def _load_policy_config() -> PromotionPolicyConfig:
    """Load promotion policy config from JSON or use defaults."""
    if not POLICY_PATH.exists():
        return PromotionPolicyConfig()
    
    try:
        with POLICY_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        return PromotionPolicyConfig(
            fragility_to_safe_max=float(raw.get("fragility_to_safe_max", 0.60)),
            min_clean_runs_for_safe=int(raw.get("min_clean_runs_for_safe", 5)),
            min_clean_runs_for_tuned_v1=int(raw.get("min_clean_runs_for_tuned_v1", 3)),
            min_clean_runs_for_tuned_v2=int(raw.get("min_clean_runs_for_tuned_v2", 4)),
            grade_ok_for_clean=tuple(raw.get("grade_ok_for_clean", ["GREEN"])),  # type: ignore[arg-type]
            allow_yellow_if_fragility_low=bool(raw.get("allow_yellow_if_fragility_low", True)),
            yellow_fragility_max=float(raw.get("yellow_fragility_max", 0.30)),
            block_ultra_fragile_anywhere=bool(raw.get("block_ultra_fragile_anywhere", True)),
            ultra_fragile_threshold=float(raw.get("ultra_fragile_threshold", 0.90)),
            lookback_jobs_per_preset=int(raw.get("lookback_jobs_per_preset", 200)),
        )
    except Exception as e:
        print(f"Warning: Failed to load promotion policy config: {e}. Using defaults.")
        return PromotionPolicyConfig()


def _normalize_grade(value: Any) -> RiskGrade:
    """Normalize risk grade to valid enum value."""
    if not value:
        return "unknown"  # type: ignore[return-value]
    v = str(value).upper()
    if v not in ("GREEN", "YELLOW", "RED"):
        return "unknown"  # type: ignore[return-value]
    return v  # type: ignore[return-value]


def _is_clean_job(entry: Dict[str, Any], cfg: PromotionPolicyConfig) -> Tuple[bool, float]:
    """
    Decide if a single job is 'clean enough' to count toward promotion.
    
    Returns:
        (is_clean, worst_fragility)
    
    Rules:
    - Ultra-fragile jobs (≥0.90) are NEVER clean
    - GREEN jobs are always clean
    - YELLOW jobs are clean only if fragility ≤0.30 (configurable)
    - RED jobs are never clean
    """
    grade = _normalize_grade(entry.get("risk_grade"))
    meta = entry.get("metadata") or {}
    cam_summary = meta.get("cam_profile_summary") or {}
    worst_fragility = cam_summary.get("worst_fragility_score")
    
    if not isinstance(worst_fragility, (int, float)):
        worst_fragility = 0.0

    # Ultra-fragile jobs are *never* considered clean
    if cfg.block_ultra_fragile_anywhere and worst_fragility >= cfg.ultra_fragile_threshold:
        return False, worst_fragility

    # Grade-based decision
    if grade in cfg.grade_ok_for_clean:
        return True, worst_fragility

    if grade == "YELLOW":
        if cfg.allow_yellow_if_fragility_low and worst_fragility <= cfg.yellow_fragility_max:
            return True, worst_fragility

    return False, worst_fragility


def _collect_preset_history(preset_id: str, cfg: PromotionPolicyConfig) -> Dict[str, Any]:
    """
    Pull recent jobs for this preset and compute statistics.
    
    Returns:
        {
            "total_runs": int,
            "clean_runs": int,
            "worst_fragility_overall": float,
            "worst_fragility_clean": float
        }
    """
    joblog_store = get_joblog_store()
    entries = [
        e for e in joblog_store.list(limit=cfg.lookback_jobs_per_preset) 
        if e.get("preset_id") == preset_id
    ]

    total_runs = len(entries)
    clean_runs = 0
    worst_fragility_overall = 0.0
    worst_fragility_clean = 0.0

    for entry in entries:
        is_clean, frag = _is_clean_job(entry, cfg)
        if frag > worst_fragility_overall:
            worst_fragility_overall = frag
        if is_clean:
            clean_runs += 1
            if frag > worst_fragility_clean:
                worst_fragility_clean = frag

    return {
        "total_runs": total_runs,
        "clean_runs": clean_runs,
        "worst_fragility_overall": worst_fragility_overall,
        "worst_fragility_clean": worst_fragility_clean,
    }


def evaluate_promotion_policy(
    preset_id: str,
    target_lane: Lane,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Core policy decision for lane promotion.
    
    Args:
        preset_id: Preset to evaluate
        target_lane: Target lane (safe, tuned_v1, tuned_v2, experimental, archived)
    
    Returns:
        (allowed, reason, stats)
        - allowed: bool - Whether promotion is allowed
        - reason: str - Human-readable explanation (shown to user)
        - stats: dict - Job history stats for UI/logging
    
    Policy Rules:
    1. Ultra-fragile block (≥0.90): Blocks promotion to ANY lane
    2. Safe lane fragility limit (≤0.60): Prevents brittle materials in production
    3. Min clean runs per lane: Requires validation before promotion
       - safe: 5 clean jobs
       - tuned_v1: 3 clean jobs
       - tuned_v2: 4 clean jobs
    
    Examples:
        # Shell+copper rosette (fragility 0.94) blocked everywhere
        allowed, reason, stats = evaluate_promotion_policy("preset_123", "safe")
        # allowed=False, reason="Blocked: worst fragility 0.94 exceeds ultra-fragile threshold 0.90..."
        
        # Wood rosette (fragility 0.32) with 2 clean jobs blocked from safe
        allowed, reason, stats = evaluate_promotion_policy("preset_456", "safe")
        # allowed=False, reason="Blocked: only 2 clean jobs found; 5 required for 'safe'."
        
        # Wood rosette with 6 clean jobs (fragility 0.28) allowed to safe
        allowed, reason, stats = evaluate_promotion_policy("preset_789", "safe")
        # allowed=True, reason="Allowed: 6/8 jobs are clean; worst fragility 0.28 within policy limits..."
    """
    cfg = _load_policy_config()
    history = _collect_preset_history(preset_id, cfg)

    total_runs = history["total_runs"]
    clean_runs = history["clean_runs"]
    worst_fragility = history["worst_fragility_overall"]

    # Ultra-fragile global block
    if cfg.block_ultra_fragile_anywhere and worst_fragility >= cfg.ultra_fragile_threshold:
        return (
            False,
            f"Blocked: worst fragility {worst_fragility:.2f} exceeds ultra-fragile threshold "
            f"{cfg.ultra_fragile_threshold:.2f}. Review materials/CAM before promotion.",
            history,
        )

    # Lane-specific requirements
    if target_lane == "safe":
        if worst_fragility > cfg.fragility_to_safe_max:
            return (
                False,
                f"Blocked: worst fragility {worst_fragility:.2f} exceeds allowed maximum "
                f"{cfg.fragility_to_safe_max:.2f} for 'safe' lane.",
                history,
            )
        if clean_runs < cfg.min_clean_runs_for_safe:
            return (
                False,
                f"Blocked: only {clean_runs} clean jobs found for this preset; "
                f"{cfg.min_clean_runs_for_safe} required before promotion to 'safe'.",
                history,
            )

    elif target_lane == "tuned_v1":
        if clean_runs < cfg.min_clean_runs_for_tuned_v1:
            return (
                False,
                f"Blocked: only {clean_runs} clean jobs found; "
                f"{cfg.min_clean_runs_for_tuned_v1} required for 'tuned_v1'.",
                history,
            )

    elif target_lane == "tuned_v2":
        if clean_runs < cfg.min_clean_runs_for_tuned_v2:
            return (
                False,
                f"Blocked: only {clean_runs} clean jobs found; "
                f"{cfg.min_clean_runs_for_tuned_v2} required for 'tuned_v2'.",
                history,
            )

    # Default: allowed
    if total_runs == 0:
        reason = "Allowed: no job history found; policy did not find evidence to block promotion."
    else:
        reason = (
            f"Allowed: {clean_runs}/{total_runs} jobs are clean; "
            f"worst fragility {worst_fragility:.2f} within policy limits for lane '{target_lane}'."
        )

    return True, reason, history
