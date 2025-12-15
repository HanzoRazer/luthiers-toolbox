Here’s a checkpoint that treats this chat as a build tree and spells out, section by section, what each bundle is supposed to add, including the little nuanced behaviors your dev absolutely should not miss.
I’ll structure it like a requirements checklist, not code, so you can compare implementation vs intent.
________________________________________
0. Context: What tree is this?
This tree is the RMOS Rosette Manufacturing OS arc we’ve been building, centered on:
•	N8.x – Persistence, migration, auditing, dashboards, and repair tools
•	N9.0 – Risk analytics + promotion lanes dashboard
Earlier N8.1–N8.5 were already defined conceptually; in this chat we focused heavily on N8.6+ and N9.0. I’ll still include N8.1–N8.5 at a high level so the tree is complete.
________________________________________
1. N8.x: RMOS Data Spine & Ops
N8.1 — Strip Family Registry (conceptual, previous)
Section goal: Create a first-class “strip family” registry that RMOS can use when planning rosette layouts.
Features to confirm:
•	Backend
o	Persistent store for strip_families (initially JSON).
o	Basic CRUD: create/update/delete/list families.
o	Each family has:
	id
	name
	optional lane and timestamps
	payload for widths/colors/sequence, etc.
•	Frontend
o	Simple manager UI: table of strip families + detail/edit panel.
o	Ability to assign a strip family to rosette plans or templates (even if only stubbed).
Nuances:
•	IDs must be stable (no random changing).
•	Families are reusable presets, not one-off per plan.
________________________________________
N8.2 — DXF-Guided Slicing Engine (conceptual, previous)
Section goal: Take DXF geometry and convert it into “slices” or segments for rosette strips.
Features to confirm:
•	Backend
o	DXF loader (e.g., via ezdxf).
o	Normalized internal representation of arcs, lines, circles.
o	API endpoints to:
	Accept DXF file/path + slice parameters.
	Return slice geometry in a JSON payload (centers, radii, sweep angles, etc.).
•	Frontend
o	Preview panel that visualizes slices over the DXF path.
o	Support for simple shapes (circle, ring, maybe ellipse; lines are okay).
Nuances:
•	Must gracefully handle DXF files with extra layers/entities (ignore unknowns, don’t crash).
•	All coordinates must be in a consistent unit system (mm or inches, but clearly defined).
________________________________________
N8.3 — Export Pipelines (Plan → JSON/PDF + G-code download)
Section goal: Export rosette plans into JSON, PDF, and G-code artifacts.
Features to confirm:
•	Backend
o	API endpoints to:
	Export plan as structured JSON.
	Generate a PDF summary (text + basic diagrams if supported).
	Emit G-code for saw/router operations (even if minimal template).
•	Frontend
o	“Export” panel:
	Buttons: Download JSON, Download PDF, Download G-code.
	Displays export status and possibly filenames or download links.
Nuances:
•	G-code template should be consistent with your existing post style (units, header/footer).
•	Exports should be idempotent: same plan → same output (unless version changes).
•	This export is tied to a specific plan/preset, not a random global state.
________________________________________
N8.4 — Jig Template Exports
Section goal: Generate jig templates from the plan so you can build physical jigs to hold strips/tiles.
Features to confirm:
•	Backend
o	API endpoint to export:
	Jig geometry (JSON).
	Jig PDF (printable drawing / layout).
•	Frontend
o	Jig export panel:
	Allows selecting jig type (e.g., full circle, partial arc).
	Buttons: Download Jig PDF, Download Jig JSON.
Nuances:
•	Jig output is derived from the same rosette plan geometry, not freehand.
•	The PDF should include scale info (1:1, etc.) to avoid print scaling confusion.
________________________________________
N8.5 — CAM Pipeline Handoff (full CAM pipeline handoff)
Section goal: Wire RMOS into a CAM pipeline service (or local queue), so exports can be processed as jobs.
Features to confirm:
•	Backend
o	/rmos/pipeline/handoff (or similar) router that:
	Accepts a plan + context (machine profile, priority, lane).
	Tries to hand off to an external pipeline service.
	Falls back to a local queue if the service is unavailable.
o	JobLog entries created when a handoff occurs.
•	Frontend
o	Send to CAM button in applicable UI (e.g., Rosette Template Lab or export panel).
o	Visual feedback that a pipeline job was created.
Nuances:
•	Handoff must be non-blocking (fire-and-forget pattern with job ID).
•	Local queue fallback should not silently fail; it must at least log the job.
________________________________________
N8.6 — Persistent SQLite Stores (patterns + joblog + strip families)
Section goal: Move RMOS from pure JSON prototypes to SQLite-backed persistence, with a clean abstraction.
Features to confirm:
•	Backend
o	core/rmos_db.py
	connect_db() with RMOS_DB_PATH env override.
	init_db() that creates:
	patterns
	joblog
	strip_families
	Indexes on joblog.preset_id, joblog.job_type, patterns.lane, etc.
o	stores/sqlite_base.py
	Base class that reads/writes payload_json plus scalar columns.
o	SQLitePatternStore, SQLiteJobLogStore, SQLiteStripFamilyStore
	Implement _extract_cols so IDs, lanes, timestamps are real columns.
o	api/deps/rmos_stores.py (PATCH)
	Switch that prefers SQLite, with env override RMOS_SQLITE_DISABLE to drop back to JSON stores.
	Uses @lru_cache() so store instances are reused.
•	Behavior
o	If SQLite initialization fails, system falls back to existing JSON stores.
o	No schema migration is required beyond table creation.
Nuances:
•	SQLite store’s create() should be UPSERT-like with INSERT OR REPLACE.
•	JSON stores should still be operational as a fallback (backwards compatibility).
•	No change in calling API: get_pattern_store() and get_joblog_store() return objects with same interface, independent of backend.
________________________________________
N8.7 — One-time JSON→SQLite Migrator
Section goal: Import existing JSON data into SQLite in a one-time, idempotent script.
Features to confirm:
•	File: server/app/tools/rmos_migrate_json_to_sqlite.py
•	Behavior:
o	CLI options for:
	--patterns-json
	--joblog-json
	--stripfam-json
	--db
	--dry-run
	--verbose
o	Accepts JSON in form:
	list of objects; or
	dict keyed by ID.
o	Skips entries with missing id.
o	On non–dry run, writes through SQLitePatternStore, SQLiteJobLogStore, SQLiteStripFamilyStore.
o	Safe to run multiple times (UPSERT replaces).
Nuances:
•	Default paths under data/rmos/*.json are provided and must match your repo layout.
•	Dry-run mode must not alter the DB but still count what it would import.
________________________________________
N8.7.1 — Migration Report (JSON/PDF/HTML)
Section goal: Generate a detailed migration report comparing JSON vs SQLite.
Features to confirm:
•	File: server/app/tools/rmos_migration_report.py
•	Outputs:
o	<out_base>.json (always).
o	<out_base>.pdf (if reportlab is installed).
o	<out_base>.html (fallback if PDF not available).
•	Metrics per dataset (patterns, joblog, strip_families):
o	JSON:
	total count
	unique ID count
	missing ID count + sample list
	duplicate ID count + sample list
	lane counts
o	SQLite:
	row count
	lane counts
o	Diff:
	only_in_json_count, only_in_sqlite_count
	sample IDs for both sides (capped).
Nuances:
•	HTML should be readable, with preformatted JSON blocks.
•	PDF summarises numeric metrics, not raw IDs, to keep it compact.
________________________________________
N8.7.2 — Migration Audit (auto-open + CI thresholds)
Section goal: Wrap the report generator in an audit runner that can:
•	Auto-open the report locally.
•	Fail CI if mismatch thresholds are exceeded.
Features to confirm:
•	File: server/app/tools/rmos_migration_audit.py
o	Runs rmos_migration_report as a module.
o	Loads resulting JSON.
o	Threshold flags:
	--max-only-in-json
	--max-only-in-sqlite
	--max-missing-ids
	--max-duplicate-ids
o	Optional --open flag to open the report (PDF/HTML/JSON).
o	Exit codes:
	0 = PASS
	2 = thresholds exceeded
	3 = report generation failure.
•	PowerShell CI wrapper: tools/ci/rmos_migration_audit.ps1
o	Shells out to Python audit script.
o	Inherits threshold options.
•	GitHub Actions workflow: .github/workflows/rmos_migration_audit.yml
o	Runs on PR + schedule + manual.
o	Executes audit with strict thresholds (likely 0).
o	Uploads migration report artifacts.
Nuances:
•	Auto-open is only meaningful locally; in CI, it just exits non-zero.
•	Thresholds are configurable via Makefile or CI environment.
________________________________________
N8.7.3 — README Badge Hook (Migration Audit Badge)
Section goal: Show a live badge in README indicating migration audit status.
Features to confirm:
•	Workflow step (in rmos_migration_audit.yml) that:
o	Writes .github/badges/rmos_migration_audit.json with Shields endpoint format:
	label: "rmos migration"
	message: "passing" or "fail"
	color: "brightgreen" or "red"
o	Commits and pushes the badge JSON to the repo after each run.
•	README snippet:
o	A Shields.io endpoint badge referencing the raw badge JSON:
o	![RMOS Migration Audit](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/<USER>/<REPO>/main/.github/badges/rmos_migration_audit.json)
Nuances:
•	Badge should update on every workflow run (success or failure).
•	Repo URL in README badge must be correctly set for your username and repo name.
________________________________________
N8.7.4 — Migration Dashboard UI
Section goal: In-app dashboard showing migration metrics and thresholds, mirroring N8.7.1/8.7.2.
Features to confirm:
•	Backend: migration_report_api.py
o	GET /rmos/migration/report: returns latest report JSON if exists, else a message.
o	POST /rmos/migration/report/run: regenerates report (calls report tool), controlled by env RMOS_ALLOW_REPORT_RUN.
•	Frontend:
o	TS model: rmos_migration_report.ts
o	Store: useMigrationReportStore.ts
	Holds report, thresholds, error state, lastRunOk.
	Methods: fetchReport, runReport, evaluateReport.
o	Component: MigrationDashboardView.vue
	Displays:
	PASS/FAIL banner based on thresholds.
	Threshold inputs (max-only-json, max-only-sqlite, max-missing, max-dup).
	Dataset cards with counts and lane breakdowns.
	Expandable panels for lane counts, missing IDs, diff ID samples.
o	View + router entry: /rmos/migration-dashboard.
Nuances:
•	PASS/FAIL logic in UI must match the threshold logic of N8.7.2.
•	Thresholds stored in store should immediately recompute PASS/FAIL when changed.
________________________________________
N8.7.5 — Fix Drift Wizard
Section goal: Provide a self-healing wizard in the UI to fix JSON↔SQLite drift.
Features to confirm:
•	Backend: migration_fix_api.py + migration_fix.py
o	Env guard: RMOS_ALLOW_FIX_ACTIONS must be honored.
o	POST /rmos/migration/fix/run-migrator
	Runs JSON→SQLite migrator (N8.7).
	Regenerates report.
	Returns { action: "run_migrator", success: true, report: ... }.
o	POST /rmos/migration/fix/export-sqlite-snapshot
	Exports SQLite back to JSON snapshots (patterns, joblog, strip_families).
	Regenerates report from exported JSON.
	Returns paths + counts + updated report.
o	GET /rmos/migration/fix/diff-download
	Returns a compact JSON package of only_in_json_ids / only_in_sqlite_ids.
•	Frontend:
o	Store patch: useMigrationReportStore.ts
	Actions:
	runMigratorFix()
	exportSqliteSnapshotFix()
	driftDiffDownloadUrl()
o	Component: MigrationFixWizard.vue
	Shows:
	Current PASS/FAIL.
	Actions:
	Re-run migrator.
	Export SQLite snapshot.
	Download drift diff.
	Last-action result (pretty-printed JSON).
	Mini table of drift metrics per dataset.
o	View + router entry: /rmos/migration-fix.
Nuances:
•	Exported JSON paths should be re-usable as sources (i.e., valid for next migration).
•	Re-running migrator or export must also re-run the report, updating the dashboard.
________________________________________
2. N9.0: Risk Analytics & Promotion Lanes
Section goal: Use JobLog + patterns to provide risk analytics, lane summaries, and promotion/rollback insights.
Backend: Analytics Core + Routes
Files:
•	schemas/rmos_analytics.py
•	core/rmos_analytics.py
•	api/routes/rmos_analytics_api.py
Features to confirm:
•	Normalized types:
o	RiskGrade (GREEN, YELLOW, RED, unknown)
o	Lane (safe, tuned_v1, tuned_v2, experimental, archived, unknown)
•	compute_lane_analytics():
o	Reads JobLog via get_joblog_store().
o	Reads patterns via get_pattern_store().
o	Normalizes lane as:
	joblog.promotion_lane → joblog.lane → pattern.promotion_lane → pattern.lane → unknown.
o	Computes:
	Global totals:
	total_jobs
	total_presets
	overall average risk score using risk grade weights:
	GREEN = 0.0
	YELLOW = 0.5
	RED = 1.0
	unknown = 0.75
	Grade counts per system and per lane.
	Average risk score per lane.
	recent_runs (up to ~200 latest jobs with key fields).
	lane_transitions derived from job_type in ("preset_promote_winner", "preset_rollback"), using old_lane/parent_lane and promotion_lane.
•	compute_risk_timeline_for_preset(preset_id):
o	List of JobLog entries for that preset.
o	Each mapped to a RiskTimelinePoint:
	created_at, risk_grade, score, lane, job_id.
o	Sorted by created_at.
•	Routes:
o	GET /rmos/analytics/risk → LaneAnalyticsResponse.
o	GET /rmos/analytics/timeline/{preset_id} → RiskTimelineResponse.
Nuances:
•	Must not require any schema migration: all data pulled from existing JobLog and patterns.
•	Graceful behavior when no jobs or no presets exist (zero counts, not errors).
•	Lane transitions logic expects promotion/rollback events to include lane hints (old_lane/parent_lane and promotion_lane).
________________________________________
Frontend: Analytics Models, Store, and Dashboard
Files:
•	models/rmos_analytics.ts
•	stores/useRmosAnalyticsStore.ts
•	components/rmos/RmosAnalyticsDashboard.vue
•	views/RmosAnalyticsView.vue
•	Router entry: /rmos/analytics
Features to confirm:
•	Store:
o	Holds riskAnalytics and timeline.
o	fetchRiskAnalytics(limit?).
o	fetchTimeline(presetId, limit?).
o	Exposes globalSummary getter.
•	Dashboard:
o	Global summary card:
	Total jobs.
	Total presets.
	Overall avg risk score.
	Grade counts.
o	Lane table:
	lane name.
	job count.
	avg risk score.
	grade counts per lane.
o	Lane transitions table:
	from→to + count.
o	Recent runs table:
	created, jobType, preset, lane, risk/doc/gantry grades.
o	Timeline:
	Input field for preset ID; Load timeline button.
	Table of timeline points for that preset.
Nuances:
•	Risk score should display with a reasonable precision (e.g., .toFixed(3) as in the code).
•	The dashboard should still render gracefully when data arrays are empty (no errors).
________________________________________
3. How to Use This Checkpoint
You can hand this to a developer and say:
“For each section (N8.1 to N8.7.5, N9.0), confirm that all items under ‘Features to confirm’ and ‘Nuances’ are implemented as specified.”
If you want, next step can be:
•	A per-file verification checklist, e.g.:
o	server/app/tools/rmos_migrate_json_to_sqlite.py: ✔ flags, ✔ idempotency, ✔ default paths, etc.
•	Or a “diff review protocol”: what to look for in PRs to ensure none of these nuances got dropped.
Here’s a per-file verification checklist for N8.6 → N9.0 that you can hand to a dev (or use to review PRs).
For each file, they should be able to tick every bullet “yes”.
________________________________________
🔹 N8.6 — Persistent SQLite Stores
server/app/core/rmos_db.py
•	get_db_path()
o	Reads RMOS_DB_PATH env var, falls back to data/rmos.sqlite3 (or equivalent data/rmos.sqlite3 path).
o	os.makedirs(os.path.dirname(path), exist_ok=True) before connect.
•	connect_db()
o	Uses sqlite3.connect(path, check_same_thread=False).
o	Sets row_factory = sqlite3.Row.
•	init_db()
o	Creates tables: patterns, joblog, strip_families.
o	Each has an id TEXT PRIMARY KEY and a payload_json TEXT NOT NULL column.
o	Indices exist on:
	joblog(preset_id)
	joblog(job_type)
	patterns(lane)
o	Commits and closes connection if it opened a new one.
________________________________________
server/app/stores/sqlite_base.py
•	Base class SQLiteStoreBase:
o	__init__ calls connect_db + init_db.
o	_row_to_obj():
	Loads payload_json as dict.
	Merges scalar columns (excluding payload_json) into that dict without overwriting payload keys unnecessarily.
o	get(id):
	Uses parameterized query with WHERE id=?.
	Returns None if not found.
o	list(limit, lane=None):
	Returns rows ordered by created_at DESC when present.
	If lane passed, filters WHERE lane=?.
o	create(obj):
	Calls _extract_cols() for scalar columns.
	Always stores full payload_json.
	Uses INSERT OR REPLACE.
o	update(id, patch):
	Reads existing object.
	Merges with patch and sets id.
	Delegates to create.
o	delete(id):
	Deletes row with WHERE id=?.
•	_extract_cols() default:
o	Always includes id first.
o	Optionally includes name, lane, parent_preset_id, source_candidate_id, promotion_lane, created_at, updated_at if present.
________________________________________
server/app/stores/sqlite_pattern_store.py
•	Inherits SQLiteStoreBase.
•	table = "patterns".
•	_extract_cols():
o	Includes id, name, lane, parent_preset_id, source_candidate_id, promotion_lane, created_at, updated_at.
________________________________________
server/app/stores/sqlite_joblog_store.py
•	Inherits SQLiteStoreBase.
•	table = "joblog".
•	_extract_cols():
o	Includes id, job_type, created_at, preset_id, parent_preset_id, parent_job_id, promotion_lane, risk_grade, doc_grade, gantry_grade, notes.
________________________________________
server/app/stores/sqlite_strip_family_store.py
•	Inherits SQLiteStoreBase.
•	table = "strip_families".
•	_extract_cols():
o	Includes id, name, lane, created_at, updated_at.
________________________________________
server/app/api/deps/rmos_stores.py (PATCH)
•	Still imports existing JSON stores (JsonPatternStore, etc.)
•	Imports new SQLite stores and get_db_path.
•	_sqlite_enabled():
o	Returns False if RMOS_SQLITE_DISABLE set to "1", "true", or "yes" (case-insensitive).
•	get_pattern_store() / get_joblog_store() / get_strip_family_store():
o	Decorated with @lru_cache().
o	Tries to construct SQLite store with get_db_path().
o	On exception, falls back cleanly to JSON store.
•	No change to consumer call sites: signature remains same.
________________________________________
🔹 N8.7 — JSON → SQLite Migrator
server/app/tools/rmos_migrate_json_to_sqlite.py
•	CLI args:
o	--patterns-json, --joblog-json, --stripfam-json, --db, --dry-run, --verbose.
o	Default JSON paths under data/rmos/….
•	_load_json(path):
o	Accepts list-of-dicts or dict-of-dicts keyed by ID.
o	Returns a List[dict] of items.
•	migrate_patterns/joblog/strip_families:
o	Skips entries with no id.
o	If dry_run, counts items but does not write.
o	Otherwise calls store.create() for each item.
•	main():
o	Initializes DB via init_db().
o	Instantiates SQLitePatternStore, etc.
o	Prints load + migrated counts.
o	--verbose mode prints some example rows after migration.
________________________________________
🔹 N8.7.1 — Migration Report
server/app/tools/rmos_migration_report.py
•	CLI args:
o	Same JSON paths + --db, --out, --verbose.
•	_summarize_json(items):
o	Computes:
	count, unique_count, missing_id_count, duplicate_id_count.
	lane_counts based on lane OR promotion_lane OR "unknown".
	missing_ids list (capped) and duplicate_ids list (capped).
•	_fetch_sqlite_ids(table):
o	Reads id, lane, promotion_lane, job_type (for joblog).
o	Builds lane_counts with same lane logic as JSON.
o	Returns (count, lane_counts, ids_set).
•	_diff_ids(json_ids, sqlite_ids):
o	Computes only_in_json / only_in_sqlite sets and counts.
•	report JSON structure:
o	generated_at (UTC ISO), db_path.
o	datasets.patterns/joblog/strip_families with:
	.json summary (without raw ids to keep small).
	.sqlite summary.
	.diff counts + sample IDs.
•	Output:
o	<out_base>.json always written.
o	If reportlab available:
	<out_base>.pdf created with global summary.
o	If not:
	<out_base>.html created with human-readable sections.
________________________________________
🔹 N8.7.2 — Migration Audit + CI
server/app/tools/rmos_migration_audit.py
•	Runs app.tools.rmos_migration_report as a subprocess:
o	Passes through all CLI args (JSON paths, DB, out).
o	Handles non-zero exit as a report-generator failure.
•	Reads <out_base>.json and parses counts:
o	Per dataset: only_in_json, only_in_sqlite, missing_ids, duplicate_ids.
•	Threshold CLI args:
o	--max-only-in-json, --max-only-in-sqlite, --max-missing-ids, --max-duplicate-ids.
•	--open:
o	Uses os.startfile (Windows) or webbrowser.open to open PDF, else HTML, else JSON.
•	Exit codes:
o	0: within thresholds.
o	2: thresholds exceeded (and prints dataset/metric/values).
o	3: report generator failed or JSON missing.
________________________________________
tools/ci/rmos_migration_audit.ps1
•	Accepts override parameters for JSON paths, DB, out, thresholds.
•	Calls python -m app.tools.rmos_migration_audit ….
•	Exits with $LASTEXITCODE if non-zero and prints a clear CI error message.
________________________________________
.github/workflows/rmos_migration_audit.yml
•	Triggers:
o	On PR to relevant paths.
o	On workflow_dispatch.
o	On schedule (e.g., Monday cron).
•	Sets up Python, installs backend deps.
•	Runs audit with strict thresholds (e.g., all zeros).
•	Uploads migration report artifacts (JSON + PDF/HTML) using upload-artifact.
________________________________________
services/api/Makefile (RMOS migration targets)
•	Variables:
o	RMOS_PATTERNS_JSON, RMOS_JOBLOG_JSON, RMOS_STRIPFAM_JSON, RMOS_DB_PATH, RMOS_REPORT_BASE.
o	Threshold vars: RMOS_MAX_ONLY_IN_JSON, RMOS_MAX_ONLY_IN_SQLITE, RMOS_MAX_MISSING_IDS, RMOS_MAX_DUPLICATE_IDS.
o	RMOS_OPEN toggle.
•	Targets:
o	rmos-migration-report: calls app.tools.rmos_migration_report.
o	rmos-migration-audit: calls app.tools.rmos_migration_audit with thresholds and optional --open.
________________________________________
Root Makefile (optional)
•	rmos-migration-report / rmos-migration-audit just delegate to services/api with -C.
________________________________________
🔹 N8.7.3 — README Badge Hook
.github/workflows/rmos_migration_audit.yml (badge step)
•	After audit step, there’s a step that:
o	Creates .github/badges directory.
o	Writes rmos_migration_audit.json with:
	schemaVersion: 1
	label: "rmos migration"
	message: "passing" or "fail" based on ${{ job.status }}.
	color: "brightgreen" or "red".
•	Commits and pushes badge JSON on every run (git commit || echo "No changes").
________________________________________
README.md
•	Contains a badge reference like:
•	![RMOS Migration Audit](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/<USER>/<REPO>/main/.github/badges/rmos_migration_audit.json)
•	<USER>/<REPO> updated to your actual GitHub user & repo.
________________________________________
🔹 N8.7.4 — Migration Dashboard UI
server/app/core/migration_report_api.py
•	load_latest_report(base):
o	Looks for <base>.json.
o	If missing, returns a small placeholder with generated_at=None, datasets={}, message="Report not found…".
•	run_report():
o	Calls app.tools.rmos_migration_report with provided JSON/DB/out paths.
o	On success, returns load_latest_report() contents.
o	Raises RuntimeError on non-zero exit.
________________________________________
server/app/api/routes/migration_report_api.py
•	GET /rmos/migration/report:
o	Returns load_latest_report().
•	POST /rmos/migration/report/run:
o	Checks RMOS_ALLOW_REPORT_RUN env; returns 403 if disabled.
o	Calls run_report and returns result.
o	Wraps exceptions in HTTPException(400, ...).
________________________________________
client/src/models/rmos_migration_report.ts
•	Types match report JSON:
o	MigrationDatasetReport with .json, .sqlite, .diff.
o	MigrationReport with generated_at, db_path, datasets, pdf_enabled, maybe message.
________________________________________
client/src/stores/useMigrationReportStore.ts (first version)
•	State:
o	report, error, loading, lastRunOk.
o	thresholds with four numeric fields.
•	fetchReport():
o	Calls GET /rmos/migration/report.
o	Updates report and lastRunOk = evaluateReport(report).
•	runReport():
o	Calls POST /rmos/migration/report/run with default data paths & db.
o	Updates report and lastRunOk.
•	evaluateReport():
o	Iterates over datasets and enforces thresholds:
	only_in_json_count <= maxOnlyInJson
	only_in_sqlite_count <= maxOnlyInSqlite
	missing_id_count <= maxMissingIds
	duplicate_id_count <= maxDuplicateIds.
________________________________________
client/src/components/rmos/MigrationDashboardView.vue
•	On mount, calls store.fetchReport().
•	Shows:
o	PASS/FAIL banner based on store.lastRunOk.
o	Threshold controls (4 numeric inputs).
o	One card per dataset:
	JSON vs SQLite counts.
	Diff counts.
	Collapsible lane counts.
	Missing / duplicate IDs listing.
	Diff ID samples listing.
•	Shows errors in a visible alert.
________________________________________
client/src/views/RmosMigrationDashboardView.vue
•	Thin wrapper that just renders <MigrationDashboardView />.
•	Router has /rmos/migration-dashboard mapped to this view.
________________________________________
🔹 N8.7.5 — Fix Drift Wizard
server/app/core/migration_fix.py
•	run_migrator():
o	Calls app.tools.rmos_migrate_json_to_sqlite with provided JSON + DB.
o	On success, calls run_report() (N8.7.4) with same paths.
o	Returns { action: "run_migrator", success: True, report: … }.
•	export_sqlite_snapshot():
o	Reads from DB (using connect_db + init_db).
o	Dumps:
	patterns rows → patterns.json
	joblog rows → joblog.json
	strip_families rows → strip_families.json
o	Then regenerates report using these new JSONs.
o	Returns { action: "export_snapshot", success: True, export_paths: {...}, counts: {...}, report: ... }.
•	build_drift_diff_package():
o	Reads latest report JSON, builds per-dataset diff summary:
	only_in_json_count, only_in_sqlite_count, only_in_json_ids, only_in_sqlite_ids.
________________________________________
server/app/api/routes/migration_fix_api.py
•	_guard():
o	Honors RMOS_ALLOW_FIX_ACTIONS; returns 403 if disabled.
•	POST /rmos/migration/fix/run-migrator:
o	Calls _guard().
o	Delegates to run_migrator(); returns JSON.
o	Wraps errors in HTTPException(400, ...).
•	POST /rmos/migration/fix/export-sqlite-snapshot:
o	export_dir, db_path, out_base parameters.
o	Same pattern as above.
•	GET /rmos/migration/fix/diff-download:
o	Returns build_drift_diff_package() as JSONResponse.
________________________________________
client/src/stores/useMigrationReportStore.ts (patched)
•	New actions:
o	runMigratorFix() → POST to /rmos/migration/fix/run-migrator, updates report + lastRunOk.
o	exportSqliteSnapshotFix() → POST to /rmos/migration/fix/export-sqlite-snapshot, updates report + lastRunOk.
o	driftDiffDownloadUrl() → returns /rmos/migration/fix/diff-download.
________________________________________
client/src/components/rmos/MigrationFixWizard.vue
•	On mount, calls store.fetchReport().
•	Shows:
o	PASS/FAIL banner (latest).
o	Three action cards:
	Re-run migrator.
	Export SQLite snapshot.
	Download drift diff.
o	Displays “Last action result” as pretty-printed JSON.
o	Displays a table of drift metrics from current report.
•	Uses store’s new fix actions.
________________________________________
client/src/views/RmosMigrationFixWizardView.vue + router
•	Thin wrapper with <MigrationFixWizard />.
•	Router entry /rmos/migration-fix pointing to this view.
________________________________________
🔹 N9.0 — Risk Analytics & Promotion Lanes
server/app/schemas/rmos_analytics.py
•	Pydantic models:
o	RiskGrade and Lane (Literal types).
o	LaneRiskSummary, GlobalRiskSummary.
o	RecentRunItem.
o	RiskTimelinePoint, RiskTimelineResponse.
o	LaneTransition, LaneAnalyticsResponse.
•	Types line up with actual data from rmos_analytics core.
________________________________________
server/app/core/rmos_analytics.py
•	Grade normalization and scoring:
o	_normalize_grade() → "GREEN", "YELLOW", "RED", "unknown".
o	_risk_score() with mapping: GREEN=0.0, YELLOW=0.5, RED=1.0, unknown=0.75.
•	Lane normalization:
o	_normalize_lane() maps unknown lanes to "unknown".
o	LANES list includes safe, tuned_v1, tuned_v2, experimental, archived, unknown.
•	Entry lane resolution:
o	_lane_for_entry() prioritizes entry.promotion_lane → entry.lane → pattern’s promotion_lane/lane → "unknown".
•	compute_lane_analytics():
o	Fetches patterns & joblog via get_pattern_store() and get_joblog_store().
o	Accumulates:
	global grade counts.
	lane job counts + grade counts + score sums.
	recent_runs limited to ~200 entries.
	lane transitions for job_type in ("preset_promote_winner", "preset_rollback") using (old_lane or parent_lane) → (promotion_lane or current lane).
o	Computes:
	global average risk.
	per-lane average risk.
o	Returns LaneAnalyticsResponse with global_summary, recent_runs, lane_transitions.
•	compute_risk_timeline_for_preset(preset_id):
o	Filters joblog by preset_id.
o	Builds RiskTimelinePoint entries and sorts by created_at.
________________________________________
server/app/api/routes/rmos_analytics_api.py
•	GET /rmos/analytics/risk?limit=:
o	limit constrained to e.g. 1..50000.
o	Returns LaneAnalyticsResponse.
•	GET /rmos/analytics/timeline/{preset_id}?limit=:
o	limit constrained to e.g. 1..20000.
o	Returns RiskTimelineResponse.
o	Wraps errors in HTTPException(400, ...).
•	Router is mounted under /rmos.
________________________________________
client/src/models/rmos_analytics.ts
•	Types mirror backend schema (LaneAnalyticsResponse, RiskTimelineResponse, etc.).
•	RiskGrade / Lane union types consistent with backend.
________________________________________
client/src/stores/useRmosAnalyticsStore.ts
•	State: riskAnalytics, timeline, loading, error.
•	fetchRiskAnalytics(limit) → GET /rmos/analytics/risk.
•	fetchTimeline(presetId, limit) → GET /rmos/analytics/timeline/{presetId}.
•	Getter globalSummary returns riskAnalytics.global_summary or null.
________________________________________
client/src/components/rmos/RmosAnalyticsDashboard.vue
•	On mount, calls store.fetchRiskAnalytics().
•	Header with:
o	text input for timelinePresetId.
o	Refresh button.
o	Load timeline button.
•	Global summary section:
o	total jobs, total presets, overall avg risk (formatted).
o	global grade counts (GREEN/YELLOW/RED/unknown).
•	Lane table:
o	lane name, job count, avg score, per-lane grade counts.
•	Lane transitions table:
o	from_lane, to_lane, count.
•	Recent runs table:
o	created_at, job_type, preset_id, lane, risk/doc/gantry grades.
•	Timeline section:
o	displays selected preset id.
o	Table of timeline points (created_at, lane, risk, score, job_id).
o	Handles “no points” gracefully.
________________________________________
client/src/views/RmosAnalyticsView.vue + router
•	Thin wrapper using <RmosAnalyticsDashboard />.
•	Router entry /rmos/analytics mapped to this view.

