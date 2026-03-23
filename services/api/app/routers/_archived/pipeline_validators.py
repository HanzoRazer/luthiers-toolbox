# services/api/app/routers/pipeline_validators.py
"""Pipeline validation functions."""
from __future__ import annotations

from typing import List

from fastapi import HTTPException

from .pipeline_schemas import PipelineOp


def validate_ops(ops: List[PipelineOp]) -> None:
    """Validate pipeline operations.

    Raises HTTPException if validation fails.
    """
    if not ops:
        raise HTTPException(status_code=400, detail="Pipeline must contain at least one operation.")

    ids = [op.id for op in ops if op.id]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="Pipeline operation IDs must be unique.")

    kinds = [op.kind for op in ops]
    if "export_post" in kinds:
        idx_export = kinds.index("export_post")
        if idx_export > 0 and "adaptive_plan_run" not in kinds[:idx_export]:
            raise HTTPException(
                status_code=400,
                detail="export_post requires a prior adaptive_plan_run operation.",
            )
