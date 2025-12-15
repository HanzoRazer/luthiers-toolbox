"""
Pytest tests for migrated pipeline modules.
Run with: pytest services/api/tests/test_pipelines.py -v
"""
import pytest
from pathlib import Path


# =============================================================================
# ROSETTE PIPELINE TESTS
# =============================================================================

class TestRosetteCalc:
    """Tests for rosette_calc.py"""
    
    def test_compute_basic(self):
        """Test basic rosette channel computation."""
        from app.pipelines.rosette import compute
        
        params = {
            'soundhole_diameter_mm': 100,
            'central_band': {'width_mm': 18, 'thickness_mm': 1.0},
        }
        result = compute(params)
        
        assert 'channel_width_mm' in result
        assert 'channel_depth_mm' in result
        assert result['channel_width_mm'] > 0
        assert result['channel_depth_mm'] > 0
    
    def test_compute_with_purflings(self):
        """Test with inner and outer purflings."""
        from app.pipelines.rosette import compute
        
        params = {
            'soundhole_diameter_mm': 100,
            'central_band': {'width_mm': 18, 'thickness_mm': 1.2},
            'inner_purflings': [
                {'width_mm': 1.5, 'thickness_mm': 0.6},
                {'width_mm': 1.0, 'thickness_mm': 0.5},
            ],
            'outer_purflings': [
                {'width_mm': 2.0, 'thickness_mm': 0.8},
            ],
        }
        result = compute(params)
        
        assert result['channel_width_mm'] > 18  # Wider with purflings
        assert result['channel_depth_mm'] >= 1.2  # At least as thick as central band
    
    def test_compute_empty_purflings(self):
        """Test with empty purfling lists (bug fix validation)."""
        from app.pipelines.rosette import compute
        
        params = {
            'soundhole_diameter_mm': 100,
            'central_band': {'width_mm': 18, 'thickness_mm': 1.0},
            'inner_purflings': [],
            'outer_purflings': [],
        }
        result = compute(params)
        
        # Should not crash (empty list handling)
        # Note: channel_width includes margin (18 * 1.009 = 18.16)
        assert result['channel_width_mm'] >= 18
        assert result['channel_depth_mm'] >= 1.0


class TestRosetteMakeGcode:
    """Tests for rosette_make_gcode.py"""
    
    def test_generate_spiral_basic(self):
        """Test basic spiral G-code generation."""
        from app.pipelines.rosette import generate_spiral_gcode
        
        gcode = generate_spiral_gcode(
            inner_r=40.0,
            outer_r=50.0,
            tool_mm=3.0,
            feed=600,
        )
        
        assert 'G21' in gcode  # mm mode
        assert 'G90' in gcode  # absolute
        assert 'G2' in gcode   # clockwise arcs
        assert 'M30' in gcode  # program end
    
    def test_generate_spiral_parameters(self):
        """Test spiral with custom parameters."""
        from app.pipelines.rosette import generate_spiral_gcode
        
        gcode = generate_spiral_gcode(
            inner_r=35.0,
            outer_r=55.0,
            tool_mm=6.0,
            feed=1200,
            rpm=12000,
            stepdown=0.8,
            total_depth=2.4,
        )
        
        assert 'S12000' in gcode
        assert 'F1200' in gcode
        lines = gcode.split('\n')
        assert len(lines) > 20  # Reasonable G-code length


class TestRosettePostFill:
    """Tests for rosette_post_fill.py"""
    
    def test_fill_template_basic(self):
        """Test basic template filling."""
        from app.pipelines.rosette import fill_template
        
        template = "Tool: {{TOOL_MM}}mm, Feed: {{FEED}}mm/min"
        params = {'TOOL_MM': 6.0, 'FEED': 1200}
        
        result = fill_template(template, params)
        
        assert '6.000mm' in result
        assert '1200' in result
        assert '{{' not in result
    
    def test_fill_template_defaults(self):
        """Test template filling with default values."""
        from app.pipelines.rosette import fill_template, DEFAULT_PARAMS
        
        template = "RPM: {{RPM}}, Safe Z: {{SAFE_Z}}"
        result = fill_template(template, {})
        
        assert str(DEFAULT_PARAMS['RPM']) in result
        assert str(DEFAULT_PARAMS['SAFE_Z']) in result


class TestRosetteToDxf:
    """Tests for rosette_to_dxf.py"""
    
    def test_generate_dxf_basic(self):
        """Test basic DXF generation."""
        from app.pipelines.rosette import generate_rosette_dxf
        
        dxf = generate_rosette_dxf(
            soundhole_r=50.0,
            channel_inner_r=52.0,
            channel_outer_r=62.0,
        )
        
        assert 'CIRCLE' in dxf
        assert 'SOUNDHOLE' in dxf
        assert 'CHANNEL_INNER' in dxf
        assert 'CHANNEL_OUTER' in dxf
        assert 'EOF' in dxf


# =============================================================================
# BRACING PIPELINE TESTS
# =============================================================================

class TestBracingCalc:
    """Tests for bracing_calc.py"""
    
    def test_brace_section_area_parabolic(self):
        """Test parabolic brace section area."""
        from app.pipelines.bracing import brace_section_area_mm2
        
        area = brace_section_area_mm2({
            'type': 'parabolic',
            'width_mm': 10,
            'height_mm': 15,
        })
        
        # Parabolic: 0.66 * width * height (actual implementation uses 0.66, not 2/3)
        expected = 0.66 * 10 * 15
        assert abs(area - expected) < 0.1
    
    def test_brace_section_area_scalloped(self):
        """Test scalloped brace section area."""
        from app.pipelines.bracing import brace_section_area_mm2
        
        area = brace_section_area_mm2({
            'type': 'scalloped',
            'width_mm': 12,
            'height_mm': 18,
            'scallop_depth_mm': 3,
        })
        
        assert area > 0
        assert area < 12 * 18  # Less than full rectangle
    
    def test_estimate_mass(self):
        """Test mass estimation."""
        from app.pipelines.bracing import estimate_mass_grams
        
        # Function signature is positional: (length_mm, area_mm2, density_kg_m3)
        mass = estimate_mass_grams(200, 99, 420)  # Spruce density
        
        # Volume: 200 * 99 = 19800 mm³ = 0.0000198 m³
        # Mass: 0.0000198 * 420 = 0.008316 kg = 8.316g
        assert abs(mass - 8.316) < 0.1


# =============================================================================
# GCODE EXPLAINER TESTS
# =============================================================================

class TestGcodeExplainer:
    """Tests for explain_gcode_ai.py"""
    
    def test_explain_basic_moves(self):
        """Test explanation of basic G-code moves."""
        from app.pipelines.gcode_explainer import ModalState, explain_line
        
        state = ModalState()
        
        # Test G21 (mm mode)
        raw, explanation, _ = explain_line('G21', state)
        assert 'millimeter' in explanation.lower()
        
        # Test G90 (absolute)
        raw, explanation, _ = explain_line('G90', state)
        assert 'absolute' in explanation.lower()
    
    def test_explain_motion(self):
        """Test explanation of motion commands."""
        from app.pipelines.gcode_explainer import ModalState, explain_line
        
        state = ModalState()
        explain_line('G21', state)  # Set units
        
        # Test G0 rapid
        raw, explanation, _ = explain_line('G0 X10 Y20', state)
        assert 'rapid' in explanation.lower() or 'move' in explanation.lower()
        
        # Test G1 feed
        raw, explanation, _ = explain_line('G1 X30 Y40 F1200', state)
        assert 'linear' in explanation.lower() or 'cut' in explanation.lower()


# =============================================================================
# BRIDGE PIPELINE TESTS
# =============================================================================

class TestBridgeToDxf:
    """Tests for bridge_to_dxf.py"""
    
    def test_create_dxf(self, tmp_path):
        """Test DXF creation from bridge model."""
        from app.pipelines.bridge import create_dxf
        
        model = {
            'scale_length_mm': 650.0,
            'nut_width_mm': 43.0,
            'saddle_offset_mm': 2.0,
            'strings': [
                {'name': 'E6', 'x_mm': 0.0, 'y_compensation_mm': 2.5},
                {'name': 'E1', 'x_mm': 37.5, 'y_compensation_mm': 1.0},
            ],
        }
        
        out_path = tmp_path / 'test_bridge.dxf'
        create_dxf(model, out_path)
        
        assert out_path.exists()
        content = out_path.read_text()
        assert 'SADDLE_LINE' in content
        assert 'NUT_REFERENCE' in content


# =============================================================================
# DXF CLEANER TESTS
# =============================================================================

class TestDxfCleaner:
    """Tests for clean_dxf.py (requires ezdxf, shapely)"""
    
    def test_arc_to_points(self):
        """Test arc to points conversion."""
        from app.pipelines.dxf_cleaner import arc_to_points
        import numpy as np
        
        # Create a mock arc object
        class MockArc:
            class Dxf:
                center = type('obj', (object,), {'x': 0, 'y': 0})()
                radius = 10.0
                start_angle = 0
                end_angle = 90
            dxf = Dxf()
        
        arc = MockArc()
        points = arc_to_points(arc, num_segments=4)
        
        assert len(points) == 4
        # First point should be at (10, 0)
        assert abs(points[0][0] - 10) < 0.01
        assert abs(points[0][1] - 0) < 0.01


# =============================================================================
# HARDWARE PIPELINE TESTS
# =============================================================================

class TestHardwareLayout:
    """Tests for hardware_layout.py"""
    
    def test_generate_dxf_circles(self):
        """Test DXF generation with circles."""
        from app.pipelines.hardware import generate_dxf
        
        items = [
            {'type': 'circle', 'x': 0, 'y': 0, 'r': 5, 'layer': 'TUNERS'},
            {'type': 'circle', 'x': 10, 'y': 0, 'r': 5, 'layer': 'TUNERS'},
        ]
        
        dxf = generate_dxf(items)
        
        assert dxf.count('CIRCLE') == 2
        assert 'TUNERS' in dxf
        assert 'EOF' in dxf
    
    def test_generate_dxf_rectangles(self):
        """Test DXF generation with rectangles."""
        from app.pipelines.hardware import generate_dxf
        
        items = [
            {'type': 'rectangle', 'x': 0, 'y': 0, 'w': 50, 'h': 30, 'layer': 'CAVITIES'},
        ]
        
        dxf = generate_dxf(items)
        
        assert 'LWPOLYLINE' in dxf
        assert 'CAVITIES' in dxf


# =============================================================================
# WIRING PIPELINE TESTS
# =============================================================================

class TestSwitchValidate:
    """Tests for switch_validate.py"""
    
    def test_validate_3way_valid(self):
        """Test valid 3-way switch configuration."""
        from app.pipelines.wiring import validate
        
        result = validate('3-way', ['Neck', 'Both', 'Bridge'])
        
        assert result['valid'] is True
        assert result['combo_count'] == 3
        assert result['excess'] == 0
    
    def test_validate_3way_exceed(self):
        """Test 3-way switch capacity exceeded."""
        from app.pipelines.wiring import validate
        
        result = validate('3-way', ['Neck', 'Neck+Mid', 'Mid', 'Mid+Bridge', 'Bridge'])
        
        assert result['valid'] is False
        assert result['excess'] == 2
    
    def test_validate_5way(self):
        """Test 5-way switch configuration."""
        from app.pipelines.wiring import validate
        
        result = validate('5-way', ['Neck', 'Neck+Mid', 'Mid', 'Mid+Bridge', 'Bridge'])
        
        assert result['valid'] is True
        assert result['combo_count'] == 5
    
    def test_suggest_hardware(self):
        """Test hardware suggestion."""
        from app.pipelines.wiring import suggest_hardware
        
        # 5 combos should suggest 5-way and above
        suggestions = suggest_hardware(['A', 'B', 'C', 'D', 'E'])
        
        assert '5-way' in suggestions
        assert '3-way' not in suggestions


class TestTrebleBleed:
    """Tests for treble_bleed.py"""
    
    def test_recommend_parallel(self):
        """Test parallel treble bleed recommendation."""
        from app.pipelines.wiring import recommend
        
        result = recommend(500000, 500, 'parallel')
        
        assert 'cap_pf' in result
        assert 'resistor_ohm' in result
        assert result['style'] == 'parallel'
        assert result['cap_pf'] > 0
        assert result['resistor_ohm'] > 0
    
    def test_recommend_cap_only(self):
        """Test cap-only treble bleed recommendation."""
        from app.pipelines.wiring import recommend
        
        result = recommend(250000, 300, 'cap-only')
        
        assert result['style'] == 'cap-only'
        assert result['resistor_ohm'] is None
        assert result['cap_pf'] > 0
    
    def test_recommend_series(self):
        """Test series treble bleed recommendation."""
        from app.pipelines.wiring import recommend
        
        result = recommend(500000, 500, 'series')
        
        assert result['style'] == 'series'
        assert result['resistor_ohm'] is not None


# =============================================================================
# TOOL LIBRARY DATA TEST
# =============================================================================

class TestToolLibrary:
    """Tests for tool_library.json"""
    
    def test_load_tool_library(self):
        """Test loading tool library JSON."""
        import json
        from pathlib import Path
        
        lib_path = Path(__file__).parent.parent / 'app' / 'data' / 'tool_library.json'
        
        assert lib_path.exists(), f"Tool library not found at {lib_path}"
        
        with open(lib_path) as f:
            data = json.load(f)
        
        assert 'tools' in data
        assert 'materials' in data
        assert 'units' in data
        assert len(data['tools']) >= 10
        assert len(data['materials']) >= 5
    
    def test_tool_structure(self):
        """Test tool entry structure."""
        import json
        from pathlib import Path
        
        lib_path = Path(__file__).parent.parent / 'app' / 'data' / 'tool_library.json'
        
        with open(lib_path) as f:
            data = json.load(f)
        
        tool = data['tools'][0]
        
        assert 'id' in tool
        # Note: tool library uses 'diameter_inch' not 'name'
        assert 'diameter_inch' in tool or 'diameter_mm' in tool
        assert 'default_rpm' in tool
