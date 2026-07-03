"""Policy guard for the API Health + Smoke nightly workflow (CI-RED-020-B).

This is a deliberately text-level ratchet, NOT a YAML framework. It exists to make
the CI-RED-020-B fix un-reintroducible:

  - the workflow must not run the full `api-verify` target (which starved the smoke
    witness and cancelled the nightly job), and
  - it must keep the load-bearing step-level `timeout-minutes` on the smoke step
    (which converts a hung smoke from `cancelled` into a named `failure`).

Guarding `api-verify`'s ABSENCE without also guarding the step-timeout's PRESENCE
would protect only the less important half — so both are asserted here.
"""
import re
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "api_health_and_smoke.yml"
)


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_file_exists():
    assert WORKFLOW.is_file(), f"workflow not found: {WORKFLOW}"


def test_no_full_api_verify():
    # The full-verification detour must be gone. Tolerant of whitespace.
    assert not re.search(r"make\s+api-verify", _text()), (
        "api_health_and_smoke.yml must NOT run `make api-verify` — the nightly smoke "
        "witness is not full API verification (CI-RED-020-B)."
    )


def test_invokes_smoke_entry_point():
    text = _text()
    assert ("make api-smoke-posts" in text) or ("run_api_smoke_posts.sh" in text), (
        "workflow must invoke the smoke entry point "
        "(`make api-smoke-posts` or `scripts/smoke/run_api_smoke_posts.sh`)."
    )


def test_uploads_smoke_artifact():
    assert "smoke_posts.json" in _text(), (
        "workflow must produce/upload the smoke witness artifact smoke_posts.json."
    )


def test_keeps_scheduled_trigger():
    text = _text()
    assert re.search(r"^\s*schedule\s*:", text, re.MULTILINE) and "cron:" in text, (
        "workflow must keep a scheduled trigger (this is the NIGHTLY witness)."
    )


def _smoke_step_block() -> str:
    """Text of the 'Run v15.5 smoke' step up to the next '- name:' step."""
    m = re.search(
        r"-\s*name:\s*Run v15\.5 smoke.*?(?=\n\s*-\s*name:)",
        _text(),
        re.DOTALL,
    )
    return m.group(0) if m else ""


def test_smoke_step_has_step_level_timeout():
    block = _smoke_step_block()
    assert block, "could not locate the 'Run v15.5 smoke (all presets)' step."
    assert re.search(r"^\s*timeout-minutes\s*:", block, re.MULTILINE), (
        "the smoke step must carry a STEP-level `timeout-minutes` — this is what "
        "converts a hung smoke from `cancelled` into a named `failure` (CI-RED-020-B)."
    )
