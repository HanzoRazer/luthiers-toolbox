"""Configuration loading with JSON schema validation.

Supports .codequalityrc.json at project root.  All values are
coerced defensively so None from the JSON never causes TypeError
downstream.

Schema
------
{
  "exclude_dirs":    ["node_modules", "dist"],
  "file_patterns":   ["**/*.vue", "**/*.ts", "**/*.py"],
  "checks":          [],           // empty = all
  "exclude_checks":  [],
  "severity_filter": ["critical", "warning", "info"],
  "workers":         4,
  "rules": {
    "duplicate_detection": {
      "enabled": true,
      "min_lines": 5,
      "ignore_css": true,
      "ignore_imports": true
    },
    "magic_numbers": {
      "enabled": true,
      "allow_css_values": true,
      "allowlist": [0, 1, 2, -1, 100]
    },
    "unused_variables": {
      "vue_script_setup_aware": true
    }
  }
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULTS: Dict[str, Any] = {
    "exclude_dirs": [
        "node_modules", "dist", ".git", "__pycache__",
        ".venv", "venv", "build", "coverage",
    ],
    "file_patterns": [
        "**/*.vue", "**/*.ts", "**/*.tsx",
        "**/*.js", "**/*.jsx", "**/*.py",
    ],
    "checks": [],          # empty = run all
    "exclude_checks": [],
    "severity_filter": ["critical", "warning", "info"],
    "workers": 4,
    "rules": {
        "duplicate_detection": {
            "enabled": True,
            "min_lines": 5,
            "ignore_css": True,
            "ignore_imports": True,
        },
        "magic_numbers": {
            "enabled": True,
            "allow_css_values": True,
            "allowlist": [0, 1, 2, -1, 100, 255, 360, 180],
        },
        "unused_variables": {
            "vue_script_setup_aware": True,
        },
    },
}

# ── Schema (lightweight — no jsonschema dep required) ─────────────────────────

_SCHEMA: Dict[str, type] = {
    "exclude_dirs":    list,
    "file_patterns":   list,
    "checks":          list,
    "exclude_checks":  list,
    "severity_filter": list,
    "workers":         int,
    "rules":           dict,
}

_VALID_SEVERITIES = {"critical", "warning", "info"}


def _validate(cfg: Dict[str, Any]) -> List[str]:
    """Return a list of validation error strings (empty = valid)."""
    errors: List[str] = []

    for key, expected_type in _SCHEMA.items():
        val = cfg.get(key)
        if val is not None and not isinstance(val, expected_type):
            errors.append(
                f"Config key '{key}' must be {expected_type.__name__}, "
                f"got {type(val).__name__}"
            )

    # Validate severity_filter values
    sev_filter = cfg.get("severity_filter") or []
    if isinstance(sev_filter, list):
        unknown = set(sev_filter) - _VALID_SEVERITIES
        if unknown:
            errors.append(
                f"severity_filter contains unknown values: {sorted(unknown)}. "
                f"Valid values: {sorted(_VALID_SEVERITIES)}"
            )

    # Validate workers
    workers = cfg.get("workers")
    if workers is not None and isinstance(workers, int) and workers < 1:
        errors.append("workers must be >= 1")

    return errors


# ── Public API ────────────────────────────────────────────────────────────────

def load_config(
    project_path: Path,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Load config from .codequalityrc.json, merge with defaults.

    Priority: CLI overrides > rc file > defaults.
    """
    import sys

    cfg = _deep_merge(DEFAULTS, {})  # start with a deep copy of defaults

    rc_path = project_path / ".codequalityrc.json"
    if rc_path.exists():
        try:
            raw = json.loads(rc_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                print(
                    f"[config] .codequalityrc.json must be a JSON object — ignored",
                    file=sys.stderr,
                )
            else:
                errors = _validate(raw)
                if errors:
                    for err in errors:
                        print(f"[config] Validation error: {err}", file=sys.stderr)
                else:
                    cfg = _deep_merge(cfg, raw)
        except json.JSONDecodeError as exc:
            print(f"[config] Failed to parse .codequalityrc.json: {exc}", file=sys.stderr)

    if overrides:
        cfg = _deep_merge(cfg, overrides)

    # Defensive coercion — ensure no None values on critical list keys
    for key in ("checks", "exclude_checks", "exclude_dirs", "file_patterns", "severity_filter"):
        if cfg.get(key) is None:
            cfg[key] = DEFAULTS[key][:]

    return cfg


def load_baseline(baseline_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON baseline file produced by a previous run."""
    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return []


def is_suppressed(
    issue: Dict[str, Any],
    baseline: List[Dict[str, Any]],
) -> bool:
    """Return True if ``issue`` matches a known baseline entry."""
    for known in baseline:
        if (
            known.get("check") == issue.get("check")
            and known.get("file") == issue.get("file")
            and known.get("line") == issue.get("line")
            and known.get("message") == issue.get("message")
        ):
            return True
    return False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``."""
    import copy
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result
