"""
Luthier's ToolBox Calculator Suite

Clean, tested calculators with proper separation of concerns.
These are pure calculators (input → output), NOT CAM geometry.

For CAM geometry (toolpaths, G-code), see:
    - generators/body_generator.py
    - generators/gcode_generator.py

Calculator hierarchy:
    BasicCalculator       - Standard 4-function calculator (+, -, *, /)
    FractionCalculator    - Extends Basic with fraction support (woodworking)
    ScientificCalculator  - Extends Fraction with trig/log/exp
    FinancialCalculator   - Extends Scientific with TVM/amortization
    LuthierCalculator     - Extends Scientific with guitar-specific calcs
"""

from .basic_calculator import BasicCalculator, CalculatorState, Operation
from .fraction_calculator import FractionCalculator, FractionResult
from .scientific_calculator import ScientificCalculator
from .financial_calculator import FinancialCalculator, TVMState, AmortizationRow
from .luthier_calculator import (
    LuthierCalculator, 
    FretPosition, 
    CompoundRadiusPoint, 
    StringTension
)

__all__ = [
    # Calculators
    'BasicCalculator',
    'FractionCalculator', 
    'ScientificCalculator',
    'FinancialCalculator',
    'LuthierCalculator',
    # Data classes
    'CalculatorState',
    'Operation',
    'FractionResult',
    'TVMState',
    'AmortizationRow',
    'FretPosition',
    'CompoundRadiusPoint',
    'StringTension',
]
