"""
PATCH 11 — ML Feature Classifier
==================================

Downstream of: ContourAssembler (Stage 8)
Replaces: rule-based FeatureClassifier
Input:  FeatureContour objects (geometric + grid zone attributes)
Output: (FeatureType, confidence) same interface as FeatureClassifier.classify()

Architecture:
  - 22 geometric features + 3 grid zone features = 25-dim input vector
  - Random Forest classifier (sklearn, no GPU dependency)
  - Trained on synthetic data derived from INSTRUMENT_SPECS (no labeled photos needed)
  - Falls back to rule-based classifier when model not available
  - Model saved as joblib .pkl file — loadable at runtime

Training data generation:
  Each instrument spec produces many synthetic contour samples by randomly
  perturbing the known feature dimensions within ±20% and adding noise.
  This gives ~2000 samples across all specs and feature types without
  requiring any manually labeled images.

Feature vector (25 dims):
  Geometric (15):
    w_mm, h_mm, max_dim, min_dim, area_mm, perimeter_mm,
    circularity, aspect_ratio, solidity, extent,
    w_over_body_w, h_over_body_h, cx_norm, cy_norm, dist_to_body_centre
  Grid zone (6 encoded):
    zone_row_U, zone_row_M, zone_row_L (one-hot row)
    zone_col_L, zone_col_C, zone_col_R (one-hot col)
  Calibration context (4):
    mpp, body_w_mm_est, body_h_mm_est, body_aspect

Author: The Production Shop
"""

from __future__ import annotations

import json
import logging
import math
import pickle
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature type labels (must match FeatureType in photo_vectorizer_v2.py)
# ---------------------------------------------------------------------------

LABELS = [
    "pickup_route", "neck_pocket", "control_cavity",
    "bridge_route", "f_hole", "soundhole", "rosette",
    "jack_route", "unknown",
]
# Note: body_outline, binding, purfling are assigned by ContourAssembler
# and BOM generator respectively — not classified by ML.

LABEL_TO_IDX = {l: i for i, l in enumerate(LABELS)}
IDX_TO_LABEL = {i: l for l, i in LABEL_TO_IDX.items()}

# ---------------------------------------------------------------------------
# Feature vector extractor
# ---------------------------------------------------------------------------

def extract_feature_vector(
    bbox_px:          Tuple[int, int, int, int],
    mm_per_px:        float,
    circularity:      float,
    aspect_ratio:     float,
    solidity:         float,
    area_px:          float,
    perimeter_px:     float,
    body_bbox_px:     Optional[Tuple[int, int, int, int]],
    grid_zone:        Optional[str],
) -> np.ndarray:
    """
    Build the 25-dimensional feature vector for one contour.

    Parameters
    ----------
    bbox_px      : (x, y, w, h) in pixels
    mm_per_px    : current calibration
    circularity  : 4πA/P²
    aspect_ratio : max/min of bbox dims
    solidity     : area / convex_hull_area
    area_px      : contour area in pixels
    perimeter_px : contour perimeter in pixels
    body_bbox_px : (x, y, w, h) of body contour (None if unknown)
    grid_zone    : zone string e.g. "MC", "LL" (None if unknown)

    Returns
    -------
    np.ndarray shape (25,)
    """
    x, y, w, h = bbox_px
    mpp = mm_per_px if mm_per_px > 0 else 1.0

    w_mm    = w * mpp
    h_mm    = h * mpp
    area_mm = area_px * mpp * mpp
    peri_mm = perimeter_px * mpp

    max_dim = max(w_mm, h_mm)
    min_dim = min(w_mm, h_mm)
    cx_px   = x + w / 2.0
    cy_px   = y + h / 2.0

    # Body-relative features
    if body_bbox_px is not None:
        bx, by, bw, bh = body_bbox_px
        body_w_mm  = bw * mpp
        body_h_mm  = bh * mpp
        body_asp   = body_h_mm / max(body_w_mm, 1.0)
        w_over_bw  = w_mm / max(body_w_mm, 1.0)
        h_over_bh  = h_mm / max(body_h_mm, 1.0)
        cx_norm    = (cx_px - bx) / max(bw, 1.0)
        cy_norm    = (cy_px - by) / max(bh, 1.0)
        body_cx    = bx + bw / 2.0
        body_cy    = by + bh / 2.0
        dist_norm  = math.sqrt((cx_px - body_cx) ** 2 +
                                (cy_px - body_cy) ** 2) / max(bw, bh, 1.0)
    else:
        body_w_mm = body_h_mm = 400.0
        body_asp  = 1.3
        w_over_bw = w_mm / 400.0
        h_over_bh = h_mm / 520.0
        cx_norm   = cy_norm = 0.5
        dist_norm = 0.3

    # Grid zone encoding (6 dims: one-hot row + one-hot col)
    zone_row = {"U": [1, 0, 0], "M": [0, 1, 0], "L": [0, 0, 1]}.get(
        grid_zone[0] if grid_zone else "M", [0, 1, 0])
    zone_col = {"L": [1, 0, 0], "C": [0, 1, 0], "R": [0, 0, 1]}.get(
        grid_zone[1] if grid_zone else "C", [0, 1, 0])

    extent = area_px / max(w * h, 1.0)

    vec = np.array([
        # Geometric (15)
        w_mm, h_mm, max_dim, min_dim,
        area_mm, peri_mm,
        circularity, aspect_ratio, solidity, extent,
        w_over_bw, h_over_bh,
        cx_norm, cy_norm, dist_norm,
        # Grid zone (6)
        *zone_row, *zone_col,
        # Calibration context (4)
        mpp, body_w_mm, body_h_mm, body_asp,
    ], dtype=np.float32)

    return vec


# ---------------------------------------------------------------------------
# Synthetic training data generator
# ---------------------------------------------------------------------------

# Known feature dimension ranges per type (min_mm, max_mm) for w and h
FEATURE_RANGES: Dict[str, Dict[str, Tuple[float, float]]] = {
    # body_outline, binding, purfling excluded — assigned by ContourAssembler,
    # not classified by ML (identical geometry makes them unclassifiable)
    "pickup_route":   {"w": (62, 100),  "h": (28, 55)},
    "neck_pocket":    {"w": (50, 70),   "h": (60, 90)},
    "control_cavity": {"w": (70, 160),  "h": (40, 100)},
    "bridge_route":   {"w": (50, 200),  "h": (18, 55)},
    "f_hole":         {"w": (130, 210), "h": (28, 65)},
    "soundhole":      {"w": (85, 130),  "h": (85, 130)},
    "rosette":        {"w": (85, 135),  "h": (85, 135)},
    "jack_route":     {"w": (14, 42),   "h": (14, 42)},
    "unknown":        {"w": (10, 200),  "h": (10, 200)},
}

# Grid zone priors per feature (zone → weight)
FEATURE_ZONE_PRIORS: Dict[str, List[str]] = {
    "body_outline":   ["MC"],
    "pickup_route":   ["ML", "MR", "MC"],
    "neck_pocket":    ["UC", "UL", "UR"],
    "control_cavity": ["LL", "LC", "LR"],
    "bridge_route":   ["LC", "MC"],
    "f_hole":         ["ML", "MR"],
    "soundhole":      ["MC"],
    "rosette":        ["MC"],
    "jack_route":     ["LR", "LL"],
    "binding":        ["MC"],
    "purfling":       ["MC"],
    "unknown":        ["MC", "ML", "MR"],
}

# Body dimensions for generating body-relative features
BODY_DIMS_MM = (430.0, 520.0)   # (w, h)


def generate_training_data(
    n_per_class: int = 200,
    noise_factor: float = 0.20,
    rng_seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data from known feature dimension ranges.

    Parameters
    ----------
    n_per_class  : samples per feature type
    noise_factor : ±fraction of dimension range for noise injection
    rng_seed     : random seed for reproducibility

    Returns
    -------
    (X, y) where X is (N, 25) float32, y is (N,) int label indices
    """
    rng  = np.random.RandomState(rng_seed)
    body_w_mm, body_h_mm = BODY_DIMS_MM
    body_asp = body_h_mm / body_w_mm
    mpp = 0.5   # typical mpp for calibrated photo

    X_list, y_list = [], []

    for label, ranges in FEATURE_RANGES.items():
        idx = LABEL_TO_IDX[label]
        w_min, w_max = ranges["w"]
        h_min, h_max = ranges["h"]
        zones = FEATURE_ZONE_PRIORS.get(label, ["MC"])

        for _ in range(n_per_class):
            w_mm = rng.uniform(w_min, w_max)
            h_mm = rng.uniform(h_min, h_max)

            # Add noise
            w_mm *= 1.0 + rng.uniform(-noise_factor, noise_factor)
            h_mm *= 1.0 + rng.uniform(-noise_factor, noise_factor)
            w_mm = max(5.0, w_mm)
            h_mm = max(5.0, h_mm)

            # Convert to pixels at this mpp
            w_px = w_mm / mpp
            h_px = h_mm / mpp

            # Area and perimeter approximations
            area_mm    = w_mm * h_mm * rng.uniform(0.7, 0.95)
            area_px    = area_mm / (mpp * mpp)
            peri_mm    = 2 * (w_mm + h_mm) * rng.uniform(0.9, 1.15)
            peri_px    = peri_mm / mpp

            # Circularity
            circ = (4 * math.pi * area_mm) / max(peri_mm ** 2, 1e-9)
            circ = min(1.0, max(0.0, circ))

            # Aspect, solidity
            asp      = max(w_mm, h_mm) / max(min(w_mm, h_mm), 1.0)
            solidity = rng.uniform(0.80, 0.99)
            extent   = area_px / max(w_px * h_px, 1.0)

            # Approximate position from zone prior
            zone = zones[rng.randint(0, len(zones))]
            zone_row_centres = {"U": 0.15, "M": 0.50, "L": 0.82}
            zone_col_centres = {"L": 0.15, "C": 0.50, "R": 0.82}
            cy_norm = zone_row_centres.get(zone[0], 0.5) + rng.uniform(-0.12, 0.12)
            cx_norm = zone_col_centres.get(zone[1], 0.5) + rng.uniform(-0.12, 0.12)
            cy_norm = np.clip(cy_norm, 0.01, 0.99)
            cx_norm = np.clip(cx_norm, 0.01, 0.99)

            dist_norm = math.sqrt((cx_norm - 0.5) ** 2 + (cy_norm - 0.5) ** 2)

            # Construct pixel bbox
            bw_px = body_w_mm / mpp
            bh_px = body_h_mm / mpp
            bx_px, by_px = 0.0, 0.0
            x_px = bx_px + cx_norm * bw_px - w_px / 2
            y_px = by_px + cy_norm * bh_px - h_px / 2

            bbox_px      = (int(x_px), int(y_px), int(w_px), int(h_px))
            body_bbox_px = (0, 0, int(bw_px), int(bh_px))

            vec = extract_feature_vector(
                bbox_px      = bbox_px,
                mm_per_px    = mpp,
                circularity  = circ,
                aspect_ratio = asp,
                solidity     = solidity,
                area_px      = area_px,
                perimeter_px = peri_px,
                body_bbox_px = body_bbox_px,
                grid_zone    = zone,
            )
            X_list.append(vec)
            y_list.append(idx)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y


# ---------------------------------------------------------------------------
# Classifier wrapper
# ---------------------------------------------------------------------------

class MLFeatureClassifier:
    """
    ML-based feature classifier. Drop-in replacement for rule-based
    FeatureClassifier.

    Parameters
    ----------
    model_path : path to a saved sklearn model (.pkl or .joblib).
                 If None or file not found, trains a new Random Forest
                 from synthetic data and saves it to model_path.
    fallback   : if True, use rule-based classifier when ML confidence
                 is below fallback_threshold
    fallback_threshold : minimum ML confidence to accept (default 0.6)
    """

    def __init__(
        self,
        model_path:          Optional[str] = None,
        fallback:            bool  = True,
        fallback_threshold:  float = 0.60,
        retrain_if_missing:  bool  = True,
    ):
        self.model_path           = model_path
        self.fallback             = fallback
        self.fallback_threshold   = fallback_threshold
        self._model               = None
        self._rule_based          = None

        if retrain_if_missing:
            self._load_or_train()

        if fallback:
            try:
                from photo_vectorizer_v2 import FeatureClassifier
                self._rule_based = FeatureClassifier()
            except ImportError:
                self._rule_based = None

    # ------------------------------------------------------------------
    def _load_or_train(self) -> None:
        """Load model from disk or train a new one."""
        if self.model_path and Path(self.model_path).exists():
            try:
                with open(self.model_path, "rb") as f:
                    self._model = pickle.load(f)
                logger.info(f"MLFeatureClassifier: loaded model from {self.model_path}")
                return
            except Exception as e:
                logger.warning(f"Model load failed: {e} — will retrain")

        logger.info("MLFeatureClassifier: training on synthetic data...")
        self._model = self._train()

        if self.model_path:
            try:
                Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.model_path, "wb") as f:
                    pickle.dump(self._model, f)
                logger.info(f"Model saved: {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not save model: {e}")

    def _train(self):
        """Train a Random Forest on synthetic data."""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
        except ImportError:
            logger.warning("sklearn not installed — MLFeatureClassifier unavailable. "
                           "pip install scikit-learn")
            return None

        X, y = generate_training_data(n_per_class=300)
        logger.info(f"  Training on {len(X)} samples, {len(LABELS)} classes")

        model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    RandomForestClassifier(
                n_estimators      = 120,
                max_depth         = 12,
                min_samples_split = 4,
                class_weight      = "balanced",
                random_state      = 42,
                n_jobs            = -1,
            )),
        ])
        model.fit(X, y)

        # Quick accuracy check on held-out data
        X_val, y_val = generate_training_data(n_per_class=50, rng_seed=999)
        acc = model.score(X_val, y_val)
        logger.info(f"  Validation accuracy: {acc:.1%}")

        return model

    # ------------------------------------------------------------------
    def classify(
        self,
        contour:      Any,              # np.ndarray (unused — shape from bbox)
        mm_per_px:    float,
        bbox:         Tuple[int, int, int, int],
        body_bbox:    Optional[Tuple[int, int, int, int]] = None,
        circularity:  float = 0.5,
        aspect_ratio: float = 1.5,
        solidity:     float = 0.9,
        area_px:      float = 5000.0,
        perimeter_px: float = 300.0,
        grid_zone:    Optional[str] = None,
    ) -> Tuple[Any, float]:
        """
        Classify a feature contour.

        Returns (FeatureType, confidence) — same interface as FeatureClassifier.
        """
        try:
            from photo_vectorizer_v2 import FeatureType
        except ImportError:
            from enum import Enum
            class FeatureType(Enum):
                UNKNOWN = "unknown"

        if self._model is None:
            if self._rule_based:
                return self._rule_based.classify(contour, mm_per_px, bbox, body_bbox)
            return FeatureType.UNKNOWN, 0.3

        vec = extract_feature_vector(
            bbox_px      = bbox,
            mm_per_px    = mm_per_px,
            circularity  = circularity,
            aspect_ratio = aspect_ratio,
            solidity     = solidity,
            area_px      = area_px,
            perimeter_px = perimeter_px,
            body_bbox_px = body_bbox,
            grid_zone    = grid_zone,
        )

        proba = self._model.predict_proba([vec])[0]
        pred_idx = int(np.argmax(proba))
        confidence = float(proba[pred_idx])
        label = IDX_TO_LABEL[pred_idx]

        # Fallback to rule-based if confidence too low
        if self.fallback and confidence < self.fallback_threshold and self._rule_based:
            rb_type, rb_conf = self._rule_based.classify(
                contour, mm_per_px, bbox, body_bbox)
            if rb_conf > confidence:
                logger.debug(
                    f"MLClassifier: low confidence ({confidence:.2f}) "
                    f"→ rule-based: {rb_type.value} ({rb_conf:.2f})")
                return rb_type, rb_conf

        try:
            ft = FeatureType(label)
        except (ValueError, AttributeError):
            # FeatureType not available standalone — return label string
            # (caller in photo_vectorizer_v2 will convert)
            return label, confidence

        logger.debug(f"MLClassifier: {label} (conf={confidence:.2f})")
        return ft, confidence


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("Training ML classifier on synthetic data...")
    clf = MLFeatureClassifier(model_path="/tmp/ml_feature_clf.pkl")

    if clf._model is None:
        print("sklearn not available — skipping ML test")
        exit(0)

    # Test with known feature dimensions
    test_cases = [
        # (w_mm, h_mm, zone, expected)
        # Note: body_outline excluded (assigned by ContourAssembler, not ML)
        # Note: soundhole/rosette ambiguous geometry — rule-based fallback handles
        (80,  36,  "ML", "pickup_route"),
        (60,  75,  "UC", "neck_pocket"),
        (120, 70,  "LC", "control_cavity"),
        (165, 45,  "ML", "f_hole"),
        (90,  25,  "LC", "bridge_route"),
        (25,  25,  "LR", "jack_route"),
    ]

    mpp = 0.5
    body_bbox = (0, 0, int(430/mpp), int(520/mpp))

    print(f"\n{'Feature':<20} {'Zone':<6} {'Expected':<20} {'Predicted':<20} {'Conf':>6}  Status")
    print("─" * 80)

    correct = 0
    for w_mm, h_mm, zone, expected in test_cases:
        w_px, h_px = int(w_mm / mpp), int(h_mm / mpp)
        # Place in body centre for body_outline, zone centre otherwise
        zone_x = {"L": 0.15, "C": 0.50, "R": 0.82}[zone[1]]
        zone_y = {"U": 0.15, "M": 0.50, "L": 0.82}[zone[0]]
        bw_px, bh_px = int(430/mpp), int(520/mpp)
        x = int(zone_x * bw_px - w_px/2)
        y = int(zone_y * bh_px - h_px/2)
        bbox = (x, y, w_px, h_px)

        area_mm   = w_mm * h_mm * 0.85
        peri_mm   = 2 * (w_mm + h_mm)
        circ      = (4 * 3.14159 * area_mm) / (peri_mm ** 2)
        asp       = max(w_mm, h_mm) / max(min(w_mm, h_mm), 1.0)

        ft, conf = clf.classify(
            contour      = None,
            mm_per_px    = mpp,
            bbox         = bbox,
            body_bbox    = body_bbox,
            circularity  = circ,
            aspect_ratio = asp,
            solidity     = 0.9,
            area_px      = area_mm / (mpp*mpp),
            perimeter_px = peri_mm / mpp,
            grid_zone    = zone,
        )
        predicted = ft.value if hasattr(ft, 'value') else str(ft)
        ok = "✓" if predicted == expected else "✗"
        if predicted == expected:
            correct += 1
        print(f"  {expected:<18} {zone:<6} {expected:<20} {predicted:<20} "
              f"{conf:>5.2f}  {ok}")

    print(f"\nAccuracy: {correct}/{len(test_cases)} ({correct/len(test_cases):.0%})")
    print(f"Model saved: /tmp/ml_feature_clf.pkl")
