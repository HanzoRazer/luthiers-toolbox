"""Phase 2 DSP: Transfer function and coherence computation.

This module provides the core DSP functions for two-channel ODS
(Operational Deflection Shape) analysis.

Migration
---------
    # Old import (deprecated)
    from scripts.phase2.dsp import compute_transfer_and_coherence, TFResult
    
    # New import (v2.0.0+)
    from tap_tone_pi.core.dsp import compute_transfer_and_coherence, TFResult
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

import numpy as np
import scipy
from scipy.signal import csd, welch


# Provenance constants for reproducibility audit trail
DSP_ALGO_VERSION = "1.0.0"
DSP_ALGO_ID = "phase2_transfer_coherence"

WindowName = Literal["hann", "hamming", "blackman", "boxcar"]


def get_dsp_provenance() -> Dict[str, str]:
    """Return provenance metadata for DSP computations."""
    return {
        "algo_id": DSP_ALGO_ID,
        "algo_version": DSP_ALGO_VERSION,
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }


@dataclass(frozen=True)
class TFResult:
    """Transfer function computation result."""
    freq_hz: np.ndarray
    H: np.ndarray           # complex transfer function roving/reference
    H_mag: np.ndarray       # |H|
    H_phase_deg: np.ndarray # angle(H) in degrees
    coherence: np.ndarray   # gamma^2
    pxx: np.ndarray         # ref PSD
    pyy: np.ndarray         # rov PSD


def compute_transfer_and_coherence(
    x_ref: np.ndarray,
    x_rov: np.ndarray,
    fs: int,
    *,
    nperseg: int = 4096,
    noverlap: int | None = None,
    window: WindowName = "hann",
    fmin_hz: float = 30.0,
    fmax_hz: float = 2000.0,
) -> TFResult:
    """Compute transfer function and coherence between reference and roving signals.
    
    Args:
        x_ref: Reference channel signal (fixed mic)
        x_rov: Roving channel signal (measurement mic)
        fs: Sample rate in Hz
        nperseg: FFT segment length
        noverlap: Overlap samples (default: nperseg // 2)
        window: Window function name
        fmin_hz: Minimum frequency to include
        fmax_hz: Maximum frequency to include
    
    Returns:
        TFResult with transfer function, coherence, and spectra
    """
    x_ref = np.asarray(x_ref, dtype=np.float32).reshape(-1)
    x_rov = np.asarray(x_rov, dtype=np.float32).reshape(-1)
    n = min(x_ref.size, x_rov.size)
    x_ref = x_ref[:n]
    x_rov = x_rov[:n]

    if noverlap is None:
        noverlap = nperseg // 2

    # Cross-spectrum and autospectra
    f, Pxy = csd(x_rov, x_ref, fs=fs, window=window, nperseg=nperseg, noverlap=noverlap, scaling="density")
    _, Pxx = welch(x_ref, fs=fs, window=window, nperseg=nperseg, noverlap=noverlap, scaling="density")
    _, Pyy = welch(x_rov, fs=fs, window=window, nperseg=nperseg, noverlap=noverlap, scaling="density")

    # Transfer function (roving/reference)
    eps = 1e-18
    H = Pxy / (Pxx + eps)

    # Coherence gamma^2 = |Pxy|^2 / (Pxx * Pyy)
    coh = (np.abs(Pxy) ** 2) / ((Pxx * Pyy) + eps)

    # Band limit
    mask = (f >= fmin_hz) & (f <= fmax_hz)
    f2 = f[mask].astype(np.float32)
    H2 = H[mask].astype(np.complex64)
    coh2 = coh[mask].astype(np.float32)
    Pxx2 = Pxx[mask].astype(np.float32)
    Pyy2 = Pyy[mask].astype(np.float32)

    mag = np.abs(H2).astype(np.float32)
    ph = (np.angle(H2) * (180.0 / np.pi)).astype(np.float32)

    return TFResult(
        freq_hz=f2,
        H=H2,
        H_mag=mag,
        H_phase_deg=ph,
        coherence=coh2,
        pxx=Pxx2,
        pyy=Pyy2,
    )


def nearest_bin(freqs: np.ndarray, target_hz: float) -> int:
    """Find index of frequency bin nearest to target."""
    freqs = np.asarray(freqs, dtype=np.float32)
    return int(np.argmin(np.abs(freqs - float(target_hz))))
