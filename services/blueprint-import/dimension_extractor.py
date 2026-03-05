"""
Blueprint Dimension Extractor
Uses EasyOCR to extract and parse dimensions from blueprint images.

Handles common dimension formats:
- Fractions: 17 3/4", 1/2"
- Decimals: 445.5mm, 21.5"
- Mixed: 17-3/4"
- Plain numbers with nearby units
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
import json

import numpy as np
import cv2

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDimension:
    """A single extracted dimension with parsed value"""
    raw_text: str           # Original OCR text
    value_mm: float         # Converted to millimeters
    value_inches: float     # Converted to inches
    unit: str               # Detected unit ('mm', 'in', 'unknown')
    confidence: float       # OCR confidence (0-1)
    bbox: Tuple[int, int, int, int]  # Bounding box (x, y, w, h)
    context: str = ""       # Nearby text for context (e.g., "body width")


@dataclass
class BlueprintDimensions:
    """Collection of extracted dimensions from a blueprint"""
    source_file: str
    dimensions: List[ExtractedDimension] = field(default_factory=list)
    raw_texts: List[str] = field(default_factory=list)

    # Categorized dimensions (populated after analysis)
    body_length_mm: Optional[float] = None
    upper_bout_mm: Optional[float] = None
    lower_bout_mm: Optional[float] = None
    waist_mm: Optional[float] = None
    scale_length_mm: Optional[float] = None
    soundhole_mm: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/database storage"""
        return {
            'source_file': self.source_file,
            'dimensions': [
                {
                    'raw_text': d.raw_text,
                    'value_mm': d.value_mm,
                    'value_inches': d.value_inches,
                    'unit': d.unit,
                    'confidence': d.confidence,
                    'bbox': d.bbox,
                    'context': d.context
                }
                for d in self.dimensions
            ],
            'body_length_mm': self.body_length_mm,
            'upper_bout_mm': self.upper_bout_mm,
            'lower_bout_mm': self.lower_bout_mm,
            'waist_mm': self.waist_mm,
            'scale_length_mm': self.scale_length_mm,
            'soundhole_mm': self.soundhole_mm,
        }


class DimensionParser:
    """Parse dimension strings into numeric values"""

    # Common fraction mappings
    FRACTIONS = {
        '1/16': 1/16, '1/8': 1/8, '3/16': 3/16, '1/4': 1/4,
        '5/16': 5/16, '3/8': 3/8, '7/16': 7/16, '1/2': 1/2,
        '9/16': 9/16, '5/8': 5/8, '11/16': 11/16, '3/4': 3/4,
        '13/16': 13/16, '7/8': 7/8, '15/16': 15/16,
    }

    # Valid dimension ranges for guitar/instrument blueprints (in mm)
    # These help filter out false positives
    MIN_DIMENSION_MM = 1.0       # Smallest valid dimension (1mm)
    MAX_DIMENSION_MM = 2000.0    # Largest valid dimension (2 meters)

    # Year range to filter out (common false positives)
    YEAR_MIN = 1800
    YEAR_MAX = 2100

    # Patterns for dimension matching
    PATTERNS = [
        # Fraction with whole number: "17 3/4" or "17-3/4"
        (r'(\d+)\s*[-\s]\s*(\d+)/(\d+)\s*["\']?', 'fraction_mixed'),
        # Simple fraction: "3/4" or "3/4""
        (r'(\d+)/(\d+)\s*["\']?', 'fraction'),
        # Decimal with unit: "445.5mm" or "17.5""
        (r'(\d+\.?\d*)\s*(mm|cm|in|inch|inches|"|\')?\s*', 'decimal'),
        # Just numbers (context needed): "445" or "17"
        (r'(\d+\.?\d*)', 'number'),
    ]

    # Label patterns - dimensions that follow descriptive labels
    # e.g., "Girth: 3.30", "Scale length is 24.625", "Waist: 5.40"
    LABEL_PATTERNS = [
        # "Label: value" pattern
        (r'(?:scale\s*length|body\s*length|width|girth|waist|depth|thickness|radius|diameter|height|length|nut|bridge|fret|bout)\s*[:\s]+(\d+\.?\d*)', 'labeled'),
        # "Label is value" pattern
        (r'(?:scale\s*length|body\s*length|width|girth|waist|depth|thickness|radius|diameter|height|length)\s+is\s+(\d+\.?\d*)', 'labeled_is'),
        # "value" after "nut to bridge" type phrases
        (r'(?:nut\s+to\s+bridge|scale)\s*[:\s]+(\d+\.?\d*)', 'labeled_scale'),
        # "value Nut to Bridge" - reversed order
        (r'(\d+\.?\d*)\s+(?:nut\s+to\s+bridge|scale\s+length)', 'value_first'),
        # Semicolon separated: "Label; value"
        (r'(?:cover|plate|thickness|depth|width)\s*[;:]\s*(\d+\.?\d*)', 'semicolon'),
        # Leading text before dimension: "text 0.039" at end
        (r'\w+\s*[;:]\s*(\d+\.?\d*)\s*$', 'trailing_value'),
    ]

    MM_PER_INCH = 25.4

    def parse(self, text: str) -> Optional[Tuple[float, str]]:
        """
        Parse dimension text into (value_mm, unit)

        Args:
            text: Raw dimension text like "17 3/4"" or "445mm"

        Returns:
            Tuple of (value in mm, detected unit) or None if unparseable
        """
        text = text.strip().lower()

        # Try fraction with whole number first: "17 3/4"
        match = re.match(r'(\d+)\s*[-\s]\s*(\d+)/(\d+)\s*(["\']|mm|cm|in)?', text)
        if match:
            whole = int(match.group(1))
            num = int(match.group(2))
            denom = int(match.group(3))
            unit_char = match.group(4) or ''
            value = whole + (num / denom)
            unit = self._detect_unit(unit_char, value)
            return self._to_mm(value, unit), unit

        # Simple fraction: "3/4"
        match = re.match(r'^(\d+)/(\d+)\s*(["\']|mm|cm|in)?$', text)
        if match:
            num = int(match.group(1))
            denom = int(match.group(2))
            unit_char = match.group(3) or ''
            value = num / denom
            unit = self._detect_unit(unit_char, value)
            return self._to_mm(value, unit), unit

        # Decimal with unit: "445.5mm" or "17.5""
        match = re.match(r'^(\d+\.?\d*)\s*(mm|cm|in|inch|inches|"|\')?\s*$', text)
        if match:
            value = float(match.group(1))
            unit_char = match.group(2) or ''
            unit = self._detect_unit(unit_char, value)
            return self._to_mm(value, unit), unit

        # Leading decimal: ".010" or ".5mm"
        match = re.match(r'^\.(\d+)\s*(mm|cm|in|inch|inches|"|\')?\s*$', text)
        if match:
            value = float('0.' + match.group(1))
            unit_char = match.group(2) or ''
            unit = self._detect_unit(unit_char, value)
            return self._to_mm(value, unit), unit

        return None

    def parse_contextual(self, text: str) -> List[Tuple[float, str, str]]:
        """
        Extract dimensions from contextual text (e.g., "Scale length is 24.625").

        Args:
            text: Full text that may contain embedded dimensions

        Returns:
            List of (value_mm, unit, label) tuples
        """
        results = []
        text_lower = text.lower()

        # Try labeled patterns first - these extract meaningful dimensions with context
        for pattern, ptype in self.LABEL_PATTERNS:
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                try:
                    value = float(match.group(1))
                    # Extract label from the matched portion
                    full_match = match.group(0)
                    label = full_match.split(':')[0] if ':' in full_match else full_match.rsplit(None, 1)[0]
                    label = label.strip()

                    unit = self._detect_unit('', value)
                    value_mm = self._to_mm(value, unit)

                    if self.MIN_DIMENSION_MM <= value_mm <= self.MAX_DIMENSION_MM:
                        results.append((value_mm, unit, label))
                except (ValueError, IndexError):
                    continue

        # Also look for standalone fraction patterns in text
        # e.g., '1/4" Jack' -> 1/4"
        fraction_pattern = r'(\d+)/(\d+)\s*(["\'])'
        for match in re.finditer(fraction_pattern, text):
            try:
                num = int(match.group(1))
                denom = int(match.group(2))
                unit_char = match.group(3)
                value = num / denom
                unit = self._detect_unit(unit_char, value)
                value_mm = self._to_mm(value, unit)

                if self.MIN_DIMENSION_MM <= value_mm <= self.MAX_DIMENSION_MM:
                    results.append((value_mm, unit, 'fraction'))
            except (ValueError, ZeroDivisionError):
                continue

        return results

    def _detect_unit(self, unit_char: str, value: float) -> str:
        """Detect unit from character or infer from value magnitude"""
        if unit_char in ['"', "'", 'in', 'inch', 'inches']:
            return 'in'
        if unit_char == 'mm':
            return 'mm'
        if unit_char == 'cm':
            return 'cm'

        # Infer from magnitude - guitar dimensions are typically:
        # - Body length: 350-550mm (14-22")
        # - Width: 250-450mm (10-18")
        # - Depth: 75-125mm (3-5")
        # If value > 30, likely mm; if < 30, likely inches
        if value > 30:
            return 'mm'
        else:
            return 'in'

    def _to_mm(self, value: float, unit: str) -> float:
        """Convert value to millimeters"""
        if unit == 'in':
            return value * self.MM_PER_INCH
        elif unit == 'cm':
            return value * 10
        else:  # mm or unknown
            return value

    def is_valid_dimension(self, raw_text: str, value_mm: float) -> bool:
        """
        Check if a parsed dimension is valid (not a false positive)

        Filters out:
        - Years (1800-2100)
        - Values outside reasonable instrument dimension range
        - Pure integers that look like page numbers, counts, etc.
        """
        text = raw_text.strip()

        # Filter out years (4-digit numbers in year range without units)
        if re.match(r'^\d{4}$', text):
            try:
                year = int(text)
                if self.YEAR_MIN <= year <= self.YEAR_MAX:
                    logger.debug(f"Filtered year: {text}")
                    return False
            except ValueError:
                pass

        # Filter out values outside reasonable range
        if value_mm < self.MIN_DIMENSION_MM or value_mm > self.MAX_DIMENSION_MM:
            logger.debug(f"Filtered out-of-range: {text} -> {value_mm}mm")
            return False

        # Filter out large round numbers without units (likely not dimensions)
        # e.g., "1000", "5000" - these are often page numbers, codes, etc.
        if re.match(r'^\d{4,}$', text) and value_mm > 500:
            logger.debug(f"Filtered large integer: {text}")
            return False

        # Filter out single digits (usually not dimensions)
        if re.match(r'^\d$', text):
            logger.debug(f"Filtered single digit: {text}")
            return False

        # Filter out likely serial numbers / codes (long digit sequences)
        if re.match(r'^\d{5,}$', text):
            logger.debug(f"Filtered serial/code: {text}")
            return False

        return True


class DimensionExtractor:
    """Extract dimensions from blueprint images using OCR"""

    def __init__(self, languages: List[str] = None):
        """
        Initialize extractor with EasyOCR

        Args:
            languages: List of language codes (default: ['en'])
        """
        import easyocr

        if languages is None:
            languages = ['en']

        logger.info(f"Initializing EasyOCR with languages: {languages}")
        self.reader = easyocr.Reader(languages, gpu=False)
        self.parser = DimensionParser()

    def extract_from_image(
        self,
        image_path: str,
        min_confidence: float = 0.3
    ) -> BlueprintDimensions:
        """
        Extract all dimensions from a blueprint image

        Args:
            image_path: Path to image file
            min_confidence: Minimum OCR confidence threshold

        Returns:
            BlueprintDimensions with extracted values
        """
        logger.info(f"Extracting dimensions from: {image_path}")

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Run OCR
        results = self.reader.readtext(image)
        logger.info(f"OCR found {len(results)} text regions")

        # Parse results
        dimensions = BlueprintDimensions(source_file=str(image_path))

        for bbox, text, confidence in results:
            dimensions.raw_texts.append(text)

            if confidence < min_confidence:
                continue

            # Calculate bounding box once
            pts = np.array(bbox)
            x, y = pts.min(axis=0).astype(int)
            x2, y2 = pts.max(axis=0).astype(int)
            dim_bbox = (int(x), int(y), int(x2 - x), int(y2 - y))

            # Try to parse as simple dimension first
            parsed = self.parser.parse(text)
            if parsed:
                value_mm, unit = parsed

                # Validate - filter out false positives
                if not self.parser.is_valid_dimension(text, value_mm):
                    continue

                dim = ExtractedDimension(
                    raw_text=text,
                    value_mm=value_mm,
                    value_inches=value_mm / 25.4,
                    unit=unit,
                    confidence=float(confidence),
                    bbox=dim_bbox
                )
                dimensions.dimensions.append(dim)
                logger.debug(f"Parsed: '{text}' -> {value_mm:.2f}mm ({unit})")
            else:
                # Try contextual parsing for text like "Scale length is 24.625"
                contextual = self.parser.parse_contextual(text)
                for value_mm, unit, label in contextual:
                    dim = ExtractedDimension(
                        raw_text=text,
                        value_mm=value_mm,
                        value_inches=value_mm / 25.4,
                        unit=unit,
                        confidence=float(confidence),
                        bbox=dim_bbox,
                        context=label
                    )
                    dimensions.dimensions.append(dim)
                    logger.debug(f"Contextual: '{text}' -> {value_mm:.2f}mm ({unit}, label={label})")

        logger.info(f"Extracted {len(dimensions.dimensions)} valid dimensions")

        # Sort by confidence
        dimensions.dimensions.sort(key=lambda d: -d.confidence)

        return dimensions

    def extract_with_context(
        self,
        image_path: str,
        min_confidence: float = 0.3,
        context_radius: int = 200
    ) -> BlueprintDimensions:
        """
        Extract dimensions with nearby text context

        Args:
            image_path: Path to image file
            min_confidence: Minimum OCR confidence
            context_radius: Pixel radius to search for context text

        Returns:
            BlueprintDimensions with context annotations
        """
        dimensions = self.extract_from_image(image_path, min_confidence)

        # Build spatial index of all text
        all_texts = []
        for bbox, text, conf in self.reader.readtext(cv2.imread(image_path)):
            pts = np.array(bbox)
            cx = pts[:, 0].mean()
            cy = pts[:, 1].mean()
            all_texts.append((cx, cy, text.lower()))

        # Find context for each dimension
        for dim in dimensions.dimensions:
            dim_cx = dim.bbox[0] + dim.bbox[2] / 2
            dim_cy = dim.bbox[1] + dim.bbox[3] / 2

            nearby = []
            for cx, cy, text in all_texts:
                dist = np.sqrt((cx - dim_cx)**2 + (cy - dim_cy)**2)
                if dist < context_radius and text != dim.raw_text.lower():
                    nearby.append(text)

            if nearby:
                dim.context = ' '.join(nearby[:3])  # First 3 nearby texts

        return dimensions


def extract_blueprint_dimensions(
    image_path: str,
    output_json: str = None
) -> Dict[str, Any]:
    """
    Convenience function to extract dimensions from a blueprint

    Args:
        image_path: Path to blueprint image
        output_json: Optional path to save JSON output

    Returns:
        Dictionary of extracted dimensions
    """
    extractor = DimensionExtractor()
    result = extractor.extract_with_context(image_path)

    data = result.to_dict()

    if output_json:
        with open(output_json, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved dimensions to: {output_json}")

    return data


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python dimension_extractor.py <image_path> [output.json]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else None

    result = extract_blueprint_dimensions(image_path, output_json)

    print(f"\nExtracted {len(result['dimensions'])} dimensions:")
    for dim in result['dimensions'][:20]:  # Show first 20
        print(f"  {dim['raw_text']:15} -> {dim['value_mm']:8.2f}mm  ({dim['unit']}, conf={dim['confidence']:.2f})")
