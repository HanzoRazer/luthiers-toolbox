"""Fraction Calculator - Luthier's ToolBox"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, Union
from fractions import Fraction
import math
import re
from .basic_calculator import BasicCalculator


@dataclass
class FractionResult:
    """
    Result that can be displayed as fraction or decimal.
    """
    decimal: float
    numerator: int
    denominator: int
    whole: int = 0
    
    @property
    def is_whole(self) -> bool:
        """True if this is a whole number."""
        return self.numerator == 0 or self.denominator == 1
    
    @property 
    def is_mixed(self) -> bool:
        """True if this has a whole number part."""
        return self.whole != 0
    
    def __str__(self) -> str:
        """Format as fraction string."""
        if self.is_whole:
            return str(self.whole if self.whole != 0 else self.numerator)
        elif self.is_mixed:
            return f"{self.whole}-{self.numerator}/{self.denominator}"
        else:
            return f"{self.numerator}/{self.denominator}"
    
    def to_improper(self) -> Tuple[int, int]:
        """Convert to improper fraction (numerator, denominator)."""
        if self.whole != 0:
            num = abs(self.whole) * self.denominator + self.numerator
            if self.whole < 0:
                num = -num
            return (num, self.denominator)
        return (self.numerator, self.denominator)


class FractionCalculator(BasicCalculator):
    """Calculator with fraction support for woodworkers."""
    
    # Common woodworking denominators
    PRECISION_8THS = 8
    PRECISION_16THS = 16
    PRECISION_32NDS = 32
    PRECISION_64THS = 64
    
    def __init__(self, precision: int = 16):
        """
        Initialize fraction calculator.
        
        Args:
            precision: Maximum denominator for display (8, 16, 32, 64)
        """
        super().__init__()
        self.precision = precision
        self._fraction_mode = True  # Display as fractions by default
        self._last_fraction: Optional[FractionResult] = None
    
    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    
    def set_precision(self, precision: int) -> 'FractionCalculator':
        """
        Set fraction precision (max denominator).
        
        Args:
            precision: 8, 16, 32, or 64
        """
        if precision not in (8, 16, 32, 64, 128):
            raise ValueError("Precision must be 8, 16, 32, 64, or 128")
        self.precision = precision
        return self
    
    def set_fraction_mode(self, enabled: bool = True) -> 'FractionCalculator':
        """Enable or disable fraction display mode."""
        self._fraction_mode = enabled
        return self
    
    def toggle_fraction_mode(self) -> 'FractionCalculator':
        """Toggle between fraction and decimal display."""
        self._fraction_mode = not self._fraction_mode
        return self
    
    # =========================================================================
    # FRACTION INPUT
    # =========================================================================
    
    def fraction(self, numerator: int, denominator: int = 1) -> 'FractionCalculator':
        """Enter a fraction."""
        if denominator == 0:
            self.state.error = "Cannot divide by zero"
            return self
        
        self._clear_error()
        value = numerator / denominator
        self.state.display = self._format_result(value)
        self._update_fraction_display(value)
        self.state.just_evaluated = False
        
        return self
    
    def mixed_number(self, whole: int, numerator: int, denominator: int) -> 'FractionCalculator':
        """Enter a mixed number."""
        if denominator == 0:
            self.state.error = "Cannot divide by zero"
            return self
        
        self._clear_error()
        sign = -1 if whole < 0 else 1
        value = sign * (abs(whole) + numerator / denominator)
        self.state.display = self._format_result(value)
        self._update_fraction_display(value)
        self.state.just_evaluated = False
        
        return self
    
    def parse_fraction(self, text: str) -> float:
        """Parse a fraction string and enter it."""
        self._clear_error()
        text = text.strip()
        
        # Try feet-inches format: 4'6-1/2" or 4' 6"
        feet_inches = re.match(
            r"(\d+)'[\s-]?(\d+)?(?:[\s-]?(\d+)/(\d+))?\"?",
            text
        )
        if feet_inches:
            feet = int(feet_inches.group(1))
            inches = int(feet_inches.group(2) or 0)
            if feet_inches.group(3) and feet_inches.group(4):
                frac = int(feet_inches.group(3)) / int(feet_inches.group(4))
            else:
                frac = 0
            value = feet * 12 + inches + frac
            self.state.display = self._format_result(value)
            self._update_fraction_display(value)
            return value
        
        # Try mixed number: "2-3/8" or "2 3/8"
        mixed = re.match(r"(-?\d+)[\s-]+(\d+)/(\d+)", text)
        if mixed:
            whole = int(mixed.group(1))
            num = int(mixed.group(2))
            denom = int(mixed.group(3))
            sign = -1 if whole < 0 else 1
            value = sign * (abs(whole) + num / denom)
            self.state.display = self._format_result(value)
            self._update_fraction_display(value)
            return value
        
        # Try simple fraction: "3/4"
        simple = re.match(r"(-?\d+)/(\d+)", text)
        if simple:
            num = int(simple.group(1))
            denom = int(simple.group(2))
            if denom == 0:
                self.state.error = "Cannot divide by zero"
                return 0.0
            value = num / denom
            self.state.display = self._format_result(value)
            self._update_fraction_display(value)
            return value
        
        # Try plain number (integer or decimal)
        try:
            value = float(text)
            self.state.display = self._format_result(value)
            self._update_fraction_display(value)
            return value
        except ValueError:
            self.state.error = f"Cannot parse: {text}"
            return 0.0
    
    # =========================================================================
    # FRACTION CONVERSION
    # =========================================================================
    
    def to_fraction(self, decimal: float = None, 
                    max_denom: int = None) -> FractionResult:
        """Convert decimal to fraction."""
        if decimal is None:
            decimal = self.state.display_value
        
        if max_denom is None:
            max_denom = self.precision
        
        # Handle negative numbers
        sign = -1 if decimal < 0 else 1
        decimal = abs(decimal)
        
        # Extract whole number part
        whole = int(decimal)
        fractional = decimal - whole
        
        # If very close to whole number, return it
        if fractional < 1e-9:
            return FractionResult(
                decimal=sign * decimal,
                numerator=0,
                denominator=1,
                whole=sign * whole
            )
        
        # Find best fraction approximation
        best_num = 0
        best_denom = 1
        best_error = float('inf')
        
        # Try all denominators up to max_denom that are powers of 2
        # (woodworking fractions are always powers of 2)
        denom = 2
        while denom <= max_denom:
            # Round to nearest fraction with this denominator
            num = round(fractional * denom)
            
            # Clamp to valid range
            if num >= denom:
                num = denom - 1
            
            error = abs(fractional - num / denom)
            
            if error < best_error:
                best_error = error
                best_num = num
                best_denom = denom
            
            denom *= 2
        
        # Reduce fraction
        gcd = math.gcd(best_num, best_denom)
        best_num //= gcd
        best_denom //= gcd
        
        # Handle case where fraction rounds to 1
        if best_num == best_denom:
            whole += 1
            best_num = 0
            best_denom = 1
        
        result = FractionResult(
            decimal=sign * (whole + best_num / best_denom if best_denom > 0 else whole),
            numerator=best_num,
            denominator=best_denom,
            whole=sign * whole if whole != 0 or best_num == 0 else 0
        )
        
        self._last_fraction = result
        return result
    
    def to_decimal(self, numerator: int, denominator: int) -> float:
        """
        Convert fraction to decimal.
        
        Args:
            numerator: Top number
            denominator: Bottom number
            
        Returns:
            Decimal value
        """
        if denominator == 0:
            self.state.error = "Cannot divide by zero"
            return 0.0
        return numerator / denominator
    
    def reduce(self, numerator: int, denominator: int) -> Tuple[int, int]:
        """
        Reduce fraction to lowest terms.
        
        Args:
            numerator: Top number
            denominator: Bottom number
            
        Returns:
            (reduced_numerator, reduced_denominator)
        """
        if denominator == 0:
            return (0, 1)
        
        gcd = math.gcd(abs(numerator), abs(denominator))
        return (numerator // gcd, denominator // gcd)
    
    # =========================================================================
    # FRACTION ARITHMETIC
    # =========================================================================
    
    def add_fractions(self, n1: int, d1: int, n2: int, d2: int) -> Tuple[int, int]:
        """
        Add two fractions.
        
        Returns:
            (numerator, denominator) reduced to lowest terms
        """
        # a/b + c/d = (ad + bc) / bd
        num = n1 * d2 + n2 * d1
        denom = d1 * d2
        return self.reduce(num, denom)
    
    def subtract_fractions(self, n1: int, d1: int, n2: int, d2: int) -> Tuple[int, int]:
        """
        Subtract two fractions.
        
        Returns:
            (numerator, denominator) reduced to lowest terms
        """
        num = n1 * d2 - n2 * d1
        denom = d1 * d2
        return self.reduce(num, denom)
    
    def multiply_fractions(self, n1: int, d1: int, n2: int, d2: int) -> Tuple[int, int]:
        """
        Multiply two fractions.
        
        Returns:
            (numerator, denominator) reduced to lowest terms
        """
        num = n1 * n2
        denom = d1 * d2
        return self.reduce(num, denom)
    
    def divide_fractions(self, n1: int, d1: int, n2: int, d2: int) -> Tuple[int, int]:
        """
        Divide two fractions.
        
        Returns:
            (numerator, denominator) reduced to lowest terms
        """
        if n2 == 0:
            return (0, 1)
        num = n1 * d2
        denom = d1 * n2
        return self.reduce(num, denom)
    
    # =========================================================================
    # DISPLAY
    # =========================================================================
    
    @property
    def display_fraction(self) -> str:
        """Get current value as fraction string."""
        result = self.to_fraction()
        return str(result)
    
    @property
    def display_mixed(self) -> str:
        """Get current value as mixed number string."""
        result = self.to_fraction()
        return str(result)
    
    @property
    def display_decimal(self) -> str:
        """Get current value as decimal string."""
        return self.state.display
    
    def _update_fraction_display(self, value: float):
        """Update internal fraction representation."""
        self._last_fraction = self.to_fraction(value)
    
    # =========================================================================
    # OVERRIDE DISPLAY FOR FRACTION MODE
    # =========================================================================
    
    @property
    def display(self) -> str:
        """Get display string (fraction or decimal based on mode)."""
        if self.state.error:
            return "Error"
        # Check if showing a constant (pi, e, etc.) - show decimal
        if hasattr(self, '_is_constant') and self._is_constant:
            return self.state.display
        if self._fraction_mode:
            return self.display_fraction
        return self.state.display
    
    # =========================================================================
    # CONVENIENCE FOR COMMON FRACTIONS
    # =========================================================================
    
    def eighth(self, n: int) -> 'FractionCalculator':
        """Enter n/8."""
        return self.fraction(n, 8)
    
    def sixteenth(self, n: int) -> 'FractionCalculator':
        """Enter n/16."""
        return self.fraction(n, 16)
    
    def thirtysecond(self, n: int) -> 'FractionCalculator':
        """Enter n/32."""
        return self.fraction(n, 32)
    
    def quarter(self, n: int = 1) -> 'FractionCalculator':
        """Enter n/4."""
        return self.fraction(n, 4)
    
    def half(self, n: int = 1) -> 'FractionCalculator':
        """Enter n/2."""
        return self.fraction(n, 2)
    
    # =========================================================================
    # FEET/INCHES SUPPORT
    # =========================================================================
    
    def feet_inches(self, feet: int, inches: float = 0, 
                    frac_num: int = 0, frac_denom: int = 1) -> 'FractionCalculator':
        """Enter measurement in feet and inches."""
        total_inches = feet * 12 + inches + (frac_num / frac_denom if frac_denom else 0)
        self.state.display = self._format_result(total_inches)
        self._update_fraction_display(total_inches)
        return self
    
    def to_feet_inches(self, inches: float = None) -> str:
        """
        Convert inches to feet-inches-fraction string.
        
        Args:
            inches: Value in inches (default: current display)
            
        Returns:
            Formatted string like 4' 6-1/2"
        """
        if inches is None:
            inches = self.state.display_value
        
        feet = int(inches // 12)
        remaining = inches % 12
        whole_inches = int(remaining)
        fractional = remaining - whole_inches
        
        frac = self.to_fraction(fractional)
        
        parts = []
        if feet > 0:
            parts.append(f"{feet}'")
        
        if frac.numerator > 0:
            parts.append(f"{whole_inches}-{frac.numerator}/{frac.denominator}\"")
        elif whole_inches > 0 or feet == 0:
            parts.append(f"{whole_inches}\"")
        
        return " ".join(parts)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Run tests
            calc = FractionCalculator()
            print("Testing fraction calculator...")
            calc.fraction(3, 4)
            print(f"3/4 = {calc.value} ({calc.display_fraction})")
            calc.fraction(3, 4).operation('+').fraction(1, 8)
            print(f"3/4 + 1/8 = {calc.equals()} ({calc.display_fraction})")
        else:
            calc = FractionCalculator()
            arg = ' '.join(sys.argv[1:])
            try:
                val = float(arg)
                result = calc.to_fraction(val)
                print(f"{val} = {result}")
            except ValueError:
                val = calc.parse_fraction(arg)
                if calc.error:
                    print(f"Error: {calc.error}")
                else:
                    print(f"{arg} = {val}")
