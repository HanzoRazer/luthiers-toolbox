# services/api/app/ai_context_adapter/__init__.py
"""
AI Context Adapter v1

Produces a single envelope for AI consumption with:
- Hard-locked capabilities (no PII, no sensitive manufacturing)
- Strict redaction (removes forbidden fields)
- Focused payload: run_summary, design_intent, artifacts

See: contracts/toolbox_ai_context_envelope_v1.schema.json
"""

from .assembler.default import build_context_envelope
from .redactor.strict import redact_strict, RedactionResult

__all__ = [
    "build_context_envelope",
    "redact_strict",
    "RedactionResult",
]
