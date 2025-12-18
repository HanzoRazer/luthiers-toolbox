"""
Fraction Calculator - Luthier's ToolBox

Woodworker-friendly calculator that displays and operates on fractions.
Slots between BasicCalculator and ScientificCalculator in the hierarchy.

Features:
    Display:
        - Show results as fractions (1/8, 3/16, 1/32)
        - Configurable precision (8ths, 16ths, 32nds, 64ths)
        - Mixed numbers (2-3/8)
        - Decimal/fraction toggle
        
    Input:
        - Enter fractions: "3/4", "1-1/2", "2 3/8"
        - Feet-inches: 4'6-1/2" 
        
    Operations:
        - Add/subtract fractions
        - Multiply/divide fractions
        - Convert decimal ↔ fraction
        - Reduce to lowest terms
        - Find common denominator

Usage:
    calc = FractionCalculator()
    
    # Add fractions
    calc.fraction(3, 4).operation('+').fraction(1, 8)
    calc.equals()  # Returns 0.875, displays "7/8"
    
    # Convert decimal to fraction
    calc.to_fraction(0.875)  # "7/8"
    calc.to_fraction(0.875, max_denom=16)  # "14/16" 
    
    # Parse fraction string
    calc.parse_fraction("2-3/8")  # 2.375

Woodworking denominators:
    Tape measures: 16ths or 32nds
    Precision work: 32nds or 64ths
    Rough carpentry: 8ths

Author: Luthier's ToolBox
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, Union
from fractions import Fraction
import math
import re
from basic_calculator import BasicCalculator


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
    """
    Calculator with fraction support for woodworkers.
    
    Extends BasicCalculator with:
    - Fraction input and display
    - Decimal ↔ fraction conversion
    - Configurable precision (8ths, 16ths, 32nds, 64ths)
    
    Example:
        >>> calc = FractionCalculator()
        >>> calc.set_precision(16)  # Work in 16ths
        >>> calc.fraction(3, 4).operation('+').fraction(1, 8)
        >>> print(calc.display_fraction)
        7/8
    """
    
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
        """
        Enter a fraction.
        
        Args:
            numerator: Top number
            denominator: Bottom number (default 1 for whole numbers)
            
        Example:
            calc.fraction(3, 4)      # 3/4
            calc.fraction(7, 8)      # 7/8
            calc.fraction(5)         # 5 (whole number)
        """
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
        """
        Enter a mixed number.
        
        Args:
            whole: Whole number part
            numerator: Fraction numerator
            denominator: Fraction denominator
            
        Example:
            calc.mixed_number(2, 3, 8)  # 2-3/8
        """
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
        """
        Parse a fraction string and enter it.
        
        Formats supported:
            "3/4"       - Simple fraction
            "2-3/8"     - Mixed number with hyphen
            "2 3/8"     - Mixed number with space
            "1-1/2"     - Mixed number
            "4'6-1/2\"" - Feet and inches
            "4' 6\""    - Feet and inches
            "0.875"     - Decimal (passthrough)
            
        Returns:
            Decimal value
        """
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
        """
        Convert decimal to fraction.
        
        Args:
            decimal: Value to convert (default: current display)
            max_denom: Maximum denominator (default: self.precision)
            
        Returns:
            FractionResult with numerator, denominator, whole part
            
        Example:
            >>> calc.to_fraction(0.875)
            FractionResult(decimal=0.875, numerator=7, denominator=8)
            
            >>> calc.to_fraction(2.375)
            FractionResult(decimal=2.375, whole=2, numerator=3, denominator=8)
        """
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
        """
        Enter measurement in feet and inches.
        
        Args:
            feet: Feet
            inches: Whole inches
            frac_num: Fractional inch numerator
            frac_denom: Fractional inch denominator
            
        Example:
            calc.feet_inches(4, 6, 1, 2)  # 4' 6-1/2"
        """
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


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Run fraction calculator tests."""
    calc = FractionCalculator()
    
    tests_passed = 0
    tests_failed = 0
    
    def test(name: str, expected, actual, tolerance: float = 0.001):
        nonlocal tests_passed, tests_failed
        if isinstance(expected, float):
            if abs(expected - actual) < tolerance:
                print(f"  ✓ {name}")
                tests_passed += 1
            else:
                print(f"  ✗ {name}: expected {expected}, got {actual}")
                tests_failed += 1
        else:
            if expected == actual:
                print(f"  ✓ {name}")
                tests_passed += 1
            else:
                print(f"  ✗ {name}: expected {expected}, got {actual}")
                tests_failed += 1
    
    print("\n=== Fraction Calculator Tests ===\n")
    
    # -------------------------------------------------------------------------
    # Fraction Input
    # -------------------------------------------------------------------------
    print("Fraction input:")
    
    calc.fraction(3, 4)
    test("3/4 = 0.75", 0.75, calc.value)
    
    calc.fraction(7, 8)
    test("7/8 = 0.875", 0.875, calc.value)
    
    calc.mixed_number(2, 3, 8)
    test("2-3/8 = 2.375", 2.375, calc.value)
    
    calc.mixed_number(-1, 1, 2)
    test("-1-1/2 = -1.5", -1.5, calc.value)
    
    # -------------------------------------------------------------------------
    # Fraction Parsing
    # -------------------------------------------------------------------------
    print("\nFraction parsing:")
    
    test("parse '3/4'", 0.75, calc.parse_fraction("3/4"))
    test("parse '7/8'", 0.875, calc.parse_fraction("7/8"))
    test("parse '2-3/8'", 2.375, calc.parse_fraction("2-3/8"))
    test("parse '2 3/8'", 2.375, calc.parse_fraction("2 3/8"))
    test("parse '1-1/2'", 1.5, calc.parse_fraction("1-1/2"))
    
    # Feet-inches
    test("parse 4'6\"", 54.0, calc.parse_fraction("4'6\""))
    test("parse 4' 6-1/2\"", 54.5, calc.parse_fraction("4' 6-1/2\""))
    
    # -------------------------------------------------------------------------
    # Decimal to Fraction
    # -------------------------------------------------------------------------
    print("\nDecimal to fraction:")
    
    result = calc.to_fraction(0.875)
    test("0.875 → 7/8", "7/8", str(result))
    
    result = calc.to_fraction(0.75)
    test("0.75 → 3/4", "3/4", str(result))
    
    result = calc.to_fraction(0.5)
    test("0.5 → 1/2", "1/2", str(result))
    
    result = calc.to_fraction(0.625)
    test("0.625 → 5/8", "5/8", str(result))
    
    result = calc.to_fraction(2.375)
    test("2.375 → 2-3/8", "2-3/8", str(result))
    
    result = calc.to_fraction(0.0625)
    test("0.0625 → 1/16", "1/16", str(result))
    
    result = calc.to_fraction(0.03125)
    calc.set_precision(32)
    result = calc.to_fraction(0.03125)
    test("0.03125 → 1/32 (32nds mode)", "1/32", str(result))
    calc.set_precision(16)
    
    # -------------------------------------------------------------------------
    # Fraction Arithmetic
    # -------------------------------------------------------------------------
    print("\nFraction arithmetic:")
    
    num, denom = calc.add_fractions(1, 2, 1, 4)
    test("1/2 + 1/4 = 3/4", (3, 4), (num, denom))
    
    num, denom = calc.add_fractions(3, 8, 1, 4)
    test("3/8 + 1/4 = 5/8", (5, 8), (num, denom))
    
    num, denom = calc.subtract_fractions(7, 8, 1, 4)
    test("7/8 - 1/4 = 5/8", (5, 8), (num, denom))
    
    num, denom = calc.multiply_fractions(1, 2, 3, 4)
    test("1/2 × 3/4 = 3/8", (3, 8), (num, denom))
    
    num, denom = calc.divide_fractions(1, 2, 1, 4)
    test("1/2 ÷ 1/4 = 2/1", (2, 1), (num, denom))
    
    # -------------------------------------------------------------------------
    # Reduce
    # -------------------------------------------------------------------------
    print("\nReduce fractions:")
    
    test("4/8 → 1/2", (1, 2), calc.reduce(4, 8))
    test("6/8 → 3/4", (3, 4), calc.reduce(6, 8))
    test("8/32 → 1/4", (1, 4), calc.reduce(8, 32))
    
    # -------------------------------------------------------------------------
    # Calculator operations with fractions
    # -------------------------------------------------------------------------
    print("\nCalculator operations:")
    
    calc.clear()
    calc.fraction(3, 4).operation('+').fraction(1, 8)
    result = calc.equals()
    test("3/4 + 1/8 = 0.875", 0.875, result)
    test("displays as 7/8", "7/8", calc.display_fraction)
    
    calc.clear()
    calc.fraction(1, 2).operation('*').fraction(3, 4)
    result = calc.equals()
    test("1/2 × 3/4 = 0.375", 0.375, result)
    test("displays as 3/8", "3/8", calc.display_fraction)
    
    # -------------------------------------------------------------------------
    # Feet/Inches
    # -------------------------------------------------------------------------
    print("\nFeet/Inches:")
    
    calc.feet_inches(4, 6, 1, 2)
    test("4' 6-1/2\" = 54.5", 54.5, calc.value)
    test("to_feet_inches(54.5)", "4' 6-1/2\"", calc.to_feet_inches(54.5))
    test("to_feet_inches(30)", "2' 6\"", calc.to_feet_inches(30))
    
    # -------------------------------------------------------------------------
    # Edge cases
    # -------------------------------------------------------------------------
    print("\nEdge cases:")
    
    result = calc.to_fraction(1.0)
    test("1.0 → 1", "1", str(result))
    
    result = calc.to_fraction(0.0)
    test("0.0 → 0", "0", str(result))
    
    result = calc.to_fraction(3.0)
    test("3.0 → 3", "3", str(result))
    
    print(f"\n=== Results: {tests_passed} passed, {tests_failed} failed ===")
    
    return tests_failed == 0


# =============================================================================
# CLI
# =============================================================================

def calculator_repl():
    """Interactive fraction calculator."""
    calc = FractionCalculator()
    
    print("=" * 55)
    print("Fraction Calculator - Luthier's ToolBox")
    print("=" * 55)
    print()
    print("Fraction input: 3/4, 2-3/8, 1 1/2, 4'6-1/2\"")
    print("Precision: 8ths, 16ths, 32nds, 64ths (default: 16ths)")
    print("Commands: dec (decimal mode), frac (fraction mode)")
    print("          p8, p16, p32, p64 (set precision)")
    print("          q (quit)")
    print()
    
    while True:
        mode = "frac" if calc._fraction_mode else "dec"
        prec = calc.precision
        
        try:
            user_input = input(f"[{calc.display}] ({mode}/{prec}) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        cmd = user_input.lower()
        
        if cmd in ('q', 'quit', 'exit'):
            break
        elif cmd in ('c', 'clear'):
            calc.clear()
        elif cmd in ('dec', 'decimal'):
            calc.set_fraction_mode(False)
            print(f"  Decimal mode: {calc.display_decimal}")
        elif cmd in ('frac', 'fraction'):
            calc.set_fraction_mode(True)
            print(f"  Fraction mode: {calc.display_fraction}")
        elif cmd == 'p8':
            calc.set_precision(8)
            print("  Precision: 8ths")
        elif cmd == 'p16':
            calc.set_precision(16)
            print("  Precision: 16ths")
        elif cmd == 'p32':
            calc.set_precision(32)
            print("  Precision: 32nds")
        elif cmd == 'p64':
            calc.set_precision(64)
            print("  Precision: 64ths")
        elif cmd == 'ft':
            print(f"  {calc.to_feet_inches()}")
        elif '/' in user_input or "'" in user_input:
            # Fraction or feet-inches input
            value = calc.parse_fraction(user_input)
            if calc.error:
                print(f"  Error: {calc.error}")
            else:
                print(f"  = {value} ({calc.display_fraction})")
        else:
            # Try as expression or number
            try:
                if any(op in user_input for op in ['+', '-', '*', '/']):
                    result = calc.evaluate(user_input)
                else:
                    result = float(user_input)
                    calc.state.display = calc._format_result(result)
                    calc._update_fraction_display(result)
                
                if calc.error:
                    print(f"  Error: {calc.error}")
                else:
                    print(f"  = {calc.display}")
            except ValueError:
                print(f"  Cannot parse: {user_input}")


# =============================================================================
# MAIN  
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            run_tests()
        else:
            # Convert argument to fraction
            calc = FractionCalculator()
            arg = ' '.join(sys.argv[1:])
            
            # Check if it's a decimal to convert
            try:
                val = float(arg)
                result = calc.to_fraction(val)
                print(f"{val} = {result}")
            except ValueError:
                # Try parsing as fraction
                val = calc.parse_fraction(arg)
                if calc.error:
                    print(f"Error: {calc.error}")
                else:
                    print(f"{arg} = {val}")
    else:
        calculator_repl()
