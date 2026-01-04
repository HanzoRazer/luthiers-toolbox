"""
Advisory Asset Schemas (DEPRECATED LOCATION)

This file re-exports from the neutral zone for backwards compatibility.
New code should import from: app.advisory.schemas

Migration: Update imports to use app.advisory instead of this location.
"""
# Re-export everything from neutral zone
from app.advisory.schemas import *  # noqa: F401, F403

# Explicit re-exports for type checkers
from app.advisory.schemas import (
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
