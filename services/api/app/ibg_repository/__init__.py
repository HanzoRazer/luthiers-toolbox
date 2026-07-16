"""
IBG Repository — Governed Repository Change Proposal contracts (PR A).

This package owns repository proposal *automation* — turning governed engineering
evidence into deterministic, reviewable repository change proposals. It is deliberately
homed OUTSIDE ``instrument_geometry/body/ibg/`` (which owns body-geometry evidence) and
OUTSIDE ``governance/`` (which defines constraints, not operational construction).

Constitutional boundary: this package moves IBG from observation to *proposal*, never to
authority. Nothing here promotes evidence, grants canonical authority, mutates a checkout,
commits, pushes, or creates a GitHub PR. PR A adds contracts only — no git, no router,
no filesystem or network I/O.
"""

from __future__ import annotations

from .proposal_target import (
    ProposalTargetBinding,
    ProposalBindingError,
    EvidenceContractError,
    InvalidTargetPathError,
    build_proposal_target_binding,
    normalize_producing_subsystem,
)
from .cbsp21_patch_adapter import (
    CBSP21_SCHEMA,
    REQUIRED_FIELDS,
    CBSP21PacketError,
    CBSP21PatchPacketAdapter,
    WHY_NOT_REDUNDANT_MIN_CHARS,
    build_cbsp21_patch_packet,
    validate_behavior_change_articulation,
    validate_cbsp21_patch_packet,
    canonical_packet_json,
    compute_packet_hash,
)
from .repository_change_proposal import (
    RepositoryChangeProposal,
    RepositoryChangeProposalError,
    PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    build_repository_change_proposal,
    validate_branch_ref,
)
from .repository_review_package import (
    RepositoryProposalReviewPackage,
    RepositoryReviewPackageError,
    build_repository_proposal_review_package,
)
# --- PR B: repository worktree isolation & proposal workspace ---
from .worktree_state import RepositoryWorktreeState
from .worktree_spec import (
    RepositoryWorktreeSpec,
    WorktreeSpecError,
    derive_workspace_id,
    derive_branch_name,
    normalize_allowed_paths,
)
from .git_runner import (
    GitRunner,
    GitRunnerError,
    GitCommandError,
    GitRunnerConfigError,
    LocalGitRunner,
    CommandResult,
)
from .worktree_validator import (
    WorktreeValidationError,
    verify_temp_root,
    verify_repository_root,
    normalize_repository_path,
    normalize_workspace_path,
    validate_workspace_path,
    validate_repository,
    validate_branch,
    validate_deterministic_naming,
    validate_worktree,
)
from .worktree_builder import (
    RepositoryWorktreeBuilder,
    WorktreeBuildError,
)
# --- PR C: review package, draft-PR metadata, deterministic exports ---
from .review_summary_builder import (
    ReviewSummaryError,
    normalize_review_sections,
    build_review_title,
    build_changed_file_summary,
    build_review_summary,
)
from .draft_pull_request_package import (
    DraftPullRequestPackage,
    DraftPullRequestPackageError,
    DRAFT_PR_CONSTITUTIONAL_CLASSIFICATION,
    build_draft_pull_request_package,
)
from .repository_review_bundle import (
    RepositoryReviewBundle,
    RepositoryReviewBundleError,
    REVIEW_BUNDLE_SCHEMA_VERSION,
    REVIEW_BUNDLE_CONSTITUTIONAL_CLASSIFICATION,
    normalize_workspace_metadata,
    build_review_bundle,
)
from .repository_review_export import (
    to_dict,
    to_json,
    to_markdown,
    build_review_json,
    build_review_markdown,
    stable_review_hash,
)
from .repository_proposal_pipeline import (
    CANONICAL_PIPELINE_MISSION,
    PIPELINE_TERMINAL_STAGE,
    PIPELINE_CONSTITUTIONAL_CLASSIFICATION,
    RepositoryProposalPipeline,
    RepositoryProposalPipelineResult,
    run_repository_proposal_pipeline,
)
# --- PR E: descriptive repository execution planning (downstream of the merged proposal) ---
from .repository_execution_plan import (
    EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION,
    STRUCTURAL_GROUPING_RELATIONSHIP,
    ExecutionGroup,
    DependencyGroup,
    ComplexitySummary,
    ProvenanceReference,
    RepositoryExecutionPlan,
)
from .execution_planner import (
    ExecutionPlanningError,
    SUPPORTED_RISK_LEVELS,
    ExecutionPlanner,
    build_execution_plan,
    execution_plan_builder,
    validate_execution_plan,
)
# --- PR F: observational repository proposal evaluation (downstream of the proposal + plan) ---
from .repository_proposal_evaluation import (
    EVALUATION_CONSTITUTIONAL_CLASSIFICATION,
    FINDING_CATEGORIES,
    FINDING_STATUSES,
    READINESS_COMPLETE,
    READINESS_INCOMPLETE,
    READINESS_SUMMARIES,
    EvaluationFinding,
    ProposalEvaluationError,
    RepositoryProposalEvaluation,
    compute_completeness_score,
    sort_findings,
    summarize_findings,
)
from .proposal_checks import GOVERNED_PROVENANCE_FIELDS
from .proposal_evaluator import (
    ProposalEvaluator,
    evaluate_execution_plan,
    evaluate_repository_proposal,
    proposal_evaluator,
    validate_repository_proposal_evaluation,
)
# --- PR G: repository readiness report (aggregation of the proposal + plan + evaluation) ---
from .repository_readiness_report import (
    READINESS_REPORT_CONSTITUTIONAL_CLASSIFICATION,
    READINESS_REPORT_ID_PREFIX,
    REPORT_SECTION_ORDER,
    ReadinessReportError,
    RepositoryGovernanceSummary,
    RepositoryReadinessReport,
    RepositoryReadinessSection,
    validate_readiness_summary,
)
from .readiness_report_builder import (
    build_repository_readiness_report,
    validate_repository_readiness_report,
)

__all__ = [
    "ProposalTargetBinding",
    "ProposalBindingError",
    "EvidenceContractError",
    "InvalidTargetPathError",
    "build_proposal_target_binding",
    "normalize_producing_subsystem",
    "CBSP21_SCHEMA",
    "REQUIRED_FIELDS",
    "CBSP21PacketError",
    "CBSP21PatchPacketAdapter",
    "build_cbsp21_patch_packet",
    "WHY_NOT_REDUNDANT_MIN_CHARS",
    "validate_behavior_change_articulation",
    "validate_cbsp21_patch_packet",
    "canonical_packet_json",
    "compute_packet_hash",
    "RepositoryChangeProposal",
    "RepositoryChangeProposalError",
    "PROPOSAL_CONSTITUTIONAL_CLASSIFICATION",
    "build_repository_change_proposal",
    "validate_branch_ref",
    "RepositoryProposalReviewPackage",
    "RepositoryReviewPackageError",
    "build_repository_proposal_review_package",
    # --- PR B: repository worktree isolation & proposal workspace ---
    "RepositoryWorktreeState",
    "RepositoryWorktreeSpec",
    "WorktreeSpecError",
    "derive_workspace_id",
    "derive_branch_name",
    "normalize_allowed_paths",
    "GitRunner",
    "GitRunnerError",
    "GitCommandError",
    "GitRunnerConfigError",
    "LocalGitRunner",
    "CommandResult",
    "WorktreeValidationError",
    "verify_temp_root",
    "verify_repository_root",
    "normalize_repository_path",
    "normalize_workspace_path",
    "validate_workspace_path",
    "validate_repository",
    "validate_branch",
    "validate_deterministic_naming",
    "validate_worktree",
    "RepositoryWorktreeBuilder",
    "WorktreeBuildError",
    # --- PR C: review package, draft-PR metadata, deterministic exports ---
    "ReviewSummaryError",
    "normalize_review_sections",
    "build_review_title",
    "build_changed_file_summary",
    "build_review_summary",
    "DraftPullRequestPackage",
    "DraftPullRequestPackageError",
    "DRAFT_PR_CONSTITUTIONAL_CLASSIFICATION",
    "build_draft_pull_request_package",
    "RepositoryReviewBundle",
    "RepositoryReviewBundleError",
    "REVIEW_BUNDLE_SCHEMA_VERSION",
    "REVIEW_BUNDLE_CONSTITUTIONAL_CLASSIFICATION",
    "normalize_workspace_metadata",
    "build_review_bundle",
    "to_dict",
    "to_json",
    "to_markdown",
    "build_review_json",
    "build_review_markdown",
    "stable_review_hash",
    # --- PR D: canonical repository proposal pipeline (orchestration-only) ---
    "CANONICAL_PIPELINE_MISSION",
    "PIPELINE_TERMINAL_STAGE",
    "PIPELINE_CONSTITUTIONAL_CLASSIFICATION",
    "RepositoryProposalPipeline",
    "RepositoryProposalPipelineResult",
    "run_repository_proposal_pipeline",
    # --- PR E: descriptive repository execution planning ---
    "EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION",
    "STRUCTURAL_GROUPING_RELATIONSHIP",
    "ExecutionGroup",
    "DependencyGroup",
    "ComplexitySummary",
    "ProvenanceReference",
    "RepositoryExecutionPlan",
    "ExecutionPlanningError",
    "SUPPORTED_RISK_LEVELS",
    "ExecutionPlanner",
    "build_execution_plan",
    "execution_plan_builder",
    "validate_execution_plan",
    # --- PR F: observational repository proposal evaluation ---
    "EVALUATION_CONSTITUTIONAL_CLASSIFICATION",
    "FINDING_CATEGORIES",
    "FINDING_STATUSES",
    "READINESS_COMPLETE",
    "READINESS_INCOMPLETE",
    "READINESS_SUMMARIES",
    "EvaluationFinding",
    "ProposalEvaluationError",
    "RepositoryProposalEvaluation",
    "compute_completeness_score",
    "sort_findings",
    "summarize_findings",
    "GOVERNED_PROVENANCE_FIELDS",
    "ProposalEvaluator",
    "evaluate_execution_plan",
    "evaluate_repository_proposal",
    "proposal_evaluator",
    "validate_repository_proposal_evaluation",
    # --- PR G: repository readiness report ---
    "READINESS_REPORT_CONSTITUTIONAL_CLASSIFICATION",
    "READINESS_REPORT_ID_PREFIX",
    "REPORT_SECTION_ORDER",
    "ReadinessReportError",
    "RepositoryGovernanceSummary",
    "RepositoryReadinessReport",
    "RepositoryReadinessSection",
    "validate_readiness_summary",
    "build_repository_readiness_report",
    "validate_repository_readiness_report",
]
