"""GitHub adapter tests using an injected fake transport (no network)."""

from __future__ import annotations

import json

import pytest

from tools.grounding_agent.adapters.github_api import (
    GitHubAdapter,
    GitHubAuthError,
    GitHubNotFound,
    GitHubUnavailable,
    HttpResponse,
)


def _transport_returning(status, body):
    def _transport(url, headers):
        assert "Authorization" in headers  # token propagated
        return HttpResponse(status_code=status, body=body)

    return _transport


def test_get_pull_request_success():
    pr = {"number": 312, "state": "open", "draft": True, "merged": False}
    adapter = GitHubAdapter(token="t", transport=_transport_returning(200, json.dumps(pr)))
    data = adapter.get_pull_request("owner/repo", 312)
    assert data["number"] == 312
    assert data["draft"] is True


def test_get_ref_success():
    body = {"sha": "abc123", "commit": {}}
    adapter = GitHubAdapter(token="t", transport=_transport_returning(200, json.dumps(body)))
    assert adapter.get_ref("owner/repo", "main")["sha"] == "abc123"


def test_missing_token_raises_auth_error():
    # No token provided and none in env (transport should never be called).
    def _boom(url, headers):  # pragma: no cover - must not be called
        raise AssertionError("transport must not be called without a token")

    adapter = GitHubAdapter(token="", transport=_boom)
    with pytest.raises(GitHubAuthError):
        adapter.get_pull_request("owner/repo", 1)


def test_401_raises_auth_error():
    adapter = GitHubAdapter(token="t", transport=_transport_returning(401, "{}"))
    with pytest.raises(GitHubAuthError):
        adapter.get_pull_request("owner/repo", 1)


def test_404_raises_not_found():
    adapter = GitHubAdapter(token="t", transport=_transport_returning(404, "{}"))
    with pytest.raises(GitHubNotFound):
        adapter.get_pull_request("owner/repo", 1)


def test_500_raises_unavailable():
    adapter = GitHubAdapter(token="t", transport=_transport_returning(500, ""))
    with pytest.raises(GitHubUnavailable):
        adapter.get_ref("owner/repo", "main")


def test_malformed_json_raises_unavailable():
    adapter = GitHubAdapter(token="t", transport=_transport_returning(200, "not-json{"))
    with pytest.raises(GitHubUnavailable):
        adapter.get_pull_request("owner/repo", 1)


def test_non_object_payload_raises_unavailable():
    adapter = GitHubAdapter(token="t", transport=_transport_returning(200, "[1, 2, 3]"))
    with pytest.raises(GitHubUnavailable):
        adapter.get_ref("owner/repo", "main")


def test_token_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "envtoken")
    captured = {}

    def _transport(url, headers):
        captured["auth"] = headers.get("Authorization")
        return HttpResponse(status_code=200, body=json.dumps({"sha": "x"}))

    adapter = GitHubAdapter(transport=_transport)
    adapter.get_ref("owner/repo", "main")
    assert captured["auth"] == "Bearer envtoken"
