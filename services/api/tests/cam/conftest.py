"""Shared fixtures for CAM router tests."""
import pytest


@pytest.fixture
def route_registered():
    """Probe whether a path is mounted AND accepts POST — the route-parity
    property the CAM migration tests assert (the intent/legacy CAM lanes are
    POST endpoints that must not be displaced).

    Returns a callable ``check(client, path) -> bool``. A probe POST with an
    empty body yields **404** when the path is unmounted, **405** when it exists
    only under another method (NOT the expected POST lane), and 200/4xx (e.g.
    400/401/403/409/422) when the POST route is present — request validation /
    auth / feasibility, never the handler's real work. Passing on
    ``status not in (404, 405)`` therefore means "mounted AND speaks POST",
    which is exactly the parity property and is robust to this codebase's
    in-flight auth gating (an added ``Depends()`` returns 401/403, not a false
    404). A positive whitelist of {200, 409, 422} was deliberately rejected as
    MORE brittle — it would false-fail the moment a probed lane gains an auth gate.

    Why a reachability probe instead of ``{r.path for r in app.routes}``:
    under the repo's fastapi>=0.137 pin, nested ``include_router`` keeps
    ``_IncludedRouter`` wrappers whose children carry *relative* paths, so a
    3-level-nested path (``/api/cam/{lane}/intent-gcode``) never appears as a
    single string in ``app.routes`` (and the wrappers have no ``.path``). The
    endpoints resolve and serve — the live-200/409/422 tests in the same test
    classes prove it; only path-string introspection could not see them.

    Why the ``not in (404, 405)`` blacklist is not fooled by a catch-all:
    the app registers no wildcard/``{path:path}`` route, no root ``Mount``, no
    SPA fallback, and no 404-rewriting exception handler; the governance /
    analytics middlewares only observe ``call_next``'s response, never fabricate
    one. An unmounted ``/api/cam/...`` path genuinely returns 404 (verified
    2026-07-01)."""

    def _check(client, path: str) -> bool:
        return client.post(path, json={}).status_code not in (404, 405)

    return _check
