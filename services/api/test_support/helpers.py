"""Reusable assertion helpers for CAM/G-code tests."""


def assert_valid_gcode(gcode: str):
    assert gcode, "G-code is empty"
    lines = gcode.strip().split("\n")
    assert len(lines) > 0, "G-code has no lines"
    has_g_commands = any(line.strip().startswith("G") for line in lines)
    assert has_g_commands, "G-code has no G commands"


def assert_valid_moves(moves: list):
    assert isinstance(moves, list), "Moves must be list"
    assert len(moves) > 0, "Moves list is empty"
    for i, move in enumerate(moves):
        assert "code" in move, f"Move {i} missing code"
        assert move["code"] in ["G0", "G1", "G2", "G3"], f"Move {i} invalid code: {move['code']}"
