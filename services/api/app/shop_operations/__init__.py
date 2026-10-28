"""Shop-operation records (SHOP-OP-RECORD-001).

Facts about operations performed on a CNC-Production-Shop job: identity,
status, measured duration, material usage, evidence and readiness references,
and human completion. No route, no UI, and no CAM or manufacturing authority.
"""
from app.shop_operations.errors import (
    DuplicateOperationRecord,
    OperationRecordError,
    OperationRecordNotFound,
    OperationRepositoryError,
    OperationSequenceError,
)
from app.shop_operations.operation_record_v1 import (
    JOB_SYSTEM,
    LEGACY_PROVENANCE_UNAVAILABLE,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V1_0,
    SCHEMA_VERSION_V1_1,
    SUPPORTED_SCHEMA_VERSIONS,
    DurationBasis,
    HumanCompletion,
    JobReference,
    JobReferenceVerification,
    MaterialMeasurementSource,
    MaterialUsage,
    MeasuredDuration,
    OperationStatus,
    ShopOperationRecordV1,
    make_operation_record,
    material_provenance_disposition,
    new_operation_record_id,
)
from app.shop_operations.repository import FileShopOperationRepository

__all__ = [
    "JOB_SYSTEM",
    "LEGACY_PROVENANCE_UNAVAILABLE",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "SCHEMA_VERSION_V1_0",
    "SCHEMA_VERSION_V1_1",
    "SUPPORTED_SCHEMA_VERSIONS",
    "DurationBasis",
    "DuplicateOperationRecord",
    "FileShopOperationRepository",
    "HumanCompletion",
    "JobReference",
    "JobReferenceVerification",
    "MaterialMeasurementSource",
    "MaterialUsage",
    "MeasuredDuration",
    "OperationRecordError",
    "OperationRecordNotFound",
    "OperationRepositoryError",
    "OperationSequenceError",
    "OperationStatus",
    "ShopOperationRecordV1",
    "make_operation_record",
    "material_provenance_disposition",
    "new_operation_record_id",
]
