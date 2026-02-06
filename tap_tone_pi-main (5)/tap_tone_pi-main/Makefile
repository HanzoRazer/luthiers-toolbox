# tap_tone_pi — Measurement Chain Makefile
# =========================================
# Usage: make <target> VAR=value ...

# ---- Dev Environment ----

.PHONY: install-dev
install-dev:
	@python -m pip install --upgrade pip
	@pip install -r requirements-dev.txt
	@pre-commit install
	@echo "✅ Dev env ready. Pre-commit hooks installed."

.PHONY: schema-guard
schema-guard:
	@python scripts/ci_guard_schema_bump.py

.PHONY: run-tests
run-tests:
	@pytest -q

.PHONY: precommit
precommit:
	@pre-commit run --all-files --show-diff-on-failure

.PHONY: format
format:
	@ruff check --fix .
	@black .

.PHONY: run-id-demo
run-id-demo:
	@python -c "from modes._shared.run_id import new_run_dir; print(new_run_dir('out'))"

# ---- Build & Distribution ----

.PHONY: build dist clean-dist lint typecheck

build:
	python -m build

dist: clean-dist build
	@echo "Wheel + sdist ready in dist/"

clean-dist:
	rm -rf dist/ build/ *.egg-info

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy tap_tone modes scripts --config-file mypy.ini

# ---- Acquisition: serial sensor capture ----

loadcell:
	@python modes/acquisition/loadcell_serial.py \
	  --config $(CFG) \
	  --out $(OUT)

dial:
	@python modes/acquisition/dial_indicator_serial.py \
	  --port $(PORT) --baud $(BAUD) --unit $(UNIT) \
	  --pattern "$(PATTERN)" --scale $(SCALE) \
	  --duration $(DUR) --rate $(RATE) \
	  --out $(OUT)

# ---- Bending Rig: measurement chain ----

bend-merge-moe:
	@python modes/bending_rig/merge_and_moe.py \
	  --load $(LOAD) --disp $(DISP) \
	  --out-dir $(OUTDIR) --rate $(RATE) \
	  --method $(METHOD) --span $(SPAN) --width $(WIDTH) --thickness $(THICKNESS) $(INNER) \
	  --fit-pct-low $(FLO) --fit-pct-high $(FHI)

plot-fvd:
	@python modes/bending_rig/plot_f_vs_d.py \
	  --pairs-csv $(PAIRS) --out $(OUT) \
	  --pct-low $(FLO) --pct-high $(FHI) --title "$(TITLE)" --dpi $(DPI)

manifest:
	@python modes/_shared/emit_manifest.py --out $(OUT) $(ARTIFACTS) $(RIG) $(NOTES)

# ---- Defaults (override on CLI) ----

# Acquisition defaults
CFG ?= config/devices/loadcell_example.json
PORT ?= COM3
BAUD ?= 9600
UNIT ?= mm
PATTERN ?= (-?[0-9]+\.?[0-9]*)
SCALE ?= 1.0
DUR ?= 10

# Bending rig defaults
RATE ?= 50
METHOD ?= 3point
SPAN ?= 400
WIDTH ?= 20
THICKNESS ?= 3.0
INNER ?=
FLO ?= 10
FHI ?= 90
DPI ?= 150
TITLE ?= Force vs Displacement

# ---- Phase 2: ODS / Grid Measurement Chain ----

# Gold-Run: one-command automated measurement (dry-run by default in Makefile)
gold-run:
	@python -m tap_tone.cli.gold_run \
	  --specimen-id $(SPECIMEN) \
	  --device $(DEVICE) \
	  --out-dir $(GOLD_OUT) \
	  --points $(GOLD_POINTS) \
	  $(if $(GOLD_SESSION),--session-id $(GOLD_SESSION),) \
	  $(if $(GOLD_BATCH),--batch-label $(GOLD_BATCH),) \
	  $(if $(GOLD_DRY),--dry-run,) \
	  $(if $(GOLD_JSON),--json,) \
	  $(if $(GOLD_INGEST),--ingest,)

# Gold-Run: dry-run (safe preview)
gold-run-dry:
	@python -m tap_tone.cli.gold_run \
	  --specimen-id $(SPECIMEN) \
	  --device $(DEVICE) \
	  --out-dir $(GOLD_OUT) \
	  --points $(GOLD_POINTS) \
	  --dry-run

# Gold-Run defaults
SPECIMEN     ?= test_plate
GOLD_OUT     ?= ./exports
GOLD_POINTS  ?= 3
GOLD_SESSION ?=
GOLD_BATCH   ?=
GOLD_DRY     ?=
GOLD_JSON    ?=
GOLD_INGEST  ?=

grid-capture:
	@python scripts/roving_grid_capture.py capture \
	  --device $(DEVICE) --grid $(GRID) --out $(OUT) \
	  --seconds $(SEC) --sample-rate $(SR)

ods-compute:
	@python scripts/ods_compute.py \
	  --capture-dir $(CAPDIR) \
	  --frequencies $(FREQS) \
	  --out $(CAPDIR)/derived/ods

grid-coherence:
	@python scripts/grid_coherence.py \
	  --capture-dir $(CAPDIR) \
	  --frequencies $(FREQS) \
	  --out $(CAPDIR)/derived/coherence

wolf-metrics:
	@python scripts/wolf_metrics.py \
	  --ods-dir $(CAPDIR)/derived/ods \
	  --coherence-dir $(CAPDIR)/derived/coherence \
	  --frequencies $(FREQS) \
	  --wsi-threshold $(WSI_THRESH) \
	  --out $(CAPDIR)/derived/wolf

# Full Phase 2 pipeline: capture → ODS → coherence → wolf
phase2-full: grid-capture ods-compute grid-coherence wolf-metrics
	@echo "Phase 2 pipeline complete: $(CAPDIR)"

# Phase 2 analysis only (assumes captures exist)
phase2-analyze: ods-compute grid-coherence wolf-metrics
	@echo "Phase 2 analysis complete: $(CAPDIR)"

# ---- Phase 2 Defaults ----

DEVICE ?= 1
GRID ?= config/grids/guitar_top_35pt.json
SEC ?= 2.0
SR ?= 48000
FREQS ?= 100,150,185,220,280,350
WSI_THRESH ?= 0.6

# ---- Simulators (hardware-free) ----

# Simulated load cell (deterministic with SEED)
sim-load:
	@python modes/acquisition/loadcell_sim.py \
	  --out $(OUT) --unit $(SIM_UNIT_F) --rate $(SIM_RATE_F) --duration $(SIM_DUR) \
	  --amp $(SIM_AMP_F) --baseline $(SIM_BASE_F) --noise $(SIM_NOISE_F) \
	  --freq $(SIM_FREQ) --drift $(SIM_DRIFT) \
	  $(if $(SEED),--seed $(SEED),)

# Simulated dial indicator (deterministic with SEED)
sim-dial:
	@python modes/acquisition/dial_indicator_sim.py \
	  --out $(OUT) --unit $(SIM_UNIT_D) --rate $(SIM_RATE_D) --duration $(SIM_DUR) \
	  --amp $(SIM_AMP_D) --baseline $(SIM_BASE_D) --noise $(SIM_NOISE_D) \
	  --freq $(SIM_FREQ) --drift $(SIM_DRIFT) \
	  $(if $(SEED),--seed $(SEED),)

# Simulator defaults
SIM_UNIT_F ?= N
SIM_UNIT_D ?= mm
SIM_RATE_F ?= 50
SIM_RATE_D ?= 20
SIM_DUR    ?= 10
SIM_AMP_F  ?= 10.0
SIM_AMP_D  ?= 0.5
SIM_BASE_F ?= 0.0
SIM_BASE_D ?= 0.0
SIM_NOISE_F?= 0.1
SIM_NOISE_D?= 0.005
SIM_FREQ   ?= 0.25
SIM_DRIFT  ?= 0.02
SEED       ?=

# ---- Chladni v1 (facts only) ----

chladni-peaks:
	@python modes/chladni/peaks_from_wav.py \
	  --wav $(WAV) --out $(OUT) \
	  --min-hz $(MINH) --max-hz $(MAXH) --prominence $(PROM)

chladni-index:
	@python modes/chladni/index_patterns.py \
	  --peaks-json $(PEAKS) \
	  --images $(IMGS) \
	  --plate-id "$(PLATE)" \
	  $(if $(TEMP),--tempC $(TEMP),) \
	  $(if $(RH),--rh $(RH),) \
	  --out $(OUT)

# Chladni defaults
MINH  ?= 50
MAXH  ?= 2000
PROM  ?= 0.02
PEAKS ?=
IMGS  ?=
PLATE ?= UNKNOWN
TEMP  ?=
RH    ?=

# ---- Validation & CI ----

# Validate output artifacts against contract schemas
validate-schemas:
	@python scripts/validate_schemas.py --out-root $(OUT_ROOT) --schemas-root $(SCHEMAS_ROOT)

# Validate viewer pack ZIP integrity (post-export)
validate-pack:
	@python scripts/viewer_pack_validate.py $(PACK)

# Validate staged pack directory (pre-export)
validate-staged-pack:
	@python -m tap_tone.validate.viewer_pack_v1 $(STAGED_PACK) $(if $(REPORT),--report $(REPORT),) $(if $(AUDIO_REQUIRED),--audio-required,)

# Compare two viewer packs (measurement regression)
diff-packs:
	@python scripts/viewer_pack_diff.py $(BASELINE) $(MODIFIED) --out $(DIFF_OUT) $(if $(PLOTS),--plots,)

# Run pytest suite (CI minimum bar)
test:
	@python -m pytest tests/ -v

# Run WAV I/O tests specifically
test-wav-io:
	@python -m pytest tests/test_wav_io.py tests/test_wav_io_roundtrip.py -v

# ToolBox ingest smoke test (validates demo artifacts against registry)
.PHONY: toolbox-smoke
toolbox-smoke:
	@python scripts/toolbox_ingest_smoke.py

# ---- Hardware-free Demos ----

.PHONY: examples-chladni-demo examples-phase2-demo examples-moe-demo

# Chladni v1 demo (creates capture.wav + peaks.json + images + chladni_run.json + manifest)
examples-chladni-demo:
	@python examples/chladni/make_demo.py
	@python scripts/validate_schemas.py --out-root out --schemas-root contracts/schemas

# Phase-2 ODS demo (creates session with canonical filenames)
examples-phase2-demo:
	@python examples/phase2/make_demo.py
	@python scripts/validate_schemas.py --out-root runs_phase2 --schemas-root contracts/schemas

# Hardware-free MOE demo (creates moe_result.json and validates)
examples-moe-demo:
	@python examples/moe/make_demo.py
	@python scripts/validate_schemas.py --out-root out --schemas-root contracts/schemas

# Validation defaults
OUT_ROOT       ?= out
SCHEMAS_ROOT   ?= contracts/schemas
PACK           ?=
STAGED_PACK    ?=
REPORT         ?=
AUDIO_REQUIRED ?=
BASELINE       ?=
MODIFIED       ?=
DIFF_OUT       ?= diff_out
PLOTS          ?=

# ---- Help ----

.PHONY: help loadcell dial bend-merge-moe plot-fvd manifest
.PHONY: grid-capture ods-compute grid-coherence wolf-metrics phase2-full phase2-analyze
.PHONY: sim-load sim-dial chladni-peaks chladni-index
.PHONY: validate-schemas validate-pack diff-packs test test-wav-io

help:
	@echo "Acquisition Targets:"
	@echo "  loadcell        Capture load cell → load_series.json (requires CFG, OUT)"
	@echo "  dial            Capture dial indicator → displacement_series.json (requires PORT, OUT)"
	@echo ""
	@echo "Bending Rig Targets:"
	@echo "  bend-merge-moe  Merge load+disp streams → pairs.csv + bending_moe.json"
	@echo "  plot-fvd        Plot force vs displacement with linear fit"
	@echo "  manifest        Emit provenance manifest for run artifacts"
	@echo ""
	@echo "Phase 2 (ODS / Wolf Metrics) Targets:"
	@echo "  grid-capture    Interactive 2-channel grid capture (requires DEVICE, GRID, OUT)"
	@echo "  ods-compute     Compute ODS transfer functions (requires CAPDIR, FREQS)"
	@echo "  grid-coherence  Compute coherence across grid (requires CAPDIR)"
	@echo "  wolf-metrics    Compute Wolf Stress Index (requires CAPDIR)"
	@echo "  phase2-full     Full pipeline: capture → ODS → coherence → wolf"
	@echo "  phase2-analyze  Analysis only (ODS → coherence → wolf)"
	@echo ""
	@echo "Validation Targets (CI minimum bar):"
	@echo "  validate-schemas  Validate out/** artifacts against contracts/schemas"
	@echo "  validate-pack     Validate viewer pack ZIP integrity (requires PACK)"
	@echo "  diff-packs        Compare two viewer packs (requires BASELINE, MODIFIED)"
	@echo "  test              Run pytest suite"
	@echo "  test-wav-io       Run WAV I/O tests only"
	@echo ""
	@echo "Examples:"
	@echo "  make loadcell CFG=config/devices/loadcell_example.json OUT=out/run/load_series.json"
	@echo "  make dial PORT=/dev/ttyUSB0 OUT=out/run/displacement_series.json UNIT=mm DUR=8"
	@echo "  make bend-merge-moe LOAD=out/run/load_series.json DISP=out/run/displacement_series.json \\"
	@echo "       OUTDIR=out/run/rig METHOD=3point SPAN=400 WIDTH=20 THICKNESS=3.0"
	@echo ""
	@echo "  make grid-capture DEVICE=1 GRID=config/grids/guitar_top_35pt.json OUT=out/grid_001"
	@echo "  make phase2-analyze CAPDIR=out/grid_001 FREQS=100,150,185,220,280"
	@echo ""
	@echo "Viewer Pack Validation/Diff Examples:"
	@echo "  make validate-pack PACK=viewer_pack_session123.zip"
	@echo "  make diff-packs BASELINE=pre_intervention.zip MODIFIED=post_intervention.zip"
	@echo "  make diff-packs BASELINE=pre.zip MODIFIED=post.zip DIFF_OUT=results/ PLOTS=1"
	@echo ""
	@echo "Simulator Targets (hardware-free):"
	@echo "  sim-load        Simulated load cell → load_series.json"
	@echo "  sim-dial        Simulated dial indicator → displacement_series.json"
	@echo ""
	@echo "Chladni v1 Targets (facts only):"
	@echo "  chladni-peaks   Extract peak frequencies from sweep/stepped WAV"
	@echo "  chladni-index   Index pattern images to frequencies → chladni_run.json"
	@echo ""
	@echo "Simulator Examples:"
	@echo "  make sim-load OUT=out/DEMO/load_series.json SIM_AMP_F=12 SIM_BASE_F=0.5 SIM_NOISE_F=0.2"
	@echo "  make sim-dial OUT=out/DEMO/displacement_series.json SIM_AMP_D=0.8 SIM_BASE_D=0.1"
	@echo "  # For reproducible runs, add: SEED=1337"
	@echo ""
	@echo "Chladni Examples:"
	@echo "  make chladni-peaks WAV=out/DEMO/chladni/capture.wav OUT=out/DEMO/chladni/peaks.json"
	@echo "  make chladni-index PEAKS=out/DEMO/chladni/peaks.json \\"
	@echo "       IMGS=\"out/DEMO/chladni/F0148.png out/DEMO/chladni/F0226.png\" \\"
	@echo "       PLATE=J45_TOP_2025_12_31_A TEMP=22.0 RH=45.0 OUT=out/DEMO/chladni/chladni_run.json"
