# Makefile for Luthier's Toolbox
# CNC lutherie CAD/CAM platform

.PHONY: help
help:
	@echo "Luthier's Toolbox - Makefile Targets"
	@echo "====================================="
	@echo "smoke-helix-posts       Test helical ramping with all post-processor presets"
	@echo "test-api                Run API smoke tests"
	@echo "start-api               Start FastAPI dev server"
	@echo "start-client            Start Vue dev client"
	@echo "check-art-studio-scope  Run Art Studio ornament-authority scope gate"
	@echo "check-boundaries        Run all architectural fence checks"
	@echo ""
	@echo "Viewer Pack v1 Contract Gate:"
	@echo "viewer-pack-fixture     Regenerate minimal viewer pack fixture zip"
	@echo "viewer-pack-parity      Check schema parity with tap_tone_pi"
	@echo "viewer-pack-gate        Run full viewer pack v1 contract gate"
	@echo ""
	@echo "Agentic Policy Verification:"
	@echo "verify-policy           Verify policy against release-assets/sessions/"
	@echo "verify-policy-fixtures  Verify policy against repo fixtures"

# Configuration
API_HOST ?= 127.0.0.1
API_PORT ?= 8000
API_BASE := http://$(API_HOST):$(API_PORT)

.PHONY: smoke-helix-posts
smoke-helix-posts:
	@echo "=== Testing Helical Post-Processor Presets ==="
	@cd services/api && python -m uvicorn app.main:app --host $(API_HOST) --port $(API_PORT) & \
	 echo $$! > .uvicorn_pid ; \
	 sleep 3 ; \
	 python ../../scripts/smoke/helix_smoke.py "$(API_BASE)" || (kill `cat .uvicorn_pid` 2>/dev/null || true; rm -f .uvicorn_pid; exit 1)
	@kill `cat services/api/.uvicorn_pid` 2>/dev/null || true ; rm -f services/api/.uvicorn_pid
	@echo "=== Saving smoke test results ==="
	@python scripts/smoke/save_helix_results.py
	@echo "=== smoke-helix-posts complete ==="

.PHONY: test-api
test-api:
	cd services/api && pytest tests/ -v

# ------------------------------------------------------------------
# API verification (Phase 32.0 contract tests included automatically)
# ------------------------------------------------------------------
.PHONY: api-test api-verify

# Runs the full API test suite (includes Phase 32.0 contract tests in app/tests)
api-test:
	@echo "🧪 Running API tests (pytest)"
	cd services/api && python -m pytest -q tests/ app/tests/

# Alias: api-verify runs all gates (fences + scope + tests)
api-verify: check-art-studio-scope check-boundaries api-test
	@echo "✅ api-verify complete"

# API Smoke Posts - post-processor smoke test for API Health + Smoke workflow
.PHONY: api-smoke-posts
api-smoke-posts:
	@echo "=== API Smoke Posts (v15.5) ==="
	@bash scripts/smoke/run_api_smoke_posts.sh "$(API_BASE)" "$(API_HOST)" "$(API_PORT)"
	@echo "=== api-smoke-posts complete ==="

.PHONY: start-api
start-api:
	cd services/api && python -m uvicorn app.main:app --reload --port $(API_PORT)

.PHONY: start-client
start-client:
	cd packages/client && npm run dev

# Architectural Boundary Enforcement
.PHONY: check-art-studio-scope
check-art-studio-scope:
	@echo "=== Art Studio Scope Gate ==="
	@python scripts/ci/check_art_studio_scope.py --repo-root .
	@echo "=== Art Studio Scope Gate complete ==="

.PHONY: check-boundaries
check-boundaries:
	@echo "=== Running Architectural Fence Checks ==="
	@echo "[1/7] External boundary (ToolBox ↔ Analyzer)..."
	@cd services/api && python -m app.ci.boundary_imports --profile toolbox --baseline app/ci/fence_baseline.json
	@echo "[2/7] RMOS ↔ CAM domain boundary..."
	@cd services/api && python -m app.ci.domain_boundaries --profile rmos_cam || true
	@echo "[3/7] Operation lane compliance..."
	@cd services/api && python -m app.ci.operation_lane_compliance || true
	@echo "[4/7] AI sandbox boundaries..."
	@python ci/ai_sandbox/check_ai_import_boundaries.py || true
	@python ci/ai_sandbox/check_ai_forbidden_calls.py || true
	@python ci/ai_sandbox/check_ai_write_paths.py || true
	@echo "[5/7] Artifact authority..."
	@python ci/rmos/check_no_direct_runartifact.py || true
	@echo "[6/7] CAM Intent schema validation..."
	@cd services/api && python -m app.ci.check_cam_intent_schema_hash
	@echo "[7/7] Legacy usage gate..."
	@cd services/api && python -m app.ci.legacy_usage_gate --roots "../../packages/client/src" --budget 10
	@echo "=== All fence checks complete ==="
	@echo "✅ See FENCE_REGISTRY.json and docs/governance/FENCE_ARCHITECTURE.md"

# ═══════════════════════════════════════════════════════════════════════════════
# Viewer Pack v1 Contract Gate
# Cross-repo contract between tap_tone_pi (producer) and ToolBox (consumer)
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: viewer-pack-fixture
viewer-pack-fixture:
	@echo "=== Regenerating Viewer Pack v1 Fixture ==="
	@python scripts/validate/generate_minimal_viewer_pack_fixture.py \
		--output services/api/tests/fixtures/viewer_packs/session_minimal.zip
	@echo "=== Fixture regenerated ==="

.PHONY: viewer-pack-parity
viewer-pack-parity:
	@echo "=== Viewer Pack v1 Schema Parity Check ==="
	@python scripts/validate/check_viewer_pack_schema_parity.py --mode check
	@echo "=== Parity check complete ==="

.PHONY: viewer-pack-gate
viewer-pack-gate: viewer-pack-parity
	@echo "=== Viewer Pack v1 Contract Gate ==="
	@cd services/api && python -m pytest tests/test_viewer_pack_v1_ingestion_gate.py -v
	@echo "=== Contract gate complete ==="

# ─────────────────────────────────────────────────────────────────────────────
# Mesh Pipeline (retopo/healing/fields → CAM policy)
# ─────────────────────────────────────────────────────────────────────────────
.PHONY: mesh-example
mesh-example:
	@echo "=== Mesh Pipeline Scaffold Example ==="
	@bash examples/retopo/run.sh qrm
	@python scripts/validate_schemas.py --out-root examples/retopo
	@echo "=== Mesh Pipeline complete ==="

.PHONY: mesh-validate
mesh-validate:
	@python scripts/validate_schemas.py --out-root examples/retopo

.PHONY: mesh-pipeline-tag
mesh-pipeline-tag:
	@bash scripts/tag_preview.sh v0.1.0

# ─────────────────────────────────────────────────────────────────────────────
# Analyzer Ingest Smoke (local - requires tap_tone_pi sibling checkout)
# ─────────────────────────────────────────────────────────────────────────────
.PHONY: analyzer-smoke-local
analyzer-smoke-local:
	@python scripts/analyzer_ingest_smoke.py \
	  --contracts-root ../tap_tone_pi/contracts \
	  --chladni-dir   ../tap_tone_pi/out/DEMO/chladni \
	  --phase2-dir    ../tap_tone_pi/runs_phase2/DEMO/session_0001 \
	  --moe-dir       ../tap_tone_pi/out/DEMO/moe

# ─────────────────────────────────────────────────────────────────────────────
# Agentic Policy Verification
# Replay external/downloaded session artifacts through policy engine
# ─────────────────────────────────────────────────────────────────────────────

# Directory containing downloaded JSONL session assets (not committed)
RELEASE_SESSIONS ?= release-assets/sessions

.PHONY: verify-policy
verify-policy:
	@echo "🔍 Verifying agentic policy against release assets"
	@test -d $(RELEASE_SESSIONS) || ( \
		echo "❌ Missing directory: $(RELEASE_SESSIONS)"; \
		echo "   Create it and drop JSONL session files inside."; \
		exit 1 \
	)
	@python tools/verify_policy.py $(RELEASE_SESSIONS)
	@echo "✅ Policy verification complete"

.PHONY: verify-policy-fixtures
verify-policy-fixtures:
	@echo "🔍 Verifying agentic policy against repo fixtures"
	@python tools/verify_policy.py services/api/tests/fixtures/
	@echo "✅ Fixture verification complete"
