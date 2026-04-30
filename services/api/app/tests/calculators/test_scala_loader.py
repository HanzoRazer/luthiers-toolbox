# services/api/app/tests/calculators/test_scala_loader.py
"""
Tests for Scala (.scl) file parser.

Sprint FRET-A Phase 1.5, Commit 2.
"""

import pytest
from pathlib import Path

from app.calculators.scala_loader import (
    parse_scala_content,
    parse_scala_file,
    scala_to_fret_ratios,
    serialize_scala_to_text,
    ScalaScale,
    ScalaPitch,
)
from app.calculators.alternative_temperaments import compute_n_tet_ratios

SAMPLES = Path(__file__).resolve().parents[3] / "data" / "scala_samples"


class TestParseScalaContent:
    """Tests for parse_scala_content and parse_scala_file."""

    def test_parses_12tet(self):
        """12tet.scl parses correctly."""
        scale = parse_scala_file(SAMPLES / "12tet.scl")
        assert scale.pitch_count == 12
        assert len(scale.pitches) == 12
        # Last is 2/1
        assert scale.pitches[-1].frequency_ratio == pytest.approx(2.0)

    def test_parses_just_major(self):
        """just_major.scl parses correctly."""
        scale = parse_scala_file(SAMPLES / "just_major.scl")
        assert scale.pitch_count == 7
        # 5/4 is the second pitch (index 1)
        assert scale.pitches[1].ratio == (5, 4)
        assert scale.pitches[1].frequency_ratio == pytest.approx(1.25)

    def test_parses_meantone(self):
        """meantone_quarter.scl parses correctly."""
        scale = parse_scala_file(SAMPLES / "meantone_quarter.scl")
        assert scale.pitch_count == 12
        # First pitch is ~76 cents (much smaller than 12-TET 100)
        assert scale.pitches[0].cents == pytest.approx(76.049)

    def test_rejects_pitch_count_mismatch(self):
        """Pitch count must match number of pitch lines."""
        bad = "desc\n5\n100.0\n200.0\n"  # claims 5 pitches, has 2
        with pytest.raises(ValueError, match="does not match"):
            parse_scala_content(bad)

    def test_rejects_non_monotonic(self):
        """Pitches must strictly increase."""
        bad = "desc\n3\n200.0\n100.0\n300.0\n"
        with pytest.raises(ValueError, match="strictly increase"):
            parse_scala_content(bad)

    def test_handles_comment_lines(self):
        """Comment lines are ignored."""
        content = "! a comment\ndesc\n! another comment\n2\n100.0\n2/1\n"
        scale = parse_scala_content(content)
        assert scale.description == "desc"
        assert scale.pitch_count == 2

    def test_integer_pitch_treated_as_ratio_over_1(self):
        """Integer pitch is treated as ratio with denominator 1."""
        content = "desc\n1\n3\n"
        scale = parse_scala_content(content)
        assert scale.pitches[0].ratio == (3, 1)
        assert scale.pitches[0].frequency_ratio == 3.0

    def test_rejects_empty_file(self):
        """File must have at least description and pitch count."""
        with pytest.raises(ValueError, match="at least"):
            parse_scala_content("desc\n")

    def test_rejects_invalid_ratio(self):
        """Invalid ratio format raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            parse_scala_content("desc\n1\n3/0\n")


class TestScalaToFretRatios:
    """Tests for scala_to_fret_ratios conversion."""

    def test_12tet_round_trip(self):
        """Parsing 12tet.scl and using it to generate ratios should match
        compute_n_tet_ratios(12) within floating-point precision."""
        scale = parse_scala_file(SAMPLES / "12tet.scl")
        scl_ratios = scala_to_fret_ratios(scale, fret_count=12)
        ntet_ratios = compute_n_tet_ratios(12, 12)
        for s, n in zip(scl_ratios, ntet_ratios):
            assert abs(s - n) < 1e-9

    def test_loops_across_period(self):
        """For 22-fret guitar, 12-TET .scl should loop into the second octave."""
        scale = parse_scala_file(SAMPLES / "12tet.scl")
        ratios = scala_to_fret_ratios(scale, fret_count=22)
        assert len(ratios) == 22
        # Fret 12 = 2/1, Fret 13 should be 2 * (12-TET first ratio)
        first = ratios[0]
        assert abs(ratios[12] - 2.0 * first) < 1e-9

    def test_just_major_first_pitch(self):
        """Just major first pitch is 9/8."""
        scale = parse_scala_file(SAMPLES / "just_major.scl")
        ratios = scala_to_fret_ratios(scale, fret_count=7)
        assert abs(ratios[0] - 9/8) < 1e-9
        assert abs(ratios[-1] - 2.0) < 1e-9

    def test_rejects_zero_fret_count(self):
        """fret_count must be >= 1."""
        scale = parse_scala_file(SAMPLES / "12tet.scl")
        with pytest.raises(ValueError, match=">= 1"):
            scala_to_fret_ratios(scale, fret_count=0)

    def test_rejects_empty_scale(self):
        """Scale with no pitches raises ValueError."""
        empty = ScalaScale(description="empty", pitch_count=0, pitches=[])
        with pytest.raises(ValueError, match="no pitches"):
            scala_to_fret_ratios(empty, fret_count=12)


class TestSerializeScala:
    """Tests for serialize_scala_to_text."""

    def test_round_trip_12tet(self):
        """Parse → serialize → parse should produce identical scale."""
        original = parse_scala_file(SAMPLES / "12tet.scl")
        text = serialize_scala_to_text(original)
        reparsed = parse_scala_content(text)

        assert reparsed.description == original.description
        assert reparsed.pitch_count == original.pitch_count
        for o, r in zip(original.pitches, reparsed.pitches):
            assert abs(o.frequency_ratio - r.frequency_ratio) < 1e-9

    def test_round_trip_just_major(self):
        """Ratio-based scale serializes correctly."""
        original = parse_scala_file(SAMPLES / "just_major.scl")
        text = serialize_scala_to_text(original)
        reparsed = parse_scala_content(text)

        assert reparsed.pitch_count == original.pitch_count
        for o, r in zip(original.pitches, reparsed.pitches):
            assert abs(o.frequency_ratio - r.frequency_ratio) < 1e-9
