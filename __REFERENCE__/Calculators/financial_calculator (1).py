"""
Financial Calculator - Luthier's ToolBox

Time Value of Money (TVM) and business calculations.
Modeled after HP-12C / TI BA II Plus behavior.

TVM Variables:
    N       Number of periods
    I/Y     Interest rate per year (%)
    PV      Present Value
    PMT     Payment per period
    FV      Future Value

TVM Functions:
    solve_fv()      Future Value
    solve_pv()      Present Value  
    solve_pmt()     Payment
    solve_n()       Number of periods
    solve_rate()    Interest rate

Amortization:
    amortization_schedule()     Full payment schedule
    amortization_period()       Single period breakdown

Depreciation:
    straight_line()             SL depreciation
    declining_balance()         DB depreciation
    sum_of_years()              SYD depreciation

Business:
    markup()                    Cost to price
    margin()                    Price to margin
    breakeven()                 Units to break even

Usage:
    calc = FinancialCalculator()
    
    # Loan payment: $200,000 mortgage, 30 years, 6.5% APR
    calc.n = 360        # months
    calc.i_y = 6.5/12   # monthly rate
    calc.pv = 200000
    calc.fv = 0
    payment = calc.solve_pmt()  # -1264.14

Author: Luthier's ToolBox
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import math
from scientific_calculator import ScientificCalculator


@dataclass
class TVMState:
    """
    Time Value of Money register state.
    
    Sign convention (cash flow):
        Positive = money received (inflow)
        Negative = money paid out (outflow)
    """
    n: Optional[float] = None       # Number of periods
    i_y: Optional[float] = None     # Interest rate per period (%)
    pv: Optional[float] = None      # Present Value
    pmt: Optional[float] = None     # Payment per period
    fv: Optional[float] = None      # Future Value
    
    # Settings
    payments_per_year: int = 12     # For annualizing
    begin_mode: bool = False        # True = beginning of period (annuity due)


@dataclass 
class AmortizationRow:
    """Single row in amortization schedule."""
    period: int
    payment: float
    principal: float
    interest: float
    balance: float


class FinancialCalculator(ScientificCalculator):
    """
    Financial calculator with TVM and business functions.
    
    Example - Monthly mortgage payment:
        >>> calc = FinancialCalculator()
        >>> calc.n = 360          # 30 years * 12 months
        >>> calc.i_y = 6.5 / 12   # 6.5% APR / 12 months
        >>> calc.pv = 200000      # Loan amount
        >>> calc.fv = 0           # Paid off at end
        >>> calc.solve_pmt()
        -1264.14
        
    Example - Investment growth:
        >>> calc.clear_tvm()
        >>> calc.n = 10           # 10 years
        >>> calc.i_y = 7          # 7% annual return
        >>> calc.pv = -10000      # Initial investment (outflow)
        >>> calc.pmt = 0          # No additional contributions
        >>> calc.solve_fv()
        19671.51
    """
    
    def __init__(self):
        super().__init__()
        self.tvm = TVMState()
    
    # =========================================================================
    # TVM REGISTER ACCESS
    # =========================================================================
    
    @property
    def n(self) -> Optional[float]:
        """Number of periods."""
        return self.tvm.n
    
    @n.setter
    def n(self, value: float):
        self.tvm.n = value
    
    @property
    def i_y(self) -> Optional[float]:
        """Interest rate per period (%)."""
        return self.tvm.i_y
    
    @i_y.setter
    def i_y(self, value: float):
        self.tvm.i_y = value
    
    @property
    def pv(self) -> Optional[float]:
        """Present Value."""
        return self.tvm.pv
    
    @pv.setter
    def pv(self, value: float):
        self.tvm.pv = value
    
    @property
    def pmt(self) -> Optional[float]:
        """Payment per period."""
        return self.tvm.pmt
    
    @pmt.setter
    def pmt(self, value: float):
        self.tvm.pmt = value
    
    @property
    def fv(self) -> Optional[float]:
        """Future Value."""
        return self.tvm.fv
    
    @fv.setter
    def fv(self, value: float):
        self.tvm.fv = value
    
    def clear_tvm(self) -> 'FinancialCalculator':
        """Clear all TVM registers."""
        self.tvm = TVMState()
        return self
    
    def set_begin_mode(self, begin: bool = True) -> 'FinancialCalculator':
        """Set payment timing: begin (True) or end (False) of period."""
        self.tvm.begin_mode = begin
        return self
    
    # =========================================================================
    # TVM CORE CALCULATIONS
    # =========================================================================
    
    def _get_rate(self) -> float:
        """Get periodic interest rate as decimal."""
        if self.tvm.i_y is None:
            raise ValueError("Interest rate (I/Y) not set")
        return self.tvm.i_y / 100
    
    def _type_factor(self) -> int:
        """Return 1 for begin mode, 0 for end mode."""
        return 1 if self.tvm.begin_mode else 0
    
    def solve_fv(self) -> float:
        """
        Solve for Future Value.
        
        FV = -PV(1+i)^n - PMT * [(1+i)^n - 1] / i * (1 + i*type)
        
        Returns:
            Future Value
        """
        n = self.tvm.n
        i = self._get_rate()
        pv = self.tvm.pv or 0
        pmt = self.tvm.pmt or 0
        t = self._type_factor()
        
        if n is None:
            raise ValueError("N (periods) not set")
        
        if i == 0:
            # Simple case: no interest
            fv = -pv - pmt * n
        else:
            # Standard TVM formula
            compound = (1 + i) ** n
            fv = -pv * compound - pmt * ((compound - 1) / i) * (1 + i * t)
        
        self.tvm.fv = round(fv, 2)
        self.state.display = self._format_result(self.tvm.fv)
        self._history.append(f"FV = {self.tvm.fv}")
        return self.tvm.fv
    
    def solve_pv(self) -> float:
        """
        Solve for Present Value.
        
        PV = -FV / (1+i)^n - PMT * [1 - (1+i)^-n] / i * (1 + i*type)
        
        Returns:
            Present Value
        """
        n = self.tvm.n
        i = self._get_rate()
        pmt = self.tvm.pmt or 0
        fv = self.tvm.fv or 0
        t = self._type_factor()
        
        if n is None:
            raise ValueError("N (periods) not set")
        
        if i == 0:
            pv = -fv - pmt * n
        else:
            compound = (1 + i) ** n
            pv = -fv / compound - pmt * ((1 - (1 + i) ** -n) / i) * (1 + i * t)
        
        self.tvm.pv = round(pv, 2)
        self.state.display = self._format_result(self.tvm.pv)
        self._history.append(f"PV = {self.tvm.pv}")
        return self.tvm.pv
    
    def solve_pmt(self) -> float:
        """
        Solve for Payment.
        
        PMT = -(PV + FV / (1+i)^n) / ([1 - (1+i)^-n] / i * (1 + i*type))
        
        Returns:
            Payment per period
        """
        n = self.tvm.n
        i = self._get_rate()
        pv = self.tvm.pv or 0
        fv = self.tvm.fv or 0
        t = self._type_factor()
        
        if n is None:
            raise ValueError("N (periods) not set")
        
        if i == 0:
            if n == 0:
                raise ValueError("Cannot calculate PMT with N=0 and I/Y=0")
            pmt = -(pv + fv) / n
        else:
            compound = (1 + i) ** n
            annuity_factor = ((1 - (1 + i) ** -n) / i) * (1 + i * t)
            pmt = -(pv + fv / compound) / annuity_factor
        
        self.tvm.pmt = round(pmt, 2)
        self.state.display = self._format_result(self.tvm.pmt)
        self._history.append(f"PMT = {self.tvm.pmt}")
        return self.tvm.pmt
    
    def solve_n(self) -> float:
        """
        Solve for Number of periods.
        
        Uses iterative approach for complex cases.
        
        Returns:
            Number of periods
        """
        i = self._get_rate()
        pv = self.tvm.pv or 0
        pmt = self.tvm.pmt or 0
        fv = self.tvm.fv or 0
        t = self._type_factor()
        
        if i == 0:
            if pmt == 0:
                raise ValueError("Cannot solve N with PMT=0 and I/Y=0")
            n = -(pv + fv) / pmt
        else:
            # n = ln[(PMT*(1+i*t) - FV*i) / (PMT*(1+i*t) + PV*i)] / ln(1+i)
            pmt_adj = pmt * (1 + i * t)
            numerator = pmt_adj - fv * i
            denominator = pmt_adj + pv * i
            
            if denominator == 0 or numerator / denominator <= 0:
                raise ValueError("Cannot solve for N with given values")
            
            n = math.log(numerator / denominator) / math.log(1 + i)
        
        self.tvm.n = round(n, 2)
        self.state.display = self._format_result(self.tvm.n)
        self._history.append(f"N = {self.tvm.n}")
        return self.tvm.n
    
    def solve_rate(self, max_iterations: int = 100, tolerance: float = 1e-10) -> float:
        """
        Solve for Interest Rate using Newton-Raphson iteration.
        
        Returns:
            Interest rate per period (%)
        """
        n = self.tvm.n
        pv = self.tvm.pv or 0
        pmt = self.tvm.pmt or 0
        fv = self.tvm.fv or 0
        t = self._type_factor()
        
        if n is None:
            raise ValueError("N (periods) not set")
        
        # Initial guess
        i = 0.1  # 10%
        
        for _ in range(max_iterations):
            # f(i) = PV + PMT*[(1-(1+i)^-n)/i]*(1+i*t) + FV*(1+i)^-n = 0
            if i == 0:
                f = pv + pmt * n + fv
                df = pmt * n * (n - 1) / 2  # Approximate derivative
            else:
                compound = (1 + i) ** n
                annuity = ((1 - (1 + i) ** -n) / i) * (1 + i * t)
                f = pv + pmt * annuity + fv / compound
                
                # Derivative (approximate)
                h = 1e-8
                i_plus = i + h
                compound_plus = (1 + i_plus) ** n
                annuity_plus = ((1 - (1 + i_plus) ** -n) / i_plus) * (1 + i_plus * t)
                f_plus = pv + pmt * annuity_plus + fv / compound_plus
                df = (f_plus - f) / h
            
            if abs(df) < 1e-15:
                break
            
            i_new = i - f / df
            
            if abs(i_new - i) < tolerance:
                break
            
            i = i_new
            
            # Keep rate reasonable
            if i < -0.99:
                i = -0.99
            elif i > 10:
                i = 10
        
        self.tvm.i_y = round(i * 100, 6)
        self.state.display = self._format_result(self.tvm.i_y)
        self._history.append(f"I/Y = {self.tvm.i_y}%")
        return self.tvm.i_y
    
    # =========================================================================
    # AMORTIZATION
    # =========================================================================
    
    def amortization_schedule(self, periods: int = None) -> List[AmortizationRow]:
        """
        Generate full amortization schedule.
        
        Args:
            periods: Number of periods (defaults to N)
            
        Returns:
            List of AmortizationRow with payment breakdown
        """
        n = periods or int(self.tvm.n or 0)
        i = self._get_rate()
        balance = abs(self.tvm.pv or 0)
        pmt = abs(self.tvm.pmt or 0)
        
        schedule = []
        
        for period in range(1, n + 1):
            interest = balance * i
            principal = pmt - interest
            balance = max(0, balance - principal)
            
            schedule.append(AmortizationRow(
                period=period,
                payment=round(pmt, 2),
                principal=round(principal, 2),
                interest=round(interest, 2),
                balance=round(balance, 2)
            ))
            
            if balance <= 0:
                break
        
        return schedule
    
    def amortization_period(self, period: int) -> AmortizationRow:
        """
        Get amortization breakdown for specific period.
        
        Args:
            period: Period number (1-based)
            
        Returns:
            AmortizationRow for that period
        """
        schedule = self.amortization_schedule(period)
        if period <= len(schedule):
            return schedule[period - 1]
        raise ValueError(f"Period {period} exceeds schedule length")
    
    def total_interest(self) -> float:
        """Calculate total interest paid over life of loan."""
        schedule = self.amortization_schedule()
        total = sum(row.interest for row in schedule)
        return round(total, 2)
    
    def total_payments(self) -> float:
        """Calculate total of all payments."""
        schedule = self.amortization_schedule()
        total = sum(row.payment for row in schedule)
        return round(total, 2)
    
    # =========================================================================
    # DEPRECIATION
    # =========================================================================
    
    def straight_line(self, cost: float, salvage: float, life: int, period: int = None) -> float:
        """
        Straight-line depreciation.
        
        Args:
            cost: Initial asset cost
            salvage: Salvage value at end of life
            life: Useful life in periods
            period: Specific period (or None for annual amount)
            
        Returns:
            Depreciation amount
        """
        if life <= 0:
            raise ValueError("Life must be positive")
        
        annual = (cost - salvage) / life
        return round(annual, 2)
    
    def declining_balance(self, cost: float, salvage: float, life: int, 
                          period: int, factor: float = 2.0) -> float:
        """
        Declining balance depreciation (default double declining).
        
        Args:
            cost: Initial asset cost
            salvage: Salvage value
            life: Useful life in periods
            period: Period to calculate (1-based)
            factor: Declining factor (2.0 = double declining)
            
        Returns:
            Depreciation for specified period
        """
        if life <= 0 or period <= 0:
            raise ValueError("Life and period must be positive")
        
        rate = factor / life
        book_value = cost
        
        for p in range(1, period + 1):
            depreciation = book_value * rate
            
            # Don't depreciate below salvage
            if book_value - depreciation < salvage:
                depreciation = max(0, book_value - salvage)
            
            if p == period:
                return round(depreciation, 2)
            
            book_value -= depreciation
        
        return 0.0
    
    def sum_of_years(self, cost: float, salvage: float, life: int, period: int) -> float:
        """
        Sum-of-years-digits depreciation.
        
        Args:
            cost: Initial asset cost
            salvage: Salvage value
            life: Useful life in periods
            period: Period to calculate (1-based)
            
        Returns:
            Depreciation for specified period
        """
        if life <= 0 or period <= 0 or period > life:
            raise ValueError("Invalid life or period")
        
        # Sum of years = n(n+1)/2
        sum_years = life * (life + 1) / 2
        depreciable = cost - salvage
        
        # Remaining years at start of period
        remaining = life - period + 1
        depreciation = depreciable * (remaining / sum_years)
        
        return round(depreciation, 2)
    
    # =========================================================================
    # BUSINESS CALCULATIONS
    # =========================================================================
    
    def markup(self, cost: float, markup_percent: float) -> float:
        """
        Calculate selling price from cost and markup percentage.
        
        Markup% = (Price - Cost) / Cost * 100
        
        Args:
            cost: Product cost
            markup_percent: Markup as percentage of cost
            
        Returns:
            Selling price
        """
        price = cost * (1 + markup_percent / 100)
        return round(price, 2)
    
    def markup_percent(self, cost: float, price: float) -> float:
        """
        Calculate markup percentage from cost and price.
        
        Returns:
            Markup as percentage
        """
        if cost == 0:
            raise ValueError("Cost cannot be zero")
        markup = ((price - cost) / cost) * 100
        return round(markup, 2)
    
    def margin(self, cost: float, margin_percent: float) -> float:
        """
        Calculate selling price from cost and margin percentage.
        
        Margin% = (Price - Cost) / Price * 100
        
        Args:
            cost: Product cost
            margin_percent: Margin as percentage of price
            
        Returns:
            Selling price
        """
        if margin_percent >= 100:
            raise ValueError("Margin cannot be >= 100%")
        price = cost / (1 - margin_percent / 100)
        return round(price, 2)
    
    def margin_percent(self, cost: float, price: float) -> float:
        """
        Calculate margin percentage from cost and price.
        
        Returns:
            Margin as percentage
        """
        if price == 0:
            raise ValueError("Price cannot be zero")
        margin = ((price - cost) / price) * 100
        return round(margin, 2)
    
    def breakeven_units(self, fixed_costs: float, price: float, 
                        variable_cost: float) -> float:
        """
        Calculate break-even quantity.
        
        Args:
            fixed_costs: Total fixed costs
            price: Selling price per unit
            variable_cost: Variable cost per unit
            
        Returns:
            Number of units to break even
        """
        contribution = price - variable_cost
        if contribution <= 0:
            raise ValueError("Price must exceed variable cost")
        
        units = fixed_costs / contribution
        return math.ceil(units)  # Round up - can't sell partial units
    
    def breakeven_revenue(self, fixed_costs: float, margin_percent: float) -> float:
        """
        Calculate break-even revenue.
        
        Args:
            fixed_costs: Total fixed costs
            margin_percent: Gross margin percentage
            
        Returns:
            Revenue needed to break even
        """
        if margin_percent <= 0:
            raise ValueError("Margin must be positive")
        
        revenue = fixed_costs / (margin_percent / 100)
        return round(revenue, 2)
    
    # =========================================================================
    # INTEREST CONVERSIONS
    # =========================================================================
    
    def nominal_to_effective(self, nominal_rate: float, 
                             compounds_per_year: int) -> float:
        """
        Convert nominal (APR) to effective annual rate (APY/EAR).
        
        Args:
            nominal_rate: Nominal annual rate (%)
            compounds_per_year: Compounding periods per year
            
        Returns:
            Effective annual rate (%)
        """
        r = nominal_rate / 100
        n = compounds_per_year
        effective = ((1 + r/n) ** n - 1) * 100
        return round(effective, 4)
    
    def effective_to_nominal(self, effective_rate: float,
                             compounds_per_year: int) -> float:
        """
        Convert effective annual rate (APY) to nominal rate (APR).
        
        Args:
            effective_rate: Effective annual rate (%)
            compounds_per_year: Compounding periods per year
            
        Returns:
            Nominal annual rate (%)
        """
        ear = effective_rate / 100
        n = compounds_per_year
        nominal = n * ((1 + ear) ** (1/n) - 1) * 100
        return round(nominal, 4)


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Run financial calculator tests."""
    calc = FinancialCalculator()
    
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
    calc = FinancialCalculator()
    
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
            except Exception as e:
                print(f"  Error: {e}")
        
        elif cmd in ('fv', 'solvefv'):
            try:
                result = calc.solve_fv()
                print(f"  FV = {result}")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif cmd in ('pv', 'solvepv'):
            try:
                result = calc.solve_pv()
                print(f"  PV = {result}")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif cmd in ('pmt', 'solvepmt'):
            try:
                result = calc.solve_pmt()
                print(f"  PMT = {result}")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif cmd in ('n', 'solven'):
            try:
                result = calc.solve_n()
                print(f"  N = {result}")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif cmd in ('rate', 'solverate', 'i_y'):
            try:
                result = calc.solve_rate()
                print(f"  I/Y = {result}%")
            except Exception as e:
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


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        calculator_repl()
