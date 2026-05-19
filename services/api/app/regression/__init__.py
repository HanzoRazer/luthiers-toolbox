"""
Regression Observability Infrastructure
========================================

MRP-1B: Framework for defining and comparing protected system outputs.

Components:
- signature_schema: Base schema for regression signatures
- blueprint_signature: Blueprint Reader output signature model
- dxf_comparator: Basic dimensional DXF comparison
- invariants: Invariant definitions for protected systems
- comparison_harness: Baseline comparison utilities

Part of MRP Governance Framework.
"""

from .signature_schema import (
    RegressionSignature,
    SignatureComparison,
    ComparisonResult,
)
from .blueprint_signature import (
    BlueprintOutputSignature,
    extract_blueprint_signature,
)
from .dxf_comparator import (
    DXFSummary,
    extract_dxf_summary,
    compare_dxf_summaries,
)
from .invariants import (
    InvariantCheck,
    InvariantResult,
    BLUEPRINT_READER_INVARIANTS,
    check_invariants,
)
from .comparison_harness import (
    BaselineComparison,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)

__all__ = [
    # Signature schema
    "RegressionSignature",
    "SignatureComparison",
    "ComparisonResult",
    # Blueprint signature
    "BlueprintOutputSignature",
    "extract_blueprint_signature",
    # DXF comparator
    "DXFSummary",
    "extract_dxf_summary",
    "compare_dxf_summaries",
    # Invariants
    "InvariantCheck",
    "InvariantResult",
    "BLUEPRINT_READER_INVARIANTS",
    "check_invariants",
    # Comparison harness
    "BaselineComparison",
    "compare_to_baseline",
    "load_baseline",
    "save_baseline",
]
