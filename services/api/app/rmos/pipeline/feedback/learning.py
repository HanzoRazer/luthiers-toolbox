"""
RMOS Pipeline Learning Service

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 5

Service for learning events, decisions, and multiplier application.
Enables parameter optimization based on operator feedback.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    JobLogMetrics,
    QualitySignal,
    LearningMultipliers,
    LearningSuggestion,
    LearningEvent,
    LearningEventResponse,
    LearningDecisionPolicy,
    LearningDecision,
    LearningDecisionRequest,
    LearningDecisionResponse,
)
from .config import (
    is_apply_overrides_enabled,
    get_learned_overrides_path,
)
from ..store import write_artifact, read_artifact, query_artifacts
from ..schemas import PipelineStage, PipelineStatus, ArtifactQuery
from ...runs import create_run_id, sha256_of_obj


def _utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# Signal Detection
# =============================================================================

# Keywords that indicate quality signals in notes
_SIGNAL_KEYWORDS = {
    QualitySignal.BURN: ["burn", "scorch", "smoke", "char", "dark"],
    QualitySignal.TEAROUT: ["tearout", "tear", "chip", "splinter", "fuzzy"],
    QualitySignal.KICKBACK: ["kickback", "kick", "grab", "bind", "stall"],
    QualitySignal.CHATTER: ["chatter", "vibrat", "resonan", "harmonic"],
    QualitySignal.TOOL_WEAR: ["wear", "dull", "worn", "blunt"],
    QualitySignal.EXCELLENT: ["excellent", "perfect", "great", "smooth", "clean"],
}


def detect_signals(
    metrics: JobLogMetrics,
    notes: Optional[str] = None,
) -> List[QualitySignal]:
    """
    Detect quality signals from metrics and notes.

    Args:
        metrics: Job metrics
        notes: Operator notes

    Returns:
        List of detected signals
    """
    signals = []

    # Check metrics flags
    if metrics.burn:
        signals.append(QualitySignal.BURN)
    if metrics.tearout:
        signals.append(QualitySignal.TEAROUT)
    if metrics.kickback:
        signals.append(QualitySignal.KICKBACK)
    if metrics.chatter:
        signals.append(QualitySignal.CHATTER)
    if metrics.tool_wear:
        signals.append(QualitySignal.TOOL_WEAR)

    # Check notes for keywords
    if notes:
        notes_lower = notes.lower()
        for signal, keywords in _SIGNAL_KEYWORDS.items():
            if signal not in signals:
                if any(kw in notes_lower for kw in keywords):
                    signals.append(signal)

    return signals


# =============================================================================
# Suggestion Generation
# =============================================================================

# Default multiplier adjustments for each signal
_SIGNAL_SUGGESTIONS: Dict[QualitySignal, Tuple[float, float, float, float, str]] = {
    # (rpm_mult, feed_mult, doc_mult, woc_mult, rationale)
    QualitySignal.BURN: (1.1, 1.15, 1.0, 1.0, "Burn detected - increase feed to reduce heat buildup"),
    QualitySignal.TEAROUT: (1.0, 0.9, 0.85, 1.0, "Tearout detected - reduce feed and DOC"),
    QualitySignal.KICKBACK: (1.0, 0.8, 0.9, 0.9, "Kickback detected - reduce feed significantly"),
    QualitySignal.CHATTER: (0.95, 1.0, 0.9, 0.9, "Chatter detected - adjust RPM and reduce engagement"),
    QualitySignal.TOOL_WEAR: (1.0, 0.95, 0.95, 1.0, "Tool wear - reduce feed and DOC until tool change"),
    QualitySignal.EXCELLENT: (1.0, 1.0, 1.0, 1.0, "Excellent finish - current parameters are optimal"),
}


def generate_suggestions(signals: List[QualitySignal]) -> List[LearningSuggestion]:
    """
    Generate learning suggestions based on detected signals.

    Args:
        signals: List of detected quality signals

    Returns:
        List of learning suggestions
    """
    suggestions = []

    for signal in signals:
        if signal in _SIGNAL_SUGGESTIONS:
            rpm_m, feed_m, doc_m, woc_m, rationale = _SIGNAL_SUGGESTIONS[signal]
            suggestions.append(LearningSuggestion(
                signal=signal,
                confidence=0.7 if signal != QualitySignal.EXCELLENT else 0.9,
                multipliers=LearningMultipliers(
                    spindle_rpm_mult=rpm_m,
                    feed_rate_mult=feed_m,
                    doc_mult=doc_m,
                    woc_mult=woc_m,
                ),
                rationale=rationale,
            ))

    return suggestions


def aggregate_multipliers(suggestions: List[LearningSuggestion]) -> LearningMultipliers:
    """
    Aggregate multipliers from multiple suggestions.

    Uses weighted average based on confidence.

    Args:
        suggestions: List of suggestions

    Returns:
        Aggregated multipliers
    """
    if not suggestions:
        return LearningMultipliers()

    total_conf = sum(s.confidence for s in suggestions)
    if total_conf == 0:
        return LearningMultipliers()

    rpm = sum(s.multipliers.spindle_rpm_mult * s.confidence for s in suggestions) / total_conf
    feed = sum(s.multipliers.feed_rate_mult * s.confidence for s in suggestions) / total_conf
    doc = sum(s.multipliers.doc_mult * s.confidence for s in suggestions) / total_conf
    woc = sum(s.multipliers.woc_mult * s.confidence for s in suggestions) / total_conf

    return LearningMultipliers(
        spindle_rpm_mult=round(rpm, 3),
        feed_rate_mult=round(feed, 3),
        doc_mult=round(doc, 3),
        woc_mult=round(woc, 3),
    )


# =============================================================================
# Learning Service
# =============================================================================

class LearningService:
    """
    Service for managing learning events and decisions.
    """

    def __init__(self, tool_type: str):
        self.tool_type = tool_type

    def _kind(self, suffix: str) -> str:
        return f"{self.tool_type}_{suffix}"

    def emit_event(
        self,
        job_log_artifact_id: str,
        execution_artifact_id: str,
        metrics: JobLogMetrics,
        notes: Optional[str] = None,
        *,
        tool_id: Optional[str] = None,
        material_id: Optional[str] = None,
        operation_type: Optional[str] = None,
    ) -> LearningEventResponse:
        """
        Emit a learning event from job log analysis.

        Args:
            job_log_artifact_id: Source job log
            execution_artifact_id: Related execution
            metrics: Job metrics
            notes: Operator notes
            tool_id: Tool identifier
            material_id: Material identifier
            operation_type: Operation type

        Returns:
            LearningEventResponse with artifact ID
        """
        # Detect signals
        signals = detect_signals(metrics, notes)

        # Generate suggestions
        suggestions = generate_suggestions(signals)

        # Aggregate multipliers
        aggregate = aggregate_multipliers(suggestions)

        # Read execution for context
        execution = read_artifact(execution_artifact_id)
        execution_meta = execution.get("index_meta", {}) if execution else {}
        batch_label = execution_meta.get("batch_label")

        payload = {
            "created_utc": _utc_now_iso(),
            "job_log_artifact_id": job_log_artifact_id,
            "execution_artifact_id": execution_artifact_id,
            "tool_id": tool_id,
            "material_id": material_id,
            "operation_type": operation_type,
            "signals": [s.value for s in signals],
            "suggestions": [s.model_dump() for s in suggestions],
            "aggregate_multipliers": aggregate.model_dump(),
            "tool_type": self.tool_type,
            "batch_label": batch_label,
        }

        index_meta = {
            "tool_type": self.tool_type,
            "tool_kind": self.tool_type,
            "kind_group": "learning",
            "parent_job_log_artifact_id": job_log_artifact_id,
            "parent_execution_artifact_id": execution_artifact_id,
            "batch_label": batch_label,
            "signal_burn": QualitySignal.BURN in signals,
            "signal_tearout": QualitySignal.TEAROUT in signals,
            "signal_kickback": QualitySignal.KICKBACK in signals,
        }

        artifact_id = write_artifact(
            kind=self._kind("learning_event"),
            stage=PipelineStage.EXECUTE,
            status=PipelineStatus.OK,
            index_meta=index_meta,
            payload=payload,
        )

        return LearningEventResponse(
            learning_event_artifact_id=artifact_id,
            job_log_artifact_id=job_log_artifact_id,
            signals_detected=[s.value for s in signals],
            suggestions_count=len(suggestions),
        )

    def create_decision(
        self,
        learning_event_artifact_id: str,
        policy: LearningDecisionPolicy,
        decided_by: str,
        *,
        reason: Optional[str] = None,
        multipliers: Optional[LearningMultipliers] = None,
    ) -> LearningDecisionResponse:
        """
        Create a learning decision.

        Args:
            learning_event_artifact_id: Learning event to decide on
            policy: PROPOSE, ACCEPT, or REJECT
            decided_by: Who made the decision
            reason: Decision rationale
            multipliers: Override multipliers (optional)

        Returns:
            LearningDecisionResponse with artifact ID
        """
        # Read learning event
        event = read_artifact(learning_event_artifact_id)
        event_payload = event.get("payload", {}) if event else {}

        # Get multipliers (use provided or event's aggregate)
        accepted_multipliers = None
        if policy == LearningDecisionPolicy.ACCEPT:
            if multipliers:
                accepted_multipliers = multipliers
            else:
                agg = event_payload.get("aggregate_multipliers", {})
                accepted_multipliers = LearningMultipliers(**agg)

        payload = {
            "created_utc": _utc_now_iso(),
            "learning_event_artifact_id": learning_event_artifact_id,
            "policy": policy.value,
            "decided_by": decided_by,
            "reason": reason,
            "accepted_multipliers": accepted_multipliers.model_dump() if accepted_multipliers else None,
        }

        index_meta = {
            "tool_type": self.tool_type,
            "tool_kind": self.tool_type,
            "kind_group": "learning",
            "parent_learning_event_artifact_id": learning_event_artifact_id,
            "policy": policy.value,
            "decided_by": decided_by,
        }

        artifact_id = write_artifact(
            kind=self._kind("learning_decision"),
            stage=PipelineStage.EXECUTE,
            status=PipelineStatus.OK,
            index_meta=index_meta,
            payload=payload,
        )

        # Persist to learned overrides file if accepted
        if policy == LearningDecisionPolicy.ACCEPT and accepted_multipliers:
            self._persist_override(
                learning_event_artifact_id,
                artifact_id,
                event_payload,
                accepted_multipliers,
            )

        return LearningDecisionResponse(
            learning_decision_artifact_id=artifact_id,
            learning_event_artifact_id=learning_event_artifact_id,
            policy=policy.value,
            will_be_applied=policy == LearningDecisionPolicy.ACCEPT,
        )

    def _persist_override(
        self,
        event_id: str,
        decision_id: str,
        event_payload: Dict[str, Any],
        multipliers: LearningMultipliers,
    ) -> None:
        """Persist accepted override to JSONL file."""
        path = get_learned_overrides_path(self.tool_type)
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": _utc_now_iso(),
            "learning_event_artifact_id": event_id,
            "learning_decision_artifact_id": decision_id,
            "tool_id": event_payload.get("tool_id"),
            "material_id": event_payload.get("material_id"),
            "operation_type": event_payload.get("operation_type"),
            "multipliers": multipliers.model_dump(),
        }

        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def resolve_multipliers(
        self,
        tool_id: Optional[str] = None,
        material_id: Optional[str] = None,
        operation_type: Optional[str] = None,
    ) -> Tuple[LearningMultipliers, Dict[str, Any]]:
        """
        Resolve learned multipliers for a context.

        Args:
            tool_id: Tool identifier
            material_id: Material identifier
            operation_type: Operation type

        Returns:
            Tuple of (multipliers, provenance)
        """
        path = get_learned_overrides_path(self.tool_type)

        if not os.path.exists(path):
            return LearningMultipliers(), {"source_count": 0, "sources": []}

        # Load all accepted overrides
        overrides = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        overrides.append(record)
                    except json.JSONDecodeError:
                        continue

        # Filter by context
        matches = []
        for o in overrides:
            # Match if no filter or filter matches
            if tool_id and o.get("tool_id") and o["tool_id"] != tool_id:
                continue
            if material_id and o.get("material_id") and o["material_id"] != material_id:
                continue
            if operation_type and o.get("operation_type") and o["operation_type"] != operation_type:
                continue
            matches.append(o)

        if not matches:
            return LearningMultipliers(), {"source_count": 0, "sources": []}

        # Average the multipliers
        rpm_sum = sum(m["multipliers"].get("spindle_rpm_mult", 1.0) for m in matches)
        feed_sum = sum(m["multipliers"].get("feed_rate_mult", 1.0) for m in matches)
        doc_sum = sum(m["multipliers"].get("doc_mult", 1.0) for m in matches)
        woc_sum = sum(m["multipliers"].get("woc_mult", 1.0) for m in matches)
        n = len(matches)

        multipliers = LearningMultipliers(
            spindle_rpm_mult=round(rpm_sum / n, 3),
            feed_rate_mult=round(feed_sum / n, 3),
            doc_mult=round(doc_sum / n, 3),
            woc_mult=round(woc_sum / n, 3),
        )

        provenance = {
            "source_count": n,
            "sources": [m["learning_decision_artifact_id"] for m in matches[:10]],
        }

        return multipliers, provenance

    def apply_to_context(
        self,
        context: Dict[str, Any],
        multipliers: LearningMultipliers,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Apply multipliers to a machining context.

        Args:
            context: Original context
            multipliers: Multipliers to apply

        Returns:
            Tuple of (modified_context, tuning_stamp)
        """
        modified = context.copy()
        tuning_stamp = {
            "applied": True,
            "before": {},
            "after": {},
            "multipliers": multipliers.model_dump(),
        }

        # Apply spindle RPM
        if "spindle_rpm" in modified:
            before = modified["spindle_rpm"]
            modified["spindle_rpm"] = round(before * multipliers.spindle_rpm_mult)
            tuning_stamp["before"]["spindle_rpm"] = before
            tuning_stamp["after"]["spindle_rpm"] = modified["spindle_rpm"]

        # Apply feed rate
        for key in ["feed_rate", "feed_rate_mm_min", "feed_mm_min"]:
            if key in modified:
                before = modified[key]
                modified[key] = round(before * multipliers.feed_rate_mult, 1)
                tuning_stamp["before"][key] = before
                tuning_stamp["after"][key] = modified[key]
                break

        # Apply depth of cut
        for key in ["doc_mm", "depth_of_cut", "stepdown"]:
            if key in modified:
                before = modified[key]
                modified[key] = round(before * multipliers.doc_mult, 2)
                tuning_stamp["before"][key] = before
                tuning_stamp["after"][key] = modified[key]
                break

        return modified, tuning_stamp


# =============================================================================
# Convenience Functions
# =============================================================================

def emit_learning_event(
    tool_type: str,
    job_log_artifact_id: str,
    execution_artifact_id: str,
    metrics: JobLogMetrics,
    notes: Optional[str] = None,
    **kwargs: Any,
) -> LearningEventResponse:
    """Emit a learning event."""
    service = LearningService(tool_type)
    return service.emit_event(
        job_log_artifact_id,
        execution_artifact_id,
        metrics,
        notes,
        **kwargs,
    )


def create_learning_decision(
    tool_type: str,
    learning_event_artifact_id: str,
    policy: LearningDecisionPolicy,
    decided_by: str,
    **kwargs: Any,
) -> LearningDecisionResponse:
    """Create a learning decision."""
    service = LearningService(tool_type)
    return service.create_decision(
        learning_event_artifact_id,
        policy,
        decided_by,
        **kwargs,
    )


def resolve_learned_multipliers(
    tool_type: str,
    **kwargs: Any,
) -> Tuple[LearningMultipliers, Dict[str, Any]]:
    """Resolve learned multipliers for a context."""
    service = LearningService(tool_type)
    return service.resolve_multipliers(**kwargs)


def apply_multipliers_to_context(
    tool_type: str,
    context: Dict[str, Any],
    multipliers: Optional[LearningMultipliers] = None,
    **kwargs: Any,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Apply learned multipliers to a context.

    If multipliers not provided, resolves from learned overrides.
    Returns (modified_context, tuning_stamp).
    """
    service = LearningService(tool_type)

    if multipliers is None:
        multipliers, _ = service.resolve_multipliers(**kwargs)

    if not is_apply_overrides_enabled(tool_type):
        return context, {"applied": False, "reason": "disabled"}

    return service.apply_to_context(context, multipliers)
