# tests/test_post_processor.py

"""
Tests for CNC Post-Processor Module (LP-GAP-06)

Validates:
- G43 tool length compensation after M6 tool changes
- G41/G42 cutter radius compensation
- Tool change sequencing with M0/M1 pauses
- Controller-specific dialect support
"""

import pytest
from app.cam.post_processor import (
    PostProcessor,
    PostConfig,
    ToolSpec,
    ToolChangeMode,
    CutterCompMode,
    generate_tool_change,
    generate_cutter_comp_sequence,
)


# =============================================================================
# TOOL LENGTH COMPENSATION (G43) TESTS
# =============================================================================


class TestToolLengthCompensation:
    """Tests for G43 tool length compensation."""

    def test_tool_change_emits_g43_by_default(self):
        """Tool change should emit G43 Hn after M6 by default."""
        post = PostProcessor()
        lines = post.tool_change(tool_number=1, rpm=18000, tool_name="Test Tool")

        gcode = "\n".join(lines)
        assert "T1 M6" in gcode
        assert "G43 H1" in gcode

    def test_tool_change_g43_after_m6(self):
        """G43 should appear AFTER M6 in the sequence."""
        post = PostProcessor()
        lines = post.tool_change(tool_number=3, rpm=12000)

        m6_index = None
        g43_index = None
        for i, line in enumerate(lines):
            if "M6" in line:
                m6_index = i
            if "G43" in line:
                g43_index = i

        assert m6_index is not None, "M6 not found"
        assert g43_index is not None, "G43 not found"
        assert g43_index > m6_index, "G43 must come after M6"

    def test_tool_change_h_equals_tool_number(self):
        """H register should match tool number by default."""
        post = PostProcessor()

        for tool_num in [1, 2, 5, 10]:
            lines = post.tool_change(tool_number=tool_num, rpm=18000)
            gcode = "\n".join(lines)
            assert f"G43 H{tool_num}" in gcode, f"Expected G43 H{tool_num}"

    def test_tool_change_custom_h_register(self):
        """Should support custom H register different from T."""
        post = PostProcessor()
        tool = ToolSpec(tool_number=1, offset_number=5, rpm=18000)
        lines = post.tool_change(tool=tool)

        gcode = "\n".join(lines)
        assert "T1 M6" in gcode
        assert "G43 H5" in gcode  # H5, not H1

    def test_tool_change_g43_disabled(self):
        """Should not emit G43 when disabled."""
        config = PostConfig(emit_tool_length_comp=False)
        post = PostProcessor(config)
        lines = post.tool_change(tool_number=1, rpm=18000)

        gcode = "\n".join(lines)
        assert "T1 M6" in gcode
        assert "G43" not in gcode

    def test_cancel_tool_length_comp(self):
        """Should emit G49 to cancel tool length comp."""
        post = PostProcessor()
        lines = post.cancel_tool_length_comp()

        assert any("G49" in line for line in lines)


# =============================================================================
# CUTTER COMPENSATION (G41/G42) TESTS
# =============================================================================


class TestCutterCompensation:
    """Tests for G41/G42 cutter radius compensation."""

    def test_cutter_comp_left_emits_g41(self):
        """Climb milling should emit G41."""
        post = PostProcessor()
        tool = ToolSpec(tool_number=1, diameter_mm=12.7)
        post._current_tool = tool

        lines = post.cutter_comp_left()
        gcode = "\n".join(lines)
        assert "G41" in gcode
        assert "D1" in gcode

    def test_cutter_comp_right_emits_g42(self):
        """Conventional milling should emit G42."""
        post = PostProcessor()
        tool = ToolSpec(tool_number=2, diameter_mm=6.35)
        post._current_tool = tool

        lines = post.cutter_comp_right()
        gcode = "\n".join(lines)
        assert "G42" in gcode
        assert "D2" in gcode

    def test_cutter_comp_start_climb(self):
        """cutter_comp_start with climb=True should emit G41."""
        post = PostProcessor()
        tool = ToolSpec(tool_number=1)

        lines = post.cutter_comp_start(climb=True, tool=tool)
        assert any("G41" in line for line in lines)

    def test_cutter_comp_start_conventional(self):
        """cutter_comp_start with climb=False should emit G42."""
        post = PostProcessor()
        tool = ToolSpec(tool_number=1)

        lines = post.cutter_comp_start(climb=False, tool=tool)
        assert any("G42" in line for line in lines)

    def test_cutter_comp_cancel_emits_g40(self):
        """Should emit G40 to cancel cutter comp."""
        post = PostProcessor()
        lines = post.cutter_comp_cancel()

        assert any("G40" in line for line in lines)

    def test_cutter_comp_active_tracking(self):
        """Should track cutter comp active state."""
        post = PostProcessor()
        tool = ToolSpec(tool_number=1)

        assert not post.is_cutter_comp_active

        post.cutter_comp_left(tool)
        assert post.is_cutter_comp_active

        post.cutter_comp_cancel()
        assert not post.is_cutter_comp_active

    def test_cutter_comp_custom_d_register(self):
        """Should support custom D register."""
        post = PostProcessor()
        tool = ToolSpec(tool_number=1, offset_number=7)

        lines = post.cutter_comp_left(tool)
        gcode = "\n".join(lines)
        assert "D7" in gcode


# =============================================================================
# TOOL CHANGE SEQUENCING (M0/M1) TESTS
# =============================================================================


class TestToolChangeSequencing:
    """Tests for tool change pause modes."""

    def test_tool_change_no_pause_default(self):
        """Should not include M0/M1 by default."""
        config = PostConfig(tool_change_pause=ToolChangeMode.NONE)
        post = PostProcessor(config)
        lines = post.tool_change(tool_number=1, rpm=18000)

        gcode = "\n".join(lines)
        assert "M0" not in gcode
        assert "M1" not in gcode

    def test_tool_change_mandatory_stop(self):
        """M0 mode should include mandatory stop."""
        config = PostConfig(tool_change_pause=ToolChangeMode.M0)
        post = PostProcessor(config)
        lines = post.tool_change(tool_number=1, rpm=18000)

        gcode = "\n".join(lines)
        assert "M0" in gcode

    def test_tool_change_optional_stop(self):
        """M1 mode should include optional stop."""
        config = PostConfig(tool_change_pause=ToolChangeMode.M1)
        post = PostProcessor(config)
        lines = post.tool_change(tool_number=1, rpm=18000)

        gcode = "\n".join(lines)
        assert "M1" in gcode

    def test_tool_change_dwell_after_spindle(self):
        """Should include dwell after spindle start."""
        config = PostConfig(dwell_after_spindle_ms=3000)
        post = PostProcessor(config)
        lines = post.tool_change(tool_number=1, rpm=18000)

        gcode = "\n".join(lines)
        # Should have G4 dwell command
        assert "G4" in gcode

    def test_tool_change_safe_z_retract(self):
        """Should retract to safe Z after tool change."""
        config = PostConfig(safe_z_mm=75.0)
        post = PostProcessor(config)
        lines = post.tool_change(tool_number=1, rpm=18000)

        gcode = "\n".join(lines)
        assert "G0 Z75.000" in gcode

    def test_tool_change_sequence_order(self):
        """Tool change sequence should be in correct order."""
        config = PostConfig(
            emit_tool_length_comp=True,
            tool_change_pause=ToolChangeMode.M1,
            dwell_after_spindle_ms=2000,
        )
        post = PostProcessor(config)
        lines = post.tool_change(tool_number=1, rpm=18000, tool_name="Ball End")

        # Find indices of key elements
        indices = {}
        for i, line in enumerate(lines):
            if "M5" in line and "M6" not in line:
                indices["spindle_off"] = i
            if "M6" in line:
                indices["tool_change"] = i
            if "G43" in line:
                indices["tool_length_comp"] = i
            if "M3" in line:
                indices["spindle_on"] = i
            if "M1" in line:
                indices["optional_stop"] = i
            if "G4" in line:
                indices["dwell"] = i

        # Verify order: M5 -> M6 -> G43 -> M3 -> M1 -> G4
        assert indices["spindle_off"] < indices["tool_change"]
        assert indices["tool_change"] < indices["tool_length_comp"]
        assert indices["tool_length_comp"] < indices["spindle_on"]
        assert indices["spindle_on"] < indices["optional_stop"]
        assert indices["optional_stop"] < indices["dwell"]


# =============================================================================
# PROGRAM STRUCTURE TESTS
# =============================================================================


class TestProgramStructure:
    """Tests for program header/footer generation."""

    def test_program_header_safety_block(self):
        """Header should include safety block codes."""
        post = PostProcessor()
        lines = post.program_header(program_name="Test Program")

        gcode = "\n".join(lines)
        assert "G21" in gcode  # mm mode
        assert "G90" in gcode  # absolute
        assert "G17" in gcode  # XY plane
        assert "G40" in gcode  # cancel cutter comp
        assert "G49" in gcode  # cancel tool length comp
        assert "G80" in gcode  # cancel canned cycles
        assert "G54" in gcode  # work offset

    def test_program_header_inch_mode(self):
        """Header should support inch mode."""
        post = PostProcessor()
        lines = post.program_header(units="inch")

        gcode = "\n".join(lines)
        assert "G20" in gcode
        assert "G21" not in gcode

    def test_program_footer_safe_end(self):
        """Footer should include safe program end sequence."""
        post = PostProcessor()
        lines = post.program_footer()

        gcode = "\n".join(lines)
        assert "G40" in gcode  # cancel cutter comp
        assert "G49" in gcode  # cancel tool length comp
        assert "M5" in gcode   # spindle off
        assert "M9" in gcode   # coolant off
        assert "M30" in gcode  # program end

    def test_program_header_linuxcnc_g64(self):
        """LinuxCNC should include G64 path blending."""
        config = PostConfig(controller="LinuxCNC")
        post = PostProcessor(config)
        lines = post.program_header()

        gcode = "\n".join(lines)
        assert "G64" in gcode


# =============================================================================
# CONTROLLER DIALECT TESTS
# =============================================================================


class TestControllerDialects:
    """Tests for controller-specific G-code dialects."""

    def test_haas_dwell_in_seconds(self):
        """Haas uses G4 with seconds, not milliseconds."""
        config = PostConfig(controller="Haas", dwell_after_spindle_ms=2000)
        post = PostProcessor(config)
        dwell = post._format_dwell(2000)

        # Haas: G4 P2.000 (2 seconds)
        assert "G4 P2" in dwell

    def test_grbl_dwell_format(self):
        """GRBL uses G4 with seconds (decimal)."""
        config = PostConfig(controller="GRBL", dwell_after_spindle_ms=2000)
        post = PostProcessor(config)
        dwell = post._format_dwell(2000)

        assert "G4 P2" in dwell


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for standalone convenience functions."""

    def test_generate_tool_change_function(self):
        """generate_tool_change should produce valid sequence."""
        lines = generate_tool_change(
            tool_number=1,
            rpm=18000,
            tool_name="1/2 Ball End",
            emit_g43=True,
            pause_mode=ToolChangeMode.M1,
        )

        gcode = "\n".join(lines)
        assert "T1 M6" in gcode
        assert "G43 H1" in gcode
        assert "S18000 M3" in gcode
        assert "M1" in gcode

    def test_generate_cutter_comp_sequence(self):
        """generate_cutter_comp_sequence should return start/cancel pair."""
        start, cancel = generate_cutter_comp_sequence(climb=True, tool_number=3)

        start_gcode = "\n".join(start)
        cancel_gcode = "\n".join(cancel)

        assert "G41" in start_gcode
        assert "D3" in start_gcode
        assert "G40" in cancel_gcode


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests for complete G-code programs."""

    def test_complete_multi_tool_program(self):
        """Generate a complete multi-tool program."""
        config = PostConfig(
            emit_tool_length_comp=True,
            tool_change_pause=ToolChangeMode.M1,
            safe_z_mm=50.0,
        )
        post = PostProcessor(config)

        program_lines = []

        # Header
        program_lines.extend(post.program_header(program_name="Multi-Tool Test"))

        # Tool 1: Roughing
        program_lines.extend(post.tool_change(
            tool_number=1, rpm=16000, tool_name="1/2 Ball End - Roughing"
        ))
        program_lines.append("( Roughing operations here )")

        # Tool 2: Finishing
        program_lines.extend(post.tool_change(
            tool_number=3, rpm=20000, tool_name="1/8 Ball End - Finishing"
        ))
        program_lines.append("( Finishing operations here )")

        # Footer
        program_lines.extend(post.program_footer())

        gcode = "\n".join(program_lines)

        # Verify structure
        assert gcode.count("M6") == 2  # Two tool changes
        assert gcode.count("G43") == 2  # Two G43 calls
        assert "G43 H1" in gcode
        assert "G43 H3" in gcode
        assert gcode.count("M1") == 2  # Two optional stops
        assert "M30" in gcode  # Program end

    def test_profiling_with_cutter_comp(self):
        """Generate profiling operation with cutter compensation."""
        config = PostConfig(emit_tool_length_comp=True)
        post = PostProcessor(config)

        lines = []

        # Tool change
        tool = ToolSpec(tool_number=1, name="1/4 Flat End", diameter_mm=6.35, rpm=18000)
        lines.extend(post.tool_change(tool=tool))

        # Enable cutter comp for climb milling
        lines.extend(post.cutter_comp_start(climb=True, tool=tool))
        lines.append("( Lead-in move required here )")
        lines.append("G1 X0 Y0 F1000")
        lines.append("( Profile cut )")
        lines.append("G1 X100 Y0")
        lines.append("G1 X100 Y100")

        # Cancel cutter comp
        lines.extend(post.cutter_comp_cancel())

        gcode = "\n".join(lines)

        assert "G43 H1" in gcode
        assert "G41 D1" in gcode
        assert "G40" in gcode

        # Verify G41 comes after G43
        g43_pos = gcode.find("G43")
        g41_pos = gcode.find("G41")
        g40_pos = gcode.find("G40", g41_pos)  # Find G40 after G41

        assert g43_pos < g41_pos < g40_pos


# =============================================================================
# RESOLVES GAPS: LP-GAP-06, EX-GAP-13, SG-GAP-14, OM-PURF-07, FV-GAP-07
# =============================================================================
