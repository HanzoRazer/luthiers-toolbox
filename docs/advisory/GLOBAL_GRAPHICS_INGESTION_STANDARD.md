📄 GLOBAL_GRAPHICS_INGESTION_STANDARD.md
ToolBox-Wide Graphics, Blueprint, Vector & CAD Import Requirements
Version: 1.1
Last Updated: November 26, 2025
________________________________________
🎸 Luthier’s ToolBox — Global Graphics Ingestion Standard (GGIS v1.1)
This Standard applies to every module in the ToolBox ecosystem, including:
•	Art Studio (Rosette, Inlay, Headstock)
•	Adaptive Lab (DXF-based)
•	Relief Lab (heightmaps & raster reliefs)
•	Blueprint Analyzer (image → DXF path)
•	Unified CAM Pipeline
•	Toolpath Generator
•	G-code Export System
It ensures:
•	CNC manufacturability
•	Predictable toolpaths
•	Clean geometry
•	Reliable CAM operations
•	Preventing bad vendor files
•	Protecting bits, spindles, and material
If an imported file fails this standard, ToolBox will decline the file and recommend correction or the paid Cleanup Service.
________________________________________
📚 Table of Contents
1.	Raster File Requirements
2.	PDF Requirements
3.	Vector File Requirements (DXF, SVG)
4.	Geometry Requirements (All Labs)
5.	Unit & Scaling Requirements
6.	Manufacturability Requirements
7.	Integrity Requirements
8.	ToolBox Rejection Policy
9.	Corrective Options
10.	Appendix A: Illustrator Export Settings
11.	Appendix B: Inkscape Export Settings
________________________________________
I. Raster File Requirements
Raster formats include: PNG, JPG/JPEG, BMP, TIFF
✔ 1. Minimum Resolution: 300 DPI
•	Mandatory for all raster imports.
•	Ensures ToolBox can detect edges, trace vectors, and determine scale.
✔ 2. Recommended Resolution: 600–1200 DPI
High precision required for:
•	Rosette petals
•	Headstock inlays
•	Fretboard engravings
•	Blueprint extraction
•	Relief carving
❌ 3. Not Accepted
•	Screenshots
•	72 DPI web images
•	Low-resolution photos
•	JPEGs with compression artifacts
•	Pixelated scans
✔ 4. Raster PDFs count as raster input
PDFs containing embedded images must follow the same 300 DPI rule.
________________________________________
II. PDF Requirements
PDFs are accepted only under strict conditions.
✔ 1. Preferred: Vector PDF
Allowed if:
•	Contains pure paths/shapes
•	No clipping masks
•	No transparency
•	No filters/blends/effects
•	No live text (must be outlined)
•	No embedded raster images
•	Coordinates reflect real-world scale
✔ 2. Raster PDFs
Must:
•	Include a 300 DPI minimum image
•	Use lossless compression (no heavy JPEG artifacting)
•	Have a clean background
❌ 3. Not Accepted PDFs
•	Illustrator files with active filters or envelope distortions
•	PDFs with invisible layers
•	PDFs containing 72 DPI art inside
•	PDFs relying on blend modes or masks
________________________________________
III. Vector File Requirements (DXF, SVG)
✔ A. DXF Requirements
•	DXF R12 Polyline ONLY
•	Must contain closed polylines
•	Splines discouraged → must be flattened or will be converted
•	No 3D polyface meshes
•	No exploded solids
•	No text
•	No anonymous blocks
•	No enumerated hatch fills
✔ B. SVG Requirements
•	SVG 1.1 (Plain)
•	All strokes must be expanded (converted to outlines)
•	No filters
•	No masks
•	No clipping paths
•	No transforms requiring matrix decomposition
•	No embedded rasters
✔ C. Illustrator → SVG Requirements
Use:
Illustrator → Export As → SVG  
Type: SVG 1.1  
CSS Properties: Presentation Attributes  
Decimal Places: 3  
Image Location: Embed  
Advanced Options → Outline Strokes  
❌ D. Prohibited Vector Formats
•	EPS
•	Generic AI files
•	DOCX vector shapes
•	PDF with blend/object effects
•	Figma SVG masked exports
•	CorelDRAW proprietary formats
________________________________________
IV. Geometry Requirements (All Labs)
Applies universally across:
•	Rosette Designer
•	Adaptive Kernel (DXF)
•	Relief Lab
•	PipelineLab
✔ 1. All paths must be closed
No gaps, breaks, or dangling endpoints.
✔ 2. No self-intersections
Self-crossing polygons cause:
•	toolpath explosions
•	invalid offsets
•	Fusion360 crashes
✔ 3. No duplicate or overlapping segments
Toolpaths double-cut and burn material.
✔ 4. No zero-length or degenerate shapes
Microscopic segments are automatically rejected.
✔ 5. Smooth curvature
•	No “spike” artifacts
•	No 1-degree wiggles
•	Nerfed bezier handles produce stable offsets
✔ 6. No raster disguised as vector
Vector paths must contain actual command-based shapes, not embedded PNGs.
________________________________________
V. Unit & Scaling Requirements
✔ 1. File must be 1:1 scale
•	Inches or millimeters allowed
•	No 10× scaling errors
•	No arbitrary resizing
✔ 2. Scale must be declared or inferable
If ToolBox cannot determine scale → rejected
✔ 3. No fractional pixel units
e.g., path width of 0.421337 px = invalid
Must be real-world metric or imperial.
________________________________________
VI. Manufacturability Requirements
✔ 1. Minimum manufacturable size
Minimum feature width =
Tool radius × 1.2 (safety factor)
Example:
•	Tool diameter: 1.0 mm
•	Min manufacturable width: 1.2 mm
✔ 2. Minimum wall thickness
Wall thickness =
Tool diameter × 1.3
Thin walls → flagged red in Art Studio overlays.
✔ 3. Relatable Reachability Check
ToolBox will check:
•	Tool can physically enter the cavity
•	No inlay pockets narrower than tool diameter
•	No relief areas unreachable by ball-end mill
✔ 4. Overhang & Undercut Detection
Files requiring undercuts (not allowed in 3-axis CNC) trigger errors.
________________________________________
VII. Integrity Requirements
✔ 1. File must load without errors
Reject:
•	corrupt DXF
•	partial PDF exports
•	Illustrator “missing glyph” issues
•	invalid SVG transforms
•	missing font outlines
✔ 2. Must contain a primary boundary
Art with no clear boundaries fails.
✔ 3. Must not depend on external assets
No linking:
•	external images
•	cloud fonts
•	external CSS
•	external SVG references
________________________________________
VIII. ToolBox Rejection Policy
If an imported file fails GGIS v1.1:
🔒 ToolBox will NOT generate toolpaths
🔒 ToolBox will NOT allow Pipeline execution
🔒 ToolBox will NOT attempt simulations
🔒 ToolBox will flag and list all errors visually
This protects your machine, time, and materials.
________________________________________
IX. Corrective Options
When a file fails, ToolBox offers:
✔ Option 1 — Auto-Fix (basic)
•	Close small gaps
•	Remove duplicates
•	Heal shapes
•	Convert minor strokes → outlines
•	Clean degenerate points
✔ Option 2 — Auto-Fix (advanced, paid)
•	Rebuild geometry
•	Retopologize curves
•	Remove noise
•	Conform to CNC offset rules
•	Recreate manufacturable features
•	Replace bad curves entirely
✔ Option 3 — User Fix Using GGIS
Users follow ToolBox guidelines for Illustrator/Inkscape repair.
✔ Option 4 — Studio Services
ToolBox produces clean geometry from concept or sketch.
________________________________________
Appendix A — Illustrator Export Settings
Required checklist:
✓ Flatten Transparency  
✓ Outline Strokes  
✓ Expand Appearance  
✓ SVG 1.1  
✓ No raster effects  
✓ All text outlined  
✓ Set artboard to 1:1 scale  
✓ No live brushes  
✓ No masks  
✓ No embedded images  
________________________________________
Appendix B — Inkscape Export Settings
Required:
File → Save As → Plain SVG  
Path → Stroke to Path  
Path → Combine  
Path → Simplify (lightly)  
Extensions → Clean → Remove Duplicates  
Extensions → Clean → Remove Overlaps  

