"""Forced-visible NOT_RUN reporting for the VEC-ROOT-001 harness.

The corpus cannot be committed, so on CI these tests cannot run. A harness that
quietly skips is a test that cannot fail, so every skip is recorded and printed
in a banner at the end of the session with the exact path that was missing.

``test_harness_is_wired`` always runs and never needs the corpus, so this
directory can never report "all green" because nothing executed.
"""

from __future__ import annotations

import pytest

NOT_RUN_RECORDS: list[tuple[str, str]] = []


def record_not_run(nodeid: str, reason: str) -> None:
    NOT_RUN_RECORDS.append((nodeid, reason))


def skip_not_run(request, reason: str) -> None:
    """Record a NOT_RUN and skip with a reason that names the cause."""
    record_not_run(request.node.nodeid, reason)
    pytest.skip(reason)


def pytest_terminal_summary(terminalreporter, exitstatus, config):  # noqa: ARG001
    if not NOT_RUN_RECORDS:
        return
    write = terminalreporter.write_line
    write("")
    write("=" * 78)
    write("VEC-ROOT-001 HARNESS: %d CRITERION(S) NOT RUN" % len(NOT_RUN_RECORDS))
    write("=" * 78)
    write("These are NOT passes. The eligibility defect recorded in")
    write("docs/audit/VEC-ROOT-001_eligibility_body_definition.md section 8 was")
    write("not measured on this run.")
    write("")
    for nodeid, reason in NOT_RUN_RECORDS:
        write("  %s" % nodeid)
        write("      %s" % reason)
    write("")
    write("Set VEC_ROOT_001_CORPUS to the directory holding the plans, or place")
    write("them in '<repo>/Guitar Plans' (gitignored). See corpus.py.")
    write("=" * 78)
