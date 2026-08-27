"""Grounding Agent v0.1 — read-only handoff truth check.

This package verifies whether a structured handoff still describes the live
repository before an implementation agent acts. It is read-only by
construction: its adapters expose read operations only and it never repairs a
mismatch (see ``docs/governance/agents/GROUNDING_AGENT_v0.1.md``).
"""

__version__ = "0.1.0"
