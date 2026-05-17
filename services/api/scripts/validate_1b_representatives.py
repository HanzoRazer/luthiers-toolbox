#!/usr/bin/env python3
"""
IBG Morphology Validation 1B — Representative Corpus Processing
================================================================

Processes 10 representative instruments through the morphology pipeline:
1. Generate HarvestRecord
2. Convert to BodyEvidence
3. Run Body Grid analysis
4. Emit MorphologyDescriptor
5. Generate validation overlays
6. Record failures/ambiguities

Focus: Discovering failures, ambiguities, weak primitives, and edge cases.

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Corpus Ingestion & Morphology Validation 1B
"""

import json
import sys
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add api directory to path
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

from app.instrument_geometry.body.ibg.morphology_harvest import (
    HarvestCoordinator,
    HarvestRecord,
    PDFInventoryScanner,
    generate_harvest_overlay,
    OverlayConfig,
)

# Representative instruments for 1B validation
REPRESENTATIVES = [
    {
        "id": "les_paul_59",
        "file": "Gibson-Les-Paul-59-Complete.pdf",
        "category": "single_cut",
        "expected_class": "ROUNDED_SINGLE_CUT",
        "notes": "Classic single-cutaway, carved top",
        "attention": ["carved top detection", "asymmetry handling"],
    },
    {
        "id": "sg_complete",
        "file": "01-Gibson-SG-Complete-Template.pdf",
        "category": "double_cut",
        "expected_class": "ROUNDED_DOUBLE_CUT",
        "notes": "Symmetric double-cutaway, thin body",
        "attention": ["horn detection", "cutaway symmetry"],
    },
    {
        "id": "stratocaster_62",
        "file": "Fender-Stratocaster-62.pdf",
        "category": "slab_body",
        "expected_class": "SLAB_BODY",
        "notes": "Slab body with contours, offset waist",
        "attention": ["contour detection", "waist offset"],
    },
    {
        "id": "jazzmaster_62",
        "file": "Fender-Jazzmaster-62-Body.pdf",
        "category": "offset",
        "expected_class": "OFFSET_DOUBLE_CUT",
        "notes": "Asymmetric offset body, distinctive waist",
        "attention": ["asymmetry handling", "offset detection", "waist behavior"],
    },
    {
        "id": "explorer_complete",
        "file": "Gibson-Explorer-05-Complete-Plans.pdf",
        "category": "angular",
        "expected_class": "ANGULAR_WEDGE",
        "notes": "Angular topology, no traditional bouts",
        "attention": ["angular primitive detection", "suppressed waist", "non-traditional zones"],
    },
    {
        "id": "dreadnought",
        "file": "A003-Dreadnought-MM.pdf",
        "category": "acoustic_dread",
        "expected_class": "ROUNDED_ACOUSTIC",
        "notes": "Traditional acoustic dreadnought",
        "attention": ["bout ratios", "waist detection", "symmetry"],
    },
    {
        "id": "classical_santos",
        "file": "Classical-Santos-Hernandez-MM.pdf",
        "category": "classical",
        "expected_class": "CLASSICAL_FIGURE_8",
        "notes": "Classical figure-8 proportions",
        "attention": ["bout proportions", "waist position", "classical vs acoustic"],
    },
    {
        "id": "es335_complete",
        "file": "Gibson-335/Gibson-335-Dot-Complete.pdf",
        "category": "semi_hollow",
        "expected_class": "ROUNDED_DOUBLE_CUT",
        "notes": "Semi-hollow with f-holes, double cutaway",
        "attention": ["f-hole detection", "hollow body handling", "cutaway behavior"],
    },
    {
        "id": "klein_ergonomic",
        "file": "Klein-Guitar-Plan.pdf",
        "category": "ergonomic",
        "expected_class": "HYBRID_FORM",
        "notes": "Ergonomic non-traditional shape",
        "attention": ["non-canonical morphology", "zone mapping failure", "hybrid detection"],
    },
    {
        "id": "cuatro_pr",
        "file": "El Cuatro/cuatro puertoriqueño.pdf",
        "category": "latin_folk",
        "expected_class": "ROUNDED_ACOUSTIC",
        "notes": "Puerto Rican cuatro, small acoustic",
        "attention": ["scale assumptions", "non-guitar morphology", "size handling"],
    },
]


@dataclass
class ValidationResult:
    """Result of validating one instrument."""
    instrument_id: str
    file_path: str
    category: str
    expected_class: str

    # Processing status
    pdf_readable: bool = False
    harvest_success: bool = False
    body_evidence_created: bool = False
    body_grid_success: bool = False
    overlay_generated: bool = False

    # Results
    actual_class: Optional[str] = None
    classification_confidence: float = 0.0
    centerline_confidence: float = 0.0
    asymmetry_score: float = 0.0
    zone_coverage: Dict[str, float] = field(default_factory=dict)
    primitives_detected: int = 0
    missing_regions: List[str] = field(default_factory=list)

    # Validation
    classification_match: bool = False

    # Failures and issues
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)

    # Human review notes
    attention_points: List[str] = field(default_factory=list)
    review_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FailureTaxonomyEntry:
    """Entry in the failure taxonomy."""
    failure_type: str
    instrument_id: str
    description: str
    severity: str  # critical, major, minor, observation
    category: str  # ocr, contour, centerline, zone, primitive, classification, etc.
    remediation_hint: Optional[str] = None


class Validation1BRunner:
    """Runs 1B validation on representative instruments."""

    def __init__(self, corpus_root: str, output_dir: str):
        self.corpus_root = Path(corpus_root)
        self.output_dir = Path(output_dir)
        self.records_dir = self.output_dir / "records"
        self.overlays_dir = self.output_dir / "overlays"

        self.coordinator = HarvestCoordinator()
        self.results: List[ValidationResult] = []
        self.failures: List[FailureTaxonomyEntry] = []

    def run_all(self) -> None:
        """Run validation on all representatives."""
        print("=" * 70)
        print("IBG Morphology Validation 1B — Representative Corpus")
        print("=" * 70)
        print(f"Corpus root: {self.corpus_root}")
        print(f"Output dir: {self.output_dir}")
        print(f"Representatives: {len(REPRESENTATIVES)}")
        print()

        # Check system status
        status = self.coordinator.check_systems()
        print("System status:")
        for name, info in status.items():
            avail = "available" if info["available"] else info.get("reason", "unavailable")
            print(f"  {name}: {avail}")
        print()

        for i, rep in enumerate(REPRESENTATIVES, 1):
            print(f"[{i}/{len(REPRESENTATIVES)}] Processing: {rep['id']}")
            print(f"    File: {rep['file']}")
            print(f"    Expected: {rep['expected_class']}")

            result = self.validate_instrument(rep)
            self.results.append(result)

            # Summary
            if result.harvest_success:
                match_str = "MATCH" if result.classification_match else "MISMATCH"
                print(f"    Result: {result.actual_class} ({match_str})")
                print(f"    Confidence: {result.classification_confidence:.2f}")
            else:
                print(f"    Result: FAILED")
                for err in result.errors[:3]:
                    print(f"      - {err}")
            print()

        # Generate reports
        self.save_results()
        self.generate_failure_taxonomy()
        self.generate_summary_report()

    def validate_instrument(self, rep: Dict) -> ValidationResult:
        """Validate a single instrument."""
        result = ValidationResult(
            instrument_id=rep["id"],
            file_path=rep["file"],
            category=rep["category"],
            expected_class=rep["expected_class"],
            attention_points=rep.get("attention", []),
        )

        # Resolve file path
        pdf_path = self.corpus_root / rep["file"]
        if not pdf_path.exists():
            result.errors.append(f"File not found: {pdf_path}")
            self._add_failure("file_not_found", rep["id"],
                            f"PDF not found: {rep['file']}", "critical", "io")
            return result

        result.pdf_readable = True

        # Step 1: Harvest
        try:
            harvest_result = self.coordinator.harvest_from_pdf(str(pdf_path))

            if harvest_result.success or harvest_result.partial:
                result.harvest_success = True
                record = harvest_result.record

                # Save harvest record
                record_path = self.records_dir / f"{rep['id']}_harvest.json"
                record.save(str(record_path))

                # Check for harvest issues
                if harvest_result.errors:
                    result.warnings.extend(harvest_result.errors)

            else:
                result.errors.append("Harvest failed: no data extracted")
                for err in harvest_result.errors:
                    result.errors.append(f"Harvest error: {err}")
                self._add_failure("harvest_failed", rep["id"],
                                "No morphology data extracted from PDF", "major", "extraction")
                return result

        except Exception as e:
            result.errors.append(f"Harvest exception: {e}")
            self._add_failure("harvest_exception", rep["id"],
                            str(e), "critical", "extraction")
            return result

        # Step 2: Convert to BodyEvidence
        try:
            body_evidence = record.to_body_evidence()
            if body_evidence and body_evidence.landmarks:
                result.body_evidence_created = True
                result.review_notes.append(f"Created {len(body_evidence.landmarks)} landmarks")
            else:
                result.warnings.append("No landmarks for BodyEvidence conversion")
                self._add_failure("no_landmarks", rep["id"],
                                "Could not create BodyEvidence landmarks", "major", "conversion")
        except Exception as e:
            result.errors.append(f"BodyEvidence conversion failed: {e}")
            self._add_failure("body_evidence_failed", rep["id"],
                            str(e), "major", "conversion")

        # Step 3: Body Grid analysis
        if result.body_evidence_created:
            try:
                from app.instrument_geometry.body.ibg.body_grid.morphology_descriptor import (
                    MorphologyAnalyzer
                )

                analyzer = MorphologyAnalyzer()
                descriptor = analyzer.analyze(body_evidence)

                result.body_grid_success = True

                # Extract results
                result.actual_class = descriptor.variant_match.morphology_class.value.upper()
                result.classification_confidence = descriptor.confidence
                result.centerline_confidence = descriptor.centerline.confidence
                result.asymmetry_score = descriptor.asymmetry.asymmetry_score
                result.primitives_detected = len(descriptor.primitives)
                result.missing_regions = descriptor.missing_regions

                # Zone coverage
                result.zone_coverage = descriptor.zone_coverage

                # Check classification match
                result.classification_match = (
                    result.actual_class == result.expected_class
                )

                if not result.classification_match:
                    self._add_failure("classification_mismatch", rep["id"],
                                    f"Expected {result.expected_class}, got {result.actual_class}",
                                    "major", "classification")
                    result.ambiguities.append(
                        f"Classification mismatch: expected {result.expected_class}, "
                        f"got {result.actual_class} (conf: {result.classification_confidence:.2f})"
                    )

                # Check for low confidence
                if result.classification_confidence < 0.5:
                    self._add_failure("low_confidence", rep["id"],
                                    f"Classification confidence only {result.classification_confidence:.2f}",
                                    "minor", "classification")
                    result.warnings.append(f"Low classification confidence: {result.classification_confidence:.2f}")

                # Check for high asymmetry on expected-symmetric instruments
                if result.asymmetry_score > 0.3 and rep["category"] not in ["offset", "ergonomic"]:
                    result.ambiguities.append(
                        f"High asymmetry ({result.asymmetry_score:.2f}) on expected-symmetric instrument"
                    )

                # Check for missing regions
                if result.missing_regions:
                    result.warnings.append(f"Missing regions: {', '.join(result.missing_regions)}")

                # Save descriptor
                desc_path = self.records_dir / f"{rep['id']}_descriptor.json"
                with open(desc_path, 'w') as f:
                    json.dump(descriptor.to_dict(), f, indent=2)

            except Exception as e:
                result.errors.append(f"Body Grid analysis failed: {e}")
                self._add_failure("body_grid_failed", rep["id"],
                                str(e), "major", "analysis")
                traceback.print_exc()

        # Step 4: Generate overlay
        try:
            overlay_path = self.overlays_dir / f"{rep['id']}_validation.png"
            config = OverlayConfig(
                width=800,
                height=1000,
                show_dimensions=True,
                show_review_status=True,
            )

            generated = generate_harvest_overlay(record, str(overlay_path), config)
            if generated:
                result.overlay_generated = True
            else:
                result.warnings.append("Overlay generation failed (PIL not available?)")
        except Exception as e:
            result.warnings.append(f"Overlay generation error: {e}")

        return result

    def _add_failure(self, failure_type: str, instrument_id: str,
                    description: str, severity: str, category: str,
                    remediation: Optional[str] = None) -> None:
        """Add entry to failure taxonomy."""
        self.failures.append(FailureTaxonomyEntry(
            failure_type=failure_type,
            instrument_id=instrument_id,
            description=description,
            severity=severity,
            category=category,
            remediation_hint=remediation,
        ))

    def save_results(self) -> None:
        """Save all validation results."""
        results_path = self.output_dir / "validation_results.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "corpus_root": str(self.corpus_root),
            "total_instruments": len(self.results),
            "successful_harvests": sum(1 for r in self.results if r.harvest_success),
            "classification_matches": sum(1 for r in self.results if r.classification_match),
            "results": [r.to_dict() for r in self.results],
        }

        with open(results_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Results saved: {results_path}")

    def generate_failure_taxonomy(self) -> None:
        """Generate MORPHOLOGY_FAILURE_TAXONOMY.md."""
        # Navigate from services/api to repo root, then to docs/governance
        repo_root = self.output_dir.parent.parent.parent.parent.parent.parent.parent.parent.parent
        taxonomy_path = repo_root / "docs" / "governance" / "MORPHOLOGY_FAILURE_TAXONOMY.md"

        # Group failures by category
        by_category: Dict[str, List[FailureTaxonomyEntry]] = {}
        for f in self.failures:
            by_category.setdefault(f.category, []).append(f)

        lines = [
            "# Morphology Failure Taxonomy",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
            "**Sprint:** IBG Corpus Ingestion & Morphology Validation 1B",
            "**Status:** ACTIVE — Updated during validation",
            "",
            "---",
            "",
            "## Purpose",
            "",
            "Tracks failure modes discovered during morphology validation.",
            "This taxonomy is essential for vectorizer robustness improvements.",
            "",
            "---",
            "",
            "## Failure Summary",
            "",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| Critical | {sum(1 for f in self.failures if f.severity == 'critical')} |",
            f"| Major | {sum(1 for f in self.failures if f.severity == 'major')} |",
            f"| Minor | {sum(1 for f in self.failures if f.severity == 'minor')} |",
            f"| Observation | {sum(1 for f in self.failures if f.severity == 'observation')} |",
            "",
            "---",
            "",
            "## Failures by Category",
            "",
        ]

        category_descriptions = {
            "io": "File I/O and Access",
            "extraction": "PDF/Image Extraction",
            "conversion": "Data Conversion",
            "analysis": "Body Grid Analysis",
            "classification": "Morphology Classification",
            "ocr": "OCR and Text Detection",
            "contour": "Contour Detection",
            "centerline": "Centerline Detection",
            "zone": "Zone Assignment",
            "primitive": "Primitive Detection",
            "asymmetry": "Asymmetry Handling",
            "topology": "Topology Handling",
        }

        for category, failures in sorted(by_category.items()):
            cat_name = category_descriptions.get(category, category.title())
            lines.append(f"### {cat_name}")
            lines.append("")
            lines.append("| Type | Instrument | Severity | Description |")
            lines.append("|------|------------|----------|-------------|")

            for f in failures:
                desc = f.description[:60] + "..." if len(f.description) > 60 else f.description
                lines.append(f"| {f.failure_type} | {f.instrument_id} | {f.severity} | {desc} |")

            lines.append("")

        # Add expected failure categories (even if empty)
        lines.extend([
            "---",
            "",
            "## Expected Failure Categories (Reference)",
            "",
            "These categories should be tracked during morphology validation:",
            "",
            "| Category | Description |",
            "|----------|-------------|",
            "| OCR failures | Text detection issues in scanned plans |",
            "| Contour fragmentation | Incomplete or broken contour detection |",
            "| Centerline ambiguity | Cannot determine body centerline |",
            "| Zone misclassification | Wrong zone assigned to region |",
            "| Asymmetry breakdown | Asymmetry detection fails or misbehaves |",
            "| False primitive detection | Primitives detected that don't exist |",
            "| Missing primitive detection | Real primitives not detected |",
            "| Dimension ambiguity | Cannot associate dimensions with geometry |",
            "| Raster degradation | Quality loss in scanned/raster plans |",
            "| Scan skew | Rotated or skewed scan affects geometry |",
            "| Topology collapse | Unusual shape breaks zone/primitive model |",
            "| Scale mismatch | Extracted dimensions don't match expected |",
            "",
            "---",
            "",
            "## Remediation Priority",
            "",
            "1. **Critical** — Blocks further processing, must fix",
            "2. **Major** — Significant impact on morphology quality",
            "3. **Minor** — Affects accuracy but doesn't block",
            "4. **Observation** — Noted for future improvement",
            "",
        ])

        with open(taxonomy_path, 'w') as f:
            f.write("\n".join(lines))

        print(f"Failure taxonomy saved: {taxonomy_path}")

    def generate_summary_report(self) -> None:
        """Generate human-readable summary report."""
        report_path = self.output_dir / "VALIDATION_1B_REPORT.md"

        successful = [r for r in self.results if r.harvest_success]
        matches = [r for r in self.results if r.classification_match]

        lines = [
            "# IBG Morphology Validation 1B Report",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
            f"**Corpus:** {self.corpus_root}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total instruments | {len(self.results)} |",
            f"| Successful harvests | {len(successful)} ({len(successful)*100//len(self.results)}%) |",
            f"| Classification matches | {len(matches)} ({len(matches)*100//len(self.results) if self.results else 0}%) |",
            f"| Failures recorded | {len(self.failures)} |",
            "",
            "---",
            "",
            "## Per-Instrument Results",
            "",
        ]

        for r in self.results:
            status = "PASS" if r.classification_match else ("PARTIAL" if r.harvest_success else "FAIL")
            lines.append(f"### {r.instrument_id} ({r.category})")
            lines.append("")
            lines.append(f"**File:** `{r.file_path}`")
            lines.append(f"**Status:** {status}")
            lines.append("")

            if r.harvest_success:
                lines.append(f"| Metric | Value |")
                lines.append(f"|--------|-------|")
                lines.append(f"| Expected class | {r.expected_class} |")
                lines.append(f"| Actual class | {r.actual_class or 'N/A'} |")
                lines.append(f"| Classification confidence | {r.classification_confidence:.2f} |")
                lines.append(f"| Centerline confidence | {r.centerline_confidence:.2f} |")
                lines.append(f"| Asymmetry score | {r.asymmetry_score:.2f} |")
                lines.append(f"| Primitives detected | {r.primitives_detected} |")
                lines.append("")

            if r.errors:
                lines.append("**Errors:**")
                for err in r.errors:
                    lines.append(f"- {err}")
                lines.append("")

            if r.warnings:
                lines.append("**Warnings:**")
                for warn in r.warnings:
                    lines.append(f"- {warn}")
                lines.append("")

            if r.ambiguities:
                lines.append("**Ambiguities:**")
                for amb in r.ambiguities:
                    lines.append(f"- {amb}")
                lines.append("")

            if r.attention_points:
                lines.append("**Attention points:**")
                for pt in r.attention_points:
                    lines.append(f"- {pt}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Add observations section
        lines.extend([
            "## Key Observations",
            "",
            "### Classification Accuracy",
            "",
        ])

        if matches:
            lines.append(f"Successfully classified {len(matches)} of {len(self.results)} instruments:")
            for r in matches:
                lines.append(f"- {r.instrument_id}: {r.actual_class} (conf: {r.classification_confidence:.2f})")
        else:
            lines.append("No instruments correctly classified.")

        lines.append("")

        mismatches = [r for r in self.results if r.harvest_success and not r.classification_match]
        if mismatches:
            lines.append("### Classification Mismatches")
            lines.append("")
            for r in mismatches:
                lines.append(f"- **{r.instrument_id}**: Expected {r.expected_class}, got {r.actual_class}")
            lines.append("")

        # Failure summary
        if self.failures:
            lines.extend([
                "### Failure Summary",
                "",
                f"Total failures recorded: {len(self.failures)}",
                "",
                "See `docs/governance/MORPHOLOGY_FAILURE_TAXONOMY.md` for details.",
                "",
            ])

        with open(report_path, 'w') as f:
            f.write("\n".join(lines))

        print(f"Summary report saved: {report_path}")


def main():
    corpus_root = r"C:\Users\thepr\Downloads\luthiers-toolbox\Guitar Plans"
    output_dir = r"C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\instrument_geometry\body\ibg\morphology_harvest\outputs\validation_1b"

    runner = Validation1BRunner(corpus_root, output_dir)
    runner.run_all()

    print()
    print("=" * 70)
    print("Validation 1B Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
