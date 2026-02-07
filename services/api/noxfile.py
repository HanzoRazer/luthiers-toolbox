"""
Nox sessions for the agentic spine test suite.

Usage:
    nox -s spine
"""

import nox


@nox.session
def spine(session):
    """Run the full agentic spine test suite."""
    session.install("-r", "requirements-dev.txt")
    # If you use poetry/pdm, swap to your install method.

    session.run("pytest", "-q", "tests/test_event_contract_parity.py")
    session.run("pytest", "-q", "tests/test_moments_engine_v1.py")
    session.run("pytest", "-q", "tests/test_policy_engine_v1.py")
    session.run("pytest", "-q", "tests/test_replay_smoke.py")
