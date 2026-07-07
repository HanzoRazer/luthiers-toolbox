from __future__ import annotations

from types import SimpleNamespace

from scripts import build_endpoint_consumer_map as builder


class _IncludedRouter:
    def __init__(self, original_router, prefix: str, tags: list[str]):
        self.original_router = original_router
        self.include_context = SimpleNamespace(prefix=prefix, tags=tags)


def _endpoint(module: str = "app.routers.cam.geometry_authority_router"):
    def handler():
        return None

    handler.__module__ = module
    return handler


def test_extract_endpoint_literals_from_js_and_python_strings():
    text = """
    fetch("/api/cam/jobs/123");
    const url = `/api/rmos/runs/${runId}`;
    client.get('/health');
    """

    assert builder.extract_endpoint_literals(text) == [
        "/api/cam/jobs/123",
        "/api/rmos/runs/${runId}",
        "/health",
    ]


def test_extract_legacy_exports_root_literal():
    # CI-RED-016-C: the legacy DXF export surface is mounted without an /api
    # prefix; a plain quoted literal must be recognized as an endpoint reference.
    text = 'await fetch("/exports/polyline_dxf", { method: "POST" });'
    assert builder.extract_endpoint_literals(text) == ["/exports/polyline_dxf"]


def test_extract_template_base_exports_suffix():
    # The frontend DXF helper (packages/client/src/utils/curvemath_dxf.ts) calls
    # `${API_BASE}/exports/...`; the static suffix must be normalized to the mounted
    # path, dropping the interpolated base expression, so a variable base URL still
    # counts as first-party consumer evidence.
    text = "\n".join(
        [
            "fetch(`${API_BASE}/exports/polyline_dxf`, { method: 'POST' });",
            "fetch(`${API_BASE}/exports/biarc_dxf`, opts);",
            "fetch(`${API_BASE}/exports/dxf/health`);",
        ]
    )
    assert builder.extract_endpoint_literals(text) == [
        "/exports/biarc_dxf",
        "/exports/dxf/health",
        "/exports/polyline_dxf",
    ]


def test_extract_template_base_exports_suffix_with_query_string():
    text = "fetch(`${API_BASE}/exports/polyline_dxf?download=1`, opts);"
    assert builder.extract_endpoint_literals(text) == [
        "/exports/polyline_dxf?download=1"
    ]


def test_extract_template_base_scoped_to_exports_only():
    # CI-RED-016-C scopes the template-base form to the legacy /exports surface.
    # A template-base /api reference is intentionally NOT recognized here (that
    # generalization is a separate follow-up), so this PR does not reclassify
    # unrelated /api endpoints.
    text = "fetch(`${API_BASE}/api/tooling/library/materials`);"
    assert builder.extract_endpoint_literals(text) == []


def test_extract_ignores_non_endpoint_root_assets():
    # Conservative extractor: only mounted API roots count, not arbitrary assets.
    text = 'const logo = "/assets/logo.svg"; const css = `${BASE}/static/app.css`;'
    assert builder.extract_endpoint_literals(text) == []


def test_frontend_curvemath_dxf_exports_consumers_are_detected():
    path = builder.repo_root() / "packages/client/src/utils/curvemath_dxf.ts"
    literals = builder.extract_endpoint_literals(path.read_text(encoding="utf-8"))

    assert "/exports/polyline_dxf" in literals
    assert "/exports/biarc_dxf" in literals
    assert "/exports/dxf/health" in literals


def test_parameterized_endpoint_matches_static_consumer_prefix():
    assert builder.reference_matches_endpoint(
        "/api/cam/jobs/123",
        "/api/cam/jobs/{job_id}",
    )
    assert not builder.reference_matches_endpoint(
        "/api/cam/job-history/123",
        "/api/cam/jobs/{job_id}",
    )


def test_consumer_file_classification_by_root():
    root = builder.repo_root()

    assert builder.classify_consumer_file(
        root / "packages/client/src/sdk/endpoints/cam.ts"
    ) == "frontend_sdk"
    assert builder.classify_consumer_file(
        root / "packages/client/src/components/CamPanel.tsx"
    ) == "frontend_product"
    assert builder.classify_consumer_file(
        root / "services/api/tests/test_cam.py"
    ) == "test_only"
    assert builder.classify_consumer_file(
        root / "services/api/app/ci/fence.py"
    ) == "ci_governance"


def test_consumer_scan_treats_exports_examples_in_scanner_artifacts_as_noise():
    self_paths = [
        "services/api/scripts/build_endpoint_consumer_map.py",
        "services/api/tests/test_endpoint_consumer_map_builder.py",
        "docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md",
        "docs/audit/CI_RED_016C_LEGACY_EXPORT_CLUSTER_DISPOSITION.md",
    ]

    for rel in self_paths:
        assert builder.is_self_observation_noise(rel, "/exports/polyline_dxf")

    assert not builder.is_self_observation_noise(
        "packages/client/src/utils/curvemath_dxf.ts",
        "/exports/polyline_dxf",
    )
    assert not builder.is_self_observation_noise(
        "services/api/scripts/build_endpoint_consumer_map.py",
        "/api/jobs",
    )


def test_included_router_flattening_preserves_prefix_tags_and_module():
    route = SimpleNamespace(
        path="/references/canonical/process-approved",
        methods={"POST"},
        endpoint=_endpoint(),
        name="create_process_approved_reference",
        tags=["Authority"],
    )
    app = SimpleNamespace(
        routes=[
            _IncludedRouter(
                SimpleNamespace(routes=[route]),
                prefix="/api/cam/geometry-authority",
                tags=["CAM"],
            )
        ]
    )

    entries = list(builder.iter_http_routes_from_app(app))

    assert entries == [
        {
            "method": "POST",
            "path": "/api/cam/geometry-authority/references/canonical/process-approved",
            "route_name": "create_process_approved_reference",
            "router_module": "app.routers.cam.geometry_authority_router",
            "router_file": "services/api/app/routers/cam/geometry_authority_router.py",
            "tags": ("CAM", "Authority"),
        }
    ]


def test_lane_classifier_keeps_authority_and_governance_distinct():
    assert builder.classify_lane(
        "/api/cam/geometry-authority/references",
        ["app.routers.cam.geometry_authority_router"],
        ["CAM"],
    ) == "authority_reference"
    assert builder.classify_lane(
        "/api/cam/translator-governance/reviews",
        ["app.routers.cam.translator_governance_review_router"],
        ["CAM"],
    ) == "cam_governance"
    assert builder.classify_lane(
        "/api/blueprint/vectorize",
        ["app.routers.blueprint.phase3_router"],
        ["Blueprint"],
    ) == "blueprint_vectorizer"
    assert builder.classify_lane(
        "/api/woodworking/bandsaw/kerf",
        ["app.routers.woodworking_router"],
        ["Woodworking"],
    ) == "woodworking_instrument_design"


def test_no_consumer_note_is_protective_for_governance_lanes():
    endpoint = builder.EndpointRecord(
        method="POST",
        path="/api/cam/geometry-authority/references",
        operation_id="create_reference",
        route_names=("create_reference",),
        router_modules=("app.routers.cam.geometry_authority_router",),
        router_files=("services/api/app/routers/cam/geometry_authority_router.py",),
        tags=("CAM",),
        lane="authority_reference",
    )

    item = builder.EndpointWithConsumers(endpoint=endpoint)

    assert item.primary_consumer_class == "no_first_party_consumer_found"
    assert "not deletion evidence" in item.notes[0]
