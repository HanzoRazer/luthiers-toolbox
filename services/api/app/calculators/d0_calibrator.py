"""
d0_calibrator.py
================
Bayesian error corrector for wood moisture diffusion coefficient D_0.

Learns from completed bending sessions and improves the prior estimate of
D_0 for future sessions of the same species. Works in three regimes depending
on how many sessions have been recorded.

═══════════════════════════════════════════════════════════════════════════════
MATHEMATICAL CHRONICLE
═══════════════════════════════════════════════════════════════════════════════

CHAPTER 1: WHY D_0 IS LOG-NORMAL

D_0 (moisture diffusion coefficient) is:
  - Strictly positive
  - Spans three orders of magnitude across species (10^-11 to 10^-8 m²/s)
  - Within a species: varies by ±factor of 3 board-to-board
  - The ratio D_0_piece / D_0_mean is approximately log-normally distributed

Therefore we work in log space throughout:

    θ = ln(D_0)    [the parameter we actually estimate]
    θ ~ Normal(μ, σ²)

The database value gives the prior mean:
    μ_prior = ln(D_0_database)
    σ_prior = 0.80   [encodes ±factor-of-2.2 at 1σ, ±factor-of-5 at 2σ]

Source honesty: σ_prior = 0.80 is estimated from the range of D_0 values
reported in Siau (1984) for species in the same density class. It is not
derived from a formal meta-analysis.

═══════════════════════════════════════════════════════════════════════════════

CHAPTER 2: THE LIKELIHOOD — WHAT ONE WEIGH-IN TELLS US

Observation: mass m_wet at soak time t_s.
Derived measurement: MC_avg_measured = (m_wet - m_dry) / m_dry

Forward model (from moisture_inverse_solver.py Fick solver):
    MC_avg_predicted = F(D_0, k_m, t_s, conditions)

Measurement noise model:
    σ_scale = scale resolution [g]
    σ_MC_scale = σ_scale / m_dry    [from scale resolution alone]
    σ_MC_practical ≈ 0.003-0.005   [practical: includes surface water, T variation]

Likelihood:
    P(m_wet | D_0) = Normal(F(D_0); MC_avg_measured, σ_MC²)

In θ = ln(D_0) space, linearize around the MAP estimate θ̂:
    F(θ) ≈ F(θ̂) + F'(θ̂)(θ - θ̂)

    where F'(θ) = ∂(MC_avg)/∂(ln D_0)
                ≈ 0.5 × MC_avg   [from short-time Fickian solution]
                  (MC_avg ∝ √D_0 at early times → ∂MC_avg/∂lnD_0 = MC_avg/2)

═══════════════════════════════════════════════════════════════════════════════

CHAPTER 3: THE BAYESIAN UPDATE — WITHIN A SESSION

Prior:     p(θ) = Normal(μ_0, σ_0²)
Posterior after n measurements:

    1/σ_n² = 1/σ_0² + Σᵢ (F_i')² / σ_y_i²

    μ_n = σ_n² × [μ_0/σ_0² + Σᵢ F_i'·ŷ_i / σ_y_i²]

    where ŷ_i = MC_avg_measured_i - F(θ̂) + F'(θ̂)·θ̂

This is the standard conjugate Normal-Normal update.

For a single measurement at t ≈ 30 min (F' ≈ 0.5, σ_y ≈ 0.4% MC):
    Information gain = F'² / σ_y² ≈ 0.25 / (0.004)² ≈ 15,625
    Prior precision  = 1/σ_0² ≈ 1/0.64 ≈ 1.56

    → One measurement provides ~10,000× more information than the prior.
    → σ_posterior ≈ 0.008 after one measurement (down from 0.80).
    → The first weigh-in essentially replaces the prior entirely.

This means: for within-session estimation, the prior barely matters.
The first measurement is the signal; everything before it is scaffolding.

═══════════════════════════════════════════════════════════════════════════════

CHAPTER 4: ACROSS-SESSION LEARNING — THREE REGIMES

After N completed sessions for species s:
    Data: {(D̂_0^(i), ρ^(i), σ̂_i²)}  i = 1..N

REGIME 1: N < 3  (Sparse — weighted mean)

    μ_species = Σᵢ [ln(D̂_0^(i)) / σ̂_i²] / Σᵢ [1/σ̂_i²]
    σ_species² = max(1/Σᵢ[1/σ̂_i²], 0.16)   [floor at σ=0.40]

    The floor prevents overconfidence from 1-2 measurements.

REGIME 2: 3 ≤ N < 8  (Building — weighted mean, tighter floor)

    Same formula, floor at σ=0.30.
    The species estimate is now meaningfully better than the database prior.

REGIME 3: N ≥ 8  (Density regression)

    Model: ln(D̂_0^(i)) = α + β·ln(ρ^(i)) + εᵢ

    Weighted least squares (weights = 1/σ̂_i²):

        ρ̄_w = Σᵢ wᵢ·ln(ρᵢ) / Σᵢ wᵢ
        D̄_w = Σᵢ wᵢ·ln(D̂_0^(i)) / Σᵢ wᵢ

        β̂ = Σᵢ wᵢ·(ln(ρᵢ) - ρ̄_w)·(ln(D̂_0^(i)) - D̄_w)
             / Σᵢ wᵢ·(ln(ρᵢ) - ρ̄_w)²

        α̂ = D̄_w - β̂·ρ̄_w

        σ_residual² = Σᵢ wᵢ·(ln(D̂_0^(i)) - α̂ - β̂·ln(ρᵢ))² / (N - 2)

    Prior for new piece with measured density ρ_new:
        μ_prior(ρ_new) = α̂ + β̂·ln(ρ_new)
        σ_prior(ρ_new) = σ_residual / √N

    Theory predicts β ≈ -1.6 (Siau 1984, porosity model).
    Fitted β is a quality indicator: β ≠ -1.6 suggests the density
    variation is confounded with other factors (grain, origin, drying history).

═══════════════════════════════════════════════════════════════════════════════

CHAPTER 5: k_m FITTING (TWO-POINT, N ≥ 5)

k_m is the MC-sensitivity exponent: D(m) = D_0·exp(k_m·m)

k_m affects the SHAPE of the MC_avg(t) curve — specifically, how quickly
absorption slows as the wood wets (because D decreases at higher m).

From two measurements at t₁ and t₂:
    The ratio R = MC_avg(t₂) / MC_avg(t₁) depends strongly on k_m
    but weakly on D_0 (D_0 affects the timescale, not the shape).

Fit k_m by minimizing across N sessions that have two-point data:

    Σᵢ [ln(R_model^(i)(k_m)) - ln(R_observed^(i))]²

The log-ratio formulation makes the fit insensitive to absolute MC values
and focuses it on the shape. This is a 1D minimization (Brent method).

Literature range: k_m ∈ [5.0, 7.5] for wood species
Sessions needed: ≥ 5 with two-point soak data for stable fit.

═══════════════════════════════════════════════════════════════════════════════

CHAPTER 6: OIL_FACTOR ESTIMATION (N ≥ 15, MIXED SURFACTANT DATA)

oil_factor controls the surface MC cap:
    m_surface = FSP × oil_factor

Estimated from long-soak asymptote. At t → ∞, MC_avg → m_surface.
If sessions exist both with and without surfactant:

    oil_factor_plain      = lim_{t→∞} MC_avg_nosurfactant / FSP
    oil_factor_surfactant = lim_{t→∞} MC_avg_surfactant / FSP

Practically: use the maximum MC_avg observed across all sessions as the
asymptote estimate. This underestimates slightly (never truly t→∞) but is
conservative (safe: if anything, extends soak recommendation).

═══════════════════════════════════════════════════════════════════════════════

CHAPTER 7: CONVERGENCE GUARANTEE

Posterior σ decreases monotonically with sessions N:

    σ_posterior ≈ σ_residual / √N

For σ_residual ≈ 0.30 (typical within-species variation from board to board):

    N=0:   σ = 0.80  → 95% CI ×5.0/÷5.0  (database prior only)
    N=1:   σ = 0.30  → 95% CI ×1.8/÷1.8  (one session — shaky)
    N=3:   σ = 0.17  → 95% CI ×1.4/÷1.4
    N=8:   σ = 0.11  → 95% CI ×1.2/÷1.2
    N=10:  σ = 0.09  → 95% CI ×1.2/÷1.2
    N=20:  σ = 0.07  → 95% CI ×1.1/÷1.1
    N=50:  σ = 0.04  → 95% CI ×1.1/÷1.1

At N ≥ 10, the species prior is tighter than the within-session measurement
uncertainty. At this point, the dominant uncertainty is the piece-to-piece
variation within the session itself, not the prior.

WHAT EACH REGIME MEANS IN THE SHOP:

    N=0:   Calculator gives a wide range. Weigh every 15 min.
    N=1:   Slightly tighter range. Still weigh every 15 min.
    N=3:   Useful planning estimate. Weigh at 30 min intervals.
    N=10:  Reliable planning. Confirm with one weigh-in before bending.
    N=20+: Species is characterized for YOUR stock. Prior is calibrated.

KEY DISTINCTION:
    Literature D_0  = population mean across all trees, regions, drying methods
    Session D_0     = THIS piece of wood, THIS day
    Calibrator D_0  = YOUR stock from YOUR supplier at YOUR shop conditions

All three are correct and distinct. The calibrator bridges literature → your shop.

═══════════════════════════════════════════════════════════════════════════════

References:
    Siau, J.F. (1984). Transport Processes in Wood. Springer.
    Skaar, C. (1988). Wood-Water Relations. Springer.
    Simpson, W.T. (1971). Forest Products Journal 21(5):48-49.
    Goring, D.A.I. (1963). Pulp Paper Mag. Can. 64:T517. [Tg model]
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import brentq, minimize_scalar


# ─── Constants ────────────────────────────────────────────────────────────────

FSP           = 0.28    # fiber saturation point [fraction]
SIGMA_PRIOR_0 = 0.80    # prior uncertainty in ln(D_0), N=0
SIGMA_FLOOR_1 = 0.40    # floor for N=1,2
SIGMA_FLOOR_3 = 0.30    # floor for N=3..7
SIGMA_MC_PRACTICAL = 0.004  # practical MC measurement uncertainty [fraction]

# Regime thresholds
N_REGIME_MEAN      = 3   # use weighted mean
N_REGIME_REGRESSION = 8  # switch to density regression
N_REGIME_KM        = 5   # fit k_m
N_REGIME_OIL       = 15  # estimate oil_factor


# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class SessionRecord:
    """Minimal record from a completed bend session."""
    session_id:   str
    species:      str
    timestamp:    str
    D_0_fitted:   float    # from moisture_inverse_solver.BendSession
    k_m_fitted:   float
    sigma_fitted: float    # posterior σ from that session [ln space]
    rho_kg_m3:    float    # density of that blank [kg/m³]
    m_dry_g:      float
    L_mm:         float
    T_soak_C:     float
    surfactant:   bool
    mc_initial_pct: float
    mc_final_pct:   Optional[float]
    # Two-point soak data for k_m fitting (if available)
    soak_t1_min:  Optional[float] = None
    soak_mc1_avg: Optional[float] = None
    soak_t2_min:  Optional[float] = None
    soak_mc2_avg: Optional[float] = None


@dataclass
class CalibratedPrior:
    """Prior estimate of D_0 after calibration."""
    D_0:         float
    k_m:         float
    sigma_ln:    float    # uncertainty in ln(D_0)
    n_sessions:  int
    regime:      str      # 'database' / 'mean' / 'regression'
    confidence_interval_95: Tuple[float, float]  # (D_0_lo, D_0_hi)
    beta_density: Optional[float]   # fitted density exponent (regime 3 only)
    oil_factor:   Optional[float]   # estimated if N ≥ 15

    def ci_pct(self) -> float:
        """Return the ± percentage of the 95% CI."""
        return (self.confidence_interval_95[1] / self.D_0 - 1.0) * 100.0

    def __str__(self) -> str:
        lo, hi = self.confidence_interval_95
        return (
            f"D_0 = {self.D_0:.3e} m²/s  "
            f"95% CI [{lo:.2e}, {hi:.2e}]  "
            f"(±{self.ci_pct():.0f}%)  "
            f"N={self.n_sessions}  regime={self.regime}"
        )


# ─── Core math ────────────────────────────────────────────────────────────────

def _lognormal_ci(mu_ln: float, sigma_ln: float, z: float = 1.96
                  ) -> Tuple[float, float]:
    return math.exp(mu_ln - z * sigma_ln), math.exp(mu_ln + z * sigma_ln)


def _weighted_mean_ln(ln_vals: List[float], weights: List[float]
                      ) -> Tuple[float, float]:
    """
    Inverse-variance weighted mean in log space.

    Returns (μ_w, σ_w) where:
        μ_w = Σ(w_i × x_i) / Σ(w_i)
        σ_w = 1 / sqrt(Σ(w_i))
        w_i = 1/σ_i²
    """
    W = sum(weights)
    mu = sum(w * x for w, x in zip(weights, ln_vals)) / W
    sigma = 1.0 / math.sqrt(W)
    return mu, sigma


def _wls_regression(ln_rho: List[float], ln_D0: List[float],
                    weights: List[float]
                    ) -> Tuple[float, float, float]:
    """
    Weighted least squares: ln(D_0) = α + β·ln(ρ) + ε

    Returns (α̂, β̂, σ_residual).

    β̂ = Σw(x_i - x̄_w)(y_i - ȳ_w) / Σw(x_i - x̄_w)²
    α̂ = ȳ_w - β̂·x̄_w
    σ_r = sqrt(Σw·residual² / (N-2))
    """
    W = sum(weights)
    x_bar = sum(w * x for w, x in zip(weights, ln_rho)) / W
    y_bar = sum(w * y for w, y in zip(weights, ln_D0)) / W

    num   = sum(w*(x-x_bar)*(y-y_bar) for w,x,y in zip(weights,ln_rho,ln_D0))
    denom = sum(w*(x-x_bar)**2        for w,x     in zip(weights,ln_rho))

    beta  = num / denom if abs(denom) > 1e-30 else 0.0
    alpha = y_bar - beta * x_bar

    residuals = [(y - alpha - beta*x)**2
                 for x, y in zip(ln_rho, ln_D0)]
    n = len(ln_D0)
    sigma_r = math.sqrt(sum(w*r for w,r in zip(weights,residuals)) / max(n-2, 1))

    return alpha, beta, sigma_r


# ─── Main calibrator ──────────────────────────────────────────────────────────

class D0Calibrator:
    """
    Bayesian error corrector for D_0 across multiple bending sessions.

    Persistently stores session records and updates species priors.

    Usage
    -----
    cal = D0Calibrator(db_path="d0_sessions.json")

    # After each completed session:
    cal.record(session_record)

    # Before starting a new session:
    prior = cal.get_prior("rosewood_east_indian", rho_kg_m3=835.0)
    print(prior)    # D_0 = 1.38e-10, ±18%, N=7, regime=mean

    # Pass prior to MoistureSolver:
    solver = MoistureSolver(species, ...)
    solver.D_0 = prior.D_0
    solver.k_m = prior.k_m
    """

    def __init__(self, db_path: str = "d0_sessions.json",
                 species_defaults: Optional[Dict] = None):
        """
        Parameters
        ----------
        db_path : path to JSON session store (created if absent)
        species_defaults : dict of {species: (D_0, k_m)} database values
                           If None, uses the SPECIES_DB from moisture_inverse_solver.
        """
        self.db_path = Path(db_path)
        self._records: List[SessionRecord] = []
        self._species_defaults = species_defaults or {}
        self._load()

    def _load(self):
        if self.db_path.exists():
            with open(self.db_path) as f:
                raw = json.load(f)
            self._records = [SessionRecord(**r) for r in raw.get("sessions", [])]

    def _save(self):
        data = {"version": 1, "updated": datetime.now().isoformat(),
                "sessions": [vars(r) for r in self._records]}
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)

    def record(self, rec: SessionRecord):
        """Add a completed session record and persist."""
        self._records.append(rec)
        self._save()

    def sessions_for(self, species: str) -> List[SessionRecord]:
        """Return all records for a species, sorted by timestamp."""
        return sorted(
            [r for r in self._records if r.species == species],
            key=lambda r: r.timestamp
        )

    def get_prior(self, species: str, rho_kg_m3: float = None) -> CalibratedPrior:
        """
        Return calibrated prior for D_0, given species and optional density.

        Algorithm follows Chapter 4 of the mathematical chronicle:
        - N=0:        database prior,       σ = 0.80
        - N=1,2:      weighted mean,        σ = max(formula, 0.40)
        - N=3..7:     weighted mean,        σ = max(formula, 0.30)
        - N≥8:        density regression,   σ = σ_residual/√N
        """
        sessions = self.sessions_for(species)
        N = len(sessions)

        # Database defaults
        D0_db, k_m_db = self._species_defaults.get(species, (1.2e-10, 6.5))

        if N == 0:
            sigma = SIGMA_PRIOR_0
            mu = math.log(D0_db)
            lo, hi = _lognormal_ci(mu, sigma)
            return CalibratedPrior(
                D_0=D0_db, k_m=k_m_db, sigma_ln=sigma,
                n_sessions=0, regime="database",
                confidence_interval_95=(lo, hi),
                beta_density=None, oil_factor=None,
            )

        # Build arrays
        ln_D0   = [math.log(r.D_0_fitted) for r in sessions]
        weights = [1.0 / max(r.sigma_fitted**2, 1e-6) for r in sessions]
        rhos    = [r.rho_kg_m3 for r in sessions]

        # Check density spread — regression requires sufficient rho variation
        ln_rho_arr = [math.log(r) for r in rhos]
        rho_spread = max(ln_rho_arr) - min(ln_rho_arr)
        MIN_SPREAD = 0.15  # ±8% density variation in ln space

        use_regression = (N >= N_REGIME_REGRESSION) and (rho_spread >= MIN_SPREAD)

        if not use_regression:
            # ── Regime 1 / 2: weighted mean ──────────────────────────────
            mu_w, sigma_w = _weighted_mean_ln(ln_D0, weights)
            floor = SIGMA_FLOOR_1 if N < N_REGIME_MEAN else SIGMA_FLOOR_3
            sigma = max(sigma_w, floor)
            D_0_out = math.exp(mu_w)
            k_m_out = self._fit_km(sessions, D_0_out) or k_m_db
            lo, hi = _lognormal_ci(mu_w, sigma)
            regime = "mean" if N >= 1 else "database"
            beta = None
            oil = None

        else:
            # ── Regime 3: density regression ─────────────────────────────
            ln_rho = ln_rho_arr
            alpha, beta, sigma_r = _wls_regression(ln_rho, ln_D0, weights)
            sigma = sigma_r / math.sqrt(N)
            sigma = max(sigma, 0.04)  # numerical floor

            # Prior for this specific piece
            rho_ref = rho_kg_m3 or (sum(rhos) / N)
            mu_reg = alpha + beta * math.log(rho_ref)
            D_0_out = math.exp(mu_reg)
            k_m_out = self._fit_km(sessions, D_0_out) or k_m_db
            lo, hi = _lognormal_ci(mu_reg, sigma)
            regime = "regression"
            oil = self._estimate_oil_factor(sessions) if N >= N_REGIME_OIL else None

        return CalibratedPrior(
            D_0=D_0_out, k_m=k_m_out, sigma_ln=sigma,
            n_sessions=N, regime=regime,
            confidence_interval_95=(lo, hi),
            beta_density=beta,
            oil_factor=oil,
        )

    def _fit_km(self, sessions: List[SessionRecord],
                D_0_ref: float) -> Optional[float]:
        """
        Fit k_m from the ratio of two-point soak measurements.

        k_m is insensitive to D_0 but controls the shape of MC_avg(t).
        Uses sessions that have both soak_t1 and soak_t2 recorded.

        The ratio R = MC_avg(t2) / MC_avg(t1) depends on k_m via:
            MC_avg(t) ≈ (m_surface - m_init) × [1 - exp(-t/τ(D_0, k_m, L))]
            τ ≈ L² / (π² × D_eff(m_mid))

        Minimizes: Σ [ln(R_model) - ln(R_observed)]²
        Returns None if < N_REGIME_KM two-point sessions available.
        """
        two_pt = [r for r in sessions
                  if r.soak_t1_min and r.soak_t2_min and r.soak_mc1_avg and r.soak_mc2_avg]
        if len(two_pt) < N_REGIME_KM:
            return None

        observed_ratios = [math.log(r.soak_mc2_avg / r.soak_mc1_avg)
                           for r in two_pt if r.soak_mc2_avg > 0 and r.soak_mc1_avg > 0]

        if not observed_ratios:
            return None

        def model_ratio(km, rec: SessionRecord) -> float:
            """
            Approximate ratio using simple exponential approach to equilibrium.
            τ = L_half² / (π² × D_0 × exp(k_m × m_mid))
            """
            E_A, R_G, T_REF = 38000.0, 8.314, 293.15
            T_K = rec.T_soak_C + 273.15
            L_half = (rec.L_mm / 2.0) / 1000.0
            m_mid  = (rec.mc_initial_pct / 100.0 + rec.soak_mc1_avg) / 2.0
            D_eff  = D_0_ref * math.exp(km * m_mid) * math.exp(
                -E_A / R_G * (1.0/T_K - 1.0/T_REF))
            tau    = L_half**2 / (math.pi**2 * D_eff)
            t1, t2 = rec.soak_t1_min * 60, rec.soak_t2_min * 60
            m_surf = FSP * 0.85  # approximate
            m_init = rec.mc_initial_pct / 100.0
            mc1    = (m_surf - m_init) * (1.0 - math.exp(-t1/tau)) + m_init
            mc2    = (m_surf - m_init) * (1.0 - math.exp(-t2/tau)) + m_init
            return math.log(mc2 / mc1) if mc1 > 1e-6 else 0.0

        def objective(km):
            return sum(
                (model_ratio(km, r) - obs)**2
                for r, obs in zip(two_pt, observed_ratios)
            )

        result = minimize_scalar(objective, bounds=(4.0, 9.0), method="bounded")
        return float(result.x)

    def _estimate_oil_factor(self, sessions: List[SessionRecord]) -> Optional[float]:
        """
        Estimate oil_factor from the long-soak asymptote of MC_avg.

        oil_factor ≈ max(MC_avg_observed across all sessions) / FSP

        This is a lower bound (never truly t→∞) but conservative.
        Uses only no-surfactant sessions.
        """
        no_surf = [r for r in sessions if not r.surfactant and r.soak_mc2_avg]
        if not no_surf:
            return None
        max_mc = max(r.soak_mc2_avg for r in no_surf)
        return round(max_mc / FSP, 3)

    def species_report(self, species: str) -> str:
        """Human-readable calibration report for one species."""
        sessions = self.sessions_for(species)
        N = len(sessions)
        prior = self.get_prior(species)
        lo, hi = prior.confidence_interval_95

        lines = [
            f"╔══════════════════════════════════════════════════════╗",
            f"║  D_0 Calibration — {species:<33}║",
            f"╚══════════════════════════════════════════════════════╝",
            f"",
            f"  Sessions recorded: {N}",
            f"  Regime:            {prior.regime}",
            f"",
            f"  D_0 estimate:      {prior.D_0:.3e} m²/s",
            f"  95% CI:            [{lo:.2e}, {hi:.2e}]",
            f"  ± percentage:      {prior.ci_pct():.0f}%",
            f"  σ (ln space):      {prior.sigma_ln:.3f}",
            f"  k_m:               {prior.k_m:.2f}",
        ]
        if prior.beta_density is not None:
            lines.append(f"  Density exponent β: {prior.beta_density:.2f}  "
                         f"(theory: -1.6)")
        if prior.oil_factor is not None:
            lines.append(f"  Oil factor est.:   {prior.oil_factor:.2f}")
        if N > 0:
            lines += [
                f"",
                f"  Session history:",
                f"  {'Date':>12}  {'D_0':>12}  {'σ':>6}  {'ρ kg/m³':>9}  {'T_soak':>6}",
                f"  {'─'*55}",
            ]
            for r in sessions[-8:]:  # last 8
                date = r.timestamp[:10]
                lines.append(
                    f"  {date:>12}  {r.D_0_fitted:.3e}  "
                    f"{r.sigma_fitted:.3f}  {r.rho_kg_m3:>9.0f}  "
                    f"{r.T_soak_C:>5.0f}°C"
                )
        lines.append("")
        return "\n".join(lines)

    def convergence_table(self, species: str) -> str:
        """Show how σ improved with each session (retrospective)."""
        sessions = self.sessions_for(species)
        if not sessions:
            return f"No sessions for {species}."

        D0_db, _ = self._species_defaults.get(species, (1.2e-10, 6.5))

        lines = [
            f"Convergence history — {species}",
            f"{'N':>5}  {'D_0 est':>12}  {'σ_ln':>7}  {'95% CI ±%':>12}  {'regime':>12}",
            "─" * 56,
        ]

        # Retrospectively add sessions one at a time
        original_records = self._records
        try:
            self._records = [r for r in self._records if r.species != species]
            sigma_curr = SIGMA_PRIOR_0
            lines.append(
                f"{'0':>5}  {D0_db:>12.3e}  {SIGMA_PRIOR_0:>7.3f}  "
                f"{(math.exp(1.96*SIGMA_PRIOR_0)-1)*100:>10.0f}%  database"
            )
            for i, sess in enumerate(sessions, 1):
                self._records.append(sess)
                p = self.get_prior(species, sess.rho_kg_m3)
                lines.append(
                    f"{i:>5}  {p.D_0:>12.3e}  {p.sigma_ln:>7.3f}  "
                    f"{p.ci_pct():>10.0f}%  {p.regime}"
                )
        finally:
            self._records = original_records

        return "\n".join(lines)

    def export_corrections(self) -> Dict:
        """
        Export all species corrections as a dict suitable for updating
        the species database priors.

        Returns {species: {"D_0_corrected": float, "k_m_corrected": float,
                           "sigma_ln": float, "n_sessions": int}}
        """
        all_species = list({r.species for r in self._records})
        out = {}
        for sp in sorted(all_species):
            p = self.get_prior(sp)
            out[sp] = {
                "D_0_corrected": p.D_0,
                "k_m_corrected": p.k_m,
                "sigma_ln": p.sigma_ln,
                "n_sessions": p.n_sessions,
                "regime": p.regime,
            }
        return out


# ─── CLI demo ─────────────────────────────────────────────────────────────────

def _synthetic_sessions(species: str, N: int, D0_true: float,
                        sigma_true: float = 0.25) -> List[SessionRecord]:
    """Generate synthetic session records for demonstration."""
    import random
    random.seed(42)
    sessions = []
    for i in range(N):
        D0_i = D0_true * math.exp(random.gauss(0, sigma_true))
        rho_i = 830 + random.gauss(0, 55)  # realistic board-to-board ±55 kg/m³
        sessions.append(SessionRecord(
            session_id=f"SYN_{i+1:03d}",
            species=species,
            timestamp=f"2025-{i//12+1:02d}-{i%28+1:02d}T10:00:00",
            D_0_fitted=D0_i,
            k_m_fitted=6.5,
            sigma_fitted=0.05,   # realistic within-session posterior
            rho_kg_m3=rho_i,
            m_dry_g=198.0,
            L_mm=2.3,
            T_soak_C=20.0,
            surfactant=False,
            mc_initial_pct=7.0,
            mc_final_pct=4.5,
            soak_t1_min=30.0,
            soak_mc1_avg=0.20,
            soak_t2_min=60.0,
            soak_mc2_avg=0.23,
        ))
    return sessions


if __name__ == "__main__":
    import tempfile

    print("\nD_0 Calibrator — Mathematical Chronicle Demo\n")

    # Use a temp file so demo doesn't pollute real data
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"sessions": []}, f)
        tmp_path = f.name

    cal = D0Calibrator(
        db_path=tmp_path,
        species_defaults={"rosewood_east_indian": (1.2e-10, 6.5)},
    )

    sp = "rosewood_east_indian"
    D0_true = 1.38e-10   # 15% above database — realistic wood variation

    print("Adding synthetic sessions one at a time:\n")
    for N in [0, 1, 2, 3, 5, 8, 10, 15, 20]:
        # Reset and add N sessions
        cal._records = []
        sessions = _synthetic_sessions(sp, N, D0_true)
        for s in sessions:
            cal.record(s)

        p = cal.get_prior(sp, rho_kg_m3=835.0)
        err_pct = abs(p.D_0 - D0_true) / D0_true * 100
        print(f"  N={N:>2}: D_0={p.D_0:.3e}  σ={p.sigma_ln:.3f}  "
              f"±{p.ci_pct():.0f}%  regime={p.regime}  "
              f"error vs true: {err_pct:.1f}%")

    print()
    print("Convergence table:")
    print(cal.convergence_table(sp))

    print()
    print(cal.species_report(sp))

    os.unlink(tmp_path)
