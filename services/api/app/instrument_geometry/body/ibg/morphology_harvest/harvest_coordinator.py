"""
Harvest Coordinator — Thin Orchestration Layer
===============================================

Coordinates morphology evidence extraction from multiple systems.
This is a COORDINATION layer, not an extraction engine.

All extraction is delegated to:
- Blueprint Vectorizer for PDF → DXF (canonical pipeline)
- Calibration (embedded in vectorizer response)
- Body Grid for morphology analysis

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md

1B-FIX-v2: Uses canonical blueprint_reader.html pipeline, NOT Phase 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4

from .schema import HarvestRecord, HarvestSource, ReviewStatus
from .evidence_categories import BodyData, ConstructionNotes
from .adapters import (
    get_blueprint_adapter,
    get_calibration_adapter,
    get_body_grid_adapter,
    check_all_adapters,
    AdapterResult,
)
from .pdf_inventory import PDFInventoryEntry


@dataclass
class HarvestResult:
    """
    Result of a harvest operation.

    Attributes:
        record: HarvestRecord if successful
        success: Whether harvest produced usable data
        partial: Whether some but not all systems contributed
        adapter_status: Status of each adapter
        errors: List of errors encountered
    """
    record: Optional[HarvestRecord]
    success: bool
    partial: bool = False
    adapter_status: Dict[str, bool] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.adapter_status is None:
            self.adapter_status = {}
        if self.errors is None:
            self.errors = []


class HarvestCoordinator:
    """
    Thin coordination layer for morphology harvest.

    Delegates ALL extraction to existing authority systems.
    Never parses dimensions, detects scales, or classifies
    morphology directly — coordinates calls to systems that do.

    Usage:
        coordinator = HarvestCoordinator()

        # Check what's available
        status = coordinator.check_systems()
        print(status)

        # Harvest from PDF
        result = coordinator.harvest_from_pdf("plans/dreadnought.pdf")
        if result.success:
            record = result.record
            record.save("records/dreadnought.json")
    """

    def __init__(self):
        self._blueprint = get_blueprint_adapter()
        self._calibration = get_calibration_adapter()
        self._body_grid = get_body_grid_adapter()

    def check_systems(self) -> Dict[str, Any]:
        """
        Check availability of all upstream systems.

        Returns dict with status of each system.
        """
        results = check_all_adapters()

        return {
            name: {
                "available": result.available,
                "reason": result.reason,
            }
            for name, result in results.items()
        }

    def harvest_from_pdf(
        self,
        pdf_path: str,
        page: int = 1,
        inventory_entry: Optional[PDFInventoryEntry] = None,
    ) -> HarvestResult:
        """
        Harvest morphology data from a PDF blueprint.

        Coordinates calls to Phase 4, calibration, and body_grid.
        Does NOT perform extraction itself.

        Args:
            pdf_path: Path to PDF blueprint
            page: Page number (1-indexed)
            inventory_entry: Optional pre-scanned inventory entry

        Returns:
            HarvestResult with HarvestRecord if successful
        """
        harvest_id = f"harvest_{uuid4().hex[:8]}"
        errors = []
        adapter_status = {}

        # Create base record
        record = HarvestRecord(
            harvest_id=harvest_id,
            source_pdf=pdf_path,
            page_number=page,
            harvest_timestamp=datetime.now().isoformat(),
        )

        # Determine source type from inventory if available
        if inventory_entry:
            record.harvest_source = self._classify_source(inventory_entry)

            # Pre-populate from inventory
            if inventory_entry.instrument_family_normalized:
                record.body_data.instrument_family_normalized = \
                    inventory_entry.instrument_family_normalized

            if inventory_entry.dimension_strings:
                record.construction_notes.dimension_strings = \
                    inventory_entry.dimension_strings[:20]
                record.construction_notes.observed = True
                record.construction_notes.source_type = "pdf_text"
                record.construction_notes.source_authority = "inventory"

            if inventory_entry.keywords_detected:
                record.construction_notes.mark_observed(
                    confidence=0.6,
                    source_type="pdf_text",
                    source_authority="inventory",
                )

        # Step 1: Try Blueprint Vectorizer for dimension extraction (canonical pipeline)
        blueprint_result = self._blueprint.check_availability()
        adapter_status["blueprint_vectorizer"] = blueprint_result.available

        if blueprint_result.available:
            try:
                extraction = self._blueprint.extract_dimension_values(pdf_path, page)

                # Handle return format: {"dimensions": {...}, "raw_extraction": {...}, "confidence": ...}
                if extraction and isinstance(extraction, dict):
                    if "error" in extraction:
                        errors.append(f"Blueprint extraction error: {extraction['error']}")
                    else:
                        dimensions = extraction.get("dimensions", {})
                        if dimensions:
                            self._apply_dimensions(record, dimensions)

                            # Update confidence from extraction result
                            confidence = extraction.get("confidence", 0.7)
                            if record.body_data.observed:
                                record.body_data.confidence = confidence

                            record.vectorizer_result_id = f"blueprint_{harvest_id}"
                            record.upstream_sources["blueprint_vectorizer"] = {
                                "available": True,
                                "dimensions_extracted": len(dimensions),
                                "confidence": confidence,
                                "svg_present": extraction.get("svg_content") is not None,
                                "dxf_present": extraction.get("dxf_base64") is not None,
                            }

                            # Store artifacts for downstream use
                            if extraction.get("svg_content"):
                                record.svg_content = extraction["svg_content"]
                            if extraction.get("dxf_base64"):
                                record.dxf_base64 = extraction["dxf_base64"]
                        else:
                            record.upstream_sources["blueprint_vectorizer"] = {
                                "available": True,
                                "dimensions_extracted": 0,
                                "note": "No dimensions mapped from extraction",
                            }
            except Exception as e:
                errors.append(f"Blueprint extraction error: {e}")
        else:
            record.upstream_sources["blueprint_vectorizer"] = {
                "available": False,
                "reason": blueprint_result.reason,
            }

        # Step 2: Try calibration for scale
        cal_result = self._calibration.check_availability()
        adapter_status["calibration"] = cal_result.available

        if cal_result.available:
            try:
                method = self._calibration.get_calibration_method(pdf_path, page)
                if method:
                    record.calibration_method = method
                    record.upstream_sources["calibration"] = {
                        "available": True,
                        "method": method,
                    }
            except Exception as e:
                errors.append(f"Calibration error: {e}")
        else:
            record.upstream_sources["calibration"] = {
                "available": False,
                "reason": cal_result.reason,
            }

        # Step 3: Try Body Grid for morphology classification
        body_grid_result = self._body_grid.check_availability()
        adapter_status["body_grid"] = body_grid_result.available

        if body_grid_result.available and record.body_data.observed:
            try:
                body_evidence = record.to_body_evidence()
                if body_evidence and body_evidence.landmarks:
                    morph_class = self._body_grid.get_morphology_class(body_evidence)
                    if morph_class:
                        record.body_data.morphology_class = morph_class
                        record.upstream_sources["body_grid"] = {
                            "available": True,
                            "morphology_class": morph_class,
                        }
            except Exception as e:
                errors.append(f"Body Grid error: {e}")
        else:
            record.upstream_sources["body_grid"] = {
                "available": body_grid_result.available,
                "reason": body_grid_result.reason if not body_grid_result.available else "no body data",
            }

        # Determine success
        has_body_data = record.body_data.observed
        has_any_data = any([
            record.body_data.observed,
            record.neck_pocket_data.observed,
            record.neck_system_data.observed,
            record.fretboard_data.observed,
            record.headstock_data.observed,
            record.hardware_cavity_data.observed,
            record.alignment_data.observed,
            record.construction_notes.observed,
        ])

        # Set review status
        if record.requires_human_review():
            record.review_status = ReviewStatus.PENDING_REVIEW
        elif has_body_data and record.body_data.confidence >= 0.8:
            record.review_status = ReviewStatus.APPROVED

        return HarvestResult(
            record=record,
            success=has_body_data,
            partial=has_any_data and not has_body_data,
            adapter_status=adapter_status,
            errors=errors,
        )

    def harvest_from_inventory_entry(
        self,
        entry: PDFInventoryEntry,
        page: int = 1,
    ) -> HarvestResult:
        """
        Harvest from a pre-scanned inventory entry.

        Convenience method that uses inventory metadata.
        """
        return self.harvest_from_pdf(
            entry.file_path,
            page=page,
            inventory_entry=entry,
        )

    def batch_harvest(
        self,
        pdf_paths: List[str],
        progress_callback=None,
    ) -> List[HarvestResult]:
        """
        Harvest from multiple PDFs.

        Args:
            pdf_paths: List of PDF paths
            progress_callback: Optional callback(current, total, path, result)

        Returns:
            List of HarvestResults
        """
        results = []

        for i, path in enumerate(pdf_paths):
            result = self.harvest_from_pdf(path)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, len(pdf_paths), path, result)

        return results

    def _apply_dimensions(
        self,
        record: HarvestRecord,
        dimensions: Dict[str, float],
    ) -> None:
        """
        Apply extracted dimensions to harvest record.

        Uses canonical field names per governance audit.
        """
        body = record.body_data

        if "body_length_mm" in dimensions:
            body.body_length_mm = dimensions["body_length_mm"]
        if "lower_bout_width_mm" in dimensions:
            body.lower_bout_width_mm = dimensions["lower_bout_width_mm"]
        if "upper_bout_width_mm" in dimensions:
            body.upper_bout_width_mm = dimensions["upper_bout_width_mm"]
        if "waist_width_mm" in dimensions:
            body.waist_width_mm = dimensions["waist_width_mm"]
        if "waist_y_norm" in dimensions:
            body.waist_y_norm = dimensions["waist_y_norm"]

        # Mark as observed if we got body dimensions
        if body.body_length_mm or body.lower_bout_width_mm:
            body.mark_observed(
                confidence=0.7,  # Phase 4 extraction confidence
                source_type="phase4_extraction",
                source_authority="phase4",
            )

        # Neck system data
        if "scale_length_mm" in dimensions:
            record.neck_system_data.scale_length_mm = dimensions["scale_length_mm"]
            record.neck_system_data.mark_observed(
                confidence=0.7,
                source_type="phase4_extraction",
                source_authority="phase4",
            )

    def _classify_source(self, entry: PDFInventoryEntry) -> HarvestSource:
        """Classify source type from inventory entry."""
        if entry.vector_text_present and entry.has_vectors:
            return HarvestSource.VECTOR_TEXT
        elif entry.has_vectors and not entry.has_text:
            return HarvestSource.VECTOR_NO_TEXT
        elif entry.raster_content_present and not entry.has_vectors:
            if entry.has_text:
                return HarvestSource.RASTER_CLEAN
            else:
                return HarvestSource.RASTER_NOISY
        elif entry.vector_text_present and entry.raster_content_present:
            return HarvestSource.MIXED
        else:
            return HarvestSource.UNKNOWN


# CLI interface
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Harvest morphology data from PDF blueprints"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to PDF blueprint"
    )
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number (default: 1)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON path (default: stdout)"
    )
    parser.add_argument(
        "--check-systems",
        action="store_true",
        help="Just check system availability"
    )

    args = parser.parse_args()

    coordinator = HarvestCoordinator()

    if args.check_systems:
        status = coordinator.check_systems()
        print(json.dumps(status, indent=2))
    else:
        result = coordinator.harvest_from_pdf(args.pdf_path, args.page)

        if result.success:
            output = result.record.to_dict()
        else:
            output = {
                "success": False,
                "partial": result.partial,
                "errors": result.errors,
                "adapter_status": result.adapter_status,
            }

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"Saved: {args.output}")
        else:
            print(json.dumps(output, indent=2))
