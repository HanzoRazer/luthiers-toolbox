"""RMOS-CONVERGE-001B — retract contract guards.

Separate from ``test_rmos_output_route_convergence.py`` on purpose. That module
witnesses the *convergence*: one authority, four routes, no machine output while
blocked. This module pins four narrower contracts that the convergence made
load-bearing but does not itself assert:

1. the ``_governed`` aliases are pure delegations and cannot drift from their
   plain counterparts;
2. an unrecognised retract strategy fails loudly instead of yielding a
   motionless program under a ``.nc`` filename;
3. the two disjoint retract strategy vocabularies are recorded as they stand —
   pinned, **not** endorsed;
4. ``POST /gcode`` binds query-string scalars (a JSON body is ignored);
   ``POST /gcode/download`` binds a JSON body. The Vue exporter talks to
   ``/gcode``, so this is the frontend/API compatibility point.

Only the pair-parity check looks at a status code, and it compares the two
routes rather than asserting a particular value, so these guards keep their
meaning after a retract evaluator lands and the lane returns GREEN.
"""

from __future__ import annotations

import ast
import inspect

import pytest


SIMPLE_PAIR = ("/api/cam/retract/gcode", "/api/cam/retract/gcode_governed")
DOWNLOAD_PAIR = (
    "/api/cam/retract/gcode/download",
    "/api/cam/retract/gcode/download_governed",
)
DOWNLOAD_BODY = {
    "features": [[[0, 0, -10], [10, 0, -10], [10, 10, -10]]],
    "strategy": "safe",
}

# Headers that differ between two identical calls by construction and cannot be
# pinned from the client side.
VOLATILE_HEADERS = {"date", "x-run-id", "server"}

# `RequestIdMiddleware` (app/main.py) echoes a caller-supplied x-request-id and
# only generates one when absent. Supplying the same value on both calls keeps
# that header INSIDE the comparison instead of blinding the test to it — a route
# that started rewriting it would still be caught.
PARITY_REQUEST_ID = "req_alias_parity_probe"

ALIAS_PAIRS = [
    ("generate_simple_retract_gcode", "generate_simple_retract_gcode_governed"),
    ("download_retract_gcode", "download_retract_gcode_governed"),
]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setenv("ENV", "test")
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Could not import FastAPI app: {e}")
    return TestClient(app)


def _post(client, path):
    headers = {"X-Request-ID": PARITY_REQUEST_ID}
    if path in DOWNLOAD_PAIR:
        return client.post(path, json=DOWNLOAD_BODY, headers=headers)
    return client.post(path, headers=headers)


def _comparable(response):
    """Response reduced to what two delegating routes must agree on."""
    headers = {
        k.lower(): v
        for k, v in response.headers.items()
        if k.lower() not in VOLATILE_HEADERS
    }
    body = response.text
    try:
        payload = response.json()
    except ValueError:
        return response.status_code, headers, body

    # run_id is a fresh uuid per call. Blank it rather than drop the field, so a
    # route that stopped emitting one would still register as a difference.
    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, dict) and "run_id" in detail:
        detail["run_id"] = "<run_id>"
    return response.status_code, headers, payload


# ---------------------------------------------------------------------------
# 1. The `_governed` aliases are pure delegations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("plain_name", "alias_name"), ALIAS_PAIRS)
def test_alias_declares_the_same_signature_as_its_plain_counterpart(
    plain_name, alias_name
):
    """
    The alias re-declares its parameters rather than sharing them, so the two
    signatures can drift silently. A different default on one path would make
    the "same authority, same behaviour" claim false for every caller who omits
    that parameter.
    """
    from app.routers.retract import retract_gcode_router as rr

    plain = inspect.signature(getattr(rr, plain_name))
    alias = inspect.signature(getattr(rr, alias_name))

    assert list(plain.parameters) == list(alias.parameters)
    for name, param in plain.parameters.items():
        other = alias.parameters[name]
        assert param.default == other.default, f"{alias_name}.{name} default drifted"
        assert param.annotation == other.annotation, (
            f"{alias_name}.{name} annotation drifted"
        )


@pytest.mark.parametrize(("plain_name", "alias_name"), ALIAS_PAIRS)
def test_alias_body_is_a_single_delegating_return(plain_name, alias_name):
    """
    Structural, not behavioural: the alias must *be* a delegation, not merely
    behave like one while the lane happens to be blocked. An alias that grew its
    own authority or generation code would reopen exactly the second-lane
    problem 001B closed.
    """
    from app.routers.retract import retract_gcode_router as rr

    fn = ast.parse(inspect.getsource(getattr(rr, alias_name))).body[0]
    body = [
        stmt
        for stmt in fn.body
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
    ]

    assert len(body) == 1, f"{alias_name} does more than delegate"
    stmt = body[0]
    assert isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call), (
        f"{alias_name} must return the result of its plain counterpart"
    )

    callee = getattr(stmt.value.func, "id", None) or getattr(
        stmt.value.func, "attr", None
    )
    assert callee == plain_name, (
        f"{alias_name} delegates to {callee!r}, not {plain_name!r}"
    )

    # Every declared parameter is forwarded. A dropped one would silently fall
    # back to the plain route's default instead of the caller's value.
    forwarded = {kw.arg for kw in stmt.value.keywords if kw.arg}
    positional = len(stmt.value.args)
    declared = [arg.arg for arg in fn.args.args]
    assert len(forwarded) + positional == len(declared), (
        f"{alias_name} forwards {sorted(forwarded)} plus {positional} positional, "
        f"but declares {declared}"
    )


@pytest.mark.parametrize(("plain", "alias"), [SIMPLE_PAIR, DOWNLOAD_PAIR])
def test_alias_response_is_indistinguishable_from_the_plain_route(client, plain, alias):
    """
    Behavioural parity on identical input: same status, same headers (bar the
    per-call volatile ones) and same body once the fresh run_id is normalised.

    Deliberately asserts equality between the pair rather than a specific
    status, so it keeps testing the delegation contract after an evaluator lands
    and both routes start returning 200 with G-code.

    Both calls carry the same client-supplied ``X-Request-ID``. Without that the
    correlation middleware mints a fresh id per call and the comparison fails on
    a header that has nothing to do with the delegation contract.
    """
    assert _comparable(_post(client, plain)) == _comparable(_post(client, alias))


# ---------------------------------------------------------------------------
# 2. An unrecognised strategy fails loudly
# ---------------------------------------------------------------------------

SUPPORTED_SIMPLE_STRATEGIES = ("direct", "ramped", "helical")
MOTION_CODES = ("G0 Z", "G1 Z", "G2 X")


@pytest.mark.parametrize("strategy", ["", "bogus", "safe", "minimal", "incremental"])
def test_unsupported_strategy_raises_instead_of_emitting_a_motionless_program(strategy):
    """
    Before this branch existed the builder fell through every case and returned
    a program of header, comments and M30 — no motion at all — which would reach
    an operator as ``retract_<strategy>.nc``. A retract that retracts nothing is
    worse than a failure.

    The download vocabulary values are in this list deliberately: ``safe``,
    ``minimal`` and ``incremental`` are valid on the *other* retract route (see
    the vocabulary guard below), so they are the values most likely to arrive
    here by mistake.
    """
    from app.routers.retract.retract_gcode_router import _build_simple_retract_gcode

    with pytest.raises(ValueError) as exc:
        _build_simple_retract_gcode(strategy, 0.0, 5.0, 600.0, 5.0, 1.0)

    message = str(exc.value)
    assert repr(strategy) in message
    for supported in SUPPORTED_SIMPLE_STRATEGIES:
        assert supported in message, "the error must name the accepted set"


@pytest.mark.parametrize("strategy", SUPPORTED_SIMPLE_STRATEGIES)
def test_supported_strategies_still_emit_motion(strategy):
    """
    Companion to the raise: proves the new ``else`` did not swallow a working
    branch, and that each accepted strategy produces actual Z motion rather than
    the header-only program the raise exists to prevent.
    """
    from app.routers.retract.retract_gcode_router import _build_simple_retract_gcode

    gcode = _build_simple_retract_gcode(strategy, -10.0, 5.0, 600.0, 5.0, 1.0)

    assert any(code in gcode for code in MOTION_CODES), gcode
    assert gcode.strip().endswith("(End of retract sequence)")


def test_simple_builder_embeds_query_equivalent_scalars():
    """
    The Vue exporter's query params only matter if they reach the builder.
    This is the generation half of the query-binding contract; the HTTP half
    is ``test_simple_gcode_binds_query_params_not_json_body``.
    """
    from app.routers.retract.retract_gcode_router import _build_simple_retract_gcode

    ramped = _build_simple_retract_gcode("ramped", -20.0, 12.5, 777.0, 5.0, 1.0)
    assert "(Retract Strategy: ramped)" in ramped
    assert "(Current Z: -20.0mm -> Safe Z: 12.5mm)" in ramped
    assert "G1 Z12.5000 F777" in ramped

    helical = _build_simple_retract_gcode("helical", -10.0, 5.0, 600.0, 7.5, 2.0)
    assert "I7.5000" in helical
    assert "Z" in helical


# ---------------------------------------------------------------------------
# 3. The strategy vocabularies are pinned, not endorsed
# ---------------------------------------------------------------------------

def test_retract_strategy_vocabularies_are_split_and_unreconciled():
    """
    CHARACTERISATION GUARD — this pins the current state, it does not bless it.

    One capability carries two disjoint strategy vocabularies::

        POST /gcode           -> direct | ramped | helical
        POST /gcode/download  -> minimal | safe | incremental   (default: safe)

    Both feed ``tool_id=f"retract:{strategy}"``, so RMOS sees six peer
    identities under one mode, and neither route validates its input against the
    other's set. Reconciling them is queued as a ruling that must land **before**
    any retract evaluator is written — an evaluator must not be built against six
    ambiguous peer identities (census section 8).

    This guard exists so the split cannot (a) change silently, or (b) persist
    silently into evaluator work. If you are here because it failed, the ruling
    is the deliverable, not an edit to the assertion.
    """
    from app.routers.retract.retract_apply_router import RetractStrategyIn
    from app.routers.retract.retract_gcode_router import _build_simple_retract_gcode
    from app.rmos.api.rmos_feasibility_router import resolve_mode

    candidates = ("direct", "ramped", "helical", "minimal", "safe", "incremental")
    simple_vocab = set()
    for candidate in candidates:
        try:
            _build_simple_retract_gcode(candidate, -10.0, 5.0, 600.0, 5.0, 1.0)
        except ValueError:
            continue
        simple_vocab.add(candidate)

    download_default = RetractStrategyIn.model_fields["strategy"].default
    download_vocab = {"minimal", "safe", "incremental"}

    assert simple_vocab == {"direct", "ramped", "helical"}
    assert download_default == "safe"
    assert download_default in download_vocab
    assert simple_vocab.isdisjoint(download_vocab), (
        "the two vocabularies are expected to be disjoint; if they now overlap "
        "or match, the reconciliation ruling has happened and this guard must be "
        "replaced by the canonical vocabulary it establishes"
    )

    # Both vocabularies collapse to one RMOS mode, which is why the split is an
    # identity problem rather than a routing one.
    for strategy in simple_vocab | download_vocab:
        assert resolve_mode(f"retract:{strategy}") == "retract"


# ---------------------------------------------------------------------------
# 4. /gcode binds query params; /gcode/download binds a JSON body
# ---------------------------------------------------------------------------

_SIMPLE_QUERY_NAMES = {
    "strategy",
    "current_z",
    "safe_z",
    "ramp_feed",
    "helix_radius",
    "helix_pitch",
}


def test_simple_gcode_openapi_declares_query_params_not_a_body(client):
    """
    OpenAPI is the public contract. If someone wraps these scalars in a
    Pydantic body model, the Vue query-string POST would silently revert to
    defaults — the exact bug the #315 frontend change closed.
    """
    from app.main import app

    app.openapi_schema = None
    schema = app.openapi()

    simple = schema["paths"]["/api/cam/retract/gcode"]["post"]
    alias = schema["paths"]["/api/cam/retract/gcode_governed"]["post"]
    download = schema["paths"]["/api/cam/retract/gcode/download"]["post"]

    for spec in (simple, alias):
        query_names = {
            p["name"] for p in spec.get("parameters", []) if p.get("in") == "query"
        }
        assert _SIMPLE_QUERY_NAMES <= query_names, query_names
        assert "requestBody" not in spec

    assert "requestBody" in download
    download_query = {
        p["name"] for p in download.get("parameters", []) if p.get("in") == "query"
    }
    assert not (_SIMPLE_QUERY_NAMES & download_query)


def test_simple_gcode_binds_query_params_not_json_body(client):
    """
    Live FastAPI binding, not just OpenAPI.

    Query params must reach authorization (and therefore the builder, once the
    lane reopens) even while the capability is 409 SAFETY_BLOCKED. A JSON body
    with different values is ignored — that was the pre-#315 Vue client, and
    changing the frontend to query params is a bug fix, not a silent behaviour
    change for body-sending callers.

    Asserts against the persisted run rather than a status code, so it keeps
    meaning after a retract evaluator lands.
    """
    from app.rmos.runs_v2.store_api import get_run

    query = (
        "strategy=helical&current_z=-20&safe_z=12"
        "&ramp_feed=800&helix_radius=7.5&helix_pitch=1.5"
    )
    conflicting_body = {
        "strategy": "direct",
        "current_z": 0,
        "safe_z": 0,
        "ramp_feed": 1,
        "helix_radius": 1,
        "helix_pitch": 1,
    }

    r = client.post(f"/api/cam/retract/gcode?{query}", json=conflicting_body)
    assert r.headers.get("X-Run-ID"), r.headers
    run = get_run(r.headers["X-Run-ID"])
    assert run.tool_id == "retract:helical"
    assert run.request_summary["strategy"] == "helical"
    assert run.request_summary["current_z"] == -20.0
    assert run.request_summary["safe_z"] == 12.0
    assert run.request_summary["ramp_feed"] == 800.0
    assert run.request_summary["helix_radius"] == 7.5
    assert run.request_summary["helix_pitch"] == 1.5

    # JSON body alone must not override the documented defaults.
    r_body = client.post(
        "/api/cam/retract/gcode",
        json={"strategy": "helical", "current_z": -99.0, "safe_z": 99.0},
    )
    run_body = get_run(r_body.headers["X-Run-ID"])
    assert run_body.tool_id == "retract:direct"
    assert run_body.request_summary["strategy"] == "direct"
    assert run_body.request_summary["current_z"] == -10.0
    assert run_body.request_summary["safe_z"] == 5.0
