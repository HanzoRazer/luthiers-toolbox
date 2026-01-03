from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_artifact_linkage_gate_script_exists_and_importable():
    p = Path("scripts/governance/check_artifact_linkage_invariants.py")
    assert p.exists()
    assert p.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3")
