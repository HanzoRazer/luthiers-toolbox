# File: services/api/app/services/pipeline_spec_validator.py
# NEW – validate pipeline specs before saving/importing

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal


@dataclass
class PipelineSpecIssue:
    path: str
    message: str
    severity: Literal["error", "warning"] = "error"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class PipelineSpecValidationResult:
    ok: bool
    errors: List[PipelineSpecIssue]
    warnings: List[PipelineSpecIssue]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }


_ALLOWED_KINDS = {
    "dxf_preflight",
    "adaptive_plan",
    "adaptive_plan_run",
    "export_post",
    "simulate_gcode",
}

_UNITS_ALLOWED = {"mm", "inch"}


def _require_dict(
    spec: Any,
    issues: List[PipelineSpecIssue],
) -> Optional[Dict[str, Any]]:
    if not isinstance(spec, dict):
        issues.append(
            PipelineSpecIssue(
                path="",
                message=f"Expected pipeline spec to be an object, got {type(spec).__name__}",
                severity="error",
            )
        )
        return None
    return spec


def _validate_top_level(
    spec: Dict[str, Any],
    errors: List[PipelineSpecIssue],
    warnings: List[PipelineSpecIssue],
) -> None:
    # tool_d
    tool_d = spec.get("tool_d")
    if tool_d is None:
        warnings.append(
            PipelineSpecIssue(
                path="tool_d",
                message="tool_d not set; defaulting to 6.0mm in runner is allowed but explicit is preferred.",
                severity="warning",
            )
        )
    else:
        try:
            val = float(tool_d)
            if val <= 0:
                errors.append(
                    PipelineSpecIssue(
                        path="tool_d",
                        message="tool_d must be > 0.",
                        severity="error",
                    )
                )
        except Exception:
            errors.append(
                PipelineSpecIssue(
                    path="tool_d",
                    message=f"tool_d must be a number, got {type(tool_d).__name__}.",
                    severity="error",
                )
            )

    # units
    units = spec.get("units")
    if units is not None:
        if units not in _UNITS_ALLOWED:
            errors.append(
                PipelineSpecIssue(
                    path="units",
                    message=f"units must be one of {sorted(_UNITS_ALLOWED)}, got {units!r}.",
                    severity="error",
                )
            )
    else:
        warnings.append(
            PipelineSpecIssue(
                path="units",
                message="units not set; runner will default to 'mm'.",
                severity="warning",
            )
        )

    # geometry_layer: optional but recommend string if present
    if "geometry_layer" in spec and spec["geometry_layer"] is not None:
        if not isinstance(spec["geometry_layer"], str):
            errors.append(
                PipelineSpecIssue(
                    path="geometry_layer",
                    message="geometry_layer must be a string if provided.",
                    severity="error",
                )
            )

    # machine_id / post_id: no strict validation here; just type check
    for key in ("machine_id", "post_id"):
        if key in spec and spec[key] is not None and not isinstance(spec[key], str):
            errors.append(
                PipelineSpecIssue(
                    path=key,
                    message=f"{key} must be a string or null.",
                    severity="error",
                )
            )


def _validate_ops(
    spec: Dict[str, Any],
    errors: List[PipelineSpecIssue],
    warnings: List[PipelineSpecIssue],
) -> None:
    ops = spec.get("ops")
    if ops is None:
        errors.append(
            PipelineSpecIssue(
                path="ops",
                message="ops is required and must be a non-empty array.",
                severity="error",
            )
        )
        return

    if not isinstance(ops, list):
        errors.append(
            PipelineSpecIssue(
                path="ops",
                message=f"ops must be an array, got {type(ops).__name__}.",
                severity="error",
            )
        )
        return

    if not ops:
        errors.append(
            PipelineSpecIssue(
                path="ops",
                message="ops may not be empty; define at least one operation.",
                severity="error",
            )
        )
        return

    for idx, op in enumerate(ops):
        path_prefix = f"ops[{idx}]"
        if not isinstance(op, dict):
            errors.append(
                PipelineSpecIssue(
                    path=path_prefix,
                    message=f"Each op must be an object, got {type(op).__name__}.",
                    severity="error",
                )
            )
            continue

        kind = op.get("kind")
        if not isinstance(kind, str):
            errors.append(
                PipelineSpecIssue(
                    path=f"{path_prefix}.kind",
                    message="kind is required and must be a string.",
                    severity="error",
                )
            )
            continue

        if kind not in _ALLOWED_KINDS:
            errors.append(
                PipelineSpecIssue(
                    path=f"{path_prefix}.kind",
                    message=f"Unknown op kind {kind!r}. Allowed kinds: {sorted(_ALLOWED_KINDS)}.",
                    severity="error",
                )
            )

        params = op.get("params")
        if params is not None and not isinstance(params, dict):
            errors.append(
                PipelineSpecIssue(
                    path=f"{path_prefix}.params",
                    message=f"params must be an object if provided, got {type(params).__name__}.",
                    severity="error",
                )
            )
            continue

        # Kind-specific checks
        if kind == "dxf_preflight":
            if not params or "profile" not in params:
                warnings.append(
                    PipelineSpecIssue(
                        path=f"{path_prefix}.params.profile",
                        message="profile is not set; generic preflight will be used.",
                        severity="warning",
                    )
                )
        elif kind == "adaptive_plan":
            if params and "geometry_layer" in params:
                if params["geometry_layer"] is not None and not isinstance(
                    params["geometry_layer"], str
                ):
                    errors.append(
                        PipelineSpecIssue(
                            path=f"{path_prefix}.params.geometry_layer",
                            message="geometry_layer must be a string or null.",
                            severity="error",
                        )
                    )
        elif kind == "export_post":
            if not params or "endpoint" not in params:
                errors.append(
                    PipelineSpecIssue(
                        path=f"{path_prefix}.params.endpoint",
                        message="export_post requires params.endpoint to be set (e.g. '/cam/roughing_gcode').",
                        severity="error",
                    )
                )


def validate_pipeline_spec(spec: Any) -> PipelineSpecValidationResult:
    """
    Validate a pipeline spec structure.

    This is invoked before persisting presets or running pipelines to catch
    structural issues early and provide clear diagnostics to the UI.
    """
    errors: List[PipelineSpecIssue] = []
    warnings: List[PipelineSpecIssue] = []

    spec_dict = _require_dict(spec, errors)
    if spec_dict is None:
        return PipelineSpecValidationResult(ok=False, errors=errors, warnings=warnings)

    _validate_top_level(spec_dict, errors, warnings)
    _validate_ops(spec_dict, errors, warnings)

    ok = not errors
    return PipelineSpecValidationResult(ok=ok, errors=errors, warnings=warnings)
