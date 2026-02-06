"""I/O utilities: WAV read/write, manifest generation.

This is the canonical location for WAV I/O. All other modules should
import from here, never directly from scipy.io.wavfile.

Usage:
    from tap_tone_pi.io.wav import read_wav_mono, write_wav_mono
    from tap_tone_pi.io.manifest import write_manifest
"""
