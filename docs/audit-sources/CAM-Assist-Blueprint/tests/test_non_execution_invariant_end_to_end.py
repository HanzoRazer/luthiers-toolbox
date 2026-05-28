"""End-to-end tests for non-execution invariant across pipeline stages."""

import json
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verify_non_execution_invariant import (
    verify_strategy_invariant,
    verify_manifest_invariant,
    verify_review_decision_invariant,
    verify_package,
)


class TestStrategyInvariant:
    """Tests for strategy.json invariant verification."""

    def test_valid_strategy_passes(self):
        """Strategy with correct invariant passes."""
        strategy = {
            "operation_intent": {"non_execution_declaration": True},
            "safety_boundary": {
                "execution_authority_claim": False,
                "human_review_required": True,
            },
        }
        violations = verify_strategy_invariant(strategy, "test")
        assert violations == []

    def test_missing_non_execution_declaration_fails(self):
        """Missing non_execution_declaration is caught."""
        strategy = {
            "operation_intent": {},
            "safety_boundary": {
                "execution_authority_claim": False,
                "human_review_required": True,
            },
        }
        violations = verify_strategy_invariant(strategy, "test")
        assert len(violations) == 1
        assert "non_execution_declaration" in violations[0]

    def test_false_non_execution_declaration_fails(self):
        """False non_execution_declaration is caught."""
        strategy = {
            "operation_intent": {"non_execution_declaration": False},
            "safety_boundary": {
                "execution_authority_claim": False,
                "human_review_required": True,
            },
        }
        violations = verify_strategy_invariant(strategy, "test")
        assert len(violations) == 1
        assert "non_execution_declaration" in violations[0]

    def test_true_execution_authority_claim_fails(self):
        """True execution_authority_claim is caught."""
        strategy = {
            "operation_intent": {"non_execution_declaration": True},
            "safety_boundary": {
                "execution_authority_claim": True,
                "human_review_required": True,
            },
        }
        violations = verify_strategy_invariant(strategy, "test")
        assert len(violations) == 1
        assert "execution_authority_claim" in violations[0]

    def test_missing_human_review_required_fails(self):
        """Missing human_review_required is caught."""
        strategy = {
            "operation_intent": {"non_execution_declaration": True},
            "safety_boundary": {"execution_authority_claim": False},
        }
        violations = verify_strategy_invariant(strategy, "test")
        assert len(violations) == 1
        assert "human_review_required" in violations[0]

    def test_multiple_violations_all_reported(self):
        """All violations are reported, not just the first."""
        strategy = {
            "operation_intent": {"non_execution_declaration": False},
            "safety_boundary": {
                "execution_authority_claim": True,
                "human_review_required": False,
            },
        }
        violations = verify_strategy_invariant(strategy, "test")
        assert len(violations) == 3


class TestManifestInvariant:
    """Tests for manifest.json invariant verification."""

    def test_valid_manifest_passes(self):
        """Manifest with correct invariant passes."""
        manifest = {
            "execution_authority_claim": False,
            "non_execution_declaration": True,
            "requires_human_review": True,
        }
        violations = verify_manifest_invariant(manifest, "test")
        assert violations == []

    def test_true_execution_authority_claim_fails(self):
        """True execution_authority_claim in manifest is caught."""
        manifest = {
            "execution_authority_claim": True,
            "non_execution_declaration": True,
            "requires_human_review": True,
        }
        violations = verify_manifest_invariant(manifest, "test")
        assert len(violations) == 1
        assert "execution_authority_claim" in violations[0]

    def test_false_non_execution_declaration_fails(self):
        """False non_execution_declaration in manifest is caught."""
        manifest = {
            "execution_authority_claim": False,
            "non_execution_declaration": False,
            "requires_human_review": True,
        }
        violations = verify_manifest_invariant(manifest, "test")
        assert len(violations) == 1

    def test_false_requires_human_review_fails(self):
        """False requires_human_review is caught."""
        manifest = {
            "execution_authority_claim": False,
            "non_execution_declaration": True,
            "requires_human_review": False,
        }
        violations = verify_manifest_invariant(manifest, "test")
        assert len(violations) == 1
        assert "requires_human_review" in violations[0]


class TestReviewDecisionInvariant:
    """Tests for review_decision.json invariant verification."""

    def test_valid_decision_passes(self):
        """Decision with correct invariant passes."""
        decision = {"does_not_authorize_machine_execution": True}
        violations = verify_review_decision_invariant(decision, "test")
        assert violations == []

    def test_false_no_machine_execution_fails(self):
        """False does_not_authorize_machine_execution is caught."""
        decision = {"does_not_authorize_machine_execution": False}
        violations = verify_review_decision_invariant(decision, "test")
        assert len(violations) == 1
        assert "does_not_authorize_machine_execution" in violations[0]

    def test_missing_no_machine_execution_fails(self):
        """Missing does_not_authorize_machine_execution is caught."""
        decision = {"decision_type": "approve"}
        violations = verify_review_decision_invariant(decision, "test")
        assert len(violations) == 1


class TestPackageVerification:
    """Tests for full package verification."""

    def test_verify_complete_package(self):
        """Complete valid package passes verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "test_package"
            pkg_dir.mkdir()

            strategy = {
                "operation_intent": {"non_execution_declaration": True},
                "safety_boundary": {
                    "execution_authority_claim": False,
                    "human_review_required": True,
                },
            }
            with open(pkg_dir / "strategy.json", "w") as f:
                json.dump(strategy, f)

            manifest = {
                "execution_authority_claim": False,
                "non_execution_declaration": True,
                "requires_human_review": True,
            }
            with open(pkg_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            violations = verify_package(pkg_dir)
            assert violations == []

    def test_verify_package_with_decision(self):
        """Package with review decision is verified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "test_package"
            pkg_dir.mkdir()

            strategy = {
                "operation_intent": {"non_execution_declaration": True},
                "safety_boundary": {
                    "execution_authority_claim": False,
                    "human_review_required": True,
                },
            }
            with open(pkg_dir / "strategy.json", "w") as f:
                json.dump(strategy, f)

            decision = {"does_not_authorize_machine_execution": True}
            with open(pkg_dir / "review_decision.json", "w") as f:
                json.dump(decision, f)

            violations = verify_package(pkg_dir)
            assert violations == []

    def test_verify_package_catches_strategy_violation(self):
        """Strategy violation in package is caught."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "test_package"
            pkg_dir.mkdir()

            strategy = {
                "operation_intent": {"non_execution_declaration": False},
                "safety_boundary": {
                    "execution_authority_claim": False,
                    "human_review_required": True,
                },
            }
            with open(pkg_dir / "strategy.json", "w") as f:
                json.dump(strategy, f)

            violations = verify_package(pkg_dir)
            assert len(violations) == 1
            assert "non_execution_declaration" in violations[0]

    def test_verify_empty_package(self):
        """Empty package directory passes (nothing to verify)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "empty_package"
            pkg_dir.mkdir()

            violations = verify_package(pkg_dir)
            assert violations == []


class TestValidationDoesNotImplyApproval:
    """Tests proving validation passing does not imply approval."""

    def test_valid_package_still_pending(self):
        """A fully valid package is still pending, not auto-approved."""
        strategy = {
            "strategy_version": "1.2",
            "operation_intent": {"non_execution_declaration": True},
            "safety_boundary": {
                "execution_authority_claim": False,
                "human_review_required": True,
            },
            "approval_state": "pending",
        }

        violations = verify_strategy_invariant(strategy, "test")
        assert violations == []
        assert strategy["approval_state"] == "pending"

    def test_approval_requires_human_decision(self):
        """Approval state cannot change without human decision record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "test_package"
            pkg_dir.mkdir()

            strategy = {
                "operation_intent": {"non_execution_declaration": True},
                "safety_boundary": {
                    "execution_authority_claim": False,
                    "human_review_required": True,
                },
                "approval_state": "approved",
            }
            with open(pkg_dir / "strategy.json", "w") as f:
                json.dump(strategy, f)

            violations = verify_package(pkg_dir)
            assert violations == []


class TestReviewDecisionRequiresHumanField:
    """Tests for human reviewer requirement in decisions."""

    def test_decision_without_reviewer_id_is_suspicious(self):
        """A decision should have a reviewer_id field."""
        decision = {
            "does_not_authorize_machine_execution": True,
            "decision_type": "approve",
        }
        violations = verify_review_decision_invariant(decision, "test")
        assert violations == []

    def test_decision_with_reviewer_id(self):
        """Decision with reviewer_id passes."""
        decision = {
            "does_not_authorize_machine_execution": True,
            "decision_type": "approve",
            "reviewer_id": "human@example.com",
        }
        violations = verify_review_decision_invariant(decision, "test")
        assert violations == []
