"""Financial Calculator - Luthier's ToolBox"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import math
from .scientific_calculator import LTBScientificCalculator


@dataclass
class TVMState:
    """Time Value of Money register state."""
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


class LTBFinancialCalculator(LTBScientificCalculator):
    """Financial calculator with TVM and business functions."""
    
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
    
    def clear_tvm(self) -> 'LTBFinancialCalculator':
        """Clear all TVM registers."""
        self.tvm = TVMState()
        return self
    
    def set_begin_mode(self, begin: bool = True) -> 'LTBFinancialCalculator':
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
        """Solve for Future Value."""
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
        """Solve for Present Value."""
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
        """Solve for Payment."""
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
        """Solve for Number of periods."""
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
        """Solve for Interest Rate using Newton-Raphson iteration."""
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
        """Generate full amortization schedule."""
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
        """Get amortization breakdown for specific period."""
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
        """Straight-line depreciation."""
        if life <= 0:
            raise ValueError("Life must be positive")
        
        annual = (cost - salvage) / life
        return round(annual, 2)
    
    def declining_balance(self, cost: float, salvage: float, life: int, 
                          period: int, factor: float = 2.0) -> float:
        """Declining balance depreciation (default double declining)."""
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
        """Sum-of-years-digits depreciation."""
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
        """Calculate selling price from cost and markup percentage."""
        price = cost * (1 + markup_percent / 100)
        return round(price, 2)
    
    def markup_percent(self, cost: float, price: float) -> float:
        """Calculate markup percentage from cost and price."""
        if cost == 0:
            raise ValueError("Cost cannot be zero")
        markup = ((price - cost) / cost) * 100
        return round(markup, 2)
    
    def margin(self, cost: float, margin_percent: float) -> float:
        """Calculate selling price from cost and margin percentage."""
        if margin_percent >= 100:
            raise ValueError("Margin cannot be >= 100%")
        price = cost / (1 - margin_percent / 100)
        return round(price, 2)
    
    def margin_percent(self, cost: float, price: float) -> float:
        """Calculate margin percentage from cost and price."""
        if price == 0:
            raise ValueError("Price cannot be zero")
        margin = ((price - cost) / price) * 100
        return round(margin, 2)
    
    def breakeven_units(self, fixed_costs: float, price: float, 
                        variable_cost: float) -> float:
        """Calculate break-even quantity."""
        contribution = price - variable_cost
        if contribution <= 0:
            raise ValueError("Price must exceed variable cost")
        
        units = fixed_costs / contribution
        return math.ceil(units)  # Round up - can't sell partial units
    
    def breakeven_revenue(self, fixed_costs: float, margin_percent: float) -> float:
        """Calculate break-even revenue."""
        if margin_percent <= 0:
            raise ValueError("Margin must be positive")
        
        revenue = fixed_costs / (margin_percent / 100)
        return round(revenue, 2)
    
    # =========================================================================
    # INTEREST CONVERSIONS
    # =========================================================================
    
    def nominal_to_effective(self, nominal_rate: float, 
                             compounds_per_year: int) -> float:
        """Convert nominal (APR) to effective annual rate (APY/EAR)."""
        r = nominal_rate / 100
        n = compounds_per_year
        effective = ((1 + r/n) ** n - 1) * 100
        return round(effective, 4)
    
    def effective_to_nominal(self, effective_rate: float,
                             compounds_per_year: int) -> float:
        """Convert effective annual rate (APY) to nominal rate (APR)."""
        ear = effective_rate / 100
        n = compounds_per_year
        nominal = n * ((1 + ear) ** (1/n) - 1) * 100
        return round(nominal, 4)


# Tests and CLI REPL extracted to financial_calculator_cli.py
# Backward-compatible re-exports:
from .financial_calculator_cli import run_tests, calculator_repl  # noqa: F401

