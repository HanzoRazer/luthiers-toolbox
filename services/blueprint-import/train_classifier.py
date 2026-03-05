#!/usr/bin/env python3
"""
Bootstrap ML classifier from rule-based pseudo-labels.
Trains on multiple blueprints using rule-based classification as ground truth.
"""
import sys
from pathlib import Path
import numpy as np
import joblib

# Add blueprint-import to path
sys.path.insert(0, str(Path(__file__).parent))

from vectorizer_phase3 import (
    Phase3Vectorizer, MLContourClassifier, ContourCategory,
    SKLEARN_AVAILABLE
)

if not SKLEARN_AVAILABLE:
    print("ERROR: sklearn required. Install with: pip install scikit-learn")
    sys.exit(1)

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score


def collect_training_data(pdf_paths: list[str], dpi: int = 400) -> tuple[np.ndarray, np.ndarray]:
    """Extract features and labels from multiple blueprints."""
    vectorizer = Phase3Vectorizer(dpi=dpi)
    ml_helper = MLContourClassifier()  # For feature extraction
    mm_per_px = 25.4 / dpi  # Calculate mm per pixel from DPI
    all_features = []
    all_labels = []

    for pdf_path in pdf_paths:
        path = Path(pdf_path)
        if not path.exists():
            print(f"  SKIP: {path.name} (not found)")
            continue

        print(f"  Processing: {path.name}")
        try:
            result = vectorizer.extract(str(path))

            # Iterate over contours_by_category dict
            for category_name, contour_list in result.contours_by_category.items():
                # Skip page borders and small features
                if category_name in ('page_border', 'small_feature'):
                    continue

                for contour_info in contour_list:
                    # Extract features from raw contour
                    features = ml_helper.extract_features(
                        contour_info.contour,
                        mm_per_px
                    )
                    all_features.append(features)
                    all_labels.append(category_name)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    return np.array(all_features), np.array(all_labels)


def train_model(X: np.ndarray, y: np.ndarray, output_path: str):
    """Train RandomForest classifier and save."""
    print(f"\nTraining on {len(X)} samples, {len(set(y))} classes...")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )

    # Cross-validation
    scores = cross_val_score(model, X_scaled, y, cv=5)
    print(f"Cross-validation accuracy: {scores.mean():.3f} (+/- {scores.std()*2:.3f})")

    # Train on full data
    model.fit(X_scaled, y)

    # Save model and scaler
    joblib.dump(model, output_path)
    scaler_path = Path(output_path).with_suffix('.scaler')
    joblib.dump(scaler, str(scaler_path))

    print(f"\nSaved: {output_path}")
    print(f"Saved: {scaler_path}")

    # Feature importances
    print("\nTop 5 features:")
    feature_names = [
        'w_mm', 'h_mm', 'area', 'perimeter', 'circularity', 'aspect',
        'convexity', 'solidity', 'extent', 'hu0', 'hu1', 'hu2', 'hu3',
        'hu4', 'hu5', 'hu6', 'point_count', 'max_dim', 'min_dim',
        'bbox_area', 'compactness'
    ]
    importances = list(zip(feature_names, model.feature_importances_))
    importances.sort(key=lambda x: -x[1])
    for name, imp in importances[:5]:
        print(f"  {name}: {imp:.3f}")


def main():
    # Find training blueprints
    guitar_plans = Path(r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans")

    training_pdfs = [
        guitar_plans / "04-Gibson-SG-Plans.pdf",
        guitar_plans / "01-Gibson-SG-Complete-Template.pdf",
        guitar_plans / "03-Gibson-SG-Body-Headstock.pdf",
        guitar_plans / "01-Gibson-CS-356.pdf",
        guitar_plans / "00-Gibson-1963-SG-JR.pdf",
    ]

    # Also check Downloads for other blueprints
    downloads = Path(r"C:\Users\thepr\Downloads")
    for pattern in ["*Jazzmaster*.pdf", "*Stratocaster*.pdf", "*Telecaster*.pdf"]:
        training_pdfs.extend(downloads.glob(pattern))

    print(f"Found {len(training_pdfs)} training blueprints\n")

    # Collect data
    print("Collecting training data...")
    X, y = collect_training_data([str(p) for p in training_pdfs])

    if len(X) == 0:
        print("\nERROR: No samples collected. Check blueprint paths.")
        sys.exit(1)

    if len(X) < 50:
        print(f"\nWARNING: Only {len(X)} samples. More blueprints recommended.")

    # Show class distribution
    unique, counts = np.unique(y, return_counts=True)
    print("\nClass distribution:")
    for label, count in zip(unique, counts):
        print(f"  {label}: {count}")

    # Train
    output_path = Path(__file__).parent / "contour_classifier.joblib"
    train_model(X, y, str(output_path))

    print("\n" + "="*60)
    print("To use: python vectorizer_phase3.py input.pdf --ml-model contour_classifier.joblib")


if __name__ == "__main__":
    main()
