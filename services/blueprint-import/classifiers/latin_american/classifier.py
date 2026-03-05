"""
Latin American Strings Classifier
=================================

ML-assisted classification for Latin American string instruments.

Classification Strategy:
1. Fast path: Dimensional analysis against known profiles
2. ML boost: Feature extraction + neural classification when confidence < 0.7
3. Multi-factor scoring: Scale + body + features

Author: Luthier's Toolbox
Version: 4.0.0-alpha
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .instruments import (
    InstrumentProfile,
    InstrumentFamily,
    ALL_PROFILES,
    get_profile_by_name
)

logger = logging.getLogger(__name__)


@dataclass
class ClassificationCandidate:
    """A candidate instrument classification with confidence."""
    profile: InstrumentProfile
    confidence: float
    scores: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'instrument': self.profile.name,
            'family': self.profile.family.value,
            'confidence': round(self.confidence, 3),
            'scores': {k: round(v, 3) for k, v in self.scores.items()},
            'notes': self.notes
        }


@dataclass
class ClassificationResult:
    """Complete classification result with ranked candidates."""
    primary: Optional[ClassificationCandidate]
    alternatives: List[ClassificationCandidate]
    measurements_used: Dict[str, float]
    classification_method: str  # "dimensional", "ml_assisted", "hybrid"

    @property
    def is_confident(self) -> bool:
        """Check if classification is confident (>0.7)."""
        return self.primary is not None and self.primary.confidence >= 0.7

    @property
    def needs_review(self) -> bool:
        """Check if classification needs human review."""
        if self.primary is None:
            return True
        if self.primary.confidence < 0.5:
            return True
        if len(self.alternatives) > 0 and self.alternatives[0].confidence > self.primary.confidence * 0.85:
            return True  # Close runner-up
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary': self.primary.to_dict() if self.primary else None,
            'alternatives': [a.to_dict() for a in self.alternatives[:3]],
            'measurements_used': self.measurements_used,
            'method': self.classification_method,
            'confident': self.is_confident,
            'needs_review': self.needs_review
        }


@dataclass
class ExtractedMeasurements:
    """Measurements extracted from blueprint for classification."""
    scale_length_mm: Optional[float] = None
    body_length_mm: Optional[float] = None
    lower_bout_width_mm: Optional[float] = None
    upper_bout_width_mm: Optional[float] = None
    waist_width_mm: Optional[float] = None
    soundhole_diameter_mm: Optional[float] = None
    nut_width_mm: Optional[float] = None
    string_count: Optional[int] = None
    fret_count: Optional[int] = None

    # Derived ratios
    waist_ratio: Optional[float] = None  # waist / lower_bout
    bout_ratio: Optional[float] = None   # upper / lower bout

    def calculate_ratios(self):
        """Calculate derived ratios from measurements."""
        if self.waist_width_mm and self.lower_bout_width_mm:
            self.waist_ratio = self.waist_width_mm / self.lower_bout_width_mm

        if self.upper_bout_width_mm and self.lower_bout_width_mm:
            self.bout_ratio = self.upper_bout_width_mm / self.lower_bout_width_mm

    def to_dict(self) -> Dict[str, float]:
        """Export measurements as dictionary."""
        self.calculate_ratios()
        result = {}

        if self.scale_length_mm:
            result['scale_length_mm'] = self.scale_length_mm
        if self.body_length_mm:
            result['body_length_mm'] = self.body_length_mm
        if self.lower_bout_width_mm:
            result['lower_bout_width_mm'] = self.lower_bout_width_mm
        if self.upper_bout_width_mm:
            result['upper_bout_width_mm'] = self.upper_bout_width_mm
        if self.waist_width_mm:
            result['waist_width_mm'] = self.waist_width_mm
        if self.soundhole_diameter_mm:
            result['soundhole_diameter_mm'] = self.soundhole_diameter_mm
        if self.nut_width_mm:
            result['nut_width_mm'] = self.nut_width_mm
        if self.string_count:
            result['string_count'] = self.string_count
        if self.fret_count:
            result['fret_count'] = self.fret_count
        if self.waist_ratio:
            result['waist_ratio'] = self.waist_ratio
        if self.bout_ratio:
            result['bout_ratio'] = self.bout_ratio

        return result


class LatinAmericanStringsClassifier:
    """
    Unified classifier for Latin American string instruments.

    Supports:
    - Venezuelan Cuatro
    - Puerto Rican Cuatro
    - Colombian Tiple
    - Requinto
    - Charango
    - Bandola

    Usage:
        classifier = LatinAmericanStringsClassifier()

        # From measurements
        result = classifier.classify(
            scale_length_mm=530,
            lower_bout_width_mm=260
        )

        # From extraction result
        result = classifier.classify_from_extraction(extraction_result)

        print(f"Instrument: {result.primary.profile.name}")
        print(f"Confidence: {result.primary.confidence:.0%}")
    """

    # Scoring weights
    WEIGHT_SCALE = 0.35       # Scale length is primary identifier
    WEIGHT_BODY = 0.25        # Body proportions
    WEIGHT_STRINGS = 0.20    # String/course count
    WEIGHT_FEATURES = 0.10   # Soundhole, nut, etc.
    WEIGHT_RATIOS = 0.10     # Body ratios

    # Confidence thresholds
    CONFIDENCE_HIGH = 0.8
    CONFIDENCE_MEDIUM = 0.6
    CONFIDENCE_LOW = 0.4
    ML_BOOST_THRESHOLD = 0.7  # Below this, use ML assistance

    def __init__(
        self,
        profiles: Optional[List[InstrumentProfile]] = None,
        enable_ml_boost: bool = True
    ):
        """
        Initialize classifier.

        Args:
            profiles: Custom profile list (default: all Latin American)
            enable_ml_boost: Enable ML-assisted classification for low confidence
        """
        self.profiles = profiles or ALL_PROFILES
        self.enable_ml_boost = enable_ml_boost
        self._ml_model = None

        logger.info(f"Initialized classifier with {len(self.profiles)} profiles")

    def classify(
        self,
        scale_length_mm: Optional[float] = None,
        body_length_mm: Optional[float] = None,
        lower_bout_width_mm: Optional[float] = None,
        upper_bout_width_mm: Optional[float] = None,
        waist_width_mm: Optional[float] = None,
        soundhole_diameter_mm: Optional[float] = None,
        nut_width_mm: Optional[float] = None,
        string_count: Optional[int] = None,
        fret_count: Optional[int] = None
    ) -> ClassificationResult:
        """
        Classify instrument from measurements.

        Args:
            scale_length_mm: Scale length (nut to bridge)
            body_length_mm: Total body length
            lower_bout_width_mm: Lower bout width
            upper_bout_width_mm: Upper bout width
            waist_width_mm: Waist width
            soundhole_diameter_mm: Soundhole diameter
            nut_width_mm: Nut width
            string_count: Number of strings
            fret_count: Number of frets

        Returns:
            ClassificationResult with ranked candidates
        """
        measurements = ExtractedMeasurements(
            scale_length_mm=scale_length_mm,
            body_length_mm=body_length_mm,
            lower_bout_width_mm=lower_bout_width_mm,
            upper_bout_width_mm=upper_bout_width_mm,
            waist_width_mm=waist_width_mm,
            soundhole_diameter_mm=soundhole_diameter_mm,
            nut_width_mm=nut_width_mm,
            string_count=string_count,
            fret_count=fret_count
        )
        measurements.calculate_ratios()

        return self._classify_from_measurements(measurements)

    def classify_from_extraction(
        self,
        extraction_result: Any,
        ocr_dimensions: Optional[List[Dict]] = None
    ) -> ClassificationResult:
        """
        Classify instrument from extraction result.

        Args:
            extraction_result: ExtractionResult from vectorizer
            ocr_dimensions: Optional OCR-extracted dimensions

        Returns:
            ClassificationResult
        """
        measurements = self._extract_measurements(extraction_result, ocr_dimensions)
        return self._classify_from_measurements(measurements)

    def _classify_from_measurements(
        self,
        measurements: ExtractedMeasurements
    ) -> ClassificationResult:
        """Core classification logic."""
        candidates = []

        for profile in self.profiles:
            candidate = self._score_profile(profile, measurements)
            if candidate.confidence > 0.1:  # Filter out very poor matches
                candidates.append(candidate)

        # Sort by confidence
        candidates.sort(key=lambda c: -c.confidence)

        # Determine primary and alternatives
        primary = candidates[0] if candidates else None
        alternatives = candidates[1:5] if len(candidates) > 1 else []

        method = "dimensional"

        # ML boost for low confidence
        if self.enable_ml_boost and primary and primary.confidence < self.ML_BOOST_THRESHOLD:
            ml_result = self._apply_ml_boost(measurements, candidates)
            if ml_result:
                primary, alternatives = ml_result
                method = "ml_assisted"

        return ClassificationResult(
            primary=primary,
            alternatives=alternatives,
            measurements_used=measurements.to_dict(),
            classification_method=method
        )

    def _score_profile(
        self,
        profile: InstrumentProfile,
        measurements: ExtractedMeasurements
    ) -> ClassificationCandidate:
        """Score a profile against measurements."""
        scores = {}
        notes = []
        total_weight = 0.0
        weighted_score = 0.0

        # Scale length score
        if measurements.scale_length_mm:
            scale_score = profile.matches_scale(measurements.scale_length_mm)
            scores['scale'] = scale_score
            weighted_score += scale_score * self.WEIGHT_SCALE
            total_weight += self.WEIGHT_SCALE

            if scale_score >= 0.9:
                notes.append(f"Scale length matches {profile.name} typical")
            elif scale_score < 0.5:
                notes.append(f"Scale length atypical for {profile.name}")

        # Body width score
        if measurements.lower_bout_width_mm:
            body_score = profile.matches_body_width(measurements.lower_bout_width_mm)
            scores['body'] = body_score
            weighted_score += body_score * self.WEIGHT_BODY
            total_weight += self.WEIGHT_BODY

        # String count (definitive for some instruments)
        if measurements.string_count:
            string_score = self._score_string_count(
                profile, measurements.string_count
            )
            scores['strings'] = string_score
            weighted_score += string_score * self.WEIGHT_STRINGS
            total_weight += self.WEIGHT_STRINGS

            if string_score == 1.0:
                notes.append(f"{measurements.string_count} strings matches {profile.name}")
            elif string_score < 0.3:
                notes.append(f"String count doesn't match {profile.name}")

        # Nut width
        if measurements.nut_width_mm:
            nut_score = self._score_dimension(
                measurements.nut_width_mm, profile.nut_width
            )
            scores['nut'] = nut_score
            weighted_score += nut_score * self.WEIGHT_FEATURES
            total_weight += self.WEIGHT_FEATURES

        # Body ratios
        if measurements.waist_ratio:
            ratio_score = self._score_waist_ratio(profile, measurements.waist_ratio)
            scores['ratio'] = ratio_score
            weighted_score += ratio_score * self.WEIGHT_RATIOS
            total_weight += self.WEIGHT_RATIOS

        # Calculate final confidence
        if total_weight > 0:
            confidence = weighted_score / total_weight
        else:
            confidence = 0.0

        # Boost confidence if multiple strong indicators
        strong_scores = sum(1 for s in scores.values() if s >= 0.8)
        if strong_scores >= 3:
            confidence = min(confidence * 1.15, 1.0)
            notes.append("Multiple strong matches")

        return ClassificationCandidate(
            profile=profile,
            confidence=confidence,
            scores=scores,
            notes=notes
        )

    def _score_string_count(
        self,
        profile: InstrumentProfile,
        string_count: int
    ) -> float:
        """Score string count match."""
        if string_count == profile.string_count:
            return 1.0

        # Allow for paired/unpaired variations
        if string_count == profile.course_count:
            return 0.7  # Could be listing courses not strings

        # Within 2 strings (variation)
        diff = abs(string_count - profile.string_count)
        if diff <= 2:
            return 0.5

        return 0.0

    def _score_dimension(
        self,
        measured: float,
        expected: Tuple[float, float, float],
        tolerance_pct: float = 0.1
    ) -> float:
        """Score a dimension against expected range."""
        min_val, typical, max_val = expected

        if abs(measured - typical) < typical * 0.02:
            return 1.0

        if min_val <= measured <= max_val:
            distance = abs(measured - typical)
            range_size = max(typical - min_val, max_val - typical)
            return max(0.6, 1.0 - (distance / range_size) * 0.4)

        expanded_min = min_val * (1 - tolerance_pct)
        expanded_max = max_val * (1 + tolerance_pct)

        if expanded_min <= measured <= expanded_max:
            return 0.4

        return 0.0

    def _score_waist_ratio(
        self,
        profile: InstrumentProfile,
        measured_ratio: float
    ) -> float:
        """Score waist-to-bout ratio."""
        # Calculate expected ratio
        min_waist = profile.waist_width[0]
        typical_waist = profile.waist_width[1]
        max_waist = profile.waist_width[2]

        min_bout = profile.lower_bout_width[0]
        typical_bout = profile.lower_bout_width[1]
        max_bout = profile.lower_bout_width[2]

        expected_ratio = typical_waist / typical_bout
        ratio_diff = abs(measured_ratio - expected_ratio)

        if ratio_diff < 0.02:
            return 1.0
        elif ratio_diff < 0.05:
            return 0.8
        elif ratio_diff < 0.10:
            return 0.5
        else:
            return 0.2

    def _extract_measurements(
        self,
        extraction_result: Any,
        ocr_dimensions: Optional[List[Dict]]
    ) -> ExtractedMeasurements:
        """Extract measurements from extraction result and OCR."""
        measurements = ExtractedMeasurements()

        # From OCR dimensions
        if ocr_dimensions:
            for dim in ocr_dimensions:
                label = dim.get('label', '').lower()
                value = dim.get('value_mm')

                if not value:
                    continue

                if 'scale' in label or 'nut to bridge' in label:
                    measurements.scale_length_mm = value
                elif 'body length' in label or 'body_length' in label:
                    measurements.body_length_mm = value
                elif 'lower bout' in label:
                    measurements.lower_bout_width_mm = value
                elif 'upper bout' in label:
                    measurements.upper_bout_width_mm = value
                elif 'waist' in label:
                    measurements.waist_width_mm = value
                elif 'soundhole' in label or 'sound hole' in label:
                    measurements.soundhole_diameter_mm = value
                elif 'nut' in label and 'width' in label:
                    measurements.nut_width_mm = value

        # From extraction result
        if hasattr(extraction_result, 'ocr_dimensions'):
            for dim in extraction_result.ocr_dimensions:
                if isinstance(dim, dict):
                    text = dim.get('raw_text', '').lower()
                    value = dim.get('value_mm')

                    if value and not measurements.scale_length_mm:
                        if 'scale' in text:
                            measurements.scale_length_mm = value

        measurements.calculate_ratios()
        return measurements

    def _apply_ml_boost(
        self,
        measurements: ExtractedMeasurements,
        candidates: List[ClassificationCandidate]
    ) -> Optional[Tuple[ClassificationCandidate, List[ClassificationCandidate]]]:
        """
        Apply ML model to boost classification confidence.

        Currently a stub - will be implemented with actual ML model.
        """
        # TODO: Implement neural network boost
        # For now, return None to indicate no ML boost applied
        logger.debug("ML boost requested but not yet implemented")
        return None

    def get_profile(self, name: str) -> Optional[InstrumentProfile]:
        """Get profile by name."""
        return get_profile_by_name(name)

    def list_instruments(self) -> List[str]:
        """List all supported instrument names."""
        return [p.name for p in self.profiles]
