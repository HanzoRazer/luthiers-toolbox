"""
Scientific Calculator - Luthier's ToolBox

Extends FractionCalculator with scientific functions.
Built for engineers who know that e^1 = 2.7182818285

Functions:
    Exponential:
        e^x     Euler's number raised to x
        10^x    10 raised to x
        x^y     x raised to y power
        
    Logarithmic:
        ln      Natural log (base e)
        log     Common log (base 10)
        
    Trigonometric (radians by default):
        sin, cos, tan
        asin, acos, atan
        
    Other:
        π       Pi constant
        e       Euler's constant
        x²      Square
        x³      Cube
        1/x     Reciprocal
        n!      Factorial
        abs     Absolute value

Usage:
    calc = ScientificCalculator()
    
    # The engineering sanity check
    calc.exp()  # e^1 when display is 1
    assert abs(calc.value - 2.7182818285) < 1e-9
    
    # Or:
    result = calc.evaluate("e^1")  # 2.718281828459045

Author: Luthier's ToolBox
"""

from __future__ import annotations
import math
from typing import Optional
from .fraction_calculator import FractionCalculator
from .basic_calculator import CalculatorState, Operation


class ScientificCalculator(FractionCalculator):
    """
    Scientific calculator extending FractionCalculator.
    
    Adds exponential, logarithmic, and trigonometric functions.
    
    Example:
        >>> calc = ScientificCalculator()
        >>> calc.digit(1).exp()  # e^1
        >>> print(calc.display)
        2.7182818285
        
        >>> calc.pi().operation('*').digit(2).equals()
        6.283185307179586
    """
    
    # Constants
    E = math.e       # 2.718281828459045
    PI = math.pi     # 3.141592653589793
    
    def __init__(self, angle_mode: str = 'rad'):
        """
        Initialize scientific calculator.
        
        Args:
            angle_mode: 'rad' for radians (default), 'deg' for degrees
        """
        super().__init__()
        self.angle_mode = angle_mode  # 'rad' or 'deg'
    
    # =========================================================================
    # CONSTANTS
    # =========================================================================
    
    def pi(self) -> 'ScientificCalculator':
        """Enter π (pi)."""
        self._clear_error()
        self.state.display = self._format_result(self.PI)
        self.state.just_evaluated = True
        return self
    
    def euler(self) -> 'ScientificCalculator':
        """Enter e (Euler's number)."""
        self._clear_error()
        self.state.display = self._format_result(self.E)
        self.state.just_evaluated = True
        return self
    
    # =========================================================================
    # EXPONENTIAL FUNCTIONS
    # =========================================================================
    
    def exp(self) -> 'ScientificCalculator':
        """
        Calculate e^x (Euler's number raised to display value).
        
        The classic engineering sanity check:
            calc.digit(1).exp() should give 2.7182818285
        """
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
    
    # =========================================================================
    # LOGARITHMIC FUNCTIONS
    # =========================================================================
    
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
    
    # =========================================================================
    # OTHER FUNCTIONS
    # =========================================================================
    
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
    
    # =========================================================================
    # MODE TOGGLE
    # =========================================================================
    
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
    
    # =========================================================================
    # EXTENDED EXPRESSION PARSING
    # =========================================================================
    
    def evaluate(self, expression: str) -> float:
        """
        Evaluate expression with scientific functions.
        
        Supports: +, -, *, /, ^, sqrt(), sin(), cos(), tan(), 
                  ln(), log(), e, pi, exp()
        
        Examples:
            calc.evaluate("e^1")           # 2.718281828459045
            calc.evaluate("sin(pi/2)")     # 1.0
            calc.evaluate("log(100)")      # 2.0
            calc.evaluate("2^10")          # 1024.0
        """
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
        except Exception as e:
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


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            print("Testing scientific calculator...")
            calc = ScientificCalculator()
            calc.digit(1).exp()
            print(f"e^1 = {calc.value}")
            print(f"Sanity check: {'PASS' if sanity_check() else 'FAIL'}")
        elif sys.argv[1] == 'sanity':
            passed = sanity_check()
            print(f"Sanity check: {'PASS' if passed else 'FAIL'}")
        else:
            calc = ScientificCalculator()
            expr = ' '.join(sys.argv[1:])
            result = calc.evaluate(expr)
            if calc.error:
                print(f"Error: {calc.error}")
            else:
                print(result)
