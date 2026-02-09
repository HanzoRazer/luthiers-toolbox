"""Fraction Calculator CLI & tests — Luthier's ToolBox."""

from .fraction_calculator import LTBFractionCalculator


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Run fraction calculator tests."""
    calc = LTBFractionCalculator()

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
    calc = LTBFractionCalculator()

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
