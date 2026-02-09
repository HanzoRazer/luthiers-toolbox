"""Financial Calculator CLI REPL and inline tests (extracted from financial_calculator.py)."""
from __future__ import annotations

from .financial_calculator import LTBFinancialCalculator


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Run financial calculator tests."""
    calc = LTBFinancialCalculator()

    tests_passed = 0
    tests_failed = 0

    def test(name: str, expected: float, actual: float, tolerance: float = 0.01):
        nonlocal tests_passed, tests_failed
        if abs(expected - actual) < tolerance:
            print(f"  ✓ {name}")
            tests_passed += 1
        else:
            print(f"  ✗ {name}: expected {expected}, got {actual}")
            tests_failed += 1

    print("\n=== Financial Calculator Tests ===\n")

    # -------------------------------------------------------------------------
    # TVM: Mortgage Payment
    # -------------------------------------------------------------------------
    print("TVM - Mortgage Payment:")
    print("  $200,000 loan, 30 years, 6.5% APR")
    calc.clear_tvm()
    calc.n = 360            # 30 years * 12 months
    calc.i_y = 6.5 / 12     # Monthly rate
    calc.pv = 200000        # Loan amount
    calc.fv = 0             # Paid off
    pmt = calc.solve_pmt()
    test("Monthly payment = -$1,264.14", -1264.14, pmt, 0.01)

    # -------------------------------------------------------------------------
    # TVM: Investment Growth
    # -------------------------------------------------------------------------
    print("\nTVM - Investment Growth:")
    print("  $10,000 initial, 7% annual, 10 years")
    calc.clear_tvm()
    calc.n = 10
    calc.i_y = 7
    calc.pv = -10000        # Investment (outflow)
    calc.pmt = 0
    fv = calc.solve_fv()
    test("Future value = $19,671.51", 19671.51, fv, 0.01)

    # -------------------------------------------------------------------------
    # TVM: Solve for N
    # -------------------------------------------------------------------------
    print("\nTVM - Solve for N:")
    print("  How long to double money at 8%?")
    calc.clear_tvm()
    calc.i_y = 8
    calc.pv = -1000
    calc.pmt = 0
    calc.fv = 2000
    n = calc.solve_n()
    test("Years to double ≈ 9.01 (Rule of 72: 9)", 9.01, n, 0.1)

    # -------------------------------------------------------------------------
    # TVM: Solve for Rate
    # -------------------------------------------------------------------------
    print("\nTVM - Solve for Rate:")
    print("  $1,000 grows to $2,000 in 10 years, what rate?")
    calc.clear_tvm()
    calc.n = 10
    calc.pv = -1000
    calc.pmt = 0
    calc.fv = 2000
    rate = calc.solve_rate()
    test("Interest rate ≈ 7.18%", 7.18, rate, 0.1)

    # -------------------------------------------------------------------------
    # TVM: Car Loan
    # -------------------------------------------------------------------------
    print("\nTVM - Car Loan:")
    print("  $25,000 loan, 5 years, 4.5% APR")
    calc.clear_tvm()
    calc.n = 60             # 5 years * 12
    calc.i_y = 4.5 / 12     # Monthly
    calc.pv = 25000
    calc.fv = 0
    pmt = calc.solve_pmt()
    test("Monthly payment = -$465.85", -465.85, pmt, 0.01)

    # -------------------------------------------------------------------------
    # Amortization
    # -------------------------------------------------------------------------
    print("\nAmortization:")
    calc.clear_tvm()
    calc.n = 360
    calc.i_y = 6.5 / 12
    calc.pv = 200000
    calc.pmt = -1264.14

    row1 = calc.amortization_period(1)
    test("Month 1 interest = $1,083.33", 1083.33, row1.interest, 0.01)
    test("Month 1 principal = $180.81", 180.81, row1.principal, 0.01)

    total_int = calc.total_interest()
    test("Total interest ≈ $255,088", 255088, total_int, 100)

    # -------------------------------------------------------------------------
    # Depreciation
    # -------------------------------------------------------------------------
    print("\nDepreciation:")
    print("  $10,000 asset, $1,000 salvage, 5 year life")

    sl = calc.straight_line(10000, 1000, 5)
    test("Straight-line = $1,800/year", 1800, sl)

    ddb1 = calc.declining_balance(10000, 1000, 5, 1)
    test("DDB year 1 = $4,000", 4000, ddb1)

    ddb2 = calc.declining_balance(10000, 1000, 5, 2)
    test("DDB year 2 = $2,400", 2400, ddb2)

    syd1 = calc.sum_of_years(10000, 1000, 5, 1)
    test("SYD year 1 = $3,000", 3000, syd1)

    syd5 = calc.sum_of_years(10000, 1000, 5, 5)
    test("SYD year 5 = $600", 600, syd5)

    # -------------------------------------------------------------------------
    # Business Calculations
    # -------------------------------------------------------------------------
    print("\nBusiness Calculations:")

    price = calc.markup(100, 50)
    test("$100 cost + 50% markup = $150", 150, price)

    price = calc.margin(100, 40)
    test("$100 cost + 40% margin = $166.67", 166.67, price, 0.01)

    units = calc.breakeven_units(50000, 25, 10)
    test("Break-even: $50k fixed, $25 price, $10 var = 3,334 units", 3334, units)

    # -------------------------------------------------------------------------
    # Interest Conversions
    # -------------------------------------------------------------------------
    print("\nInterest Conversions:")

    apy = calc.nominal_to_effective(12, 12)  # 12% APR, monthly
    test("12% APR monthly → 12.68% APY", 12.68, apy, 0.01)

    apr = calc.effective_to_nominal(12.68, 12)
    test("12.68% APY → 12% APR", 12.0, apr, 0.01)

    print(f"\n=== Results: {tests_passed} passed, {tests_failed} failed ===")

    return tests_failed == 0


# =============================================================================
# CLI
# =============================================================================

def calculator_repl():
    """Interactive financial calculator."""
    calc = LTBFinancialCalculator()

    print("=" * 55)
    print("Financial Calculator - Luthier's ToolBox")
    print("=" * 55)
    print("TVM Registers: n, i_y (rate%), pv, pmt, fv")
    print("Solve: fv, pv, pmt, n, rate")
    print("Commands: show (display registers), clear, amort, q")
    print()
    print("Example: n=360, i_y=0.5417, pv=200000, fv=0, pmt")
    print()

    while True:
        try:
            user_input = input(f"[{calc.display}] fin> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ('q', 'quit', 'exit'):
            break

        elif cmd in ('c', 'clear'):
            calc.clear_tvm()
            print("  TVM registers cleared")

        elif cmd in ('show', 'status', 'regs'):
            print(f"  N   = {calc.n}")
            print(f"  I/Y = {calc.i_y}%")
            print(f"  PV  = {calc.pv}")
            print(f"  PMT = {calc.pmt}")
            print(f"  FV  = {calc.fv}")
            print(f"  Mode: {'BEGIN' if calc.tvm.begin_mode else 'END'}")

        elif cmd == 'amort':
            try:
                schedule = calc.amortization_schedule()[:12]  # First 12 periods
                print(f"  {'Per':>4} {'Payment':>10} {'Principal':>10} {'Interest':>10} {'Balance':>12}")
                print("  " + "-" * 50)
                for row in schedule:
                    print(f"  {row.period:4d} {row.payment:10.2f} {row.principal:10.2f} "
                          f"{row.interest:10.2f} {row.balance:12.2f}")
                if calc.n and calc.n > 12:
                    print(f"  ... ({int(calc.n) - 12} more periods)")
            except (ValueError, TypeError, ArithmeticError) as e:
                print(f"  Error: {e}")

        elif cmd in ('fv', 'solvefv'):
            try:
                result = calc.solve_fv()
                print(f"  FV = {result}")
            except (ValueError, TypeError, ArithmeticError) as e:
                print(f"  Error: {e}")

        elif cmd in ('pv', 'solvepv'):
            try:
                result = calc.solve_pv()
                print(f"  PV = {result}")
            except (ValueError, TypeError, ArithmeticError) as e:
                print(f"  Error: {e}")

        elif cmd in ('pmt', 'solvepmt'):
            try:
                result = calc.solve_pmt()
                print(f"  PMT = {result}")
            except (ValueError, TypeError, ArithmeticError) as e:
                print(f"  Error: {e}")

        elif cmd in ('n', 'solven'):
            try:
                result = calc.solve_n()
                print(f"  N = {result}")
            except (ValueError, TypeError, ArithmeticError) as e:
                print(f"  Error: {e}")

        elif cmd in ('rate', 'solverate', 'i_y'):
            try:
                result = calc.solve_rate()
                print(f"  I/Y = {result}%")
            except (ValueError, TypeError, ArithmeticError) as e:
                print(f"  Error: {e}")

        elif '=' in user_input:
            # Register assignment: n=360, i_y=6.5, etc.
            try:
                var, val = user_input.split('=', 1)
                var = var.strip().lower()
                val = float(val.strip())

                if var == 'n':
                    calc.n = val
                elif var in ('i_y', 'iy', 'i', 'rate'):
                    calc.i_y = val
                elif var == 'pv':
                    calc.pv = val
                elif var == 'pmt':
                    calc.pmt = val
                elif var == 'fv':
                    calc.fv = val
                else:
                    print(f"  Unknown register: {var}")
                    continue

                print(f"  {var.upper()} = {val}")
            except ValueError as e:
                print(f"  Error: {e}")

        else:
            # Try as expression
            result = calc.evaluate(user_input)
            if calc.error:
                print(f"  Error: {calc.error}")
            else:
                print(f"  = {result}")
