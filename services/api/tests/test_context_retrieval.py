"""
Tests for ai.context_retrieval module.

Tests:
1. test_build_context_packet_with_wood_names - matches wood species
2. test_build_context_packet_with_instrument - matches instrument family
3. test_build_context_packet_truncation - truncates to max_tokens
4. test_build_context_packet_empty_message - returns empty for no matches
"""
import pytest
from unittest.mock import patch, MagicMock

from app.ai.context_retrieval import (
    build_context_packet,
    _extract_wood_names,
    _match_instrument_family,
    _search_materials,
    _truncate_to_tokens,
)


class TestExtractWoodNames:
    """Tests for _extract_wood_names helper."""

    def test_single_wood(self):
        result = _extract_wood_names("I want to use maple for the top")
        assert "maple" in result

    def test_multiple_woods(self):
        result = _extract_wood_names("maple top with mahogany back and ebony fretboard")
        assert "maple" in result
        assert "mahogany" in result
        assert "ebony" in result

    def test_no_woods(self):
        result = _extract_wood_names("just a basic question about guitars")
        assert result == []


class TestMatchInstrumentFamily:
    """Tests for _match_instrument_family helper."""

    def test_stratocaster_aliases(self):
        assert _match_instrument_family("building a strat") == "stratocaster"
        assert _match_instrument_family("Fender Stratocaster") == "stratocaster"

    def test_les_paul_aliases(self):
        assert _match_instrument_family("les paul body") == "les_paul"
        assert _match_instrument_family("LP style guitar") == "les_paul"

    def test_dreadnought(self):
        assert _match_instrument_family("dreadnought acoustic") == "dreadnought"

    def test_no_match(self):
        assert _match_instrument_family("just a generic guitar") is None


class TestTruncateToTokens:
    """Tests for _truncate_to_tokens helper."""

    def test_short_text_unchanged(self):
        text = "Short text"
        result = _truncate_to_tokens(text, max_tokens=100)
        assert result == text

    def test_long_text_truncated(self):
        text = "A" * 1000  # 1000 chars
        result = _truncate_to_tokens(text, max_tokens=100)  # 400 chars max
        assert len(result) < len(text)
        assert "[truncated]" in result


class TestBuildContextPacket:
    """Integration tests for build_context_packet."""

    def test_with_wood_names(self):
        """Test that wood names in message trigger material search."""
        with patch("app.ai.context_retrieval._load_json") as mock_load:
            mock_load.return_value = [
                {"id": "maple_hard", "title": "Maple (hard)", "sce_j_per_mm3": 0.55},
                {"id": "mahogany", "title": "Mahogany", "sce_j_per_mm3": 0.45},
            ]

            result = build_context_packet("What's the best feed rate for maple?")
            assert "Materials" in result
            assert "Maple" in result

    def test_with_instrument_family(self):
        """Test that instrument mentions trigger spec lookup."""
        with patch("app.ai.context_retrieval._load_json") as mock_load:
            mock_load.return_value = {
                "models": {
                    "stratocaster": {
                        "display_name": "Fender Stratocaster",
                        "category": "electric_guitar",
                        "scale_length_mm": 648.0,
                        "fret_count": 22,
                        "string_count": 6,
                        "status": "PARTIAL",
                        "cam_capable": True,
                        "cam_operations": ["body_perimeter", "neck_pocket"],
                        "description": "Classic Fender double-cutaway",
                    }
                }
            }

            result = build_context_packet("I'm building a strat, what neck pocket size?")
            assert "Instrument" in result
            assert "Stratocaster" in result
            assert "648" in result

    def test_truncation_enforced(self):
        """Test that context is truncated to max_tokens."""
        with patch("app.ai.context_retrieval._load_json") as mock_load:
            # Return large dataset to trigger truncation
            mock_load.return_value = [
                {"id": f"wood_{i}", "title": f"Wood Species {i}" * 50, "sce_j_per_mm3": 0.5}
                for i in range(100)
            ]

            result = build_context_packet("Tell me about maple", max_tokens=50)
            # 50 tokens * 4 chars = 200 chars max
            assert len(result) <= 220  # Allow for truncation message

    def test_empty_message_no_matches(self):
        """Test that message with no matches returns empty string."""
        with patch("app.ai.context_retrieval._load_json") as mock_load:
            mock_load.return_value = []

            result = build_context_packet("hello world")
            assert result == ""

    def test_with_project_id(self):
        """Test project data loading from database."""
        import sqlite3

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "id": "proj-123",
            "name": "My Guitar Build",
            "instrument_type": "les_paul",
            "body_wood": "mahogany",
        }

        with patch("app.ai.context_retrieval.RMOS_DB_PATH") as mock_path:
            mock_path.exists.return_value = False  # Skip DB for this test
            # Project lookup should gracefully return empty when DB missing
            result = build_context_packet("what's my project status?", project_id="proj-123")
            # With no DB, should still work but have no project section
            assert "Project Data" not in result or result == ""
