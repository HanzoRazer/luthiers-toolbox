"""
app/analyzer/viewer_pack_bridge.py

Extracts plate design inputs from a ViewerPackV1 instance and constructs
the dataclasses the inverse solver expects.

This module is the only coupling point between the tap_tone_pi measurement
contract and the Production Shop inverse engine. It knows about both sides
but imports from neither — it works entirely with standard Python dicts and
dataclasses from the local calculators package.

INSTRUMENT CLASS: DECISION SUPPORT
Outputs from this module feed the inverse brace engine, which is advisory.
They do not appear in viewer_pack_v1 and are not subject to provenance tracking.

Usage:
    from app.analyzer.viewer_pack_loader import load_viewer_pack
    from app.analyzer.viewer_pack_bridge import plate_inputs_from_pack, BridgeError

    pack = load_viewer_pack("session.zip")
    try:
        inputs = plate_inputs_from_pack(pack)
    except BridgeError as e:
        # Pack missing required fields — tell user what's needed
        print(e)

    # inputs.plate is an OrthotropicPlate ready for rayleigh_ritz
    # inputs.target_frequencies is a list of (mode_name, Hz) tuples
    # inputs.metadata carries provenance for the prescription report
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Species defaults — used when pack contains no bending measurement
# ---------------------------------------------------------------------------

# E_L_GPa, E_C_GPa, rho_kg_m3, G_LC_GPa, nu_LC
_SPECIES_DEFAULTS: Dict[str, Tuple[float, float, float, float, float]] = {
    "sitka_spruce":       (10.5, 0.80, 430, 0.70, 0.37),
    "engelmann_spruce":   (9.5,  0.72, 400, 0.64, 0.37),
    "western_red_cedar":  (8.0,  0.65, 390, 0.56, 0.35),
    "adirondack_spruce":  (12.0, 0.85, 450, 0.78, 0.37),
    "red_spruce":         (11.5, 0.82, 440, 0.75, 0.37),
    "lutz_spruce":        (10.0, 0.76, 420, 0.68, 0.37),
}

_DEFAULT_SPECIES = "sitka_spruce"

# Poisson ratio for plate-width correction (nu_LC, nu_CL are symmetric for wood)
_DEFAULT_POISSON = 0.37
_DEFAULT_G_LC_GPa = 0.70   # shear modulus, GPa


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PlateInputs:
    """
    All inputs the inverse solver needs, extracted from a viewer pack.

    Fields align with OrthotropicPlate.from_wood() signature in rayleigh_ritz.py
    and InverseDesignProblem in inverse_solver.py.
    """

    # Material properties — from bending measurement or species default
    E_L_GPa: float                        # Along-grain modulus
    E_C_GPa: float                        # Cross-grain modulus
    G_LC_GPa: float                       # Shear modulus
    nu_LC: float                          # Poisson ratio (L→C direction)
    rho_kg_m3: float                      # Density

    # Geometry — from session metadata or defaults
    plate_length_mm: float                # a dimension (body length)
    plate_width_mm: float                 # b dimension (body width at waist)
    thickness_mm: float                   # Current graduation thickness

    # Modal targets — from measured peaks in the pack
    # List of (mode_label, frequency_Hz) — used to seed InverseDesignProblem
    target_frequencies: List[Tuple[str, float]] = field(default_factory=list)

    # Provenance
    source_session: str = ""              # session name from pack
    species: str = ""                     # species from metadata
    bending_measured: bool = False        # True = from measurement, False = species default
    bending_source_sha256: str = ""       # SHA256 of source bending_moe.json
    notes: List[str] = field(default_factory=list)  # warnings / fallback notices

    def to_orthotropic_plate_kwargs(self) -> Dict[str, Any]:
        """
        Return kwargs for OrthotropicPlate.from_wood() in rayleigh_ritz.py.

        OrthotropicPlate.from_wood(E_L, E_C, rho, h, a, b) signature.
        """
        return {
            "E_L":   self.E_L_GPa * 1e9,       # Pa
            "E_C":   self.E_C_GPa * 1e9,       # Pa
            "rho":   self.rho_kg_m3,            # kg/m³
            "h":     self.thickness_mm / 1000,  # m
            "a":     self.plate_length_mm / 1000,  # m
            "b":     self.plate_width_mm / 1000,   # m
        }


class BridgeError(ValueError):
    """Raised when a viewer pack is missing fields required for plate design."""
    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def plate_inputs_from_pack(
    pack: Any,
    thickness_override_mm: Optional[float] = None,
    species_override: Optional[str] = None,
) -> PlateInputs:
    """
    Extract PlateInputs from a ViewerPackV1 instance.

    The pack object is the return value of viewer_pack_loader.load_viewer_pack().
    This function accesses it as a duck-typed dict-like object or dataclass —
    it works with both the validated dataclass and a raw dict.

    Args:
        pack:                   ViewerPackV1 instance or dict
        thickness_override_mm:  Force a specific graduation thickness
                                (overrides pack metadata value)
        species_override:       Force a specific species key for defaults
                                (overrides pack metadata value)

    Returns:
        PlateInputs ready for InverseDesignProblem.

    Raises:
        BridgeError: If pack geometry is missing and cannot be inferred.
    """
    notes: List[str] = []

    # ── Normalise pack to dict ────────────────────────────────────────────
    raw = _pack_to_dict(pack)

    # ── Session provenance ────────────────────────────────────────────────
    source_session = raw.get("source_capdir", "")

    # ── Session metadata ──────────────────────────────────────────────────
    meta = _extract_meta(raw)
    species = species_override or meta.get("species", _DEFAULT_SPECIES)
    if species not in _SPECIES_DEFAULTS:
        notes.append(
            f"Unknown species '{species}' — falling back to {_DEFAULT_SPECIES} defaults."
        )
        species = _DEFAULT_SPECIES

    # ── Material properties ───────────────────────────────────────────────
    bending = raw.get("bending") or {}
    bending_measured = False
    bending_sha = ""

    if bending and (bending.get("E_L_GPa") or bending.get("E_C_GPa")):
        # Measured values from tap_tone_pi bending rig — use them
        E_L_raw = bending.get("E_L_GPa")
        E_C_raw = bending.get("E_C_GPa")
        if E_L_raw:
            E_L = float(E_L_raw)
            E_C = float(E_C_raw) if E_C_raw else _species_E_C(species, E_L)
        else:
            # Cross-grain only measurement — estimate E_L from E_C and ratio
            E_C = float(E_C_raw)
            defaults = _SPECIES_DEFAULTS.get(species, _SPECIES_DEFAULTS[_DEFAULT_SPECIES])
            ratio = defaults[0] / defaults[1] if defaults[1] > 0 else 13.0
            E_L = round(E_C * ratio, 4)
            notes.append(
                f"Only E_C in bending data — E_L estimated from {species} "
                f"orthotropic ratio ({ratio:.1f}:1)."
            )
        rho = float(bending.get("density_g_cm3", 0) * 1000) or _species_rho(species)
        bending_measured = True
        bending_sha = bending.get("source_bundle", "")

        if not bending.get("E_C_GPa"):
            notes.append(
                f"E_C not in pack bending data — estimated from E_L using "
                f"{species} orthotropic ratio."
            )
        if not bending.get("density_g_cm3"):
            notes.append(
                f"Density not in pack bending data — using {species} species default "
                f"({_species_rho(species)} kg/m³)."
            )
    else:
        # No bending measurement — fall back to species defaults
        defaults = _SPECIES_DEFAULTS.get(species, _SPECIES_DEFAULTS[_DEFAULT_SPECIES])
        E_L, E_C, rho = defaults[0], defaults[1], defaults[2]
        notes.append(
            f"No bending measurement in pack — using {species} species defaults "
            f"(E_L={E_L} GPa, E_C={E_C} GPa, ρ={rho} kg/m³). "
            f"Run bending rig for a specimen-specific prescription."
        )

    G_LC = _species_G_LC(species)
    nu_LC = _species_nu(species)

    # ── Geometry ──────────────────────────────────────────────────────────
    dims = meta.get("dimensions_mm", {}) or {}
    plate_length = float(dims.get("length", 0) or dims.get("plate_length_mm", 0))
    plate_width  = float(dims.get("width",  0) or dims.get("plate_width_mm",  0))
    thickness    = thickness_override_mm or float(
        dims.get("thickness", 0) or dims.get("thickness_mm", 0)
    )

    # Instrument-type defaults when dimensions are absent
    instrument_type = meta.get("instrument_type", "steel_string_dreadnought")
    if not plate_length or not plate_width:
        plate_length, plate_width = _default_dimensions(instrument_type)
        notes.append(
            f"Plate dimensions not in pack metadata — using {instrument_type} defaults "
            f"({plate_length} × {plate_width} mm)."
        )

    if not thickness:
        thickness = 3.0
        notes.append(
            "Graduation thickness not in pack metadata — defaulting to 3.0 mm. "
            "Override with thickness_override_mm."
        )

    # ── Modal targets ─────────────────────────────────────────────────────
    target_frequencies = _extract_targets(raw)
    if not target_frequencies:
        notes.append(
            "No peak data in pack — no modal targets set. "
            "Run Find Peaks in the analyzer before exporting."
        )

    return PlateInputs(
        E_L_GPa=E_L,
        E_C_GPa=E_C,
        G_LC_GPa=G_LC,
        nu_LC=nu_LC,
        rho_kg_m3=rho,
        plate_length_mm=plate_length,
        plate_width_mm=plate_width,
        thickness_mm=thickness,
        target_frequencies=target_frequencies,
        source_session=source_session,
        species=species,
        bending_measured=bending_measured,
        bending_source_sha256=bending_sha,
        notes=notes,
    )


def plate_inputs_from_dict(
    data: Dict[str, Any],
    **kwargs,
) -> PlateInputs:
    """Convenience wrapper — accepts a raw dict instead of a ViewerPackV1."""
    return plate_inputs_from_pack(data, **kwargs)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pack_to_dict(pack: Any) -> Dict[str, Any]:
    """Normalise ViewerPackV1 dataclass or dict to a plain dict."""
    if isinstance(pack, dict):
        return pack
    # dataclass — use __dict__ or vars()
    try:
        import dataclasses
        if dataclasses.is_dataclass(pack):
            return dataclasses.asdict(pack)
    except Exception:
        pass
    # Pydantic model
    try:
        return pack.model_dump()
    except AttributeError:
        pass
    try:
        return pack.dict()
    except AttributeError:
        pass
    # Last resort
    return vars(pack)


def _extract_meta(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract session metadata from various possible locations in the pack."""
    # viewer_pack_v1 puts metadata under files or session metadata
    meta = raw.get("meta", {}) or {}
    if not meta:
        # Sometimes nested under session
        meta = raw.get("session", {}) or {}
    if not meta:
        # Flat pack — look at top level
        meta = {
            k: raw[k] for k in (
                "species", "instrument_type", "dimensions_mm",
                "thickness_mm", "plate_length_mm", "plate_width_mm"
            ) if k in raw
        }
    return meta


def _extract_targets(raw: Dict[str, Any]) -> List[Tuple[str, float]]:
    """
    Extract modal frequency targets from the pack's points/peaks data.

    Looks for analysis peaks in the points array. Returns the dominant
    peaks as (label, hz) tuples for use as InverseDesignProblem targets.
    """
    targets: List[Tuple[str, float]] = []

    # viewer_pack_v1: points is a list of point IDs (strings)
    # Actual peak data lives in files under spectra/points/*/analysis.json
    # In the loaded pack, peaks may be pre-extracted into a peaks list
    peaks = raw.get("peaks", []) or []
    if not peaks:
        # Try nested under analysis
        peaks = raw.get("analysis", {}).get("peaks", []) or []

    for i, peak in enumerate(peaks[:6]):  # cap at 6 modes
        if isinstance(peak, dict):
            hz = peak.get("freq_hz") or peak.get("frequency_Hz") or peak.get("frequency_hz")
        elif isinstance(peak, (int, float)):
            hz = float(peak)
        else:
            continue
        if hz and hz > 0:
            targets.append((f"mode_{i+1}", float(hz)))

    return targets


def _species_E_C(species: str, E_L: float) -> float:
    """Estimate E_C from E_L using species orthotropic ratio."""
    defaults = _SPECIES_DEFAULTS.get(species, _SPECIES_DEFAULTS[_DEFAULT_SPECIES])
    ratio = defaults[0] / defaults[1] if defaults[1] > 0 else 13.0
    return round(E_L / ratio, 4)


def _species_rho(species: str) -> float:
    defaults = _SPECIES_DEFAULTS.get(species, _SPECIES_DEFAULTS[_DEFAULT_SPECIES])
    return defaults[2]


def _species_G_LC(species: str) -> float:
    defaults = _SPECIES_DEFAULTS.get(species, _SPECIES_DEFAULTS[_DEFAULT_SPECIES])
    return defaults[3] if len(defaults) > 3 else _DEFAULT_G_LC_GPa


def _species_nu(species: str) -> float:
    defaults = _SPECIES_DEFAULTS.get(species, _SPECIES_DEFAULTS[_DEFAULT_SPECIES])
    return defaults[4] if len(defaults) > 4 else _DEFAULT_POISSON


def _default_dimensions(instrument_type: str) -> Tuple[float, float]:
    """Default plate dimensions (length mm, width mm at waist) by instrument type."""
    _DIMS = {
        "steel_string_dreadnought": (500.0, 200.0),
        "steel_string_om":          (490.0, 195.0),
        "steel_string_000":         (480.0, 190.0),
        "classical_guitar":         (485.0, 185.0),
        "archtop":                  (495.0, 210.0),
        "ukulele_concert":          (295.0, 145.0),
        "ukulele_tenor":            (340.0, 160.0),
    }
    return _DIMS.get(instrument_type, _DIMS["steel_string_dreadnought"])
