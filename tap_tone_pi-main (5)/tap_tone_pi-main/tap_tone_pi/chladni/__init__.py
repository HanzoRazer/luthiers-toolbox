"""
tap_tone_pi.chladni — Chladni pattern frequency indexing.

Migrated from: modes/chladni/

Modules:
    peaks_from_wav: Extract frequency peaks from sweep/step recordings
    index_patterns: Associate image filenames to detected frequencies

Example:
    python -m tap_tone_pi.chladni.peaks_from_wav \\
        --wav capture.wav --out peaks.json --min-hz 50 --max-hz 2000
"""
