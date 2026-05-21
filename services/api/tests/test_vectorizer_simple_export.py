"""PR-1: ExtractionMode.SIMPLE must not emit empty DXF when contours exist."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BLUEPRINT_IMPORT = REPO_ROOT / "services" / "blueprint-import"
if str(BLUEPRINT_IMPORT) not in sys.path:
    sys.path.insert(0, str(BLUEPRINT_IMPORT))


@pytest.fixture
def simple_test_image(tmp_path: Path) -> str:
    """White canvas with black rectangle (contours guaranteed)."""
    img = np.ones((200, 300, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (50, 40), (250, 160), (0, 0, 0), 3)
    path = tmp_path / "simple_rect.png"
    cv2.imwrite(str(path), img)
    return str(path)


def test_simple_mode_exports_non_empty_dxf(simple_test_image: str):
    from vectorizer_phase3 import ExtractionMode, Phase3Vectorizer

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.dxf"
        vectorizer = Phase3Vectorizer(
            enable_feedback=False,
            enable_scale_detection=False,
            enable_ocr=False,
        )
        result = vectorizer.extract(
            simple_test_image,
            output_path=str(out),
            extraction_mode=ExtractionMode.SIMPLE,
            validate=False,
            use_ml=False,
            detect_primitives=False,
        )
        assert out.is_file(), "DXF file should exist"
        text = out.read_text(encoding="utf-8", errors="ignore")
        assert "\nLINE\n" in text or "LINE" in text, "SIMPLE export should contain LINE entities"
        assert result.validation_passed is True


def test_export_to_dxf_unknown_not_excluded_by_default():
    from vectorizer_phase3 import (
        ContourCategory,
        ContourInfo,
        export_to_dxf,
    )

    cnt = np.array([[[0, 0]], [[100, 0]], [[100, 50]], [[0, 50]]], dtype=np.int32)
    info = ContourInfo(
        contour=cnt,
        category=ContourCategory.UNKNOWN,
        width_mm=100,
        height_mm=50,
        area_px=5000,
        perimeter_px=300,
        circularity=0.5,
        aspect_ratio=2.0,
        point_count=4,
        bbox=(0, 0, 100, 50),
    )
    classified = {ContourCategory.UNKNOWN: [info]}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "unknown.dxf"
        _, _, exported = export_to_dxf(
            classified,
            str(out),
            image_height=200,
            mm_per_px=0.5,
            excluded_categories=[
                ContourCategory.TEXT,
                ContourCategory.PAGE_BORDER,
                ContourCategory.SMALL_FEATURE,
            ],
        )
        assert exported >= 1
