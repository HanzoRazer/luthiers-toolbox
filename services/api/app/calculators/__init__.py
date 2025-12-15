# services/api/app/calculators/__init__.py
"""
Calculator / physics facade for RMOS & Art Studio.

This package is the "front door" for all physics-style calculations:

- chipload
- heat
- deflection
- rim-speed
- material efficiency / BOM

Wave 4 introduces a simple MLPath-based feasibility function used by
Rosette and Relief Art Studio endpoints. Later waves can route that
call to more detailed per-operation calculators (Saw Lab, etc.).

Available calculators:
- bracing_calc: Bracing section calculations
- rosette_calc: Rosette channel calculations
- inlay_calc: Fretboard inlay calculations
- service: Unified CalculatorService facade

Feasibility facade:
- evaluate_mlpaths_feasibility: MLPath-based feasibility for Art Studio
"""

# Import the feasibility function from saw_bridge when available
try:
    from .saw_bridge import evaluate_operation_feasibility  # noqa: F401
except ImportError:
    # Saw bridge not yet available; this is fine during Wave 4
    evaluate_operation_feasibility = None

# Re-export key services (optional, may have RMOS dependencies)
try:
    from .service import CalculatorService  # noqa: F401
except ImportError:
    # RMOS/service not available, this is fine for isolated testing
    CalculatorService = None

__all__ = [
    "CalculatorService",
    "evaluate_operation_feasibility",
]
