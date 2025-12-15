"""
Basic Calculator - Luthier's ToolBox

A clean, working calculator modeled after Google/Android calculators.
No frills, just solid math that works.

Operations:
    +  Addition
    -  Subtraction
    ×  Multiplication (*)
    ÷  Division (/)
    %  Percentage
    ±  Negate
    √  Square root
    C  Clear all
    CE Clear entry
    ⌫  Backspace

Usage:
    calc = BasicCalculator()
    calc.digit(5)
    calc.operation('+')
    calc.digit(3)
    result = calc.equals()  # 8.0

    # Or parse expression string:
    result = calc.evaluate("5 + 3")  # 8.0

Author: Luthier's ToolBox
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import math
import re


class Operation(Enum):
    """Basic calculator operations."""
    ADD = '+'
    SUBTRACT = '-'
    MULTIPLY = '*'
    DIVIDE = '/'
    NONE = ''


@dataclass
class CalculatorState:
    """
    Calculator internal state.
    
    Models a standard calculator's memory:
    - display: Current number being entered/displayed
    - accumulator: Running result from previous operations
    - pending_op: Operation waiting to be applied
    - just_evaluated: True if equals was just pressed (for chain operations)
    - error: Error message if something went wrong
    """
    display: str = '0'
    accumulator: Optional[float] = None
    pending_op: Operation = Operation.NONE
    just_evaluated: bool = False
    error: Optional[str] = None
    
    @property
    def display_value(self) -> float:
        """Get display as float."""
        try:
            return float(self.display)
        except ValueError:
            return 0.0


class BasicCalculator:
    """
    Basic calculator with Google/Android-style behavior.
    
    Example:
        >>> calc = BasicCalculator()
        >>> calc.digit(1)
        >>> calc.digit(2)
        >>> calc.operation('+')
        >>> calc.digit(3)
        >>> calc.equals()
        15.0
        
        >>> calc.clear()
        >>> calc.evaluate("100 / 4")
        25.0
    """
    
    MAX_DIGITS = 15  # Prevent overflow
    
    def __init__(self):
        self.state = CalculatorState()
        self._history: list[str] = []
    
    # =========================================================================
    # DIGIT ENTRY
    # =========================================================================
    
    def digit(self, d: int) -> 'BasicCalculator':
        """
        Enter a digit (0-9).
        
        Args:
            d: Single digit 0-9
            
        Returns:
            self for chaining
        """
        if not 0 <= d <= 9:
            return self
        
        self._clear_error()
        
        # After equals, start fresh number
        if self.state.just_evaluated:
            self.state.display = '0'
            self.state.just_evaluated = False
        
        # Handle display
        if self.state.display == '0' and d == 0:
            # Don't add leading zeros
            pass
        elif self.state.display == '0':
            # Replace leading zero
            self.state.display = str(d)
        elif len(self.state.display.replace('.', '').replace('-', '')) < self.MAX_DIGITS:
            # Append digit
            self.state.display += str(d)
        
        return self
    
    def decimal(self) -> 'BasicCalculator':
        """Add decimal point."""
        self._clear_error()
        
        if self.state.just_evaluated:
            self.state.display = '0.'
            self.state.just_evaluated = False
        elif '.' not in self.state.display:
            self.state.display += '.'
        
        return self
    
    def backspace(self) -> 'BasicCalculator':
        """Delete last digit."""
        self._clear_error()
        
        if self.state.just_evaluated:
            return self
        
        if len(self.state.display) > 1:
            self.state.display = self.state.display[:-1]
            # Handle case where we delete digit after decimal
            if self.state.display.endswith('.'):
                pass  # Keep the decimal
            elif self.state.display == '-':
                self.state.display = '0'
        else:
            self.state.display = '0'
        
        return self
    
    # =========================================================================
    # OPERATIONS
    # =========================================================================
    
    def operation(self, op: str) -> 'BasicCalculator':
        """
        Set pending operation (+, -, *, /).
        
        If there's already a pending operation, evaluate it first
        (chain calculation).
        """
        self._clear_error()
        
        # Map operator strings
        op_map = {
            '+': Operation.ADD,
            '-': Operation.SUBTRACT,
            '*': Operation.MULTIPLY,
            '×': Operation.MULTIPLY,
            '/': Operation.DIVIDE,
            '÷': Operation.DIVIDE,
        }
        
        new_op = op_map.get(op, Operation.NONE)
        if new_op == Operation.NONE:
            return self
        
        # If we have a pending operation, evaluate it first (chain)
        if self.state.pending_op != Operation.NONE and not self.state.just_evaluated:
            self._evaluate_pending()
        
        # Store current display as accumulator
        if self.state.accumulator is None or self.state.just_evaluated:
            self.state.accumulator = self.state.display_value
        
        self.state.pending_op = new_op
        self.state.just_evaluated = True  # Next digit starts new number
        
        return self
    
    def equals(self) -> float:
        """
        Evaluate pending operation and return result.
        
        Returns:
            The calculated result
        """
        self._clear_error()
        
        if self.state.pending_op == Operation.NONE:
            return self.state.display_value
        
        result = self._evaluate_pending()
        
        # Reset for next calculation
        self.state.pending_op = Operation.NONE
        self.state.accumulator = None
        self.state.just_evaluated = True
        
        return result
    
    def _evaluate_pending(self) -> float:
        """Evaluate the pending operation."""
        if self.state.accumulator is None:
            return self.state.display_value
        
        a = self.state.accumulator
        b = self.state.display_value
        
        result = 0.0
        
        if self.state.pending_op == Operation.ADD:
            result = a + b
        elif self.state.pending_op == Operation.SUBTRACT:
            result = a - b
        elif self.state.pending_op == Operation.MULTIPLY:
            result = a * b
        elif self.state.pending_op == Operation.DIVIDE:
            if b == 0:
                self.state.error = "Cannot divide by zero"
                result = 0.0
            else:
                result = a / b
        
        # Update state
        self.state.accumulator = result
        self.state.display = self._format_result(result)
        
        # Add to history
        op_symbol = {
            Operation.ADD: '+',
            Operation.SUBTRACT: '-',
            Operation.MULTIPLY: '×',
            Operation.DIVIDE: '÷',
        }.get(self.state.pending_op, '?')
        self._history.append(f"{a} {op_symbol} {b} = {result}")
        
        return result
    
    # =========================================================================
    # UNARY OPERATIONS
    # =========================================================================
    
    def negate(self) -> 'BasicCalculator':
        """Toggle positive/negative (±)."""
        self._clear_error()
        
        if self.state.display == '0':
            return self
        
        if self.state.display.startswith('-'):
            self.state.display = self.state.display[1:]
        else:
            self.state.display = '-' + self.state.display
        
        return self
    
    def percent(self) -> 'BasicCalculator':
        """
        Convert to percentage.
        
        Behavior depends on context:
        - Standalone: divide by 100
        - After operator: calculate percentage of accumulator
          e.g., 200 + 10% = 200 + 20 = 220
        """
        self._clear_error()
        
        value = self.state.display_value
        
        if self.state.pending_op != Operation.NONE and self.state.accumulator is not None:
            # Percentage of accumulator
            value = self.state.accumulator * (value / 100)
        else:
            # Simple percentage
            value = value / 100
        
        self.state.display = self._format_result(value)
        
        return self
    
    def sqrt(self) -> 'BasicCalculator':
        """Square root."""
        self._clear_error()
        
        value = self.state.display_value
        
        if value < 0:
            self.state.error = "Cannot take square root of negative number"
            return self
        
        result = math.sqrt(value)
        self.state.display = self._format_result(result)
        self.state.just_evaluated = True
        
        self._history.append(f"√{value} = {result}")
        
        return self
    
    # =========================================================================
    # CLEAR / RESET
    # =========================================================================
    
    def clear(self) -> 'BasicCalculator':
        """Clear all (C)."""
        self.state = CalculatorState()
        return self
    
    def clear_entry(self) -> 'BasicCalculator':
        """Clear current entry only (CE)."""
        self.state.display = '0'
        self._clear_error()
        return self
    
    def _clear_error(self):
        """Clear error state."""
        self.state.error = None
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _format_result(self, value: float) -> str:
        """Format a result for display."""
        # Handle special cases
        if math.isnan(value):
            return "Error"
        if math.isinf(value):
            return "Error"
        
        # Remove unnecessary decimal places
        if value == int(value) and abs(value) < 1e15:
            return str(int(value))
        
        # Scientific notation for very large/small numbers
        if abs(value) >= 1e15 or (abs(value) < 1e-10 and value != 0):
            return f"{value:.6e}"
        
        # Regular formatting, strip trailing zeros
        formatted = f"{value:.10f}".rstrip('0').rstrip('.')
        
        # Limit length
        if len(formatted) > self.MAX_DIGITS + 2:  # +2 for - and .
            formatted = f"{value:.6e}"
        
        return formatted
    
    # =========================================================================
    # EXPRESSION PARSING
    # =========================================================================
    
    def evaluate(self, expression: str) -> float:
        """
        Evaluate a simple expression string.
        
        Supports: +, -, *, /, parentheses
        
        Args:
            expression: Math expression like "5 + 3 * 2"
            
        Returns:
            Calculated result
            
        Example:
            >>> calc.evaluate("10 + 5 * 2")
            20.0
            >>> calc.evaluate("(10 + 5) * 2")
            30.0
        """
        self.clear()
        
        # Sanitize input
        expr = expression.strip()
        expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-')
        
        # Validate characters
        if not re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', expr):
            self.state.error = "Invalid characters in expression"
            return 0.0
        
        try:
            # Use Python's eval with restricted globals for safety
            # Only allow math operations, no builtins
            result = eval(expr, {"__builtins__": {}}, {})
            
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
        except Exception as e:
            self.state.error = f"Error: {str(e)}"
            return 0.0
    
    # =========================================================================
    # PROPERTIES
    # =========================================================================
    
    @property
    def display(self) -> str:
        """Get current display string."""
        if self.state.error:
            return "Error"
        return self.state.display
    
    @property
    def value(self) -> float:
        """Get current display as float."""
        return self.state.display_value
    
    @property
    def error(self) -> Optional[str]:
        """Get current error message, if any."""
        return self.state.error
    
    @property
    def history(self) -> list[str]:
        """Get calculation history."""
        return self._history.copy()
    
    def __repr__(self) -> str:
        return f"BasicCalculator(display='{self.display}')"


# =============================================================================
# CLI INTERFACE
# =============================================================================

def calculator_repl():
    """Interactive calculator REPL."""
    calc = BasicCalculator()
    
    print("=" * 40)
    print("Basic Calculator - Luthier's ToolBox")
    print("=" * 40)
    print("Commands: digits, +, -, *, /, =, c(lear), q(uit)")
    print("Or enter full expression: 5 + 3 * 2")
    print()
    
    while True:
        try:
            user_input = input(f"[{calc.display}] > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        if user_input in ('q', 'quit', 'exit'):
            print("Goodbye!")
            break
        
        if user_input in ('c', 'clear'):
            calc.clear()
            continue
        
        if user_input == 'ce':
            calc.clear_entry()
            continue
        
        if user_input == 'h' or user_input == 'history':
            for h in calc.history[-10:]:
                print(f"  {h}")
            continue
        
        # Check if it's a full expression
        if any(op in user_input for op in ['+', '-', '*', '/', '(']) and len(user_input) > 2:
            result = calc.evaluate(user_input)
            if calc.error:
                print(f"  Error: {calc.error}")
            else:
                print(f"  = {result}")
            continue
        
        # Single character/token processing
        for char in user_input:
            if char.isdigit():
                calc.digit(int(char))
            elif char == '.':
                calc.decimal()
            elif char in '+-*/':
                calc.operation(char)
            elif char == '=':
                result = calc.equals()
                print(f"  = {result}")
            elif char == '%':
                calc.percent()
            elif char == 'n':  # negate
                calc.negate()
            elif char == 'r':  # square root
                calc.sqrt()
                print(f"  = {calc.display}")


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Run basic calculator tests."""
    calc = BasicCalculator()
    
    tests_passed = 0
    tests_failed = 0
    
    def test(name: str, expected, actual):
        nonlocal tests_passed, tests_failed
        if abs(expected - actual) < 1e-10:
            print(f"  ✓ {name}")
            tests_passed += 1
        else:
            print(f"  ✗ {name}: expected {expected}, got {actual}")
            tests_failed += 1
    
    print("\n=== Basic Calculator Tests ===\n")
    
    # Basic operations
    print("Addition:")
    calc.clear()
    calc.digit(5).operation('+').digit(3)
    test("5 + 3 = 8", 8, calc.equals())
    
    print("\nSubtraction:")
    calc.clear()
    calc.digit(1).digit(0).operation('-').digit(4)
    test("10 - 4 = 6", 6, calc.equals())
    
    print("\nMultiplication:")
    calc.clear()
    calc.digit(6).operation('*').digit(7)
    test("6 × 7 = 42", 42, calc.equals())
    
    print("\nDivision:")
    calc.clear()
    calc.digit(2).digit(0).operation('/').digit(4)
    test("20 ÷ 4 = 5", 5, calc.equals())
    
    # Decimals
    print("\nDecimals:")
    calc.clear()
    calc.digit(3).decimal().digit(1).digit(4).operation('+').digit(2).decimal().digit(8).digit(6)
    test("3.14 + 2.86 = 6", 6, calc.equals())
    
    # Chained operations
    print("\nChained operations:")
    calc.clear()
    calc.digit(5).operation('+').digit(3).operation('*').digit(2)
    test("5 + 3 * 2 = 16 (left-to-right)", 16, calc.equals())
    
    # Expression parsing (respects precedence)
    print("\nExpression parsing:")
    test("evaluate('5 + 3 * 2') = 11", 11, calc.evaluate("5 + 3 * 2"))
    test("evaluate('(5 + 3) * 2') = 16", 16, calc.evaluate("(5 + 3) * 2"))
    test("evaluate('100 / 4 / 5') = 5", 5, calc.evaluate("100 / 4 / 5"))
    
    # Percentage
    print("\nPercentage:")
    calc.clear()
    calc.digit(2).digit(0).digit(0).percent()
    test("200% = 2", 2, calc.value)
    
    calc.clear()
    calc.digit(2).digit(0).digit(0).operation('+').digit(1).digit(0).percent()
    test("200 + 10% → 10% of 200 = 20", 20, calc.value)
    
    # Square root
    print("\nSquare root:")
    calc.clear()
    calc.digit(1).digit(6).sqrt()
    test("√16 = 4", 4, calc.value)
    
    calc.clear()
    calc.digit(2).sqrt()
    test("√2 ≈ 1.414", 1.41421356, calc.value)
    
    # Negation
    print("\nNegation:")
    calc.clear()
    calc.digit(5).negate()
    test("-5", -5, calc.value)
    calc.negate()
    test("back to 5", 5, calc.value)
    
    # Division by zero
    print("\nError handling:")
    calc.clear()
    calc.digit(5).operation('/').digit(0).equals()
    print(f"  ✓ 5/0 error: {calc.error}" if calc.error else "  ✗ No error for 5/0")
    
    print(f"\n=== Results: {tests_passed} passed, {tests_failed} failed ===")
    
    return tests_failed == 0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            run_tests()
        else:
            # Evaluate expression from command line
            calc = BasicCalculator()
            expr = ' '.join(sys.argv[1:])
            result = calc.evaluate(expr)
            if calc.error:
                print(f"Error: {calc.error}")
            else:
                print(result)
    else:
        calculator_repl()
