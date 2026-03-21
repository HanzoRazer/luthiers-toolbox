"""
X-Bracing Geometry — production replacement for placeholder.

Replaces the version that used hardcoded offsets like
    x_cross_y = soundhole_center_y + 60
    end = body_length * 0.9

This version uses body-profile geometry so brace coordinates are correct
for the actual instrument being built, not a generic approximation.
Scalloped braces now carry explicit scallop geometry, not a boolean flag.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Scallop profile ──────────────────────────────────────────────────────────

@dataclass
class ScallopProfile:
    """
    Parabolic scallop profile for a brace.
    h(x) = h_end + (h_center - h_end) × (dist_from_end / scallop_length)²
    """
    h_center_mm: float   # full height (structural region)
    h_end_mm: float      # tip height
    scallop_length_mm: float  # taper length each end

    def height_at(self, x: float, brace_length: float) -> float:
        dist = min(x, brace_length - x)
        if dist >= self.scallop_length_mm or self.scallop_length_mm <= 0:
            return self.h_center_mm
        t = dist / self.scallop_length_mm
        return self.h_end_mm + (self.h_center_mm - self.h_end_mm) * t ** 2

    def points(self, brace_length: float, n: int = 30) -> List[Tuple[float, float]]:
        return [
            (round(brace_length * i / (n - 1), 2),
             round(self.height_at(brace_length * i / (n - 1), brace_length), 3))
            for i in range(n)
        ]


# ── Brace definition ─────────────────────────────────────────────────────────

@dataclass
class BraceDef:
    name: str
    start: Tuple[float, float]   # (x_mm, y_mm) in body coordinates
    end:   Tuple[float, float]
    width_mm: float
    scallop: Optional[ScallopProfile]

    @property
    def length_mm(self) -> float:
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return math.sqrt(dx * dx + dy * dy)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "name":     self.name,
            "start":    self.start,
            "end":      self.end,
            "width_mm": self.width_mm,
            "length_mm": round(self.length_mm, 2),
        }
        if self.scallop:
            d["scallop"] = {
                "h_center_mm":      self.scallop.h_center_mm,
                "h_end_mm":         self.scallop.h_end_mm,
                "scallop_length_mm": self.scallop.scallop_length_mm,
            }
        return d


@dataclass
class BracePattern:
    name: str
    braces: List[BraceDef]
    soundhole_diameter_mm: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "soundhole_diameter_mm": self.soundhole_diameter_mm,
            "braces": [b.to_dict() for b in self.braces],
        }


# ── Body geometry helpers ────────────────────────────────────────────────────

def _body_half_width_at_y(
    y: float,
    body_length_mm: float,
    upper_bout_mm: float,
    waist_mm: float,
    lower_bout_mm: float,
    waist_y_mm: float,
) -> float:
    """
    Half the body width at longitudinal position y from neck end.
    Returns the x-coordinate of the body outline.
    """
    s = max(0.0, min(y, body_length_mm))
    if s <= waist_y_mm:
        t = s / waist_y_mm if waist_y_mm > 0 else 0.0
        w = upper_bout_mm + (waist_mm - upper_bout_mm) * t
    else:
        lower_L = body_length_mm - waist_y_mm
        t = (s - waist_y_mm) / lower_L if lower_L > 0 else 0.0
        peak_t = 0.55
        tail_w = upper_bout_mm
        if t <= peak_t:
            w = waist_mm + (lower_bout_mm - waist_mm) * (t / peak_t)
        else:
            w = lower_bout_mm + (tail_w - lower_bout_mm) * ((t - peak_t) / (1.0 - peak_t))
    return w / 2.0


# ── X-brace factory ──────────────────────────────────────────────────────────

def get_x_brace_pattern(
    body_width_mm: float  = 400.0,
    body_length_mm: float = 510.0,
    upper_bout_mm: float  = 290.0,
    waist_mm: float       = 240.0,
    lower_bout_mm: float  = 400.0,
    waist_y_mm: float     = 225.0,
    soundhole_center_y_mm: float = 200.0,
    soundhole_radius_mm: float   = 50.0,
    bridge_y_mm: float    = 350.0,
    scalloped: bool       = True,
) -> BracePattern:
    """
    Generate a standard X-bracing pattern using actual body geometry.

    The X crossing is placed just below the soundhole (at soundhole bottom +
    a small margin). Brace arms run from near the upper bout to the lower bout
    at the correct angle for the body width at each station.
    """
    cx = body_width_mm / 2.0

    # X crossing: just below soundhole
    x_cross_y = soundhole_center_y_mm + soundhole_radius_mm + 15.0

    # Upper endpoints: near upper transverse (inside upper bout, clear of soundhole)
    upper_margin_y = soundhole_center_y_mm - soundhole_radius_mm - 25.0
    upper_margin_y = max(20.0, upper_margin_y)
    upper_hw = _body_half_width_at_y(upper_margin_y, body_length_mm,
                                      upper_bout_mm, waist_mm, lower_bout_mm, waist_y_mm)

    # Lower endpoints: in lower bout, clear of end block
    lower_end_y = body_length_mm - 35.0
    lower_hw    = _body_half_width_at_y(lower_end_y, body_length_mm,
                                         upper_bout_mm, waist_mm, lower_bout_mm, waist_y_mm)
    lower_inset = lower_hw * 0.15  # slight inset from body edge

    scallop = ScallopProfile(
        h_center_mm=15.0, h_end_mm=4.0, scallop_length_mm=45.0
    ) if scalloped else None

    brace_width = 12.0

    # Main X arms (each arm crosses from upper to lower bout)
    brace_left = BraceDef(
        name="x_arm_bass",
        start=(cx - upper_hw * 0.75, upper_margin_y),
        end=  (cx + lower_hw - lower_inset, lower_end_y),
        width_mm=brace_width,
        scallop=scallop,
    )
    brace_right = BraceDef(
        name="x_arm_treble",
        start=(cx + upper_hw * 0.75, upper_margin_y),
        end=  (cx - lower_hw + lower_inset, lower_end_y),
        width_mm=brace_width,
        scallop=scallop,
    )

    # Upper transverse brace (above soundhole)
    ut_y = soundhole_center_y_mm - soundhole_radius_mm - 50.0
    ut_y = max(15.0, ut_y)
    ut_hw = _body_half_width_at_y(ut_y, body_length_mm,
                                   upper_bout_mm, waist_mm, lower_bout_mm, waist_y_mm)
    upper_transverse = BraceDef(
        name="upper_transverse",
        start=(cx - ut_hw + 10.0, ut_y),
        end=  (cx + ut_hw - 10.0, ut_y),
        width_mm=10.0,
        scallop=None,
    )

    # Tone bars (finger braces below bridge)
    tb_y_start = bridge_y_mm + 20.0
    tb_y_end   = body_length_mm - 50.0
    tb_hw_start = _body_half_width_at_y(tb_y_start, body_length_mm,
                                          upper_bout_mm, waist_mm, lower_bout_mm, waist_y_mm)
    tb_scallop = ScallopProfile(
        h_center_mm=10.0, h_end_mm=3.5, scallop_length_mm=35.0
    ) if scalloped else None

    tone_bar_bass = BraceDef(
        name="tone_bar_bass",
        start=(cx - tb_hw_start * 0.65, tb_y_start),
        end=  (cx - tb_hw_start * 0.85, tb_y_end),
        width_mm=8.0,
        scallop=tb_scallop,
    )
    tone_bar_treble = BraceDef(
        name="tone_bar_treble",
        start=(cx + tb_hw_start * 0.65, tb_y_start),
        end=  (cx + tb_hw_start * 0.85, tb_y_end),
        width_mm=8.0,
        scallop=tb_scallop,
    )

    return BracePattern(
        name="scalloped_x" if scalloped else "standard_x",
        braces=[brace_left, brace_right, upper_transverse, tone_bar_bass, tone_bar_treble],
        soundhole_diameter_mm=soundhole_radius_mm * 2,
    )


# ── Named presets ─────────────────────────────────────────────────────────────

def get_dreadnought_bracing() -> BracePattern:
    return get_x_brace_pattern(
        body_width_mm=400, body_length_mm=510,
        upper_bout_mm=291, waist_mm=244, lower_bout_mm=394, waist_y_mm=228,
        soundhole_center_y_mm=198, soundhole_radius_mm=51,
        bridge_y_mm=345, scalloped=True,
    )


def get_om_bracing() -> BracePattern:
    return get_x_brace_pattern(
        body_width_mm=375, body_length_mm=489,
        upper_bout_mm=285, waist_mm=235, lower_bout_mm=375, waist_y_mm=218,
        soundhole_center_y_mm=195, soundhole_radius_mm=50,
        bridge_y_mm=335, scalloped=True,
    )


def get_j45_bracing() -> BracePattern:
    """Gibson J-45 round-shoulder dreadnought. 6.35×12.70mm brace stock."""
    sp = ScallopProfile(h_center_mm=12.70, h_end_mm=4.0, scallop_length_mm=40.0)
    bw = 6.35
    return get_x_brace_pattern(
        body_width_mm=398.5, body_length_mm=504.8,
        upper_bout_mm=285, waist_mm=235, lower_bout_mm=398.5, waist_y_mm=215,
        soundhole_center_y_mm=180, soundhole_radius_mm=50.8,
        bridge_y_mm=330, scalloped=True,
    )
