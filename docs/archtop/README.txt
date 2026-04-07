Luthier Archtop Contour Kit (FULL)
==================================
Requires: python -m pip install numpy ezdxf shapely matplotlib

A) From measured points (CSV):
   python archtop_contour_generator.py csv --in sample_top_points.csv --levels 0,1,2,3 --out-prefix top_test

B) From outline (Mottola-style):
   python archtop_contour_generator.py outline --in sample_outline_oval.dxf --origin 0,0 --scales 0.90,0.78,0.66,0.54,0.37 --out-prefix oval_test

Import the resulting DXF rings into Fusion to pocket/contour by ring.
