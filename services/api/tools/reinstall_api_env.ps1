# Luthier's Tool Box API Environment Reinstaller
# Safely recreates your Python venv with pinned geometry stack
# Supports Python 3.11+ (3.13 recommended for latest fixes)

Param(
  [string]$Py = "python",            # or "py -3.11"
  [string]$EnvName = ".venv311",     # your preferred venv folder name
  [switch]$Force                     # remove existing venv first
)

$ErrorActionPreference = "Stop"

# Move to API root (script is inside services/api/tools)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiRoot   = Split-Path -Parent $scriptDir
Set-Location $apiRoot

Write-Host "==> API root: $apiRoot" -ForegroundColor Cyan

if ($Force -and (Test-Path $EnvName)) {
  Write-Host "==> Removing existing venv: $EnvName" -ForegroundColor Yellow
  Remove-Item -Recurse -Force $EnvName
}

Write-Host "==> Creating venv with: $Py -m venv $EnvName" -ForegroundColor Cyan
& $Py -m venv $EnvName

$pip    = Join-Path $EnvName "Scripts\pip.exe"
$python = Join-Path $EnvName "Scripts\python.exe"

Write-Host "==> Upgrading pip/setuptools/wheel" -ForegroundColor Cyan
& $pip install --upgrade pip setuptools wheel

# Prefer pinned lock file; fallback to requirements.txt
$lockFile = Join-Path $apiRoot "requirements.lock"
$reqFile  = Join-Path $apiRoot "requirements.txt"

if (Test-Path $lockFile) {
  Write-Host "==> Installing pinned deps from requirements.lock" -ForegroundColor Green
  & $pip install -r $lockFile
} elseif (Test-Path $reqFile) {
  Write-Host "==> Installing deps from requirements.txt" -ForegroundColor Green
  & $pip install -r $reqFile
  # Ensure geometry stack present if not pinned in requirements.txt
  Write-Host "==> Ensuring shapely + ezdxf are installed" -ForegroundColor Green
  & $pip install "shapely>=2.0.0" "ezdxf>=1.4.0"
  Write-Host "==> Note: pyclipper may fail on Python 3.13 (contour mode unavailable)" -ForegroundColor Yellow
  try {
    & $pip install "pyclipper==1.3.0.post5" 2>&1 | Out-Null
    Write-Host "    ✓ pyclipper installed successfully" -ForegroundColor Green
  } catch {
    Write-Host "    ⚠ pyclipper build failed (expected on Python 3.13)" -ForegroundColor Yellow
  }
} else {
  throw "No requirements.lock or requirements.txt found in $apiRoot"
}

Write-Host "`n==> Verifying geometry stack imports…" -ForegroundColor Cyan
$verifier = @'
import sys
ok = True
errs = []

try:
    import shapely
    from shapely import __version__ as SHAPELY_VER
except Exception as e:
    ok = False; errs.append(f"shapely import failed: {e!r}")
else:
    print(f"✓ shapely OK  : {SHAPELY_VER}")

try:
    import pyclipper
    PYCLIPPER_VER = getattr(pyclipper, "__version__", "unknown")
except Exception as e:
    errs.append(f"⚠ pyclipper import failed: {e!r} (contour mode unavailable)")
    print("⚠ pyclipper NOT available (expected on Python 3.13)")
else:
    print(f"✓ pyclipper OK: {PYCLIPPER_VER}")

try:
    import fastapi
    from fastapi import FastAPI
except Exception as e:
    ok = False; errs.append(f"fastapi import failed: {e!r}")
else:
    print(f"✓ fastapi OK  : {getattr(fastapi, '__version__', 'unknown')}")

try:
    import ezdxf
except Exception as e:
    ok = False; errs.append(f"ezdxf import failed: {e!r}")
else:
    print(f"✓ ezdxf OK    : {getattr(ezdxf, '__version__', 'unknown')}")

try:
    import numpy
except Exception as e:
    ok = False; errs.append(f"numpy import failed: {e!r}")
else:
    print(f"✓ numpy OK    : {getattr(numpy, '__version__', 'unknown')}")

if not ok:
    print("\n== VERIFICATION FAILED ==", file=sys.stderr)
    for m in errs:
        if "pyclipper" not in m:  # pyclipper is optional
            print("- " + m, file=sys.stderr)
    sys.exit(1)
print("\n== VERIFICATION PASSED ==")
print("Art Studio v13 is ready (raster mode)")
if "pyclipper" not in str(errs):
    print("Contour mode also available")
'@

# Run the verifier
$codeFile = Join-Path $env:TEMP "ltb_verify_geom_stack.py"
$verifier | Out-File -FilePath $codeFile -Encoding utf8
& $python $codeFile

$activatePath = (Resolve-Path (Join-Path $EnvName "Scripts\Activate.ps1")).Path

Write-Host "`n✅ All set! Activate with:" -ForegroundColor Green
Write-Host "  & `"$activatePath`"" -ForegroundColor White

Write-Host "`nQuick smoke test:" -ForegroundColor Cyan
Write-Host "  cd $apiRoot" -ForegroundColor White
Write-Host "  & `"$activatePath`"" -ForegroundColor White
Write-Host "  python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor White
