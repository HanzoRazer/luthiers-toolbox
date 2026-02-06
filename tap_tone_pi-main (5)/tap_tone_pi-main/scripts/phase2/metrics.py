from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

from .grid import Grid
from .dsp import nearest_bin, get_dsp_provenance

# Provenance constants for WSI/wolf metrics
METRICS_ALGO_VERSION = "1.0.0"
METRICS_ALGO_ID = "phase2_wsi_wolf"


def get_metrics_provenance() -> Dict[str, Any]:
    """Return provenance metadata for WSI/wolf metric computations."""
    dsp_prov = get_dsp_provenance()
    return {
        "algo_id": METRICS_ALGO_ID,
        "algo_version": METRICS_ALGO_VERSION,
        "dsp_provenance": dsp_prov,
        "numpy_version": np.__version__,
    }


@dataclass(frozen=True)
class PointSpectrum:
    point_id: str
    x_mm: float
    y_mm: float
    freq_hz: np.ndarray
    H_mag: np.ndarray
    coherence: np.ndarray
    phase_deg: np.ndarray


def build_adjacency(grid: Grid) -> Dict[str, List[str]]:
    # Simple adjacency: connect each point to its 4 nearest neighbors by euclidean distance (k=4).
    # This is robust without assuming perfect rect grid.
    pts = grid.points
    xy = np.array([(p.x, p.y) for p in pts], dtype=np.float32)
    ids = [p.id for p in pts]
    adj: Dict[str, List[str]] = {pid: [] for pid in ids}

    for i, pid in enumerate(ids):
        d = np.sqrt(np.sum((xy - xy[i]) ** 2, axis=1))
        order = np.argsort(d)
        neigh = [ids[j] for j in order[1:5]]  # skip self
        adj[pid] = neigh
    return adj


def compute_localization_index(mags: np.ndarray) -> float:
    # Localization index L = max / mean (clipped)
    mags = np.asarray(mags, dtype=np.float32)
    m_mean = float(np.mean(mags)) if mags.size else 0.0
    m_max = float(np.max(mags)) if mags.size else 0.0
    if m_mean <= 1e-12:
        return 0.0
    return float(m_max / m_mean)


def compute_energy_gradient(
    point_mags: Dict[str, float],
    adjacency: Dict[str, List[str]],
) -> float:
    # E∇ = mean absolute neighbor difference normalized by mean magnitude
    diffs: List[float] = []
    mags = list(point_mags.values())
    denom = float(np.mean(mags)) if mags else 0.0
    if denom <= 1e-12:
        return 0.0

    for pid, neigh in adjacency.items():
        m = point_mags.get(pid, 0.0)
        for nid in neigh:
            mn = point_mags.get(nid, 0.0)
            diffs.append(abs(m - mn))

    if not diffs:
        return 0.0
    return float(np.mean(diffs) / denom)


def compute_phase_disorder(phases_deg: np.ndarray) -> float:
    # Eφ: circular dispersion. Map deg -> unit vectors, take 1 - |mean|.
    phases = np.asarray(phases_deg, dtype=np.float32)
    if phases.size == 0:
        return 0.0
    ang = phases * (np.pi / 180.0)
    v = np.exp(1j * ang)
    R = np.abs(np.mean(v))
    return float(1.0 - R)


def compute_wsi(
    *,
    loc: float,
    grad: float,
    phase_disorder: float,
    coh_mean: float,
    coherence_threshold: float = 0.7,
) -> Tuple[float, bool]:
    """
    Compute Wolf Suspicion Index with coherence-based admissibility gating.

    Returns:
        (wsi, admissible): WSI score in [0,1] and whether measurement meets
        coherence threshold for admissibility.

    Admissibility: If coh_mean < coherence_threshold, the candidate is marked
    inadmissible (measurement quality too low to trust).
    """
    # Composite, measurement-only:
    # - Higher localization and higher gradient increase risk
    # - Higher phase disorder increases risk
    # - Low coherence increases risk (but we downweight if coherence is good)
    # WSI in [0, 1] by squashing.
    coh_penalty = max(0.0, 1.0 - float(coh_mean))  # 0 when coherence=1
    raw = (0.45 * loc) + (0.35 * grad) + (0.20 * phase_disorder) + (0.25 * coh_penalty)

    # squash with logistic-like
    wsi = 1.0 - np.exp(-0.35 * float(raw))
    wsi_val = float(np.clip(wsi, 0.0, 1.0))

    # Coherence gating: admissible only if mean coherence meets threshold
    admissible = float(coh_mean) >= float(coherence_threshold)

    return wsi_val, admissible


def wsi_curve(
    spectra: List[PointSpectrum],
    grid: Grid,
    *,
    fmin_hz: float = 30.0,
    fmax_hz: float = 2000.0,
    coherence_threshold: float = 0.7,
) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """
    Compute WSI curve across frequency bins with coherence-based admissibility.

    Args:
        spectra: List of PointSpectrum for each grid point
        grid: Grid definition
        fmin_hz: Minimum frequency (Hz)
        fmax_hz: Maximum frequency (Hz)
        coherence_threshold: Minimum mean coherence for admissibility (default 0.7)

    Returns:
        freqs: (n_bins,) frequency axis
        wsi: (n_bins,) WSI values
        per_bin_details: list of dict with loc/grad/phase/coh/admissible

    Assumes all spectra share the same freq axis.
    """
    if not spectra:
        raise ValueError("No point spectra provided")

    freq = spectra[0].freq_hz
    for s in spectra[1:]:
        if s.freq_hz.shape != freq.shape or float(np.max(np.abs(s.freq_hz - freq))) > 1e-6:
            raise ValueError("Point spectra do not share a common frequency axis")

    # band mask
    mask = (freq >= fmin_hz) & (freq <= fmax_hz)
    idxs = np.where(mask)[0]
    if idxs.size == 0:
        raise ValueError("No frequency bins in requested band")

    adjacency = build_adjacency(grid)

    wsi_vals: List[float] = []
    details: List[Dict[str, float]] = []

    ids = [p.point_id for p in spectra]

    for bi in idxs:
        # per point magnitudes/coherence/phase at this bin
        pmag: Dict[str, float] = {}
        pcoh: List[float] = []
        pph: List[float] = []

        mags_arr: List[float] = []
        for s in spectra:
            m = float(s.H_mag[bi])
            pmag[s.point_id] = m
            mags_arr.append(m)
            pcoh.append(float(s.coherence[bi]))
            pph.append(float(s.phase_deg[bi]))

        loc = compute_localization_index(np.array(mags_arr, dtype=np.float32))
        grad = compute_energy_gradient(pmag, adjacency)
        phase_d = compute_phase_disorder(np.array(pph, dtype=np.float32))
        coh_mean = float(np.mean(pcoh)) if pcoh else 0.0

        w, admissible = compute_wsi(
            loc=loc,
            grad=grad,
            phase_disorder=phase_d,
            coh_mean=coh_mean,
            coherence_threshold=coherence_threshold,
        )
        wsi_vals.append(w)
        details.append({
            "loc": float(loc),
            "grad": float(grad),
            "phase_disorder": float(phase_d),
            "coh_mean": float(coh_mean),
            "admissible": admissible,
        })

    return freq[idxs].astype(np.float32), np.array(wsi_vals, dtype=np.float32), details
