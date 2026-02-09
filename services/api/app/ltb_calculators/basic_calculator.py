"""Basic Calculator - Luthier's ToolBox"""

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
    """Calculator internal state."""
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


class LTBBasicCalculator:
    """Basic calculator with Google/Android-style behavior."""
    
    MAX_DIGITS = 15  # Prevent overflow
    
    def __init__(self):
        self.state = CalculatorState()
        self._history: list[str] = []
    
    # =========================================================================
    # DIGIT ENTRY
    # =========================================================================
    
    def digit(self, d: int) -> 'LTBBasicCalculator':
        """Enter a digit (0-9)."""
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
    
    def decimal(self) -> 'LTBBasicCalculator':
        """Add decimal point."""
        self._clear_error()
        
        if self.state.just_evaluated:
            self.state.display = '0.'
            self.state.just_evaluated = False
        elif '.' not in self.state.display:
            self.state.display += '.'
        
        return self
    
    def backspace(self) -> 'LTBBasicCalculator':
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
    
    def operation(self, op: str) -> 'LTBBasicCalculator':
        """Set pending operation (+, -, *, /)."""
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
        """Evaluate pending operation and return result."""
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
    
    def negate(self) -> 'LTBBasicCalculator':
        """Toggle positive/negative (±)."""
        self._clear_error()
        
        if self.state.display == '0':
            return self
        
        if self.state.display.startswith('-'):
            self.state.display = self.state.display[1:]
        else:
            self.state.display = '-' + self.state.display
        
        return self
    
    def percent(self) -> 'LTBBasicCalculator':
        """Convert to percentage."""
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
    
    def sqrt(self) -> 'LTBBasicCalculator':
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
    
    def clear(self) -> 'LTBBasicCalculator':
        """Clear all (C)."""
        self.state = CalculatorState()
        return self
    
    def clear_entry(self) -> 'LTBBasicCalculator':
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
        """Evaluate a simple expression string."""
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
        except (ValueError, TypeError, ArithmeticError) as e:  # WP-1: narrowed from except Exception
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



# =============================================================================
# TESTS
# =============================================================================



# =============================================================================
# MAIN
# =============================================================================

