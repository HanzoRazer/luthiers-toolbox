# services/api/app/rmos/runs_v2/schemas/__init__.py
"""
Re-export all schemas from the parent schemas module.

Note: This package (schemas/) shadows the schemas.py module at the same level.
All imports from app.rmos.runs_v2.schemas resolve here.
"""
import importlib.util
import sys
from pathlib import Path

# Load the sibling schemas.py file directly
_schemas_file = Path(__file__).parent.parent / "schemas.py"
_spec = importlib.util.spec_from_file_location("_schemas_module", _schemas_file)
_schemas_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_schemas_module)

# Re-export key classes from schemas.py
utc_now = _schemas_module.utc_now
RunStatus = _schemas_module.RunStatus
ExplanationStatus = _schemas_module.ExplanationStatus
RiskLevel = _schemas_module.RiskLevel
VariantStatus = _schemas_module.VariantStatus
RejectReasonCode = _schemas_module.RejectReasonCode
Hashes = _schemas_module.Hashes
RunDecision = _schemas_module.RunDecision
RunOutputs = _schemas_module.RunOutputs
RunLineage = _schemas_module.RunLineage
RunAttachment = _schemas_module.RunAttachment
AdvisoryInputRef = _schemas_module.AdvisoryInputRef
RunArtifact = _schemas_module.RunArtifact
RunAttachmentCreateRequest = _schemas_module.RunAttachmentCreateRequest
RunAttachmentCreateResponse = _schemas_module.RunAttachmentCreateResponse
BindArtStudioCandidateRequest = _schemas_module.BindArtStudioCandidateRequest
BindArtStudioCandidateResponse = _schemas_module.BindArtStudioCandidateResponse
RunAttachmentRowV1 = _schemas_module.RunAttachmentRowV1
RunAttachmentsListResponseV1 = _schemas_module.RunAttachmentsListResponseV1

# Re-export advisory schemas
from .advisory_schemas import (
    AdvisoryAttachRequest,
    AdvisoryAttachResponse,
    AdvisoryVariantReviewRequest,
    AdvisoryVariantReviewRecord,
    BulkReviewAdvisoryVariantsRequest,
    BulkReviewAdvisoryVariantsResponse,
    PromoteVariantResponse,
)
