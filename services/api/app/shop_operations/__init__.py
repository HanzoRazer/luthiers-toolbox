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
    SCHEMA_ID,
    SCHEMA_VERSION,
    DurationBasis,
    HumanCompletion,
    JobReference,
    JobReferenceVerification,
    MaterialUsage,
    MeasuredDuration,
    OperationStatus,
    ShopOperationRecordV1,
    make_operation_record,
)
from app.shop_operations.repository import FileShopOperationRepository

__all__ = [
    "JOB_SYSTEM",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "DurationBasis",
    "DuplicateOperationRecord",
    "FileShopOperationRepository",
    "HumanCompletion",
    "JobReference",
    "JobReferenceVerification",
    "MaterialUsage",
    "MeasuredDuration",
    "OperationRecordError",
    "OperationRecordNotFound",
    "OperationRepositoryError",
    "OperationSequenceError",
    "OperationStatus",
    "ShopOperationRecordV1",
    "make_operation_record",
]
