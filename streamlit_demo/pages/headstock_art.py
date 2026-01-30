# Headstock Art Generator Page
import streamlit as st
import io

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
    MODULES_LOADED = False
    IMPORT_ERROR = str(e)

st.title("🎨 Headstock Art Generator")
st.markdown("AI-powered inlay design visualization")

if not MODULES_LOADED:
    st.error(f"Could not load modules: {IMPORT_ERROR}")
    st.stop()

# Check API availability
client = get_image_client(provider="openai")
if not client.is_configured:
    st.warning("⚠️ OpenAI API key not configured. Image generation disabled.")
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
    if st.button("🎨 Generate Headstock Art", disabled=not API_AVAILABLE, type="primary"):
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
    if st.button("🎨 Generate Custom Headstock", disabled=not API_AVAILABLE, type="primary"):
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
            "📥 Download Image (PNG)",
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
st.markdown("### 📚 Template Gallery")

cols = st.columns(4)
for i, (tid, template) in enumerate(HEADSTOCK_TEMPLATES.items()):
    with cols[i % 4]:
        st.markdown(f"**{template['name']}**")
        st.caption(template['description'][:50] + "...")
