from __future__ import annotations

from .analysis import AnalysisResult

def print_summary(label: str | None, res: AnalysisResult) -> None:
    print("")
    if label:
        print(f"Label: {label}")
    print(f"Dominant: {res.dominant_hz if res.dominant_hz else 'n/a'} Hz")
    print(f"RMS: {res.rms:.6f}   Clipped: {res.clipped}   Confidence: {res.confidence:.2f}")
    if res.peaks:
        print("Top peaks:")
        for p in res.peaks[:8]:
            print(f"  - {p.freq_hz:8.2f} Hz   mag={p.magnitude:.3f}")
    else:
        print("No peaks detected (try higher gain or quieter room).")
    print("")
