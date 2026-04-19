"""OpenAPI schema generation regression guard.

Catches PydanticUserError from Response subclasses used as return
annotations - a class of error that surfaces only at schema-gen
time, not at import or route-registration time. Python 3.14
deferred annotations made this a common regression.

Template for all 14 repos post-split.
"""


def test_openapi_schema_builds():
    """Regression guard: /openapi.json must return 200."""
    from app.main import app

    app.openapi_schema = None  # bypass cache, force regeneration
    schema = app.openapi()
    assert schema is not None
    assert "paths" in schema and len(schema["paths"]) > 0
