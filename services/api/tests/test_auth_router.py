"""
Tests for auth_router endpoints.

Tests /api/auth/* endpoints for profile and tier management.
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.auth.principal import Principal


class TestAuthRouterEndpoints:
    """Integration tests for auth router endpoints."""

    @pytest.fixture
    def mock_principal(self):
        """Create a mock principal for testing."""
        return Principal(
            user_id="test-user-123",
            roles={"user"},
            email="test@example.com"
        )

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def client(self, mock_principal, mock_db_session):
        """Create test client with mocked auth and db."""
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        app.dependency_overrides[get_current_principal] = lambda: mock_principal
        app.dependency_overrides[get_db] = lambda: mock_db_session

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()

    def test_auth_health(self, client):
        """Auth health endpoint returns ok."""
        response = client.get("/api/auth/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "auth"

    def test_get_me_creates_profile_if_not_exists(self, mock_principal, mock_db_session):
        """GET /me creates profile for new user."""
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        # First query returns no profile (None)
        mock_db_session.execute.return_value.fetchone.return_value = None

        app.dependency_overrides[get_current_principal] = lambda: mock_principal
        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            with TestClient(app) as client:
                response = client.get("/api/auth/me")

                # Should succeed and return default profile
                assert response.status_code == 200
                data = response.json()
                assert data["tier"] == "free"
                assert data["id"] == "test-user-123"

                # Verify commit was called (profile created)
                assert mock_db_session.commit.called
        finally:
            app.dependency_overrides.clear()

    def test_get_me_returns_existing_profile(self, mock_principal, mock_db_session):
        """GET /me returns existing profile."""
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        # Create mock row with proper attribute access
        mock_row = MagicMock()
        mock_row.id = "test-user-123"
        mock_row.tier = "pro"
        mock_row.tier_expires_at = None
        mock_row.display_name = "Test User"
        mock_row.avatar_url = "https://example.com/avatar.png"
        mock_row.preferences = {"theme": "dark"}

        mock_db_session.execute.return_value.fetchone.return_value = mock_row

        app.dependency_overrides[get_current_principal] = lambda: mock_principal
        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            with TestClient(app) as client:
                response = client.get("/api/auth/me")

                assert response.status_code == 200
                data = response.json()
                assert data["tier"] == "pro"
                assert data["display_name"] == "Test User"
                assert data["preferences"]["theme"] == "dark"
        finally:
            app.dependency_overrides.clear()

    def test_patch_me_updates_display_name(self, mock_principal, mock_db_session):
        """PATCH /me updates display_name."""
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        # Mock the get after update
        mock_row = MagicMock()
        mock_row.id = "test-user-123"
        mock_row.tier = "free"
        mock_row.tier_expires_at = None
        mock_row.display_name = "New Name"
        mock_row.avatar_url = None
        mock_row.preferences = {}

        mock_db_session.execute.return_value.fetchone.return_value = mock_row

        app.dependency_overrides[get_current_principal] = lambda: mock_principal
        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            with TestClient(app) as client:
                response = client.patch(
                    "/api/auth/me",
                    json={"display_name": "New Name"}
                )

                assert response.status_code == 200
                # Verify execute was called (for update)
                assert mock_db_session.execute.called
        finally:
            app.dependency_overrides.clear()

    def test_patch_me_no_fields_returns_400(self, mock_principal, mock_db_session):
        """PATCH /me with no fields returns 400."""
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        app.dependency_overrides[get_current_principal] = lambda: mock_principal
        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            with TestClient(app) as client:
                response = client.patch("/api/auth/me", json={})

                assert response.status_code == 400
                assert "no fields" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_get_tier_returns_features(self, mock_principal, mock_db_session):
        """GET /tier returns tier and features."""
        from app.main import app
        from app.auth.deps import get_current_principal
        from app.db.session import get_db

        # Mock tier query result
        tier_row = MagicMock()
        tier_row.tier = "free"
        tier_row.tier_expires_at = None

        # Mock features query result
        feature1 = MagicMock()
        feature1.feature_key = "basic_dxf_export"
        feature1.display_name = "Basic DXF Export"
        feature1.description = "Export DXF files"
        feature1.min_tier = "free"
        feature1.enabled = True

        feature2 = MagicMock()
        feature2.feature_key = "ai_vision"
        feature2.display_name = "AI Vision"
        feature2.description = "AI-powered analysis"
        feature2.min_tier = "pro"
        feature2.enabled = True

        # Setup mock to return different results for different queries
        def mock_execute(query, *args, **kwargs):
            result = MagicMock()
            query_str = str(query)
            if "tier_expires_at FROM user_profiles" in query_str:
                result.fetchone.return_value = tier_row
            elif "FROM feature_flags" in query_str:
                result.fetchall.return_value = [feature1, feature2]
            else:
                result.fetchone.return_value = None
                result.fetchall.return_value = []
            return result

        mock_db_session.execute.side_effect = mock_execute

        app.dependency_overrides[get_current_principal] = lambda: mock_principal
        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            with TestClient(app) as client:
                response = client.get("/api/auth/tier")

                assert response.status_code == 200
                data = response.json()
                assert data["current_tier"] == "free"
                assert len(data["features"]) == 2
        finally:
            app.dependency_overrides.clear()


class TestAuthRouterNoAuth:
    """Tests for endpoints without authentication."""

    def test_auth_health_no_auth_required(self):
        """Auth health endpoint doesn't require auth."""
        from app.main import app

        # Ensure no override is in place
        app.dependency_overrides.clear()

        with TestClient(app) as client:
            response = client.get("/api/auth/health")
            assert response.status_code == 200
