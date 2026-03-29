"""MachineClass enum for saw adapters."""

from __future__ import annotations

from app.calculators.saw_adapters import MachineClass


def test_uses_rim_speed():
    assert MachineClass.BANDSAW.uses_rim_speed is True
    assert MachineClass.TABLE_SAW.uses_rim_speed is True


def test_supports_curves():
    assert MachineClass.BANDSAW.supports_curves is True
    assert MachineClass.TABLE_SAW.supports_curves is False
