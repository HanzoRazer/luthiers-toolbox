"""
tap_tone_pi.design — Plate thickness design and coupled-system analysis.

This module provides tools for determining optimal plate thickness using
orthotropic plate theory and coupled oscillator models.

Core Concepts:
    Orthotropic Plate:
        - E_L: Longitudinal (long-grain) modulus
        - E_C: Cross-grain modulus
        - R_anis = E_L/E_C: Orthotropic ratio (typically 10-20 for tonewoods)

    Coupled Oscillator Models:
        2-Oscillator (rigid back): Top + Air (closed-form)
        3-Oscillator (active back): Top + Air + Back (eigenvalue)

    Advanced Physics:
        Alpha/Beta formulation: Physical model for gamma = sqrt(alpha/beta)
        Rayleigh-Ritz: Variational method for accurate mode shapes
        Gamma Calibration: Derive γ from measured Chladni/box frequencies
        Inverse Solver: Find thickness for target frequencies

Modules:
    thickness_calculator: Orthotropic plate solver + 3-oscillator model
    coupled_2osc: 2-oscillator model for rigid back designs
    alpha_beta: Physical alpha/beta formulation for gamma calculation
    rayleigh_ritz: Rayleigh-Ritz variational mode solver
    gamma_calibration: Calibrate γ from measurement data
    inverse_solver: Inverse thickness optimization
    calibration: Body style calibration tables
"""

from .thickness_calculator import (
    plate_modal_frequency,
    thickness_for_target_frequency,
    helmholtz_frequency,
    chladni_to_box_frequency,
    box_to_chladni_frequency,
    coupled_eigenfrequencies,
    PlateThicknessResult,
    CoupledSystemResult,
    analyze_plate,
    analyze_coupled_system,
)

from .coupled_2osc import (
    coupled_2osc_eigenfrequencies,
    back_activity_ratio,
    minimum_back_thickness_for_rigid,
    Coupled2OscResult,
    analyze_coupled_2osc,
    format_2osc_report,
)

from .alpha_beta import (
    # Core alpha/beta functions
    compute_alpha,
    compute_beta,
    compute_gamma,
    # Component calculations
    plate_bending_stiffness,
    brace_stiffness,
    brace_mass,
    air_virtual_mass,
    air_virtual_mass_cavity,
    # High-level analysis
    AlphaBetaResult,
    analyze_alpha_beta,
    format_alpha_beta_report,
)

from .rayleigh_ritz import (
    # Plate model
    OrthotropicPlate,
    BoundaryCondition,
    # Solver
    solve_rayleigh_ritz,
    RayleighRitzMode,
    RayleighRitzResult,
    format_rayleigh_ritz_report,
)

from .calibration import (
    BodyStyle,
    get_body_calibration,
    list_body_styles,
    MaterialPreset,
    get_material_preset,
    list_materials,
)

from .gamma_calibration import (
    # Data classes
    ModeMeasurement,
    SpecimenData,
    GammaCalibrationResult,
    # Calibration engine
    GammaCalibration,
    # Convenience functions
    calibrate_gamma_from_pairs,
    calibrate_gamma_multi_specimen,
    format_gamma_calibration_report,
)

from .inverse_solver import (
    # Enums and constraints
    ForwardModel,
    ThicknessConstraints,
    FrequencyTarget,
    # Result class
    InverseSolverResult,
    # Simple solver
    solve_for_thickness,
    # Advanced solver
    InverseDesignProblem,
    # Material selection
    MaterialCandidate,
    solve_for_material_and_thickness,
    format_inverse_solver_report,
)

__all__ = [
    # Core functions
    "plate_modal_frequency",
    "thickness_for_target_frequency",
    "helmholtz_frequency",
    "chladni_to_box_frequency",
    "box_to_chladni_frequency",
    "coupled_eigenfrequencies",
    # 2-oscillator model
    "coupled_2osc_eigenfrequencies",
    "back_activity_ratio",
    "minimum_back_thickness_for_rigid",
    "Coupled2OscResult",
    "analyze_coupled_2osc",
    "format_2osc_report",
    # Alpha/Beta formulation
    "compute_alpha",
    "compute_beta",
    "compute_gamma",
    "plate_bending_stiffness",
    "brace_stiffness",
    "brace_mass",
    "air_virtual_mass",
    "air_virtual_mass_cavity",
    "AlphaBetaResult",
    "analyze_alpha_beta",
    "format_alpha_beta_report",
    # Rayleigh-Ritz
    "OrthotropicPlate",
    "BoundaryCondition",
    "solve_rayleigh_ritz",
    "RayleighRitzMode",
    "RayleighRitzResult",
    "format_rayleigh_ritz_report",
    # Gamma Calibration
    "ModeMeasurement",
    "SpecimenData",
    "GammaCalibrationResult",
    "GammaCalibration",
    "calibrate_gamma_from_pairs",
    "calibrate_gamma_multi_specimen",
    "format_gamma_calibration_report",
    # Inverse Solver
    "ForwardModel",
    "ThicknessConstraints",
    "FrequencyTarget",
    "InverseSolverResult",
    "solve_for_thickness",
    "InverseDesignProblem",
    "MaterialCandidate",
    "solve_for_material_and_thickness",
    "format_inverse_solver_report",
    # Result classes
    "PlateThicknessResult",
    "CoupledSystemResult",
    # Analysis functions
    "analyze_plate",
    "analyze_coupled_system",
    # Calibration
    "BodyStyle",
    "get_body_calibration",
    "list_body_styles",
    "MaterialPreset",
    "get_material_preset",
    "list_materials",
]
