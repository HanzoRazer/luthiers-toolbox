"""Closed vocabulary for a build-response witness.

These names are the contract. A verifier result that uses them is not
scientific, production, CAM, or machine approval.
"""

from __future__ import annotations

SCHEMA_VERSION = "1"
WITNESS_CLASS = "BUILD_RESPONSE_WITNESS"
AUTHORITY_BOUNDARY_ID = "PEM-BUILD-WITNESS-001"
LITERATURE_STATUS = "BLOCKED_BEFORE_PREFLIGHT"

CAPTURE_INCOMPLETE = "CAPTURE_INCOMPLETE"
CAPTURE_COMPLETE = "CAPTURE_COMPLETE"
INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"
METHOD_REVIEW_PENDING = "METHOD_REVIEW_PENDING"
CALIBRATION_UNVERIFIED = "CALIBRATION_UNVERIFIED"
BUILD_RESPONSE_OBSERVED = "BUILD_RESPONSE_OBSERVED"
REFERENCE_COMPARISON_BLOCKED = "REFERENCE_COMPARISON_BLOCKED"
SCIENTIFIC_INTERPRETATION_PENDING = "SCIENTIFIC_INTERPRETATION_PENDING"

STORED_STATES = frozenset(
    {
        CAPTURE_INCOMPLETE,
        CAPTURE_COMPLETE,
        METHOD_REVIEW_PENDING,
        CALIBRATION_UNVERIFIED,
        BUILD_RESPONSE_OBSERVED,
        REFERENCE_COMPARISON_BLOCKED,
        SCIENTIFIC_INTERPRETATION_PENDING,
    }
)

PROHIBITED_STATES = frozenset(
    {
        "MATERIAL_PROPERTY_WITNESS",
        "SCIENTIFICALLY_VALIDATED",
        "PRODUCTION_READY",
        "CAM_AUTHORIZED",
        "MACHINE_EXECUTABLE",
    }
)

PROHIBITED_KEYS = frozenset(
    {
        "cam_authorized",
        "cam_toolpath",
        "cnc_program",
        "gcode",
        "intrinsic_moe",
        "machine_executable",
        "production_ready",
        "reference_comparison_result",
        "scientifically_validated",
        "species_inference",
    }
)

MEASUREMENT_SOURCES = frozenset(
    {
        "DECLARED_BUILD_PROPERTY",
        "DERIVED_FROM_CAPTURE",
        "DIRECT_AUDIO_CAPTURE",
        "DIRECT_DIMENSION_MEASUREMENT",
        "DIRECT_INSTRUMENT_READING",
        "DIRECT_MASS_MEASUREMENT",
        "DIRECT_SENSOR_CAPTURE",
        "IMPORTED_MEASUREMENT",
        "OPERATOR_OBSERVATION",
    }
)

DIRECT_SOURCES = frozenset(
    {
        "DIRECT_AUDIO_CAPTURE",
        "DIRECT_DIMENSION_MEASUREMENT",
        "DIRECT_INSTRUMENT_READING",
        "DIRECT_MASS_MEASUREMENT",
        "DIRECT_SENSOR_CAPTURE",
    }
)

CALIBRATION_VERIFIED = "CALIBRATION_VERIFIED"
CALIBRATION_UNVERIFIED_STATUS = "CALIBRATION_UNVERIFIED"
CALIBRATION_STATUSES = frozenset({CALIBRATION_VERIFIED, CALIBRATION_UNVERIFIED_STATUS})

IDENTITY_STATUSES = frozenset({"DECLARED_ONLY", "UNDECLARED", "VERIFIED"})

ALLOWED_DERIVATIONS = frozenset(
    {
        "capture_duration",
        "capture_warnings",
        "dominant_spectral_peaks",
        "envelope_decay",
        "noise_floor",
        "peak_amplitude",
        "peak_frequencies",
        "repeatability",
        "rms_level",
        "trial_differences",
    }
)

REFUSED_DERIVATIONS = frozenset(
    {
        "damping_coefficient",
        "density",
        "equivalence",
        "moe",
        "species",
        "substitution",
    }
)

MATERIAL_IDENTITY_STATEMENT = (
    "Material identity in this record is declared unless an independent "
    "evidence reference establishes it. A trade name is not a botanical species."
)

NON_AUTHORITY_STATEMENT = (
    "Verification of this package establishes only that its files, sizes, and "
    "SHA-256 digests match the manifest and that the records follow the "
    "build-response contract. It does not approve a scientific conclusion, a "
    "material property, a species identification, a literature comparison, a "
    "production release, a CAM program, or machine execution."
)

ALGORITHM_ID = "pem_descriptive_v1"
ALGORITHM_VERSION = "1"
FFT_SIZE = 256
