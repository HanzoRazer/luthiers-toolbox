"""
AI Context Adapter - Validator CLI

Validates context envelopes against the JSON schema.
Can be run standalone or as a pytest gate.

Usage:
    python -m app.ai_context.validator --envelope envelope.json
    python -m app.ai_context.validator --test-redaction
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import jsonschema
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# Schema path (relative to repo root)
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent.parent / "contracts" / "AI_CONTEXT_ADAPTER_INTERFACE_v1.json"


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_envelope(envelope: Dict[str, Any]) -> List[str]:
    """
    Validate an envelope against the JSON schema.
    
    Returns list of validation errors (empty if valid).
    """
    if not HAS_JSONSCHEMA:
        return ["jsonschema library not installed"]
    
    schema = load_schema()
    errors: List[str] = []
    
    validator = jsonschema.Draft202012Validator(schema)
    for error in validator.iter_errors(envelope):
        path = ".".join(str(p) for p in error.absolute_path)
        errors.append(f"{path}: {error.message}" if path else error.message)
    
    return errors


def validate_redaction(envelope: Dict[str, Any]) -> List[str]:
    """
    Validate that forbidden content is properly redacted.
    
    Returns list of redaction violations (empty if clean).
    """
    violations: List[str] = []
    
    # Get forbidden categories from policy
    policy = envelope.get("policy", {})
    forbidden = set(policy.get("forbidden_categories", []))
    
    # Check for forbidden content in sources
    context = envelope.get("context", {})
    sources = context.get("sources", [])
    
    for source in sources:
        payload = source.get("payload", {})
        source_id = source.get("source_id", "unknown")
        
        # Check for forbidden field patterns
        violations.extend(_check_payload_for_forbidden(payload, source_id, forbidden))
    
    return violations


def _check_payload_for_forbidden(
    payload: Any,
    source_id: str,
    forbidden: set,
    path: str = "",
) -> List[str]:
    """Recursively check payload for forbidden content."""
    violations: List[str] = []
    
    if not isinstance(payload, dict):
        return violations
    
    # Forbidden field patterns by category
    field_patterns = {
        "toolpaths": ["toolpath", "toolpaths", "path_data", "trajectory"],
        "gcode": ["gcode", "g_code", "nc_code", "ngc"],
        "machine_secrets": ["api_key", "password", "token", "secret", "credential"],
        "credential_material": ["api_key", "password", "token", "bearer", "private_key"],
        "player_pedagogy": ["player_id", "lesson_id", "coach_feedback", "practice_session"],
        "personal_data": ["email", "phone", "ssn", "credit_card", "bank_account"],
    }
    
    for key, value in payload.items():
        key_lower = key.lower()
        full_path = f"{path}.{key}" if path else key
        
        # Check each forbidden category
        for category in forbidden:
            patterns = field_patterns.get(category, [])
            for pattern in patterns:
                if pattern in key_lower:
                    # Check if it's properly redacted
                    if value != "[REDACTED]":
                        violations.append(
                            f"{source_id}:{full_path} - forbidden content ({category}): {key}"
                        )
        
        # Recurse into nested dicts
        if isinstance(value, dict):
            violations.extend(_check_payload_for_forbidden(value, source_id, forbidden, full_path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    violations.extend(_check_payload_for_forbidden(
                        item, source_id, forbidden, f"{full_path}[{i}]"
                    ))
    
    return violations


def test_redaction_pipeline() -> List[str]:
    """
    Test the redaction pipeline with sample data.
    
    Returns list of failures (empty if all tests pass).
    """
    from .schemas import (
        Actor,
        ActorKind,
        ActorRole,
        ContextRequest,
        ContextSource,
        RedactionPolicy,
        Scope,
        SourceKind,
    )
    from .redactor import strict_redactor
    
    failures: List[str] = []
    
    # Test 1: Toolpath field should be redacted
    source = ContextSource(
        source_id="test_1",
        kind=SourceKind.RUN_SUMMARY,
        content_type="application/json",
        payload={
            "run_id": "run_123",
            "toolpath_data": {"moves": [1, 2, 3]},  # Should be redacted
            "status": "ok",
        },
    )
    
    policy = RedactionPolicy()
    redacted, warnings = strict_redactor.redact_sources([source], policy)
    
    if redacted[0].payload.get("toolpath_data") != "[REDACTED]":
        failures.append("Test 1 FAILED: toolpath_data not redacted")
    
    # Test 2: Credential field should be redacted
    source = ContextSource(
        source_id="test_2",
        kind=SourceKind.RUN_SUMMARY,
        content_type="application/json",
        payload={
            "config": {
                "api_key": "secret123",  # Should be redacted
                "endpoint": "https://api.example.com",
            },
        },
    )
    
    redacted, warnings = strict_redactor.redact_sources([source], policy)
    
    if redacted[0].payload.get("config", {}).get("api_key") != "[REDACTED]":
        failures.append("Test 2 FAILED: api_key not redacted")
    
    # Test 3: Player pedagogy should be redacted
    source = ContextSource(
        source_id="test_3",
        kind=SourceKind.RUN_SUMMARY,
        content_type="application/json",
        payload={
            "player_id": "player_abc",  # Should be redacted
            "lesson_progress": 75,  # Should be redacted
            "pattern_name": "Classic Rosette",  # Should NOT be redacted
        },
    )
    
    redacted, warnings = strict_redactor.redact_sources([source], policy)
    
    if redacted[0].payload.get("player_id") != "[REDACTED]":
        failures.append("Test 3 FAILED: player_id not redacted")
    if redacted[0].payload.get("lesson_progress") != "[REDACTED]":
        failures.append("Test 3 FAILED: lesson_progress not redacted")
    if redacted[0].payload.get("pattern_name") != "Classic Rosette":
        failures.append("Test 3 FAILED: pattern_name incorrectly modified")
    
    # Test 4: Action patterns should be redacted
    source = ContextSource(
        source_id="test_4",
        kind=SourceKind.GOVERNANCE_NOTES,
        content_type="application/json",
        payload={
            "instructions": "To fix, POST /api/runs/123/approve",  # Should be redacted
            "explanation": "The run needs approval",  # Should NOT be redacted
        },
    )
    
    redacted, warnings = strict_redactor.redact_sources([source], policy)
    
    instructions = redacted[0].payload.get("instructions", "")
    if "POST /api/" in instructions:
        failures.append("Test 4 FAILED: action pattern not redacted")
    
    return failures


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate AI Context Adapter envelopes"
    )
    parser.add_argument(
        "--envelope",
        type=str,
        help="Path to envelope JSON file to validate",
    )
    parser.add_argument(
        "--test-redaction",
        action="store_true",
        help="Run redaction pipeline tests",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Only validate JSON schema, skip redaction check",
    )
    
    args = parser.parse_args()
    
    if args.test_redaction:
        print("Running redaction pipeline tests...")
        failures = test_redaction_pipeline()
        
        if failures:
            print(f"\n❌ {len(failures)} test(s) failed:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        else:
            print("✅ All redaction tests passed")
            return 0
    
    if args.envelope:
        envelope_path = Path(args.envelope)
        
        if not envelope_path.exists():
            print(f"❌ File not found: {envelope_path}")
            return 1
        
        with open(envelope_path) as f:
            envelope = json.load(f)
        
        print(f"Validating envelope: {envelope_path}")
        
        # Schema validation
        schema_errors = validate_envelope(envelope)
        if schema_errors:
            print(f"\n❌ Schema validation failed ({len(schema_errors)} errors):")
            for error in schema_errors[:10]:  # Limit output
                print(f"  - {error}")
            if len(schema_errors) > 10:
                print(f"  ... and {len(schema_errors) - 10} more")
            return 1
        else:
            print("✅ Schema validation passed")
        
        # Redaction validation
        if not args.schema_only:
            redaction_violations = validate_redaction(envelope)
            if redaction_violations:
                print(f"\n❌ Redaction validation failed ({len(redaction_violations)} violations):")
                for violation in redaction_violations[:10]:
                    print(f"  - {violation}")
                if len(redaction_violations) > 10:
                    print(f"  ... and {len(redaction_violations) - 10} more")
                return 1
            else:
                print("✅ Redaction validation passed")
        
        print("\n✅ All validations passed")
        return 0
    
    # No action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
