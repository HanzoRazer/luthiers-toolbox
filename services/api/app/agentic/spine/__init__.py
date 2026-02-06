# app/agentic/spine/__init__.py
"""
Agentic Spine — Reference Implementation

This module contains the core agentic orchestration logic:
- moments.py: Moment detection from event streams
- policy.py: Decision policy engine

These implementations are intentionally conservative and designed to:
1. Pass the test suite in tests/test_moments_engine_v1.py and tests/test_policy_engine_v1.py
2. Work correctly in shadow mode (M0)
3. Provide reasonable defaults for M1/M2

For full specifications, see:
- docs/EVENT_MOMENTS_CATALOG_V1.md
- docs/AGENT_DECISION_POLICY_V1.md
- docs/UWSM_UPDATE_RULES_V1.md
"""

from .moments import detect_moments
from .policy import decide

__all__ = ["detect_moments", "decide"]
