"""
Advisory Domain (Neutral Zone)

This module provides the shared advisory types and storage that both
AI sandbox and RMOS code may import from. It is the boundary between
AI generation and RMOS authority.

Architectural decision:
- AI sandbox creates advisories and persists them here
- RMOS links advisories to runs via attach_advisory()
- This module is NEUTRAL - neither AI sandbox nor RMOS authority

See docs/AI_SANDBOX_GOVERNANCE.md for details.
"""

# Schemas - all types for advisory assets
from .schemas import (
    AdvisoryAssetType,
    RejectionReason,
    AdvisoryAsset,
    AdvisoryAssetRef,
    AdvisoryAssetOut,
    GenerateImageRequest,
    GenerateImageResponse,
    ReviewAssetRequest,
    AttachToRunRequest,
    AttachToRunResponse,
    BulkReviewItem,
    BulkReviewRequest,
    BulkReviewResponse,
    ListAssetsResponse,
    CostEstimateRequest,
    ProviderCostEstimate,
    CostComparisonResponse,
    BudgetConfig,
    BudgetStatus,
    BatchEstimateRequest,
    BatchEstimateResponse,
    StylePreset,
    NegativePromptEntry,
    PromptTemplate,
    AssetSearchRequest,
    AssetSearchResponse,
    ExportFormat,
    ExportFilterRequest,
    ExportResult,
    SimilarityMatch,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    RequestRecord,
    PromptHistoryEntry,
    PromptHistoryResponse,
)

# Store - persistence layer
from .store import (
    AdvisoryAssetStore,
    PromptHistoryStore,
    BudgetTracker,
    RequestStore,
    get_advisory_store,
    get_prompt_history_store,
    get_budget_tracker,
    get_request_store,
    compute_content_hash,
    compute_prompt_hash,
)

__all__ = [
    # Types
    "AdvisoryAssetType",
    "RejectionReason",
    "AdvisoryAsset",
    "AdvisoryAssetRef",
    "AdvisoryAssetOut",
    "GenerateImageRequest",
    "GenerateImageResponse",
    "ReviewAssetRequest",
    "AttachToRunRequest",
    "AttachToRunResponse",
    "BulkReviewItem",
    "BulkReviewRequest",
    "BulkReviewResponse",
    "ListAssetsResponse",
    "CostEstimateRequest",
    "ProviderCostEstimate",
    "CostComparisonResponse",
    "BudgetConfig",
    "BudgetStatus",
    "BatchEstimateRequest",
    "BatchEstimateResponse",
    "StylePreset",
    "NegativePromptEntry",
    "PromptTemplate",
    "AssetSearchRequest",
    "AssetSearchResponse",
    "ExportFormat",
    "ExportFilterRequest",
    "ExportResult",
    "SimilarityMatch",
    "DuplicateCheckRequest",
    "DuplicateCheckResponse",
    "RequestRecord",
    "PromptHistoryEntry",
    "PromptHistoryResponse",
    # Store
    "AdvisoryAssetStore",
    "PromptHistoryStore",
    "BudgetTracker",
    "RequestStore",
    "get_advisory_store",
    "get_prompt_history_store",
    "get_budget_tracker",
    "get_request_store",
    "compute_content_hash",
    "compute_prompt_hash",
]
