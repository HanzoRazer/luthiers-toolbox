"""
Tests for tier_gate middleware.

Tests feature and tier gating dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.auth.principal import Principal


class TestTierGate:
    """Tests for tier gate middleware."""

    @pytest.fixture
    def mock_principal(self):
        """Create a mock principal."""
        return Principal(
            user_id="test-user-123",
            roles={"user"},
            email="test@example.com"
        )

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock()

    def test_tier_levels_hierarchy(self):
        """Verify tier level hierarchy is correct."""
        from app.middleware.tier_gate import TIER_LEVELS

        assert TIER_LEVELS["free"] < TIER_LEVELS["pro"]

    @pytest.mark.asyncio
    async def test_get_user_tier_returns_tier(self, mock_db_session):
        """_get_user_tier returns user's tier."""
        from app.middleware.tier_gate import _get_user_tier

        mock_row = MagicMock()
        mock_row.tier = "pro"
        mock_db_session.execute.return_value.fetchone.return_value = mock_row

        tier = await _get_user_tier("user-123", mock_db_session)

        assert tier == "pro"

    @pytest.mark.asyncio
    async def test_get_user_tier_default_free(self, mock_db_session):
        """_get_user_tier returns 'free' for unknown user."""
        from app.middleware.tier_gate import _get_user_tier

        mock_db_session.execute.return_value.fetchone.return_value = None

        tier = await _get_user_tier("unknown-user", mock_db_session)

        assert tier == "free"

    @pytest.mark.asyncio
    async def test_check_feature_access_allowed(self, mock_db_session):
        """_check_feature_access returns True when allowed."""
        from app.middleware.tier_gate import _check_feature_access

        mock_row = MagicMock()
        mock_row.enabled = True
        mock_row.min_tier = "free"
        mock_db_session.execute.return_value.fetchone.return_value = mock_row

        result = await _check_feature_access("free", "basic_feature", mock_db_session)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_feature_access_denied_tier(self, mock_db_session):
        """_check_feature_access returns False when tier insufficient."""
        from app.middleware.tier_gate import _check_feature_access

        mock_row = MagicMock()
        mock_row.enabled = True
        mock_row.min_tier = "pro"
        mock_db_session.execute.return_value.fetchone.return_value = mock_row

        result = await _check_feature_access("free", "pro_feature", mock_db_session)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_feature_access_disabled(self, mock_db_session):
        """_check_feature_access returns False when feature disabled."""
        from app.middleware.tier_gate import _check_feature_access

        mock_row = MagicMock()
        mock_row.enabled = False
        mock_row.min_tier = "free"
        mock_db_session.execute.return_value.fetchone.return_value = mock_row

        result = await _check_feature_access("pro", "disabled_feature", mock_db_session)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_feature_access_unknown_feature(self, mock_db_session):
        """_check_feature_access returns False for unknown feature."""
        from app.middleware.tier_gate import _check_feature_access

        mock_db_session.execute.return_value.fetchone.return_value = None

        result = await _check_feature_access("pro", "nonexistent", mock_db_session)

        assert result is False


class TestRequireFeature:
    """Tests for require_feature dependency factory."""

    @pytest.fixture
    def mock_principal(self):
        return Principal(user_id="user-123", roles={"user"}, email="test@example.com")

    def test_require_feature_returns_callable(self):
        """require_feature returns a callable dependency."""
        from app.middleware.tier_gate import require_feature

        dependency = require_feature("test_feature")
        assert callable(dependency)

    @pytest.mark.asyncio
    async def test_require_feature_allows_when_feature_available(self, mock_principal):
        """require_feature allows access when feature is available."""
        from app.middleware.tier_gate import require_feature

        gate = require_feature("basic_dxf_export")

        # Mock the internals
        with patch("app.middleware.tier_gate._get_user_tier", new_callable=AsyncMock) as mock_tier:
            with patch("app.middleware.tier_gate._check_feature_access", new_callable=AsyncMock) as mock_access:
                mock_tier.return_value = "free"
                mock_access.return_value = True

                mock_db = MagicMock()

                # Call the gate directly with mocked dependencies
                with patch("app.middleware.tier_gate.get_current_principal", return_value=mock_principal):
                    with patch("app.middleware.tier_gate.get_db", return_value=mock_db):
                        # The gate function is async, call it with mocked deps
                        result = await gate(principal=mock_principal, db=mock_db)

                        assert result == mock_principal

    @pytest.mark.asyncio
    async def test_require_feature_denies_when_feature_not_available(self, mock_principal):
        """require_feature raises 403 when feature not available."""
        from fastapi import HTTPException
        from app.middleware.tier_gate import require_feature

        gate = require_feature("ai_vision")

        with patch("app.middleware.tier_gate._get_user_tier", new_callable=AsyncMock) as mock_tier:
            with patch("app.middleware.tier_gate._check_feature_access", new_callable=AsyncMock) as mock_access:
                mock_tier.return_value = "free"
                mock_access.return_value = False  # Not available

                mock_db = MagicMock()

                with pytest.raises(HTTPException) as exc_info:
                    await gate(principal=mock_principal, db=mock_db)

                assert exc_info.value.status_code == 403
                assert exc_info.value.detail["error"] == "feature_not_available"


class TestRequireTier:
    """Tests for require_tier dependency factory."""

    @pytest.fixture
    def mock_principal(self):
        return Principal(user_id="user-123", roles={"user"}, email="test@example.com")

    def test_require_tier_returns_callable(self):
        """require_tier returns a callable dependency."""
        from app.middleware.tier_gate import require_tier

        dependency = require_tier("pro")
        assert callable(dependency)

    @pytest.mark.asyncio
    async def test_require_tier_allows_sufficient_tier(self, mock_principal):
        """require_tier allows when user has sufficient tier."""
        from app.middleware.tier_gate import require_tier

        gate = require_tier("free")

        with patch("app.middleware.tier_gate._get_user_tier", new_callable=AsyncMock) as mock_tier:
            mock_tier.return_value = "pro"  # Pro can access free features
            mock_db = MagicMock()

            result = await gate(principal=mock_principal, db=mock_db)

            assert result == mock_principal

    @pytest.mark.asyncio
    async def test_require_tier_denies_insufficient_tier(self, mock_principal):
        """require_tier raises 403 when tier insufficient."""
        from fastapi import HTTPException
        from app.middleware.tier_gate import require_tier

        gate = require_tier("pro")

        with patch("app.middleware.tier_gate._get_user_tier", new_callable=AsyncMock) as mock_tier:
            mock_tier.return_value = "free"  # Free cannot access pro
            mock_db = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await gate(principal=mock_principal, db=mock_db)

            assert exc_info.value.status_code == 403
            assert exc_info.value.detail["error"] == "tier_required"
            assert exc_info.value.detail["required_tier"] == "pro"


class TestRequirePro:
    """Tests for require_pro convenience dependency."""

    def test_require_pro_is_configured(self):
        """require_pro is properly configured."""
        from app.middleware.tier_gate import require_pro

        # require_pro should be a callable gate function
        assert callable(require_pro)
