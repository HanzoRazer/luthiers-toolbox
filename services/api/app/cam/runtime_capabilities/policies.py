"""
Execution Policy Federation.

Sprint: MRP-5V
Status: PROTOTYPE

Policy evaluation for capability eligibility.

Design principles:
  - Policy determines eligibility, not semantics
  - Policy does NOT mutate requests
  - Policy does NOT redefine capability meaning
  - Decisions are deterministic given same input

MRP-5V scope:
  - enabled/disabled check
  - deterministic requirement
  - replay_safe requirement
  - existence check
  - compatibility_tags intersection
  - required_tags satisfaction

Future work (not MRP-5V):
  - Deep geometry compatibility
  - Dynamic policy rules
  - Adaptive policy
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Set

from .contracts import (
    CompatibilitySummary,
    FederatedCapability,
    PolicyDecision,
    ResolutionContext,
)


# -----------------------------------------------------------------------------
# Policy Result
# -----------------------------------------------------------------------------

@dataclass
class PolicyEvaluationResult:
    """Result of a single policy evaluation."""

    policy_name: str
    decision: PolicyDecision
    reason: Optional[str] = None

    @property
    def is_allowed(self) -> bool:
        return self.decision == PolicyDecision.ALLOWED

    @property
    def is_rejected(self) -> bool:
        return self.decision == PolicyDecision.REJECTED


# -----------------------------------------------------------------------------
# Policy Interface
# -----------------------------------------------------------------------------

class ExecutionPolicy(ABC):
    """
    Base class for execution policies.

    Each policy evaluates one aspect of capability eligibility.
    """

    @property
    @abstractmethod
    def policy_name(self) -> str:
        """Unique name for this policy."""
        ...

    @abstractmethod
    def evaluate(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> PolicyEvaluationResult:
        """
        Evaluate this policy for a capability.

        Args:
            capability: The capability to evaluate
            context: Resolution context

        Returns:
            PolicyEvaluationResult with decision
        """
        ...


# -----------------------------------------------------------------------------
# Built-in Policies
# -----------------------------------------------------------------------------

class EnabledPolicy(ExecutionPolicy):
    """Check that capability is enabled."""

    @property
    def policy_name(self) -> str:
        return "enabled"

    def evaluate(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> PolicyEvaluationResult:
        if capability.enabled:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
            )
        return PolicyEvaluationResult(
            policy_name=self.policy_name,
            decision=PolicyDecision.REJECTED,
            reason="Capability is disabled",
        )


class DeterministicPolicy(ExecutionPolicy):
    """Check deterministic requirement."""

    @property
    def policy_name(self) -> str:
        return "deterministic"

    def evaluate(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> PolicyEvaluationResult:
        if not context.require_deterministic:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
                reason="Deterministic not required",
            )

        if capability.deterministic:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
            )

        return PolicyEvaluationResult(
            policy_name=self.policy_name,
            decision=PolicyDecision.REJECTED,
            reason="Capability is not deterministic",
        )


class ReplaySafetyPolicy(ExecutionPolicy):
    """Check replay safety requirement."""

    @property
    def policy_name(self) -> str:
        return "replay_safety"

    def evaluate(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> PolicyEvaluationResult:
        if not context.require_replay_safe:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
                reason="Replay safety not required",
            )

        if capability.replay_safe:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
            )

        return PolicyEvaluationResult(
            policy_name=self.policy_name,
            decision=PolicyDecision.REJECTED,
            reason="Capability is not replay-safe",
        )


class CompatibilityTagsPolicy(ExecutionPolicy):
    """Check compatibility tags intersection."""

    @property
    def policy_name(self) -> str:
        return "compatibility_tags"

    def evaluate(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> PolicyEvaluationResult:
        if not context.required_compatibility_tags:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
                reason="No compatibility tags required",
            )

        # Check if capability has all required tags
        missing = context.required_compatibility_tags - capability.compatibility_tags

        if not missing:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
            )

        return PolicyEvaluationResult(
            policy_name=self.policy_name,
            decision=PolicyDecision.REJECTED,
            reason=f"Missing compatibility tags: {sorted(missing)}",
        )


class RequiredTagsPolicy(ExecutionPolicy):
    """Check that capability's required tags are satisfied."""

    @property
    def policy_name(self) -> str:
        return "required_tags"

    def evaluate(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> PolicyEvaluationResult:
        if not capability.required_tags:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
                reason="Capability has no required tags",
            )

        # Check if context provides all required tags
        provided = context.required_compatibility_tags
        missing = capability.required_tags - provided

        if not missing:
            return PolicyEvaluationResult(
                policy_name=self.policy_name,
                decision=PolicyDecision.ALLOWED,
            )

        return PolicyEvaluationResult(
            policy_name=self.policy_name,
            decision=PolicyDecision.REJECTED,
            reason=f"Capability requires tags not provided: {sorted(missing)}",
        )


# -----------------------------------------------------------------------------
# Policy Federation
# -----------------------------------------------------------------------------

@dataclass
class FederatedPolicyResult:
    """Result of federated policy evaluation."""

    overall_decision: PolicyDecision
    policy_results: List[PolicyEvaluationResult] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    compatibility_summary: CompatibilitySummary = field(
        default_factory=CompatibilitySummary
    )

    @property
    def is_allowed(self) -> bool:
        return self.overall_decision == PolicyDecision.ALLOWED

    @property
    def policies_evaluated(self) -> List[str]:
        return [r.policy_name for r in self.policy_results]


class ExecutionPolicyFederation:
    """
    Federation of execution policies.

    Evaluates multiple policies and aggregates results.
    All policies must pass for capability to be allowed.

    Policy federation does NOT:
      - Mutate the capability
      - Mutate the context
      - Redefine capability semantics
      - Repair metadata
    """

    def __init__(self, policies: Optional[List[ExecutionPolicy]] = None):
        if policies is None:
            # Default policy stack
            policies = [
                EnabledPolicy(),
                DeterministicPolicy(),
                ReplaySafetyPolicy(),
                CompatibilityTagsPolicy(),
                RequiredTagsPolicy(),
            ]
        self._policies = policies

    def evaluate(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> FederatedPolicyResult:
        """
        Evaluate all policies for a capability.

        Args:
            capability: The capability to evaluate
            context: Resolution context

        Returns:
            FederatedPolicyResult with aggregated decision
        """
        results: List[PolicyEvaluationResult] = []
        rejection_reasons: List[str] = []
        overall_decision = PolicyDecision.ALLOWED

        for policy in self._policies:
            result = policy.evaluate(capability, context)
            results.append(result)

            if result.is_rejected:
                overall_decision = PolicyDecision.REJECTED
                if result.reason:
                    rejection_reasons.append(f"{result.policy_name}: {result.reason}")

        # Build compatibility summary
        compatibility_summary = self._build_compatibility_summary(
            capability, context
        )

        return FederatedPolicyResult(
            overall_decision=overall_decision,
            policy_results=results,
            rejection_reasons=rejection_reasons,
            compatibility_summary=compatibility_summary,
        )

    def _build_compatibility_summary(
        self,
        capability: FederatedCapability,
        context: ResolutionContext,
    ) -> CompatibilitySummary:
        """Build compatibility summary from capability and context."""
        required = context.required_compatibility_tags
        provided = capability.compatibility_tags

        satisfied = required & provided
        missing = required - provided

        return CompatibilitySummary(
            compatible=len(missing) == 0,
            satisfied_tags=satisfied,
            missing_tags=missing,
        )

    def add_policy(self, policy: ExecutionPolicy) -> None:
        """Add a policy to the federation."""
        self._policies.append(policy)

    def list_policies(self) -> List[str]:
        """List policy names in evaluation order."""
        return [p.policy_name for p in self._policies]


# -----------------------------------------------------------------------------
# Global Federation
# -----------------------------------------------------------------------------

_global_federation: Optional[ExecutionPolicyFederation] = None


def get_policy_federation() -> ExecutionPolicyFederation:
    """Get the global policy federation."""
    global _global_federation
    if _global_federation is None:
        _global_federation = ExecutionPolicyFederation()
    return _global_federation


def reset_policy_federation() -> None:
    """Reset the global policy federation."""
    global _global_federation
    _global_federation = None
