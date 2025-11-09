# Luthier's Tool Box API Makefile
# Cross-platform venv management for macOS/Linux
#
# Usage:
#   make api-env          Create venv and install deps
#   make api-verify       Check geometry stack imports
#   make api-reinstall    Clean reinstall (removes venv first)
#   make api-clean        Remove venv
#   make api-run          Start uvicorn dev server
#   make api-health       Health check (start server, test endpoint, shutdown)

# Adjust as needed
PY      ?= python3
VENV    ?= .venv311
PIP     := $(VENV)/bin/pip
PYTHON  := $(VENV)/bin/python

API_DIR := $(CURDIR)
PORT    ?= 8088

.PHONY: api-env api-reinstall api-verify api-clean api-run api-test api-health

api-env:
	@echo "==> Creating venv: $(VENV)"
	@$(PY) -m venv $(VENV)
	@$(PIP) install --upgrade pip setuptools wheel
	@if [ -f requirements.lock ]; then \
	  echo "==> Installing pinned deps from requirements.lock"; \
	  $(PIP) install -r requirements.lock; \
	elif [ -f requirements.txt ]; then \
	  echo "==> Installing deps from requirements.txt"; \
	  $(PIP) install -r requirements.txt; \
	  echo "==> Ensuring shapely + ezdxf present"; \
	  $(PIP) install "shapely>=2.0.0" "ezdxf>=1.4.0"; \
	  echo "==> Attempting pyclipper install (may fail on Python 3.13)"; \
	  $(PIP) install "pyclipper==1.3.0.post5" || echo "⚠ pyclipper build failed (contour mode unavailable)"; \
	else \
	  echo "ERROR: No requirements.lock or requirements.txt in $(API_DIR)"; \
	  exit 1; \
	fi
	@echo ""
	@echo "✅ Venv created. Activate with:"
	@echo "   source $(VENV)/bin/activate"

api-verify:
	@echo "==> Verifying geometry stack imports…"
	@$(PYTHON) - <<'PY'
import sys
ok=True; errs=[]
try:
    import shapely
    from shapely import __version__ as SHAPELY_VER
except Exception as e:
    ok=False; errs.append(f"shapely import failed: {e!r}")
else:
    print(f"✓ shapely OK  : {SHAPELY_VER}")
try:
    import pyclipper
    PYCLIPPER_VER=getattr(pyclipper,"__version__","unknown")
except Exception as e:
    errs.append(f"⚠ pyclipper import failed: {e!r} (contour mode unavailable)")
    print("⚠ pyclipper NOT available")
else:
    print(f"✓ pyclipper OK: {PYCLIPPER_VER}")
try:
    import fastapi
    from fastapi import FastAPI
except Exception as e:
    ok=False; errs.append(f"fastapi import failed: {e!r}")
else:
    print(f"✓ fastapi OK  : {getattr(fastapi,'__version__','unknown')}")
try:
    import ezdxf
except Exception as e:
    ok=False; errs.append(f"ezdxf import failed: {e!r}")
else:
    print(f"✓ ezdxf OK    : {getattr(ezdxf,'__version__','unknown')}")
try:
    import numpy
except Exception as e:
    ok=False; errs.append(f"numpy import failed: {e!r}")
else:
    print(f"✓ numpy OK    : {getattr(numpy,'__version__','unknown')}")
if not ok:
    print("\n== VERIFICATION FAILED ==", file=sys.stderr)
    for m in errs:
        if "pyclipper" not in m:
            print("-", m, file=sys.stderr)
    sys.exit(1)
print("\n== VERIFICATION PASSED ==")
print("Art Studio v13 is ready (raster mode)")
PY

api-reinstall: api-clean api-env api-verify
	@echo ""
	@echo "✅ API environment reinstalled successfully"

api-clean:
	@echo "==> Removing venv: $(VENV)"
	@rm -rf $(VENV)

api-run:
	@echo "==> Starting uvicorn dev server on http://127.0.0.1:8000"
	@$(PYTHON) -m uvicorn app.main:app --reload --port 8000

api-test:
	@echo "==> Running API smoke tests"
	@$(PYTHON) -c "from app.routers.cam_vcarve_router import router; print('✓ cam_vcarve_router imports OK')"
	@$(PYTHON) -c "from app.main import app; print('✓ FastAPI app imports OK')"
	@echo ""
	@echo "✅ Smoke tests passed"
	@echo ""
	@echo "Full test: Start server with 'make api-run' and curl:"
	@echo '  curl -X POST http://127.0.0.1:8000/api/cam_vcarve/preview_infill \\'
	@echo '    -H "Content-Type: application/json" \\'
	@echo '    -d "{\"mode\":\"raster\",\"flat_stepover_mm\":1.0}"'

api-health:
	@echo "==> Launching FastAPI server on port $(PORT) for health check"
	@($(PYTHON) -m uvicorn app.main:app --port $(PORT) --log-level warning & \
		SERVER_PID=$$!; \
		sleep 3; \
		echo "==> Curling /api/cam_vcarve/preview_infill"; \
		curl -s -X POST "http://127.0.0.1:$(PORT)/api/cam_vcarve/preview_infill" \
		     -H "Content-Type: application/json" \
		     -d '{"mode":"raster","approx_stroke_width_mm":1.2,"raster_angle_deg":45,"flat_stepover_mm":1.0}' \
		     | head -c 500; \
		echo ""; \
		echo "==> Health check completed."; \
		pkill -f "uvicorn app.main:app" >/dev/null 2>&1 || true)

help:
	@echo "Luthier's Tool Box API Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  api-env          Create venv and install dependencies"
	@echo "  api-verify       Verify geometry stack imports"
	@echo "  api-reinstall    Clean reinstall (removes venv first)"
	@echo "  api-clean        Remove venv"
	@echo "  api-run          Start uvicorn dev server"
	@echo "  api-test         Run smoke tests"
	@echo "  api-health       Health check (start server, test endpoint, shutdown)"
	@echo ""
	@echo "Variables:"
	@echo "  PY=$(PY)          Python interpreter"
	@echo "  VENV=$(VENV)      Virtual environment directory"
	@echo "  PORT=$(PORT)      Port for health check (default: 8088)"
