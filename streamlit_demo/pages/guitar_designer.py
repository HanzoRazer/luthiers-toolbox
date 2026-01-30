# Parametric Guitar Designer Page
import streamlit as st
import io
import json
from PIL import Image, ImageDraw

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
    MODULES_LOADED = False
    IMPORT_ERROR = str(e)

st.title("Guitar Body Designer")
st.markdown("Parametric body outlines and templates")

if not MODULES_LOADED:
    st.error(f"Could not load modules: {IMPORT_ERROR}")
    st.stop()

# Sidebar controls
st.sidebar.markdown("### Design Mode")
mode = st.sidebar.radio("Mode", ["Template Library", "Parametric Design"])

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
        st.stop()

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
