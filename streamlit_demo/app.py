# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Luthier's Toolbox - Streamlit Demo
A web interface for guitar design and CAM tools
"""

import os
import sys
from pathlib import Path

# Add API to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api"))

# Load environment
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

import streamlit as st

# Page config
st.set_page_config(
    page_title="Luthier's Toolbox",
    page_icon="guitar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #8B4513;
        text-align: center;
        padding: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background-color: #8B4513;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Luthier's Toolbox")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Tool",
    [
        "Home",
        "Rosette Builder",
        "Headstock Art",
        "Guitar Designer",
        "Calculator Suite",
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Demo Version**")
st.sidebar.markdown("Built with Streamlit")


def show_home():
    """Home page content."""
    st.markdown('<p class="main-header">Luthier\'s Toolbox</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Guitar Design & CAM Tools</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Rosette Builder")
        st.markdown("""
        - Traditional matrix patterns
        - Masters: Torres, Hauser, Romanillos
        - Formula-accurate rendering
        - Cut lists & assembly instructions
        """)

    with col2:
        st.markdown("### Headstock Art")
        st.markdown("""
        - AI-generated inlay designs
        - Multiple headstock styles
        - Custom wood & material combos
        - Hummingbird, Dragon, Tree of Life
        """)

    with col3:
        st.markdown("### Guitar Designer")
        st.markdown("""
        - Parametric body outlines
        - Dimension-driven CAD
        - DXF/SVG export
        - CAM toolpath generation
        """)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Calculator Suite")
        st.markdown("""
        - Basic, Scientific, Financial calculators
        - Fraction calculator for woodworking
        - Luthier-specific calculations
        - Linear regression & statistics
        """)

    st.markdown("---")
    st.info("Select a tool from the sidebar to get started.")


def show_rosette_builder():
    """Rosette Builder page."""
    import io
    from PIL import Image

    st.title("Rosette Pattern Builder")
    st.markdown("Traditional matrix patterns from the masters")

    # Import toolbox modules
    try:
        from app.cam.rosette.traditional_builder import TraditionalBuilder, PRESET_MATRICES
        from app.cam.rosette.pattern_renderer import PatternRenderer, RenderConfig
        MODULES_LOADED = True
    except ImportError as e:
        st.error(f"Could not load modules: {e}")
        return

    # Initialize
    builder = TraditionalBuilder()
    renderer = PatternRenderer(RenderConfig(image_size=600, ring_width_mm=10.0))

    # Sidebar controls
    st.sidebar.markdown("### Pattern Settings")

    # Get patterns organized by master
    masters = builder.list_master_patterns()

    # Master selection
    master = st.sidebar.selectbox(
        "Select Master",
        list(masters.keys())
    )

    # Pattern selection based on master
    patterns = masters[master]
    pattern_names = {p: builder.get_pattern_info(p)["name"] for p in patterns}
    pattern_id = st.sidebar.selectbox(
        "Select Pattern",
        patterns,
        format_func=lambda x: pattern_names[x]
    )

    # Display options
    st.sidebar.markdown("### Display Options")
    num_repeats = st.sidebar.slider("Ring Repeats", 2, 6, 4)
    show_matrix = st.sidebar.checkbox("Show Matrix View", True)
    show_ring = st.sidebar.checkbox("Show Ring View", True)
    show_instructions = st.sidebar.checkbox("Show Instructions", True)

    # Main content
    col1, col2 = st.columns([1, 1])

    # Get pattern info
    info = builder.get_pattern_info(pattern_id)
    formula = PRESET_MATRICES[pattern_id]

    with col1:
        st.markdown(f"### {info['name']}")
        st.markdown(f"**Matrix:** {info['rows']} rows x {info['columns']} columns")
        st.markdown(f"**Materials:** {', '.join(info['materials'])}")

        if info.get('notes'):
            st.info(info['notes'])

        # Show matrix formula
        st.markdown("#### Matrix Formula")
        st.markdown(f"**Column Sequence:** `{' - '.join(map(str, formula.column_sequence))}`")

        st.markdown("**Row Definitions:**")
        for i, row in enumerate(formula.rows, 1):
            row_desc = ", ".join(f"{count}x {mat}" for mat, count in row.items())
            st.markdown(f"- Row {i}: {row_desc}")

    with col2:
        # Render pattern
        if show_matrix:
            st.markdown("#### Matrix Strip View")
            strip_img = renderer.render_matrix_pattern(formula, show_labels=True)
            st.image(strip_img, caption="Matrix structure (before bending)")

        if show_ring:
            st.markdown("#### Rosette Ring View")
            ring_img = renderer.render_rosette_ring(formula, num_repeats=num_repeats)
            st.image(ring_img, caption=f"Ring with {num_repeats} pattern repeats")

    # Project sheet
    if show_instructions:
        st.markdown("---")
        st.markdown("### Project Sheet")

        project = builder.create_project(pattern_id)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Cut List")
            for item in project.cut_list:
                st.markdown(f"- **{item.species.upper()}**: {item.num_strips}x strips @ {item.strip_width_mm}mm x {item.strip_length_mm}mm")

        with col2:
            st.markdown("#### Stick Definitions")
            for stick in project.stick_definitions:
                strips = ", ".join(f"{count}x {mat}" for mat, count in stick.strips)
                st.markdown(f"- **Stick {stick.stick_number}**: {strips}")

        st.markdown("#### Assembly Instructions")
        for i, step in enumerate(project.instructions, 1):
            st.markdown(f"{i}. {step}")

        st.markdown(f"**Difficulty:** {project.difficulty} | **Est. Time:** {project.estimated_time_hours:.1f} hours")

    # Download options
    st.markdown("---")
    st.markdown("### Downloads")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Download ring image
        if show_ring:
            ring_buffer = io.BytesIO()
            ring_img.save(ring_buffer, format="PNG")
            st.download_button(
                "Download Ring Image (PNG)",
                ring_buffer.getvalue(),
                file_name=f"{pattern_id}_ring.png",
                mime="image/png"
            )

    with col2:
        # Download matrix image
        if show_matrix:
            strip_buffer = io.BytesIO()
            strip_img.save(strip_buffer, format="PNG")
            st.download_button(
                "Download Matrix Image (PNG)",
                strip_buffer.getvalue(),
                file_name=f"{pattern_id}_matrix.png",
                mime="image/png"
            )

    with col3:
        # Download project sheet
        project_text = project.print_project_sheet()
        st.download_button(
            "Download Project Sheet (TXT)",
            project_text,
            file_name=f"{pattern_id}_project.txt",
            mime="text/plain"
        )


def show_headstock_art():
    """Headstock Art Generator page."""
    import io

    st.title("Headstock Art Generator")
    st.markdown("AI-powered inlay design visualization")

    # Import toolbox modules
    try:
        from app.cam.headstock import (
            generate_headstock_prompt,
            get_template_prompt,
            list_available_options,
            HEADSTOCK_TEMPLATES,
            WOOD_DESCRIPTIONS,
            INLAY_DESIGNS,
        )
        from app.ai.transport.image_client import get_image_client
        MODULES_LOADED = True
    except ImportError as e:
        st.error(f"Could not load modules: {e}")
        return

    # Check API availability
    client = get_image_client(provider="openai")
    if not client.is_configured:
        st.warning("OpenAI API key not configured. Image generation disabled.")
        API_AVAILABLE = False
    else:
        API_AVAILABLE = True

    # Get available options
    options = list_available_options()

    # Sidebar controls
    st.sidebar.markdown("### Design Mode")
    mode = st.sidebar.radio("Mode", ["Template", "Custom"])

    if mode == "Template":
        st.sidebar.markdown("### Select Template")
        template_id = st.sidebar.selectbox(
            "Template",
            list(HEADSTOCK_TEMPLATES.keys()),
            format_func=lambda x: HEADSTOCK_TEMPLATES[x]["name"]
        )

        template = HEADSTOCK_TEMPLATES[template_id]

        # Show template details
        st.markdown(f"### {template['name']}")
        st.markdown(f"*{template['description']}*")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Specifications")
            st.markdown(f"- **Style:** {template['style']}")
            st.markdown(f"- **Headstock Wood:** {template['headstock_wood']}")
            st.markdown(f"- **Inlay Design:** {template['inlay_design']}")
            st.markdown(f"- **Inlay Material:** {template['inlay_material']}")
            st.markdown(f"- **Tuners:** {template['tuner_style']}")

        with col2:
            st.markdown("#### Wood Description")
            wood_desc = WOOD_DESCRIPTIONS.get(template['headstock_wood'], "N/A")
            st.info(f"**{template['headstock_wood'].title()}:** {wood_desc}")

            inlay_mat_desc = WOOD_DESCRIPTIONS.get(template['inlay_material'], "N/A")
            st.info(f"**{template['inlay_material'].title()}:** {inlay_mat_desc}")

        # Generate button
        if st.button("Generate Headstock Art", disabled=not API_AVAILABLE, type="primary"):
            with st.spinner("Generating with DALL-E 3 (this may take 15-30 seconds)..."):
                prompt = get_template_prompt(template_id)

                response = client.generate(
                    prompt=prompt,
                    size="1024x1024",
                    quality="hd",
                )

                st.session_state['headstock_image'] = response.image_bytes
                st.session_state['headstock_name'] = template['name']

    else:  # Custom mode
        st.sidebar.markdown("### Custom Design")

        style = st.sidebar.selectbox("Headstock Style", options["headstock_styles"])
        headstock_wood = st.sidebar.selectbox("Headstock Wood", list(WOOD_DESCRIPTIONS.keys())[:10])
        inlay_design = st.sidebar.selectbox("Inlay Design", options["inlay_designs"])
        inlay_material = st.sidebar.selectbox("Inlay Material", list(WOOD_DESCRIPTIONS.keys())[10:])
        tuner_style = st.sidebar.text_input("Tuner Style", "chrome vintage tuners")

        # Show selections
        st.markdown("### Custom Headstock Design")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Your Selections")
            st.markdown(f"- **Style:** {style}")
            st.markdown(f"- **Headstock Wood:** {headstock_wood}")
            st.markdown(f"- **Inlay Design:** {inlay_design}")
            st.markdown(f"- **Inlay Material:** {inlay_material}")
            st.markdown(f"- **Tuners:** {tuner_style}")

        with col2:
            st.markdown("#### Inlay Description")
            inlay_desc = INLAY_DESIGNS.get(inlay_design, "Custom design")
            st.info(inlay_desc[:300] + "..." if len(inlay_desc) > 300 else inlay_desc)

        # Additional details
        additional = st.text_area("Additional Details (optional)", placeholder="Add any specific details for the AI...")

        # Generate button
        if st.button("Generate Custom Headstock", disabled=not API_AVAILABLE, type="primary"):
            with st.spinner("Generating with DALL-E 3 (this may take 15-30 seconds)..."):
                prompt = generate_headstock_prompt(
                    style=style,
                    headstock_wood=headstock_wood,
                    inlay_design=inlay_design,
                    inlay_material=inlay_material,
                    tuner_style=tuner_style,
                    additional_details=additional if additional else None,
                )

                response = client.generate(
                    prompt=prompt,
                    size="1024x1024",
                    quality="hd",
                )

                st.session_state['headstock_image'] = response.image_bytes
                st.session_state['headstock_name'] = f"{style}_{inlay_design}"

    # Display generated image
    if 'headstock_image' in st.session_state:
        st.markdown("---")
        st.markdown("### Generated Headstock Art")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.image(st.session_state['headstock_image'], caption="AI Generated Headstock")

        with col2:
            st.markdown("#### Download")
            st.download_button(
                "Download Image (PNG)",
                st.session_state['headstock_image'],
                file_name=f"{st.session_state['headstock_name']}_headstock.png",
                mime="image/png"
            )

            st.markdown("#### Notes")
            st.info("""
            This is an AI-generated concept image.
            For actual inlay work, you'll need:
            - Vector artwork (DXF/SVG)
            - Professional inlay design
            - CNC cutting files
            """)

    # Gallery of templates
    st.markdown("---")
    st.markdown("### Template Gallery")

    cols = st.columns(4)
    for i, (tid, template) in enumerate(HEADSTOCK_TEMPLATES.items()):
        with cols[i % 4]:
            st.markdown(f"**{template['name']}**")
            st.caption(template['description'][:50] + "...")


def show_guitar_designer():
    """Parametric Guitar Designer page."""
    import io
    import json
    from PIL import Image, ImageDraw

    st.title("Guitar Body Designer")
    st.markdown("Parametric body outlines and templates")

    # Import toolbox modules
    try:
        from app.instrument_geometry.body import (
            get_body_outline,
            get_available_outlines,
            get_body_metadata,
            get_body_dimensions,
            list_bodies_by_category,
            get_dxf_path,
            BodyDimensions,
            generate_parametric_outline,
            compute_bounding_box,
        )
        MODULES_LOADED = True
    except ImportError as e:
        st.error(f"Could not load modules: {e}")
        return

    # Helper function to render body outline
    def render_body_outline(outline, title="Body Outline", width=600, height=600):
        """Render body outline as PIL Image."""
        if not outline or len(outline) < 3:
            return None

        # Compute bounding box
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        body_width = max_x - min_x
        body_height = max_y - min_y

        # Calculate scale to fit in image with padding
        padding = 40
        scale_x = (width - 2 * padding) / body_width if body_width > 0 else 1
        scale_y = (height - 2 * padding) / body_height if body_height > 0 else 1
        scale = min(scale_x, scale_y)

        # Create image
        img = Image.new("RGB", (width, height), "#f5f5f0")
        draw = ImageDraw.Draw(img)

        # Draw grid
        grid_color = "#e0e0e0"
        for i in range(0, width, 50):
            draw.line([(i, 0), (i, height)], fill=grid_color, width=1)
        for i in range(0, height, 50):
            draw.line([(0, i), (width, i)], fill=grid_color, width=1)

        # Transform and draw outline
        def transform(p):
            x = (p[0] - min_x) * scale + padding
            y = height - ((p[1] - min_y) * scale + padding)  # Flip Y
            return (x, y)

        transformed = [transform(p) for p in outline]

        # Draw filled body
        draw.polygon(transformed, fill="#8B4513", outline="#5a2d0c")

        # Draw outline again for emphasis
        draw.polygon(transformed, outline="#2c1a0d", width=2)

        # Draw centerline
        center_x = width / 2
        draw.line([(center_x, padding - 10), (center_x, height - padding + 10)],
                  fill="#666666", width=1)

        # Draw dimension lines
        draw.text((10, 10), f"{body_width:.1f} x {body_height:.1f} mm", fill="#333333")

        return img

    # Sidebar controls
    st.sidebar.markdown("### Design Mode")
    mode = st.sidebar.radio("Mode", ["Template Library", "Parametric Design"])

    if mode == "Template Library":
        st.sidebar.markdown("### Select Category")
        category = st.sidebar.selectbox(
            "Category",
            ["acoustic", "electric", "other"],
            format_func=lambda x: x.title()
        )

        # Get bodies in category
        bodies = list_bodies_by_category(category)

        if not bodies:
            st.warning(f"No bodies found in {category} category")
            return

        # Create friendly names
        body_names = {}
        for body_id in bodies:
            meta = get_body_metadata(body_id)
            if meta:
                body_names[body_id] = body_id.replace("_", " ").title()

        selected_body = st.sidebar.selectbox(
            "Body Template",
            bodies,
            format_func=lambda x: body_names.get(x, x.title())
        )

        # Get body info
        meta = get_body_metadata(selected_body)
        outline = get_body_outline(selected_body, detailed=True)

        # Main content
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"### {body_names.get(selected_body, selected_body.title())}")

            # Render outline
            img = render_body_outline(outline, title=selected_body)
            if img:
                st.image(img, caption=f"{selected_body.replace('_', ' ').title()} body outline")

        with col2:
            st.markdown("#### Specifications")
            if meta:
                st.markdown(f"- **Width:** {meta['width_mm']:.1f} mm ({meta['width_mm']/25.4:.2f}\")")
                st.markdown(f"- **Height:** {meta['height_mm']:.1f} mm ({meta['height_mm']/25.4:.2f}\")")
                st.markdown(f"- **Category:** {meta['category'].title()}")
                st.markdown(f"- **Points:** {len(outline):,}")

            # Scale adjustment
            st.markdown("#### Scale")
            scale_percent = st.slider("Scale %", 50, 150, 100, 5)
            scale_factor = scale_percent / 100.0

            if scale_factor != 1.0:
                scaled_outline = [(x * scale_factor, y * scale_factor) for x, y in outline]
                bbox = compute_bounding_box(scaled_outline)
                st.info(f"Scaled: {bbox['width']:.1f} x {bbox['height']:.1f} mm")

        # Downloads
        st.markdown("---")
        st.markdown("### Downloads")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Download outline image
            if img:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                st.download_button(
                    "Download Image (PNG)",
                    img_buffer.getvalue(),
                    file_name=f"{selected_body}_outline.png",
                    mime="image/png"
                )

        with col2:
            # Download points as JSON
            points_json = json.dumps({
                "model": selected_body,
                "dimensions_mm": {"width": meta["width_mm"], "height": meta["height_mm"]} if meta else {},
                "points": outline,
            }, indent=2)
            st.download_button(
                "Download Points (JSON)",
                points_json,
                file_name=f"{selected_body}_points.json",
                mime="application/json"
            )

        with col3:
            # Check for DXF file
            dxf_path = get_dxf_path(selected_body)
            if dxf_path and dxf_path.exists():
                with open(dxf_path, "rb") as f:
                    dxf_bytes = f.read()
                st.download_button(
                    "Download DXF",
                    dxf_bytes,
                    file_name=f"{selected_body}_body.dxf",
                    mime="application/dxf"
                )
            else:
                st.info("DXF not available")

        # Gallery
        st.markdown("---")
        st.markdown("### Template Gallery")

        all_bodies = get_available_outlines()
        cols = st.columns(4)

        for i, body_id in enumerate(all_bodies[:12]):  # Show first 12
            meta = get_body_metadata(body_id)
            with cols[i % 4]:
                st.markdown(f"**{body_id.replace('_', ' ').title()}**")
                if meta:
                    st.caption(f"{meta['category']} - {meta['width_mm']:.0f}x{meta['height_mm']:.0f}mm")

    else:  # Parametric Design mode
        st.sidebar.markdown("### Dimensions (mm)")

        # Preset templates
        presets = {
            "Dreadnought": {"length": 505, "upper": 286, "lower": 394, "waist": 280},
            "Concert": {"length": 480, "upper": 265, "lower": 380, "waist": 250},
            "Jumbo": {"length": 520, "upper": 310, "lower": 430, "waist": 290},
            "Parlor": {"length": 450, "upper": 240, "lower": 350, "waist": 220},
            "OM/000": {"length": 490, "upper": 275, "lower": 385, "waist": 260},
            "Classical": {"length": 485, "upper": 270, "lower": 370, "waist": 255},
            "Custom": {"length": 500, "upper": 280, "lower": 390, "waist": 260},
        }

        preset = st.sidebar.selectbox("Start From Preset", list(presets.keys()))
        defaults = presets[preset]

        body_length = st.sidebar.number_input(
            "Body Length",
            min_value=300.0, max_value=700.0,
            value=float(defaults["length"]),
            step=5.0
        )
        upper_width = st.sidebar.number_input(
            "Upper Bout Width",
            min_value=150.0, max_value=450.0,
            value=float(defaults["upper"]),
            step=5.0
        )
        lower_width = st.sidebar.number_input(
            "Lower Bout Width",
            min_value=200.0, max_value=500.0,
            value=float(defaults["lower"]),
            step=5.0
        )
        waist_width = st.sidebar.number_input(
            "Waist Width",
            min_value=150.0, max_value=400.0,
            value=float(defaults["waist"]),
            step=5.0
        )

        scale_length = st.sidebar.number_input(
            "Scale Length",
            min_value=500.0, max_value=700.0,
            value=648.0,
            step=1.0
        )

        resolution = st.sidebar.slider("Curve Resolution", 24, 96, 48)

        # Generate outline
        dims = BodyDimensions(
            body_length_mm=body_length,
            upper_width_mm=upper_width,
            lower_width_mm=lower_width,
            waist_width_mm=waist_width,
            scale_length_mm=scale_length,
        )

        outline = generate_parametric_outline(dims, resolution=resolution)
        bbox = compute_bounding_box(outline)

        # Main content
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"### Parametric Body Design")
            st.markdown(f"*Based on {preset} preset*")

            # Render outline
            img = render_body_outline(outline, title="Parametric Body")
            if img:
                st.image(img, caption="Custom parametric body outline")

        with col2:
            st.markdown("#### Generated Dimensions")
            st.markdown(f"- **Width:** {bbox['width']:.1f} mm ({bbox['width']/25.4:.2f}\")")
            st.markdown(f"- **Height:** {bbox['height']:.1f} mm ({bbox['height']/25.4:.2f}\")")
            st.markdown(f"- **Points:** {len(outline)}")

            st.markdown("#### Input Parameters")
            st.markdown(f"- **Body Length:** {body_length:.0f} mm")
            st.markdown(f"- **Upper Bout:** {upper_width:.0f} mm")
            st.markdown(f"- **Lower Bout:** {lower_width:.0f} mm")
            st.markdown(f"- **Waist:** {waist_width:.0f} mm")
            st.markdown(f"- **Scale:** {scale_length:.0f} mm")

            # Ratios
            st.markdown("#### Proportions")
            ratio = lower_width / upper_width if upper_width > 0 else 0
            waist_ratio = waist_width / lower_width if lower_width > 0 else 0
            st.info(f"Lower/Upper: {ratio:.2f}\nWaist/Lower: {waist_ratio:.2f}")

        # Downloads
        st.markdown("---")
        st.markdown("### Downloads")

        col1, col2 = st.columns(2)

        with col1:
            # Download image
            if img:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                st.download_button(
                    "Download Image (PNG)",
                    img_buffer.getvalue(),
                    file_name=f"parametric_{preset.lower()}_body.png",
                    mime="image/png"
                )

        with col2:
            # Download points as JSON
            points_json = json.dumps({
                "type": "parametric",
                "preset": preset,
                "parameters": {
                    "body_length_mm": body_length,
                    "upper_width_mm": upper_width,
                    "lower_width_mm": lower_width,
                    "waist_width_mm": waist_width,
                    "scale_length_mm": scale_length,
                },
                "bounding_box": bbox,
                "points": outline,
            }, indent=2)
            st.download_button(
                "Download Design (JSON)",
                points_json,
                file_name=f"parametric_{preset.lower()}_design.json",
                mime="application/json"
            )

        # Comparison with templates
        st.markdown("---")
        st.markdown("### Compare with Templates")
        st.caption("Your parametric design compared to standard body sizes")

        comparison_data = [
            ("Dreadnought", 404, 510),
            ("Jumbo", 474, 385),
            ("OM/000", 398, 500),
            ("Classical", 371, 490),
            ("Your Design", bbox['width'], bbox['height']),
        ]

        cols = st.columns(len(comparison_data))
        for i, (name, w, h) in enumerate(comparison_data):
            with cols[i]:
                is_custom = name == "Your Design"
                st.markdown(f"**{name}**")
                if is_custom:
                    st.markdown(f":green[{w:.0f} x {h:.0f} mm]")
                else:
                    st.markdown(f"{w:.0f} x {h:.0f} mm")


def show_calculators():
    """Calculator Suite page."""
    st.title("Calculator Suite")
    st.markdown("Professional calculators for luthiers and woodworkers")

    # Import calculators
    try:
        from app.calculators.suite import (
            BasicCalculator,
            FractionCalculator,
            ScientificCalculator,
            FinancialCalculator,
            LuthierCalculator,
        )
        MODULES_LOADED = True
    except ImportError as e:
        st.error(f"Could not load calculator modules: {e}")
        return

    # Calculator type selection
    calc_type = st.sidebar.selectbox(
        "Calculator Type",
        ["Basic", "Scientific", "Fraction", "Financial", "Luthier/Woodworking"]
    )

    # Initialize calculators in session state
    if 'basic_calc' not in st.session_state:
        st.session_state.basic_calc = BasicCalculator()
    if 'sci_calc' not in st.session_state:
        st.session_state.sci_calc = ScientificCalculator()
    if 'frac_calc' not in st.session_state:
        st.session_state.frac_calc = FractionCalculator()
    if 'fin_calc' not in st.session_state:
        st.session_state.fin_calc = FinancialCalculator()
    if 'luth_calc' not in st.session_state:
        st.session_state.luth_calc = LuthierCalculator()

    if calc_type == "Basic":
        show_basic_calculator()
    elif calc_type == "Scientific":
        show_scientific_calculator()
    elif calc_type == "Fraction":
        show_fraction_calculator()
    elif calc_type == "Financial":
        show_financial_calculator()
    elif calc_type == "Luthier/Woodworking":
        show_luthier_calculator()


def show_basic_calculator():
    """Basic calculator interface."""
    calc = st.session_state.basic_calc

    st.markdown("### Basic Calculator")
    st.markdown("Standard 4-function calculator with memory")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Expression input
        expr = st.text_input("Enter expression", placeholder="e.g., 5 + 3 * 2", key="basic_expr")

        if st.button("Calculate", key="basic_calc_btn"):
            if expr:
                result = calc.evaluate(expr)
                if calc.error:
                    st.error(f"Error: {calc.error}")
                else:
                    st.success(f"Result: {result}")

        # Display current value
        st.metric("Display", calc.display)

        # Memory indicator
        if calc.has_memory:
            st.info(f"Memory: {calc.memory}")

    with col2:
        st.markdown("#### Quick Operations")

        # Memory buttons
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button("MC", help="Clear memory"):
                calc.memory_clear()
                st.rerun()
            if st.button("M+", help="Add to memory"):
                calc.memory_add()
                st.rerun()
        with col_m2:
            if st.button("MR", help="Recall memory"):
                calc.memory_recall()
                st.rerun()
            if st.button("M-", help="Subtract from memory"):
                calc.memory_subtract()
                st.rerun()

        if st.button("Clear (C)"):
            calc.clear()
            st.rerun()

    # History
    if calc.history:
        st.markdown("#### History")
        for h in calc.history[-5:]:
            st.text(h)


def show_scientific_calculator():
    """Scientific calculator interface."""
    calc = st.session_state.sci_calc

    st.markdown("### Scientific Calculator")
    st.markdown("Advanced functions with statistics and regression")

    # Mode selection
    col1, col2 = st.columns(2)
    with col1:
        angle_mode = st.radio("Angle Mode", ["Radians", "Degrees"], horizontal=True)
        if angle_mode == "Degrees":
            calc.set_degrees()
        else:
            calc.set_radians()

    # Expression input
    expr = st.text_input("Enter expression", placeholder="e.g., sin(pi/2), e^2, sqrt(16)", key="sci_expr")

    if st.button("Calculate", key="sci_calc_btn"):
        if expr:
            result = calc.evaluate(expr)
            if calc.error:
                st.error(f"Error: {calc.error}")
            else:
                st.success(f"Result: {result}")

    st.metric("Display", calc.display)

    # Function tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Trig", "Hyperbolic", "Statistics", "Constants"])

    with tab1:
        st.markdown("**Trigonometric:** sin, cos, tan, asin, acos, atan")
        value = st.number_input("Value", value=0.0, key="trig_val")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("sin"):
                calc.state.display = str(value)
                calc.sin()
                st.rerun()
            if st.button("asin"):
                calc.state.display = str(value)
                calc.asin()
                st.rerun()
        with col2:
            if st.button("cos"):
                calc.state.display = str(value)
                calc.cos()
                st.rerun()
            if st.button("acos"):
                calc.state.display = str(value)
                calc.acos()
                st.rerun()
        with col3:
            if st.button("tan"):
                calc.state.display = str(value)
                calc.tan()
                st.rerun()
            if st.button("atan"):
                calc.state.display = str(value)
                calc.atan()
                st.rerun()

    with tab2:
        st.markdown("**Hyperbolic:** sinh, cosh, tanh, asinh, acosh, atanh")
        value = st.number_input("Value", value=0.0, key="hyp_val")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("sinh"):
                calc.state.display = str(value)
                calc.sinh()
                st.rerun()
            if st.button("asinh"):
                calc.state.display = str(value)
                calc.asinh()
                st.rerun()
        with col2:
            if st.button("cosh"):
                calc.state.display = str(value)
                calc.cosh()
                st.rerun()
            if st.button("acosh"):
                calc.state.display = str(value)
                calc.acosh()
                st.rerun()
        with col3:
            if st.button("tanh"):
                calc.state.display = str(value)
                calc.tanh()
                st.rerun()
            if st.button("atanh"):
                calc.state.display = str(value)
                calc.atanh()
                st.rerun()

    with tab3:
        st.markdown("**Statistics & Regression**")

        # Data entry
        data_input = st.text_input("Enter data (comma-separated)", placeholder="1, 2, 3, 4, 5", key="stat_data")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load Data"):
                calc.stat_clear()
                try:
                    values = [float(x.strip()) for x in data_input.split(",") if x.strip()]
                    for v in values:
                        calc.stat_add(v)
                    st.success(f"Loaded {len(values)} values")
                except ValueError:
                    st.error("Invalid data format")

        with col2:
            if st.button("Clear Stats"):
                calc.stat_clear()
                st.rerun()

        if calc.stat_n > 0:
            st.markdown(f"**n = {calc.stat_n}**")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Sum"):
                    calc.stat_sum()
                    st.rerun()
                if st.button("Mean"):
                    calc.stat_mean()
                    st.rerun()
            with col2:
                if st.button("Std Dev"):
                    calc.stat_stddev()
                    st.rerun()
                if st.button("Variance"):
                    calc.stat_variance()
                    st.rerun()
            with col3:
                if st.button("Min"):
                    calc.stat_min()
                    st.rerun()
                if st.button("Max"):
                    calc.stat_max()
                    st.rerun()

        # Linear Regression
        st.markdown("---")
        st.markdown("**Linear Regression (y = a + bx)**")
        xy_input = st.text_area("Enter X,Y pairs (one per line)", placeholder="1, 2\n2, 4\n3, 6", key="xy_data")

        if st.button("Calculate Regression"):
            calc.stat_clear_xy()
            try:
                for line in xy_input.strip().split("\n"):
                    if line.strip():
                        parts = line.split(",")
                        x, y = float(parts[0].strip()), float(parts[1].strip())
                        calc.stat_add_xy(x, y)
                reg = calc.linear_regression()
                if reg:
                    st.success(f"**{reg['equation']}**")
                    st.markdown(f"- Slope (b): {reg['slope']}")
                    st.markdown(f"- Intercept (a): {reg['intercept']}")
                    st.markdown(f"- Correlation (r): {reg['r']}")
                    st.markdown(f"- R-squared: {reg['r_squared']}")
            except (ValueError, IndexError):
                st.error("Invalid data format. Use: x, y")

    with tab4:
        st.markdown("**Mathematical Constants**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Pi (3.14159...)"):
                calc.pi()
                st.rerun()
            if st.button("e (2.71828...)"):
                calc.euler()
                st.rerun()
        with col2:
            if st.button("Tau (2*pi)"):
                calc.tau()
                st.rerun()
            if st.button("Phi (golden ratio)"):
                calc.phi()
                st.rerun()


def show_fraction_calculator():
    """Fraction calculator interface."""
    calc = st.session_state.frac_calc

    st.markdown("### Fraction Calculator")
    st.markdown("Woodworker-friendly fractions (8ths, 16ths, 32nds)")

    # Precision setting
    precision = st.sidebar.selectbox("Precision", [8, 16, 32, 64], index=1)
    calc.set_precision(precision)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Fraction Input")

        # Parse fraction string
        frac_input = st.text_input("Enter fraction", placeholder="3/4, 2-3/8, or 4' 6-1/2\"", key="frac_input")

        if st.button("Parse", key="frac_parse"):
            if frac_input:
                result = calc.parse_fraction(frac_input)
                if calc.error:
                    st.error(calc.error)
                else:
                    st.success(f"Value: {result}")
                    st.info(f"As fraction: {calc.display_fraction}")

        # Quick fraction entry
        st.markdown("#### Quick Entry")
        col_a, col_b = st.columns(2)
        with col_a:
            numerator = st.number_input("Numerator", min_value=0, value=1, key="frac_num")
        with col_b:
            denominator = st.number_input("Denominator", min_value=1, value=8, key="frac_denom")

        if st.button("Enter Fraction"):
            calc.fraction(numerator, denominator)
            st.rerun()

    with col2:
        st.markdown("#### Current Value")
        st.metric("Decimal", f"{calc.value:.6f}")
        st.metric("Fraction", calc.display_fraction)

        # Convert decimal to fraction
        st.markdown("#### Decimal to Fraction")
        decimal_val = st.number_input("Decimal value", value=0.0, format="%.6f", key="dec_val")

        if st.button("Convert"):
            result = calc.to_fraction(decimal_val)
            st.success(f"{decimal_val} = {result}")

    # Feet-Inches section
    st.markdown("---")
    st.markdown("#### Feet-Inches Calculator")

    col1, col2 = st.columns(2)

    with col1:
        feet = st.number_input("Feet", min_value=0, value=0, key="ft")
        inches = st.number_input("Inches", min_value=0.0, max_value=11.99, value=0.0, key="in")
        frac_n = st.number_input("Fraction numerator", min_value=0, value=0, key="frac_n")
        frac_d = st.selectbox("Fraction denominator", [1, 2, 4, 8, 16, 32], index=3, key="frac_d")

        if st.button("Calculate Total Inches"):
            calc.feet_inches(feet, inches, frac_n, frac_d)
            st.rerun()

    with col2:
        st.markdown("**Result:**")
        total = calc.value
        st.metric("Total Inches", f"{total:.4f}")
        st.metric("Feet-Inches", calc.to_feet_inches(total) if total > 0 else "0\"")


def show_financial_calculator():
    """Financial calculator interface."""
    calc = st.session_state.fin_calc

    st.markdown("### Financial Calculator")
    st.markdown("Time Value of Money (TVM) and business calculations")

    tab1, tab2, tab3 = st.tabs(["Loan/TVM", "Depreciation", "Business"])

    with tab1:
        st.markdown("#### Time Value of Money")
        st.markdown("*Leave one field at 0 to solve for it*")

        col1, col2 = st.columns(2)

        with col1:
            n = st.number_input("N (periods)", min_value=0.0, value=360.0, key="tvm_n")
            i_y = st.number_input("I/Y (interest rate %)", min_value=0.0, value=6.5, key="tvm_iy")
            pv = st.number_input("PV (present value)", value=200000.0, key="tvm_pv")

        with col2:
            pmt = st.number_input("PMT (payment)", value=0.0, key="tvm_pmt")
            fv = st.number_input("FV (future value)", value=0.0, key="tvm_fv")

        solve_for = st.selectbox("Solve for", ["PMT", "PV", "FV", "N", "I/Y"])

        if st.button("Calculate", key="tvm_calc"):
            calc.clear_tvm()
            calc.n = n if n > 0 else None
            calc.i_y = i_y / 12 if i_y > 0 else None  # Monthly rate
            calc.pv = pv if pv != 0 else None
            calc.pmt = pmt if pmt != 0 else None
            calc.fv = fv

            try:
                if solve_for == "PMT":
                    result = calc.solve_pmt()
                    st.success(f"Monthly Payment: ${-result:,.2f}")
                elif solve_for == "PV":
                    result = calc.solve_pv()
                    st.success(f"Present Value: ${result:,.2f}")
                elif solve_for == "FV":
                    result = calc.solve_fv()
                    st.success(f"Future Value: ${result:,.2f}")
                elif solve_for == "N":
                    result = calc.solve_n()
                    st.success(f"Periods: {result:.1f}")
                elif solve_for == "I/Y":
                    result = calc.solve_rate()
                    st.success(f"Rate: {result * 12:.4f}% annually")
            except Exception as e:
                st.error(f"Error: {e}")

        # Amortization preview
        if st.checkbox("Show Amortization Schedule"):
            calc.clear_tvm()
            calc.n = n
            calc.i_y = i_y / 12
            calc.pv = pv
            calc.fv = 0
            calc.solve_pmt()
            schedule = calc.amortization_schedule(min(int(n), 12))

            st.markdown("**First 12 Months:**")
            data = []
            for row in schedule[:12]:
                data.append({
                    "Period": row.period,
                    "Payment": f"${row.payment:,.2f}",
                    "Principal": f"${row.principal:,.2f}",
                    "Interest": f"${row.interest:,.2f}",
                    "Balance": f"${row.balance:,.2f}"
                })
            st.table(data)

    with tab2:
        st.markdown("#### Depreciation Calculator")

        cost = st.number_input("Asset Cost ($)", min_value=0.0, value=15000.0, key="dep_cost")
        salvage = st.number_input("Salvage Value ($)", min_value=0.0, value=1000.0, key="dep_salvage")
        life = st.number_input("Useful Life (years)", min_value=1, value=5, key="dep_life")
        method = st.selectbox("Method", ["Straight-Line", "Double Declining Balance"])

        if st.button("Calculate Depreciation", key="dep_calc"):
            if method == "Straight-Line":
                annual = calc.straight_line(cost, salvage, life)
                st.success(f"Annual Depreciation: ${annual:,.2f}")

                # Show schedule
                st.markdown("**Depreciation Schedule:**")
                data = []
                book_value = cost
                for year in range(1, life + 1):
                    dep = min(annual, book_value - salvage)
                    book_value -= dep
                    data.append({
                        "Year": year,
                        "Depreciation": f"${dep:,.2f}",
                        "Book Value": f"${book_value:,.2f}"
                    })
                st.table(data)
            else:
                st.markdown("**Double Declining Balance:**")
                data = []
                book_value = cost
                for year in range(1, life + 1):
                    dep = calc.declining_balance(cost, salvage, life, year, 2.0)
                    book_value = cost - sum(calc.declining_balance(cost, salvage, life, y, 2.0) for y in range(1, year + 1))
                    data.append({
                        "Year": year,
                        "Depreciation": f"${dep:,.2f}",
                        "Book Value": f"${book_value:,.2f}"
                    })
                st.table(data)

    with tab3:
        st.markdown("#### Business Calculations")

        st.markdown("**Markup & Margin**")
        col1, col2 = st.columns(2)

        with col1:
            cost_val = st.number_input("Cost ($)", min_value=0.0, value=100.0, key="biz_cost")
            markup_pct = st.number_input("Markup %", min_value=0.0, value=50.0, key="biz_markup")

            if st.button("Calculate Markup"):
                price = calc.markup(cost_val, markup_pct)
                st.success(f"Selling Price: ${price:,.2f}")

        with col2:
            margin_pct = st.number_input("Margin %", min_value=0.0, max_value=99.0, value=33.0, key="biz_margin")

            if st.button("Calculate Margin"):
                price = calc.margin(cost_val, margin_pct)
                st.success(f"Selling Price: ${price:,.2f}")

        st.markdown("---")
        st.markdown("**Break-Even Analysis**")

        fixed = st.number_input("Fixed Costs ($)", min_value=0.0, value=5000.0, key="be_fixed")
        price_unit = st.number_input("Price per Unit ($)", min_value=0.01, value=50.0, key="be_price")
        var_cost = st.number_input("Variable Cost per Unit ($)", min_value=0.0, value=30.0, key="be_var")

        if st.button("Calculate Break-Even"):
            try:
                units = calc.breakeven_units(fixed, price_unit, var_cost)
                revenue = units * price_unit
                st.success(f"Break-Even: {units:,.0f} units (${revenue:,.2f} revenue)")
            except ValueError as e:
                st.error(str(e))


def show_luthier_calculator():
    """Luthier/Woodworking calculator interface."""
    calc = st.session_state.luth_calc

    st.markdown("### Luthier & Woodworking Calculator")
    st.markdown("Guitar building and woodworking calculations")

    tab1, tab2, tab3, tab4 = st.tabs(["Frets", "Radius", "Woodworking", "String Tension"])

    with tab1:
        st.markdown("#### Fret Position Calculator")

        scale_length = st.number_input("Scale Length (inches)", min_value=20.0, max_value=30.0, value=25.5, key="fret_scale")
        num_frets = st.slider("Number of Frets", 12, 27, 24)

        if st.button("Calculate Fret Positions"):
            positions = calc.fret_table(scale_length, num_frets)

            data = []
            for pos in positions:
                data.append({
                    "Fret": pos.fret_number,
                    "From Nut": f'{pos.distance_from_nut:.4f}"',
                    "Spacing": f'{pos.distance_from_previous:.4f}"',
                    "To Bridge": f'{pos.remaining_to_bridge:.4f}"'
                })

            st.table(data[:12])  # Show first 12

            if num_frets > 12:
                with st.expander("Show all frets"):
                    st.table(data)

    with tab2:
        st.markdown("#### Radius Calculator")

        calc_mode = st.radio("Calculation Mode", ["From Chord & Height", "Compound Radius", "From 3 Points"])

        if calc_mode == "From Chord & Height":
            chord = st.number_input("Chord Length (straightedge)", min_value=0.1, value=12.0, key="r_chord")
            height = st.number_input("Height (gap at center)", min_value=0.001, value=0.5, key="r_height")

            if st.button("Calculate Radius", key="r_calc1"):
                radius = calc.radius_from_chord(chord, height)
                st.success(f"Radius: {radius:.4f}\"")

        elif calc_mode == "Compound Radius":
            nut_r = st.number_input("Nut Radius", min_value=1.0, value=9.5, key="nut_r")
            saddle_r = st.number_input("Saddle Radius", min_value=1.0, value=14.0, key="saddle_r")
            scale = st.number_input("Scale Length", min_value=20.0, value=25.5, key="comp_scale")
            position = st.number_input("Position (from nut)", min_value=0.0, value=12.75, key="comp_pos")

            if st.button("Calculate", key="r_calc2"):
                radius = calc.compound_radius(nut_r, saddle_r, scale, position)
                st.success(f"Radius at {position}\": {radius:.4f}\"")

        else:  # From 3 Points
            st.markdown("Enter 3 points on the curve:")
            col1, col2 = st.columns(2)
            with col1:
                x1, y1 = st.number_input("X1", value=0.0, key="x1"), st.number_input("Y1", value=0.0, key="y1")
                x2, y2 = st.number_input("X2", value=6.0, key="x2"), st.number_input("Y2", value=0.5, key="y2")
                x3, y3 = st.number_input("X3", value=12.0, key="x3"), st.number_input("Y3", value=0.0, key="y3")

            if st.button("Calculate", key="r_calc3"):
                radius = calc.radius_from_3_points((x1, y1), (x2, y2), (x3, y3))
                st.success(f"Radius: {radius:.4f}\"")

    with tab3:
        st.markdown("#### Woodworking Calculations")

        calc_type = st.selectbox("Calculation", [
            "Board Feet",
            "Wedge Angle",
            "Miter Angle",
            "Dovetail Angle",
            "Kerf Bend Spacing"
        ])

        if calc_type == "Board Feet":
            thickness = st.number_input("Thickness (inches)", min_value=0.25, value=1.0, key="bf_t")
            width = st.number_input("Width (inches)", min_value=1.0, value=6.0, key="bf_w")
            length = st.number_input("Length (feet)", min_value=1.0, value=8.0, key="bf_l")

            if st.button("Calculate Board Feet"):
                bf = calc.board_feet(thickness, width, length)
                st.success(f"Board Feet: {bf:.2f}")

        elif calc_type == "Wedge Angle":
            wedge_length = st.number_input("Length", min_value=0.1, value=12.0, key="w_len")
            thick_end = st.number_input("Thick End", min_value=0.1, value=1.0, key="w_thick")
            thin_end = st.number_input("Thin End", min_value=0.0, value=0.5, key="w_thin")

            if st.button("Calculate Wedge Angle"):
                angle = calc.wedge_angle(wedge_length, thick_end, thin_end)
                st.success(f"Wedge Angle: {angle:.4f} degrees")

        elif calc_type == "Miter Angle":
            num_sides = st.number_input("Number of Sides", min_value=3, value=6, key="miter_sides")

            if st.button("Calculate Miter"):
                angle = calc.miter_angle(num_sides)
                st.success(f"Miter Angle: {angle:.4f} degrees")
                st.info(f"Set your saw to {angle:.1f} degrees")

        elif calc_type == "Dovetail Angle":
            ratio = st.text_input("Ratio (e.g., 1:8)", value="1:8", key="dt_ratio")

            if st.button("Calculate Dovetail"):
                angle = calc.dovetail_angle(ratio)
                st.success(f"Dovetail Angle: {angle:.2f} degrees")

        else:  # Kerf Bend
            bend_radius = st.number_input("Bend Radius", min_value=1.0, value=24.0, key="kerf_r")
            material_t = st.number_input("Material Thickness", min_value=0.1, value=0.25, key="kerf_t")

            if st.button("Calculate Kerf Spacing"):
                spacing = calc.kerf_bend_spacing(bend_radius, material_t)
                st.success(f"Kerf Spacing: {spacing:.4f}\"")

    with tab4:
        st.markdown("#### String Tension Calculator")

        scale = st.number_input("Scale Length (inches)", min_value=20.0, value=25.5, key="tens_scale")
        frequency = st.number_input("Frequency (Hz)", min_value=50.0, value=329.63, key="tens_freq",
                                    help="E4 = 329.63 Hz")
        unit_weight = st.number_input("Unit Weight (lb/in)", min_value=0.00001, value=0.00004, format="%.6f",
                                      key="tens_uw", help="Check string manufacturer specs")

        if st.button("Calculate Tension"):
            result = calc.string_tension(scale, frequency, unit_weight)
            st.success(f"Tension: {result.tension_lbs:.2f} lbs ({result.tension_newtons:.2f} N)")

        # Common string reference
        with st.expander("Common Guitar String Frequencies"):
            st.markdown("""
            | String | Note | Frequency (Hz) |
            |--------|------|----------------|
            | 1st    | E4   | 329.63         |
            | 2nd    | B3   | 246.94         |
            | 3rd    | G3   | 196.00         |
            | 4th    | D3   | 146.83         |
            | 5th    | A2   | 110.00         |
            | 6th    | E2   | 82.41          |
            """)


# Route to the correct page
if page == "Home":
    show_home()
elif page == "Rosette Builder":
    show_rosette_builder()
elif page == "Headstock Art":
    show_headstock_art()
elif page == "Guitar Designer":
    show_guitar_designer()
elif page == "Calculator Suite":
    show_calculators()
