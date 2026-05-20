"""
IBG E-2-E Functional Spine Runner
==================================

Orchestrates the complete end-to-end pipeline:

    PDF → Canonical Vectorizer → Artifacts
    → BodyEvidence → Body Grid → MorphologyDescriptor
    → IBG Reconstruction → BOE Review Package

Author: Production Shop
Date: 2026-05-17
Sprint: IBG E-2-E Functional Spine
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .adapters import get_blueprint_adapter, get_photo_adapter
from .artifact_body_evidence_adapter import (
    ArtifactBodyEvidenceAdapter,
    ArtifactMetadata,
    AdapterResult as ArtifactAdapterResult,
)
from .json_utils import SafeJSONEncoder, json_safe

logger = logging.getLogger(__name__)

# Output directory (gitignored staging)
OUTPUT_DIR = Path(__file__).parent / "outputs" / "e2e_spine"


@dataclass
class E2ESpineResult:
    """Complete result of E-2-E spine execution."""

    # Identification
    run_id: str
    source_file: str
    source_mode: str
    timestamp: str

    # Stage results
    vectorizer_success: bool = False
    artifact_parse_success: bool = False
    body_evidence_created: bool = False
    body_grid_success: bool = False
    morphology_descriptor_created: bool = False
    ibg_reconstruction_attempted: bool = False
    ibg_reconstruction_success: bool = False
    boe_package_created: bool = False

    # Data
    dimensions: Optional[Dict[str, float]] = None
    body_evidence_summary: Optional[Dict[str, Any]] = None
    morphology_descriptor: Optional[Dict[str, Any]] = None
    ibg_result: Optional[Dict[str, Any]] = None

    # Artifacts
    svg_artifact_path: Optional[str] = None
    dxf_artifact_path: Optional[str] = None
    boe_package_path: Optional[str] = None

    # Status
    failures: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    review_status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BOEReviewPackage:
    """BOE-reviewable output package."""

    # Source
    source_file: str
    source_mode: str
    run_id: str
    timestamp: str

    # Artifacts
    svg_artifact_path: Optional[str] = None
    dxf_artifact_path: Optional[str] = None

    # Evidence
    body_evidence_summary: Optional[Dict[str, Any]] = None

    # Analysis
    body_grid_result: Optional[Dict[str, Any]] = None
    morphology_descriptor: Optional[Dict[str, Any]] = None

    # Reconstruction
    ibg_reconstruction_status: str = "not_attempted"
    ibg_result: Optional[Dict[str, Any]] = None

    # Review
    failures: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    review_notes_placeholder: str = ""
    review_status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class E2ESpineRunner:
    """
    Runs the complete IBG E-2-E functional spine.

    Usage:
        runner = E2ESpineRunner()

        # Run for single PDF
        result = runner.run_pdf("path/to/blueprint.pdf")

        # Run for all 10 representative instruments
        results = runner.run_representative_set()
    """

    # Representative instrument set
    REPRESENTATIVE_INSTRUMENTS = [
        ("Gibson-Les-Paul-59-Complete.pdf", "single_cut", "ROUNDED_SINGLE_CUT"),
        ("01-Gibson-SG-Complete-Template.pdf", "double_cut", "ROUNDED_DOUBLE_CUT"),
        ("Fender-Stratocaster-62.pdf", "slab_body", "SLAB_BODY"),
        ("Fender-Jazzmaster-62-Body.pdf", "offset", "OFFSET_DOUBLE_CUT"),
        ("Gibson-Explorer-05-Complete-Plans.pdf", "angular", "ANGULAR_WEDGE"),
        ("A003-Dreadnought-MM.pdf", "acoustic_dread", "ROUNDED_ACOUSTIC"),
        ("Classical-Santos-Hernandez-MM.pdf", "classical", "CLASSICAL_FIGURE_8"),
        ("Gibson-335/Gibson-335-Dot-Complete.pdf", "semi_hollow", "ROUNDED_DOUBLE_CUT"),
        ("Klein-Guitar-Plan.pdf", "ergonomic", "HYBRID_FORM"),
        ("El Cuatro/cuatro puertoriqueño.pdf", "latin_folk", "ROUNDED_ACOUSTIC"),
    ]

    def __init__(self, corpus_root: Optional[str] = None):
        self.corpus_root = Path(corpus_root) if corpus_root else Path(r"C:\Users\thepr\Downloads\luthiers-toolbox\Guitar Plans")
        self.blueprint_adapter = get_blueprint_adapter()
        self.artifact_adapter = ArtifactBodyEvidenceAdapter()

        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run_pdf(
        self,
        pdf_path: str,
        expected_class: Optional[str] = None,
    ) -> E2ESpineResult:
        """
        Run E-2-E spine for a single PDF.

        Args:
            pdf_path: Path to PDF blueprint
            expected_class: Expected morphology class (for validation)

        Returns:
            E2ESpineResult with complete pipeline results
        """
        run_id = f"e2e_{uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()
        source_file = Path(pdf_path).name

        result = E2ESpineResult(
            run_id=run_id,
            source_file=source_file,
            source_mode="pdf",
            timestamp=timestamp,
        )

        logger.info(f"[{run_id}] Starting E-2-E spine for: {source_file}")

        # Stage 1: Canonical Vectorizer
        result = self._stage_vectorizer(result, pdf_path)
        if not result.vectorizer_success:
            return self._finalize(result)

        # Stage 2: Artifact → BodyEvidence
        result = self._stage_artifact_parse(result)
        if not result.body_evidence_created:
            return self._finalize(result)

        # Stage 3: Body Grid Analysis
        result = self._stage_body_grid(result)

        # Stage 4: IBG Reconstruction
        result = self._stage_ibg_reconstruction(result)

        # Stage 5: BOE Package
        result = self._stage_boe_package(result, expected_class)

        return self._finalize(result)

    def _stage_vectorizer(
        self,
        result: E2ESpineResult,
        pdf_path: str,
    ) -> E2ESpineResult:
        """Stage 1: Get artifacts from canonical vectorizer."""
        logger.info(f"[{result.run_id}] Stage 1: Canonical Vectorizer")

        try:
            extraction = self.blueprint_adapter.extract_dimension_values(pdf_path)

            if "error" in extraction and extraction.get("error"):
                result.failures.append(f"Vectorizer error: {extraction['error']}")
                return result

            result.dimensions = extraction.get("dimensions", {})
            result.vectorizer_success = True

            # Store artifacts for later stages
            result._svg_content = extraction.get("svg_content")
            result._dxf_base64 = extraction.get("dxf_base64")
            result._raw_extraction = extraction.get("raw_extraction", {})

            logger.info(f"[{result.run_id}] Vectorizer success: {result.dimensions}")

        except Exception as e:
            result.failures.append(f"Vectorizer exception: {e}")
            logger.exception(f"[{result.run_id}] Vectorizer failed")

        return result

    def _stage_artifact_parse(self, result: E2ESpineResult) -> E2ESpineResult:
        """Stage 2: Parse artifacts into BodyEvidence."""
        logger.info(f"[{result.run_id}] Stage 2: Artifact → BodyEvidence")

        try:
            adapter_result = self.artifact_adapter.from_vectorizer_response(
                dxf_base64=getattr(result, '_dxf_base64', None),
                svg_content=getattr(result, '_svg_content', None),
                dimensions=result.dimensions,
                source_file=result.source_file,
                source_mode=result.source_mode,
            )

            if not adapter_result.success:
                result.failures.append(f"Artifact parse failed: {adapter_result.errors}")
                return result

            result.artifact_parse_success = True
            result._body_evidence = adapter_result.body_evidence
            result._parsed_artifact = adapter_result.parsed_artifact
            result.body_evidence_created = True

            # Summarize evidence
            evidence = adapter_result.body_evidence
            result.body_evidence_summary = {
                "outline_points_count": len(evidence.outline_points) if evidence.outline_points else 0,
                "contour_segments_count": len(evidence.contour_segments) if evidence.contour_segments else 0,
                "landmarks_count": len(evidence.landmarks) if evidence.landmarks else 0,
                "source_type": evidence.source_type.value if evidence.source_type else "unknown",
                "bounding_box_mm": evidence.bounding_box_mm,
                "centerline_x_mm": evidence.centerline_x_mm,
            }

            # Save artifacts
            artifact_dir = OUTPUT_DIR / result.run_id
            artifact_dir.mkdir(parents=True, exist_ok=True)

            if adapter_result.parsed_artifact:
                if adapter_result.parsed_artifact.svg_content:
                    svg_path = artifact_dir / "artifact.svg"
                    svg_path.write_text(adapter_result.parsed_artifact.svg_content)
                    result.svg_artifact_path = str(svg_path)

                if adapter_result.parsed_artifact.dxf_content:
                    dxf_path = artifact_dir / "artifact.dxf"
                    dxf_path.write_bytes(adapter_result.parsed_artifact.dxf_content)
                    result.dxf_artifact_path = str(dxf_path)

            logger.info(f"[{result.run_id}] BodyEvidence created: {result.body_evidence_summary}")

        except Exception as e:
            result.failures.append(f"Artifact parse exception: {e}")
            logger.exception(f"[{result.run_id}] Artifact parsing failed")

        return result

    def _stage_body_grid(self, result: E2ESpineResult) -> E2ESpineResult:
        """Stage 3: Body Grid analysis → MorphologyDescriptor."""
        logger.info(f"[{result.run_id}] Stage 3: Body Grid Analysis")

        try:
            # Import MorphologyAnalyzer
            from ..body_grid.morphology_descriptor import MorphologyAnalyzer

            analyzer = MorphologyAnalyzer()
            evidence = getattr(result, '_body_evidence', None)

            if not evidence:
                result.failures.append("No BodyEvidence available for Body Grid")
                return result

            descriptor = analyzer.analyze(evidence)
            result.body_grid_success = True
            result.morphology_descriptor_created = True

            # Serialize descriptor
            result.morphology_descriptor = {
                "morphology_class": descriptor.variant_match.morphology_class.value if descriptor.variant_match else None,
                "confidence": descriptor.confidence,
                "centerline_x_mm": descriptor.centerline.x_mm if descriptor.centerline else None,
                "asymmetry_score": descriptor.asymmetry.asymmetry_score if descriptor.asymmetry else 0.0,
                "is_symmetric": descriptor.asymmetry.is_symmetric if descriptor.asymmetry else True,
                "zone_coverage": descriptor.zone_coverage,
                "primitives_count": len(descriptor.primitives) if descriptor.primitives else 0,
            }

            result._morphology_descriptor = descriptor

            logger.info(f"[{result.run_id}] MorphologyDescriptor: class={result.morphology_descriptor.get('morphology_class')}, confidence={result.morphology_descriptor.get('confidence'):.2f}")

        except ImportError as e:
            result.failures.append(f"Body Grid import failed: {e}")
            result.uncertainties.append("MorphologyAnalyzer not available in current context")
            logger.warning(f"[{result.run_id}] Body Grid import failed: {e}")

        except Exception as e:
            result.failures.append(f"Body Grid exception: {e}")
            logger.exception(f"[{result.run_id}] Body Grid analysis failed")

        return result

    def _stage_ibg_reconstruction(self, result: E2ESpineResult) -> E2ESpineResult:
        """Stage 4: IBG reconstruction attempt."""
        logger.info(f"[{result.run_id}] Stage 4: IBG Reconstruction")

        result.ibg_reconstruction_attempted = True

        try:
            from ..instrument_body_generator import InstrumentBodyGenerator

            # Try to determine spec from morphology
            spec_name = self._guess_spec_from_morphology(result)

            if not spec_name:
                result.uncertainties.append("Could not determine instrument spec for reconstruction")
                spec_name = "stratocaster"  # Default fallback

            generator = InstrumentBodyGenerator(spec_name)

            # Check if we have DXF artifact for reconstruction
            dxf_path = result.dxf_artifact_path
            if dxf_path and Path(dxf_path).exists():
                try:
                    model = generator.complete_from_dxf(dxf_path)
                    result.ibg_reconstruction_success = True

                    result.ibg_result = {
                        "status": "complete",
                        "spec_used": spec_name,
                        "confidence": model.confidence if hasattr(model, 'confidence') else 0.5,
                        "outline_points": len(model.outline) if hasattr(model, 'outline') else 0,
                    }

                    logger.info(f"[{result.run_id}] IBG reconstruction complete: {result.ibg_result}")

                except Exception as e:
                    result.ibg_result = {
                        "status": "failed",
                        "spec_used": spec_name,
                        "error": str(e),
                    }
                    result.failures.append(f"IBG reconstruction failed: {e}")
            else:
                result.ibg_result = {
                    "status": "no_dxf_artifact",
                    "spec_used": spec_name,
                }
                result.uncertainties.append("No DXF artifact available for reconstruction")

        except ImportError as e:
            result.ibg_result = {
                "status": "not_callable_yet",
                "error": str(e),
            }
            result.uncertainties.append(f"IBG not importable: {e}")
            logger.warning(f"[{result.run_id}] IBG import failed: {e}")

        except Exception as e:
            result.ibg_result = {
                "status": "exception",
                "error": str(e),
            }
            result.failures.append(f"IBG exception: {e}")
            logger.exception(f"[{result.run_id}] IBG reconstruction failed")

        return result

    def _stage_boe_package(
        self,
        result: E2ESpineResult,
        expected_class: Optional[str] = None,
    ) -> E2ESpineResult:
        """Stage 5: Create BOE review package."""
        logger.info(f"[{result.run_id}] Stage 5: BOE Package")

        try:
            package = BOEReviewPackage(
                source_file=result.source_file,
                source_mode=result.source_mode,
                run_id=result.run_id,
                timestamp=result.timestamp,
                svg_artifact_path=result.svg_artifact_path,
                dxf_artifact_path=result.dxf_artifact_path,
                body_evidence_summary=result.body_evidence_summary,
                body_grid_result={
                    "success": result.body_grid_success,
                    "morphology_class": result.morphology_descriptor.get("morphology_class") if result.morphology_descriptor else None,
                    "confidence": result.morphology_descriptor.get("confidence") if result.morphology_descriptor else 0.0,
                },
                morphology_descriptor=result.morphology_descriptor,
                ibg_reconstruction_status=result.ibg_result.get("status") if result.ibg_result else "not_attempted",
                ibg_result=result.ibg_result,
                failures=result.failures,
                uncertainties=result.uncertainties,
                review_status="needs_review" if result.failures or result.uncertainties else "ready",
            )

            # Add validation if expected class provided
            if expected_class and result.morphology_descriptor:
                actual_class = result.morphology_descriptor.get("morphology_class")
                if actual_class != expected_class:
                    package.uncertainties.append(f"Expected {expected_class}, got {actual_class}")

            # Save package
            artifact_dir = OUTPUT_DIR / result.run_id
            artifact_dir.mkdir(parents=True, exist_ok=True)

            package_path = artifact_dir / "boe_review_package.json"
            with open(package_path, 'w') as f:
                json.dump(json_safe(package.to_dict()), f, indent=2, cls=SafeJSONEncoder)

            result.boe_package_path = str(package_path)
            result.boe_package_created = True

            logger.info(f"[{result.run_id}] BOE package created: {package_path}")

        except Exception as e:
            result.failures.append(f"BOE package creation failed: {e}")
            logger.exception(f"[{result.run_id}] BOE package creation failed")

        return result

    def _guess_spec_from_morphology(self, result: E2ESpineResult) -> Optional[str]:
        """Guess instrument spec from morphology descriptor."""
        if not result.morphology_descriptor:
            return None

        morph_class = result.morphology_descriptor.get("morphology_class")

        mapping = {
            "ROUNDED_SINGLE_CUT": "les_paul",
            "ROUNDED_DOUBLE_CUT": "stratocaster",
            "SLAB_BODY": "stratocaster",
            "OFFSET_DOUBLE_CUT": "stratocaster",
            "ANGULAR_WEDGE": "stratocaster",
            "ROUNDED_ACOUSTIC": "dreadnought",
            "CLASSICAL_FIGURE_8": "dreadnought",
            "HYBRID_FORM": "stratocaster",
        }

        return mapping.get(morph_class)

    def _finalize(self, result: E2ESpineResult) -> E2ESpineResult:
        """Finalize result and save summary."""

        # Determine review status
        if result.failures:
            result.review_status = "failed"
        elif result.uncertainties:
            result.review_status = "needs_review"
        elif result.boe_package_created:
            result.review_status = "ready"

        # Save result summary
        artifact_dir = OUTPUT_DIR / result.run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        summary_path = artifact_dir / "e2e_result.json"
        with open(summary_path, 'w') as f:
            # Remove internal attributes
            result_dict = json_safe(result.to_dict())
            result_dict = {k: v for k, v in result_dict.items() if not k.startswith('_')}
            json.dump(result_dict, f, indent=2, cls=SafeJSONEncoder)

        logger.info(f"[{result.run_id}] E-2-E complete: status={result.review_status}")

        return result

    def run_representative_set(self) -> List[E2ESpineResult]:
        """Run E-2-E spine for all 10 representative instruments."""
        results = []

        for filename, category, expected_class in self.REPRESENTATIVE_INSTRUMENTS:
            pdf_path = self.corpus_root / filename

            if not pdf_path.exists():
                logger.warning(f"PDF not found: {pdf_path}")
                result = E2ESpineResult(
                    run_id=f"e2e_{uuid4().hex[:8]}",
                    source_file=filename,
                    source_mode="pdf",
                    timestamp=datetime.now().isoformat(),
                )
                result.failures.append(f"PDF not found: {pdf_path}")
                results.append(result)
                continue

            result = self.run_pdf(str(pdf_path), expected_class)
            results.append(result)

        # Generate summary report
        self._generate_summary_report(results)

        return results

    def _generate_summary_report(self, results: List[E2ESpineResult]) -> None:
        """Generate summary report for representative set."""
        report_path = OUTPUT_DIR / "e2e_summary_report.json"

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_instruments": len(results),
            "vectorizer_success": sum(1 for r in results if r.vectorizer_success),
            "body_evidence_created": sum(1 for r in results if r.body_evidence_created),
            "body_grid_success": sum(1 for r in results if r.body_grid_success),
            "ibg_reconstruction_success": sum(1 for r in results if r.ibg_reconstruction_success),
            "boe_packages_created": sum(1 for r in results if r.boe_package_created),
            "results": [json_safe(r.to_dict()) for r in results],
        }

        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2, cls=SafeJSONEncoder)

        logger.info(f"Summary report saved: {report_path}")


# CLI interface
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    parser = argparse.ArgumentParser(description="IBG E-2-E Functional Spine Runner")
    parser.add_argument("--pdf", help="Single PDF to process")
    parser.add_argument("--all", action="store_true", help="Run all 10 representative instruments")
    parser.add_argument("--corpus", help="Corpus root directory")

    args = parser.parse_args()

    runner = E2ESpineRunner(corpus_root=args.corpus)

    if args.pdf:
        result = runner.run_pdf(args.pdf)
        print(json.dumps(json_safe(result.to_dict()), indent=2, cls=SafeJSONEncoder))
    elif args.all:
        results = runner.run_representative_set()
        print(f"\nCompleted {len(results)} instruments")
        for r in results:
            status = "[OK]" if r.boe_package_created else "[FAIL]"
            print(f"  {status} {r.source_file}: {r.review_status}")
    else:
        parser.print_help()
