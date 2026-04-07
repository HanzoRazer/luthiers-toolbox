@echo off
setlocal
python archtop_contour_generator.py outline --in sample_outline_oval.dxf --origin 0,0 --scales 0.90,0.78,0.66,0.54,0.37 --out-prefix oval_test
echo.
echo Output files: oval_test_ScaledRings.dxf/svg/png
pause
