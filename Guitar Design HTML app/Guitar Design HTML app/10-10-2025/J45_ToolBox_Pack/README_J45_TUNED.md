# J-45 — Shop Safety & Automation Pack

Included
- `fusion/SafePost_J45_INSERTS.cps` — Fusion post guards (G21/G90/G54), tags: `COMPONENT`, `MATERIAL`, `STOCK_THICKNESS_MM`, `POLICY_STEPDOWN_CAP_MM`, `EXPECTED_TOOL`, `STEPDOWN_MM`.
- `preflight_plus/nc_lint_autovars.py` — Preflight that writes HTML + optional JSON and `.vars` (#5000–#5002).
- `preflight_plus/*.yaml` — Policies per J-45 component (conservative defaults — edit to match your billets/ops).
- `mach4/m200.mcs`, `mach4/m201.mcs`, `mach4/m205.mcs` — SafeStart, advisory, and auto-vars loader.

Quick Start
1) Paste the Fusion inserts into your active `.cps` (in `onOpen/onSection/onClose`). Set `COMPONENT`, `MATERIAL`, and `STOCK_THICKNESS_MM` per job.
2) Post your NC and run preflight:
   ```bash
   python preflight_plus/nc_lint_autovars.py PATH/your.nc      -c preflight_plus/J45_top_spruce.yaml      --emit-json job_summary.json      --emit-vars job_vars.vars      --fail-on-policy
   ```
3) Copy `job_vars.vars` into your Mach4 profile’s `Macros` folder (or edit `VARS_PATH` in `m205.mcs`), run `M205`, then run `M200` before cycle start.
4) Use `M201` for quick operator reminders (per component).

Notes
- The stepdown caps here are intentionally conservative for safety; tune them to your cutters, fixturing, and wood.
- All YAMLs assume **metric** and **G54**; edit if your shop standard differs.
