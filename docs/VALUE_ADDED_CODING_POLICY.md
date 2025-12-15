# Value-Added Coding Roadmap & Policy

**Last Updated:** November 22, 2025  
**Owner:** Art Studio / RMOS Core Team

This guide describes how and when to introduce additional runtimes (Lua, C++, lightweight HTML shells, etc.) on top of the current Python + TypeScript stack. Treat it as the contract between sandbox development and future value-added integrations.

---

## 1. Strategic Goals

1. **Protect the Sandbox Delivery** – Finish Phase 29 bundles, SpeedsFeeds, and docs/tests on the existing stack before broadening technologies.
2. **Add Capability, Not Chaos** – New runtimes must unlock measurable functionality (e.g., real-time CNC scripting, high-performance CAM kernels) with minimal disruption.
3. **Keep Safety First** – Any embedded scripting or native module must respect unit consistency, machine safety, and export integrity policies outlined in `CODING_POLICY.md`.

---

## 2. Introduction Timeline

| Phase | Target Window | Scope | Exit Criteria |
|-------|---------------|-------|---------------|
| P29 Completion | Current sprint | Finish Art namespace wiring, SpeedsFeeds, docs/tests | ✅ API + client routes stable, tests green |
| Foundation Hardening | +2 sprints | Stabilize logs, telemetry, config system for new runtimes | ✅ Monitoring + error budget defined |
| Value-Added Pilot | +3 sprints | Introduce Lua scripting sandbox + C++ CAM accelerators | ✅ Pilot features shipped behind feature flags |
| Broad Rollout | +4 sprints | Documented workflows, CI coverage, developer training | ✅ Policy sign-off, onboarding updates |

---

## 3. Technology Tracks

### 3.1 Lua Scripting Layer
- **Use Case:** User-authored automation (post tuning, custom workflows, shop macros).
- **Embedding Pattern:** Deterministic sandbox (e.g., `lupa`/`lualite`) running inside the API with hard timeouts and whitelisted stdlib.
- **Data Surface:** JSON payload describing moves/metadata; scripts can return modified payloads or annotations only.
- **Safety Policy:**
  - No direct file/network IO; expose curated helper API.
  - Enforce unit conversions at the boundary; scripts receive mm-only data.
  - Require static analysis (lint) before accepting scripts into the system.

### 3.2 C++ Acceleration Modules
- **Use Case:** High-performance geometry, adaptive kernels, or machine-time estimators.
- **Integration Style:**
  - Header-only or shared-library modules built via CMake; expose Python bindings (pybind11) and optional WASM builds for client use.
  - Maintain feature parity with Python reference implementations to keep fallbacks.
- **Deployment Rules:**
  - All native builds must pass cross-platform CI (Windows + Linux).
  - Provide deterministic tests comparing native vs Python outputs for regressions.
  - Document build flags, ABI expectations, and performance targets.

### 3.3 Lightweight HTML Utilities
- **Scope:** Static micro-UIs for shop-floor kiosks or offline reference.
- **Policy:** Keep them generated from the Vue codebase (e.g., Vite export) to avoid divergent styling/logic. Only pure static info/manuals live outside the SPA.

---

## 4. Policy Checklist for New Runtimes

1. **Justification Memo** – Describe the gap, impacted stakeholders, and why Python/TS cannot deliver the functionality efficiently.
2. **Design Review** – Cross-team meeting covering API surfaces, security model, and CI workflow updates.
3. **Feature Flagging** – All value-added modules ship behind config flags (`VITE_FEATURE_LUA`, `ART_ENABLE_CPP_ACCEL`, etc.).
4. **Testing Plan** –
   - Unit tests for the new language layer.
   - Integration smokes mirroring existing PowerShell scripts.
   - Performance regression baselines (before/after metrics).
5. **Documentation Update** – Add quickrefs, onboarding steps, and troubleshooting guides to `docs/` plus entries in `CODING_POLICY.md`.
6. **Operational Readiness** – Monitoring hooks, log redaction, error handling paths, and incident runbooks updated.

---

## 5. Developer Guidance

- **Stay Focused Now:** Complete the sandbox deliverables using Python + TypeScript. Do not introduce new runtimes mid-sprint without explicit approval.
- **Prototype in Isolation:** When green-lit, build Lua/C++ prototypes in `labs/` or feature branches with clear READMEs explaining setup.
- **Follow the Policy:** No feature graduates unless it satisfies the checklist in Section 4 and aligns with `CODING_POLICY.md`.
- **Review Cadence:** Hold a monthly value-added review meeting to evaluate pilots, deprecations, and roadmap adjustments.

---

## 6. Future Work Items

1. Draft Lua helper API (geometry accessors, metadata writers) and publish sandbox examples.
2. Benchmark C++ adaptive kernels vs Python L.3 implementation to set target gains.
3. Extend CI to build/test native artifacts and run Lua safety scans.
4. Update onboarding materials once pilots prove stable.

---

**Questions or proposals?** Ping the Art Studio core team or file an RFC referencing this document so new work remains aligned with the agreed policy.
