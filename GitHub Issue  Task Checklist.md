2. GitHub Issue / Task Checklist

(Paste this directly into GitHub as an Issue)

🧹 Orphaned Client Migration — Task Checklist

This checklist tracks the controlled migration of the legacy client/ tree into the canonical packages/client/ monorepo structure.

📦 Phase 0 — Safety

 Zip backup of entire client/ folder

 Commit orphaned inventory to repo

 Create branch: feature/client-migration

📂 Phase 1 — Canonical Structure

 Ensure these exist under packages/client/src/:

 components/toolbox/

 components/compare/

 views/

 utils/

 utils/math/

 labs/

🧮 Phase 2 — Toolbox Calculators Migration (38 components)

 Copy all toolbox components

 Fix imports

 Add Toolbox routes

 Commit bundle

🔍 Phase 3 — Compare Engine Merge

 Compare and merge duplicate compare components

 Move composables + utils

 Reconnect tests

 Commit bundle

🧰 Phase 4 — Utilities / Math Migration

 Move curve math, radius math, neck generators

 Move wiring calculators (treble bleed, switch validator)

 Commit bundle

🖥 Phase 5 — Views & Dashboards

 Migrate Art Studio dashboards

 Migrate Saw Lab dashboard

 Migrate CAM dashboards

 Migrate Preset Hub

 Update router/index.ts

 Commit bundle
⚙️ Phase 6 — G-Code / DXF Tools

 Migrate G-Code Explainer UI

 Migrate DXF tools

 Bind to /api/ai-cam/ and /api/cam/ endpoints

 Commit bundle

🗑 Phase 7 — Retirement of client/

 Verify everything migrated

 Delete client/ folder

 Fix imports

 Build project

 Run all tests

 Commit “remove legacy client tree”

🎉 Completion Criteria

 All UI now lives only under packages/client/src/

 No orphaned code remains

 All calculators functional

 All dashboards accessible

 Build passes

 Test suite passes