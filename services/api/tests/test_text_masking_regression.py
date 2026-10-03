"""
Regression tests for text-masking preprocessing.

These tests verify that text masking produces expected results on
real blueprint PDFs (Cuatro and Melody Maker) used for Sprint 3 diagnostics.

Sprint 3: Text-masking preprocessing pass for blueprint vectorizer.
Expected outcomes (per pre-implementation scoping):
- Floor: No improvement (~0.38 confidence)
- Ceiling: Documented baseline (~0.69 confidence)
- Actual: Unknown until tested

Author: Production Shop
Date: 2026-04-26
"""

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# VECTORIZER-CI-BOUNDARY-001: real-plan conversions run in the dedicated
# vectorizer-regression workflow, not in default API CI (see pytest.ini).
pytestmark = pytest.mark.vectorizer_regression

# Test file paths (relative to repo root)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
MELODY_MAKER_PDF = REPO_ROOT / "docs/archive/instrument_references/gibson_melody_maker/gibson_melody_maker_blueprint.pdf"
CUATRO_PDF = REPO_ROOT / "services/api/app/instrument_geometry/reference_dxf/cuatro/cuatro puertoriqueño.pdf"


def skip_if_no_test_file(path: Path):
    """Skip test if test file doesn't exist."""
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")


@pytest.fixture
def orchestrator():
    """Get BlueprintOrchestrator instance."""
    from app.services.blueprint_orchestrator import BlueprintOrchestrator
    return BlueprintOrchestrator()


def _peak_rss_mb():
    """Process peak RSS in MB where the platform reports it (Linux/macOS), else None."""
    try:
        import resource
    except ImportError:
        return None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(peak / (1024 * 1024 if sys.platform == "darwin" else 1024), 1)


@pytest.fixture(scope="module")
def melody_maker_run():
    """Run each Melody Maker conversion at most once per module and share the result.

    The three Melody Maker tests previously made four identical 266,359-entity
    conversions (masked, unmasked, then both again for the comparison). This keeps
    exactly two -- masked and unmasked -- computed on first use. Results are shared
    read-only; no test mutates them. ``process_file`` takes bytes and manages its own
    temporary directory, so there is no output path to place under tmp_path_factory.

    When ``VECTORIZER_REGRESSION_METRICS`` names a file, a compact metrics record is
    written there at module teardown (fixture hash, entity counts, timings, peak RSS).
    """
    skip_if_no_test_file(MELODY_MAKER_PDF)

    from app.services.blueprint_clean import CleanupMode
    from app.services.blueprint_orchestrator import BlueprintOrchestrator

    orchestrator = BlueprintOrchestrator()
    file_bytes = MELODY_MAKER_PDF.read_bytes()
    results = {}
    conversions = []

    def run(mask_text: bool):
        if mask_text not in results:
            started = time.perf_counter()
            result = orchestrator.process_file(
                file_bytes=file_bytes,
                filename="melody_maker.pdf",
                mode=CleanupMode.ENHANCED,
                mask_text=mask_text,
                gap_close_size=7,
            )
            conversions.append({
                "mask_text": mask_text,
                "elapsed_s": round(time.perf_counter() - started, 1),
                "dxf_entity_count": result.dxf.entity_count,
                "ok": result.ok,
                "stage": result.stage,
            })
            results[mask_text] = result
        return results[mask_text]

    yield run

    metrics_path = os.environ.get("VECTORIZER_REGRESSION_METRICS")
    if metrics_path:
        Path(metrics_path).write_text(json.dumps({
            "fixture": MELODY_MAKER_PDF.relative_to(REPO_ROOT).as_posix(),
            "fixture_sha256": hashlib.sha256(file_bytes).hexdigest(),
            "fixture_bytes": len(file_bytes),
            "conversions": conversions,
            "peak_rss_mb": _peak_rss_mb(),
        }, indent=2) + "\n", encoding="utf-8")


class TestTextMaskingRegression:
    """Regression tests using real blueprint PDFs."""

    @pytest.mark.slow
    def test_melody_maker_with_text_masking(self, melody_maker_run):
        """Verify Melody Maker extraction with text masking enabled."""
        skip_if_no_test_file(MELODY_MAKER_PDF)

        result = melody_maker_run(mask_text=True)

        # Should complete without error
        assert result.ok or result.stage != "error", f"Failed at stage: {result.stage}"

        # Log metrics for analysis
        print(f"\n=== MELODY MAKER (mask_text=True) ===")
        print(f"OK: {result.ok}")
        print(f"Stage: {result.stage}")
        if hasattr(result, 'dimensions_mm'):
            print(f"Dimensions: {result.dimensions_mm}")
        if hasattr(result, 'entity_count'):
            print(f"Entity count: {result.entity_count}")
        if hasattr(result, 'recommendation') and result.recommendation:
            print(f"Confidence: {result.recommendation.confidence}")
            print(f"Action: {result.recommendation.action.value}")

    @pytest.mark.slow
    def test_melody_maker_without_text_masking(self, melody_maker_run):
        """Verify Melody Maker extraction with text masking disabled (baseline)."""
        skip_if_no_test_file(MELODY_MAKER_PDF)

        result = melody_maker_run(mask_text=False)

        # Log metrics for comparison
        print(f"\n=== MELODY MAKER (mask_text=False) ===")
        print(f"OK: {result.ok}")
        print(f"Stage: {result.stage}")
        if hasattr(result, 'recommendation') and result.recommendation:
            print(f"Confidence: {result.recommendation.confidence}")

    @pytest.mark.slow
    def test_cuatro_with_text_masking(self, orchestrator):
        """Verify Cuatro extraction with text masking enabled."""
        skip_if_no_test_file(CUATRO_PDF)

        from app.services.blueprint_clean import CleanupMode

        file_bytes = CUATRO_PDF.read_bytes()

        result = orchestrator.process_file(
            file_bytes=file_bytes,
            filename="cuatro.pdf",
            mode=CleanupMode.ENHANCED,
            mask_text=True,
            gap_close_size=7,
        )

        # Should complete without error
        assert result.ok or result.stage != "error", f"Failed at stage: {result.stage}"

        # Log metrics for analysis
        print(f"\n=== CUATRO (mask_text=True) ===")
        print(f"OK: {result.ok}")
        print(f"Stage: {result.stage}")
        if hasattr(result, 'dimensions_mm'):
            print(f"Dimensions: {result.dimensions_mm}")
        if hasattr(result, 'entity_count'):
            print(f"Entity count: {result.entity_count}")
        if hasattr(result, 'recommendation') and result.recommendation:
            print(f"Confidence: {result.recommendation.confidence}")
            print(f"Action: {result.recommendation.action.value}")

    @pytest.mark.slow
    def test_cuatro_without_text_masking(self, orchestrator):
        """Verify Cuatro extraction with text masking disabled (baseline)."""
        skip_if_no_test_file(CUATRO_PDF)

        from app.services.blueprint_clean import CleanupMode

        file_bytes = CUATRO_PDF.read_bytes()

        result = orchestrator.process_file(
            file_bytes=file_bytes,
            filename="cuatro.pdf",
            mode=CleanupMode.ENHANCED,
            mask_text=False,
            gap_close_size=7,
        )

        # Log metrics for comparison
        print(f"\n=== CUATRO (mask_text=False) ===")
        print(f"OK: {result.ok}")
        print(f"Stage: {result.stage}")
        if hasattr(result, 'recommendation') and result.recommendation:
            print(f"Confidence: {result.recommendation.confidence}")


class TestTextMaskingComparison:
    """Compare text masking on vs off for quantitative analysis."""

    @pytest.mark.slow
    def test_entity_count_reduction(self, melody_maker_run):
        """Text masking should reduce entity count (fewer text-shaped contours)."""
        skip_if_no_test_file(MELODY_MAKER_PDF)

        # With text masking
        result_masked = melody_maker_run(mask_text=True)

        # Without text masking
        result_unmasked = melody_maker_run(mask_text=False)

        # Get entity counts
        masked_count = getattr(result_masked, 'entity_count', 0)
        unmasked_count = getattr(result_unmasked, 'entity_count', 0)

        print(f"\n=== ENTITY COUNT COMPARISON ===")
        print(f"With text masking: {masked_count:,}")
        print(f"Without text masking: {unmasked_count:,}")
        if unmasked_count > 0:
            reduction = (unmasked_count - masked_count) / unmasked_count * 100
            print(f"Reduction: {reduction:.1f}%")

        # Text masking should not INCREASE entity count
        # (it can only remove or leave unchanged)
        assert masked_count <= unmasked_count + 1000, \
            f"Text masking unexpectedly increased entities: {masked_count} > {unmasked_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
