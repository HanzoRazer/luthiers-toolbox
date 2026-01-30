# Rosette Builder Page
import streamlit as st
import io
from PIL import Image

# Import toolbox modules
try:
    from app.cam.rosette.traditional_builder import TraditionalBuilder, PRESET_MATRICES
    from app.cam.rosette.pattern_renderer import PatternRenderer, RenderConfig
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    IMPORT_ERROR = str(e)

st.title("🔘 Rosette Pattern Builder")
st.markdown("Traditional matrix patterns from the masters")

if not MODULES_LOADED:
    st.error(f"Could not load modules: {IMPORT_ERROR}")
    st.stop()

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
    st.markdown(f"**Matrix:** {info['rows']} rows × {info['columns']} columns")
    st.markdown(f"**Materials:** {', '.join(info['materials'])}")

    if info.get('notes'):
        st.info(info['notes'])

    # Show matrix formula
    st.markdown("#### Matrix Formula")
    st.markdown(f"**Column Sequence:** `{' - '.join(map(str, formula.column_sequence))}`")

    st.markdown("**Row Definitions:**")
    for i, row in enumerate(formula.rows, 1):
        row_desc = ", ".join(f"{count}× {mat}" for mat, count in row.items())
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
    st.markdown("### 📋 Project Sheet")

    project = builder.create_project(pattern_id)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Cut List")
        for item in project.cut_list:
            st.markdown(f"- **{item.species.upper()}**: {item.num_strips}× strips @ {item.strip_width_mm}mm × {item.strip_length_mm}mm")

    with col2:
        st.markdown("#### Stick Definitions")
        for stick in project.stick_definitions:
            strips = ", ".join(f"{count}× {mat}" for mat, count in stick.strips)
            st.markdown(f"- **Stick {stick.stick_number}**: {strips}")

    st.markdown("#### Assembly Instructions")
    for i, step in enumerate(project.instructions, 1):
        st.markdown(f"{i}. {step}")

    st.markdown(f"**Difficulty:** {project.difficulty} | **Est. Time:** {project.estimated_time_hours:.1f} hours")

# Download options
st.markdown("---")
st.markdown("### 📥 Downloads")

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
