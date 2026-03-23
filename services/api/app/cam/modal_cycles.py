"""Modal drilling cycle generation (G81-G89).

Supports both canned cycles and expanded G0/G1 moves.
"""
from typing import List, Dict, Any, Tuple, Optional

from ..core.safety import safety_critical


@safety_critical
def generate_g81_drill(holes, depth, retract, feed, safe_z, use_modal=True):
    return [], {}


@safety_critical
def generate_g83_peck_drill(holes, depth, retract, feed, safe_z, peck_depth=5.0, use_modal=True):
    return [], {}


@safety_critical
def generate_g73_chip_break(holes, depth, retract, feed, safe_z, peck_depth=5.0, chip_break_retract=0.5, use_modal=True):
    return [], {}


@safety_critical
def generate_g84_tap(holes, depth, retract, thread_pitch, spindle_rpm, safe_z, use_modal=True):
    return [], {}


@safety_critical
def generate_g85_bore(holes, depth, retract, feed, safe_z, use_modal=True):
    return [], {}


def should_expand_cycles(post_id):
    return False


@safety_critical
def generate_drilling_gcode(cycle, holes, depth, retract, feed, safe_z, **kwargs):
    return '', {}
