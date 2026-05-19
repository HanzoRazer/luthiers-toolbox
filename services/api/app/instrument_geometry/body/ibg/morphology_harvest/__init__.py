"""
Morphology Harvest — Semantic Evidence Coordination Layer
==========================================================

A thin coordination layer that preserves and normalizes morphology
evidence from multiple extraction systems without duplicating
extraction logic.

This module:
- Inventories the instrument corpus
- Preserves semantic morphology evidence
- Normalizes terminology per governance audit
- Coordinates existing extraction authorities
- Generates human-reviewable morphology records

This module does NOT:
- Extract dimensions (delegates to canonical blueprint_reader.html pipeline)
- Detect scale (embedded in vectorizer response)
- Classify morphology (delegates to body_grid)
- Own ontology authority
- Implement adaptive/LLM behavior

Governance: docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md

Usage:
    from app.instrument_geometry.body.ibg.morphology_harvest import (
        HarvestCoordinator,
        HarvestRecord,
        PDFInventoryScanner,
        ManifestManager,
    )

    # Scan corpus
    scanner = PDFInventoryScanner("Guitar Plans/")
    corpus = scanner.scan()
    print(f"Found {corpus.total_pdfs} PDFs")
    print(f"Suggested representatives: {corpus.suggested_representatives}")

    # Harvest from PDF
    coordinator = HarvestCoordinator()
    result = coordinator.harvest_from_pdf("plans/dreadnought.pdf")
    if result.success:
        record = result.record

    # Save with manifest tracking
    manager = ManifestManager("outputs/")
    manager.save_record(record, generate_overlay=True)

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
"""

from .schema import (
    HarvestRecord,
    HarvestSource,
    ReviewStatus,
    TermNormalization,
    TERM_NORMALIZATIONS,
)

from .evidence_categories import (
    BodyData,
    NeckPocketData,
    NeckSystemData,
    FretboardData,
    HeadstockData,
    HardwareCavityData,
    AlignmentData,
    ConstructionNotes,
    create_empty_categories,
)

from .pdf_inventory import (
    PDFInventoryEntry,
    PDFInventoryScanner,
    CorpusManifest,
    scan_corpus,
)

from .adapters import (
    AdapterResult,
    BlueprintVectorizerAdapter,
    PhotoVectorizerAdapter,
    CalibrationMetadataAdapter,
    BodyGridAdapter,
    get_blueprint_adapter,
    get_photo_adapter,
    get_phase4_adapter,  # Deprecated alias
    get_calibration_adapter,
    get_body_grid_adapter,
    check_all_adapters,
)

from .harvest_coordinator import (
    HarvestCoordinator,
    HarvestResult,
)

from .overlay_wrapper import (
    HarvestOverlayWrapper,
    OverlayConfig,
    generate_harvest_overlay,
)

from .review_manifest import (
    HarvestManifest,
    ManifestEntry,
    ManifestManager,
)


__all__ = [
    # Schema
    "HarvestRecord",
    "HarvestSource",
    "ReviewStatus",
    "TermNormalization",
    "TERM_NORMALIZATIONS",
    # Evidence categories
    "BodyData",
    "NeckPocketData",
    "NeckSystemData",
    "FretboardData",
    "HeadstockData",
    "HardwareCavityData",
    "AlignmentData",
    "ConstructionNotes",
    "create_empty_categories",
    # PDF inventory
    "PDFInventoryEntry",
    "PDFInventoryScanner",
    "CorpusManifest",
    "scan_corpus",
    # Adapters
    "AdapterResult",
    "BlueprintVectorizerAdapter",
    "PhotoVectorizerAdapter",
    "CalibrationMetadataAdapter",
    "BodyGridAdapter",
    "get_blueprint_adapter",
    "get_photo_adapter",
    "get_phase4_adapter",  # Deprecated alias
    "get_calibration_adapter",
    "get_body_grid_adapter",
    "check_all_adapters",
    # Coordinator
    "HarvestCoordinator",
    "HarvestResult",
    # Overlay
    "HarvestOverlayWrapper",
    "OverlayConfig",
    "generate_harvest_overlay",
    # Manifest
    "HarvestManifest",
    "ManifestEntry",
    "ManifestManager",
]
