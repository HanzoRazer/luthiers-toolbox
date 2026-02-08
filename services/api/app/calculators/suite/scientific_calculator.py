"""Scientific Calculator - Luthier's ToolBox"""

from __future__ import annotations
import math
from typing import Optional
from .fraction_calculator import FractionCalculator
from .basic_calculator import CalculatorState, Operation
from .scientific_stats_mixin import ScientificStatsMixin


class ScientificCalculator(ScientificStatsMixin, FractionCalculator):
    """Scientific calculator extending FractionCalculator."""
    
    # Constants
    E = math.e       # 2.718281828459045
    PI = math.pi     # 3.141592653589793
    
    def __init__(self, angle_mode: str = 'rad'):
        """Initialize scientific calculator."""
        super().__init__()
        self.angle_mode = angle_mode  # 'rad' or 'deg'
        self._stat_data: list = []  # Statistical data register
        self._stat_xy: list = []  # Regression data (x, y) pairs
        self._is_constant: bool = False  # Flag to display constants with full precision
    
    # --- CONSTANTS ---
    
    def pi(self) -> 'ScientificCalculator':
        """Enter pi (3.141592653589793)."""
        self._clear_error()
        # Display with full precision, bypass fraction formatting
        self.state.display = "3.141592653589793"
        self.state.just_evaluated = True
        self._is_constant = True  # Flag to prevent fraction conversion
        return self

    def euler(self) -> 'ScientificCalculator':
        """Enter e (Euler's number, 2.718281828459045)."""
        self._clear_error()
        self.state.display = "2.718281828459045"
        self.state.just_evaluated = True
        self._is_constant = True
        return self

    def tau(self) -> 'ScientificCalculator':
        """Enter tau (2*pi = 6.283185307179586)."""
        self._clear_error()
        self.state.display = "6.283185307179586"
        self.state.just_evaluated = True
        self._is_constant = True
        return self

    def phi(self) -> 'ScientificCalculator':
        """Enter phi (golden ratio = 1.618033988749895)."""
        self._clear_error()
        self.state.display = "1.618033988749895"
        self.state.just_evaluated = True
        self._is_constant = True
        return self
    
    # --- EXPONENTIAL FUNCTIONS ---
    
    def exp(self) -> 'ScientificCalculator':
        """Calculate e^x (Euler's number raised to display value)."""
        self._clear_error()
        x = self.state.display_value
        
        try:
            result = math.exp(x)
            self.state.display = self._format_result(result)
            self._history.append(f"e^{x} = {result}")
        except OverflowError:
            self.state.error = "Result too large"
        
        self.state.just_evaluated = True
        return self
    
    def pow10(self) -> 'ScientificCalculator':
        """Calculate 10^x."""
        self._clear_error()
        x = self.state.display_value
        
        try:
            result = math.pow(10, x)
            self.state.display = self._format_result(result)
            self._history.append(f"10^{x} = {result}")
        except OverflowError:
            self.state.error = "Result too large"
        
        self.state.just_evaluated = True
        return self
    
    def power(self, exponent: float = None) -> 'ScientificCalculator':
        """
        Calculate x^y.
        
        If exponent is None, sets up for y^x operation (like x^y button).
        """
        if exponent is not None:
            # Direct calculation
            self._clear_error()
            base = self.state.display_value
            try:
                result = math.pow(base, exponent)
                self.state.display = self._format_result(result)
                self._history.append(f"{base}^{exponent} = {result}")
            except (OverflowError, ValueError) as e:
                self.state.error = str(e)
            self.state.just_evaluated = True
        else:
            # Set up as binary operation (use multiply slot creatively)
            # Store base, wait for exponent
            self.operation('^')
        return self
    
    def square(self) -> 'ScientificCalculator':
        """Calculate x²."""
        return self.power(2)
    
    def cube(self) -> 'ScientificCalculator':
        """Calculate x³."""
        return self.power(3)
    
    # --- LOGARITHMIC FUNCTIONS ---
    
    def ln(self) -> 'ScientificCalculator':
        """Natural logarithm (base e)."""
        self._clear_error()
        x = self.state.display_value
        
        if x <= 0:
            self.state.error = "Cannot take log of non-positive number"
            return self
        
        result = math.log(x)
        self.state.display = self._format_result(result)
        self._history.append(f"ln({x}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def log(self) -> 'ScientificCalculator':
        """Common logarithm (base 10)."""
        self._clear_error()
        x = self.state.display_value
        
        if x <= 0:
            self.state.error = "Cannot take log of non-positive number"
            return self
        
        result = math.log10(x)
        self.state.display = self._format_result(result)
        self._history.append(f"log₁₀({x}) = {result}")
        self.state.just_evaluated = True
        return self
    
    # --- TRIGONOMETRIC FUNCTIONS ---
    
    def _to_radians(self, angle: float) -> float:
        """Convert angle to radians based on current mode."""
        if self.angle_mode == 'deg':
            return math.radians(angle)
        return angle
    
    def _from_radians(self, angle: float) -> float:
        """Convert radians to current angle mode."""
        if self.angle_mode == 'deg':
            return math.degrees(angle)
        return angle
    
    def sin(self) -> 'ScientificCalculator':
        """Sine function."""
        self._clear_error()
        x = self._to_radians(self.state.display_value)
        result = math.sin(x)
        self.state.display = self._format_result(result)
        self._history.append(f"sin({self.state.display_value}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def cos(self) -> 'ScientificCalculator':
        """Cosine function."""
        self._clear_error()
        x = self._to_radians(self.state.display_value)
        result = math.cos(x)
        self.state.display = self._format_result(result)
        self._history.append(f"cos({self.state.display_value}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def tan(self) -> 'ScientificCalculator':
        """Tangent function."""
        self._clear_error()
        x = self._to_radians(self.state.display_value)
        
        # Check for undefined (90°, 270°, etc.)
        cos_x = math.cos(x)
        if abs(cos_x) < 1e-15:
            self.state.error = "Undefined (division by zero)"
            return self
        
        result = math.tan(x)
        self.state.display = self._format_result(result)
        self._history.append(f"tan({self.state.display_value}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def asin(self) -> 'ScientificCalculator':
        """Arc sine (inverse sine)."""
        self._clear_error()
        x = self.state.display_value
        
        if x < -1 or x > 1:
            self.state.error = "asin domain error: -1 ≤ x ≤ 1"
            return self
        
        result = self._from_radians(math.asin(x))
        self.state.display = self._format_result(result)
        self._history.append(f"asin({x}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def acos(self) -> 'ScientificCalculator':
        """Arc cosine (inverse cosine)."""
        self._clear_error()
        x = self.state.display_value
        
        if x < -1 or x > 1:
            self.state.error = "acos domain error: -1 ≤ x ≤ 1"
            return self
        
        result = self._from_radians(math.acos(x))
        self.state.display = self._format_result(result)
        self._history.append(f"acos({x}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def atan(self) -> 'ScientificCalculator':
        """Arc tangent (inverse tangent)."""
        self._clear_error()
        x = self.state.display_value
        result = self._from_radians(math.atan(x))
        self.state.display = self._format_result(result)
        self._history.append(f"atan({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def atan2(self, x: float) -> 'ScientificCalculator':
        """Arc tangent of y/x (atan2), using display as y."""
        self._clear_error()
        y = self.state.display_value
        result = self._from_radians(math.atan2(y, x))
        self.state.display = self._format_result(result)
        self._history.append(f"atan2({y}, {x}) = {result}")
        self.state.just_evaluated = True
        return self

    # --- HYPERBOLIC FUNCTIONS ---

    def sinh(self) -> 'ScientificCalculator':
        """Hyperbolic sine."""
        self._clear_error()
        x = self.state.display_value
        result = math.sinh(x)
        self.state.display = self._format_result(result)
        self._history.append(f"sinh({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def cosh(self) -> 'ScientificCalculator':
        """Hyperbolic cosine."""
        self._clear_error()
        x = self.state.display_value
        result = math.cosh(x)
        self.state.display = self._format_result(result)
        self._history.append(f"cosh({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def tanh(self) -> 'ScientificCalculator':
        """Hyperbolic tangent."""
        self._clear_error()
        x = self.state.display_value
        result = math.tanh(x)
        self.state.display = self._format_result(result)
        self._history.append(f"tanh({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def asinh(self) -> 'ScientificCalculator':
        """Inverse hyperbolic sine."""
        self._clear_error()
        x = self.state.display_value
        result = math.asinh(x)
        self.state.display = self._format_result(result)
        self._history.append(f"asinh({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def acosh(self) -> 'ScientificCalculator':
        """Inverse hyperbolic cosine."""
        self._clear_error()
        x = self.state.display_value
        if x < 1:
            self.state.error = "acosh domain error: x >= 1"
            return self
        result = math.acosh(x)
        self.state.display = self._format_result(result)
        self._history.append(f"acosh({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def atanh(self) -> 'ScientificCalculator':
        """Inverse hyperbolic tangent."""
        self._clear_error()
        x = self.state.display_value
        if x <= -1 or x >= 1:
            self.state.error = "atanh domain error: -1 < x < 1"
            return self
        result = math.atanh(x)
        self.state.display = self._format_result(result)
        self._history.append(f"atanh({x}) = {result}")
        self.state.just_evaluated = True
        return self

    # --- OTHER FUNCTIONS ---
    
    def reciprocal(self) -> 'ScientificCalculator':
        """Calculate 1/x."""
        self._clear_error()
        x = self.state.display_value
        
        if x == 0:
            self.state.error = "Cannot divide by zero"
            return self
        
        result = 1 / x
        self.state.display = self._format_result(result)
        self._history.append(f"1/{x} = {result}")
        self.state.just_evaluated = True
        return self
    
    def factorial(self) -> 'ScientificCalculator':
        """Calculate n! (factorial)."""
        self._clear_error()
        n = self.state.display_value
        
        if n < 0:
            self.state.error = "Factorial undefined for negative numbers"
            return self
        
        if n != int(n):
            self.state.error = "Factorial requires integer"
            return self
        
        if n > 170:
            self.state.error = "Factorial too large"
            return self
        
        result = math.factorial(int(n))
        self.state.display = self._format_result(result)
        self._history.append(f"{int(n)}! = {result}")
        self.state.just_evaluated = True
        return self
    
    def abs_val(self) -> 'ScientificCalculator':
        """Absolute value."""
        self._clear_error()
        x = self.state.display_value
        result = abs(x)
        self.state.display = self._format_result(result)
        self._history.append(f"|{x}| = {result}")
        self.state.just_evaluated = True
        return self

    def modulo(self, divisor: float) -> 'ScientificCalculator':
        """Modulo operation (remainder)."""
        self._clear_error()
        x = self.state.display_value
        if divisor == 0:
            self.state.error = "Cannot divide by zero"
            return self
        result = x % divisor
        self.state.display = self._format_result(result)
        self._history.append(f"{x} mod {divisor} = {result}")
        self.state.just_evaluated = True
        return self

    def floor_val(self) -> 'ScientificCalculator':
        """Floor (round down)."""
        self._clear_error()
        x = self.state.display_value
        result = math.floor(x)
        self.state.display = self._format_result(result)
        self._history.append(f"floor({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def ceil_val(self) -> 'ScientificCalculator':
        """Ceiling (round up)."""
        self._clear_error()
        x = self.state.display_value
        result = math.ceil(x)
        self.state.display = self._format_result(result)
        self._history.append(f"ceil({x}) = {result}")
        self.state.just_evaluated = True
        return self

    def round_val(self, decimals: int = 0) -> 'ScientificCalculator':
        """Round to specified decimal places."""
        self._clear_error()
        x = self.state.display_value
        result = round(x, decimals)
        self.state.display = self._format_result(result)
        self._history.append(f"round({x}, {decimals}) = {result}")
        self.state.just_evaluated = True
        return self

    def nPr(self, r: int) -> 'ScientificCalculator':
        """Permutations: n! / (n-r)!"""
        self._clear_error()
        n = int(self.state.display_value)
        if n < 0 or r < 0 or r > n:
            self.state.error = "Invalid permutation parameters"
            return self
        result = math.perm(n, r)
        self.state.display = self._format_result(result)
        self._history.append(f"P({n},{r}) = {result}")
        self.state.just_evaluated = True
        return self

    def nCr(self, r: int) -> 'ScientificCalculator':
        """Combinations: n! / (r! * (n-r)!)"""
        self._clear_error()
        n = int(self.state.display_value)
        if n < 0 or r < 0 or r > n:
            self.state.error = "Invalid combination parameters"
            return self
        result = math.comb(n, r)
        self.state.display = self._format_result(result)
        self._history.append(f"C({n},{r}) = {result}")
        self.state.just_evaluated = True
        return self

    # =========================================================================
    # STATISTICS, REGRESSION, AND EXPRESSION EVAL
    # → Provided by ScientificStatsMixin (scientific_stats_mixin.py)
    # =========================================================================

    # --- MODE TOGGLE ---
    
    def toggle_angle_mode(self) -> 'ScientificCalculator':
        """Toggle between radians and degrees."""
        self.angle_mode = 'deg' if self.angle_mode == 'rad' else 'rad'
        return self
    
    def set_radians(self) -> 'ScientificCalculator':
        """Set angle mode to radians."""
        self.angle_mode = 'rad'
        return self
    
    def set_degrees(self) -> 'ScientificCalculator':
        """Set angle mode to degrees."""
        self.angle_mode = 'deg'
        return self
    
    # evaluate() → provided by ScientificStatsMixin


# --- ENGINEERING SANITY CHECK ---

def sanity_check() -> bool:
    """
    The old engineering student trick: e^1 should equal 2.7182818285
    
    Returns True if calculator is working correctly.
    """
    calc = ScientificCalculator()
    
    # Method 1: Button press
    calc.digit(1).exp()
    result1 = calc.value
    
    # Method 2: Expression
    result2 = calc.evaluate("e**1")
    
    # Method 3: Direct constant
    calc.euler()
    result3 = calc.value
    
    expected = 2.7182818285
    tolerance = 1e-9
    
    check1 = abs(result1 - expected) < tolerance
    check2 = abs(result2 - expected) < tolerance
    check3 = abs(result3 - expected) < tolerance
    
    return check1 and check2 and check3
