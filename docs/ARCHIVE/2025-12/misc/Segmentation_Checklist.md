🪚 Segmentation Checklist
Luthier’s ToolBox — Multi-Edition Product Split Guide
Version 1.0 — Drop this file in repo root
________________________________________
Purpose
This checklist guides the controlled segmentation of the current ToolBox codebase into:
1.	Express Edition (hobbyist design suite)
2.	Pro Edition (full luthier CAM + jigs + overrides)
3.	Enterprise Edition (financial backroom + shop ops + e-commerce)
This document ensures:
•	Safe cloning of the repo
•	Planned removal of features
•	No loss of core IP
•	Each product can be sandboxed and built independently
________________________________________
✅ 0. Pre-Split Preparation
0.1. Clean and commit all working changes
git add .
git commit -m "Pre-segmentation cleanup"
0.2. Create a snapshot tag
git tag -a v0.8.0-core -m "Pre-segmentation snapshot"
git push --tags
0.3. Back up entire repo to offline storage
•	External SSD
•	NAS
•	Cloud encrypted zip
0.4. Confirm the repo builds cleanly
•	Backend: uvicorn main:app
•	Frontend: npm run build
•	Ensure no broken routes / components
________________________________________
🪞 1. Clone the base repo into 3 independent sandboxes
1.1. Clone working copies for each product
Express:
git clone <repo-url> LTB_Express
cd LTB_Express
git remote remove origin
Pro:
git clone <repo-url> LTB_Pro
cd LTB_Pro
git remote remove origin
Enterprise:
git clone <repo-url> LTB_Enterprise
cd LTB_Enterprise
git remote remove origin
1.2. Create new empty repos on your hosting provider
•	luthiers-toolbox-express
•	luthiers-toolbox-pro
•	luthiers-toolbox-enterprise
Then add remotes:
git remote add origin <new-url>
________________________________________
✂️ 2. Feature Identification & Mapping
2.1. Mark each folder/module with edition tags
Use this quick rule:
Tag	Edition	Definition
E	Express	Design-only features
P	Pro	CAM + overrides + production
X	Enterprise	Business/financial/operations
2.2. Walk through the repo and assign tags
•	/cam/ → P
•	/overrides_engine/ → P
•	/posts/ → P
•	/joblogs/ → P
•	/jigs/ → P
•	/commerce/ → X
•	/financials/ → X
•	/orders/ → X
•	/inventory/ → X
•	/integrations/ → X
•	/rosettes/ → E/P
•	/curves/ → E/P
•	/fretboards/ → E/P
•	/viewer/ → E/P/X
•	/geometry/ → E/P/X
2.3. Mark code comments (optional but recommended)
Add edition markers at the top of modules , e.g.:
# EDITION: PRO
________________________________________
🧹 3. Build Express Edition Repo
3.1. Delete Pro-only modules from Express repo
Remove:
/cam/
/posts/
/overrides_engine/
/joblogs/
/jigs/
/risk_model/
/material_presets/
/multi_machine/
3.2. Delete Enterprise-only modules
/orders/
/customers/
/inventory/
/financials/
/commerce/
/integrations/
/production_schedule/
3.3. Remove UI routes/views referring to removed modules
Delete any Vue pages for:
•	Post Configurator
•	CAM Lab
•	Risk Timeline
•	Production
•	Enterprise dashboards
3.4. Apply Express feature flags in .env
APP_EDITION=EXPRESS
FEATURE_CAM=false
FEATURE_RISK_MODEL=false
FEATURE_FINANCIAL=false
FEATURE_ECOM=false
FEATURE_CUSTOMER_PORTAL=false
3.5. Test that:
•	The design suite loads (Rosette, Curves, Fretboard)
•	Viewer works
•	Export to PDF/SVG works
•	No broken routes in the UI
Commit as:
git add .
git commit -m "Express Edition initial pruning"
git push -u origin main
________________________________________
🛠 4. Build Pro Edition Repo
4.1. Keep everything related to guitar design + CAM + jigs + overrides
Leave in place:
/cam/
/overrides_engine/
/jigs/
/material_presets/
/risk_model/
/joblogs/
/artifacts/
/toolpath_simulator/
4.2. Remove Enterprise-only modules
/orders/
/financials/
/commerce/
/customers/
/inventory/
/ecom_integrations/
4.3. Apply Pro feature flags
APP_EDITION=PRO
FEATURE_CAM=true
FEATURE_RISK_MODEL=true
FEATURE_FINANCIAL=false
FEATURE_ECOM=false
FEATURE_CUSTOMER_PORTAL=false
4.4. Test that:
•	CAM pipelines run
•	Toolpaths export
•	Posts generate
•	Overrides engine loads
•	Jigs connect
•	Dataset saving & loading works
Commit as:
git add .
git commit -m "Pro Edition ready"
git push -u origin main
________________________________________
🏭 5. Build Enterprise Edition Repo
5.1. Keep everything from Pro
Plus Enterprise modules:
/orders/
/customers/
/inventory/
/financials/
/reports/
/ecom_integrations/
/production_schedule/
/analytics/
5.2. Apply Enterprise feature flags
APP_EDITION=ENTERPRISE
FEATURE_CAM=true
FEATURE_RISK_MODEL=true
FEATURE_FINANCIAL=true
FEATURE_ECOM=true
FEATURE_CUSTOMER_PORTAL=true
5.3. Test that:
•	QuickBooks/Shopify integration mocks function
•	Orders load and update
•	Production schedule renders
•	Inventory & BOM sync
•	Customer portal views load
Commit:
git add .
git commit -m "Enterprise Edition initial segmentation"
git push -u origin main
________________________________________
🔁 6. Core Sync Strategy (optional but recommended)
Optional future improvement:
•	Extract /core/geometry/, /core/io/, /core/viewer/, /core/utils/ into a shared repo (ltb-core)
•	Use git submodules, or keep a manual sync process.
For now:
Copy/paste updates into each repo every 60–90 days.
________________________________________
🧪 7. QA Matrix
Create one checklist per edition with must-pass tests:
7.1 Express QA
•	UI loads with no CAM or financial options
•	Rosette / Curve / Fretboard open & save
•	Viewer displays G-code paths
•	Exports PDF/SVG/PNG
•	No Pro-only menus appear
7.2 Pro QA
•	CAM PipelineLab runs
•	Post Configurator exports G-code
•	Overrides engine loads/saves JSON
•	Risk model computes
•	Jig/USB connections work
•	No Enterprise menus appear
7.3 Enterprise QA
•	Orders CRUD
•	Customer approval flows
•	BOM/COGS generate
•	E-commerce sync mock
•	Production calendar updates
•	Everything in Pro also works
________________________________________
🚀 8. Release Checklist (Per Edition)
8.1 Frontend build
npm run build
8.2 Backend build
•	Run packaging script
•	Check Python dependencies
•	Confirm SQLite schema migrated
8.3 Installer build (Electron/Tauri)
•	Windows .exe
•	macOS .dmg
•	Optional Linux AppImage
8.4 Code signing (optional)
8.5 Tag release
git tag -a v1.0.0 -m "Edition 1.0 release"
git push --tags
8.6 Publish release notes
________________________________________
🏁 9. Post-Split Maintenance
Every 30–90 days:
1.	Sync geometry/viewer fixes across all editions
2.	Merge critical bug fixes into all repos
3.	Hold off on Enterprise-only or CAM-heavy updates unless needed
4.	Keep Express ultra-stable and light
________________________________________
🎉 Segmentation Complete
When all checkboxes are satisfied for all three repos, segmentation is complete.

