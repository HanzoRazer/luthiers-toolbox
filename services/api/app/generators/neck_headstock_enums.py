"""
Neck & Headstock Enums — HeadstockStyle and NeckProfile.

Split from neck_headstock_config.py during decomposition.
"""

from enum import Enum


class HeadstockStyle(str, Enum):
    GIBSON_OPEN = "gibson_open"
    GIBSON_SOLID = "gibson_solid"
    FENDER_STRAT = "fender_strat"
    FENDER_TELE = "fender_tele"
    PRS = "prs"
    CLASSICAL = "classical"
    MARTIN = "martin"           # Martin acoustic slotted headstock (OM-GAP-06)
    BENEDETTO = "benedetto"     # Benedetto archtop headstock (BEN-GAP-06)
    PADDLE = "paddle"


class NeckProfile(str, Enum):
    C_SHAPE = "c"
    D_SHAPE = "d"
    V_SHAPE = "v"
    U_SHAPE = "u"
    ASYMMETRIC = "asymmetric"
    COMPOUND = "compound"
