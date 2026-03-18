from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Tuple

from body_isolation_result import BodyIsolationResult
from body_isolation_stage import BodyIsolationParams
from contour_stage import StageParams
from geometry_coach import CoachDecision  # reuse V1 type if needed


CRITICAL_EXPORT_THRESHOLD = 0.30


@dataclass
class CoachV2Config:
    max_retries: int = 2
    epsilon: float = 0.03  # minimum score improvement to accept rerun

    # Trigger thresholds
    body_isolation_review_threshold: float = 0.45
    contour_target_threshold: float = 0.80
    severe_border_penalty_threshold: float = 0.5
    ownership_retry_threshold: float = 0.60

    # Retry profiles for body isolation
    body_retry_profiles: List[BodyIsolationParams] = field(
        default_factory=lambda: [
            BodyIsolationParams(profile="lower_bout_recovery"),
            BodyIsolationParams(profile="border_suppression"),
            BodyIsolationParams(profile="body_region_expansion"),
        ]
    )

    # Existing contour-stage retry profiles
    contour_retry_profiles: List[StageParams] = field(default_factory=list)


@dataclass
class CoachDecisionV2:
    action: str  # accept|rerun_body_isolation|rerun_contour_stage|manual_review_required
    reason: str
    notes: List[str] = field(default_factory=list)
    retry_count: int = 0

    body_retry_params: Optional[BodyIsolationParams] = None
    contour_retry_params: Optional[StageParams] = None

    original_body_score: Optional[float] = None
    original_contour_score: Optional[float] = None
    candidate_body_score: Optional[float] = None
    candidate_contour_score: Optional[float] = None


class GeometryCoachV2:
    """
    Coach V2 widens scope from contour-only retries to body-ownership retries.

    Primary responsibilities:
      1. Inspect BodyIsolationResult
      2. Inspect ContourStageResult
      3. Choose the *next safest rerun target*
      4. Enforce guardrails:
         - max retries
         - monotonic improvement
         - no silent downgrade
         - terminal manual review state
    """

    def __init__(self, config: Optional[CoachV2Config] = None):
        self.config = config or CoachV2Config()

    def should_retry(
        self,
        *,
        body_result: BodyIsolationResult,
        contour_result: Any,
        retry_count: int = 0,
    ) -> bool:
        if retry_count >= self.config.max_retries:
            return False

        body_score = float(getattr(body_result, "completeness_score", 0.0))
        contour_score = float(getattr(contour_result, "best_score", 0.0))

        # Ownership gate — low ownership always warrants a retry attempt
        ownership_score = self._ownership_score(contour_result)
        if ownership_score is not None and ownership_score < self.config.ownership_retry_threshold:
            return True

        if contour_score < self.config.contour_target_threshold:
            return True

        if body_score < self.config.body_isolation_review_threshold:
            return True

        return False

    def decide(
        self,
        *,
        body_result: BodyIsolationResult,
        contour_result: Any,
        retry_count: int = 0,
    ) -> CoachDecisionV2:
        """
        Decide the next action without performing it.

        Priority:
          1. If body ownership is suspect, rerun body isolation first
          2. Else if contour score is weak and merge behavior is suspicious, rerun contour stage
          3. Else accept
          4. If retry budget exhausted and still weak -> manual review
        """
        body_score = float(getattr(body_result, "completeness_score", 0.0))
        contour_score = float(getattr(contour_result, "best_score", 0.0))

        # Rule 0: body ownership gate — fires before retry budget check so
        # the first ownership failure always gets a retry attempt.
        ownership_score = self._ownership_score(contour_result)
        if ownership_score is not None and ownership_score < self.config.ownership_retry_threshold:
            if retry_count < self.config.max_retries:
                params = self._choose_body_retry_profile(
                    retry_count,
                    preferred_profile="body_region_expansion",
                )
                if params is not None:
                    return CoachDecisionV2(
                        action="rerun_body_isolation",
                        reason=(
                            f"Contour failed body ownership gate "
                            f"({ownership_score:.3f} < {self.config.ownership_retry_threshold:.3f})."
                        ),
                        retry_count=retry_count,
                        body_retry_params=params,
                        original_body_score=body_score,
                        original_contour_score=contour_score,
                        notes=[
                            "Ownership failure suggests body region is incomplete or neck-heavy.",
                            "Forcing body isolation retry before contour-only retry.",
                        ],
                    )
            return CoachDecisionV2(
                action="manual_review_required",
                reason=(
                    f"Contour failed body ownership gate "
                    f"({ownership_score:.3f}) and no safe body retry remains."
                ),
                retry_count=retry_count,
                original_body_score=body_score,
                original_contour_score=contour_score,
                notes=["manual_review_required due to persistent body ownership failure"],
            )

        if retry_count >= self.config.max_retries:
            return CoachDecisionV2(
                action="manual_review_required",
                reason="Maximum retry budget exhausted.",
                retry_count=retry_count,
                original_body_score=body_score,
                original_contour_score=contour_score,
                notes=["Retries exhausted before reaching acceptable contour/body scores."],
            )

        # Rule A: lower bout likely missing -> body isolation first
        if body_result.lower_bout_missing_likely and body_score < self.config.body_isolation_review_threshold:
            params = self._choose_body_retry_profile(retry_count)
            return CoachDecisionV2(
                action="rerun_body_isolation",
                reason="Body isolation likely under-captured lower bout.",
                retry_count=retry_count,
                body_retry_params=params,
                original_body_score=body_score,
                original_contour_score=contour_score,
                notes=["Rule A fired: lower-bout recovery attempt."],
            )

        # Rule B: border contamination likely -> body isolation first
        if body_result.border_contact_likely and body_result.score_breakdown.border_contact_penalty >= self.config.severe_border_penalty_threshold:
            params = self._choose_body_retry_profile(retry_count)
            return CoachDecisionV2(
                action="rerun_body_isolation",
                reason="Body isolation likely contaminated by border/crop contact.",
                retry_count=retry_count,
                body_retry_params=params,
                original_body_score=body_score,
                original_contour_score=contour_score,
                notes=["Rule B fired: border-contact suppression attempt."],
            )

        # Rule C: contour-stage disagreement/merge suspicion -> contour retry
        if self._contour_retry_worthwhile(contour_result):
            params = self._choose_contour_retry_profile(retry_count)
            return CoachDecisionV2(
                action="rerun_contour_stage",
                reason="Contour plausibility is weak and alternate merge profile may improve election.",
                retry_count=retry_count,
                contour_retry_params=params,
                original_body_score=body_score,
                original_contour_score=contour_score,
                notes=["Rule C fired: contour retry based on pre/post disagreement or merge tradeoff."],
            )

        # Rule D: poor scores but no useful retry path
        if contour_score < CRITICAL_EXPORT_THRESHOLD or body_score < self.config.body_isolation_review_threshold:
            return CoachDecisionV2(
                action="manual_review_required",
                reason="Scores remain too low for safe autonomous correction.",
                retry_count=retry_count,
                original_body_score=body_score,
                original_contour_score=contour_score,
                notes=["No safe retry path selected."],
            )

        return CoachDecisionV2(
            action="accept",
            reason="Current body isolation and contour election are acceptable.",
            retry_count=retry_count,
            original_body_score=body_score,
            original_contour_score=contour_score,
        )

    def accept_candidate(
        self,
        *,
        original_body_result: BodyIsolationResult,
        original_contour_result: Any,
        candidate_body_result: Optional[BodyIsolationResult] = None,
        candidate_contour_result: Optional[Any] = None,
    ) -> bool:
        """
        Comparative acceptance gate.

        Accept a retry result only if:
          - contour score improved by epsilon OR
          - body score improved by epsilon without contour score degrading materially
        """
        old_body = float(getattr(original_body_result, "completeness_score", 0.0))
        old_contour = float(getattr(original_contour_result, "best_score", 0.0))

        new_body = float(getattr(candidate_body_result, "completeness_score", old_body))
        new_contour = float(getattr(candidate_contour_result, "best_score", old_contour))

        contour_improved = new_contour > (old_contour + self.config.epsilon)
        body_improved = new_body > (old_body + self.config.epsilon)

        # Prefer contour improvement; allow body improvement only if contour does not regress
        if contour_improved:
            return True

        if body_improved and new_contour >= old_contour:
            return True

        return False

    def evaluate(
        self,
        *,
        body_stage_runner: Any,
        contour_stage_runner: Any,
        image: Any,
        fg_mask: Any,
        original_image: Any,
        instrument_family: Any,
        geometry_authority: Any,
        contour_inputs: Dict[str, Any],
        body_result: BodyIsolationResult,
        contour_result: Any,
    ) -> Tuple[BodyIsolationResult, Any, CoachDecisionV2]:
        """
        Execute a guarded V2 retry loop.

        Expects:
          body_stage_runner.run(...)
          contour_stage_runner.run(...)

        Returns:
          (
            current_body_result,
            current_contour_result,
            coach_decision
          )

        The returned body/contour results are the accepted best-known results
        after any safe retries have been evaluated.
        """
        current_body = body_result
        current_contour = contour_result

        def _ensure_diag(obj: Any) -> Dict[str, Any]:
            diag = getattr(obj, "diagnostics", None)
            if diag is None:
                diag = {}
                setattr(obj, "diagnostics", diag)
            return diag

        def _profile_name(profile: Any) -> Optional[str]:
            if profile is None:
                return None
            name = getattr(profile, "profile", None)
            if name:
                return str(name)
            return getattr(profile, "__class__", type(profile)).__name__

        def _annotate_retry_attempt(
            contour_obj: Any,
            *,
            retry_reason: str,
            retry_profile_used: Optional[str],
            retry_iteration: int,
            score_before: Optional[float],
            score_after: Optional[float],
            ownership_before: Optional[float] = None,
            ownership_after: Optional[float] = None,
        ) -> None:
            diag = _ensure_diag(contour_obj)
            attempts = diag.setdefault("retry_attempts", [])
            delta = None
            if score_before is not None and score_after is not None:
                try:
                    delta = float(score_after) - float(score_before)
                except (TypeError, ValueError):
                    delta = None
            entry: Dict[str, Any] = {
                "retry_reason": retry_reason,
                "retry_profile_used": retry_profile_used,
                "retry_iteration": retry_iteration,
                "score_before": score_before,
                "score_after": score_after,
                "score_delta": delta,
            }
            if ownership_before is not None or ownership_after is not None:
                entry["ownership_before"] = ownership_before
                entry["ownership_after"] = ownership_after
            attempts.append(entry)

        for retry_count in range(self.config.max_retries + 1):
            decision = self.decide(
                body_result=current_body,
                contour_result=current_contour,
                retry_count=retry_count,
            )

            if decision.action in ("accept", "manual_review_required"):
                return current_body, current_contour, decision

            if decision.action == "rerun_body_isolation":
                candidate_body = body_stage_runner.run(
                    image,
                    fg_mask=fg_mask,
                    original_image=original_image,
                    instrument_family=instrument_family,
                    geometry_authority=geometry_authority,
                    params=decision.body_retry_params,
                )

                candidate_contour = contour_stage_runner.run(
                    edges=contour_inputs["edges"],
                    alpha_mask=contour_inputs["alpha_mask"],
                    body_region=candidate_body.body_region,
                    calibration=contour_inputs["calibration"],
                    family=contour_inputs["family"],
                    image_shape=contour_inputs["image_shape"],
                )

                if self.accept_candidate(
                    original_body_result=current_body,
                    original_contour_result=current_contour,
                    candidate_body_result=candidate_body,
                    candidate_contour_result=candidate_contour,
                ):
                    _annotate_retry_attempt(
                        candidate_contour,
                        retry_reason=decision.reason,
                        retry_profile_used=_profile_name(decision.body_retry_params),
                        retry_iteration=retry_count + 1,
                        score_before=getattr(current_contour, "best_score", None),
                        score_after=getattr(candidate_contour, "best_score", None),
                        ownership_before=getattr(current_contour, "ownership_score", None),
                        ownership_after=getattr(candidate_contour, "ownership_score", None),
                    )

                    decision = replace(
                        decision,
                        candidate_body_score=candidate_body.completeness_score,
                        candidate_contour_score=getattr(candidate_contour, "best_score", None),
                    )
                    current_body = candidate_body
                    current_contour = candidate_contour
                    continue

                decision.notes.append(
                    "Body-isolation retry rejected by monotonic improvement gate."
                )
                _annotate_retry_attempt(
                    current_contour,
                    retry_reason=decision.reason,
                    retry_profile_used=_profile_name(decision.body_retry_params),
                    retry_iteration=retry_count + 1,
                    score_before=getattr(current_contour, "best_score", None),
                    score_after=getattr(candidate_contour, "best_score", None),
                    ownership_before=getattr(current_contour, "ownership_score", None),
                    ownership_after=getattr(candidate_contour, "ownership_score", None),
                )
                return current_body, current_contour, decision

            if decision.action == "rerun_contour_stage":
                candidate_contour = contour_stage_runner.run(
                    edges=contour_inputs["edges"],
                    alpha_mask=contour_inputs["alpha_mask"],
                    body_region=current_body.body_region,
                    calibration=contour_inputs["calibration"],
                    family=contour_inputs["family"],
                    image_shape=contour_inputs["image_shape"],
                    params=decision.contour_retry_params,
                )

                if self.accept_candidate(
                    original_body_result=current_body,
                    original_contour_result=current_contour,
                    candidate_body_result=current_body,
                    candidate_contour_result=candidate_contour,
                ):
                    _annotate_retry_attempt(
                        candidate_contour,
                        retry_reason=decision.reason,
                        retry_profile_used=_profile_name(decision.contour_retry_params),
                        retry_iteration=retry_count + 1,
                        score_before=getattr(current_contour, "best_score", None),
                        score_after=getattr(candidate_contour, "best_score", None),
                        ownership_before=getattr(current_contour, "ownership_score", None),
                        ownership_after=getattr(candidate_contour, "ownership_score", None),
                    )

                    decision = replace(
                        decision,
                        candidate_body_score=current_body.completeness_score,
                        candidate_contour_score=getattr(candidate_contour, "best_score", None),
                    )
                    current_contour = candidate_contour
                    continue

                decision.notes.append(
                    "Contour-stage retry rejected by monotonic improvement gate."
                )
                _annotate_retry_attempt(
                    current_contour,
                    retry_reason=decision.reason,
                    retry_profile_used=_profile_name(decision.contour_retry_params),
                    retry_iteration=retry_count + 1,
                    score_before=getattr(current_contour, "best_score", None),
                    score_after=getattr(candidate_contour, "best_score", None),
                    ownership_before=getattr(current_contour, "ownership_score", None),
                    ownership_after=getattr(candidate_contour, "ownership_score", None),
                )
                return current_body, current_contour, decision

        fallback = CoachDecisionV2(
            action="manual_review_required",
            reason="Retry loop exited unexpectedly without acceptable result.",
            retry_count=self.config.max_retries,
            original_body_score=current_body.completeness_score,
            original_contour_score=getattr(current_contour, "best_score", None),
        )
        return current_body, current_contour, fallback

    def _choose_body_retry_profile(
        self,
        retry_count: int,
        preferred_profile: Optional[str] = None,
    ) -> Optional[BodyIsolationParams]:
        if preferred_profile is not None:
            for profile in self.config.body_retry_profiles:
                if profile.profile == preferred_profile:
                    return profile
        idx = min(retry_count, len(self.config.body_retry_profiles) - 1)
        return self.config.body_retry_profiles[idx]

    def _choose_contour_retry_profile(self, retry_count: int) -> Optional[StageParams]:
        if not self.config.contour_retry_profiles:
            return None
        idx = min(retry_count, len(self.config.contour_retry_profiles) - 1)
        return self.config.contour_retry_profiles[idx]

    # Normal election paths — retries are not worthwhile when the
    # contour election completed through a stable baseline decision.
    # Only "pre_merge_guarded" (merge guard override) signals instability
    # that may benefit from a retry.
    _STABLE_ELECTION_SOURCES = frozenset({"pre_merge", "post_merge"})

    @staticmethod
    def _ownership_score(contour_result: Any) -> Optional[float]:
        if contour_result is None:
            return None
        if hasattr(contour_result, "ownership_score"):
            value = getattr(contour_result, "ownership_score")
            return None if value is None else float(value)
        diagnostics = getattr(contour_result, "diagnostics", {}) or {}
        value = diagnostics.get("ownership_score")
        return None if value is None else float(value)

    @staticmethod
    def _contour_retry_worthwhile(contour_result: Any) -> bool:
        """
        Detect whether Stage 8 disagreement suggests a contour-only retry may help.

        Additional guard:
        If the contour stage elected its result through a stable baseline
        election path (pre_merge or post_merge), retries are not worthwhile.
        The election logic already evaluated candidate contours and selected
        the best option.

        Only retry when instability signals exist (merge guard override,
        dimensional plausibility issues, etc.).

        Compatibility: tolerates older ContourStageResult stubs that may lack
        contour_scores_pre, contour_scores_post, or export_block_issues.
        Returns False if contour_result is None or best_score is missing.
        """
        if contour_result is None:
            return False

        elected_source = getattr(contour_result, "elected_source", None)
        if elected_source in GeometryCoachV2._STABLE_ELECTION_SOURCES:
            return False

        best_score_raw = getattr(contour_result, "best_score", None)
        if best_score_raw is None:
            return False

        try:
            best_score = float(best_score_raw)
        except (TypeError, ValueError):
            return False

        if best_score >= 0.80:
            return False

        # Fall back gracefully when score lists are missing or malformed
        pre_scores = getattr(contour_result, "contour_scores_pre", None) or []
        post_scores = getattr(contour_result, "contour_scores_post", None) or []

        try:
            pre_best = max((s.score for s in pre_scores), default=best_score)
        except (TypeError, AttributeError):
            pre_best = best_score

        try:
            post_best = max((s.score for s in post_scores), default=best_score)
        except (TypeError, AttributeError):
            post_best = best_score

        # Missing issues field must degrade safely
        issues = getattr(contour_result, "export_block_issues", None) or []

        disagreement = abs(pre_best - post_best) > 0.08
        merge_tradeoff = any(
            kw in issue for issue in issues
            for kw in ("neck included", "dimension plausibility")
        )

        return disagreement or merge_tradeoff
