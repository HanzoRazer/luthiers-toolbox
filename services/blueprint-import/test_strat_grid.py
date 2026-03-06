"""
Test GridZoneClassifier on Stratocaster Grid Image
===================================================

Loads the Stratocaster overlay image from STEM Guitar PPTX and
classifies the body contour using the GridZoneClassifier.
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from classifiers.grid_zone import (
    GridZoneClassifier,
    ELECTRIC_GUITAR_GRID
)


def extract_guitar_contour(image_path: str):
    """Extract the main guitar body contour from the image."""
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    height, width = img.shape[:2]
    print(f"Image size: {width}x{height}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # The guitar body is the semi-transparent overlay on the grid
    # We need to detect the guitar outline (darker pixels)

    # Threshold to find the guitar body (it's lighter than the grid lines)
    # The guitar appears as a cream/white color over the grid
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Invert to get guitar as white
    thresh_inv = cv2.bitwise_not(thresh)

    # Find contours
    contours, _ = cv2.findContours(thresh_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        # Try different approach - detect the guitar outline by color
        # The guitar has a tan/cream color
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Define range for tan/cream color
        lower = np.array([10, 20, 150])
        upper = np.array([30, 100, 255])
        mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print("No contours found with color detection, trying edge detection...")
        # Edge detection approach
        edges = cv2.Canny(gray, 50, 150)

        # Dilate to connect edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort by area, get largest (should be guitar body)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    print(f"Found {len(contours)} contours")
    for i, c in enumerate(contours[:5]):
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        print(f"  Contour {i}: area={area:.0f}, bbox=({x},{y},{w},{h})")

    return contours, img, width, height


def analyze_with_grid_classifier(contours, width, height):
    """Classify contours using GridZoneClassifier."""
    classifier = GridZoneClassifier()

    print("\n" + "="*60)
    print("GRID ZONE CLASSIFICATION RESULTS")
    print("="*60)

    results = []

    for i, contour in enumerate(contours[:5]):  # Top 5 contours
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        # Normalize to grid coordinates
        x_min = x / width
        y_min = y / height
        x_max = (x + w) / width
        y_max = (y + h) / height

        # Classify
        result = classifier.classify_bbox(x_min, y_min, x_max, y_max)
        results.append((contour, result))

        print(f"\nContour {i} (area={area:.0f} px)")
        print(f"  Bbox (normalized): ({x_min:.3f}, {y_min:.3f}) - ({x_max:.3f}, {y_max:.3f})")
        print(f"  Primary Category: {result.primary_category}")
        print(f"  Primary Zone: {result.primary_zone.zone_type.value if result.primary_zone else 'None'}")
        print(f"  Symmetry Score: {result.symmetry_score:.3f}")
        print(f"  Wing Extend Left: {result.wing_extend_left:.3f}")
        print(f"  Wing Extend Right: {result.wing_extend_right:.3f}")
        print(f"  Proportion Valid: {result.proportion_valid}")
        print(f"  Is Confident: {result.is_confident}")
        print(f"  Zones Overlapped: {len(result.all_zones)}")

        if result.all_zones:
            print("  Zone Overlaps:")
            for zm in result.all_zones[:5]:
                print(f"    - {zm.zone.zone_type.value}: {zm.overlap:.1%}")

        if result.notes:
            print("  Notes:")
            for note in result.notes:
                print(f"    - {note}")

    return results


def create_visualization(img, results, output_path):
    """Create visualization with zones overlaid."""
    height, width = img.shape[:2]

    # Create zone overlay
    classifier = GridZoneClassifier()
    zone_overlay = classifier.visualize_zones(width, height)

    # Blend with original
    blended = cv2.addWeighted(img, 0.6, zone_overlay, 0.4, 0)

    # Draw contours and their classifications
    for contour, result in results:
        x, y, w, h = cv2.boundingRect(contour)

        # Color based on category
        color = (0, 255, 0) if result.is_confident else (0, 165, 255)

        # Draw bbox
        cv2.rectangle(blended, (x, y), (x+w, y+h), color, 2)

        # Draw label
        label = f"{result.primary_category}"
        cv2.putText(blended, label, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Draw contour
        cv2.drawContours(blended, [contour], -1, (255, 0, 0), 1)

    # Save
    cv2.imwrite(output_path, blended)
    print(f"\nVisualization saved to: {output_path}")

    return blended


def main():
    # Path to Stratocaster grid image
    image_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\STEM Guitar\pptx_extract\ppt\media\image19.png"

    if not Path(image_path).exists():
        print(f"Image not found: {image_path}")
        return

    print("="*60)
    print("STRATOCASTER GRID IMAGE ANALYSIS")
    print("="*60)
    print(f"Image: {image_path}")

    # Extract contours
    contours, img, width, height = extract_guitar_contour(image_path)

    if not contours:
        print("No contours found!")
        return

    # Classify with grid zones
    results = analyze_with_grid_classifier(contours, width, height)

    # Create visualization
    output_path = str(Path(image_path).parent / "strat_grid_classified.png")
    create_visualization(img, results, output_path)

    # Print ML features for largest contour
    if results:
        print("\n" + "="*60)
        print("ML FEATURES (Largest Contour)")
        print("="*60)
        _, result = results[0]
        for key, value in sorted(result.ml_features.items()):
            print(f"  {key}: {value:.4f}")


if __name__ == "__main__":
    main()
