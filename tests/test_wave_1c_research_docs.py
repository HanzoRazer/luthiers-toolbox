from pathlib import Path
import pytest

R = Path(__file__).resolve().parents[1] / "docs" / "research"

@pytest.mark.parametrize("n", [
    "SEMANTIC_ARTIFACT_QUALITY.md",
    "WAVE_1C_QUALITY_FIXTURES.md",
])
def test_1c(n):
    assert (R / n).is_file()
