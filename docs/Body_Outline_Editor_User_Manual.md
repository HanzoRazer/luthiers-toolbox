# Body Outline Editor User Manual
## v3.0.0 — Internal Use Only

Chapter 1: Interface Orientation
What the Body Outline Editor does
The Body Outline Editor is a browser-based CAD tool for drawing and editing guitar body outlines. You work in millimeters, with a coordinate origin at the body center and the Y-axis pointing toward the neck. The tool produces three outputs: DXF files for CAM and Fusion 360, JSON files for the instrument body generator API, and SVG files for documentation or web display.
The tool is designed for the workflow of tracing a reference photograph, refining the traced outline with Bezier curves, and exporting geometry that matches a real instrument to millimeter precision. For the Smart Guitar specifically, this means starting from a concept render or photograph, calibrating scale against a known dimension, and producing a body outline that feeds directly into the parametric CAD and CAM pipeline.
Opening the editor
The editor runs entirely in the browser. No installation is required. Open the URL in any modern browser — Chrome, Edge, or Firefox. When the page loads, you see four regions: the toolbar at the top, the canvas in the center, the right-side panel, and the status bar at the bottom. A default dreadnought-like outline appears on the canvas so you have something to work with immediately.
The toolbar
The toolbar runs across the top of the window in nine grouped sections, separated by vertical divider lines.
File and history group. The leftmost group has New, Undo, and Redo. New clears the canvas and resets to the default outline; if you have unsaved changes, it asks for confirmation first. Undo and Redo work on a fifty-step history, and a gesture counts as one step — a full node drag is one undo, not one undo per pixel of movement.
Grid and display group. Grid toggles the coordinate grid on and off. The Snap dropdown sets the grid increment to 1, 5, or 10 millimeters; nodes snap to these intervals when you drag them. Handles toggles visibility of Bezier control handles for every node at once; by default, handles show only for the node you have selected.
Mode group. Mirror toggles symmetric editing mode, which you will use for virtually all body outline work since guitar bodies are symmetric. Outer and + Void switch between editing the main body outline and editing a void (cavity, pickup opening, soundhole).
Path editing group. Simplify reduces the number of nodes in the active path while approximating the original curve; the tolerance field next to it controls how aggressive the reduction is. Smooth All converts every node in the active path to a smooth curve at once, useful after loading a template or cleaning up an imported shape.
Measurement group. Measure lets you click two points on the canvas and see the distance between them in millimeters.
Image and calibration group. Import Image loads a JPEG or PNG as a reference photograph, Calibrate sets the real-world scale of that image, and Clear Image removes it.
Template group. The Template dropdown lists eight built-in body shapes (Dreadnought, Jumbo, OM/000, Classical, Parlor, Stratocaster, Les Paul, Telecaster). Load Template replaces the current outline with the selected template's geometry.
Instrument and Solve group. The Instrument dropdown selects the instrument spec for the backend solver (Dreadnought, Cuatro Venezolano, Stratocaster, Jumbo). Solve Outline sends the current outline's landmarks to the backend and receives a parametrically-derived outline in return. A confidence badge next to the button shows the solver's confidence in the result (green ≥70%, amber 40-69%, orange <40%).
Export group. Export DXF, Export JSON, and Export SVG each download a file in the corresponding format.
Auth group (hidden by default). Login and Logout buttons for paid-tier API access. A user badge shows "✓ Paid Tier" when authenticated. This group appears only when the backend returns a 401 or when an API key is already stored.
The canvas
The canvas fills the center of the window and is where all geometry work happens. A dark grid shows the coordinate system. The origin — the point where X equals zero and Y equals zero — sits at the center of the workspace, and you should think of this as the center of the guitar body. The Y-axis points upward on screen and corresponds to the direction from tail to neck on the instrument; positive Y values are toward the neck, negative Y values are toward the tail. The X-axis runs left-right; positive X is toward the bass side of the body (if you hold the guitar the normal way), negative X is toward the treble side.
Legend. A small legend strip below the canvas lists the four most important modifier-key gestures: Alt+click on a node toggles sharp or smooth, Alt+drag on a handle makes it asymmetric, Delete removes a node, and Space+drag pans the view. Arrow keys for nudging are supported but not shown in the legend.
Three readouts show coordinate and dimension information, and they answer different questions. It's worth distinguishing them up front because they're easy to confuse.

Bounding box readout. In the upper-right corner of the canvas, a small text block displays the width and height of the whole outline, in millimeters. It updates whenever a node is added, moved, or deleted. This is your sanity check on overall size — for the Smart Guitar, you're aiming for W: 368.3 × H: 444.5. The number here does not change as you move the mouse; it only changes when the outline itself changes.

Cursor readout (in the status bar at the bottom). The X, Y coordinates of your mouse pointer in millimeters, updating continuously as you move. This answers "where am I about to click," not "what is the size of the outline." Use it when placing new nodes at approximate positions.

Selected node readout (Nodes panel on the right, and the Selected field in the status bar). Shows the exact X, Y coordinates of whichever node you currently have selected. Use this to verify where a specific node landed after placement or to identify a node you want to edit numerically.

Quick rule of thumb: bounding box answers "how big is the outline?" Cursor answers "where is my mouse?" Selected answers "where is this specific node?"

Distance readout. When you use the Measure tool, a separate readout appears showing the measured distance between two clicked points.
The right panel
The right side of the window holds a set of stacked panels that give you structural information about what you're editing.
Nodes panel. Lists every node in the currently active path, with its X and Y coordinates in millimeters. The count appears next to the heading. Clicking a row in this list selects that node on the canvas — useful when a node is hidden under another or when you want to edit a specific numbered point.
Reference Image panel. This panel appears only after you import an image. It contains an opacity slider that ranges from 20 to 80 percent, letting you fade the photograph so your geometry is easier to see against it.
Voids panel. Lists every void you have added to the outline, showing the role (pickup, control cavity, switch, jack, soundhole, other) and providing a delete button for each. An "+ Add Void" button at the bottom opens the dialog to create a new void.
The status bar
A thin bar across the bottom of the window shows seven live indicators, left to right.
Cursor — the X and Y coordinates of your mouse pointer in millimeters. Watch this as you move the mouse to understand where you are in the coordinate system.
Selected — the index of the currently selected node, or a dash when nothing is selected.
Nodes — total count of nodes in the active path.
Zoom — current zoom level as a percentage. One hundred percent is the default; the range is 25 to 400 percent.
Grid — whether the grid is currently visible.
Mode — which path you are editing: Outer (the body outline), or the identifier of a specific void.
Auto-save indicator — a green "✓ Auto-saved" appears briefly after each edit operation, then fades after two seconds. If you don't see this indicator appearing during editing, auto-save may be failing (check browser console for localStorage errors).
Working on the Smart Guitar body specifically
For a Smart Guitar body outline, three things in this interface matter more than the rest.
Mirror mode will be on. The Smart Guitar body is symmetric across the centerline — an Explorer-Klein hybrid with balanced upper and lower bouts. Turn mirror mode on before you start placing nodes, and every change you make to one side will propagate to the other automatically. You only need to draw half the outline; the editor maintains the other half.
Bounding box target. The Smart Guitar body specification calls for 444.5 millimeters wide by 368.3 millimeters tall. Keep the bounding-box readout visible as you work and aim to land within a millimeter of those numbers. The ±5 millimeter tolerance you see on a typical guitar spec does not apply here because the body is a parametric design — the dimensions are the design, not a fabrication allowance.
The reference image is the concept render. You are working from an existing image that shows the ergonomic voids (upper bass, upper treble, lower bass), the cutaway geometry, and the overall proportions. Import it early, calibrate it against any known dimension (the nut width, a fret position, the body length itself if marked), and trace over it with the opacity set low enough that your nodes stand out clearly.

Chapter 2: Creating and Moving Nodes
Every outline in the editor is made of nodes — points on the canvas that the outline passes through — connected by curves. Drawing a guitar body comes down to placing nodes in the right positions and shaping the curves between them. This chapter covers how to place, move, select, and delete nodes, along with the numeric entry tools for precise positioning.
The default starting point
When you open the editor, a small dreadnought-like outline is already drawn on the canvas. This is an eight-node starter shape at roughly one-quarter scale, centered on the origin. Think of it as scaffolding — something to edit into whatever you actually want to draw. You can work with it directly, or replace it entirely by loading a template (covered in Chapter 7) or clicking New to reset.
The two kinds of clicks that place nodes
Clicking on an existing curve inserts a new node. Move your cursor until it hovers over the line between two existing nodes. When the cursor is within about seven pixels of the curve (at current zoom level), a click at that position inserts a new node exactly on the curve. The new node is smooth by default, meaning the curve continues to pass through it without a corner. This is how you add detail to an outline — if you need more nodes in the waist region, click on the curve in that region and a node appears.
Clicking in empty space deselects. Clicking anywhere that isn't a node or a curve clears your current selection. Nothing is placed.
There is no "create a new path from scratch" gesture. The editor always has exactly one outer path; you edit it into the shape you want rather than drawing it from nothing.
Selecting nodes
Single-click a node to select it. The node highlights and its Bezier handles become visible (two small orange diamonds connected by thin lines). The status bar shows the node's position. The Nodes panel on the right highlights the corresponding row.
Shift+click to add a second node to the selection. Multi-selection is capped at two nodes — you cannot select three or more at once with shift. This is a design choice to keep the mirror and nudge behaviors predictable.
Click in the Nodes panel to select a specific node. Every node is listed in the right panel with its X and Y coordinates. Clicking the row selects that node on the canvas. This is useful when nodes overlap or when you want to find a specific coordinate.
Click empty space to deselect all.
Moving nodes
Once a node is selected, four mechanisms are available for moving it.
Dragging with the mouse
Click and hold on a selected node, then drag. The node follows the cursor, snapping to the grid interval set by the Snap dropdown (1, 5, or 10 mm). A small orange circle appears at each snap point you cross, giving visual feedback that snapping is active. Release the mouse to commit the move.
If mirror mode is on and the node is on or very near the centerline (within half of the current snap size), the node is constrained to X=0 — you cannot drag it off the centerline. If the node is not on the centerline, its counterpart on the opposite side moves in mirror symmetry as you drag. Chapter 4 covers the details of mirror mode.
A drag gesture counts as one undo step. You can undo the entire drag with Ctrl+Z regardless of how far you moved.
Keyboard nudging
With one or more nodes selected, the arrow keys move them in 1mm, 5mm, or 10mm increments — whatever your current snap size is set to. Arrow up moves toward the neck (positive Y), arrow down moves toward the tail, arrow left and right move along the X-axis.
Hold Shift while pressing an arrow key for 0.1mm fine movement. This overrides the snap size and is the only way to move nodes in sub-millimeter increments via keyboard.
Nudges work on multi-selections: if you have two nodes selected, both move together. Nudges also respect mirror mode — nudging a node on the right side simultaneously mirrors the corresponding node on the left.
Nudges are disabled when the focus is in an input field (so typing a number into the coordinate modal doesn't also move the node).
Numeric coordinate entry
Double-click a selected node to open the Edit Node Coordinates dialog. Two fields appear: X in millimeters and Y in millimeters. Enter exact values and click OK. The node jumps to the entered position.
This is the right tool for placing a node at a specific design dimension — for example, if your spec calls for the waist minimum to sit at X = ±110 mm, Y = 160 mm, numeric entry gets you there exactly.
Live dimension feedback during drag
While you drag a single node, an orange text label follows the cursor showing the change in position from where the drag started: Δx and Δy in millimeters, with a plus or minus sign. The label disappears when you release the mouse.
This is the feature you use when a design calls for "move this node 12mm toward the neck" — you can watch the number count up as you drag and stop when it reads +12.00.
The dimension label only appears for single-node drags. Multi-node drags and keyboard nudges do not show it.
Deleting nodes
Select one or more nodes and press Delete.
Deleting a single node removes it immediately without confirmation.
Deleting two nodes at once prompts for confirmation. A dialog asks "Delete 2 selected nodes?" with OK/Cancel. This exists because multi-node deletion is a less-common action and harder to undo gracefully if accidental — the confirmation is there to catch misfires.
You cannot delete below three nodes. Both the outer path and every void require at least three nodes to remain a closed shape. The editor blocks the delete and shows an alert if you try.
If mirror mode is on, the editor re-validates mirror symmetry after deletion and may show a warning if the remaining nodes are now asymmetric.
The coordinate system in practical terms
The origin (0, 0) sits at the center of the body. Y is vertical on screen, with positive values toward the neck. X is horizontal, with positive toward the bass side and negative toward the treble side.
For a symmetric guitar body, you can think of it this way: every node on the bass side has a mirror twin on the treble side with the same Y and the opposite X. A node at (+130, 180) has a twin at (−130, 180). The butt-center and neck-center nodes sit at X = 0 by definition. This is the structure mirror mode maintains for you automatically.
The bounding-box readout at the top right of the canvas continuously shows the outline's current width and height in mm. If you're tracing to a target size, keep an eye on this number. For a Smart Guitar body at 444.5 × 368.3 mm, W should read 444.50 and H should read 368.30 when you're done.
What's selected in the status bar
The Selected field in the status bar shows the index of the currently selected node — the zero-based position in the path. When two nodes are selected, it shows the first; the second is tracked internally. When nothing is selected, it shows a dash.
The Nodes field shows the total count in the active path. As you insert or delete nodes, this number updates in real time. A typical guitar body outline ends up with somewhere between 20 and 60 nodes after refinement, depending on how much curve detail you want.
Automatic work preservation
Every node operation — placement, move, nudge, delete — triggers an auto-save to your browser's local storage. A small green "✓ Auto-saved" indicator briefly appears in the status bar after each save, then fades. If you close the tab by accident or the browser crashes, reopening the editor within 24 hours will prompt you to restore. Older auto-saves are discarded automatically.
This is a safety net, not a substitute for saving sessions. Chapter 8 covers the session format and export workflow, both of which produce files you can store outside the browser.
Working on the Smart Guitar specifically
For the Smart Guitar body, three aspects of node work matter more than the rest.
The centerline nodes are fixed at X = 0. The butt-center at roughly Y = −184 and the neck-center at roughly Y = +184 must sit exactly on the centerline. When you work with mirror mode on, these snap to X = 0 automatically when you place them near it.
Key reference points. The Explorer-Klein hybrid shape has specific points that matter: the upper bass corner, the upper treble transition, the waist minimum, the lower bass bulge, the lower treble bulge. Place nodes at these points first, with numeric entry if you have dimensions from the design doc, and fill in the intermediate nodes afterward by clicking on the curves.
Sub-millimeter precision in key regions. For cutaway geometry and the ergonomic void outlines, use Shift+arrow for 0.1mm nudges. The default 5mm snap is too coarse for fine features like the horn tips where every millimeter changes the playability.

Chapter 3: Bezier Curves and Node Shaping
The Body Outline Editor is a Bezier editor, not a polyline editor. That matters because a guitar body outline is mostly smooth curves with a few sharp transitions, and Bezier curves model that shape with far fewer nodes than polylines require. A dreadnought outline can be expressed in 20–30 nodes with well-placed Bezier handles; the same shape as a polyline would need hundreds to look smooth.
This chapter covers how the editor represents curves, how to shape them with handles, and how to switch between smooth and cusp behavior at each node.
What a Bezier node is, in this editor
Every node has three components:

The anchor point — the X/Y position you see and drag on the canvas.
The handle-in vector — controls how the curve approaches the node from the previous node.
The handle-out vector — controls how the curve leaves the node toward the next node.

The handles are vectors from the anchor point. If a handle is zero length, it has no influence and the segment on that side is a straight line. If a handle has length, it pulls the curve in the direction it points, with more pull the longer it is.
There are three meaningful node states in practice:
Cusp (no handles): both handles are zero. The curve passes straight through the node with no smoothing, creating a sharp corner. Use this at actual corners — the tip of a Stratocaster horn, for example, or the pointed upper corners of an Explorer.
Smooth symmetric (handles exist, mirror each other): the two handles are equal in length and opposite in direction. The curve flows through the node with continuous tangent — no visible corner, no tightening on one side. This is the default state when Paper.js automatically smooths nodes, and it's right for almost all body outline work.
Smooth asymmetric (handles exist, independent): the two handles have different lengths or non-opposite directions. The curve is still continuous at the node (no corner), but it tightens differently on each side. Use this when the curvature before a node is meaningfully different from the curvature after it — like the transition from a tight waist into a wider lower bout.
Showing and hiding handles
By default, handles are invisible. They only appear for nodes that are currently selected. Select a node and you see two small orange diamonds, one for each handle, connected to the anchor point by thin lines.
The "Handles: OFF / ON" toolbar button toggles a global show-all mode. When on, every node's handles are visible at once. This is useful for inspecting the overall shape of a curve or spotting a node whose handles are set oddly, but it gets visually noisy on a dense outline. For routine work, leave it off and rely on per-node visibility.
Dragging a handle
With a node selected so its handles are visible, click and drag one of the orange diamonds. The curve updates live as you drag.
Default drag is symmetric. Moving handle-in automatically moves handle-out to the mirror position (same length, opposite direction). Dragging handle-out does the reverse. This keeps the node smooth as you shape the curve — you adjust one side, and the other side follows to preserve tangent continuity.
Hold Alt while dragging to break the symmetry. With Alt held, only the handle you're dragging moves. The opposite handle stays put. This produces an asymmetric smooth node — still smooth (no corner), but with independent tangent magnitudes on each side.
Once a node is asymmetric, it stays asymmetric. Handle drags without Alt will continue to move the dragged handle only; the asymmetry doesn't auto-correct. To return to symmetric, Alt+click the node twice: once to clear both handles (cusp), once to re-smooth (fresh symmetric handles computed by Paper.js).
There's a subtle gotcha here worth flagging: Paper.js's .smooth() computes handles based on the adjacent node positions at that moment. If you smooth, then move the adjacent nodes significantly, the smoothed handles can look wrong because they reflect the old neighbor positions. Running Smooth All again recomputes them against current positions.
Alt+click to toggle smooth and cusp
Hold Alt and click on a node (not a handle). The node toggles between its current state and the other main state:

If the node has any handles → they're cleared. Node becomes a cusp.
If the node has no handles → .smooth() runs. Node becomes smooth symmetric with handles computed from neighbors.

There's no direct gesture to go from asymmetric to cusp without passing through symmetric, or from cusp to asymmetric. In practice this doesn't matter: you toggle through the states as needed.
The Smooth All button
Clicking Smooth All runs .smooth() on every node in the active path at once. This gives all nodes fresh symmetric handles based on their current neighbors.
When it's useful:

After loading a template (templates come in with all-cusp nodes by default and need smoothing)
After Simplify, if the simplified curve came out too angular
When a series of edits has left the outline with a mix of cusp and smooth nodes and you want a clean baseline

When to avoid it:

If you've carefully set asymmetric handles on specific nodes, Smooth All will overwrite them with symmetric defaults. No warning, no undo-preview.
If you have intentional cusps at corners (horn tips, sharp transitions), Smooth All will smooth them too and turn corners into curves.

There's no "smooth selected only" option. If you want to preserve specific nodes, the workflow is: Smooth All first, then Alt+click the nodes that should be cusps to sharpen them back.
The Simplify button
Simplify reduces the number of nodes in the active path while approximating the original curve. It's Paper.js's built-in path.simplify(tolerance) function.
The tolerance field next to the button controls aggressiveness — default 2.5, range 1 to 10. Lower tolerance preserves more detail (keeps more nodes). Higher tolerance approximates more loosely (removes more nodes).
When to use it:

The outline was imported or generated with far more nodes than you need (200+ nodes on a shape that should have 30).
After tracing a reference image with liberal node placement, to cut the count down to something manageable.
Before exporting DXF, if downstream CAM tools struggle with high node counts.

What it actually does: Paper.js uses a curve-fitting algorithm that replaces runs of nodes with fewer Bezier curves matching the original shape within the tolerance. It's not a decimation — it's a re-fit. The output nodes are at new positions that aren't in the input.
Gotchas:

Simplify works on the active path only. If you're editing the outer body, voids aren't affected, and vice versa.
The re-fit happens in one step and is fully undoable with Ctrl+Z, but you cannot preview the result before committing.
Simplify can move nodes off the centerline slightly. If mirror symmetry matters (it usually does), verify X=0 on the centerline nodes after running Simplify, and use numeric entry to correct them if they drifted.
Running Simplify repeatedly on the same path produces diminishing returns. Each pass re-fits based on the current state, not the original. If you over-simplified, undo rather than trying to "de-simplify" with a lower tolerance.

Shaping a curve in practice
The typical workflow for shaping a body outline curve:

Place nodes at the key anchor points — bout maxes, waist minimum, endpoint centers. Use numeric entry or click-to-place.
Run Smooth All to get default symmetric handles throughout.
Inspect the result. Most of the curve will look right. Some sections will look too tight or too loose.
For sections that look wrong, select the nodes and drag their handles to adjust. Default symmetric drag handles most cases.
For transitions where the curve needs to change character noticeably — the waist narrowing into the bout, for example — hold Alt and drag one handle to create asymmetry.
For actual corners, Alt+click to cusp.
If you ended up with too many nodes, run Simplify. Verify the result and re-adjust if needed.

Handle length as a design lever
One thing that takes practice: handle length controls the "tension" of the curve, and small length changes make a real difference.

Short handles (say, 20% of the distance to the next node) make the curve hug the anchor points closely — tighter, more angular feel.
Medium handles (around 35–40%) give the "natural" look — the shape Paper.js's auto-smooth targets.
Long handles (50%+) make the curve swing outward between nodes — looser, more sweeping feel.

For a guitar body, you generally want medium handles in the bouts (smooth arcs) and shorter handles near the waist (tighter curvature). Asymmetric handles where the bout meets the waist let you transition naturally.
There's no numeric handle-length field in the editor. Length is adjusted by dragging — eyeball it, watch the curve, adjust. If you need exact handle lengths, the session JSON stores them explicitly and you can edit the file directly.
What's stored when you save
Every node's anchor point and both handle vectors are saved in full:

Session files (.sgession) preserve everything
JSON export preserves everything through tessellation (the curves are evaluated at 20 points each, so the exact handle values aren't in the JSON — the sampled curve is)
DXF export is just LINE entities from the tessellated curve, so handle information is lost at export

This means: if you export to DXF, edit the geometry in CAD, and bring it back, you lose the Bezier structure. Round-tripping requires JSON. For ongoing editing, save sessions.
Working on the Smart Guitar specifically
The Smart Guitar body has specific curve requirements worth keeping in mind.
The lower bass bulge and upper bass/treble corners need asymmetric handles. The transitions into and out of these features have different curvature characteristics on each side. Plan to Alt+drag the handles on the three or four nodes defining each transition.
The ergonomic voids are not simple circles. They have intentional flat sections and gradual transitions. Each void will be a separate path with its own Bezier nodes — plan on 8–12 nodes per void, with a mix of symmetric and asymmetric handles.
The cutaway is where asymmetric handles matter most. The transition from the upper bout around the cutaway into the neck region changes character abruptly. The node at the top of the cutaway should be asymmetric — smooth going in from the upper bout, tighter coming out toward the neck join.
Don't Simplify until the shape is locked. Running Simplify on in-progress work can collapse intentional shape features. Save it for end-of-session cleanup after you're happy with the overall form.

Internal-use notes for Chapter 3:
The asymmetric state isn't visually distinguished from symmetric in the UI. A symmetric smooth node and an asymmetric smooth node look identical unless you select them and can see the handle lengths differ. If you come back to a session and want to know which nodes have asymmetric handles, you have to click each one. Not a bug, just a UX gap.
Paper.js handles and DXF export. The export tessellates at 20 steps per curve, which is pretty coarse for a tight radius. If you have a very tight curve (horn tip, for example) in a 20-step tessellation, it will show as a slight polygon rather than a smooth curve. The fix is either more nodes in that region (so each curve segment is smaller) or bumping the tessellation steps — which requires editing the code.
The "Smart Guitar" workflow I've been writing up assumes the body spec is locked. If the spec is still being iterated (ergonomic voids moving, cutaway geometry changing), you'll be retracing this workflow multiple times. The session save/load flow is designed for that — save a session after each major spec change, and you can load-compare to the previous revision.

Chapter 4: Mirror Mode
A guitar body is symmetric across its centerline. The bass side and treble side are mirror images. Mirror mode is the editor's built-in enforcement of that symmetry — you draw half the outline, and the other half is maintained automatically as you work.
This chapter covers how mirror mode works, when to use it, where it can drift, and how to verify the symmetry is actually preserved.
Turning mirror mode on and off
Click the "Mirror: OFF" button in the toolbar to toggle mirror mode on. The button label changes to "Mirror: ON" and highlights in green. A dashed green centerline appears on the canvas running vertically through X = 0, showing you the axis of symmetry.
Click the button again to turn it off. The centerline disappears and mirror enforcement stops. Nodes you've already placed remain symmetric; new edits just won't mirror.
There's no keyboard shortcut for mirror mode. It's mouse-only, which is a minor UX gap for an action you'll toggle frequently.
What mirror mode actually does during editing
When mirror mode is on, four behaviors change:
Dragging a non-centerline node moves its mirror twin. As you drag a node on the bass side (positive X), the editor finds the corresponding node on the treble side (negative X) and moves it to the mirrored position in real time. Same Y coordinate, opposite X.
Dragging a centerline node stays on the centerline. If a node starts on or within half a snap size of X = 0, mirror mode constrains it to X = 0 during the drag. You can move it up and down the centerline but not off it. This is how the butt-center and neck-center nodes stay locked to the axis of symmetry.
Keyboard nudges mirror as well. Arrow-key nudges respect the same rules — bass-side nudge moves the treble twin, centerline nudge stays on the centerline.
Handles mirror too. When you drag a Bezier handle on a bass-side node, the mirror twin's corresponding handle is updated with the opposite X sign and the same Y. Smooth curves stay smooth on both sides, asymmetric handles stay asymmetric on both sides.
Inserting a new node, deleting nodes, or using Alt+click to toggle smooth/cusp are not automatically mirrored. Those operations affect only the node you clicked on. More on that below.
How the editor finds the mirror twin
This is the most important part of the chapter for actually using mirror mode well.
When you drag a node, the editor scans every other node in the path looking for the best mirror candidate. The scoring formula weights three things:

Y-coordinate match (weight 2): the mirror twin should have the same Y.
X-coordinate mirror match (weight 3): the mirror twin should have the X-value negated. This is weighted highest — being close in X is the strongest signal.
Handle similarity (weight 1): the mirror twin's handles should already be in the mirror configuration.

The candidate with the lowest total score wins, and only if that score is below 30. If no candidate scores below 30, no twin is found and the drag affects only the node you moved.
What this means in practice: mirror mode works well when your outline is already approximately symmetric. It struggles when the two sides have drifted apart, because the weighted search can't find a good twin — or worse, can match to the wrong node.
If you've never set up symmetry in the first place (for example, you drew half the outline freeform without mirror mode, then turned it on), mirror mode cannot retroactively create twins. It only maintains symmetry for nodes that already have mirror partners.
The workflow that actually works
Given how mirror matching works, here's the reliable sequence:

Start with mirror mode on, from the beginning. Either use the default starter outline (which is already symmetric) or load a template (which generates symmetric outlines).
Insert new nodes with mirror mode on. When you click on a curve to insert a node, the node appears at that single position — it isn't automatically mirrored. You need to insert a second node at the mirrored position manually. This is clunky; we'll cover it more below.
Edit nodes by dragging, and the twins follow.
Delete carefully. Deleting a node does not delete its twin. You need to delete both, one at a time, or use multi-select (shift+click both, then Delete with confirmation).

The insertion gotcha
Inserting a new node by clicking on a curve is the single most error-prone operation in mirror mode. The editor inserts one node — not a mirrored pair.
What happens: you click on the right-side curve between two nodes. A new node appears there. The left side now has one fewer node than the right side, and the outline is no longer symmetric.
The fix: after inserting, click on the corresponding position on the left-side curve to insert a mirror node. Eyeball it or use the bounding-box readout to judge "the same spot on the other side." Then drag one of the two newly-inserted nodes — and mirror mode will search for the twin and snap it into place.
A better workflow when you know you need to add detail to both sides: insert the right-side node, note its X and Y (visible in the Nodes panel), then double-click the left-side curve at approximately the same Y, insert a node there, and immediately double-click to open the coordinate dialog. Enter the mirror X value explicitly.
This is a real usability gap in the editor. An "insert mirrored pair" gesture would be useful, but it doesn't exist.
Mirror validation — the symmetry check
The editor has a validation function that reports on symmetry. It runs automatically after node deletion when mirror mode is on, and you can trigger it anytime via the testWeightedMirror() console function.
What it checks:

Node count balance: the number of nodes on the left (X < −0.1) should roughly equal the number on the right (X > 0.1). More than one node difference triggers a warning.
Pairing quality: for each left-side node, it tries to find a right-side node within 20mm in Y and 10mm in X of the mirrored position. Unmatched left-side nodes count as "unpaired" and trigger warnings.
Centerline nodes: nodes within 0.1mm of X = 0 are treated as centerline nodes and don't need pairing.

Warnings appear as an orange toast in the bottom-right of the canvas, auto-fading after 8 seconds. The full detail goes to the browser console.
Important caveat: these are warnings, not errors. The editor will let you export an asymmetric outline. If you export to DXF and the outline was only approximately symmetric, the asymmetry rides through to CAM.
Things mirror mode does not do
Several operations that sound like they should mirror actually don't:

Alt+click smooth/cusp toggle affects only the clicked node. If you make a right-side node a cusp, the left twin stays smooth. Apply the toggle to both sides manually.
Simplify and Smooth All operate on all nodes equally — they don't respect mirror pairs. In practice this is fine because they operate symmetrically on already-symmetric input, but if the input is asymmetric, the output will be too.
Inserting nodes (covered above).
Voids — mirror mode does not apply to void paths, only to the currently active path. If you want a symmetric pickup cavity, you have to draw it symmetrically yourself or accept minor asymmetries.

That last one is a bigger limitation than it sounds. On instruments with a single centered soundhole, you just draw the hole symmetrically once. But on instruments with paired pickups or symmetric control cavities, you're editing each side manually — mirror mode doesn't help.
Mirror mode with templates
All eight built-in templates generate symmetric outlines by construction. The generateTemplateOutline function produces one side's nodes mathematically, then mirrors them to create the other side. When you load a template with mirror mode on, the outline is perfectly symmetric to floating-point precision.
This is the ideal starting point for mirror work. Load the template closest to your target shape, turn on mirror mode, and start editing. The initial symmetry is maintained as you drag nodes.
Verifying symmetry before export
Before you commit to a DXF export, it's worth a symmetry check:

Check the node count: left and right node counts should match (look at the Nodes panel and count, or run testWeightedMirror() in the console).
Look at the outline shape with grid on and the centerline visible. Mirror mode's green dashed centerline should visually bisect the shape.
Pick a few matched pairs and click each one — the Y coordinates should match and the X coordinates should be equal in magnitude.
Check centerline nodes explicitly — butt-center and neck-center should show X = 0.00 exactly in the Nodes panel.

If any of these fail, you have drift. Fix it before export — once it's in DXF it's someone else's problem to reconcile.
Working on the Smart Guitar specifically
The Smart Guitar body is symmetric across the centerline by design, so mirror mode is your default working state.
Centerline nodes to lock in first. The butt-center node at roughly (0, −184) and the neck-center node at roughly (0, +184). Place these with numeric entry so they're exactly at X = 0. They'll stay there under mirror mode.
The Explorer-Klein corners are symmetric but sharp. The upper bass corner and upper treble corner of the Explorer-inspired silhouette are cusps, not smooth curves. Remember mirror mode doesn't auto-propagate Alt+click — you'll need to Alt+click both corners.
The ergonomic voids are centered but not symmetric. The upper bass void, upper treble void, and lower bass void are individually non-symmetric shapes whose positions are asymmetric on the body (there's no "lower treble void"). Mirror mode won't help here. Each void is drawn manually as its own path.
The cutaway breaks symmetry intentionally. A single cutaway on one side (typically treble side for right-handed players) means the body's upper region is asymmetric by design. For the Smart Guitar, decide early whether you're modeling the body with the cutaway as part of the main outline (in which case mirror mode is unusable from that point forward) or as a separate void (in which case mirror mode stays usable for the main body).
For the Smart Guitar spec as it stands, the cutaway is part of the main outline. This means the recommended workflow is: build the symmetric body first with mirror mode on, verify symmetry, then turn mirror mode off and cut the cutaway into the treble-side upper bout by moving those specific nodes.

Internal-use notes for Chapter 4:
The 30-point scoring threshold is arbitrary. It's in the code as a hardcoded magic number. For bodies at typical guitar scale (~500mm body length), it works. If you ever use this editor for very small or very large bodies (ukulele, upright bass), the threshold might need adjustment. There's no UI for this.
The insertion gotcha is a known pain point. I'd flag it as a candidate for v3.1 improvement — "insert mirrored pair when mirror mode is on" is a small code change and would make mirror workflows significantly smoother.
Mirror validation is observational, not corrective. It tells you when things are wrong but doesn't fix them. A "re-symmetrize" button that forced left-side nodes to match right-side (or vice versa) would be genuinely useful, especially after operations that break symmetry. Also a v3.1 candidate.
Testing mirror mode in console. testWeightedMirror() is a manual test harness for the pairing algorithm. Running it from the browser console on an edited outline will tell you how the matcher is performing on your actual geometry. Useful when mirror behavior feels off — the diagnostic output is more detailed than the UI warnings.

Chapter 5: Reference Images and Calibration
The Body Outline Editor is fundamentally a tracing tool. You can draw outlines freehand from numeric specifications, but the faster workflow is to import a reference image — a photograph, a scan of a paper plan, or a CAD render — place it behind the geometry layer, and trace over it with nodes and Bezier curves. For the traced outline to have correct real-world dimensions, the image needs to be calibrated against a known distance. This chapter covers both halves: getting images in, and making them dimensionally correct.
Image formats and sources
The editor accepts JPEG and PNG files. No other formats — no GIF, no TIFF, no PDF, no SVG, no DXF-as-image. If you have a reference in another format, convert it to JPEG or PNG first.
In practice, the useful sources are:
Scanned paper plans. Most guitar plans published on paper are drawn to 1:1 scale. Scanning at 300 DPI or higher gives you a workable reference. These are the most common input.
Photographs of existing instruments. Workable for shape reference, but bad for absolute dimensions because of perspective distortion, lens curvature, and no known reference distance. If you calibrate against a feature whose length you know (a nut width, a fret span), you can still get reasonable results.
Concept renders from CAD or AI tools. These work well because they're rendered orthographically without lens distortion. For the Smart Guitar specifically, concept renders are the primary reference since the body is a new design without physical instruments to photograph.
Screenshots from other software. Fusion 360, SolidWorks, Blender — anything that can produce a flat orthographic image of a body outline. Calibrate against a dimension you know from the source file.
Importing an image
Click "Import Image" in the toolbar. A standard file picker opens. Select a JPEG or PNG.
The image loads into the canvas as a background layer:

Positioned at the current view center (origin of the coordinate system by default)
Opacity set to 50%
Sent behind the grid and geometry layers

The Reference Image panel appears in the right sidebar with an opacity slider. The default 50% is a reasonable starting point — visible enough to trace over, faded enough that your nodes and curves stand out clearly on top. Adjust from 20% to 80% as needed; darker images generally want lower opacity.
If you already have an image loaded, importing a new one replaces it. The previous image is discarded, and any calibration applied to it is invalidated.
Image positioning
The image arrives at the view center, which is the origin by default. If you've panned the view before importing, the image goes to wherever your view is centered, not to origin. This can be confusing on import — the image might appear off-center relative to the coordinate grid.
The fix: after importing, press Ctrl+N (New) if the canvas is empty, or manually pan back to origin. There's no "re-center image" button; the image's position is only set once, at import time.
You cannot drag the image to reposition it. The image is locked in place on the canvas. If the subject of the photograph isn't centered within the image frame, the subject won't be at origin in the editor. You have two options:

Pre-crop the image before importing so the subject is centered.
Ignore it and trace anyway. Your outline will be centered on origin regardless of where the image sits, because you place nodes based on the reference visually — not based on image pixel coordinates.

Most of the time, option 2 is fine. You're tracing a shape, not aligning to image pixels.
The opacity slider
The Reference Image panel has a single control: an opacity slider ranging from 20% to 80%, default 50%.
Lower opacity makes the image fainter and your outline stand out more. Higher opacity makes the image more visible and your outline harder to see against it. Adjust based on contrast: a dark photograph on a dark canvas background wants low opacity, a light-colored plan wants higher opacity.
There's no brightness or contrast adjustment. If your image is poorly exposed or low contrast, the editor can't improve it — preprocess the image in a photo editor first.
Removing an image
"Clear Image" removes the current reference image entirely. The image panel disappears, any calibration is cleared, and the image's stored calibration data is discarded.
This is a destructive operation. There's no undo for image import/clear. If you clear an image, then want it back, you have to import it again and recalibrate.
What calibration actually does
The editor's coordinate system is in millimeters. When you import an image, the pixels are displayed at some arbitrary size that has no relationship to mm — by default, a pixel is roughly a mm, but that's just a coincidence of the display, not calibrated truth.
Calibration establishes the real-world scale of the image. You tell the editor: "these two points on the image are N millimeters apart in reality." The editor calculates how much to scale the image so that pixel distances match mm distances, and scales the raster accordingly.
After calibration:

The image is resized so that real-world dimensions match coordinate-space dimensions.
A node placed at (100, 0) on the canvas corresponds to a point 100mm to the right of center on the real instrument.
The bounding-box readout accurately reflects body width and height in mm.

Calibration affects the image only. Your geometry (nodes, curves) is unaffected — those were always in mm. Calibration makes the image align to the geometry's coordinate system, not the other way around.
The calibration workflow

Import the image first. Calibration won't run without an image loaded — you'll get an alert.
Identify a reference distance you know in real-world millimeters. Options:


A printed dimension on the plan (e.g., "508 mm" next to an arrow on the plan)
A scale bar (e.g., a 100mm indicator line on the plan)
A feature you know from the instrument spec (nut width, 12th-fret position, total body length)
An object of known size included in the photograph (ruler, coin, reference block)


Click Calibrate (button or C key). A status label appears at the top-left of the canvas: "Click point A".
Click the first endpoint of your reference distance on the image. A marker appears at that point. Status changes to "Click point B".
Click the second endpoint. A second marker appears. A modal opens asking for the known distance in millimeters.
Enter the distance (default value is 100). Click Apply.

The image is rescaled, markers disappear, and a green confirmation appears briefly in the status bar: "✓ Calibrated: 100mm = 432.1px" (or similar).
Cancel Calibrate at any point by clicking the Cancel button in the modal or by starting a different mode (e.g., pressing M for Measure). Partial calibration — clicking point A but not point B — can be cleared by clicking Calibrate again to restart.
The validation checks
The calibration function runs five checks before applying:

Numeric input. The distance must be a positive number. Negative numbers, zero, or non-numeric input shows an alert and aborts.
Points exist. You need to have clicked two points. If the modal somehow opens without two points recorded, it aborts.
Points not too close. If the two clicked points are within 5 pixels of each other, calibration aborts — that's not a meaningful reference distance, and the resulting scale factor would be enormous.
Sanity check on scale. If the computed scale factor is below 0.01 or above 100 — which usually means you entered the wrong distance — a confirmation prompt asks whether to proceed. Click OK to apply anyway, Cancel to abort.
Resulting image size check. If applying the scale would make the image smaller than 50 pixels in either dimension, or larger than 5000 pixels, a second confirmation asks whether to proceed.

These are safeguards against mis-calibration. The most common mistake — entering the distance in inches instead of millimeters, or picking two points that are actually much farther apart than you think — gets caught by checks 4 and 5.
Calibration accuracy in practice
Calibration precision depends entirely on how accurately you click the two reference points and how confident you are in the real-world distance.
High-accuracy calibration (±0.5mm over a 500mm body):

Scanned paper plan with a printed scale bar or explicit dimension line
Click precisely at the endpoints of the scale bar
Zoom in (mouse wheel) before clicking so pixel-level precision is actually available
Enter the distance to 0.1mm precision

Medium-accuracy calibration (±2mm over a 500mm body):

Photograph or render with a known feature (body length, scale length)
Click endpoints as best you can judge them
Enter the feature's dimension from spec

Low-accuracy calibration (worse than ±5mm):

Photograph without an in-frame reference, relying on "the body is roughly this long"
Loose click placement
Works for rough layout but not for dimensional work

For the Smart Guitar, accuracy better than ±1mm is expected because the body is a parametric design and downstream CAM depends on precise geometry.
Re-calibrating
If your initial calibration was wrong, run Calibrate again. The new calibration replaces the old one — the image is rescaled from its current (already-scaled) state by the new factor.
This is important: recalibration doesn't reset to the original import scale. If you calibrate once incorrectly and then calibrate again, the second calibration compounds on the first. If the first was off by a factor of 2 and you try to correct it, you need to enter a reference that corrects for the combined error.
The reliable reset path: Clear Image, re-import, recalibrate. This gives you a clean starting point.
What calibration doesn't do
Calibration does not correct perspective distortion. If you photograph a guitar body at an angle, the image will not be perfectly flat — features farther from the camera will appear smaller. Calibrating against one dimension will make that dimension correct, but other dimensions will be off proportional to how much perspective is in the image.
Calibration does not correct lens distortion. Wide-angle and fisheye lenses curve straight lines. The editor can't straighten those.
For the Smart Guitar: concept renders from CAD tools are orthographic, so no perspective correction is needed. If you're ever tracing from a phone photograph, expect ±5mm errors in dimensions far from your calibration points.
Calibration is not saved by default
When you Export JSON or Export DXF, the calibration factor is not explicitly recorded in the output. The geometry is in mm regardless — calibration just ensures the image was properly scaled relative to your node placements.
When you Save Session (.sgession), the reference image is serialized into the session file as a base64 data URL, and the calibration factor is saved as imagePixelsPerMM. Loading a session restores the image at its calibrated scale. This is the only way calibration persists across sessions.
Working on the Smart Guitar specifically
For Smart Guitar body tracing, two workflow patterns work:
Pattern 1: trace from a concept render with explicit dimensions.

Start with an orthographic render of the Smart Guitar body concept — flat projection, no perspective.
Import the render.
Calibrate against the 444.5mm body width dimension (widest horizontal point of the body). This gets you the best horizontal accuracy.
Verify the 368.3mm height matches by using the Measure tool after calibration — click top and bottom of the body, read the distance. Should be within 1–2mm of 368.3.
If height is off, your render has unequal X/Y scaling (unusual but possible). Decide whether to re-calibrate against height instead, or accept the small discrepancy.

Pattern 2: trace from a paper plan or scaled drawing.

Scan the plan at 300 DPI or higher.
Import the scan.
Calibrate against the plan's scale bar if one is present, or against the body length dimension.
Set opacity to 40% — paper scans tend to be dense and need more fading.
Begin tracing.

In both patterns, zoom in for calibration clicks. The wheel-zoom is cheap; use it.
One last Smart Guitar-specific note: the ergonomic voids visible in concept renders are three-dimensional features — they're carved into the body top, not through-body cutouts. When you trace them as voids, you're capturing their plan-view outlines. The depth profile is a separate design input that lives outside the 2D outline editor.

Internal-use notes for Chapter 5:
The 50-pixel / 5000-pixel bounds on calibration are soft warnings, not hard limits. You can click through both confirmation prompts and calibrate to absurd scales. The editor won't stop you. If a user accidentally click-throughs and then can't figure out why nothing looks right, recalibrating or clearing and re-importing is the recovery.
There's no image rotation. If your reference image is oriented with the neck pointing down instead of up, you have to rotate the image file externally before importing. Rotating in the editor isn't supported. For Smart Guitar work where the design convention is neck-up, make sure renders are delivered that way.
Image position offset is unrecoverable without clearing. If the image ends up positioned awkwardly (because view was panned when you imported), there's no "re-center image on origin" operation. The workaround is clear-and-reimport, or (for advanced use) editing the session JSON directly to zero out referenceImage.position.
The data-URL session serialization is expensive for large images. A 3000×3000px reference image becomes a ~20MB base64 string in the .sgession file. Save Session is slow in that case. For reference images above ~2000px per side, consider resampling before import.

Chapter 6: Voids
A void is a closed region inside the body outline that represents a cavity, opening, or material removal. Pickup routes, control cavities, switch pockets, output jack holes, soundholes — all of these are voids in the outline geometry. This chapter covers creating, editing, and exporting voids, and the role they play in the overall design.
What a void is, precisely
In the editor's data model, a void is a separate closed path, independent of the outer body outline. Each void carries three pieces of information:

A unique ID generated at creation time
A role — one of six categories: pickup, control cavity, switch, jack, soundhole, or other
A path — the Bezier geometry defining the void's shape

Voids are edited the same way as the outer outline: place nodes, drag them, shape Bezier handles, use Alt+click to toggle cusps. The same keyboard shortcuts apply. The only difference is that voids are the active path only when selected, and certain operations (mirror mode, for example) behave differently.
Creating a void
Two entry points: the "+ Void" button in the toolbar, or the "+ Add Void" button at the bottom of the Voids panel in the right sidebar. Both open the same dialog.
The dialog has one control: a Role dropdown. Pick from pickup, control_cavity, switch, jack, soundhole, or other. Click Create.
A new void appears at origin — a small default closed shape (typically a small rectangle or circle; exact initial geometry is generated at creation). The void is added to the Voids list in the right panel with an entry showing its role and a delete button. The editor automatically switches the active path to the new void, so any editing you do next is on the void, not on the body outline.
You can create as many voids as you need. There's no hard limit. Practical limits are about how many you can meaningfully manage in the UI.
The six roles
Role is primarily a labeling choice — it determines the void's color on the canvas and its layer name in DXF export. It doesn't constrain the void's shape; a void tagged "pickup" isn't required to look like a pickup.
pickup (orange). For pickup routes. In DXF: VOID_PICKUP layer.
control_cavity (amber). For potentiometer and wiring cavity openings. In DXF: VOID_CONTROL_CAVITY layer.
switch (yellow). For toggle switch pockets. In DXF: VOID_SWITCH layer.
jack (orange-red). For output jack holes or jack plate cutouts. In DXF: VOID_JACK layer.
soundhole (blue). For acoustic instrument soundholes. In DXF: VOID_SOUNDHOLE layer.
other (purple). Catch-all for anything that doesn't fit the other categories — rib channels, chamfer boundaries, decorative inlays, trussrod access, whatever you need. In DXF: VOID_OTHER layer.
The role is a tag, not a constraint. If you need a void that conceptually is none of these — an ergonomic void on the Smart Guitar, for example — use "other" and document what it represents in your design notes.
Switching between the outer outline and voids
The toolbar has two mode buttons: "Outer" and "+ Void". "Outer" makes the main body outline the active path. "+ Void" creates a new void (it's the same button as the toolbar one). Once voids exist, the Voids panel becomes the primary way to switch between them — each void entry in the list is clickable, and clicking makes that void the active path.
The status bar's "Mode" field shows the current active path: "Outer" when editing the body, or the void's ID when editing a void.
Only the active path responds to editing. If you have the main outline active and click on a void's node, nothing happens — the click is interpreted as a canvas click in the void's area, not a selection. You must make the void active first. This is subtle and easy to miss.
Editing voids
All the Chapter 2 and Chapter 3 operations apply to voids:

Click to select nodes, drag to move them.
Click on a void's curve to insert a new node.
Double-click for numeric coordinate entry.
Arrow keys to nudge (with Shift for 0.1mm fine movement).
Alt+click to toggle smooth/cusp.
Drag handles to shape curves, Alt+drag for asymmetric.
Delete to remove nodes (minimum 3 enforced).
Simplify and Smooth All buttons operate on the active path, so they apply to the currently active void.

Mirror mode and voids
Mirror mode does not apply to voids. When mirror mode is on and you have a void active, the centerline still displays visually, but mirror enforcement is disabled. Dragging a void node moves only that node. The mirror-pairing algorithm doesn't run on voids.
This is a significant limitation for instruments with symmetric pickup cavities or paired control routes. You have two options:

Draw one side, then duplicate. Build the right-side pickup with all its nodes and curves. Save the session, inspect the JSON, and manually create a mirrored left-side void by negating every X coordinate. Not a polished workflow.
Draw each side independently. Accept that small asymmetries will creep in. For routes that will be cut with a template and a router, this might not matter practically — but it will show up in DXF export.

A future enhancement (v3.1 or later) that added mirror support for voids would meaningfully improve the workflow. Worth flagging for the roadmap.
Void winding and DXF export
DXF export enforces winding direction:

Outer body outline: counterclockwise (CCW) winding
Voids: clockwise (CW) winding

This convention matches standard CAM expectations — outer boundaries CCW, inner boundaries (holes) CW. The exporter automatically reverses point order if the path's natural winding doesn't match the expected direction. You don't have to think about it during editing; the enforcement happens at export time.
Why it matters: if a downstream CAM tool processes the DXF without understanding layer semantics, it may use winding direction to distinguish "cut boundary" from "cut pocket." A void with the wrong winding direction could be interpreted as a positive feature instead of a negative one. The editor's automatic enforcement prevents this.
Void positioning and accuracy
For Smart Guitar work — and any parametric design — voids need to be positioned to tight tolerance. The workflow:

Look up the void's position from the design spec (center coordinates in mm relative to body center).
Create the void.
Use numeric coordinate entry (double-click nodes) to place each node at its exact specified position.
Verify the bounding box of the void matches the spec dimensions.

Don't eyeball void positioning. The default void geometry at creation is small and centered at origin — it needs to be moved into place node-by-node. Every node's X and Y should come from numeric values, not from looking at the screen.
Exporting void geometry
DXF export produces a line-by-line tessellated representation: each Bezier curve is sampled at 20 points and emitted as a sequence of LINE entities. This is coarse for tight-radius voids (small soundholes, round pickup corners). If you have a void with a radius under ~10mm, the 20-step tessellation will visibly polygon-ize it in CAD.
Workarounds:

Accept the polygon and re-round in CAD. Fusion 360 can take a roughly circular polygon and fit a true circle to it. This is extra work but works.
More nodes at tight features. Rather than relying on Bezier smoothing, place more nodes around tight curves so each curve segment is shorter. A circular pickup modeled as 16 nodes with smooth handles will tessellate closer to a true circle than 8 nodes with the same handles.
JSON export and downstream re-curving. The JSON export records the same tessellated points but in a more machine-readable form. A custom downstream tool could re-fit curves from the JSON.

For Smart Guitar, the ergonomic voids are large enough that tessellation artifacts won't be visible. The pickup routes and control cavities are smaller and might need the "more nodes" workaround.
Deleting voids
Each void in the Voids panel has an × button to delete it. Clicking it removes the void immediately, no confirmation.
This is a design oversight — multi-node deletion within a path prompts for confirmation (Chapter 2), but whole-void deletion doesn't. Be careful clicking the × buttons. If you accidentally delete a void, Ctrl+Z should bring it back since void deletion is captured in the undo stack.
There's no multi-select on voids. You delete them one at a time.
What voids look like in session files and exports
Session (.sgession): voids are serialized with full Bezier information (anchor points, handle-in, handle-out) in an array. Loading restores them exactly.
JSON export: voids are in a voids array. Each entry has id, role, closed: true, winding: "cw", and a points array from tessellation. No Bezier structure — just sampled points. Re-importing the JSON wouldn't give you the original curves.
DXF export: each void becomes a series of LINE entities on a layer named VOID_<ROLE>. The LINES form a closed polygon. No curve information, no layer hierarchy beyond the flat layer name. This is the most lossy output but also the most universally readable.
SVG export: voids appear as colored paths in the SVG, preserving Bezier curves but not role metadata (beyond stroke color).
Choose the export format based on where the geometry is going:

Going to CAM or Fusion 360 for fabrication → DXF
Going to another tool that understands structured data → JSON
Going to documentation, web display, or illustration → SVG
Staying in the editor for later editing → Save Session (.sgession)

Working on the Smart Guitar specifically
The Smart Guitar body has multiple voids, each with specific design intent:
Three ergonomic voids (upper bass, upper treble, lower bass). These are the ribcage-and-forearm carved relief areas. Use the "other" role since they're not standard cavities. Each is a large, gently-curved closed shape; 10–14 nodes per void with smooth symmetric handles is typical.
Pickup routes. Two humbucker pickup positions if the spec includes them. Use the "pickup" role. Position by numeric coordinate — the pickup spacing is fixed by scale length and hardware dimensions, not aesthetic choice.
Control cavity. Single large cavity for pots, switch, and wiring. Use "control_cavity". Position per spec.
Jack. Output jack hole. Use "jack". Usually a small round opening; place 8–12 nodes around it to get a clean circular outline.
Embedded Pi 5 cavity. The Smart Guitar has an internal cavity for the Raspberry Pi 5 and related electronics. This is a body cavity, not a body top opening — whether it should be represented as a void in the 2D outline depends on whether you're modeling the top plate or the full body. Use "other" if you do include it.
Recommended sequence: draw the outer body outline first and verify its dimensions. Add ergonomic voids next since they're the largest and their positions are part of the body's visual identity. Add pickup routes and control cavity third. Add jack and any auxiliary voids last.
Between each step, save a session. Voids are cumulative; each step adds complexity, and a bad edit late in the sequence can cascade. Having intermediate sessions lets you back out to a known-good state.
A note on dimensional truth
The Smart Guitar spec lives in your design documents as numbers: body width 444.5mm, body length 368.3mm, ergonomic void positions relative to body center, pickup spacing from neck reference, and so on. The Body Outline Editor is where those numbers become geometry.
The single most important discipline at this stage: every critical dimension should come from numeric entry, not from visual judgment. Numeric entry is slower than drawing, but slower at this stage saves tremendous downstream work. A void that's "about right" visually in the editor becomes a feature that's several millimeters off in CAD, which becomes a measurement correction in Fusion 360, which becomes a tool-path adjustment in CAM, which becomes wasted wood on the CNC. Every one of those correction steps is more expensive than getting it right here.
Numeric coordinates for every void node, every centerline node, every key body outline node. Visual judgment for the curves between them.

Internal-use notes for Chapter 6:
The mirror limitation on voids is a real workflow problem for paired features. Working around it via session-file editing is possible but not something a non-developer user would do. If Smart Guitar v1 has paired voids that must be symmetric, plan on either (a) drawing them carefully and accepting minor asymmetry, (b) drawing one and asking the engineer to script a mirror operation on the session file, or (c) pushing to add void mirror support before production use.
No multi-path operations. You can't select multiple voids and move them together. You can't copy a void to another position. You can't duplicate a void with a transformation. These would all be v3.1+ enhancements. For now, each void is drawn from scratch.
Void templates would be a quick win. Standard pickup route dimensions, standard control cavity shapes, standard jack hole templates — each as a one-click "insert standard X" feature. The data is already known from hardware specs. v3.1 candidate.
Role labels are stored as strings. There's no enum enforcement. In principle, a corrupted or hand-edited session could have a role value that isn't in the six standard categories, and the editor would load it but display it with the "other" color. Worth noting if you're ever debugging loaded sessions that render oddly.

Chapter 7: Templates, Measure, Grid, and View Controls
This chapter covers four supporting features that don't create geometry directly but make the geometry work easier: templates that give you a starting outline, the measure tool for checking distances, grid controls for alignment, and view controls for navigating the canvas. Each of these is small in scope but meaningful in daily use.
The template library
Eight built-in templates ship with the editor, spanning common acoustic and electric body shapes. Each template loads a pre-drawn outline with realistic dimensions — not exact replicas of specific instrument models, but reasonable starting approximations.
Template selection is in the toolbar. The Template dropdown sits in its own group, with a Load Template button next to it.
The eight templates:
Acoustic:

Dreadnought — body length 508mm, lower bout 394mm, upper bout 286mm, waist 254mm
Jumbo — 530 / 432 / 304 / 280
OM/000 — 482 / 380 / 280 / 254
Classical — 482 / 362 / 280 / 242
Parlor — 400 / 304 / 228 / 204

Electric:

Stratocaster — 400 / 318 / 166 / 220
Les Paul — 400 / 342 / 166 / 230
Telecaster — 394 / 318 / 204 / 240

All dimensions in millimeters, format: body length / lower bout / upper bout / waist.
How templates are generated
Templates aren't loaded from files — they're generated procedurally from four dimensions (body length, lower bout, upper bout, waist) plus a waist position as a fraction of body length. The generator creates 40 points along the right side of the body with linear interpolation between the three width zones (lower bout → waist, waist → upper bout), then mirrors those points to produce the left side. The result is a symmetric closed path with roughly 80 nodes.
Practical implication: the templates are approximate silhouettes, not accurate reproductions. A "Les Paul" template is a shape that resembles a Les Paul in proportion — same bout widths, same waist position — but it's not the actual Gibson Les Paul outline. Nobody will look at a Les Paul template export and say "that's a Les Paul." They'll say "that's a single-cut electric, roughly Les Paul-sized."
Use templates as scaffolding, not as final geometry. Load the closest template, then edit it into the actual shape you want.
Loading a template

Select a template from the dropdown.
Click Load Template.
The current active path's nodes are replaced with the template's nodes.
The template runs through Paper.js's .smooth() immediately, giving every node symmetric Bezier handles.
The view auto-centers on the new outline.

Important behavior: loading a template replaces the outer path only. It doesn't affect voids. If you have voids drawn and load a template, the voids stay where they are, now possibly inside (or outside) the new outer outline. Usually you want to start fresh — hit New before loading a template if the previous geometry isn't needed.
Loading a template pushes a state onto the undo stack, so Ctrl+Z recovers the previous geometry if you load by accident.
Template-to-instrument-spec mapping
When you load a template, the editor also updates the separate Instrument dropdown (the one next to the Solve Outline button) to a matching instrument spec. The mapping:
TemplateInstrument SpecDreadnoughtdreadnoughtJumbojumboOM/000dreadnoughtClassicalcuatro_venezolanoParlorcuatro_venezolanoStratocasterstratocasterLes PaulstratocasterTelecasterstratocaster
This mapping is approximate. "Classical" maps to "cuatro_venezolano" because those are the closest matches in the backend's instrument spec list, not because they're actually the same instrument. If you're using the Solve Outline feature (Chapter 9), the instrument spec matters — double-check it after loading a template.
Why no Smart Guitar template
There is no Smart Guitar template in the built-in library. The eight templates are standard instrument shapes; the Smart Guitar is a specific design that doesn't match any of them. Load the closest template as scaffolding (Stratocaster or Les Paul, since the Smart Guitar is electric and roughly that size) and then edit aggressively toward the Explorer-Klein hybrid form.
A future enhancement would add a "custom templates" mechanism — load a previously-saved session as a template. This doesn't exist yet; the workaround is to save Smart Guitar sessions and load them via Open Session (Ctrl+O) when you want to start from a known baseline.
The measure tool
Measure is a ruler. It lets you click two points on the canvas and reads out the distance between them in millimeters. It doesn't create geometry or modify anything — it's informational only.
Activating: click the Measure button, or press M. A status label appears at the top-left of the canvas: "Click first point".
Clicking two points:

First click — a blue circle appears at the point. Status updates to "Click second point".
Second click — a second blue circle appears, a dashed blue line connects the two points, and the distance is displayed both in a dedicated readout above the canvas and as a text label at the midpoint of the line.

Auto-fade: after 5 seconds, the markers and labels fade out and disappear. This keeps the canvas clean during extended work sessions.
Cancellation: clicking Measure again before the second point, or pressing M a second time, cancels the measurement without committing.
What measure is for in practice
Verifying dimensions after calibration. Import a reference image, calibrate against one dimension, then use Measure to check a second dimension. If the second dimension reads correctly, calibration is sound. If it's off, there's perspective distortion or the calibration was wrong.
Sanity-checking outline dimensions. After placing key nodes, measure the body width at the widest point or the height at the longest point, and confirm it matches the spec. The bounding-box readout does this automatically for the whole outline, but measure lets you check specific features — width of the waist, distance from neck join to pickup position, etc.
Checking void positions. Measure from a void's center (estimate visually) to a body reference point. Confirm it matches the spec. Faster than reading coordinates off each void node.
General "is this roughly right" check. Even without specs, measure gives you a reality check. Is the upper bout roughly 60-70% of the lower bout? Measure both. Is the waist at approximately 45% of body length? Measure and check.
What measure doesn't do
It doesn't measure path length. The distance shown is the straight-line distance between two clicks, not the distance along a curve. If you want to measure the perimeter of the body or the length of a specific curve segment, there's no tool for that — you'd have to sample many points along the curve and sum the straight-line distances manually, or read from the JSON export after the fact.
It doesn't measure angles. Two clicks give distance, not angle. If you need to check that a feature is at a specific angle relative to the centerline, you'll need to compute it from node coordinates yourself.
It doesn't snap to nodes. A measure click doesn't have node-hit detection — wherever the cursor is when you click, that's the measurement endpoint. To measure node-to-node distance accurately, zoom in before clicking, or do the math from node coordinates in the Nodes panel.
The grid
The coordinate grid is the background reference that makes positioning possible. By default it's on; toggle with G or the "Grid: ON/OFF" button.
What the grid shows:

Minor gridlines at each mm interval (faint)
Major gridlines every 10 mm (brighter)
The origin highlighted with slightly stronger lines
Numeric labels on major gridlines at key intervals

The grid redraws dynamically as you zoom. At very high zoom, you see individual millimeter lines. At low zoom, the minor lines disappear and only the 10mm and 50mm lines remain visible to avoid visual clutter.
Grid with mirror mode: when mirror mode is on, the grid adds a dashed green vertical line at X = 0 — the mirror axis. This is independent of the regular grid; toggling grid off doesn't remove the mirror centerline.
Snap size
The Snap dropdown sets the grid increment for node movement: 1, 5, or 10 mm.
When to use each:
10 mm — roughest positioning. Good for initial node placement when you're sketching. Too coarse for final dimensions.
5 mm — default and most common. Appropriate for overall body shape work where ±2.5mm is acceptable precision.
1 mm — fine work. Use for void positioning, critical dimensions, and final adjustments. Smart Guitar work happens mostly at this setting.
Shift+arrow keyboard override: regardless of snap size, holding Shift while pressing an arrow key moves in 0.1mm increments. This is the only sub-millimeter control; there's no "0.5mm" or "0.1mm" option in the Snap dropdown.
Smart Guitar recommendation: start at 5mm for rough shaping, drop to 1mm for refinement, and use Shift+arrow for the last millimeter of adjustment on critical nodes. For numeric coordinate entry (double-click), snap doesn't apply — you can enter any value to two decimal places.
View controls
The canvas supports pan and zoom.
Zoom. Mouse wheel zooms in and out, anchored at the cursor position. One hundred percent is the default; the range is 25% to 400%. The zoom level shows in the status bar.
Zoom doesn't change geometry or real-world dimensions. A 100mm line is still 100mm at 400% zoom — it just occupies more screen pixels. This matters for the Smart Guitar workflow: don't use zoom level to judge absolute size, use the bounding-box readout.
Pan. Hold Space and drag to pan the view. The view center updates as you drag. Releasing Space commits the pan.
Pan doesn't affect geometry either. You're moving the camera, not the objects.
Resetting the view. There's no "fit to window" or "reset view" button. If you've panned far away from origin and want to get back, the recovery options are:

Zoom out with the wheel until origin comes into view
Load a template (auto-centers the view)
Hit New (resets view to origin)

A "home view" keyboard shortcut would be a reasonable enhancement; it doesn't exist currently.
The status bar as an orientation aid
Below the canvas, the status bar shows six live readouts:

Cursor — current mouse position in mm
Selected — index of the selected node, or em-dash if nothing selected
Nodes — total node count in active path
Zoom — current zoom as percentage
Grid — ON or OFF
Mode — Outer or a void ID

Watch Cursor when you're about to click. The coordinate shown is where the click will land, subject to snapping. If you're trying to click at exactly (120, 0) and the status bar reads (119.8, 0.5), you're close but not there — adjust the mouse before clicking, or click and then use numeric entry to correct.
For Smart Guitar work, Cursor is the fastest way to place nodes with approximate precision. Move the cursor until the readout shows roughly the coordinate you want, then click. The 1mm snap will round it to the nearest millimeter automatically.
Working on the Smart Guitar specifically
Four workflow patterns for Smart Guitar that use this chapter's features:
Template scaffold + aggressive edit. Load Stratocaster or Les Paul as a starting point. Resize via node dragging to approximate the 444.5 × 368.3mm Smart Guitar bounding box. Use the bounding-box readout to verify. Then edit the outline shape into the Explorer-Klein hybrid form.
Measure-before-commit verification. After placing key nodes (butt-center, neck-center, widest points), use Measure to verify: body length should read 368.3mm ± 0.5mm, body width 444.5mm ± 0.5mm. If either is off, fix the nodes before continuing.
Snap progression. Start at 10mm for rough body shape. Drop to 5mm once the general form is right. Drop to 1mm for void placement and final adjustments. Never work at 10mm for final geometry.
Zoomed numeric verification. Zoom in to 300-400% when placing critical dimension nodes (void corners, centerline anchors). The cursor readout becomes reliable at that zoom level, and you can visually confirm nodes are landing exactly where expected.

Internal-use notes for Chapter 7:
The eight built-in templates are under-researched. The dimensions are reasonable but not rigorously sourced to real instruments. Dreadnought 508mm body length is standard, but specific Martin vs Taylor vs Gibson dreadnought dimensions vary. If someone loads "Dreadnought" expecting a Martin HD-28 outline, they'll be disappointed. This is a candidate for upgrade — replace hardcoded dimensions with a JSON config that can be versioned and updated.
No custom template mechanism. You can't save a session as a template for reuse. The workaround (Open Session from a reference .sgession) works but isn't discoverable. A "Save as Template" action would be a useful v3.1 addition.
Measure doesn't persist. After the 5-second fade, the measurement is gone. If you measure, then want to recall the value, you either write it down or measure again. A measurement history panel would be a genuinely useful UX improvement.
Grid labels become unreadable at certain zoom levels. Around 150-200% zoom, the major gridline labels get dense enough that they overlap. Not a critical bug, but visually distracting.
Cursor readout precision is two decimals (0.01mm) but doesn't reflect snapping. The Cursor field shows the raw mouse position, not the snapped position that a click would produce. If snap is at 5mm and cursor reads 122.37, a click lands at 120 — but the readout gives the false impression of pixel-level precision. Worth knowing.

Chapter 8: Saving, Loading, and Exporting
Every piece of work in the Body Outline Editor eventually needs to leave the editor. It either goes downstream to CAM, CAD, or design tools, or it gets preserved so you can continue working on it later. This chapter covers the five ways geometry exits the editor: auto-save, session files, DXF, JSON, and SVG — what each is for, what each preserves, and when to use which.
The five paths out
PathFormatWhat's preservedWhere it goesAuto-saveBrowser localStorageFull editor stateRecovery only — stays in browserSave Session.sgession fileFull editor state + reference imageContinuing work later, sharing with teammatesExport DXF.dxf fileTessellated line geometryCAM, Fusion 360, downstream fabricationExport JSON.json fileTessellated points with structureProgrammatic consumers, API integrationsExport SVG.svg fileBezier curves with stylingDocumentation, web display, illustration
Each is lossy or preserving in different dimensions. Understanding what each loses tells you when to use which.
Auto-save
Every node operation — move, insert, delete, handle drag, nudge, Alt+click — triggers an auto-save to your browser's local storage. You don't invoke it; it happens continuously.
What's saved: the current state of all paths (outer + voids), including every node's anchor point and both Bezier handles, plus viewport state (zoom level and pan position).
What's not saved: the reference image. Auto-save skips it to keep storage overhead low — a typical reference image is megabytes of base64-encoded data and would push localStorage past its quota fast.
Retention: 24 hours. Auto-saves older than a day are discarded automatically on next load.
Recovery: if you close and reopen the browser within 24 hours, a dialog prompts: "Restore auto-saved work from X minutes ago?" Click OK to restore, Cancel to start fresh. The prompt appears once per session; dismissing it means that auto-save is gone.
Visual feedback: a green "✓ Auto-saved" indicator briefly appears in the status bar after each save, fading after two seconds. If you don't see it appear during editing, auto-save is failing — check the browser console for localStorage errors (usually a quota issue on browsers with very restrictive storage limits).
Auto-save is a safety net, not a save format. Don't rely on it for keeping work beyond a day, and don't rely on it across devices or browsers — it's specific to one browser profile on one computer.
Session files (.sgession)
The .sgession format is the editor's native save format. It preserves everything needed to continue editing a design, including the reference image.
Saving: Ctrl+S, or there's no dedicated toolbar button for this action — it's keyboard-only. A browser download dialog appears with the default filename body_outline.sgession. Rename before saving if you want descriptive names.
Loading: Ctrl+O opens a file picker, or drag-and-drop a .sgession file onto the editor (the drop behavior is wired in code).
What's preserved:

All outer outline nodes with full Bezier handle data
All voids with their IDs, roles, and full Bezier handle data
Viewport state (zoom, pan center)
Reference image (if present) as base64-encoded data URL
Calibration factor (imagePixelsPerMM)
Reference image position and opacity

What's not preserved:

Undo/redo history (resets on load)
Selection state (no nodes selected after load)
Any measurement markers
Mirror mode state (defaults to off on load, toggle on manually)

Format details: JSON internally, with the .sgession extension to distinguish from generic JSON exports. File size scales with reference image size — sessions without images are a few KB, sessions with large images can hit 20+ MB because of the base64 image encoding.
The canonical save format for in-progress work. If you're going to stop mid-design and resume later, save a session. Auto-save covers 24 hours; session files cover everything beyond that.
DXF export
DXF is the format that leaves the editor for fabrication. CAM tools, Fusion 360, AutoCAD, and every CNC control software understand DXF. This is where your geometry goes when it stops being editable and starts being machinable.
Invoking: click "Export DXF" in the toolbar. A validation check runs first (Chapter 8's note below). If validation passes, a browser download dialog appears with the default filename body_outline.dxf.
What's preserved:

Outer outline as LINE entities on the BODY_OUTLINE layer
Each void as LINE entities on a VOID_<ROLE> layer (VOID_PICKUP, VOID_CONTROL_CAVITY, etc.)
Correct winding direction (CCW outer, CW voids) enforced at export
DXF version AC1009 (R12) for maximum CAM compatibility
Coordinates in millimeters

What's lost:

All Bezier curve information. Curves are sampled at 20 points each and emitted as straight LINE entities. What was a smooth curve becomes a polygon approximation.
Handle data, cusp/smooth node distinction, selection state — none of it maps to DXF.
The reference image (DXF is geometry-only).

Tessellation detail: each Bezier curve segment between two adjacent nodes is sampled at 20 evenly-spaced t values from 0 to 1. On a typical guitar body outline with 25-40 nodes, this produces 500-800 LINE entities for the outer outline alone — more than enough visual smoothness for all but the tightest curves.
Pre-export validation: before writing the DXF, the exporter runs validateOutlineBeforeExport(), which checks the outer outline for self-intersection — places where the outline crosses itself. If found, a confirmation dialog appears: "⚠️ Self-intersection detected in outline! Found N intersecting segment pair(s). This may cause CAM toolpath errors. Export anyway?" Click OK to export despite the intersection, Cancel to abort and fix the geometry first.
Self-intersections are almost always bugs — they happen when node placement crosses an earlier part of the outline, usually during aggressive shape edits. CAM toolpaths can behave unpredictably on self-intersecting boundaries (which side of the line is "inside"?), so the warning is serious. Fix before exporting unless you have a specific reason to ignore it.
Tight-radius limitations: the 20-point tessellation is fine for gentle curves but coarse for tight radii. A pickup hole with a radius of 10mm tessellated at 20 points will visibly polygon-ize in CAD. The workaround is adding more nodes around tight features in the editor, so each Bezier segment spans a smaller arc and tessellates closer to the true curve. Chapter 6 covers this in more detail for voids.
JSON export
JSON export is for programmatic consumers — other tools, scripts, or backend services that need to read the geometry as structured data rather than as a CAD file.
Invoking: click "Export JSON" in the toolbar, or press Ctrl+E.
What's preserved:

Schema version for forward compatibility
Units (mm) and origin convention (body_center_y_positive_toward_neck)
Metadata (name, source, timestamp)
Outer outline as a points array with winding marked ("winding": "ccw")
Each void as a structured object with id, role, closed: true, winding: "cw", and a points array
paths_control placeholder (currently null) for future control-path support

What's lost:

Same as DXF: Bezier handles, curve structure, cusp/smooth distinction
Reference image
Selection, viewport, undo history

Format shape:
json{
  "schema_version": 1,
  "units": "mm",
  "origin": "body_center_y_positive_toward_neck",
  "metadata": { "name": "untitled", "source": "body_outline_editor_sandbox", "created_at": "..." },
  "outer": { "id": "body", "role": "outer", "closed": true, "winding": "ccw", "points": [[x, y], ...] },
  "voids": [ { "id": "pickup_0", "role": "pickup", "closed": true, "winding": "cw", "points": [[x, y], ...] } ],
  "paths_control": null
}
When to use JSON over DXF: when the consumer is code, not CAD. JSON is easier to parse, easier to validate, easier to transform. The Solve Outline backend API (Chapter 9) accepts JSON-style landmarks, not DXF. Other downstream tooling — spec validators, parametric geometry generators, documentation generators — also want JSON.
When to use DXF over JSON: when the consumer is CAD or CAM. No CNC control software reads JSON.
For Smart Guitar work, both exports are relevant. DXF goes to Fusion 360 for the physical CAM path. JSON goes to the instrument body generator backend for parametric validation and downstream geometry derivation.
SVG export
SVG is for visual display — documentation, web embedding, illustrations in specs or papers.
Invoking: click "Export SVG" in the toolbar.
What's preserved:

Bezier curves as SVG path elements (actual curves, not tessellated)
Stroke color reflecting layer/role (green for body, role colors for voids)
Correct topology

What's lost:

Role metadata (beyond color)
Units (SVG uses its own coordinate space)
Any structured data — SVG is a visual format, not semantic

When to use SVG: when you want the geometry to look right somewhere that isn't CAD. Putting a body outline in a blog post, a design doc, a PowerPoint — SVG is the right format. It scales cleanly, renders in browsers, and preserves curves visually.
SVG is not a fabrication format. Don't feed SVG to a CAM tool and expect good results; convert to DXF first.
The reality check: which format preserves what
A clearer way to think about the export decision:
Keep editing: Session file. Only format that round-trips with full fidelity.
Fabricate: DXF. Universal CAM format.
Programmatic use: JSON. Structured data for code.
Visual display: SVG. Curves stay curves.
Emergency recovery: Auto-save. Browser-local only, 24 hours.
Downloads and file management
All five exports trigger a browser download. The file goes to wherever your browser saves downloads — typically your Downloads folder, but your browser settings control this. The editor doesn't manage files; once the download completes, the file is yours to organize.
The editor doesn't remember what you've exported. There's no export history, no "re-export same filename" button, no indication that an export has occurred other than the download dialog. Re-exporting uses the default filename each time, so if you're iterating and saving multiple versions, rename manually during the save dialog or in the filesystem afterward.
Naming conventions worth adopting
For Smart Guitar work specifically, a naming convention helps when you have multiple iterations:

Session files: smart_guitar_body_YYYYMMDD_vN.sgession
DXF exports: smart_guitar_body_YYYYMMDD_vN.dxf
Related exports (same revision, different format): use the same base name, change extension

The editor defaults to body_outline.* which says nothing about which body, which revision, or when. Rename at save time to whatever naming convention your project uses.
Working on the Smart Guitar specifically
Smart Guitar workflow for this chapter:
Save a session at every meaningful state. "Meaningful" is loose — start of session, after rough shaping, after void placement, before risky edits, after corrections. Sessions are cheap (small files without images) and recoverable (one-click load). Session bloat is not a real problem given the file sizes involved.
Name sessions by revision, not by date alone. smart_guitar_body_v7_ergonomic_voids.sgession tells you what's in it; body_outline_20260420.sgession doesn't.
Export DXF only when the outline is locked. DXF is the handoff to CAM. Don't hand a draft to CAM; hand a committed design. Every DXF export should correspond to a design state you're willing to commit to.
Export JSON alongside DXF when handing off. The JSON is the structured counterpart. If Fusion 360 is where the geometry goes for fabrication, the JSON is what the spec validator, the dimension checker, and the parametric downstream tools consume. Both should exist for every release revision.
Archive sessions at milestones. When a design revision goes to fabrication, save the corresponding session file somewhere durable (outside the browser's localStorage). This is the only way to continue editing that specific design state later, since DXF and JSON can't round-trip back.

Internal-use notes for Chapter 8:
No "export all" option. Getting DXF + JSON + SVG of the same design requires three clicks. A single "export all formats" action would save a few seconds per release cycle. Small v3.1 candidate.
No export history or log. If you export, then export again an hour later, there's no record of what was exported when. For release accountability, you're relying on filesystem timestamps and naming discipline. A lightweight export log (what was exported, when, from what source session) would help. Out of scope for v3.0.
Session format isn't versioned. The session file has a version: 1 field but no forward-compatibility machinery. If the data schema ever changes, loading old sessions may break silently. Worth adding a schema-version check to loadSession() before the schema evolves.
The 24-hour auto-save expiry is hardcoded. No UI to adjust. If a user takes a vacation and comes back to resume work, their auto-save is gone. Not critical — sessions are the real save mechanism — but worth knowing.
Self-intersection detection is O(n²). For a typical 40-node outline it's fast. For a pathological 1000-node outline (which shouldn't happen but could) it would noticeably slow export. Not a concern for normal use.

Chapter 9: Solve Outline and Backend Integration
This chapter covers the Solve Outline feature — the editor's integration with a backend geometry solver. Solve takes landmarks from your drawn outline, sends them to a server, and gets back a mathematically-derived body outline that satisfies design constraints for the selected instrument class. It's the bridge between the freehand editor and parametric design.
What Solve does, conceptually
When you draw a body outline in the editor, you're placing nodes at positions that look right. The shape is visually correct but mathematically arbitrary — it happens to match a dreadnought or a Les Paul because you drew it that way, not because the underlying geometry is derived from first principles.
A parametric body solver works the other way. Given a few key dimensions (lower bout width, waist position, body length) and an instrument class (dreadnought, stratocaster, cuatro venezolano), it derives a mathematically consistent outline from known relationships between features. The result is an outline that's provably self-consistent — the curves tension correctly into the waist, the upper bout proportions match the class's convention, the symmetry is exact.
Solve is the editor's way to say to the backend: "here are the landmarks I care about; generate the outline that satisfies them."
The UI
Three toolbar elements drive Solve:
Instrument dropdown. Lists four instrument specs: Dreadnought, Cuatro Venezolano, Stratocaster, Jumbo. This is the class the solver uses — the body type whose geometric relationships apply. Not to be confused with the Template dropdown (Chapter 7), which is visual scaffolding; this dropdown is semantic classification for the solver.
Solve Outline button. Green-backgrounded to indicate it's an "action" button rather than a neutral control. Click to invoke the solver against the current outline.
Confidence badge. Shows the result of the last solve, with color coding: green ≥70%, amber 40-69%, orange below 40%. Higher is better.
How Solve works when you click the button

Landmark extraction. The editor's pathToLandmarks() function analyzes the outer path and extracts up to five landmarks: lower_bout_max, waist_min, upper_bout_max, butt_center, neck_center. Each is a named point with X/Y coordinates in millimeters.
Landmark validation. validateLandmarks() runs the extracted landmarks through geometric sanity checks: lower bout should be wider than upper bout, waist should be narrower than both bouts, Y-coordinates should order correctly (butt below waist below neck). Warnings appear as an orange toast in the canvas corner; errors abort the solve.
Minimum landmarks check. At least three landmarks (lower_bout_max, butt_center, neck_center) must be present. Fewer aborts with an alert.
Request to backend. The API client posts the landmarks and instrument spec to POST /api/body/solve-from-landmarks. A loading overlay appears: "Solving body geometry..."
Response handling. The backend returns a structured response with a generated outline, dimensions, confidence score, and optional side-height data for 3D.
Outline replacement. If the response includes outline points, the editor replaces the current outer path's nodes with the solver's output. The new outline is smoothed automatically.
Feedback. The confidence badge updates with the solver's reported confidence. A temporary overlay shows the computed dimensions (body length, lower bout, upper bout, waist) for 5 seconds before fading.

Mock mode and live mode
The InstrumentBodyAPI class has two modes: mock and live.
Mock mode (useMock: true, the default). The solver runs locally in the browser. No network calls, no backend. It generates a synthetic response using built-in dimension tables — a dreadnought returns ~520mm body length, ~381mm lower bout; non-dreadnought specs return ~350mm/~250mm. Confidence is hardcoded to 0.85. Response time is artificially delayed by 500ms to simulate a network call.
Mock mode is for testing the UI and the request/response flow without a working backend. The geometry it returns is schematic, not accurate — don't use mock output for design work.
Live mode (useMock: false). The client makes real HTTP calls to the configured baseUrl (default /api). Responses come from the actual solver backend. This is the mode for real work.
Switching modes. There's no UI toggle. Changing modes requires editing the code: window.bodyAPI.useMock = false; in the browser console, or changing the default in the InstrumentBodyAPI constructor.
Why it matters: if you click Solve Outline and get suspiciously generic-looking results, check which mode the client is in. The browser console logs ⚠️ IBG API in MOCK mode or ✅ IBG API connected to /api/body on startup.
The authentication layer
The Solve feature has a paid-tier authentication mechanism. Auth controls are hidden by default but appear when the backend returns a 401 response, or when an API key is already stored.
The auth UI elements (hidden by default):

Login button (green background)
Logout button
User badge (shows "✓ Paid Tier" when authenticated)

How authentication works:

Click Login. A browser prompt asks "Enter your API key for paid tier features:".
The entered key is stored both in the API client (setAuthToken()) and in localStorage (ibg_api_key).
All subsequent requests include Authorization: Bearer <key> header.
On page reload, the stored key is retrieved and applied automatically; the auth UI becomes visible.

How logout works:

Click Logout. The stored key is removed from localStorage and from the client.
User badge clears. Subsequent requests are unauthenticated.

Rate limiting and 429 responses. If the backend returns 429 (rate limit exceeded), the client shows an alert: "Rate limit exceeded. Please wait a moment and try again." The request is not retried automatically.
Security note: API keys are stored in localStorage in plaintext. This is a low-security storage mechanism — any JavaScript running in the same origin can read it. For production use, this is acceptable because the editor is a trusted first-party tool, but it means API keys shouldn't be shared carelessly.
The response format
A successful solve returns a JSON object with several fields:

session_id — a server-side identifier for this solve. Stored in localStorage as ibg_last_session for future reference or resumption.
status — "completed" on success.
confidence — a number between 0 and 1. Drives the confidence badge color.
dimensions — an object with body_length_mm, lower_bout_mm, upper_bout_mm, waist_mm, waist_y_norm. These are the computed dimensions of the solver's output, which may differ from the input landmarks.
outline_points — an array of [x, y] tuples in millimeters. This is the solved outline geometry that replaces the editor's current outline.
side_heights — an optional array of height values for 3D body modeling. Stored in state.sideHeights for downstream use.
radii_by_zone — curvature radii for different body zones (lower bout, waist, upper bout).

The editor uses outline_points to replace the path. The other fields are metadata the backend provides; the editor surfaces some (dimensions in the overlay, confidence in the badge) and stores others (session_id, side_heights) for later reference.
Confidence as a signal
The confidence number drives the badge color and is the editor's single-number summary of how well the solver could fit an outline to your landmarks. Interpreting it:

≥70% (green). Solver was confident. Your landmarks were consistent with the instrument class's geometry, and the generated outline satisfies them well.
40-69% (amber). Solver found a reasonable fit but had to make compromises. Landmarks may be slightly inconsistent, or your drawn shape differs meaningfully from the class norm.
<40% (orange). Solver struggled. Landmarks may conflict with each other or with the class's geometric constraints. The generated outline is unlikely to match intent.

Low confidence is informational. The solver still returns an outline; confidence tells you how much to trust it. For Smart Guitar work, where the body is non-standard, expect lower confidence than for a dreadnought — the solver is classifying against instrument types, and the Smart Guitar doesn't match any of them cleanly.
The workflow that makes sense
Solve isn't "draw something and press the button." It's "draw the landmark points that matter, let the solver fill in the curve math."
Effective Solve workflow:

Start with a template close to your target shape (Chapter 7). This populates the outline with nodes in plausible positions.
Drag the key landmark nodes to their specified positions: lower bout maximum, waist minimum, upper bout maximum, butt center (X=0), neck center (X=0). Use numeric coordinate entry for accuracy.
Pick the closest matching instrument spec from the dropdown.
Click Solve Outline.
The editor replaces your current outline with the solver's output.
Refine the result if needed — the solver produces mathematically consistent geometry, but you may need aesthetic adjustments.

This is iterative. You can solve, edit the result, solve again. Each solve replaces the current outline; if you want to preserve intermediate states, save sessions between solves.
Smart Guitar and Solve: a caveat
The Solve Outline feature is classification-based. It solves geometry against known instrument types. The Smart Guitar is a new design that doesn't map to any of the four available specs (Dreadnought, Cuatro Venezolano, Stratocaster, Jumbo).
Stratocaster is the closest match for the Smart Guitar — both are electric, both are roughly the same size. Solving against Stratocaster produces an outline with Stratocaster-class geometric relationships: upper/lower bout ratios, waist position, curvature style. This may or may not be what the Smart Guitar design calls for.
Two practical approaches:

Use Solve as a starting point, then edit freehand. Solve against Stratocaster, accept the Stratocaster-shaped output, then modify toward the Smart Guitar spec by direct node editing. Solve gives you a clean parametric base; your edits deviate from it toward the actual design.
Don't use Solve for Smart Guitar at all. Draw the outline freehand, using numeric entry for every critical dimension. Accept that the Smart Guitar's geometry is custom and doesn't benefit from class-based derivation.

For ongoing Smart Guitar development, approach 2 is probably right. The Smart Guitar's Explorer-Klein hybrid shape isn't derived from any standard class; trying to fit it to one loses the distinctive character. Save Solve for when you're prototyping a more conventional instrument later.
When a Smart Guitar body spec is fully parametric and documented, a custom instrument spec could be added to the backend and the Solve Outline feature would then apply cleanly. That's a project beyond v3.0 — for now, freehand is the Smart Guitar path.
Error handling
Solve can fail in several ways. Each produces a specific response:

Landmark validation errors. Alert: "Cannot solve: [error message]." Common causes: missing required landmarks (outline too minimal), waist wider than bouts (geometric impossibility), Y-order inverted (landmarks flipped).
Fewer than 3 landmarks. Alert: "Need at least 3 landmarks (lower_bout, butt, neck)." The outline doesn't have enough structure to solve.
Authentication required (401). The auth UI reveals itself, and an alert appears: "Authentication required. Please login for paid tier access."
Rate limited (429). Alert: "Rate limit exceeded. Please wait a moment and try again."
Network or server error. Alert with the error message from the backend, or a generic "Failed to solve" with the underlying error.
Request cancellation. If you click Solve again before the previous request completes, the previous one is cancelled silently. Console logs "Request cancelled".

Errors clear the loading overlay and re-enable the Solve button. Your current outline is not modified when a solve fails.
Testing functions for internal use
The browser console exposes several test helpers:

testBackendAPI() — runs a full API integration test, confirms connectivity and response format.
testAll() — runs all v3.0 tests (includes backend, template, landmarks, self-intersection, weighted mirror).
testTemplate(id) — loads a template by ID and verifies the load.
testLandmarks() — extracts landmarks from the current outline and runs validation.
testWeightedMirror() — runs mirror validation on the current path.
testSelfIntersection() — checks the outer outline for self-crossings.

These are developer tools, not user features. Run them from the browser console when debugging or validating a release.

Internal-use notes for Chapter 9:
The mock mode default is an easy footgun. A user without backend access will click Solve and get mock results that look plausible but aren't real. Nothing in the UI warns about this. Worth adding a visible "MOCK" indicator in live deployments so there's no confusion.
No offline handling beyond the mock mode default. If useMock: false is set and the backend is unreachable, every Solve attempt fails. The client doesn't fall back to mock. For a deployed tool used in environments with intermittent connectivity, explicit offline handling would be worth adding.
Session resumption isn't wired to anything. The ibg_last_session localStorage key is saved but never read back. If the backend supports session continuation (loading a prior solve and iterating), the editor doesn't use that capability. Could be a future feature.
The four instrument specs are limiting. Dreadnought, Cuatro Venezolano, Stratocaster, Jumbo covers a narrow slice of instruments. Les Paul, Telecaster, Classical, Parlor — all in the template library — have no solver-side equivalents. Template-to-spec mapping in the UI (Chapter 7) papers over this by substituting close matches, but it means Solve is only useful for a subset of designs.
Landmark extraction is hardcoded to an outline topology. The algorithm assumes roughly-symmetric, roughly-rectangular bodies. On a truly unusual shape (the Smart Guitar's Explorer-Klein hybrid), extraction may produce landmarks that don't correspond to actual features, causing validation failures or low-confidence solves. This is the practical reason the Smart Guitar doesn't benefit from Solve — the extraction step assumes a body type the Smart Guitar isn't.

The manual is now complete at nine chapters covering the full feature set of v3.0.0.
