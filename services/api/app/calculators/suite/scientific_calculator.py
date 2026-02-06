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
        self._stat_data: list = []  # Statistical data register
        self._stat_xy: list = []  # Regression data (x, y) pairs
        self._is_constant: bool = False  # Flag to display constants with full precision
    
    # =========================================================================
    # CONSTANTS
    # =========================================================================
    
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

    def atan2(self, x: float) -> 'ScientificCalculator':
        """Arc tangent of y/x (atan2), using display as y."""
        self._clear_error()
        y = self.state.display_value
        result = self._from_radians(math.atan2(y, x))
        self.state.display = self._format_result(result)
        self._history.append(f"atan2({y}, {x}) = {result}")
        self.state.just_evaluated = True
        return self

    # =========================================================================
    # HYPERBOLIC FUNCTIONS
    # =========================================================================

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
    # STATISTICAL FUNCTIONS
    # =========================================================================

    def stat_clear(self) -> 'ScientificCalculator':
        """Clear statistical data register."""
        self._stat_data = []
        self._history.append("STAT CLR")
        return self

    def stat_add(self, value: float = None) -> 'ScientificCalculator':
        """Add value to statistical data (Sigma+)."""
        if value is None:
            value = self.state.display_value
        self._stat_data.append(value)
        self._history.append(f"SUM+ {value} (n={len(self._stat_data)})")
        return self

    def stat_remove(self, value: float = None) -> 'ScientificCalculator':
        """Remove value from statistical data (Sigma-)."""
        if value is None:
            value = self.state.display_value
        if value in self._stat_data:
            self._stat_data.remove(value)
            self._history.append(f"SUM- {value} (n={len(self._stat_data)})")
        return self

    @property
    def stat_n(self) -> int:
        """Number of data points."""
        return len(self._stat_data)

    def stat_sum(self) -> float:
        """Sum of all data points (Sigma x)."""
        result = sum(self._stat_data)
        self.state.display = self._format_result(result)
        self._history.append(f"SUM = {result}")
        self.state.just_evaluated = True
        return result

    def stat_sum_sq(self) -> float:
        """Sum of squares (Sigma x^2)."""
        result = sum(x**2 for x in self._stat_data)
        self.state.display = self._format_result(result)
        self._history.append(f"SUM(x^2) = {result}")
        self.state.just_evaluated = True
        return result

    def stat_mean(self) -> float:
        """Arithmetic mean (average)."""
        if not self._stat_data:
            self.state.error = "No data"
            return 0.0
        result = sum(self._stat_data) / len(self._stat_data)
        self.state.display = self._format_result(result)
        self._history.append(f"MEAN = {result}")
        self.state.just_evaluated = True
        return result

    def stat_stddev(self, population: bool = False) -> float:
        """Standard deviation (sample or population)."""
        n = len(self._stat_data)
        if n < 2:
            self.state.error = "Need at least 2 data points"
            return 0.0
        mean = sum(self._stat_data) / n
        variance = sum((x - mean)**2 for x in self._stat_data)
        if population:
            variance /= n
        else:
            variance /= (n - 1)
        result = math.sqrt(variance)
        self.state.display = self._format_result(result)
        label = "Sn" if population else "Sn-1"
        self._history.append(f"{label} = {result}")
        self.state.just_evaluated = True
        return result

    def stat_variance(self, population: bool = False) -> float:
        """Variance (sample or population)."""
        n = len(self._stat_data)
        if n < 2:
            self.state.error = "Need at least 2 data points"
            return 0.0
        mean = sum(self._stat_data) / n
        variance = sum((x - mean)**2 for x in self._stat_data)
        if population:
            result = variance / n
        else:
            result = variance / (n - 1)
        self.state.display = self._format_result(result)
        self._history.append(f"VAR = {result}")
        self.state.just_evaluated = True
        return result

    def stat_min(self) -> float:
        """Minimum value in data."""
        if not self._stat_data:
            self.state.error = "No data"
            return 0.0
        result = min(self._stat_data)
        self.state.display = self._format_result(result)
        self._history.append(f"MIN = {result}")
        self.state.just_evaluated = True
        return result

    def stat_max(self) -> float:
        """Maximum value in data."""
        if not self._stat_data:
            self.state.error = "No data"
            return 0.0
        result = max(self._stat_data)
        self.state.display = self._format_result(result)
        self._history.append(f"MAX = {result}")
        self.state.just_evaluated = True
        return result

    # =========================================================================
    # LINEAR REGRESSION (2-variable statistics)
    # =========================================================================

    def stat_add_xy(self, x: float, y: float) -> 'ScientificCalculator':
        """Add (x, y) data point for regression."""
        if not hasattr(self, '_stat_xy'):
            self._stat_xy = []
        self._stat_xy.append((x, y))
        self._history.append(f"XY+ ({x}, {y}) n={len(self._stat_xy)}")
        return self

    def stat_clear_xy(self) -> 'ScientificCalculator':
        """Clear regression data."""
        self._stat_xy = []
        self._history.append("XY CLR")
        return self

    def linear_regression(self) -> dict:
        """
        Calculate linear regression (y = a + bx).

        Returns:
            Dict with slope (b), intercept (a), correlation (r), r-squared
        """
        if not hasattr(self, '_stat_xy') or len(self._stat_xy) < 2:
            self.state.error = "Need at least 2 data points"
            return {}

        n = len(self._stat_xy)
        sum_x = sum(p[0] for p in self._stat_xy)
        sum_y = sum(p[1] for p in self._stat_xy)
        sum_xy = sum(p[0] * p[1] for p in self._stat_xy)
        sum_x2 = sum(p[0]**2 for p in self._stat_xy)
        sum_y2 = sum(p[1]**2 for p in self._stat_xy)

        # Calculate slope (b) and intercept (a)
        denom = n * sum_x2 - sum_x**2
        if abs(denom) < 1e-15:
            self.state.error = "Cannot compute regression (vertical line)"
            return {}

        b = (n * sum_xy - sum_x * sum_y) / denom
        a = (sum_y - b * sum_x) / n

        # Calculate correlation coefficient (r)
        num = n * sum_xy - sum_x * sum_y
        denom_r = math.sqrt((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))
        r = num / denom_r if denom_r != 0 else 0

        result = {
            'slope': round(b, 10),
            'intercept': round(a, 10),
            'r': round(r, 10),
            'r_squared': round(r**2, 10),
            'n': n,
            'equation': f"y = {a:.4f} + {b:.4f}x"
        }

        self._history.append(f"LinReg: {result['equation']}, r={r:.4f}")
        return result

    def predict_y(self, x: float) -> float:
        """Predict y-value from linear regression."""
        reg = self.linear_regression()
        if not reg:
            return 0.0
        result = reg['intercept'] + reg['slope'] * x
        self.state.display = self._format_result(result)
        self._history.append(f"y({x}) = {result}")
        self.state.just_evaluated = True
        return result

    def predict_x(self, y: float) -> float:
        """Predict x-value from linear regression."""
        reg = self.linear_regression()
        if not reg or abs(reg['slope']) < 1e-15:
            self.state.error = "Cannot predict x (slope is zero)"
            return 0.0
        result = (y - reg['intercept']) / reg['slope']
        self.state.display = self._format_result(result)
        self._history.append(f"x({y}) = {result}")
        self.state.just_evaluated = True
        return result

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
            # Trigonometric
            'sin': lambda x: math.sin(self._to_radians(x) if self.angle_mode == 'deg' else x),
            'cos': lambda x: math.cos(self._to_radians(x) if self.angle_mode == 'deg' else x),
            'tan': lambda x: math.tan(self._to_radians(x) if self.angle_mode == 'deg' else x),
            'asin': lambda x: self._from_radians(math.asin(x)),
            'acos': lambda x: self._from_radians(math.acos(x)),
            'atan': lambda x: self._from_radians(math.atan(x)),
            'atan2': lambda y, x: self._from_radians(math.atan2(y, x)),
            # Hyperbolic
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'asinh': math.asinh,
            'acosh': math.acosh,
            'atanh': math.atanh,
            # Exponential/logarithmic
            'sqrt': math.sqrt,
            'ln': math.log,
            'log': math.log10,
            'log2': math.log2,
            'exp': math.exp,
            'pow': math.pow,
            # Rounding
            'floor': math.floor,
            'ceil': math.ceil,
            'round': round,
            'abs': abs,
            # Combinatorics
            'factorial': math.factorial,
            'perm': math.perm,
            'comb': math.comb,
            # Constants - use full precision
            'pi': 3.141592653589793,
            'e': 2.718281828459045,
            'PI': 3.141592653589793,
            'E': 2.718281828459045,
            'tau': 6.283185307179586,
            'phi': 1.618033988749895,  # Golden ratio
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
        except (TypeError, OverflowError, ArithmeticError) as e:  # WP-1
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
