"""
Tests for Supabase authentication provider.

Tests JWT decoding, Principal extraction, and tier checking.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.auth.principal import Principal


class TestSupabaseProvider:
    """Tests for supabase_provider module."""

    def test_is_supabase_configured_false_when_no_env(self):
        """Returns False when env vars not set."""
        with patch.dict("os.environ", {}, clear=True):
            # Re-import to pick up cleared env
            from app.auth import supabase_provider
            # Force reload of module-level vars
            import importlib
            importlib.reload(supabase_provider)
            assert supabase_provider.is_supabase_configured() is False

    def test_is_supabase_configured_true_when_set(self):
        """Returns True when both URL and secret are set."""
        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_JWT_SECRET": "test-secret"
        }):
            from app.auth import supabase_provider
            import importlib
            importlib.reload(supabase_provider)
            assert supabase_provider.is_supabase_configured() is True

    def test_principal_from_supabase_claims_basic(self):
        """Extracts Principal from minimal claims."""
        from app.auth.supabase_provider import principal_from_supabase_claims

        claims = {
            "sub": "user-123",
            "email": "test@example.com",
        }

        principal = principal_from_supabase_claims(claims)

        assert principal.user_id == "user-123"
        assert principal.email == "test@example.com"
        assert "user" in principal.roles  # Default role

    def test_principal_from_supabase_claims_with_roles(self):
        """Extracts roles from app_metadata."""
        from app.auth.supabase_provider import principal_from_supabase_claims

        claims = {
            "sub": "user-456",
            "email": "admin@example.com",
            "app_metadata": {
                "roles": ["admin", "pro"]
            }
        }

        principal = principal_from_supabase_claims(claims)

        assert principal.user_id == "user-456"
        assert "admin" in principal.roles
        assert "pro" in principal.roles

    def test_principal_from_supabase_claims_missing_sub_raises(self):
        """Raises 401 when JWT missing subject."""
        from fastapi import HTTPException
        from app.auth.supabase_provider import principal_from_supabase_claims

        claims = {"email": "test@example.com"}  # No sub

        with pytest.raises(HTTPException) as exc_info:
            principal_from_supabase_claims(claims)

        assert exc_info.value.status_code == 401
        assert "missing subject" in str(exc_info.value.detail).lower()

    def test_principal_from_supabase_claims_string_role(self):
        """Handles single string role in app_metadata."""
        from app.auth.supabase_provider import principal_from_supabase_claims

        claims = {
            "sub": "user-789",
            "app_metadata": {"roles": "admin"}  # String, not list
        }

        principal = principal_from_supabase_claims(claims)
        assert "admin" in principal.roles


class TestDecodeSupabaseJwt:
    """Tests for JWT decoding."""

    def test_decode_jwt_no_secret_raises(self):
        """Raises 500 when JWT secret not configured."""
        from fastapi import HTTPException

        with patch.dict("os.environ", {"SUPABASE_JWT_SECRET": ""}):
            from app.auth import supabase_provider
            import importlib
            importlib.reload(supabase_provider)

            with pytest.raises(HTTPException) as exc_info:
                supabase_provider.decode_supabase_jwt("any-token")

            assert exc_info.value.status_code == 500
            assert "not configured" in str(exc_info.value.detail).lower()

    @pytest.mark.skipif(
        not pytest.importorskip("jwt", reason="PyJWT required"),
        reason="PyJWT not installed"
    )
    def test_decode_jwt_expired_raises(self):
        """Raises 401 for expired token."""
        import jwt
        import time
        from fastapi import HTTPException

        secret = "test-secret-key"

        # Create expired token
        expired_token = jwt.encode(
            {
                "sub": "user-123",
                "aud": "authenticated",
                "exp": int(time.time()) - 3600  # 1 hour ago
            },
            secret,
            algorithm="HS256"
        )

        with patch.dict("os.environ", {"SUPABASE_JWT_SECRET": secret}):
            from app.auth import supabase_provider
            import importlib
            importlib.reload(supabase_provider)

            with pytest.raises(HTTPException) as exc_info:
                supabase_provider.decode_supabase_jwt(expired_token)

            assert exc_info.value.status_code == 401
            assert "expired" in str(exc_info.value.detail).lower()

    @pytest.mark.skipif(
        not pytest.importorskip("jwt", reason="PyJWT required"),
        reason="PyJWT not installed"
    )
    def test_decode_jwt_valid_token(self):
        """Successfully decodes valid token."""
        import jwt
        import time

        secret = "test-secret-key"

        valid_token = jwt.encode(
            {
                "sub": "user-123",
                "email": "test@example.com",
                "aud": "authenticated",
                "exp": int(time.time()) + 3600  # 1 hour from now
            },
            secret,
            algorithm="HS256"
        )

        with patch.dict("os.environ", {"SUPABASE_JWT_SECRET": secret}):
            from app.auth import supabase_provider
            import importlib
            importlib.reload(supabase_provider)

            claims = supabase_provider.decode_supabase_jwt(valid_token)

            assert claims["sub"] == "user-123"
            assert claims["email"] == "test@example.com"


class TestTierChecking:
    """Tests for tier and feature access."""

    def test_check_feature_access_free_tier_free_feature(self):
        """Free user can access free features."""
        from app.auth.supabase_provider import check_feature_access

        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = (True, "free")

        assert check_feature_access("free", "basic_dxf_export", mock_session) is True

    def test_check_feature_access_free_tier_pro_feature(self):
        """Free user cannot access pro features."""
        from app.auth.supabase_provider import check_feature_access

        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = (True, "pro")

        assert check_feature_access("free", "ai_vision", mock_session) is False

    def test_check_feature_access_pro_tier_pro_feature(self):
        """Pro user can access pro features."""
        from app.auth.supabase_provider import check_feature_access

        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = (True, "pro")

        assert check_feature_access("pro", "ai_vision", mock_session) is True

    def test_check_feature_access_disabled_feature(self):
        """Cannot access disabled features regardless of tier."""
        from app.auth.supabase_provider import check_feature_access

        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = (False, "free")

        assert check_feature_access("pro", "deprecated_feature", mock_session) is False

    def test_check_feature_access_unknown_feature(self):
        """Unknown features return False."""
        from app.auth.supabase_provider import check_feature_access

        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = None

        assert check_feature_access("pro", "nonexistent", mock_session) is False
