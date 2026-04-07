@echo off
setlocal
python archtop_contour_generator.py csv --in sample_top_points.csv --levels 0,1,2,3 --out-prefix top_test
echo.
echo Output files: top_test_Contours.dxf/svg/png
pause
