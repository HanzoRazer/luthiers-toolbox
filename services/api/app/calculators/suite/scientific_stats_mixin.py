"""
Statistical, regression, and expression evaluation methods for ScientificCalculator.

Extracted from scientific_calculator.py during WP-3 decomposition.
Mixed in via multiple inheritance: ScientificCalculator(FractionCalculator, ScientificStatsMixin).
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scientific_calculator import ScientificCalculator


class ScientificStatsMixin:
    """Mixin providing statistics, linear regression, and expression evaluation.

    Expects the host class to provide:
      - self._stat_data: list[float]
      - self._stat_xy: list[tuple[float, float]]
      - self.state (CalculatorState with .display, .error, .just_evaluated)
      - self._format_result(value) -> str
      - self._history: list[str]
      - self.clear() -> Self
      - self._to_radians(v) -> float
      - self._from_radians(v) -> float
      - self.angle_mode: str
    """

    # =========================================================================
    # STATISTICAL FUNCTIONS
    # =========================================================================

    def stat_clear(self) -> ScientificCalculator:
        """Clear statistical data register."""
        self._stat_data = []
        self._history.append("STAT CLR")
        return self

    def stat_add(self, value: float = None) -> ScientificCalculator:
        """Add value to statistical data (Sigma+)."""
        if value is None:
            value = self.state.display_value
        self._stat_data.append(value)
        self._history.append(f"SUM+ {value} (n={len(self._stat_data)})")
        return self

    def stat_remove(self, value: float = None) -> ScientificCalculator:
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

    def stat_add_xy(self, x: float, y: float) -> ScientificCalculator:
        """Add (x, y) data point for regression."""
        if not hasattr(self, '_stat_xy'):
            self._stat_xy = []
        self._stat_xy.append((x, y))
        self._history.append(f"XY+ ({x}, {y}) n={len(self._stat_xy)}")
        return self

    def stat_clear_xy(self) -> ScientificCalculator:
        """Clear regression data."""
        self._stat_xy = []
        self._history.append("XY CLR")
        return self

    def linear_regression(self) -> dict:
        """Calculate linear regression (y = a + bx)."""
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
