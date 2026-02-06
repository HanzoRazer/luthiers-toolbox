"""tap_tone_pi — Unified acoustic measurement package.

Version 2.0.0 consolidates the tap_tone, tap-tone-lab, and modes namespaces
into a single coherent package structure.

Subpackages:
- core: Analysis, config, DSP fundamentals
- capture: Audio and sensor acquisition
- io: WAV I/O, manifest generation
- phase1: Single-channel tap tone analysis
- phase2: Two-channel ODS, coherence, wolf metrics
- bending: MOE/stiffness measurement
- chladni: Pattern frequency indexing
- export: Viewer pack generation
- cli: Command-line interface
- gui: Tkinter GUI

Migration from tap_tone:
    # Old import
    from tap_tone.analysis import analyze_tap
    
    # New import (v2.0.0+)
    from tap_tone_pi.core.analysis import analyze_tap
"""

__version__ = "2.0.0"
__all__ = ["__version__"]
