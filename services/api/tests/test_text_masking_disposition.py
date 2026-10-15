"""F-3 text-masking disposition.

Fast checks for unavailable, initialization failure, execution failure,
no text, and an applied mask. They do not convert a blueprint PDF.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PHOTO_VECTORIZER_PATH = REPO_ROOT / "services" / "photo-vectorizer"
if str(PHOTO_VECTORIZER_PATH) not in sys.path:
    sys.path.insert(0, str(PHOTO_VECTORIZER_PATH))


def _photo_numpy():
    import edge_to_dxf
    return edge_to_dxf.np


def _ellipse_image():
    np = _photo_numpy()
    cv2 = pytest.importorskip("cv2")
    img = np.full((300, 400, 3), 255, np.uint8)
    cv2.ellipse(img, (200, 200), (120, 70), 0, 0, 360, (30, 30, 30), -1)
    return img


def _convert_ellipse(tmp_path, *, mask_text: bool):
    cv2 = pytest.importorskip("cv2")
    from edge_to_dxf import EdgeToDXF

    img = _ellipse_image()
    src = tmp_path / "src.png"
    out = tmp_path / "out.dxf"
    cv2.imwrite(str(src), img)
    return EdgeToDXF().convert_enhanced(
        str(src), str(out), target_height_mm=200.0, mask_text=mask_text
    ), out


class TestTextMaskingDisposition:
    """F-3: a requested mask that did not apply is DEGRADED and still emits a DXF."""

    def test_reader_constructor_failure_is_initialization(self):
        import types
        import edge_to_dxf
        from edge_to_dxf import TextDetectionError

        fake = types.ModuleType("easyocr")

        class _Reader:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("weights missing")

        fake.Reader = _Reader
        original = sys.modules.get("easyocr")
        sys.modules["easyocr"] = fake
        try:
            with pytest.raises(TextDetectionError) as caught:
                edge_to_dxf._initialize_easyocr_reader()
            assert caught.value.diagnostic_code == "OCR_INITIALIZATION_FAILED"
        finally:
            if original is None:
                sys.modules.pop("easyocr", None)
            else:
                sys.modules["easyocr"] = original

    def test_unavailable_provider_emits_degraded_dxf(self, tmp_path):
        import edge_to_dxf
        from edge_to_dxf import ConversionStatus

        original, original_avail = edge_to_dxf._EASYOCR_READER, edge_to_dxf._EASYOCR_AVAILABLE
        edge_to_dxf._EASYOCR_READER = None
        edge_to_dxf._EASYOCR_AVAILABLE = False
        try:
            result, out = _convert_ellipse(tmp_path, mask_text=True)
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail

        assert result.status is ConversionStatus.DEGRADED
        assert result.text_masking.diagnostic_code == "OCR_PROVIDER_UNAVAILABLE"
        assert result.text_masking.provider_available is False
        assert result.text_masking.attempted is False
        assert result.text_masking.applied is False
        assert out.exists()
        assert result.line_count > 0

    def test_initialization_failure_emits_degraded_dxf(self, tmp_path):
        import edge_to_dxf
        from edge_to_dxf import ConversionStatus, TextDetectionError

        def _boom():
            raise TextDetectionError(
                "init",
                diagnostic_code="OCR_INITIALIZATION_FAILED",
            )

        original, original_avail = edge_to_dxf._EASYOCR_READER, edge_to_dxf._EASYOCR_AVAILABLE
        original_init = edge_to_dxf._initialize_easyocr_reader
        edge_to_dxf._EASYOCR_READER = None
        edge_to_dxf._EASYOCR_AVAILABLE = True
        edge_to_dxf._initialize_easyocr_reader = _boom
        try:
            result, out = _convert_ellipse(tmp_path, mask_text=True)
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail
            edge_to_dxf._initialize_easyocr_reader = original_init

        assert result.status is ConversionStatus.DEGRADED
        assert result.text_masking.diagnostic_code == "OCR_INITIALIZATION_FAILED"
        assert result.text_masking.provider_available is True
        assert result.text_masking.attempted is False
        assert out.exists()

    def test_no_text_is_success(self, tmp_path):
        import edge_to_dxf
        from edge_to_dxf import ConversionStatus

        class _Empty:
            def readtext(self, image):
                return []

        original, original_avail = edge_to_dxf._EASYOCR_READER, edge_to_dxf._EASYOCR_AVAILABLE
        edge_to_dxf._EASYOCR_READER = _Empty()
        edge_to_dxf._EASYOCR_AVAILABLE = True
        try:
            result, out = _convert_ellipse(tmp_path, mask_text=True)
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail

        assert result.status is ConversionStatus.SUCCESS
        assert result.text_masking.diagnostic_code == "OCR_NO_TEXT_DETECTED"
        assert result.text_masking.attempted is True
        assert result.text_masking.applied is False
        assert result.text_detection_failed is False
        assert out.exists()

    def test_detected_text_reports_applied(self, tmp_path):
        import edge_to_dxf
        from edge_to_dxf import ConversionStatus

        class _Hit:
            def readtext(self, image):
                box = [[80, 80], [160, 80], [160, 140], [80, 140]]
                return [(box, "Melody", 0.95)]

        original, original_avail = edge_to_dxf._EASYOCR_READER, edge_to_dxf._EASYOCR_AVAILABLE
        edge_to_dxf._EASYOCR_READER = _Hit()
        edge_to_dxf._EASYOCR_AVAILABLE = True
        try:
            result, _out = _convert_ellipse(tmp_path, mask_text=True)
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail

        assert result.status is ConversionStatus.SUCCESS
        assert result.text_masking.applied is True
        assert result.text_masking.diagnostic_code == "TEXT_MASK_APPLIED"

    def test_mask_not_requested_stays_success_without_ocr(self, tmp_path):
        import edge_to_dxf
        from edge_to_dxf import ConversionStatus

        original, original_avail = edge_to_dxf._EASYOCR_READER, edge_to_dxf._EASYOCR_AVAILABLE
        edge_to_dxf._EASYOCR_READER = None
        edge_to_dxf._EASYOCR_AVAILABLE = False
        try:
            result, out = _convert_ellipse(tmp_path, mask_text=False)
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail

        assert result.status is ConversionStatus.SUCCESS
        assert result.text_masking.requested is False
        assert result.text_masking.diagnostic_code is None
        assert result.text_detection_failed is False
        assert out.exists()

    def test_enhanced_acceptance_withholds_manufacturing_accept(self):
        from app.services.blueprint_orchestrator import (
            BlueprintResult,
            enhanced_acceptance,
        )
        from app.services.contour_recommendation import RecommendationAction

        ok, stage, action, _reasons = enhanced_acceptance(
            True,
            {"diagnostic_code": "OCR_PROVIDER_UNAVAILABLE", "applied": False},
        )
        assert ok is False
        assert stage == "complete"
        assert action is RecommendationAction.REVIEW

        ok, _stage, action, _reasons = enhanced_acceptance(
            True,
            {"diagnostic_code": "OCR_NO_TEXT_DETECTED", "applied": False},
        )
        assert ok is True
        assert action is RecommendationAction.ACCEPT

        ok, _stage, action, _reasons = enhanced_acceptance(
            True,
            {"requested": False, "diagnostic_code": None},
        )
        assert ok is True
        assert action is RecommendationAction.ACCEPT

        payload = BlueprintResult(
            ok=False,
            text_masking={"diagnostic_code": "OCR_PROVIDER_UNAVAILABLE", "applied": False},
        ).to_response_dict()
        assert payload["text_masking"]["diagnostic_code"] == "OCR_PROVIDER_UNAVAILABLE"
        assert "entity_count" in payload["artifacts"]["dxf"]

    def test_enhanced_api_payload_exposes_degraded_disposition(self):
        from types import SimpleNamespace

        from app.routers.blueprint.edge_to_dxf_router import (
            EdgeToDXFResponse,
            enhanced_masking_payload,
        )
        from edge_to_dxf import TextMaskingDisposition

        result = SimpleNamespace(
            status=SimpleNamespace(value="DEGRADED"),
            text_masking=TextMaskingDisposition.from_failure("OCR_PROVIDER_UNAVAILABLE"),
        )
        payload = enhanced_masking_payload(result)
        response = EdgeToDXFResponse(line_count=3, **payload)
        assert response.success is True
        assert response.status == "DEGRADED"
        assert response.text_masking["applied"] is False
        assert response.text_masking["diagnostic_code"] == "OCR_PROVIDER_UNAVAILABLE"
