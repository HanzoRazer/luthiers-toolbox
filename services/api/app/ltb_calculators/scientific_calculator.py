"""Scientific Calculator - Luthier's ToolBox"""

from __future__ import annotations
import math
from typing import Optional
from .fraction_calculator import LTBFractionCalculator
from .basic_calculator import CalculatorState, Operation


class LTBScientificCalculator(LTBFractionCalculator):
    """Scientific calculator extending BasicCalculator."""
    
    # Constants
    E = math.e       # 2.718281828459045
    PI = math.pi     # 3.141592653589793
    
    def __init__(self, angle_mode: str = 'rad'):
        """Initialize scientific calculator."""
        super().__init__()
        self.angle_mode = angle_mode  # 'rad' or 'deg'
    
    # =========================================================================
    # CONSTANTS
    # =========================================================================
    
    def pi(self) -> 'LTBScientificCalculator':
        """Enter π (pi)."""
        self._clear_error()
        self.state.display = self._format_result(self.PI)
        self.state.just_evaluated = True
        return self
    
    def euler(self) -> 'LTBScientificCalculator':
        """Enter e (Euler's number)."""
        self._clear_error()
        self.state.display = self._format_result(self.E)
        self.state.just_evaluated = True
        return self
    
    # =========================================================================
    # EXPONENTIAL FUNCTIONS
    # =========================================================================
    
    def exp(self) -> 'LTBScientificCalculator':
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
    
    def pow10(self) -> 'LTBScientificCalculator':
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
    
    def power(self, exponent: float = None) -> 'LTBScientificCalculator':
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
    
    def square(self) -> 'LTBScientificCalculator':
        """Calculate x²."""
        return self.power(2)
    
    def cube(self) -> 'LTBScientificCalculator':
        """Calculate x³."""
        return self.power(3)
    
    # =========================================================================
    # LOGARITHMIC FUNCTIONS
    # =========================================================================
    
    def ln(self) -> 'LTBScientificCalculator':
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
    
    def log(self) -> 'LTBScientificCalculator':
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
    
    # =========================================================================
    # TRIGONOMETRIC FUNCTIONS
    # =========================================================================
    
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
    
    def sin(self) -> 'LTBScientificCalculator':
        """Sine function."""
        self._clear_error()
        x = self._to_radians(self.state.display_value)
        result = math.sin(x)
        self.state.display = self._format_result(result)
        self._history.append(f"sin({self.state.display_value}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def cos(self) -> 'LTBScientificCalculator':
        """Cosine function."""
        self._clear_error()
        x = self._to_radians(self.state.display_value)
        result = math.cos(x)
        self.state.display = self._format_result(result)
        self._history.append(f"cos({self.state.display_value}) = {result}")
        self.state.just_evaluated = True
        return self
    
    def tan(self) -> 'LTBScientificCalculator':
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
    
    def asin(self) -> 'LTBScientificCalculator':
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
    
    def acos(self) -> 'LTBScientificCalculator':
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
    
    def atan(self) -> 'LTBScientificCalculator':
        """Arc tangent (inverse tangent)."""
        self._clear_error()
        x = self.state.display_value
        result = self._from_radians(math.atan(x))
        self.state.display = self._format_result(result)
        self._history.append(f"atan({x}) = {result}")
        self.state.just_evaluated = True
        return self
    
    # =========================================================================
    # OTHER FUNCTIONS
    # =========================================================================
    
    def reciprocal(self) -> 'LTBScientificCalculator':
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
    
    def factorial(self) -> 'LTBScientificCalculator':
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
    
    def abs_val(self) -> 'LTBScientificCalculator':
        """Absolute value."""
        self._clear_error()
        x = self.state.display_value
        result = abs(x)
        self.state.display = self._format_result(result)
        self._history.append(f"|{x}| = {result}")
        self.state.just_evaluated = True
        return self
    
    # =========================================================================
    # MODE TOGGLE
    # =========================================================================
    
    def toggle_angle_mode(self) -> 'LTBScientificCalculator':
        """Toggle between radians and degrees."""
        self.angle_mode = 'deg' if self.angle_mode == 'rad' else 'rad'
        return self
    
    def set_radians(self) -> 'LTBScientificCalculator':
        """Set angle mode to radians."""
        self.angle_mode = 'rad'
        return self
    
    def set_degrees(self) -> 'LTBScientificCalculator':
        """Set angle mode to degrees."""
        self.angle_mode = 'deg'
        return self
    
    # =========================================================================
    # EXTENDED EXPRESSION PARSING
    # =========================================================================
    
    def evaluate(self, expression: str) -> float:
        """Evaluate expression with scientific functions."""
        self.clear()
        
        # Preprocess expression
        expr = expression.strip()
        expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-')
        expr = expr.replace('^', '**')  # Python power operator
        expr = expr.replace('π', 'pi')
        
        # Safe math namespace
        safe_dict = {
            'sin': lambda x: math.sin(self._to_radians(x) if self.angle_mode == 'deg' else x),
            'cos': lambda x: math.cos(self._to_radians(x) if self.angle_mode == 'deg' else x),
            'tan': lambda x: math.tan(self._to_radians(x) if self.angle_mode == 'deg' else x),
            'asin': lambda x: self._from_radians(math.asin(x)),
            'acos': lambda x: self._from_radians(math.acos(x)),
            'atan': lambda x: self._from_radians(math.atan(x)),
            'sqrt': math.sqrt,
            'ln': math.log,
            'log': math.log10,
            'exp': math.exp,
            'abs': abs,
            'pi': math.pi,
            'e': math.e,
            'PI': math.pi,
            'E': math.e,
        }
        
        try:
            result = eval(expr, {"__builtins__": {}}, safe_dict)
            
            if isinstance(result, (int, float)):
                self.state.display = self._format_result(float(result))
                self._history.append(f"{expression} = {result}")
                return float(result)
            else:
                self.state.error = "Invalid result"
                return 0.0
                
        except ZeroDivisionError:
            self.state.error = "Cannot divide by zero"
            return 0.0
        except ValueError as e:
            self.state.error = f"Math error: {e}"
            return 0.0
        except (TypeError, ArithmeticError) as e:  # WP-1: narrowed from except Exception
            self.state.error = f"Error: {str(e)}"
            return 0.0


# =============================================================================
# ENGINEERING SANITY CHECK
# =============================================================================

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
    result2 = calc.evaluate("e^1")
    
    # Method 3: Direct constant
    calc.euler()
    result3 = calc.value
    
    expected = 2.7182818285
    tolerance = 1e-9
    
    check1 = abs(result1 - expected) < tolerance
    check2 = abs(result2 - expected) < tolerance
    check3 = abs(result3 - expected) < tolerance
    
    print("=== Engineering Sanity Check ===")
    print(f"e^1 (button):     {result1:.10f}  {'✓' if check1 else '✗'}")
    print(f"e^1 (expression): {result2:.10f}  {'✓' if check2 else '✗'}")
    print(f"e (constant):     {result3:.10f}  {'✓' if check3 else '✗'}")
    print(f"Expected:         {expected}")
    print()
    
    return check1 and check2 and check3


# =============================================================================
# TESTS
# =============================================================================



# =============================================================================
# CLI
# =============================================================================



# =============================================================================
# MAIN
# =============================================================================

