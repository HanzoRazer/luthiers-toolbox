"""
Capability Resolver.

Sprint: MRP-5V
Status: PROTOTYPE

Resolves capability requests through registry and policy federation.

Design principles:
  - Resolver answers "may this capability be used?"
  - Resolver does NOT execute capabilities
  - Resolver returns metadata + decision
  - Resolution is deterministic
"""

from __future__ import annotations

from typing import Optional

from .contracts import (
    CapabilityResolutionResult,
    FederatedCapability,
    PolicyDecision,
    ResolutionContext,
    ResolutionStatus,
)
from .exceptions import (
    CapabilityNotFoundError,
    CapabilityResolutionError,
    InvalidCapabilityIdError,
)
from .policies import (
    ExecutionPolicyFederation,
    get_policy_federation,
)
from .registry import (
    CapabilityRegistry,
    get_capability_registry,
)


class CapabilityResolver:
    """
    Resolves capability requests.

    Pipeline:
    1. Validate capability ID format
    2. Look up capability in registry
    3. Evaluate policies
    4. Return resolution result

    Resolver does NOT:
      - Execute capabilities
      - Return callable objects
      - Modify registry or context
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        policy_federation: Optional[ExecutionPolicyFederation] = None,
    ):
        self._registry = registry
        self._policy_federation = policy_federation

    @property
    def registry(self) -> CapabilityRegistry:
        """Get the registry (lazy initialization)."""
        if self._registry is None:
            self._registry = get_capability_registry()
        return self._registry

    @property
    def policy_federation(self) -> ExecutionPolicyFederation:
        """Get the policy federation (lazy initialization)."""
        if self._policy_federation is None:
            self._policy_federation = get_policy_federation()
        return self._policy_federation

    def resolve(
        self,
        capability_id: str,
        context: Optional[ResolutionContext] = None,
    ) -> CapabilityResolutionResult:
        """
        Resolve a capability request.

        Args:
            capability_id: Full namespaced capability ID
            context: Resolution context (defaults to empty context)

        Returns:
            CapabilityResolutionResult with status and decision
        """
        if context is None:
            context = ResolutionContext()

        # Step 1: Look up capability
        try:
            capability = self.registry.get_capability(capability_id)
        except InvalidCapabilityIdError as e:
            return CapabilityResolutionResult(
                status=ResolutionStatus.NOT_FOUND,
                requested_capability_id=capability_id,
                rejection_reasons=[f"Invalid capability ID: {e.reason}"],
            )

        if capability is None:
            return CapabilityResolutionResult(
                status=ResolutionStatus.NOT_FOUND,
                requested_capability_id=capability_id,
                rejection_reasons=[f"Capability not registered: {capability_id}"],
            )

        # Step 2: Check enabled status (fast path)
        if not capability.enabled:
            return CapabilityResolutionResult(
                status=ResolutionStatus.DISABLED,
                requested_capability_id=capability_id,
                resolved_capability=capability,
                policy_decision=PolicyDecision.REJECTED,
                rejection_reasons=["Capability is disabled"],
                policies_evaluated=["enabled"],
            )

        # Step 3: Check replay safety (fast path for replay mode)
        if context.require_replay_safe and not capability.replay_safe:
            return CapabilityResolutionResult(
                status=ResolutionStatus.REPLAY_UNSAFE,
                requested_capability_id=capability_id,
                resolved_capability=capability,
                policy_decision=PolicyDecision.REJECTED,
                rejection_reasons=["Capability is not replay-safe"],
                policies_evaluated=["replay_safety"],
            )

        # Step 4: Full policy evaluation
        policy_result = self.policy_federation.evaluate(capability, context)

        if not policy_result.is_allowed:
            return CapabilityResolutionResult(
                status=ResolutionStatus.POLICY_REJECTED,
                requested_capability_id=capability_id,
                resolved_capability=capability,
                policy_decision=policy_result.overall_decision,
                rejection_reasons=policy_result.rejection_reasons,
                compatibility_summary=policy_result.compatibility_summary,
                policies_evaluated=policy_result.policies_evaluated,
            )

        # Step 5: Success
        return CapabilityResolutionResult(
            status=ResolutionStatus.RESOLVED,
            requested_capability_id=capability_id,
            resolved_capability=capability,
            policy_decision=PolicyDecision.ALLOWED,
            compatibility_summary=policy_result.compatibility_summary,
            policies_evaluated=policy_result.policies_evaluated,
        )

    def resolve_or_raise(
        self,
        capability_id: str,
        context: Optional[ResolutionContext] = None,
    ) -> CapabilityResolutionResult:
        """
        Resolve a capability, raising if resolution fails.

        Args:
            capability_id: Full namespaced capability ID
            context: Resolution context

        Returns:
            CapabilityResolutionResult (only if resolved)

        Raises:
            CapabilityResolutionError: If resolution fails
        """
        result = self.resolve(capability_id, context)

        if not result.is_resolved:
            raise CapabilityResolutionError(
                capability_id=capability_id,
                rejection_reasons=result.rejection_reasons,
            )

        return result

    def can_use(
        self,
        capability_id: str,
        context: Optional[ResolutionContext] = None,
    ) -> bool:
        """
        Check if a capability may be used.

        Convenience method for simple checks.

        Args:
            capability_id: Full namespaced capability ID
            context: Resolution context

        Returns:
            True if capability may be used, False otherwise
        """
        result = self.resolve(capability_id, context)
        return result.is_allowed


# -----------------------------------------------------------------------------
# Global Resolver
# -----------------------------------------------------------------------------

_global_resolver: Optional[CapabilityResolver] = None


def get_capability_resolver() -> CapabilityResolver:
    """Get the global capability resolver."""
    global _global_resolver
    if _global_resolver is None:
        _global_resolver = CapabilityResolver()
    return _global_resolver


def reset_capability_resolver() -> None:
    """Reset the global capability resolver."""
    global _global_resolver
    _global_resolver = None


def resolve_capability(
    capability_id: str,
    context: Optional[ResolutionContext] = None,
) -> CapabilityResolutionResult:
    """
    Resolve a capability using the global resolver.

    Convenience function for simple resolution.
    """
    return get_capability_resolver().resolve(capability_id, context)


def can_use_capability(
    capability_id: str,
    context: Optional[ResolutionContext] = None,
) -> bool:
    """
    Check if a capability may be used.

    Convenience function for simple checks.
    """
    return get_capability_resolver().can_use(capability_id, context)
